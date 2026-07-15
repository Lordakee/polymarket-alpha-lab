from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_source_authority_memory_guard_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_source_authority_memory_guard_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "source authority memory guard report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION
        ),
        "pass_min_guard_score": d("0.800000"),
        "watch_min_guard_score": d("0.600000"),
        "min_pass_authority_score": d("0.800000"),
        "min_watch_authority_score": d("0.600000"),
        "min_pass_memory_alignment_score": d("0.750000"),
        "min_watch_memory_alignment_score": d("0.550000"),
        "freshness_watch_age_seconds": d("86400.000000"),
        "freshness_block_age_seconds": d("259200.000000"),
        "authority_weight": d("0.500000"),
        "memory_weight": d("0.300000"),
        "freshness_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategySourceAuthorityMemoryGuardConfig(**values)


def _input(
    module: Any,
    private_reference: str = "private-alpha",
    **overrides: object,
) -> Any:
    values = {
        "private_reference": private_reference,
        "authority_score": d("0.950000"),
        "memory_alignment_score": d("0.900000"),
        "evidence_freshness_age_seconds": d("3600.000000"),
        "authority_quorum_count": d("3.000000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchStrategySourceAuthorityMemoryGuardInput(**values)


def _report(
    module: Any,
    inputs: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_source_authority_memory_guard_report(
        inputs,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    return value


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    unsigned = _thaw(payload)
    assert isinstance(unsigned, dict)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _resigned_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    resigned = _thaw(payload)
    assert isinstance(resigned, dict)
    resigned["derived_validation_digest"] = _canonical_digest(resigned)
    return resigned


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, (list, tuple)):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def _assert_public_payload_decimal_strings(payload: dict[str, Any]) -> None:
    for value in _walk_values(payload):
        if isinstance(value, bool):
            continue
        assert not isinstance(value, (Decimal, int, float))


def test_builds_pass_watch_and_block_guard_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw_candidate/market_slug?source_url=https://example.test"
                "&source_text=token dsn table",
                authority_score=d("0.950000"),
                memory_alignment_score=d("0.900000"),
                evidence_freshness_age_seconds=d("3600.000000"),
            ),
            _input(
                module,
                "private-watch",
                authority_score=d("0.700000"),
                memory_alignment_score=d("0.650000"),
                evidence_freshness_age_seconds=d("100000.000000"),
                authority_quorum_count=d("2.000000"),
            ),
            _input(
                module,
                "private-block",
                authority_score=d("0.400000"),
                memory_alignment_score=d("0.450000"),
                evidence_freshness_age_seconds=d("300000.000000"),
                authority_quorum_count=d("1.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategySourceAuthorityMemoryGuardReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_guard_score == d("0.648354")
    assert report.min_guard_score == d("0.335000")
    assert report.min_authority_score == d("0.400000")
    assert report.min_memory_alignment_score == d("0.450000")
    assert report.max_evidence_freshness_age_seconds == d("300000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategySourceAuthorityMemoryGuardRow
    assert blocked.authority_gap_score == d("0.600000")
    assert blocked.memory_gap_score == d("0.550000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.guard_score == d("0.335000")
    assert blocked.reason_codes == (
        "authority_score_block",
        "memory_alignment_block",
        "freshness_age_block",
        "composite_guard_block",
    )

    watched = report.rows[1]
    assert watched.freshness_score == d("0.614198")
    assert watched.guard_score == d("0.667840")
    assert watched.reason_codes == (
        "authority_score_watch",
        "memory_alignment_watch",
        "freshness_age_watch",
        "composite_guard_watch",
    )

    passed = report.rows[2]
    assert passed.freshness_score == d("0.986111")
    assert passed.guard_score == d("0.942222")
    assert passed.reason_codes == ("authority_memory_guard_pass",)
    assert report.reason_codes == (
        "authority_score_block",
        "memory_alignment_block",
        "freshness_age_block",
        "composite_guard_block",
        "authority_score_watch",
        "memory_alignment_watch",
        "freshness_age_watch",
        "composite_guard_watch",
        "authority_memory_guard_pass",
    )


def test_empty_report_is_pass_report_only_and_digest_checked() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "pass"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_guard_score == ZERO
    assert report.min_guard_score == ZERO
    assert report.min_authority_score == ZERO
    assert report.min_memory_alignment_score == ZERO
    assert report.max_evidence_freshness_age_seconds == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        module.research_strategy_source_authority_memory_guard_report_digest(report)
        == report.derived_validation_digest
    )
    assert (
        module.validate_research_strategy_source_authority_memory_guard_report_digest(
            report,
        )
        is True
    )


def test_payload_is_deterministic_json_ready_private_and_tamper_checked() -> None:
    module = _module()
    high_risk_ref = (
        "raw_candidate/market_slug?source_url=https://example.test"
        "&source_text=private token dsn table"
    )
    pass_input = _input(module, high_risk_ref)
    block_input = _input(
        module,
        "private-block",
        authority_score=d("0.400000"),
        memory_alignment_score=d("0.450000"),
        evidence_freshness_age_seconds=d("300000.000000"),
    )
    report_a = _report(module, (pass_input, block_input))
    report_b = _report(module, (block_input, pass_input))

    payload_a = module.research_strategy_source_authority_memory_guard_report_payload(
        report_a,
    )
    payload_b = module.research_strategy_source_authority_memory_guard_report_payload(
        report_b,
    )

    assert payload_a == payload_b
    assert payload_a == report_a.payload
    assert payload_a["derived_validation_digest"] == _canonical_digest(payload_a)
    assert payload_a["derived_validation_digest"] == report_b.derived_validation_digest
    assert payload_a["generated_at"] == "2026-07-09T16:00:00+00:00"
    assert payload_a["row_count"] == "2.000000"
    assert payload_a["rows"][0]["status"] == "block"
    assert payload_a["rows"][0]["item_digest"].startswith("sha256:")
    assert payload_a["rows"][0]["guard_score"] == "0.335000"
    json.dumps(_thaw(payload_a), sort_keys=True, allow_nan=False)
    _assert_public_payload_decimal_strings(payload_a)
    assert isinstance(payload_a, MappingProxyType)
    assert isinstance(payload_a["config"], MappingProxyType)
    assert isinstance(payload_a["rows"], tuple)
    assert isinstance(payload_a["rows"][0], MappingProxyType)
    assert isinstance(payload_a["reason_code_counts"], tuple)
    assert isinstance(payload_a["reason_code_counts"][0], MappingProxyType)
    assert isinstance(payload_a["reason_codes"], tuple)

    rendered_payload = repr(payload_a).casefold()
    rendered_report = repr(asdict(report_a)).casefold()
    for leaked in (
        "raw_candidate",
        "market_slug",
        "source_url",
        "source_text",
        "https://",
        "example.test",
        "private token",
        " dsn ",
        " table",
    ):
        assert leaked not in rendered_payload
        assert leaked not in rendered_report

    module.validate_research_strategy_source_authority_memory_guard_public_payload(
        payload_a,
    )
    with pytest.raises(TypeError):
        dict.__setitem__(payload_a, "status", "pass")
    with pytest.raises(TypeError):
        list.append(payload_a["rows"], {})
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)

    tampered = _thaw(payload_a)
    assert isinstance(tampered, dict)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            tampered,
        )


def test_row_sorting_is_total_when_primary_sort_fields_tie() -> None:
    module = _module()
    first = _input(
        module,
        "private-total-order",
        authority_score=d("0.900000"),
        memory_alignment_score=d("0.900000"),
        observed_at=OBSERVED_AT - timedelta(hours=1),
    )
    second = _input(
        module,
        "private-total-order",
        authority_score=d("0.960000"),
        memory_alignment_score=d("0.800000"),
        observed_at=OBSERVED_AT,
    )

    first_payload = module.research_strategy_source_authority_memory_guard_report_payload(
        _report(module, (first, second)),
    )
    second_payload = module.research_strategy_source_authority_memory_guard_report_payload(
        _report(module, (second, first)),
    )

    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == second_payload[
        "derived_validation_digest"
    ]
    assert tuple(row["authority_score"] for row in first_payload["rows"]) == (
        "0.900000",
        "0.960000",
    )


def test_row_sorting_uses_every_independent_downstream_tie_breaker() -> None:
    module = _module()

    def make_row(**overrides: object) -> Any:
        authority_score = overrides.pop("authority_score", d("0.700000"))
        memory_alignment_score = overrides.pop(
            "memory_alignment_score",
            d("0.650000"),
        )
        values: dict[str, object] = {
            "item_digest": f"sha256:{'8' * 64}",
            "authority_score": authority_score,
            "authority_gap_score": d("1.000000") - authority_score,
            "memory_alignment_score": memory_alignment_score,
            "memory_gap_score": d("1.000000") - memory_alignment_score,
            "evidence_freshness_age_seconds": d("100000.000000"),
            "freshness_score": d("0.600000"),
            "authority_quorum_count": d("2.000000"),
            "guard_score": d("0.650000"),
            "observed_at": OBSERVED_AT,
            "status": "watch",
            "reason_codes": ("authority_score_watch",),
        }
        values.update(overrides)
        return module.ResearchStrategySourceAuthorityMemoryGuardRow(**values)

    cases = (
        (
            {"item_digest": f"sha256:{'1' * 64}"},
            {"item_digest": f"sha256:{'2' * 64}"},
        ),
        (
            {"authority_score": d("0.600000")},
            {"authority_score": d("0.700000")},
        ),
        (
            {"memory_alignment_score": d("0.600000")},
            {"memory_alignment_score": d("0.700000")},
        ),
        (
            {"evidence_freshness_age_seconds": d("99999.000000")},
            {"evidence_freshness_age_seconds": d("100000.000000")},
        ),
        (
            {"freshness_score": d("0.500000")},
            {"freshness_score": d("0.600000")},
        ),
        (
            {"authority_quorum_count": d("1.000000")},
            {"authority_quorum_count": d("2.000000")},
        ),
        (
            {"observed_at": OBSERVED_AT - timedelta(seconds=1)},
            {"observed_at": OBSERVED_AT},
        ),
        (
            {"reason_codes": ("authority_score_watch",)},
            {"reason_codes": ("memory_alignment_watch",)},
        ),
    )
    for first_overrides, second_overrides in cases:
        first = make_row(**first_overrides)
        second = make_row(**second_overrides)
        assert module._sorted_rows((second, first)) == (first, second)


def test_public_dataclasses_and_payload_use_exact_frozen_schemas() -> None:
    module = _module()
    config = _config(module)
    guard_input = _input(module)
    report = _report(module, (guard_input,), cfg=config)
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    expected_fields = {
        module.ResearchStrategySourceAuthorityMemoryGuardConfig: (
            "config_version",
            "pass_min_guard_score",
            "watch_min_guard_score",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_memory_alignment_score",
            "min_watch_memory_alignment_score",
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
            "authority_weight",
            "memory_weight",
            "freshness_weight",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategySourceAuthorityMemoryGuardInput: (
            "private_reference",
            "authority_score",
            "memory_alignment_score",
            "evidence_freshness_age_seconds",
            "authority_quorum_count",
            "observed_at",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategySourceAuthorityMemoryGuardRow: (
            "item_digest",
            "authority_score",
            "authority_gap_score",
            "memory_alignment_score",
            "memory_gap_score",
            "evidence_freshness_age_seconds",
            "freshness_score",
            "authority_quorum_count",
            "guard_score",
            "observed_at",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount: (
            "reason_code",
            "count",
            "row_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategySourceAuthorityMemoryGuardReport: (
            "generated_at",
            "config_version",
            "config",
            "status",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_guard_score",
            "min_guard_score",
            "min_authority_score",
            "min_memory_alignment_score",
            "max_evidence_freshness_age_seconds",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    for cls, field_names in expected_fields.items():
        assert tuple(field.name for field in fields(cls)) == field_names

    for item, field_name in (
        (config, "config_version"),
        (guard_input, "private_reference"),
        (row, "status"),
        (reason_count, "count"),
        (report, "status"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(item, field_name, getattr(item, field_name))

    payload = module.research_strategy_source_authority_memory_guard_report_payload(
        report,
    )
    assert frozenset(payload) == frozenset(
        {
            "generated_at",
            "config_version",
            "config",
            "status",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_guard_score",
            "min_guard_score",
            "min_authority_score",
            "min_memory_alignment_score",
            "max_evidence_freshness_age_seconds",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )
    assert frozenset(payload["config"]) == frozenset(expected_fields[type(config)])
    assert frozenset(payload["rows"][0]) == frozenset(expected_fields[type(row)])
    assert frozenset(payload["reason_code_counts"][0]) == frozenset(
        expected_fields[type(reason_count)],
    )
    assert tuple(payload) == tuple(field.name for field in fields(type(report)))
    assert tuple(payload["config"]) == tuple(
        field.name for field in fields(type(config))
    )
    assert tuple(payload["rows"][0]) == tuple(field.name for field in fields(type(row)))
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name for field in fields(type(reason_count))
    )


def test_public_dataclasses_are_slotted() -> None:
    module = _module()
    public_types = (
        module.ResearchStrategySourceAuthorityMemoryGuardConfig,
        module.ResearchStrategySourceAuthorityMemoryGuardInput,
        module.ResearchStrategySourceAuthorityMemoryGuardRow,
        module.ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount,
        module.ResearchStrategySourceAuthorityMemoryGuardReport,
    )

    for public_type in public_types:
        assert is_dataclass(public_type)
        assert hasattr(public_type, "__slots__")
        assert "__dict__" not in public_type.__dict__


def test_timestamps_require_a_concrete_timezone_offset() -> None:
    module = _module()
    none_offset = _NoneOffsetTimezone()

    with pytest.raises(ValueError, match="observed_at.*utcoffset"):
        _input(
            module,
            observed_at=datetime(2026, 7, 9, 15, 0, tzinfo=none_offset),
        )
    with pytest.raises(ValueError, match="generated_at.*utcoffset"):
        _report(
            module,
            (),
            generated_at=datetime(2026, 7, 9, 16, 0, tzinfo=none_offset),
        )


def test_mapping_payload_rejects_reordered_fields_at_every_schema_level() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    canonical = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(report),
    )
    assert isinstance(canonical, dict)

    for path in ((), ("config",), ("rows", 0), ("reason_code_counts", 0)):
        forged = _thaw(canonical)
        target: Any = forged
        for part in path:
            target = target[part]
        items = tuple(target.items())
        target.clear()
        target.update((*items[1:], items[0]))
        forged = _resigned_payload(forged)

        with pytest.raises(ValueError, match="canonical.*field order"):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                forged,
            )
        with pytest.raises(ValueError, match="canonical.*field order"):
            module.research_strategy_source_authority_memory_guard_report_payload(
                forged,
            )


def test_mapping_payload_rejects_missing_and_wrong_schema_container_types() -> None:
    module = _module()
    canonical = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(canonical, dict)

    for path, field_name in (
        ((), "status"),
        (("config",), "authority_weight"),
        (("rows", 0), "observed_at"),
        (("reason_code_counts", 0), "row_ratio"),
    ):
        forged = _thaw(canonical)
        target: Any = forged
        for part in path:
            target = target[part]
        del target[field_name]
        with pytest.raises(ValueError, match="payload field"):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                _resigned_payload(forged),
            )

    wrong_container_payloads = []
    forged = _thaw(canonical)
    forged["config"] = tuple(forged["config"].items())
    wrong_container_payloads.append(forged)
    forged = _thaw(canonical)
    forged["rows"] = tuple(forged["rows"])
    wrong_container_payloads.append(forged)
    forged = _thaw(canonical)
    forged["rows"][0] = tuple(forged["rows"][0].items())
    wrong_container_payloads.append(forged)
    forged = _thaw(canonical)
    forged["reason_code_counts"][0] = tuple(
        forged["reason_code_counts"][0].items(),
    )
    wrong_container_payloads.append(forged)

    for forged in wrong_container_payloads:
        forged["derived_validation_digest"] = _canonical_digest(forged)
        with pytest.raises(ValueError):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                forged,
            )


def test_decimal_bounds_are_checked_before_quantization_and_signed_zero_is_rejected() -> None:
    module = _module()

    for field_name, bad_value in (
        ("pass_min_guard_score", d("1.0000004")),
        ("watch_min_guard_score", d("-0.0000004")),
    ):
        with pytest.raises(ValueError, match=field_name):
            _config(module, **{field_name: bad_value})

    for field_name, bad_value in (
        ("authority_score", d("1.0000004")),
        ("authority_score", d("-0.0000004")),
        ("memory_alignment_score", d("1.0000004")),
        ("evidence_freshness_age_seconds", d("-0.0000004")),
        ("authority_quorum_count", d("0.0000004")),
    ):
        with pytest.raises(ValueError, match=field_name):
            _input(module, **{field_name: bad_value})

    for factory, field_name in (
        (_config, "authority_weight"),
        (_input, "authority_score"),
        (_input, "evidence_freshness_age_seconds"),
        (_input, "authority_quorum_count"),
    ):
        with pytest.raises(ValueError, match=f"{field_name}.*signed zero"):
            factory(module, **{field_name: d("-0.000000")})

    with pytest.raises(ValueError, match="count.*signed zero"):
        module.ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(
            reason_code="authority_memory_guard_pass",
            count=d("-0.000000"),
            row_ratio=d("1.000000"),
        )


def test_nonfinite_decimals_are_rejected_in_objects_and_public_payloads() -> None:
    module = _module()

    for nonfinite in (d("NaN"), d("sNaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match="authority_weight.*finite Decimal"):
            _config(module, authority_weight=nonfinite)
        with pytest.raises(ValueError, match="authority_score.*finite Decimal"):
            _input(module, authority_score=nonfinite)
        with pytest.raises(ValueError, match="row_ratio.*finite Decimal"):
            module.ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(
                reason_code="authority_memory_guard_pass",
                count=d("1.000000"),
                row_ratio=nonfinite,
            )

    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(payload, dict)
    for nonfinite_text in ("NaN", "sNaN", "Infinity", "-Infinity"):
        forged = json.loads(json.dumps(payload))
        forged["rows"][0]["guard_score"] = nonfinite_text
        with pytest.raises(ValueError, match="guard_score.*finite Decimal"):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                _resigned_payload(forged),
            )


def test_decimal_arithmetic_is_isolated_from_the_ambient_context() -> None:
    module = _module()
    inputs = (
        _input(
            module,
            "private-context-alpha",
            authority_score=d("0.950000"),
            memory_alignment_score=d("0.900000"),
            evidence_freshness_age_seconds=d("3600.000000"),
        ),
        _input(
            module,
            "private-context-beta",
            authority_score=d("0.700000"),
            memory_alignment_score=d("0.650000"),
            evidence_freshness_age_seconds=d("100000.000000"),
        ),
    )
    expected = _report(module, inputs)

    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_DOWN
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        actual = _report(module, inputs)

    assert actual == expected
    assert actual.average_guard_score == d("0.805031")
    assert actual.derived_validation_digest == expected.derived_validation_digest


def test_input_and_mapping_payload_paths_are_isolated_from_hostile_decimal_context() -> None:
    module = _module()
    expected_input = _input(module)
    expected_payload = module.research_strategy_source_authority_memory_guard_report_payload(
        _report(module, (expected_input,)),
    )
    mutable_payload = _thaw(expected_payload)
    assert isinstance(mutable_payload, dict)

    with localcontext() as ambient:
        ambient.prec = 2
        ambient.rounding = ROUND_DOWN
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        actual_input = _input(module)
        actual_payload = (
            module.research_strategy_source_authority_memory_guard_report_payload(
                mutable_payload,
            )
        )

    assert actual_input == expected_input
    assert actual_payload == expected_payload


def test_public_validator_rejects_resigned_exact_schema_and_canonical_type_drift() -> None:
    module = _module()
    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(payload, dict)

    for path, field_name in (
        ((), "extra"),
        (("config",), "extra"),
        (("rows", 0), "extra"),
        (("reason_code_counts", 0), "extra"),
    ):
        forged = json.loads(json.dumps(payload))
        target: Any = forged
        for part in path:
            target = target[part]
        target[field_name] = "public"
        forged = _resigned_payload(forged)
        with pytest.raises(ValueError, match="payload field|canonical report payload"):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                forged,
            )

    noncanonical_count = json.loads(json.dumps(payload))
    noncanonical_count["row_count"] = "1"
    with pytest.raises(ValueError, match="row_count.*canonical"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(noncanonical_count),
        )

    noncanonical_timestamp = json.loads(json.dumps(payload))
    noncanonical_timestamp["generated_at"] = "2026-07-09T11:00:00-05:00"
    with pytest.raises(ValueError, match="generated_at.*canonical UTC"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(noncanonical_timestamp),
        )

    signed_zero_count = json.loads(json.dumps(payload))
    signed_zero_count["watch_count"] = "-0.000000"
    with pytest.raises(ValueError, match="watch_count.*signed zero"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(signed_zero_count),
        )


@pytest.mark.parametrize(
    ("path", "bad_value", "field_name"),
    (
        (("config", "authority_weight"), "-0.000000", "authority_weight"),
        (("rows", 0, "authority_score"), "-0.000000", "authority_score"),
        (("rows", 0, "guard_score"), "NaN", "guard_score"),
        (("rows", 0, "guard_score"), "sNaN", "guard_score"),
        (("rows", 0, "guard_score"), "Infinity", "guard_score"),
        (("rows", 0, "guard_score"), "-Infinity", "guard_score"),
        (("reason_code_counts", 0, "count"), "-0.000000", "count"),
        (("row_count",), "1", "row_count"),
        (("row_count",), "1.0", "row_count"),
        (("row_count",), "+1.000000", "row_count"),
        (("row_count",), "01.000000", "row_count"),
        (("row_count",), "1.0000000", "row_count"),
        (("row_count",), "1e0", "row_count"),
    ),
)
def test_payload_decimal_signed_zero_nonfinite_and_raw_text_matrix(
    path: tuple[object, ...],
    bad_value: str,
    field_name: str,
) -> None:
    module = _module()
    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(payload, dict)
    target: Any = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = bad_value

    with pytest.raises(ValueError, match=field_name):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(payload),
        )


def test_public_validator_rejects_resigned_derived_row_forgeries() -> None:
    module = _module()
    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(payload, dict)

    for field_name, forged_value in (
        ("authority_gap_score", "0.123456"),
        ("memory_gap_score", "0.123456"),
        ("freshness_score", "0.123456"),
        ("guard_score", "0.123456"),
    ):
        forged = json.loads(json.dumps(payload))
        forged["rows"][0][field_name] = forged_value
        if field_name == "guard_score":
            forged["average_guard_score"] = forged_value
            forged["min_guard_score"] = forged_value
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                _resigned_payload(forged),
            )

    forged_policy = json.loads(json.dumps(payload))
    forged_policy["rows"][0]["status"] = "watch"
    forged_policy["rows"][0]["reason_codes"] = ["authority_score_watch"]
    forged_policy["status"] = "watch"
    forged_policy["pass_count"] = "0.000000"
    forged_policy["watch_count"] = "1.000000"
    forged_policy["reason_codes"] = ["authority_score_watch"]
    forged_policy["reason_code_counts"] = [
        {
            "reason_code": "authority_score_watch",
            "count": "1.000000",
            "row_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="status|reason_codes"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(forged_policy),
        )


def test_public_validator_rejects_resigned_report_count_reason_and_score_forgeries() -> None:
    module = _module()
    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(payload, dict)

    for field_name, forged_value in (
        ("row_count", "2.000000"),
        ("pass_count", "2.000000"),
        ("average_guard_score", "0.123456"),
        ("min_authority_score", "0.123456"),
        ("max_evidence_freshness_age_seconds", "7200.000000"),
    ):
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                _resigned_payload(forged),
            )

    forged_reason_counts = json.loads(json.dumps(payload))
    forged_reason_counts["reason_code_counts"][0]["count"] = "2.000000"
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(forged_reason_counts),
        )


def test_resigned_payload_recomputes_all_remaining_derived_fields_and_order() -> None:
    module = _module()
    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(
                module,
                (
                    _input(module, "private-pass"),
                    _input(
                        module,
                        "private-watch",
                        authority_score=d("0.700000"),
                        memory_alignment_score=d("0.650000"),
                        evidence_freshness_age_seconds=d("100000.000000"),
                    ),
                    _input(
                        module,
                        "private-block",
                        authority_score=d("0.400000"),
                        memory_alignment_score=d("0.450000"),
                        evidence_freshness_age_seconds=d("300000.000000"),
                    ),
                ),
            ),
        ),
    )
    assert isinstance(payload, dict)

    for field_name, forged_value in (
        ("watch_count", "2.000000"),
        ("block_count", "2.000000"),
        ("min_guard_score", "0.123456"),
        ("min_memory_alignment_score", "0.123456"),
    ):
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                _resigned_payload(forged),
            )

    forged_ratio = json.loads(json.dumps(payload))
    forged_ratio["reason_code_counts"][0]["row_ratio"] = "0.123456"
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(forged_ratio),
        )

    forged_order = json.loads(json.dumps(payload))
    forged_order["rows"][0], forged_order["rows"][1] = (
        forged_order["rows"][1],
        forged_order["rows"][0],
    )
    with pytest.raises(ValueError, match="deterministic report sequence"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            _resigned_payload(forged_order),
        )


