# Team Framework BTC Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first paper-only domain-team framework slice: generic team taxonomy, route/forecast/evidence/outcome persistence, performance summaries, and a minimal `crypto_btc` workflow.

**Architecture:** Domain teams produce readonly forecast and evidence packets. The central layer keeps Polymarket microstructure, cost/edge, recommendation, risk, and outcome scoring centralized. The first runnable workflow is `crypto_btc`, but the data model supports the 10-team medium taxonomy.

**Tech Stack:** Python frozen dataclasses, `Decimal`, local Supabase/Postgres via psycopg adapters, existing JSON recovery helpers, pytest, CodeGraph, no float durable payloads.

## Global Constraints

- Phase 1 remains paper-only, report-only, readonly.
- No live trading, no wallet auth, no private keys, no account reads, no order signing, no order submission, no order cancellation, no order replacement, and no exchange/order mutation.
- All durable data must use local Supabase/Postgres only.
- No SQLite, Redis, MongoDB, hosted database assumption, or SQLAlchemy persistence path.
- Any raw DSN must be validated via `validate_local_postgres_dsn(...)` before psycopg import/connect/wrapper setup.
- Use `Decimal` for probabilities, money, scores, costs, notional, and JSON-recovered numeric values.
- JSON payloads must not contain float values.
- Dataclass report objects are frozen and explicit.
- Team agents do not fetch Polymarket microstructure directly; they consume centralized immutable snapshots.
- Team forecasts feed existing central cost-aware/side-edge logic; teams do not own cost, recommendation, allocation, or execution.

---

## File Structure

Create these focused modules:

- `src/polymarket_alpha_lab/team_taxonomy.py`
  - Team IDs, category IDs, event-template validation, team profile dataclasses.
- `src/polymarket_alpha_lab/team_paper_guard.py`
  - Shared structural guard for `paper_only`, `report_only`, `readonly`, unsafe-field rejection, and no-float JSON validation.
- `src/polymarket_alpha_lab/team_market_router.py`
  - Supplied-input route reports: one primary team, optional secondary teams, confidence, correction metadata.
- `src/polymarket_alpha_lab/team_forecast_packet.py`
  - Team forecast packet and evidence packet dataclasses, including the explicit interface into `PaperProbabilitySideEdgeInput`.
- `src/polymarket_alpha_lab/team_forecast_db_row.py`
  - DB row codecs for routes, forecasts, evidence, and outcomes with canonical JSON payloads.
- `src/polymarket_alpha_lab/team_forecast_store.py`
  - Connection-oriented insert/load functions for local Supabase/Postgres.
- `src/polymarket_alpha_lab/team_forecast_psycopg.py`
  - DSN-validating psycopg wrappers. Import psycopg only after DSN validation.
- `src/polymarket_alpha_lab/team_performance_summary.py`
  - Brier score, hit rate, sample-count gates, neutral trust report.
- `src/polymarket_alpha_lab/crypto_btc_team.py`
  - Minimal supplied-input BTC workflow that builds a team forecast packet from already-collected BTC evidence and centralized microstructure.
- `src/polymarket_alpha_lab/supabase_team_forecast_config.py`
  - Environment boundary for the local Supabase tables used by this slice.

Modify:

- `src/polymarket_alpha_lab/__init__.py`
  - Export only the stable dataclasses/builders added by this slice.
- `tests/test_database_persistence_iron_rule.py`
  - Extend iron-rule coverage to team forecast persistence modules.
- `tests/test_phase1_live_surface_guard.py`
  - Extend live-surface guard to new team modules.

Add tests:

- `tests/test_team_taxonomy.py`
- `tests/test_team_paper_guard.py`
- `tests/test_team_market_router.py`
- `tests/test_team_forecast_packet.py`
- `tests/test_team_forecast_db_row.py`
- `tests/test_team_forecast_store.py`
- `tests/test_team_forecast_psycopg.py`
- `tests/test_team_performance_summary.py`
- `tests/test_crypto_btc_team.py`
- `tests/test_supabase_team_forecast_config.py`
- `tests/test_team_framework_scope.py`

## Parallel Development Map

These tasks can be assigned to separate agents once Task 1 lands:

- Task 2 router: `team_market_router.py`, `tests/test_team_market_router.py`
- Task 3 forecast/evidence packet: `team_forecast_packet.py`, `tests/test_team_forecast_packet.py`
- Task 4 DB codecs: `team_forecast_db_row.py`, `tests/test_team_forecast_db_row.py`
- Task 6 performance summary: `team_performance_summary.py`, `tests/test_team_performance_summary.py`

Do not run two write agents on the same file set. Review and merge each task before another task extends the same module.

---

### Task 1: Team Taxonomy and Paper Guard

