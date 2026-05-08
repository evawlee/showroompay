from __future__ import annotations

import time


class AuditLog:

    _entries: list = []

    def __init__(self):
        pass

    def append(self, event: str, actor: str, target: str = "",
               meta: dict | None = None):
        self._entries.append({
            "event": event,
            "actor": actor,
            "target": target,
            "meta": dict(meta) if meta else {},
            "at": time.time(),
        })

    def entries(self) -> list:
        return [dict(e) for e in self._entries]

    def size(self) -> int:
        return len(self._entries)

    def find_for_target(self, target: str) -> list:
        return [dict(e) for e in self._entries if e.get("target") == target]

    @classmethod
    def reset(cls):
        cls._entries = []
