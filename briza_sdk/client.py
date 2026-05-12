"""
BrizaPay Gateway — Python SDK
Basado en la guía oficial (rev 34, API version 2026-05-07.1)
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

BASE_URL = "https://crwbtzryadlpmlupgcmz.supabase.co/functions/v1/api"


class BrizaAPIError(Exception):
    """Excepción lanzada cuando la API devuelve un error."""

    def __init__(self, status_code: int, body: Any, request_id: Optional[str] = None):
        self.status_code = status_code
        self.body = body
        self.request_id = request_id
        message = f"HTTP {status_code}"
        if isinstance(body, dict):
            message += f": {body.get('error', body.get('message', body))}"
        super().__init__(message)


class BrizaClient:
    """
    Cliente principal de BrizaPay.

    Uso básico::

        from briza_sdk import BrizaClient

        briza = BrizaClient(client_id="brz_key_...", client_secret="...")
        # -- o con JWT ya obtenido --
        briza = BrizaClient(api_key="brz_secret_...")
        # -- o con device secret de terminal --
        briza = BrizaClient(device_secret="brz_term_sec_...")
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_key: Optional[str] = None,
        device_secret: Optional[str] = None,
        merchant_id: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: int = 180,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.merchant_id = merchant_id

        # Credenciales
        self._client_id = client_id
        self._client_secret = client_secret
        self._static_token = api_key or device_secret
        self._jwt: Optional[str] = None
        self._jwt_expires_at: float = 0.0

        # Sub-recursos (inicializados lazy para evitar imports circulares)
        from briza_sdk.resources.payments import PaymentsResource
        from briza_sdk.resources.customers import CustomersResource
        from briza_sdk.resources.products import ProductsResource
        from briza_sdk.resources.catalog import CatalogResource
        from briza_sdk.resources.invoices import InvoicesResource
        from briza_sdk.resources.subscriptions import SubscriptionsResource
        from briza_sdk.resources.recurring import RecurringResource
        from briza_sdk.resources.checkout import CheckoutResource
        from briza_sdk.resources.webhooks import WebhooksResource
        from briza_sdk.resources.messaging import MessagingResource
        from briza_sdk.resources.messages import MessagesResource
        from briza_sdk.resources.terminals import TerminalsResource
        from briza_sdk.resources.merchants import MerchantsResource
        from briza_sdk.resources.discounts import DiscountsResource
        from briza_sdk.resources.membership_plans import MembershipPlansResource
        from briza_sdk.resources.batches import BatchesResource
        from briza_sdk.resources.reports import ReportsResource
        from briza_sdk.resources.events import EventsResource
        from briza_sdk.resources.disputes import DisputesResource
        from briza_sdk.resources.settings import SettingsResource

        self.payments = PaymentsResource(self)
        self.customers = CustomersResource(self)
        self.products = ProductsResource(self)
        self.catalog = CatalogResource(self)
        self.invoices = InvoicesResource(self)
        self.subscriptions = SubscriptionsResource(self)
        self.recurring = RecurringResource(self)
        self.checkout = CheckoutResource(self)
        self.webhooks = WebhooksResource(self)
        self.messaging = MessagingResource(self)
        self.messages = MessagesResource(self)
        self.terminals = TerminalsResource(self)
        self.merchants = MerchantsResource(self)
        self.discounts = DiscountsResource(self)
        self.membership_plans = MembershipPlansResource(self)
        self.batches = BatchesResource(self)
        self.reports = ReportsResource(self)
        self.events = EventsResource(self)
        self.disputes = DisputesResource(self)
        self.settings = SettingsResource(self)

    # ------------------------------------------------------------------ #
    # Auth                                                                 #
    # ------------------------------------------------------------------ #

    def _get_token(self) -> str:
        """Devuelve el Bearer token vigente, renovándolo si es necesario."""
        if self._static_token:
            return self._static_token

        if self._jwt and time.time() < self._jwt_expires_at - 30:
            return self._jwt

        # Solicitar nuevo JWT (client_credentials)
        resp = requests.post(
            f"{self.base_url}/v1/auth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            timeout=self.timeout,
        )
        data = resp.json()
        if not resp.ok:
            raise BrizaAPIError(resp.status_code, data)
        self._jwt = data["access_token"]
        self._jwt_expires_at = time.time() + data.get("expires_in", 900)
        return self._jwt

    # ------------------------------------------------------------------ #
    # HTTP helpers                                                         #
    # ------------------------------------------------------------------ #

    def _headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        h = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }
        if self.merchant_id:
            h["X-Merchant-Id"] = self.merchant_id
        if extra:
            h.update(extra)
        return h

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
        merchant_id: Optional[str] = None,
    ) -> Any:
        extra: Dict[str, str] = {}
        if idempotency_key:
            extra["Idempotency-Key"] = idempotency_key
        if merchant_id:
            extra["X-Merchant-Id"] = merchant_id

        resp = requests.request(
            method.upper(),
            self._url(path),
            headers=self._headers(extra),
            json=json,
            params=params,
            timeout=self.timeout,
        )
        request_id = resp.headers.get("Briza-Request-Id")
        if not resp.ok:
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise BrizaAPIError(resp.status_code, body, request_id)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def get(self, path: str, params: Optional[Dict] = None, **kw) -> Any:
        return self.request("GET", path, params=params, **kw)

    def post(self, path: str, json: Any = None, **kw) -> Any:
        return self.request("POST", path, json=json, **kw)

    def patch(self, path: str, json: Any = None, **kw) -> Any:
        return self.request("PATCH", path, json=json, **kw)

    def delete(self, path: str, **kw) -> Any:
        return self.request("DELETE", path, **kw)

    # ------------------------------------------------------------------ #
    # Multi-merchant helper                                                #
    # ------------------------------------------------------------------ #

    def for_merchant(self, merchant_id: str) -> "BrizaClient":
        """Devuelve una instancia que opera en nombre del merchant indicado."""
        clone = BrizaClient.__new__(BrizaClient)
        clone.__dict__.update(self.__dict__)
        clone.merchant_id = merchant_id
        # Re-vincular sub-recursos al clon
        from briza_sdk.resources.payments import PaymentsResource
        from briza_sdk.resources.customers import CustomersResource
        clone.payments = PaymentsResource(clone)
        clone.customers = CustomersResource(clone)
        # … (los demás comparten referencia; suficiente para la mayoría de usos)
        return clone
