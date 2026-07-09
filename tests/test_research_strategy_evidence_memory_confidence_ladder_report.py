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
    "research_strategy_evidence_memory_confidence_ladder_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_evidence_memory_confidence_ladder_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 13, 30, tzinfo=UTC)
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
    assert spec is not None, "confidence ladder report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
        ),
        "pass_min_composite_score": d("0.800000"),
        "watch_min_composite_score": d("0.600000"),
        "min_pass_evidence_score": d("0.800000"),
        "min_watch_evidence_score": d("0.600000"),
        "min_pass_memory_score": d("0.750000"),
        "min_watch_memory_score": d("0.550000"),
        "min_pass_confidence_score": d("0.750000"),
        "min_watch_confidence_score": d("0.550000"),
        "evidence_weight": d("0.400000"),
        "memory_weight": d("0.300000"),
        "confidence_weight": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceMemoryConfidenceLadderConfig(**values)


def _input(module: Any, private_reference: str = "private-alpha", **overrides: object) -> Any:
    values = {
        "private_reference": private_reference,
        "evidence_score": d("0.950000"),
        "memory_score": d("0.900000"),
        "confidence_score": d("0.850000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("analyst_reviewed",),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceMemoryConfidenceLadderInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_evidence_memory_confidence_ladder_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
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
        if field.name.endswith(("_count", "_score", "_ratio", "_weight")):
            assert type(item) is Decimal


def _copy_payload(value: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(value, sort_keys=True))
    assert type(copied) is dict
    return copied


def _refresh_payload_digest(value: dict[str, object]) -> dict[str, object]:
    payload_without_digest = dict(value)
    payload_without_digest.pop("derived_validation_digest", None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    value["derived_validation_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return value


def test_builds_pass_watch_and_block_ladder_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate/market?source_url=https://example.test&token=secret",
                evidence_score=d("0.950000"),
                memory_score=d("0.900000"),
                confidence_score=d("0.850000"),
                reason_codes=("analyst_reviewed",),
            ),
            _input(
                module,
                "private-watch",
                evidence_score=d("0.700000"),
                memory_score=d("0.650000"),
                confidence_score=d("0.600000"),
                reason_codes=("memory_rechecked",),
            ),
            _input(
                module,
                "private-block",
                evidence_score=d("0.450000"),
                memory_score=d("0.400000"),
                confidence_score=d("0.350000"),
                reason_codes=("manual_confidence_check",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyEvidenceMemoryConfidenceLadderReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_composite_score == d("0.655000")
    assert report.min_composite_score == d("0.405000")
    assert report.min_evidence_score == d("0.450000")
    assert report.min_memory_score == d("0.400000")
    assert report.min_confidence_score == d("0.350000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyEvidenceMemoryConfidenceLadderRow
    assert blocked.evidence_gap_score == d("0.550000")
    assert blocked.memory_gap_score == d("0.600000")
    assert blocked.confidence_gap_score == d("0.650000")
    assert blocked.composite_score == d("0.405000")
    assert blocked.reason_codes == (
        "manual_confidence_check",
        "evidence_block",
        "memory_block",
        "confidence_block",
        "composite_block",
    )

    watched = report.rows[1]
    assert watched.composite_score == d("0.655000")
    assert watched.reason_codes == (
        "memory_rechecked",
        "evidence_watch",
        "memory_watch",
        "confidence_watch",
        "composite_watch",
    )

    passed = report.rows[2]
    assert passed.composite_score == d("0.905000")
    assert passed.reason_codes == ("analyst_reviewed", "confidence_ladder_pass")

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
            reason_code="analyst_reviewed",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
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
    assert report.average_composite_score == ZERO
    assert report.min_composite_score == ZERO
    assert report.min_evidence_score == ZERO
    assert report.min_memory_score == ZERO
    assert report.min_confidence_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
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
                "raw-candidate/market?source_url=https://example.test&token=secret",
            ),
        ),
    )

    payload = module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report,
    )
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["composite_score"] == "0.905000"
    assert payload["rows"][0]["item_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate",
        "market",
        "source_url",
        "https://",
        "example.test",
        "token",
        "secret",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyEvidenceMemoryConfidenceLadderConfig)
    assert is_dataclass(module.ResearchStrategyEvidenceMemoryConfidenceLadderInput)
    assert is_dataclass(module.ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyEvidenceMemoryConfidenceLadderRow)
    assert is_dataclass(module.ResearchStrategyEvidenceMemoryConfidenceLadderReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.confidence_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].composite_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_composite_score"):
        _config(module, pass_min_composite_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_composite_score"):
        _config(module, watch_min_composite_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_composite_score"):
        _config(module, pass_min_composite_score=d("0.500000"))
    with pytest.raises(ValueError, match="ladder weights"):
        _config(module, evidence_weight=d("0.450000"))
    with pytest.raises(ValueError, match="private_reference"):
        _input(module, _StringSubclass("private-alpha"))
    with pytest.raises(ValueError, match="private_reference"):
        _input(module, " ")
    with pytest.raises(ValueError, match="evidence_score"):
        _input(module, evidence_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_score"):
        _input(module, memory_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score"):
        _input(module, confidence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 13, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 9, 14, 0))
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
                    observed_at=datetime(2026, 7, 9, 14, 1, tzinfo=UTC),
                ),
            ),
        )


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report,
    )

    tampered_status = dict(payload)
    tampered_status["status"] = "hold"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            tampered_status,
        )

    tampered_extra = dict(payload)
    tampered_extra["candidate"] = "hidden"
    with pytest.raises(ValueError, match="unexpected payload field"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            tampered_extra,
        )

    tampered_row = dict(payload)
    tampered_rows = [dict(payload["rows"][0])]
    tampered_rows[0]["item_digest"] = "raw-market-source-url"
    tampered_row["rows"] = tampered_rows
    with pytest.raises(ValueError, match="item_digest"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            tampered_row,
        )


