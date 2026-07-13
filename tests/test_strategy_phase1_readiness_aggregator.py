from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, make_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from json import dumps
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 58, tzinfo=UTC)
FORBIDDEN_SOURCE_SNIPPETS = (
    "requests",
    "httpx",
    "urllib",
    "socket",
    "sqlite",
    "sqlalchemy",
    "psycopg",
    "supabase",
    "web3",
    "clob",
    "private_key",
    "secret",
    "place_",
    "execute",
    "subprocess",
    "open(",
    "Path(",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _TupleSubclass(tuple):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.strategy_phase1_readiness_aggregator")


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object):
    module = api()
    values = {
        "signal_id": "signal-alpha",
        "event_ref": "event-alpha",
        "market_ref": "market-alpha",
        "observed_at": OBSERVED_AT,
        "edge_score": d("0.080000"),
        "cost_score": d("0.020000"),
        "liquidity_score": d("0.900000"),
        "resolution_score": d("0.850000"),
        "freshness_score": d("0.950000"),
        "manual_blocker_count": d("0"),
        "source_status": "pass",
        "source_reason_codes": ("cost_adjusted_edge_ready",),
    }
    values.update(overrides)
    return module.StrategyPhase1ReadinessSignal(**values)


def report(*signals: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_phase1_readiness_report(signals, generated_at=generated_at)


def test_aggregates_key_phase1_signals_into_readonly_report() -> None:
    result = report(
        signal(signal_id="ready", edge_score=d("0.090000")),
        signal(
            signal_id="watch",
            edge_score=d("0.020000"),
            cost_score=d("0.050000"),
            liquidity_score=d("0.600000"),
            resolution_score=d("0.650000"),
            freshness_score=d("0.700000"),
            source_status="watch",
            source_reason_codes=("candidate_stale",),
        ),
        signal(
            signal_id="blocked",
            edge_score=d("-0.010000"),
            cost_score=d("0.090000"),
            liquidity_score=d("0.300000"),
            resolution_score=d("0.400000"),
            freshness_score=d("0.500000"),
            manual_blocker_count=d("2"),
            source_status="block",
            source_reason_codes=("manual_blocker_present",),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-phase1-readiness-aggregator-v0"
    assert result.signal_count == d("3")
    assert result.ready_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.manual_blocker_count == d("2")
    assert result.mean_edge_score == d("0.033333")
    assert result.mean_cost_score == d("0.053333")
    assert result.mean_liquidity_score == d("0.600000")
    assert result.mean_resolution_score == d("0.633333")
    assert result.mean_freshness_score == d("0.716667")
    assert result.status == "block"
    assert result.reason_codes == ("phase1_readiness_report_block", "manual_blocker_review")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    ready, watch, blocked = result.rows
    assert ready.signal_id == "ready"
    assert ready.status == "ready"
    assert ready.readiness_score == d("0.760000")
    assert ready.reason_codes == ("phase1_readiness_ready",)

    assert watch.signal_id == "watch"
    assert watch.status == "watch"
    assert watch.readiness_score == d("0.430000")
    assert watch.reason_codes == (
        "candidate_stale",
        "cost_pressure_watch",
        "edge_pressure_watch",
        "freshness_pressure_watch",
        "liquidity_pressure_watch",
        "readiness_score_watch",
        "resolution_pressure_watch",
    )

    assert blocked.signal_id == "blocked"
    assert blocked.status == "block"
    assert blocked.readiness_score == d("0.230000")
    assert blocked.reason_codes == (
        "edge_pressure_block",
        "liquidity_pressure_block",
        "manual_blocker_present",
        "manual_blocker_review",
        "resolution_pressure_block",
    )


def test_empty_report_is_readonly_and_digest_checked() -> None:
    result = report()

    assert result.signal_count == d("0")
    assert result.ready_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.manual_blocker_count == d("0")
    assert result.rows == ()
    assert result.status == "watch"
    assert result.reason_codes == ("phase1_readiness_report_empty",)
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_source_watch_penalty_uses_status_instead_of_a_specific_reason_code() -> None:
    result = report(
        signal(
            signal_id="source-watch",
            source_status="watch",
            source_reason_codes=("source_freshness_watch",),
        ),
    )

    row = result.rows[0]
    assert row.source_status == "watch"
    assert row.source_reason_codes == ("source_freshness_watch",)
    assert row.readiness_score == d("0.730000")
    assert row.status == "watch"
    assert row.reason_codes == ("source_freshness_watch",)


def test_blocked_source_alias_cannot_be_promoted_to_ready() -> None:
    row = report(
        signal(
            signal_id="source-blocked",
            source_status="blocked",
            source_reason_codes=("source_unavailable",),
        ),
    ).rows[0]

    assert row.source_status == "blocked"
    assert row.status == "block"
    assert row.reason_codes == ("source_unavailable",)


@pytest.mark.parametrize(
    ("overrides", "expected_score", "expected_reason"),
    (
        (
            {
                "freshness_score": d("0.700000"),
                "source_reason_codes": (),
            },
            d("0.710000"),
            "freshness_pressure_watch",
        ),
        (
            {
                "edge_score": d("0.050000"),
                "cost_score": d("0.040000"),
                "liquidity_score": d("0.750000"),
                "resolution_score": d("0.750000"),
                "freshness_score": d("0.750000"),
                "source_reason_codes": (),
            },
            d("0.580000"),
            "readiness_score_watch",
        ),
    ),
)
def test_watch_rows_explain_freshness_and_composite_score_pressure(
    overrides: dict[str, object],
    expected_score: Decimal,
    expected_reason: str,
) -> None:
    row = report(signal(**overrides)).rows[0]

    assert row.status == "watch"
    assert row.readiness_score == expected_score
    assert expected_reason in row.reason_codes


def test_payload_is_json_ready_decimal_strings_and_digest_checked() -> None:
    result = report(signal(signal_id="payload"))

    payload = api().strategy_phase1_readiness_report_payload(result)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["mean_edge_score"] == "0.080000"
    assert payload["rows"][0]["readiness_score"] == "0.760000"
    assert payload["rows"][0]["derived_validation_digest"] == result.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        else:
            assert not isinstance(value, float)
            assert not isinstance(value, Decimal)

    walk(payload)


def test_payload_and_digests_use_field_semantic_decimal_text() -> None:
    module = api()
    result = report(
        signal(
            edge_score=d("1.000000"),
            cost_score=d("0.000000"),
            liquidity_score=d("1.000000"),
            resolution_score=d("1.000000"),
            freshness_score=d("1.000000"),
            manual_blocker_count=d("0.000000"),
            source_reason_codes=(),
        ),
    )

    payload = module.strategy_phase1_readiness_report_payload(result)
    row_payload = payload["rows"][0]

    assert {
        field_name: row_payload[field_name]
        for field_name in (
            "edge_score",
            "cost_score",
            "liquidity_score",
            "resolution_score",
            "freshness_score",
            "readiness_score",
        )
    } == {
        "edge_score": "1.000000",
        "cost_score": "0.000000",
        "liquidity_score": "1.000000",
        "resolution_score": "1.000000",
        "freshness_score": "1.000000",
        "readiness_score": "0.880000",
    }
    assert row_payload["manual_blocker_count"] == "0"
    assert {
        field_name: payload[field_name]
        for field_name in (
            "signal_count",
            "ready_count",
            "watch_count",
            "block_count",
            "manual_blocker_count",
        )
    } == {
        "signal_count": "1",
        "ready_count": "1",
        "watch_count": "0",
        "block_count": "0",
        "manual_blocker_count": "0",
    }
    assert {
        field_name: payload[field_name]
        for field_name in (
            "mean_edge_score",
            "mean_cost_score",
            "mean_liquidity_score",
            "mean_resolution_score",
            "mean_freshness_score",
        )
    } == {
        "mean_edge_score": "1.000000",
        "mean_cost_score": "0.000000",
        "mean_liquidity_score": "1.000000",
        "mean_resolution_score": "1.000000",
        "mean_freshness_score": "1.000000",
    }

    unsigned_row_payload = dict(row_payload)
    row_digest = unsigned_row_payload.pop("derived_validation_digest")
    assert row_digest == sha256(
        dumps(
            unsigned_row_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    unsigned_report_payload = dict(payload)
    report_digest = unsigned_report_payload.pop("derived_validation_digest")
    assert report_digest == sha256(
        dumps(
            unsigned_report_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def test_decimal_payload_classification_covers_report_and_row_decimal_fields() -> None:
    module = api()
    classified_decimal_fields = module.COUNT_DECIMAL_FIELDS | module.FIXED_SIX_DECIMAL_FIELDS

    report_decimal_fields = {
        field.name
        for field in fields(module.StrategyPhase1ReadinessReport)
        if field.type is Decimal
    }
    row_decimal_fields = {
        field.name
        for field in fields(module.StrategyPhase1ReadinessRow)
        if field.type is Decimal
    }

    assert report_decimal_fields <= classified_decimal_fields
    assert row_decimal_fields <= classified_decimal_fields


def test_report_rejects_future_rows_even_when_digest_is_recomputed() -> None:
    module = api()
    result = report(signal())
    invalid_generated_at = result.rows[0].observed_at - timedelta(seconds=1)

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        replace(
            result,
            generated_at=invalid_generated_at,
            derived_validation_digest="",
        )

    object.__setattr__(result, "generated_at", invalid_generated_at)
    object.__setattr__(
        result,
        "derived_validation_digest",
        module._derived_digest(result),
    )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.strategy_phase1_readiness_report_payload(result)


def test_dataclasses_are_frozen_flags_are_hard_and_digests_reject_tamper() -> None:
    row = report(signal()).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(signal()), readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report(signal()), ready_count=d("0"))

    with pytest.raises(ValueError, match="status"):
        replace(
            row,
            status="block",
            reason_codes=("manual_blocker_review",),
            derived_validation_digest="",
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error"),
    (
        ("signal_count", True, "signal_count must be a Decimal"),
        ("signal_count", _DecimalSubclass("1.000000"), "signal_count must be a Decimal"),
        (
            "reason_codes",
            _TupleSubclass(("phase1_readiness_report_ready",)),
            "reason_codes must be a tuple",
        ),
    ),
)
def test_payload_rejects_non_exact_report_scalar_and_container_types(
    field_name: str,
    forged_value: object,
    error: str,
) -> None:
    module = api()
    forged = report(signal())
    object.__setattr__(forged, field_name, forged_value)
    object.__setattr__(
        forged,
        "derived_validation_digest",
        module._derived_digest(forged),
    )

    with pytest.raises(ValueError, match=error):
        module.strategy_phase1_readiness_report_payload(forged)


def test_payload_rejects_non_exact_report_rows_container() -> None:
    module = api()
    forged_rows = report(signal())
    object.__setattr__(forged_rows, "rows", _TupleSubclass(forged_rows.rows))
    with pytest.raises(ValueError, match="rows must be a tuple"):
        module.strategy_phase1_readiness_report_payload(forged_rows)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error"),
    (
        ("readiness_score", _DecimalSubclass("0.760000"), "readiness_score must be a Decimal"),
        (
            "reason_codes",
            _TupleSubclass(("phase1_readiness_ready",)),
            "reason_codes must be a tuple",
        ),
    ),
)
def test_payload_recursively_rejects_non_exact_row_scalar_and_container_types(
    field_name: str,
    forged_value: object,
    error: str,
) -> None:
    module = api()
    forged = report(signal())
    object.__setattr__(forged.rows[0], field_name, forged_value)

    with pytest.raises(ValueError, match=error):
        module.strategy_phase1_readiness_report_payload(forged)


@pytest.mark.parametrize(
    ("target", "field_name", "forged_value"),
    (
        ("report", "mean_edge_score", d("0.0800000")),
        ("row", "edge_score", d("0.0800001")),
    ),
)
def test_payload_rejects_recomputed_non_six_decimal_stored_values(
    target: str,
    field_name: str,
    forged_value: Decimal,
) -> None:
    module = api()
    forged = report(signal())

    if target == "row":
        object.__setattr__(forged.rows[0], field_name, forged_value)
        object.__setattr__(
            forged.rows[0],
            "derived_validation_digest",
            module._derived_digest(forged.rows[0]),
        )
    else:
        object.__setattr__(forged, field_name, forged_value)
    object.__setattr__(
        forged,
        "derived_validation_digest",
        module._derived_digest(forged),
    )

    with pytest.raises(ValueError, match=f"{field_name} must use six decimal places"):
        module.strategy_phase1_readiness_report_payload(forged)


def test_constructors_normalize_negative_zero_to_positive_six_decimal_quantum() -> None:
    negative_zero_signal = signal(
        edge_score=d("-0.000000"),
        cost_score=d("-0.000000"),
        liquidity_score=d("-0.000000"),
        resolution_score=d("-0.000000"),
        freshness_score=d("-0.000000"),
        manual_blocker_count=d("-0.000000"),
    )
    result = report(negative_zero_signal)
    empty = report()

    for field_name in (
        "edge_score",
        "cost_score",
        "liquidity_score",
        "resolution_score",
        "freshness_score",
        "manual_blocker_count",
    ):
        signal_value = getattr(negative_zero_signal, field_name)
        row_value = getattr(result.rows[0], field_name)
        assert signal_value.is_zero()
        assert row_value.is_zero()
        assert not signal_value.is_signed()
        assert not row_value.is_signed()
        assert signal_value.same_quantum(d("0.000001"))
        assert row_value.same_quantum(d("0.000001"))

    for field_name in (
        "signal_count",
        "ready_count",
        "watch_count",
        "block_count",
        "manual_blocker_count",
        "mean_edge_score",
        "mean_cost_score",
        "mean_liquidity_score",
        "mean_resolution_score",
        "mean_freshness_score",
    ):
        value = getattr(empty, field_name)
        assert value.is_zero()
        assert not value.is_signed()
        assert value.same_quantum(d("0.000001"))


@pytest.mark.parametrize(
    ("raw_count", "error"),
    (
        (d("-0.0000001"), "manual_blocker_count must be nonnegative"),
        (d("0.0000004"), "manual_blocker_count must be a whole Decimal"),
        (d("0.9999996"), "manual_blocker_count must be a whole Decimal"),
    ),
)
def test_count_validation_rejects_raw_negative_and_fractional_values_before_quantizing(
    raw_count: Decimal,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        signal(manual_blocker_count=raw_count)


@pytest.mark.parametrize(
    "field_name",
    (
        "signal_count",
        "ready_count",
        "watch_count",
        "block_count",
        "manual_blocker_count",
    ),
)
def test_payload_rejects_rehashed_negative_zero_report_counts(field_name: str) -> None:
    module = api()
    forged = report()
    object.__setattr__(forged, field_name, d("-0.000000"))
    object.__setattr__(
        forged,
        "derived_validation_digest",
        module._derived_digest(forged),
    )

    with pytest.raises(ValueError, match=f"{field_name} must not be negative zero"):
        module.strategy_phase1_readiness_report_payload(forged)


def test_payload_rejects_rehashed_negative_zero_row_manual_blocker_count() -> None:
    module = api()
    forged = report(signal())
    object.__setattr__(forged.rows[0], "manual_blocker_count", d("-0.000000"))
    object.__setattr__(
        forged.rows[0],
        "derived_validation_digest",
        module._derived_digest(forged.rows[0]),
    )
    object.__setattr__(forged, "manual_blocker_count", d("-0.000000"))
    object.__setattr__(
        forged,
        "derived_validation_digest",
        module._derived_digest(forged),
    )

    with pytest.raises(
        ValueError,
        match="manual_blocker_count must not be negative zero",
    ):
        module.strategy_phase1_readiness_report_payload(forged)


def test_payload_recursively_rejects_non_exact_row_dataclass() -> None:
    module = api()
    forged_dataclass = report(signal())
    exact_row = forged_dataclass.rows[0]
    impostor_type = make_dataclass(
        "ImpostorStrategyPhase1ReadinessRow",
        tuple((field.name, object) for field in fields(exact_row)),
        frozen=True,
    )
    impostor = impostor_type(
        **{field.name: getattr(exact_row, field.name) for field in fields(exact_row)},
    )
    object.__setattr__(forged_dataclass, "rows", (impostor,))
    with pytest.raises(ValueError, match="StrategyPhase1ReadinessRow"):
        module.strategy_phase1_readiness_report_payload(forged_dataclass)


@pytest.mark.parametrize("field_name", ("paper_only", "report_only", "readonly"))
def test_payload_rejects_recomputed_false_nested_row_flags(field_name: str) -> None:
    module = api()
    forged = report(signal())
    object.__setattr__(forged.rows[0], field_name, False)
    object.__setattr__(
        forged.rows[0],
        "derived_validation_digest",
        module._derived_digest(forged.rows[0]),
    )
    object.__setattr__(
        forged,
        "derived_validation_digest",
        module._derived_digest(forged),
    )

    with pytest.raises(ValueError, match=field_name):
        module.strategy_phase1_readiness_report_payload(forged)


def test_payload_rejects_recomputed_noncanonical_generated_at() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))

    forged_report_time = report(signal())
    object.__setattr__(
        forged_report_time,
        "generated_at",
        forged_report_time.generated_at.astimezone(eastern),
    )
    object.__setattr__(
        forged_report_time,
        "derived_validation_digest",
        module._derived_digest(forged_report_time),
    )
    with pytest.raises(ValueError, match="generated_at must be normalized to UTC"):
        module.strategy_phase1_readiness_report_payload(forged_report_time)


def test_payload_rejects_recomputed_noncanonical_row_observed_at() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    forged_row_time = report(signal())
    object.__setattr__(
        forged_row_time.rows[0],
        "observed_at",
        forged_row_time.rows[0].observed_at.astimezone(eastern),
    )
    object.__setattr__(
        forged_row_time.rows[0],
        "derived_validation_digest",
        module._derived_digest(forged_row_time.rows[0]),
    )
    object.__setattr__(
        forged_row_time,
        "derived_validation_digest",
        module._derived_digest(forged_row_time),
    )
    with pytest.raises(ValueError, match="observed_at must be normalized to UTC"):
        module.strategy_phase1_readiness_report_payload(forged_row_time)


def test_public_dataclasses_cannot_be_subclassed() -> None:
    module = api()

    for base in (
        module.StrategyPhase1ReadinessSignal,
        module.StrategyPhase1ReadinessRow,
        module.StrategyPhase1ReadinessReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Bad{base.__name__}", (base,), {})


def test_rejects_non_decimal_inputs_subclasses_and_bad_times() -> None:
    module = api()

    with pytest.raises(ValueError, match="edge_score"):
        signal(edge_score=0.08)
    with pytest.raises(ValueError, match="edge_score"):
        signal(edge_score=_DecimalSubclass("0.080000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 8, 11, 58))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    eastern = timezone(timedelta(hours=-4))
    result = report(
        signal(observed_at=datetime(2026, 7, 8, 7, 58, tzinfo=eastern)),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=eastern),
    )
    assert result.generated_at == GENERATED_AT
    assert result.rows[0].observed_at == OBSERVED_AT

    with pytest.raises(ValueError, match="signals"):
        module.build_strategy_phase1_readiness_report("not-signals", generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="StrategyPhase1ReadinessSignal"):
        module.build_strategy_phase1_readiness_report((object(),), generated_at=GENERATED_AT)


def test_module_exports_only_report_aggregator_surface_and_has_no_io_surface() -> None:
    module = api()
    assert set(module.__all__) == {
        "StrategyPhase1ReadinessReport",
        "StrategyPhase1ReadinessRow",
        "StrategyPhase1ReadinessSignal",
        "build_strategy_phase1_readiness_report",
        "strategy_phase1_readiness_report_payload",
    }

    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered_source = source.lower()
    assert not any(snippet in lowered_source for snippet in FORBIDDEN_SOURCE_SNIPPETS)
