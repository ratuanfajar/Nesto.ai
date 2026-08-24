import os
import json
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageEnhance, ImageFilter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from tqdm import tqdm

# 1. SKEMA DATA JSON BAKU (CONTRACT OUTPUT)
class OverallDimensions(BaseModel):
    length_cm: float
    width_cm: float
    height_cm: float

class DropPocket(BaseModel):
    length_cm: float
    depth_cm: float
    height_cm: float

class PlinthBase(BaseModel):
    has_plinth: bool
    height_cm: float
    offset_cm: float

class StructuralPartitions(BaseModel):
    shelves_count: int
    doors_count: int
    drawers_count: int

class MaterialHints(BaseModel):
    board_material: str            # bahan inti (mis. Blockboard, Multiplek, MDF)
    board_thickness_mm: int        # tebal papan inti
    finish: str                    # lapisan permukaan (HPL, Duco, Melamine, ...)
    finish_color: Optional[str] = None
    finish_code: Optional[str] = None  # kode HPL (mis. "TH 232 AC")

# Pool material realistis (konvensi bengkel interior Indonesia)
_BOARDS = ["Blockboard", "Multiplek", "MDF", "Particle Board", "Plywood"]
_FINISHES = ["HPL", "Duco", "Melamine", "Veneer", "PU Coating"]
_COLORS = ["Coklat", "Abu", "Putih", "Hitam", "Grey", "Maple", "Walnut"]

def sample_material_hints() -> "MaterialHints":
    finish = random.choice(_FINISHES)
    color = random.choice(_COLORS) if random.random() < 0.8 else None
    # kode hanya relevan untuk HPL
    code = None
    if finish == "HPL" and random.random() < 0.7:
        code = f"TH {random.randint(100, 999)} {random.choice(['AC', 'AA', 'SD', 'MR'])}"
    return MaterialHints(
        board_material=random.choice(_BOARDS),
        board_thickness_mm=random.choice([12, 15, 18, 25]),
        finish=finish,
        finish_color=color,
        finish_code=code,
    )

class FurnitureBOMData(BaseModel):
    furniture_type: str
    overall_dimensions: OverallDimensions
    plinth: PlinthBase
    partitions: StructuralPartitions
    material: MaterialHints = Field(default_factory=sample_material_hints)
    drop_pocket: Optional[DropPocket] = None
    has_curve: bool = False
    default_thickness_mm: int = 18
    default_edging_mm: float = 1.0


# 2. GENERATOR PARAMETER REALISTIS (DOMAIN CONSTRAINTS)
def _plinth(has: bool, height: float, offset: float) -> PlinthBase:
    """Tanpa plinth -> tinggi & setback dinolkan.

    Kalau plinth tidak ada, kedua angka itu tak punya jejak visual apa pun di
    gambar; membiarkannya acak berarti melatih model menebak label yang mustahil
    dibaca. 0.0 adalah nilai yang benar secara konstruksi (lih. bom_engine).
    """
    if not has:
        return PlinthBase(has_plinth=False, height_cm=0.0, offset_cm=0.0)
    return PlinthBase(has_plinth=True, height_cm=height, offset_cm=offset)



def sample_furniture_parameters() -> FurnitureBOMData:
    ftype = random.choices(
        ["reception_desk", "base_cabinet", "bookshelf", "nightstand"],
        weights=[0.3, 0.35, 0.25, 0.1]
    )[0]

    if ftype == "reception_desk":
        length = round(random.uniform(120.0, 220.0), 1)
        width = round(random.uniform(50.0, 80.0), 1)
        height = round(random.uniform(85.0, 110.0), 1)
        has_plinth = True
        plinth_h = round(random.uniform(5.0, 10.0), 1)
        plinth_off = round(random.uniform(3.0, 6.0), 1)
        has_drop = random.random() < 0.7
        drop = None
        if has_drop:
            drop = DropPocket(
                length_cm=round(length * random.uniform(0.4, 0.6), 1),
                depth_cm=round(width * random.uniform(0.4, 0.6), 1),
                height_cm=round(random.uniform(15.0, 25.0), 1)
            )
        return FurnitureBOMData(
            furniture_type=ftype,
            overall_dimensions=OverallDimensions(length_cm=length, width_cm=width, height_cm=height),
            plinth=PlinthBase(has_plinth=has_plinth, height_cm=plinth_h, offset_cm=plinth_off),
            partitions=StructuralPartitions(shelves_count=random.randint(0, 2), doors_count=0, drawers_count=0),
            drop_pocket=drop,
            has_curve=random.choice([True, False])
        )

    elif ftype == "base_cabinet":
        length = round(random.uniform(60.0, 180.0), 1)
        width = round(random.uniform(50.0, 65.0), 1)
        height = round(random.uniform(75.0, 90.0), 1)
        doors = random.randint(1, 3)
        return FurnitureBOMData(
            furniture_type=ftype,
            overall_dimensions=OverallDimensions(length_cm=length, width_cm=width, height_cm=height),
            plinth=PlinthBase(has_plinth=True,
                              height_cm=round(random.uniform(6.0, 12.0), 1),
                              offset_cm=round(random.uniform(2.0, 6.0), 1)),
            partitions=StructuralPartitions(shelves_count=random.randint(1, 3), doors_count=doors, drawers_count=random.randint(0, 2)),
            has_curve=False
        )

    elif ftype == "bookshelf":
        length = round(random.uniform(80.0, 160.0), 1)
        width = round(random.uniform(30.0, 45.0), 1)
        height = round(random.uniform(150.0, 210.0), 1)
        return FurnitureBOMData(
            furniture_type=ftype,
            overall_dimensions=OverallDimensions(length_cm=length, width_cm=width, height_cm=height),
            plinth=PlinthBase(has_plinth=True,
                              height_cm=round(random.uniform(5.0, 10.0), 1),
                              offset_cm=round(random.uniform(1.5, 4.0), 1)),
            partitions=StructuralPartitions(shelves_count=random.randint(3, 6), doors_count=0, drawers_count=0),
            has_curve=False
        )

    else:  # nightstand
        length = round(random.uniform(40.0, 60.0), 1)
        width = round(random.uniform(35.0, 45.0), 1)
        height = round(random.uniform(45.0, 60.0), 1)
        return FurnitureBOMData(
            furniture_type=ftype,
            overall_dimensions=OverallDimensions(length_cm=length, width_cm=width, height_cm=height),
            plinth=_plinth(random.choice([True, False]),
                           round(random.uniform(3.0, 8.0), 1),
                           round(random.uniform(1.5, 4.0), 1)),
            partitions=StructuralPartitions(shelves_count=0, doors_count=0, drawers_count=random.randint(1, 3)),
            has_curve=False
        )


