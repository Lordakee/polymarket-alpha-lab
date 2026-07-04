from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_fomc_dissent_signal_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-rates-fomc-dissent-signal-digest-v0",
        "watch_dissent_count": d("1.000000"),
        "blocked_dissent_count": d("2.000000"),
        "watch_median_dot_shift_bps": d("25.000000"),
        "blocked_median_dot_shift_bps": d("50.000000"),
        "watch_dot_dispersion_bps": d("50.000000"),
        "blocked_dot_dispersion_bps": d("100.000000"),
        "watch_signal_score": d("0.350000"),
        "blocked_signal_score": d("0.650000"),
        "max_source_age_seconds": d("600.000000"),
        "stale_confidence_cap": d("0.300000"),
        "watch_confidence_cap": d("0.500000"),
    }
    values.update(overrides)
    return module.RatesFOMCDissentSignalDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "fomc-rate-decision-signal",
    meeting_id: str = "fomc-2026-07-29",
    dissent_count: Decimal = d("1.000000"),
    hawkish_dissent_count: Decimal = d("1.000000"),
    dovish_dissent_count: Decimal = d("0.000000"),
    median_dot_shift_bps: Decimal = d("30.000000"),
    dot_dispersion_bps: Decimal = d("60.000000"),
    committee_disagreement_score: Decimal = d("0.400000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    base_confidence: Decimal = d("0.850000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.RatesFOMCDissentSignalObservation(
        source_id=source_id,
        market_slug=market_slug,
        meeting_id=meeting_id,
        dissent_count=dissent_count,
        hawkish_dissent_count=hawkish_dissent_count,
        dovish_dissent_count=dovish_dissent_count,
        median_dot_shift_bps=median_dot_shift_bps,
        dot_dispersion_bps=dot_dispersion_bps,
        committee_disagreement_score=committee_disagreement_score,
        observed_at=observed_at,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    digest_config: Any | None = None,
) -> Any:
    module = api()
    return module.build_market_research_rates_fomc_dissent_signal_digest(
        inputs,
        config=config() if digest_config is None else digest_config,
        generated_at=generated_at,
    )


def assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_float_or_decimal_payload(child)


def test_builds_high_risk_fomc_dissent_signal_digest_with_sorting_reasons() -> None:
    report = digest(
        (
            observation(
                "beta-watch",
                market_slug="september-fomc-25bp-cut-watch",
                meeting_id="fomc-2026-09-16",
                dissent_count=d("1.000000"),
                hawkish_dissent_count=d("0.000000"),
                dovish_dissent_count=d("1.000000"),
                median_dot_shift_bps=d("-30.000000"),
                dot_dispersion_bps=d("45.000000"),
                committee_disagreement_score=d("0.200000"),
                upstream_reason_codes=("fedwatch_panel",),
            ),
            observation(
                "alpha-calm",
                market_slug="december-fomc-hold-calm",
                meeting_id="fomc-2026-12-16",
                dissent_count=d("0.000000"),
                hawkish_dissent_count=d("0.000000"),
                dovish_dissent_count=d("0.000000"),
                median_dot_shift_bps=d("5.000000"),
                dot_dispersion_bps=d("20.000000"),
                committee_disagreement_score=d("0.100000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            observation(
                "zeta-high",
                market_slug="july-fomc-hawkish-dissent-risk",
                meeting_id="fomc-2026-07-29",
                dissent_count=d("3.000000"),
                hawkish_dissent_count=d("3.000000"),
                dovish_dissent_count=d("0.000000"),
                median_dot_shift_bps=d("62.500000"),
                dot_dispersion_bps=d("125.000000"),
                committee_disagreement_score=d("0.800000"),
                observed_at=GENERATED_AT - timedelta(seconds=900),
                upstream_reason_codes=("regional_bank_rates_watch", "fedwatch_panel"),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "market-research-rates-fomc-dissent-signal-digest-v0"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.hawkish_dissent_signal_count == d("1.000000")
    assert report.dovish_dissent_signal_count == d("1.000000")
    assert report.dot_plot_upshift_count == d("2.000000")
    assert report.dot_plot_downshift_count == d("1.000000")
    assert report.max_signal_score == d("0.970000")
    assert report.average_signal_score == d("0.509167")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_rates_fomc_dissent_signal_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [(row.source_id, row.signal_status, row.signal_score) for row in report.rows] == [
        ("zeta-high", "blocked", d("0.970000")),
        ("beta-watch", "watch", d("0.467500")),
        ("alpha-calm", "pass", d("0.090000")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.source_age_seconds == d("900.000000")
    assert blocked.absolute_median_dot_shift_bps == d("62.500000")
    assert blocked.confidence_cap == d("0.300000")
    assert blocked.capped_confidence == d("0.300000")
    assert blocked.reason_codes == (
        "fedwatch_panel",
        "rates_fomc_committee_disagreement_high",
        "rates_fomc_dissent_count_blocked",
        "rates_fomc_dissent_hawkish",
        "rates_fomc_dissent_signal_high_risk",
        "rates_fomc_dot_dispersion_blocked",
        "rates_fomc_dot_plot_upshift",
        "rates_fomc_dot_shift_blocked",
        "rates_fomc_source_stale",
        "regional_bank_rates_watch",
    )
    assert watch.confidence_cap == d("0.500000")
    assert watch.capped_confidence == d("0.500000")
    assert watch.reason_codes == (
        "fedwatch_panel",
        "rates_fomc_dissent_count_watch",
        "rates_fomc_dissent_dovish",
        "rates_fomc_dissent_signal_watch",
        "rates_fomc_dot_plot_downshift",
        "rates_fomc_dot_shift_watch",
        "rates_fomc_source_fresh",
    )
    assert passed.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert passed.reason_codes == (
        "rates_fomc_dissent_none",
        "rates_fomc_dissent_signal_calm",
        "rates_fomc_dot_plot_upshift",
        "rates_fomc_source_fresh",
    )
    assert report.reason_codes == (
        "fedwatch_panel",
        "rates_fomc_committee_disagreement_high",
        "rates_fomc_dissent_count_blocked",
        "rates_fomc_dissent_count_watch",
        "rates_fomc_dissent_dovish",
        "rates_fomc_dissent_hawkish",
        "rates_fomc_dissent_none",
        "rates_fomc_dissent_signal_calm",
        "rates_fomc_dissent_signal_high_risk",
        "rates_fomc_dissent_signal_watch",
        "rates_fomc_dot_dispersion_blocked",
        "rates_fomc_dot_plot_downshift",
        "rates_fomc_dot_plot_upshift",
        "rates_fomc_dot_shift_blocked",
        "rates_fomc_dot_shift_watch",
        "rates_fomc_source_fresh",
        "rates_fomc_source_stale",
        "regional_bank_rates_watch",
    )
    assert report.reason_code_counts[0].reason_code == "fedwatch_panel"
    assert report.reason_code_counts[0].count == d("2.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.666667")


def test_empty_digest_and_payload_are_report_only_readonly_decimal_stringed() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_rates_fomc_dissent_signal_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_signal_count == d("0.000000")
    assert report.watch_signal_count == d("0.000000")
    assert report.max_signal_score == d("0.000000")
    assert report.average_signal_score == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("rates_fomc_dissent_signal_digest_empty",)
    assert report.reason_code_counts == (
        module.RatesFOMCDissentSignalReasonCodeCount(
            reason_code="rates_fomc_dissent_signal_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload(payload)


def test_non_default_thresholds_can_downgrade_dot_shift_to_watch() -> None:
    tuned_config = config(
        blocked_median_dot_shift_bps=d("70.000000"),
        blocked_signal_score=d("0.900000"),
    )
    report = digest(
        (
            observation(
                "threshold-case",
                dissent_count=d("0.000000"),
                hawkish_dissent_count=d("0.000000"),
                dovish_dissent_count=d("0.000000"),
                median_dot_shift_bps=d("60.000000"),
                dot_dispersion_bps=d("10.000000"),
                committee_disagreement_score=d("0.100000"),
            ),
        ),
        digest_config=tuned_config,
    )

    assert report.digest_status == "watch"
    assert report.blocked_signal_count == d("0.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.rows[0].signal_status == "watch"
    assert "rates_fomc_dot_shift_watch" in report.rows[0].reason_codes
    assert "rates_fomc_dot_shift_blocked" not in report.rows[0].reason_codes


def test_rejects_bad_public_types_datetimes_duplicates_future_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="dissent_count"):
        observation(dissent_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="committee_disagreement_score"):
        observation(committee_disagreement_score=d("1.100000"))

    with pytest.raises(ValueError, match="watch_dissent_count"):
        config(watch_dissent_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_dissent_count"):
        config(watch_dissent_count=d("3.000000"))

    with pytest.raises(ValueError, match="dissent_count must equal"):
        observation(
            dissent_count=d("2.000000"),
            hawkish_dissent_count=d("1.000000"),
            dovish_dissent_count=d("0.000000"),
        )

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.RatesFOMCDissentSignalDigestConfig,
        module.RatesFOMCDissentSignalObservation,
        module.RatesFOMCDissentSignalDigestRow,
        module.RatesFOMCDissentSignalReasonCodeCount,
        module.RatesFOMCDissentSignalDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_module_scope_is_pure_in_memory_without_live_or_durable_surfaces() -> None:
    module = api()
    source = inspect.getsource(module).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "database",
        "network",
        "exchange",
    ):
        assert forbidden not in source

    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/market_research_rates_fomc_dissent_signal_digest.py",
        ).read_text(),
    )
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
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

    report = digest((observation(),))
    assert is_dataclass(report)
