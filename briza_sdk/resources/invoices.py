from __future__ import annotations
from typing import Any, Dict, List, Optional
from .base import BaseResource


class InvoicesResource(BaseResource):
    """Facturas / invoices."""

    def list(self, *, status: Optional[str] = None, customer_id: Optional[str] = None) -> Dict:
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if customer_id:
            params["customer_id"] = customer_id
        return self._get("/v1/invoices", params or None)

    def get(self, invoice_id: str) -> Dict:
        return self._get(f"/v1/invoices/{invoice_id}")

    def create(
        self,
        *,
        customer_id: str,
        items: List[Dict],
        due_date: Optional[str] = None,
        auto_pay: bool = False,
        allow_partial: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Dict:
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "items": items,
            "auto_pay": auto_pay,
            "allow_partial": allow_partial,
        }
        if due_date:
            body["due_date"] = due_date
        return self._post("/v1/invoices", body, idempotency_key=idempotency_key)

    def update(self, invoice_id: str, **fields) -> Dict:
        """Solo borradores aceptan todos los campos; enviadas solo status/auto_pay."""
        return self._patch(f"/v1/invoices/{invoice_id}", fields)

    def delete(self, invoice_id: str) -> None:
        """Solo borradores."""
        return self._delete(f"/v1/invoices/{invoice_id}")

    def send(
        self,
        invoice_id: str,
        *,
        email: bool = True,
        sms: bool = False,
    ) -> Dict:
        """Envía la factura por email y/o SMS. Emite invoice.sent."""
        return self._post(
            f"/v1/invoices/{invoice_id}/send",
            {"channels": {"email": email, "sms": sms}},
        )

    def pay(self, invoice_id: str, *, card_id: Optional[int] = None) -> Dict:
        """
        Cobra la factura ahora contra una tarjeta guardada.
        Emite payment.completed + invoice.paid.
        """
        body: Dict[str, Any] = {}
        if card_id is not None:
            body["card_id"] = card_id
        return self._post(f"/v1/invoices/{invoice_id}/pay", body or None)

    def test_email(self) -> Dict:
        """Envía una factura de muestra con el branding actual."""
        return self._post("/v1/invoices/test-email")
