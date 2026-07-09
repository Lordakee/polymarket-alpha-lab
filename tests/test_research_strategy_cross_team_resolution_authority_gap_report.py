from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_cross_team_resolution_authority_gap_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_cross_team_resolution_authority_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "cross-team resolution authority gap module is missing"
    return importlib.import_module(MODULE_NAME)


def config(mod: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            mod.DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
        ),
        "min_pass_team_coverage_ratio": d("0.750000"),
        "min_watch_team_coverage_ratio": d("0.500000"),
        "min_pass_alignment_score": d("0.700000"),
        "min_watch_alignment_score": d("0.450000"),
        "min_pass_rule_mapping_score": d("0.750000"),
        "min_watch_rule_mapping_score": d("0.500000"),
        "max_pass_conflict_severity": d("0.200000"),
        "max_watch_conflict_severity": d("0.500000"),
        "max_pass_latest_observed_age_seconds": d("3600.000000"),
        "max_watch_latest_observed_age_seconds": d("86400.000000"),
        "max_pass_unresolved_dependency_count": d("0.000000"),
        "max_watch_unresolved_dependency_count": d("2.000000"),
    }
    values.update(overrides)
    return mod.ResearchStrategyCrossTeamResolutionAuthorityGapConfig(**values)


def evidence(
    mod: Any,
    *,
    resolution_ref: str = "resolution-alpha",
    team_ref: str = "team-alpha",
    resolver_ref: str = "resolver-alpha",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    team_coverage_ratio: Decimal = d("0.900000"),
    alignment_score: Decimal = d("0.850000"),
    rule_mapping_score: Decimal = d("0.900000"),
    conflict_severity: Decimal = d("0.100000"),
    unresolved_dependency_count: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return mod.ResearchStrategyCrossTeamResolutionAuthorityGapEvidence(
        resolution_ref=resolution_ref,
        team_ref=team_ref,
        resolver_ref=resolver_ref,
        observed_at=observed_at,
        team_coverage_ratio=team_coverage_ratio,
        alignment_score=alignment_score,
        rule_mapping_score=rule_mapping_score,
        conflict_severity=conflict_severity,
        unresolved_dependency_count=unresolved_dependency_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    mod: Any,
    *items: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return mod.build_research_strategy_cross_team_resolution_authority_gap_report(
        items,
        config=cfg or config(mod),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def payload_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).lower()


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"raw numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_decimal_public_fields(value: object) -> None:
    assert is_dataclass(value)
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"} or item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_decimal_public_fields(nested)
            continue
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_seconds",
                "_severity",
            ),
        ):
            assert type(item) is Decimal


