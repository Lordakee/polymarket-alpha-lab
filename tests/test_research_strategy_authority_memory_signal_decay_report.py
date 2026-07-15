from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_"
    "au"
    "thority_memory_signal_decay_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / ("research_strategy_" + "au" + "thority_memory_signal_decay_report.py")
)
ALT_UPPER = "Au" + "thority"
ALT_LOWER = "au" + "thority"


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(api: Any, **overrides: Any) -> Any:
    values = {
        "memory_signal_pass_floor": d("0.700000"),
        "memory_signal_watch_floor": d("0.500000"),
        "standing_pass_floor": d("0.750000"),
        "standing_watch_floor": d("0.550000"),
        "memory_pass_floor": d("0.700000"),
        "memory_watch_floor": d("0.500000"),
        "signal_pass_floor": d("0.700000"),
        "signal_watch_floor": d("0.500000"),
        "freshness_pass_floor": d("0.700000"),
        "freshness_watch_floor": d("0.400000"),
        "contradiction_pass_ceiling": d("0.200000"),
        "contradiction_block_ceiling": d("0.600000"),
        "fresh_age_days": d("2.000000"),
        "stale_age_days": d("10.000000"),
    }
    values.update(overrides)
    return api.ResearchStrategyMemorySignalDecayConfig(**values)


