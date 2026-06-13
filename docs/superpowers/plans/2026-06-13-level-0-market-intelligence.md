# Level 0 Market Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first read-only Polymarket market intelligence pipeline: public data fetch, raw archival, normalization, deterministic market scoring, and a local CLI that produces ranked research candidates without authentication or trading.

**Architecture:** Use small Python modules with explicit boundaries: public API access, raw archive, normalization, scoring, orchestration, and CLI. The implementation must preserve raw payloads before normalization, use `Decimal` for numeric market data, treat outcome tokens as the tradable unit, and keep execution concerns out of Phase 1.

**Tech Stack:** Python 3.11+, standard library HTTP and CLI (`urllib.request`, `argparse`, `json`, `pathlib`), frozen dataclasses, `pytest`, CodeGraph, official Polymarket public APIs.

---

## Review And Execution Protocol

The user authorized autonomous decisions, but this project has mandatory review gates:

1. Before implementation starts, submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions.
2. Do not implement Phase 1 until Claude Code reviews the goal, technical stack, implementation plan, and stage boundaries.
3. At each implementation node, run the verification commands listed for that node.
4. Before committing and pushing a node, submit the new code and the next node plan to Claude Code for review.
5. Fix Critical and Important review findings before moving to the next node.
6. After each node, write a short Handoff Summary containing repo status, verified commands, uncommitted files, and next step.

Phase 1 must not add:

- live trading
- account authentication
- private-key handling
- automated order placement
- legal, compliance, or geographic-access analysis

## Official Source Assumptions

Use official Polymarket sources first:

- Gamma markets/events metadata: `https://gamma-api.polymarket.com`
- CLOB public market data and books: `https://clob.polymarket.com`
- Data API public trades/activity aggregates: `https://data-api.polymarket.com`
- Official docs index: `https://docs.polymarket.com`

Official docs indicate that Gamma, Data API, and CLOB market-data read endpoints do not require authentication. Authenticated CLOB credentials are only for future trading, cancellations, authenticated order queries, user WebSocket, and REST heartbeat.

If an endpoint shape changes, adjust the API wrapper and tests before changing higher layers. Website scraping is not part of this plan.

Level 0A intentionally starts with Gamma `/markets` and CLOB `/book`. Follow-up Level 0B should add Gamma `/events` as the universe builder, CLOB batch `/books`, CLOB `/clob-markets/{condition_id}`, selected Data API market analytics, and explicit rate-limit/backoff handling after the single-market pipeline is stable.

The existing `.gitignore` already excludes `data/`, `artifacts/`, and `tmp/`. Level 0A outputs should remain under those ignored directories unless a future task explicitly promotes a small fixture into `tests/fixtures/`.

## Target File Structure

Create or modify these files:

- Modify: `pyproject.toml`
  - Add a console script entry point.
- Modify: `README.md`
  - Add Level 0 usage commands after implementation.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable public domain objects only if useful to tests and users.
- Modify: `src/polymarket_alpha_lab/domain.py`
  - Extend domain objects only where required by normalization and scoring.
- Create: `src/polymarket_alpha_lab/api.py`
  - Public, read-only Polymarket API client with injectable transport.
- Create: `src/polymarket_alpha_lab/archive.py`
  - Raw JSON archival helpers.
- Create: `src/polymarket_alpha_lab/normalize.py`
  - Convert raw API payloads into domain objects.
- Create: `src/polymarket_alpha_lab/scoring.py`
  - Deterministic Level 0 market scoring.
- Create: `src/polymarket_alpha_lab/pipeline.py`
  - Orchestrate fetch, archive, normalize, score, and output.
- Create: `src/polymarket_alpha_lab/cli.py`
  - Command-line interface for local scans.
- Create: `tests/test_api.py`
  - API URL construction, query encoding, timeout, and injected transport tests.
- Create: `tests/test_archive.py`
  - Raw archive path, metadata, and checksum tests.
- Create: `tests/test_normalize.py`
  - Payload parsing tests for stringified JSON, nullable fields, and token mapping.
- Create: `tests/test_scoring.py`
  - Deterministic scoring tests.
- Create: `tests/test_pipeline.py`
  - End-to-end pipeline test with fake client and temporary output directory.
- Create: `tests/test_cli.py`
  - CLI argument parsing and JSON output test.

## Node 1: Public API Client

**Goal:** Add a read-only client for official public REST surfaces with no credentials and no trading methods.

