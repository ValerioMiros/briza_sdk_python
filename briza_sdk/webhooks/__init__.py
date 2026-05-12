"""
briza_sdk.webhooks — Servidor de webhooks y verificación de firmas.

Incluye:
- ``verify_signature(raw_body, header, secret)`` — verificación HMAC-SHA256
- ``WebhookHandler`` — despachador de eventos con decoradores
- ``create_flask_app()`` — servidor Flask listo para usar
- ``create_fastapi_router()`` — router FastAPI listo para usar
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Verificación de firma
# ──────────────────────────────────────────────

def verify_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Verifica la firma HMAC-SHA256 de BrizaPay.

    Args:
        raw_body: Cuerpo crudo de la solicitud HTTP (bytes).
        signature_header: Valor del header ``X-Briza-Signature``
                          (ej. "sha256=abc123" o múltiples separados por coma
                          durante ventana de rotación).
        secret: El webhook secret guardado al crear el endpoint.

    Returns:
        True si al menos una firma en el header es válida.

    Ejemplo::

        # Flask
        is_valid = verify_signature(
            request.get_data(),
            request.headers["X-Briza-Signature"],
            WEBHOOK_SECRET,
        )
        if not is_valid:
            abort(401)
    """
    computed = "sha256=" + hmac.new(
        secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()

    signatures = [s.strip() for s in signature_header.split(",")]
    return any(
        len(sig) == len(computed) and hmac.compare_digest(sig, computed)
        for sig in signatures
    )


# ──────────────────────────────────────────────
# Despachador de eventos
# ──────────────────────────────────────────────

class WebhookHandler:
    """
    Despachador de eventos con decoradores tipo Flask.

    Uso::

        handler = WebhookHandler(secret=WEBHOOK_SECRET)

        @handler.on("payment.completed")
        def on_payment(event):
            print("Cobro aprobado:", event["data"]["id"])

        @handler.on("invoice.paid")
        def on_invoice(event):
            print("Factura pagada:", event["data"]["id"])

        # En tu vista:
        handler.dispatch(raw_body, signature_header)
    """

    def __init__(self, secret: str):
        self.secret = secret
        self._handlers: Dict[str, List[Callable]] = {}

    def on(self, event_type: str):
        """Decorador para registrar un handler para un tipo de evento."""
        def decorator(fn: Callable) -> Callable:
            self._handlers.setdefault(event_type, []).append(fn)
            return fn
        return decorator

    def dispatch(self, raw_body: bytes, signature_header: str) -> None:
        """
        Verifica la firma y llama a los handlers registrados.

        Lanza ``ValueError`` si la firma es inválida.
        """
        if not verify_signature(raw_body, signature_header, self.secret):
            raise ValueError("Firma de webhook inválida")

        event = json.loads(raw_body)
        event_type = event.get("type", "")

        for fn in self._handlers.get(event_type, []):
            try:
                fn(event)
            except Exception:
                logger.exception("Error en handler de %s", event_type)

        for fn in self._handlers.get("*", []):
            try:
                fn(event)
            except Exception:
                logger.exception("Error en handler wildcard para %s", event_type)


# ──────────────────────────────────────────────
# Servidor Flask
# ──────────────────────────────────────────────

def create_flask_app(handler: WebhookHandler, path: str = "/webhooks/briza"):
    """
    Crea una app Flask lista para recibir webhooks de BrizaPay.

    Requiere: ``pip install flask``

    Uso::

        handler = WebhookHandler(secret=os.environ["BRIZA_WEBHOOK_SECRET"])

        @handler.on("payment.completed")
        def on_payment(event):
            print(event)

        app = create_flask_app(handler)
        app.run(port=8080)
    """
    try:
        from flask import Flask, request, jsonify, abort
    except ImportError:
        raise ImportError("Instala Flask: pip install flask")

    app = Flask(__name__)

    @app.route(path, methods=["POST"])
    def webhook_endpoint():
        raw = request.get_data()
        sig = request.headers.get("X-Briza-Signature", "")
        try:
            handler.dispatch(raw, sig)
        except ValueError as e:
            logger.warning("Webhook rechazado: %s", e)
            abort(401)
        return jsonify({"ok": True}), 200

    return app


# ──────────────────────────────────────────────
# Router FastAPI
# ──────────────────────────────────────────────

def create_fastapi_router(handler: WebhookHandler, path: str = "/webhooks/briza"):
    """
    Crea un APIRouter de FastAPI listo para recibir webhooks de BrizaPay.

    Requiere: ``pip install fastapi``

    Uso::

        from fastapi import FastAPI
        from briza_sdk.webhooks import WebhookHandler, create_fastapi_router

        handler = WebhookHandler(secret=os.environ["BRIZA_WEBHOOK_SECRET"])

        @handler.on("payment.completed")
        def on_payment(event):
            print(event)

        app = FastAPI()
        app.include_router(create_fastapi_router(handler))
    """
    try:
        from fastapi import APIRouter, Request, HTTPException
        from fastapi.responses import JSONResponse
    except ImportError:
        raise ImportError("Instala FastAPI: pip install fastapi")

    router = APIRouter()

    @router.post(path)
    async def webhook_endpoint(request: Request):
        raw = await request.body()
        sig = request.headers.get("x-briza-signature", "")
        try:
            handler.dispatch(raw, sig)
        except ValueError as e:
            logger.warning("Webhook rechazado: %s", e)
            raise HTTPException(status_code=401, detail="Firma inválida")
        return JSONResponse({"ok": True})

    return router
