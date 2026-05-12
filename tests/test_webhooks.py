import hashlib
import hmac
import json

import pytest

from briza_sdk.webhooks import WebhookHandler, verify_signature


SECRET = "test_webhook_secret_abc123"
BODY = b'{"type":"payment.completed","data":{"id":"pay_001","amount":1500}}'


def _sign(body: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


# ── verify_signature ──────────────────────────────────────────────────────────

class TestVerifySignature:
    def test_valid_signature(self):
        assert verify_signature(BODY, _sign(BODY), SECRET) is True

    def test_wrong_secret_rejected(self):
        header = _sign(BODY, secret="wrong_secret")
        assert verify_signature(BODY, header, SECRET) is False

    def test_tampered_body_rejected(self):
        header = _sign(BODY)
        tampered = BODY[:-1] + b"X"
        assert verify_signature(tampered, header, SECRET) is False

    def test_empty_body(self):
        empty = b""
        assert verify_signature(empty, _sign(empty), SECRET) is True

    def test_empty_body_wrong_sig(self):
        assert verify_signature(b"", _sign(BODY), SECRET) is False

    def test_multiple_signatures_first_valid(self):
        valid = _sign(BODY)
        stale = _sign(BODY, secret="old_secret")
        header = f"{valid},{stale}"
        assert verify_signature(BODY, header, SECRET) is True

    def test_multiple_signatures_last_valid(self):
        stale = _sign(BODY, secret="old_secret")
        valid = _sign(BODY)
        header = f"{stale},{valid}"
        assert verify_signature(BODY, header, SECRET) is True

    def test_multiple_signatures_all_invalid(self):
        header = f"{_sign(BODY, 'bad1')},{_sign(BODY, 'bad2')}"
        assert verify_signature(BODY, header, SECRET) is False

    def test_signature_with_spaces_around_comma(self):
        valid = _sign(BODY)
        stale = _sign(BODY, secret="old")
        header = f"{stale} , {valid}"
        assert verify_signature(BODY, header, SECRET) is True

    def test_missing_sha256_prefix_rejected(self):
        raw_hex = hmac.new(SECRET.encode(), BODY, hashlib.sha256).hexdigest()
        assert verify_signature(BODY, raw_hex, SECRET) is False

    def test_unicode_body(self):
        body = "Cobro de $15.00 — ñoño".encode()
        assert verify_signature(body, _sign(body), SECRET) is True

    def test_large_body(self):
        body = b"x" * 100_000
        assert verify_signature(body, _sign(body), SECRET) is True


# ── WebhookHandler ────────────────────────────────────────────────────────────

class TestWebhookHandler:
    def _make_event(self, event_type: str, data: dict | None = None) -> bytes:
        payload = {"type": event_type, "data": data or {}}
        return json.dumps(payload).encode()

    def test_registered_handler_called(self):
        handler = WebhookHandler(secret=SECRET)
        received = []

        @handler.on("payment.completed")
        def on_payment(event):
            received.append(event)

        raw = self._make_event("payment.completed", {"id": "pay_1"})
        handler.dispatch(raw, _sign(raw))

        assert len(received) == 1
        assert received[0]["data"]["id"] == "pay_1"

    def test_unregistered_event_ignored(self):
        handler = WebhookHandler(secret=SECRET)
        received = []

        @handler.on("invoice.paid")
        def on_invoice(event):
            received.append(event)

        raw = self._make_event("payment.completed")
        handler.dispatch(raw, _sign(raw))

        assert received == []

    def test_multiple_handlers_for_same_event(self):
        handler = WebhookHandler(secret=SECRET)
        calls = []

        @handler.on("payment.completed")
        def h1(event):
            calls.append("h1")

        @handler.on("payment.completed")
        def h2(event):
            calls.append("h2")

        raw = self._make_event("payment.completed")
        handler.dispatch(raw, _sign(raw))

        assert calls == ["h1", "h2"]

    def test_wildcard_handler_receives_any_event(self):
        handler = WebhookHandler(secret=SECRET)
        received_types = []

        @handler.on("*")
        def catch_all(event):
            received_types.append(event["type"])

        for event_type in ("payment.completed", "invoice.paid", "subscription.cancelled"):
            raw = self._make_event(event_type)
            handler.dispatch(raw, _sign(raw))

        assert received_types == ["payment.completed", "invoice.paid", "subscription.cancelled"]

    def test_specific_and_wildcard_both_called(self):
        handler = WebhookHandler(secret=SECRET)
        calls = []

        @handler.on("payment.completed")
        def specific(event):
            calls.append("specific")

        @handler.on("*")
        def wildcard(event):
            calls.append("wildcard")

        raw = self._make_event("payment.completed")
        handler.dispatch(raw, _sign(raw))

        assert "specific" in calls
        assert "wildcard" in calls

    def test_invalid_signature_raises(self):
        handler = WebhookHandler(secret=SECRET)
        raw = self._make_event("payment.completed")
        with pytest.raises(ValueError, match="inválida"):
            handler.dispatch(raw, "sha256=badhash")

    def test_handler_exception_does_not_propagate(self):
        handler = WebhookHandler(secret=SECRET)
        after = []

        @handler.on("payment.completed")
        def bad_handler(event):
            raise RuntimeError("boom")

        @handler.on("payment.completed")
        def good_handler(event):
            after.append("ran")

        raw = self._make_event("payment.completed")
        handler.dispatch(raw, _sign(raw))  # must not raise

        assert after == ["ran"]

    def test_wildcard_exception_does_not_propagate(self):
        handler = WebhookHandler(secret=SECRET)

        @handler.on("*")
        def bad_wildcard(event):
            raise RuntimeError("boom")

        raw = self._make_event("payment.completed")
        handler.dispatch(raw, _sign(raw))  # must not raise

    def test_event_data_passed_correctly(self):
        handler = WebhookHandler(secret=SECRET)
        captured = {}

        @handler.on("invoice.paid")
        def on_invoice(event):
            captured.update(event)

        payload = {"type": "invoice.paid", "data": {"id": "inv_42", "amount": 5000}}
        raw = json.dumps(payload).encode()
        handler.dispatch(raw, _sign(raw))

        assert captured["type"] == "invoice.paid"
        assert captured["data"]["amount"] == 5000

    def test_missing_type_field_uses_empty_string(self):
        handler = WebhookHandler(secret=SECRET)
        received = []

        @handler.on("")
        def on_empty(event):
            received.append(event)

        raw = json.dumps({"data": {}}).encode()
        handler.dispatch(raw, _sign(raw))

        assert len(received) == 1

    def test_rotation_window_accepted(self):
        handler = WebhookHandler(secret=SECRET)
        received = []

        @handler.on("payment.completed")
        def on_payment(event):
            received.append(event)

        raw = self._make_event("payment.completed")
        old_sig = _sign(raw, secret="expiring_secret")
        new_sig = _sign(raw)
        handler.dispatch(raw, f"{old_sig},{new_sig}")

        assert len(received) == 1
