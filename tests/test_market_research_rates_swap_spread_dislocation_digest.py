from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_rates_swap_spread_dislocation_digest import (
    DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION,
    MarketResearchRatesSwapSpreadDislocationDigestConfig,
    MarketResearchRatesSwapSpreadDislocationDigestReport,
    MarketResearchRatesSwapSpreadDislocationDigestRow,
    MarketResearchRatesSwapSpreadDislocationObservation,
    MarketResearchRatesSwapSpreadDislocationReasonCodeCount,
    build_market_research_rates_swap_spread_dislocation_digest,
    market_research_rates_swap_spread_dislocation_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchRatesSwapSpreadDislocationDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "watch_swap_spread_bps_abs": d("15.000000"),
        "blocked_swap_spread_bps_abs": d("30.000000"),
        "spread_change_shock_bps_abs": d("10.000000"),
        "min_dislocation_persistence_hours": d("4.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchRatesSwapSpreadDislocationDigestConfig(**values)


def observation(
    research_id: str = "rates.swap-spread.5y.pass",
    *,
    instrument_id: str = "usd-5y-swap-spread",
    curve_tenor: str = "5y",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    swap_spread_bps: Decimal = d("4.000000"),
    prior_swap_spread_bps: Decimal = d("3.000000"),
    dislocation_persistence_hours: Decimal = d("1.000000"),
    confidence: Decimal = d("0.950000"),
    upstream_reason_codes: tuple[str, ...] = ("rates_desk_snapshot",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchRatesSwapSpreadDislocationObservation:
    return MarketResearchRatesSwapSpreadDislocationObservation(
        research_id=research_id,
        instrument_id=instrument_id,
        curve_tenor=curve_tenor,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        source_count=source_count,
        swap_spread_bps=swap_spread_bps,
        prior_swap_spread_bps=prior_swap_spread_bps,
        dislocation_persistence_hours=dislocation_persistence_hours,
        confidence=confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    cfg: MarketResearchRatesSwapSpreadDislocationDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchRatesSwapSpreadDislocationDigestReport:
    return build_market_research_rates_swap_spread_dislocation_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_payload(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_payload(child))
    return (value,)


def test_empty_input_returns_blocked_report_only_digest() -> None:
    digest_report = report(
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_rates_swap_spread_dislocation_screening"
    )
    assert digest_report.input_count == ZERO
    assert digest_report.row_count == ZERO
    assert digest_report.blocked_count == ZERO
    assert digest_report.watch_count == ZERO
    assert digest_report.pass_count == ZERO
    assert digest_report.spread_dislocation_count == ZERO
    assert digest_report.spread_shock_count == ZERO
    assert digest_report.persistent_dislocation_count == ZERO
    assert digest_report.data_quality_gap_count == ZERO
    assert digest_report.average_swap_spread_bps == ZERO
    assert digest_report.average_absolute_swap_spread_bps == ZERO
    assert digest_report.max_absolute_swap_spread_bps == ZERO
    assert digest_report.average_dislocation_persistence_hours == ZERO
    assert digest_report.rows == ()
    assert digest_report.reason_code_counts == ()
    assert digest_report.reason_codes == (
        "rates_swap_spread_dislocation_digest_no_inputs",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_swap_spread_dislocation_classification_sorts_and_counts() -> None:
    digest_report = report(
        observation(
            "rates.swap-spread.10y.blocked",
            instrument_id="usd-10y-swap-spread",
            curve_tenor="10y",
            observed_at=GENERATED_AT - timedelta(hours=3),
            source_count=d("1.000000"),
            swap_spread_bps=d("-38.000000"),
            prior_swap_spread_bps=d("-22.000000"),
            dislocation_persistence_hours=d("8.000000"),
            confidence=d("0.650000"),
        ),
        observation(
            "rates.swap-spread.2y.watch",
            instrument_id="usd-2y-swap-spread",
            curve_tenor="2y",
            swap_spread_bps=d("18.000000"),
            prior_swap_spread_bps=d("8.000000"),
            dislocation_persistence_hours=d("5.000000"),
            confidence=d("0.900000"),
        ),
        observation(),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.spread_dislocation_count == d("2.000000")
    assert digest_report.spread_shock_count == d("2.000000")
    assert digest_report.persistent_dislocation_count == d("2.000000")
    assert digest_report.data_quality_gap_count == d("1.000000")
    assert digest_report.average_swap_spread_bps == d("-5.333333")
    assert digest_report.average_absolute_swap_spread_bps == d("20.000000")
    assert digest_report.max_absolute_swap_spread_bps == d("38.000000")
    assert digest_report.average_dislocation_persistence_hours == d("4.666667")
    assert tuple(row.curve_tenor for row in digest_report.rows) == ("10y", "2y", "5y")
    assert digest_report.reason_codes == (
        "rates_swap_spread_dislocation_digest_blocked_spread_present",
        "rates_swap_spread_dislocation_digest_watch_spread_present",
        "rates_swap_spread_dislocation_digest_spread_shock_present",
        "rates_swap_spread_dislocation_digest_persistent_present",
        "rates_swap_spread_dislocation_digest_data_quality_gap_present",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.dislocation_status == "blocked"
    assert blocked.dislocation_direction == "negative_inversion"
    assert blocked.observation_age_seconds == d("10800.000000")
    assert blocked.absolute_swap_spread_bps == d("38.000000")
    assert blocked.spread_change_bps == d("-16.000000")
    assert blocked.absolute_spread_change_bps == d("16.000000")
    assert blocked.reason_codes == (
        "rates_swap_spread_dislocation_digest_blocked_spread",
        "rates_swap_spread_dislocation_digest_spread_shock",
        "rates_swap_spread_dislocation_digest_persistent",
        "rates_swap_spread_dislocation_digest_thin_sources",
        "rates_swap_spread_dislocation_digest_stale_observation",
        "rates_swap_spread_dislocation_digest_confidence_gap",
    )
    assert watched.dislocation_status == "watch"
    assert watched.dislocation_direction == "positive_widening"
    assert watched.reason_codes == (
        "rates_swap_spread_dislocation_digest_watch_spread",
        "rates_swap_spread_dislocation_digest_spread_shock",
        "rates_swap_spread_dislocation_digest_persistent",
    )
    assert passed.dislocation_status == "pass"
    assert passed.dislocation_direction == "neutral"
    assert passed.reason_codes == ("rates_swap_spread_dislocation_digest_pass",)

    assert digest_report.reason_code_counts == (
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_blocked_spread_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_watch_spread_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_spread_shock_present",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_persistent_present",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_data_quality_gap_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )


def test_non_default_thresholds_can_clear_moderate_dislocation() -> None:
    loose_config = config(
        watch_swap_spread_bps_abs=d("25.000000"),
        blocked_swap_spread_bps_abs=d("50.000000"),
        spread_change_shock_bps_abs=d("20.000000"),
        min_dislocation_persistence_hours=d("10.000000"),
    )

    digest_report = report(
        observation(
            swap_spread_bps=d("18.000000"),
            prior_swap_spread_bps=d("8.000000"),
            dislocation_persistence_hours=d("5.000000"),
        ),
        cfg=loose_config,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_rates_swap_spread_dislocation_screening"
    )
    assert digest_report.rows[0].dislocation_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "rates_swap_spread_dislocation_digest_pass",
    )
    assert digest_report.reason_codes == (
        "rates_swap_spread_dislocation_digest_clear",
    )
    assert digest_report.reason_code_counts == (
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_clear",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_validation_rejects_bad_inputs_subclasses_and_hard_flag_tampering() -> None:
    with pytest.raises(ValueError, match="swap_spread_bps must be a Decimal"):
        observation(swap_spread_bps=_DecimalSubclass("4.000000"))

    with pytest.raises(ValueError, match="source_count must be an integer count"):
        observation(source_count=d("1.500000"))

    with pytest.raises(TypeError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["rates_desk_snapshot"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 6, 13, 0))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_market_research_rates_swap_spread_dislocation_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 14, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")

    with pytest.raises(ValueError, match="duplicate research_id"):
        report(observation("rates.dupe"), observation("rates.dupe"))

    with pytest.raises(ValueError, match="watch_swap_spread_bps_abs"):
        config(
            watch_swap_spread_bps_abs=d("60.000000"),
            blocked_swap_spread_bps_abs=d("50.000000"),
        )

    with pytest.raises(ValueError, match="config must be exactly"):
        build_market_research_rates_swap_spread_dislocation_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError):
        class BadConfig(MarketResearchRatesSwapSpreadDislocationDigestConfig):
            pass

    with pytest.raises(ValueError, match="curve_tenor must be a string"):
        observation(curve_tenor=_StringSubclass("5y"))

    with pytest.raises(ValueError, match="observation report_only must be True"):
        observation(report_only=False)

    digest_report = report(observation("rates.flags"))
    with pytest.raises(FrozenInstanceError):
        digest_report.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(digest_report, readonly=False)


def test_public_records_reject_inconsistent_counts_and_rows() -> None:
    digest_report = report(
        observation(
            "rates.swap-spread.10y.blocked",
            instrument_id="usd-10y-swap-spread",
            curve_tenor="10y",
            source_count=d("1.000000"),
            swap_spread_bps=d("-38.000000"),
            prior_swap_spread_bps=d("-22.000000"),
            dislocation_persistence_hours=d("8.000000"),
            confidence=d("0.650000"),
        ),
    )

    with pytest.raises(ValueError, match="absolute_swap_spread_bps must match"):
        replace(digest_report.rows[0], absolute_swap_spread_bps=d("999.000000"))

    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            digest_report.rows[0],
            reason_codes=("rates_swap_spread_dislocation_digest_pass",),
        )

    with pytest.raises(ValueError, match="row_count must match rows"):
        replace(digest_report, row_count=d("2.000000"))

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_clear",
            count=ZERO,
            row_ratio=ZERO,
        )

    with pytest.raises(ValueError, match="count must be an integer count"):
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code="rates_swap_spread_dislocation_digest_clear",
            count=d("1.500000"),
            row_ratio=d("0.500000"),
        )

    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(
            digest_report,
            reason_code_counts=(
                MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
                    reason_code=(
                        "rates_swap_spread_dislocation_digest_blocked_spread_present"
                    ),
                    count=d("2.000000"),
                    row_ratio=d("1.000000"),
                ),
            ),
        )


def test_payload_serializes_six_decimal_strings_and_revalidates_nested_records() -> None:
    digest_report = report(observation("rates.payload"))
    payload = market_research_rates_swap_spread_dislocation_digest_payload(digest_report)

    assert payload["generated_at"] == "2026-07-06T14:00:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["swap_spread_bps"] == "4.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T13:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    walked = walk_payload(payload)
    assert not any(isinstance(item, Decimal) for item in walked)
    assert not any(isinstance(item, datetime) for item in walked)
    assert not any(isinstance(item, float) for item in walked)
    assert all(
        item.count(".") == 1 and len(item.rsplit(".", 1)[1]) == 6
        for item in walked
        if isinstance(item, str) and item.replace("-", "", 1).replace(".", "", 1).isdigit()
    )

    tampered_report = report(observation("rates.tampered.mapping"))
    row_payload = market_research_rates_swap_spread_dislocation_digest_payload(
        tampered_report,
    )["rows"][0]
    object.__setattr__(tampered_report, "rows", (row_payload,))
    with pytest.raises(ValueError, match="rows"):
        market_research_rates_swap_spread_dislocation_digest_payload(tampered_report)

    tampered_report = report(observation("rates.tampered.scale"))
    object.__setattr__(tampered_report.rows[0], "swap_spread_bps", d("4.0000000"))
    with pytest.raises(ValueError, match="six decimal"):
        market_research_rates_swap_spread_dislocation_digest_payload(tampered_report)

    tampered_report = report(observation("rates.tampered.timezone"))
    object.__setattr__(
        tampered_report.rows[0],
        "observed_at",
        datetime(2026, 7, 6, 9, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC"):
        market_research_rates_swap_spread_dislocation_digest_payload(tampered_report)


def test_module_contract_has_no_live_io_or_forbidden_public_surface() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_rates_swap_spread_dislocation_digest.py",
    )
    source = module_path.read_text()
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.ClassDef) and node.name.startswith("MarketResearch"):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target,
                    ast.Name,
                ):
                    assert statement.target.id not in {
                        "market_slug",
                        "question",
                        "payload_json",
                    }

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "asdict",
        "market_slug",
        "question",
        "payload_json",
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()

    digest_report = report(observation("rates.public-records"))
    public_records: tuple[Any, ...] = (
        config(),
        observation("rates.public-observation"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )
    for public_record in public_records:
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name
            if isinstance(field_value, tuple):
                assert type(field_value) is tuple, field.name
