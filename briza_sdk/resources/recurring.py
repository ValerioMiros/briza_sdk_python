"""
Recursos restantes — Recurring, Checkout, Products, Catalog, Discounts,
MembershipPlans — re-exportados desde subscriptions.py para mantener un
import limpio en client.py.
"""
from .subscriptions import (
    RecurringResource,
    CheckoutResource,
    ProductsResource,
    CatalogResource,
    DiscountsResource,
    MembershipPlansResource,
)

__all__ = [
    "RecurringResource",
    "CheckoutResource",
    "ProductsResource",
    "CatalogResource",
    "DiscountsResource",
    "MembershipPlansResource",
]
