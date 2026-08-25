"""Evaluasi & inference pipeline untuk model VL hasil fine-tune (Tahap 2).

    python evaluate.py --adapter outputs/qwen2vl-2b-nesto-lora/adapter --limit 100  # generate + skor (GPU)
    python evaluate.py --predictions outputs/preds.jsonl                            # skor ulang (tanpa GPU)

Metrik lengkap (schema validity, MAE per field, kategorikal, drop pocket,
breakdown, dampak hilir) dijelaskan di README bagian "Metrik Tahap 2".
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:                      # dipakai sebagai modul paket maupun skrip lepas
    from .schema import FurnitureBOMData, ValidationError, parse_model_output
    from .bom_engine import build_bom
    from .nesting_engine import NestConfig, nest_parts
except ImportError:       # pragma: no cover - jalur eksekusi langsung
    from schema import FurnitureBOMData, ValidationError, parse_model_output
    from bom_engine import build_bom
    from nesting_engine import NestConfig, nest_parts


DEFAULT_PROMPT = (
    "Extract all furniture dimensions, partitions, and structural specs "
    "from this technical sketch into strict JSON."
)

# Toleransi "masih bisa dipakai tukang". Field _mm dinilai dalam mm, bukan cm.
TOLERANCES_CM = (0.5, 1.0)
TOLERANCES_MM = (1.0, 2.0)


def _tolerances_for(path: str) -> Tuple[float, ...]:
    return TOLERANCES_MM if path.endswith("_mm") else TOLERANCES_CM


def _unit_of(path: str) -> str:
    return "mm" if path.endswith("_mm") else "cm"

NUMERIC_FIELDS = [
    "overall_dimensions.length_cm",
    "overall_dimensions.width_cm",
    "overall_dimensions.height_cm",
    "plinth.height_cm",
    "plinth.offset_cm",
    "drop_pocket.length_cm",
    "drop_pocket.depth_cm",
    "drop_pocket.height_cm",
    "material.board_thickness_mm",
    "default_thickness_mm",
    "default_edging_mm",
]

COUNT_FIELDS = [
    "partitions.shelves_count",
    "partitions.doors_count",
    "partitions.drawers_count",
]

CATEGORICAL_FIELDS = [
    "furniture_type",
    "plinth.has_plinth",
    "has_curve",
    "material.board_material",
    "material.finish",
    "material.finish_color",
    "material.finish_code",
]


def _get(obj: Any, path: str) -> Any:
    """Ambil nilai lewat dot-path; None kalau salah satu ruas kosong."""
    cur = obj
    for key in path.split("."):
        if cur is None:
            return None
        cur = cur.get(key) if isinstance(cur, dict) else getattr(cur, key, None)
    return cur


def _as_dict(obj: Any) -> dict:
    return obj.model_dump() if isinstance(obj, FurnitureBOMData) else obj


def _classify_validation_error(err: ValidationError) -> List[Tuple[str, str]]:
    """(field_path, jenis_error) untuk setiap pelanggaran skema."""
    out = []
    for e in err.errors():
        loc = ".".join(str(x) for x in e["loc"]) or "<root>"
        out.append((loc, e["type"]))
    return out


@dataclass
class ParseOutcome:
    sample_id: str
    ok: bool
    data: Optional[dict] = None
    error_kind: str = ""          # "json_decode" | "schema" | "empty"
    error_detail: str = ""
    field_errors: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class EvalReport:
    n_total: int = 0
    n_valid: int = 0
    parse_errors: Counter = field(default_factory=Counter)
    field_error_counter: Counter = field(default_factory=Counter)
    numeric: Dict[str, dict] = field(default_factory=dict)
    counts: Dict[str, dict] = field(default_factory=dict)
    categorical: Dict[str, dict] = field(default_factory=dict)
    drop_pocket: Dict[str, float] = field(default_factory=dict)
    by_group: Dict[str, Dict[str, dict]] = field(default_factory=dict)
    downstream: Dict[str, Any] = field(default_factory=dict)
    worst_samples: List[dict] = field(default_factory=list)
    failures: List[dict] = field(default_factory=list)

    @property
    def schema_validity_rate(self) -> float:
        return 100.0 * self.n_valid / self.n_total if self.n_total else 0.0

    @property
    def n_invalid(self) -> int:
        return self.n_total - self.n_valid

    def to_dict(self) -> dict:
        return {
            "n_total": self.n_total,
            "n_valid": self.n_valid,
            "n_invalid": self.n_invalid,
            "schema_validity_rate_pct": round(self.schema_validity_rate, 2),
            "parse_errors": dict(self.parse_errors),
            "field_error_counter": dict(self.field_error_counter),
            "numeric": self.numeric,
            "counts": self.counts,
            "categorical": self.categorical,
            "drop_pocket": self.drop_pocket,
            "by_group": self.by_group,
            "downstream": self.downstream,
            "worst_samples": self.worst_samples,
            "failures": self.failures,
        }


def parse_prediction(sample_id: str, raw: str) -> ParseOutcome:
    """Coba ubah teks mentah model jadi dict tervalidasi; catat jenis errornya."""
    if not raw or not raw.strip():
        return ParseOutcome(sample_id, False, error_kind="empty",
                            error_detail="output kosong")
    try:
        data = parse_model_output(raw)
        return ParseOutcome(sample_id, True, data=data.model_dump())
    except json.JSONDecodeError as e:
        return ParseOutcome(sample_id, False, error_kind="json_decode",
                            error_detail=f"{e.msg} (char {e.pos})")
    except ValidationError as e:
        fe = _classify_validation_error(e)
        return ParseOutcome(sample_id, False, error_kind="schema",
                            error_detail="; ".join(f"{p}: {t}" for p, t in fe[:5]),
                            field_errors=fe)
    except Exception as e:                       # jaring pengaman, jangan sampai loop mati
        return ParseOutcome(sample_id, False, error_kind=type(e).__name__,
                            error_detail=str(e)[:200])


def _numeric_stats(errors: List[float], n_missing: int, n_extra: int,
                   tolerances: Tuple[float, ...] = TOLERANCES_CM,
                   unit: str = "cm") -> dict:
    if not errors:
        return {"n": 0, "n_pred_missing": n_missing, "n_pred_extra": n_extra,
                "mae": None, "medae": None, "rmse": None, "max_err": None,
                "n_exact": 0, "unit": unit, "tolerance": {}}
    abs_err = [abs(e) for e in errors]
    stats = {
        "n": len(errors),
        "n_pred_missing": n_missing,          # ground truth ada, prediksi null
        "n_pred_extra": n_extra,              # ground truth null, prediksi mengarang
        "mae": round(sum(abs_err) / len(abs_err), 4),
        "medae": round(statistics.median(abs_err), 4),
        "rmse": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 4),
        "max_err": round(max(abs_err), 4),
        "bias": round(sum(errors) / len(errors), 4),   # + = model over-estimate
        "n_exact": sum(1 for e in abs_err if e < 1e-9),
        "unit": unit,
        "tolerance": {},
    }
    for tol in tolerances:
        n_bad = sum(1 for e in abs_err if e > tol)
        stats["tolerance"][f"+-{tol}"] = {
            "n_within": len(abs_err) - n_bad,
            "n_error": n_bad,
            "accuracy_pct": round(100.0 * (len(abs_err) - n_bad) / len(abs_err), 2),
        }
    return stats


def _score_numeric(pairs: List[Tuple[dict, dict]]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for path in NUMERIC_FIELDS:
        errors, n_missing, n_extra = [], 0, 0
        for pred, ref in pairs:
            p, r = _get(pred, path), _get(ref, path)
            if r is None and p is None:
                continue
            if r is None:
                n_extra += 1
                continue
            if p is None:
                n_missing += 1
                continue
            errors.append(float(p) - float(r))
        out[path] = _numeric_stats(errors, n_missing, n_extra,
                                   _tolerances_for(path), _unit_of(path))
    return out


def _score_counts(pairs: List[Tuple[dict, dict]]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for path in COUNT_FIELDS:
        diffs = []
        for pred, ref in pairs:
            p, r = _get(pred, path), _get(ref, path)
            if p is None or r is None:
                continue
            diffs.append(int(p) - int(r))
        if not diffs:
            out[path] = {"n": 0}
            continue
        n_wrong = sum(1 for d in diffs if d != 0)
        out[path] = {
            "n": len(diffs),
            "n_correct": len(diffs) - n_wrong,
            "n_error": n_wrong,
            "exact_match_pct": round(100.0 * (len(diffs) - n_wrong) / len(diffs), 2),
            "mae": round(sum(abs(d) for d in diffs) / len(diffs), 4),
            "off_by": dict(sorted(Counter(diffs).items())),   # {selisih: jumlah sampel}
        }
    return out


def _score_categorical(pairs: List[Tuple[dict, dict]]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for path in CATEGORICAL_FIELDS:
        n_ok = 0
        confusion: Counter = Counter()
        n = 0
        for pred, ref in pairs:
            p, r = _get(pred, path), _get(ref, path)
            n += 1
            if p == r:
                n_ok += 1
            else:
                confusion[f"{r!r} -> {p!r}"] += 1
        out[path] = {
            "n": n,
            "n_correct": n_ok,
            "n_error": n - n_ok,
            "accuracy_pct": round(100.0 * n_ok / n, 2) if n else 0.0,
            "top_confusions": dict(confusion.most_common(5)),
        }
    return out


def _score_drop_pocket(pairs: List[Tuple[dict, dict]]) -> Dict[str, float]:
    tp = fp = fn = tn = 0
    for pred, ref in pairs:
        p = _get(pred, "drop_pocket") is not None
        r = _get(ref, "drop_pocket") is not None
        tp += p and r
        fp += p and not r
        fn += (not p) and r
        tn += (not p) and (not r)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "n_error": fp + fn,
        "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
    }


def _bom_signature(data: dict, nest: bool) -> Optional[dict]:
    try:
        parts = build_bom(FurnitureBOMData.model_validate(data))
    except Exception:
        return None
    sig = {
        "n_part_types": len(parts),
        "n_pieces": sum(p.qty for p in parts),
        "area_mm2": sum(p.area_mm2() for p in parts),
        "dims": {p.part_name: (p.cut_length_mm, p.cut_width_mm, p.qty) for p in parts},
    }
    if nest:
        try:
            res = nest_parts(parts, NestConfig())
            sig["n_sheets"] = len(res.sheets)
            sig["n_unplaced"] = len(res.unplaced)
        except Exception:
            sig["n_sheets"] = None
            sig["n_unplaced"] = None
    return sig


def _score_downstream(pairs: List[Tuple[dict, dict]], nest: bool) -> Dict[str, Any]:
    """Seberapa jauh part list hasil prediksi meleset dari part list ground truth."""
    n = 0
    n_same_partlist = 0
    piece_diffs: List[int] = []
    sheet_diffs: List[int] = []
    dim_errors: List[float] = []          # |selisih| ukuran potong per part, mm
    n_part_dim_over_2mm = 0
    n_part_dim_total = 0
    missing_parts: Counter = Counter()
    extra_parts: Counter = Counter()
    n_unplaced_samples = 0            # part prediksi yang tidak muat di lembaran mana pun

    for pred, ref in pairs:
        sp, sr = _bom_signature(pred, nest), _bom_signature(ref, nest)
        if sp is None or sr is None:
            continue
        n += 1
        piece_diffs.append(sp["n_pieces"] - sr["n_pieces"])
        if nest and sp.get("n_sheets") is not None and sr.get("n_sheets") is not None:
            sheet_diffs.append(sp["n_sheets"] - sr["n_sheets"])
            if sp.get("n_unplaced"):
                n_unplaced_samples += 1

        names_p, names_r = set(sp["dims"]), set(sr["dims"])
        for name in names_r - names_p:
            missing_parts[name] += 1
        for name in names_p - names_r:
            extra_parts[name] += 1

        identical = names_p == names_r
        for name in names_p & names_r:
            (lp, wp, qp), (lr, wr, qr) = sp["dims"][name], sr["dims"][name]
            for a, b in ((lp, lr), (wp, wr)):
                err = abs(a - b)
                dim_errors.append(err)
                n_part_dim_total += 1
                if err > 2.0:
                    n_part_dim_over_2mm += 1
                if err > 0.5:
                    identical = False
            if qp != qr:
                identical = False
        n_same_partlist += identical

    if not n:
        return {"n": 0}

    return {
        "n": n,
        "partlist_identical": n_same_partlist,
        "partlist_identical_pct": round(100.0 * n_same_partlist / n, 2),
        "piece_count_mae": round(sum(abs(d) for d in piece_diffs) / n, 3),
        "piece_count_error_samples": sum(1 for d in piece_diffs if d != 0),
        "part_dim_mae_mm": round(sum(dim_errors) / len(dim_errors), 3) if dim_errors else None,
        "part_dim_error_gt_2mm": n_part_dim_over_2mm,
        "part_dim_checked": n_part_dim_total,
        "sheet_count_mae": round(sum(abs(d) for d in sheet_diffs) / len(sheet_diffs), 3)
        if sheet_diffs else None,
        "sheet_count_error_samples": sum(1 for d in sheet_diffs if d != 0) if sheet_diffs else 0,
        "unplaced_samples": n_unplaced_samples,
        "missing_parts_top": dict(missing_parts.most_common(5)),
        "extra_parts_top": dict(extra_parts.most_common(5)),
    }


def _sample_error_score(pred: dict, ref: dict) -> float:
    """Skor gabungan untuk mengurutkan sampel terburuk (cm + penalti kategorikal)."""
    total = 0.0
    for path in NUMERIC_FIELDS:
        p, r = _get(pred, path), _get(ref, path)
        if p is not None and r is not None:
            total += abs(float(p) - float(r))
        elif (p is None) != (r is None):
            total += 5.0
    for path in COUNT_FIELDS:
        p, r = _get(pred, path), _get(ref, path)
        if p is not None and r is not None:
            total += 3.0 * abs(int(p) - int(r))
    for path in CATEGORICAL_FIELDS:
        if _get(pred, path) != _get(ref, path):
            total += 2.0
    return round(total, 3)


def evaluate(
    predictions: Dict[str, str],
    references: Dict[str, dict],
    meta: Optional[Dict[str, dict]] = None,
    downstream: bool = True,
    nest: bool = False,
    worst_k: int = 10,
) -> EvalReport:
    """Bandingkan output mentah model vs ground truth, kembalikan laporan lengkap.

    predictions: {sample_id: teks mentah dari model}
    references : {sample_id: dict ground truth}
    meta       : {sample_id: {"layout": ..., ...}} untuk breakdown (opsional)
    """
    meta = meta or {}
    report = EvalReport()
    pairs: List[Tuple[dict, dict]] = []
    grouped: Dict[str, Dict[str, List[Tuple[dict, dict]]]] = {
        "furniture_type": defaultdict(list),
        "layout": defaultdict(list),
    }
    scored: List[dict] = []

    for sid, raw in predictions.items():
        ref = references.get(sid)
        if ref is None:
            continue
        report.n_total += 1
        outcome = parse_prediction(sid, raw)

        if not outcome.ok:
            report.parse_errors[outcome.error_kind] += 1
            for path, kind in outcome.field_errors:
                report.field_error_counter[f"{path} [{kind}]"] += 1
            report.failures.append({
                "id": sid,
                "error_kind": outcome.error_kind,
                "detail": outcome.error_detail,
                "raw_preview": raw[:200],
            })
            continue

        report.n_valid += 1
        pred = outcome.data
        pairs.append((pred, ref))
        grouped["furniture_type"][str(ref.get("furniture_type"))].append((pred, ref))
        layout = meta.get(sid, {}).get("layout")
        if layout:
            grouped["layout"][str(layout)].append((pred, ref))
        scored.append({"id": sid, "error_score": _sample_error_score(pred, ref)})

    if pairs:
        report.numeric = _score_numeric(pairs)
        report.counts = _score_counts(pairs)
        report.categorical = _score_categorical(pairs)
        report.drop_pocket = _score_drop_pocket(pairs)

        for gname, buckets in grouped.items():
            report.by_group[gname] = {}
            for key, sub in sorted(buckets.items()):
                num = _score_numeric(sub)
                dims = [num[p]["mae"] for p in (
                    "overall_dimensions.length_cm",
                    "overall_dimensions.width_cm",
                    "overall_dimensions.height_cm",
                ) if num[p]["mae"] is not None]
                cnt = _score_counts(sub)
                n_count_err = sum(c.get("n_error", 0) for c in cnt.values())
                report.by_group[gname][key] = {
                    "n": len(sub),
                    "dim_mae_cm": round(sum(dims) / len(dims), 4) if dims else None,
                    "count_errors": n_count_err,
                    "type_accuracy_pct": _score_categorical(sub)["furniture_type"]["accuracy_pct"],
                }

        if downstream:
            report.downstream = _score_downstream(pairs, nest)

    report.worst_samples = sorted(scored, key=lambda s: -s["error_score"])[:worst_k]
    return report


def format_report(report: EvalReport) -> str:
    L: List[str] = []
    add = L.append
    bar = "=" * 78

    add(bar)
    add("LAPORAN EVALUASI MODEL EKSTRAKSI SKETSA -> JSON")
    add(bar)
    add(f"Sampel dievaluasi        : {report.n_total}")
    add(f"Output valid (skema OK)  : {report.n_valid}")
    add(f"Output GAGAL             : {report.n_invalid}")
    add(f"Schema Validity Rate     : {report.schema_validity_rate:.2f} %  "
        f"(target > 98%) -> {'LULUS' if report.schema_validity_rate > 98 else 'BELUM LULUS'}")
    if report.parse_errors:
        add("\nRincian error parsing (jumlah sampel):")
        for kind, n in report.parse_errors.most_common():
            add(f"  - {kind:<14} : {n}")
    if report.field_error_counter:
        add("\nField penyebab pelanggaran skema (top 10):")
        for k, n in report.field_error_counter.most_common(10):
            add(f"  - {k:<48} : {n}")

    if report.numeric:
        add("\n" + bar)
        add("MEAN ABSOLUTE ERROR - FIELD NUMERIK (satuan mengikuti nama field)")
        add(bar)
        head = (f"{'field':<34}{'n':>5}{'MAE':>9}{'MedAE':>9}{'RMSE':>9}"
                f"{'max':>9}{'>tol':>7}{'acc%':>9}{'tol':>8}")
        add(head)
        add("-" * len(head))
        for path, s in report.numeric.items():
            if not s["n"]:
                add(f"{path:<34}{0:>5}{'-':>9}{'-':>9}{'-':>9}{'-':>9}{'-':>7}{'-':>9}{'-':>8}")
                continue
            # Kunci terakhir = toleransi paling longgar untuk satuan field ini.
            tol_key = list(s["tolerance"])[-1]
            tol = s["tolerance"][tol_key]
            add(f"{path:<34}{s['n']:>5}{s['mae']:>9.3f}{s['medae']:>9.3f}"
                f"{s['rmse']:>9.3f}{s['max_err']:>9.3f}{tol['n_error']:>7}"
                f"{tol['accuracy_pct']:>9.2f}{tol_key + s.get('unit', ''):>8}")
        missing = {p: s for p, s in report.numeric.items()
                   if s.get("n_pred_missing") or s.get("n_pred_extra")}
        if missing:
            add("\nField null-mismatch (prediksi null padahal ada, atau sebaliknya):")
            for p, s in missing.items():
                add(f"  - {p:<40} hilang={s['n_pred_missing']}  mengarang={s['n_pred_extra']}")

    if report.counts:
        add("\n" + bar)
        add("FIELD JUMLAH PARTISI (shelves / doors / drawers)")
        add(bar)
        for path, s in report.counts.items():
            if not s.get("n"):
                continue
            add(f"{path:<34} benar={s['n_correct']:<5} salah={s['n_error']:<5} "
                f"exact={s['exact_match_pct']:>6.2f}%  MAE={s['mae']:.3f}")
            add(f"{'':<34} distribusi selisih: {s['off_by']}")

    if report.categorical:
        add("\n" + bar)
        add("FIELD KATEGORIKAL / BOOLEAN")
        add(bar)
        for path, s in report.categorical.items():
            add(f"{path:<34} benar={s['n_correct']:<5} salah={s['n_error']:<5} "
                f"akurasi={s['accuracy_pct']:>6.2f}%")
            for pair, n in s["top_confusions"].items():
                add(f"{'':<36}salah tebak {pair}  x{n}")

    if report.drop_pocket:
        d = report.drop_pocket
        add("\n" + bar)
        add("DETEKSI DROP POCKET (ada / tidak ada)")
        add(bar)
        add(f"TP={d['tp']}  FP={d['fp']}  FN={d['fn']}  TN={d['tn']}  "
            f"total error={d['n_error']}")
        add(f"precision={d['precision']:.3f}  recall={d['recall']:.3f}  f1={d['f1']:.3f}")

    if report.by_group:
        add("\n" + bar)
        add("BREAKDOWN PER KELOMPOK")
        add(bar)
        for gname, buckets in report.by_group.items():
            if not buckets:
                continue
            add(f"[{gname}]")
            add(f"  {'kelompok':<24}{'n':>5}{'dim MAE cm':>12}{'count err':>11}{'type acc%':>11}")
            for key, s in buckets.items():
                mae = f"{s['dim_mae_cm']:.3f}" if s["dim_mae_cm"] is not None else "-"
                add(f"  {key:<24}{s['n']:>5}{mae:>12}{s['count_errors']:>11}"
                    f"{s['type_accuracy_pct']:>11.2f}")

    if report.downstream and report.downstream.get("n"):
        d = report.downstream
        add("\n" + bar)
        add("DAMPAK HILIR (part list BOM hasil prediksi vs ground truth)")
        add(bar)
        add(f"Sampel dibandingkan          : {d['n']}")
        add(f"Part list identik            : {d['partlist_identical']} "
            f"({d['partlist_identical_pct']:.2f} %)")
        add(f"MAE jumlah keping            : {d['piece_count_mae']:.3f} "
            f"(sampel meleset: {d['piece_count_error_samples']})")
        if d.get("part_dim_mae_mm") is not None:
            add(f"MAE ukuran potong part       : {d['part_dim_mae_mm']:.3f} mm "
                f"({d['part_dim_error_gt_2mm']} dari {d['part_dim_checked']} sisi meleset > 2 mm)")
        if d.get("sheet_count_mae") is not None:
            add(f"MAE jumlah lembar triplek    : {d['sheet_count_mae']:.3f} "
                f"(sampel meleset: {d['sheet_count_error_samples']})")
        if d.get("unplaced_samples"):
            add(f"Sampel dengan part tak muat  : {d['unplaced_samples']} "
                f"(dimensi prediksi melebihi kapasitas lembaran)")
        if d["missing_parts_top"]:
            add(f"Part yang hilang di prediksi : {d['missing_parts_top']}")
        if d["extra_parts_top"]:
            add(f"Part berlebih di prediksi    : {d['extra_parts_top']}")

    if report.worst_samples:
        add("\n" + bar)
        add(f"SAMPEL TERBURUK (skor error gabungan, top {len(report.worst_samples)})")
        add(bar)
        for s in report.worst_samples:
            add(f"  {s['id']:<20} skor={s['error_score']}")

    if report.failures:
        add("\n" + bar)
        add(f"CONTOH OUTPUT GAGAL PARSE ({len(report.failures)} total, tampil maks 5)")
        add(bar)
        for f_ in report.failures[:5]:
            add(f"  [{f_['id']}] {f_['error_kind']}: {f_['detail']}")
            add(f"      raw: {f_['raw_preview']!r}")

    add("")
    return "\n".join(L)


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_eval_set(
    val_file: Path, data_dir: Path, limit: Optional[int] = None
) -> Tuple[List[dict], Dict[str, dict], Dict[str, dict]]:
    """Kembalikan (rows, references, meta) dari val.jsonl.

    Ground truth diambil dari jawaban assistant di baris itu sendiri, dengan
    fallback ke `ground_truth/<id>.json`.
    """
    rows = load_jsonl(val_file)
    if limit:
        rows = rows[:limit]

    references: Dict[str, dict] = {}
    meta: Dict[str, dict] = {}
    gt_dir = data_dir / "ground_truth"

    for i, row in enumerate(rows):
        sid = row.get("id") or f"row_{i:04d}"
        row["id"] = sid
        meta[sid] = {k: row.get(k) for k in ("layout", "decimal_comma")}

        answer = row["messages"][-1]["content"]
        if isinstance(answer, list):
            answer = "".join(c.get("text", "") for c in answer)
        try:
            references[sid] = json.loads(answer)
        except json.JSONDecodeError:
            gt_path = gt_dir / f"{sid}.json"
            if gt_path.exists():
                references[sid] = json.loads(gt_path.read_text(encoding="utf-8"))

    n_missing = len(rows) - len(references)
    if n_missing:
        # Tanpa ground truth sampel tidak ikut dihitung; diam-diam mengecilkan denominator.
        print(f"PERINGATAN: {n_missing} dari {len(rows)} sampel tidak punya ground truth "
              f"yang bisa dibaca dan tidak akan ikut diskor.")
    return rows, references, meta


def image_path_of(row: dict, data_dir: Path) -> Optional[Path]:
    for part in row["messages"][0]["content"]:
        if isinstance(part, dict) and part.get("type") == "image":
            return data_dir / part["image"]
    return None


def prompt_of(row: dict) -> str:
    for part in row["messages"][0]["content"]:
        if isinstance(part, dict) and part.get("type") == "text":
            return part["text"]
    return DEFAULT_PROMPT


def load_model(adapter_dir: Path, model_id: str, min_pixels: int, max_pixels: int,
               load_4bit: bool = True):
    """Load base model 4-bit + adapter LoRA. Import berat sengaja ditunda ke sini."""
    import torch
    from transformers import (AutoProcessor, BitsAndBytesConfig,
                              Qwen2VLForConditionalGeneration)
    from peft import PeftModel

    processor = AutoProcessor.from_pretrained(
        model_id, min_pixels=min_pixels, max_pixels=max_pixels
    )
    processor.tokenizer.padding_side = "left"      # generate pakai padding kiri

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    ) if load_4bit else None

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id,
        quantization_config=quant,
        dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    if adapter_dir is not None:
        model = PeftModel.from_pretrained(model, adapter_dir)
    model.eval()
    return model, processor


def generate_predictions(
    rows: List[dict],
    data_dir: Path,
    model,
    processor,
    min_pixels: int,
    max_pixels: int,
    max_new_tokens: int = 320,
    batch_size: int = 1,
    progress: bool = True,
) -> Dict[str, str]:
    """Jalankan model pada tiap gambar; kembalikan {id: teks mentah}."""
    import torch
    from PIL import Image
    from qwen_vl_utils import process_vision_info

    preds: Dict[str, str] = {}
    for start in range(0, len(rows), batch_size):
        chunk = rows[start : start + batch_size]
        batch_msgs, ids = [], []
        for row in chunk:
            img_path = image_path_of(row, data_dir)
            if img_path is None or not img_path.exists():
                preds[row["id"]] = ""
                continue
            batch_msgs.append([{"role": "user", "content": [
                {"type": "image", "image": Image.open(img_path).convert("RGB"),
                 "min_pixels": min_pixels, "max_pixels": max_pixels},
                {"type": "text", "text": prompt_of(row)},
            ]}])
            ids.append(row["id"])

        if not batch_msgs:
            continue

        texts = [processor.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                 for m in batch_msgs]
        images, _ = process_vision_info(batch_msgs)
        inputs = processor(text=texts, images=images, padding=True, return_tensors="pt")
        inputs = inputs.to(model.device)

        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)

        trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, out)]
        decoded = processor.batch_decode(trimmed, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=False)
        for sid, text in zip(ids, decoded):
            preds[sid] = text

        if progress:
            done = min(start + batch_size, len(rows))
            print(f"\r  inference {done}/{len(rows)}", end="", flush=True)

    if progress:
        print()
    return preds


def save_predictions(preds: Dict[str, str], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for sid, raw in preds.items():
            f.write(json.dumps({"id": sid, "raw": raw}, ensure_ascii=False) + "\n")


def load_predictions(path: Path) -> Dict[str, str]:
    return {r["id"]: r.get("raw", "") for r in load_jsonl(path)}


def gold_test(
    image_dir: Path,
    model,
    processor,
    min_pixels: int,
    max_pixels: int,
    gt_dir: Optional[Path] = None,
    max_new_tokens: int = 320,
) -> Tuple[Dict[str, str], Optional[EvalReport]]:
    """Uji model pada foto sketsa nyata. Kalau ada `gt_dir`, sekalian dihitung metriknya."""
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in exts)
    rows = [{
        "id": p.stem,
        "messages": [{"role": "user", "content": [
            {"type": "image", "image": p.name},
            {"type": "text", "text": DEFAULT_PROMPT},
        ]}],
    } for p in images]

    preds = generate_predictions(rows, image_dir, model, processor, min_pixels, max_pixels,
                                 max_new_tokens=max_new_tokens)
    if gt_dir is None:
        return preds, None

    refs = {}
    for sid in preds:
        gt = gt_dir / f"{sid}.json"
        if gt.exists():
            refs[sid] = json.loads(gt.read_text(encoding="utf-8"))
    return preds, (evaluate(preds, refs) if refs else None)


def _cli() -> None:
    base = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Evaluasi model VL ekstraksi sketsa furnitur.")
    ap.add_argument("--data-dir", type=Path,
                    default=base / "dataset_generator" / "synthetic_furniture_dataset_v2")
    ap.add_argument("--val-file", type=Path, default=None)
    ap.add_argument("--adapter", type=Path,
                    default=base / "outputs" / "qwen2vl-2b-nesto-lora" / "adapter")
    ap.add_argument("--model-id", default="Qwen/Qwen2-VL-2B-Instruct")
    ap.add_argument("--no-adapter", action="store_true",
                    help="pakai model base tanpa LoRA (baseline pembanding)")
    ap.add_argument("--predictions", type=Path,
                    help="skor file prediksi yang sudah ada (lewati inference)")
    ap.add_argument("--save-predictions", type=Path, help="simpan hasil inference ke jsonl")
    ap.add_argument("--limit", type=int, default=None, help="batasi jumlah sampel")
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--max-new-tokens", type=int, default=320)
    # Wajib sama dengan MIN/MAX_PIXELS di finetune_qlora.ipynb: resolusi beda = skor
    # lebih buruk tanpa sebab.
    ap.add_argument("--min-pixels", type=int, default=256 * 28 * 28)
    ap.add_argument("--max-pixels", type=int, default=1024 * 28 * 28)
    ap.add_argument("--no-downstream", action="store_true",
                    help="lewati perbandingan part list BOM")
    ap.add_argument("--nest", action="store_true",
                    help="ikut hitung selisih jumlah lembar triplek (lebih lambat)")
    ap.add_argument("--report-json", type=Path, help="tulis laporan lengkap ke JSON")
    args = ap.parse_args()

    val_file = args.val_file or (args.data_dir / "val.jsonl")
    rows, refs, meta = load_eval_set(val_file, args.data_dir, args.limit)
    print(f"Sampel evaluasi: {len(rows)} dari {val_file}")

    if args.predictions:
        preds = load_predictions(args.predictions)
        print(f"Memuat {len(preds)} prediksi dari {args.predictions}")
    else:
        adapter = None if args.no_adapter else args.adapter
        print(f"Memuat model {args.model_id}"
              + (" (base, tanpa adapter)" if adapter is None else f" + adapter {adapter}") + " ...")
        model, processor = load_model(adapter, args.model_id,
                                      args.min_pixels, args.max_pixels)
        preds = generate_predictions(rows, args.data_dir, model, processor,
                                     args.min_pixels, args.max_pixels,
                                     max_new_tokens=args.max_new_tokens,
                                     batch_size=args.batch_size)
        if args.save_predictions:
            save_predictions(preds, args.save_predictions)
            print(f"Prediksi disimpan di {args.save_predictions}")

    report = evaluate(preds, refs, meta, downstream=not args.no_downstream, nest=args.nest)
    print(format_report(report))

    if args.report_json:
        with open(args.report_json, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Laporan JSON -> {args.report_json}")


if __name__ == "__main__":
    _cli()
