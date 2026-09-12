"""Opt-in fixed-origin public Coinbase candle GET; no credentials or writes."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from polymarket_alpha_lab.team_research_agent_types import integer
from polymarket_alpha_lab.team_research_crypto_candles import (
    MAX_CANDLE_BYTES, CoinbaseCandleSnapshot, CryptoCandleWindow,
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True, slots=True)
class CoinbaseCandleReader:
    allow_public_fetch: bool = False
    timeout_seconds: int = 15

    def __post_init__(self) -> None:
        if type(self.allow_public_fetch) is not bool:
            raise ValueError("allow_public_fetch must be an exact bool")
        integer("timeout_seconds", self.timeout_seconds, 1, 60)

    def fetch(self, window: CryptoCandleWindow) -> CoinbaseCandleSnapshot:
        """One bounded, uncredentialed GET; raw bytes are untrusted until intake.

        Historical endpoint: do not poll frequently. No pagination or retries.
        Timeout applies to blocking operations, not an absolute run deadline.
        """
        self.__post_init__()
        if type(window) is not CryptoCandleWindow:
            raise ValueError("expected exact candle window")
        window = replace(window)
        if self.allow_public_fetch is not True:
            raise ValueError("public Coinbase fetch is disabled")
        if window.end > datetime.now(UTC):
            raise ValueError("candle window is not closed")
        endpoint = window.source_reference
        try:
            request = Request(endpoint, method="GET", headers={
                "Accept": "application/json", "User-Agent": "polymarket-alpha-lab/0.1",
            })
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(request, timeout=self.timeout_seconds) as response:
                if response.geturl() != endpoint or response.status != 200:
                    raise ValueError("unexpected response origin or status")
                if response.headers.get_content_type() != "application/json":
                    raise ValueError("expected JSON response")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise ValueError("encoded response is not supported")
                raw = response.read(MAX_CANDLE_BYTES + 1)
            return CoinbaseCandleSnapshot(window, datetime.now(UTC), raw)
        except HTTPError as error:
            error.close()
            raise ValueError("coinbase_public_fetch_failed") from None
        except Exception:
            raise ValueError("coinbase_public_fetch_failed") from None


__all__ = ("CoinbaseCandleReader",)
