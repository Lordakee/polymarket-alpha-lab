from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_evidence_cost_resolution_scorecard_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_evidence_cost_resolution_scorecard_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "scorecard report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION
        ),
        "pass_min_readiness_score": d("0.800000"),
        "watch_min_readiness_score": d("0.600000"),
        "min_pass_evidence_completeness_score": d("0.800000"),
        "min_watch_evidence_completeness_score": d("0.600000"),
        "min_pass_cost_adjusted_edge_score": d("0.750000"),
        "min_watch_cost_adjusted_edge_score": d("0.550000"),
        "min_pass_microstructure_signal_score": d("0.750000"),
        "min_watch_microstructure_signal_score": d("0.550000"),
        "max_pass_resolution_ambiguity_score": d("0.200000"),
        "max_watch_resolution_ambiguity_score": d("0.450000"),
        "evidence_weight": d("0.300000"),
        "cost_adjusted_edge_weight": d("0.300000"),
        "microstructure_signal_weight": d("0.200000"),
        "resolution_certainty_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceCostResolutionScorecardConfig(**values)


def _input(module: Any, queue_item_ref: str = "queue-item-alpha", **overrides: object) -> Any:
    values = {
        "queue_item_ref": queue_item_ref,
        "evidence_completeness_score": d("0.950000"),
        "cost_adjusted_edge_score": d("0.900000"),
        "microstructure_signal_score": d("0.850000"),
        "resolution_ambiguity_score": d("0.100000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("analyst_inputs_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceCostResolutionInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
    public_notes: tuple[Any, ...] = (),
) -> Any:
    return module.build_research_strategy_evidence_cost_resolution_scorecard_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
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


def _resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_input,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["derived_validation_digest"] = sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return payload


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
        if field.name.endswith(("_count", "_score", "_ratio", "_weight")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_readiness_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private",
                evidence_completeness_score=d("0.950000"),
                cost_adjusted_edge_score=d("0.900000"),
                microstructure_signal_score=d("0.850000"),
                resolution_ambiguity_score=d("0.100000"),
                reason_codes=("analyst_inputs_ready",),
            ),
            _input(
                module,
                "queue-item-watch",
                evidence_completeness_score=d("0.700000"),
                cost_adjusted_edge_score=d("0.650000"),
                microstructure_signal_score=d("0.600000"),
                resolution_ambiguity_score=d("0.350000"),
                reason_codes=("manual_review_requested",),
            ),
            _input(
                module,
                "queue-item-block",
                evidence_completeness_score=d("0.450000"),
                cost_adjusted_edge_score=d("0.400000"),
                microstructure_signal_score=d("0.350000"),
                resolution_ambiguity_score=d("0.700000"),
                reason_codes=("manual_review_requested", "missing_resolution_detail"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        public_notes=(
            module.ResearchStrategyEvidenceCostResolutionPublicNote(
                key="review_scope",
                value="analyst queue readiness review only",
            ),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyEvidenceCostResolutionScorecardReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_readiness_score == d("0.648333")
    assert report.min_readiness_score == d("0.385000")
    assert report.min_evidence_completeness_score == d("0.450000")
    assert report.min_cost_adjusted_edge_score == d("0.400000")
    assert report.min_microstructure_signal_score == d("0.350000")
    assert report.max_resolution_ambiguity_score == d("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyEvidenceCostResolutionScorecardRow
    assert blocked.evidence_gap_score == d("0.550000")
    assert blocked.cost_adjusted_edge_gap_score == d("0.600000")
    assert blocked.microstructure_gap_score == d("0.650000")
    assert blocked.resolution_certainty_score == d("0.300000")
    assert blocked.readiness_score == d("0.385000")
    assert blocked.reason_codes == (
        "manual_review_requested",
        "missing_resolution_detail",
        "evidence_completeness_block",
        "cost_adjusted_edge_block",
        "microstructure_signal_block",
        "resolution_ambiguity_block",
        "readiness_score_block",
    )

    watched = report.rows[1]
    assert watched.readiness_score == d("0.655000")
    assert watched.reason_codes == (
        "manual_review_requested",
        "evidence_completeness_watch",
        "cost_adjusted_edge_watch",
        "microstructure_signal_watch",
        "resolution_ambiguity_watch",
        "readiness_score_watch",
    )

    passed = report.rows[2]
    assert passed.readiness_score == d("0.905000")
    assert passed.reason_codes == (
        "analyst_inputs_ready",
        "analyst_queue_ready_pass",
    )

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyEvidenceCostResolutionReasonCodeCount(
            reason_code="manual_review_requested",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        )
    )


def test_empty_report_is_report_only_block() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_readiness_score == ZERO
    assert report.min_readiness_score == ZERO
    assert report.min_evidence_completeness_score == ZERO
    assert report.min_cost_adjusted_edge_score == ZERO
    assert report.min_microstructure_signal_score == ZERO
    assert report.max_resolution_ambiguity_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyEvidenceCostResolutionReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_redacts_private_refs_and_serializes_decimal_strings() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private",
            ),
        ),
    )

    payload = module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report,
    )
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["readiness_score"] == "0.905000"
    assert payload["rows"][0]["queue_item_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "market",
        "slug",
        "token",
        "hidden",
        "wallet",
        "private",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyEvidenceCostResolutionScorecardConfig)
    assert is_dataclass(module.ResearchStrategyEvidenceCostResolutionInput)
    assert is_dataclass(module.ResearchStrategyEvidenceCostResolutionPublicNote)
    assert is_dataclass(module.ResearchStrategyEvidenceCostResolutionReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyEvidenceCostResolutionScorecardRow)
    assert is_dataclass(module.ResearchStrategyEvidenceCostResolutionScorecardReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_adjusted_edge_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].readiness_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_readiness_score"):
        _config(module, pass_min_readiness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_readiness_score"):
        _config(module, watch_min_readiness_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_readiness_score"):
        _config(module, pass_min_readiness_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_resolution_ambiguity_score"):
        _config(module, max_pass_resolution_ambiguity_score=d("0.600000"))
    with pytest.raises(ValueError, match="scorecard weights"):
        _config(module, evidence_weight=d("0.350000"))
    with pytest.raises(ValueError, match="queue_item_ref"):
        _input(module, _StringSubclass("queue-item-alpha"))
    with pytest.raises(ValueError, match="queue_item_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="evidence_completeness_score"):
        _input(module, evidence_completeness_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_adjusted_edge_score"):
        _input(module, cost_adjusted_edge_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="microstructure_signal_score"):
        _input(module, microstructure_signal_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, 15, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="config"):
        _report(module, (), cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        _report(module, (object(),))
    with pytest.raises(ValueError, match="observed_at"):
        _report(
            module,
            (
                _input(
                    module,
                    observed_at=datetime(2026, 7, 8, 16, 1, tzinfo=UTC),
                ),
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("key", "source_url"),
        ("key", "wallet"),
        ("value", "https://example.test/source"),
        ("value", "raw source text copied here"),
        ("value", "buy or sell recommendation"),
        ("value", "wallet auth token"),
        ("value", "order trade position"),
        ("value", "private key copied"),
        ("value", "database table dsn"),
    ),
)
def test_public_leak_rejection_for_notes(field_name: str, field_value: str) -> None:
    module = _module()
    values = {"key": "review_scope", "value": "analyst queue readiness review only"}
    values[field_name] = field_value
    with pytest.raises(ValueError, match="unsafe public"):
        module.ResearchStrategyEvidenceCostResolutionPublicNote(**values)


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report,
    )
    rendered = repr(payload).casefold()

    for token in (
        "candidate",
        "market",
        "slug",
        "question",
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
        "sizing",
        "buy",
        "sell",
        "recommendation",
        "private key",
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
            tampered_field,
        )

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
        module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
            tampered_value,
        )


def test_public_payload_rejects_digest_valid_schema_extensions() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report,
    )

    tampered_payloads = []

    top_level_extra = dict(payload)
    top_level_extra["review_metadata"] = "analyst_only"
    tampered_payloads.append(top_level_extra)

    nested_extra = json.loads(json.dumps(payload))
    nested_extra["rows"][0]["review_metadata"] = "analyst_only"
    tampered_payloads.append(nested_extra)

    for tampered in tampered_payloads:
        with pytest.raises(ValueError, match="payload schema"):
            module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
                _resign_payload(tampered),
            )


def test_public_payload_rejects_digest_valid_flag_and_scalar_drift() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report,
    )

    tampered_payloads = []

    top_level_flag = json.loads(json.dumps(payload))
    top_level_flag["paper_only"] = False
    tampered_payloads.append(top_level_flag)

    nested_flag = json.loads(json.dumps(payload))
    nested_flag["rows"][0]["readonly"] = False
    tampered_payloads.append(nested_flag)

    count_format = json.loads(json.dumps(payload))
    count_format["row_count"] = "1"
    tampered_payloads.append(count_format)

    datetime_format = json.loads(json.dumps(payload))
    datetime_format["generated_at"] = "2026-07-08T12:00:00-04:00"
    tampered_payloads.append(datetime_format)

    for tampered in tampered_payloads:
        with pytest.raises(ValueError, match="payload schema"):
            module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
                _resign_payload(tampered),
            )


