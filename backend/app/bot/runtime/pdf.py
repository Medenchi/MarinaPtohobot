"""Красивая верстка PDF подборок образов.

Изменения от первой версии:
* Обложка с цветной плашкой, большой serif-подобной шапкой бренда,
  крупным именем клиента и датой.
* Каждый блок (Понравилось / Может подойти) открывается своей
  цветной полосой-заголовком на всю ширину.
* Карточка: квадратное превью образа слева, заголовок + чипсы-теги
  (цвета/стили/сезоны/поводы) справа, тонкая разделительная линия
  под карточкой.
* В чипсах — серый pill-фон, читабельный размер.
* Внизу каждой страницы — тонкий watermark.
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
MARGIN = 40

# Палитра
INK = HexColor("#1a1a1a")
MUTED = HexColor("#6b6b6b")
LINE = HexColor("#e6e1d8")
PAPER = HexColor("#faf7f2")
ACCENT = HexColor("#8b6f47")  # тёплый бежевый/коричневый
LIKED = HexColor("#b08968")  # для секции "Понравилось"
MAYBE = HexColor("#a8a8a8")  # для секции "Может подойти"

_FONT_REGISTERED = False
_FONT_NAME = "Helvetica"
_FONT_NAME_BOLD = "Helvetica-Bold"


def _ensure_fonts() -> None:
    global _FONT_REGISTERED, _FONT_NAME, _FONT_NAME_BOLD
    if _FONT_REGISTERED:
        return
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
    """Тонкий футер: слева бренд, по центру — клиент/бот/дата. Домен НЕ выводим."""
    c.setFillColor(LINE)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(MARGIN, MARGIN - 4, PAGE_W - MARGIN, MARGIN - 4)
    c.setFont(_FONT_NAME, 7)
    c.setFillColor(MUTED)
    label = f"@{client.lstrip('@')}  ·  @{bot.lstrip('@')}  ·  {when}"
    c.drawCentredString(PAGE_W / 2, MARGIN - 14, label)
    c.setFillColor(ACCENT)
    c.setFont(_FONT_NAME_BOLD, 7)
    c.drawString(MARGIN, MARGIN - 14, settings.brand_name.upper())
    c.setFillColor(INK)


def _download_image(storage_path: str) -> bytes | None:
    if not storage_path:
        return None
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    url = storage_path if storage_path.startswith("http") else f"{base}/storage/v1/object/public/{bucket}/{storage_path}"
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


def _chips(c: canvas.Canvas, x: float, y: float, w: float, items: list[str]) -> float:
    """Отрисовать ряды чипсов-тэгов, возвращает y нижней границы."""
    if not items:
        return y
    pad_x = 6
    pad_y = 3
    gap = 4
    line_h = 14
    c.setFont(_FONT_NAME, 7.5)
    cur_x = x
    cur_y = y
    for tag in items:
        if not tag:
            continue
        tw = c.stringWidth(tag, _FONT_NAME, 7.5)
        chip_w = tw + pad_x * 2
        if cur_x + chip_w > x + w:
            cur_x = x
            cur_y -= line_h + gap
        c.setFillColor(PAPER)
        c.setStrokeColor(LINE)
        c.roundRect(cur_x, cur_y - pad_y - 1, chip_w, line_h, 6, stroke=1, fill=1)
        c.setFillColor(INK)
        c.drawString(cur_x + pad_x, cur_y + 2, tag)
        cur_x += chip_w + gap
    return cur_y - 4


def _split_tags(value: str) -> list[str]:
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def _draw_card(
    c: canvas.Canvas,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    outfit: dict[str, Any],
) -> None:
    """Карточка: квадратное превью слева, заголовок + чипсы справа."""
    # Тонкая рамка
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=0)

    img_size = h - 16
    img_x = x + 8
    img_y = y + 8
    images = outfit.get("outfit_images") or []
    drew = False
    if images:
        path = images[0].get("storage_path") or ""
        blob = _download_image(path)
        if blob:
            try:
                ir = ImageReader(io.BytesIO(blob))
                iw, ih = ir.getSize()
                ratio = min(img_size / iw, img_size / ih)
                draw_w, draw_h = iw * ratio, ih * ratio
                offset_x = img_x + (img_size - draw_w) / 2
                offset_y = img_y + (img_size - draw_h) / 2
                # Бекграунд под фото
                c.setFillColor(PAPER)
                c.rect(img_x, img_y, img_size, img_size, stroke=0, fill=1)
                c.drawImage(
                    ir,
                    offset_x,
                    offset_y,
                    width=draw_w,
                    height=draw_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                drew = True
            except Exception as exc:
                log.warning("Image draw failed: %s", exc)
    if not drew:
        c.setFillColor(PAPER)
        c.rect(img_x, img_y, img_size, img_size, stroke=0, fill=1)
        c.setFillColor(MUTED)
        c.setFont(_FONT_NAME, 8)
        c.drawCentredString(img_x + img_size / 2, img_y + img_size / 2, "нет фото")
        c.setFillColor(INK)

    # Правая часть: заголовок + теги
    right_x = x + img_size + 24
    right_w = w - img_size - 32
    title = str(outfit.get("title") or "Образ")
    c.setFillColor(INK)
    c.setFont(_FONT_NAME_BOLD, 12)
    c.drawString(right_x, y + h - 22, title[:60])

    desc = (outfit.get("description") or "").strip()
    if desc:
        c.setFont(_FONT_NAME, 8.5)
        c.setFillColor(MUTED)
        _draw_wrapped(c, desc, right_x, y + h - 38, right_w, max_lines=2, line_h=11)

    # Собираем чипсы: занимают остаток высоты
    chips: list[str] = []
    for kind_key in ("colors", "styles", "occasions", "seasons", "shoot_types"):
        chips.extend(_split_tags(str(outfit.get(kind_key) or "")))
    chips = chips[:14]  # не больше 14
    _chips(c, right_x, y + h - 68, right_w, chips)


def _draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    w: float,
    *,
    max_lines: int,
    line_h: float = 11,
    font_size: float = 8.5,
) -> None:
    words = text.split()
    line: list[str] = []
    drawn = 0
    cur_y = y
    for word in words:
        cand = (" ".join([*line, word])).strip()
        if c.stringWidth(cand, _FONT_NAME, font_size) <= w:
            line.append(word)
        else:
            if line:
                c.drawString(x, cur_y, " ".join(line))
                cur_y -= line_h
                drawn += 1
                if drawn >= max_lines:
                    return
            line = [word]
    if line and drawn < max_lines:
        c.drawString(x, cur_y, " ".join(line))


def _cover(c: canvas.Canvas, *, client: str, when: str, subtitle: str) -> None:
    # Большая бежевая плашка сверху на треть страницы
    c.setFillColor(PAPER)
    c.rect(0, PAGE_H * 0.62, PAGE_W, PAGE_H * 0.38, stroke=0, fill=1)

    # Бренд
    c.setFillColor(ACCENT)
    c.setFont(_FONT_NAME_BOLD, 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.86, "MARINA ZAUGOLNIKOVA")
    # Декоративная линия
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.6)
    c.line(PAGE_W / 2 - 30, PAGE_H * 0.85, PAGE_W / 2 + 30, PAGE_H * 0.85)

    # Заголовок
    c.setFillColor(INK)
    c.setFont(_FONT_NAME_BOLD, 36)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.74, "Подбор образов")

    # Подзаголовок
    c.setFillColor(MUTED)
    c.setFont(_FONT_NAME, 12)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.70, subtitle)

    # Нижняя часть: клиент + дата
    c.setFillColor(INK)
    c.setFont(_FONT_NAME, 11)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.4, f"для @{client.lstrip('@') or 'клиента'}")
    c.setFillColor(MUTED)
    c.setFont(_FONT_NAME, 10)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.4 - 16, when)

    # Контакты внизу (без сайта — он динамически меняется и в PDF не нужен)
    c.setFont(_FONT_NAME, 8)
    c.setFillColor(MUTED)
    c.drawCentredString(PAGE_W / 2, MARGIN + 30, "+7 (985) 196-30-84")
    c.drawCentredString(PAGE_W / 2, MARGIN + 18, "mzaugolnikova@gmail.com")


def _section_header(c: canvas.Canvas, title: str, count: int, color: HexColor) -> float:
    """Цветная плашка-заголовок секции. Возвращает y под плашкой."""
    h = 44
    top_y = PAGE_H - MARGIN
    c.setFillColor(color)
    c.rect(0, top_y - h, PAGE_W, h, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(_FONT_NAME_BOLD, 18)
    c.drawString(MARGIN, top_y - 28, title)
    c.setFont(_FONT_NAME, 9)
    c.drawRightString(PAGE_W - MARGIN, top_y - 28, f"{count} образ(ов)")
    c.setFillColor(INK)
    return top_y - h - 20


def _draw_outfits_page(
    c: canvas.Canvas,
    outfits: list[dict[str, Any]],
    *,
    start_y: float,
    client: str,
    bot: str,
    when: str,
    section_title: str | None = None,
    section_color: HexColor | None = None,
) -> None:
    """Раскладывает 4 карточки на страницу. Если влезло не всё — следующая страница."""
    cards_per_page = 4
    card_h = 130
    gap = 10
    card_w = PAGE_W - 2 * MARGIN

    cur_y = start_y
    slot = 0
    for outfit in outfits:
        if slot >= cards_per_page:
            _watermark(c, client=client, bot=bot, when=when)
            c.showPage()
            # На новой странице — мини-хедер секции (если задана)
            if section_title:
                c.setFillColor(MUTED)
                c.setFont(_FONT_NAME_BOLD, 9)
                c.drawString(MARGIN, PAGE_H - MARGIN + 4, section_title.upper())
                c.setStrokeColor(LINE)
                c.line(MARGIN, PAGE_H - MARGIN - 2, PAGE_W - MARGIN, PAGE_H - MARGIN - 2)
                c.setFillColor(INK)
            cur_y = PAGE_H - MARGIN - 16
            slot = 0
        _draw_card(
            c,
            x=MARGIN,
            y=cur_y - card_h,
            w=card_w,
            h=card_h,
            outfit=outfit,
        )
        cur_y -= card_h + gap
        slot += 1


def generate_pdf(
    *,
    outfits: list[dict[str, Any]],
    client_username: str,
    bot_username: str,
) -> bytes:
    """Один раздел — все образы подряд."""
    _ensure_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"{settings.brand_name} — Подбор образов")
    when = datetime.now(tz=UTC).strftime("%d.%m.%Y")

    _cover(
        c, client=client_username, when=when, subtitle=f"{len(outfits)} образ(ов) под твою съёмку"
    )
    _watermark(c, client=client_username, bot=bot_username, when=when)
    c.showPage()

    start_y = _section_header(c, "Подборка", len(outfits), ACCENT)
    _draw_outfits_page(
        c,
        outfits,
        start_y=start_y,
        client=client_username,
        bot=bot_username,
        when=when,
        section_title="Подборка",
        section_color=ACCENT,
    )
    _watermark(c, client=client_username, bot=bot_username, when=when)
    c.showPage()
    c.save()
    return buf.getvalue()


def generate_pdf_sections(
    *,
    sections: list[dict[str, Any]],
    client_username: str,
    bot_username: str,
) -> bytes:
    """Многосекционный PDF."""
    _ensure_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"{settings.brand_name} — Подбор образов")
    when = datetime.now(tz=UTC).strftime("%d.%m.%Y")
    total = sum(len(s.get("outfits") or []) for s in sections)

    _cover(
        c,
        client=client_username,
        when=when,
        subtitle=f"{total} образ(ов) · {len(sections)} раздела",
    )
    _watermark(c, client=client_username, bot=bot_username, when=when)
    c.showPage()

    palette = [LIKED, MAYBE, ACCENT]
    for i, section in enumerate(sections):
        title = str(section.get("title") or "Раздел")
        outfits = section.get("outfits") or []
        if not outfits:
            continue
        color = palette[i % len(palette)]
        start_y = _section_header(c, title, len(outfits), color)
        _draw_outfits_page(
            c,
            outfits,
            start_y=start_y,
            client=client_username,
            bot=bot_username,
            when=when,
            section_title=title,
            section_color=color,
        )
        _watermark(c, client=client_username, bot=bot_username, when=when)
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
