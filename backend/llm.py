"""Thin wrapper around Ollama for streaming + JSON-mode agent calls."""
import json
from typing import AsyncIterator, Optional
import httpx
from config import settings


async def stream_chat(
    system: str,
    user: str,
    temperature: float = None,
    max_tokens: int = None,
) -> AsyncIterator[str]:
    """Yields tokens as they arrive from Ollama."""
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": True,
        "options": {
            "temperature": temperature if temperature is not None else settings.llm_temperature,
            "num_predict": max_tokens if max_tokens is not None else settings.llm_max_tokens,
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{settings.ollama_host}/api/chat", json=payload) as r:
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message", {})
                tok = msg.get("content", "")
                if tok:
                    yield tok
                if obj.get("done"):
                    break


async def complete_json(system: str, user: str, temperature: float = 0.2) -> dict:
    """Non-streaming JSON call — used when we need a structured object back."""
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature, "num_predict": settings.llm_max_tokens},
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{settings.ollama_host}/api/chat", json=payload)
        r.raise_for_status()
        content = r.json()["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Best-effort recovery: find first {...} block
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"error": "invalid_json", "raw": content}


async def complete_text(system: str, user: str, temperature: float = 0.3) -> str:
    """Plain text completion — used for freeform copilot / narrative replies."""
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": settings.llm_max_tokens},
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{settings.ollama_host}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()["message"]["content"]


async def check_ollama() -> Optional[str]:
    """Returns None if healthy, or an error string if not."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.ollama_host}/api/tags")
        if r.status_code != 200:
            return f"Ollama responded with {r.status_code}"
        tags = r.json().get("models", [])
        names = [t["name"] for t in tags]
        wanted = settings.ollama_model
        if not any(wanted in n for n in names):
            return f"Model '{wanted}' not pulled. Run: ollama pull {wanted}"
        return None
    except Exception as e:
        return f"Cannot reach Ollama at {settings.ollama_host}: {e}"
