from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_source_claim_memory_ladder_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_source_claim_memory_ladder_report.py",
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
    assert spec is not None, "source claim memory ladder report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_MEMORY_LADDER_CONFIG_VERSION
        ),
        "pass_min_ladder_score": d("0.800000"),
        "watch_min_ladder_score": d("0.600000"),
        "min_pass_provenance_score": d("0.800000"),
        "min_watch_provenance_score": d("0.600000"),
        "min_pass_claim_score": d("0.800000"),
        "min_watch_claim_score": d("0.600000"),
        "min_pass_memory_score": d("0.750000"),
        "min_watch_memory_score": d("0.550000"),
        "provenance_weight": d("0.350000"),
        "claim_weight": d("0.350000"),
        "memory_weight": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchStrategySourceClaimMemoryLadderConfig(**values)


def _input(module: Any, private_reference: str = "private-alpha", **overrides: object) -> Any:
    values = {
        "private_reference": private_reference,
        "provenance_score": d("0.950000"),
        "claim_score": d("0.900000"),
        "memory_score": d("0.850000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("analyst_reviewed",),
    }
    values.update(overrides)
    return module.ResearchStrategySourceClaimMemoryLadderInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_source_claim_memory_ladder_report(
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


def test_builds_pass_watch_and_block_ladder_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate/market?source_url=https://example.test&token=secret",
                provenance_score=d("0.950000"),
                claim_score=d("0.900000"),
                memory_score=d("0.850000"),
                reason_codes=("analyst_reviewed",),
            ),
            _input(
                module,
                "private-watch",
                provenance_score=d("0.700000"),
                claim_score=d("0.650000"),
                memory_score=d("0.600000"),
                reason_codes=("provenance_rechecked",),
            ),
            _input(
                module,
                "private-block",
                provenance_score=d("0.450000"),
                claim_score=d("0.400000"),
                memory_score=d("0.350000"),
                reason_codes=("memory_recalled",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategySourceClaimMemoryLadderReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_MEMORY_LADDER_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_ladder_score == d("0.652500")
    assert report.min_ladder_score == d("0.402500")
    assert report.min_provenance_score == d("0.450000")
    assert report.min_claim_score == d("0.400000")
    assert report.min_memory_score == d("0.350000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategySourceClaimMemoryLadderRow
    assert blocked.provenance_gap_score == d("0.550000")
    assert blocked.claim_gap_score == d("0.600000")
    assert blocked.memory_gap_score == d("0.650000")
    assert blocked.ladder_score == d("0.402500")
    assert blocked.reason_codes == (
        "memory_recalled",
        "provenance_block",
        "claim_block",
        "memory_block",
        "ladder_block",
    )

    watched = report.rows[1]
    assert watched.ladder_score == d("0.652500")
    assert watched.reason_codes == (
        "provenance_rechecked",
        "provenance_watch",
        "claim_watch",
        "memory_watch",
        "ladder_watch",
    )

    passed = report.rows[2]
    assert passed.ladder_score == d("0.902500")
    assert passed.reason_codes == ("analyst_reviewed", "ladder_pass")

    assert report.reason_code_counts[0] == (
        module.ResearchStrategySourceClaimMemoryLadderReasonCodeCount(
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
    assert report.average_ladder_score == ZERO
    assert report.min_ladder_score == ZERO
    assert report.min_provenance_score == ZERO
    assert report.min_claim_score == ZERO
    assert report.min_memory_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategySourceClaimMemoryLadderReasonCodeCount(
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

    payload = module.research_strategy_source_claim_memory_ladder_report_payload(report)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["ladder_score"] == "0.902500"
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
        "dsn",
        "table",
        "token",
        "secret",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategySourceClaimMemoryLadderConfig)
    assert is_dataclass(module.ResearchStrategySourceClaimMemoryLadderInput)
    assert is_dataclass(module.ResearchStrategySourceClaimMemoryLadderReasonCodeCount)
    assert is_dataclass(module.ResearchStrategySourceClaimMemoryLadderRow)
    assert is_dataclass(module.ResearchStrategySourceClaimMemoryLadderReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.memory_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].ladder_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_MEMORY_LADDER_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_ladder_score"):
        _config(module, pass_min_ladder_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_ladder_score"):
        _config(module, watch_min_ladder_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_ladder_score"):
        _config(module, pass_min_ladder_score=d("0.500000"))
    with pytest.raises(ValueError, match="ladder weights"):
        _config(module, provenance_weight=d("0.400000"))
    with pytest.raises(ValueError, match="private_reference"):
        _input(module, _StringSubclass("private-alpha"))
    with pytest.raises(ValueError, match="private_reference"):
        _input(module, " ")
    with pytest.raises(ValueError, match="provenance_score"):
        _input(module, provenance_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="claim_score"):
        _input(module, claim_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_score"):
        _input(module, memory_score=Decimal("NaN"))
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
    payload = module.research_strategy_source_claim_memory_ladder_report_payload(report)

    tampered_status = dict(payload)
    tampered_status["status"] = "hold"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_source_claim_memory_ladder_report_payload(
            tampered_status,
        )

    tampered_extra = dict(payload)
    tampered_extra["source_url"] = "hidden"
    with pytest.raises(ValueError, match="unexpected payload field|unsafe public field"):
        module.research_strategy_source_claim_memory_ladder_report_payload(
            tampered_extra,
        )

    tampered_row = dict(payload)
    tampered_rows = [dict(payload["rows"][0])]
    tampered_rows[0]["item_digest"] = "raw-source-url-token"
    tampered_row["rows"] = tampered_rows
    with pytest.raises(ValueError, match="item_digest|unsafe public value"):
        module.research_strategy_source_claim_memory_ladder_report_payload(
            tampered_row,
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
        replace(passed, reason_codes=("ladder_pass", "ladder_watch"))
    with pytest.raises(ValueError, match="ladder_score"):
        replace(passed, ladder_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="item_digest"):
        replace(passed, item_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        mixed = _report(
            module,
            (
                _input(module, "private-z", memory_score=d("0.350000")),
                _input(module, "private-a"),
            ),
        )
        replace(mixed, rows=tuple(reversed(mixed.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_sequence() -> None:
    module = _module()
    rows = (
        _input(module, "private-c", memory_score=d("0.350000")),
        _input(module, "private-a"),
        _input(module, "private-b", provenance_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_source_claim_memory_ladder_report_payload(
        report_a,
    ) == module.research_strategy_source_claim_memory_ladder_report_payload(report_b)

    tampered = module.research_strategy_source_claim_memory_ladder_report_payload(
        report_a,
    )
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_source_claim_memory_ladder_report_payload(tampered)


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
        "DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_MEMORY_LADDER_CONFIG_VERSION",
        "ResearchStrategySourceClaimMemoryLadderConfig",
        "ResearchStrategySourceClaimMemoryLadderInput",
        "ResearchStrategySourceClaimMemoryLadderReasonCodeCount",
        "ResearchStrategySourceClaimMemoryLadderReport",
        "ResearchStrategySourceClaimMemoryLadderRow",
        "build_research_strategy_source_claim_memory_ladder_report",
        "research_strategy_source_claim_memory_ladder_report_payload",
        "validate_research_strategy_source_claim_memory_ladder_public_payload",
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
