from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_resolution_review_capacity_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_resolution_review_capacity_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-resolution-review-capacity-report-v0",
        "pass_max_deadline_proximity": d("0.300000"),
        "watch_max_deadline_proximity": d("0.700000"),
        "pass_max_evidence_age_seconds": d("21600.000000"),
        "watch_max_evidence_age_seconds": d("86400.000000"),
        "pass_max_oracle_lag_seconds": d("1200.000000"),
        "watch_max_oracle_lag_seconds": d("7200.000000"),
        "watch_min_team_capacity": d("0.500000"),
        "pass_min_team_capacity": d("0.750000"),
        "watch_min_domain_expertise": d("0.500000"),
        "pass_min_domain_expertise": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamResolutionReviewCapacityConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "review_team_key": "alpha_review",
        "domain_key": "macro_rates",
        "aggregate_deadline_proximity": d("0.200000"),
        "evidence_age_seconds": d("3600.000000"),
        "oracle_lag_seconds": d("600.000000"),
        "team_capacity": d("0.900000"),
        "domain_expertise": d("0.850000"),
        "observed_at": GENERATED_AT - timedelta(hours=1),
    }
    values.update(overrides)
    return module.ResearchTeamResolutionReviewCapacityInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_resolution_review_capacity_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"public payload numeric must be Decimal-derived: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def assert_no_forbidden_public_surface(value: object) -> None:
    forbidden = (
        "raw",
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = key.lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_resolution_capacity_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_RESOLUTION_REVIEW_CAPACITY_REPORT_CONFIG_VERSION == (
        "research-team-resolution-review-capacity-report-v0"
    )
    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_RESOLUTION_REVIEW_CAPACITY_REPORT_CONFIG_VERSION",
        "ResearchTeamResolutionReviewCapacityConfig",
        "ResearchTeamResolutionReviewCapacityInput",
        "ResearchTeamResolutionReviewCapacityReasonCodeCount",
        "ResearchTeamResolutionReviewCapacityReport",
        "ResearchTeamResolutionReviewCapacityRow",
        "build_research_team_resolution_review_capacity_report",
        "research_team_resolution_review_capacity_report_payload",
    )

    defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamResolutionReviewCapacityConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True