def test_hard_flags_are_enforced() -> None:
    module = _module()

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(module, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        _input(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.ResearchStrategyEvidenceCostResolutionPublicNote(
            key="review_scope",
            value="analyst queue readiness review only",
            report_only=False,
        )

    report = _report(module, (_input(module),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.reason_code_counts[0], readonly=False)


def test_manual_report_and_row_drift_rejected() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    passed = report.rows[0]

    with pytest.raises(ValueError, match="status"):
        replace(passed, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=("analyst_queue_ready_pass", "readiness_score_watch"),
        )
    with pytest.raises(ValueError, match="readiness_score"):
        replace(passed, readiness_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="queue_item_digest"):
        replace(passed, queue_item_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(module, "queue-item-z", resolution_ambiguity_score=d("0.700000")),
                _input(module, "queue-item-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "queue-item-c", resolution_ambiguity_score=d("0.700000")),
        _input(module, "queue-item-a"),
        _input(module, "queue-item-b", evidence_completeness_score=d("0.700000")),
    )
    notes = (
        module.ResearchStrategyEvidenceCostResolutionPublicNote(
            key="review_scope",
            value="analyst queue readiness review only",
        ),
    )

    report_a = _report(module, rows, public_notes=notes)
    report_b = _report(module, tuple(reversed(rows)), public_notes=notes)

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report_a,
    ) == module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report_b,
    )

    tampered = module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report_a,
    )
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
            tampered,
        )


