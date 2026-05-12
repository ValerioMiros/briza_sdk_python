# briza-sdk — BrizaPay Gateway Python SDK

Official Python client for the [BrizaPay](https://brizapay.com) payment gateway (API version `2026-05-07.1`).

Supports payments, invoices, subscriptions, webhooks, terminals, multi-merchant, and more — with a single runtime dependency: `requests`.

---

## Installation

```bash
pip install briza-sdk
```

With optional webhook server helpers:

```bash
pip install "briza-sdk[flask]"
pip install "briza-sdk[fastapi]"
```

For development / testing:

```bash
pip install "briza-sdk[dev]"
```

---

## Authentication

BrizaPay supports three auth modes. Pick the one that matches your setup.

### Option 1 — OAuth client credentials (recommended for backends)

```python
from briza_sdk import BrizaClient

briza = BrizaClient(
    client_id="brz_key_...",
    client_secret="your_secret",
)
# Token is fetched and renewed automatically
```

### Option 2 — Static API key

```python
briza = BrizaClient(api_key="brz_secret_...")
```

### Option 3 — Terminal device secret

```python
briza = BrizaClient(device_secret="brz_term_sec_...")
```

---

## Quick start

```python
import uuid
from briza_sdk import BrizaClient, BrizaAPIError

briza = BrizaClient(client_id="brz_key_...", client_secret="...")

# Create a customer
customer = briza.customers.create(
    first_name="María",
    last_name="López",
    email="maria@example.com",
    phone="+5215551234567",
    idempotency_key=f"cust-{uuid.uuid4()}",
)

# Charge $150.00 (amounts are always integer centavos)
txn = briza.payments.charge(
    amount=15000,
    idempotency_key=f"charge-{uuid.uuid4()}",
    payment_token="tok_...",
    customer_id=customer["id"],
)

# IMPORTANT: always check status — 201 can be "approved", "declined", or "failed"
if txn["status"] != "approved":
    print("Payment not approved:", txn["status"])
```

---

## Webhooks

### Signature verification

```python
from briza_sdk.webhooks import verify_signature

# Flask example
@app.route("/webhooks/briza", methods=["POST"])
def briza_webhook():
    raw = request.get_data()
    if not verify_signature(raw, request.headers["X-Briza-Signature"], WEBHOOK_SECRET):
        abort(401)
    event = request.get_json(force=True)
    # process event...
    return "", 200
```

### Event dispatcher

```python
import os
from briza_sdk.webhooks import WebhookHandler

handler = WebhookHandler(secret=os.environ["BRIZA_WEBHOOK_SECRET"])

@handler.on("payment.completed")
def on_payment(event):
    print("Paid:", event["data"]["id"], event["data"]["amount"] / 100)

@handler.on("invoice.paid")
def on_invoice(event):
    print("Invoice paid:", event["data"]["id"])

@handler.on("*")  # catch-all
def on_any(event):
    print("Event:", event["type"])

# In your view — raises ValueError on bad signature
handler.dispatch(raw_body, signature_header)
```

### Ready-to-use Flask server

```python
from briza_sdk.webhooks import WebhookHandler, create_flask_app

handler = WebhookHandler(secret=os.environ["BRIZA_WEBHOOK_SECRET"])

@handler.on("payment.completed")
def on_payment(event):
    ...

app = create_flask_app(handler, path="/webhooks/briza")
app.run(port=8080)
```

### Ready-to-use FastAPI router

```python
from fastapi import FastAPI
from briza_sdk.webhooks import WebhookHandler, create_fastapi_router

handler = WebhookHandler(secret=os.environ["BRIZA_WEBHOOK_SECRET"])

@handler.on("payment.completed")
def on_payment(event):
    ...

app = FastAPI()
app.include_router(create_fastapi_router(handler, path="/webhooks/briza"))
```

---

## Multi-merchant (ISV / platform)

```python
# Scope a client to a specific merchant
briza_merchant = briza.for_merchant("brz_mer_abc123")
briza_merchant.payments.list()  # returns only that merchant's transactions

# Or pass merchant_id per-request
briza.payments.list(merchant_id="brz_mer_abc123")
```

---

## Other resources

```python
# Invoices
invoice = briza.invoices.create(
    customer_id=customer["id"],
    items=[{"name": "Monthly rent", "quantity": 1, "unit_price": 12900}],
    due_date="2026-06-01",
    auto_pay=True,
)
briza.invoices.send(invoice["id"], email=True)

# Subscriptions
plan = briza.membership_plans.create(name="Basic", price=12900, billing_cycle="monthly")
sub  = briza.subscriptions.create(
    customer_id=customer["id"],
    plan_id=plan["id"],
    payment_token="tok_...",
    idempotency_key=f"sub-{uuid.uuid4()}",
)

# SMS messaging
briza.messages.send_sms(to="+5215551234567", body_text="Your rent is due Friday.")

# Register a webhook endpoint
hook = briza.webhooks.create(
    url="https://yourapp.com/webhooks/briza",
    events=["payment.completed", "invoice.paid"],
)
print("Secret (save this now!):", hook["secret"])

# Paginate all events automatically
for event in briza.events.iter_all(type="payment.completed", after="2026-01-01T00:00:00Z"):
    process(event)
```

---

## Key conventions

| Convention | Detail |
|---|---|
| Amounts | Always integer **centavos** — `1500` = $15.00 |
| `idempotency_key` | Required on all write operations that move money. Use a UUID per request; valid for 24 h |
| Charge status | `"approved"`, `"declined"`, or `"failed"` — always check `response["status"]` |
| Webhook secret | Returned **once** at `webhooks.create()`. Capture from `response["secret"]` immediately |

---

## Testing

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run the test suite
pytest tests/ -v
```

The webhook tests are self-contained (no network calls, no credentials required).

---

## Error handling

```python
from briza_sdk import BrizaAPIError

try:
    txn = briza.payments.charge(amount=15000, idempotency_key="...", payment_token="tok_...")
except BrizaAPIError as e:
    print(e.status_code)   # HTTP status
    print(e.body)          # raw API error body
    print(e.request_id)    # Briza-Request-Id header for support
```

---

## Publishing

### Build distributables

```bash
pip install build
python -m build
# Produces: dist/briza_sdk-1.0.0.tar.gz  and  dist/briza_sdk-1.0.0-py3-none-any.whl
```

### Test on TestPyPI first

```bash
pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ briza-sdk

# Validate imports
python -c "from briza_sdk import BrizaClient; from briza_sdk.webhooks import verify_signature; print('OK')"
```

### Publish to PyPI

```bash
twine upload dist/*
```

You will be prompted for your PyPI credentials (or use `--username __token__` with an API token).

### Using a `.pypirc` file (recommended for CI)

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-...
```

---

## License

MIT — see [LICENSE](LICENSE).
