"""Ad Poster Engine — the one engine that calls out to Gemini.

Every other engine in AXIOM runs entirely on the local llama3.2 model. Image
generation is the one capability a small local model can't do, so this engine
uses Google's Gemini API (gemini-2.5-flash-image) purely for that — nothing
else about the business ever leaves the machine through this path beyond the
poster prompt itself.

The API key lives in backend/.env (gitignored) and is never logged or returned
to the client. If it's missing, or the account has no quota, the engine fails
loudly with Google's own error message rather than pretending to succeed.
"""
import base64
import re
import uuid
from pathlib import Path
from datetime import datetime
import httpx
from sqlmodel import Session, select
from config import settings
from db import engine as db_engine
from models import Business, AdPoster
from metrics import compute_kpis

STATIC_DIR = Path(__file__).parent / "static" / "posters"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class PosterError(Exception):
    """Raised with a user-safe message — never includes the API key."""


def _business_brief() -> dict:
    with Session(db_engine) as s:
        biz = s.exec(select(Business)).first()
    kpis = compute_kpis()
    return {
        "name": biz.name if biz else "the business",
        "industry": biz.industry if biz else "D2C",
        "description": biz.description if biz else "",
        "growth_score": kpis.get("growth_score", 0),
    }


def build_prompt(user_brief: str) -> str:
    """Combine the founder's brief with real business context into one
    image-generation prompt."""
    biz = _business_brief()
    return (
        f"Professional advertising poster for {biz['name']}, a {biz['industry']} brand. "
        f"{biz['description'] or ''} "
        f"Creative brief: {user_brief}. "
        "High-end commercial ad photography style, clean composition, tasteful "
        "typography space, no spelling errors in any text shown, square 1:1 aspect ratio."
    ).strip()


async def generate_poster(user_brief: str) -> dict:
    """Calls Gemini to generate one ad poster image. Persists it (image on disk,
    metadata in SQLite) and returns the row's public info. Raises PosterError
    with a clean, user-facing message on any failure — including quota/billing
    errors from Google, surfaced verbatim so the founder knows exactly what to fix."""
    if not settings.gemini_api_key:
        raise PosterError(
            "No Gemini API key configured. Add GEMINI_API_KEY to backend/.env and restart."
        )

    prompt = build_prompt(user_brief)
    url = _GEMINI_URL.format(model=settings.gemini_image_model)

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                url,
                params={"key": settings.gemini_api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
                },
            )
        except httpx.RequestError as e:
            raise PosterError(f"Could not reach Gemini: {e}")

    if r.status_code != 200:
        try:
            detail = r.json().get("error", {}).get("message", r.text[:300])
        except Exception:
            detail = r.text[:300]
        _persist_error(prompt, f"Gemini {r.status_code}: {detail}")
        raise PosterError(detail)

    data = r.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise PosterError("Gemini returned no candidates — try a different brief.")

    parts = candidates[0].get("content", {}).get("parts", [])
    image_b64 = None
    caption = None
    for p in parts:
        inline = p.get("inlineData") or p.get("inline_data")
        if inline and inline.get("data"):
            image_b64 = inline["data"]
        if p.get("text"):
            caption = p["text"]

    if not image_b64:
        raise PosterError("Gemini responded but returned no image data for this prompt.")

    filename = f"{uuid.uuid4().hex}.png"
    (STATIC_DIR / filename).write_bytes(base64.b64decode(image_b64))

    with Session(db_engine) as s:
        row = AdPoster(prompt=prompt, image_path=f"posters/{filename}",
                        caption=caption, status="ok")
        s.add(row)
        s.commit()
        s.refresh(row)
        return _serialize(row)


def _persist_error(prompt: str, error: str) -> None:
    with Session(db_engine) as s:
        s.add(AdPoster(prompt=prompt, image_path="", status="error", error=error))
        s.commit()


def _serialize(row: AdPoster) -> dict:
    return {
        "id": row.id, "ts": row.ts.isoformat(), "prompt": row.prompt,
        "image_url": f"/static/{row.image_path}" if row.image_path else None,
        "caption": row.caption, "status": row.status, "error": row.error,
    }


def list_posters(limit: int = 20) -> list[dict]:
    with Session(db_engine) as s:
        rows = s.exec(select(AdPoster).order_by(AdPoster.id.desc()).limit(limit)).all()
        return [_serialize(r) for r in rows]