def test_summarizes_resolution_review_capacity_into_pass_watch_and_block_rows() -> None:
    report = build_report(
        signal(
            review_team_key="beta_review",
            domain_key="crypto_stables",
            aggregate_deadline_proximity=d("0.500000"),
            evidence_age_seconds=d("40000.000000"),
            oracle_lag_seconds=d("5000.000000"),
            team_capacity=d("0.600000"),
            domain_expertise=d("0.650000"),
        ),
        signal(
            review_team_key="gamma_review",
            domain_key="sports_soccer",
            aggregate_deadline_proximity=d("0.900000"),
            evidence_age_seconds=d("100000.000000"),
            oracle_lag_seconds=d("10000.000000"),
            team_capacity=d("0.200000"),
            domain_expertise=d("0.300000"),
        ),
        signal(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-team-resolution-review-capacity-report-v0"
    assert report.status == "block"
    assert report.review_scope_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_deadline_proximity == d("0.533333")
    assert report.average_evidence_age_seconds == d("47866.666667")
    assert report.average_oracle_lag_seconds == d("5200.000000")
    assert report.average_team_capacity == d("0.566667")
    assert report.average_domain_expertise == d("0.600000")
    assert report.average_capacity_score == d("0.507840")
    assert report.lowest_capacity_score == d("0.120000")
    assert report.reason_codes == (
        "resolution_review_capacity_report_block_rows",
        "resolution_review_capacity_report_watch_rows",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple((row.review_team_key, row.domain_key) for row in report.rows) == (
        ("alpha_review", "macro_rates"),
        ("beta_review", "crypto_stables"),
        ("gamma_review", "sports_soccer"),
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert tuple(row.capacity_score for row in report.rows) == (
        d("0.885000"),
        d("0.518519"),
        d("0.120000"),
    )
    assert report.rows[0].reason_codes == ("resolution_review_capacity_pass",)
    assert report.rows[1].reason_codes == (
        "deadline_proximity_watch",
        "evidence_age_watch",
        "oracle_lag_watch",
        "team_capacity_watch",
        "domain_expertise_watch",
    )
    assert report.rows[2].reason_codes == (
        "deadline_proximity_block",
        "evidence_age_block",
        "oracle_lag_block",
        "team_capacity_block",
        "domain_expertise_block",
    )

    reason_counts = {item.reason_code: item for item in report.reason_code_counts}
    assert reason_counts["resolution_review_capacity_pass"].count == d("1.000000")
    assert reason_counts["resolution_review_capacity_pass"].review_scope_ratio == d(
        "0.333333",
    )
    assert reason_counts["deadline_proximity_watch"].count == d("1.000000")
    assert reason_counts["deadline_proximity_block"].count == d("1.000000")


def test_empty_report_is_public_block_without_private_detail() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.review_scope_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_deadline_proximity == d("0.000000")
    assert report.average_evidence_age_seconds == d("0.000000")
    assert report.average_oracle_lag_seconds == d("0.000000")
    assert report.average_team_capacity == d("0.000000")
    assert report.average_domain_expertise == d("0.000000")
    assert report.average_capacity_score == d("0.000000")
    assert report.lowest_capacity_score == d("0.000000")
    assert report.reason_codes == ("resolution_review_capacity_no_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rejects_non_decimal_inputs_unsafe_identifiers_and_mutation() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        signal(aggregate_deadline_proximity=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Decimal"):
        signal(team_capacity=_DecimalSubclass("0.100000"))

    with pytest.raises(TypeError, match="datetime"):
        signal(observed_at="2026-07-08T11:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))

    with pytest.raises(TypeError, match="str"):
        signal(review_team_key=_StringSubclass("alpha_review"))

    with pytest.raises(ValueError, match="UTC-aware"):
        signal(observed_at=datetime(2026, 7, 8, 11, 0))

    with pytest.raises(ValueError, match="whole second"):
        signal(observed_at=datetime(2026, 7, 8, 11, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(ValueError, match="nonnegative"):
        signal(evidence_age_seconds=d("-1.000000"))

    with pytest.raises(ValueError, match="unit interval"):
        signal(aggregate_deadline_proximity=d("1.000001"))

    with pytest.raises(ValueError, match="public-safe"):
        signal(domain_key="market_slug")

    with pytest.raises(ValueError, match="public-safe"):
        signal(review_team_key="source_team")

    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        signal(readonly=False)

    frozen = signal()
    with pytest.raises(FrozenInstanceError):
        frozen.team_capacity = d("0.100000")  # type: ignore[misc]

    report = build_report(signal())
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    assert replace(frozen, team_capacity=d("0.700000")).team_capacity == d("0.700000")


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    first = build_report(
        signal(review_team_key="beta_review", domain_key="crypto_stables"),
        signal(review_team_key="alpha_review", domain_key="macro_rates"),
    )
    second = build_report(
        signal(review_team_key="alpha_review", domain_key="macro_rates"),
        signal(review_team_key="beta_review", domain_key="crypto_stables"),
    )

    first_payload = module.research_team_resolution_review_capacity_report_payload(first)
    second_payload = module.research_team_resolution_review_capacity_report_payload(second)

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":"))
    assert_no_int_or_float_values(first_payload)
    assert_no_forbidden_public_surface(first_payload)

    digest = first_payload["derived_validation_digest"]
    assert isinstance(digest, str)
    assert len(digest) == 64
    assert all(character in "0123456789abcdef" for character in digest)

    with pytest.raises(ValueError, match="digest"):
        module.research_team_resolution_review_capacity_report_payload(
            dict(first_payload, pass_count="9.000000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        module.research_team_resolution_review_capacity_report_payload(
            dict(first_payload, paper_only=False),
        )


def test_module_source_has_no_write_or_execution_surfaces() -> None:
    module_ast = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "asyncio",
        "http",
        "os",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "websocket",
    }
    forbidden_call_names = {
        "buy",
        "commit",
        "connect",
        "delete",
        "execute",
        "insert",
        "mutate",
        "open",
        "patch",
        "place_order",
        "post",
        "put",
        "send",
        "sell",
        "submit",
        "trade",
        "update",
        "write",
    }

    for node in ast.walk(module_ast):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            assert root not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
