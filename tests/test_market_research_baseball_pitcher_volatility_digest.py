from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-baseball-pitcher-volatility-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[override]
        return None

    def dst(self, dt):  # type: ignore[override]
        return None


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_pitcher_volatility_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "era_range_watch_threshold": d("0.600000"),
        "whip_range_watch_threshold": d("0.150000"),
        "pitch_count_range_watch_threshold": d("18.000000"),
        "velocity_drop_watch_threshold": d("1.500000"),
        "min_snapshot_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBaseballPitcherVolatilityDigestConfig(**values)


def snapshot(
    pitcher_key: str = "pitcher.cole",
    pitcher_name: str = "Gerrit Cole",
    team_key: str = "nyy",
    *,
    observed_at: datetime = BASE_OBSERVED_AT,
    projected_era: Decimal = d("3.200000"),
    projected_whip: Decimal = d("1.050000"),
    projected_pitch_count: Decimal = d("92.000000"),
    fastball_velocity_mph: Decimal = d("96.000000"),
    source_count: Decimal = d("2.000000"),
    source_config_version: str = "pitcher-volatility-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBaseballPitcherVolatilityDigestSnapshot(
        pitcher_key=pitcher_key,
        pitcher_name=pitcher_name,
        team_key=team_key,
        observed_at=observed_at,
        projected_era=projected_era,
        projected_whip=projected_whip,
        projected_pitch_count=projected_pitch_count,
        fastball_velocity_mph=fastball_velocity_mph,
        source_count=source_count,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*snapshots, **overrides):
    digest = module()
    values = {
        "snapshots": snapshots,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_baseball_pitcher_volatility_digest(**values)


def test_digest_flags_pitcher_projection_velocity_and_pitch_count_volatility() -> None:
    report = build_report(
        snapshot(
            "pitcher.cole",
            "Gerrit Cole",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=4),
            projected_era=d("3.100000"),
            projected_whip=d("1.020000"),
            projected_pitch_count=d("96.000000"),
            fastball_velocity_mph=d("96.400000"),
            source_config_version="pitcher-feed-v0",
        ),
        snapshot(
            "pitcher.cole",
            "Gerrit Cole",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=2),
            projected_era=d("3.950000"),
            projected_whip=d("1.240000"),
            projected_pitch_count=d("74.000000"),
            fastball_velocity_mph=d("94.600000"),
            source_config_version="pitcher-feed-v1",
        ),
        snapshot(
            "pitcher.webb",
            "Logan Webb",
            "sf",
            observed_at=GENERATED_AT - timedelta(minutes=40),
            projected_era=d("3.400000"),
            projected_whip=d("1.100000"),
            projected_pitch_count=d("91.000000"),
            fastball_velocity_mph=d("92.800000"),
        ),
        snapshot(
            "pitcher.webb",
            "Logan Webb",
            "sf",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            projected_era=d("3.450000"),
            projected_whip=d("1.120000"),
            projected_pitch_count=d("90.000000"),
            fastball_velocity_mph=d("92.700000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_baseball_pitcher_volatility_digest"
    )
    assert report.pitcher_count == d("2")
    assert report.watch_pitcher_count == d("1")
    assert report.clear_pitcher_count == d("1")
    assert report.snapshot_count == d("4")
    assert report.volatile_era_pitcher_count == d("1")
    assert report.volatile_whip_pitcher_count == d("1")
    assert report.volatile_pitch_count_pitcher_count == d("1")
    assert report.velocity_drop_pitcher_count == d("1")
    assert report.max_era_range == d("0.850000")
    assert report.max_whip_range == d("0.220000")
    assert report.max_pitch_count_range == d("22.000000")
    assert report.max_velocity_drop == d("1.800000")
    assert report.reason_codes == (
        "baseball_pitcher_volatility_era_range_high",
        "baseball_pitcher_volatility_pitch_count_range_high",
        "baseball_pitcher_volatility_velocity_drop",
        "baseball_pitcher_volatility_whip_range_high",
    )
    assert report.reason_code_counts == (
        module().MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code="baseball_pitcher_volatility_era_range_high",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
        module().MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code="baseball_pitcher_volatility_pitch_count_range_high",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
        module().MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code="baseball_pitcher_volatility_velocity_drop",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
        module().MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code="baseball_pitcher_volatility_whip_range_high",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
    )
    assert report.source_config_versions == (
        ("pitcher.cole", "pitcher-feed-v0"),
        ("pitcher.cole", "pitcher-feed-v1"),
        ("pitcher.webb", "pitcher-volatility-source-v0"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.pitcher_key for row in report.rows) == (
        "pitcher.cole",
        "pitcher.webb",
    )
    cole = report.rows[0]
    assert cole.pitcher_name == "Gerrit Cole"
    assert cole.team_key == "nyy"
    assert cole.snapshot_count == d("2")
    assert cole.latest_observed_at == GENERATED_AT - timedelta(hours=2)
    assert cole.latest_projected_era == d("3.950000")
    assert cole.era_range == d("0.850000")
    assert cole.whip_range == d("0.220000")
    assert cole.pitch_count_range == d("22.000000")
    assert cole.velocity_drop == d("1.800000")
    assert cole.digest_status == "watch"
    assert cole.reason_codes == (
        "baseball_pitcher_volatility_era_range_high",
        "baseball_pitcher_volatility_pitch_count_range_high",
        "baseball_pitcher_volatility_velocity_drop",
        "baseball_pitcher_volatility_whip_range_high",
    )

    webb = report.rows[1]
    assert webb.digest_status == "clear"
    assert webb.reason_codes == ("baseball_pitcher_volatility_clear",)


def test_digest_passes_for_empty_stable_and_insufficient_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.pitcher_count == d("0")
    assert empty_report.snapshot_count == d("0")
    assert empty_report.rows == ()
    assert empty_report.max_era_range is None
    assert empty_report.reason_codes == ("baseball_pitcher_volatility_empty",)

    stable_report = build_report(
        snapshot("pitcher.alpha", "Alpha Starter", "lad", projected_era=d("3.100000")),
        snapshot(
            "pitcher.alpha",
            "Alpha Starter",
            "lad",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_era=d("3.200000"),
            projected_pitch_count=d("91.000000"),
        ),
        snapshot("pitcher.beta", "Beta Starter", "bos"),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "baseball_pitcher_volatility_insufficient_history",
        "baseball_pitcher_volatility_passed",
    )
    assert tuple((row.pitcher_key, row.digest_status) for row in stable_report.rows) == (
        ("pitcher.beta", "insufficient_history"),
        ("pitcher.alpha", "clear"),
    )


def test_payload_helper_uses_json_ready_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        snapshot(
            "pitcher.payload",
            "Payload Starter",
            "sea",
            observed_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
            projected_era=d("3.000000"),
        ),
        snapshot(
            "pitcher.payload",
            "Payload Starter",
            "sea",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            projected_era=d("3.700000"),
        ),
    )

    payload = digest.market_research_baseball_pitcher_volatility_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["pitcher_count"] == "1.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-03T17:30:00+00:00"
    assert payload["rows"][0]["era_range"] == "0.700000"
    assert payload["rows"][0]["snapshot_count"] == "2.000000"
    assert payload["reason_code_counts"][0]["pitcher_count"] == "1.000000"
    assert payload["reason_code_counts"][0]["pitcher_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
        ):
            assert forbidden not in payload_text


def test_payload_strings_are_exact_six_decimal_for_all_public_numeric_fields() -> None:
    digest = module()
    report = build_report(
        snapshot(
            "pitcher.payload-six",
            "Payload Six",
            "sea",
            observed_at=BASE_OBSERVED_AT,
            projected_era=d("3.000000"),
            projected_whip=d("1.000000"),
            projected_pitch_count=d("96.000000"),
            fastball_velocity_mph=d("96.300000"),
        ),
        snapshot(
            "pitcher.payload-six",
            "Payload Six",
            "sea",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_era=d("3.700000"),
            projected_whip=d("1.220000"),
            projected_pitch_count=d("74.000000"),
            fastball_velocity_mph=d("94.500000"),
        ),
    )

    payload = digest.market_research_baseball_pitcher_volatility_digest_payload(report)

    for field_name, value in _walk_payload_items(payload):
        if not _is_public_numeric_field(field_name):
            continue
        assert type(value) is str
        whole, separator, fractional = value.partition(".")
        assert whole
        assert separator == "."
        assert len(fractional) == 6
        Decimal(value)


def test_payload_helper_rejects_raw_containers_and_unknown_public_objects() -> None:
    digest = module()

    unsupported_values = (
        [],
        {},
        set(),
        config(),
        snapshot(),
        object(),
    )
    for unsupported_value in unsupported_values:
        with pytest.raises(ValueError, match="unsupported"):
            digest._payload_value(unsupported_value)


def test_payload_revalidates_nested_dataclasses_and_rejects_tampering() -> None:
    digest = module()

    def make_report():
        return build_report(
            snapshot(
                "pitcher.payload-revalidate",
                "Payload Revalidate",
                "sea",
                observed_at=BASE_OBSERVED_AT,
                projected_era=d("3.000000"),
            ),
            snapshot(
                "pitcher.payload-revalidate",
                "Payload Revalidate",
                "sea",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
                projected_era=d("3.700000"),
            ),
        )

    nested_flag_report = make_report()
    object.__setattr__(nested_flag_report.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="row report_only must be True"):
        digest.market_research_baseball_pitcher_volatility_digest_payload(
            nested_flag_report,
        )

    noncanonical_decimal_report = make_report()
    object.__setattr__(
        noncanonical_decimal_report.rows[0],
        "era_range",
        d("0.7000001"),
    )
    with pytest.raises(ValueError, match="era_range must have at most six decimal places"):
        digest.market_research_baseball_pitcher_volatility_digest_payload(
            noncanonical_decimal_report,
        )

    non_utc_datetime_report = make_report()
    object.__setattr__(
        non_utc_datetime_report.rows[0],
        "latest_observed_at",
        datetime(2026, 7, 3, 13, 30, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="latest_observed_at must be UTC"):
        digest.market_research_baseball_pitcher_volatility_digest_payload(
            non_utc_datetime_report,
        )


def test_payload_rejects_tampered_report_and_reason_count_flags_and_precision() -> None:
    digest = module()

    def make_report():
        return build_report(
            snapshot(
                "pitcher.payload-reason-count",
                "Payload Reason Count",
                "sea",
                observed_at=BASE_OBSERVED_AT,
                projected_era=d("3.000000"),
            ),
            snapshot(
                "pitcher.payload-reason-count",
                "Payload Reason Count",
                "sea",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
                projected_era=d("3.700000"),
            ),
        )

    report_flag_report = make_report()
    object.__setattr__(report_flag_report, "readonly", False)
    with pytest.raises(ValueError, match="report readonly must be True"):
        digest.market_research_baseball_pitcher_volatility_digest_payload(
            report_flag_report,
        )

    nested_flag_report = make_report()
    object.__setattr__(nested_flag_report.reason_code_counts[0], "paper_only", False)
    with pytest.raises(ValueError, match="reason_code_count paper_only must be True"):
        digest.market_research_baseball_pitcher_volatility_digest_payload(
            nested_flag_report,
        )

    noncanonical_decimal_report = make_report()
    object.__setattr__(
        noncanonical_decimal_report.reason_code_counts[0],
        "pitcher_ratio",
        d("1.0000001"),
    )
    with pytest.raises(ValueError, match="pitcher_ratio must have at most six"):
        digest.market_research_baseball_pitcher_volatility_digest_payload(
            noncanonical_decimal_report,
        )


def test_dataclasses_validate_decimal_datetime_flags_consistency_and_types() -> None:
    digest = module()

    row = snapshot()
    with pytest.raises(FrozenInstanceError):
        row.projected_era = d("3.300000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="projected_era must be a Decimal"):
        snapshot(projected_era=3.2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 3, 16, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="pitcher_key must be a string"):
        snapshot(pitcher_key=_StringSubclass("pitcher.cole"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            snapshot(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="era_range_watch_threshold"):
        config(era_range_watch_threshold=_DecimalSubclass("0.600000"))

    with pytest.raises(ValueError, match="min_snapshot_count"):
        config(min_snapshot_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="snapshots must not contain duplicate"):
        build_report(snapshot(source_config_version="v0"), snapshot(source_config_version="v1"))

    report = build_report(
        snapshot("pitcher.gamma", "Gamma Starter", "stl"),
        snapshot(
            "pitcher.gamma",
            "Gamma Starter",
            "stl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["pitcher_count"] = d("2")
    with pytest.raises(ValueError, match="pitcher_count"):
        digest.MarketResearchBaseballPitcherVolatilityDigestReport(**bad_report_values)


def test_public_dataclass_constructors_reject_explicit_false_flags() -> None:
    digest = module()
    sample_config = config()
    sample_snapshot = snapshot()
    sample_report = build_report(
        snapshot(
            "pitcher.false-flags",
            "False Flags",
            "sea",
            observed_at=BASE_OBSERVED_AT,
            projected_era=d("3.000000"),
        ),
        snapshot(
            "pitcher.false-flags",
            "False Flags",
            "sea",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_era=d("3.700000"),
        ),
    )
    public_samples = (
        (
            "config",
            digest.MarketResearchBaseballPitcherVolatilityDigestConfig,
            sample_config,
        ),
        (
            "snapshot",
            digest.MarketResearchBaseballPitcherVolatilityDigestSnapshot,
            sample_snapshot,
        ),
        (
            "reason_code_count",
            digest.MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount,
            sample_report.reason_code_counts[0],
        ),
        (
            "row",
            digest.MarketResearchBaseballPitcherVolatilityDigestRow,
            sample_report.rows[0],
        ),
        (
            "report",
            digest.MarketResearchBaseballPitcherVolatilityDigestReport,
            sample_report,
        ),
    )

    for label, public_class, sample in public_samples:
        values = {field.name: getattr(sample, field.name) for field in fields(sample)}
        for flag_name in ("paper_only", "report_only", "readonly"):
            tampered_values = {**values, flag_name: False}
            with pytest.raises(ValueError, match=f"{label} {flag_name} must be True"):
                public_class(**tampered_values)


def test_public_dataclasses_reject_subclassing_and_exact_type_instantiation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest = module()
    public_classes = (
        digest.MarketResearchBaseballPitcherVolatilityDigestConfig,
        digest.MarketResearchBaseballPitcherVolatilityDigestSnapshot,
        digest.MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount,
        digest.MarketResearchBaseballPitcherVolatilityDigestRow,
        digest.MarketResearchBaseballPitcherVolatilityDigestReport,
    )

    for public_class in public_classes:
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{public_class.__name__}", (public_class,), {})

    def allow_subclass(cls, **kwargs) -> None:
        return None

    monkeypatch.setattr(
        digest.MarketResearchBaseballPitcherVolatilityDigestConfig,
        "__init_subclass__",
        classmethod(allow_subclass),
    )
    config_subclass = type(
        "ConfigSubclass",
        (digest.MarketResearchBaseballPitcherVolatilityDigestConfig,),
        {},
    )
    with pytest.raises(ValueError, match="config must be exactly"):
        config_subclass(config_version=CONFIG_VERSION)


def test_dataclass_constructors_reject_noncanonical_ordering() -> None:
    digest = module()
    report = build_report(
        snapshot(
            "pitcher.det-watch",
            "Det Watch",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=3),
            projected_era=d("3.100000"),
            projected_whip=d("1.020000"),
            projected_pitch_count=d("96.000000"),
            fastball_velocity_mph=d("96.400000"),
            source_config_version="pitcher-feed-v0",
        ),
        snapshot(
            "pitcher.det-watch",
            "Det Watch",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=2),
            projected_era=d("3.950000"),
            projected_whip=d("1.240000"),
            projected_pitch_count=d("74.000000"),
            fastball_velocity_mph=d("94.600000"),
            source_config_version="pitcher-feed-v1",
        ),
        snapshot("pitcher.det-clear", "Det Clear", "sea", projected_era=d("3.000000")),
        snapshot(
            "pitcher.det-clear",
            "Det Clear",
            "sea",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=45),
            projected_era=d("3.100000"),
        ),
    )

    row_values = {
        field.name: getattr(report.rows[0], field.name)
        for field in fields(report.rows[0])
    }
    row_values["reason_codes"] = tuple(reversed(report.rows[0].reason_codes))
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        digest.MarketResearchBaseballPitcherVolatilityDigestRow(**row_values)

    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["rows"] = tuple(reversed(report.rows))
    with pytest.raises(ValueError, match="rows must be canonical"):
        digest.MarketResearchBaseballPitcherVolatilityDigestReport(**report_values)

    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["source_config_versions"] = tuple(
        reversed(report.source_config_versions),
    )
    with pytest.raises(ValueError, match="source_config_versions must be canonical"):
        digest.MarketResearchBaseballPitcherVolatilityDigestReport(**report_values)

    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["reason_code_counts"] = tuple(reversed(report.reason_code_counts))
    with pytest.raises(ValueError, match="reason_code_counts must be canonical"):
        digest.MarketResearchBaseballPitcherVolatilityDigestReport(**report_values)


def test_reason_code_counts_empty_inputs_and_sensitive_strings_are_hardened() -> None:
    digest = module()

    with pytest.raises(ValueError, match="pitcher_count must be positive"):
        digest.MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code="baseball_pitcher_volatility_era_range_high",
            pitcher_count=d("0.000000"),
            pitcher_ratio=d("0.000000"),
        )

    empty_report = build_report()
    assert empty_report.reason_code_counts == (
        digest.MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code="baseball_pitcher_volatility_empty",
            pitcher_count=d("1.000000"),
            pitcher_ratio=d("0.000000"),
        ),
    )
    empty_payload = digest.market_research_baseball_pitcher_volatility_digest_payload(
        empty_report,
    )
    assert empty_payload["reason_code_counts"] == [
        {
            "reason_code": "baseball_pitcher_volatility_empty",
            "pitcher_count": "1.000000",
            "pitcher_ratio": "0.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    with pytest.raises(ValueError, match="unsafe public text"):
        snapshot(source_config_version="pitcher-feed-to" + "ken")


def test_public_numeric_fields_are_decimal_only() -> None:
    report = build_report(
        snapshot("pitcher.decimal", "Decimal Starter", "mia"),
        snapshot(
            "pitcher.decimal",
            "Decimal Starter",
            "mia",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            projected_era=d("3.800000"),
        ),
    )

    public_values = (report, *report.rows, *report.reason_code_counts)
    for value in public_values:
        for field in fields(value):
            if _is_public_numeric_field(field.name):
                field_value = getattr(value, field.name)
                if field_value is not None:
                    assert type(field_value) is Decimal


def test_module_scope_has_no_io_live_trading_float_or_durable_store_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_baseball_pitcher_volatility_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()

    for forbidden in (
        "live trading",
        "wallet",
        "keys",
        "broker",
        "signing",
        "submit",
        "cancel",
        "order",
        "replace",
        "exchange",
        "account",
        "advice",
        "auth",
        "private",
        "secret",
        "token",
        "open(",
        "requests",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "sql",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def test_payload_path_does_not_use_dataclasses_asdict() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_baseball_pitcher_volatility_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source_text)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "dataclasses":
            imported_names = {alias.name for alias in node.names}
            assert "asdict" not in imported_names
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "asdict"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr != "asdict"


def _walk_payload_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload_values(item)
    else:
        yield value


def _walk_payload_items(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk_payload_items(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_payload_items(item)


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_threshold")
        or field_name.endswith("_range")
        or field_name.endswith("_drop")
        or field_name.startswith("latest_projected_")
        or field_name.startswith("latest_fastball_")
        or field_name.startswith("fastball_velocity_")
        or field_name.startswith("era_")
        or field_name.startswith("whip_")
        or field_name.startswith("pitch_count_")
        or field_name.startswith("max_")
        or field_name.startswith("min_")
    )