**Files:**

- Create: `src/polymarket_alpha_lab/api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing tests for transport injection and URL construction**

Create `tests/test_api.py` with:

```python
from polymarket_alpha_lab.api import PolymarketPublicClient


class FakeTransport:
    def __init__(self):
        self.calls = []

    def get_json(self, url, *, timeout):
        self.calls.append((url, timeout))
        return [{"id": "1"}]


def test_list_markets_uses_gamma_endpoint_and_query_parameters():
    transport = FakeTransport()
    client = PolymarketPublicClient(transport=transport, timeout_seconds=7)

    payload = client.list_markets(active=True, closed=False, limit=25)

    assert payload == [{"id": "1"}]
    assert transport.calls == [
        (
            "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=25",
            7,
        )
    ]


def test_get_order_book_uses_clob_book_endpoint():
    transport = FakeTransport()
    client = PolymarketPublicClient(transport=transport)

    client.get_order_book(token_id="123")

    assert transport.calls[0][0] == "https://clob.polymarket.com/book?token_id=123"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_api.py -q
```

Expected: import failure because `polymarket_alpha_lab.api` does not exist.

- [ ] **Step 3: Implement minimal API client**

Create `src/polymarket_alpha_lab/api.py` with:

```python
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
```

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_api.py tests/test_domain.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Request Claude Code review before commit**

Submit the staged Node 1 diff plus Node 2 plan summary to Claude Code:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Node 1 public API client changes in /home/ubuntu/polymarket-alpha-lab. Requirements: read-only public endpoints only, no auth, no trading, injectable transport, deterministic tests. Also review next node plan: raw JSON archive helpers. Report Critical, Important, Minor findings only."
```

- [ ] **Step 6: Commit Node 1 after review findings are resolved**

Run:

```bash
git add src/polymarket_alpha_lab/api.py tests/test_api.py
git commit -m "feat: add public polymarket api client"
```

## Node 2: Raw Payload Archive

**Goal:** Preserve raw API payloads before normalization in timestamped JSON files under a caller-selected directory, with sidecar metadata and a content checksum.

**Files:**

- Create: `src/polymarket_alpha_lab/archive.py`
- Create: `tests/test_archive.py`

- [ ] **Step 1: Write failing archive tests**

Create `tests/test_archive.py` with:

```python
import json
from datetime import UTC, datetime

from polymarket_alpha_lab.archive import RawArchive, sha256_json


def test_raw_archive_writes_payload_metadata_and_checksum(tmp_path):
    archive = RawArchive(root=tmp_path)
    captured_at = datetime(2026, 6, 13, 12, 30, tzinfo=UTC)
    payload = [{"conditionId": "0xabc"}]

    entry = archive.write(
        source="gamma",
        name="markets",
        payload=payload,
        captured_at=captured_at,
        endpoint="/markets",
        params={"active": True, "closed": False, "limit": 25},
    )

    assert entry.payload_path == tmp_path / "gamma" / "20260613T123000Z-markets.json"
    assert entry.metadata_path == tmp_path / "gamma" / "20260613T123000Z-markets.meta.json"
    assert json.loads(entry.payload_path.read_text()) == payload

    metadata = json.loads(entry.metadata_path.read_text())
    assert metadata == {
        "captured_at": "2026-06-13T12:30:00+00:00",
        "endpoint": "/markets",
        "name": "markets",
        "params": {"active": True, "closed": False, "limit": 25},
        "payload_sha256": sha256_json(payload),
        "source": "gamma",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_archive.py -q
```

Expected: import failure because `polymarket_alpha_lab.archive` does not exist.

- [ ] **Step 3: Implement raw archive helper**

Create `src/polymarket_alpha_lab/archive.py` with:

