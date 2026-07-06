from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 6, 14, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab"
        ".market_research_macro_jolts_quits_rate_inflection_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    release_id: str = "us-jolts-release",
    region: str = "us",
    industry: str = "total-nonfarm",
    current_quits_rate: str | Decimal = "2.300000",
    prior_quits_rate: str | Decimal = "2.200000",
    expected_quits_rate: str | Decimal = "2.250000",
    current_job_openings_rate: str | Decimal = "4.700000",
    prior_job_openings_rate: str | Decimal = "4.600000",
    source_age_hours: str | Decimal = "6.000000",
    source_count: str | Decimal = "3.000000",
    source_disagreement: str | Decimal = "0.040000",
    observed_at: datetime = datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_release",),
):
    module = digest()
    return module.MacroJoltsQuitsRateInflectionObservation(
        source_id=source_id,
        release_id=release_id,
        region=region,
        industry=industry,
        current_quits_rate=(
            current_quits_rate
            if isinstance(current_quits_rate, Decimal)
            else d(current_quits_rate)
        ),
        prior_quits_rate=(
            prior_quits_rate if isinstance(prior_quits_rate, Decimal) else d(prior_quits_rate)
        ),
        expected_quits_rate=(
            expected_quits_rate
            if isinstance(expected_quits_rate, Decimal)
            else d(expected_quits_rate)
        ),
        current_job_openings_rate=(
            current_job_openings_rate
            if isinstance(current_job_openings_rate, Decimal)
            else d(current_job_openings_rate)
        ),
        prior_job_openings_rate=(
            prior_job_openings_rate
            if isinstance(prior_job_openings_rate, Decimal)
            else d(prior_job_openings_rate)
        ),
        source_age_hours=(
            source_age_hours if isinstance(source_age_hours, Decimal) else d(source_age_hours)
        ),
        source_count=source_count if isinstance(source_count, Decimal) else d(source_count),
        source_disagreement=(
            source_disagreement
            if isinstance(source_disagreement, Decimal)
            else d(source_disagreement)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_macro_jolts_quits_rate_inflection_digest(
        rows,
        config=cfg or module.MacroJoltsQuitsRateInflectionDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.MacroJoltsQuitsRateInflectionDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-macro-jolts-quits-rate-inflection-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_jolts_quits_rate_inflection_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.inflection_count == d("0.000000")
    assert digest_report.deteriorating_count == d("0.000000")
    assert digest_report.improving_count == d("0.000000")
    assert digest_report.openings_confirmation_count == d("0.000000")
    assert digest_report.source_quality_gap_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.max_absolute_quits_rate_inflection == d("0.000000")
    assert digest_report.average_absolute_quits_rate_inflection == d("0.000000")
    assert digest_report.inflection_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "macro_jolts_quits_rate_inflection_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.MacroJoltsQuitsRateInflectionReasonCodeCount(
            reason_code="macro_jolts_quits_rate_inflection_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_quits_rate_inflection_blocks_or_watches_macro_screening() -> None:
    digest_report = report(
        observation(
            "source-deteriorating",
            release_id="us-jolts-deteriorating",
            current_quits_rate="1.900000",
            prior_quits_rate="2.220000",
            expected_quits_rate="2.150000",
            current_job_openings_rate="4.200000",
            prior_job_openings_rate="4.550000",
            source_age_hours="3.000000",
            source_count="4.000000",
            source_disagreement="0.050000",
        ),
        observation(
            "source-quality",
            release_id="us-jolts-source-quality",
            current_quits_rate="2.100000",
            prior_quits_rate="2.100000",
            expected_quits_rate="2.100000",
            current_job_openings_rate="4.300000",
            prior_job_openings_rate="4.300000",
            source_age_hours="72.000000",
            source_count="1.000000",
            source_disagreement="0.300000",
            upstream_reason_codes=("vendor_revision",),
        ),
        observation(
            "source-improving",
            release_id="us-jolts-improving",
            industry="private",
            current_quits_rate="2.420000",
            prior_quits_rate="2.260000",
            expected_quits_rate="2.300000",
            current_job_openings_rate="4.700000",
            prior_job_openings_rate="4.520000",
            observed_at=datetime(
                2026,
                7,
                6,
                8,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-inline",
            release_id="us-jolts-inline",
            current_quits_rate="2.210000",
            prior_quits_rate="2.200000",
            expected_quits_rate="2.200000",
            current_job_openings_rate="4.400000",
            prior_job_openings_rate="4.400000",
            upstream_reason_codes=(),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_jolts_quits_rate_inflection_screening"
    )
    assert digest_report.input_count == d("4.000000")
    assert digest_report.row_count == d("4.000000")
    assert digest_report.blocked_count == d("2.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.inflection_count == d("2.000000")
    assert digest_report.deteriorating_count == d("1.000000")
    assert digest_report.improving_count == d("1.000000")
    assert digest_report.openings_confirmation_count == d("2.000000")
    assert digest_report.source_quality_gap_count == d("1.000000")
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.max_absolute_quits_rate_inflection == d("0.320000")
    assert digest_report.average_absolute_quits_rate_inflection == d("0.122500")
    assert digest_report.inflection_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "macro_jolts_quits_rate_inflection_blocked_present",
        "macro_jolts_quits_rate_inflection_watch_present",
        "macro_jolts_quits_rate_deteriorating_present",
        "macro_jolts_quits_rate_improving_present",
        "macro_jolts_quits_rate_openings_confirmation_present",
        "macro_jolts_quits_rate_source_stale_present",
        "macro_jolts_quits_rate_source_count_gap_present",
        "macro_jolts_quits_rate_source_disagreement_present",
        "macro_jolts_quits_rate_upstream_reasons_present",
    )
    assert tuple(row.release_id for row in digest_report.rows) == (
        "us-jolts-deteriorating",
        "us-jolts-source-quality",
        "us-jolts-improving",
        "us-jolts-inline",
    )

    blocked, source_quality, watched, passed = digest_report.rows
    assert blocked.inflection_status == "blocked"
    assert blocked.inflection_direction == "deteriorating"
    assert blocked.quits_rate_delta == d("-0.320000")
    assert blocked.quits_rate_surprise == d("-0.250000")
    assert blocked.job_openings_rate_delta == d("-0.350000")
    assert blocked.absolute_quits_rate_inflection == d("0.320000")
    assert blocked.reason_codes == (
        "macro_jolts_quits_rate_blocked_inflection",
        "macro_jolts_quits_rate_deteriorating",
        "macro_jolts_quits_rate_openings_confirmation",
        "macro_jolts_quits_rate_upstream_reasons",
    )
    assert source_quality.inflection_status == "blocked"
    assert source_quality.inflection_direction == "flat"
    assert source_quality.reason_codes == (
        "macro_jolts_quits_rate_inline",
        "macro_jolts_quits_rate_source_stale",
        "macro_jolts_quits_rate_source_count_low",
        "macro_jolts_quits_rate_source_disagreement",
        "macro_jolts_quits_rate_upstream_reasons",
    )
    assert watched.inflection_status == "watch"
    assert watched.inflection_direction == "improving"
    assert watched.observed_at == datetime(2026, 7, 6, 12, 30, tzinfo=UTC)
    assert watched.reason_codes == (
        "macro_jolts_quits_rate_watch_inflection",
        "macro_jolts_quits_rate_improving",
        "macro_jolts_quits_rate_openings_confirmation",
        "macro_jolts_quits_rate_upstream_reasons",
    )
    assert passed.inflection_status == "pass"
    assert passed.reason_codes == ("macro_jolts_quits_rate_inline",)


def test_rows_reason_codes_and_counts_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        release_id="zeta-watch",
        current_quits_rate="2.360000",
        prior_quits_rate="2.200000",
        current_job_openings_rate="4.700000",
        prior_job_openings_rate="4.500000",
    )
    second = observation(
        "source-blocked",
        release_id="beta-blocked",
        current_quits_rate="1.900000",
        prior_quits_rate="2.200000",
        current_job_openings_rate="4.200000",
        prior_job_openings_rate="4.500000",
    )
    third = observation(
        "source-watch-a",
        release_id="alpha-watch",
        current_quits_rate="2.360000",
        prior_quits_rate="2.200000",
        current_job_openings_rate="4.700000",
        prior_job_openings_rate="4.500000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.release_id for row in forward.rows) == (
        "beta-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    assert forward.reason_codes == (
        "macro_jolts_quits_rate_inflection_blocked_present",
        "macro_jolts_quits_rate_inflection_watch_present",
        "macro_jolts_quits_rate_deteriorating_present",
        "macro_jolts_quits_rate_improving_present",
        "macro_jolts_quits_rate_openings_confirmation_present",
        "macro_jolts_quits_rate_upstream_reasons_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "macro_jolts_quits_rate_inflection_blocked_present",
        "macro_jolts_quits_rate_inflection_watch_present",
        "macro_jolts_quits_rate_deteriorating_present",
        "macro_jolts_quits_rate_improving_present",
        "macro_jolts_quits_rate_openings_confirmation_present",
        "macro_jolts_quits_rate_upstream_reasons_present",
    )
    assert tuple(item.count for item in forward.reason_code_counts) == (
        d("1.000000"),
        d("2.000000"),
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("3.000000"),
    )
    assert tuple(item.row_ratio for item in forward.reason_code_counts) == (
        d("0.333333"),
        d("0.666667"),
        d("0.333333"),
        d("0.666667"),
        d("1.000000"),
        d("1.000000"),
    )


def test_non_default_thresholds_can_downgrade_moderate_inflection_risk() -> None:
    module = digest()
    cfg = module.MacroJoltsQuitsRateInflectionDigestConfig(
        watch_inflection_delta=d("0.250000"),
        blocked_inflection_delta=d("0.500000"),
        openings_confirmation_threshold=d("0.500000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            current_quits_rate="2.360000",
            prior_quits_rate="2.200000",
            current_job_openings_rate="4.700000",
            prior_job_openings_rate="4.520000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_macro_jolts_quits_rate_inflection_screening"
    )
    assert digest_report.rows[0].inflection_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "macro_jolts_quits_rate_inline",
        "macro_jolts_quits_rate_upstream_reasons",
    )
    assert digest_report.inflection_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "macro_jolts_quits_rate_upstream_reasons_present",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="current_quits_rate must be a Decimal"):
        observation(current_quits_rate=_DecimalSubclass("2.300000"))
    with pytest.raises(ValueError, match="source_age_hours must be nonnegative"):
        observation(source_age_hours="-1.000000")
    with pytest.raises(ValueError, match="source_count must be an integer Decimal"):
        observation(source_count="1.500000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_macro_jolts_quits_rate_inflection_digest(
            (),
            config=module.MacroJoltsQuitsRateInflectionDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_inflection_delta"):
        module.MacroJoltsQuitsRateInflectionDigestConfig(
            watch_inflection_delta=d("0.500000"),
            blocked_inflection_delta=d("0.250000"),
        )
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["official_release"])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadObservation(module.MacroJoltsQuitsRateInflectionObservation):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadConfig(module.MacroJoltsQuitsRateInflectionDigestConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadRow(module.MacroJoltsQuitsRateInflectionDigestRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReasonCodeCount(module.MacroJoltsQuitsRateInflectionReasonCodeCount):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(module.MacroJoltsQuitsRateInflectionDigestReport):
            pass

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="absolute_quits_rate_inflection must match"):
        replace(valid_row, absolute_quits_rate_inflection=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "macro_jolts_quits_rate_inline",
                "macro_jolts_quits_rate_blocked_inflection",
            ),
        )
    with pytest.raises(ValueError, match="count must be positive"):
        module.MacroJoltsQuitsRateInflectionReasonCodeCount(
            reason_code="macro_jolts_quits_rate_inflection_digest_clear",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="count must be an integer Decimal"):
        module.MacroJoltsQuitsRateInflectionReasonCodeCount(
            reason_code="macro_jolts_quits_rate_inflection_digest_clear",
            count=d("1.500000"),
            row_ratio=d("0.500000"),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        count.paper_only and count.report_only and count.readonly
        for count in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MacroJoltsQuitsRateInflectionDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count readonly must be True"):
        replace(digest_report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_revalidates_tampered_nested_records() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_macro_jolts_quits_rate_inflection_digest_payload(
        digest_report,
    )

    assert module.__all__ == (
        "DEFAULT_MACRO_JOLTS_QUITS_RATE_INFLECTION_DIGEST_CONFIG_VERSION",
        "MacroJoltsQuitsRateInflectionDigestConfig",
        "MacroJoltsQuitsRateInflectionObservation",
        "MacroJoltsQuitsRateInflectionDigestRow",
        "MacroJoltsQuitsRateInflectionReasonCodeCount",
        "MacroJoltsQuitsRateInflectionDigestReport",
        "build_market_research_macro_jolts_quits_rate_inflection_digest",
        "market_research_macro_jolts_quits_rate_inflection_digest_payload",
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["current_quits_rate"] == "2.300000"
    assert payload["rows"][0]["quits_rate_delta"] == "0.100000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T12:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in _forbidden_surface_terms()
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MacroJoltsQuitsRateInflectionDigestConfig(),
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
                assert len(format(field_value, "f").rsplit(".", 1)[1]) == 6
            if isinstance(field_value, tuple):
                assert type(field_value) is tuple, field.name

    object.__setattr__(
        digest_report.rows[0],
        "absolute_quits_rate_inflection",
        d("999.000000"),
    )
    with pytest.raises(ValueError, match="absolute_quits_rate_inflection must match"):
        module.market_research_macro_jolts_quits_rate_inflection_digest_payload(
            digest_report,
        )

    fresh_report = report(observation("source-count-tamper"))
    object.__setattr__(fresh_report.reason_code_counts[0], "count", d("0.000000"))
    with pytest.raises(ValueError, match="count must be positive"):
        module.market_research_macro_jolts_quits_rate_inflection_digest_payload(
            fresh_report,
        )


def test_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            function_name = ""
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            assert function_name not in _forbidden_call_names()
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in _forbidden_import_fragments()
    )
    lowered_source = source.lower()
    for forbidden in _forbidden_surface_terms():
        assert forbidden not in lowered_source


def _forbidden_call_names() -> tuple[str, ...]:
    return (
        "".join(("op", "en")),
        "".join(("connect",)),
        "".join(("execute",)),
        "".join(("request",)),
        "".join(("url", "open")),
        "".join(("trade",)),
        "".join(("submit",)),
        "".join(("cancel",)),
        "".join(("sign",)),
    )


def _forbidden_import_fragments() -> tuple[str, ...]:
    return (
        "".join(("req", "uests")),
        "".join(("http", "x")),
        "".join(("url", "lib")),
        "".join(("sock", "et")),
        "".join(("sub", "process")),
        "".join(("psy", "copg")),
        "".join(("supa", "base")),
        "".join(("path", "lib")),
        "".join(("sqlite", "3")),
    )


def _forbidden_surface_terms() -> tuple[str, ...]:
    return (
        "".join(("as", "dict")),
        "".join(("market", "_", "slug")),
        "".join(("ques", "tion")),
        "".join(("pay", "load", "_", "json")),
        "".join(("private", "_", "key")),
        "".join(("wal", "let")),
        "".join(("url", "open")),
        "".join(("connect", "(")),
        "".join(("execute", "(")),
        "".join(("live", " ", "trading")),
        "".join(("submit", "_", "order")),
        "".join(("cancel", "_", "order")),
        "".join(("replace", "_", "order")),
        "".join(("auth", "entication")),
        "".join(("api", "_", "key")),
    )