**Files:**
- Create: `src/polymarket_alpha_lab/team_taxonomy.py`
- Create: `src/polymarket_alpha_lab/team_paper_guard.py`
- Test: `tests/test_team_taxonomy.py`
- Test: `tests/test_team_paper_guard.py`

**Interfaces:**
- Produces:
  - `TEAM_IDS: tuple[str, ...]`
  - `TEAM_CATEGORIES: tuple[str, ...]`
  - `TeamProfile`
  - `build_default_team_profiles() -> tuple[TeamProfile, ...]`
  - `require_team_id(field_name: str, value: object) -> str`
  - `require_category_id(field_name: str, value: object) -> str`
  - `require_paper_only_flags(label: str, value: object) -> None`
  - `reject_unsafe_surface_fields(label: str, payload: object) -> None`
  - `json_ready_no_floats(value: object) -> object`
- Consumes: none.

- [ ] **Step 1: Write failing taxonomy tests**

Add to `tests/test_team_taxonomy.py`:

```python
from dataclasses import FrozenInstanceError

import pytest

from polymarket_alpha_lab.team_taxonomy import (
    TEAM_IDS,
    TeamProfile,
    build_default_team_profiles,
    require_category_id,
    require_team_id,
)


def test_default_team_profiles_cover_medium_taxonomy_and_are_frozen():
    profiles = build_default_team_profiles()

    assert tuple(profile.team_id for profile in profiles) == TEAM_IDS
    assert "crypto_btc" in TEAM_IDS
    assert "sports_basketball" in TEAM_IDS
    assert len(profiles) == 10
    assert all(profile.paper_only is True for profile in profiles)
    assert all(profile.report_only is True for profile in profiles)
    assert all(profile.readonly is True for profile in profiles)

    with pytest.raises(FrozenInstanceError):
        profiles[0].display_name = "changed"  # type: ignore[misc]


def test_team_profile_validates_team_category_and_agent_roles():
    profile = TeamProfile(
        team_id="crypto_btc",
        display_name="Crypto BTC",
        primary_categories=("finance.crypto.btc",),
        agent_roles=("btc_lead_forecaster", "btc_memory_postmortem"),
    )

    assert profile.team_id == "crypto_btc"
    assert profile.primary_categories == ("finance.crypto.btc",)

    with pytest.raises(ValueError, match="team_id must be a known team"):
        require_team_id("team_id", "unknown_team")

    with pytest.raises(ValueError, match="category_id must be a known category"):
        require_category_id("category_id", "unknown.category")

    with pytest.raises(ValueError, match="agent_roles must contain canonical strings"):
        TeamProfile(
            team_id="crypto_btc",
            display_name="Crypto BTC",
            primary_categories=("finance.crypto.btc",),
            agent_roles=(" bad ",),
        )
```

- [ ] **Step 2: Write failing paper guard tests**

Add to `tests/test_team_paper_guard.py`:

```python
from dataclasses import dataclass
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


@dataclass(frozen=True)
class SafePacket:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class UnsafePacket:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = False


def test_require_paper_only_flags_rejects_false_flags():
    require_paper_only_flags("safe", SafePacket())

    with pytest.raises(ValueError, match="readonly must be True"):
        require_paper_only_flags("unsafe", UnsafePacket())


def test_reject_unsafe_surface_fields_blocks_live_surface_terms():
    safe_payload = {"forecast_probability": Decimal("0.510000")}
    reject_unsafe_surface_fields("payload", safe_payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        reject_unsafe_surface_fields("payload", {"order_submission": "never"})

    with pytest.raises(ValueError, match="unsafe live surface field"):
        reject_unsafe_surface_fields("payload", {"wallet": {"address": "0x0"}})


def test_json_ready_no_floats_serializes_decimals_and_rejects_float():
    payload = json_ready_no_floats(
        {
            "probability": Decimal("0.510000"),
            "rows": ({"team_id": "crypto_btc"},),
            "paper_only": True,
        },
    )

    assert payload == {
        "probability": "0.510000",
        "rows": [{"team_id": "crypto_btc"}],
        "paper_only": True,
    }

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        json_ready_no_floats({"probability": 0.51})
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 -m pytest -q tests/test_team_taxonomy.py tests/test_team_paper_guard.py
```

Expected: import failures for missing modules.

- [ ] **Step 4: Implement `team_taxonomy.py`**

Create `src/polymarket_alpha_lab/team_taxonomy.py` with these public objects:

