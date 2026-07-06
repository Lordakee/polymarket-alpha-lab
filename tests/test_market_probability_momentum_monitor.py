from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from importlib import import_module
import inspect
import json

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 2, 11, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # noqa: ANN001
        return None


def _api():
    return import_module("polymarket_alpha_lab.market_probability_momentum_monitor")


def _config(**overrides):
    values = {
        "config_version": "market-probability-momentum-monitor-v0",
        "reversal_threshold": Decimal("0.030000"),
        "volatility_watch_threshold": Decimal("0.040000"),
    }
    values.update(overrides)
    return _api().MarketProbabilityMomentumMonitorConfig(**values)


def _observation(index: int, probability: str):
    return _api().MarketProbabilityObservation(
        observation_id=f"obs-{index}",
        observed_at=BASE_OBSERVED_AT + timedelta(minutes=index),
        probability=Decimal(probability),
    )


def _monitor(*probabilities: str, **config_overrides):
    return _api().build_market_probability_momentum_monitor_report(
        tuple(_observation(index + 1, probability) for index, probability in enumerate(probabilities)),
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in JSON payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_floats(item)


def test_probability_momentum_summarizes_direction_reversals_and_volatility() -> None:
    api = _api()

    report = _monitor("0.400000", "0.460000", "0.430000", "0.500000", "0.470000")

    assert type(report) is api.MarketProbabilityMomentumMonitorReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-probability-momentum-monitor-v0"
    assert report.momentum_status == "volatile_reversal"
    assert report.observation_count == Decimal("5")
    assert report.first_observed_at == BASE_OBSERVED_AT + timedelta(minutes=1)
    assert report.latest_observed_at == BASE_OBSERVED_AT + timedelta(minutes=5)
    assert report.first_probability == Decimal("0.400000")
    assert report.latest_probability == Decimal("0.470000")
    assert report.net_probability_change == Decimal("0.070000")
    assert report.absolute_probability_change == Decimal("0.070000")
    assert report.mean_step_change == Decimal("0.017500")
    assert report.mean_absolute_step_change == Decimal("0.047500")
    assert report.max_up_step_change == Decimal("0.070000")
    assert report.max_down_step_change == Decimal("-0.030000")
    assert report.reversal_count == Decimal("3")
    assert report.volatility_score == Decimal("0.047500")
    assert report.direction == "up"
    assert report.reason_codes == (
        "probability_reversal_observed",
        "probability_volatility_watch",
        "probability_momentum_up",
    )
    assert report.movement_rows == (
        api.MarketProbabilityMovementRow(
            movement_index=Decimal("1"),
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=2),
            probability=Decimal("0.460000"),
            previous_probability=Decimal("0.400000"),
            step_change=Decimal("0.060000"),
            absolute_step_change=Decimal("0.060000"),
            direction="up",
            reversal_from_previous=False,
        ),
        api.MarketProbabilityMovementRow(
            movement_index=Decimal("2"),
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=3),
            probability=Decimal("0.430000"),
            previous_probability=Decimal("0.460000"),
            step_change=Decimal("-0.030000"),
            absolute_step_change=Decimal("0.030000"),
            direction="down",
            reversal_from_previous=True,
        ),
        api.MarketProbabilityMovementRow(
            movement_index=Decimal("3"),
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=4),
            probability=Decimal("0.500000"),
            previous_probability=Decimal("0.430000"),
            step_change=Decimal("0.070000"),
            absolute_step_change=Decimal("0.070000"),
            direction="up",
            reversal_from_previous=True,
        ),
        api.MarketProbabilityMovementRow(
            movement_index=Decimal("4"),
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=5),
            probability=Decimal("0.470000"),
            previous_probability=Decimal("0.500000"),
            step_change=Decimal("-0.030000"),
            absolute_step_change=Decimal("0.030000"),
            direction="down",
            reversal_from_previous=True,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(not hasattr(row, "market_slug") for row in report.movement_rows)
    assert all(not hasattr(row, "question") for row in report.movement_rows)


