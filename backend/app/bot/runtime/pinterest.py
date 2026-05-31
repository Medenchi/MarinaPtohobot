"""Pinterest import poller.

Listens to `pinterest_imports` table.
When a new request appears, fetches the URL using WhatsApp User-Agent,
extracts the og:image URL, downloads it, uploads it to Supabase Storage,
creates an outfit_images record, and marks the request as done.
"""

import asyncio
import io
import logging
import re
import urllib.request
from datetime import UTC, datetime

from app.core.supabase import get_supabase
from app.core.config import settings
from app.bot.runtime.pdf import upload_pdf  # we can reuse or write a small upload func

log = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3.0

def _fetch_pinterest_image_url(url: str) -> str | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "WhatsApp/2.19.81 A",
            "Accept": "text/html"
        }
    )
    try:
        html = urllib.request.urlopen(req, timeout=10.0).read().decode('utf-8')
        m = re.search(r'<meta[^>]+property="og:image"[^>]*content="([^"]+)"', html, re.I)
        if not m:
            m = re.search(r'content="([^"]+)"[^>]+property="og:image"', html, re.I)
        if m and m.group(1):
            return m.group(1)
    except Exception as e:
        log.warning("Pinterest fetch failed: %s", e)
    return None

def _download_image(url: str) -> bytes | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "WhatsApp/2.19.81 A"
        }
    )
    try:
        return urllib.request.urlopen(req, timeout=15.0).read()
    except Exception as e:
        log.warning("Failed to download image from %s: %s", url, e)
        return None

async def poll_pinterest_imports() -> None:
    sb = get_supabase()
    while True:
        try:
            resp = (
                sb.table("pinterest_imports")
                .select("*")
                .eq("status", "pending")
                .order("created_at", desc=False)
                .limit(5)
                .execute()
            )
            for row in resp.data or []:
                req_id = row["id"]
                url = row["pinterest_url"]
                outfit_id = row["outfit_id"]

                # Mark as processing
                sb.table("pinterest_imports").update({"status": "processing"}).eq("id", req_id).execute()

                img_url = _fetch_pinterest_image_url(url)
                if not img_url:
                    sb.table("pinterest_imports").update({
                        "status": "error",
                        "error_text": "Не удалось найти изображение (пин скрыт или удален)"
                    }).eq("id", req_id).execute()
                    continue

                img_bytes = _download_image(img_url)
                if not img_bytes:
                    sb.table("pinterest_imports").update({
                        "status": "error",
                        "error_text": "Не удалось скачать картинку"
                    }).eq("id", req_id).execute()
                    continue

                # Upload to Supabase Storage
                import uuid
                ext = "jpg"
                if img_url.lower().endswith(".png"): ext = "png"
                elif img_url.lower().endswith(".webp"): ext = "webp"
                
                filename = f"pinterest_{uuid.uuid4().hex[:8]}.{ext}"
                bucket = settings.storage_bucket_outfits
                
                # Upload using Supabase JS client equivalent
                res = sb.storage.from_(bucket).upload(
                    path=filename,
                    file=img_bytes,
                    file_options={"content-type": f"image/{ext}"}
                )
                
                # Insert into outfit_images
                sb.table("outfit_images").insert({
                    "outfit_id": outfit_id,
                    "storage_path": filename,
                    "sort_order": 0
                }).execute()

                sb.table("pinterest_imports").update({
                    "status": "done"
                }).eq("id", req_id).execute()

        except Exception as e:
            log.error("Error in pinterest poller: %s", e)
        
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
