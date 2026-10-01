"""In-process fan-out for authenticated RFP ticket notifications."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

_EVENT_NAME = "rfp_ticket_created"
_MAX_PENDING_EVENTS = 100


class RFPEventHub:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_MAX_PENDING_EVENTS)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    async def publish(self, payload: dict[str, Any]) -> None:
        for queue in tuple(self._subscribers):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(payload)

    async def stream(self) -> AsyncIterator[str]:
        queue = self.subscribe()
        try:
            yield ": connected\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield f"event: {_EVENT_NAME}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
        finally:
            self.unsubscribe(queue)


rfp_events = RFPEventHub()
