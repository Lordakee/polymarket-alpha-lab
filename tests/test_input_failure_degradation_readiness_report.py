from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


MODULE_NAME = "polymarket_alpha_lab.input_failure_degradation_readiness_report"
SOURCE = Path("src/polymarket_alpha_lab/input_failure_degradation_readiness_report.py")
GENERATED_AT = datetime(2026, 7, 12, 10, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> object:
    return importlib.import_module(MODULE_NAME)


def failure(
    source_name: str,
    *,
    failed: bool = True,
    required: bool = True,
) -> object:
    return api().InputFailureSignal(
        source_name=source_name,
        failed=failed,
        required=required,
        blocking_reason=f"{source_name}_unavailable",
    )


def report(*signals: object, generated_at: datetime = GENERATED_AT) -> object:
    return api().build_input_failure_degradation_readiness_report(
        signals,
        generated_at=generated_at,
    )


@pytest.mark.parametrize(
    ("source_name", "expected_reason"),
    (
        ("scrapling", "scrapling_unavailable"),
        ("agent_reach", "agent_reach_unavailable"),
        ("llm_forecast", "llm_forecast_unavailable"),
        ("market_data", "market_data_unavailable"),
    ),
)
def test_any_required_input_failure_blocks_readonly_recommendations(
    source_name: str,
    expected_reason: str,
) -> None:
    result = report(failure(source_name))

    assert is_dataclass(result)
    assert result.degradation_status == "blocked_readonly_degraded"
    assert result.manual_review_required is True
    assert result.recommendation_allowed is False
    assert result.prohibited_recommendation_conditions == (
        "missing_required_input",
        "manual_review_pending",
        "readonly_degraded_state",
    )
    assert result.blocking_reasons == (expected_reason,)
    assert result.reason_codes == (
        "required_input_failed",
        "manual_review_required",
        "recommendation_prohibited",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_optional_failure_degrades_to_watch_without_enabling_recommendations() -> None:
    result = report(
        failure("scrapling", required=False),
        failure("agent_reach", failed=False),
        failure("llm_forecast", failed=False),
        failure("market_data", failed=False),
    )

    assert result.degradation_status == "watch_readonly_degraded"
    assert result.manual_review_required is True
    assert result.recommendation_allowed is False
    assert result.blocking_reasons == ("scrapling_unavailable",)
    assert result.reason_codes == (
        "optional_input_failed",
        "manual_review_required",
        "recommendation_prohibited",
    )
    assert result.prohibited_recommendation_conditions == (
        "manual_review_pending",
        "readonly_degraded_state",
    )


def test_no_failures_remains_ready_but_readonly_phase_one() -> None:
    result = report(
        failure("scrapling", failed=False),
        failure("agent_reach", failed=False),
        failure("llm_forecast", failed=False),
        failure("market_data", failed=False),
    )

    assert result.degradation_status == "ready_readonly"
    assert result.manual_review_required is False
    assert result.recommendation_allowed is True
    assert result.blocking_reasons == ()
    assert result.reason_codes == ("all_required_inputs_available",)
    assert result.prohibited_recommendation_conditions == (
        "phase_one_paper_only",
        "phase_one_report_only",
        "phase_one_readonly",
    )
    for condition in result.prohibited_recommendation_conditions:
        assert not any(term in condition for term in ("live", "order", "execution"))


def test_empty_signal_set_fails_closed_with_canonical_missing_signal_reason() -> None:
    result = report()

    assert result.degradation_status == "blocked_readonly_degraded"
    assert result.manual_review_required is True
    assert result.recommendation_allowed is False
    assert result.reason_codes == (
        "input_failure_signals_missing",
        "manual_review_required",
        "recommendation_prohibited",
    )
    assert result.blocking_reasons == ("input_failure_signals_missing",)
    assert result.prohibited_recommendation_conditions == (
        "missing_required_input",
        "manual_review_pending",
        "readonly_degraded_state",
    )

    with pytest.raises(ValueError, match="degradation_status must match input failures"):
        replace(
            result,
            degradation_status="ready_readonly",
            manual_review_required=False,
            recommendation_allowed=True,
            reason_codes=("all_required_inputs_available",),
            blocking_reasons=(),
            prohibited_recommendation_conditions=(
                "phase_one_paper_only",
                "phase_one_report_only",
                "phase_one_readonly",
            ),
            payload_digest="",
        )


def test_payload_is_public_deterministic_and_explains_manual_review() -> None:
    result = report(
        failure("scrapling"),
        failure("agent_reach"),
        failure("llm_forecast"),
        failure("market_data"),
    )

    payload = result.public_payload
    assert payload == {
        "generated_at": "2026-07-12T10:30:00+00:00",
        "degradation_status": "blocked_readonly_degraded",
        "manual_review_required": True,
        "recommendation_allowed": False,
        "reason_codes": [
            "required_input_failed",
            "manual_review_required",
            "recommendation_prohibited",
        ],
        "blocking_reasons": [
            "agent_reach_unavailable",
            "llm_forecast_unavailable",
            "market_data_unavailable",
            "scrapling_unavailable",
        ],
        "prohibited_recommendation_conditions": [
            "missing_required_input",
            "manual_review_pending",
            "readonly_degraded_state",
        ],
        "input_count": "4.000000",
        "failed_input_count": "4.000000",
        "required_failed_input_count": "4.000000",
        "signals": [
            {
                "source_name": "agent_reach",
                "failed": True,
                "required": True,
                "blocking_reason": "agent_reach_unavailable",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            {
                "source_name": "llm_forecast",
                "failed": True,
                "required": True,
                "blocking_reason": "llm_forecast_unavailable",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            {
                "source_name": "market_data",
                "failed": True,
                "required": True,
                "blocking_reason": "market_data_unavailable",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            {
                "source_name": "scrapling",
                "failed": True,
                "required": True,
                "blocking_reason": "scrapling_unavailable",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": result.payload_digest,
    }
    without_digest = dict(payload)
    without_digest.pop("payload_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert result.payload_digest == expected_digest


def test_public_payload_is_deeply_immutable_for_every_standard_mutator() -> None:
    payload = report(failure("scrapling")).public_payload

    _assert_json_payload_is_deeply_immutable(payload)


def test_generated_at_requires_exact_aware_datetime_and_normalizes_to_utc() -> None:
    offset = timezone(timedelta(hours=5, minutes=30))
    source = datetime(2026, 7, 12, 16, 0, tzinfo=offset)

    result = report(failure("scrapling"), generated_at=source)

    assert type(result.generated_at) is datetime
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.public_payload["generated_at"] == "2026-07-12T10:30:00+00:00"

    class DatetimeSubclass(datetime):
        pass

    invalid_values = (
        "2026-07-12T10:30:00+00:00",
        datetime(2026, 7, 12, 10, 30),
        DatetimeSubclass(2026, 7, 12, 10, 30, tzinfo=UTC),
    )
    for value in invalid_values:
        with pytest.raises(ValueError, match="generated_at.*timezone-aware datetime"):
            report(failure("scrapling"), generated_at=value)  # type: ignore[arg-type]


def test_signal_requires_and_publishes_all_phase_one_hard_flags() -> None:
    module = api()
    signal = failure("scrapling")

    assert signal.paper_only is True
    assert signal.report_only is True
    assert signal.readonly is True
    assert report(signal).public_payload["signals"] == [
        {
            "source_name": "scrapling",
            "failed": True,
            "required": True,
            "blocking_reason": "scrapling_unavailable",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    for field_name in ("paper_only", "report_only", "readonly"):
        for invalid_value in (False, 1):
            kwargs = {
                "source_name": "scrapling",
                "failed": True,
                "required": True,
                "blocking_reason": "scrapling_unavailable",
                field_name: invalid_value,
            }
            with pytest.raises(ValueError, match=field_name):
                module.InputFailureSignal(**kwargs)


@pytest.mark.parametrize(
    "invalid_value",
    (
        1,
        1.0,
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        Decimal("-1"),
        Decimal("1.5"),
    ),
)
@pytest.mark.parametrize(
    "field_name",
    ("input_count", "failed_input_count", "required_failed_input_count"),
)
def test_report_counts_require_exact_finite_nonnegative_whole_decimals(
    field_name: str,
    invalid_value: object,
) -> None:
    result = report(failure("scrapling"))

    with pytest.raises(ValueError, match=field_name):
        replace(result, **{field_name: invalid_value})


def test_report_counts_reject_decimal_subclasses() -> None:
    class DecimalSubclass(Decimal):
        pass

    result = report(failure("scrapling"))
    for field_name in (
        "input_count",
        "failed_input_count",
        "required_failed_input_count",
    ):
        with pytest.raises(ValueError, match=field_name):
            replace(result, **{field_name: DecimalSubclass("1")})


@pytest.mark.parametrize(
    "field_name",
    ("input_count", "failed_input_count", "required_failed_input_count"),
)
@pytest.mark.parametrize(
    ("invalid_value", "message"),
    (
        (Decimal("0"), "must use six decimal places"),
        (Decimal("-0.000000"), "must use positive zero"),
    ),
)
def test_public_payload_rejects_rehashed_noncanonical_stored_counts(
    field_name: str,
    invalid_value: Decimal,
    message: str,
) -> None:
    result = report()
    unsigned_payload = dict(result.public_payload)
    unsigned_payload.pop("payload_digest")
    unsigned_payload[field_name] = format(invalid_value, "f")
    forged_digest = hashlib.sha256(
        json.dumps(
            unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    object.__setattr__(result, field_name, invalid_value)
    object.__setattr__(result, "payload_digest", forged_digest)

    with pytest.raises(ValueError, match=message):
        _ = result.public_payload


@pytest.mark.parametrize(
    "field_name",
    (
        "reason_codes",
        "blocking_reasons",
        "prohibited_recommendation_conditions",
    ),
)
def test_derived_string_tuples_require_exact_tuple_and_string_types(
    field_name: str,
) -> None:
    class StringSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    result = report(failure("scrapling"))
    expected = getattr(result, field_name)
    invalid_values = (
        TupleSubclass(expected),
        tuple(StringSubclass(value) for value in expected),
    )
    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match=field_name):
            replace(
                result,
                **{field_name: invalid_value, "payload_digest": ""},
            )

        tampered = report(failure("scrapling"))
        object.__setattr__(tampered, field_name, invalid_value)
        with pytest.raises(ValueError, match=field_name):
            _ = tampered.public_payload


def test_payload_digest_is_stored_filled_validated_and_rechecked() -> None:
    module = api()
    result = report(failure("scrapling"))

    assert "payload_digest" in {
        field.name for field in fields(module.InputFailureDegradationReadinessReport)
    }
    assert type(result.payload_digest) is str
    assert len(result.payload_digest) == 64
    assert replace(result, payload_digest="").payload_digest == result.payload_digest
    assert replace(result, payload_digest=result.payload_digest) == result

    for invalid_digest in (None, "", "0" * 64, result.payload_digest.upper()):
        if invalid_digest == "":
            continue
        with pytest.raises(ValueError, match="payload_digest"):
            replace(result, payload_digest=invalid_digest)

    tampered = report(failure("scrapling"))
    object.__setattr__(tampered, "failed_input_count", Decimal("0.000000"))
    with pytest.raises(ValueError, match="failed_input_count"):
        _ = tampered.public_payload

    digest_tampered = report(failure("scrapling"))
    object.__setattr__(digest_tampered, "payload_digest", "0" * 64)
    with pytest.raises(ValueError, match="payload_digest"):
        _ = digest_tampered.public_payload


def test_public_payload_rechecks_tampered_signal_hard_flags() -> None:
    result = report(failure("scrapling"))
    object.__setattr__(result.signals[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        _ = result.public_payload


def test_signal_and_report_validation_rejects_unsafe_phase_one_drift() -> None:
    module = api()

    assert type(failure("scrapling")) is module.InputFailureSignal
    with pytest.raises(FrozenInstanceError):
        failure("scrapling").failed = False  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubSignal(module.InputFailureSignal):  # type: ignore[misc,valid-type]
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubReport(module.InputFailureDegradationReadinessReport):  # type: ignore[misc,valid-type]
            pass

    with pytest.raises(ValueError, match="source_name"):
        module.InputFailureSignal(
            source_name="Scrapling",
            failed=True,
            required=True,
            blocking_reason="scrapling_unavailable",
        )
    with pytest.raises(ValueError, match="blocking_reason"):
        module.InputFailureSignal(
            source_name="scrapling",
            failed=True,
            required=True,
            blocking_reason="",
        )
    with pytest.raises(ValueError, match="signals"):
        report(failure("scrapling"), failure("scrapling"))
    with pytest.raises(ValueError, match="paper_only"):
        module.build_input_failure_degradation_readiness_report(
            (failure("scrapling"),),
            generated_at=GENERATED_AT,
            paper_only=False,
        )


def test_module_keeps_readonly_no_network_no_execution_surface() -> None:
    module = api()
    source = SOURCE.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        ".write(",
        "open(",
        "live trading",
        "auth",
        "wallet",
        "private_key",
        "secret",
        "signature",
        "signing",
    )
    for term in forbidden_terms:
        assert term not in source

    public_names = set(module.__all__)
    assert public_names == {
        "InputFailureDegradationReadinessReport",
        "InputFailureSignal",
        "build_input_failure_degradation_readiness_report",
    }
    for name in public_names:
        assert inspect.getmodule(getattr(module, name)) is module

    type_hints = {
        field.name: field.type
        for field in fields(module.InputFailureDegradationReadinessReport)
    }
    assert type_hints["input_count"] == Decimal
    assert type_hints["failed_input_count"] == Decimal
    assert type_hints["required_failed_input_count"] == Decimal
    assert type_hints["generated_at"] == datetime


def _assert_json_payload_is_deeply_immutable(payload: object) -> None:
    assert isinstance(payload, dict)
    signals = payload["signals"]
    assert isinstance(signals, list)
    signal = signals[0]
    assert isinstance(signal, dict)

    object_mutators = (
        lambda value: value.__setitem__("readonly", False),
        lambda value: value.__delitem__("readonly"),
        lambda value: value.clear(),
        lambda value: value.pop("readonly"),
        lambda value: value.popitem(),
        lambda value: value.setdefault("extra", True),
        lambda value: value.update({"readonly": False}),
        lambda value: value.__ior__({"readonly": False}),
    )
    for value in (payload, signal):
        for mutate in object_mutators:
            with pytest.raises(TypeError, match="payload is immutable"):
                mutate(value)

    array_mutators = (
        lambda value: value.__setitem__(0, value[0]),
        lambda value: value.__delitem__(0),
        lambda value: value.append(value[0]),
        lambda value: value.clear(),
        lambda value: value.extend((value[0],)),
        lambda value: value.insert(0, value[0]),
        lambda value: value.pop(),
        lambda value: value.remove(value[0]),
        lambda value: value.reverse(),
        lambda value: value.sort(),
        lambda value: value.__iadd__((value[0],)),
        lambda value: value.__imul__(2),
    )
    for value in (payload["reason_codes"], signals):
        assert isinstance(value, list)
        for mutate in array_mutators:
            with pytest.raises(TypeError, match="payload is immutable"):
                mutate(value)