def test_payload_round_trips_reports_built_with_custom_config() -> None:
    module = _module()
    cfg = _config(
        module,
        evidence_weight=d("1.000000"),
        cost_adjusted_edge_weight=ZERO,
        microstructure_signal_weight=ZERO,
        resolution_certainty_weight=ZERO,
    )
    report = _report(module, (_input(module),), cfg=cfg)

    assert report.rows[0].readiness_score == d("0.950000")
    assert module.research_strategy_evidence_cost_resolution_scorecard_report_payload(
        report,
    )["rows"][0]["readiness_score"] == "0.950000"


def test_public_numeric_fields_are_decimals() -> None:
    module = _module()
    source_row = _input(module)
    report = _report(module, (source_row,))

    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(report)
    _assert_decimal_numeric_fields(report.rows[0])
    _assert_decimal_numeric_fields(report.reason_code_counts[0])


def test_module_scope_is_read_only_report_only_and_public_api_is_narrow() -> None:
    module = _module()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION",
        "ResearchStrategyEvidenceCostResolutionInput",
        "ResearchStrategyEvidenceCostResolutionPublicNote",
        "ResearchStrategyEvidenceCostResolutionReasonCodeCount",
        "ResearchStrategyEvidenceCostResolutionScorecardConfig",
        "ResearchStrategyEvidenceCostResolutionScorecardReport",
        "ResearchStrategyEvidenceCostResolutionScorecardRow",
        "build_research_strategy_evidence_cost_resolution_scorecard_report",
        "research_strategy_evidence_cost_resolution_scorecard_report_payload",
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
