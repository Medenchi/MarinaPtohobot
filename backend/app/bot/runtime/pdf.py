"""PDF подборки — версия 'для печати'.

Одна страница = один образ. Фото занимает ~80% страницы. Заголовок снизу.
Никаких чипсов-тегов, никаких подзаголовков секций — чистый лукбук.

Обложка: имя клиента, дата, бренд Марины.
"""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4
MARGIN = 36

INK = HexColor("#1a1a1a")
MUTED = HexColor("#7a7a7a")
PAPER = HexColor("#faf7f2")
ACCENT = HexColor("#8b6f47")

_FONT_REGISTERED = False
_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"


def _ensure_fonts() -> None:
    global _FONT_REGISTERED, _FONT, _FONT_BOLD
    if _FONT_REGISTERED:
        return
    for reg, bold in [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ]:
        try:
            pdfmetrics.registerFont(TTFont("Body", reg))
            pdfmetrics.registerFont(TTFont("BodyBold", bold))
            _FONT = "Body"
            _FONT_BOLD = "BodyBold"
            _FONT_REGISTERED = True
            return
        except Exception:
            continue
    log.warning("DejaVu fonts not found; Cyrillic may render as boxes.")
    _FONT_REGISTERED = True


def _download_image(storage_path: str) -> bytes | None:
    if not storage_path:
        return None
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    url = f"{base}/storage/v1/object/public/{bucket}/{storage_path}"
    try:
        with httpx.Client(timeout=20.0) as cli:
            resp = cli.get(url)
            if resp.status_code != 200:
                return None
            return resp.content
    except Exception:
        return None


def _draw_cover(c: canvas.Canvas, *, client: str, when: str, total: int) -> None:
    """Минималистичная обложка: бренд сверху, заголовок по центру, имя+дата."""
    # Бежевая плашка сверху
    c.setFillColor(PAPER)
    c.rect(0, PAGE_H * 0.6, PAGE_W, PAGE_H * 0.4, stroke=0, fill=1)

    # Бренд
    c.setFillColor(ACCENT)
    c.setFont(_FONT_BOLD, 10)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.88, "MARINA ZAUGOLNIKOVA")
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.7)
    c.line(PAGE_W / 2 - 40, PAGE_H * 0.87, PAGE_W / 2 + 40, PAGE_H * 0.87)

    # Главный заголовок
    c.setFillColor(INK)
    c.setFont(_FONT_BOLD, 44)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.74, "ПОДБОРКА")

    c.setFillColor(MUTED)
    c.setFont(_FONT, 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.69, "ОБРАЗОВ")

    # Метаданные
    c.setFillColor(INK)
    c.setFont(_FONT, 11)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.45, f"для @{client.lstrip('@') or 'клиента'}")
    c.setFillColor(MUTED)
    c.setFont(_FONT, 10)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.45 - 18, when)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.45 - 34, f"{total} образ(а/ов)")

    # Контакты
    c.setFont(_FONT, 8)
    c.drawCentredString(PAGE_W / 2, MARGIN + 24, "+7 (985) 196-30-84  ·  mzaugolnikova@gmail.com")


def _draw_section_divider(c: canvas.Canvas, title: str) -> None:
    """Отдельная страница-разделитель для секции (Понравилось / Может подойти)."""
    c.setFillColor(PAPER)
    c.rect(0, PAGE_H * 0.4, PAGE_W, PAGE_H * 0.2, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(_FONT_BOLD, 36)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 6, title.upper())
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.7)
    c.line(PAGE_W / 2 - 60, PAGE_H / 2 - 26, PAGE_W / 2 + 60, PAGE_H / 2 - 26)
    c.setFillColor(MUTED)
    c.setFont(_FONT, 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 44, "MARINA ZAUGOLNIKOVA")


