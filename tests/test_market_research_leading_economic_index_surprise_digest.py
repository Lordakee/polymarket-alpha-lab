from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.market_research_leading_economic_index_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchLeadingEconomicIndexSurpriseDigestConfig,
    MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount,
    MarketResearchLeadingEconomicIndexSurpriseDigestReport,
    MarketResearchLeadingEconomicIndexSurpriseDigestRow,
    MarketResearchLeadingEconomicIndexSurpriseDigestSignal,
    build_market_research_leading_economic_index_surprise_digest,
    market_research_leading_economic_index_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
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


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_leading_economic_index_surprise_digest",
    )


def config(**overrides: object) -> MarketResearchLeadingEconomicIndexSurpriseDigestConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.030000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.700000"),
        "stale_confidence_decay": d("0.250000"),
        "thin_source_confidence_decay": d("0.150000"),
        "revision_confidence_decay": d("0.100000"),
        "confirmation_confidence_decay": d("0.150000"),
    }
    values.update(overrides)
    return MarketResearchLeadingEconomicIndexSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_lei_headline",
    *,
    research_key: str = "research.leading_economic_index.headline",
    release_key: str = "conference_board.leading_economic_index.headline",
    indicator_key: str = "leading_economic_index",
    public_signal_reference: str = "conference-board-public-lei-release",
    observed_at: datetime | None = None,
    expected_index_change: Decimal = d("0.001000"),
    actual_index_change: Decimal = d("0.001000"),
    surprise_score: Decimal = d("0.010000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.020000"),
    confirmation_ratio: Decimal = d("0.900000"),
    base_confidence: Decimal = d("0.950000"),
    signal_config_version: str = "leading-economic-index-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchLeadingEconomicIndexSurpriseDigestSignal:
    return MarketResearchLeadingEconomicIndexSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        indicator_key=indicator_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        expected_index_change=expected_index_change,
        actual_index_change=actual_index_change,
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


