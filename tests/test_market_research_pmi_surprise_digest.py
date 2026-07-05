from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_pmi_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchPmiSurpriseDigestConfig,
    MarketResearchPmiSurpriseDigestReasonCodeCount,
    MarketResearchPmiSurpriseDigestReport,
    MarketResearchPmiSurpriseDigestRow,
    MarketResearchPmiSurpriseDigestSignal,
    build_market_research_pmi_surprise_digest,
    market_research_pmi_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchPmiSurpriseDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION,
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.200000"),
        "max_revision_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "stale_confidence_decay": d("0.200000"),
        "thin_source_confidence_decay": d("0.150000"),
        "revision_confidence_decay": d("0.100000"),
        "confirmation_confidence_decay": d("0.200000"),
    }
    values.update(overrides)
    return MarketResearchPmiSurpriseDigestConfig(**values)


def signal(
    research_key: str = "research.pmi.ism.manufacturing",
    *,
    condition_id: str = "condition_pmi_manufacturing",
    release_key: str = "ism.manufacturing.pmi",
    pmi_family: str = "manufacturing",
    public_signal_reference: str = "ism-public-release",
    observed_at: datetime | None = None,
    expected_pmi: Decimal = d("50.800000"),
    actual_pmi: Decimal = d("51.000000"),
    surprise_score: Decimal = d("0.040000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.020000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "pmi-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPmiSurpriseDigestSignal:
    return MarketResearchPmiSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        pmi_family=pmi_family,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=45),
        expected_pmi=expected_pmi,
        actual_pmi=actual_pmi,
        surprise_score=surprise_score,
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
    rows: tuple[MarketResearchPmiSurpriseDigestSignal, ...],
    *,
    cfg: MarketResearchPmiSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPmiSurpriseDigestReport:
    return build_market_research_pmi_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _assert_public_numeric_fields_are_exact_decimals(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_seconds",
                "_threshold",
                "_decay",
                "_confidence",
                "_pmi",
                "_delta",
            )
        ):
            assert type(value) is Decimal, (field.name, value, type(value))


def _walk_payload(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _walk_payload(child)
    elif isinstance(value, list):
        for child in value:
            _walk_payload(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))