# 3. RENDERING ENGINE ISOMETRIK CAD (MATPLOTLIB)
ISO_ANGLE = np.radians(30)
_COS, _SIN = np.cos(ISO_ANGLE), np.sin(ISO_ANGLE)

# Format angka pada GAMBAR, diacak titik/koma agar model robust. JSON ground truth
# tetap memakai titik.
_STYLE = {"comma": False}

# Koordinat teks header (axes fraction) — dipakai sama di kedua layout.
HEADER_X_L = 0.02     # judul (rata kiri)
HEADER_X_R = 0.98     # catatan material (rata kanan)
HEADER_TOP = 0.975    # baris atas header
HEADER_SUB = 0.925    # baris kedua (mis. NOTE radius)

def fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s.replace('.', ',') if _STYLE["comma"] else s

def _material_note(data) -> str:
    """Blok catatan material ala title-block gambar kerja (2 baris)."""
    m = data.material
    l1 = f"MATERIAL: {m.board_material.upper()} {m.board_thickness_mm}mm"
    finish = f"FINISH: {m.finish.upper()}"
    if m.finish_color:
        finish += f" {m.finish_color.upper()}"
    if m.finish_code:
        finish += f" ({m.finish_code})"
    return l1 + "\n" + finish

def _draw_material_note(ax, data):
    ax.text(HEADER_X_R, HEADER_TOP, _material_note(data), transform=ax.transAxes,
            fontsize=7.5, color='#64748b', ha='right', va='top', linespacing=1.4,
            family='monospace')

def _draw_header_title(ax, data):
    ax.text(HEADER_X_L, HEADER_TOP,
            f"MODEL: {data.furniture_type.upper().replace('_', ' ')}",
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            color='#334155', ha='left', va='top')
    if data.has_curve:
        ax.text(HEADER_X_L, HEADER_SUB, "NOTE: RADIUS CORNER (R8.0)",
                transform=ax.transAxes, fontsize=8, color='#64748b',
                ha='left', va='top')

def project_iso(x: float, y: float, z: float):
    # Proyeksi isometrik: 30 derajat
    iso_x = (x - y) * _COS
    iso_y = (x + y) * _SIN + z
    return iso_x, iso_y

# --- Helper gambar pada bidang muka depan (y konstan) ---
def _face_line(ax, u1, v1, u2, v2, y=0.0, **kw):
    """Garis pada bidang muka: sumbu-u sejajar L, sumbu-v sejajar H."""
    p1, p2 = project_iso(u1, y, v1), project_iso(u2, y, v2)
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], **kw)

def _face_rect(ax, u0, v0, u1, v1, y=0.0, **kw):
    pts = [(u0, v0), (u1, v0), (u1, v1), (u0, v1), (u0, v0)]
    xs, ys = zip(*[project_iso(u, y, v) for u, v in pts])
    ax.plot(xs, ys, **kw)

def draw_cad_dimension(ax, a3, b3, text, label_side=(0, 0), text_rot=0, witness_from=None):
    """Garis dimensi CAD: panah <-> + garis bantu (witness) + label ber-offset.
    a3/b3 = titik ujung dimensi dalam koordinat 3D (x,y,z)."""
    p1, p2 = project_iso(*a3), project_iso(*b3)
    # Garis bantu (extension lines) dari objek ke garis dimensi
    if witness_from is not None:
        w1, w2 = witness_from
        for src, dst in ((project_iso(*w1), p1), (project_iso(*w2), p2)):
            ax.plot([src[0], dst[0]], [src[1], dst[1]],
                    color="#94a3b8", lw=0.7, ls=(0, (4, 3)))
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="<->", color="#1f2937", lw=1.2,
                                shrinkA=0, shrinkB=0))
    mid_x = (p1[0] + p2[0]) / 2 + label_side[0]
    mid_y = (p1[1] + p2[1]) / 2 + label_side[1]
    ax.text(mid_x, mid_y, text, fontsize=9, fontweight='bold',
            color="#111827", ha='center', va='center', rotation=text_rot,
            rotation_mode='anchor',
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))

