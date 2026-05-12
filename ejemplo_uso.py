"""
ejemplo_uso.py — Demostración completa del SDK de BrizaPay en Python.

Configura las variables de entorno antes de ejecutar:
    export BRIZA_CLIENT_ID=brz_key_...
    export BRIZA_CLIENT_SECRET=tu_secret
    export BRIZA_WEBHOOK_SECRET=whsec_...

Ejecución:
    python ejemplo_uso.py
"""

import os
import uuid
from briza_sdk import BrizaClient, BrizaAPIError, WebhookHandler, verify_signature
from briza_sdk.webhooks import create_flask_app, create_fastapi_router

# ──────────────────────────────────────────────────────────────
# 1. Inicializar el cliente
# ──────────────────────────────────────────────────────────────

briza = BrizaClient(
    client_id=os.environ.get("BRIZA_CLIENT_ID", "brz_key_DEMO"),
    client_secret=os.environ.get("BRIZA_CLIENT_SECRET", "secret_DEMO"),
    # merchant_id="brz_mer_..."  # opcional: actúa en nombre de un merchant
)

print("=" * 60)
print("BrizaPay SDK — Ejemplo de uso")
print("=" * 60)

# ──────────────────────────────────────────────────────────────
# 2. Clientes
# ──────────────────────────────────────────────────────────────

print("\n[1] Crear cliente")
try:
    customer = briza.customers.create(
        first_name="María",
        last_name="López",
        email="maria@example.com",
        phone="+5215551234567",
        idempotency_key=f"cust-{uuid.uuid4()}",
    )
    print(f"    Cliente creado: {customer['id']}")
except BrizaAPIError as e:
    print(f"    Error: {e}")
    customer = {"id": "brz_cus_DEMO"}

