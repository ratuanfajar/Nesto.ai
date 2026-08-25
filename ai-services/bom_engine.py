"""Rule-engine BOM: dimensi global -> daftar part lembaran, dalam mm (Tahap 3).

Deterministik, tanpa model. Konvensi: `length_mm` searah serat, `width_mm` tegak
lurus serat, `eb` = [top, right, bottom, left]; `cut_*` = ukuran potong setelah edging.
Rumus sambungan carcass ada di README bagian "Asumsi konstruksi".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Sequence

try:                      # dipakai sebagai modul paket maupun skrip lepas
    from .schema import FurnitureBOMData, parse_model_output
except ImportError:       # pragma: no cover
    from schema import FurnitureBOMData, parse_model_output


@dataclass
class BOMConfig:
    """Aturan bengkel yang bisa diputar tanpa menyentuh logika dekomposisi."""

    back_panel_thickness_mm: int = 4      # 0 = tanpa panel belakang
    shelf_setback_mm: int = 20            # ambalan dimundurkan dari muka
    door_gap_mm: float = 3.0              # celah antar pintu & ke tepi carcass
    drawer_front_height_mm: float = 150.0
    drawer_slide_clearance_mm: float = 13.0   # sisi kiri/kanan box laci untuk rel
    drawer_box_height_reduction_mm: float = 30.0
    drawer_depth_reduction_mm: float = 50.0
    drawer_bottom_thickness_mm: int = 9
    edging_on_hidden_edges: bool = False  # True = semua tepi di-edging

    # Harus sama dengan ukuran lembaran di NestConfig, kalau tidak part jadi unplaced.
    max_panel_length_mm: int = 2440
    max_panel_width_mm: int = 1220
    door_min_height_mm: float = 120.0     # jatah minimum area pintu saat ada laci


@dataclass
class Part:
    part_name: str
    length_mm: int
    width_mm: int
    thickness_mm: int
    qty: int
    eb: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    material: str = ""
    grain_locked: bool = True             # False = boleh diputar 90 derajat saat nesting
    notes: str = ""
    cut_length_mm: int = 0
    cut_width_mm: int = 0

    def area_mm2(self) -> int:
        return self.length_mm * self.width_mm * self.qty

    def to_dict(self) -> dict:
        return asdict(self)


def _mm(cm: float) -> float:
    return cm * 10.0


def _finish_part(
    name: str,
    length: float,
    width: float,
    thickness: float,
    qty: int,
    eb: Sequence[int],
    cfg: BOMConfig,
    edging_mm: float,
    material: str,
    grain_locked: bool = True,
    notes: str = "",
) -> Optional[Part]:
    """Bulatkan ke mm dan terapkan kompensasi edging. None kalau part tidak masuk akal."""
    length, width = round(length), round(width)
    if qty <= 0 or length <= 0 or width <= 0:
        return None

    eb = [1, 1, 1, 1] if cfg.edging_on_hidden_edges else [int(bool(v)) for v in eb]
    cut_l = length - edging_mm * (eb[1] + eb[3])
    cut_w = width - edging_mm * (eb[0] + eb[2])

    return Part(
        part_name=name,
        length_mm=int(length),
        width_mm=int(width),
        thickness_mm=int(round(thickness)),
        qty=int(qty),
        eb=list(eb),
        material=material,
        grain_locked=grain_locked,
        notes=notes,
        cut_length_mm=int(round(cut_l)),
        cut_width_mm=int(round(cut_w)),
    )


def _panel_fits(length: float, width: float, cfg: BOMConfig, swappable: bool) -> bool:
    ok = length <= cfg.max_panel_length_mm and width <= cfg.max_panel_width_mm
    if swappable:
        ok = ok or (width <= cfg.max_panel_length_mm and length <= cfg.max_panel_width_mm)
    return ok


def _split_panel(
    length: float, width: float, cfg: BOMConfig, swappable: bool = True, max_pieces: int = 8
) -> List[tuple]:
    """Pecah panel lebih besar dari satu lembar jadi n keping sambungan -> [(p, l, qty)].

    Tanpa ini panel besar (mis. 1500x1900) tidak muat di lembaran mana pun dan
    diam-diam hilang dari nesting, membuat kebutuhan triplek kurang dihitung.
    """
    if _panel_fits(length, width, cfg, swappable):
        return [(length, width, 1)]

    for n in range(2, max_pieces + 1):
        if length >= width:
            seg = length / n
            if _panel_fits(seg, width, cfg, swappable):
                return [(seg, width, n)]
        else:
            seg = width / n
            if _panel_fits(length, seg, cfg, swappable):
                return [(length, seg, n)]

    raise ValueError(
        f"panel {length:.0f} x {width:.0f} mm tidak bisa dipecah menjadi <= {max_pieces} "
        f"keping yang muat di lembaran {cfg.max_panel_length_mm} x {cfg.max_panel_width_mm} mm"
    )


def build_bom(data: FurnitureBOMData, cfg: Optional[BOMConfig] = None) -> List[Part]:
    """Terjemahkan spesifikasi global menjadi daftar part lembaran."""
    cfg = cfg or BOMConfig()

    # board_thickness_mm = yang tertulis di sketsa; default_thickness_mm hanya cadangan.
    t = float(data.material.board_thickness_mm or data.default_thickness_mm)
    edging = float(data.default_edging_mm)
    mat = f"{data.material.board_material} {int(t)}mm"

    L = _mm(data.overall_dimensions.length_cm)      # panjang total
    D = _mm(data.overall_dimensions.width_cm)       # kedalaman total
    H = _mm(data.overall_dimensions.height_cm)      # tinggi total

    plinth_h = _mm(data.plinth.height_cm) if data.plinth.has_plinth else 0.0
    plinth_off = _mm(data.plinth.offset_cm) if data.plinth.has_plinth else 0.0

    back_t = cfg.back_panel_thickness_mm
    carcass_h = H - plinth_h                        # tinggi badan di atas plinth
    side_h = carcass_h - 2 * t                      # top & bottom menjepit samping
    shelf_len = L - 2 * t                           # ambalan di antara dua samping
    shelf_depth = D - cfg.shelf_setback_mm - back_t

    parts: List[Optional[Part]] = []
    add = parts.append

    # ---------- Carcass ----------
    add(_finish_part("Side Panel", side_h, D, t, 2, [0, 1, 0, 0], cfg, edging, mat,
                     notes="tepi depan di-edging"))
    add(_finish_part("Top Panel", L, D, t, 1, [0, 0, 1, 0], cfg, edging, mat,
                     notes="tepi depan di-edging"))
    add(_finish_part("Bottom Panel", L, D, t, 1, [0, 0, 1, 0], cfg, edging, mat,
                     notes="tepi depan di-edging"))

    n_shelf = data.partitions.shelves_count
    if n_shelf > 0:
        add(_finish_part("Shelf", shelf_len, shelf_depth, t, n_shelf, [0, 0, 1, 0],
                         cfg, edging, mat, notes="tepi depan di-edging"))

    if back_t > 0:
        segments = _split_panel(L, carcass_h, cfg, swappable=True)
        note = "dipaku/overlay di belakang carcass"
        if len(segments) > 1 or segments[0][2] > 1:
            note += f" (disambung {segments[0][2]} keping)"
        for seg_l, seg_w, seg_qty in segments:
            add(_finish_part("Back Panel", seg_l, seg_w, back_t, seg_qty, [0, 0, 0, 0],
                             cfg, edging, f"Plywood {back_t}mm", grain_locked=False,
                             notes=note))

    # ---------- Plinth ----------
    if data.plinth.has_plinth and plinth_h > 0:
        plinth_depth = D - plinth_off
        add(_finish_part("Plinth Side Rail", plinth_depth, plinth_h, t, 2, [0, 0, 0, 0],
                         cfg, edging, mat, grain_locked=False))
        add(_finish_part("Plinth Front/Back Rail", L - 2 * t, plinth_h, t, 2, [0, 0, 0, 0],
                         cfg, edging, mat, grain_locked=False,
                         notes=f"rail depan mundur {plinth_off:.0f} mm dari muka"))

    # ---------- Pembagian muka: laci di atas, pintu di bawah ----------
    n_door = data.partitions.doors_count
    n_drawer = data.partitions.drawers_count
    gap = cfg.door_gap_mm
    front_h = carcass_h
    drawer_zone = 0.0

    if n_drawer > 0:
        # Jatah pintu disisakan dulu, kalau tidak pintu bertinggi <= 0 dan hilang.
        avail = front_h - (n_drawer + 1) * gap
        if n_door > 0:
            avail -= cfg.door_min_height_mm + gap
        drawer_front_h = min(cfg.drawer_front_height_mm, avail / n_drawer)
        if drawer_front_h <= 0:
            raise ValueError(
                f"tinggi muka {front_h:.0f} mm tidak cukup untuk {n_drawer} laci"
                + (f" + {n_door} pintu" if n_door else "")
            )
        drawer_zone = n_drawer * drawer_front_h + n_drawer * gap
        fw = L - 2 * gap
        add(_finish_part("Drawer Front", fw, drawer_front_h, t, n_drawer, [1, 1, 1, 1],
                         cfg, edging, mat, notes="muka laci, seluruh sisi di-edging"))

        # Box laci: bahan carcass, alas plywood tipis.
        box_w = fw - 2 * cfg.drawer_slide_clearance_mm
        box_h = drawer_front_h - cfg.drawer_box_height_reduction_mm
        box_d = D - cfg.drawer_depth_reduction_mm
        add(_finish_part("Drawer Box Side", box_d, box_h, t, 2 * n_drawer, [1, 0, 0, 0],
                         cfg, edging, mat))
        add(_finish_part("Drawer Box Front/Back", box_w - 2 * t, box_h, t, 2 * n_drawer,
                         [1, 0, 0, 0], cfg, edging, mat))
        add(_finish_part("Drawer Bottom", box_w - 2 * t, box_d - 2 * t,
                         cfg.drawer_bottom_thickness_mm, n_drawer, [0, 0, 0, 0], cfg, edging,
                         f"Plywood {cfg.drawer_bottom_thickness_mm}mm", grain_locked=False))

    if n_door > 0:
        door_h = front_h - drawer_zone - 2 * gap
        door_w = (L - (n_door + 1) * gap) / n_door
        if door_h <= 0 or door_w <= 0:
            raise ValueError(
                f"muka {L:.0f} x {front_h:.0f} mm tidak cukup untuk {n_door} pintu "
                f"(tinggi pintu {door_h:.0f} mm, lebar {door_w:.0f} mm)"
            )
        add(_finish_part("Door", door_w, door_h, t, n_door, [1, 1, 1, 1], cfg, edging, mat,
                         notes="pintu overlay, seluruh sisi di-edging"))

    # ---------- Drop pocket (meja resepsionis) ----------
    if data.drop_pocket is not None:
        dp_l = _mm(data.drop_pocket.length_cm)
        dp_d = _mm(data.drop_pocket.depth_cm)
        dp_h = _mm(data.drop_pocket.height_cm)
        add(_finish_part("Drop Pocket Bottom", dp_l, dp_d, t, 1, [0, 0, 1, 0], cfg, edging, mat))
        add(_finish_part("Drop Pocket Side", dp_d, dp_h, t, 2, [0, 1, 0, 0], cfg, edging, mat))
        add(_finish_part("Drop Pocket Back", dp_l - 2 * t, dp_h, t, 1, [1, 0, 0, 0],
                         cfg, edging, mat))

    return [p for p in parts if p is not None]


def bom_summary(parts: Sequence[Part]) -> dict:
    """Ringkasan: jumlah part, total keping, luas per tebal, panjang edging."""
    by_thickness: dict = {}
    for p in parts:
        by_thickness.setdefault(p.thickness_mm, 0)
        by_thickness[p.thickness_mm] += p.area_mm2()

    edging_mm = sum(
        p.qty * (p.eb[0] + p.eb[2]) * p.length_mm + p.qty * (p.eb[1] + p.eb[3]) * p.width_mm
        for p in parts
    )
    return {
        "part_types": len(parts),
        "total_pieces": sum(p.qty for p in parts),
        "area_m2_by_thickness": {k: round(v / 1e6, 3) for k, v in sorted(by_thickness.items())},
        "edging_length_m": round(edging_mm / 1000.0, 2),
    }


def bom_from_json(raw: str, cfg: Optional[BOMConfig] = None) -> List[Part]:
    """Jalan pintas: teks JSON mentah dari model -> daftar part."""
    return build_bom(parse_model_output(raw), cfg)


def _cli() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Dekomposisi JSON furnitur menjadi part list.")
    ap.add_argument("json_file", help="file JSON spesifikasi (ground truth atau output model)")
    ap.add_argument("-o", "--out", help="tulis part list ke file JSON")
    ap.add_argument("--all-edges", action="store_true", help="edging di semua tepi")
    args = ap.parse_args()

    cfg = BOMConfig(edging_on_hidden_edges=args.all_edges)
    with open(args.json_file, encoding="utf-8") as f:
        parts = bom_from_json(f.read(), cfg)

    payload = [p.to_dict() for p in parts]
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"{len(parts)} jenis part -> {args.out}")
    else:
        print(json.dumps(payload, indent=2))
    print(json.dumps(bom_summary(parts), indent=2))


if __name__ == "__main__":
    _cli()
