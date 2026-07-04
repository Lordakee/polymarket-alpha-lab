from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

import polymarket_alpha_lab.strategy_recommendation_actionability_triage as triage_module
from polymarket_alpha_lab.strategy_recommendation_actionability_triage import (
    StrategyRecommendationActionabilityTriageConfig,
    StrategyRecommendationActionabilityTriageReport,
    StrategyRecommendationArtifact,
    build_strategy_recommendation_actionability_triage_report,
    strategy_recommendation_actionability_triage_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CONFIG = StrategyRecommendationActionabilityTriageConfig(
    config_version="strategy-recommendation-actionability-triage-v0",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _MissingOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _artifact(
    market_slug: str,
    *,
    artifact_id: str | None = None,
    status: str = "watch",
    severity_score: Decimal = d("0.100000"),
    confidence_ratio: Decimal = d("0.500000"),
    generated_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationArtifact:
    return StrategyRecommendationArtifact(
        artifact_id=artifact_id if artifact_id is not None else f"{market_slug}-{status}",
        market_slug=market_slug,
        status=status,
        severity_score=severity_score,
        confidence_ratio=confidence_ratio,
        generated_at=generated_at,
        reason_codes=reason_codes if reason_codes is not None else (f"{status}_reason",),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *artifacts: StrategyRecommendationArtifact,
    generated_at: datetime = GENERATED_AT,
    config: StrategyRecommendationActionabilityTriageConfig = CONFIG,
) -> StrategyRecommendationActionabilityTriageReport:
    return build_strategy_recommendation_actionability_triage_report(
        artifacts,
        config=config,
        generated_at=generated_at,
    )


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return tuple(values)
    return (value,)


def test_actionability_triage_empty_input_is_report_only() -> None:
    report = _report(
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "strategy-recommendation-actionability-triage-v0"
    assert report.triage_status == "empty"
    assert report.artifact_count == d("0")
    assert report.row_count == d("0")
    assert report.actionable_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.actionable_ratio == d("0.000000")
    assert report.watch_ratio == d("0.000000")
    assert report.blocked_ratio == d("0.000000")
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_actionability_triage_mixed_artifacts_reduce_to_rows() -> None:
    report = _report(
        _artifact(
            "market-b",
            artifact_id="a1",
            status="actionable",
            severity_score=d("0.200000"),
            confidence_ratio=d("0.800000"),
            reason_codes=("edge_present",),
        ),
        _artifact(
            "market-a",
            artifact_id="b1",
            status="blocked",
            severity_score=d("0.900000"),
            confidence_ratio=d("0.500000"),
            reason_codes=("missing_evidence", "stale_probability"),
        ),
        _artifact(
            "market-a",
            artifact_id="b2",
            status="blocked",
            severity_score=d("0.700000"),
            confidence_ratio=d("0.400000"),
            reason_codes=("missing_evidence",),
        ),
        _artifact(
            "market-c",
            artifact_id="w1",
            status="watch",
            severity_score=d("0.500000"),
            confidence_ratio=d("0.600000"),
            reason_codes=("thin_liquidity",),
        ),
        _artifact(
            "market-a",
            artifact_id="w2",
            status="watch",
            severity_score=d("0.800000"),
            confidence_ratio=d("0.700000"),
            reason_codes=("cost_buffer_needed",),
        ),
    )

    assert report.triage_status == "blocked"
    assert report.artifact_count == d("5")
    assert report.row_count == d("4")
    assert report.actionable_count == d("1")
    assert report.watch_count == d("2")
    assert report.blocked_count == d("2")
    assert report.actionable_ratio == d("0.200000")
    assert report.watch_ratio == d("0.400000")
    assert report.blocked_ratio == d("0.400000")
    assert tuple((row.status, row.market_slug) for row in report.rows) == (
        ("blocked", "market-a"),
        ("watch", "market-a"),
        ("watch", "market-c"),
        ("actionable", "market-b"),
    )

    blocked = report.rows[0]
    assert blocked.artifact_count == d("2")
    assert blocked.max_severity_score == d("0.900000")
    assert blocked.mean_confidence_ratio == d("0.450000")
    assert blocked.latest_artifact_at == GENERATED_AT
    assert blocked.reason_codes == ("missing_evidence", "stale_probability")
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("missing_evidence", d("2")),
        ("cost_buffer_needed", d("1")),
        ("edge_present", d("1")),
        ("stale_probability", d("1")),
        ("thin_liquidity", d("1")),
    )


def test_actionability_triage_sorting_is_stable_by_status_severity_market() -> None:
    report = _report(
        _artifact(
            "zeta",
            artifact_id="z",
            status="blocked",
            severity_score=d("0.500000"),
        ),
        _artifact(
            "alpha",
            artifact_id="a",
            status="blocked",
            severity_score=d("0.800000"),
        ),
        _artifact(
            "beta",
            artifact_id="b",
            status="blocked",
            severity_score=d("0.800000"),
        ),
        _artifact(
            "alpha",
            artifact_id="w",
            status="watch",
            severity_score=d("0.900000"),
        ),
        _artifact(
            "alpha",
            artifact_id="x",
            status="actionable",
            severity_score=d("0.990000"),
        ),
    )

    assert tuple((row.status, row.market_slug, row.max_severity_score) for row in report.rows) == (
        ("blocked", "alpha", d("0.800000")),
        ("blocked", "beta", d("0.800000")),
        ("blocked", "zeta", d("0.500000")),
        ("watch", "alpha", d("0.900000")),
        ("actionable", "alpha", d("0.990000")),
    )


def test_actionability_triage_payload_uses_decimal_strings_and_no_floats() -> None:
    report = _report(
        _artifact(
            "market-a",
            status="actionable",
            severity_score=d("0.333333"),
            confidence_ratio=d("0.666667"),
        ),
    )

    payload = strategy_recommendation_actionability_triage_payload(report)
    values = _walk_values(payload)

    assert payload["artifact_count"] == "1"
    assert payload["actionable_ratio"] == "1.000000"
    assert payload["rows"][0]["max_severity_score"] == "0.333333"
    assert payload["rows"][0]["mean_confidence_ratio"] == "0.666667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in values)
    json.dumps(payload, sort_keys=True)


def test_actionability_triage_rejects_invalid_inputs_and_consistency() -> None:
    with pytest.raises(ValueError, match="status"):
        _artifact("market-a", status="ready")
    with pytest.raises(ValueError, match="market_slug"):
        _artifact(" market-a", artifact_id="bad-market-slug")
    with pytest.raises(ValueError, match="severity_score"):
        _artifact("market-a", severity_score=d("-0.000001"))
    with pytest.raises(ValueError, match="confidence_ratio"):
        _artifact("market-a", confidence_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="confidence_ratio"):
        _artifact("market-a", confidence_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="severity_score"):
        _artifact("market-a", severity_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        _artifact("market-a", reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        _artifact("market-a", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _artifact("market-a", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _artifact("market-a", readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        _artifact("market-a", generated_at=datetime(2026, 7, 2))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        _artifact(
            "market-a",
            generated_at=datetime(2026, 7, 2, tzinfo=_MissingOffsetTZ()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _artifact(
            "market-a",
            generated_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        _report(
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_MissingOffsetTZ()),
        )
    with pytest.raises(ValueError, match="config"):
        build_strategy_recommendation_actionability_triage_report(
            (),
            config="bad",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    report = _report(_artifact("market-a", status="watch"))
    with pytest.raises(ValueError, match="artifact_count"):
        replace(report, artifact_count=d("2"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2"))
    with pytest.raises(ValueError, match="triage_status"):
        replace(report, triage_status="blocked")


def test_actionability_triage_rejects_sensitive_values_without_leaking_them() -> None:
    sensitive_market = "service-role-secret"
    with pytest.raises(ValueError, match="unsafe") as market_error:
        _artifact(sensitive_market, artifact_id="safe-artifact")
    assert sensitive_market not in str(market_error.value).lower()

    sensitive_reason = "api_key_exposed"
    with pytest.raises(ValueError, match="unsafe") as reason_error:
        _artifact("market-a", reason_codes=(sensitive_reason,))
    assert sensitive_reason not in str(reason_error.value)

    sensitive_config = "token_config"
    with pytest.raises(ValueError, match="unsafe") as config_error:
        StrategyRecommendationActionabilityTriageConfig(config_version=sensitive_config)
    assert sensitive_config not in str(config_error.value)


def test_actionability_triage_payload_rechecks_boundary_after_tampering() -> None:
    flag_tampered = _report(_artifact("market-a"))
    object.__setattr__(flag_tampered, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_actionability_triage_payload(flag_tampered)

    numeric_tampered = _report(_artifact("market-a"))
    object.__setattr__(numeric_tampered, "actionable_ratio", 0.1)
    with pytest.raises(ValueError, match="float"):
        strategy_recommendation_actionability_triage_payload(numeric_tampered)

    value_tampered = _report(_artifact("market-a"))
    object.__setattr__(value_tampered.rows[0], "reason_codes", ("private_key_seen",))
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_actionability_triage_payload(value_tampered)


def test_actionability_triage_public_dataclasses_are_frozen() -> None:
    artifact = _artifact("market-a")
    report = _report(artifact)

    with pytest.raises(FrozenInstanceError):
        artifact.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.triage_status = "blocked"  # type: ignore[misc]


def test_actionability_triage_module_stays_report_only_scope() -> None:
    source = inspect.getsource(triage_module)
    lowered_source = source.lower()
    forbidden_markers = (
        "net" + "work",
        "li" + "ve",
        "tra" + "de",
        "au" + "th",
        "wall" + "et",
        "bro" + "ker",
        "ord" + "er",
        "can" + "cel",
        "rep" + "lace",
        "sig" + "ning",
        "adv" + "ice",
        "private" + "_key",
        "api" + "_key",
        "sec" + "ret",
    )

    assert all(marker not in lowered_source for marker in forbidden_markers)

    tree = ast.parse(source)
    imports = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports.isdisjoint(
        {
            "asyncio",
            "httpx",
            "pathlib",
            "pickle",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
        },
    )

    forbidden_name_calls = {"eval", "exec", "open", "compile", "__import__"}
    forbidden_attribute_calls = {
        "connect",
        "execute",
        "post",
        "put",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_name_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attribute_calls