def test_report_revalidates_direct_rows_against_its_config() -> None:
    module = _module()
    report = _report(module, (_input(module),))

    forged_freshness = replace(
        report.rows[0],
        freshness_score=d("0.123456"),
    )
    with pytest.raises(ValueError, match="freshness_score"):
        replace(
            report,
            rows=(forged_freshness,),
            derived_validation_digest="",
        )

    forged_guard = replace(
        report.rows[0],
        guard_score=d("0.123456"),
    )
    with pytest.raises(ValueError, match="guard_score"):
        replace(
            report,
            rows=(forged_guard,),
            average_guard_score=d("0.123456"),
            min_guard_score=d("0.123456"),
            derived_validation_digest="",
        )


def test_report_revalidation_rejects_rows_observed_after_generated_at() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    future_row = replace(
        report.rows[0],
        observed_at=GENERATED_AT + timedelta(microseconds=1),
    )

    with pytest.raises(ValueError, match="observed_at.*generated_at"):
        replace(
            report,
            rows=(future_row,),
            derived_validation_digest="",
        )


def test_mapping_payload_revalidation_rejects_rows_observed_after_generated_at() -> None:
    module = _module()
    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            _report(module, (_input(module),)),
        ),
    )
    assert isinstance(payload, dict)
    payload["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(microseconds=1)
    ).isoformat()
    payload = _resigned_payload(payload)

    with pytest.raises(ValueError, match="observed_at.*generated_at"):
        module.validate_research_strategy_source_authority_memory_guard_public_payload(
            payload,
        )
    with pytest.raises(ValueError, match="observed_at.*generated_at"):
        module.research_strategy_source_authority_memory_guard_report_payload(payload)


