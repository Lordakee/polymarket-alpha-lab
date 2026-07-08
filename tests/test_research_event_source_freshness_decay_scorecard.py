from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_source_freshness_decay_scorecard import (
    DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION,
    ResearchEventSourceFreshnessDecayObservation,
    ResearchEventSourceFreshnessDecayReasonCodeCount,
    ResearchEventSourceFreshnessDecayScoreRow,
    ResearchEventSourceFreshnessDecayScorecardConfig,
    ResearchEventSourceFreshnessDecayScorecardReport,
    build_research_event_source_freshness_decay_scorecard,
    research_event_source_freshness_decay_scorecard_public_digest,
    research_event_source_freshness_decay_scorecard_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_event_source_freshness_decay_scorecard.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventSourceFreshnessDecayScorecardConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION
        ),
        "fresh_source_age_seconds": d("3600.000000"),
        "stale_source_age_seconds": d("86400.000000"),
        "target_update_cadence_seconds": d("21600.000000"),
        "stale_update_cadence_seconds": d("86400.000000"),
        "fresh_catalyst_age_seconds": d("3600.000000"),
        "stale_catalyst_age_seconds": d("86400.000000"),
        "fresh_contradiction_age_seconds": d("3600.000000"),
        "stale_contradiction_age_seconds": d("86400.000000"),
        "pass_freshness_decay_score": d("0.700000"),
        "watch_freshness_decay_score": d("0.400000"),
        "source_age_weight": d("0.350000"),
        "update_cadence_weight": d("0.250000"),
        "catalyst_recency_weight": d("0.200000"),
        "contradiction_age_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchEventSourceFreshnessDecayScorecardConfig(**values)


