from __future__ import annotations

import secrets
import time


STATE_DRAFT = "draft"
STATE_PENDING = "pending"
STATE_CONFIRMED = "confirmed"
STATE_REFUNDED = "refunded"
STATE_CANCELLED = "cancelled"


class OrderStore:

    _orders: dict = {}

    def __init__(self):
        pass

    def create_order(self, tenant_id: str, customer_email: str, amount_cents: int,
                     currency: str = "USD") -> str:
        if not tenant_id or not customer_email or amount_cents <= 0:
            raise ValueError("tenant_id, customer_email, positive amount required")
        order_id = secrets.token_urlsafe(12)
        self._orders[order_id] = {
            "order_id": order_id,
            "tenant_id": tenant_id,
            "customer_email": customer_email,
            "amount_cents": amount_cents,
            "currency": currency,
            "state": STATE_DRAFT,
            "payment_method_token": None,
            "created_at": time.time(),
            "transitions": [(STATE_DRAFT, time.time())],
        }
        return order_id

    def attach_payment_method(self, order_id: str, payment_method_token: str) -> bool:
        record = self._orders.get(order_id)
        if record is None:
            return False
        record["payment_method_token"] = payment_method_token
        return True

    def get_order(self, order_id: str) -> dict | None:
        record = self._orders.get(order_id)
        if record is None:
            return None
        return dict(record)

    def set_state(self, order_id: str, new_state: str) -> bool:
        record = self._orders.get(order_id)
        if record is None:
            return False
        record["state"] = new_state
        record["transitions"].append((new_state, time.time()))
        return True

    def list_for_tenant(self, tenant_id: str) -> list:
        return [dict(o) for o in self._orders.values() if o.get("tenant_id") == tenant_id]

    def get_state(self, order_id: str) -> str | None:
        record = self._orders.get(order_id)
        return record.get("state") if record else None

    def size(self) -> int:
        return len(self._orders)

    @classmethod
    def reset(cls):
        cls._orders = {}
