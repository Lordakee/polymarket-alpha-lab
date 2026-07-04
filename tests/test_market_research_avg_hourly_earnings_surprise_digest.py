import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_avg_hourly_earnings_surprise_digest import (
    AvgHourlyEarningsSurpriseDigestConfig,
    AvgHourlyEarningsSurpriseInput,
    build_market_research_avg_hourly_earnings_surprise_digest,
)


def _observation(
    *,
    market_id: str = "avg-hourly-earnings-hot-print",
    release_at: datetime = datetime(2026, 2, 6, 8, 30, tzinfo=timezone(timedelta(hours=-5))),
    actual_avg_hourly_earnings_growth: Decimal | str = "0.004",
    consensus_avg_hourly_earnings_growth: Decimal | str = "0.003",
    previous_avg_hourly_earnings_growth: Decimal | str = "0.002",
    market_probability: Decimal | str = "0.64",
    threshold_probability: Decimal | str = "0.55",
    source_count: Decimal | str = "3",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> AvgHourlyEarningsSurpriseInput:
    return AvgHourlyEarningsSurpriseInput(
        market_id=market_id,
        release_at=release_at,
        actual_avg_hourly_earnings_growth=Decimal(actual_avg_hourly_earnings_growth),
        consensus_avg_hourly_earnings_growth=Decimal(consensus_avg_hourly_earnings_growth),
        previous_avg_hourly_earnings_growth=Decimal(previous_avg_hourly_earnings_growth),
        market_probability=Decimal(market_probability),
        threshold_probability=Decimal(threshold_probability),
        source_count=Decimal(source_count),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_digest_sorts_rows_normalizes_utc_and_emits_deterministic_reason_codes_and_ratios() -> None:
    report = build_market_research_avg_hourly_earnings_surprise_digest(
        [
            _observation(
                market_id="avg-hourly-earnings-cool-print",
                release_at=datetime(2026, 4, 3, 12, 30, tzinfo=UTC),
                actual_avg_hourly_earnings_growth="0.002",
                consensus_avg_hourly_earnings_growth="0.003",
                previous_avg_hourly_earnings_growth="0.003",
                market_probability="0.45",
                threshold_probability="0.55",
                source_count="2",
            ),
            _observation(),
            _observation(
                market_id="avg-hourly-earnings-inline-print",
                release_at=datetime(2026, 3, 6, 13, 30, tzinfo=UTC),
                actual_avg_hourly_earnings_growth="0.003",
                consensus_avg_hourly_earnings_growth="0.003",
                previous_avg_hourly_earnings_growth="0.002",
                market_probability="0.55",
                threshold_probability="0.55",
                source_count="1",
            ),
        ],
        config=AvgHourlyEarningsSurpriseDigestConfig(
            config_version="avg-hourly-earnings-surprise-v1",
        ),
        generated_at=datetime(2026, 5, 1, 9, 0, tzinfo=timezone(timedelta(hours=2))),
    )

    assert report.generated_at == datetime(2026, 5, 1, 7, 0, tzinfo=UTC)
    assert report.config_version == "avg-hourly-earnings-surprise-v1"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_avg_hourly_earnings_surprise_markets"
    assert report.input_count == Decimal("3")
    assert report.positive_surprise_count == Decimal("1")
    assert report.negative_surprise_count == Decimal("1")
    assert report.inline_count == Decimal("1")
    assert report.stale_release_count == Decimal("0")
    assert report.missing_evidence_count == Decimal("0")
    assert report.total_source_count == Decimal("6")
    assert report.positive_surprise_ratio == Decimal("0.333333")
    assert report.negative_surprise_ratio == Decimal("0.333333")
    assert report.market_probability_edge_ratio == Decimal("0.333333")
    assert report.largest_abs_surprise_market_id == "avg-hourly-earnings-cool-print"
    assert report.largest_abs_surprise_ratio == Decimal("0.333333")
    assert report.reason_codes == (
        "avg_hourly_earnings_surprise_negative_present",
        "avg_hourly_earnings_surprise_positive_present",
        "avg_hourly_earnings_surprise_probability_edge_present",
    )
    assert tuple(row.market_id for row in report.surprise_rows) == (
        "avg-hourly-earnings-hot-print",
        "avg-hourly-earnings-inline-print",
        "avg-hourly-earnings-cool-print",
    )
    assert report.surprise_rows[0].release_at == datetime(2026, 2, 6, 13, 30, tzinfo=UTC)
    assert report.surprise_rows[0].release_age_seconds == Decimal("7234200.000000")
    assert report.surprise_rows[0].surprise_growth_points == Decimal("0.001")
    assert report.surprise_rows[0].surprise_ratio == Decimal("0.333333")
    assert report.surprise_rows[0].market_probability_edge == Decimal("0.09")
    assert report.surprise_rows[0].surprise_direction == "positive"
    assert report.surprise_rows[0].reason_codes == (
        "avg_hourly_earnings_surprise_positive_present",
        "avg_hourly_earnings_surprise_probability_edge_present",
    )
    assert report.surprise_rows[1].surprise_direction == "inline"
    assert report.surprise_rows[2].surprise_direction == "negative"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(
        isinstance(getattr(report, field_name), Decimal)
        for field_name in (
            "input_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
            "stale_release_count",
            "missing_evidence_count",
            "total_source_count",
            "positive_surprise_ratio",
            "negative_surprise_ratio",
            "market_probability_edge_ratio",
            "largest_abs_surprise_ratio",
        )
    )
    assert all(
        isinstance(getattr(report.surprise_rows[0], field_name), Decimal)
        for field_name in (
            "actual_avg_hourly_earnings_growth",
            "consensus_avg_hourly_earnings_growth",
            "previous_avg_hourly_earnings_growth",
            "market_probability",
            "threshold_probability",
            "source_count",
            "release_age_seconds",
            "surprise_growth_points",
            "surprise_ratio",
            "market_probability_edge",
        )
    )
    import polymarket_alpha_lab.market_research_avg_hourly_earnings_surprise_digest as digest

    payload_fn = getattr(
        digest,
        "market_research_avg_hourly_earnings_surprise_digest_payload",
        None,
    )
    assert callable(payload_fn)
    payload = payload_fn(report)
    assert payload["generated_at"] == "2026-05-01T07:00:00+00:00"
    assert payload["input_count"] == "3.000000"
    assert payload["positive_surprise_ratio"] == "0.333333"
    assert payload["stale_release_count"] == "0.000000"
    assert payload["missing_evidence_count"] == "0.000000"
    assert payload["surprise_rows"][0]["release_at"] == "2026-02-06T13:30:00+00:00"
    assert payload["surprise_rows"][0]["release_age_seconds"] == "7234200.000000"
    assert payload["surprise_rows"][0]["source_count"] == "3.000000"
    assert payload["surprise_rows"][0]["surprise_growth_points"] == "0.001000"
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(
        hasattr(report, unsafe_name)
        for unsafe_name in ("auth", "wallet", "order", "private_key", "account", "persisted")
    )


def test_empty_digest_is_blocked_with_decimal_zero_counts_and_no_optional_ratios() -> None:
    report = build_market_research_avg_hourly_earnings_surprise_digest(
        (),
        config=AvgHourlyEarningsSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "collect_avg_hourly_earnings_surprise_inputs"
    assert report.input_count == Decimal("0")
    assert report.positive_surprise_count == Decimal("0")
    assert report.negative_surprise_count == Decimal("0")
    assert report.inline_count == Decimal("0")
    assert report.stale_release_count == Decimal("0")
    assert report.missing_evidence_count == Decimal("0")
    assert report.total_source_count == Decimal("0")
    assert report.positive_surprise_ratio is None
    assert report.negative_surprise_ratio is None
    assert report.market_probability_edge_ratio is None
    assert report.largest_abs_surprise_market_id is None
    assert report.largest_abs_surprise_ratio is None
    assert report.surprise_rows == ()
    assert report.reason_codes == ("avg_hourly_earnings_surprise_digest_empty",)


def test_dataclasses_are_frozen_and_reject_non_decimal_public_numbers() -> None:
    item = _observation()
    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="actual_avg_hourly_earnings_growth must be a Decimal"):
        AvgHourlyEarningsSurpriseInput(
            market_id="bad",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_avg_hourly_earnings_growth=0.004,  # type: ignore[arg-type]
            consensus_avg_hourly_earnings_growth=Decimal("0.003"),
            previous_avg_hourly_earnings_growth=Decimal("0.002"),
            market_probability=Decimal("0.50"),
            threshold_probability=Decimal("0.50"),
            source_count=Decimal("1"),
        )

    with pytest.raises(ValueError, match="source_count must be an integral Decimal"):
        _observation(source_count="1.5")

    with pytest.raises(ValueError, match="config_version must be the supported config version"):
        AvgHourlyEarningsSurpriseDigestConfig(config_version="unsupported")

    with pytest.raises(ValueError, match="max_release_age_seconds must be a Decimal"):
        AvgHourlyEarningsSurpriseDigestConfig(
            max_release_age_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="config must be an AvgHourlyEarningsSurpriseDigestConfig"):
        build_market_research_avg_hourly_earnings_surprise_digest(
            [item],
            config=object(),  # type: ignore[arg-type]
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    report = build_market_research_avg_hourly_earnings_surprise_digest(
        [item],
        config=AvgHourlyEarningsSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.surprise_rows[0].market_id = "changed"  # type: ignore[misc]


def test_rejects_naive_datetimes_false_hard_flags_probability_bounds_and_bad_collections() -> None:
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        _observation(release_at=datetime(2026, 1, 1))

    with pytest.raises(ValueError, match="AvgHourlyEarningsSurpriseInput must be paper_only"):
        _observation(paper_only=False)

    with pytest.raises(ValueError, match="AvgHourlyEarningsSurpriseInput must be report_only"):
        _observation(report_only=False)

    with pytest.raises(ValueError, match="AvgHourlyEarningsSurpriseInput must be readonly"):
        _observation(readonly=False)

    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        _observation(market_probability="1.01")

    with pytest.raises(ValueError, match="inputs must be a list or tuple"):
        build_market_research_avg_hourly_earnings_surprise_digest(
            "bad",  # type: ignore[arg-type]
            config=AvgHourlyEarningsSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="inputs must contain AvgHourlyEarningsSurpriseInput values"):
        build_market_research_avg_hourly_earnings_surprise_digest(
            [object()],  # type: ignore[list-item]
            config=AvgHourlyEarningsSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    report = build_market_research_avg_hourly_earnings_surprise_digest(
        [_observation()],
        config=AvgHourlyEarningsSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_stale_release_and_missing_evidence_are_report_only_blocking_reasons() -> None:
    generated_at = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    report = build_market_research_avg_hourly_earnings_surprise_digest(
        [
            _observation(
                market_id="avg-hourly-earnings-stale-hot",
                release_at=generated_at - timedelta(hours=2),
                actual_avg_hourly_earnings_growth="0.004",
                consensus_avg_hourly_earnings_growth="0.003",
                market_probability="0.64",
                threshold_probability="0.55",
                source_count="2",
            ),
            _observation(
                market_id="avg-hourly-earnings-missing-evidence",
                release_at=generated_at - timedelta(minutes=15),
                actual_avg_hourly_earnings_growth="0.003",
                consensus_avg_hourly_earnings_growth="0.003",
                market_probability="0.55",
                threshold_probability="0.55",
                source_count="0",
            ),
        ],
        config=AvgHourlyEarningsSurpriseDigestConfig(
            max_release_age_seconds=Decimal("3600.000000"),
            min_source_count=Decimal("1.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "collect_avg_hourly_earnings_surprise_evidence"
    assert report.stale_release_count == Decimal("1.000000")
    assert report.missing_evidence_count == Decimal("1.000000")
    assert report.reason_codes == (
        "avg_hourly_earnings_surprise_release_stale",
        "avg_hourly_earnings_surprise_missing_evidence",
        "avg_hourly_earnings_surprise_positive_present",
        "avg_hourly_earnings_surprise_probability_edge_present",
    )
    assert tuple(row.market_id for row in report.surprise_rows) == (
        "avg-hourly-earnings-stale-hot",
        "avg-hourly-earnings-missing-evidence",
    )
    assert report.surprise_rows[0].release_age_seconds == Decimal("7200.000000")
    assert report.surprise_rows[0].reason_codes == (
        "avg_hourly_earnings_surprise_release_stale",
        "avg_hourly_earnings_surprise_positive_present",
        "avg_hourly_earnings_surprise_probability_edge_present",
    )
    assert report.surprise_rows[1].release_age_seconds == Decimal("900.000000")
    assert report.surprise_rows[1].reason_codes == (
        "avg_hourly_earnings_surprise_missing_evidence",
    )


def test_module_has_no_io_secret_or_trading_mutation_surface() -> None:
    import polymarket_alpha_lab.market_research_avg_hourly_earnings_surprise_digest as digest

    assert digest.__all__ == (
        "DEFAULT_AVG_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION",
        "AvgHourlyEarningsSurpriseDigestConfig",
        "AvgHourlyEarningsSurpriseInput",
        "AvgHourlyEarningsSurpriseRow",
        "AvgHourlyEarningsSurpriseDigestReport",
        "build_market_research_avg_hourly_earnings_surprise_digest",
        "market_research_avg_hourly_earnings_surprise_digest_payload",
    )
    forbidden_names = (
        "account",
        "auth",
        "cancel",
        "db",
        "exchange",
        "network",
        "open",
        "order",
        "private_key",
        "replace",
        "requests",
        "session",
        "socket",
        "sqlite",
        "supabase",
        "trade",
        "wallet",
    )
    assert all(not hasattr(digest, name) for name in forbidden_names)

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_avg_hourly_earnings_surprise_digest.py",
    ).read_text(encoding="utf-8")
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
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
        "exchange",
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
    assert "private_key" not in source.lower()


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in _walk_values(nested))
    return (value,)