def test_probability_momentum_reports_empty_single_and_flat_histories() -> None:
    empty = _monitor()
    single = _monitor("0.510000")
    flat = _monitor("0.500000", "0.500000", "0.500000")

    assert empty.momentum_status == "insufficient_observations"
    assert empty.observation_count == Decimal("0")
    assert empty.movement_rows == ()
    assert empty.reason_codes == ("empty_probability_history",)
    assert single.momentum_status == "insufficient_observations"
    assert single.first_probability == Decimal("0.510000")
    assert single.latest_probability == Decimal("0.510000")
    assert single.reason_codes == ("insufficient_probability_history",)
    assert flat.momentum_status == "stable"
    assert flat.direction == "flat"
    assert flat.net_probability_change == Decimal("0.000000")
    assert flat.mean_absolute_step_change == Decimal("0.000000")
    assert flat.reversal_count == Decimal("0")
    assert flat.reason_codes == ("probability_momentum_stable",)


def test_probability_momentum_orders_observations_before_reducing() -> None:
    api = _api()
    late = _observation(3, "0.550000")
    early = _observation(1, "0.450000")
    middle = _observation(2, "0.500000")

    report = api.build_market_probability_momentum_monitor_report(
        (late, early, middle),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.first_observed_at == early.observed_at
    assert report.latest_observed_at == late.observed_at
    assert report.net_probability_change == Decimal("0.100000")
    assert tuple(row.probability for row in report.movement_rows) == (
        Decimal("0.500000"),
        Decimal("0.550000"),
    )


def test_probability_momentum_dataclasses_are_strict_frozen_decimal_and_consistent() -> None:
    api = _api()
    report = _monitor("0.420000", "0.460000", "0.440000")

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadConfig(api.MarketProbabilityMomentumMonitorConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadObservation(api.MarketProbabilityObservation):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadMovementRow(api.MarketProbabilityMovementRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(api.MarketProbabilityMomentumMonitorReport):
            pass

    with pytest.raises(FrozenInstanceError):
        report.momentum_status = "stable"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        api.MarketProbabilityObservation(
            observation_id="obs-float",
            observed_at=BASE_OBSERVED_AT,
            probability=0.42,
        )
    with pytest.raises(ValueError, match="between zero and one"):
        replace(_observation(1, "0.500000"), probability=Decimal("1.000001"))
    with pytest.raises(ValueError, match="deterministic"):
        replace(report, movement_rows=tuple(reversed(report.movement_rows)))
    multi_reason_report = _monitor(
        "0.400000",
        "0.460000",
        "0.430000",
        "0.500000",
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason_report,
            reason_codes=tuple(reversed(multi_reason_report.reason_codes)),
        )
    with pytest.raises(ValueError, match="reversal_count"):
        replace(report, reversal_count=Decimal("1"))
    with pytest.raises(ValueError, match="observation_count must be a Decimal"):
        replace(report, observation_count=3)
    with pytest.raises(ValueError, match="movement_index must be a Decimal"):
        replace(report.movement_rows[0], movement_index=1)

    for value in (report, *report.movement_rows):
        for field in fields(value):
            if field.name.endswith("_count") or field.name.endswith("_index"):
                assert type(getattr(value, field.name)) is Decimal


def test_probability_momentum_payload_uses_decimal_strings_and_no_float_values() -> None:
    api = _api()
    report = _monitor("0.400000", "0.460000", "0.430000")

    payload = api.market_probability_momentum_monitor_payload(report)

    assert payload["observation_count"] == "3"
    assert payload["reversal_count"] == "1"
    assert payload["net_probability_change"] == "0.030000"
    assert payload["movement_rows"][0]["movement_index"] == "1"
    assert payload["movement_rows"][0]["step_change"] == "0.060000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_floats(payload)
    json.dumps(payload, sort_keys=True)

    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "wallet",
        "broker",
        "order",
        "auth",
        "signing",
        "advice",
    ):
        assert forbidden not in payload_text

    with pytest.raises(
        ValueError,
        match="report must be a MarketProbabilityMomentumMonitorReport",
    ):
        api.market_probability_momentum_monitor_payload(object())


def test_probability_momentum_derived_validation_digest_is_payload_bound() -> None:
    api = _api()
    report = _monitor("0.400000", "0.460000", "0.430000")

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    payload = api.market_probability_momentum_monitor_payload(report)
    assert api.market_probability_momentum_monitor_payload(dict(payload)) == payload

    tampered_report = _monitor("0.410000", "0.450000", "0.420000")
    object.__setattr__(tampered_report, "net_probability_change", Decimal("0.990000"))
    with pytest.raises(ValueError, match="derived_validation_digest|net_probability_change"):
        api.market_probability_momentum_monitor_payload(tampered_report)

    tampered_payload = dict(payload)
    tampered_payload["config_version"] = "market-probability-momentum-monitor-v1"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.market_probability_momentum_monitor_payload(tampered_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.market_probability_momentum_monitor_payload(missing_digest)


def test_probability_momentum_public_payload_rejects_unsafe_surfaces() -> None:
    api = _api()
    payload = api.market_probability_momentum_monitor_payload(
        _monitor("0.400000", "0.460000", "0.430000"),
    )

    unsafe_keys = (
        "li" + "ve_mode",
        "a" + "uth_token",
        "wal" + "let_address",
        "or" + "der_id",
        "net" + "work_client",
        "data" + "base_url",
        "per" + "sist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            api.market_probability_momentum_monitor_payload(unsafe_payload)

    unsafe_values = (
        "li" + "ve mode enabled",
        "a" + "uth token configured",
        "wal" + "let transfer configured",
        "submit " + "or" + "der configured",
        "net" + "work request configured",
        "data" + "base writer configured",
        "per" + "sist report configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["config_version"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            api.market_probability_momentum_monitor_payload(unsafe_payload)

    with pytest.raises(ValueError, match="unsafe"):
        api.MarketProbabilityObservation(
            observation_id="wal" + "let-private-source",
            observed_at=BASE_OBSERVED_AT,
            probability=Decimal("0.420000"),
        )
    with pytest.raises(ValueError, match="unsafe"):
        _config(config_version="net" + "work-enabled")


def test_probability_momentum_rejects_wrong_inputs_and_unsafe_surfaces() -> None:
    api = _api()

    with pytest.raises(ValueError, match="MarketProbabilityMomentumMonitorConfig"):
        api.build_market_probability_momentum_monitor_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        api.build_market_probability_momentum_monitor_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="MarketProbabilityObservation"):
        api.build_market_probability_momentum_monitor_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.build_market_probability_momentum_monitor_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.build_market_probability_momentum_monitor_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    class BadDateTime(datetime):
        pass

    with pytest.raises(ValueError, match="must be a datetime"):
        api.build_market_probability_momentum_monitor_report(
            (),
            config=_config(),
            generated_at=BadDateTime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate observation_id"):
        api.build_market_probability_momentum_monitor_report(
            (_observation(1, "0.400000"), _observation(1, "0.410000")),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    source = inspect.getsource(api)
    public_names = tuple(api.__all__)
    forbidden_fragments = (
        "market_slug",
        "question",
        "payload_json",
        "live",
        "auth",
        "wallet",
        "order",
        "account",
        "investment",
        "advice",
        "fast",
    )
    assert all(
        fragment not in name
        for name in public_names
        for fragment in forbidden_fragments
    )
    for fragment in (
        "polymarket_alpha_lab.cli",
        "psycopg",
        "requests",
        "sqlite3",
        "wallet",
        "place_order",
        "submit_order",
        "investment",
        "fast",
    ):
        assert fragment not in source
    assert "float" not in source


def test_probability_momentum_hard_flags_are_required_on_all_public_dataclasses() -> None:
    report = _monitor("0.420000", "0.460000", "0.440000")

    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            replace(_config(), **{flag_name: False})
        with pytest.raises(ValueError, match=flag_name):
            replace(_observation(1, "0.500000"), **{flag_name: False})
        with pytest.raises(ValueError, match=flag_name):
            replace(report.movement_rows[0], **{flag_name: False})
        with pytest.raises(ValueError, match=flag_name):
            replace(report, **{flag_name: False})
