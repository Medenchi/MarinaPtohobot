"""Generate A4 portrait PDFs of the matched outfits with a bottom watermark.

Layout per page: 2 outfits stacked vertically (image + caption + chips).
Watermark at the very bottom: ``@client · @bot · DD.MM.YYYY``.

We use ReportLab — no system dependencies, easy to vendor in the Docker image.
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
MARGIN = 36  # 0.5"
GUTTER = 14
CARD_TITLE_PT = 14
CARD_BODY_PT = 9
WATERMARK_PT = 8

# Lazy register a unicode font for Cyrillic. Falls back to Helvetica if not found.
_FONT_REGISTERED = False
_FONT_NAME = "Helvetica"
_FONT_NAME_BOLD = "Helvetica-Bold"


def _ensure_fonts() -> None:
    global _FONT_REGISTERED, _FONT_NAME, _FONT_NAME_BOLD
    if _FONT_REGISTERED:
        return
    # Try common DejaVu locations (present in Debian-based Docker images and
    # most Linux dev machines). Cyrillic glyphs are essential.
    candidates = [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for reg, bold in candidates:
        try:
            pdfmetrics.registerFont(TTFont("Body", reg))
            pdfmetrics.registerFont(TTFont("BodyBold", bold))
            _FONT_NAME = "Body"
            _FONT_NAME_BOLD = "BodyBold"
            _FONT_REGISTERED = True
            return
        except Exception:
            continue
    log.warning("DejaVu fonts not found; Cyrillic in PDF may render as boxes.")
    _FONT_REGISTERED = True


def _watermark(c: canvas.Canvas, *, client: str, bot: str, when: str) -> None:
    label = f"@{client.lstrip('@')}  ·  @{bot.lstrip('@')}  ·  {when}"
    c.setFont(_FONT_NAME, WATERMARK_PT)
    c.setFillColor(HexColor("#9a9a9a"))
    c.drawCentredString(PAGE_W / 2, MARGIN / 2, label)
    # Brand line above (very subtle)
    brand = f"{settings.brand_name}  ·  {settings.public_web_url.replace('https://', '')}"
    c.setFillColor(HexColor("#cccccc"))
    c.drawCentredString(PAGE_W / 2, MARGIN / 2 + 10, brand)
    c.setFillColor(HexColor("#000000"))


def _download_image(storage_path: str) -> bytes | None:
    """Fetch outfit image bytes from Supabase Storage (public bucket)."""
    if not storage_path:
        return None
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    url = f"{base}/storage/v1/object/public/{bucket}/{storage_path}"
    try:
        with httpx.Client(timeout=20.0) as cli:
            resp = cli.get(url)
            if resp.status_code != 200:
                log.warning("Image fetch failed (%s): %s", resp.status_code, url)
                return None
            return resp.content
    except Exception as exc:
        log.warning("Image fetch error: %s", exc)
        return None


def _draw_outfit_card(
    c: canvas.Canvas,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    outfit: dict[str, Any],
) -> None:
    """Draw a single outfit card occupying the given rect."""
    # Image area (top 70% of the card)
    img_h = h * 0.66
    img_y = y + h - img_h
    images = outfit.get("outfit_images") or []
    main_img = images[0] if images else None
    drew_image = False
    if main_img:
        blob = _download_image(main_img.get("storage_path") or "")
        if blob:
            try:
                ir = ImageReader(io.BytesIO(blob))
                iw, ih = ir.getSize()
                ratio = min(w / iw, img_h / ih)
                draw_w, draw_h = iw * ratio, ih * ratio
                offset_x = x + (w - draw_w) / 2
                offset_y = img_y + (img_h - draw_h) / 2
                c.drawImage(
                    ir,
                    offset_x,
                    offset_y,
                    width=draw_w,
                    height=draw_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                drew_image = True
            except Exception as exc:
                log.warning("Image draw failed: %s", exc)

    if not drew_image:
        c.setFillColor(HexColor("#f1f1f1"))
        c.rect(x, img_y, w, img_h, stroke=0, fill=1)
        c.setFillColor(HexColor("#888"))
        c.setFont(_FONT_NAME, 10)
        c.drawCentredString(x + w / 2, img_y + img_h / 2, "нет фото")
        c.setFillColor(HexColor("#000"))

    # Title under image
    title = str(outfit.get("title") or "Образ")
    c.setFont(_FONT_NAME_BOLD, CARD_TITLE_PT)
    c.setFillColor(HexColor("#111"))
    c.drawString(x, img_y - 8 - CARD_TITLE_PT, title[:80])

    # Description / metadata
    desc = outfit.get("description") or ""
    if desc:
        c.setFont(_FONT_NAME, CARD_BODY_PT)
        c.setFillColor(HexColor("#444"))
        _draw_wrapped(c, desc, x, img_y - 8 - CARD_TITLE_PT - 6, w, max_lines=3)


def _draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    w: float,
    *,
    max_lines: int,
    line_h: float = 11,
) -> None:
    """Naive word-wrap. Enough for short captions."""
    words = text.split()
    line: list[str] = []
    lines_drawn = 0
    cur_y = y
    for word in words:
        candidate = (" ".join([*line, word])).strip()
        if c.stringWidth(candidate, _FONT_NAME, CARD_BODY_PT) <= w:
            line.append(word)
        else:
            if line:
                c.drawString(x, cur_y - line_h, " ".join(line))
                cur_y -= line_h
                lines_drawn += 1
                if lines_drawn >= max_lines:
                    return
            line = [word]
    if line and lines_drawn < max_lines:
        c.drawString(x, cur_y - line_h, " ".join(line))


def generate_pdf(
    *,
    outfits: list[dict[str, Any]],
    client_username: str,
    bot_username: str,
) -> bytes:
    """Render a multi-page PDF and return raw bytes."""
    _ensure_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"{settings.brand_name} — Подбор образов")
    when = datetime.now(tz=UTC).strftime("%d.%m.%Y")

    # Cover page
    c.setFont(_FONT_NAME_BOLD, 28)
    c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN * 3, settings.brand_name)
    c.setFont(_FONT_NAME, 14)
    c.setFillColor(HexColor("#555"))
    c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN * 3 - 28, "Подбор образов")
    c.setFillColor(HexColor("#111"))
    c.setFont(_FONT_NAME, 11)
    c.drawCentredString(
        PAGE_W / 2,
        PAGE_H - MARGIN * 3 - 60,
        f"Для @{client_username.lstrip('@') or 'клиента'}",
    )
    c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN * 3 - 80, when)
    _watermark(c, client=client_username, bot=bot_username, when=when)
    c.showPage()

    # Outfit pages — 2 cards per page (stacked vertically)
    cards_per_page = 2
    card_w = PAGE_W - 2 * MARGIN
    available_h = PAGE_H - 2 * MARGIN - GUTTER * (cards_per_page - 1)
    card_h = available_h / cards_per_page

    for i, outfit in enumerate(outfits):
        slot = i % cards_per_page
        if slot == 0 and i != 0:
            _watermark(c, client=client_username, bot=bot_username, when=when)
            c.showPage()
        y_top = PAGE_H - MARGIN - slot * (card_h + GUTTER)
        _draw_outfit_card(
            c,
            x=MARGIN,
            y=y_top - card_h,
            w=card_w,
            h=card_h,
            outfit=outfit,
        )

    _watermark(c, client=client_username, bot=bot_username, when=when)
    c.showPage()
    c.save()
    return buf.getvalue()


def upload_pdf(blob: bytes, *, telegram_id: int) -> str:
    """Upload generated PDF to Supabase and return its public URL."""
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
