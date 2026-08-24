"""HTTP API Nesto: sketsa furnitur -> spesifikasi JSON -> part list -> rencana potong."""

from __future__ import annotations

import io
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from nesto_core.bom_engine import BOMConfig
from nesto_core.nesting_engine import NestConfig
from nesto_core.schema import parse_model_output

from . import pipeline
from .api_models import (AnalyzeResponse, BOMOptions, BOMRequest, BOMResponse,
                         ExtractResponse, NestOptions, NestRequest, NestResponse)
from .config import settings
from .vlm import vlm

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("nesto.api")


def _warmup() -> None:
    """Sekali generate pada gambar kosong supaya kernel CUDA sudah ter-compile."""
    t0 = time.perf_counter()
    vlm.extract(Image.new("RGB", (448, 448), "white"), max_new_tokens=8)
    log.info("Warmup selesai dalam %.1f detik", time.perf_counter() - t0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Di startup, bukan saat request pertama: bobot rusak ketahuan lewat /ready.
    try:
        await run_in_threadpool(vlm.load)
        if settings.warmup:
            await run_in_threadpool(_warmup)
    except Exception as exc:                       # noqa: BLE001 - service tetap hidup
        vlm.load_error = str(exc)
        log.error("Gagal memuat model: %s", exc)
        log.error("Service tetap jalan; /v1/bom dan /v1/nest yang tidak butuh GPU "
                  "masih bisa dipakai. /v1/extract dan /v1/analyze akan balas 503.")
    yield


app = FastAPI(
    title="Nesto AI",
    version="1.0.0",
    description="Sketsa furnitur -> spesifikasi JSON -> part list -> rencana potong triplek.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*", "X-API-Key"],
)


async def require_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail={
            "error": "unauthorized", "message": "Header X-API-Key salah atau tidak ada."})


# Util

async def read_image(upload: UploadFile) -> Image.Image:
    data = await upload.read()
    if not data:
        raise HTTPException(400, {"error": "empty_file", "message": "File gambar kosong."})
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, {
            "error": "file_too_large",
            "message": f"Ukuran file {len(data) / 1e6:.1f} MB melebihi batas "
                       f"{settings.max_upload_bytes / 1e6:.0f} MB."})
    try:
        img = Image.open(io.BytesIO(data))
        # Foto HP menyimpan orientasi di EXIF: tanpa ini sketsa masuk miring 90 derajat.
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, {
            "error": "invalid_image",
            "message": f"Berkas tidak bisa dibaca sebagai gambar: {exc}"}) from exc


def parse_options(raw: Optional[str], model):
    """Option dikirim sebagai string JSON di dalam form-data multipart."""
    if not raw or not raw.strip():
        return None
    try:
        return model.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as exc:
        # Penyebab tersering: Swagger UI mengirim placeholder harfiah "string".
        hint = ""
        if raw.strip() == "string":
            hint = (" Nilai yang terkirim adalah kata 'string' - itu placeholder "
                    "bawaan Swagger UI. Kosongkan kolom option ini (tombol "
                    "'Send empty value') supaya memakai default.")
        raise HTTPException(422, {
            "error": "invalid_options",
            "message": f"Field option bukan JSON yang valid: {exc}.{hint}"}) from exc


def parse_spec_or_422(raw: str):
    """Teks model -> spec tervalidasi, atau 422 yang menyertakan teks aslinya."""
    try:
        return parse_model_output(raw)
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        # 422, bukan 500: service sehat, model yang gagal membaca gambar.
        raise HTTPException(422, {
            "error": "model_output_invalid",
            "message": "Model tidak menghasilkan JSON yang sesuai skema. "
                       "Coba foto ulang sketsa dengan pencahayaan lebih rata "
                       "dan pastikan seluruh garis dimensi terlihat.",
            "raw_output": raw,
            "detail": str(exc)}) from exc


def ensure_spec_usable(spec, from_model: bool = False) -> None:
    """Tolak spesifikasi berdimensi <= 0.

    Tanpa ini, spec 0x0x0 (mis. contoh bawaan Swagger yang dikirim apa adanya)
    dijawab 200 dengan `parts: []` - jawaban yang benar secara logika tapi
    membingungkan: user menyangka enginenya rusak, padahal masukannya yang kosong.
    """
    d = spec.overall_dimensions
    bad = [name for name, value in (("length_cm", d.length_cm),
                                    ("width_cm", d.width_cm),
                                    ("height_cm", d.height_cm)) if value <= 0]
    if not bad:
        return
    if from_model:
        raise HTTPException(422, {
            "error": "model_output_invalid",
            "message": f"Model membaca {', '.join(bad)} sebagai nol - garis dimensi "
                       f"pada sketsa kemungkinan tidak terbaca. Foto ulang dengan "
                       f"pencahayaan lebih rata."})
    raise HTTPException(422, {
        "error": "invalid_spec",
        "message": f"Dimensi {', '.join(bad)} harus lebih besar dari nol. "
                   f"Kalau ini dari halaman /docs, contoh bawaannya memang berisi "
                   f"nol semua - ganti dengan ukuran sungguhan."})


def ensure_model_ready() -> None:
    if not vlm.ready:
        raise HTTPException(503, {
            "error": "model_unavailable",
            "message": "Model belum siap.",
            "detail": vlm.load_error or "sedang dimuat"})


# Kesehatan dan metadata