def test_phase_one_flags_cannot_be_downgraded_anywhere_in_the_payload_tree() -> None:
    module = _module()
    config = _config(module)
    report = _report(module, (_input(module),), cfg=config)

    with pytest.raises(ValueError, match="config.paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="input.report_only"):
        _input(module, report_only=False)
    with pytest.raises(ValueError, match="row.readonly"):
        replace(report.rows[0], readonly=False, validation_config=config)
    with pytest.raises(ValueError, match="reason_code_count.paper_only"):
        replace(report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report.report_only"):
        replace(report, report_only=False)

    payload = _thaw(
        module.research_strategy_source_authority_memory_guard_report_payload(
            report,
        ),
    )
    assert isinstance(payload, dict)
    for path, flag in (
        ((), "paper_only"),
        (("config",), "report_only"),
        (("rows", 0), "readonly"),
        (("reason_code_counts", 0), "paper_only"),
    ):
        forged = json.loads(json.dumps(payload))
        target: Any = forged
        for part in path:
            target = target[part]
        target[flag] = False
        with pytest.raises(ValueError, match=flag):
            module.validate_research_strategy_source_authority_memory_guard_public_payload(
                _resigned_payload(forged),
            )


def test_rejects_bad_decimal_types_flags_timestamps_and_manual_drift() -> None:
    module = _module()

    with pytest.raises(ValueError, match="pass_min_guard_score"):
        _config(module, pass_min_guard_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_guard_score"):
        _config(module, watch_min_guard_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_guard_score"):
        _config(module, pass_min_guard_score=d("0.500000"))
    with pytest.raises(ValueError, match="guard weights"):
        _config(module, authority_weight=d("0.600000"))
    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION,
            ),
        )

    with pytest.raises(ValueError, match="private_reference"):
        _input(module, " ")
    with pytest.raises(ValueError, match="authority_score"):
        _input(module, authority_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_alignment_score"):
        _input(module, memory_alignment_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="evidence_freshness_age_seconds"):
        _input(module, evidence_freshness_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="authority_quorum_count"):
        _input(module, authority_quorum_count=d("1.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 9, 16, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _report(
            module,
            (
                _input(
                    module,
                    observed_at=datetime(2026, 7, 9, 16, 1, tzinfo=UTC),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        _input(module, paper_only=False)

    report = _report(module, (_input(module),))
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="hold")
    with pytest.raises(ValueError, match="guard_score"):
        replace(report.rows[0], guard_score=ZERO, validation_config=_config(module))
    with pytest.raises(TypeError):
        class _BadRow(module.ResearchStrategySourceAuthorityMemoryGuardRow):  # type: ignore[misc, valid-type]
            pass


def test_public_api_and_module_scope_stay_report_only_safe_and_decimal_only() -> None:
    module = _module()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_STATUSES",
        "ResearchStrategySourceAuthorityMemoryGuardConfig",
        "ResearchStrategySourceAuthorityMemoryGuardInput",
        "ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount",
        "ResearchStrategySourceAuthorityMemoryGuardReport",
        "ResearchStrategySourceAuthorityMemoryGuardRow",
        "build_research_strategy_source_authority_memory_guard_report",
        "research_strategy_source_authority_memory_guard_report_digest",
        "research_strategy_source_authority_memory_guard_report_payload",
        "validate_research_strategy_source_authority_memory_guard_public_payload",
        "validate_research_strategy_source_authority_memory_guard_report_digest",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = _report(module, (_input(module),))
    for value in (report, report.rows[0], report.reason_code_counts[0], _config(module)):
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(item, Decimal):
                assert type(item) is Decimal
            if field.name.endswith(("_count", "_score", "_weight", "_seconds")):
                assert type(item) is Decimal

    unsafe_public_fields = {
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "position_size",
        "recommendation",
    }
    exported_fields = {
        field.name
        for cls in (
            type(_config(module)),
            type(_input(module)),
            type(report),
            type(report.rows[0]),
            type(report.reason_code_counts[0]),
        )
        for field in fields(cls)
    }
    assert unsafe_public_fields.isdisjoint(exported_fields)

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncpg",
        "boto3",
        "hmac",
        "httpx",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
    }
    imported_roots: set[str] = set()
    forbidden_calls = {
        "approve",
        "buy",
        "commit",
        "connect",
        "cursor",
        "dump",
        "execute",
        "executemany",
        "insert",
        "open",
        "patch",
        "place_order",
        "post",
        "put",
        "read",
        "read_bytes",
        "read_text",
        "request",
        "rollback",
        "sell",
        "send",
        "sign_transaction",
        "trade",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    assert imported_roots.isdisjoint(forbidden_import_roots)
    payload = module.research_strategy_source_authority_memory_guard_report_payload(
        report,
    )
    _assert_public_payload_decimal_strings(payload)
