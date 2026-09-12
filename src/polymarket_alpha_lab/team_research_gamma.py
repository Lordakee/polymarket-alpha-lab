"""Opt-in fixed-origin Gamma market context reader. No model calls or writes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from polymarket_alpha_lab.team_research_agent_types import integer
from polymarket_alpha_lab.team_research_intake import (
    GAMMA_MARKET_PREFIX, MAX_GAMMA_RESPONSE_BYTES, GammaMarketSnapshot, require_market_slug,
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True, slots=True)
class GammaResearchReader:
    allow_public_fetch: bool = False
    timeout_seconds: int = 15

    def __post_init__(self) -> None:
        if type(self.allow_public_fetch) is not bool:
            raise ValueError("allow_public_fetch must be an exact bool")
        integer("timeout_seconds", self.timeout_seconds, 1, 60)

    def fetch(self, *, market_slug: str) -> GammaMarketSnapshot:
        """Retrieve one public market, retaining exact bytes and retrieval time.

        The snapshot is untrusted context until the pure intake gate validates
        it. Current network data must not be labeled as historical evidence.
        """
        self.__post_init__()
        require_market_slug(market_slug)
        if self.allow_public_fetch is not True:
            raise ValueError("public Gamma fetch is disabled")
        endpoint = GAMMA_MARKET_PREFIX + market_slug
        try:
            request = Request(endpoint, method="GET", headers={
                "Accept": "application/json", "User-Agent": "polymarket-alpha-lab/0.1",
            })
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(request, timeout=self.timeout_seconds) as response:
                if response.geturl() != endpoint or response.status != 200:
                    raise ValueError("unexpected response origin or status")
                if response.headers.get_content_type() != "application/json":
                    raise ValueError("expected JSON content")
                raw = response.read(MAX_GAMMA_RESPONSE_BYTES + 1)
            return GammaMarketSnapshot(market_slug, datetime.now(UTC), raw)
        except HTTPError as error:
            error.close()
            raise ValueError("gamma_public_fetch_failed") from None
        except Exception:
            raise ValueError("gamma_public_fetch_failed") from None


__all__ = ("GammaResearchReader",)
