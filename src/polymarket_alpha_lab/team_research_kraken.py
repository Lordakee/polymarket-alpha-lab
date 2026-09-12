"""Opt-in public Kraken OHLC reader; fixed origin, no auth or persistence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from polymarket_alpha_lab.team_research_agent_types import integer
from polymarket_alpha_lab.team_research_crypto_candles import CryptoCandleWindow
from polymarket_alpha_lab.team_research_kraken_candles import (
    MAX_KRAKEN_BYTES, KrakenCandleSnapshot, kraken_reference, kraken_window,
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True, slots=True)
class KrakenCandleReader:
    allow_public_fetch: bool = False
    timeout_seconds: int = 15

    def __post_init__(self) -> None:
        if type(self.allow_public_fetch) is not bool:
            raise ValueError("allow_public_fetch must be an exact bool")
        integer("timeout_seconds", self.timeout_seconds, 1, 60)

    def fetch(self, window: CryptoCandleWindow) -> KrakenCandleSnapshot:
        self.__post_init__()
        window = kraken_window(window)
        if self.allow_public_fetch is not True:
            raise ValueError("public Kraken fetch is disabled")
        if window.end > datetime.now(UTC):
            raise ValueError("candle window is not closed")
        endpoint = kraken_reference(window)
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
                raw = response.read(MAX_KRAKEN_BYTES + 1)
            return KrakenCandleSnapshot(window, datetime.now(UTC), raw)
        except HTTPError as error:
            error.close()
            raise ValueError("kraken_public_fetch_failed") from None
        except Exception:
            raise ValueError("kraken_public_fetch_failed") from None


__all__ = ("KrakenCandleReader",)