def test_scores_cross_team_resolution_authority_gaps_deterministically() -> None:
    mod = module()
    summary = report(
        mod,
        evidence(
            mod,
            resolution_ref="resolution-pass",
            team_ref="team-beta",
            resolver_ref="resolver-beta",
            team_coverage_ratio=d("0.800000"),
            alignment_score=d("0.950000"),
            rule_mapping_score=d("0.800000"),
        ),
        evidence(mod, resolution_ref="resolution-pass"),
        evidence(
            mod,
            resolution_ref="resolution-watch",
            team_ref="team-watch",
            resolver_ref="resolver-watch",
            observed_at=GENERATED_AT - timedelta(hours=2),
            team_coverage_ratio=d("0.650000"),
            alignment_score=d("0.650000"),
            rule_mapping_score=d("0.700000"),
            conflict_severity=d("0.300000"),
            unresolved_dependency_count=d("1.000000"),
            reason_codes=("manual_review_requested",),
        ),
        evidence(
            mod,
            resolution_ref="resolution-block",
            team_ref="team-block",
            resolver_ref="resolver-block",
            observed_at=GENERATED_AT - timedelta(days=2),
            team_coverage_ratio=d("0.400000"),
            alignment_score=d("0.300000"),
            rule_mapping_score=d("0.400000"),
            conflict_severity=d("0.700000"),
            unresolved_dependency_count=d("4.000000"),
            reason_codes=("manual_review_requested",),
        ),
    )

    assert mod.RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(summary) is mod.ResearchStrategyCrossTeamResolutionAuthorityGapReport
    assert summary.status == "block"
    assert summary.resolution_count == d("3.000000")
    assert summary.evidence_count == d("4.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_resolution_gap_score == d("0.385749")
    assert summary.highest_resolution_gap_score == d("0.766667")
    assert summary.oldest_latest_observed_age_seconds == d("172800.000000")
    assert summary.reason_codes == (
        "resolution_authority_gap_block",
        "resolution_authority_gap_watch",
        "resolution_authority_gap_pass",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert set(summary.derived_validation_digest) <= set("0123456789abcdef")
    assert_decimal_public_fields(summary)

    assert tuple(row.status for row in summary.rows) == ("block", "pass", "watch")
    blocked, passed, watched = summary.rows

    assert blocked.resolution_gap_score == d("0.766667")
    assert blocked.reason_codes == (
        "team_coverage_block",
        "alignment_block",
        "rule_mapping_block",
        "conflict_severity_block",
        "latest_observed_age_block",
        "unresolved_dependency_block",
        "input_manual_review_requested",
    )

    assert passed.evidence_count == d("2.000000")
    assert passed.team_count == d("2.000000")
    assert passed.resolver_count == d("2.000000")
    assert passed.average_team_coverage_ratio == d("0.850000")
    assert passed.average_alignment_score == d("0.900000")
    assert passed.average_rule_mapping_score == d("0.850000")
    assert passed.resolution_gap_score == d("0.083333")
    assert passed.reason_codes == ("resolution_authority_gap_pass",)

    assert watched.resolution_gap_score == d("0.307246")
    assert watched.reason_codes == (
        "team_coverage_watch",
        "alignment_watch",
        "rule_mapping_watch",
        "conflict_severity_watch",
        "latest_observed_age_watch",
        "unresolved_dependency_watch",
        "input_manual_review_requested",
    )

    same_summary = report(
        mod,
        evidence(
            mod,
            resolution_ref="resolution-block",
            team_ref="team-block",
            resolver_ref="resolver-block",
            observed_at=GENERATED_AT - timedelta(days=2),
            team_coverage_ratio=d("0.400000"),
            alignment_score=d("0.300000"),
            rule_mapping_score=d("0.400000"),
            conflict_severity=d("0.700000"),
            unresolved_dependency_count=d("4.000000"),
            reason_codes=("manual_review_requested",),
        ),
        evidence(mod, resolution_ref="resolution-pass"),
        evidence(
            mod,
            resolution_ref="resolution-watch",
            team_ref="team-watch",
            resolver_ref="resolver-watch",
            observed_at=GENERATED_AT - timedelta(hours=2),
            team_coverage_ratio=d("0.650000"),
            alignment_score=d("0.650000"),
            rule_mapping_score=d("0.700000"),
            conflict_severity=d("0.300000"),
            unresolved_dependency_count=d("1.000000"),
            reason_codes=("manual_review_requested",),
        ),
        evidence(
            mod,
            resolution_ref="resolution-pass",
            team_ref="team-beta",
            resolver_ref="resolver-beta",
            team_coverage_ratio=d("0.800000"),
            alignment_score=d("0.950000"),
            rule_mapping_score=d("0.800000"),
        ),
    )
    assert same_summary == summary


def test_empty_input_returns_blocked_report_only_snapshot() -> None:
    mod = module()
    summary = report(mod)

    assert summary.status == "block"
    assert summary.resolution_count == d("0.000000")
    assert summary.evidence_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("resolution_authority_gap_empty",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_is_public_deterministic_decimal_only_and_digest_validated() -> None:
    mod = module()
    summary = report(
        mod,
        evidence(
            mod,
            resolution_ref=(
                "raw-candidate-market-id-slug-question-"
                "https://example.invalid/source-text"
            ),
            team_ref="team-wallet-order-trade-sizing-hidden",
            resolver_ref="resolver-token-secret-dsn-table-name",
        ),
    )

    payload = mod.research_strategy_cross_team_resolution_authority_gap_report_payload(
        summary,
    )

    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == summary.derived_validation_digest
    assert (
        mod.research_strategy_cross_team_resolution_authority_gap_report_payload(summary)
        == payload
    )
    assert_no_raw_numeric_payload_values(payload)
    assert payload["rows"][0]["gap_score"] == "0.075000"
    assert payload["rows"][0]["resolution_key"].startswith("resolution:")
    assert payload["rows"][0]["team_keys"][0].startswith("team:")
    assert payload["rows"][0]["resolver_keys"][0].startswith("resolver:")

    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "source-text",
        "dsn",
        "table-name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "secret",
        "raw-",
    )
    encoded = payload_text(payload)
    assert all(fragment not in encoded for fragment in forbidden_fragments)


def test_payload_rejects_digest_mismatch_and_public_leakage() -> None:
    mod = module()
    summary = report(mod, evidence(mod))

    with pytest.raises(ValueError, match="digest"):
        mod.research_strategy_cross_team_resolution_authority_gap_report_payload(
            replace(summary, derived_validation_digest="0" * 64),
        )

    with pytest.raises(ValueError, match="unsafe public payload|reason_codes"):
        replace(
            summary,
            reason_codes=("candidate_market_leak", "resolution_authority_gap_pass"),
            derived_validation_digest="",
        )


def test_validation_is_strict_decimal_frozen_and_report_only() -> None:
    mod = module()
    summary = report(mod, evidence(mod))

    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].resolution_gap_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="min_pass_team_coverage_ratio"):
        config(mod, min_pass_team_coverage_ratio=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_team_coverage_ratio"):
        config(mod, min_watch_team_coverage_ratio=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(mod, evidence(mod), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            mod,
            evidence(mod),
            generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(mod, evidence(mod, observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(mod), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_owned_module_has_no_db_network_wallet_order_or_live_trading_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "dsn",
        "database",
        "table_name",
        "wallet",
        "order",
        "trade",
        "trading",
        "position_size",
        "sizing",
        "recommendation",
        "api_key",
        "bearer",
        "open(",
        "connect(",
    )

    assert all(term not in source for term in forbidden_terms)