```python
from __future__ import annotations

from dataclasses import dataclass


TEAM_IDS = (
    "politics",
    "crypto_btc",
    "crypto_eth",
    "macro_rates",
    "equity_indices",
    "commodities_gold",
    "commodities_oil",
    "sports_soccer",
    "sports_basketball",
    "sports_other",
)

TEAM_CATEGORIES = (
    "politics",
    "finance.crypto.btc",
    "finance.crypto.eth",
    "finance.macro.rates",
    "finance.equity.indices",
    "finance.commodities.gold",
    "finance.commodities.oil",
    "sports.soccer",
    "sports.basketball",
    "sports.other",
)


@dataclass(frozen=True)
class TeamProfile:
    team_id: str
    display_name: str
    primary_categories: tuple[str, ...]
    agent_roles: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("display_name", self.display_name)
        object.__setattr__(
            self,
            "primary_categories",
            _normalize_categories(self.primary_categories),
        )
        object.__setattr__(
            self,
            "agent_roles",
            _normalize_string_tuple("agent_roles", self.agent_roles),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")
```

Add helper functions and `build_default_team_profiles()` in the same file. The builder must return profiles in `TEAM_IDS` order with agent roles from the architecture report.

- [ ] **Step 5: Implement `team_paper_guard.py`**

Create `src/polymarket_alpha_lab/team_paper_guard.py` with:

```python
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


UNSAFE_SURFACE_FIELD_FRAGMENTS = frozenset(
    (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
    ),
)


def require_paper_only_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def reject_unsafe_surface_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def json_ready_no_floats(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return json_ready_no_floats(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        return _json_dict_no_floats(value)
    if isinstance(value, (list, tuple)):
        return [json_ready_no_floats(item) for item in value]
    raise ValueError("value is not JSON serializable")
```

Add `_iter_keys()` and `_json_dict_no_floats()` helpers.

- [ ] **Step 6: Run task tests**

Run:

