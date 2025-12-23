from __future__ import annotations
from pathlib import Path
from textwrap import wrap
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modules.image_analysis import analyze_image_content
from modules.story_generator import generate_storybook
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


UPLOAD_DIR = Path("temp/uploads")
EXPORT_DIR = Path("temp/exports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_REGISTRY: Dict[str, Path] = {}
EXPORT_REGISTRY: Dict[str, Path] = {}

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

class ColorProfile(BaseModel):
    brightness: float
    saturation: float
    dominant_colors: List[str]


class AnalysisResult(BaseModel):
    caption: str
    emotion: str
    color_profile: ColorProfile
    tags: List[str]


class PhotoPayload(BaseModel):
    image_id: str
    analysis: AnalysisResult


class Panel(BaseModel):
    image_id: str
    title: str
    body: str


class StorybookPayload(BaseModel):
    title: str = "AI Story Album"
    panels: List[Panel]
    summary: Optional[str] = None


class StoryRequest(BaseModel):
    photos: List[PhotoPayload]
    style: str = "Heartwarming (溫馨)"
    language: Optional[str] = "en"


class ExportRequest(BaseModel):
    storybook: StorybookPayload
    format: str = "pdf"


app = FastAPI(title="AI Story Album API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


async def _save_upload_file(upload_file: UploadFile) -> Tuple[str, Path]:
    suffix = Path(upload_file.filename or "uploaded.jpg").suffix or ".jpg"
    image_id = uuid4().hex
    file_path = UPLOAD_DIR / f"{image_id}{suffix}"
    contents = await upload_file.read()
    file_path.write_bytes(contents)
    IMAGE_REGISTRY[image_id] = file_path
    return image_id, file_path


@app.post("/api/analyze")
async def analyze_endpoint(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one image.")

    photos = []
    for upload in files:
        image_id, file_path = await _save_upload_file(upload)
        try:
            analysis = analyze_image_content(str(file_path))
        except Exception as exc:  # pragma: no cover - surface error to caller
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        photos.append(
            {"image_id": image_id, "filename": upload.filename, "analysis": analysis}
        )

    return {"photos": photos}


@app.post("/api/story")
async def story_endpoint(payload: StoryRequest):
    if not payload.photos:
        raise HTTPException(status_code=400, detail="No photos provided.")

    storybook = generate_storybook(
        photos=[photo.dict() for photo in payload.photos],
        style=payload.style,
        language=payload.language or "en",
    )
    return storybook


def _get_image_path(image_id: str) -> Path:
    path = IMAGE_REGISTRY.get(image_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Image not found. Please re-upload.")
    return path


def _draw_panel_page(pdf: canvas.Canvas, panel: Panel, width: float, height: float):
    image_path = _get_image_path(panel.image_id)
    try:
        with Image.open(image_path) as img:
            iw, ih = img.size
            ratio = min(width / iw, height / ih)
            draw_w = iw * ratio
            draw_h = ih * ratio
            x = (width - draw_w) / 2
            y = (height - draw_h) / 2
            pdf.drawImage(ImageReader(img), x, y, draw_w, draw_h)
    except Exception as exc:  # pragma: no cover - use solid color fallback
        print(f"無法載入圖片 {image_path}: {exc}")
        pdf.setFillColorRGB(0.85, 0.9, 1)
        pdf.rect(0, 0, width, height, fill=1, stroke=0)

    overlay_h = height * 0.35
    pdf.setFillColorRGB(0.07, 0.16, 0.29)
    pdf.rect(0, 0, width, overlay_h, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("STSong-Light", 24)
    pdf.drawString(48, overlay_h - 48, panel.title)

    pdf.setFont("STSong-Light", 16)
    text_y = overlay_h - 80
    for line in wrap(panel.body, width=35):
        pdf.drawString(48, text_y, line)
        text_y -= 22


def _draw_summary_page(pdf: canvas.Canvas, storybook: StorybookPayload, width: float, height: float):
    pdf.setFillColorRGB(0.93, 0.51, 0.2)
    pdf.rect(0, height - 120, width, 120, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("STSong-Light", 28)
    pdf.drawString(48, height - 70, storybook.title)
    pdf.setFillColorRGB(0.09, 0.18, 0.29)
    pdf.setFont("STSong-Light", 18)
    text_y = height - 160
    for line in wrap(storybook.summary or "", width=45):
        pdf.drawString(48, text_y, line)
        text_y -= 24


def _build_pdf_story(storybook: StorybookPayload) -> Path:
    export_id = uuid4().hex
    file_path = EXPORT_DIR / f"storybook_{export_id}.pdf"
    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4

    for panel in storybook.panels:
        _draw_panel_page(pdf, panel, width, height)
        pdf.showPage()

    if storybook.summary:
        _draw_summary_page(pdf, storybook, width, height)

    pdf.save()
    EXPORT_REGISTRY[export_id] = file_path
    return file_path, export_id


@app.post("/api/export")
async def export_endpoint(payload: ExportRequest):
    if payload.format.lower() != "pdf":
        raise HTTPException(status_code=400, detail="目前僅支援 PDF 匯出。")

    file_path, export_id = _build_pdf_story(payload.storybook)
    return {"export_id": export_id, "download_url": f"/api/exports/{export_id}"}


@app.get("/api/exports/{export_id}")
async def download_export(export_id: str):
    file_path = EXPORT_REGISTRY.get(export_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Export not found.")
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "text/html"
    return FileResponse(path=file_path, filename=file_path.name, media_type=media_type)