def digest(
    inputs: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestSignal, ...],
    *,
    cfg: MarketResearchLeadingEconomicIndexSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchLeadingEconomicIndexSurpriseDigestReport:
    return build_market_research_leading_economic_index_surprise_digest(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, child in value.items():
            items.append(key)
            items.extend(_walk_payload_values(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(_walk_payload_values(child))
        return tuple(items)
    return (value,)


def _assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def test_leading_economic_index_surprise_digest_reduces_report_only_rows() -> None:
    report = digest(
        (
            signal(
                "condition_ready",
                release_key="conference_board.leading_economic_index.headline",
                observed_at=(GENERATED_AT - timedelta(minutes=30)).astimezone(
                    timezone(timedelta(hours=2)),
                ),
            ),
            signal(
                "condition_watch",
                research_key="research.leading_economic_index.diffusion",
                release_key="conference_board.leading_economic_index.diffusion",
                indicator_key="leading_economic_index_diffusion",
                public_signal_reference="https://example.test/lei?signal=abc",
                observed_at=GENERATED_AT - timedelta(minutes=45),
                expected_index_change=d("-0.002000"),
                actual_index_change=d("-0.006000"),
                surprise_score=d("0.050000"),
                revision_ratio=d("0.300000"),
                base_confidence=d("0.850000"),
            ),
            signal(
                "condition_blocked",
                research_key="research.leading_economic_index.composite",
                release_key="conference_board.leading_economic_index.composite",
                indicator_key="leading_economic_index_composite",
                public_signal_reference="public-lei-composite",
                observed_at=GENERATED_AT - timedelta(hours=5),
                expected_index_change=d("0.004000"),
                actual_index_change=d("-0.010000"),
                surprise_score=d("0.120000"),
                source_count=d("1.000000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.800000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_leading_economic_index_surprise_digest"
    )
    assert report.signal_count == d("3.000000")
    assert report.ready_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.material_surprise_count == d("2.000000")
    assert report.upside_surprise_count == ZERO
    assert report.downside_surprise_count == d("2.000000")
    assert report.inline_surprise_count == d("1.000000")
    assert report.stale_signal_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.high_revision_count == d("1.000000")
    assert report.confirmation_gap_count == d("1.000000")
    assert report.average_surprise_score == d("0.060000")
    assert report.average_final_confidence == d("0.650000")
    assert report.max_observed_signal_age_seconds == d("18000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.digest_status, row.release_key) for row in report.rows) == (
        ("blocked", "conference_board.leading_economic_index.composite"),
        ("watch", "conference_board.leading_economic_index.diffusion"),
        ("ready", "conference_board.leading_economic_index.headline"),
    )

    blocked = report.rows[0]
    assert blocked.surprise_direction == "downside"
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=5)
    assert blocked.signal_age_seconds == d("18000.000000")
    assert blocked.leading_index_surprise_delta == d("-0.014000")
    assert blocked.confidence_decay_factor == d("0.550000")
    assert blocked.final_confidence == d("0.250000")
    assert blocked.reason_codes == (
        "market_research_leading_economic_index_surprise_digest_material_surprise",
        "market_research_leading_economic_index_surprise_digest_confirmation_gap",
        "market_research_leading_economic_index_surprise_digest_stale_signal",
        "market_research_leading_economic_index_surprise_digest_thin_sources",
    )

    watched = report.rows[1]
    assert watched.surprise_direction == "downside"
    assert watched.redacted_public_signal_reference == "sha256:46404b8e43c7"
    assert watched.signal_age_seconds == d("2700.000000")
    assert watched.leading_index_surprise_delta == d("-0.004000")
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.750000")
    assert watched.reason_codes == (
        "market_research_leading_economic_index_surprise_digest_material_surprise",
        "market_research_leading_economic_index_surprise_digest_high_revision",
    )

    ready = report.rows[2]
    assert ready.surprise_direction == "inline"
    assert ready.observed_at == GENERATED_AT - timedelta(minutes=30)
    assert ready.reason_codes == (
        "market_research_leading_economic_index_surprise_digest_ready",
    )
    assert ready.final_confidence == d("0.950000")

    assert report.reason_code_counts == (
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_"
                "material_surprise"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_"
                "confirmation_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_"
                "high_revision"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_"
                "stale_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_"
                "thin_sources"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_ready"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == tuple(
        item.reason_code for item in report.reason_code_counts
    )


def test_empty_leading_economic_index_digest_blocks_as_missing_evidence() -> None:
    report = digest(())

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_leading_economic_index_surprise_digest"
    )
    assert report.signal_count == ZERO
    assert report.ready_signal_count == ZERO
    assert report.watch_signal_count == ZERO
    assert report.blocked_signal_count == ZERO
    assert report.material_surprise_count == ZERO
    assert report.max_observed_signal_age_seconds == ZERO
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_leading_economic_index_surprise_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_leading_economic_index_surprise_digest_no_inputs"
            ),
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_serializes_six_decimal_strings_utc_and_no_floats() -> None:
    report = digest((signal(surprise_score=d("0.015000")),))
    payload = market_research_leading_economic_index_surprise_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T14:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.015000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T13:30:00+00:00"
    assert payload["rows"][0]["actual_index_change"] == "0.001000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["reason_code_counts"][0]["signal_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(
        isinstance(value, (Decimal, datetime, float))
        for value in _walk_payload_values(payload)
    )
    _assert_six_decimal_string(payload["signal_count"])
    _assert_six_decimal_string(payload["average_final_confidence"])
    _assert_six_decimal_string(payload["rows"][0]["source_count"])

    with pytest.raises(
        ValueError,
        match="MarketResearchLeadingEconomicIndexSurpriseDigestReport",
    ):
        market_research_leading_economic_index_surprise_digest_payload(payload)  # type: ignore[arg-type]


def test_public_dataclasses_are_frozen_exact_type_and_decimal_only() -> None:
    report = digest((signal(),))

    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "watch"  # type: ignore[misc]

    public_numeric_names = {
        "actual_index_change",
        "average_final_confidence",
        "average_surprise_score",
        "base_confidence",
        "blocked_signal_count",
        "confirmation_confidence_decay",
        "confirmation_gap_count",
        "confirmation_ratio",
        "confidence_decay_factor",
        "count",
        "downside_surprise_count",
        "expected_index_change",
        "final_confidence",
        "high_revision_count",
        "inline_surprise_count",
        "leading_index_surprise_delta",
        "material_surprise_count",
        "material_surprise_threshold",
        "max_observed_signal_age_seconds",
        "max_revision_ratio",
        "max_signal_age_seconds",
        "min_confirmation_ratio",
        "min_source_count",
        "ready_signal_count",
        "revision_confidence_decay",
        "revision_ratio",
        "signal_age_seconds",
        "signal_count",
        "signal_ratio",
        "source_count",
        "stale_confidence_decay",
        "stale_signal_count",
        "surprise_score",
        "thin_source_confidence_decay",
        "thin_source_count",
        "upside_surprise_count",
        "watch_signal_count",
    }
    for cls in (
        MarketResearchLeadingEconomicIndexSurpriseDigestConfig,
        MarketResearchLeadingEconomicIndexSurpriseDigestSignal,
        MarketResearchLeadingEconomicIndexSurpriseDigestRow,
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount,
        MarketResearchLeadingEconomicIndexSurpriseDigestReport,
    ):
        assert cls.__dataclass_params__.frozen is True
        type_hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in public_numeric_names:
                assert type_hints[field.name] is Decimal
            assert "float" not in str(type_hints[field.name]).lower()
            assert "int" not in str(type_hints[field.name]).lower()

    with pytest.raises(TypeError, match="subclassing"):
        class ConfigSubclass(MarketResearchLeadingEconomicIndexSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class SignalSubclass(MarketResearchLeadingEconomicIndexSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class RowSubclass(MarketResearchLeadingEconomicIndexSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReasonCountSubclass(
            MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReportSubclass(MarketResearchLeadingEconomicIndexSurpriseDigestReport):
            pass

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id=_StringSubclass("condition_string_subclass"))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 3, 13, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="expected_index_change"):
        signal(expected_index_change=_DecimalSubclass("0.001000"))


def test_rejects_false_flags_bad_datetimes_and_bad_scalars() -> None:
    report = digest((signal(),))

    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: signal(paper_only=False),
        lambda: signal(report_only=False),
        lambda: signal(readonly=False),
        lambda: replace(report.rows[0], paper_only=False),
        lambda: replace(report.rows[0], report_only=False),
        lambda: replace(report.rows[0], readonly=False),
        lambda: replace(report.reason_code_counts[0], paper_only=False),
        lambda: replace(report.reason_code_counts[0], report_only=False),
        lambda: replace(report.reason_code_counts[0], readonly=False),
        lambda: replace(report, paper_only=False),
        lambda: replace(report, report_only=False),
        lambda: replace(report, readonly=False),
    )
    for make_value in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_value()

    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(
            observed_at=datetime(
                2026,
                7,
                3,
                14,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        digest(
            (),
            generated_at=datetime(
                2026,
                7,
                3,
                14,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_count"):
        signal(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="confirmation_ratio"):
        signal(confirmation_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="surprise_score"):
        signal(surprise_score=d("-0.000001"))
    with pytest.raises(ValueError, match="unique condition_id"):
        digest((signal("duplicate_condition"), signal("duplicate_condition")))
    with pytest.raises(ValueError, match="config"):
        build_market_research_leading_economic_index_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_public_constructors_reject_nondeterministic_rows_reasons_and_counts() -> None:
    report = digest(
        (
            signal("condition_ready", release_key="z.ready.lei"),
            signal(
                "condition_watch",
                release_key="m.watch.lei",
                surprise_score=d("0.050000"),
                revision_ratio=d("0.250000"),
            ),
            signal(
                "condition_blocked",
                release_key="a.blocked.lei",
                observed_at=GENERATED_AT - timedelta(hours=5),
                source_count=d("1.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=tuple(reversed(report.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=tuple(reversed(report.reason_codes)))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="leading_index_surprise_delta"):
        replace(report.rows[0], leading_index_surprise_delta=d("0.000001"))
    with pytest.raises(ValueError, match="final_confidence"):
        replace(report.rows[0], final_confidence=d("0.999999"))
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="review_report")
    with pytest.raises(ValueError, match="count"):
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
            reason_code="market_research_leading_economic_index_surprise_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_module_is_pure_phase1_report_only_without_io_or_live_action_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "ccxt",
        "eth_account",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "cursor",
        "execute",
        "open",
        "request",
        "send",
        "sign",
        "submit",
        "urlopen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function_name = ""
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            assert function_name not in forbidden_call_names

    lowered = source.lower()
    for forbidden_fragment in (
        "api_key",
        "authentication",
        "cancel_order",
        "live_trading",
        "place_order",
        "private_key",
        "replace_order",
        "submit_order",
        "wallet",
    ):
        assert forbidden_fragment not in lowered
