import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.market_research_capacity_utilization_surprise_digest as digest_module
from polymarket_alpha_lab.market_research_capacity_utilization_surprise_digest import (
    CapacityUtilizationSurpriseDigestConfig,
    CapacityUtilizationSurpriseInput,
    build_market_research_capacity_utilization_surprise_digest,
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal) and not isinstance(value, bool)


def _decimal(value: Decimal | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(value)


def _observation(
    *,
    market_id: str = "capacity-utilization-above-consensus",
    release_at: datetime = datetime(2026, 1, 16, 8, 15, tzinfo=timezone(timedelta(hours=-5))),
    actual_utilization_rate: Decimal | str = "0.792",
    consensus_utilization_rate: Decimal | str = "0.785",
    previous_utilization_rate: Decimal | str = "0.781",
    market_probability: Decimal | str = "0.62",
    threshold_probability: Decimal | str = "0.55",
    source_count: Decimal | str = "3",
) -> CapacityUtilizationSurpriseInput:
    return CapacityUtilizationSurpriseInput(
        market_id=market_id,
        release_at=release_at,
        actual_utilization_rate=_decimal(actual_utilization_rate),
        consensus_utilization_rate=_decimal(consensus_utilization_rate),
        previous_utilization_rate=_decimal(previous_utilization_rate),
        market_probability=_decimal(market_probability),
        threshold_probability=_decimal(threshold_probability),
        source_count=_decimal(source_count),
    )


def test_digest_sorts_rows_normalizes_utc_and_emits_deterministic_reason_codes_and_ratios() -> None:
    report = build_market_research_capacity_utilization_surprise_digest(
        [
            _observation(
                market_id="capacity-negative",
                release_at=datetime(2026, 3, 17, 12, 15, tzinfo=UTC),
                actual_utilization_rate="0.771",
                consensus_utilization_rate="0.779",
                previous_utilization_rate="0.780",
                market_probability="0.48",
                threshold_probability="0.55",
                source_count="2",
            ),
            _observation(),
            _observation(
                market_id="capacity-inline",
                release_at=datetime(2026, 2, 18, 13, 15, tzinfo=UTC),
                actual_utilization_rate="0.783",
                consensus_utilization_rate="0.783",
                previous_utilization_rate="0.782",
                market_probability="0.55",
                threshold_probability="0.55",
                source_count="1",
            ),
        ],
        config=CapacityUtilizationSurpriseDigestConfig(
            config_version="capacity-utilization-surprise-v1",
        ),
        generated_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone(timedelta(hours=2))),
    )

    assert report.generated_at == datetime(2026, 4, 1, 7, 0, tzinfo=UTC)
    assert report.config_version == "capacity-utilization-surprise-v1"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_capacity_utilization_surprise_markets"
    assert report.input_count == Decimal("3")
    assert report.positive_surprise_count == Decimal("1")
    assert report.negative_surprise_count == Decimal("1")
    assert report.inline_count == Decimal("1")
    assert report.total_source_count == Decimal("6")
    assert report.positive_surprise_ratio == Decimal("0.333333")
    assert report.negative_surprise_ratio == Decimal("0.333333")
    assert report.market_probability_edge_ratio == Decimal("0.333333")
    assert report.largest_abs_surprise_market_id == "capacity-negative"
    assert report.largest_abs_surprise_ratio == Decimal("0.010270")
    assert report.reason_codes == (
        "capacity_utilization_surprise_negative_present",
        "capacity_utilization_surprise_positive_present",
        "capacity_utilization_surprise_probability_edge_present",
    )
    assert tuple(row.market_id for row in report.surprise_rows) == (
        "capacity-utilization-above-consensus",
        "capacity-inline",
        "capacity-negative",
    )
    assert report.surprise_rows[0].release_at == datetime(2026, 1, 16, 13, 15, tzinfo=UTC)
    assert report.surprise_rows[0].surprise_rate_points == Decimal("0.007")
    assert report.surprise_rows[0].surprise_ratio == Decimal("0.008917")
    assert report.surprise_rows[0].market_probability_edge == Decimal("0.07")
    assert report.surprise_rows[0].surprise_direction == "positive"
    assert report.surprise_rows[1].surprise_direction == "inline"
    assert report.surprise_rows[2].surprise_direction == "negative"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(isinstance(getattr(report, field_name), Decimal) for field_name in (
        "input_count",
        "positive_surprise_count",
        "negative_surprise_count",
        "inline_count",
        "total_source_count",
        "positive_surprise_ratio",
        "negative_surprise_ratio",
        "market_probability_edge_ratio",
        "largest_abs_surprise_ratio",
    ))
    assert all(
        isinstance(getattr(report.surprise_rows[0], field_name), Decimal)
        for field_name in (
            "actual_utilization_rate",
            "consensus_utilization_rate",
            "previous_utilization_rate",
            "market_probability",
            "threshold_probability",
            "source_count",
            "surprise_rate_points",
            "surprise_ratio",
            "market_probability_edge",
        )
    )
    assert not any(
        hasattr(report, unsafe_name)
        for unsafe_name in ("auth", "wallet", "order", "private_key", "account", "persisted")
    )


