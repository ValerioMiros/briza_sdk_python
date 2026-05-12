from __future__ import annotations
from typing import Any, Dict, List, Optional
from .base import BaseResource


# ──────────────────────────────────────────────
# Suscripciones a planes
# ──────────────────────────────────────────────

class SubscriptionsResource(BaseResource):
    """customer-subscriptions: suscripción de un cliente a un plan."""

    def list(self, *, customer_id: Optional[str] = None, plan_id: Optional[str] = None, status: Optional[str] = None) -> Dict:
        params: Dict[str, Any] = {}
        if customer_id:
            params["customer_id"] = customer_id
        if plan_id:
            params["plan_id"] = plan_id
        if status:
            params["status"] = status
        return self._get("/v1/customer-subscriptions", params or None)

    def get(self, subscription_id: str) -> Dict:
        return self._get(f"/v1/customer-subscriptions/{subscription_id}")

    def create(
        self,
        *,
        customer_id: str,
        plan_id: str,
        card_id: Optional[int] = None,
        payment_token: Optional[str] = None,
        charge_now: bool = True,
        items: Optional[List[Dict]] = None,
        billing_anchor: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
        **extra,
    ) -> Dict:
        """
        Suscribe a un cliente a un plan.

        Args:
            charge_now: Si True (defecto), cobra el primer ciclo al instante.
            items: Add-ons de una sola vez para el primer cobro.
            billing_anchor: ``{ mode, day, first_cycle, grace_days }``
                            para anclar el ciclo a un día del mes.
        """
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "plan_id": plan_id,
            "charge_now": charge_now,
            **extra,
        }
        if card_id is not None:
            body["card_id"] = card_id
        if payment_token:
            body["payment_token"] = payment_token
        if items:
            body["items"] = items
        if billing_anchor:
            body["billing_anchor"] = billing_anchor
        return self._post("/v1/customer-subscriptions", body, idempotency_key=idempotency_key)

    def update(self, subscription_id: str, **fields) -> Dict:
        return self._patch(f"/v1/customer-subscriptions/{subscription_id}", fields)

    def cancel(self, subscription_id: str) -> None:
        return self._delete(f"/v1/customer-subscriptions/{subscription_id}")


# ──────────────────────────────────────────────
# Recurrente simple (sin plan)
# ──────────────────────────────────────────────

class RecurringResource(BaseResource):
    def list(self, **params) -> Dict:
        return self._get("/v1/recurring", params or None)

    def get(self, recurring_id: str) -> Dict:
        return self._get(f"/v1/recurring/{recurring_id}")

    def create(
        self,
        *,
        customer_id: str,
        amount: int,
        frequency: str,
        next_billing_date: str,
        card_id: Optional[int] = None,
        total_cycles: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict:
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "frequency": frequency,
            "next_billing_date": next_billing_date,
        }
        if card_id is not None:
            body["card_id"] = card_id
        if total_cycles is not None:
            body["total_cycles"] = total_cycles
        return self._post("/v1/recurring", body, idempotency_key=idempotency_key)

    def update(self, recurring_id: str, **fields) -> Dict:
        return self._patch(f"/v1/recurring/{recurring_id}", fields)

    def delete(self, recurring_id: str) -> None:
        return self._delete(f"/v1/recurring/{recurring_id}")


# ──────────────────────────────────────────────
# Checkout sessions
# ──────────────────────────────────────────────

