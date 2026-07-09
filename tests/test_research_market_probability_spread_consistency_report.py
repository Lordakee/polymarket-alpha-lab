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


GENERATED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_market_probability_spread_consistency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "case_digest": digest("case-alpha"),
        "model_probability": d("0.610000"),
        "book_probability": d("0.600000"),
        "bid_probability": d("0.590000"),
        "ask_probability": d("0.610000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.MarketProbabilitySpreadConsistencySignal(**values)


def report(rows: list[object] | tuple[object, ...]) -> Any:
    module = api()
    return module.build_research_market_probability_spread_consistency_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_report_scores_and_sorts_probability_spread_consistency_statuses() -> None:
    module = api()
    passed = signal(case_digest=digest("case-pass"))
    watched = signal(
        case_digest=digest("case-watch"),
        model_probability=d("0.650000"),
        book_probability=d("0.640000"),
        bid_probability=d("0.600000"),
        ask_probability=d("0.660000"),
    )
    blocked = signal(
        case_digest=digest("case-block"),
        model_probability=d("0.800000"),
        book_probability=d("0.700000"),
        bid_probability=d("0.550000"),
        ask_probability=d("0.650000"),
    )

    consistency_report = report([passed, watched, blocked])
    repeated_report = report([blocked, passed, watched])

    assert type(consistency_report) is module.MarketProbabilitySpreadConsistencyReport
    assert is_dataclass(consistency_report)
    assert consistency_report.generated_at == GENERATED_AT
    assert consistency_report.config_version == (
        module.DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_CONSISTENCY_CONFIG_VERSION
    )
    assert consistency_report.report_status == "block"
    assert consistency_report.case_count == d("3.000000")
    assert consistency_report.pass_count == d("1.000000")
    assert consistency_report.watch_count == d("1.000000")
    assert consistency_report.block_count == d("1.000000")
    assert consistency_report.mean_consistency_score == d("0.444444")
    assert consistency_report.min_consistency_score == d("0.000000")
    assert consistency_report.max_book_midpoint_gap == d("0.100000")
    assert consistency_report.max_spread_width == d("0.100000")
    assert [row.case_digest for row in consistency_report.rows] == [
        digest("case-block"),
        digest("case-watch"),
        digest("case-pass"),
    ]

    block_row, watch_row, pass_row = consistency_report.rows
    assert block_row.consistency_status == "block"
    assert block_row.midpoint_probability == d("0.600000")
    assert block_row.spread_width == d("0.100000")
    assert block_row.book_midpoint_gap == d("0.100000")
    assert block_row.model_midpoint_gap == d("0.200000")
    assert block_row.consistency_score == d("0.000000")
    assert block_row.manual_research_ready is False
    assert block_row.reason_codes == (
        "probability_spread_consistency_block",
        "book_midpoint_gap_block",
        "spread_width_block",
        "model_midpoint_gap_block",
    )
    assert watch_row.consistency_status == "watch"
    assert watch_row.midpoint_probability == d("0.630000")
    assert watch_row.spread_width == d("0.060000")
    assert watch_row.book_midpoint_gap == d("0.010000")
    assert watch_row.model_midpoint_gap == d("0.020000")
    assert watch_row.consistency_score == d("0.500000")
    assert watch_row.reason_codes == (
        "probability_spread_consistency_watch",
        "book_midpoint_gap_watch",
        "spread_width_watch",
    )
    assert pass_row.consistency_status == "pass"
    assert pass_row.midpoint_probability == d("0.600000")
    assert pass_row.spread_width == d("0.020000")
    assert pass_row.book_midpoint_gap == d("0.000000")
    assert pass_row.model_midpoint_gap == d("0.010000")
    assert pass_row.consistency_score == d("0.833333")
    assert pass_row.manual_research_ready is True
    assert pass_row.reason_codes == ("probability_spread_consistency_pass",)
    assert consistency_report.reason_code_counts == (
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="book_midpoint_gap_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="book_midpoint_gap_watch",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="model_midpoint_gap_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="probability_spread_consistency_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="probability_spread_consistency_pass",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="probability_spread_consistency_watch",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="spread_width_block",
            row_count=d("1.000000"),
        ),
        module.MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code="spread_width_watch",
            row_count=d("1.000000"),
        ),
    )
    assert (
        consistency_report.derived_validation_digest
        == repeated_report.derived_validation_digest
    )
    assert len(consistency_report.derived_validation_digest) == 64
    int(consistency_report.derived_validation_digest, 16)
    assert consistency_report.paper_only is True
    assert consistency_report.report_only is True
    assert consistency_report.readonly is True


def test_empty_input_uses_only_pass_watch_block_statuses() -> None:
    consistency_report = report([])

    assert consistency_report.report_status == "pass"
    assert consistency_report.rows == ()
    assert consistency_report.reason_code_counts == ()
    assert consistency_report.case_count == d("0.000000")
    assert consistency_report.pass_count == d("0.000000")
    assert consistency_report.watch_count == d("0.000000")
    assert consistency_report.block_count == d("0.000000")
    assert consistency_report.mean_consistency_score == d("0.000000")
    assert consistency_report.min_consistency_score == d("0.000000")
    assert consistency_report.max_book_midpoint_gap == d("0.000000")
    assert consistency_report.max_spread_width == d("0.000000")