def draw_iso_detail_dim(ax, a3, b3, text, label_side=(0, 0), text_rot=0, witness_from=None):
    """Dimensi detail (plinth / drop pocket): sama seperti draw_cad_dimension
    tapi panah & huruf lebih kecil supaya tak menutupi dimensi utama."""
    p1, p2 = project_iso(*a3), project_iso(*b3)
    if witness_from is not None:
        w1, w2 = witness_from
        for src, dst in ((project_iso(*w1), p1), (project_iso(*w2), p2)):
            ax.plot([src[0], dst[0]], [src[1], dst[1]],
                    color="#94a3b8", lw=0.6, ls=(0, (3, 2)))
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="<->", color="#1f2937", lw=0.9,
                                shrinkA=0, shrinkB=0, mutation_scale=9))
    ax.text((p1[0] + p2[0]) / 2 + label_side[0], (p1[1] + p2[1]) / 2 + label_side[1],
            text, fontsize=7.5, fontweight='bold', color="#111827",
            ha='center', va='center', rotation=text_rot, rotation_mode='anchor',
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def _draw_partitions(ax, data, L, W, H):
    """Gambar partisi (laci/pintu/rak) pada bidang muka depan agar tiap
    field JSON dapat dihitung secara visual dari gambar."""
    n_draw = data.partitions.drawers_count
    n_door = data.partitions.doors_count
    n_shelf = data.partitions.shelves_count

    base = data.plinth.height_cm if data.plinth.has_plinth else 0.0
    top = H
    mx = L * 0.045                      # margin horizontal (tebal rangka)
    u0, u1 = mx, L - mx
    region_bot = base + H * 0.015
    region_top = top - H * 0.015

    # Zona laci di bagian atas bila laci hidup bersama pintu/rak
    if n_draw > 0 and (n_door > 0 or n_shelf > 0):
        draw_bot = region_top - (region_top - region_bot) * 0.32
    else:
        draw_bot = region_bot            # laci mengisi penuh (mis. nightstand)
    door_top = draw_bot if n_draw > 0 else region_top

    grey = '#475569'
    # Hidden-line (konvensi CAD), selalu tampak agar shelves_count terhitung dari gambar.
    if n_shelf > 0:
        for i in range(1, n_shelf + 1):
            v = region_bot + (door_top - region_bot) * i / (n_shelf + 1)
            _face_line(ax, u0, v, u1, v, color=grey, lw=0.9, ls=(0, (5, 3)))

    # Pintu: kolom-kolom vertikal berhandel
    if n_door > 0:
        for i in range(n_door):
            du0 = u0 + (u1 - u0) * i / n_door
            du1 = u0 + (u1 - u0) * (i + 1) / n_door
            _face_rect(ax, du0 + L * 0.008, region_bot, du1 - L * 0.008, door_top,
                       color=grey, lw=1.1)
            # knob dekat sisi tengah pintu
            knob_u = du1 - (du1 - du0) * 0.12
            knob = project_iso(knob_u, 0, (region_bot + door_top) / 2)
            ax.plot(knob[0], knob[1], 'o', ms=3.2, color='#1e293b')

    # Laci: baris-baris horizontal berhandel
    if n_draw > 0:
        for i in range(n_draw):
            dv0 = draw_bot + (region_top - draw_bot) * i / n_draw
            dv1 = draw_bot + (region_top - draw_bot) * (i + 1) / n_draw
            _face_rect(ax, u0, dv0 + H * 0.006, u1, dv1 - H * 0.006,
                       color=grey, lw=1.1)
            # handel: garis horizontal pendek di tengah muka laci
            hv = (dv0 + dv1) / 2
            hc = L * 0.11
            _face_line(ax, L / 2 - hc, hv, L / 2 + hc, hv, color='#1e293b', lw=1.6)

def render_furniture_sketch(data: FurnitureBOMData, save_path: str):
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_facecolor('#fafafa')
    fig.patch.set_facecolor('#fafafa')

    L = data.overall_dimensions.length_cm
    W = data.overall_dimensions.width_cm
    H = data.overall_dimensions.height_cm

    # 8 Titik Sudut Balok Utama
    c = {
        '000': project_iso(0, 0, 0),
        'L00': project_iso(L, 0, 0),
        'LW0': project_iso(L, W, 0),
        '0W0': project_iso(0, W, 0),
        '00H': project_iso(0, 0, H),
        'L0H': project_iso(L, 0, H),
        'LWH': project_iso(L, W, H),
        '0WH': project_iso(0, W, H),
    }

    # Garis Rangka Utama
    edges = [
        ('000', 'L00'), ('L00', 'LW0'), ('LW0', '0W0'), ('0W0', '000'),
        ('00H', 'L0H'), ('L0H', 'LWH'), ('LWH', '0WH'), ('0WH', '00H'),
        ('000', '00H'), ('L00', 'L0H'), ('LW0', 'LWH'), ('0W0', '0WH')
    ]
    for e in edges:
        p1, p2 = c[e[0]], c[e[1]]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#1e293b', lw=1.8)

    # Titik ekstra (label detail) yg wajib ikut diperhitungkan saat set_xlim
    extra_pts = []

    # Partisi struktural (laci / pintu / rak) pada muka depan
    _draw_partitions(ax, data, L, W, H)

    # Rendering Plinth Kaki (kickboard set-back pada muka depan)
    if data.plinth.has_plinth:
        pH = data.plinth.height_cm
        p_off = data.plinth.offset_cm
        # garis atas plinth + dua sisi vertikal pendek -> terbaca sbg recess
        _face_line(ax, p_off, pH, L - p_off, pH, color='#64748b', lw=1.3)
        _face_line(ax, p_off, 0, p_off, pH, color='#64748b', lw=1.1)
        _face_line(ax, L - p_off, 0, L - p_off, pH, color='#64748b', lw=1.1)
        _m = max(L, W, H)
        # dimensi tinggi plinth (vertikal, di kiri muka depan)
        dx = -_m * 0.06
        draw_iso_detail_dim(
            ax, (dx, 0, 0), (dx, 0, pH), f"{fmt(pH)}",
            label_side=(-_m * 0.05, 0), text_rot=90,
            witness_from=((0, 0, 0), (0, 0, pH)))
        # dimensi setback plinth (horizontal, di depan-bawah kiri)
        dy = -_m * 0.09
        draw_iso_detail_dim(
            ax, (0, dy, 0), (p_off, dy, 0), f"{fmt(p_off)}",
            label_side=(0, -max(L, W, H) * 0.035), text_rot=30,
            witness_from=((0, 0, 0), (p_off, 0, 0)))

    # Rendering Drop Pocket (cekungan pada permukaan atas z=H)
    if data.drop_pocket:
        dp = data.drop_pocket
        ou0, ou1 = L * 0.2, L * 0.2 + dp.length_cm      # sepanjang L
        oy0, oy1 = (W - dp.depth_cm) / 2, (W + dp.depth_cm) / 2  # sepanjang W
        zt, zb = H, H - dp.height_cm
        top_rect = [(ou0, oy0), (ou1, oy0), (ou1, oy1), (ou0, oy1), (ou0, oy0)]
        # bibir atas cekungan
        xs, ys = zip(*[project_iso(x, y, zt) for x, y in top_rect])
        ax.plot(xs, ys, color='#0f172a', lw=1.4)
        # dasar cekungan + dinding vertikal di 4 sudut
        xs, ys = zip(*[project_iso(x, y, zb) for x, y in top_rect])
        ax.plot(xs, ys, color='#334155', lw=1.0, ls=(0, (4, 3)))
        for x, y in [(ou0, oy0), (ou1, oy0), (ou1, oy1), (ou0, oy1)]:
            a, b = project_iso(x, y, zt), project_iso(x, y, zb)
            ax.plot([a[0], b[0]], [a[1], b[1]], color='#334155', lw=1.0)
        # dimensi pocket pada bidang atas: panjang (arah L) & kedalaman (arah W)
        gapd = max(L, W, H) * 0.05
        draw_iso_detail_dim(
            ax, (ou0, oy1 + gapd * 1.6, zt), (ou1, oy1 + gapd * 1.6, zt), f"{fmt(dp.length_cm)}",
            label_side=(0, gapd * 0.55), text_rot=30,
            witness_from=((ou0, oy1, zt), (ou1, oy1, zt)))
        draw_iso_detail_dim(
            ax, (ou1 + gapd, oy0, zt), (ou1 + gapd, oy1, zt), f"{fmt(dp.depth_cm)}",
            label_side=(gapd * 0.55, 0), text_rot=-30,
            witness_from=((ou1, oy0, zt), (ou1, oy1, zt)))
        # kedalaman turun pocket: leader note (dinding vertikal sulit didimensi di iso)
        _lp = project_iso(ou0, oy1, (zt + zb) / 2)
        ax.annotate(f"POCKET DALAM {fmt(dp.height_cm)} cm",
                    xy=(_lp[0], _lp[1]),
                    xytext=(_lp[0] - max(L, W, H) * 0.30, _lp[1] + max(L, W, H) * 0.16),
                    fontsize=7.5, fontweight='bold', color="#111827", ha='right',
                    va='center',
                    arrowprops=dict(arrowstyle="->", color="#334155", lw=0.9))
        extra_pts.append((_lp[0] - max(L, W, H) * 0.42, _lp[1] + max(L, W, H) * 0.16))
        extra_pts.append(project_iso(ou1 + gapd * 2.2, oy1, zt))

    # Rendering Garis Dimensi CAD (di luar siluet, offset konsisten)
    off = max(L, W, H) * 0.15
    off_w = off + W          # offset luar PENUH utk dimensi kedalaman (W)
    # 1. Panjang (L): di depan-bawah (y = -off)
    draw_cad_dimension(
        ax, (0, -off, 0), (L, -off, 0), f"{fmt(L)} cm",
        label_side=(0, -off * 0.5), text_rot=30,
        witness_from=((0, 0, 0), (L, 0, 0)))
    # 2. Kedalaman (W): di kanan, digeser keluar sejauh off_w -> bersih dari body
    draw_cad_dimension(
        ax, (L + off_w, 0, 0), (L + off_w, W, 0), f"{fmt(W)} cm",
        label_side=(off * 0.6, 0), text_rot=-30,
        witness_from=((L, 0, 0), (L, W, 0)))
    # 3. Tinggi (H): di kiri-belakang (x = -off, y = W) -> jelas di luar box
    draw_cad_dimension(
        ax, (-off, W, 0), (-off, W, H), f"{fmt(H)} cm",
        label_side=(-off * 0.5, 0), text_rot=90,
        witness_from=((0, W, 0), (0, W, H)))

    ax.set_aspect('equal')
    ax.axis('off')

    # Batas gambar + headroom judul (cegah judul menabrak rangka)
    dim_pts = [
        project_iso(-off, W, 0), project_iso(0, -off, 0),
        project_iso(L + off_w, 0, 0), project_iso(L + off_w, W, 0),
        project_iso(0, 0, H + off),
    ]
    xs_all = [p[0] for p in c.values()] + [p[0] for p in dim_pts] + [p[0] for p in extra_pts]
    ys_all = [p[1] for p in c.values()] + [p[1] for p in dim_pts] + [p[1] for p in extra_pts]
    xmin, xmax = min(xs_all), max(xs_all)
    ymin, ymax = min(ys_all), max(ys_all)
    xr, yr = xmax - xmin, ymax - ymin
    pad = 0.08 * max(xr, yr)
    head = 0.13 * yr                       # ruang khusus judul di atas
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - pad, ymax + pad + head)

    # Judul + catatan material di zona headroom (koordinat header seragam)
    _draw_header_title(ax, data)
    _draw_material_note(ax, data)

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