class CheckoutResource(BaseResource):
    def create_session(
        self,
        *,
        amount: int,
        reference: Optional[str] = None,
        customer_id: Optional[str] = None,
        save_card: bool = False,
        return_url: Optional[str] = None,
        line_items: Optional[List[Dict]] = None,
        payment_methods: Optional[List[str]] = None,
        pricing: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        skip_customer_info: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Dict:
        """
        Crea una sesión de checkout hosteado.
        Retorna ``{ id, url, ... }`` — redirige al cliente a ``url``.
        """
        body: Dict[str, Any] = {"amount": amount, "save_card": save_card}
        if reference:
            body["reference"] = reference
        if customer_id:
            body["customer_id"] = customer_id
        if return_url:
            body["return_url"] = return_url
        if line_items:
            body["line_items"] = line_items
        if payment_methods:
            body["payment_methods"] = payment_methods
        if pricing:
            body["pricing"] = pricing
        if metadata:
            body["metadata"] = metadata
        if skip_customer_info:
            body["skip_customer_info"] = True
        return self._post("/v1/checkout/sessions", body, idempotency_key=idempotency_key)

    def get_session(self, session_id: str) -> Dict:
        return self._get(f"/v1/checkout/sessions/{session_id}")


# ──────────────────────────────────────────────
# Productos
# ──────────────────────────────────────────────

class ProductsResource(BaseResource):
    def list(
        self,
        *,
        expand: Optional[str] = None,
        updated_since: Optional[str] = None,
        department_id: Optional[int] = None,
        enabled: Optional[bool] = None,
        search: Optional[str] = None,
        page_size: int = 100,
    ) -> Dict:
        params: Dict[str, Any] = {"pageSize": page_size}
        if expand:
            params["expand"] = expand
        if updated_since:
            params["updated_since"] = updated_since
        if department_id is not None:
            params["department_id"] = department_id
        if enabled is not None:
            params["enabled"] = enabled
        if search:
            params["search"] = search
        return self._get("/v1/products", params)

    def get(self, product_id: str, expand: Optional[str] = None) -> Dict:
        params = {"expand": expand} if expand else None
        return self._get(f"/v1/products/{product_id}", params)

    def create(self, **fields) -> Dict:
        return self._post("/v1/products", fields)

    def update(self, product_id: str, **fields) -> Dict:
        return self._patch(f"/v1/products/{product_id}", fields)

    def delete(self, product_id: str) -> None:
        return self._delete(f"/v1/products/{product_id}")

    # Variantes
    def list_variants(self, product_id: str) -> Dict:
        return self._get(f"/v1/products/{product_id}/variants")

    def create_variant(self, product_id: str, **fields) -> Dict:
        return self._post(f"/v1/products/{product_id}/variants", fields)

    def update_variant(self, product_id: str, variant_id: str, **fields) -> Dict:
        return self._patch(f"/v1/products/{product_id}/variants/{variant_id}", fields)

    def delete_variant(self, product_id: str, variant_id: str) -> None:
        return self._delete(f"/v1/products/{product_id}/variants/{variant_id}")


# ──────────────────────────────────────────────
# Catálogo auxiliar
# ──────────────────────────────────────────────

class CatalogResource(BaseResource):
    """Departments, categories, product-groups, mod-groups, modifiers, etc."""

    def get_all(self, updated_since: Optional[str] = None) -> Dict:
        params = {"updated_since": updated_since} if updated_since else None
        return self._get("/v1/catalog/all", params)

    def list(self, entity: str, updated_since: Optional[str] = None) -> Dict:
        params: Dict[str, Any] = {"entity": entity}
        if updated_since:
            params["updated_since"] = updated_since
        return self._get("/v1/catalog", params)

    def create(self, entity: str, **fields) -> Dict:
        return self._client.post("/v1/catalog", json=fields, params={"entity": entity})  # type: ignore[attr-defined]

    def update(self, entity: str, entity_id: str, **fields) -> Dict:
        return self._client.patch(f"/v1/catalog/{entity_id}", json=fields, params={"entity": entity})  # type: ignore[attr-defined]

    def delete(self, entity: str, entity_id: str) -> None:
        return self._client.delete(f"/v1/catalog/{entity_id}", params={"entity": entity})  # type: ignore[attr-defined]


# ──────────────────────────────────────────────
# Descuentos
# ──────────────────────────────────────────────

class DiscountsResource(BaseResource):
    def list(self, enabled: Optional[bool] = None) -> Dict:
        params = {"enabled": enabled} if enabled is not None else None
        return self._get("/v1/discounts", params)

    def get(self, discount_id: str) -> Dict:
        return self._get(f"/v1/discounts/{discount_id}")

    def create(self, **fields) -> Dict:
        return self._post("/v1/discounts", fields)

    def update(self, discount_id: str, **fields) -> Dict:
        return self._patch(f"/v1/discounts/{discount_id}", fields)

    def delete(self, discount_id: str) -> None:
        return self._delete(f"/v1/discounts/{discount_id}")


# ──────────────────────────────────────────────
# Planes de membresía
# ──────────────────────────────────────────────

class MembershipPlansResource(BaseResource):
    def list(self) -> Dict:
        return self._get("/v1/membership-plans")

    def get(self, plan_id: str) -> Dict:
        return self._get(f"/v1/membership-plans/{plan_id}")

    def create(
        self,
        *,
        name: str,
        price: int,
        billing_cycle: str,
        items: Optional[List[Dict]] = None,
        discount_percent: Optional[float] = None,
        duration_type: Optional[str] = None,
        duration_value: Optional[int] = None,
    ) -> Dict:
        body: Dict[str, Any] = {"name": name, "price": price, "billing_cycle": billing_cycle}
        if items:
            body["items"] = items
        if discount_percent is not None:
            body["discount_percent"] = discount_percent
        if duration_type:
            body["duration_type"] = duration_type
        if duration_value is not None:
            body["duration_value"] = duration_value
        return self._post("/v1/membership-plans", body)

    def update(self, plan_id: str, **fields) -> Dict:
        return self._patch(f"/v1/membership-plans/{plan_id}", fields)

    def delete(self, plan_id: str) -> None:
        return self._delete(f"/v1/membership-plans/{plan_id}")