@app.get("/health", tags=["ops"])
def health():
    """Liveness. Selalu 200 selama proses hidup - jangan dipakai untuk gating traffic."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
def ready():
    """Readiness. 503 selama model belum termuat, supaya load balancer menunggu."""
    if not vlm.ready:
        return JSONResponse(status_code=503, content={
            "status": "loading", "model_dir": str(vlm.model_dir), "error": vlm.load_error})
    # merge_info: "model mana yang disajikan" terjawab tanpa masuk ke container.
    return {"status": "ready", "model_dir": str(vlm.model_dir),
            "load_4bit": settings.load_4bit, "model": vlm.merge_info}


@app.get("/v1/config", tags=["ops"], dependencies=[Depends(require_api_key)])
def config():
    """Default seluruh knob - dipakai frontend untuk merender form tanpa hardcode."""
    payload = {
        "bom_defaults": dict(BOMConfig().__dict__),
        "nest_defaults": dict(NestConfig().__dict__),
        "nest_algorithms": ["guillotine", "maxrects"],
        "max_upload_bytes": settings.max_upload_bytes,
        "max_new_tokens": settings.max_new_tokens,
    }
    if vlm.ready:
        payload["model"] = vlm.resolution_limits()
    return payload


# Pipeline

@app.post("/v1/extract", response_model=ExtractResponse, tags=["pipeline"],
          dependencies=[Depends(require_api_key)])
async def extract(image: UploadFile = File(..., description="PNG/JPG sketsa teknis")):
    """Tahap 1: gambar -> spesifikasi JSON. Butuh GPU."""
    ensure_model_ready()
    img = await read_image(image)
    raw, seconds = await run_in_threadpool(vlm.extract, img)
    return ExtractResponse(spec=parse_spec_or_422(raw), raw_output=raw,
                           inference_seconds=round(seconds, 3))


@app.post("/v1/bom", response_model=BOMResponse, tags=["pipeline"],
          dependencies=[Depends(require_api_key)])
def bom(req: BOMRequest):
    """Tahap 3: spesifikasi -> part list. Murni CPU, tidak butuh model."""
    ensure_spec_usable(req.spec)
    parts, summary, _ = pipeline.run_bom(req.spec, req.options)
    return BOMResponse(parts=pipeline.parts_to_dicts(parts), summary=summary)


@app.post("/v1/nest", response_model=NestResponse, tags=["pipeline"],
          dependencies=[Depends(require_api_key)])
def nest(req: NestRequest):
    """Tahap 4: part list -> penempatan di lembaran. Murni CPU."""
    if req.parts is not None:
        parts = pipeline.dicts_to_parts([p.model_dump() for p in req.parts])
    elif req.spec is not None:
        ensure_spec_usable(req.spec)
        parts, _, _ = pipeline.run_bom(req.spec, req.bom_options)
    else:
        raise HTTPException(422, {"error": "missing_input",
                                  "message": "Kirim salah satu: parts atau spec."})
    payload, _ = pipeline.run_nesting(parts, req.options, req.include_svg)
    return NestResponse(**payload)


@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["pipeline"],
          dependencies=[Depends(require_api_key)])
async def analyze(
    image: UploadFile = File(..., description="PNG/JPG sketsa teknis"),
    include_nesting: bool = Form(True),
    include_svg: bool = Form(False),
    bom_options: Optional[str] = Form(None, description="JSON, lihat /v1/config"),
    nest_options: Optional[str] = Form(None, description="JSON, lihat /v1/config"),
):
    """Seluruh pipeline dalam satu panggilan. Endpoint utama untuk frontend."""
    ensure_model_ready()

    bopt = parse_options(bom_options, BOMOptions)
    nopt = parse_options(nest_options, NestOptions)

    img = await read_image(image)
    t_start = time.perf_counter()

    raw, t_infer = await run_in_threadpool(vlm.extract, img)
    spec = parse_spec_or_422(raw)
    ensure_spec_usable(spec, from_model=True)

    parts, summary, t_bom = await run_in_threadpool(pipeline.run_bom, spec, bopt)

    nesting = None
    t_nest = 0.0
    if include_nesting:
        warning = pipeline.check_sheet_consistency(
            pipeline.bom_config(bopt), pipeline.nest_config(nopt))
        if warning:
            log.warning(warning)
        payload, t_nest = await run_in_threadpool(
            pipeline.run_nesting, parts, nopt, include_svg)
        if warning:
            payload["summary"]["warning"] = warning
        nesting = NestResponse(**payload)

    return AnalyzeResponse(
        spec=spec,
        parts=pipeline.parts_to_dicts(parts),
        bom_summary=summary,
        nesting=nesting,
        raw_output=raw,
        timings={"inference": round(t_infer, 3), "bom": round(t_bom, 4),
                 "nesting": round(t_nest, 4), "total": round(time.perf_counter() - t_start, 3)},
    )


@app.post("/v1/nest/svg", tags=["pipeline"], dependencies=[Depends(require_api_key)],
          response_class=Response)
def nest_svg(req: NestRequest):
    """Sama seperti /v1/nest tapi membalas image/svg+xml langsung.

    Berguna untuk tag img atau tombol cetak, tanpa perlu menyisipkan string SVG
    ke dalam DOM secara manual.
    """
    req.include_svg = True
    result = nest(req)
    return Response(content=result.svg, media_type="image/svg+xml")
