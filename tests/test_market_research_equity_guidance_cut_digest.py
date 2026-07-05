from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_equity_guidance_cut_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION,
    MarketResearchEquityGuidanceCutDigestConfig,
    MarketResearchEquityGuidanceCutDigestReasonCodeCount,
    MarketResearchEquityGuidanceCutDigestReport,
    MarketResearchEquityGuidanceCutDigestRow,
    MarketResearchEquityGuidanceCutObservation,
    build_market_research_equity_guidance_cut_digest,
    market_research_equity_guidance_cut_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _is_numeric_payload_key(key: str) -> bool:
    return (
        key.endswith("_count")
        or key.endswith("_seconds")
        or key.endswith("_ratio")
        or key.endswith("_eps")
        or key.endswith("_abs")
        or key.endswith("_confidence")
        or key == "price_reaction"
    )


def _assert_serialized_decimal(value: object) -> None:
    assert type(value) is str
    whole, dot, fractional = value.partition(".")
    assert dot == "."
    assert whole.lstrip("-").isdigit()
    assert len(fractional) == 6
    assert fractional.isdigit()


def _walk_payload_guard(value: object, key: str = "") -> None:
    forbidden_fragments = (
        "private_key",
        "secret_key",
        "api_key",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
        "auth",
    )
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            lowered_key = child_key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            if _is_numeric_payload_key(lowered_key):
                _assert_serialized_decimal(child_value)
            _walk_payload_guard(child_value, lowered_key)
    elif isinstance(value, list):
        for child_value in value:
            _walk_payload_guard(child_value, key)
    else:
        assert not isinstance(value, (Decimal, datetime, float))
        if isinstance(value, str):
            lowered_value = value.lower()
            assert not any(fragment in lowered_value for fragment in forbidden_fragments)


