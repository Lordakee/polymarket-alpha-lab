from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.research_market_probability_gap_stability_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "case_digest": digest("candidate-alpha"),
        "model_probability": d("0.650000"),
        "book_probability": d("0.600000"),
        "spread_width": d("0.005000"),
        "depth_score": d("0.900000"),
        "fee_drag": d("0.005000"),
        "volatility_score": d("0.100000"),
        "book_age_seconds": d("60.000000"),
        "liquidity_uncertainty": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.MarketProbabilityGapStabilitySignal(**values)


def report(rows: list[object] | tuple[object, ...]) -> Any:
    module = api()
    return module.build_research_market_probability_gap_stability_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_report_scores_and_sorts_probability_gap_stability_statuses() -> None:
    module = api()
    passed = signal(case_digest=digest("case-pass"))
    watched = signal(
        case_digest=digest("case-watch"),
        model_probability=d("0.610000"),
        book_probability=d("0.570000"),
        spread_width=d("0.010000"),
        depth_score=d("0.700000"),
        fee_drag=d("0.008000"),
        volatility_score=d("0.500000"),
        book_age_seconds=d("600.000000"),
        liquidity_uncertainty=d("0.200000"),
    )
    blocked = signal(
        case_digest=digest("case-block"),
        model_probability=d("0.530000"),
        book_probability=d("0.520000"),
        spread_width=d("0.006000"),
        depth_score=d("0.200000"),
        fee_drag=d("0.004000"),
        volatility_score=d("0.200000"),
        book_age_seconds=d("4000.000000"),
        liquidity_uncertainty=d("0.700000"),
    )

    stability_report = report([passed, watched, blocked])
    repeated_report = report([blocked, passed, watched])

    assert type(stability_report) is module.MarketProbabilityGapStabilityReport
    assert is_dataclass(stability_report)
    assert stability_report.generated_at == GENERATED_AT
    assert stability_report.config_version == (
        module.DEFAULT_RESEARCH_MARKET_PROBABILITY_GAP_STABILITY_CONFIG_VERSION
    )
    assert stability_report.report_status == "block"
    assert stability_report.case_count == d("3.000000")
    assert stability_report.pass_count == d("1.000000")
    assert stability_report.watch_count == d("1.000000")
    assert stability_report.block_count == d("1.000000")
    assert stability_report.mean_stability_score == d("0.444444")
    assert stability_report.min_stability_score == d("0.000000")
    assert stability_report.max_adjusted_gap == d("0.040000")
    assert [row.case_digest for row in stability_report.rows] == [
        digest("case-block"),
        digest("case-watch"),
        digest("case-pass"),
    ]

    assert stability_report.rows[0].stability_status == "block"
    assert stability_report.rows[0].adjusted_gap == d("0.000000")
    assert stability_report.rows[0].stability_score == d("0.000000")
    assert stability_report.rows[0].manual_research_ready is False
    assert stability_report.rows[0].reason_codes == (
        "gap_stability_block",
        "adjusted_gap_block",
        "depth_block",
        "book_age_block",
        "liquidity_uncertainty_block",
    )
    assert stability_report.rows[1].stability_status == "watch"
    assert stability_report.rows[1].adjusted_gap == d("0.022000")
    assert stability_report.rows[1].stability_score == d("0.500000")
    assert stability_report.rows[1].reason_codes == (
        "gap_stability_watch",
        "adjusted_gap_watch",
        "volatility_watch",
    )
    assert stability_report.rows[2].stability_status == "pass"
    assert stability_report.rows[2].adjusted_gap == d("0.040000")
    assert stability_report.rows[2].stability_score == d("0.833333")
    assert stability_report.rows[2].manual_research_ready is True
    assert stability_report.rows[2].reason_codes == ("gap_stability_pass",)
    assert stability_report.reason_code_counts == (
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="adjusted_gap_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="adjusted_gap_watch",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="book_age_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="depth_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="gap_stability_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="gap_stability_pass",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="gap_stability_watch",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="liquidity_uncertainty_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilityGapStabilityReasonCodeCount(
            reason_code="volatility_watch",
            row_count=d("1.000000"),
        ),
    )
    assert (
        stability_report.derived_validation_digest
        == repeated_report.derived_validation_digest
    )
    assert len(stability_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in stability_report.derived_validation_digest
    )
    assert stability_report.paper_only is True
    assert stability_report.report_only is True
    assert stability_report.readonly is True


def test_empty_input_still_uses_only_pass_watch_block_statuses() -> None:
    stability_report = report([])

    assert stability_report.report_status == "pass"
    assert stability_report.rows == ()
    assert stability_report.reason_code_counts == ()
    assert stability_report.case_count == d("0.000000")
    assert stability_report.pass_count == d("0.000000")
    assert stability_report.watch_count == d("0.000000")
    assert stability_report.block_count == d("0.000000")
    assert stability_report.mean_stability_score == d("0.000000")
    assert stability_report.min_stability_score == d("0.000000")
    assert stability_report.max_adjusted_gap == d("0.000000")


