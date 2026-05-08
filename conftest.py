import pytest

from showroompay.tenants import TenantRegistry
from showroompay.orders import OrderStore
from showroompay.webhooks import WebhookCache
from showroompay.sessions import AdminSessionStore
from showroompay.audit import AuditLog
from showroompay import runtime


@pytest.fixture(autouse=True)
def _reset_stores():
    TenantRegistry.reset()
    OrderStore.reset()
    WebhookCache.reset()
    AdminSessionStore.reset()
    AuditLog.reset()
    runtime._reset_defaults()
    yield
    TenantRegistry.reset()
    OrderStore.reset()
    WebhookCache.reset()
    AdminSessionStore.reset()
    AuditLog.reset()
    runtime._reset_defaults()
