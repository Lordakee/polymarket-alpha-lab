from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_ppi_final_demand_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchPpiFinalDemandSurpriseDigestConfig,
    MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount,
    MarketResearchPpiFinalDemandSurpriseDigestReport,
    MarketResearchPpiFinalDemandSurpriseDigestRow,
    MarketResearchPpiFinalDemandSurpriseDigestSignal,
    build_market_research_ppi_final_demand_surprise_digest,
    market_research_ppi_final_demand_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchPpiFinalDemandSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_release_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.100000"),
        "high_revision_threshold": d("0.080000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchPpiFinalDemandSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_ppi_final_demand",
    *,
    research_id: str = "research.ppi.final_demand",
    release_id: str = "ppi.final_demand.latest",
    ppi_series_id: str = "ppi.final_demand.mom",
    public_source_reference: str = "public-bls-ppi-release",
    observed_at: datetime | None = None,
    expected_final_demand_ppi: Decimal = d("0.200000"),
    actual_final_demand_ppi: Decimal = d("0.300000"),
    prior_final_demand_ppi: Decimal = d("0.100000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.020000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "ppi-final-demand-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPpiFinalDemandSurpriseDigestSignal:
    return MarketResearchPpiFinalDemandSurpriseDigestSignal(
        condition_id=condition_id,
        research_id=research_id,
        release_id=release_id,
        ppi_series_id=ppi_series_id,
        public_source_reference=public_source_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=45),
        expected_final_demand_ppi=expected_final_demand_ppi,
        actual_final_demand_ppi=actual_final_demand_ppi,
        prior_final_demand_ppi=prior_final_demand_ppi,
        source_count=source_count,
        revision_ratio=revision_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestSignal, ...],
    *,
    cfg: MarketResearchPpiFinalDemandSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPpiFinalDemandSurpriseDigestReport:
    return build_market_research_ppi_final_demand_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _assert_public_numeric_fields_are_exact_six_decimal_decimals(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_seconds",
                "_threshold",
                "_confidence",
                "_factor",
                "_ppi",
                "_delta",
            ),
        ):
            assert type(value) is Decimal, (field.name, value, type(value))
            assert value.as_tuple().exponent == -6, (field.name, value)


def _assert_payload_has_no_decimal_datetime_or_float(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_payload_has_no_decimal_datetime_or_float(child)
    elif isinstance(value, list):
        for child in value:
            _assert_payload_has_no_decimal_datetime_or_float(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))