def test_deterministic_ordering_and_payload_use_six_decimal_strings() -> None:
    first = _observation(
        market_id="zeta-positive",
        release_at=datetime(2026, 2, 18, 13, 15, tzinfo=UTC),
        actual_utilization_rate="0.792",
        consensus_utilization_rate="0.785",
        market_probability="0.62",
        threshold_probability="0.55",
    )
    second = _observation(
        market_id="alpha-negative",
        release_at=datetime(2026, 1, 16, 8, 15, tzinfo=timezone(timedelta(hours=-5))),
        actual_utilization_rate="0.771",
        consensus_utilization_rate="0.779",
        market_probability="0.48",
        threshold_probability="0.55",
        source_count="2",
    )
    third = _observation(
        market_id="alpha-inline",
        release_at=datetime(2026, 2, 18, 13, 15, tzinfo=UTC),
        actual_utilization_rate="0.783",
        consensus_utilization_rate="0.783",
        market_probability="0.55",
        threshold_probability="0.55",
        source_count="1",
    )

    forward = build_market_research_capacity_utilization_surprise_digest(
        [first, second, third],
        config=CapacityUtilizationSurpriseDigestConfig(),
        generated_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone(timedelta(hours=2))),
    )
    reverse = build_market_research_capacity_utilization_surprise_digest(
        [third, second, first],
        config=CapacityUtilizationSurpriseDigestConfig(),
        generated_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
    )

    assert forward == reverse
    assert tuple(row.market_id for row in forward.surprise_rows) == (
        "alpha-negative",
        "alpha-inline",
        "zeta-positive",
    )
    assert forward.reason_codes == (
        "capacity_utilization_surprise_negative_present",
        "capacity_utilization_surprise_positive_present",
        "capacity_utilization_surprise_probability_edge_present",
    )

    payload = digest_module.market_research_capacity_utilization_surprise_digest_payload(
        forward,
    )

    assert payload["generated_at"] == "2026-04-01T07:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "3.000000"
    assert payload["positive_surprise_ratio"] == "0.333333"
    assert payload["largest_abs_surprise_ratio"] == "0.010270"
    assert payload["surprise_rows"][0]["source_count"] == "2.000000"
    assert payload["surprise_rows"][0]["surprise_rate_points"] == "-0.008000"
    assert payload["surprise_rows"][2]["actual_utilization_rate"] == "0.792000"
    assert payload["surprise_rows"][2]["market_probability_edge"] == "0.070000"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        CapacityUtilizationSurpriseDigestConfig(),
        _observation(),
        forward.surprise_rows[0],
        forward,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name