@pytest.mark.parametrize("leaked", ("wallet-0xabc123", "order-12345", "trade-67890"))
def test_public_payload_rejects_wallet_order_and_trade_values_with_valid_digest(
    leaked: str,
) -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report,
    )

    tampered = _copy_payload(payload)
    tampered["config_version"] = leaked
    _refresh_payload_digest(tampered)

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            tampered,
        )


def test_public_payload_rejects_recomputed_schema_and_report_drift() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report,
    )

    bad_config = _copy_payload(payload)
    bad_config["config_version"] = (
        "research-strategy-evidence-memory-confidence-ladder-report-v9"
    )
    _refresh_payload_digest(bad_config)
    with pytest.raises(ValueError, match="config_version"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            bad_config,
        )

    bad_score = _copy_payload(payload)
    bad_score["average_composite_score"] = "9.000000"
    _refresh_payload_digest(bad_score)
    with pytest.raises(ValueError, match="average_composite_score"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            bad_score,
        )

    bad_row_count = _copy_payload(payload)
    bad_row_count["row_count"] = "4.000000"
    _refresh_payload_digest(bad_row_count)
    with pytest.raises(ValueError, match="row_count"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            bad_row_count,
        )

    bad_gap = _copy_payload(payload)
    bad_gap_rows = bad_gap["rows"]
    assert type(bad_gap_rows) is list
    assert type(bad_gap_rows[0]) is dict
    bad_gap_rows[0]["evidence_gap_score"] = "0.000000"
    _refresh_payload_digest(bad_gap)
    with pytest.raises(ValueError, match="evidence_gap_score"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            bad_gap,
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
        replace(passed, reason_codes=("confidence_ladder_pass", "composite_watch"))
    with pytest.raises(ValueError, match="composite_score"):
        replace(passed, composite_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="item_digest"):
        replace(passed, item_digest="raw-candidate-market")
    with pytest.raises(ValueError, match="observed_at"):
        future_row = replace(passed, observed_at=GENERATED_AT + timedelta(minutes=1))
        replace(report, rows=(future_row,), derived_validation_digest="")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        mixed = _report(
            module,
            (
                _input(module, "private-z", confidence_score=d("0.350000")),
                _input(module, "private-a"),
            ),
        )
        replace(mixed, rows=tuple(reversed(mixed.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_sequence() -> None:
    module = _module()
    rows = (
        _input(module, "private-c", confidence_score=d("0.350000")),
        _input(module, "private-a"),
        _input(module, "private-b", evidence_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report_a,
    ) == module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report_b,
    )

    tampered = module.research_strategy_evidence_memory_confidence_ladder_report_payload(
        report_a,
    )
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_evidence_memory_confidence_ladder_report_payload(
            tampered,
        )


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
        "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION",
        "ResearchStrategyEvidenceMemoryConfidenceLadderConfig",
        "ResearchStrategyEvidenceMemoryConfidenceLadderInput",
        "ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount",
        "ResearchStrategyEvidenceMemoryConfidenceLadderReport",
        "ResearchStrategyEvidenceMemoryConfidenceLadderRow",
        "build_research_strategy_evidence_memory_confidence_ladder_report",
        "research_strategy_evidence_memory_confidence_ladder_report_payload",
        "validate_research_strategy_evidence_memory_confidence_ladder_public_payload",
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