def observation(
    event_domain: str = "weather",
    evidence_ref: str = "https://raw.example/source_text/market-42/question",
    *,
    source_age_seconds: Decimal = d("1800.000000"),
    update_cadence_seconds: Decimal = d("3600.000000"),
    catalyst_age_seconds: Decimal = d("1800.000000"),
    contradiction_age_seconds: Decimal = d("86400.000000"),
    contradiction_present: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventSourceFreshnessDecayObservation:
    return ResearchEventSourceFreshnessDecayObservation(
        event_domain=event_domain,
        evidence_ref=evidence_ref,
        source_age_seconds=source_age_seconds,
        update_cadence_seconds=update_cadence_seconds,
        catalyst_age_seconds=catalyst_age_seconds,
        contradiction_age_seconds=contradiction_age_seconds,
        contradiction_present=contradiction_present,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventSourceFreshnessDecayScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventSourceFreshnessDecayScorecardReport:
    return build_research_event_source_freshness_decay_scorecard(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_scorecard_reduces_event_domains_to_pass_watch_block_deterministically() -> None:
    summary = report(
        (
            observation(
                "sports",
                "raw-market-id:0xabc/source_url",
                source_age_seconds=d("108000.000000"),
                update_cadence_seconds=d("108000.000000"),
                catalyst_age_seconds=d("108000.000000"),
                contradiction_age_seconds=d("1800.000000"),
                contradiction_present=True,
            ),
            observation("weather", "https://raw.example/source/001"),
            observation(
                "policy",
                "private-source-text-policy",
                source_age_seconds=d("21600.000000"),
                update_cadence_seconds=d("43200.000000"),
                catalyst_age_seconds=d("43200.000000"),
                contradiction_age_seconds=d("43200.000000"),
                contradiction_present=True,
            ),
            observation("weather", "https://raw.example/source/002"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION
    )
    assert summary.scorecard_status == "block"
    assert summary.domain_count == d("3.000000")
    assert summary.observation_count == d("4.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_freshness_decay_score == d("0.529167")
    assert summary.max_aggregate_source_age_seconds == d("108000.000000")
    assert summary.max_update_cadence_seconds == d("108000.000000")
    assert summary.max_catalyst_age_seconds == d("108000.000000")
    assert summary.min_contradiction_age_seconds == d("1800.000000")
    assert tuple(row.event_domain for row in summary.rows) == (
        "policy",
        "sports",
        "weather",
    )
    assert {row.status for row in summary.rows} == {"pass", "watch", "block"}
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    watched = summary.rows[0]
    assert type(watched) is ResearchEventSourceFreshnessDecayScoreRow
    assert watched.event_domain == "policy"
    assert watched.observation_count == d("1.000000")
    assert watched.aggregate_source_age_seconds == d("21600.000000")
    assert watched.update_cadence_seconds == d("43200.000000")
    assert watched.catalyst_age_seconds == d("43200.000000")
    assert watched.minimum_contradiction_age_seconds == d("43200.000000")
    assert watched.contradiction_count == d("1.000000")
    assert watched.source_age_score == d("0.750000")
    assert watched.update_cadence_score == d("0.500000")
    assert watched.catalyst_recency_score == d("0.500000")
    assert watched.contradiction_age_score == d("0.500000")
    assert watched.freshness_decay_score == d("0.587500")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "research_event_source_freshness_decay_scorecard_source_age_watch",
        "research_event_source_freshness_decay_scorecard_update_cadence_watch",
        "research_event_source_freshness_decay_scorecard_catalyst_recency_watch",
        "research_event_source_freshness_decay_scorecard_contradiction_age_watch",
        "research_event_source_freshness_decay_scorecard_score_watch",
    )

    blocked = summary.rows[1]
    assert blocked.event_domain == "sports"
    assert blocked.freshness_decay_score == ZERO
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "research_event_source_freshness_decay_scorecard_source_age_block",
        "research_event_source_freshness_decay_scorecard_update_cadence_block",
        "research_event_source_freshness_decay_scorecard_catalyst_recency_block",
        "research_event_source_freshness_decay_scorecard_contradiction_age_block",
        "research_event_source_freshness_decay_scorecard_score_block",
    )

    passed = summary.rows[2]
    assert passed.event_domain == "weather"
    assert passed.observation_count == d("2.000000")
    assert passed.freshness_decay_score == d("1.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == (
        "research_event_source_freshness_decay_scorecard_pass",
    )


def test_mildly_stale_source_age_watch_remains_valid_and_deterministic() -> None:
    source_row = observation(
        "weather",
        "https://raw.example/source/001",
        source_age_seconds=d("7200.000000"),
    )

    first_summary = report((source_row,))
    second_summary = report((source_row,))
    first_payload = research_event_source_freshness_decay_scorecard_public_payload(
        first_summary,
    )
    second_payload = research_event_source_freshness_decay_scorecard_public_payload(
        second_summary,
    )

    assert first_summary.public_digest == second_summary.public_digest
    assert first_payload == second_payload
    assert first_summary.scorecard_status == "watch"
    assert first_summary.pass_count == ZERO
    assert first_summary.watch_count == d("1.000000")
    assert first_summary.block_count == ZERO

    row = first_summary.rows[0]
    assert row.event_domain == "weather"
    assert row.source_age_score == d("0.916667")
    assert row.freshness_decay_score == d("0.970833")
    assert row.status == "watch"
    assert row.reason_codes == (
        "research_event_source_freshness_decay_scorecard_source_age_watch",
    )
    assert first_payload["rows"][0]["freshness_decay_score"] == "0.970833"
    assert first_payload["rows"][0]["status"] == "watch"


def test_empty_scorecard_blocks_as_report_only_workflow() -> None:
    summary = report(())

    assert summary.scorecard_status == "block"
    assert summary.domain_count == ZERO
    assert summary.observation_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_freshness_decay_score == ZERO
    assert summary.max_aggregate_source_age_seconds == ZERO
    assert summary.max_update_cadence_seconds == ZERO
    assert summary.max_catalyst_age_seconds == ZERO
    assert summary.min_contradiction_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchEventSourceFreshnessDecayReasonCodeCount(
            reason_code="research_event_source_freshness_decay_scorecard_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_event_source_freshness_decay_scorecard_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_digest_is_deterministic_decimal_only_and_public_safe() -> None:
    rows = (
        observation(
            "z-domain",
            "https://raw.example/source_url/market-42/question",
            source_age_seconds=d("21600.000000"),
            update_cadence_seconds=d("43200.000000"),
            catalyst_age_seconds=d("43200.000000"),
            contradiction_age_seconds=d("43200.000000"),
            contradiction_present=True,
        ),
        observation("a-domain", "source_text:private-market-slug"),
    )

    first_summary = report(rows)
    second_summary = report(tuple(reversed(rows)))
    first_payload = research_event_source_freshness_decay_scorecard_public_payload(
        first_summary,
    )
    second_payload = research_event_source_freshness_decay_scorecard_public_payload(
        second_summary,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["domain_count"] == "2.000000"
    assert first_payload["rows"][0]["event_domain"] == "a-domain"
    assert first_payload["rows"][0]["freshness_decay_score"] == "1.000000"
    assert first_payload["public_digest"] == first_summary.public_digest
    assert first_summary.public_digest == second_summary.public_digest
    assert first_summary.public_digest == (
        research_event_source_freshness_decay_scorecard_public_digest(first_summary)
    )
    assert first_summary.public_digest == (
        research_event_source_freshness_decay_scorecard_public_digest(first_payload)
    )
    assert len(first_summary.public_digest) == 64
    assert not any(isinstance(value, float) for value in walk_values(first_payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw.example",
        "source_url",
        "source_text",
        "market-42",
        "market-slug",
        "question",
        "private",
    ):
        assert leaked not in encoded.lower()

    tampered_payload = dict(first_payload)
    tampered_payload["scorecard_status"] = "pass"
    with pytest.raises(ValueError, match="public_digest"):
        research_event_source_freshness_decay_scorecard_public_payload(tampered_payload)

    leaky_payload = dict(first_payload)
    leaky_payload["market_id"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe public payload key"):
        research_event_source_freshness_decay_scorecard_public_payload(leaky_payload)

    leaky_payload = dict(first_payload)
    leaky_payload["workflow_note"] = "buy size recommendation"
    with pytest.raises(ValueError, match="unsafe public payload value"):
        research_event_source_freshness_decay_scorecard_public_payload(leaky_payload)

    numeric_payload = dict(first_payload)
    numeric_payload["domain_count"] = 2
    with pytest.raises(ValueError, match="Decimal strings"):
        research_event_source_freshness_decay_scorecard_public_payload(numeric_payload)


def test_public_contracts_validate_exact_types_flags_and_frozen_dataclasses() -> None:
    assert is_dataclass(ResearchEventSourceFreshnessDecayScorecardConfig)
    assert is_dataclass(ResearchEventSourceFreshnessDecayObservation)
    assert is_dataclass(ResearchEventSourceFreshnessDecayScoreRow)
    assert is_dataclass(ResearchEventSourceFreshnessDecayReasonCodeCount)
    assert is_dataclass(ResearchEventSourceFreshnessDecayScorecardReport)

    cfg = config()
    source_row = observation()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.source_age_seconds = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].freshness_decay_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="fresh_source_age_seconds"):
        config(fresh_source_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_source_age_seconds"):
        config(
            fresh_source_age_seconds=d("86400.000000"),
            stale_source_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="pass_freshness_decay_score"):
        config(pass_freshness_decay_score=d("0.300000"))
    with pytest.raises(ValueError, match="source_age_weight"):
        config(source_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="update_cadence_weight"):
        config(update_cadence_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="event_domain"):
        observation(_StringSubclass("weather"))
    with pytest.raises(ValueError, match="event_domain"):
        observation("market_question")
    with pytest.raises(ValueError, match="source_age_seconds"):
        observation(source_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="catalyst_age_seconds"):
        observation(catalyst_age_seconds=_DecimalSubclass("1800.000000"))
    with pytest.raises(ValueError, match="contradiction_present"):
        observation(contradiction_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_research_event_source_freshness_decay_scorecard(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_source_freshness_decay_scorecard(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready_summary = report((observation(),))
    ready = ready_summary.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_event_source_freshness_decay_scorecard_pass",
                "research_event_source_freshness_decay_scorecard_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="block")
    with pytest.raises(ValueError, match="freshness_decay_score"):
        replace(ready, freshness_decay_score=ZERO)
    with pytest.raises(ValueError, match="pass_count"):
        replace(ready_summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="public_digest"):
        replace(ready_summary, public_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        replace(ready_summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ready_summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(ready_summary, readonly=False)


def test_public_numeric_fields_are_exact_decimals() -> None:
    source_row = observation()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_owned_module_has_no_io_store_execution_or_research_action_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "wallet",
        "order",
        "trade",
        "live",
        "recommend",
        "sizing",
        "position",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
        "connect(",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
