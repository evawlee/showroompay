from __future__ import annotations

import time


class WebhookCache:

    _seen: dict = {}

    def __init__(self):
        pass

    def record(self, webhook_id: str, tenant_id: str, payload_digest: str) -> bool:
        if not webhook_id:
            return False
        self._seen[webhook_id] = {
            "webhook_id": webhook_id,
            "tenant_id": tenant_id,
            "payload_digest": payload_digest,
            "seen_at": time.time(),
        }
        return True

    def has_seen(self, webhook_id: str) -> bool:
        return webhook_id in self._seen

    def lookup(self, webhook_id: str) -> dict | None:
        record = self._seen.get(webhook_id)
        if record is None:
            return None
        return dict(record)

    def size(self) -> int:
        return len(self._seen)

    @classmethod
    def reset(cls):
        cls._seen = {}
