from __future__ import annotations
from typing import Any, Dict, Optional
from .base import BaseResource


class CustomersResource(BaseResource):
    """Clientes y sus tarjetas guardadas."""

    def list(self, *, search: Optional[str] = None, status: Optional[str] = None, page_size: int = 50, page: int = 1) -> Dict:
        params: Dict[str, Any] = {"pageSize": page_size, "page": page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        return self._get("/v1/customers", params)

    def get(self, customer_id: str) -> Dict:
        """Incluye cards_count y total_spent."""
        return self._get(f"/v1/customers/{customer_id}")

    def create(
        self,
        *,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
        **extra,
    ) -> Dict:
        body: Dict[str, Any] = {"first_name": first_name, "last_name": last_name, **extra}
        if email:
            body["email"] = email
        if phone:
            body["phone"] = phone
        if address:
            body.update(address)
        return self._post("/v1/customers", body, idempotency_key=idempotency_key)

    def update(self, customer_id: str, **fields) -> Dict:
        return self._patch(f"/v1/customers/{customer_id}", fields)

    def delete(self, customer_id: str) -> None:
        """Soft-delete: cancela suscripciones, pausa recurrentes."""
        return self._delete(f"/v1/customers/{customer_id}")

    # -- Tarjetas --

    def list_cards(self, customer_id: str) -> Dict:
        return self._get(f"/v1/customers/{customer_id}/cards")

    def add_card(self, customer_id: str, *, payment_token: str, **extra) -> Dict:
        """
        Guarda una tarjeta manualmente.
        Retorna 201 si es nueva, 200 si ya existía (por token o fingerprint).
        """
        return self._post(f"/v1/customers/{customer_id}/cards", {"payment_token": payment_token, **extra})

    def delete_card(self, customer_id: str, card_id: int) -> None:
        return self._delete(f"/v1/customers/{customer_id}/cards/{card_id}")

    # -- Historial --

    def list_transactions(self, customer_id: str, **params) -> Dict:
        return self._get(f"/v1/customers/{customer_id}/transactions", params or None)

    def list_subscriptions(self, customer_id: str) -> Dict:
        return self._get(f"/v1/customers/{customer_id}/subscriptions")

    # -- Portal self-serve --

    def create_portal_session(
        self,
        customer_id: str,
        *,
        return_url: str,
        expires_in: int = 3600,
    ) -> Dict:
        """Genera una URL firmada para que el cliente gestione su cuenta."""
        return self._post(
            f"/v1/customers/{customer_id}/portal-sessions",
            {"return_url": return_url, "expires_in": expires_in},
        )