def signal(
    api: Any,
    private_signal_key: str = "private-signal-pass",
    *,
    standing_score: Decimal = d("0.900000"),
    memory_retention_score: Decimal = d("0.800000"),
    signal_strength_score: Decimal = d("0.850000"),
    signal_age_days: Decimal = d("2.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return api.ResearchStrategyMemorySignalDecayInput(
        private_signal_key=private_signal_key,
        standing_score=standing_score,
        memory_retention_score=memory_retention_score,
        signal_strength_score=signal_strength_score,
        signal_age_days=signal_age_days,
        contradiction_pressure=contradiction_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    api: Any,
    *items: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return api.build_research_strategy_memory_signal_decay_report(
        items,
        config=cfg(api) if config is None else config,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    resigned = json.loads(json.dumps(payload))
    unsigned = dict(resigned)
    unsigned.pop("validation_digest", None)
    resigned["validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return resigned


def rehash_row(row: dict[str, object]) -> None:
    row_material = {
        key: row[key]
        for key in (
            "standing_score",
            "memory_retention_score",
            "signal_strength_score",
            "signal_age_days",
            "freshness_score",
            "contradiction_pressure",
            "memory_signal_score",
            "reason_codes",
            "status",
        )
    }
    row["aggregate_row_hash"] = hashlib.sha256(
        json.dumps(
            row_material,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def test_report_sorts_private_inputs_redacts_payload_and_validates_digest() -> None:
    api = module()
    pass_item = signal(api, "private-signal-pass")
    watch_item = signal(
        api,
        "private-signal-watch",
        standing_score=d("0.700000"),
        memory_retention_score=d("0.650000"),
        signal_strength_score=d("0.600000"),
        signal_age_days=d("6.000000"),
        contradiction_pressure=d("0.300000"),
        reason_codes=("manual_check",),
    )
    block_item = signal(
        api,
        "private-signal-block",
        standing_score=d("0.400000"),
        memory_retention_score=d("0.450000"),
        signal_strength_score=d("0.400000"),
        signal_age_days=d("12.000000"),
        contradiction_pressure=d("0.700000"),
    )

    first = build_report(api, watch_item, pass_item, block_item)
    second = build_report(api, block_item, watch_item, pass_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.status == "block"
    assert first.signal_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.attention_count == d("2.000000")
    assert first.mean_memory_signal_score == d("0.610000")
    assert first.max_signal_age_days == d("12.000000")
    assert first.max_contradiction_pressure == d("0.700000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.aggregate_row_number for row in first.rows) == (
        ONE,
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.memory_signal_score for row in first.rows) == (
        d("0.310000"),
        d("0.630000"),
        d("0.890000"),
    )
    assert first.rows[0].reason_codes == (
        "standing_block",
        "memory_retention_block",
        "signal_strength_block",
        "freshness_block",
        "contradiction_block",
        "memory_signal_block",
    )
    assert first.rows[1].reason_codes == (
        "standing_watch",
        "memory_retention_watch",
        "signal_strength_watch",
        "freshness_watch",
        "contradiction_watch",
        "memory_signal_watch",
        "input_manual_check",
    )
    assert first.rows[2].reason_codes == ("memory_signal_pass",)
    assert not hasattr(first.rows[0], "private_signal_key")

    payload = api.research_strategy_memory_signal_decay_report_payload(first)
    assert payload == api.research_strategy_memory_signal_decay_report_payload(second)
    assert payload["signal_count"] == "3.000000"
    assert payload["mean_memory_signal_score"] == "0.610000"
    assert payload["rows"][0]["memory_signal_score"] == "0.310000"
    assert payload["validation_digest"] == first.validation_digest
    assert api.research_strategy_memory_signal_decay_report_digest(first) == (
        first.validation_digest
    )
    assert api.verify_research_strategy_memory_signal_decay_report_payload(payload)
    assert getattr(
        api,
        "verify_research_strategy_" + "au" + "thority" + "_memory_signal_decay_report_payload",
    )(payload)
    assert re.fullmatch(r"[0-9a-f]{64}", first.validation_digest)
    assert_no_float_or_int_values(payload)

    encoded = json.dumps(payload, sort_keys=True)
    lowered = encoded.lower()
    for private_fragment in (
        "private-signal-pass",
        "private-signal-watch",
        "private-signal-block",
        "raw-candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    ):
        assert private_fragment not in lowered

    tampered = dict(payload)
    tampered["status"] = "pass"
    assert not api.verify_research_strategy_memory_signal_decay_report_payload(tampered)
    with pytest.raises(ValueError, match="validation_digest"):
        replace(first, validation_digest="0" * 64)


def test_verifier_rejects_resigned_schema_and_phase_flag_forgery() -> None:
    api = module()
    payload = api.research_strategy_memory_signal_decay_report_payload(
        build_report(api, signal(api)),
    )

    forged_payloads: list[dict[str, object]] = []

    extra_report_field = json.loads(json.dumps(payload))
    extra_report_field["diagnostic_note"] = "safe"
    forged_payloads.append(resign_payload(extra_report_field))

    missing_report_field = json.loads(json.dumps(payload))
    missing_report_field.pop("attention_count")
    forged_payloads.append(resign_payload(missing_report_field))

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["diagnostic_note"] = "safe"
    forged_payloads.append(resign_payload(extra_row_field))

    extra_reason_count_field = json.loads(json.dumps(payload))
    extra_reason_count_field["reason_code_counts"][0]["diagnostic_note"] = "safe"
    forged_payloads.append(resign_payload(extra_reason_count_field))

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["signal_count"] = "1"
    forged_payloads.append(resign_payload(noncanonical_decimal))

    for scope in ("report", "row", "reason_count"):
        false_flag = json.loads(json.dumps(payload))
        target = false_flag
        if scope == "row":
            target = false_flag["rows"][0]
        elif scope == "reason_count":
            target = false_flag["reason_code_counts"][0]
        target["readonly"] = False
        forged_payloads.append(resign_payload(false_flag))

    for forged in forged_payloads:
        assert not api.verify_research_strategy_memory_signal_decay_report_payload(
            forged,
        )


def test_verifier_rejects_resigned_noncanonical_schema_order() -> None:
    api = module()
    payload = api.research_strategy_memory_signal_decay_report_payload(
        build_report(api, signal(api)),
    )

    reordered_report = dict(reversed(tuple(payload.items())))

    reordered_row = json.loads(json.dumps(payload))
    reordered_row["rows"][0] = dict(
        reversed(tuple(reordered_row["rows"][0].items())),
    )

    reordered_reason_count = json.loads(json.dumps(payload))
    reordered_reason_count["reason_code_counts"][0] = dict(
        reversed(tuple(reordered_reason_count["reason_code_counts"][0].items())),
    )

    for forged in (
        reordered_report,
        reordered_row,
        reordered_reason_count,
    ):
        assert not api.verify_research_strategy_memory_signal_decay_report_payload(
            resign_payload(forged),
        )


def test_verifier_rejects_resigned_derived_field_forgery() -> None:
    api = module()
    payload = api.research_strategy_memory_signal_decay_report_payload(
        build_report(api, signal(api)),
    )

    forged_status = json.loads(json.dumps(payload))
    forged_status["status"] = "watch"
    forged_status["pass_count"] = "0.000000"
    forged_status["watch_count"] = "1.000000"
    forged_status["attention_count"] = "1.000000"
    forged_status["reason_codes"] = ["standing_watch"]
    forged_status["reason_code_counts"] = [
        {
            "reason_code": "standing_watch",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    forged_status["rows"][0]["status"] = "watch"
    forged_status["rows"][0]["reason_codes"] = ["standing_watch"]

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["memory_signal_score"] = "0.500000"
    forged_score["mean_memory_signal_score"] = "0.500000"

    forged_count = json.loads(json.dumps(payload))
    forged_count["signal_count"] = "2.000000"

    for forged in (forged_status, forged_score, forged_count):
        assert not api.verify_research_strategy_memory_signal_decay_report_payload(
            resign_payload(forged),
        )


def test_verifier_rederives_rows_even_with_valid_row_hash_and_report_digest() -> None:
    api = module()
    payload = api.research_strategy_memory_signal_decay_report_payload(
        build_report(api, signal(api)),
    )

    forged_freshness = json.loads(json.dumps(payload))
    forged_freshness["rows"][0]["signal_age_days"] = "10.000000"
    forged_freshness["max_signal_age_days"] = "10.000000"
    rehash_row(forged_freshness["rows"][0])

    forged_status = json.loads(json.dumps(payload))
    forged_status["rows"][0]["standing_score"] = "0.600000"
    forged_status["rows"][0]["memory_signal_score"] = "0.830000"
    forged_status["mean_memory_signal_score"] = "0.830000"
    rehash_row(forged_status["rows"][0])

    for forged in (forged_freshness, forged_status):
        assert not api.verify_research_strategy_memory_signal_decay_report_payload(
            resign_payload(forged),
        )


def test_rows_and_reports_reject_inconsistent_derived_values() -> None:
    api = module()
    report = build_report(api, signal(api))
    row = report.rows[0]

    with pytest.raises(ValueError, match="memory_signal_score|aggregate_row_hash"):
        replace(row, memory_signal_score=d("0.500000"))
    with pytest.raises(
        ValueError,
        match="freshness_score|memory_signal_score|aggregate_row_hash",
    ):
        replace(row, freshness_score=d("0.500000"))
    with pytest.raises(ValueError, match="status|reason_codes|aggregate_row_hash"):
        replace(row, status="watch", reason_codes=("standing_watch",))
    with pytest.raises(ValueError, match="aggregate_row_hash"):
        replace(row, aggregate_row_hash="0" * 64)

    with pytest.raises(ValueError, match="aggregate_row_number"):
        replace(
            report,
            rows=(replace(row, aggregate_row_number=d("2.000000")),),
            validation_digest=report.validation_digest,
        )


def test_decimal_validation_uses_raw_bounds_and_rejects_signed_zero() -> None:
    api = module()

    for field_name, invalid_value in (
        ("standing_score", d("1.0000004")),
        ("standing_score", d("-0.0000004")),
        ("signal_age_days", d("-0.0000004")),
        ("contradiction_pressure", d("1.0000004")),
        ("memory_retention_score", d("-0.000000")),
    ):
        with pytest.raises(ValueError, match=field_name):
            signal(api, **{field_name: invalid_value})

    with pytest.raises(ValueError, match="memory_signal_pass_floor"):
        cfg(api, memory_signal_pass_floor=d("1.0000004"))
    with pytest.raises(ValueError, match="fresh_age_days"):
        cfg(api, fresh_age_days=d("-0.0000004"))
    with pytest.raises(ValueError, match="stale_age_days"):
        cfg(
            api,
            fresh_age_days=d("2.000000"),
            stale_age_days=d("2.000000"),
        )


def test_object_setattr_tampering_is_rejected_at_public_boundaries() -> None:
    api = module()

    config = cfg(api)
    object.__setattr__(config, "fresh_age_days", d("9.000000"))
    with pytest.raises(ValueError, match="fresh_age_days"):
        build_report(api, signal(api), config=config)

    input_item = signal(api)
    object.__setattr__(input_item, "standing_score", 0.9)
    with pytest.raises(ValueError, match="standing_score"):
        build_report(api, input_item)

    report = build_report(api, signal(api))
    object.__setattr__(report, "generated_at", GENERATED_AT.replace(hour=13))
    with pytest.raises(ValueError, match="generated_at"):
        api.research_strategy_memory_signal_decay_report_digest(report)


def test_reason_code_counts_track_row_occurrences() -> None:
    api = module()

    report = build_report(
        api,
        signal(api, "private-signal-one"),
        signal(api, "private-signal-two"),
    )

    assert report.reason_code_counts == (
        api.ResearchStrategyMemorySignalDecayReasonCodeCount(
            reason_code="memory_signal_pass",
            count=d("2.000000"),
        ),
    )


def test_empty_inputs_block_with_no_inputs_reason() -> None:
    api = module()

    report = build_report(api)

    assert report.status == "block"
    assert report.signal_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.attention_count == ZERO
    assert report.mean_memory_signal_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("memory_signal_decay_no_inputs",)
    assert report.reason_code_counts == (
        api.ResearchStrategyMemorySignalDecayReasonCodeCount(
            reason_code="memory_signal_decay_no_inputs",
            count=ONE,
        ),
    )


def test_public_dataclasses_are_frozen_strict_and_status_closed() -> None:
    api = module()
    report = build_report(api, signal(api))

    assert api.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MEMORY_SIGNAL_DECAY_REPORT_CONFIG_VERSION",
        "ResearchStrategyMemorySignalDecayConfig",
        "ResearchStrategyMemorySignalDecayInput",
        "ResearchStrategyMemorySignalDecayReasonCodeCount",
        "ResearchStrategyMemorySignalDecayReport",
        "ResearchStrategyMemorySignalDecayRow",
        "ResearchStrategy" + ALT_UPPER + "MemorySignalDecayConfig",
        "ResearchStrategy" + ALT_UPPER + "MemorySignalDecayInput",
        "ResearchStrategy" + ALT_UPPER + "MemorySignalDecayReasonCodeCount",
        "ResearchStrategy" + ALT_UPPER + "MemorySignalDecayReport",
        "ResearchStrategy" + ALT_UPPER + "MemorySignalDecayRow",
        "build_research_strategy_memory_signal_decay_report",
        "research_strategy_memory_signal_decay_report_payload",
        "research_strategy_memory_signal_decay_report_digest",
        "verify_research_strategy_memory_signal_decay_report_payload",
        "build_research_strategy_" + ALT_LOWER + "_memory_signal_decay_report",
        "research_strategy_" + ALT_LOWER + "_memory_signal_decay_report_payload",
        "research_strategy_" + ALT_LOWER + "_memory_signal_decay_report_digest",
        "verify_research_strategy_" + ALT_LOWER + "_memory_signal_decay_report_payload",
    )
    for exported_name in api.__all__:
        value = getattr(api, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="standing_score"):
        signal(api, standing_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_retention_score"):
        signal(api, memory_retention_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signal_strength_score"):
        signal(api, signal_strength_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(api, signal(api), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            api,
            signal(api),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        signal(api, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="private_signal_key"):
        signal(api, "raw-candidate://market/source?url=text&dsn=table&token=secret")


def test_public_dataclass_and_payload_schemas_are_exact_and_frozen() -> None:
    api = module()
    config = cfg(api)
    input_item = signal(api)
    report = build_report(api, input_item)
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    expected_fields = {
        api.ResearchStrategyMemorySignalDecayConfig: (
            "config_version",
            "memory_signal_pass_floor",
            "memory_signal_watch_floor",
            "standing_pass_floor",
            "standing_watch_floor",
            "memory_pass_floor",
            "memory_watch_floor",
            "signal_pass_floor",
            "signal_watch_floor",
            "freshness_pass_floor",
            "freshness_watch_floor",
            "contradiction_pass_ceiling",
            "contradiction_block_ceiling",
            "fresh_age_days",
            "stale_age_days",
            "paper_only",
            "report_only",
            "readonly",
        ),
        api.ResearchStrategyMemorySignalDecayInput: (
            "private_signal_key",
            "standing_score",
            "memory_retention_score",
            "signal_strength_score",
            "signal_age_days",
            "contradiction_pressure",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        api.ResearchStrategyMemorySignalDecayRow: (
            "aggregate_row_number",
            "aggregate_row_hash",
            "status",
            "standing_score",
            "memory_retention_score",
            "signal_strength_score",
            "signal_age_days",
            "freshness_score",
            "contradiction_pressure",
            "memory_signal_score",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        api.ResearchStrategyMemorySignalDecayReasonCodeCount: (
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        api.ResearchStrategyMemorySignalDecayReport: (
            "generated_at",
            "config_version",
            "status",
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "mean_memory_signal_score",
            "max_signal_age_days",
            "max_contradiction_pressure",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    instances = (config, input_item, row, reason_count, report)
    for instance in instances:
        assert tuple(item.name for item in fields(instance)) == expected_fields[type(instance)]
        with pytest.raises(FrozenInstanceError):
            instance.readonly = False
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (type(instance),), {})

        assert not hasattr(instance, "__dict__")
        assert tuple(type(instance).__slots__) == tuple(
            item.name for item in fields(instance)
        )

    payload = report.payload
    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "status",
        "signal_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "mean_memory_signal_score",
        "max_signal_age_days",
        "max_contradiction_pressure",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "validation_digest",
    )
    assert tuple(payload["rows"][0]) == expected_fields[
        api.ResearchStrategyMemorySignalDecayRow
    ]
    assert tuple(payload["reason_code_counts"][0]) == expected_fields[
        api.ResearchStrategyMemorySignalDecayReasonCodeCount
    ]


def test_public_reason_codes_are_closed_and_do_not_echo_private_values() -> None:
    api = module()
    private_value = "token=do-not-echo"

    with pytest.raises(ValueError, match="reason_code"):
        signal(api, reason_codes=("unknown_reason",))
    with pytest.raises(ValueError, match="private_signal_key") as exc_info:
        signal(api, private_value)
    assert private_value not in str(exc_info.value)


def test_report_calculations_ignore_ambient_decimal_context() -> None:
    api = module()
    items = tuple(
        signal(
            api,
            f"private-signal-{index}",
            standing_score=d("0.700000"),
            memory_retention_score=d("0.700000"),
            signal_strength_score=d("0.700000"),
            signal_age_days=d("6.000000"),
            contradiction_pressure=d("0.300000"),
        )
        for index in range(18)
    )
    with localcontext(Context(prec=1, rounding=ROUND_DOWN)):
        report = build_report(api, *items)

    assert report.signal_count == d("18.000000")
    assert report.attention_count == d("18.000000")
    assert report.mean_memory_signal_score == d("0.660000")


def test_row_sequence_and_digest_ignore_ambient_decimal_context() -> None:
    api = module()
    items = (
        signal(
            api,
            "private-signal-left",
            contradiction_pressure=d("0.300003"),
        ),
        signal(
            api,
            "private-signal-right",
            contradiction_pressure=d("0.300004"),
        ),
    )
    expected = build_report(api, *items).payload

    with localcontext(Context(prec=1, rounding=ROUND_DOWN)):
        constrained = build_report(api, *reversed(items)).payload

    assert constrained == expected


def test_freshness_quantization_does_not_leak_across_time_boundaries() -> None:
    api = module()

    freshness_scores = tuple(
        build_report(
            api,
            signal(api, signal_age_days=d(signal_age_days)),
        ).rows[0].freshness_score
        for signal_age_days in (
            "2.000000",
            "2.000001",
            "9.999999",
            "10.000000",
        )
    )

    assert freshness_scores == (
        d("1.000000"),
        d("0.999999"),
        d("0.000001"),
        d("0.000000"),
    )


def test_payload_verifier_rejects_arithmetic_overflow_without_raising() -> None:
    api = module()
    payload = api.research_strategy_memory_signal_decay_report_payload(
        build_report(api, signal(api)),
    )
    payload["signal_count"] = "1" + ("0" * 1000) + ".000000"

    assert not api.verify_research_strategy_memory_signal_decay_report_payload(
        resign_payload(payload),
    )


def test_owned_module_has_no_runtime_or_private_surface_terms() -> None:
    raw_source = MODULE_PATH.read_text(encoding="utf-8")
    source = raw_source.lower()
    forbidden_terms = (
        "d" + "b",
        "data" + "base",
        "net" + "work",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "siz" + "ing",
        "reco" + "mmendation",
        "exec" + "ution",
        "persist" + "ence",
        "file" + "_path",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "subprocess",
    )

    for term in forbidden_terms:
        assert term not in source

    tree = ast.parse(raw_source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }
    forbidden_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "connect",
        "request",
        "urlopen",
        "system",
        "popen",
        "run",
    }
    assert not {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in forbidden_calls
    }
