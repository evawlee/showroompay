from __future__ import annotations

import hashlib
import hmac
import json
import time

from showroompay.runtime import (
    get_default_orders,
    get_default_webhooks,
    get_default_tenants,
)
from showroompay.orders import (
    STATE_DRAFT,
    STATE_PENDING,
    STATE_CONFIRMED,
    STATE_REFUNDED,
    STATE_CANCELLED,
)


WEBHOOK_SHARED_SECRET = b"showroompay-shared-webhook-secret-do-not-leak"


def _compute_signature(payload: bytes) -> str:
    return hmac.new(WEBHOOK_SHARED_SECRET, payload, hashlib.sha256).hexdigest()


def _digest_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def submit_payment(order_id: str, payment_method_token: str) -> dict:
    orders = get_default_orders()
    record = orders.get_order(order_id)
    if record is None:
        return {"status": "error", "reason": "unknown_order"}
    if not payment_method_token:
        return {"status": "error", "reason": "missing_payment_method"}
    orders.attach_payment_method(order_id, payment_method_token)
    orders.set_state(order_id, STATE_PENDING)
    return {"status": "ok", "order_id": order_id, "state": STATE_PENDING}


def confirm_order(order_id: str) -> dict:
    orders = get_default_orders()
    record = orders.get_order(order_id)
    if record is None:
        return {"status": "error", "reason": "unknown_order"}
    orders.set_state(order_id, STATE_CONFIRMED)
    return {"status": "ok", "order_id": order_id, "state": STATE_CONFIRMED}


def refund_order(order_id: str) -> dict:
    orders = get_default_orders()
    record = orders.get_order(order_id)
    if record is None:
        return {"status": "error", "reason": "unknown_order"}
    orders.set_state(order_id, STATE_REFUNDED)
    return {"status": "ok", "order_id": order_id, "state": STATE_REFUNDED}


def cancel_order(order_id: str) -> dict:
    orders = get_default_orders()
    record = orders.get_order(order_id)
    if record is None:
        return {"status": "error", "reason": "unknown_order"}
    orders.set_state(order_id, STATE_CANCELLED)
    return {"status": "ok", "order_id": order_id, "state": STATE_CANCELLED}


def handle_webhook(webhook_id: str, signature: str, payload: bytes) -> dict:
    expected = _compute_signature(payload)
    if not hmac.compare_digest(expected, signature):
        return {"status": "error", "reason": "bad_signature"}
    cache = get_default_webhooks()
    parsed = json.loads(payload.decode("utf-8"))
    order_id = parsed.get("order_id")
    event_type = parsed.get("event_type")
    tenant_id = parsed.get("tenant_id", "")
    cache.record(webhook_id, tenant_id, _digest_payload(payload))
    if event_type == "payment_succeeded":
        confirm_order(order_id)
    elif event_type == "payment_failed":
        cancel_order(order_id)
    elif event_type == "refund_issued":
        refund_order(order_id)
    return {"status": "ok", "order_id": order_id, "event_type": event_type}


def get_order_summary(order_id: str, requesting_tenant_id: str) -> dict:
    orders = get_default_orders()
    record = orders.get_order(order_id)
    if record is None:
        return {"status": "error", "reason": "unknown_order"}
    return {
        "status": "ok",
        "order_id": record["order_id"],
        "tenant_id": record["tenant_id"],
        "customer_email": record["customer_email"],
        "amount_cents": record["amount_cents"],
        "currency": record["currency"],
        "state": record["state"],
        "payment_method_token": record.get("payment_method_token"),
    }
