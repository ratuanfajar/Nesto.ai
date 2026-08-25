"""Perekat Tahap 1-4. Semua logika nyata ada di nesto_core; di sini hanya alur."""

from __future__ import annotations

import dataclasses
import time
from typing import List, Optional, Tuple

from nesto_core.bom_engine import BOMConfig, Part, bom_summary, build_bom
from nesto_core.nesting_engine import NestConfig, nest_parts, to_svg
from nesto_core.schema import FurnitureBOMData

from .api_models import BOMOptions, NestOptions


def _apply(cfg, options) -> object:
    """Timpa field dataclass config dengan option yang tidak None."""
    if options is None:
        return cfg
    for key, value in options.model_dump(exclude_none=True).items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def bom_config(options: Optional[BOMOptions] = None) -> BOMConfig:
    return _apply(BOMConfig(), options)


def nest_config(options: Optional[NestOptions] = None) -> NestConfig:
    cfg = _apply(NestConfig(), options)
    return cfg


def check_sheet_consistency(bcfg: BOMConfig, ncfg: NestConfig) -> Optional[str]:
    """Peringatkan kalau batas panel BOM beda dari ukuran lembaran nesting.

    Kalau beda, part yang menurut BOM sudah dipecah benar tetap muncul diam-diam
    sebagai pieces_unplaced > 0.
    """
    if (bcfg.max_panel_length_mm, bcfg.max_panel_width_mm) != (
            ncfg.sheet_length_mm, ncfg.sheet_width_mm):
        return (
            f"Ukuran lembaran nesting ({ncfg.sheet_length_mm}x{ncfg.sheet_width_mm} mm) "
            f"berbeda dari batas pemecahan panel di BOM "
            f"({bcfg.max_panel_length_mm}x{bcfg.max_panel_width_mm} mm). "
            f"Part yang lebih besar dari lembaran akan muncul sebagai unplaced."
        )
    return None


def parts_to_dicts(parts: List[Part]) -> List[dict]:
    return [p.to_dict() for p in parts]


def dicts_to_parts(rows: List[dict]) -> List[Part]:
    """Terima part list yang dikirim balik oleh frontend (mis. setelah diedit)."""
    fields = {f.name for f in dataclasses.fields(Part)}
    return [Part(**{k: v for k, v in row.items() if k in fields}) for row in rows]


def run_bom(spec: FurnitureBOMData, options: Optional[BOMOptions] = None
            ) -> Tuple[List[Part], dict, float]:
    t0 = time.perf_counter()
    parts = build_bom(spec, bom_config(options))
    return parts, bom_summary(parts), time.perf_counter() - t0


def run_nesting(parts: List[Part], options: Optional[NestOptions] = None,
                include_svg: bool = False) -> Tuple[dict, float]:
    t0 = time.perf_counter()
    cfg = nest_config(options)
    result = nest_parts(parts, cfg)
    payload = result.to_dict()
    if include_svg:
        payload["svg"] = to_svg(result)
    return payload, time.perf_counter() - t0