```python
"""Raw JSON archival helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RawArchiveEntry:
    source: str
    name: str
    captured_at: datetime
    payload_path: Path
    metadata_path: Path
    payload_sha256: str


@dataclass(frozen=True)
class RawArchive:
    root: Path

    def write(
        self,
        *,
        source: str,
        name: str,
        payload: Any,
        captured_at: datetime | None = None,
        endpoint: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> RawArchiveEntry:
        timestamp_value = _normalize_timestamp(captured_at or datetime.now(UTC))
        timestamp = _format_timestamp(timestamp_value)
        directory = self.root / source
        directory.mkdir(parents=True, exist_ok=True)
        payload_path = directory / f"{timestamp}-{name}.json"
        metadata_path = directory / f"{timestamp}-{name}.meta.json"
        payload_hash = sha256_json(payload)
        payload_path.write_text(
            _canonical_json(payload, indent=2),
            encoding="utf-8",
        )
        metadata_path.write_text(
            _canonical_json(
                {
                    "captured_at": timestamp_value.isoformat(),
                    "endpoint": endpoint,
                    "name": name,
                    "params": params or {},
                    "payload_sha256": payload_hash,
                    "source": source,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return RawArchiveEntry(
            source=source,
            name=name,
            captured_at=timestamp_value,
            payload_path=payload_path,
            metadata_path=metadata_path,
            payload_sha256=payload_hash,
        )


def _format_timestamp(value: datetime) -> str:
    return _normalize_timestamp(value).strftime("%Y%m%dT%H%M%SZ")


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload, indent=None).encode("utf-8")).hexdigest()


def _canonical_json(payload: Any, *, indent: int | None) -> str:
    return json.dumps(payload, indent=indent, sort_keys=True, separators=(",", ": ")) + "\n"
```

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_archive.py tests/test_api.py tests/test_domain.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Request Claude Code review before commit**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Node 2 raw archive changes in /home/ubuntu/polymarket-alpha-lab. Requirements: preserve raw payload before normalization, write metadata sidecar, include SHA-256 checksum, no auth, no trading. Also review next node plan: Gamma/CLOB normalization into domain objects. Report Critical, Important, Minor findings only."
```

- [ ] **Step 6: Commit Node 2**

Run:

```bash
git add src/polymarket_alpha_lab/archive.py tests/test_archive.py
git commit -m "feat: archive raw market payloads"
```

## Node 3: Normalization

**Goal:** Convert raw market and order book payloads into domain objects while preserving distinctions between missing, zero, and unknown values.

**Files:**

- Modify: `src/polymarket_alpha_lab/domain.py`
- Create: `src/polymarket_alpha_lab/normalize.py`
- Create: `tests/test_normalize.py`

- [ ] **Step 1: Write failing normalization tests**

Create `tests/test_normalize.py` with:

```python
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.normalize import (
    normalize_gamma_market,
    normalize_order_book,
)


def test_normalize_gamma_market_parses_stringified_tokens_and_prices():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    payload = {
        "conditionId": "0xabc",
        "slug": "example-market",
        "question": "Will the example resolve yes?",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "endDate": "2026-07-01T00:00:00Z",
        "volume24hr": "123.45",
        "liquidity": "456.78",
        "orderMinSize": "5",
        "orderPriceMinTickSize": "0.01",
        "outcomes": '["Yes","No"]',
        "clobTokenIds": '["111","222"]',
        "description": "Example rules",
        "resolutionSource": "https://example.com",
    }

    normalized = normalize_gamma_market(payload, captured_at=captured_at)

    assert normalized.market.condition_id == "0xabc"
    assert normalized.market.is_tradeable is True
    assert normalized.market.volume_24h == Decimal("123.45")
    assert normalized.market.enable_order_book is True
    assert normalized.market.order_min_size == Decimal("5")
    assert normalized.market.order_price_min_tick_size == Decimal("0.01")
    assert normalized.tokens[0].token_id == "111"
    assert normalized.tokens[0].outcome_name == "Yes"
    assert normalized.tokens[1].token_id == "222"
    assert normalized.rules_text == "Example rules"
    assert normalized.resolution_source == "https://example.com"


def test_normalize_order_book_sorts_bids_descending_and_asks_ascending():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    payload = {
        "asset_id": "111",
        "bids": [{"price": "0.40", "size": "10"}, {"price": "0.45", "size": "3"}],
        "asks": [{"price": "0.60", "size": "8"}, {"price": "0.55", "size": "4"}],
    }

    book = normalize_order_book(payload, captured_at=captured_at)

    assert book.token_id == "111"
    assert [level.price for level in book.bids] == [Decimal("0.45"), Decimal("0.40")]
    assert [level.price for level in book.asks] == [Decimal("0.55"), Decimal("0.60")]
    assert book.spread == Decimal("0.10")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_normalize.py -q
