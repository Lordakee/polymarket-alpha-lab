from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_employment_cost_index_surprise_digest import (
    DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION,
    EmploymentCostIndexSurpriseDigestConfig,
    EmploymentCostIndexSurpriseDigestReport,
    EmploymentCostIndexSurpriseInput,
    EmploymentCostIndexSurpriseRow,
    build_market_research_employment_cost_index_surprise_digest,
    market_research_employment_cost_index_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 31, 14, 0, tzinfo=timezone(timedelta(hours=2)))


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    market_id: str = "eci-hot-wage-print",
    release_at: datetime = datetime(2026, 7, 31, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    actual_employment_cost_index_growth: str = "0.012",
    consensus_employment_cost_index_growth: str = "0.010",
    previous_employment_cost_index_growth: str = "0.009",
    market_probability: str = "0.66",
    threshold_probability: str = "0.55",
    source_count: str = "3",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> EmploymentCostIndexSurpriseInput:
    return EmploymentCostIndexSurpriseInput(
        market_id=market_id,
        release_at=release_at,
        actual_employment_cost_index_growth=d(actual_employment_cost_index_growth),
        consensus_employment_cost_index_growth=d(consensus_employment_cost_index_growth),
        previous_employment_cost_index_growth=d(previous_employment_cost_index_growth),
        market_probability=d(market_probability),
        threshold_probability=d(threshold_probability),
        source_count=d(source_count),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_digest_sorts_rows_normalizes_utc_and_emits_deterministic_reasons() -> None:
    report = build_market_research_employment_cost_index_surprise_digest(
        (
            observation(
                market_id="eci-cool-benefits-print",
                release_at=datetime(2026, 10, 30, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
                actual_employment_cost_index_growth="0.008",
                consensus_employment_cost_index_growth="0.010",
                previous_employment_cost_index_growth="0.011",
                market_probability="0.44",
                threshold_probability="0.55",
                source_count="2",
            ),
            observation(),
            observation(
                market_id="eci-inline-compensation-print",
                release_at=datetime(2026, 7, 31, 12, 30, tzinfo=UTC),
                actual_employment_cost_index_growth="0.010",
                consensus_employment_cost_index_growth="0.010",
                previous_employment_cost_index_growth="0.009",
                market_probability="0.55",
                threshold_probability="0.55",
                source_count="1",
            ),
        ),
        config=EmploymentCostIndexSurpriseDigestConfig(
            config_version=DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
    assert (
        report.config_version
        == DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_employment_cost_index_surprise_markets"
    assert report.input_count == d("3")
    assert report.positive_surprise_count == d("1")
    assert report.negative_surprise_count == d("1")
    assert report.inline_count == d("1")
    assert report.total_source_count == d("6")
    assert report.positive_surprise_ratio == d("0.333333")
    assert report.negative_surprise_ratio == d("0.333333")
    assert report.market_probability_edge_ratio == d("0.333333")
    assert report.largest_abs_surprise_market_id == "eci-hot-wage-print"
    assert report.largest_abs_surprise_ratio == d("0.200000")
    assert report.reason_codes == (
        "employment_cost_index_surprise_negative_present",
        "employment_cost_index_surprise_positive_present",
        "employment_cost_index_surprise_probability_edge_present",
    )
    assert tuple(row.market_id for row in report.surprise_rows) == (
        "eci-hot-wage-print",
        "eci-inline-compensation-print",
        "eci-cool-benefits-print",
    )
    hot_row = report.surprise_rows[0]
    assert hot_row.release_at == datetime(2026, 7, 31, 12, 30, tzinfo=UTC)
    assert hot_row.surprise_direction == "positive"
    assert hot_row.surprise_growth_points == d("0.002")
    assert hot_row.surprise_ratio == d("0.200000")
    assert hot_row.market_probability_edge == d("0.11")
    assert report.surprise_rows[1].surprise_direction == "inline"
    assert report.surprise_rows[2].surprise_direction == "negative"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    for field_name in (
        "input_count",
        "positive_surprise_count",
        "negative_surprise_count",
        "inline_count",
        "total_source_count",
        "positive_surprise_ratio",
        "negative_surprise_ratio",
        "market_probability_edge_ratio",
        "largest_abs_surprise_ratio",
    ):
        assert type(getattr(report, field_name)) is Decimal
    for field_name in (
        "actual_employment_cost_index_growth",
        "consensus_employment_cost_index_growth",
        "previous_employment_cost_index_growth",
        "market_probability",
        "threshold_probability",
        "source_count",
        "surprise_growth_points",
        "surprise_ratio",
        "market_probability_edge",
    ):
        assert type(getattr(hot_row, field_name)) is Decimal


def test_empty_digest_is_blocked_with_decimal_zero_counts_and_no_optional_ratios() -> None:
    report = build_market_research_employment_cost_index_surprise_digest(
        [],
        config=EmploymentCostIndexSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "collect_employment_cost_index_surprise_inputs"
    assert report.input_count == d("0")
    assert report.positive_surprise_count == d("0")
    assert report.negative_surprise_count == d("0")
    assert report.inline_count == d("0")
    assert report.total_source_count == d("0")
    assert report.positive_surprise_ratio is None
    assert report.negative_surprise_ratio is None
    assert report.market_probability_edge_ratio is None
    assert report.largest_abs_surprise_market_id is None
    assert report.largest_abs_surprise_ratio is None
    assert report.surprise_rows == ()
    assert report.reason_codes == ("employment_cost_index_surprise_digest_empty",)


def test_dataclasses_are_frozen_and_public_numeric_surface_rejects_float() -> None:
    config = EmploymentCostIndexSurpriseDigestConfig()
    item = observation()
    assert is_dataclass(config)
    assert is_dataclass(item)
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"  # type: ignore[misc]

    for dataclass_type in (
        EmploymentCostIndexSurpriseDigestConfig,
        EmploymentCostIndexSurpriseInput,
        EmploymentCostIndexSurpriseRow,
        EmploymentCostIndexSurpriseDigestReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Bad{dataclass_type.__name__}", (dataclass_type,), {})

    with pytest.raises(ValueError, match="config_version must be the supported"):
        EmploymentCostIndexSurpriseDigestConfig(
            config_version="employment-cost-index-surprise-v0",
        )

    with pytest.raises(ValueError, match="market_id must be a string"):
        observation(
            market_id=_StringSubclass("eci-string-subclass"),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="release_at must be a datetime"):
        observation(release_at=_DatetimeSubclass(2026, 1, 1, tzinfo=UTC))

    with pytest.raises(
        ValueError,
        match="actual_employment_cost_index_growth must be a Decimal",
    ):
        EmploymentCostIndexSurpriseInput(
            market_id="bad-decimal-subclass",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_employment_cost_index_growth=_DecimalSubclass("0.012"),
            consensus_employment_cost_index_growth=d("0.010"),
            previous_employment_cost_index_growth=d("0.009"),
            market_probability=d("0.50"),
            threshold_probability=d("0.50"),
            source_count=d("1"),
        )

    with pytest.raises(
        ValueError,
        match="actual_employment_cost_index_growth must be a Decimal",
    ):
        EmploymentCostIndexSurpriseInput(
            market_id="bad-float",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_employment_cost_index_growth=0.012,  # type: ignore[arg-type]
            consensus_employment_cost_index_growth=d("0.010"),
            previous_employment_cost_index_growth=d("0.009"),
            market_probability=d("0.50"),
            threshold_probability=d("0.50"),
            source_count=d("1"),
        )

    with pytest.raises(ValueError, match="source_count must be an integral Decimal"):
        observation(source_count="1.5")

    with pytest.raises(ValueError, match="config must be an EmploymentCostIndexSurpriseDigestConfig"):
        build_market_research_employment_cost_index_surprise_digest(
            (item,),
            config=object(),  # type: ignore[arg-type]
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    report = build_market_research_employment_cost_index_surprise_digest(
        (item,),
        config=EmploymentCostIndexSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.surprise_rows[0].market_id = "changed"  # type: ignore[misc]
    for field_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=field_name):
            replace(report.surprise_rows[0], **{field_name: False})
        with pytest.raises(ValueError, match=field_name):
            replace(report, **{field_name: False})


def test_rejects_naive_datetimes_false_flags_bounds_bad_collections_and_payload_is_json_ready() -> None:
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        observation(release_at=datetime(2026, 1, 1))
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        observation(release_at=datetime(2026, 1, 1, tzinfo=_NoneOffsetTimezone()))

    for field_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=field_name):
            EmploymentCostIndexSurpriseDigestConfig(**{field_name: False})
        with pytest.raises(ValueError, match=f"EmploymentCostIndexSurpriseInput must be {field_name}"):
            observation(**{field_name: False})

    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        observation(market_probability="1.01")

    with pytest.raises(ValueError, match="inputs must be a list or tuple"):
        build_market_research_employment_cost_index_surprise_digest(
            "bad",  # type: ignore[arg-type]
            config=EmploymentCostIndexSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="inputs must contain EmploymentCostIndexSurpriseInput values"):
        build_market_research_employment_cost_index_surprise_digest(
            (object(),),  # type: ignore[arg-type]
            config=EmploymentCostIndexSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    payload = market_research_employment_cost_index_surprise_digest_payload(
        build_market_research_employment_cost_index_surprise_digest(
            (observation(),),
            config=EmploymentCostIndexSurpriseDigestConfig(),
            generated_at=GENERATED_AT,
        ),
    )
    assert payload["input_count"] == "1.000000"
    assert payload["positive_surprise_ratio"] == "1.000000"
    assert payload["surprise_rows"][0]["release_at"] == "2026-07-31T12:30:00+00:00"
    assert payload["surprise_rows"][0]["source_count"] == "3.000000"
    assert payload["surprise_rows"][0]["actual_employment_cost_index_growth"] == "0.012000"
    assert payload["surprise_rows"][0]["market_probability"] == "0.660000"
    assert payload["surprise_rows"][0]["surprise_ratio"] == "0.200000"
    assert "wallet" not in repr(payload).lower()
    assert "order" not in repr(payload).lower()


def test_module_scope_is_pure_in_memory_and_excludes_live_or_durable_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_employment_cost_index_surprise_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "private_key",
        "account",
        "open(",
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "insert",
        "update ",
        "delete ",
        "order placement",
        "cancel",
        "replace",
        "live trading",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_employment_cost_index_surprise_digest",
    )
    assert not any(name.startswith("load_") or name.startswith("insert_") for name in dir(module))
