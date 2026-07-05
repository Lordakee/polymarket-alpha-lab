import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_fed_dot_plot_dispersion_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    condition_id: str = "condition-fed-june-cuts",
    market_slug: str = "fed-june-2026-rate-cut",
    meeting_id: str = "fomc-2026-06-17",
    central_bank: str = "federal-reserve",
    public_dot_reference: str = "fomc-sep-public-release",
    observed_at: datetime = datetime(2026, 6, 17, 17, 45, tzinfo=UTC),
    source_count: str | Decimal = "3.000000",
    median_rate_prior_bps: str | Decimal = "350.000000",
    median_rate_current_bps: str | Decimal = "350.000000",
    hawkish_tail_width_bps: str | Decimal = "20.000000",
    dovish_tail_width_bps: str | Decimal = "20.000000",
    market_event_sensitivity: str | Decimal = "0.200000",
    base_confidence: str | Decimal = "0.820000",
    dot_config_version: str = "fed-dot-ingest-v1",
):
    module = digest()
    return module.RatesFedDotPlotDispersionObservation(
        source_id=source_id,
        condition_id=condition_id,
        market_slug=market_slug,
        meeting_id=meeting_id,
        central_bank=central_bank,
        public_dot_reference=public_dot_reference,
        observed_at=observed_at,
        source_count=source_count if isinstance(source_count, Decimal) else d(source_count),
        median_rate_prior_bps=(
            median_rate_prior_bps
            if isinstance(median_rate_prior_bps, Decimal)
            else d(median_rate_prior_bps)
        ),
        median_rate_current_bps=(
            median_rate_current_bps
            if isinstance(median_rate_current_bps, Decimal)
            else d(median_rate_current_bps)
        ),
        hawkish_tail_width_bps=(
            hawkish_tail_width_bps
            if isinstance(hawkish_tail_width_bps, Decimal)
            else d(hawkish_tail_width_bps)
        ),
        dovish_tail_width_bps=(
            dovish_tail_width_bps
            if isinstance(dovish_tail_width_bps, Decimal)
            else d(dovish_tail_width_bps)
        ),
        market_event_sensitivity=(
            market_event_sensitivity
            if isinstance(market_event_sensitivity, Decimal)
            else d(market_event_sensitivity)
        ),
        base_confidence=(
            base_confidence
            if isinstance(base_confidence, Decimal)
            else d(base_confidence)
        ),
        dot_config_version=dot_config_version,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_rates_fed_dot_plot_dispersion_digest(
        rows,
        config=module.RatesFedDotPlotDispersionDigestConfig() if cfg is None else cfg,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.RatesFedDotPlotDispersionDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-rates-fed-dot-plot-dispersion-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_rates_fed_dot_plot_dispersion_digest"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.max_total_dispersion_bps == d("0.000000")
    assert digest_report.average_total_dispersion_bps == d("0.000000")
    assert digest_report.average_market_event_sensitivity == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "rates_fed_dot_plot_dispersion_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.RatesFedDotPlotDispersionReasonCodeCount(
            reason_code="rates_fed_dot_plot_dispersion_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_dispersion_median_revision_and_tail_width_block_rates_market_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            market_slug="fed-june-2026-no-cut",
            public_dot_reference="https://federalreserve.example/fomc/dots?row=1",
            median_rate_prior_bps="350.000000",
            median_rate_current_bps="425.000000",
            hawkish_tail_width_bps="125.000000",
            dovish_tail_width_bps="25.000000",
            market_event_sensitivity="0.820000",
            base_confidence="0.930000",
        ),
        observation(
            "source-watch",
            market_slug="fed-june-2026-one-cut",
            median_rate_prior_bps="350.000000",
            median_rate_current_bps="325.000000",
            hawkish_tail_width_bps="20.000000",
            dovish_tail_width_bps="65.000000",
            market_event_sensitivity="0.450000",
        ),
        observation(
            "source-pass",
            market_slug="fed-june-2026-two-cuts",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.median_revision_alert_count == d("2.000000")
    assert digest_report.dispersion_alert_count == d("2.000000")
    assert digest_report.hawkish_tail_alert_count == d("1.000000")
    assert digest_report.dovish_tail_alert_count == d("1.000000")
    assert digest_report.market_event_sensitive_count == d("2.000000")
    assert digest_report.max_total_dispersion_bps == d("150.000000")
    assert digest_report.average_total_dispersion_bps == d("91.666667")
    assert digest_report.max_absolute_median_revision_bps == d("75.000000")
    assert digest_report.average_market_event_sensitivity == d("0.490000")

    blocked, watched, passed = digest_report.rows
    assert blocked.market_slug == "fed-june-2026-no-cut"
    assert blocked.signal_status == "blocked"
    assert blocked.source_age_seconds == d("900.000000")
    assert blocked.median_revision_bps == d("75.000000")
    assert blocked.absolute_median_revision_bps == d("75.000000")
    assert blocked.total_dispersion_bps == d("150.000000")
    assert blocked.tail_skew_bps == d("100.000000")
    assert blocked.signal_score == d("0.955000")
    assert blocked.capped_confidence == d("0.300000")
    assert blocked.redacted_public_dot_reference.startswith("sha256:")
    assert blocked.reason_codes == (
        "rates_fed_dot_plot_dispersion_high_risk",
        "rates_fed_dot_plot_source_fresh",
        "rates_fed_dot_plot_median_upshift",
        "rates_fed_dot_plot_median_revision_blocked",
        "rates_fed_dot_plot_total_dispersion_blocked",
        "rates_fed_dot_plot_hawkish_tail_wide",
        "rates_fed_dot_plot_tail_skew_blocked",
        "rates_fed_dot_plot_market_event_sensitivity_blocked",
    )

    assert watched.signal_status == "watch"
    assert watched.market_slug == "fed-june-2026-one-cut"
    assert watched.tail_skew_bps == d("-45.000000")
    assert watched.reason_codes == (
        "rates_fed_dot_plot_dispersion_watch",
        "rates_fed_dot_plot_source_fresh",
        "rates_fed_dot_plot_median_downshift",
        "rates_fed_dot_plot_median_revision_watch",
        "rates_fed_dot_plot_total_dispersion_watch",
        "rates_fed_dot_plot_dovish_tail_wide",
        "rates_fed_dot_plot_tail_skew_watch",
        "rates_fed_dot_plot_market_event_sensitivity_watch",
    )

    assert passed.signal_status == "pass"
    assert passed.reason_codes == (
        "rates_fed_dot_plot_dispersion_calm",
        "rates_fed_dot_plot_source_fresh",
        "rates_fed_dot_plot_median_inline",
        "rates_fed_dot_plot_total_dispersion_inline",
        "rates_fed_dot_plot_tail_balanced",
        "rates_fed_dot_plot_market_event_sensitivity_low",
    )


def test_stale_and_thin_source_observations_are_blocked() -> None:
    digest_report = report(
        observation(
            "source-stale-thin",
            observed_at=datetime(2026, 6, 17, 14, 30, tzinfo=UTC),
            source_count="1.000000",
        ),
    )

    row = digest_report.rows[0]
    assert digest_report.digest_status == "blocked"
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.thin_source_count == d("1.000000")
    assert row.signal_status == "blocked"
    assert row.source_age_seconds == d("12600.000000")
    assert "rates_fed_dot_plot_source_stale" in row.reason_codes
    assert "rates_fed_dot_plot_thin_sources" in row.reason_codes


def test_rows_and_reasons_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="fed-watch-beta",
        median_rate_current_bps="375.000000",
        hawkish_tail_width_bps="55.000000",
        dovish_tail_width_bps="20.000000",
        market_event_sensitivity="0.360000",
    )
    second = observation(
        "source-blocked",
        market_slug="fed-blocked-alpha",
        median_rate_current_bps="425.000000",
        hawkish_tail_width_bps="125.000000",
        dovish_tail_width_bps="25.000000",
        market_event_sensitivity="0.820000",
    )
    third = observation(
        "source-watch-a",
        market_slug="fed-watch-alpha",
        median_rate_current_bps="375.000000",
        hawkish_tail_width_bps="55.000000",
        dovish_tail_width_bps="20.000000",
        market_event_sensitivity="0.360000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "fed-blocked-alpha",
        "fed-watch-alpha",
        "fed-watch-beta",
    )
    assert forward.reason_codes == tuple(
        item.reason_code for item in forward.reason_code_counts
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=_DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 6, 17, 17, 45))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            observed_at=datetime(2026, 6, 17, 17, 45, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_rates_fed_dot_plot_dispersion_digest(
            (),
            config=module.RatesFedDotPlotDispersionDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 6, 17, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="observed_at cannot be after generated_at"):
        report(
            observation(
                "source-future",
                observed_at=datetime(2026, 6, 17, 18, 1, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="watch_total_dispersion_bps"):
        module.RatesFedDotPlotDispersionDigestConfig(
            watch_total_dispersion_bps=d("120.000000"),
            blocked_total_dispersion_bps=d("100.000000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="total_dispersion_bps must match tail widths"):
        replace(valid_row, total_dispersion_bps=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must use canonical order"):
        replace(
            valid_row,
            reason_codes=(
                "rates_fed_dot_plot_dispersion_calm",
                "rates_fed_dot_plot_dispersion_watch",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must match row state"):
        replace(
            valid_row,
            reason_codes=(
                "rates_fed_dot_plot_dispersion_watch",
                "rates_fed_dot_plot_dispersion_calm",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_public_dataclasses_are_exact_frozen_types_without_subclassing() -> None:
    module = digest()
    digest_report = report(observation("source-exact-types"))
    public_records = (
        module.RatesFedDotPlotDispersionDigestConfig(),
        observation("source-exact-observation"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )

    for public_record in public_records:
        assert type(public_record).__dataclass_params__.frozen
        assert type(public_record) is public_record.__class__

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadConfig(module.RatesFedDotPlotDispersionDigestConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadObservation(module.RatesFedDotPlotDispersionObservation):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadRow(module.RatesFedDotPlotDispersionDigestRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadReasonCount(module.RatesFedDotPlotDispersionReasonCodeCount):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadReport(module.RatesFedDotPlotDispersionDigestReport):
            pass


def test_hard_flags_are_enforced_on_config_observations_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.RatesFedDotPlotDispersionDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_manual_reason_code_counts_must_be_positive() -> None:
    module = digest()

    with pytest.raises(ValueError, match="count must be positive"):
        module.RatesFedDotPlotDispersionReasonCodeCount(
            reason_code="rates_fed_dot_plot_dispersion_calm",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )


def test_report_constructor_rejects_noncanonical_rows_and_reason_count_order() -> None:
    module = digest()
    canonical = report(
        observation(
            "source-watch-b",
            market_slug="fed-watch-beta-constructor",
            median_rate_current_bps="375.000000",
            hawkish_tail_width_bps="55.000000",
            dovish_tail_width_bps="20.000000",
            market_event_sensitivity="0.360000",
        ),
        observation(
            "source-blocked-constructor",
            market_slug="fed-blocked-alpha-constructor",
            median_rate_current_bps="425.000000",
            hawkish_tail_width_bps="125.000000",
            dovish_tail_width_bps="25.000000",
            market_event_sensitivity="0.820000",
        ),
        observation(
            "source-watch-a",
            market_slug="fed-watch-alpha-constructor",
            median_rate_current_bps="375.000000",
            hawkish_tail_width_bps="55.000000",
            dovish_tail_width_bps="20.000000",
            market_event_sensitivity="0.360000",
        ),
    )

    kwargs = dict(
        generated_at=canonical.generated_at,
        config_version=canonical.config_version,
        input_count=canonical.input_count,
        row_count=canonical.row_count,
        blocked_count=canonical.blocked_count,
        watch_count=canonical.watch_count,
        pass_count=canonical.pass_count,
        stale_source_count=canonical.stale_source_count,
        thin_source_count=canonical.thin_source_count,
        median_revision_alert_count=canonical.median_revision_alert_count,
        dispersion_alert_count=canonical.dispersion_alert_count,
        hawkish_tail_alert_count=canonical.hawkish_tail_alert_count,
        dovish_tail_alert_count=canonical.dovish_tail_alert_count,
        market_event_sensitive_count=canonical.market_event_sensitive_count,
        max_total_dispersion_bps=canonical.max_total_dispersion_bps,
        average_total_dispersion_bps=canonical.average_total_dispersion_bps,
        max_absolute_median_revision_bps=canonical.max_absolute_median_revision_bps,
        average_market_event_sensitivity=canonical.average_market_event_sensitivity,
        max_signal_score=canonical.max_signal_score,
        average_signal_score=canonical.average_signal_score,
        digest_status=canonical.digest_status,
        recommended_next_step=canonical.recommended_next_step,
        rows=canonical.rows,
        reason_codes=canonical.reason_codes,
        reason_code_counts=canonical.reason_code_counts,
    )

    assert module.RatesFedDotPlotDispersionDigestReport(**kwargs) == canonical
    with pytest.raises(ValueError, match="rows must use canonical order"):
        module.RatesFedDotPlotDispersionDigestReport(
            **{**kwargs, "rows": tuple(reversed(canonical.rows))},
        )
    with pytest.raises(ValueError, match="reason_codes must use canonical order"):
        module.RatesFedDotPlotDispersionDigestReport(
            **{**kwargs, "reason_codes": tuple(reversed(canonical.reason_codes))},
        )
    with pytest.raises(ValueError, match="reason_code_counts must use canonical order"):
        module.RatesFedDotPlotDispersionDigestReport(
            **{
                **kwargs,
                "reason_code_counts": tuple(reversed(canonical.reason_code_counts)),
            },
        )


def test_payload_revalidates_tampered_public_dataclasses_before_serialization() -> None:
    module = digest()

    def assert_payload_rejects(mutator: object, message: str) -> None:
        digest_report = report(observation("source-payload-revalidate"))
        mutator(digest_report)  # type: ignore[operator]
        with pytest.raises(ValueError, match=message):
            module.market_research_rates_fed_dot_plot_dispersion_digest_payload(
                digest_report,
            )

    assert_payload_rejects(
        lambda digest_report: object.__setattr__(
            digest_report.rows[0],
            "total_dispersion_bps",
            d("999.000000"),
        ),
        "total_dispersion_bps must match tail widths",
    )
    assert_payload_rejects(
        lambda digest_report: object.__setattr__(
            digest_report.rows[0],
            "readonly",
            False,
        ),
        "readonly must be True",
    )
    assert_payload_rejects(
        lambda digest_report: object.__setattr__(
            digest_report,
            "report_only",
            False,
        ),
        "report_only must be True",
    )


def test_payload_replays_constructor_validation_for_public_dataclasses() -> None:
    module = digest()

    negative_source_age_report = report(observation("source-negative-age"))
    object.__setattr__(
        negative_source_age_report.rows[0],
        "source_age_seconds",
        d("-1.000000"),
    )
    with pytest.raises(ValueError, match="source_age_seconds must be nonnegative"):
        module.market_research_rates_fed_dot_plot_dispersion_digest_payload(
            negative_source_age_report,
        )

    invalid_status_report = report(observation("source-invalid-status"))
    object.__setattr__(invalid_status_report.rows[0], "signal_status", "bogus")
    with pytest.raises(ValueError, match="signal_status must be one of"):
        module.market_research_rates_fed_dot_plot_dispersion_digest_payload(
            invalid_status_report,
        )

    invalid_config = module.RatesFedDotPlotDispersionDigestConfig()
    object.__setattr__(invalid_config, "max_source_age_seconds", d("0.000000"))
    with pytest.raises(ValueError, match="max_source_age_seconds must be positive"):
        module._payload_value(invalid_config)

    invalid_observation = observation("source-invalid-observation")
    object.__setattr__(invalid_observation, "source_count", d("-1.000000"))
    with pytest.raises(ValueError, match="source_count must be nonnegative"):
        module._payload_value(invalid_observation)


def test_payload_rejects_tampered_non_utc_datetimes_and_non_six_decimal_values() -> None:
    module = digest()
    eastern_generated_at = GENERATED_AT.astimezone(timezone(timedelta(hours=-4)))

    non_utc_report = report(observation("source-non-utc-payload"))
    object.__setattr__(non_utc_report, "generated_at", eastern_generated_at)
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        module.market_research_rates_fed_dot_plot_dispersion_digest_payload(
            non_utc_report,
        )

    non_six_decimal_report = report(observation("source-non-six-decimal-payload"))
    object.__setattr__(
        non_six_decimal_report,
        "average_signal_score",
        Decimal("0.1"),
    )
    with pytest.raises(ValueError, match="average_signal_score must use six decimals"):
        module.market_research_rates_fed_dot_plot_dispersion_digest_payload(
            non_six_decimal_report,
        )


def test_payload_helper_rejects_raw_containers_and_unknown_public_objects() -> None:
    module = digest()

    for value in ({}, [], set(), object()):
        with pytest.raises(ValueError, match="payload value"):
            module._payload_value(value)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_rates_fed_dot_plot_dispersion_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["median_revision_bps"] == "0.000000"
    assert payload["rows"][0]["observed_at"] == "2026-06-17T17:45:00+00:00"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.RatesFedDotPlotDispersionDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_rates_fed_dot_plot_dispersion_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "pathlib",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "dataclasses.asdict",
        "private_key",
        "credential",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "http://",
        "https://",
    ):
        assert forbidden not in source.lower()