def _assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def test_ppi_final_demand_surprise_digest_reduces_report_only_rows() -> None:
    summary = report(
        (
            signal(
                "condition_ready",
                release_id="ppi.final_demand.ready",
                public_source_reference="public-ppi-ready-release",
                observed_at=(GENERATED_AT - timedelta(minutes=45)).astimezone(
                    timezone(timedelta(hours=2)),
                ),
                expected_final_demand_ppi=d("0.200000"),
                actual_final_demand_ppi=d("0.240000"),
                prior_final_demand_ppi=d("0.180000"),
            ),
            signal(
                "condition_watch",
                release_id="ppi.final_demand.watch",
                public_source_reference="https://vendor.example/ppi?token=secret-123",
                observed_at=GENERATED_AT - timedelta(minutes=80),
                expected_final_demand_ppi=d("0.100000"),
                actual_final_demand_ppi=d("0.280000"),
                prior_final_demand_ppi=d("0.120000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.020000"),
                confirmation_ratio=d("0.620000"),
                base_confidence=d("0.850000"),
                signal_config_version="ppi-final-demand-watch-v0",
            ),
            signal(
                "condition_blocked",
                release_id="ppi.final_demand.blocked",
                public_source_reference="private-ppi-feed",
                observed_at=GENERATED_AT - timedelta(hours=5),
                expected_final_demand_ppi=d("0.300000"),
                actual_final_demand_ppi=d("-0.050000"),
                prior_final_demand_ppi=d("0.180000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.110000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.700000"),
                signal_config_version="ppi-final-demand-blocked-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchPpiFinalDemandSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ppi_final_demand_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_release_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("2.000000")
    assert summary.average_abs_surprise_delta == d("0.190000")
    assert summary.max_abs_surprise_delta == d("0.350000")
    assert summary.max_observed_release_age_seconds == d("18000.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.digest_status, row.release_id) for row in summary.rows) == (
        ("blocked", "ppi.final_demand.blocked"),
        ("watch", "ppi.final_demand.watch"),
        ("ready", "ppi.final_demand.ready"),
    )

    blocked = summary.rows[0]
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=5)
    assert blocked.observed_at.tzinfo is UTC
    assert blocked.release_age_seconds == d("18000.000000")
    assert blocked.surprise_delta == d("-0.350000")
    assert blocked.abs_surprise_delta == d("0.350000")
    assert blocked.prior_revision_delta == d("-0.230000")
    assert blocked.confidence_decay_factor == d("0.400000")
    assert blocked.final_confidence == d("0.280000")
    assert blocked.redacted_public_source_reference.startswith("sha256:")
    assert blocked.reason_codes == (
        "market_research_ppi_final_demand_surprise_digest_material_surprise",
        "market_research_ppi_final_demand_surprise_digest_confirmation_gap",
        "market_research_ppi_final_demand_surprise_digest_stale_release",
        "market_research_ppi_final_demand_surprise_digest_thin_sources",
        "market_research_ppi_final_demand_surprise_digest_high_revision",
    )

    watched = summary.rows[1]
    assert watched.release_age_seconds == d("4800.000000")
    assert watched.surprise_delta == d("0.180000")
    assert watched.abs_surprise_delta == d("0.180000")
    assert watched.prior_revision_delta == d("0.160000")
    assert watched.confidence_decay_factor == d("0.800000")
    assert watched.final_confidence == d("0.680000")
    assert watched.redacted_public_source_reference.startswith("sha256:")
    assert watched.reason_codes == (
        "market_research_ppi_final_demand_surprise_digest_material_surprise",
        "market_research_ppi_final_demand_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.observed_at == GENERATED_AT - timedelta(minutes=45)
    assert ready.surprise_delta == d("0.040000")
    assert ready.abs_surprise_delta == d("0.040000")
    assert ready.confidence_decay_factor == d("1.000000")
    assert ready.final_confidence == d("0.900000")
    assert ready.redacted_public_source_reference == "public-ppi-ready-release"
    assert ready.reason_codes == (
        "market_research_ppi_final_demand_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_stale_release",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )

    public_repr = repr(summary).lower()
    for forbidden in ("secret-123", "vendor.example", "token=", "private-ppi-feed"):
        assert forbidden not in public_repr

    for instance in (
        config(),
        signal(),
        summary,
        summary.rows[0],
        summary.reason_code_counts[0],
    ):
        _assert_public_numeric_fields_are_exact_six_decimal_decimals(instance)


def test_ppi_final_demand_empty_inputs_block_with_missing_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ppi_final_demand_surprise_digest"
    )
    assert summary.signal_count == d("0.000000")
    assert summary.ready_signal_count == d("0.000000")
    assert summary.watch_signal_count == d("0.000000")
    assert summary.blocked_signal_count == d("0.000000")
    assert summary.rows == ()
    assert summary.average_abs_surprise_delta == d("0.000000")
    assert summary.max_abs_surprise_delta == d("0.000000")
    assert summary.max_observed_release_age_seconds == d("0.000000")
    assert summary.reason_codes == (
        "market_research_ppi_final_demand_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ppi_final_demand_payload_serializes_six_decimal_strings() -> None:
    summary = report((signal(),))
    payload = market_research_ppi_final_demand_surprise_digest_payload(summary)

    json.dumps(payload, sort_keys=True)
    assert payload == market_research_ppi_final_demand_surprise_digest_payload(summary)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["average_abs_surprise_delta"] == "0.100000"
    assert payload["rows"][0]["actual_final_demand_ppi"] == "0.300000"  # type: ignore[index]
    assert payload["reason_code_counts"][0]["count"] == "1.000000"  # type: ignore[index]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_payload_has_no_decimal_datetime_or_float(payload)
    _assert_six_decimal_string(payload["signal_count"])
    _assert_six_decimal_string(payload["rows"][0]["actual_final_demand_ppi"])  # type: ignore[index]

    with pytest.raises(ValueError, match="report"):
        market_research_ppi_final_demand_surprise_digest_payload(object())  # type: ignore[arg-type]


def test_ppi_final_demand_rejects_false_flags_decimal_subclasses_and_bad_datetimes() -> None:
    summary = report((signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.final_confidence = d("0.1")  # type: ignore[misc]

    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: signal(paper_only=False),
        lambda: signal(report_only=False),
        lambda: signal(readonly=False),
        lambda: replace(row, paper_only=False),
        lambda: replace(row, report_only=False),
        lambda: replace(row, readonly=False),
        lambda: replace(reason_count, paper_only=False),
        lambda: replace(reason_count, report_only=False),
        lambda: replace(reason_count, readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    )
    for make_invalid in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_invalid()

    with pytest.raises(TypeError, match="Decimal"):
        signal(actual_final_demand_ppi=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Decimal"):
        signal(actual_final_demand_ppi=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 3, 14, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_count"):
        signal(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="base_confidence"):
        signal(base_confidence=d("1.000001"))


def test_ppi_final_demand_public_constructors_reject_noncanonical_sequences() -> None:
    summary = report(
        (
            signal("condition_ready", release_id="z.ready.ppi"),
            signal(
                "condition_watch",
                release_id="m.watch.ppi",
                actual_final_demand_ppi=d("0.500000"),
                confirmation_ratio=d("0.500000"),
            ),
            signal(
                "condition_blocked",
                release_id="a.blocked.ppi",
                source_count=d("1.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=(summary.rows[2], summary.rows[0], summary.rows[1]))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            summary.rows[1],
            reason_codes=(
                "market_research_ppi_final_demand_surprise_digest_confirmation_gap",
                "market_research_ppi_final_demand_surprise_digest_material_surprise",
            ),
        )

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            summary,
            reason_code_counts=(
                MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
                    reason_code=(
                        "market_research_ppi_final_demand_surprise_digest_no_inputs"
                    ),
                    count=d("1.000000"),
                    signal_ratio=d("0.000000"),
                ),
            ),
            reason_codes=("market_research_ppi_final_demand_surprise_digest_no_inputs",),
        )
    with pytest.raises(ValueError, match="config_version"):
        replace(summary, config_version="market-research-ppi-final-demand-surprise-digest-v1")
    with pytest.raises(ValueError, match="count"):
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
            reason_code="market_research_ppi_final_demand_surprise_digest_ready",
            count=d("1.500000"),
            signal_ratio=d("1.000000"),
        )


def test_ppi_final_demand_rejects_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):
        class ConfigSubclass(MarketResearchPpiFinalDemandSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class SignalSubclass(MarketResearchPpiFinalDemandSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class RowSubclass(MarketResearchPpiFinalDemandSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReasonCountSubclass(
            MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReportSubclass(MarketResearchPpiFinalDemandSurpriseDigestReport):
            pass


def test_ppi_final_demand_module_has_no_live_durable_or_float_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_ppi_final_demand_surprise_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "ccxt",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
        "float",
    }
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float

    lowered = source.lower()
    for forbidden_fragment in (
        "api_key",
        "auth",
        "broker",
        "cancel_order",
        "database",
        "durable",
        "exchange",
        "live_trading",
        "order_id",
        "place_order",
        "private_key",
        "replace_order",
        "submit_order",
        "wallet",
    ):
        assert forbidden_fragment not in lowered
