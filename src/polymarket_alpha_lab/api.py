"""Read-only public API access for Polymarket research data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen


JsonValue = dict[str, Any] | list[Any]


class JsonTransport(Protocol):
    def get_json(self, url: str, *, timeout: float) -> JsonValue:
        """Return decoded JSON for a GET request."""


@dataclass(frozen=True)
class UrlopenTransport:
    user_agent: str = "polymarket-alpha-lab/0.1"

    def get_json(self, url: str, *, timeout: float) -> JsonValue:
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))


@dataclass(frozen=True)
class PolymarketPublicClient:
    transport: JsonTransport = UrlopenTransport()
    timeout_seconds: float = 15.0
    gamma_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"
    data_base_url: str = "https://data-api.polymarket.com"

    def list_markets(
        self, *, active: bool = True, closed: bool = False, limit: int = 100
    ) -> JsonValue:
        return self._get(
            self.gamma_base_url,
            "/markets",
            {"active": active, "closed": closed, "limit": limit},
        )

    def get_order_book(self, *, token_id: str) -> JsonValue:
        return self._get(self.clob_base_url, "/book", {"token_id": token_id})

    def _get(self, base_url: str, path: str, query: dict[str, object]) -> JsonValue:
        encoded_query = urlencode(
            {
                key: _encode_query_value(value)
                for key, value in query.items()
                if value is not None
            }
        )
        url = f"{base_url}{path}"
        if encoded_query:
            url = f"{url}?{encoded_query}"
        return self.transport.get_json(url, timeout=self.timeout_seconds)


def _encode_query_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
