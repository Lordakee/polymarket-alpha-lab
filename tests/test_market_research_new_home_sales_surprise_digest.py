from __future__ import annotations

import ast
import importlib
import re
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_new_home_sales_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchNewHomeSalesSurpriseDigestConfig,
    MarketResearchNewHomeSalesSurpriseDigestObservation,
    MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount,
    MarketResearchNewHomeSalesSurpriseDigestReport,
    MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket,
    build_market_research_new_home_sales_surprise_digest,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def test_digest_reduces_new_home_sales_surprises_with_stable_ordering() -> None:
    report = build_market_research_new_home_sales_surprise_digest(
        (
            _observation(
                release_id="release-watch",
                release_at=datetime(2026, 7, 24, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
                actual_sales=Decimal("627000"),
                consensus_sales=Decimal("650000"),
                prior_sales=Decimal("645000"),
            ),
            _observation(
                release_id="release-pass",
                release_at=datetime(2026, 6, 25, 14, 0, tzinfo=UTC),
                actual_sales=Decimal("623000"),
                consensus_sales=Decimal("620000"),
                prior_sales=Decimal("621000"),
            ),
            _observation(
                release_id="release-blocked",
                release_at=datetime(2026, 5, 23, 9, 30, tzinfo=timezone(timedelta(hours=2))),
                actual_sales=Decimal("700000"),
                consensus_sales=Decimal("650000"),
                prior_sales=Decimal("660000"),
            ),
        ),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(
            watch_abs_surprise_threshold=Decimal("0.020000"),
            blocked_abs_surprise_threshold=Decimal("0.050000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketResearchNewHomeSalesSurpriseDigestReport)
    assert report.generated_at == datetime(2026, 7, 2, 16, 0, tzinfo=UTC)
    assert (
        report.config_version
        == DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.digest_next_step == "review_new_home_sales_surprise_digest"
    assert report.observation_count == Decimal("3")
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.blocked_count == Decimal("1")
    assert report.upside_surprise_count == Decimal("2")
    assert report.downside_surprise_count == Decimal("1")
    assert report.average_surprise_ratio == Decimal("0.015459")
    assert report.max_abs_surprise_ratio == Decimal("0.076923")
    assert report.blocked_observation_ratio == Decimal("0.333333")
    assert report.reason_codes == (
        "new_home_sales_surprise_blocked_threshold_breached",
        "new_home_sales_surprise_watch_threshold_breached",
    )
    assert report.reason_code_counts == (
        MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount(
            reason_code="new_home_sales_surprise_blocked_threshold_breached",
            count=Decimal("1.000000"),
            observation_ratio=Decimal("0.333333"),
        ),
        MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount(
            reason_code="new_home_sales_surprise_watch_threshold_breached",
            count=Decimal("1.000000"),
            observation_ratio=Decimal("0.333333"),
        ),
    )
    assert report.surprise_buckets == (
        MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket(
            surprise_bucket="blocked",
            observation_count=Decimal("1"),
            average_surprise_ratio=Decimal("0.076923"),
            max_abs_surprise_ratio=Decimal("0.076923"),
        ),
        MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket(
            surprise_bucket="watch",
            observation_count=Decimal("1"),
            average_surprise_ratio=Decimal("-0.035385"),
            max_abs_surprise_ratio=Decimal("0.035385"),
        ),
        MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket(
            surprise_bucket="pass",
            observation_count=Decimal("1"),
            average_surprise_ratio=Decimal("0.004839"),
            max_abs_surprise_ratio=Decimal("0.004839"),
        ),
    )
    assert tuple(row.release_id for row in report.observations) == (
        "release-blocked",
        "release-watch",
        "release-pass",
    )
    assert report.observations[0].release_at == datetime(2026, 5, 23, 7, 30, tzinfo=UTC)
    assert report.observations[0].surprise_status == "blocked"
    assert report.observations[0].surprise_ratio == Decimal("0.076923")
    assert report.observations[1].surprise_status == "watch"
    assert report.observations[1].surprise_ratio == Decimal("-0.035385")
    assert report.observations[2].surprise_status == "pass"
    assert report.observations[2].surprise_ratio == Decimal("0.004839")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_observation_sort_preserves_one_microsecond_at_long_horizon() -> None:
    generated_at = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    report = build_market_research_new_home_sales_surprise_digest(
        (
            _observation(
                release_id="release-a-older",
                release_at=generated_at - timedelta(microseconds=1),
            ),
            _observation(
                release_id="release-z-newer",
                release_at=generated_at,
            ),
        ),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=generated_at,
    )

    assert tuple(item.release_id for item in report.observations) == (
        "release-z-newer",
        "release-a-older",
    )


def test_empty_digest_blocks_with_zero_decimal_public_metrics() -> None:
    report = build_market_research_new_home_sales_surprise_digest(
        (),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.reason_codes == ("new_home_sales_surprise_digest_empty",)
    assert report.observation_count == Decimal("0")
    assert report.pass_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.blocked_count == Decimal("0")
    assert report.upside_surprise_count == Decimal("0")
    assert report.downside_surprise_count == Decimal("0")
    assert report.average_surprise_ratio is None
    assert report.max_abs_surprise_ratio is None
    assert report.blocked_observation_ratio is None
    assert report.surprise_buckets == ()
    assert report.observations == ()
    assert report.reason_code_counts == (
        MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount(
            reason_code="new_home_sales_surprise_digest_empty",
            count=Decimal("1.000000"),
            observation_ratio=Decimal("0.000000"),
        ),
    )


def test_all_public_numeric_count_ratio_fields_are_decimal_or_none() -> None:
    report = build_market_research_new_home_sales_surprise_digest(
        (_observation(),),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    for value in (
        MarketResearchNewHomeSalesSurpriseDigestConfig(),
        _observation(),
        report.observations[0],
        report.surprise_buckets[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            field_value = getattr(value, field.name)
            if type(field_value) is Decimal:
                assert field_value.as_tuple().exponent == -6, field.name
            if _is_public_numeric_count_or_ratio(field.name):
                assert field_value is None or type(field_value) is Decimal, field.name


def test_rejects_bad_types_inconsistent_values_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_new_home_sales_surprise_digest(
            (),
            config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_new_home_sales_surprise_digest(
            (),
            config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="release_at"):
        _observation(release_at=datetime(2026, 7, 2, 12, 0, tzinfo=_MissingOffsetTimezone()))
    with pytest.raises(ValueError, match="config"):
        build_market_research_new_home_sales_surprise_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config_version"):
        MarketResearchNewHomeSalesSurpriseDigestConfig(config_version="unsupported")
    with pytest.raises(ValueError, match="observations"):
        build_market_research_new_home_sales_surprise_digest(
            (object(),),
            config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="actual_sales"):
        _observation(actual_sales=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="consensus_sales"):
        _observation(consensus_sales=Decimal("0"))
    with pytest.raises(ValueError, match="release_id"):
        _observation(release_id=" release")
    with pytest.raises(ValueError, match="paper_only"):
        MarketResearchNewHomeSalesSurpriseDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        MarketResearchNewHomeSalesSurpriseDigestConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        MarketResearchNewHomeSalesSurpriseDigestConfig(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_observation(), readonly=False)

    valid_bucket = MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket(
        surprise_bucket="pass",
        observation_count=Decimal("1"),
        average_surprise_ratio=Decimal("0.000000"),
        max_abs_surprise_ratio=Decimal("0.000000"),
    )
    with pytest.raises(ValueError, match="surprise_buckets"):
        MarketResearchNewHomeSalesSurpriseDigestReport(
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            config_version=DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION,
            digest_status="pass",
            digest_next_step="review_new_home_sales_surprise_digest",
            observation_count=Decimal("1"),
            pass_count=Decimal("1"),
            watch_count=Decimal("0"),
            blocked_count=Decimal("0"),
            upside_surprise_count=Decimal("0"),
            downside_surprise_count=Decimal("0"),
            average_surprise_ratio=Decimal("0.000000"),
            max_abs_surprise_ratio=Decimal("0.000000"),
            blocked_observation_ratio=Decimal("0.000000"),
            surprise_buckets=(
                MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket(
                    surprise_bucket="watch",
                    observation_count=Decimal("1"),
                    average_surprise_ratio=Decimal("0.020000"),
                    max_abs_surprise_ratio=Decimal("0.020000"),
                ),
                valid_bucket,
            ),
            observations=(
                MarketResearchNewHomeSalesSurpriseDigestObservation(
                    release_id="release-1",
                    release_at=datetime(2026, 7, 1, tzinfo=UTC),
                    actual_sales=Decimal("620000"),
                    consensus_sales=Decimal("620000"),
                    prior_sales=Decimal("620000"),
                ),
            ),
            reason_code_counts=(
                MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount(
                    reason_code="new_home_sales_surprise_digest_passed",
                    count=Decimal("1"),
                    observation_ratio=Decimal("1"),
                ),
            ),
            reason_codes=("new_home_sales_surprise_digest_passed",),
        )

    report = build_market_research_new_home_sales_surprise_digest(
        (_observation(),),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.surprise_buckets[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.reason_code_counts[0], paper_only=False)


def test_rejects_subclassing_for_public_dataclasses() -> None:
    for cls in (
        MarketResearchNewHomeSalesSurpriseDigestConfig,
        MarketResearchNewHomeSalesSurpriseDigestObservation,
        MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket,
        MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount,
        MarketResearchNewHomeSalesSurpriseDigestReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Bad{cls.__name__}", (cls,), {})


def test_dataclasses_are_frozen() -> None:
    report = build_market_research_new_home_sales_surprise_digest(
        (_observation(),),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )
    values = (
        MarketResearchNewHomeSalesSurpriseDigestConfig(),
        _observation(),
        report.observations[0],
        report.surprise_buckets[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_manual_report_rejects_unsorted_rows_reason_counts_and_versions() -> None:
    report = build_market_research_new_home_sales_surprise_digest(
        (
            _observation(
                release_id="release-z",
                release_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
                actual_sales=Decimal("700000"),
                consensus_sales=Decimal("650000"),
            ),
            _observation(
                release_id="release-a",
                release_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
                actual_sales=Decimal("627000"),
                consensus_sales=Decimal("650000"),
            ),
            _observation(
                release_id="release-pass",
                release_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
                actual_sales=Decimal("623000"),
                consensus_sales=Decimal("620000"),
            ),
        ),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="observations"):
        replace(report, observations=tuple(reversed(report.observations)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="reason_code_counts.*canonical"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("new_home_sales_surprise_digest_passed",))
    with pytest.raises(ValueError, match="reason_codes.*canonical"):
        replace(report, reason_codes=tuple(reversed(report.reason_codes)))
    with pytest.raises(ValueError, match="reason_codes.*unique"):
        replace(report, reason_codes=report.reason_codes + (report.reason_codes[0],))
    with pytest.raises(ValueError, match="config_version"):
        replace(report, config_version="unsupported")


def test_module_scope_excludes_io_db_network_auth_wallet_order_and_trading_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_new_home_sales_surprise_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    serialized_source = source.lower()
    serialized_report = repr(
        asdict(
            build_market_research_new_home_sales_surprise_digest(
                (_observation(),),
                config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
                generated_at=GENERATED_AT,
            ),
        ),
    ).lower()

    forbidden_literals = (
        "auth",
        "buy",
        "database",
        "db",
        "execute",
        "live",
        "order",
        "persist",
        "sell",
        "store",
        "trade",
        "wallet",
    )
    assert not any(token in serialized_report for token in forbidden_literals)
    assert not any(token in serialized_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "open",
        "persist",
        "rollback",
        "send",
        "timestamp",
        "total_seconds",
        "write",
    }
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)


def test_payload_serializes_public_values_without_decimal_datetime_or_float_leakage() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_new_home_sales_surprise_digest",
    )
    report = build_market_research_new_home_sales_surprise_digest(
        (
            _observation(
                release_id="release-watch",
                release_at=datetime(2026, 7, 24, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
                actual_sales=Decimal("627000"),
                consensus_sales=Decimal("650000"),
                prior_sales=Decimal("645000"),
            ),
        ),
        config=MarketResearchNewHomeSalesSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    payload = module.market_research_new_home_sales_surprise_digest_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_surprise_ratio"] == "-0.035385"
    assert payload["blocked_observation_ratio"] == "0.000000"
    assert payload["observations"][0]["release_at"] == "2026-07-24T14:00:00+00:00"
    assert payload["observations"][0]["actual_sales"] == "627000.000000"
    assert payload["observations"][0]["surprise_ratio"] == "-0.035385"
    assert payload["surprise_buckets"][0]["observation_count"] == "1.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"

    with pytest.raises(ValueError, match="report"):
        module.market_research_new_home_sales_surprise_digest_payload(object())

    _assert_no_decimal_datetime_or_float_values(payload)
    _assert_six_decimal_numeric_strings(payload)


def _observation(**overrides: object) -> MarketResearchNewHomeSalesSurpriseDigestObservation:
    values = {
        "release_id": "release-1",
        "release_at": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        "actual_sales": Decimal("620000"),
        "consensus_sales": Decimal("620000"),
        "prior_sales": Decimal("618000"),
    }
    values.update(overrides)
    return MarketResearchNewHomeSalesSurpriseDigestObservation(**values)


def _is_public_numeric_count_or_ratio(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_sales")
        or field_name.endswith("_threshold")
    )


def _assert_no_decimal_datetime_or_float_values(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_decimal_datetime_or_float_values(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_decimal_datetime_or_float_values(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))


def _assert_six_decimal_numeric_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _is_public_numeric_count_or_ratio(str(key)):
                assert type(child) is str, key
                assert SIX_DECIMAL_RE.fullmatch(child), (key, child)
            _assert_six_decimal_numeric_strings(child)
    elif isinstance(value, list):
        for child in value:
            _assert_six_decimal_numeric_strings(child)