```

Expected: import failure because `polymarket_alpha_lab.normalize` does not exist.

- [ ] **Step 3: Extend domain model**

`MarketScore` and `OrderBookSnapshot.spread` already exist in `src/polymarket_alpha_lab/domain.py`; do not replace their definitions or change the existing weighted `MarketScore.total` formula. Only extend the model with the fields below.

Extend `MarketSnapshot` in `src/polymarket_alpha_lab/domain.py` with Phase 1 data-quality fields after `captured_at` so existing callers remain stable:

```python
    enable_order_book: bool | None = None
    order_min_size: Decimal | None = None
    order_price_min_tick_size: Decimal | None = None
    resolution_status: str | None = None
```

Add a new frozen dataclass:

```python
@dataclass(frozen=True)
class NormalizedMarket:
    """Market metadata plus its tradable outcome tokens."""

    market: MarketSnapshot
    tokens: tuple[OutcomeToken, ...]
    rules_text: str | None
    resolution_source: str | None
```

Export `NormalizedMarket` from `src/polymarket_alpha_lab/__init__.py`.

- [ ] **Step 4: Implement normalization functions**

Create `src/polymarket_alpha_lab/normalize.py` with:

```python
"""Normalization from raw Polymarket payloads into domain objects."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)


def normalize_gamma_market(
    payload: dict[str, Any], *, captured_at: datetime
) -> NormalizedMarket:
    condition_id = str(payload.get("conditionId") or "")
    outcomes = _as_list(payload.get("outcomes"))
    token_ids = _as_list(payload.get("clobTokenIds"))
    tokens = tuple(
        OutcomeToken(
            condition_id=condition_id,
            token_id=str(token_id),
            outcome_index=index,
            outcome_name=str(outcomes[index]) if index < len(outcomes) else str(index),
        )
        for index, token_id in enumerate(token_ids)
    )
    market = MarketSnapshot(
        condition_id=condition_id,
        market_slug=str(payload.get("slug") or payload.get("marketSlug") or ""),
        question=str(payload.get("question") or ""),
        active=bool(payload.get("active")),
        closed=bool(payload.get("closed")),
        accepting_orders=bool(payload.get("acceptingOrders"))
        and bool(payload.get("enableOrderBook", True)),
        end_time=_parse_datetime(payload.get("endDate")),
        volume_24h=_parse_decimal(payload.get("volume24hr")),
        liquidity=_parse_decimal(payload.get("liquidity")),
        captured_at=captured_at,
        enable_order_book=_parse_optional_bool(payload.get("enableOrderBook")),
        order_min_size=_parse_decimal(payload.get("orderMinSize")),
        order_price_min_tick_size=_parse_decimal(payload.get("orderPriceMinTickSize")),
        resolution_status=_optional_string(
            payload.get("resolutionStatus") or payload.get("resolved")
        ),
    )
    return NormalizedMarket(
        market=market,
        tokens=tokens,
        rules_text=_optional_string(payload.get("description") or payload.get("rules")),
        resolution_source=_optional_string(payload.get("resolutionSource")),
    )


def normalize_order_book(
    payload: dict[str, Any], *, captured_at: datetime
) -> OrderBookSnapshot:
    token_id = str(payload.get("asset_id") or payload.get("token_id") or "")
    bids = tuple(
        sorted(
            (_book_level(level) for level in payload.get("bids", [])),
            key=lambda level: level.price,
            reverse=True,
        )
    )
    asks = tuple(
        sorted(
            (_book_level(level) for level in payload.get("asks", [])),
            key=lambda level: level.price,
        )
    )
    return OrderBookSnapshot(token_id=token_id, bids=bids, asks=asks, captured_at=captured_at)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, list) else []
    return []


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _parse_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return bool(value)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return datetime.fromisoformat(text).astimezone(UTC)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _book_level(payload: dict[str, Any]) -> OrderBookLevel:
    price = _parse_decimal(payload.get("price")) or Decimal("0")
    size = _parse_decimal(payload.get("size")) or Decimal("0")
    return OrderBookLevel(price=price, size=size)
```

- [ ] **Step 5: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_normalize.py tests/test_domain.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Request Claude Code review before commit**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Node 3 normalization changes in /home/ubuntu/polymarket-alpha-lab. Requirements: parse Gamma stringified JSON arrays, preserve nullable numerics, map CLOB token ids to outcome tokens, normalize CLOB order books with sorted bids/asks, no auth, no trading. Also review next node plan: deterministic market scoring. Report Critical, Important, Minor findings only."
```

- [ ] **Step 7: Commit Node 3**

Run:

```bash
git add src/polymarket_alpha_lab/domain.py src/polymarket_alpha_lab/__init__.py src/polymarket_alpha_lab/normalize.py tests/test_normalize.py tests/test_domain.py
git commit -m "feat: normalize public market payloads"
```

## Node 4: Deterministic Market Scoring

**Goal:** Convert normalized markets and top-of-book quality into a deterministic 0 to 100 research priority score.

**Files:**

- Create: `src/polymarket_alpha_lab/scoring.py`
- Create: `tests/test_scoring.py`

- [ ] **Step 1: Write failing scoring tests**

Create `tests/test_scoring.py` with:

```python
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)
from polymarket_alpha_lab.scoring import score_market


def test_score_market_rewards_activity_liquidity_and_tight_spread():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    market = NormalizedMarket(
        market=MarketSnapshot(
            condition_id="0xabc",
            market_slug="example",
            question="Will this happen?",
            active=True,
            closed=False,
            accepting_orders=True,
            end_time=None,
            volume_24h=Decimal("10000"),
            liquidity=Decimal("20000"),
            captured_at=captured_at,
        ),
        tokens=(
            OutcomeToken("0xabc", "111", 0, "Yes"),
            OutcomeToken("0xabc", "222", 1, "No"),
        ),
        rules_text="Clear rule text",
        resolution_source="https://example.com",
    )
    books = {
        "111": OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.49"), Decimal("500")),),
            asks=(OrderBookLevel(Decimal("0.51"), Decimal("500")),),
            captured_at=captured_at,
        )
    }

    scores = score_market(market, books)

    assert len(scores) == 2
    assert scores[0].token_id == "111"
    assert scores[0].activity > Decimal("0")
    assert scores[0].liquidity > Decimal("0")
    assert scores[0].spread_quality > Decimal("0")
    assert scores[0].total > Decimal("50")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_scoring.py -q
```

Expected: import failure because `polymarket_alpha_lab.scoring` does not exist.

- [ ] **Step 3: Implement scoring**

Create `src/polymarket_alpha_lab/scoring.py` with deterministic helper functions:

```python
"""Deterministic Level 0 market scoring."""

from __future__ import annotations

from decimal import Decimal

from polymarket_alpha_lab.domain import MarketScore, NormalizedMarket, OrderBookSnapshot


def score_market(
    market: NormalizedMarket,
    books_by_token_id: dict[str, OrderBookSnapshot],
) -> list[MarketScore]:
    return [
        MarketScore(
            condition_id=market.market.condition_id,
            token_id=token.token_id,
            activity=_score_amount(market.market.volume_24h, Decimal("10000")),
            liquidity=_score_amount(market.market.liquidity, Decimal("20000")),
            spread_quality=_score_spread(books_by_token_id.get(token.token_id)),
            time_structure=Decimal("50"),
            information_structure=_score_information(market),
            price_behavior=Decimal("50"),
            duplicate_penalty=Decimal("0"),
        )
        for token in market.tokens
    ]


def _score_amount(value: Decimal | None, full_score_at: Decimal) -> Decimal:
    if value is None or value <= 0:
        return Decimal("0")
    return min(Decimal("100"), (value / full_score_at) * Decimal("100"))


def _score_spread(book: OrderBookSnapshot | None) -> Decimal:
    if book is None or book.spread is None:
        return Decimal("0")
    spread = book.spread
    if spread <= Decimal("0.01"):
        return Decimal("100")
    if spread >= Decimal("0.20"):
        return Decimal("0")
    return max(Decimal("0"), Decimal("100") - (spread * Decimal("500")))


def _score_information(market: NormalizedMarket) -> Decimal:
    score = Decimal("0")
    if market.rules_text:
        score += Decimal("50")
    if market.resolution_source:
        score += Decimal("50")
    return score
```

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_scoring.py tests/test_normalize.py tests/test_domain.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Request Claude Code review before commit**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Node 4 scoring changes in /home/ubuntu/polymarket-alpha-lab. Requirements: deterministic 0-100 research scoring, uses existing weights, no buy/sell recommendations, no auth, no trading. Also review next node plan: read-only market scan pipeline with raw archival and JSON output. Report Critical, Important, Minor findings only."
```

- [ ] **Step 6: Commit Node 4**

Run:

```bash
git add src/polymarket_alpha_lab/scoring.py tests/test_scoring.py
git commit -m "feat: score research markets"
```

## Node 5: Pipeline Orchestration

**Goal:** Build a local pipeline that fetches public market payloads, archives raw data, normalizes markets, optionally fetches books, scores tokens, and writes ranked JSON output.

**Files:**

- Create: `src/polymarket_alpha_lab/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing pipeline test**

Create `tests/test_pipeline.py` with:

```python
import json
from datetime import UTC, datetime

from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan


class FakeClient:
    def __init__(self):
        self.book_calls = []

    def list_markets(self, *, active, closed, limit):
        assert active is True
        assert closed is False
        assert limit == 2
        return [
            {
                "conditionId": "0xabc",
                "slug": "example-market",
                "question": "Will the example resolve yes?",
                "active": True,
                "closed": False,
                "acceptingOrders": True,
                "enableOrderBook": True,
                "volume24hr": "10000",
                "liquidity": "20000",
                "outcomes": '["Yes","No"]',
                "clobTokenIds": '["111","222"]',
                "description": "Clear rules",
                "resolutionSource": "https://example.com",
            }
        ]

    def get_order_book(self, *, token_id):
        self.book_calls.append(token_id)
        if token_id == "222":
            raise RuntimeError("book temporarily unavailable")
        return {
            "asset_id": token_id,
            "bids": [{"price": "0.49", "size": "500"}],
            "asks": [{"price": "0.51", "size": "500"}],
        }


def test_run_market_scan_archives_raw_data_and_writes_ranked_candidates(tmp_path):
    captured_at = datetime(2026, 6, 13, 12, 30, tzinfo=UTC)
    output_path = tmp_path / "artifacts" / "scores.json"
    client = FakeClient()

    candidates = run_market_scan(
        client=client,
        config=MarketScanConfig(
            limit=2,
            archive_root=tmp_path / "raw",
            output_path=output_path,
            fetch_books=True,
        ),
        captured_at=captured_at,
    )

    assert client.book_calls == ["111", "222"]
    assert [candidate.token_id for candidate in candidates] == ["111", "222"]
    assert candidates[0].market_slug == "example-market"
    assert candidates[1].token_id == "222"
    assert candidates[0].raw_archive_path.endswith("20260613T123000Z-markets.json")

    raw_markets = tmp_path / "raw" / "gamma" / "20260613T123000Z-markets.json"
    raw_book = tmp_path / "raw" / "clob" / "20260613T123000Z-book-111.json"
    assert raw_markets.exists()
    assert raw_book.exists()

    written = json.loads(output_path.read_text())
    assert written[0]["condition_id"] == "0xabc"
    assert written[0]["token_id"] == "111"
    assert written[0]["market_slug"] == "example-market"
    assert written[0]["question"] == "Will the example resolve yes?"
    assert written[0]["raw_archive_path"].endswith("20260613T123000Z-markets.json")


def test_run_market_scan_fails_fast_when_primary_market_fetch_fails(tmp_path):
    class BrokenClient:
        def list_markets(self, *, active, closed, limit):
            raise RuntimeError("primary market fetch failed")

    try:
        run_market_scan(
            client=BrokenClient(),
            config=MarketScanConfig(
                limit=1,
                archive_root=tmp_path / "raw",
                output_path=tmp_path / "scores.json",
            ),
            captured_at=datetime(2026, 6, 13, tzinfo=UTC),
        )
    except RuntimeError as exc:
        assert str(exc) == "primary market fetch failed"
    else:
        raise AssertionError("expected primary market fetch failure to propagate")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_pipeline.py -q
```

Expected: import failure because `polymarket_alpha_lab.pipeline` does not exist.

- [ ] **Step 3: Implement pipeline dataclasses and `run_market_scan`**

Create `src/polymarket_alpha_lab/pipeline.py` with:

```python
"""Read-only market scan orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from polymarket_alpha_lab.archive import RawArchive
from polymarket_alpha_lab.domain import OrderBookSnapshot
from polymarket_alpha_lab.normalize import normalize_gamma_market, normalize_order_book
from polymarket_alpha_lab.scoring import score_market


