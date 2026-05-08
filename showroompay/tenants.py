from __future__ import annotations


class TenantRegistry:

    _tenants: dict = {}

    def __init__(self):
        pass

    def register(self, tenant_id: str, name: str, currency: str = "USD",
                 checkout_enabled: bool = False, admin_enabled: bool = False) -> bool:
        if not tenant_id or not name:
            return False
        self._tenants[tenant_id] = {
            "tenant_id": tenant_id,
            "name": name,
            "currency": currency,
            "checkout_enabled": checkout_enabled,
            "admin_enabled": admin_enabled,
        }
        return True

    def get(self, tenant_id: str) -> dict | None:
        record = self._tenants.get(tenant_id)
        if record is None:
            return None
        return dict(record)

    def list_ids(self) -> list:
        return list(self._tenants.keys())

    def is_checkout_enabled(self, tenant_id: str) -> bool:
        record = self._tenants.get(tenant_id)
        return bool(record and record.get("checkout_enabled"))

    def size(self) -> int:
        return len(self._tenants)

    @classmethod
    def reset(cls):
        cls._tenants = {}
