"""2D cutting optimizer untuk lembaran triplek/MDF (Tahap 4).

Membungkus `rectpack` (Guillotine / MaxRects) dengan hal-hal yang membuat hasilnya
benar-benar bisa dipakai di bengkel:

- **Kerf**: tebal pisau (default 3 mm) ditambahkan ke setiap part sebelum di-pack,
  lalu dipotong lagi saat pelaporan koordinat sehingga (x, y, w, h) yang keluar
  adalah ukuran part sesungguhnya dan celah antar part = kerf. Ukuran bin sengaja
  dibuat `usable + kerf`: potongan terakhir di tiap sumbu tidak butuh kerf di
  dalam lembar, jadi part yang persis selebar lembaran tetap muat.
- **Trim margin**: tepi lembaran yang dibuang lebih dulu (default 0 mm).
- **Grain**: `rectpack` hanya punya satu flag rotasi per packer, jadi saat
  `respect_grain=True` rotasi dimatikan untuk seluruh lembar. Part yang
  `grain_locked=False` (panel belakang, alas laci, rail plinth) tetap boleh
  di-swap orientasinya secara manual kalau memang tidak muat memanjang.
  Set `respect_grain=False` untuk membiarkan optimizer memutar semua part.
- **Pisah per tebal/material**: papan 18 mm dan 4 mm tidak boleh dicampur dalam
  satu lembar, jadi setiap kombinasi (material, tebal) dipack terpisah.

Output: daftar `Sheet`, masing-masing berisi penempatan part (x, y, w, h) beserta
persentase sisa bahan (waste %).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Tuple

from rectpack import newPacker, PackingBin, PackingMode
from rectpack.guillotine import GuillotineBssfSas
from rectpack.maxrects import MaxRectsBssf

try:                      # dipakai sebagai modul paket maupun skrip lepas
    from .bom_engine import Part, bom_from_json
except ImportError:       # pragma: no cover - jalur eksekusi langsung
    from bom_engine import Part, bom_from_json


# Lembaran standar Indonesia: 2440 x 1220 mm (4 x 8 ft).
SHEET_LENGTH_MM = 2440
SHEET_WIDTH_MM = 1220

_ALGOS = {
    "guillotine": GuillotineBssfSas,   # Best Short Side Fit + Shorter Axis Split
    "maxrects": MaxRectsBssf,
}


@dataclass
class NestConfig:
    sheet_length_mm: int = SHEET_LENGTH_MM
    sheet_width_mm: int = SHEET_WIDTH_MM
    kerf_mm: float = 3.0          # tebal pisau
    trim_mm: float = 0.0          # tepi lembaran yang dibuang lebih dulu
    algorithm: str = "guillotine"  # "guillotine" | "maxrects"
    respect_grain: bool = True    # False = semua part boleh diputar 90 derajat


@dataclass
class Placement:
    part_name: str
    x_mm: float
    y_mm: float
    length_mm: float       # ukuran setelah penempatan (sudah dikurangi kerf)
    width_mm: float
    rotated: bool
    piece_index: int       # keping ke-berapa dari part dengan qty > 1

    def area_mm2(self) -> float:
        return self.length_mm * self.width_mm


@dataclass
class Sheet:
    index: int
    material: str
    thickness_mm: int
    sheet_length_mm: int
    sheet_width_mm: int
    placements: List[Placement] = field(default_factory=list)

    @property
    def used_area_mm2(self) -> float:
        return sum(p.area_mm2() for p in self.placements)

    @property
    def sheet_area_mm2(self) -> int:
        return self.sheet_length_mm * self.sheet_width_mm

    @property
    def utilization_pct(self) -> float:
        return 100.0 * self.used_area_mm2 / self.sheet_area_mm2

    @property
    def waste_pct(self) -> float:
        return 100.0 - self.utilization_pct

    def to_dict(self) -> dict:
        d = asdict(self)
        d["utilization_pct"] = round(self.utilization_pct, 2)
        d["waste_pct"] = round(self.waste_pct, 2)
        return d


@dataclass
class NestResult:
    sheets: List[Sheet]
    unplaced: List[Tuple[str, float, float]]   # part yang tidak muat di lembaran manapun
    config: NestConfig

    @property
    def total_waste_pct(self) -> float:
        total = sum(s.sheet_area_mm2 for s in self.sheets)
        used = sum(s.used_area_mm2 for s in self.sheets)
        return 100.0 - (100.0 * used / total) if total else 0.0

    def summary(self) -> dict:
        return {
            "sheets_used": len(self.sheets),
            "sheets_per_material": _count_by(
                [f"{s.material} ({s.thickness_mm}mm)" for s in self.sheets]
            ),
            "total_waste_pct": round(self.total_waste_pct, 2),
            "per_sheet_waste_pct": [round(s.waste_pct, 2) for s in self.sheets],
            "pieces_placed": sum(len(s.placements) for s in self.sheets),
            "pieces_unplaced": len(self.unplaced),
            "unplaced": [
                {"part_name": n, "length_mm": l, "width_mm": w} for n, l, w in self.unplaced
            ],
        }

    def to_dict(self) -> dict:
        return {
            "config": asdict(self.config),
            "summary": self.summary(),
            "sheets": [s.to_dict() for s in self.sheets],
        }


def _count_by(items: Sequence[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for it in items:
        out[it] = out.get(it, 0) + 1
    return out


def _group_key(part: Part) -> Tuple[str, int]:
    return (part.material or "board", part.thickness_mm)


def nest_parts(parts: Sequence[Part], cfg: Optional[NestConfig] = None) -> NestResult:
    """Susun semua part ke lembaran standar; kembalikan koordinat + waste per lembar."""
    cfg = cfg or NestConfig()
    if cfg.algorithm not in _ALGOS:
        raise ValueError(f"algorithm harus salah satu dari {sorted(_ALGOS)}")

    usable_l = cfg.sheet_length_mm - 2 * cfg.trim_mm
    usable_w = cfg.sheet_width_mm - 2 * cfg.trim_mm
    kerf = cfg.kerf_mm
    # Tiap rect membawa kerf-nya sendiri; bin dilebihkan satu kerf supaya potongan
    # terakhir di tiap sumbu tidak ikut dikenai kerf (lihat catatan di docstring).
    bin_l, bin_w = usable_l + kerf, usable_w + kerf

    # Kelompokkan per (material, tebal): satu lembar tidak boleh campur bahan.
    groups: Dict[Tuple[str, int], List[Part]] = {}
    for p in parts:
        groups.setdefault(_group_key(p), []).append(p)

    sheets: List[Sheet] = []
    unplaced: List[Tuple[str, float, float]] = []
    sheet_no = 0

    allow_rot = not cfg.respect_grain

    for (material, thickness), group in sorted(groups.items(), key=lambda kv: -kv[0][1]):
        packer = newPacker(
            mode=PackingMode.Offline,       # semua rect diketahui di depan
            bin_algo=PackingBin.Global,     # padatkan satu lembar sebelum membuka lembar baru
            pack_algo=_ALGOS[cfg.algorithm],
            rotation=allow_rot,
        )

        rid_map: Dict[int, Tuple[Part, int]] = {}
        rid = 0
        total_pieces = 0
        for p in group:
            # Ukuran potong (sudah dikompensasi edging); kerf ditambahkan saat add_rect.
            cl, cw = float(p.cut_length_mm), float(p.cut_width_mm)

            # Part bebas serat yang tidak muat memanjang: tukar orientasinya manual.
            if (not (cl <= usable_l and cw <= usable_w) and not p.grain_locked
                    and cw <= usable_l and cl <= usable_w):
                cl, cw = cw, cl

            for piece in range(p.qty):
                fits = (cl <= usable_l and cw <= usable_w) or (
                    allow_rot and cw <= usable_l and cl <= usable_w
                )
                if not fits:
                    unplaced.append((p.part_name, p.cut_length_mm, p.cut_width_mm))
                    continue
                packer.add_rect(cl + kerf, cw + kerf, rid)
                rid_map[rid] = (p, piece + 1)
                rid += 1
                total_pieces += 1

        if total_pieces == 0:
            continue

        # Sediakan lembar sebanyak jumlah keping (batas atas yang pasti cukup).
        for _ in range(total_pieces):
            packer.add_bin(bin_l, bin_w)
        packer.pack()

        by_bin: Dict[int, List[Placement]] = {}
        for bin_idx, x, y, w, h, r_id in packer.rect_list():
            part, piece_index = rid_map[r_id]
            # Buang kerf lagi supaya yang dilaporkan = ukuran part sesungguhnya.
            real_l, real_w = w - kerf, h - kerf
            # Bandingkan dengan ukuran potong asli: menangkap rotasi oleh rectpack
            # maupun penukaran orientasi manual di atas.
            rotated = abs(real_l - part.cut_length_mm) > 0.51   # toleransi pembulatan
            by_bin.setdefault(bin_idx, []).append(
                Placement(
                    part_name=part.part_name,
                    x_mm=round(x + cfg.trim_mm, 1),
                    y_mm=round(y + cfg.trim_mm, 1),
                    length_mm=round(real_l, 1),
                    width_mm=round(real_w, 1),
                    rotated=rotated,
                    piece_index=piece_index,
                )
            )

        for bin_idx in sorted(by_bin):
            sheet_no += 1
            sheets.append(
                Sheet(
                    index=sheet_no,
                    material=material,
                    thickness_mm=thickness,
                    sheet_length_mm=cfg.sheet_length_mm,
                    sheet_width_mm=cfg.sheet_width_mm,
                    placements=sorted(by_bin[bin_idx], key=lambda p: (p.y_mm, p.x_mm)),
                )
            )

    return NestResult(sheets=sheets, unplaced=unplaced, config=cfg)


# --------------------------------------------------------------------------- #
# Visualisasi: SVG mandiri (tanpa matplotlib) supaya bisa dibuka di browser
# --------------------------------------------------------------------------- #

_PALETTE = [
    "#7ba7d7", "#8fcf9a", "#e8b45f", "#d98c8c", "#b39ddb",
    "#7fc9c4", "#c9c06a", "#e0a3c4", "#9fb2c9", "#a9cf7f",
]


def to_svg(result: NestResult, scale: float = 0.18, gap_px: int = 28) -> str:
    """Render seluruh lembar sebagai satu file SVG (satu lembar per baris)."""
    colors: Dict[str, str] = {}

    def color_for(name: str) -> str:
        if name not in colors:
            colors[name] = _PALETTE[len(colors) % len(_PALETTE)]
        return colors[name]

    sw = result.config.sheet_length_mm * scale
    sh = result.config.sheet_width_mm * scale
    header = 22
    body: List[str] = []

    for i, sheet in enumerate(result.sheets):
        oy = i * (sh + header + gap_px) + header
        body.append(
            f'<text x="0" y="{oy - 6:.1f}" font-family="monospace" font-size="12" fill="#222">'
            f"Sheet {sheet.index} - {sheet.material} {sheet.thickness_mm}mm - "
            f"waste {sheet.waste_pct:.1f}%</text>"
        )
        body.append(
            f'<rect x="0" y="{oy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
            f'fill="#f4f1ea" stroke="#333" stroke-width="1"/>'
        )
        for pl in sheet.placements:
            x = pl.x_mm * scale
            y = oy + pl.y_mm * scale
            w = pl.length_mm * scale
            h = pl.width_mm * scale
            body.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                f'fill="{color_for(pl.part_name)}" fill-opacity="0.75" '
                f'stroke="#1a1a1a" stroke-width="0.6"/>'
            )
            if w > 46 and h > 16:
                body.append(
                    f'<text x="{x + 3:.1f}" y="{y + 12:.1f}" font-family="monospace" '
                    f'font-size="8" fill="#111">{pl.part_name[:22]}</text>'
                )
                body.append(
                    f'<text x="{x + 3:.1f}" y="{y + 21:.1f}" font-family="monospace" '
                    f'font-size="7" fill="#333">'
                    f"{pl.length_mm:.0f}x{pl.width_mm:.0f}{' R' if pl.rotated else ''}</text>"
                )

    total_h = len(result.sheets) * (sh + header + gap_px) + header
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sw + 20:.0f}" '
        f'height="{total_h + 20:.0f}" viewBox="-10 -10 {sw + 20:.0f} {total_h + 20:.0f}">'
        f'<rect x="-10" y="-10" width="{sw + 20:.0f}" height="{total_h + 20:.0f}" fill="#fff"/>'
        + "".join(body)
        + "</svg>"
    )


def _cli() -> None:
    import argparse

    ap = argparse.ArgumentParser(
        description="Optimasi pemotongan 2D dari JSON spesifikasi atau part list."
    )
    ap.add_argument("json_file", help="JSON spesifikasi furnitur, atau part list (--parts)")
    ap.add_argument("--parts", action="store_true",
                    help="input sudah berupa part list hasil bom_engine")
    ap.add_argument("--kerf", type=float, default=3.0, help="tebal pisau mm (default 3)")
    ap.add_argument("--trim", type=float, default=0.0, help="trim tepi lembaran mm")
    ap.add_argument("--algo", choices=sorted(_ALGOS), default="guillotine")
    ap.add_argument("--allow-rotation", action="store_true",
                    help="abaikan arah serat, semua part boleh diputar")
    ap.add_argument("--sheet", default=f"{SHEET_LENGTH_MM}x{SHEET_WIDTH_MM}",
                    help="ukuran lembaran, mis. 2440x1220")
    ap.add_argument("-o", "--out", help="tulis hasil JSON ke file")
    ap.add_argument("--svg", help="tulis visualisasi layout ke file SVG")
    args = ap.parse_args()

    sl, sw = (int(v) for v in args.sheet.lower().split("x"))
    cfg = NestConfig(
        sheet_length_mm=sl,
        sheet_width_mm=sw,
        kerf_mm=args.kerf,
        trim_mm=args.trim,
        algorithm=args.algo,
        respect_grain=not args.allow_rotation,
    )

    with open(args.json_file, encoding="utf-8") as f:
        raw = f.read()

    if args.parts:
        parts = [Part(**d) for d in json.loads(raw)]
    else:
        parts = bom_from_json(raw)

    result = nest_parts(parts, cfg)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"Hasil nesting -> {args.out}")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as f:
            f.write(to_svg(result))
        print(f"Visualisasi -> {args.svg}")

    print(json.dumps(result.summary(), indent=2))


if __name__ == "__main__":
    _cli()
