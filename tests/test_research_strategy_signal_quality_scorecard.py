from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_signal_quality_scorecard import (
    DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION,
    ResearchStrategySignalQualityInput,
    ResearchStrategySignalQualityPublicNote,
    ResearchStrategySignalQualityReasonCodeCount,
    ResearchStrategySignalQualityReport,
    ResearchStrategySignalQualityRow,
    ResearchStrategySignalQualityScorecardConfig,
    build_research_strategy_signal_quality_scorecard,
    research_strategy_signal_quality_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_strategy_signal_quality_scorecard.py")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchStrategySignalQualityScorecardConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION,
        "min_evidence_strength_score": d("0.600000"),
        "pass_evidence_strength_score": d("0.800000"),
        "watch_freshness_age_hours": d("24.000000"),
        "block_freshness_age_hours": d("72.000000"),
        "watch_conflict_rate": d("0.250000"),
        "block_conflict_rate": d("0.600000"),
        "watch_calibration_error_rate": d("0.250000"),
        "block_calibration_error_rate": d("0.400000"),
        "min_calibration_sample_count": d("5.000000"),
        "pass_quality_score": d("0.750000"),
        "watch_quality_score": d("0.500000"),
        "evidence_strength_weight": d("0.350000"),
        "timeliness_weight": d("0.250000"),
        "conflict_rate_weight": d("0.200000"),
        "calibration_history_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategySignalQualityScorecardConfig(**values)


def _input(signal_key: str = "signal-alpha", **overrides: object) -> ResearchStrategySignalQualityInput:
    values = {
        "signal_key": signal_key,
        "evidence_strength_score": d("0.900000"),
        "evidence_freshness_age_hours": d("6.000000"),
        "conflict_rate": d("0.100000"),
        "calibration_error_rate": d("0.100000"),
        "calibration_sample_count": d("20.000000"),
    }
    values.update(overrides)
    return ResearchStrategySignalQualityInput(**values)


def _report(
    rows: tuple[ResearchStrategySignalQualityInput, ...],
    *,
    cfg: ResearchStrategySignalQualityScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
    public_notes: tuple[ResearchStrategySignalQualityPublicNote, ...] = (),
) -> ResearchStrategySignalQualityReport:
    return build_research_strategy_signal_quality_scorecard(
        rows,
        generated_at=generated_at,
        config=cfg or _config(),
        public_notes=public_notes,
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def _assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_rate", "_score", "_hours", "_ratio")):
            assert type(item) is Decimal


def test_scorecard_builds_pass_watch_and_block_public_report() -> None:
    summary = _report(
        (
            _input("raw-candidate-alpha?market=hidden&token=secret"),
            _input(
                "signal-watch",
                evidence_strength_score=d("0.700000"),
                evidence_freshness_age_hours=d("30.000000"),
                conflict_rate=d("0.300000"),
                calibration_error_rate=d("0.300000"),
                calibration_sample_count=d("3.000000"),
            ),
            _input(
                "signal-block",
                evidence_strength_score=d("0.500000"),
                evidence_freshness_age_hours=d("80.000000"),
                conflict_rate=d("0.700000"),
                calibration_error_rate=d("0.500000"),
                calibration_sample_count=d("1.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        public_notes=(
            ResearchStrategySignalQualityPublicNote(
                key="review_scope",
                value="human review only",
            ),
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION
    assert summary.human_review_status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_quality_score == d("0.590000")
    assert summary.min_evidence_strength_score == d("0.500000")
    assert summary.max_freshness_age_hours == d("80.000000")
    assert summary.max_conflict_rate == d("0.700000")
    assert summary.max_calibration_error_rate == d("0.500000")
    assert summary.min_calibration_sample_count == d("1.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.human_review_status for row in summary.rows) == (
        "block",
        "watch",
        "pass",
    )

    blocked = summary.rows[0]
    assert type(blocked) is ResearchStrategySignalQualityRow
    assert blocked.evidence_strength_score == d("0.500000")
    assert blocked.evidence_freshness_age_hours == d("80.000000")
    assert blocked.timeliness_score == ZERO
    assert blocked.conflict_rate == d("0.700000")
    assert blocked.calibration_history_score == d("0.100000")
    assert blocked.quality_score == d("0.255000")
    assert blocked.reason_codes == (
        "evidence_strength_block",
        "timeliness_block",
        "conflict_rate_block",
        "calibration_error_block",
        "quality_score_block",
        "calibration_sample_watch",
    )

    watched = summary.rows[1]
    assert watched.timeliness_score == d("0.583333")
    assert watched.calibration_history_score == d("0.425000")
    assert watched.quality_score == d("0.615833")
    assert watched.reason_codes == (
        "evidence_strength_watch",
        "timeliness_watch",
        "conflict_rate_watch",
        "calibration_error_watch",
        "calibration_sample_watch",
        "quality_score_watch",
    )

    passed = summary.rows[2]
    assert passed.quality_score == d("0.899167")
    assert passed.reason_codes == ("signal_quality_pass",)


def test_empty_scorecard_is_report_only_block() -> None:
    summary = _report(())

    assert summary.human_review_status == "block"
    assert summary.row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_quality_score == ZERO
    assert summary.min_evidence_strength_score == ZERO
    assert summary.max_freshness_age_hours == ZERO
    assert summary.max_conflict_rate == ZERO
    assert summary.max_calibration_error_rate == ZERO
    assert summary.min_calibration_sample_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchStrategySignalQualityReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("empty_input",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_redacts_private_keys_and_serializes_decimal_strings() -> None:
    summary = _report(
        (
            _input("raw-candidate-id/market-slug?token=hidden&wallet=private"),
        ),
    )

    payload = research_strategy_signal_quality_scorecard_payload(summary)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == summary.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["quality_score"] == "0.899167"
    assert payload["rows"][0]["signal_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == summary.derived_validation_digest
    assert len(summary.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "token",
        "hidden",
        "wallet",
        "private",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(summary)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    assert is_dataclass(ResearchStrategySignalQualityScorecardConfig)
    assert is_dataclass(ResearchStrategySignalQualityInput)
    assert is_dataclass(ResearchStrategySignalQualityPublicNote)
    assert is_dataclass(ResearchStrategySignalQualityReasonCodeCount)
    assert is_dataclass(ResearchStrategySignalQualityRow)
    assert is_dataclass(ResearchStrategySignalQualityReport)

    cfg = _config()
    row = _input()
    summary = _report((row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.conflict_rate = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].quality_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.human_review_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass(DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION))
    with pytest.raises(ValueError, match="min_evidence_strength_score"):
        _config(min_evidence_strength_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_conflict_rate"):
        _config(watch_conflict_rate=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="block_freshness_age_hours"):
        _config(block_freshness_age_hours=d("12.000000"))
    with pytest.raises(ValueError, match="watch_conflict_rate"):
        _config(watch_conflict_rate=d("0.700000"))
    with pytest.raises(ValueError, match="watch_calibration_error_rate"):
        _config(watch_calibration_error_rate=d("0.500000"))
    with pytest.raises(ValueError, match="pass_quality_score"):
        _config(pass_quality_score=d("0.400000"))
    with pytest.raises(ValueError, match="quality score weights"):
        _config(evidence_strength_weight=d("0.300000"))
    with pytest.raises(ValueError, match="signal_key"):
        _input(_StringSubclass("signal-alpha"))
    with pytest.raises(ValueError, match="signal_key"):
        _input(" signal-alpha")
    with pytest.raises(ValueError, match="evidence_strength_score"):
        _input(evidence_strength_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_freshness_age_hours"):
        _input(evidence_freshness_age_hours=6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_rate"):
        _input(conflict_rate=Decimal("NaN"))
    with pytest.raises(ValueError, match="calibration_sample_count"):
        _input(calibration_sample_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_strategy_signal_quality_scorecard(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=_config(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_strategy_signal_quality_scorecard(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=_config(),
        )
    with pytest.raises(ValueError, match="config"):
        build_research_strategy_signal_quality_scorecard(
            (),
            generated_at=GENERATED_AT,
            config=object(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="inputs"):
        _report((object(),))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("public_note", "key", "source_ref"),
        ("public_note", "key", "wallet"),
        ("public_note", "value", "https://example.test/source"),
        ("public_note", "value", "raw source text copied here"),
        ("public_note", "value", "buy or sell recommendation"),
        ("public_note", "value", "wallet auth token"),
        ("public_note", "value", "order trade position"),
    ),
)
def test_public_leak_rejection_for_notes(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    assert factory_name == "public_note"
    values = {"key": "review_scope", "value": "human review only"}
    values[field_name] = field_value
    with pytest.raises(ValueError, match="unsafe public|contains unsafe public"):
        ResearchStrategySignalQualityPublicNote(**values)


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    summary = _report((_input(),))
    payload = research_strategy_signal_quality_scorecard_payload(summary)
    rendered = repr(payload).casefold()

    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["human_review_status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        research_strategy_signal_quality_scorecard_payload(tampered_status)

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        research_strategy_signal_quality_scorecard_payload(tampered_field)

    tampered_value = dict(payload)
    tampered_value["public_notes"] = [
        {
            "key": "review_scope",
            "value": "source text copied here",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="unsafe public value"):
        research_strategy_signal_quality_scorecard_payload(tampered_value)


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchStrategySignalQualityPublicNote(
            key="review_scope",
            value="human review only",
            report_only=False,
        )

    summary = _report((_input(),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.reason_code_counts[0], readonly=False)


def test_manual_report_and_row_drift_rejected() -> None:
    summary = _report((_input(),))
    ready = summary.rows[0]

    with pytest.raises(ValueError, match="human_review_status"):
        replace(ready, human_review_status="block")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=("signal_quality_pass", "quality_score_watch"),
        )
    with pytest.raises(ValueError, match="quality_score"):
        replace(ready, quality_score=ZERO, validation_config=_config())
    with pytest.raises(ValueError, match="signal_digest"):
        replace(ready, signal_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report((
            _input("signal-z", conflict_rate=d("0.700000")),
            _input("signal-a"),
        ))
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    rows = (
        _input("signal-c", conflict_rate=d("0.700000")),
        _input("signal-a"),
        _input("signal-b", evidence_strength_score=d("0.700000")),
    )
    notes = (
        ResearchStrategySignalQualityPublicNote(
            key="review_scope",
            value="human review only",
        ),
    )

    report_a = _report(rows, public_notes=notes)
    report_b = _report(tuple(reversed(rows)), public_notes=notes)

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_strategy_signal_quality_scorecard_payload(
        report_a,
    ) == research_strategy_signal_quality_scorecard_payload(report_b)
    assert tuple(row.human_review_status for row in report_a.rows) == (
        "block",
        "watch",
        "pass",
    )

    tampered = research_strategy_signal_quality_scorecard_payload(report_a)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_signal_quality_scorecard_payload(tampered)


def test_public_numeric_fields_are_decimals() -> None:
    source_row = _input()
    summary = _report((source_row,))

    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(summary)
    _assert_decimal_numeric_fields(summary.rows[0])
    _assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_scope_is_read_only_report_only_and_public_api_is_narrow() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_strategy_signal_quality_scorecard",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION",
        "ResearchStrategySignalQualityInput",
        "ResearchStrategySignalQualityPublicNote",
        "ResearchStrategySignalQualityReasonCodeCount",
        "ResearchStrategySignalQualityReport",
        "ResearchStrategySignalQualityRow",
        "ResearchStrategySignalQualityScorecardConfig",
        "build_research_strategy_signal_quality_scorecard",
        "research_strategy_signal_quality_scorecard_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
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

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