# 3b. RENDERING MULTI-VIEW 2D ORTOGRAFIK (TAMPAK DEPAN / SAMPING)
FRAME, GREY, DIMC, WITC = '#1e293b', '#475569', '#1f2937', '#94a3b8'

def _panel_rect(ax, ox, oy, w, h, **kw):
    ax.plot([ox, ox + w, ox + w, ox, ox], [oy, oy, oy + h, oy + h, oy], **kw)

def _dim_line(ax, p1, p2, text, rot=0, label_off=(0, 0)):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="<->", color=DIMC, lw=1.1, shrinkA=0, shrinkB=0))
    mx = (p1[0] + p2[0]) / 2 + label_off[0]
    my = (p1[1] + p2[1]) / 2 + label_off[1]
    ax.text(mx, my, text, fontsize=8.5, fontweight='bold', color="#111827",
            ha='center', va='center', rotation=rot, rotation_mode='anchor',
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))

def _dim_line_small(ax, p1, p2, text, rot=0, label_off=(0, 0)):
    """Dimensi detail multiview (plinth / pocket): panah & huruf lebih kecil."""
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="<->", color=DIMC, lw=0.9,
                                shrinkA=0, shrinkB=0, mutation_scale=9))
    ax.text((p1[0] + p2[0]) / 2 + label_off[0], (p1[1] + p2[1]) / 2 + label_off[1],
            text, fontsize=7.5, fontweight='bold', color="#111827",
            ha='center', va='center', rotation=rot, rotation_mode='anchor',
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def _witness(ax, a, b):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=WITC, lw=0.7, ls=(0, (4, 3)))