def test_custom_config_builds_rows_without_default_threshold_revalidation() -> None:
    module = api()
    consistency_report = module.build_research_market_probability_spread_consistency_report(
        [
            signal(
                case_digest=digest("custom-config-case"),
                model_probability=d("0.610000"),
                book_probability=d("0.600000"),
                bid_probability=d("0.590000"),
                ask_probability=d("0.610000"),
            ),
        ],
        generated_at=GENERATED_AT,
        config=module.MarketProbabilitySpreadConsistencyConfig(
            watch_book_midpoint_gap=d("0.000001"),
            block_book_midpoint_gap=d("0.900000"),
            watch_spread_width=d("0.000001"),
            block_spread_width=d("0.900000"),
            watch_model_midpoint_gap=d("0.000001"),
            block_model_midpoint_gap=d("0.900000"),
        ),
    )

    assert consistency_report.report_status == "watch"
    assert consistency_report.rows[0].reason_codes == (
        "probability_spread_consistency_watch",
        "spread_width_watch",
        "model_midpoint_gap_watch",
    )


def test_payload_is_json_safe_immutable_public_only_and_digest_backed() -> None:
    module = api()
    raw_private_reference = (
        "candidate-alpha market-alpha slug-alpha question-alpha "
        "https://example.invalid/path token-alpha"
    )
    consistency_report = report(
        [
            signal(
                case_digest=digest(raw_private_reference),
                model_probability=d("0.620000"),
                book_probability=d("0.610000"),
                bid_probability=d("0.590000"),
                ask_probability=d("0.630000"),
            ),
        ],
    )

    payload = module.research_market_probability_spread_consistency_report_payload(
        consistency_report,
    )
    rendered_payload = json.dumps(payload, sort_keys=True)
    unsigned_payload = dict(payload)
    supplied_digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert payload["generated_at"] == "2026-07-09T10:00:00+00:00"
    assert payload["case_count"] == "1.000000"
    assert payload["rows"][0]["case_digest"] == digest(raw_private_reference)
    assert payload["rows"][0]["model_probability"] == "0.620000"
    assert payload["rows"][0]["book_probability"] == "0.610000"
    assert payload["rows"][0]["bid_probability"] == "0.590000"
    assert payload["rows"][0]["ask_probability"] == "0.630000"
    assert payload["rows"][0]["midpoint_probability"] == "0.610000"
    assert payload["rows"][0]["manual_research_ready"] is False
    assert supplied_digest == expected_digest
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


def test_validation_is_strict_frozen_digest_backed_and_report_only() -> None:
    module = api()
    base_signal = signal()
    consistency_report = report(
        [
            base_signal,
            signal(
                case_digest=digest("case-beta"),
                book_probability=d("0.610000"),
            ),
        ],
    )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_CONSISTENCY_CONFIG_VERSION",
        "MarketProbabilitySpreadConsistencyConfig",
        "MarketProbabilitySpreadConsistencySignal",
        "MarketProbabilitySpreadConsistencyRow",
        "MarketProbabilitySpreadConsistencyReasonCodeCount",
        "MarketProbabilitySpreadConsistencyReport",
        "build_research_market_probability_spread_consistency_report",
        "research_market_probability_spread_consistency_report_payload",
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
    with pytest.raises(ValueError, match="bid_probability"):
        signal(bid_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="ask_probability"):
        signal(bid_probability=d("0.700000"), ask_probability=d("0.600000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_probability_spread_consistency_report(
            [base_signal],
            generated_at=_DateTimeSubclass(2026, 7, 9, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(base_signal, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(consistency_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(consistency_report, derived_validation_digest="0" * 64)

    blocked_row = report(
        [
            signal(
                case_digest=digest("row-validation"),
                book_probability=d("0.700000"),
                bid_probability=d("0.550000"),
                ask_probability=d("0.650000"),
            ),
        ],
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=(
                "probability_spread_consistency_block",
                "spread_width_block",
            ),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="rows"):
        module.MarketProbabilitySpreadConsistencyReport(
            generated_at=consistency_report.generated_at,
            config_version=consistency_report.config_version,
            report_status=consistency_report.report_status,
            case_count=consistency_report.case_count,
            pass_count=consistency_report.pass_count,
            watch_count=consistency_report.watch_count,
            block_count=consistency_report.block_count,
            mean_consistency_score=consistency_report.mean_consistency_score,
            min_consistency_score=consistency_report.min_consistency_score,
            max_book_midpoint_gap=consistency_report.max_book_midpoint_gap,
            max_spread_width=consistency_report.max_spread_width,
            rows=tuple(reversed(consistency_report.rows)),
            reason_code_counts=consistency_report.reason_code_counts,
            derived_validation_digest=consistency_report.derived_validation_digest,
        )


def test_source_file_exposes_no_execution_or_private_reference_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_spread_consistency_report.py"
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
        "sizing",
        "recommend",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in banned_payload_fragments)
            _assert_public_payload_safe(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_payload_safe(item)