def _assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def test_pmi_surprise_digest_reduces_rows_with_utc_normalization_and_deterministic_sorting() -> None:
    summary = report(
        (
            signal(
                "research.pmi.ism.manufacturing",
                condition_id="condition_ready",
                release_key="ism.manufacturing.pmi",
                pmi_family="manufacturing",
                public_signal_reference="ism-public-release",
                observed_at=(GENERATED_AT - timedelta(minutes=45)).astimezone(
                    timezone(timedelta(hours=2)),
                ),
            ),
            signal(
                "research.pmi.spglobal.services",
                condition_id="condition_watch",
                release_key="spglobal.services.pmi",
                pmi_family="services",
                public_signal_reference="https://vendor.example/pmi?token=secret-123",
                observed_at=GENERATED_AT - timedelta(minutes=80),
                expected_pmi=d("51.200000"),
                actual_pmi=d("49.900000"),
                surprise_score=d("0.260000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.350000"),
                confirmation_ratio=d("0.700000"),
                base_confidence=d("0.850000"),
                signal_config_version="pmi-signal-services-v0",
            ),
            signal(
                "research.pmi.private.composite",
                condition_id="condition_blocked",
                release_key="private.composite.pmi",
                pmi_family="composite",
                public_signal_reference="private-pmi-feed",
                observed_at=GENERATED_AT - timedelta(hours=5),
                expected_pmi=d("50.500000"),
                actual_pmi=d("47.400000"),
                surprise_score=d("0.620000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.100000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.700000"),
                signal_config_version="pmi-signal-private-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchPmiSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_pmi_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("1.000000")
    assert summary.average_surprise_score == d("0.306667")
    assert summary.average_final_confidence == d("0.600000")
    assert summary.max_observed_signal_age_seconds == d("18000.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.digest_status, row.release_key) for row in summary.rows) == (
        ("blocked", "private.composite.pmi"),
        ("watch", "spglobal.services.pmi"),
        ("ready", "ism.manufacturing.pmi"),
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, MarketResearchPmiSurpriseDigestRow)
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=5)
    assert blocked.observed_at.tzinfo is UTC
    assert blocked.signal_age_seconds == d("18000.000000")
    assert blocked.surprise_delta == d("-3.100000")
    assert blocked.confidence_decay_factor == d("0.550000")
    assert blocked.final_confidence == d("0.150000")
    assert blocked.reason_codes == (
        "market_research_pmi_surprise_digest_confirmation_gap",
        "market_research_pmi_surprise_digest_material_surprise",
        "market_research_pmi_surprise_digest_stale_signal",
        "market_research_pmi_surprise_digest_thin_sources",
    )

    watched = summary.rows[1]
    assert watched.redacted_public_signal_reference == "sha256:8247107fe56a"
    assert watched.signal_age_seconds == d("4800.000000")
    assert watched.surprise_delta == d("-1.300000")
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.750000")
    assert watched.reason_codes == (
        "market_research_pmi_surprise_digest_high_revision",
        "market_research_pmi_surprise_digest_material_surprise",
    )

    ready = summary.rows[2]
    assert ready.observed_at == GENERATED_AT - timedelta(minutes=45)
    assert ready.reason_codes == ("market_research_pmi_surprise_digest_ready",)
    assert ready.redacted_public_signal_reference == "ism-public-release"
    assert ready.final_confidence == d("0.900000")

    assert summary.reason_code_counts == (
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_confirmation_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("ism.manufacturing.pmi", "pmi-signal-v0"),
        ("private.composite.pmi", "pmi-signal-private-v0"),
        ("spglobal.services.pmi", "pmi-signal-services-v0"),
    )

    for instance in (
        summary,
        summary.rows[0],
        summary.reason_code_counts[0],
        config(),
        signal(),
    ):
        _assert_public_numeric_fields_are_exact_decimals(instance)


def test_pmi_surprise_digest_empty_inputs_are_blocked_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_pmi_surprise_digest"
    )
    assert summary.signal_count == d("0.000000")
    assert summary.ready_signal_count == d("0.000000")
    assert summary.watch_signal_count == d("0.000000")
    assert summary.blocked_signal_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_pmi_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_pmi_surprise_digest_frozen_payload_and_validation_guards() -> None:
    summary = report((signal(),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].digest_status = "watch"  # type: ignore[misc]

    payload = market_research_pmi_surprise_digest_payload(summary)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["actual_pmi"] == "51.000000"  # type: ignore[index]
    _walk_payload(payload)
    _assert_six_decimal_string(payload["signal_count"])
    _assert_six_decimal_string(payload["average_final_confidence"])
    _assert_six_decimal_string(payload["rows"][0]["actual_pmi"])  # type: ignore[index]

    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="aware datetime"):
        signal(observed_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="exact Decimal"):
        signal(expected_pmi=_DecimalSubclass("50.000000"))
    with pytest.raises(ValueError, match="unique"):
        report((signal(release_key="duplicate.pmi"), signal(release_key="duplicate.pmi")))


def test_pmi_surprise_digest_rejects_each_false_report_only_flag() -> None:
    summary = report((signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    false_flag_cases = (
        ("config paper_only", lambda: config(paper_only=False)),
        ("config report_only", lambda: config(report_only=False)),
        ("config readonly", lambda: config(readonly=False)),
        ("signal paper_only", lambda: signal(paper_only=False)),
        ("signal report_only", lambda: signal(report_only=False)),
        ("signal readonly", lambda: signal(readonly=False)),
        ("row paper_only", lambda: replace(row, paper_only=False)),
        ("row report_only", lambda: replace(row, report_only=False)),
        ("row readonly", lambda: replace(row, readonly=False)),
        ("reason count paper_only", lambda: replace(reason_count, paper_only=False)),
        ("reason count report_only", lambda: replace(reason_count, report_only=False)),
        ("reason count readonly", lambda: replace(reason_count, readonly=False)),
        ("report paper_only", lambda: replace(summary, paper_only=False)),
        ("report report_only", lambda: replace(summary, report_only=False)),
        ("report readonly", lambda: replace(summary, readonly=False)),
    )

    for _label, make_value in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_value()


def test_pmi_surprise_digest_rejects_bad_count_ratio_and_tzinfo_surfaces() -> None:
    with pytest.raises(ValueError, match="source_count must be a whole-count Decimal"):
        signal(source_count=d("1.500000"))

    with pytest.raises(ValueError, match="min_source_count must be a whole-count Decimal"):
        config(min_source_count=d("1.500000"))

    with pytest.raises(ValueError, match="confirmation_ratio must be between 0 and 1"):
        signal(confirmation_ratio=d("1.000001"))

    with pytest.raises(ValueError, match="confirmation_ratio must be between 0 and 1"):
        signal(confirmation_ratio=d("1.0000004"))

    with pytest.raises(ValueError, match="surprise_score must be nonnegative"):
        signal(surprise_score=d("-0.0000004"))

    with pytest.raises(ValueError, match="source_count must be a whole-count Decimal"):
        signal(source_count=d("1.0000004"))

    with pytest.raises(ValueError, match="signal_ratio must be between 0 and 1"):
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code="market_research_pmi_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("1.000001"),
        )

    with pytest.raises(ValueError, match="aware datetime|timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="aware datetime|timezone-aware"):
        report((), generated_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTz()))


def test_pmi_surprise_digest_manual_construction_normalizes_and_validates_ordering() -> None:
    summary = report(
        (
            signal(
                "research.pmi.ready",
                condition_id="condition_ready",
                release_key="z.ready.pmi",
            ),
            signal(
                "research.pmi.watch",
                condition_id="condition_watch",
                release_key="m.watch.pmi",
                surprise_score=d("0.300000"),
                revision_ratio=d("0.300000"),
            ),
            signal(
                "research.pmi.blocked",
                condition_id="condition_blocked",
                release_key="a.blocked.pmi",
                source_count=d("1.000000"),
                confirmation_ratio=d("0.400000"),
            ),
        ),
    )

    normalized = replace(
        summary,
        rows=(summary.rows[2], summary.rows[0], summary.rows[1]),
        signal_config_versions=tuple(reversed(summary.signal_config_versions)),
        reason_code_counts=tuple(reversed(summary.reason_code_counts)),
    )

    assert normalized.rows == summary.rows
    assert normalized.signal_config_versions == summary.signal_config_versions
    assert normalized.reason_code_counts == summary.reason_code_counts

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(
            summary.rows[1],
            reason_codes=(
                "market_research_pmi_surprise_digest_material_surprise",
                "market_research_pmi_surprise_digest_high_revision",
            ),
        )

    with pytest.raises(ValueError, match="reason_code is not valid for this scope"):
        replace(
            summary.rows[1],
            reason_codes=("market_research_pmi_surprise_digest_no_inputs",),
        )

    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(
            summary,
            reason_code_counts=(
                MarketResearchPmiSurpriseDigestReasonCodeCount(
                    reason_code="market_research_pmi_surprise_digest_no_inputs",
                    count=d("1.000000"),
                    signal_ratio=d("0.000000"),
                ),
            ),
            reason_codes=("market_research_pmi_surprise_digest_no_inputs",),
        )

    with pytest.raises(ValueError, match="signal_config_versions must match rows"):
        replace(
            summary,
            signal_config_versions=(("unknown.release.pmi", "pmi-signal-v0"),),
        )


def test_pmi_surprise_digest_has_no_network_durable_store_or_live_trading_surface() -> None:
    source_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_pmi_surprise_digest.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert imported_roots.isdisjoint(
        {
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
        },
    )
    forbidden_calls = {"open", "connect", "request", "urlopen", "Session"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls

    lowered = source.lower()
    for forbidden_fragment in (
        "api_key",
        "auth",
        "broker",
        "cancel_order",
        "database",
        "exchange",
        "live_trading",
        "place_order",
        "persist",
        "private_key",
        "replace_order",
        "secret",
        "submit_order",
        "token",
        "trade",
        "wallet",
        "wallet_address",
    ):
        assert forbidden_fragment not in lowered
