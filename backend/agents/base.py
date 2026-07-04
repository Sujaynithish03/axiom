"""BaseAgent — all six agents share this event-emitting scaffolding."""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Callable, Awaitable, Optional
from sqlmodel import Session
from db import engine
from models import AgentEvent
from llm import stream_chat, complete_json

EventEmitter = Callable[[dict], Awaitable[None]]


class BaseAgent:
    name: str = "base"
    display: str = "Base Agent"
    role: str = ""

    def __init__(self, emit: Optional[EventEmitter] = None):
        self._emit = emit

    async def emit(self, kind: str, content: str, meta: dict | None = None):
        """Persist an event and broadcast it to all connected websockets."""
        with Session(engine) as s:
            evt = AgentEvent(agent=self.name, kind=kind, content=content, meta=meta)
            s.add(evt)
            s.commit()
            s.refresh(evt)
            payload = {
                "id": evt.id, "ts": evt.ts.isoformat(),
                "agent": self.name, "display": self.display,
                "kind": kind, "content": content, "meta": meta or {},
            }
        if self._emit:
            await self._emit(payload)

    async def stream_thinking(self, system: str, user: str, max_tokens: int = 300):
        """Stream a thought aloud — every token becomes a websocket event.
        Chunks tokens into ~20-char windows so the UI doesn't get spammed."""
        buffer = ""
        full = ""
        async for tok in stream_chat(system, user, max_tokens=max_tokens):
            buffer += tok
            full += tok
            if len(buffer) >= 20 or "\n" in buffer:
                await self.emit("thinking", buffer)
                buffer = ""
                await asyncio.sleep(0.01)  # yield to event loop
        if buffer:
            await self.emit("thinking", buffer)
        return full

    async def structured(self, system: str, user: str) -> dict:
        """Return a JSON-mode structured response."""
        return await complete_json(system, user)

    # Subclasses implement this
    async def run(self, ctx: dict) -> dict:
        raise NotImplementedError