def test_custom_config_drives_row_reason_validation_and_digest() -> None:
    module = api()
    custom_config = module.MarketProbabilityGapStabilityConfig(
        watch_adjusted_gap=d("0.020000"),
        block_adjusted_gap=d("0.005000"),
    )

    stability_report = module.build_research_market_probability_gap_stability_report(
        [
            signal(
                case_digest=digest("custom-config-thresholds"),
                model_probability=d("0.620000"),
                book_probability=d("0.600000"),
                spread_width=d("0.005000"),
                fee_drag=d("0.005000"),
            ),
        ],
        generated_at=GENERATED_AT,
        config=custom_config,
    )

    assert stability_report.report_status == "watch"
    assert stability_report.rows[0].adjusted_gap == d("0.010000")
    assert stability_report.rows[0].stability_status == "watch"
    assert stability_report.rows[0].reason_codes == (
        "gap_stability_watch",
        "adjusted_gap_watch",
    )
    assert len(stability_report.derived_validation_digest) == 64


def test_payload_is_json_safe_immutable_and_public_only() -> None:
    module = api()
    raw_private_reference = (
        "candidate-alpha market-alpha slug-alpha question-alpha "
        "https://example.invalid/path token-alpha"
    )
    stability_report = report(
        [
            signal(
                case_digest=digest(raw_private_reference),
                model_probability=d("0.720000"),
                book_probability=d("0.660000"),
            ),
        ],
    )

    payload = module.research_market_probability_gap_stability_report_payload(
        stability_report,
    )
    rendered_payload = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["case_count"] == "1.000000"
    assert payload["rows"][0]["case_digest"] == digest(raw_private_reference)
    assert payload["rows"][0]["model_probability"] == "0.720000"
    assert payload["rows"][0]["book_probability"] == "0.660000"
    assert payload["rows"][0]["manual_research_ready"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_float(payload)
    assert raw_private_reference not in rendered_payload
    assert "candidate-alpha" not in rendered_payload
    assert "market-alpha" not in rendered_payload
    assert "slug-alpha" not in rendered_payload
    assert "question-alpha" not in rendered_payload
    assert "https://example.invalid/path" not in rendered_payload
    assert "token-alpha" not in rendered_payload
    _assert_public_payload_safe(payload)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["case_count"] = "9.000000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]


def test_validation_is_strict_frozen_digest_backed_and_paper_only() -> None:
    module = api()
    base_signal = signal()
    stability_report = report(
        [
            base_signal,
            signal(
                case_digest=digest("case-beta"),
                model_probability=d("0.620000"),
            ),
        ],
    )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_GAP_STABILITY_CONFIG_VERSION",
        "MarketProbabilityGapStabilityConfig",
        "MarketProbabilityGapStabilitySignal",
        "MarketProbabilityGapStabilityRow",
        "MarketProbabilityGapStabilityReasonCodeCount",
        "MarketProbabilityGapStabilityReport",
        "build_research_market_probability_gap_stability_report",
        "research_market_probability_gap_stability_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        base_signal.case_digest = digest("mutated")  # type: ignore[misc]
    with pytest.raises(ValueError, match="case_digest"):
        signal(case_digest=_StringSubclass(digest("case-alpha")))
    with pytest.raises(ValueError, match="case_digest"):
        signal(case_digest="not-a-digest")
    with pytest.raises(ValueError, match="model_probability"):
        signal(model_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="book_probability"):
        signal(book_probability=d("1.500000"))
    with pytest.raises(ValueError, match="depth_score"):
        signal(depth_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="book_age_seconds"):
        signal(book_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_probability_gap_stability_report(
            [base_signal],
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(base_signal, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(stability_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(stability_report, derived_validation_digest="0" * 64)

    blocked_row = report(
        [
            signal(
                case_digest=digest("row-validation"),
                depth_score=d("0.100000"),
            ),
        ],
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=("gap_stability_block", "volatility_block"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="rows"):
        module.MarketProbabilityGapStabilityReport(
            generated_at=stability_report.generated_at,
            config_version=stability_report.config_version,
            report_status=stability_report.report_status,
            case_count=stability_report.case_count,
            pass_count=stability_report.pass_count,
            watch_count=stability_report.watch_count,
            block_count=stability_report.block_count,
            mean_stability_score=stability_report.mean_stability_score,
            min_stability_score=stability_report.min_stability_score,
            max_adjusted_gap=stability_report.max_adjusted_gap,
            rows=tuple(reversed(stability_report.rows)),
            reason_code_counts=stability_report.reason_code_counts,
            derived_validation_digest=stability_report.derived_validation_digest,
        )


def test_source_file_exposes_no_execution_or_private_reference_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_gap_stability_report.py"
    )
    tree = ast.parse(source_path.read_text())
    banned_identifier_fragments = (
        "network",
        "socket",
        "requests",
        "urllib",
        "auth",
        "wallet",
        "account",
        "broker",
        "trade",
        "trading",
        "order",
        "database",
        "sqlite",
        "postgres",
        "dsn",
        "token",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in banned_identifier_fragments)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in banned_identifier_fragments)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.lower() for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                names.append(node.module.lower())
            assert not any(
                fragment in name
                for name in names
                for fragment in banned_identifier_fragments
            )


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _assert_public_payload_safe(value: object) -> None:
    banned_payload_fragments = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in banned_payload_fragments)
            _assert_public_payload_safe(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_payload_safe(item)
