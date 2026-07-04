from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_rates_futures_positioning_digest import (
    DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION,
    RatesFuturesPositioningBucketRollup,
    RatesFuturesPositioningDigestConfig,
    RatesFuturesPositioningDigestInput,
    RatesFuturesPositioningDigestReport,
    RatesFuturesPositioningReasonCodeCount,
    RatesFuturesPositioningRow,
    build_market_research_rates_futures_positioning_digest,
    market_research_rates_futures_positioning_digest_json_record,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _FloatSubclass(float):
    pass


def _config(**overrides: object) -> RatesFuturesPositioningDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION
        ),
        "watch_position_change_contracts": Decimal("1000.000000"),
        "blocked_position_change_contracts": Decimal("4000.000000"),
        "watch_position_pressure_share": Decimal("0.100000"),
        "blocked_position_pressure_share": Decimal("0.250000"),
        "source_quorum_watch_threshold": Decimal("0.600000"),
        "positioning_score_watch_threshold": Decimal("0.500000"),
        "positioning_score_blocked_threshold": Decimal("0.750000"),
    }
    values.update(overrides)
    return RatesFuturesPositioningDigestConfig(**values)


def _input(
    condition_id: str,
    rates_bucket: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    prior_net_position_contracts: Decimal = Decimal("1200.000000"),
    net_position_contracts: Decimal = Decimal("1300.000000"),
    open_interest_contracts: Decimal = Decimal("10000.000000"),
    source_quorum_share: Decimal = Decimal("0.800000"),
    source_config_version: str = "rates-futures-positioning-source-v0",
    source_ref: str | None = "public-rates-positioning-ref",
) -> RatesFuturesPositioningDigestInput:
    return RatesFuturesPositioningDigestInput(
        condition_id=condition_id,
        rates_bucket=rates_bucket,
        observed_at=observed_at,
        prior_net_position_contracts=prior_net_position_contracts,
        net_position_contracts=net_position_contracts,
        open_interest_contracts=open_interest_contracts,
        source_quorum_share=source_quorum_share,
        source_config_version=source_config_version,
        source_ref=source_ref,
    )