def _draw_partitions_flat(ax, data, ox, oy, w, h, base):
    """Partisi pada bidang datar (tampak depan): sumbu-x = panjang, sumbu-y = tinggi."""
    n_draw = data.partitions.drawers_count
    n_door = data.partitions.doors_count
    n_shelf = data.partitions.shelves_count
    mx = w * 0.045
    x0, x1 = ox + mx, ox + w - mx
    reg_bot = oy + base + h * 0.015
    reg_top = oy + h - h * 0.015
    if n_draw > 0 and (n_door > 0 or n_shelf > 0):
        draw_bot = reg_top - (reg_top - reg_bot) * 0.30
    else:
        draw_bot = reg_bot
    door_top = draw_bot if n_draw > 0 else reg_top

    # Rak internal: hidden-line putus-putus (opsi 1)
    if n_shelf > 0:
        for i in range(1, n_shelf + 1):
            yy = reg_bot + (door_top - reg_bot) * i / (n_shelf + 1)
            ax.plot([x0, x1], [yy, yy], color=GREY, lw=0.9, ls=(0, (5, 3)))
    # Pintu: kolom vertikal + knob
    if n_door > 0:
        for i in range(n_door):
            dx0 = x0 + (x1 - x0) * i / n_door
            dx1 = x0 + (x1 - x0) * (i + 1) / n_door
            _panel_rect(ax, dx0 + w * 0.008, reg_bot,
                        (dx1 - dx0) - w * 0.016, door_top - reg_bot, color=GREY, lw=1.1)
            ax.plot(dx1 - (dx1 - dx0) * 0.14, (reg_bot + door_top) / 2, 'o', ms=3.2, color=FRAME)
    # Laci: baris horizontal + handel
    if n_draw > 0:
        for i in range(n_draw):
            dy0 = draw_bot + (reg_top - draw_bot) * i / n_draw
            dy1 = draw_bot + (reg_top - draw_bot) * (i + 1) / n_draw
            _panel_rect(ax, x0, dy0 + h * 0.006, x1 - x0, (dy1 - dy0) - h * 0.012, color=GREY, lw=1.1)
            hc = w * 0.11
            ax.plot([ox + w / 2 - hc, ox + w / 2 + hc], [(dy0 + dy1) / 2] * 2, color=FRAME, lw=1.6)

