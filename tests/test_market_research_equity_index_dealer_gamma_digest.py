from __future__ import annotations

import ast
import dataclasses
from dataclasses import FrozenInstanceError, asdict, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_equity_index_dealer_gamma_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION,
    MarketResearchEquityIndexDealerGammaDigestConfig,
    MarketResearchEquityIndexDealerGammaInputRow,
    MarketResearchEquityIndexDealerGammaReasonCodeCount,
    MarketResearchEquityIndexDealerGammaReport,
    MarketResearchEquityIndexDealerGammaRow,
    build_market_research_equity_index_dealer_gamma_digest,
    market_research_equity_index_dealer_gamma_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEquityIndexDealerGammaDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION
        ),
        "max_surface_age_seconds": d("1800.000000"),
        "min_abs_net_gamma_exposure_usd": d("250000000.000000"),
        "max_zero_gamma_distance_pct": d("0.015000"),
        "high_put_call_skew_score": d("0.700000"),
        "min_source_count": d("2"),
        "max_acknowledgement_lag_seconds": d("900.000000"),
    }
    values.update(overrides)
    return MarketResearchEquityIndexDealerGammaDigestConfig(**values)


def input_row(
    research_key: str = "research.spx.gamma",
    *,
    condition_id: str = "condition_spx_gamma",
    index_symbol: str = "SPX",
    gamma_surface_key: str = "spx.weekly.gamma",
    source_reference: str = "public-options-surface",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3"),
    net_gamma_exposure_usd: Decimal = d("500000000.000000"),
    zero_gamma_distance_pct: Decimal = d("0.040000"),
    put_call_skew_score: Decimal = d("0.300000"),
    spot_move_pct: Decimal = d("0.004000"),
    contradiction_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEquityIndexDealerGammaInputRow:
    return MarketResearchEquityIndexDealerGammaInputRow(
        research_key=research_key,
        condition_id=condition_id,
        index_symbol=index_symbol,
        gamma_surface_key=gamma_surface_key,
        source_reference=source_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=10),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=5)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        net_gamma_exposure_usd=net_gamma_exposure_usd,
        zero_gamma_distance_pct=zero_gamma_distance_pct,
        put_call_skew_score=put_call_skew_score,
        spot_move_pct=spot_move_pct,
        contradiction_count=contradiction_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchEquityIndexDealerGammaInputRow, ...],
    *,
    cfg: MarketResearchEquityIndexDealerGammaDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEquityIndexDealerGammaReport:
    return build_market_research_equity_index_dealer_gamma_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_dealer_gamma_digest_scores_rows_redacts_refs_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.ndx.short_gamma",
                condition_id="condition_ndx_gamma",
                index_symbol="NDX",
                gamma_surface_key="ndx.weekly.gamma",
                source_reference="https://vendor.example/gamma?key=raw",
                observed_at=GENERATED_AT - timedelta(hours=2),
                acknowledged_at=None,
                source_count=d("1"),
                net_gamma_exposure_usd=d("-900000000.000000"),
                zero_gamma_distance_pct=d("0.006000"),
                put_call_skew_score=d("0.850000"),
                spot_move_pct=d("-0.025000"),
                contradiction_count=d("1"),
            ),
            input_row(
                "research.spx.long_gamma",
                condition_id="condition_spx_gamma",
                index_symbol="SPX",
                gamma_surface_key="spx.weekly.gamma",
                source_reference="public-options-surface",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                acknowledged_at=GENERATED_AT - timedelta(minutes=15),
                source_count=d("3"),
                net_gamma_exposure_usd=d("650000000.000000"),
                zero_gamma_distance_pct=d("0.050000"),
                put_call_skew_score=d("0.300000"),
                spot_move_pct=d("0.004000"),
            ),
            input_row(
                "research.rty.gamma_pin",
                condition_id="condition_rty_gamma",
                index_symbol="RTY",
                gamma_surface_key="rty.weekly.gamma",
                source_reference="public-russell-options-surface",
                observed_at=GENERATED_AT - timedelta(minutes=35),
                acknowledged_at=GENERATED_AT - timedelta(minutes=10),
                source_count=d("2"),
                net_gamma_exposure_usd=d("-300000000.000000"),
                zero_gamma_distance_pct=d("0.010000"),
                put_call_skew_score=d("0.720000"),
                spot_move_pct=d("-0.012000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_equity_index_dealer_gamma_digest"
    )
    assert summary.surface_count == d("3")
    assert summary.ready_surface_count == d("1")
    assert summary.watch_surface_count == d("1")
    assert summary.blocked_surface_count == d("1")
    assert summary.material_gamma_count == d("3")
    assert summary.short_gamma_count == d("2")
    assert summary.near_zero_gamma_count == d("2")
    assert summary.stale_surface_count == d("2")
    assert summary.thin_source_count == d("1")
    assert summary.missing_acknowledgement_count == d("1")
    assert summary.slow_acknowledgement_count == d("1")
    assert summary.elevated_skew_count == d("2")
    assert summary.contradiction_surface_count == d("1")
    assert summary.net_gamma_exposure_usd == d("-550000000.000000")
    assert summary.gross_gamma_exposure_usd == d("1850000000.000000")
    assert summary.max_gamma_abs_usd == d("900000000.000000")
    assert summary.average_zero_gamma_distance_pct == d("0.022000")
    assert summary.average_put_call_skew_score == d("0.623333")
    assert summary.max_surface_age_seconds == d("7200.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.index_symbol, row.gamma_surface_key) for row in summary.rows) == (
        ("NDX", "ndx.weekly.gamma"),
        ("RTY", "rty.weekly.gamma"),
        ("SPX", "spx.weekly.gamma"),
    )

    ndx = summary.rows[0]
    assert ndx.gamma_status == "blocked"
    assert ndx.surface_age_seconds == d("7200.000000")
    assert ndx.acknowledgement_lag_seconds is None
    assert ndx.gamma_abs_usd == d("900000000.000000")
    assert ndx.redacted_source_reference == "sha256:6e59d1ba20cd"
    assert ndx.reason_codes == (
        "market_research_equity_index_dealer_gamma_digest_material_gamma",
        "market_research_equity_index_dealer_gamma_digest_short_gamma",
        "market_research_equity_index_dealer_gamma_digest_near_zero_gamma",
        "market_research_equity_index_dealer_gamma_digest_stale_surface",
        "market_research_equity_index_dealer_gamma_digest_thin_sources",
        "market_research_equity_index_dealer_gamma_digest_missing_acknowledgement",
        "market_research_equity_index_dealer_gamma_digest_elevated_skew",
        "market_research_equity_index_dealer_gamma_digest_contradiction_present",
    )

    rty = summary.rows[1]
    assert rty.gamma_status == "watch"
    assert rty.surface_age_seconds == d("2100.000000")
    assert rty.acknowledgement_lag_seconds == d("1500.000000")
    assert rty.reason_codes == (
        "market_research_equity_index_dealer_gamma_digest_material_gamma",
        "market_research_equity_index_dealer_gamma_digest_short_gamma",
        "market_research_equity_index_dealer_gamma_digest_near_zero_gamma",
        "market_research_equity_index_dealer_gamma_digest_stale_surface",
        "market_research_equity_index_dealer_gamma_digest_slow_acknowledgement",
        "market_research_equity_index_dealer_gamma_digest_elevated_skew",
    )

    spx = summary.rows[2]
    assert spx.gamma_status == "ready"
    assert spx.surface_age_seconds == d("1200.000000")
    assert spx.acknowledgement_lag_seconds == d("300.000000")
    assert spx.reason_codes == (
        "market_research_equity_index_dealer_gamma_digest_ready",
        "market_research_equity_index_dealer_gamma_digest_material_gamma",
    )

    assert summary.reason_codes == (
        "market_research_equity_index_dealer_gamma_digest_material_gamma",
        "market_research_equity_index_dealer_gamma_digest_short_gamma",
        "market_research_equity_index_dealer_gamma_digest_near_zero_gamma",
        "market_research_equity_index_dealer_gamma_digest_stale_surface",
        "market_research_equity_index_dealer_gamma_digest_thin_sources",
        "market_research_equity_index_dealer_gamma_digest_missing_acknowledgement",
        "market_research_equity_index_dealer_gamma_digest_slow_acknowledgement",
        "market_research_equity_index_dealer_gamma_digest_elevated_skew",
        "market_research_equity_index_dealer_gamma_digest_contradiction_present",
    )
    assert summary.reason_code_counts == (
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_material_gamma",
            count=d("3"),
            surface_ratio=d("1.000000"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_short_gamma",
            count=d("2"),
            surface_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_near_zero_gamma",
            count=d("2"),
            surface_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_stale_surface",
            count=d("2"),
            surface_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_elevated_skew",
            count=d("2"),
            surface_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_thin_sources",
            count=d("1"),
            surface_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code=(
                "market_research_equity_index_dealer_gamma_digest_"
                "missing_acknowledgement"
            ),
            count=d("1"),
            surface_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code=(
                "market_research_equity_index_dealer_gamma_digest_"
                "slow_acknowledgement"
            ),
            count=d("1"),
            surface_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code=(
                "market_research_equity_index_dealer_gamma_digest_"
                "contradiction_present"
            ),
            count=d("1"),
            surface_ratio=d("0.333333"),
        ),
    )

    public = repr(asdict(summary)).lower()
    for token in ("key=raw", "vendor.example", "https://"):
        assert token not in public

    payload = market_research_equity_index_dealer_gamma_digest_payload(summary)
    payload_text = repr(payload).lower()
    assert "condition_ndx_gamma" not in payload_text
    assert "key=raw" not in payload_text
    assert payload["rows"][0]["redacted_condition_ref"] == "<redacted-condition-001>"
    assert payload["rows"][0]["redacted_source_reference"] == "sha256:6e59d1ba20cd"
    assert payload["rows"][0]["gamma_abs_usd"] == "900000000.000000"
    assert payload["surface_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    assert_public_numeric_fields_are_decimals(summary)
    assert_public_numeric_fields_are_decimals(summary.rows[0])


def test_empty_input_returns_blocked_report_only_digest() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_equity_index_dealer_gamma_digest"
    )
    assert summary.surface_count == ZERO
    assert summary.ready_surface_count == ZERO
    assert summary.watch_surface_count == ZERO
    assert summary.blocked_surface_count == ZERO
    assert summary.net_gamma_exposure_usd == ZERO
    assert summary.gross_gamma_exposure_usd == ZERO
    assert summary.average_zero_gamma_distance_pct == ZERO
    assert summary.average_put_call_skew_score == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_equity_index_dealer_gamma_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_no_inputs",
            count=d("1.000000"),
            surface_ratio=d("1.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_decimal_microsecond_timing_is_deterministic() -> None:
    summary = report(
        (
            input_row(
                observed_at=datetime(2026, 7, 4, 15, 59, 57, 1, tzinfo=UTC),
                acknowledged_at=datetime(2026, 7, 4, 15, 59, 59, 999999, tzinfo=UTC),
            ),
        ),
        generated_at=datetime(2026, 7, 4, 16, 0, 0, 234567, tzinfo=UTC),
    )

    assert summary.max_surface_age_seconds == d("3.234566")
    assert summary.rows[0].surface_age_seconds == d("3.234566")
    assert summary.rows[0].acknowledgement_lag_seconds == d("2.999998")


def test_validation_guards_decimals_datetimes_flags_and_frozen_instances() -> None:
    summary = report((input_row(),))

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].gamma_abs_usd = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 4, 15, 45))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            (input_row(),),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="zero_gamma_distance_pct"):
        input_row(zero_gamma_distance_pct=d("-0.010000"))
    with pytest.raises(ValueError, match="put_call_skew_score"):
        input_row(put_call_skew_score=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report((input_row(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="acknowledged_at must not precede observed_at"):
        report(
            (
                input_row(
                    observed_at=GENERATED_AT - timedelta(minutes=10),
                    acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="input row readonly must be True"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        build_market_research_equity_index_dealer_gamma_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    payload = market_research_equity_index_dealer_gamma_digest_payload(summary)
    assert_no_floats(payload)


def test_row_reason_count_and_report_dataclasses_validate_consistency() -> None:
    ready = report((input_row(),))

    with pytest.raises(ValueError, match="ready rows require ready status"):
        MarketResearchEquityIndexDealerGammaRow(
            research_key="research.bad",
            condition_id="condition_bad",
            index_symbol="SPX",
            gamma_surface_key="spx.bad",
            gamma_status="watch",
            observed_at=GENERATED_AT,
            acknowledged_at=GENERATED_AT,
            surface_age_seconds=d("1.000000"),
            acknowledgement_lag_seconds=d("1.000000"),
            source_count=d("2"),
            net_gamma_exposure_usd=d("1.000000"),
            gamma_abs_usd=d("1.000000"),
            zero_gamma_distance_pct=d("0.100000"),
            put_call_skew_score=d("0.100000"),
            spot_move_pct=d("0.001000"),
            contradiction_count=ZERO,
            redacted_source_reference="public",
            reason_codes=(
                "market_research_equity_index_dealer_gamma_digest_ready",
            ),
        )

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code="market_research_equity_index_dealer_gamma_digest_ready",
            count=ZERO,
            surface_ratio=ZERO,
        )

    with pytest.raises(ValueError, match="surface_count must match rows"):
        MarketResearchEquityIndexDealerGammaReport(
            generated_at=ready.generated_at,
            config_version=ready.config_version,
            digest_status=ready.digest_status,
            recommended_next_step=ready.recommended_next_step,
            surface_count=ZERO,
            ready_surface_count=ready.ready_surface_count,
            watch_surface_count=ready.watch_surface_count,
            blocked_surface_count=ready.blocked_surface_count,
            material_gamma_count=ready.material_gamma_count,
            short_gamma_count=ready.short_gamma_count,
            near_zero_gamma_count=ready.near_zero_gamma_count,
            stale_surface_count=ready.stale_surface_count,
            thin_source_count=ready.thin_source_count,
            missing_acknowledgement_count=ready.missing_acknowledgement_count,
            slow_acknowledgement_count=ready.slow_acknowledgement_count,
            elevated_skew_count=ready.elevated_skew_count,
            contradiction_surface_count=ready.contradiction_surface_count,
            net_gamma_exposure_usd=ready.net_gamma_exposure_usd,
            gross_gamma_exposure_usd=ready.gross_gamma_exposure_usd,
            max_gamma_abs_usd=ready.max_gamma_abs_usd,
            average_zero_gamma_distance_pct=ready.average_zero_gamma_distance_pct,
            average_put_call_skew_score=ready.average_put_call_skew_score,
            max_surface_age_seconds=ready.max_surface_age_seconds,
            rows=ready.rows,
            reason_code_counts=ready.reason_code_counts,
            reason_codes=ready.reason_codes,
        )


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_equity_index_dealer_gamma_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    assert "persist" not in source.lower()
    assert "database" not in source.lower()
    assert "advice" not in source.lower()


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_floats(nested)
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_floats(nested)


def assert_public_numeric_fields_are_decimals(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "distance",
        "exposure",
        "lag",
        "move",
        "pct",
        "ratio",
        "score",
        "skew",
        "usd",
    )
    for field in dataclasses.fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value: Any = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
