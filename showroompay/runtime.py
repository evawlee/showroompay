from __future__ import annotations

from showroompay.tenants import TenantRegistry
from showroompay.orders import OrderStore
from showroompay.webhooks import WebhookCache
from showroompay.sessions import AdminSessionStore
from showroompay.audit import AuditLog


_default_tenants = TenantRegistry()
_default_orders = OrderStore()
_default_webhooks = WebhookCache()
_default_sessions = AdminSessionStore()
_default_audit = AuditLog()


def get_default_tenants() -> TenantRegistry:
    return _default_tenants


def get_default_orders() -> OrderStore:
    return _default_orders


def get_default_webhooks() -> WebhookCache:
    return _default_webhooks


def get_default_sessions() -> AdminSessionStore:
    return _default_sessions


def get_default_audit() -> AuditLog:
    return _default_audit


def _reset_defaults():
    global _default_tenants, _default_orders, _default_webhooks
    global _default_sessions, _default_audit
    _default_tenants = TenantRegistry()
    _default_orders = OrderStore()
    _default_webhooks = WebhookCache()
    _default_sessions = AdminSessionStore()
    _default_audit = AuditLog()