def render_multiview_2d(data: FurnitureBOMData, save_path: str):
    """Gambar kerja 2D: TAMPAK DEPAN (L x H) + TAMPAK SAMPING (W x H),
    plus TAMPAK ATAS bila ada drop pocket."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    ax.set_facecolor('#fafafa')
    fig.patch.set_facecolor('#fafafa')

    L = data.overall_dimensions.length_cm
    W = data.overall_dimensions.width_cm
    H = data.overall_dimensions.height_cm
    base = data.plinth.height_cm if data.plinth.has_plinth else 0.0

    gap = max(L, W) * 0.55            # jarak antar tampak
    fx, fy = 0.0, 0.0                 # origin tampak depan
    sx, sy = L + gap, 0.0            # origin tampak samping

    # ---------- TAMPAK DEPAN ----------
    _panel_rect(ax, fx, fy, L, H, color=FRAME, lw=1.8)
    if data.plinth.has_plinth:
        p_off = data.plinth.offset_cm
        # toe-kick digambar sbg recess: garis atas + dua sisi vertikal ber-setback
        ax.plot([fx + p_off, fx + L - p_off], [fy + base, fy + base], color=GREY, lw=1.2)
        ax.plot([fx + p_off, fx + p_off], [fy, fy + base], color=GREY, lw=1.0)
        ax.plot([fx + L - p_off, fx + L - p_off], [fy, fy + base], color=GREY, lw=1.0)
        # dimensi tinggi plinth: di kiri tampak depan, di luar dimensi H
        pxd = fx - L * 0.155
        _witness(ax, (fx, fy), (pxd, fy))
        _witness(ax, (fx + p_off, fy + base), (pxd, fy + base))
        _dim_line_small(ax, (pxd, fy), (pxd, fy + base), f"{fmt(base)}",
                        rot=90, label_off=(-L * 0.035, 0))
        # dimensi setback plinth: di bawah dimensi panjang
        pyd = fy - H * 0.175
        _witness(ax, (fx, fy), (fx, pyd)); _witness(ax, (fx + p_off, fy), (fx + p_off, pyd))
        _dim_line_small(ax, (fx, pyd), (fx + p_off, pyd), f"{fmt(p_off)}",
                        label_off=(0, -H * 0.032))
    _draw_partitions_flat(ax, data, fx, fy, L, H, base)
    # dimensi L (bawah) & H (kiri)
    dband = H * 0.11
    _witness(ax, (fx, fy), (fx, fy - dband)); _witness(ax, (fx + L, fy), (fx + L, fy - dband))
    _dim_line(ax, (fx, fy - dband * 0.7), (fx + L, fy - dband * 0.7), f"{fmt(L)} cm",
              label_off=(0, -H * 0.045))
    dbandx = L * 0.10
    _witness(ax, (fx, fy), (fx - dbandx, fy)); _witness(ax, (fx, fy + H), (fx - dbandx, fy + H))
    _dim_line(ax, (fx - dbandx * 0.7, fy), (fx - dbandx * 0.7, fy + H), f"{fmt(H)} cm",
              rot=90, label_off=(-L * 0.04, 0))
    # Tinggi tiap kompartemen; dibatasi <=3 rak agar label tidak tumpang tindih.
    if data.partitions.doors_count == 0 and 1 <= data.partitions.shelves_count <= 3:
        ns = data.partitions.shelves_count
        ys = [fy + base] + [fy + base + (H - base) * i / (ns + 1) for i in range(1, ns + 1)] + [fy + H]
        xr = fx + L + L * 0.06
        for a, b in zip(ys[:-1], ys[1:]):
            _dim_line(ax, (xr, a), (xr, b), f"{fmt(b - a)}", rot=90)

    # ---------- TAMPAK SAMPING ----------
    if data.drop_pocket:
        _dp = data.drop_pocket
        _px0, _px1 = sx + (W - _dp.depth_cm) / 2, sx + (W + _dp.depth_cm) / 2
        _pyb = sy + H - _dp.height_cm
        # siluet samping dgn mulut cekungan terbuka di sisi atas
        ax.plot([sx, sx, sx + W, sx + W], [sy + H, sy, sy, sy + H], color=FRAME, lw=1.8)
        ax.plot([sx, _px0, _px0, _px1, _px1, sx + W],
                [sy + H, sy + H, _pyb, _pyb, sy + H, sy + H], color=FRAME, lw=1.8)
    else:
        _panel_rect(ax, sx, sy, W, H, color=FRAME, lw=1.8)
    if data.plinth.has_plinth:
        ax.plot([sx, sx + W], [sy + base, sy + base], color=GREY, lw=1.2)
    # rak muncul sbg garis horizontal pd tampak samping (kedalaman penuh)
    if data.partitions.shelves_count > 0:
        ns = data.partitions.shelves_count
        rb = sy + base + H * 0.015
        rt = sy + H - H * 0.015
        for i in range(1, ns + 1):
            yy = rb + (rt - rb) * i / (ns + 1)
            ax.plot([sx + W * 0.05, sx + W * 0.95], [yy, yy], color=GREY, lw=0.9, ls=(0, (5, 3)))
    if data.plinth.has_plinth:
        po = data.plinth.offset_cm
        ax.plot([sx + po, sx + W], [sy + base, sy + base], color=GREY, lw=1.2)
        ax.plot([sx + po, sx + po], [sy, sy + base], color=GREY, lw=1.0)
    # drop pocket tampak sbg cekungan pd sisi atas -> tinggi & kedalaman terbaca
    if data.drop_pocket:
        dps = data.drop_pocket
        px0, px1, pyb = _px0, _px1, _pyb
        # tinggi pocket: dimensi di kiri tampak samping (zona kosong antar tampak)
        hxd = sx - max(W * 0.30, H * 0.10)
        _witness(ax, (px0, sy + H), (hxd, sy + H)); _witness(ax, (px0, pyb), (hxd, pyb))
        _dim_line_small(ax, (hxd, pyb), (hxd, sy + H), f"{fmt(dps.height_cm)}",
                        rot=90, label_off=(-W * 0.09, 0))
        # kedalaman pocket: dimensi tepat di atas mulut cekungan
        dyd = sy + H + H * 0.05
        _witness(ax, (px0, sy + H), (px0, dyd)); _witness(ax, (px1, sy + H), (px1, dyd))
        _dim_line_small(ax, (px0, dyd), (px1, dyd), f"{fmt(dps.depth_cm)}",
                        label_off=(0, H * 0.035))
    dbw = H * 0.11
    _witness(ax, (sx, sy), (sx, sy - dbw)); _witness(ax, (sx + W, sy), (sx + W, sy - dbw))
    _dim_line(ax, (sx, sy - dbw * 0.7), (sx + W, sy - dbw * 0.7), f"{fmt(W)} cm",
              label_off=(0, -H * 0.045))
    # offset luar utk tinggi tampak samping (kedalaman) — diperbesar agar tak sempit
    dbwx = max(W * 0.22, H * 0.12)
    _witness(ax, (sx + W, sy), (sx + W + dbwx, sy)); _witness(ax, (sx + W, sy + H), (sx + W + dbwx, sy + H))
    _dim_line(ax, (sx + W + dbwx * 0.7, sy), (sx + W + dbwx * 0.7, sy + H), f"{fmt(H)} cm",
              rot=90, label_off=(dbwx * 0.4, 0))

    # ---------- TAMPAK ATAS (hanya bila drop pocket) ----------
    extra_low = 0.0
    if data.drop_pocket:
        dp = data.drop_pocket
        ty0 = fy - H * 0.55 - W        # di bawah tampak depan
        _panel_rect(ax, fx, ty0, L, W, color=FRAME, lw=1.6)
        pu0 = fx + L * 0.2
        pv0 = ty0 + (W - dp.depth_cm) / 2
        _panel_rect(ax, pu0, pv0, dp.length_cm, dp.depth_cm, color=GREY, lw=1.2)
        ax.text(fx + L * 0.5, ty0 + W * 0.5, "DROP\nPOCKET", fontsize=6.5,
                color=GREY, ha='center', va='center')
        _dim_line(ax, (pu0, pv0 - W * 0.12), (pu0 + dp.length_cm, pv0 - W * 0.12),
                  f"{fmt(dp.length_cm)} cm", label_off=(0, -W * 0.05))
        # kedalaman pocket (arah W) pd tampak atas
        dxd = pu0 + dp.length_cm + L * 0.05
        _witness(ax, (pu0 + dp.length_cm, pv0), (dxd, pv0))
        _witness(ax, (pu0 + dp.length_cm, pv0 + dp.depth_cm), (dxd, pv0 + dp.depth_cm))
        _dim_line_small(ax, (dxd, pv0), (dxd, pv0 + dp.depth_cm), f"{fmt(dp.depth_cm)} cm",
                        rot=90, label_off=(L * 0.045, 0))
        ax.text(fx - L * 0.02, ty0 + W * 1.12, "TAMPAK ATAS", fontsize=8,
                fontweight='bold', color='#334155', ha='left')
        extra_low = (fy - ty0)

    # ---------- LABEL TAMPAK & JUDUL ----------
    ax.text(fx, fy + H + H * 0.06, "TAMPAK DEPAN", fontsize=8.5,
            fontweight='bold', color='#334155', ha='left')
    ax.text(sx, sy + H + (H * 0.20 if data.drop_pocket else H * 0.06), "TAMPAK SAMPING",
            fontsize=8.5, fontweight='bold', color='#334155', ha='left')

    ax.set_aspect('equal')
    ax.axis('off')

    xmin = fx - (L * 0.26 if data.plinth.has_plinth else L * 0.18)
    if data.drop_pocket:
        xmin = min(xmin, sx - max(W * 0.30, H * 0.10) - W * 0.18)
    xmax = sx + W + dbwx + max(W * 0.20, H * 0.12)
    ymin = fy - (H * 0.27 if data.plinth.has_plinth else H * 0.18) - extra_low
    ymax = fy + H + (H * 0.10 if data.drop_pocket else 0.0)
    xr, yr = xmax - xmin, ymax - ymin
    pad = 0.05 * max(xr, yr)
    head = 0.15 * yr
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - pad, ymax + pad + head)

    # Judul + catatan material di zona headroom (koordinat header seragam)
    _draw_header_title(ax, data)
    _draw_material_note(ax, data)

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def render_furniture(data: FurnitureBOMData, save_path: str, iso_ratio: float = 0.5) -> str:
    """Dispatcher layout: sebagian isometrik 3D, sebagian multi-view 2D."""
    if random.random() < iso_ratio:
        render_furniture_sketch(data, save_path)
        return "isometric"
    render_multiview_2d(data, save_path)
    return "multiview_2d"


# 4. AUGMENTASI VISUAL (NOISE & TEXTURE)
def apply_realistic_paper_effects(img_path: str):
    img = Image.open(img_path).convert('RGB')

    # 1. Sedikit Jitter Rotasi (-2 sampai +2 derajat)
    angle = random.uniform(-2.0, 2.0)
    img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=(250, 250, 250))

    # 2. Tambah Noise Halus (Kertas Kamera Bengkel)
    np_img = np.array(img).astype(np.float32)
    noise = np.random.normal(0, random.uniform(2, 6), np_img.shape)
    np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(np_img)

    # 3. Kontras & Kecerahan
    img = ImageEnhance.Contrast(img).enhance(random.uniform(0.9, 1.1))
    img = ImageEnhance.Brightness(img).enhance(random.uniform(0.95, 1.05))

    img.save(img_path, quality=92)


# 5. PIPELINE EKSEKUSI & EXPORT JSONL
def generate_full_dataset(total_samples=1500, output_dir="./dataset_output", seed=42):
    random.seed(seed)
    np.random.seed(seed)
    img_dir = os.path.join(output_dir, "images")
    gt_dir = os.path.join(output_dir, "ground_truth")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(gt_dir, exist_ok=True)

    jsonl_records = []
    print(f"Sedang mengenerate {total_samples} sampel data sintetik...")

    for idx in tqdm(range(total_samples)):
        sample_id = f"synth_{idx+1:04d}"
        img_filename = f"{sample_id}.png"
        img_path = os.path.join(img_dir, img_filename)
        gt_path = os.path.join(gt_dir, f"{sample_id}.json")

        # 1. Buat parameter acak
        data = sample_furniture_parameters()

        # 1b. Acak konvensi desimal label gambar (koma/titik) utk robustness
        _STYLE["comma"] = random.random() < 0.5

        # 2. Render gambar (50% isometrik / 50% multi-view 2D) & augmentasi
        layout = render_furniture(data, img_path, iso_ratio=0.5)
        apply_realistic_paper_effects(img_path)

        # 3. Simpan ground-truth JSON
        json_str = data.model_dump_json(indent=2)
        with open(gt_path, 'w') as f:
            f.write(json_str)

        # 4. Format pesan ChatML untuk Qwen2-VL
        # Path relatif POSIX (portabel Linux/Windows) terhadap output_dir
        img_rel = f"images/{img_filename}"
        record = {
            "id": sample_id,
            "layout": layout,
            "decimal_comma": _STYLE["comma"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img_rel},
                        {"type": "text", "text": "Extract all furniture dimensions, partitions, and structural specs from this technical sketch into strict JSON."}
                    ]
                },
                {
                    "role": "assistant",
                    "content": data.model_dump_json()
                }
            ]
        }
        jsonl_records.append(record)

    # 5. Split Train (80%) dan Validation (20%)
    random.shuffle(jsonl_records)
    split_idx = int(len(jsonl_records) * 0.8)
    train_data = jsonl_records[:split_idx]
    val_data = jsonl_records[split_idx:]

    with open(os.path.join(output_dir, "train.jsonl"), 'w') as f:
        for item in train_data:
            f.write(json.dumps(item) + '\n')

    with open(os.path.join(output_dir, "val.jsonl"), 'w') as f:
        for item in val_data:
            f.write(json.dumps(item) + '\n')

    print(f"\nSelesai! Dataset tersimpan di folder: {output_dir}")
    print(f"Total Train: {len(train_data)} | Total Val: {len(val_data)}")

if __name__ == "__main__":
    generate_full_dataset(total_samples=1500, output_dir="./synthetic_furniture_dataset")