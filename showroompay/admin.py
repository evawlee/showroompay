from __future__ import annotations

from showroompay.runtime import (
    get_default_sessions,
    get_default_orders,
    get_default_tenants,
)
from showroompay.orders import STATE_REFUNDED


CAP_VIEW_ORDERS = "view_orders"
CAP_REFUND_ORDERS = "refund_orders"
CAP_MANAGE_TENANT = "manage_tenant"


def admin_list_orders(session_id: str, tenant_id: str) -> dict:
    sessions = get_default_sessions()
    if not sessions.is_active(session_id):
        return {"status": "error", "reason": "session_inactive"}
    if not sessions.has_capability(session_id, CAP_VIEW_ORDERS):
        return {"status": "error", "reason": "missing_capability"}
    orders = get_default_orders()
    return {
        "status": "ok",
        "tenant_id": tenant_id,
        "orders": orders.list_for_tenant(tenant_id),
    }


def admin_refund_order(session_id: str, order_id: str) -> dict:
    sessions = get_default_sessions()
    if not sessions.is_active(session_id):
        return {"status": "error", "reason": "session_inactive"}
    if not sessions.has_capability(session_id, CAP_REFUND_ORDERS):
        return {"status": "error", "reason": "missing_capability"}
    orders = get_default_orders()
    record = orders.get_order(order_id)
    if record is None:
        return {"status": "error", "reason": "unknown_order"}
    orders.set_state(order_id, STATE_REFUNDED)
    return {"status": "ok", "order_id": order_id, "state": STATE_REFUNDED}


def admin_update_tenant(session_id: str, tenant_id: str,
                        currency: str | None = None,
                        checkout_enabled: bool | None = None) -> dict:
    sessions = get_default_sessions()
    if not sessions.is_active(session_id):
        return {"status": "error", "reason": "session_inactive"}
    if not sessions.has_capability(session_id, CAP_MANAGE_TENANT):
        return {"status": "error", "reason": "missing_capability"}
    tenants = get_default_tenants()
    record = tenants.get(tenant_id)
    if record is None:
        return {"status": "error", "reason": "unknown_tenant"}
    name = record["name"]
    new_currency = currency if currency is not None else record["currency"]
    new_checkout = checkout_enabled if checkout_enabled is not None else record["checkout_enabled"]
    tenants.register(tenant_id, name, currency=new_currency,
                     checkout_enabled=new_checkout,
                     admin_enabled=record["admin_enabled"])
    return {"status": "ok", "tenant_id": tenant_id}
