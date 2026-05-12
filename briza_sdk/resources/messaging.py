from __future__ import annotations
from typing import Any, Dict, List, Optional
from .base import BaseResource


class _NumbersResource(BaseResource):
    def search(self, *, area_code: Optional[str] = None, number_type: str = "local", capabilities: Optional[List[str]] = None, **extra) -> Dict:
        body: Dict[str, Any] = {"numberType": number_type, **extra}
        if area_code:
            body["areaCode"] = area_code
        if capabilities:
            body["capabilities"] = capabilities
        return self._post("/v1/messaging/numbers/search", body)

    def buy(self, *, e164: str, capabilities: Optional[List[str]] = None, sms_inbound_webhook_url: Optional[str] = None, **extra) -> Dict:
        body: Dict[str, Any] = {"e164": e164, **extra}
        if capabilities:
            body["capabilities"] = capabilities
        if sms_inbound_webhook_url:
            body["smsInboundWebhookUrl"] = sms_inbound_webhook_url
        return self._post("/v1/messaging/numbers/buy", body)

    def list(self, *, status: Optional[str] = None, campaign_id: Optional[str] = None, provider: Optional[str] = None) -> Dict:
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if campaign_id:
            params["campaignId"] = campaign_id
        if provider:
            params["provider"] = provider
        return self._get("/v1/messaging/numbers", params or None)

    def get(self, number_id: str) -> Dict:
        return self._get(f"/v1/messaging/numbers/{number_id}")

    def update(self, number_id: str, **fields) -> Dict:
        return self._patch(f"/v1/messaging/numbers/{number_id}", fields)

    def release(self, number_id: str) -> Dict:
        return self._delete(f"/v1/messaging/numbers/{number_id}")


class _BrandsResource(BaseResource):
    def create(self, *, submit: bool = True, **fields) -> Dict:
        return self._post("/v1/messaging/brands", {"submit": submit, **fields})

    def list(self) -> Dict:
        return self._get("/v1/messaging/brands")

    def get(self, brand_id: str) -> Dict:
        return self._get(f"/v1/messaging/brands/{brand_id}")

    def update(self, brand_id: str, *, submit: bool = False, **fields) -> Dict:
        return self._patch(f"/v1/messaging/brands/{brand_id}", {"submit": submit, **fields})

    def refresh_status(self, brand_id: str) -> Dict:
        """Fuerza un sondeo al proveedor (máx 1/min/brand)."""
        return self._post(f"/v1/messaging/brands/{brand_id}/refresh-status")

    def sync(self, brand_id: str) -> Dict:
        """Reenvía un brand en draft/failed sin volver a ingresar datos."""
        return self._post(f"/v1/messaging/brands/{brand_id}/sync")


class _CampaignsResource(BaseResource):
    def create(self, **fields) -> Dict:
        """El brand debe estar en estado 'approved'."""
        return self._post("/v1/messaging/campaigns", fields)

    def list(self) -> Dict:
        return self._get("/v1/messaging/campaigns")

    def get(self, campaign_id: str) -> Dict:
        return self._get(f"/v1/messaging/campaigns/{campaign_id}")

    def update(self, campaign_id: str, **fields) -> Dict:
        return self._patch(f"/v1/messaging/campaigns/{campaign_id}", fields)

    def refresh_status(self, campaign_id: str) -> Dict:
        return self._post(f"/v1/messaging/campaigns/{campaign_id}/refresh-status")

    def attach_numbers(self, campaign_id: str, messaging_number_ids: List[str]) -> Dict:
        """Adjunta números en bulk. La campaña debe estar 'approved'."""
        return self._post(
            f"/v1/messaging/campaigns/{campaign_id}/numbers",
            {"messagingNumberIds": messaging_number_ids},
        )

    def detach_number(self, campaign_id: str, number_id: str) -> None:
        return self._delete(f"/v1/messaging/campaigns/{campaign_id}/numbers/{number_id}")


class _TollfreeVerificationsResource(BaseResource):
    def create(self, **fields) -> Dict:
        return self._post("/v1/messaging/tollfree-verifications", fields)

    def list(self) -> Dict:
        return self._get("/v1/messaging/tollfree-verifications")

    def get(self, tfv_id: str) -> Dict:
        return self._get(f"/v1/messaging/tollfree-verifications/{tfv_id}")

    def update(self, tfv_id: str, **fields) -> Dict:
        return self._patch(f"/v1/messaging/tollfree-verifications/{tfv_id}", fields)

    def refresh_status(self, tfv_id: str) -> Dict:
        return self._post(f"/v1/messaging/tollfree-verifications/{tfv_id}/refresh-status")


class MessagingResource(BaseResource):
    """
    Aprovisionamiento de mensajería: números, brands 10DLC, campañas, TFV, voz.

    Flujo típico::

        # 1. Buscar y comprar número
        results = briza.messaging.numbers.search(area_code="415")
        num = briza.messaging.numbers.buy(e164=results["results"][0]["e164"])

        # 2. Registrar brand → campaña → adjuntar número
        brand = briza.messaging.brands.create(legalName="Acme LLC", ...)
        briza.messaging.brands.refresh_status(brand["id"])  # sondear hasta 'approved'

        campaign = briza.messaging.campaigns.create(brandId=brand["id"], ...)
        briza.messaging.campaigns.refresh_status(campaign["id"])

        briza.messaging.campaigns.attach_numbers(campaign["id"], [num["id"]])

        # 3. Enviar SMS (a través de messages.send_sms)
        briza.messages.send_sms(to="+14155551234", body="Hola!")
    """

    def __init__(self, client):
        super().__init__(client)
        self.numbers = _NumbersResource(client)
        self.brands = _BrandsResource(client)
        self.campaigns = _CampaignsResource(client)
        self.tollfree_verifications = _TollfreeVerificationsResource(client)

    def get_usage(self) -> Dict:
        """Resumen de uso del mes actual para el merchant."""
        return self._get("/v1/messaging/usage")

    def update_settings(self, **fields) -> Dict:
        """
        Actualiza cap mensual y email de alertas.
        Cap ≤ 10,000 desde scope merchant; más requiere admin.
        """
        return self._patch("/v1/messaging/settings", fields)

    def get_fees(self) -> Dict:
        """Vista de solo lectura del programa de tarifas del ISV."""
        return self._get("/v1/messaging/fees")

    def get_tiers(self) -> Dict:
        """Lista de tiers configurados para el picker del merchant."""
        return self._get("/v1/messaging/tiers")

    def get_upcoming_charges(self) -> Dict:
        """Cargos pendientes para la próxima factura mensual."""
        return self._get("/v1/messaging/upcoming-charges")

    def get_failure_resolution(self, code: Optional[str] = None) -> Dict:
        """Traduce códigos de error de proveedores a pasos de remediación."""
        params = {"code": code} if code else None
        return self._get("/v1/messaging/failure-resolution", params)

    def place_call(self, *, from_number: str, to: str, twiml_url: str) -> Dict:
        """Realiza una llamada de voz saliente."""
        return self._post("/v1/messaging/voice/calls", {
            "from": from_number,
            "to": to,
            "twimlUrl": twiml_url,
        })
