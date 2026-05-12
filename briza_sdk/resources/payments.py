from __future__ import annotations
from typing import Any, Dict, List, Optional
from .base import BaseResource


class PaymentsResource(BaseResource):
    """
    Cobros, reembolsos, anulaciones y recibos.

    Documentación: secciones 4.1–4.3 de la guía BrizaPay.
    """

    def charge(
        self,
        *,
        amount: int,
        idempotency_key: str,
        mode: str = "cnp",
        payment_token: Optional[str] = None,
        card_id: Optional[int] = None,
        customer_id: Optional[str] = None,
        reference: Optional[str] = None,
        metadata: Optional[Dict] = None,
        save_card: bool = False,
        tip: Optional[int] = None,
        terminal_id: Optional[str] = None,
        **extra,
    ) -> Dict:
        """
        Crea un cobro.

        Args:
            amount: Total en centavos (ej. 1500 = $15.00).
            idempotency_key: Requerido. Clave única para idempotencia (24 h).
            mode: "cnp" (card-not-present) | "cp" (card-present, terminal).
            payment_token: Token de tarjeta para CNP.
            card_id: ID de tarjeta guardada.
            customer_id: ID del cliente.
            reference: Referencia interna.
            save_card: Si True, guarda la tarjeta al cliente.
            tip: Propina en centavos (solo CP).
            terminal_id: ID del terminal (solo CP).

        Returns:
            Objeto de transacción con campos status, id, etc.

        Notas:
            - ``status`` en un 201 puede ser "approved", "declined", "failed" o
              "canceled" (solo CP). Siempre verifica ``response.status``.
            - Para CP el timeout puede ser hasta 180 s.
        """
        body: Dict[str, Any] = {"amount": amount, "mode": mode, **extra}
        if payment_token:
            body["payment_token"] = payment_token
        if card_id is not None:
            body["card_id"] = card_id
        if customer_id:
            body["customer_id"] = customer_id
        if reference:
            body["reference"] = reference
        if metadata:
            body["metadata"] = metadata
        if save_card:
            body["save_card"] = True
        if tip is not None:
            body["tip"] = tip
        if terminal_id:
            body["terminal_id"] = terminal_id
        return self._post("/v1/payments", body, idempotency_key=idempotency_key)

    def get(self, transaction_id: str) -> Dict:
        """Obtiene una transacción por ID."""
        return self._get(f"/v1/payments/{transaction_id}")

    def list(
        self,
        *,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page_size: int = 50,
        page: int = 1,
    ) -> Dict:
        """Lista transacciones con filtros opcionales."""
        params: Dict[str, Any] = {"pageSize": page_size, "page": page}
        if customer_id:
            params["customer_id"] = customer_id
        if status:
            params["status"] = status
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/v1/payments", params)

    def void(self, transaction_id: str) -> Dict:
        """Anula una transacción autorizada (antes de que se liquide)."""
        return self._post(f"/v1/payments/{transaction_id}/void")

    def refund(
        self,
        transaction_id: str,
        *,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> Dict:
        """
        Reembolsa total o parcialmente una transacción.

        Args:
            amount: Monto en centavos. Si se omite → reembolso total.
            subscription_id: Para reembolso de una línea de bundle.
        """
        body: Dict[str, Any] = {}
        if amount is not None:
            body["amount"] = amount
        if reason:
            body["reason"] = reason
        if subscription_id:
            body["subscription_id"] = subscription_id
        return self._post(f"/v1/payments/{transaction_id}/refund", body)

    def send_receipt(
        self,
        transaction_id: str,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Dict:
        """Envía el recibo de una transacción por email y/o SMS."""
        body: Dict[str, Any] = {}
        if email:
            body["email"] = email
        if phone:
            body["phone"] = phone
        return self._post(f"/v1/payments/{transaction_id}/receipt", body)

    def authorize(
        self,
        *,
        amount: int,
        idempotency_key: str,
        payment_token: Optional[str] = None,
        card_id: Optional[int] = None,
        customer_id: Optional[str] = None,
        **extra,
    ) -> Dict:
        """Auth-Only: reserva fondos sin capturar. Capture con capture()."""
        body: Dict[str, Any] = {
            "amount": amount,
            "mode": "cnp",
            "capture": False,
            **extra,
        }
        if payment_token:
            body["payment_token"] = payment_token
        if card_id is not None:
            body["card_id"] = card_id
        if customer_id:
            body["customer_id"] = customer_id
        return self._post("/v1/payments", body, idempotency_key=idempotency_key)

    def capture(self, transaction_id: str, *, amount: Optional[int] = None) -> Dict:
        """Captura una autorización previa."""
        body: Dict[str, Any] = {}
        if amount is not None:
            body["amount"] = amount
        return self._post(f"/v1/payments/{transaction_id}/capture", body or None)
