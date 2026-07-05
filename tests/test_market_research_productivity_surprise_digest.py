from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.market_research_productivity_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_PRODUCTIVITY_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchProductivitySurpriseDigestConfig,
    MarketResearchProductivitySurpriseDigestReasonCodeCount,
    MarketResearchProductivitySurpriseDigestReport,
    MarketResearchProductivitySurpriseDigestRow,
    MarketResearchProductivitySurpriseDigestSignal,
    build_market_research_productivity_surprise_digest,
    market_research_productivity_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "missing-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchProductivitySurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_PRODUCTIVITY_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("5400.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.030000"),
        "max_revision_ratio": d("0.150000"),
        "min_confirmation_ratio": d("0.700000"),
        "watch_confidence_threshold": d("0.750000"),
    }
    values.update(overrides)
    return MarketResearchProductivitySurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_productivity_headline",
    *,
    research_key: str = "research.productivity.headline",
    release_key: str = "productivity.nonfarm_business.prelim",
    sector_key: str = "nonfarm_business",
    public_signal_reference: str = "public-productivity-release",
    observed_at: datetime | None = None,
    expected_productivity_growth: Decimal = d("0.012000"),
    actual_productivity_growth: Decimal = d("-0.010000"),
    surprise_score: Decimal = d("0.020000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.040000"),
    confirmation_ratio: Decimal = d("0.900000"),
    base_confidence: Decimal = d("0.920000"),
    signal_config_version: str = "productivity-surprise-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchProductivitySurpriseDigestSignal:
    return MarketResearchProductivitySurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        sector_key=sector_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        expected_productivity_growth=expected_productivity_growth,
        actual_productivity_growth=actual_productivity_growth,
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
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchProductivitySurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchProductivitySurpriseDigestReport:
    return build_market_research_productivity_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_productivity_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_output_per_hour",
                research_key="research.productivity.output_per_hour",
                release_key="productivity.output_per_hour.final",
                sector_key="output_per_hour",
                public_signal_reference="https://example.test/productivity?token=secret",
                observed_at=GENERATED_AT - timedelta(hours=2),
                expected_productivity_growth=d("0.018000"),
                actual_productivity_growth=d("-0.034000"),
                surprise_score=d("0.080000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.210000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_unit_labor_cost",
                research_key="research.productivity.unit_labor_cost",
                release_key="productivity.unit_labor_cost",
                sector_key="unit_labor_cost",
                public_signal_reference="private productivity panel",
                observed_at=GENERATED_AT - timedelta(minutes=45),
                expected_productivity_growth=d("-0.004000"),
                actual_productivity_growth=d("0.031000"),
                surprise_score=d("0.050000"),
                source_count=d("2.000000"),
                revision_ratio=d("0.080000"),
                confirmation_ratio=d("0.660000"),
                base_confidence=d("0.840000"),
            ),
            signal(
                "condition_manufacturing",
                research_key="research.productivity.manufacturing",
                release_key="productivity.manufacturing",
                sector_key="manufacturing",
                public_signal_reference="public-manufacturing-productivity",
                observed_at=datetime(
                    2026,
                    7,
                    3,
                    13,
                    50,
                    tzinfo=timezone(timedelta(hours=-1)),
                ),
                expected_productivity_growth=d("0.011000"),
                actual_productivity_growth=d("0.009000"),
                surprise_score=d("0.010000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.030000"),
                confirmation_ratio=d("0.940000"),
                base_confidence=d("0.930000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_PRODUCTIVITY_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_productivity_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("2.000000")
    assert summary.average_surprise_score == d("0.046667")
    assert summary.max_signal_age_seconds == d("7200.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "productivity.output_per_hour.final",
        "productivity.unit_labor_cost",
        "productivity.manufacturing",
    )

    output_per_hour = summary.rows[0]
    assert output_per_hour.digest_status == "blocked"
    assert output_per_hour.observed_at == GENERATED_AT - timedelta(hours=2)
    assert output_per_hour.signal_age_seconds == d("7200.000000")
    assert output_per_hour.productivity_surprise_delta == d("-0.052000")
    assert output_per_hour.confidence_decay_factor == d("0.250000")
    assert output_per_hour.final_confidence == d("0.220000")
    assert output_per_hour.redacted_public_signal_reference == "sha256:f3d5bd3621b5"
    assert output_per_hour.reason_codes == (
        "market_research_productivity_surprise_digest_stale_signal",
        "market_research_productivity_surprise_digest_material_surprise",
        "market_research_productivity_surprise_digest_thin_sources",
        "market_research_productivity_surprise_digest_high_revision",
        "market_research_productivity_surprise_digest_confirmation_gap",
    )

    labor_cost = summary.rows[1]
    assert labor_cost.digest_status == "watch"
    assert labor_cost.signal_age_seconds == d("2700.000000")
    assert labor_cost.productivity_surprise_delta == d("0.035000")
    assert labor_cost.confidence_decay_factor == d("1.000000")
    assert labor_cost.final_confidence == d("0.840000")
    assert labor_cost.redacted_public_signal_reference == "sha256:7cf149683c61"
    assert labor_cost.reason_codes == (
        "market_research_productivity_surprise_digest_material_surprise",
        "market_research_productivity_surprise_digest_confirmation_gap",
    )

    manufacturing = summary.rows[2]
    assert manufacturing.digest_status == "ready"
    assert manufacturing.observed_at == GENERATED_AT - timedelta(minutes=10)
    assert manufacturing.signal_age_seconds == d("600.000000")
    assert manufacturing.productivity_surprise_delta == d("-0.002000")
    assert manufacturing.confidence_decay_factor == d("1.000000")
    assert manufacturing.final_confidence == d("0.930000")
    assert manufacturing.redacted_public_signal_reference == (
        "public-manufacturing-productivity"
    )
    assert manufacturing.reason_codes == (
        "market_research_productivity_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_productivity_surprise_digest_confirmation_gap",
        "market_research_productivity_surprise_digest_material_surprise",
        "market_research_productivity_surprise_digest_stale_signal",
        "market_research_productivity_surprise_digest_thin_sources",
        "market_research_productivity_surprise_digest_high_revision",
        "market_research_productivity_surprise_digest_ready",
    )


def test_empty_productivity_surprise_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_productivity_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.average_surprise_score is None
    assert summary.max_signal_age_seconds == ZERO
    assert summary.reason_code_counts == (
        MarketResearchProductivitySurpriseDigestReasonCodeCount(
            reason_code="market_research_productivity_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_productivity_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_uses_decimal_strings_utc_datetimes_and_no_floats() -> None:
    summary = report((signal(surprise_score=d("0.015000")),))
    payload = market_research_productivity_surprise_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.015000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T14:40:00+00:00"
    assert payload["rows"][0]["productivity_surprise_delta"] == "-0.022000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    with pytest.raises(
        ValueError,
        match="MarketResearchProductivitySurpriseDigestReport",
    ):
        market_research_productivity_surprise_digest_payload(payload)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report"):
        market_research_productivity_surprise_digest_payload(object())


def test_public_dataclasses_are_frozen_decimal_only_and_reject_bad_inputs() -> None:
    summary = report((signal(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].sector_key = "services"  # type: ignore[misc]

    public_numeric_names = {
        "actual_productivity_growth",
        "average_source_count",
        "average_surprise_score",
        "base_confidence",
        "blocked_signal_count",
        "confirmation_gap_count",
        "confirmation_ratio",
        "confidence_decay_factor",
        "count",
        "expected_productivity_growth",
        "final_confidence",
        "high_revision_count",
        "material_surprise_count",
        "material_surprise_threshold",
        "max_revision_ratio",
        "max_signal_age_seconds",
        "max_signal_age_seconds_threshold",
        "min_confirmation_ratio",
        "min_source_count",
        "productivity_surprise_delta",
        "ready_signal_count",
        "revision_ratio",
        "signal_age_seconds",
        "signal_count",
        "signal_ratio",
        "source_count",
        "stale_signal_count",
        "surprise_score",
        "thin_source_count",
        "watch_confidence_threshold",
        "watch_signal_count",
    }
    for cls in (
        MarketResearchProductivitySurpriseDigestConfig,
        MarketResearchProductivitySurpriseDigestSignal,
        MarketResearchProductivitySurpriseDigestRow,
        MarketResearchProductivitySurpriseDigestReasonCodeCount,
        MarketResearchProductivitySurpriseDigestReport,
    ):
        type_hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in public_numeric_names:
                assert type_hints[field.name] in (Decimal, Decimal | None)

    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(
            observed_at=datetime(
                2026,
                7,
                3,
                15,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            (),
            generated_at=datetime(
                2026,
                7,
                3,
                15,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="expected_productivity_growth"):
        signal(expected_productivity_growth=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="surprise_score"):
        signal(surprise_score=d("1.000001"))
    with pytest.raises(ValueError, match="unique condition_id"):
        report((signal("condition_a"), signal("condition_a", release_key="other")))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_productivity_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_public_dataclasses_reject_false_phase_flags_explicitly() -> None:
    summary = report((signal(),))

    with pytest.raises(ValueError, match="config.report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="signal.paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="row.readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count.paper_only"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report.report_only"):
        replace(summary, report_only=False)


def test_payload_serializer_rejects_raw_dicts_even_when_json_ready() -> None:
    valid_payload = market_research_productivity_surprise_digest_payload(
        report((signal(),)),
    )

    with pytest.raises(
        ValueError,
        match="MarketResearchProductivitySurpriseDigestReport",
    ):
        market_research_productivity_surprise_digest_payload(valid_payload)  # type: ignore[arg-type]


def test_exact_public_scalar_types_are_required() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "market-research-productivity-surprise-digest-v0",
            ),
        )
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="surprise_score"):
        signal(surprise_score=_DecimalSubclass("0.100000"))


def test_manual_rows_and_reports_reject_inconsistent_reason_codes_and_counts() -> None:
    ready = MarketResearchProductivitySurpriseDigestRow(
        condition_id="condition_ready",
        research_key="research.productivity.ready",
        release_key="productivity.ready",
        sector_key="headline",
        digest_status="ready",
        observed_at=GENERATED_AT,
        signal_age_seconds=ZERO,
        expected_productivity_growth=ZERO,
        actual_productivity_growth=ZERO,
        productivity_surprise_delta=ZERO,
        surprise_score=ZERO,
        source_count=d("2.000000"),
        revision_ratio=ZERO,
        confirmation_ratio=d("1.000000"),
        base_confidence=d("1.000000"),
        confidence_decay_factor=d("1.000000"),
        final_confidence=d("1.000000"),
        redacted_public_signal_reference="public-productivity",
        signal_config_version="productivity-surprise-signal-v0",
        reason_codes=("market_research_productivity_surprise_digest_ready",),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_productivity_surprise_digest_ready",
                "market_research_productivity_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="supported reason codes"):
        replace(
            ready,
            reason_codes=("market_research_productivity_surprise_digest_no_inputs",),
        )
    with pytest.raises(ValueError, match="digest_status"):
        replace(ready, digest_status="blocked")
    with pytest.raises(ValueError, match="productivity_surprise_delta"):
        replace(ready, productivity_surprise_delta=d("0.000001"))

    blocked = report(
        (
            signal(
                "condition_output_per_hour",
                release_key="productivity.output_per_hour.final",
                observed_at=GENERATED_AT - timedelta(hours=2),
                surprise_score=d("0.080000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.210000"),
                confirmation_ratio=d("0.400000"),
            ),
            signal(
                "condition_manufacturing",
                release_key="productivity.manufacturing",
            ),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked.rows[0],
            reason_codes=tuple(reversed(blocked.rows[0].reason_codes)),
        )
    with pytest.raises(ValueError, match="rows"):
        replace(blocked, rows=tuple(reversed(blocked.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            blocked,
            reason_code_counts=tuple(reversed(blocked.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="source_count"):
        signal(source_count=d("1.500000"))

    summary = MarketResearchProductivitySurpriseDigestReport(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_MARKET_RESEARCH_PRODUCTIVITY_SURPRISE_DIGEST_CONFIG_VERSION,
        digest_status="ready",
        recommended_next_step=(
            "allow_report_only_market_research_productivity_surprise_digest"
        ),
        signal_count=d("1.000000"),
        ready_signal_count=d("1.000000"),
        watch_signal_count=ZERO,
        blocked_signal_count=ZERO,
        material_surprise_count=ZERO,
        stale_signal_count=ZERO,
        thin_source_count=ZERO,
        high_revision_count=ZERO,
        confirmation_gap_count=ZERO,
        average_surprise_score=ZERO,
        max_signal_age_seconds=ZERO,
        average_source_count=d("2.000000"),
        rows=(ready,),
        reason_code_counts=(
            MarketResearchProductivitySurpriseDigestReasonCodeCount(
                reason_code="market_research_productivity_surprise_digest_ready",
                count=d("1.000000"),
                signal_ratio=d("1.000000"),
            ),
        ),
        reason_codes=("market_research_productivity_surprise_digest_ready",),
    )

    with pytest.raises(ValueError, match="signal_count"):
        replace(summary, signal_count=d("2.000000"))
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(summary, recommended_next_step="review")


def test_module_is_pure_phase1_in_memory_and_has_no_forbidden_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_productivity_surprise_digest",
    )
    source = getattr(module, "__loader__").get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    forbidden_import_roots = {
        "builtins.open",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
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
        "replace",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open"


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(_walk_payload_values(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_walk_payload_values(item))
        return tuple(items)
    return (value,)
