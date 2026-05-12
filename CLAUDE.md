# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

BrizaPay Gateway Python SDK. Wraps the BrizaPay REST API (v2026-05-07.1, hosted on Supabase Edge Functions). Only runtime dependency is `requests`.

Install: `pip install requests` (optionally `flask` or `fastapi` for the webhook server helpers).

Run the usage example: `python ejemplo_uso.py` (set env vars first: `BRIZA_CLIENT_ID`, `BRIZA_CLIENT_SECRET`, `BRIZA_WEBHOOK_SECRET`).

There are no tests and no linting configured.

## Architecture

```
BrizaClient (client.py)
    ├── 20 resource attributes (payments, customers, invoices, subscriptions, …)
    ├── _get_token()   — JWT client_credentials flow (auto-renewing) or static api_key/device_secret
    └── request()      — single HTTP dispatch with auth headers

BaseResource (resources/base.py)
    └── thin wrappers: _get, _post, _patch, _delete → delegate to BrizaClient.request()

briza_sdk/webhooks/__init__.py
    ├── verify_signature()   — HMAC-SHA256 on raw bytes
    ├── WebhookHandler       — decorator-based event dispatcher
    ├── create_flask_app()   — ready-to-use Flask app
    └── create_fastapi_router() — ready-to-use FastAPI router
```

### Resource file layout (non-obvious)

Most resource classes live in two "mega" files regardless of their named `.py` stub:

- `resources/subscriptions.py` — also contains `RecurringResource`, `CheckoutResource`, `ProductsResource`, `CatalogResource`, `DiscountsResource`, `MembershipPlansResource`
- `resources/messages.py` — also contains `TerminalsResource`, `MerchantsResource`, `BatchesResource`, `ReportsResource`, `EventsResource`, `DisputesResource`, `SettingsResource`

The individual stub files (e.g. `catalog.py`, `events.py`) are thin re-exports. When editing a resource, find it in `subscriptions.py` or `messages.py`, not its stub.

## Key conventions

- **Amounts are always integer centavos** (e.g. `1500` = $15.00).
- **`idempotency_key` is required** on all write operations that create money movement (charge, create customer, create subscription, etc.). Use a UUID per request; keys are valid for 24 h.
- **`status` on a `charge()` 201 can be `"approved"`, `"declined"`, or `"failed"`** — always check `response["status"]`, don't assume approval.
- **Auth modes** — `BrizaClient` accepts three credential combinations:
  - `client_id` + `client_secret` → JWT via `POST /v1/auth/token` (auto-renewed, 30 s buffer)
  - `api_key` → static Bearer token
  - `device_secret` → terminal static Bearer token
- **Multi-merchant** — use `briza.for_merchant("brz_mer_...")` to get a cloned client scoped to that merchant, or pass `merchant_id=` per-request to `BrizaClient.request()`.
- **Webhook secret** — only returned once on `webhooks.create()`. Capture it immediately from `response["secret"]`.
- **Event backfill** — `briza.events.iter_all(**filters)` is a generator that auto-paginates using `next_cursor` / `has_more`.
- **Terminal pairing** — `terminals.pair()` bypasses auth and calls the API directly (no Bearer token), since the terminal doesn't have credentials yet.
