from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_probability_cost_confidence_floor_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_probability_cost_confidence_floor_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION
        ),
        "watch_total_cost_ratio": d("0.030000"),
        "block_total_cost_ratio": d("0.080000"),
        "watch_confidence_floor_ratio": d("0.650000"),
        "block_confidence_floor_ratio": d("0.500000"),
        "watch_cost_adjusted_gap_floor_ratio": d("0.020000"),
        "block_cost_adjusted_gap_floor_ratio": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityCostConfidenceFloorReportConfig(
        **values,
    )


def signal(
    public_signal_ref: str = "public-alpha",
    *,
    observed_at: datetime | None = None,
    research_probability: Decimal = d("0.590000"),
    public_probability: Decimal = d("0.500000"),
    fee_cost_ratio: Decimal = d("0.006000"),
    spread_cost_ratio: Decimal = d("0.010000"),
    slippage_cost_ratio: Decimal = d("0.004000"),
    confidence_ratio: Decimal = d("0.800000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketProbabilityCostConfidenceFloorInput(
        public_signal_ref=public_signal_ref,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        research_probability=research_probability,
        public_probability=public_probability,
        fee_cost_ratio=fee_cost_ratio,
        spread_cost_ratio=spread_cost_ratio,
        slippage_cost_ratio=slippage_cost_ratio,
        confidence_ratio=confidence_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *signals: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_probability_cost_confidence_floor_report(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    trimmed = dict(payload)
    trimmed.pop("derived_validation_digest", None)
    return trimmed


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(
            item for nested in value.values() for item in walk_payload_values(nested)
        )
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def test_builds_pass_watch_block_rows_with_decimal_only_floor_math() -> None:
    module = api()
    built = report(
        signal("pass-public-signal"),
        signal(
            "watch-public-signal",
            research_probability=d("0.550000"),
            fee_cost_ratio=d("0.010000"),
            spread_cost_ratio=d("0.015000"),
            slippage_cost_ratio=d("0.010000"),
            confidence_ratio=d("0.620000"),
        ),
        signal(
            "block-public-signal",
            research_probability=d("0.520000"),
            fee_cost_ratio=d("0.030000"),
            spread_cost_ratio=d("0.035000"),
            slippage_cost_ratio=d("0.025000"),
            confidence_ratio=d("0.450000"),
            reason_codes=("manual_public_note",),
        ),
    )

    assert type(built) is module.ResearchMarketProbabilityCostConfidenceFloorReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.generated_at.tzinfo is UTC
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.total_cost_watch_count == d("2.000000")
    assert built.confidence_floor_watch_count == d("2.000000")
    assert built.cost_adjusted_gap_floor_watch_count == d("2.000000")
    assert built.max_total_cost_ratio == d("0.090000")
    assert built.min_confidence_ratio == d("0.450000")
    assert built.min_cost_adjusted_gap_ratio == ZERO
    assert built.average_confidence_floor_score == d("0.021767")
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_signal_ref == "block-public-signal"
    assert blocked.probability_gap_ratio == d("0.020000")
    assert blocked.total_cost_ratio == d("0.090000")
    assert blocked.cost_adjusted_gap_ratio == ZERO
    assert blocked.confidence_floor_gap_ratio == d("0.200000")
    assert blocked.confidence_floor_score == ZERO
    assert blocked.reason_codes == (
        "input_manual_public_note",
        "probability_cost_confidence_floor_block",
        "probability_cost_confidence_floor_confidence_block",
        "probability_cost_confidence_floor_cost_adjusted_gap_block",
        "probability_cost_confidence_floor_total_cost_block",
    )
    assert watched.cost_adjusted_gap_ratio == d("0.015000")
    assert watched.confidence_floor_gap_ratio == d("0.030000")
    assert watched.confidence_floor_score == d("0.009300")
    assert watched.reason_codes == (
        "probability_cost_confidence_floor_confidence_watch",
        "probability_cost_confidence_floor_cost_adjusted_gap_watch",
        "probability_cost_confidence_floor_total_cost_watch",
        "probability_cost_confidence_floor_watch",
    )
    assert passed.total_cost_ratio == d("0.020000")
    assert passed.cost_adjusted_gap_ratio == d("0.070000")
    assert passed.confidence_floor_score == d("0.056000")
    assert passed.reason_codes == ("probability_cost_confidence_floor_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)


def test_empty_inputs_block_with_report_only_no_inputs_reason() -> None:
    module = api()
    built = report()

    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.max_total_cost_ratio == ZERO
    assert built.min_confidence_ratio == ZERO
    assert built.min_cost_adjusted_gap_ratio == ZERO
    assert built.average_confidence_floor_score == ZERO
    assert built.rows == ()
    assert built.reason_codes == (
        "probability_cost_confidence_floor_no_inputs",
    )
    assert built.reason_code_counts == (
        module.ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount(
            reason_code="probability_cost_confidence_floor_no_inputs",
            count=d("1.000000"),
        ),
    )


def test_public_payload_and_digest_are_deterministic_and_redacted() -> None:
    module = api()
    first = report(
        signal("beta-public-signal", research_probability=d("0.570000")),
        signal("alpha-public-signal"),
    )
    second = report(
        signal("alpha-public-signal"),
        signal("beta-public-signal", research_probability=d("0.570000")),
    )

    first_payload = module.research_market_probability_cost_confidence_floor_report_payload(
        first,
    )
    second_payload = module.research_market_probability_cost_confidence_floor_report_payload(
        second,
    )
    digest = module.research_market_probability_cost_confidence_floor_report_digest(
        first,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first.public_payload == first_payload
    assert first_payload == second_payload
    assert digest == hashlib.sha256(
        json.dumps(
            payload_without_digest(first_payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert digest == first_payload["derived_validation_digest"]
    assert digest == second.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["public_signal_ref"] == "alpha-public-signal"
    assert first_payload["rows"][0]["confidence_floor_score"] == "0.056000"
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    for raw_fragment in (
        "raw-candidate",
        "raw-market",
        "raw question",
        "example.test",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    ):
        assert raw_fragment not in encoded.lower()


def test_digest_validation_rejects_report_and_nested_payload_tampering() -> None:
    module = api()
    built = report(signal("tamper-public-signal"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    object.__setattr__(built.rows[0], "confidence_floor_score", d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_cost_confidence_floor_report_payload(built)


def test_input_reason_codes_cannot_drive_floor_status() -> None:
    built = report(
        signal(
            "manual-status-public-signal",
            reason_codes=("manual_block", "manual_watch"),
        ),
    )

    assert built.status == "pass"
    assert built.rows[0].status == "pass"
    assert built.rows[0].reason_codes == (
        "input_manual_block",
        "input_manual_watch",
        "probability_cost_confidence_floor_clear",
    )


def test_report_validation_rejects_input_count_that_does_not_match_rows() -> None:
    module = api()
    built = report(signal("count-public-signal"))
    values = module._report_values_without_digest(built)
    values["input_count"] = d("2.000000")

    with pytest.raises(ValueError, match="input_count"):
        module.ResearchMarketProbabilityCostConfidenceFloorReport(
            **values,
            derived_validation_digest=module._report_digest_from_values(values),
        )


def test_frozen_dataclasses_hard_flags_and_decimal_only_validation() -> None:
    module = api()
    built = report(signal("frozen-public-signal"))

    for public_type in (
        module.ResearchMarketProbabilityCostConfidenceFloorReportConfig,
        module.ResearchMarketProbabilityCostConfidenceFloorInput,
        module.ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount,
        module.ResearchMarketProbabilityCostConfidenceFloorRow,
        module.ResearchMarketProbabilityCostConfidenceFloorReport,
    ):
        assert is_dataclass(public_type)

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].confidence_floor_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="watch_total_cost_ratio"):
        config(watch_total_cost_ratio=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="research_probability"):
        signal(research_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_signal_ref"):
        signal(public_signal_ref="raw-candidate-001")
    with pytest.raises(ValueError, match="public_signal_ref"):
        signal(public_signal_ref="https://example.test/path?token=secret")
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 9, 11, 55))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal("aware-public-signal"), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 9, 11, 55, tzinfo=UTC))

    row = built.rows[0]
    with pytest.raises(ValueError, match="status"):
        module.ResearchMarketProbabilityCostConfidenceFloorRow(
            public_signal_ref=row.public_signal_ref,
            observed_at=row.observed_at,
            research_probability=row.research_probability,
            public_probability=row.public_probability,
            probability_gap_ratio=row.probability_gap_ratio,
            fee_cost_ratio=row.fee_cost_ratio,
            spread_cost_ratio=row.spread_cost_ratio,
            slippage_cost_ratio=row.slippage_cost_ratio,
            total_cost_ratio=row.total_cost_ratio,
            cost_adjusted_gap_ratio=row.cost_adjusted_gap_ratio,
            confidence_ratio=row.confidence_ratio,
            confidence_floor_gap_ratio=row.confidence_floor_gap_ratio,
            confidence_floor_score=row.confidence_floor_score,
            status="blocked",
            reason_codes=row.reason_codes,
        )

    for item in (built, *built.rows, *built.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_exports_and_static_forbidden_surface_are_exact() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchMarketProbabilityCostConfidenceFloorReportConfig",
        "ResearchMarketProbabilityCostConfidenceFloorInput",
        "ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount",
        "ResearchMarketProbabilityCostConfidenceFloorReport",
        "ResearchMarketProbabilityCostConfidenceFloorRow",
        "build_research_market_probability_cost_confidence_floor_report",
        "research_market_probability_cost_confidence_floor_report_digest",
        "research_market_probability_cost_confidence_floor_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live trading",
        "trading",
        "sizing",
        "recommendation",
        "requests",
        "http://",
        "https://",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "private_key",
        "api_key",
        "secret",
        "client",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
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
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
