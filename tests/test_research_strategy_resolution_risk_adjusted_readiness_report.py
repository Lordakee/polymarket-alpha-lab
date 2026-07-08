from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_resolution_risk_adjusted_readiness_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_resolution_risk_adjusted_readiness_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "research-strategy-resolution-risk-adjusted-readiness-report-v1"
        ),
        "pass_component_score": d("0.700000"),
        "watch_component_score": d("0.400000"),
        "pass_readiness_score": d("0.750000"),
        "watch_readiness_score": d("0.500000"),
        "watch_contradiction_pressure": d("0.300000"),
        "block_contradiction_pressure": d("0.600000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyResolutionRiskAdjustedReadinessConfig(**values)


def input_row(
    label: str = "packet-alpha",
    *,
    settlement_clarity_score: Decimal = d("0.900000"),
    quorum_score: Decimal = d("0.800000"),
    contradiction_pressure_score: Decimal = d("0.100000"),
    event_timing_score: Decimal = d("0.850000"),
    risk_adjustment_quality: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyResolutionRiskAdjustedReadinessInput(
        review_packet_label=label,
        settlement_clarity_score=settlement_clarity_score,
        quorum_score=quorum_score,
        contradiction_pressure_score=contradiction_pressure_score,
        event_timing_score=event_timing_score,
        risk_adjustment_quality=risk_adjustment_quality,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*inputs: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_strategy_resolution_risk_adjusted_readiness_report(
        inputs,
        generated_at=generated_at,
        config=config or cfg(),
    )


def test_empty_input_returns_block_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-strategy-resolution-risk-adjusted-readiness-report-v1"
    )
    assert empty_report.status == "block"
    assert empty_report.reason_codes == ("resolution_readiness_no_packets",)
    assert empty_report.review_packet_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.average_adjusted_readiness_score is None
    assert empty_report.max_contradiction_pressure_score == d("0.000000")
    assert empty_report.min_settlement_clarity_score == d("0.000000")
    assert empty_report.min_quorum_score == d("0.000000")
    assert empty_report.min_event_timing_score == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_fields(empty_report)

    payload = module.research_strategy_resolution_risk_adjusted_readiness_report_payload(
        empty_report,
    )
    digest_value = module.research_strategy_resolution_risk_adjusted_readiness_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "block"
    assert payload["review_packet_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    int(digest_value, 16)


def test_scores_resolution_readiness_after_risk_adjustment() -> None:
    built = report(
        input_row("packet-pass"),
        input_row(
            "packet-watch",
            settlement_clarity_score=d("0.740000"),
            quorum_score=d("0.620000"),
            contradiction_pressure_score=d("0.250000"),
            event_timing_score=d("0.780000"),
            risk_adjustment_quality=d("0.900000"),
        ),
        input_row(
            "packet-block",
            settlement_clarity_score=d("0.720000"),
            quorum_score=d("0.500000"),
            contradiction_pressure_score=d("0.750000"),
            event_timing_score=d("0.820000"),
            risk_adjustment_quality=d("0.900000"),
            reason_codes=("contradiction_review",),
        ),
    )

    assert built.status == "block"
    assert built.review_packet_count == d("3")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.average_adjusted_readiness_score == d("0.647250")
    assert built.max_contradiction_pressure_score == d("0.750000")
    assert built.min_settlement_clarity_score == d("0.720000")
    assert built.min_quorum_score == d("0.500000")
    assert built.min_event_timing_score == d("0.780000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    block_row, watch_row, pass_row = built.rows
    assert block_row.review_packet_label == "packet-block"
    assert block_row.contradiction_relief_score == d("0.250000")
    assert block_row.adjusted_readiness_score == d("0.515250")
    assert block_row.lowest_adequacy_score == d("0.250000")
    assert block_row.status == "block"
    assert "contradiction_pressure_block" in block_row.reason_codes
    assert "input_contradiction_review" in block_row.reason_codes

    assert watch_row.review_packet_label == "packet-watch"
    assert watch_row.contradiction_relief_score == d("0.750000")
    assert watch_row.adjusted_readiness_score == d("0.650250")
    assert watch_row.lowest_adequacy_score == d("0.620000")
    assert watch_row.status == "watch"
    assert "quorum_watch" in watch_row.reason_codes
    assert "contradiction_pressure_watch" in watch_row.reason_codes

    assert pass_row.review_packet_label == "packet-pass"
    assert pass_row.contradiction_relief_score == d("0.900000")
    assert pass_row.adjusted_readiness_score == d("0.776250")
    assert pass_row.lowest_adequacy_score == d("0.800000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "contradiction_pressure_pass",
        "event_timing_pass",
        "quorum_pass",
        "resolution_readiness_pass",
        "risk_adjustment_pass",
        "settlement_clarity_pass",
    )


def test_payload_is_deterministic_public_safe_decimal_only_and_digest_checked() -> None:
    module = api()
    first = report(
        input_row("packet-zeta", reason_codes=("zeta", "alpha")),
        input_row("packet-alpha"),
    )
    second = report(
        input_row("packet-alpha"),
        input_row("packet-zeta", reason_codes=("alpha", "zeta")),
    )

    payload = first.payload
    second_payload = module.research_strategy_resolution_risk_adjusted_readiness_report_payload(
        second,
    )
    json.dumps(payload, sort_keys=True)

    assert tuple(row.review_packet_label for row in first.rows) == (
        "packet-alpha",
        "packet-zeta",
    )
    assert payload == second_payload
    assert payload["rows"][0]["adjusted_readiness_score"] == "0.776250"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_strategy_resolution_risk_adjusted_readiness_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_fields(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_resolution_risk_adjusted_readiness_public_payload(
            tampered,
        )


def test_dataclasses_are_frozen_exact_and_flags_are_hard_required() -> None:
    module = api()
    built = report(input_row())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyResolutionRiskAdjustedReadinessConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)

    assert all(row.status in {"pass", "watch", "block"} for row in built.rows)
    assert built.status in {"pass", "watch", "block"}


def test_strict_decimal_datetime_public_label_and_consistency_validation() -> None:
    module = api()
    with pytest.raises(ValueError, match="settlement_clarity_score"):
        input_row(settlement_clarity_score=_DecimalSubclass("0.900000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="quorum_score"):
        input_row(quorum_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="risk_adjustment_quality"):
        input_row(risk_adjustment_quality=d("1.100000"))

    with pytest.raises(ValueError, match="review_packet_label"):
        input_row("raw-candidate-17")

    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))

    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 14, 30))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="utcoffset"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 14, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="pass_component_score"):
        cfg(pass_component_score=d("0.300000"))

    with pytest.raises(ValueError, match="block_contradiction_pressure"):
        cfg(block_contradiction_pressure=d("0.200000"))

    built = report(input_row())
    with pytest.raises(ValueError, match="adjusted_readiness_score"):
        replace(built.rows[0], adjusted_readiness_score=d("0.100000"))

    with pytest.raises(ValueError, match="status"):
        replace(built, status="ready")

    with pytest.raises(ValueError, match="rows"):
        module.ResearchStrategyResolutionRiskAdjustedReadinessReport(
            **{**built.__dict__, "rows": "not-rows"},
        )


def test_owned_module_has_no_database_network_wallet_or_action_surfaces() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    for cls in (
        module.ResearchStrategyResolutionRiskAdjustedReadinessConfig,
        module.ResearchStrategyResolutionRiskAdjustedReadinessInput,
        module.ResearchStrategyResolutionRiskAdjustedReadinessRow,
        module.ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount,
        module.ResearchStrategyResolutionRiskAdjustedReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "raw" not in lowered
            assert "candidate" not in lowered
            assert "market_id" not in lowered
            assert "market_slug" not in lowered
            assert "slug" not in lowered
            assert "question" not in lowered
            assert "url" not in lowered
            assert "source_text" not in lowered
            assert "dsn" not in lowered
            assert "table" not in lowered
            assert "token" not in lowered
            assert "wallet" not in lowered
            assert "order" not in lowered
            assert "trade" not in lowered
            assert "recommend" not in lowered
            assert "sizing" not in lowered

    forbidden_public_name_fragments = {
        "client",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    }
    for name in module.__all__:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "private",
        "auth",
        "wallet",
        "network",
        "database",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        for fragment in forbidden_fragments:
            assert fragment not in lowered, value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_codes", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "quality",
                "pressure",
                "quorum",
                "clarity",
                "timing",
            )
        ):
            field_value = getattr(value, field.name)
            assert field_value is None or type(field_value) is Decimal, field.name