print("\n[2] Listar clientes (búsqueda)")
try:
    result = briza.customers.list(search="María", page_size=5)
    print(f"    Encontrados: {result.get('total', '?')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 3. Cobros
# ──────────────────────────────────────────────────────────────

print("\n[3] Cobrar con tarjeta (CNP)")
try:
    txn = briza.payments.charge(
        amount=15000,                  # $150.00 en centavos
        idempotency_key=f"charge-{uuid.uuid4()}",
        payment_token="tok_demo_visa",
        customer_id=customer["id"],
        reference="orden-2026-001",
        save_card=True,
        metadata={"orden_id": "2026-001", "canal": "web"},
    )
    print(f"    Transacción: {txn.get('id')} — Estado: {txn.get('status')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")
    txn = {"id": "brz_txn_DEMO", "status": "approved"}

print("\n[4] Reembolso parcial")
try:
    refund = briza.payments.refund(txn["id"], amount=5000, reason="Descuento retroactivo")
    print(f"    Reembolso: {refund.get('id')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 4. Checkout hosteado
# ──────────────────────────────────────────────────────────────

print("\n[5] Crear sesión de checkout")
try:
    session = briza.checkout.create_session(
        amount=9999,
        customer_id=customer["id"],
        return_url="https://mitienda.com/gracias",
        line_items=[
            {"name": "Producto A", "quantity": 2, "unit_price": 4000},
            {"name": "Envío", "quantity": 1, "unit_price": 1999},
        ],
        metadata={"orden_id": "2026-002"},
        idempotency_key=f"sess-{uuid.uuid4()}",
    )
    print(f"    URL de pago: {session.get('url', '(no disponible en modo demo)')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 5. Facturación
# ──────────────────────────────────────────────────────────────

print("\n[6] Crear y enviar factura")
try:
    invoice = briza.invoices.create(
        customer_id=customer["id"],
        items=[
            {"name": "Renta unidad B-12", "quantity": 1, "unit_price": 12900},
        ],
        due_date="2026-06-01",
        auto_pay=True,
    )
    print(f"    Factura: {invoice.get('id')}")
    sent = briza.invoices.send(invoice["id"], email=True, sms=False)
    print(f"    Enviada: {sent}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 6. Suscripciones
# ──────────────────────────────────────────────────────────────

print("\n[7] Planes y suscripciones")
try:
    plan = briza.membership_plans.create(
        name="Renta Mensual Básica",
        price=12900,
        billing_cycle="monthly",
    )
    print(f"    Plan: {plan.get('id')}")

    sub = briza.subscriptions.create(
        customer_id=customer["id"],
        plan_id=plan["id"],
        payment_token="tok_demo_visa",
        charge_now=True,
        items=[{"name": "Cargo de inscripción", "quantity": 1, "unit_price": 2500}],
        billing_anchor={"mode": "calendar_day", "day": 1},
        idempotency_key=f"sub-{uuid.uuid4()}",
    )
    print(f"    Suscripción: {sub.get('id')} — Estado: {sub.get('status')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 7. Mensajería SMS
# ──────────────────────────────────────────────────────────────

print("\n[8] Enviar SMS")
try:
    sms = briza.messages.send_sms(
        to="+5215551234567",
        body_text="Hola María, tu renta de $129 vence el viernes. Responde STOP para cancelar.",
    )
    print(f"    SMS enviado: {sms.get('id')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 8. Productos y catálogo
# ──────────────────────────────────────────────────────────────

print("\n[9] Catálogo de productos")
try:
    catalog = briza.catalog.get_all()
    print(f"    Departamentos: {len(catalog.get('departments', []))}")
    print(f"    Productos: (se listan aparte)")

    products = briza.products.list(expand="department,category", page_size=5)
    print(f"    Productos listados: {len(products.get('data', []))}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 9. Webhooks
# ──────────────────────────────────────────────────────────────

print("\n[10] Registrar webhook")
try:
    hook = briza.webhooks.create(
        url="https://miapp.com/webhooks/briza",
        events=[
            "payment.completed",
            "payment.declined",
            "invoice.paid",
            "subscription.payment_failed",
            "messaging.brand.approved",
        ],
    )
    print(f"    Webhook: {hook.get('id')}")
    print(f"    ⚠️  Secret (guárdalo AHORA): {hook.get('secret', '(oculto en demo)')}")
except BrizaAPIError as e:
    print(f"    Error: {e}")

# ──────────────────────────────────────────────────────────────
# 10. Configurar servidor de webhooks
# ──────────────────────────────────────────────────────────────

print("\n[11] Configurar servidor de webhooks")

WEBHOOK_SECRET = os.environ.get("BRIZA_WEBHOOK_SECRET", "whsec_DEMO")
handler = WebhookHandler(secret=WEBHOOK_SECRET)

@handler.on("payment.completed")
def on_payment_completed(event):
    data = event["data"]
    print(f"  💳 Pago aprobado: {data.get('id')} por ${data.get('amount', 0)/100:.2f}")

@handler.on("payment.declined")
def on_payment_declined(event):
    data = event["data"]
    print(f"  ❌ Pago declinado: {data.get('id')}")

@handler.on("invoice.paid")
def on_invoice_paid(event):
    data = event["data"]
    print(f"  📄 Factura pagada: {data.get('id')}")

@handler.on("subscription.payment_failed")
def on_sub_failed(event):
    data = event["data"]
    print(f"  ⚠️  Fallo en suscripción: {data.get('subscription_id')}")

@handler.on("*")  # Catch-all
def on_any_event(event):
    print(f"  📨 Evento recibido: {event.get('type')}")

# Simular verificación de firma
import json, hmac as hmac_lib, hashlib
test_payload = json.dumps({"type": "payment.completed", "data": {"id": "brz_txn_TEST", "amount": 5000}}).encode()
sig = "sha256=" + hmac_lib.new(WEBHOOK_SECRET.encode(), test_payload, hashlib.sha256).hexdigest()
is_valid = verify_signature(test_payload, sig, WEBHOOK_SECRET)
print(f"    Firma de prueba válida: {is_valid}")

print("\n[12] Servidores disponibles:")
print("    Flask  → from briza_sdk.webhooks import create_flask_app")
print("             app = create_flask_app(handler); app.run(port=8080)")
print("    FastAPI→ from briza_sdk.webhooks import create_fastapi_router")
print("             app.include_router(create_fastapi_router(handler))")

# ──────────────────────────────────────────────────────────────
# 11. Backfill de eventos perdidos
# ──────────────────────────────────────────────────────────────

print("\n[13] Backfill de eventos (paginación automática)")
print("""
    # Recuperar todos los eventos de cobros aprobados desde enero:
    for event in briza.events.iter_all(
        type="payment.completed",
        after="2026-01-01T00:00:00Z",
    ):
        procesar(event)
""")

# ──────────────────────────────────────────────────────────────
# 12. Multi-merchant (ISV / admin)
# ──────────────────────────────────────────────────────────────

print("[14] Multi-merchant (ISV)")
print("""
    # Operar en nombre de un merchant específico:
    briza_merchant = briza.for_merchant("brz_mer_abc123")
    briza_merchant.payments.list()  # solo transacciones de ese merchant
    
    # O por request:
    briza.get("/v1/products", merchant_id="brz_mer_abc123")
""")

print("\n✅ Ejemplo completado.")
print("   Configura tus credenciales reales y ejecuta en modo test_mode=True.")
