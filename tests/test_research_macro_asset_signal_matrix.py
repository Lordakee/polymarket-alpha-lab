from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_macro_asset_signal_matrix import (
    DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION,
    MacroAssetSignalMatrixConfig,
    MacroAssetSignalMatrixReasonCodeCount,
    MacroAssetSignalMatrixReport,
    MacroAssetSignalMatrixRow,
    MacroAssetSignalObservation,
    build_research_macro_asset_signal_matrix,
    research_macro_asset_signal_matrix_digest,
    research_macro_asset_signal_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def test_signal_matrix_rolls_up_pass_watch_and_block_rows() -> None:
    report = build_research_macro_asset_signal_matrix(
        (
            _observation(
                asset_class="rates",
                macro_theme="rates",
                region="us",
                event_family="treasury_auction",
                observed_at=datetime(2026, 7, 8, 11, 55, tzinfo=UTC),
                rates_signal_score=Decimal("0.840000"),
                inflation_signal_score=Decimal("0.200000"),
                employment_signal_score=Decimal("0.150000"),
                central_bank_calendar_score=Decimal("0.780000"),
                cross_asset_confirmation_score=Decimal("0.920000"),
                uncertainty_score=Decimal("0.300000"),
                reason_codes=("rates_signal_elevated",),
            ),
            _observation(
                asset_class="fx",
                macro_theme="central_bank",
                region="eu",
                event_family="policy_calendar",
                observed_at=datetime(
                    2026,
                    7,
                    8,
                    13,
                    0,
                    tzinfo=timezone(timedelta(hours=2)),
                ),
                rates_signal_score=Decimal("0.300000"),
                inflation_signal_score=Decimal("0.260000"),
                employment_signal_score=Decimal("0.200000"),
                central_bank_calendar_score=Decimal("0.620000"),
                cross_asset_confirmation_score=Decimal("0.500000"),
                uncertainty_score=Decimal("0.420000"),
                reason_codes=("central_bank_calendar_watch",),
            ),
            _observation(
                asset_class="equity_index",
                macro_theme="employment",
                region="us",
                event_family="labor_release",
                observed_at=datetime(2026, 7, 8, 11, 50, tzinfo=UTC),
                rates_signal_score=Decimal("0.120000"),
                inflation_signal_score=Decimal("0.160000"),
                employment_signal_score=Decimal("0.180000"),
                central_bank_calendar_score=Decimal("0.100000"),
                cross_asset_confirmation_score=Decimal("0.100000"),
                uncertainty_score=Decimal("0.100000"),
                reason_codes=("macro_signal_clear",),
            ),
        ),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MacroAssetSignalMatrixReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION
    assert report.report_status == "block"
    assert report.human_research_focus == "triage_macro_asset_signal_matrix_block"
    assert report.row_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.rates_watch_count == Decimal("1.000000")
    assert report.inflation_watch_count == Decimal("0.000000")
    assert report.employment_watch_count == Decimal("0.000000")
    assert report.central_bank_watch_count == Decimal("2.000000")
    assert report.stale_observation_count == Decimal("0.000000")
    assert report.max_priority_score == Decimal("0.581500")
    assert report.average_priority_score == Decimal("0.362500")
    assert report.reason_codes == ("macro_asset_signal_matrix_block",)
    assert report.reason_code_counts == (
        MacroAssetSignalMatrixReasonCodeCount(
            reason_code="central_bank_calendar_watch",
            count=Decimal("2.000000"),
        ),
        MacroAssetSignalMatrixReasonCodeCount(
            reason_code="macro_signal_block",
            count=Decimal("1.000000"),
        ),
        MacroAssetSignalMatrixReasonCodeCount(
            reason_code="macro_signal_clear",
            count=Decimal("1.000000"),
        ),
        MacroAssetSignalMatrixReasonCodeCount(
            reason_code="macro_signal_watch",
            count=Decimal("1.000000"),
        ),
        MacroAssetSignalMatrixReasonCodeCount(
            reason_code="rates_signal_elevated",
            count=Decimal("1.000000"),
        ),
    )
    assert report.rows == (
        MacroAssetSignalMatrixRow(
            asset_class="rates",
            macro_theme="rates",
            region="us",
            event_family="treasury_auction",
            observed_at=datetime(2026, 7, 8, 11, 55, tzinfo=UTC),
            observation_age_seconds=Decimal("300.000000"),
            rates_signal_score=Decimal("0.840000"),
            inflation_signal_score=Decimal("0.200000"),
            employment_signal_score=Decimal("0.150000"),
            central_bank_calendar_score=Decimal("0.780000"),
            cross_asset_confirmation_score=Decimal("0.920000"),
            uncertainty_score=Decimal("0.300000"),
            priority_score=Decimal("0.581500"),
            row_status="block",
            reason_codes=(
                "central_bank_calendar_watch",
                "macro_signal_block",
                "rates_signal_elevated",
            ),
        ),
        MacroAssetSignalMatrixRow(
            asset_class="fx",
            macro_theme="central_bank",
            region="eu",
            event_family="policy_calendar",
            observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            observation_age_seconds=Decimal("3600.000000"),
            rates_signal_score=Decimal("0.300000"),
            inflation_signal_score=Decimal("0.260000"),
            employment_signal_score=Decimal("0.200000"),
            central_bank_calendar_score=Decimal("0.620000"),
            cross_asset_confirmation_score=Decimal("0.500000"),
            uncertainty_score=Decimal("0.420000"),
            priority_score=Decimal("0.377000"),
            row_status="watch",
            reason_codes=("central_bank_calendar_watch", "macro_signal_watch"),
        ),
        MacroAssetSignalMatrixRow(
            asset_class="equity_index",
            macro_theme="employment",
            region="us",
            event_family="labor_release",
            observed_at=datetime(2026, 7, 8, 11, 50, tzinfo=UTC),
            observation_age_seconds=Decimal("600.000000"),
            rates_signal_score=Decimal("0.120000"),
            inflation_signal_score=Decimal("0.160000"),
            employment_signal_score=Decimal("0.180000"),
            central_bank_calendar_score=Decimal("0.100000"),
            cross_asset_confirmation_score=Decimal("0.100000"),
            uncertainty_score=Decimal("0.100000"),
            priority_score=Decimal("0.129000"),
            row_status="pass",
            reason_codes=("macro_signal_clear",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_inputs_block_with_decimal_zeroes() -> None:
    report = build_research_macro_asset_signal_matrix(
        (),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "block"
    assert report.human_research_focus == "triage_macro_asset_signal_matrix_block"
    assert report.row_count == Decimal("0.000000")
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.max_priority_score == Decimal("0.000000")
    assert report.average_priority_score == Decimal("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("macro_asset_signal_matrix_empty",)
    assert report.reason_code_counts == (
        MacroAssetSignalMatrixReasonCodeCount(
            reason_code="macro_asset_signal_matrix_empty",
            count=Decimal("1.000000"),
        ),
    )


def test_all_clear_inputs_pass() -> None:
    report = build_research_macro_asset_signal_matrix(
        (_observation(),),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "pass"
    assert report.human_research_focus == "log_macro_asset_signal_matrix_pass"
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.reason_codes == ("macro_asset_signal_matrix_pass",)


def test_decimal_type_datetime_and_status_rejections() -> None:
    with pytest.raises(ValueError, match="config_version"):
        MacroAssetSignalMatrixConfig(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="supported config version"):
        MacroAssetSignalMatrixConfig(config_version="unsupported-version")
    with pytest.raises(ValueError, match="watch_priority_score"):
        MacroAssetSignalMatrixConfig(watch_priority_score=Decimal("0.700000"))
    with pytest.raises(ValueError, match="rates_signal_score"):
        _observation(rates_signal_score=0.1)
    with pytest.raises(ValueError, match="rates_signal_score"):
        _observation(rates_signal_score=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="rates_signal_score"):
        _observation(rates_signal_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_macro_asset_signal_matrix(
            (),
            config=MacroAssetSignalMatrixConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="row_status"):
        MacroAssetSignalMatrixRow(
            **{
                **_row_kwargs(),
                "row_status": "blocked",
            },
        )
    with pytest.raises(ValueError, match="inputs"):
        build_research_macro_asset_signal_matrix(
            (object(),),
            config=MacroAssetSignalMatrixConfig(),
            generated_at=GENERATED_AT,
        )


def test_public_surface_rejects_unsafe_identifiers_values_and_tampering() -> None:
    unsafe_values = (
        {"event_family": "raw_candidate_123"},
        {"event_family": "market_slug_cpi"},
        {"event_family": "market_question"},
        {"event_family": "source_ref_bls"},
        {"event_family": "https://example.test/path"},
        {"reason_codes": ("buy_now",)},
        {"reason_codes": ("wallet_check",)},
        {"reason_codes": ("orders_table_token",)},
    )
    for overrides in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            _observation(**overrides)

    report = build_research_macro_asset_signal_matrix(
        (_observation(),),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "event_family", "source_text_blob")
    with pytest.raises(ValueError, match="unsafe public"):
        research_macro_asset_signal_matrix_payload(report)


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    config = MacroAssetSignalMatrixConfig()
    observation = _observation()
    report = build_research_macro_asset_signal_matrix(
        (observation,),
        config=config,
        generated_at=GENERATED_AT,
    )
    values = (config, observation, report, *report.rows, *report.reason_code_counts)

    for value in values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False

    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation, report_only=False)

    object.__setattr__(report.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        research_macro_asset_signal_matrix_payload(report)


def test_payload_is_deterministic_public_and_digest_matches_report() -> None:
    observations = (
        _observation(
            asset_class="fx",
            macro_theme="inflation",
            region="uk",
            event_family="inflation_release",
            observed_at=datetime(2026, 7, 8, 10, 30, tzinfo=UTC),
            inflation_signal_score=Decimal("0.610000"),
            cross_asset_confirmation_score=Decimal("0.510000"),
            uncertainty_score=Decimal("0.430000"),
            reason_codes=("inflation_signal_elevated",),
        ),
        _observation(
            asset_class="rates",
            macro_theme="rates",
            region="us",
            event_family="auction_cycle",
            observed_at=datetime(2026, 7, 8, 11, 55, tzinfo=UTC),
            rates_signal_score=Decimal("0.810000"),
            central_bank_calendar_score=Decimal("0.720000"),
            cross_asset_confirmation_score=Decimal("0.860000"),
            uncertainty_score=Decimal("0.300000"),
            reason_codes=("rates_signal_elevated",),
        ),
    )
    report_a = build_research_macro_asset_signal_matrix(
        observations,
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )
    report_b = build_research_macro_asset_signal_matrix(
        tuple(reversed(observations)),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )

    payload_a = research_macro_asset_signal_matrix_payload(report_a)
    payload_b = research_macro_asset_signal_matrix_payload(report_b)
    digest = research_macro_asset_signal_matrix_digest(report_a)

    assert payload_a == payload_b
    assert json.dumps(payload_a, sort_keys=True) == json.dumps(payload_b, sort_keys=True)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["row_count"] == "2.000000"
    assert payload_a["rows"][0]["priority_score"] == "0.525500"
    assert payload_a["rows"][0]["observed_at"] == "2026-07-08T11:55:00+00:00"
    assert payload_a["reason_code_counts"][0]["count"] == "1.000000"
    assert digest == {
        "generated_at": payload_a["generated_at"],
        "config_version": payload_a["config_version"],
        "report_status": payload_a["report_status"],
        "human_research_focus": payload_a["human_research_focus"],
        "row_count": payload_a["row_count"],
        "pass_count": payload_a["pass_count"],
        "watch_count": payload_a["watch_count"],
        "block_count": payload_a["block_count"],
        "reason_codes": payload_a["reason_codes"],
        "top_rows": payload_a["rows"],
    }
    _assert_no_float_or_decimal_payload(payload_a)
    _assert_no_unsafe_public_payload(payload_a)


def test_report_constructor_rejects_inconsistent_public_digest_fields() -> None:
    report = build_research_macro_asset_signal_matrix(
        (
            _observation(),
            _observation(
                asset_class="fx",
                macro_theme="inflation",
                region="uk",
                event_family="inflation_release",
                observed_at=GENERATED_AT - timedelta(minutes=5),
                inflation_signal_score=Decimal("0.610000"),
                reason_codes=("inflation_signal_elevated",),
            ),
        ),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )
    kwargs = _dataclass_kwargs(report)
    kwargs["pass_count"] = Decimal("0.000000")

    with pytest.raises(ValueError, match="pass_count"):
        MacroAssetSignalMatrixReport(**kwargs)

    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows + report.rows)))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))


def test_public_dataclasses_reject_subclassing() -> None:
    report = build_research_macro_asset_signal_matrix(
        (_observation(),),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )
    cases = (
        (MacroAssetSignalMatrixConfig, {}),
        (MacroAssetSignalObservation, _observation_kwargs()),
        (MacroAssetSignalMatrixRow, _row_kwargs()),
        (
            MacroAssetSignalMatrixReasonCodeCount,
            {"reason_code": "macro_signal_clear", "count": Decimal("1.000000")},
        ),
        (MacroAssetSignalMatrixReport, _dataclass_kwargs(report)),
    )

    for public_type, kwargs in cases:
        value = public_type(**kwargs)
        assert type(value) is public_type
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def _observation(**overrides: object) -> MacroAssetSignalObservation:
    return MacroAssetSignalObservation(**_observation_kwargs(**overrides))


def _observation_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "asset_class": "rates",
        "macro_theme": "rates",
        "region": "us",
        "event_family": "treasury_auction",
        "observed_at": GENERATED_AT,
        "rates_signal_score": Decimal("0.100000"),
        "inflation_signal_score": Decimal("0.100000"),
        "employment_signal_score": Decimal("0.100000"),
        "central_bank_calendar_score": Decimal("0.100000"),
        "cross_asset_confirmation_score": Decimal("0.100000"),
        "uncertainty_score": Decimal("0.100000"),
        "reason_codes": ("macro_signal_clear",),
    }
    values.update(overrides)
    return values


def _row_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "asset_class": "rates",
        "macro_theme": "rates",
        "region": "us",
        "event_family": "treasury_auction",
        "observed_at": GENERATED_AT,
        "observation_age_seconds": Decimal("0.000000"),
        "rates_signal_score": Decimal("0.100000"),
        "inflation_signal_score": Decimal("0.100000"),
        "employment_signal_score": Decimal("0.100000"),
        "central_bank_calendar_score": Decimal("0.100000"),
        "cross_asset_confirmation_score": Decimal("0.100000"),
        "uncertainty_score": Decimal("0.100000"),
        "priority_score": Decimal("0.100000"),
        "row_status": "pass",
        "reason_codes": ("macro_signal_clear",),
    }
    values.update(overrides)
    return values


def _dataclass_kwargs(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_float_or_decimal_payload(child)


def _assert_no_unsafe_public_payload(value: object) -> None:
    unsafe_terms = (
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in unsafe_terms)
        assert "://" not in value
    elif isinstance(value, dict):
        for key, child in value.items():
            _assert_no_unsafe_public_payload(key)
            _assert_no_unsafe_public_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_unsafe_public_payload(child)


def test_public_numeric_fields_are_decimal_before_payload_conversion() -> None:
    report = build_research_macro_asset_signal_matrix(
        (_observation(),),
        config=MacroAssetSignalMatrixConfig(),
        generated_at=GENERATED_AT,
    )
    values = (
        MacroAssetSignalMatrixConfig(),
        _observation(),
        report,
        *report.rows,
        *report.reason_code_counts,
    )
    numeric_suffixes = (
        "_count",
        "_score",
        "_seconds",
    )
    for value in values:
        for field in fields(value):
            public_value = getattr(value, field.name)
            if field.name.endswith(numeric_suffixes):
                assert type(public_value) is Decimal
