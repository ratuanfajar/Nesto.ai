"""Bentuk request/response HTTP. Skema spesifikasi dipakai dari nesto_core.schema."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from nesto_core.schema import FurnitureBOMData


class BOMOptions(BaseModel):
    """Aturan bengkel. Semua opsional; yang kosong memakai default BOMConfig."""

    # forbid: option salah nama jadi 422, bukan diabaikan diam-diam lalu dijawab 200.
    model_config = ConfigDict(extra="forbid")

    back_panel_thickness_mm: Optional[int] = Field(None, ge=0, le=25)
    shelf_setback_mm: Optional[int] = Field(None, ge=0, le=200)
    door_gap_mm: Optional[float] = Field(None, ge=0, le=20)
    drawer_front_height_mm: Optional[float] = Field(None, gt=0, le=500)
    drawer_slide_clearance_mm: Optional[float] = Field(None, ge=0, le=50)
    edging_on_hidden_edges: Optional[bool] = None
    # Harus ikut berubah kalau ukuran lembaran diubah - lihat check_sheet_consistency.
    max_panel_length_mm: Optional[int] = Field(None, ge=500, le=5000)
    max_panel_width_mm: Optional[int] = Field(None, ge=500, le=5000)


class NestOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_length_mm: Optional[int] = Field(None, ge=500, le=5000)
    sheet_width_mm: Optional[int] = Field(None, ge=500, le=5000)
    kerf_mm: Optional[float] = Field(None, ge=0, le=20)
    trim_mm: Optional[float] = Field(None, ge=0, le=100)
    algorithm: Optional[str] = Field(None, pattern="^(guillotine|maxrects)$")
    respect_grain: Optional[bool] = None


class PartOut(BaseModel):
    part_name: str
    length_mm: int
    width_mm: int
    thickness_mm: int
    qty: int
    eb: List[int]                # [top, right, bottom, left], 1 = tepi di-edging
    material: str
    grain_locked: bool
    notes: str
    cut_length_mm: int           # ukuran potong = ukuran jadi - edging
    cut_width_mm: int


class PlacementOut(BaseModel):
    part_name: str
    x_mm: float
    y_mm: float
    length_mm: float
    width_mm: float
    rotated: bool
    piece_index: int


class SheetOut(BaseModel):
    index: int
    material: str
    thickness_mm: int
    sheet_length_mm: int
    sheet_width_mm: int
    placements: List[PlacementOut]
    utilization_pct: float
    waste_pct: float


class ExtractResponse(BaseModel):
    spec: FurnitureBOMData
    raw_output: str
    inference_seconds: float


class BOMResponse(BaseModel):
    parts: List[PartOut]
    summary: Dict


class NestResponse(BaseModel):
    summary: Dict
    sheets: List[SheetOut]
    config: Dict
    svg: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Satu panggilan, seluruh pipeline. Ini yang dipakai frontend."""

    spec: FurnitureBOMData
    parts: List[PartOut]
    bom_summary: Dict
    nesting: Optional[NestResponse] = None
    raw_output: str
    timings: Dict[str, float]


class BOMRequest(BaseModel):
    spec: FurnitureBOMData
    options: Optional[BOMOptions] = None


class NestRequest(BaseModel):
    """Boleh kirim `parts` (hasil /v1/bom) atau `spec` (biar BOM dihitung ulang)."""

    parts: Optional[List[PartOut]] = None
    spec: Optional[FurnitureBOMData] = None
    bom_options: Optional[BOMOptions] = None
    options: Optional[NestOptions] = None
    include_svg: bool = False


class ErrorDetail(BaseModel):
    error: str
    message: str
    raw_output: Optional[str] = None
