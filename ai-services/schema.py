"""Skema JSON baku hasil ekstraksi model VL (kontrak output Tahap 1 & 2).

Harus identik dengan skema di dataset_generator/generate_dataset.py; generator
sengaja tidak meng-import modul ini agar bebas dependensi runtime inference.
"""

from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, ValidationError


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
    board_material: str
    board_thickness_mm: int
    finish: str
    finish_color: Optional[str] = None
    finish_code: Optional[str] = None


class FurnitureBOMData(BaseModel):
    furniture_type: str
    overall_dimensions: OverallDimensions
    plinth: PlinthBase
    partitions: StructuralPartitions
    material: MaterialHints
    drop_pocket: Optional[DropPocket] = None
    has_curve: bool = False
    default_thickness_mm: int = 18
    default_edging_mm: float = 1.0


def parse_model_output(raw: str) -> FurnitureBOMData:
    """Validasi teks mentah dari model menjadi FurnitureBOMData.

    Melempar `ValueError` (JSON rusak) atau `pydantic.ValidationError` (skema salah)
    supaya pemanggil bisa membedakan kedua kegagalan itu.
    """
    text = raw.strip()

    # Buang pagar ```json ... ``` kalau model membungkus jawaban.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]

    # Ambil objek JSON terluar kalau ada teks pengantar/penutup.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]

    return FurnitureBOMData.model_validate(json.loads(text))


__all__ = [
    "OverallDimensions",
    "DropPocket",
    "PlinthBase",
    "StructuralPartitions",
    "MaterialHints",
    "FurnitureBOMData",
    "parse_model_output",
    "ValidationError",
]