class MarketDataClient(Protocol):
    def list_markets(self, *, active: bool, closed: bool, limit: int) -> Any:
        """Return raw public market payloads."""

    def get_order_book(self, *, token_id: str) -> Any:
        """Return raw public order book payload for one CLOB token id."""


@dataclass(frozen=True)
class MarketScanConfig:
    limit: int
    archive_root: Path
    output_path: Path
    fetch_books: bool = True


@dataclass(frozen=True)
class ScoredCandidate:
    condition_id: str
    token_id: str
    market_slug: str
    question: str
    total_score: str
    raw_archive_path: str


def run_market_scan(
    *,
    client: MarketDataClient,
    config: MarketScanConfig,
    captured_at: datetime | None = None,
) -> list[ScoredCandidate]:
    timestamp = captured_at or datetime.now(UTC)
    archive = RawArchive(config.archive_root)
    markets_payload = client.list_markets(active=True, closed=False, limit=config.limit)
    markets_archive = archive.write(
        source="gamma",
        name="markets",
        payload=markets_payload,
        captured_at=timestamp,
        endpoint="/markets",
        params={"active": True, "closed": False, "limit": config.limit},
    )

    ranked: list[tuple[Decimal, ScoredCandidate]] = []
    for raw_market in _iter_dicts(markets_payload):
        normalized_market = normalize_gamma_market(raw_market, captured_at=timestamp)
        if (
            not normalized_market.market.condition_id
            or not normalized_market.tokens
            or not normalized_market.market.is_tradeable
        ):
            continue
        books_by_token_id: dict[str, OrderBookSnapshot] = {}
        if config.fetch_books:
            books_by_token_id = _fetch_books(
                client=client,
                archive=archive,
                token_ids=[token.token_id for token in normalized_market.tokens],
                captured_at=timestamp,
            )
        for score in score_market(normalized_market, books_by_token_id):
            candidate = ScoredCandidate(
                condition_id=score.condition_id,
                token_id=score.token_id,
                market_slug=normalized_market.market.market_slug,
                question=normalized_market.market.question,
                total_score=_format_decimal(score.total),
                raw_archive_path=str(markets_archive.payload_path),
            )
            ranked.append((score.total, candidate))

    candidates = [
        candidate
        for _, candidate in sorted(
            ranked, key=lambda item: (item[0], item[1].token_id), reverse=True
        )
    ]
    _write_output(config.output_path, candidates)
    return candidates