def _draw_full_page_outfit(
    c: canvas.Canvas, outfit: dict[str, Any], *, index: int, total: int
) -> None:
    """Одна страница = один образ. Фото на 80% страницы, заголовок снизу."""
    images = outfit.get("outfit_images") or []
    main_img = images[0] if images else None

    # Фото-область (большая, без рамок)
    img_top_margin = 50  # сверху небольшой отступ для номера
    img_bottom_margin = 80  # снизу место для названия
    img_area_h = PAGE_H - img_top_margin - img_bottom_margin
    img_area_w = PAGE_W - 2 * MARGIN

    if main_img:
        blob = _download_image(main_img.get("storage_path") or "")
        if blob:
            try:
                ir = ImageReader(io.BytesIO(blob))
                iw, ih = ir.getSize()
                ratio = min(img_area_w / iw, img_area_h / ih)
                draw_w, draw_h = iw * ratio, ih * ratio
                offset_x = (PAGE_W - draw_w) / 2
                offset_y = img_bottom_margin + (img_area_h - draw_h) / 2
                c.drawImage(
                    ir,
                    offset_x,
                    offset_y,
                    width=draw_w,
                    height=draw_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception as exc:
                log.warning("image draw failed: %s", exc)
                _draw_no_image(c, img_bottom_margin, img_area_h)
        else:
            _draw_no_image(c, img_bottom_margin, img_area_h)
    else:
        _draw_no_image(c, img_bottom_margin, img_area_h)

    # Номер сверху справа
    c.setFillColor(MUTED)
    c.setFont(_FONT, 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 22, f"{index} / {total}")

    # Название образа крупно снизу
    title = str(outfit.get("title") or "Образ")
    c.setFillColor(INK)
    c.setFont(_FONT_BOLD, 18)
    c.drawCentredString(PAGE_W / 2, img_bottom_margin - 30, title[:80])

    # Краткое описание тонким шрифтом (если короткое)
    desc = (outfit.get("description") or "").strip()
    if desc and len(desc) < 100:
        c.setFillColor(MUTED)
        c.setFont(_FONT, 9)
        c.drawCentredString(PAGE_W / 2, img_bottom_margin - 48, desc[:100])

    # Бренд внизу
    c.setFillColor(ACCENT)
    c.setFont(_FONT_BOLD, 7)
    c.drawCentredString(PAGE_W / 2, MARGIN - 8, "MARINA ZAUGOLNIKOVA")


def _draw_no_image(c: canvas.Canvas, y_base: float, h: float) -> None:
    c.setFillColor(PAPER)
    c.rect(MARGIN, y_base, PAGE_W - 2 * MARGIN, h, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont(_FONT, 12)
    c.drawCentredString(PAGE_W / 2, y_base + h / 2, "нет фото")


def generate_pdf(
    *,
    outfits: list[dict[str, Any]],
    client_username: str,
    bot_username: str,
) -> bytes:
    """Один образ на страницу, без секций."""
    _ensure_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"{settings.brand_name} — Подборка образов")
    when = datetime.now(tz=UTC).strftime("%d.%m.%Y")

    _draw_cover(c, client=client_username, when=when, total=len(outfits))
    c.showPage()

    for i, outfit in enumerate(outfits, 1):
        if not isinstance(outfit, dict):
            continue
        _draw_full_page_outfit(c, outfit, index=i, total=len(outfits))
        c.showPage()

    c.save()
    return buf.getvalue()


def generate_pdf_sections(
    *,
    sections: list[dict[str, Any]],
    client_username: str,
    bot_username: str,
) -> bytes:
    """Многосекционный PDF: каждая секция получает разделитель и страницы по 1 образу."""
    _ensure_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"{settings.brand_name} — Подборка образов")
    when = datetime.now(tz=UTC).strftime("%d.%m.%Y")
    total = sum(len(s.get("outfits") or []) for s in sections)

    _draw_cover(c, client=client_username, when=when, total=total)
    c.showPage()

    for section in sections:
        title = str(section.get("title") or "Раздел")
        outfits = section.get("outfits") or []
        if not outfits:
            continue
        _draw_section_divider(c, title)
        c.showPage()
        for i, outfit in enumerate(outfits, 1):
            if not isinstance(outfit, dict):
                continue
            _draw_full_page_outfit(c, outfit, index=i, total=len(outfits))
            c.showPage()

    c.save()
    return buf.getvalue()


def upload_pdf(blob: bytes, *, telegram_id: int) -> str:
    sb = get_supabase()
    ts = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    path = f"{telegram_id}/{ts}.pdf"
    sb.storage.from_(settings.storage_bucket_pdfs).upload(
        path=path,
        file=blob,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    base = settings.supabase_url.rstrip("/")
    return f"{base}/storage/v1/object/public/{settings.storage_bucket_pdfs}/{path}"
