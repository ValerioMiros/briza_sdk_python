from __future__ import annotations
from typing import Any, Dict, List, Optional
from .base import BaseResource


class MessagesResource(BaseResource):
    """Envío de emails y SMS transaccionales (canal ya aprovisionado)."""

    def send_email(self, *, to: str, subject: str, html: str, text: Optional[str] = None, reply_to: Optional[str] = None) -> Dict:
        body: Dict[str, Any] = {"to": to, "subject": subject, "html": html}
        if text:
            body["text"] = text
        if reply_to:
            body["reply_to"] = reply_to
        return self._post("/v1/messages/email", body)

    def send_sms(self, *, to: str, body_text: str, from_number: Optional[str] = None, media_urls: Optional[List[str]] = None) -> Dict:
        """
        Envía un SMS.

        Errores comunes:
        - 409 messaging_not_approved → campaña no aprobada
        - 409 tollfree_not_verified  → TFV no aprobada
        - 402 quota_exceeded         → cap mensual alcanzado
        - 403 mms_disabled           → ISV tiene MMS desactivado
        """
        body: Dict[str, Any] = {"to": to, "body": body_text}
        if from_number:
            body["from"] = from_number
        if media_urls:
            body["mediaUrls"] = media_urls
        return self._post("/v1/messages/sms", body)


class TerminalsResource(BaseResource):
    """Terminales POS — pairing, bootstrap, rotación de secrets."""

    def list(self) -> Dict:
        return self._get("/v1/terminals")

    def get(self, terminal_id: str) -> Dict:
        return self._get(f"/v1/terminals/{terminal_id}")

    def update(self, terminal_id: str, **fields) -> Dict:
        return self._patch(f"/v1/terminals/{terminal_id}", fields)

    def delete(self, terminal_id: str) -> None:
        return self._delete(f"/v1/terminals/{terminal_id}")

    def mint_pair_code(self, *, suggested_name: Optional[str] = None, expires_in: int = 600) -> Dict:
        body: Dict[str, Any] = {"expires_in": expires_in}
        if suggested_name:
            body["suggested_name"] = suggested_name
        return self._post("/v1/terminals/pair-codes", body)

    def pair(self, *, code: str, name: str, device_info: Optional[Dict] = None) -> Dict:
        """
        Sin auth. Devuelve terminal + device_secret (guárdalo ya).
        """
        body: Dict[str, Any] = {"code": code, "name": name}
        if device_info:
            body["device_info"] = device_info
        # Llamada sin autenticación
        import requests
        resp = requests.post(
            self._client._url("/v1/terminals/pair"),
            json=body,
            timeout=self._client.timeout,
        )
        if not resp.ok:
            from briza_sdk.client import BrizaAPIError
            raise BrizaAPIError(resp.status_code, resp.json())
        return resp.json()

    def rotate(self, terminal_id: str) -> Dict:
        """Nuevo device_secret. El anterior deja de funcionar al instante."""
        return self._post(f"/v1/terminals/{terminal_id}/rotate")

    def reissue_pair_code(self, terminal_id: str) -> Dict:
        """Par-code ligado al terminal existente. Al redimirse rota el secret."""
        return self._post(f"/v1/terminals/{terminal_id}/pair-code")

    def bootstrap(self, updated_since: Optional[str] = None) -> Dict:
        """
        Endpoint de arranque del POS. Devuelve merchant, settings, catálogo,
        productos, descuentos, clientes y proveedores de pago en un solo call.
        """
        params = {"updated_since": updated_since} if updated_since else None
        return self._get("/v1/terminal/bootstrap", params)

    def get_realtime_token(self) -> Dict:
        return self._post("/v1/terminals/realtime-token")


class MerchantsResource(BaseResource):
    """Merchants, developers y grupos (admin / ISV)."""

    def list(self) -> Dict:
        return self._get("/v1/merchants")

    def get(self, merchant_id: str) -> Dict:
        return self._get(f"/v1/merchants/{merchant_id}")

    def create(self, **fields) -> Dict:
        return self._post("/v1/merchants", fields)

    def onboard(self, **fields) -> Dict:
        """Onboarding completo. ISV owner auto-asignado."""
        return self._post("/v1/merchants/onboard", fields)

    def update(self, merchant_id: str, **fields) -> Dict:
        return self._patch(f"/v1/merchants/{merchant_id}", fields)

    def get_accessible(self) -> Dict:
        return self._get("/v1/me/accessible-merchants")


class BatchesResource(BaseResource):
    """Lotes de transacciones para cierre de caja."""

    def list(self, status: Optional[str] = None) -> Dict:
        params = {"status": status} if status else None
        return self._get("/v1/batches", params)

    def get(self, batch_id: str) -> Dict:
        return self._get(f"/v1/batches/{batch_id}")

    def open(self) -> Dict:
        return self._post("/v1/batches")

    def close(self, batch_id: str) -> Dict:
        """Calcula totales desde las transacciones."""
        return self._post(f"/v1/batches/{batch_id}/close")

    def settle(self, batch_id: str) -> Dict:
        return self._post(f"/v1/batches/{batch_id}/settle")

    def get_processor_data(self, *, date: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
        """Solo Dejavoo. Extrae datos de liquidación directamente de iPOSpays."""
        params: Dict[str, Any] = {}
        if date:
            params["date"] = date
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/v1/batches/processor", params or None)


class ReportsResource(BaseResource):
    def get(self, *, from_date: str, to_date: str, merchant_id: Optional[str] = None) -> Dict:
        params: Dict[str, Any] = {"from": from_date, "to": to_date}
        if merchant_id:
            params["merchantId"] = merchant_id
        return self._get("/v1/reports", params)


class EventsResource(BaseResource):
    """API de eventos para backfill / replay."""

    def list(
        self,
        *,
        type: Optional[str] = None,
        resource_id: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        starting_after: Optional[str] = None,
        limit: int = 100,
    ) -> Dict:
        params: Dict[str, Any] = {"limit": limit}
        if type:
            params["type"] = type
        if resource_id:
            params["resource_id"] = resource_id
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if starting_after:
            params["starting_after"] = starting_after
        return self._get("/v1/events", params)

    def get(self, event_id: str) -> Dict:
        return self._get(f"/v1/events/{event_id}")

    def iter_all(self, **kwargs):
        """
        Generador que pagina automáticamente hasta agotar los eventos.

        Uso::
            for event in briza.events.iter_all(type="payment.completed", after="2026-01-01T00:00:00Z"):
                process(event)
        """
        cursor = None
        while True:
            if cursor:
                kwargs["starting_after"] = cursor
            page = self.list(**kwargs)
            for event in page.get("data", []):
                yield event
            if not page.get("has_more"):
                break
            cursor = page.get("next_cursor")


class DisputesResource(BaseResource):
    def list(self) -> Dict:
        return self._get("/v1/disputes")

    def get(self, dispute_id: str) -> Dict:
        return self._get(f"/v1/disputes/{dispute_id}")

    def submit_evidence(self, dispute_id: str, **evidence) -> Dict:
        return self._post(f"/v1/disputes/{dispute_id}/evidence", evidence)


class SettingsResource(BaseResource):
    def get(self) -> Dict:
        return self._get("/v1/settings")

    def update(self, **fields) -> Dict:
        """
        Actualización parcial. Si cambia cardMarkupPercent, recalcula
        automáticamente card_price en todos los productos.
        """
        return self._patch("/v1/settings", fields)