def test_empty_digest_is_blocked_with_decimal_zero_counts_and_no_optional_ratios() -> None:
    report = build_market_research_capacity_utilization_surprise_digest(
        (),
        config=CapacityUtilizationSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "collect_capacity_utilization_surprise_inputs"
    assert report.input_count == Decimal("0")
    assert report.positive_surprise_count == Decimal("0")
    assert report.negative_surprise_count == Decimal("0")
    assert report.inline_count == Decimal("0")
    assert report.total_source_count == Decimal("0")
    assert report.positive_surprise_ratio is None
    assert report.negative_surprise_ratio is None
    assert report.market_probability_edge_ratio is None
    assert report.largest_abs_surprise_market_id is None
    assert report.largest_abs_surprise_ratio is None
    assert report.surprise_rows == ()
    assert report.reason_codes == ("capacity_utilization_surprise_digest_empty",)


def test_dataclasses_are_frozen_and_reject_non_decimal_public_numbers() -> None:
    item = _observation()
    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="actual_utilization_rate must be a Decimal"):
        CapacityUtilizationSurpriseInput(
            market_id="bad",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_utilization_rate=79.2,  # type: ignore[arg-type]
            consensus_utilization_rate=Decimal("0.785"),
            previous_utilization_rate=Decimal("0.781"),
            market_probability=Decimal("0.50"),
            threshold_probability=Decimal("0.50"),
            source_count=Decimal("1"),
        )
    with pytest.raises(ValueError, match="actual_utilization_rate must be a Decimal"):
        _observation(actual_utilization_rate=_DecimalSubclass("0.792"))

    with pytest.raises(ValueError, match="source_count must be an integral Decimal"):
        _observation(source_count="1.5")
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_market_research_capacity_utilization_surprise_digest(
            (),
            config=CapacityUtilizationSurpriseDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 1, 1, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="config must be a CapacityUtilizationSurpriseDigestConfig"):
        build_market_research_capacity_utilization_surprise_digest(
            [item],
            config=object(),  # type: ignore[arg-type]
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    report = build_market_research_capacity_utilization_surprise_digest(
        [item],
        config=CapacityUtilizationSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.surprise_rows[0].market_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="market_probability_edge must match"):
        replace(report.surprise_rows[0], market_probability_edge=Decimal("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            report,
            reason_codes=(
                "capacity_utilization_surprise_digest_empty",
                "capacity_utilization_surprise_positive_present",
            ),
        )


def test_rejects_naive_datetimes_false_hard_flags_probability_bounds_and_bad_collections() -> None:
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        _observation(release_at=datetime(2026, 1, 1))

    with pytest.raises(ValueError, match="CapacityUtilizationSurpriseDigestConfig must be report_only"):
        CapacityUtilizationSurpriseDigestConfig(report_only=False)

    with pytest.raises(ValueError, match="CapacityUtilizationSurpriseInput must be paper_only"):
        CapacityUtilizationSurpriseInput(
            market_id="unsafe",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_utilization_rate=Decimal("0.792"),
            consensus_utilization_rate=Decimal("0.785"),
            previous_utilization_rate=Decimal("0.781"),
            market_probability=Decimal("0.50"),
            threshold_probability=Decimal("0.50"),
            source_count=Decimal("1"),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        _observation(market_probability="1.01")

    with pytest.raises(ValueError, match="inputs must be a list or tuple"):
        build_market_research_capacity_utilization_surprise_digest(
            "bad",  # type: ignore[arg-type]
            config=CapacityUtilizationSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="inputs must contain CapacityUtilizationSurpriseInput values"):
        build_market_research_capacity_utilization_surprise_digest(
            [object()],  # type: ignore[list-item]
            config=CapacityUtilizationSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    report = build_market_research_capacity_utilization_surprise_digest(
        [_observation()],
        config=CapacityUtilizationSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="CapacityUtilizationSurpriseRow must be readonly"):
        replace(report.surprise_rows[0], readonly=False)
    with pytest.raises(ValueError, match="CapacityUtilizationSurpriseDigestReport must be paper_only"):
        replace(report, paper_only=False)


def test_module_exposes_no_durable_live_or_mutating_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_capacity_utilization_surprise_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "cancel(",
        "exchange",
    ):
        assert forbidden not in source.lower()