def test_digest_summarizes_rates_futures_positioning_by_bucket() -> None:
    report = build_market_research_rates_futures_positioning_digest(
        (
            _input(
                "condition_beta",
                "treasury",
                observed_at=GENERATED_AT - timedelta(seconds=600),
                prior_net_position_contracts=Decimal("-1000.000000"),
                net_position_contracts=Decimal("-5000.000000"),
                open_interest_contracts=Decimal("10000.000000"),
                source_quorum_share=Decimal("0.350000"),
                source_ref="api key",
            ),
            _input(
                "condition_alpha",
                "fed",
                observed_at=GENERATED_AT - timedelta(seconds=300),
                prior_net_position_contracts=Decimal("1000.000000"),
                net_position_contracts=Decimal("2500.000000"),
                open_interest_contracts=Decimal("10000.000000"),
                source_quorum_share=Decimal("0.550000"),
                source_config_version="rates-futures-positioning-source-v1",
            ),
            _input("condition_gamma", "fed"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, RatesFuturesPositioningDigestReport)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "review_rates_futures_positioning_digest"
    assert report.condition_count == Decimal("3")
    assert report.bucket_count == Decimal("2")
    assert report.positioning_shift_condition_count == Decimal("2")
    assert report.blocked_condition_count == Decimal("1")
    assert report.watch_condition_count == Decimal("1")
    assert report.low_quorum_condition_count == Decimal("2")
    assert report.position_change_condition_count == Decimal("2")
    assert report.pressure_condition_count == Decimal("2")
    assert report.max_position_change_contracts == Decimal("4000.000000")
    assert report.max_position_pressure_share == Decimal("0.400000")
    assert report.max_positioning_score == Decimal("1.000000")
    assert report.reason_codes == (
        "rates_futures_positioning_blocked_score",
        "rates_futures_positioning_low_quorum",
        "rates_futures_positioning_position_change",
        "rates_futures_positioning_pressure",
        "rates_futures_positioning_watch_score",
    )
    assert report.reason_code_counts == (
        RatesFuturesPositioningReasonCodeCount(
            reason_code="rates_futures_positioning_blocked_score",
            condition_count=Decimal("1"),
        ),
        RatesFuturesPositioningReasonCodeCount(
            reason_code="rates_futures_positioning_low_quorum",
            condition_count=Decimal("2"),
        ),
        RatesFuturesPositioningReasonCodeCount(
            reason_code="rates_futures_positioning_position_change",
            condition_count=Decimal("2"),
        ),
        RatesFuturesPositioningReasonCodeCount(
            reason_code="rates_futures_positioning_pressure",
            condition_count=Decimal("2"),
        ),
        RatesFuturesPositioningReasonCodeCount(
            reason_code="rates_futures_positioning_watch_score",
            condition_count=Decimal("1"),
        ),
    )
    assert report.bucket_rollups == (
        RatesFuturesPositioningBucketRollup(
            rates_bucket="fed",
            condition_count=Decimal("2"),
            positioning_shift_condition_count=Decimal("1"),
            blocked_condition_count=Decimal("0"),
            watch_condition_count=Decimal("1"),
            low_quorum_condition_count=Decimal("1"),
            position_change_condition_count=Decimal("1"),
            pressure_condition_count=Decimal("1"),
            max_position_change_contracts=Decimal("1500.000000"),
            max_position_pressure_share=Decimal("0.150000"),
            max_positioning_score=Decimal("0.600000"),
            bucket_status="watch",
            reason_codes=(
                "rates_futures_positioning_low_quorum",
                "rates_futures_positioning_position_change",
                "rates_futures_positioning_pressure",
                "rates_futures_positioning_watch_score",
            ),
        ),
        RatesFuturesPositioningBucketRollup(
            rates_bucket="treasury",
            condition_count=Decimal("1"),
            positioning_shift_condition_count=Decimal("1"),
            blocked_condition_count=Decimal("1"),
            watch_condition_count=Decimal("0"),
            low_quorum_condition_count=Decimal("1"),
            position_change_condition_count=Decimal("1"),
            pressure_condition_count=Decimal("1"),
            max_position_change_contracts=Decimal("4000.000000"),
            max_position_pressure_share=Decimal("0.400000"),
            max_positioning_score=Decimal("1.000000"),
            bucket_status="blocked",
            reason_codes=(
                "rates_futures_positioning_blocked_score",
                "rates_futures_positioning_low_quorum",
                "rates_futures_positioning_position_change",
                "rates_futures_positioning_pressure",
            ),
        ),
    )
    assert report.rows == (
        RatesFuturesPositioningRow(
            condition_id="condition_alpha",
            rates_bucket="fed",
            observed_at=GENERATED_AT - timedelta(seconds=300),
            prior_net_position_contracts=Decimal("1000.000000"),
            net_position_contracts=Decimal("2500.000000"),
            position_change_contracts=Decimal("1500.000000"),
            open_interest_contracts=Decimal("10000.000000"),
            position_pressure_share=Decimal("0.150000"),
            source_quorum_share=Decimal("0.550000"),
            positioning_score=Decimal("0.600000"),
            positioning_status="watch",
            source_config_version="rates-futures-positioning-source-v1",
            redacted_source_ref="public-rates-positioning-ref",
            reason_codes=(
                "rates_futures_positioning_low_quorum",
                "rates_futures_positioning_position_change",
                "rates_futures_positioning_pressure",
                "rates_futures_positioning_watch_score",
            ),
        ),
        RatesFuturesPositioningRow(
            condition_id="condition_gamma",
            rates_bucket="fed",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            prior_net_position_contracts=Decimal("1200.000000"),
            net_position_contracts=Decimal("1300.000000"),
            position_change_contracts=Decimal("100.000000"),
            open_interest_contracts=Decimal("10000.000000"),
            position_pressure_share=Decimal("0.010000"),
            source_quorum_share=Decimal("0.800000"),
            positioning_score=Decimal("0.040000"),
            positioning_status="pass",
            source_config_version="rates-futures-positioning-source-v0",
            redacted_source_ref="public-rates-positioning-ref",
            reason_codes=("rates_futures_positioning_stable",),
        ),
        RatesFuturesPositioningRow(
            condition_id="condition_beta",
            rates_bucket="treasury",
            observed_at=GENERATED_AT - timedelta(seconds=600),
            prior_net_position_contracts=Decimal("-1000.000000"),
            net_position_contracts=Decimal("-5000.000000"),
            position_change_contracts=Decimal("4000.000000"),
            open_interest_contracts=Decimal("10000.000000"),
            position_pressure_share=Decimal("0.400000"),
            source_quorum_share=Decimal("0.350000"),
            positioning_score=Decimal("1.000000"),
            positioning_status="blocked",
            source_config_version="rates-futures-positioning-source-v0",
            redacted_source_ref="[REDACTED]",
            reason_codes=(
                "rates_futures_positioning_blocked_score",
                "rates_futures_positioning_low_quorum",
                "rates_futures_positioning_position_change",
                "rates_futures_positioning_pressure",
            ),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_and_stable_inputs_pass_with_deterministic_reasons() -> None:
    empty_report = build_market_research_rates_futures_positioning_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert empty_report.digest_status == "pass"
    assert empty_report.condition_count == Decimal("0")
    assert empty_report.bucket_count == Decimal("0")
    assert empty_report.max_position_change_contracts is None
    assert empty_report.max_position_pressure_share is None
    assert empty_report.max_positioning_score is None
    assert empty_report.reason_codes == ("rates_futures_positioning_digest_empty",)

    stable_report = build_market_research_rates_futures_positioning_digest(
        (_input("condition_alpha", "fed"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.positioning_shift_condition_count == Decimal("0")
    assert stable_report.reason_codes == ("rates_futures_positioning_digest_passed",)
    assert stable_report.rows[0].positioning_status == "pass"
    assert stable_report.rows[0].reason_codes == ("rates_futures_positioning_stable",)


def test_digest_honors_non_default_positioning_score_thresholds() -> None:
    report = build_market_research_rates_futures_positioning_digest(
        (
            _input(
                "condition_alpha",
                "fed",
                prior_net_position_contracts=Decimal("1000.000000"),
                net_position_contracts=Decimal("2500.000000"),
                open_interest_contracts=Decimal("10000.000000"),
                source_quorum_share=Decimal("0.800000"),
            ),
        ),
        config=_config(
            positioning_score_watch_threshold=Decimal("0.900000"),
            positioning_score_blocked_threshold=Decimal("0.950000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "watch"
    assert report.watch_condition_count == Decimal("1")
    assert report.rows[0].positioning_score == Decimal("0.600000")
    assert report.rows[0].positioning_status == "watch"
    assert report.rows[0].reason_codes == (
        "rates_futures_positioning_position_change",
        "rates_futures_positioning_pressure",
    )


def test_json_record_uses_decimal_strings_utc_datetimes_and_redaction() -> None:
    report = build_market_research_rates_futures_positioning_digest(
        (
            _input(
                "condition_beta",
                "treasury",
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                prior_net_position_contracts=Decimal("-1000.000000"),
                net_position_contracts=Decimal("-5000.000000"),
                open_interest_contracts=Decimal("10000.000000"),
                source_quorum_share=Decimal("0.350000"),
                source_ref="source credential",
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    record = market_research_rates_futures_positioning_digest_json_record(report)
    json.dumps(record, sort_keys=True)

    assert record["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert record["condition_count"] == "1"
    assert record["max_position_change_contracts"] == "4000.000000"
    assert record["max_position_pressure_share"] == "0.400000"
    assert record["max_positioning_score"] == "1.000000"
    assert record["rows"][0]["observed_at"] == "2026-07-04T11:30:00+00:00"
    assert record["rows"][0]["redacted_source_ref"] == "[REDACTED]"
    assert record["bucket_rollups"][0]["condition_count"] == "1"
    assert record["reason_code_counts"][0]["condition_count"] == "1"
    assert not any(isinstance(value, float) for value in _walk_record_values(record))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in _walk_record_values(record)
    )
    for restricted_ref in (
        "bearer quote feed",
        "private quote feed",
        "secret quote feed",
        "token quote feed",
    ):
        restricted = build_market_research_rates_futures_positioning_digest(
            (
                _input(
                    "condition_restricted",
                    "fed",
                    source_ref=restricted_ref,
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
        assert restricted.rows[0].redacted_source_ref == "[REDACTED]"


def test_validation_rejects_floats_nonfinite_dates_duplicates_and_false_flags() -> None:
    with pytest.raises(ValueError, match="net_position_contracts"):
        _input(
            "condition_alpha",
            "fed",
            net_position_contracts=2500.0,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="finite"):
        _input(
            "condition_alpha",
            "fed",
            source_quorum_share=Decimal("NaN"),
        )

    with pytest.raises(ValueError, match="Decimal"):
        _input(
            "condition_alpha",
            "fed",
            source_quorum_share=_DecimalSubclass("0.5"),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        _input(
            "condition_alpha",
            "fed",
            source_quorum_share=_FloatSubclass(0.5),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        _input(
            "condition_alpha",
            "fed",
            observed_at=datetime(2026, 7, 4, 12, 0),
        )

    with pytest.raises(ValueError, match="datetime"):
        build_market_research_rates_futures_positioning_digest(
            (),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_market_research_rates_futures_positioning_digest(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 4, 12, 0),
        )

    with pytest.raises(ValueError, match="unique condition_id"):
        build_market_research_rates_futures_positioning_digest(
            (
                _input("condition_alpha", "fed"),
                _input("condition_alpha", "treasury"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        RatesFuturesPositioningDigestInput(
            condition_id="condition_alpha",
            rates_bucket="fed",
            observed_at=GENERATED_AT,
            prior_net_position_contracts=Decimal("1000.000000"),
            net_position_contracts=Decimal("2500.000000"),
            open_interest_contracts=Decimal("10000.000000"),
            source_quorum_share=Decimal("0.900000"),
            source_config_version="rates-futures-positioning-source-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only"):
        RatesFuturesPositioningDigestInput(
            condition_id="condition_alpha",
            rates_bucket="fed",
            observed_at=GENERATED_AT,
            prior_net_position_contracts=Decimal("1000.000000"),
            net_position_contracts=Decimal("2500.000000"),
            open_interest_contracts=Decimal("10000.000000"),
            source_quorum_share=Decimal("0.900000"),
            source_config_version="rates-futures-positioning-source-v0",
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        RatesFuturesPositioningDigestInput(
            condition_id="condition_alpha",
            rates_bucket="fed",
            observed_at=GENERATED_AT,
            prior_net_position_contracts=Decimal("1000.000000"),
            net_position_contracts=Decimal("2500.000000"),
            open_interest_contracts=Decimal("10000.000000"),
            source_quorum_share=Decimal("0.900000"),
            source_config_version="rates-futures-positioning-source-v0",
            readonly=False,
        )


def test_public_dataclasses_are_frozen_decimal_only_and_reject_inconsistent_reports() -> None:
    row = RatesFuturesPositioningRow(
        condition_id="condition_alpha",
        rates_bucket="fed",
        observed_at=GENERATED_AT,
        prior_net_position_contracts=Decimal("1000.000000"),
        net_position_contracts=Decimal("2500.000000"),
        position_change_contracts=Decimal("1500.000000"),
        open_interest_contracts=Decimal("10000.000000"),
        position_pressure_share=Decimal("0.150000"),
        source_quorum_share=Decimal("0.900000"),
        positioning_score=Decimal("0.600000"),
        positioning_status="watch",
        source_config_version="rates-futures-positioning-source-v0",
        redacted_source_ref=None,
        reason_codes=(
            "rates_futures_positioning_position_change",
            "rates_futures_positioning_pressure",
            "rates_futures_positioning_watch_score",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        row.rates_bucket = "treasury"  # type: ignore[misc]

    with pytest.raises(ValueError, match="position_change_contracts"):
        replace(row, position_change_contracts=Decimal("1600.000000"))

    report = build_market_research_rates_futures_positioning_digest(
        (_input("condition_alpha", "fed"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="condition_count"):
        replace(report, condition_count=Decimal("9"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=())
    stable_row = report.rows[0]
    with pytest.raises(ValueError, match="positioning_status"):
        replace(
            stable_row,
            positioning_status="pass",
            reason_codes=("rates_futures_positioning_position_change",),
        )
    with pytest.raises(ValueError, match="bucket_status"):
        replace(
            report.bucket_rollups[0],
            bucket_status="blocked",
            reason_codes=("rates_futures_positioning_stable",),
        )
    with pytest.raises(ValueError, match="max values"):
        replace(report.bucket_rollups[0], max_positioning_score=None)
    mixed_report = build_market_research_rates_futures_positioning_digest(
        (
            _input("condition_beta", "treasury"),
            _input("condition_alpha", "fed"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="rows"):
        replace(mixed_report, rows=tuple(reversed(mixed_report.rows)))
    with pytest.raises(ValueError, match="bucket_rollups"):
        replace(
            mixed_report,
            bucket_rollups=tuple(reversed(mixed_report.bucket_rollups)),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            mixed_report,
            reason_code_counts=(
                RatesFuturesPositioningReasonCodeCount(
                    reason_code="rates_futures_positioning_digest_empty",
                    condition_count=Decimal("1"),
                ),
            ),
        )

    public_classes = (
        RatesFuturesPositioningBucketRollup,
        RatesFuturesPositioningDigestConfig,
        RatesFuturesPositioningDigestInput,
        RatesFuturesPositioningDigestReport,
        RatesFuturesPositioningReasonCodeCount,
        RatesFuturesPositioningRow,
    )
    for public_class in public_classes:
        assert public_class.__dataclass_params__.frozen is True
        for field in fields(public_class):
            if field.name in {
                "paper_only",
                "reason_code_counts",
                "report_only",
                "readonly",
            }:
                continue
            if any(
                fragment in field.name
                for fragment in (
                    "contracts",
                    "count",
                    "ratio",
                    "score",
                    "share",
                    "threshold",
                )
            ):
                assert "Decimal" in str(field.type) or field.type is Decimal


def test_rejects_future_inputs_and_has_no_mutation_network_db_or_file_io_surface() -> None:
    with pytest.raises(ValueError, match="iterable"):
        build_market_research_rates_futures_positioning_digest(
            "not rows",  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="RatesFuturesPositioningDigestInput"):
        build_market_research_rates_futures_positioning_digest(
            (object(),),  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_rates_futures_positioning_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_market_research_rates_futures_positioning_digest(
            (
                _input(
                    "condition_future",
                    "fed",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_futures_positioning_digest",
    )
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION",
        "RatesFuturesPositioningBucketRollup",
        "RatesFuturesPositioningDigestConfig",
        "RatesFuturesPositioningDigestInput",
        "RatesFuturesPositioningDigestReport",
        "RatesFuturesPositioningReasonCodeCount",
        "RatesFuturesPositioningRow",
        "build_market_research_rates_futures_positioning_digest",
        "market_research_rates_futures_positioning_digest_json_record",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    forbidden_imports = {
        "builtins.open",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_name_fragments = (
        "account",
        "auth",
        "cancel",
        "order",
        "private_key",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_imports
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open"

    lowered_source = source.lower()
    for forbidden in (
        "account",
        "auth",
        "cancel",
        "exchange",
        "market_slug",
        "order",
        "payload",
        "private_key",
        "secret",
        "token",
        "trade",
        "wallet",
    ):
        assert forbidden not in lowered_source


def _walk_record_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(_walk_record_values(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_walk_record_values(item))
        return tuple(items)
    return (value,)
