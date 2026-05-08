import json
import pytest

from showroompay import (
    TenantRegistry,
    OrderStore,
    WebhookCache,
    AdminSessionStore,
    AuditLog,
    submit_payment,
    confirm_order,
    refund_order,
    cancel_order,
    handle_webhook,
    get_order_summary,
    admin_list_orders,
    admin_refund_order,
    admin_update_tenant,
    CAP_VIEW_ORDERS,
    CAP_REFUND_ORDERS,
    CAP_MANAGE_TENANT,
    STATE_DRAFT,
    STATE_PENDING,
    STATE_CONFIRMED,
    STATE_REFUNDED,
    STATE_CANCELLED,
    get_default_tenants,
    get_default_orders,
    get_default_sessions,
)
from showroompay.checkout import _compute_signature


class TestTenantRegistry:

    def test_register_and_get(self):
        tr = TenantRegistry()
        assert tr.register("t1", "Acme", currency="EUR", checkout_enabled=True)
        record = tr.get("t1")
        assert record["name"] == "Acme"
        assert record["currency"] == "EUR"
        assert record["checkout_enabled"] is True

    def test_list_ids(self):
        tr = TenantRegistry()
        tr.register("t1", "Acme")
        tr.register("t2", "Beta")
        ids = tr.list_ids()
        assert set(ids) == {"t1", "t2"}

    def test_unknown_tenant_returns_none(self):
        tr = TenantRegistry()
        assert tr.get("missing") is None


class TestOrderStore:

    def test_create_and_lookup(self):
        os_ = OrderStore()
        oid = os_.create_order("t1", "alice@example.com", 5000)
        record = os_.get_order(oid)
        assert record["customer_email"] == "alice@example.com"
        assert record["amount_cents"] == 5000
        assert record["state"] == STATE_DRAFT

    def test_set_state_appends_transition(self):
        os_ = OrderStore()
        oid = os_.create_order("t1", "alice@example.com", 5000)
        os_.set_state(oid, STATE_PENDING)
        os_.set_state(oid, STATE_CONFIRMED)
        record = os_.get_order(oid)
        states = [t[0] for t in record["transitions"]]
        assert states == [STATE_DRAFT, STATE_PENDING, STATE_CONFIRMED]

    def test_list_for_tenant_filters(self):
        os_ = OrderStore()
        os_.create_order("t1", "a@example.com", 100)
        os_.create_order("t2", "b@example.com", 200)
        os_.create_order("t1", "c@example.com", 300)
        results = os_.list_for_tenant("t1")
        assert len(results) == 2
        for o in results:
            assert o["tenant_id"] == "t1"

    def test_invalid_create_raises(self):
        os_ = OrderStore()
        with pytest.raises(ValueError):
            os_.create_order("", "a@example.com", 100)
        with pytest.raises(ValueError):
            os_.create_order("t1", "a@example.com", 0)


class TestWebhookCache:

    def test_record_and_seen(self):
        wc = WebhookCache()
        wc.record("wh-1", "t1", "deadbeef")
        assert wc.has_seen("wh-1")
        assert not wc.has_seen("wh-2")

    def test_lookup_returns_record(self):
        wc = WebhookCache()
        wc.record("wh-1", "t1", "deadbeef")
        record = wc.lookup("wh-1")
        assert record["tenant_id"] == "t1"
        assert record["payload_digest"] == "deadbeef"


class TestAdminSessionStore:

    def test_create_session_returns_id(self):
        ss = AdminSessionStore()
        sid = ss.create_session("admin-1", "t1", capabilities=[CAP_VIEW_ORDERS])
        assert isinstance(sid, str) and len(sid) > 8

    def test_is_active_for_fresh_session(self):
        ss = AdminSessionStore()
        sid = ss.create_session("admin-1", "t1")
        assert ss.is_active(sid)

    def test_invalidate_marks_inactive(self):
        ss = AdminSessionStore()
        sid = ss.create_session("admin-1", "t1")
        ss.invalidate_session(sid)
        assert not ss.is_active(sid)

    def test_capability_check(self):
        ss = AdminSessionStore()
        sid = ss.create_session("admin-1", "t1", capabilities=[CAP_REFUND_ORDERS])
        assert ss.has_capability(sid, CAP_REFUND_ORDERS)
        assert not ss.has_capability(sid, CAP_MANAGE_TENANT)


