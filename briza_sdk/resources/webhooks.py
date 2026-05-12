from __future__ import annotations
from typing import Any, Dict, List, Optional
from .base import BaseResource


class WebhooksResource(BaseResource):
    """Registro, gestión y verificación de webhooks."""

    def list(self, merchant_id: Optional[str] = None) -> Dict:
        params = {"merchantId": merchant_id} if merchant_id else None
        return self._get("/v1/webhooks", params)

    def create(self, *, url: str, events: List[str]) -> Dict:
        """
        Registra un endpoint.

        ⚠️ El campo ``secret`` solo aparece en esta respuesta.
        Guárdalo inmediatamente — no se puede recuperar después.
        """
        return self._post("/v1/webhooks", {"url": url, "events": events})

    def update(self, webhook_id: str, *, url: Optional[str] = None, events: Optional[List[str]] = None, is_active: Optional[bool] = None) -> Dict:
        body: Dict[str, Any] = {}
        if url:
            body["url"] = url
        if events is not None:
            body["events"] = events
        if is_active is not None:
            body["isActive"] = is_active
        return self._patch(f"/v1/webhooks/{webhook_id}", body)

    def delete(self, webhook_id: str) -> None:
        return self._delete(f"/v1/webhooks/{webhook_id}")

    def test(self, webhook_id: str) -> Dict:
        """Dispara un evento sintético webhook.test."""
        return self._post(f"/v1/webhooks/{webhook_id}/test")

    def rotate_secret(self, webhook_id: str, *, overlap_hours: Optional[int] = None) -> Dict:
        """
        Rota el secret. Devuelve old_secret + new_secret.
        Ambos son válidos durante overlap_hours.
        """
        body: Dict[str, Any] = {}
        if overlap_hours is not None:
            body["overlap_hours"] = overlap_hours
        return self._post(f"/v1/webhooks/{webhook_id}/rotate-secret", body or None)

    def list_deliveries(self, webhook_id: str) -> Dict:
        return self._get(f"/v1/webhooks/{webhook_id}/deliveries")

    def retry_delivery(self, webhook_id: str, delivery_id: str) -> Dict:
        return self._post(f"/v1/webhooks/{webhook_id}/deliveries/{delivery_id}/retry")