def _config(
    **overrides: object,
) -> MarketResearchEquityGuidanceCutDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_guidance_cut_ratio": d("0.050000"),
        "material_consensus_gap_ratio": d("0.030000"),
        "min_guidance_confidence": d("0.650000"),
        "material_price_reaction_abs": d("0.020000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchEquityGuidanceCutDigestConfig(**values)


def _observation(
    research_key: str = "research.nvda.guidance",
    *,
    condition_id: str = "condition_nvda_guidance",
    equity_symbol: str = "NVDA",
    guidance_event_key: str = "guidance.nvda.fy2026q2",
    guidance_reference: str = "public-earnings-release",
    observed_at: datetime = GENERATED_AT,
    acknowledged_at: datetime | None = GENERATED_AT,
    source_count: Decimal = d("3.000000"),
    previous_guidance_eps: Decimal = d("6.000000"),
    current_guidance_eps: Decimal = d("6.000000"),
    consensus_eps: Decimal = d("6.000000"),
    guidance_confidence: Decimal = d("0.900000"),
    price_reaction: Decimal = d("0.004000"),
    source_config_version: str = "equity-guidance-cut-source-v0",
) -> MarketResearchEquityGuidanceCutObservation:
    return MarketResearchEquityGuidanceCutObservation(
        research_key=research_key,
        condition_id=condition_id,
        equity_symbol=equity_symbol,
        guidance_event_key=guidance_event_key,
        guidance_reference=guidance_reference,
        observed_at=observed_at,
        acknowledged_at=acknowledged_at,
        source_count=source_count,
        previous_guidance_eps=previous_guidance_eps,
        current_guidance_eps=current_guidance_eps,
        consensus_eps=consensus_eps,
        guidance_confidence=guidance_confidence,
        price_reaction=price_reaction,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchEquityGuidanceCutObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchEquityGuidanceCutDigestConfig | None = None,
) -> MarketResearchEquityGuidanceCutDigestReport:
    return build_market_research_equity_guidance_cut_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_guidance_cut_digest_summarizes_cut_risk_and_sorts_deterministically() -> None:
    report = _report(
        _observation(
            "research.aapl.guidance",
            condition_id="condition_aapl_guidance",
            equity_symbol="AAPL",
            guidance_event_key="guidance.aapl.fy2026q3",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            acknowledged_at=GENERATED_AT - timedelta(minutes=20),
            source_count=d("1.000000"),
            previous_guidance_eps=d("5.000000"),
            current_guidance_eps=d("5.100000"),
            consensus_eps=d("5.090000"),
            guidance_confidence=d("0.800000"),
            price_reaction=d("0.005000"),
        ),
        _observation(
            "research.msft.guidance",
            condition_id="condition_msft_guidance",
            equity_symbol="MSFT",
            guidance_event_key="guidance.msft.fy2026q4",
            guidance_reference="private-board-packet",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            acknowledged_at=None,
            source_count=d("2.000000"),
            previous_guidance_eps=d("10.000000"),
            current_guidance_eps=d("8.500000"),
            consensus_eps=d("9.800000"),
            guidance_confidence=d("0.580000"),
            price_reaction=d("-0.040000"),
        ),
        _observation(
            observed_at=GENERATED_AT - timedelta(minutes=5),
            acknowledged_at=GENERATED_AT - timedelta(minutes=4),
        ),
        generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_equity_guidance_cut_digest"
    )
    assert report.event_count == d("3.000000")
    assert report.ready_event_count == d("1.000000")
    assert report.watch_event_count == d("1.000000")
    assert report.blocked_event_count == d("1.000000")
    assert report.material_guidance_cut_count == d("1.000000")
    assert report.negative_guidance_cut_count == d("1.000000")
    assert report.consensus_gap_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.low_confidence_count == d("1.000000")
    assert report.missing_acknowledgement_count == d("1.000000")
    assert report.slow_acknowledgement_count == d("0.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.price_reaction_pressure_count == d("1.000000")
    assert report.average_guidance_cut_ratio == d("0.050000")
    assert report.max_guidance_cut_ratio == d("0.150000")
    assert report.average_source_count == d("2.000000")
    assert report.average_guidance_confidence == d("0.760000")
    assert report.max_observation_age_seconds == d("9000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.equity_symbol, row.guidance_event_key) for row in report.rows) == (
        ("MSFT", "guidance.msft.fy2026q4"),
        ("AAPL", "guidance.aapl.fy2026q3"),
        ("NVDA", "guidance.nvda.fy2026q2"),
    )

    msft = report.rows[0]
    assert msft.digest_status == "blocked"
    assert msft.observation_age_seconds == d("9000.000000")
    assert msft.acknowledgement_lag_seconds is None
    assert msft.guidance_cut_abs == d("1.500000")
    assert msft.guidance_cut_ratio == d("0.150000")
    assert msft.consensus_gap_ratio == d("0.132653")
    assert msft.price_reaction_abs == d("0.040000")
    assert msft.redacted_guidance_reference == "sha256:4dfe3cbe5c9a"
    assert msft.reason_codes == (
        "market_research_equity_guidance_cut_digest_material_guidance_cut",
        "market_research_equity_guidance_cut_digest_negative_guidance_cut",
        "market_research_equity_guidance_cut_digest_consensus_gap",
        "market_research_equity_guidance_cut_digest_price_reaction_pressure",
        "market_research_equity_guidance_cut_digest_missing_acknowledgement",
        "market_research_equity_guidance_cut_digest_low_confidence",
        "market_research_equity_guidance_cut_digest_stale_observation",
    )

    aapl = report.rows[1]
    assert aapl.digest_status == "watch"
    assert aapl.observation_age_seconds == d("1800.000000")
    assert aapl.acknowledgement_lag_seconds == d("600.000000")
    assert aapl.guidance_cut_abs == d("0.000000")
    assert aapl.guidance_cut_ratio == d("0.000000")
    assert aapl.reason_codes == (
        "market_research_equity_guidance_cut_digest_thin_sources",
    )

    nvda = report.rows[2]
    assert nvda.digest_status == "ready"
    assert nvda.reason_codes == (
        "market_research_equity_guidance_cut_digest_ready",
    )

    assert report.reason_code_counts == (
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code=(
                "market_research_equity_guidance_cut_digest_"
                "material_guidance_cut"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code=(
                "market_research_equity_guidance_cut_digest_"
                "negative_guidance_cut"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_consensus_gap",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code=(
                "market_research_equity_guidance_cut_digest_"
                "price_reaction_pressure"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_thin_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code=(
                "market_research_equity_guidance_cut_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_ready",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_low_confidence",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code=(
                "market_research_equity_guidance_cut_digest_"
                "stale_observation"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == (
        "market_research_equity_guidance_cut_digest_material_guidance_cut",
        "market_research_equity_guidance_cut_digest_negative_guidance_cut",
        "market_research_equity_guidance_cut_digest_consensus_gap",
        "market_research_equity_guidance_cut_digest_price_reaction_pressure",
        "market_research_equity_guidance_cut_digest_thin_sources",
        "market_research_equity_guidance_cut_digest_missing_acknowledgement",
        "market_research_equity_guidance_cut_digest_low_confidence",
        "market_research_equity_guidance_cut_digest_stale_observation",
    )


def test_guidance_cut_digest_normalizes_timezones_and_source_versions() -> None:
    report = _report(
        _observation(
            "research.orcl.guidance",
            condition_id="condition_orcl_guidance",
            equity_symbol="ORCL",
            guidance_event_key="guidance.orcl.fy2026q1",
            observed_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
            acknowledged_at=datetime(
                2026,
                7,
                3,
                12,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            source_config_version="guidance-cut-source-b",
        ),
        generated_at=datetime(2026, 7, 3, 13, 0, tzinfo=timezone(timedelta(hours=-3))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
    assert report.rows[0].acknowledged_at == datetime(2026, 7, 3, 16, 45, tzinfo=UTC)
    assert report.rows[0].acknowledgement_lag_seconds == d("6300.000000")
    assert report.rows[0].reason_codes == (
        "market_research_equity_guidance_cut_digest_slow_acknowledgement",
    )
    assert report.digest_status == "watch"
    assert report.source_config_versions == (
        ("research.orcl.guidance", "guidance-cut-source-b"),
    )


def test_guidance_cut_digest_empty_input_is_blocked_and_payload_is_stable() -> None:
    report = _report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_equity_guidance_cut_digest"
    )
    assert report.event_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == (
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )
    assert report.reason_codes == (
        "market_research_equity_guidance_cut_digest_no_inputs",
    )

    payload = market_research_equity_guidance_cut_digest_payload(report)
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["event_count"] == "0.000000"
    assert payload["reason_code_counts"] == [
        {
            "reason_code": "market_research_equity_guidance_cut_digest_no_inputs",
            "count": "1.000000",
            "event_ratio": "0.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_guidance_cut_digest_payload_serializes_public_values_without_live_surfaces() -> None:
    report = _report(
        _observation(
            "research.msft.guidance",
            condition_id="condition_msft_guidance",
            equity_symbol="MSFT",
            guidance_event_key="guidance.msft.fy2026q4",
            guidance_reference="public-release?revision=1",
            observed_at=GENERATED_AT - timedelta(seconds=90, microseconds=1),
            acknowledged_at=GENERATED_AT - timedelta(seconds=30, microseconds=1),
            previous_guidance_eps=d("10.000000"),
            current_guidance_eps=d("8.500000"),
            consensus_eps=d("9.800000"),
            guidance_confidence=d("0.580000"),
            price_reaction=d("-0.040000"),
        ),
    )

    payload = market_research_equity_guidance_cut_digest_payload(report)

    assert payload["event_count"] == "1.000000"
    assert payload["average_guidance_cut_ratio"] == "0.150000"
    assert payload["rows"][0]["observation_age_seconds"] == "90.000001"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "60.000000"
    assert payload["rows"][0]["guidance_cut_abs"] == "1.500000"
    assert payload["rows"][0]["price_reaction"] == "-0.040000"
    assert payload["rows"][0]["redacted_guidance_reference"].startswith("sha256:")
    _walk_payload_guard(payload)


def test_guidance_cut_digest_payload_rejects_tampered_nested_public_values() -> None:
    report = _report(_observation())

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_equity_guidance_cut_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_equity_guidance_cut_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "guidance_confidence", d("0.9000001"))
    with pytest.raises(ValueError, match="six decimals"):
        market_research_equity_guidance_cut_digest_payload(report)


def test_guidance_cut_digest_validates_exact_types_flags_freezing_and_duplicates() -> None:
    assert MarketResearchEquityGuidanceCutDigestConfig.__dataclass_params__.frozen
    assert MarketResearchEquityGuidanceCutObservation.__dataclass_params__.frozen
    assert MarketResearchEquityGuidanceCutDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchEquityGuidanceCutDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchEquityGuidanceCutDigestReport.__dataclass_params__.frozen

    for public_dataclass in (
        MarketResearchEquityGuidanceCutDigestConfig,
        MarketResearchEquityGuidanceCutObservation,
        MarketResearchEquityGuidanceCutDigestRow,
        MarketResearchEquityGuidanceCutDigestReasonCodeCount,
        MarketResearchEquityGuidanceCutDigestReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Bad{public_dataclass.__name__}", (public_dataclass,), {})

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("bad-version"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=2)
    with pytest.raises(ValueError, match="guidance_confidence"):
        _observation(guidance_confidence=0.8)
    with pytest.raises(ValueError, match="material_guidance_cut_ratio"):
        _config(material_guidance_cut_ratio=_DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="research_key"):
        _observation(research_key=_StringSubclass("research.bad"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_equity_guidance_cut_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            observed_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        _observation(
            acknowledged_at=datetime(
                2026,
                7,
                3,
                16,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        _observation(guidance_reference="private-plan-secret")
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(research_key="research.dup"),
            _observation(research_key="research.dup"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_ready",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
            readonly=False,
        )
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_guidance_cut_digest_public_numeric_fields_are_decimal_only_and_consistent() -> None:
    report = _report(_observation())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_ratio")
                or field.name.endswith("_eps")
                or field.name.endswith("_abs")
                or field.name.endswith("_confidence")
                or field.name == "price_reaction"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_confidence")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert reason_count.paper_only is True
        assert reason_count.report_only is True
        assert reason_count.readonly is True
        assert type(reason_count.count) is Decimal
        assert type(reason_count.event_ratio) is Decimal

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchEquityGuidanceCutDigestReport)
    }
    assert MarketResearchEquityGuidanceCutDigestReport(**kwargs).digest_status == "ready"
    with pytest.raises(ValueError, match="event_count"):
        MarketResearchEquityGuidanceCutDigestReport(
            **{**kwargs, "event_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchEquityGuidanceCutDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchEquityGuidanceCutDigestReasonCodeCount(
                        reason_code=(
                            "market_research_equity_guidance_cut_digest_ready"
                        ),
                        count=d("2.000000"),
                        event_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code="market_research_equity_guidance_cut_digest_ready",
            count=d("0.000000"),
            event_ratio=d("0.000000"),
        )


def test_guidance_cut_digest_public_constructors_reject_nondeterministic_sequences() -> None:
    report = _report(
        _observation(
            "research.msft.guidance",
            condition_id="condition_msft_guidance",
            equity_symbol="MSFT",
            guidance_event_key="guidance.msft.fy2026q4",
            previous_guidance_eps=d("10.000000"),
            current_guidance_eps=d("8.500000"),
            consensus_eps=d("9.800000"),
            price_reaction=d("-0.040000"),
        ),
        _observation(
            "research.aapl.guidance",
            condition_id="condition_aapl_guidance",
            equity_symbol="AAPL",
            guidance_event_key="guidance.aapl.fy2026q3",
            source_count=d("1.000000"),
        ),
    )
    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchEquityGuidanceCutDigestReport)
    }

    with pytest.raises(ValueError, match="rows"):
        MarketResearchEquityGuidanceCutDigestReport(
            **{**kwargs, "rows": tuple(reversed(report.rows))},
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchEquityGuidanceCutDigestReport(
            **{
                **kwargs,
                "source_config_versions": tuple(
                    reversed(report.source_config_versions),
                ),
            },
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchEquityGuidanceCutDigestReport(
            **{
                **kwargs,
                "reason_code_counts": tuple(reversed(report.reason_code_counts)),
            },
        )
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchEquityGuidanceCutDigestReport(
            **{**kwargs, "reason_codes": tuple(reversed(report.reason_codes))},
        )


def test_guidance_cut_digest_module_scope_excludes_io_durable_store_and_execution_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_equity_guidance_cut_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "trading",
        "live trading",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "private_key",
        "secret_key",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "mutation",
        "auth",
        "supabase",
        "sqlite",
        "psycopg",
        "requests",
        "urllib",
        "socket",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {"open", "read", "write", "submit", "cancel"}

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "pathlib",
        "sqlite",
        "requests",
        "socket",
        "urllib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
