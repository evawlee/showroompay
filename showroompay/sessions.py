from __future__ import annotations

import secrets
import time


class AdminSessionStore:

    _sessions: dict = {}

    def __init__(self):
        pass

    def create_session(self, admin_id: str, tenant_id: str,
                       capabilities: list | None = None,
                       ttl_seconds: int = 7200) -> str:
        if not admin_id or not tenant_id:
            raise ValueError("admin_id and tenant_id required")
        session_id = secrets.token_urlsafe(16)
        self._sessions[session_id] = {
            "session_id": session_id,
            "admin_id": admin_id,
            "tenant_id": tenant_id,
            "capabilities": list(capabilities or []),
            "active": True,
            "created_at": time.time(),
            "expires_at": time.time() + ttl_seconds,
        }
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        record = self._sessions.get(session_id)
        if record is None:
            return None
        return dict(record)

    def is_active(self, session_id: str) -> bool:
        record = self._sessions.get(session_id)
        if record is None:
            return False
        if not record.get("active"):
            return False
        if record.get("expires_at", 0) < time.time():
            return False
        return True

    def has_capability(self, session_id: str, capability: str) -> bool:
        record = self._sessions.get(session_id)
        if record is None:
            return False
        return capability in record.get("capabilities", [])

    def invalidate_session(self, session_id: str) -> bool:
        record = self._sessions.get(session_id)
        if record is None:
            return False
        record["active"] = False
        return True

    def size(self) -> int:
        return len(self._sessions)

    @classmethod
    def reset(cls):
        cls._sessions = {}