def _fetch_books(
    *,
    client: MarketDataClient,
    archive: RawArchive,
    token_ids: list[str],
    captured_at: datetime,
) -> dict[str, OrderBookSnapshot]:
    books: dict[str, OrderBookSnapshot] = {}
    for token_id in token_ids:
        try:
            raw_book = client.get_order_book(token_id=token_id)
        except Exception:
            continue
        archive.write(
            source="clob",
            name=f"book-{token_id}",
            payload=raw_book,
            captured_at=captured_at,
            endpoint="/book",
            params={"token_id": token_id},
        )
        if isinstance(raw_book, dict):
            book = normalize_order_book(raw_book, captured_at=captured_at)
            books[book.token_id] = book
    return books


def _iter_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return [item for item in payload["data"] if isinstance(item, dict)]
    return []


def _write_output(path: Path, candidates: list[ScoredCandidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(candidate) for candidate in candidates], indent=2) + "\n",
        encoding="utf-8",
    )


def _format_decimal(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.001")))
```

Error handling policy:

- Primary Gamma market fetch errors propagate to the caller because no scan can be trusted without the universe payload.
- Individual CLOB book fetch errors are skipped so one unavailable book does not prevent scoring other tokens.
- Markets with missing `condition_id`, no CLOB token ids, or non-tradeable lifecycle flags are skipped.
- Level 0A does not implement retry/backoff. Keep default scan limits small; add explicit 429/backoff handling in Level 0B when batch endpoints are introduced.

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_pipeline.py tests/test_scoring.py tests/test_normalize.py tests/test_archive.py tests/test_api.py tests/test_domain.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Request Claude Code review before commit**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Node 5 pipeline changes in /home/ubuntu/polymarket-alpha-lab. Requirements: fetch public active markets, archive raw payloads first, normalize only dict payloads, fetch books only when configured, skip individual book failures, write ranked JSON, no auth, no trading. Also review next node plan: CLI and README usage. Report Critical, Important, Minor findings only."
```

- [ ] **Step 6: Commit Node 5**

Run:

```bash
git add src/polymarket_alpha_lab/pipeline.py tests/test_pipeline.py
git commit -m "feat: run read-only market scan pipeline"
```

## Node 6: CLI And Documentation

**Goal:** Expose the pipeline through a local CLI and document how to run a read-only scan.

**Files:**

- Modify: `pyproject.toml`
- Create: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_cli.py` with:

```python
from pathlib import Path

from polymarket_alpha_lab.cli import main


def test_scan_cli_builds_read_only_scan_config(tmp_path):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_runner(*, client, config):
        calls.append((client, config))
        return []

    output_path = tmp_path / "scores.json"
    archive_root = tmp_path / "raw"

    exit_code = main(
        [
            "scan",
            "--limit",
            "3",
            "--archive-root",
            str(archive_root),
            "--output",
            str(output_path),
            "--no-books",
        ],
        runner=fake_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    client, config = calls[0]
    assert client == "fake-client"
    assert config.limit == 3
    assert config.archive_root == archive_root
    assert config.output_path == output_path
    assert config.fetch_books is False


def test_scan_cli_returns_one_when_runner_fails(tmp_path):
    def broken_runner(*, client, config):
        raise RuntimeError("scan failed")

    exit_code = main(
        [
            "scan",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "scores.json"),
        ],
        runner=broken_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

Expected: import failure because `polymarket_alpha_lab.cli` does not exist.

- [ ] **Step 3: Implement CLI**

Create `src/polymarket_alpha_lab/cli.py` with:

```python
"""Command-line interface for read-only market scans."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

from polymarket_alpha_lab.api import PolymarketPublicClient
from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan


Runner = Callable[..., object]
ClientFactory = Callable[[], Any]


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = run_market_scan,
    client_factory: ClientFactory = PolymarketPublicClient,
) -> int:
    parser = argparse.ArgumentParser(prog="polymarket-alpha-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan")
    scan.add_argument("--limit", type=int, default=25)
    scan.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    scan.add_argument("--output", type=Path, default=Path("artifacts/market-scores.json"))
    scan.add_argument("--no-books", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "scan":
        try:
            runner(
                client=client_factory(),
                config=MarketScanConfig(
                    limit=args.limit,
                    archive_root=args.archive_root,
                    output_path=args.output,
                    fetch_books=not args.no_books,
                ),
            )
            return 0
        except Exception as exc:
            print(f"scan failed: {exc}", file=sys.stderr)
            return 1

    return 2
```

- [ ] **Step 4: Add console script**

Modify `pyproject.toml`:

```toml
[project.scripts]
polymarket-alpha-lab = "polymarket_alpha_lab.cli:main"
```

- [ ] **Step 5: Update README usage**

Add commands:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/polymarket-alpha-lab scan --limit 25 --output artifacts/market-scores.json
```

Document that this command is read-only and writes raw payloads under `data/raw/`, which is ignored by git.

- [ ] **Step 6: Run full verification**

Run:

```bash
.venv/bin/python -m pytest
codegraph sync .
codegraph status .
git status --short --branch
```

Expected:

- pytest reports all tests passing
- CodeGraph index is up to date
- only intentional files are modified or staged

- [ ] **Step 7: Request Claude Code review before final Level 0 push**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review all Level 0 market intelligence changes in /home/ubuntu/polymarket-alpha-lab before final push. Requirements: public REST client only, raw archival, normalization, deterministic scoring, read-only pipeline, CLI, README usage, no auth, no private keys, no order placement, no live trading. Also review next-stage direction: Level 1 automated research packets and bid/ask paper trading, not live trading. Report Critical, Important, Minor findings only."
```

- [ ] **Step 8: Commit and push Node 6**

Run:

```bash
git add pyproject.toml README.md src/polymarket_alpha_lab/cli.py tests/test_cli.py
git commit -m "feat: add read-only market scan cli"
git push
```

## Level 0 Completion Criteria

Level 0 is complete only when:

- public REST client exists and has no auth or trading methods
- raw payload archive exists and is tested
- normalization handles stringified JSON fields and nullable numerics
- scoring is deterministic and tested
- pipeline produces ranked candidate JSON from fake client tests
- CLI can run a read-only scan
- README documents usage and Phase 1 boundaries
- full pytest suite passes
- CodeGraph sync/status passes
- Claude Code reviewed the plan and every code node before push
- GitHub `main` contains the verified commits

## Handoff Summary Template

At the end of each node, write:

```text
Handoff Summary
- Repo status: branch, latest commit, clean/dirty state, pushed/not pushed.
- Verified commands: exact commands and pass/fail result.
- Uncommitted files: list or "none".
- Claude review: model, review scope, unresolved findings.
- Next step: one concrete next action.
```