class TestAuditLog:

    def test_append_and_size(self):
        al = AuditLog()
        al.append("test_event", "actor-1", target="tgt-1")
        assert al.size() == 1

    def test_find_for_target(self):
        al = AuditLog()
        al.append("e1", "a1", target="tgt-1")
        al.append("e2", "a1", target="tgt-2")
        al.append("e3", "a1", target="tgt-1")
        results = al.find_for_target("tgt-1")
        assert len(results) == 2


class TestCheckoutHappyPath:

    def test_submit_payment_moves_to_pending(self):
        get_default_tenants().register("t1", "Acme", checkout_enabled=True)
        oid = get_default_orders().create_order("t1", "a@example.com", 1000)
        result = submit_payment(oid, "pm_test_123")
        assert result["status"] == "ok"
        assert result["state"] == STATE_PENDING

    def test_webhook_with_valid_signature_confirms(self):
        get_default_tenants().register("t1", "Acme", checkout_enabled=True)
        oid = get_default_orders().create_order("t1", "a@example.com", 1000)
        get_default_orders().set_state(oid, STATE_PENDING)
        payload = json.dumps({
            "order_id": oid,
            "tenant_id": "t1",
            "event_type": "payment_succeeded",
        }).encode("utf-8")
        sig = _compute_signature(payload)
        result = handle_webhook("wh-baseline-1", sig, payload)
        assert result["status"] == "ok"
        assert get_default_orders().get_state(oid) == STATE_CONFIRMED

    def test_webhook_with_bad_signature_rejected(self):
        get_default_tenants().register("t1", "Acme", checkout_enabled=True)
        oid = get_default_orders().create_order("t1", "a@example.com", 1000)
        payload = json.dumps({"order_id": oid, "tenant_id": "t1", "event_type": "payment_succeeded"}).encode("utf-8")
        result = handle_webhook("wh-bad-1", "deadbeef", payload)
        assert result["status"] == "error"

    def test_get_order_summary_returns_record(self):
        get_default_tenants().register("t1", "Acme", checkout_enabled=True)
        oid = get_default_orders().create_order("t1", "a@example.com", 1000)
        result = get_order_summary(oid, "t1")
        assert result["status"] == "ok"
        assert result["amount_cents"] == 1000


class TestAdminHappyPath:

    def test_admin_list_orders_with_capability(self):
        get_default_tenants().register("t1", "Acme", admin_enabled=True)
        get_default_orders().create_order("t1", "a@example.com", 1000)
        sid = get_default_sessions().create_session("admin-1", "t1",
                                                     capabilities=[CAP_VIEW_ORDERS])
        result = admin_list_orders(sid, "t1")
        assert result["status"] == "ok"
        assert len(result["orders"]) == 1

    def test_admin_refund_with_capability(self):
        get_default_tenants().register("t1", "Acme", admin_enabled=True)
        oid = get_default_orders().create_order("t1", "a@example.com", 1000)
        get_default_orders().set_state(oid, STATE_PENDING)
        get_default_orders().set_state(oid, STATE_CONFIRMED)
        sid = get_default_sessions().create_session("admin-1", "t1",
                                                     capabilities=[CAP_REFUND_ORDERS])
        result = admin_refund_order(sid, oid)
        assert result["status"] == "ok"
        assert get_default_orders().get_state(oid) == STATE_REFUNDED

    def test_admin_without_capability_denied(self):
        get_default_tenants().register("t1", "Acme", admin_enabled=True)
        oid = get_default_orders().create_order("t1", "a@example.com", 1000)
        sid = get_default_sessions().create_session("admin-1", "t1", capabilities=[])
        result = admin_refund_order(sid, oid)
        assert result["status"] == "error"

    def test_admin_with_inactive_session_denied(self):
        get_default_tenants().register("t1", "Acme", admin_enabled=True)
        sid = get_default_sessions().create_session("admin-1", "t1",
                                                     capabilities=[CAP_VIEW_ORDERS])
        get_default_sessions().invalidate_session(sid)
        result = admin_list_orders(sid, "t1")
        assert result["status"] == "error"

    def test_admin_update_tenant_currency(self):
        get_default_tenants().register("t1", "Acme", admin_enabled=True, currency="USD")
        sid = get_default_sessions().create_session("admin-1", "t1",
                                                     capabilities=[CAP_MANAGE_TENANT])
        result = admin_update_tenant(sid, "t1", currency="EUR")
        assert result["status"] == "ok"
        assert get_default_tenants().get("t1")["currency"] == "EUR"