```bash
python3 -m pytest -q tests/test_team_taxonomy.py tests/test_team_paper_guard.py
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 1**

```bash
git add src/polymarket_alpha_lab/team_taxonomy.py src/polymarket_alpha_lab/team_paper_guard.py tests/test_team_taxonomy.py tests/test_team_paper_guard.py
git commit -m "feat: add team taxonomy and paper guard"
```

---

### Task 2: Market Router

**Files:**
- Create: `src/polymarket_alpha_lab/team_market_router.py`
- Test: `tests/test_team_market_router.py`

**Interfaces:**
- Consumes:
  - `require_team_id()`, `require_category_id()` from `team_taxonomy.py`
  - `require_paper_only_flags()` from `team_paper_guard.py`
- Produces:
  - `TeamMarketRouteConfig`
  - `TeamMarketRouteInput`
  - `TeamMarketRouteRow`
  - `TeamMarketRouteReport`
  - `build_team_market_route_report(inputs, *, config, generated_at)`

- [ ] **Step 1: Write failing router tests**

Add `tests/test_team_market_router.py` with tests for:

```python
def test_router_assigns_exactly_one_primary_team_and_optional_secondary():
    report = build_team_market_route_report(
        (
            TeamMarketRouteInput(
                condition_id="condition-btc",
                market_slug="bitcoin-above-120k",
                question="Will Bitcoin hit 120000 before August 31?",
                category_hint="finance.crypto.btc",
                event_template="btc_hit_price",
                routing_reason_codes=("keyword_bitcoin", "template_hit_price"),
            ),
        ),
        config=TeamMarketRouteConfig(config_version="team-router-v0"),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.primary_team_id == "crypto_btc"
    assert row.secondary_team_ids == ()
    assert row.routing_confidence == Decimal("0.900000")
    assert report.route_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
```

Also test:

- unknown category routes to `sports_other` only when category starts with `sports.unknown`,
- secondary team cannot equal primary,
- `routing_corrected_team_id` must be known when present,
- confidence is `Decimal` and quantized to `0.000001`,
- false safety flags raise.

- [ ] **Step 2: Run router tests to verify failure**

```bash
python3 -m pytest -q tests/test_team_market_router.py
```

Expected: import failure for `team_market_router`.

- [ ] **Step 3: Implement router dataclasses**

Create `team_market_router.py` with frozen dataclasses:

```python
@dataclass(frozen=True)
class TeamMarketRouteConfig:
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class TeamMarketRouteInput:
    condition_id: str
    market_slug: str
    question: str
    category_hint: str
    event_template: str
    routing_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class TeamMarketRouteRow:
    condition_id: str
    market_slug: str
    question: str
    category_id: str
    event_template: str
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    routing_confidence: Decimal
    routing_reason_codes: tuple[str, ...]
    routing_corrected_team_id: str | None = None
    routing_correction_timestamp: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Add `TeamMarketRouteReport` with counts and rows.

- [ ] **Step 4: Implement deterministic category routing**

Implement a small deterministic map:

```python
CATEGORY_TO_PRIMARY_TEAM = {
    "politics": "politics",
    "finance.crypto.btc": "crypto_btc",
    "finance.crypto.eth": "crypto_eth",
    "finance.macro.rates": "macro_rates",
    "finance.equity.indices": "equity_indices",
    "finance.commodities.gold": "commodities_gold",
    "finance.commodities.oil": "commodities_oil",
    "sports.soccer": "sports_soccer",
    "sports.basketball": "sports_basketball",
    "sports.other": "sports_other",
}
```

For the first slice, do not use LLM classification. Use supplied `category_hint` and validated map only.

- [ ] **Step 5: Run router tests**

```bash
python3 -m pytest -q tests/test_team_market_router.py
```

Expected: pass.

- [ ] **Step 6: Commit Task 2**

```bash
git add src/polymarket_alpha_lab/team_market_router.py tests/test_team_market_router.py
git commit -m "feat: add team market router"
```

---

### Task 3: Forecast and Evidence Packets

**Files:**
- Create: `src/polymarket_alpha_lab/team_forecast_packet.py`
- Test: `tests/test_team_forecast_packet.py`

**Interfaces:**
- Consumes:
  - `TeamMarketRouteRow`
  - `PaperProbabilitySideEdgeInput`
  - `require_paper_only_flags()`
- Produces:
  - `TeamForecastPacket`
  - `TeamForecastEvidencePacket`
  - `TeamForecastCostInterfaceInput`
  - `team_forecast_to_side_edge_input(...) -> PaperProbabilitySideEdgeInput`

- [ ] **Step 1: Write failing forecast packet tests**

Add tests that construct a BTC packet and assert:

- all probabilities are `Decimal`,
- `selected_side` is `yes` or `no`,
- `forecast_probability` is between zero and one,
- `confidence`, `evidence_quality`, `data_freshness_score`, `resolution_risk`, and `base_rate` are `Decimal` probabilities,
- memory/source references are canonical tuples,
- false safety flags raise,
- unsafe fields are rejected when serializing to DB payload,
- adapter builds a `PaperProbabilitySideEdgeInput` without recalculating team-owned costs.

Use this representative assertion:

```python
side_edge_input = team_forecast_to_side_edge_input(
    forecast,
    cost_input=TeamForecastCostInterfaceInput(
        side_price=Decimal("0.570000"),
        fee_cost_per_share=Decimal("0.004902"),
        spread_cost_per_share=Decimal("0.010000"),
        slippage_cost_per_share=Decimal("0.001000"),
        funding_cost_per_share=Decimal("0.000000"),
        finalization_cost_per_share=Decimal("0.000000"),
        time_cost_per_share=Decimal("0.000000"),
        risk_cost_per_share=Decimal("0.002000"),
        capital_cost_per_share=Decimal("0.001000"),
        requested_paper_shares=Decimal("10.000000"),
        max_executable_shares=Decimal("25.000000"),
        market_context_fresh=True,
        settlement_context_fresh=True,
    ),
)

assert side_edge_input.side == "yes"
assert side_edge_input.forecast_probability == Decimal("0.620000")
assert "team_crypto_btc" in side_edge_input.reason_codes
```

- [ ] **Step 2: Run forecast packet tests to verify failure**

```bash
python3 -m pytest -q tests/test_team_forecast_packet.py
```

Expected: import failure.

- [ ] **Step 3: Implement `TeamForecastEvidencePacket`**

Fields:

```python
evidence_id: str
team_id: str
market_slug: str
source_id: str
source_type: str
data_timestamp: datetime
data_freshness_seconds: int
evidence_type: str
evidence_text: str
weight: Decimal
reason_codes: tuple[str, ...]
paper_only: bool = True
report_only: bool = True
readonly: bool = True
```

Validation:

- `team_id` known,
- timestamp timezone-aware or normalized to UTC,
- `weight` quantized probability,
- no blank canonical fields,
- safety flags true.

- [ ] **Step 4: Implement `TeamForecastPacket`**

Fields:

```python
forecast_id: str
team_id: str
condition_id: str
market_slug: str
question: str
category_id: str
event_template: str
selected_side: str
forecast_probability: Decimal
confidence: Decimal
evidence_quality: Decimal
data_freshness_score: Decimal
resolution_risk: Decimal
base_rate: Decimal
market_implied_probability_observed: Decimal
reason_codes: tuple[str, ...]
memory_references: tuple[str, ...]
source_references: tuple[str, ...]
known_failure_modes: tuple[str, ...]
config_version: str
prompt_version: str
generated_at: datetime
paper_only: bool = True
report_only: bool = True
readonly: bool = True
```

Validation:

- `selected_side` is `yes` or `no`,
- all probability fields quantize to `0.000001`,
- `team_id`/`category_id` are known,
- safety flags true.

- [ ] **Step 5: Implement side-edge interface adapter**

Implement:

```python
@dataclass(frozen=True)
class TeamForecastCostInterfaceInput:
    side_price: Decimal
    fee_cost_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal
    capital_cost_per_share: Decimal
    requested_paper_shares: Decimal
    max_executable_shares: Decimal
    market_context_fresh: bool
    settlement_context_fresh: bool
```

Then implement:

```python
def team_forecast_to_side_edge_input(
    forecast: TeamForecastPacket,
    *,
    cost_input: TeamForecastCostInterfaceInput,
) -> PaperProbabilitySideEdgeInput:
    ...
```

This function only adapts team probability plus central cost/microstructure values into the existing side-edge reducer. It must not fetch Polymarket, connect to DB, or compute allocation.

- [ ] **Step 6: Run forecast packet tests**

```bash
python3 -m pytest -q tests/test_team_forecast_packet.py
```

Expected: pass.

- [ ] **Step 7: Commit Task 3**

```bash
git add src/polymarket_alpha_lab/team_forecast_packet.py tests/test_team_forecast_packet.py
git commit -m "feat: add team forecast packet"
```

---

### Task 4: DB Row Codecs

**Files:**
- Create: `src/polymarket_alpha_lab/team_forecast_db_row.py`
- Test: `tests/test_team_forecast_db_row.py`

**Interfaces:**
- Consumes:
  - `TeamMarketRouteReport`
  - `TeamForecastPacket`
  - `TeamForecastEvidencePacket`
  - `json_ready_no_floats()`
- Produces:
  - `TeamMarketRouteDbRow`
  - `TeamForecastDbRow`
  - `TeamForecastEvidenceDbRow`
  - `TeamForecastOutcomeDbRow`
  - `team_route_to_db_row()`, `team_route_from_db_row()`
  - `team_forecast_to_db_row()`, `team_forecast_from_db_row()`
  - `team_forecast_evidence_to_db_row()`, `team_forecast_evidence_from_db_row()`
  - `team_forecast_outcome_to_db_row()`, `team_forecast_outcome_from_db_row()`

- [ ] **Step 1: Write failing DB row codec tests**

Test each row:

- SHA-256 payload hash is lowercase 64 chars,
- payload contains Decimals as strings,
- payload contains no floats,
- row scalar fields match payload,
- recovered report/packet matches original,
- unsafe payload fields raise,
- false hard flags raise,
- malformed row bypassing constructor is rejected on recovery.

Include an outcome row test:

```python
outcome = TeamForecastOutcome(
    outcome_id="outcome-btc-1",
    forecast_id="forecast-btc-1",
    team_id="crypto_btc",
    market_slug="bitcoin-above-120k",
    actual_outcome="yes",
    resolved_at=GENERATED_AT,
    settlement_source="polymarket_public_resolution",
    forecast_error=Decimal("0.380000"),
    brier_score=Decimal("0.144400"),
    paper_pnl=Decimal("0.000000"),
    cost_adjusted_return=Decimal("0.000000"),
    directionally_correct=True,
    profitable_after_cost=False,
    resolution_dispute_flag=False,
    reason_codes=("settled_yes",),
)
```

- [ ] **Step 2: Run DB row tests to verify failure**

```bash
python3 -m pytest -q tests/test_team_forecast_db_row.py
```

Expected: import failure.

- [ ] **Step 3: Implement DB row dataclasses and codecs**

Use the existing pattern from `paper_probability_recommendation_queue_db_row.py`:

- `report_sha256` or packet-specific `payload_sha256`,
- scalar columns for filter/sort fields,
- `payload_json`,
- safety flags.

Required canonical row fields:

```python
payload_sha256: str
generated_at: datetime
team_id: str
market_slug: str
config_version: str
payload_json: dict[str, Any]
paper_only: bool = True
report_only: bool = True
readonly: bool = True
```

Evidence rows additionally include:

```python
forecast_id: str
evidence_id: str
source_id: str
data_timestamp: datetime
data_freshness_seconds: int
evidence_type: str
weight: Decimal
```

Outcome rows additionally include:

```python
outcome_id: str
forecast_id: str
resolved_at: datetime
actual_outcome: str
brier_score: Decimal
```

- [ ] **Step 4: Run DB row tests**

```bash
python3 -m pytest -q tests/test_team_forecast_db_row.py
```

Expected: pass.

- [ ] **Step 5: Commit Task 4**

```bash
git add src/polymarket_alpha_lab/team_forecast_db_row.py tests/test_team_forecast_db_row.py
git commit -m "feat: add team forecast db rows"
```

---

### Task 5: Supabase Config, Store, and psycopg Wrappers

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_team_forecast_config.py`
- Create: `src/polymarket_alpha_lab/team_forecast_store.py`
- Create: `src/polymarket_alpha_lab/team_forecast_psycopg.py`
- Test: `tests/test_supabase_team_forecast_config.py`
- Test: `tests/test_team_forecast_store.py`
- Test: `tests/test_team_forecast_psycopg.py`

**Interfaces:**
- Consumes:
  - DB row codecs from Task 4.
  - `validate_local_postgres_dsn`.
- Produces:
  - `SupabaseTeamForecastConfig`
  - `from_team_forecast_db_env(env: Mapping[str, str] | None = None)`
  - insert/load store functions for route, forecast, evidence, outcome rows.
  - psycopg wrappers that validate DSN before importing psycopg.

- [ ] **Step 1: Write config tests**

Tests must cover:

- disabled config can omit DSN,
- enabled config requires DSN,
- DSN is validated through `validate_local_postgres_dsn`,
- table names are simple lowercase identifiers,
- `repr()` redacts DSN.

- [ ] **Step 2: Write store tests**

Use fake connection/cursor classes. Test:

- inserts close cursors on success,
- insert errors close cursor and re-raise,
- rowcount must be 0 or 1,
- loads return newest-first for forecasts/outcomes,
- idempotent `ON CONFLICT (payload_sha256) DO NOTHING` for route/forecast/evidence,
- outcome idempotency uses `ON CONFLICT (outcome_id) DO NOTHING`.

- [ ] **Step 3: Write psycopg tests**

Tests must monkeypatch import path so:

- bad DSN raises before psycopg import,
- missing psycopg raises runtime error after DSN validation,
- connection commit/rollback/close semantics match existing adapters.

Use the same style as existing psycopg tests.

- [ ] **Step 4: Run tests to verify failure**

```bash
python3 -m pytest -q tests/test_supabase_team_forecast_config.py tests/test_team_forecast_store.py tests/test_team_forecast_psycopg.py
```

Expected: import failures.

- [ ] **Step 5: Implement config**

Implement one config object with one DSN and table names:

```python
TEAM_FORECAST_DB_ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED"
TEAM_FORECAST_DB_DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN"
TEAM_PROFILE_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE"
TEAM_ROUTE_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE"
TEAM_FORECAST_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE"
TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE"
TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE"
```

Default table names:

```python
team_profiles
team_market_routes
team_forecasts
team_forecast_evidence
team_forecast_outcomes
```

- [ ] **Step 6: Implement stores**

Implement connection-based functions:

```python
insert_team_market_route(connection, row, *, table_name)
insert_team_forecast(connection, row, *, table_name)
insert_team_forecast_evidence(connection, row, *, table_name)
insert_team_forecast_outcome(connection, row, *, table_name)
load_team_forecasts(connection, *, team_id=None, market_slug=None, limit=None, table_name)
load_team_forecast_outcomes(connection, *, team_id=None, market_slug=None, limit=None, table_name)
```

Validate table names and query params. Use parameterized SQL for values. Only table names may be interpolated after validation.

- [ ] **Step 7: Implement psycopg wrappers**

Functions:

```python
insert_team_forecast_with_psycopg(dsn: str, packet: TeamForecastPacket, *, table_name: str) -> TeamForecastDbRow
load_team_forecasts_with_psycopg(dsn: str, *, team_id: str | None = None, market_slug: str | None = None, limit: int | None = None, table_name: str) -> tuple[TeamForecastPacket, ...]
```

Validate DSN before `import psycopg`.

- [ ] **Step 8: Run persistence tests**

```bash
python3 -m pytest -q tests/test_supabase_team_forecast_config.py tests/test_team_forecast_store.py tests/test_team_forecast_psycopg.py
```

Expected: pass.

- [ ] **Step 9: Commit Task 5**

```bash
git add src/polymarket_alpha_lab/supabase_team_forecast_config.py src/polymarket_alpha_lab/team_forecast_store.py src/polymarket_alpha_lab/team_forecast_psycopg.py tests/test_supabase_team_forecast_config.py tests/test_team_forecast_store.py tests/test_team_forecast_psycopg.py
git commit -m "feat: persist team forecasts locally"
```

---

### Task 6: Outcome and Performance Summary

**Files:**
- Create: `src/polymarket_alpha_lab/team_performance_summary.py`
- Test: `tests/test_team_performance_summary.py`

**Interfaces:**
- Consumes:
  - `TeamForecastPacket`
  - `TeamForecastOutcome`
- Produces:
  - `TeamPerformanceSummaryConfig`
  - `TeamPerformanceSummaryRow`
  - `TeamPerformanceSummaryReport`
  - `build_team_performance_summary_report(forecasts, outcomes, *, config, generated_at)`

- [ ] **Step 1: Write failing performance tests**

Test:

- Brier score is independently calculated from forecast probability and outcome,
- unresolved forecasts are excluded from settled metrics,
- outcome idempotency is represented by unique `forecast_id`,
- trust multiplier stays `1.000000` until `min_trust_sample_count`,
- allocation multiplier stays neutral until `min_allocation_sample_count`,
- insufficient sample reason codes are present,
- false safety flags raise.

Representative assertions:

```python
assert row.settled_count == 2
assert row.average_brier_score == Decimal("0.170000")
assert row.team_trust_score == Decimal("1.000000")
assert "insufficient_trust_sample" in row.reason_codes
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python3 -m pytest -q tests/test_team_performance_summary.py
```

Expected: import failure.

- [ ] **Step 3: Implement performance summary dataclasses**

Config defaults:

```python
min_trust_sample_count: int = 30
min_allocation_sample_count: int = 50
config_version: str = "team-performance-summary-v0"
```

Rows grouped by `team_id` and `category_id`.

Computed fields:

```python
forecast_count
settled_count
directionally_correct_count
profitable_after_cost_count
average_brier_score
hit_rate
paper_pnl
cost_adjusted_return
team_trust_score
allocation_trust_score
reason_codes
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest -q tests/test_team_performance_summary.py
```

Expected: pass.

- [ ] **Step 5: Commit Task 6**

```bash
git add src/polymarket_alpha_lab/team_performance_summary.py tests/test_team_performance_summary.py
git commit -m "feat: add team performance summary"
```

---

### Task 7: Minimal Crypto BTC Workflow

**Files:**
- Create: `src/polymarket_alpha_lab/crypto_btc_team.py`
- Test: `tests/test_crypto_btc_team.py`

**Interfaces:**
- Consumes:
  - `TeamForecastPacket`
  - `TeamForecastEvidencePacket`
  - `TeamForecastCostInterfaceInput`
  - `team_forecast_to_side_edge_input`
- Produces:
  - `CryptoBtcTeamConfig`
  - `CryptoBtcEvidenceInput`
  - `build_crypto_btc_team_forecast(...)`

- [ ] **Step 1: Write failing BTC workflow tests**

Test a supplied-input BTC hit-price market:

```python
forecast, evidence_rows = build_crypto_btc_team_forecast(
    condition_id="condition-btc",
    market_slug="bitcoin-above-120k",
    question="Will Bitcoin hit 120000 before August 31?",
    event_template="btc_hit_price",
    evidence=(
        CryptoBtcEvidenceInput(
            source_id="btc_spot_reference",
            source_type="market_data",
            evidence_text="BTC spot trades below target with high realized volatility.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=120,
            evidence_type="spot_volatility",
            weight=Decimal("0.600000"),
            probability_impact=Decimal("0.020000"),
            reason_codes=("btc_spot_fresh",),
        ),
    ),
    base_probability=Decimal("0.600000"),
    config=CryptoBtcTeamConfig(config_version="crypto-btc-team-v0"),
    generated_at=GENERATED_AT,
)

assert forecast.team_id == "crypto_btc"
assert forecast.category_id == "finance.crypto.btc"
assert forecast.forecast_probability == Decimal("0.620000")
assert forecast.selected_side == "yes"
assert evidence_rows[0].team_id == "crypto_btc"
```

Also test:

- forecast clamps at `0.000000`/`1.000000`,
- stale evidence lowers data freshness score,
- empty evidence raises,
- unsafe side values raise.

- [ ] **Step 2: Run BTC tests to verify failure**

```bash
python3 -m pytest -q tests/test_crypto_btc_team.py
```

Expected: import failure.

- [ ] **Step 3: Implement supplied-input BTC workflow**

This is not a web-research agent. It consumes supplied evidence and produces the first team packet. Probability:

```python
forecast_probability = base_probability + sum(e.probability_impact for e in evidence)
```

Clamp and quantize to `0.000001`. Confidence:

```python
confidence = min(1, max(0, average evidence weight))
```

Evidence quality:

```python
evidence_quality = min(1, total evidence weight / evidence_count)
```

Data freshness score:

```python
1.000000 if max data_freshness_seconds <= 300
0.750000 if <= 3600
0.500000 if <= 21600
0.250000 otherwise
```

Selected side:

```python
"yes" if forecast_probability >= market_implied_probability_hint else "no"
```

For the first slice, include `market_implied_probability_hint: Decimal = Decimal("0.500000")` in config.

- [ ] **Step 4: Run BTC workflow tests**

```bash
python3 -m pytest -q tests/test_crypto_btc_team.py
```

Expected: pass.

- [ ] **Step 5: Commit Task 7**

```bash
git add src/polymarket_alpha_lab/crypto_btc_team.py tests/test_crypto_btc_team.py
git commit -m "feat: add crypto btc team workflow"
```

---

### Task 8: Scope Guards, Exports, and Docs

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_database_persistence_iron_rule.py`
- Modify: `tests/test_phase1_live_surface_guard.py`
- Create: `tests/test_team_framework_scope.py`
- Create: `docs/team-agent-framework.md`

**Interfaces:**
- Consumes all prior tasks.
- Produces public API exports and project guard coverage.

- [ ] **Step 1: Write scope tests**

Add `tests/test_team_framework_scope.py` to assert:

- new modules do not import forbidden live-trading/auth/order surfaces,
- team modules do not import `psycopg` directly except `team_forecast_psycopg.py`,
- team modules do not import Polymarket execution/order clients,
- no `float(` construction in team modules,
- no durable JSON helper accepts floats.

- [ ] **Step 2: Extend persistence iron rule tests**

Add the new DB modules to the local Supabase-only allowlist:

```python
TEAM_DB_MODULES = (
    "polymarket_alpha_lab.supabase_team_forecast_config",
    "polymarket_alpha_lab.team_forecast_store",
    "polymarket_alpha_lab.team_forecast_psycopg",
)
```

Assert all raw DSN use goes through `validate_local_postgres_dsn`.

- [ ] **Step 3: Extend live-surface guard**

Add new team modules to the static live-surface guard. The allowed occurrence of guarded words must be in explicit denial/guard code or docs, not implementation surfaces.

- [ ] **Step 4: Export stable API**

Add imports in `__init__.py` for:

```python
TeamProfile
build_default_team_profiles
TeamMarketRouteConfig
TeamMarketRouteInput
TeamMarketRouteReport
build_team_market_route_report
TeamForecastPacket
TeamForecastEvidencePacket
team_forecast_to_side_edge_input
TeamPerformanceSummaryReport
build_team_performance_summary_report
CryptoBtcTeamConfig
CryptoBtcEvidenceInput
build_crypto_btc_team_forecast
```

- [ ] **Step 5: Add docs**

Create `docs/team-agent-framework.md` covering:

- first slice scope,
- 10-team taxonomy,
- `crypto_btc` only runnable in this slice,
- central microstructure/cost/recommendation boundary,
- local Supabase persistence,
- sample-count gates,
- no live trading/order/auth/wallet/account mutation.

- [ ] **Step 6: Run guard tests**

```bash
python3 -m pytest -q tests/test_team_framework_scope.py tests/test_database_persistence_iron_rule.py tests/test_phase1_live_surface_guard.py tests/test_init.py
```

Expected: pass.

- [ ] **Step 7: Commit Task 8**

```bash
git add src/polymarket_alpha_lab/__init__.py tests/test_team_framework_scope.py tests/test_database_persistence_iron_rule.py tests/test_phase1_live_surface_guard.py docs/team-agent-framework.md tests/test_init.py
git commit -m "docs: document team framework boundaries"
```

---

## Final Verification

After all tasks land:

- [ ] Run targeted team tests:

```bash
python3 -m pytest -q \
  tests/test_team_taxonomy.py \
  tests/test_team_paper_guard.py \
  tests/test_team_market_router.py \
  tests/test_team_forecast_packet.py \
  tests/test_team_forecast_db_row.py \
  tests/test_supabase_team_forecast_config.py \
  tests/test_team_forecast_store.py \
  tests/test_team_forecast_psycopg.py \
  tests/test_team_performance_summary.py \
  tests/test_crypto_btc_team.py \
  tests/test_team_framework_scope.py
```

Expected: all pass.

- [ ] Run project-wide verification:

```bash
python3 -m pytest -q
python3 -m compileall -q src/polymarket_alpha_lab tests
git diff --check
codegraph sync
```

Expected: all commands pass.

- [ ] Run secret scan:

```bash
{ git diff --cached --unified=0 --diff-filter=ACMR -- .; git diff --unified=0 --diff-filter=ACMR -- .; git ls-files --others --exclude-standard | xargs -r sed -n '1,260p'; } | rg -n --pcre2 'ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}_[A-Za-z0-9_]{20,}|-----BEGIN [^-]*(PRIVATE KEY|OPENSSH PRIVATE KEY)-----' || true
```

Expected: no output.

- [ ] Request OpenCode review:

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 "Review the team framework BTC slice for Phase 1 paper-only safety, local Supabase persistence, Decimal-only JSON, and integration with the existing cost-aware pipeline. Return critical/important/minor findings only."
```

Expected: no critical findings; important findings are either fixed or explicitly rejected with technical rationale.

- [ ] Push:

```bash
git status --short --branch
git push origin main
```

Expected: branch pushed and clean.

## Self-Review Notes

- Spec coverage: this plan covers taxonomy, paper-only guard, router, forecast/evidence packets, persistence, outcome/performance summary, and one `crypto_btc` workflow.
- Deferred scope: all other teams, cross-team memory analogs, automated lesson promotion, source reliability scoring, and trust-weighted allocation are out of scope for this plan.
- Type consistency: the plan consistently uses `TeamForecastPacket`, `TeamForecastEvidencePacket`, `TeamMarketRouteRow`, `TeamForecastOutcome`, and `TeamPerformanceSummaryReport`.
- Safety: every durable object requires `paper_only`, `report_only`, `readonly`, `Decimal`, no floats, and local Supabase/Postgres persistence only.
