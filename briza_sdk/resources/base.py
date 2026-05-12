from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from briza_sdk.client import BrizaClient


class BaseResource:
    def __init__(self, client: "BrizaClient"):
        self._client = client

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        return self._client.get(path, params=params)

    def _post(self, path: str, body: Any = None, *, idempotency_key: Optional[str] = None) -> Any:
        return self._client.post(path, json=body, idempotency_key=idempotency_key)

    def _patch(self, path: str, body: Any = None) -> Any:
        return self._client.patch(path, json=body)

    def _delete(self, path: str) -> Any:
        return self._client.delete(path)
