from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_average_workweek_surprise_digest import (
    AverageWorkweekSurpriseDigestConfig,
    AverageWorkweekSurpriseInput,
    build_market_research_average_workweek_surprise_digest,
    market_research_average_workweek_surprise_digest_payload,
)


SOURCE_TZ = timezone(timedelta(hours=-5))
GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=timezone(timedelta(hours=3)))


def _input(
    *,
    market_id: str = "average-workweek-above-consensus",
    release_at: datetime = datetime(2026, 7, 3, 8, 30, tzinfo=SOURCE_TZ),
    actual_hours: Decimal | str = "34.5",
    consensus_hours: Decimal | str = "34.3",
    previous_hours: Decimal | str = "34.4",
    market_probability: Decimal | str = "0.64",
    threshold_probability: Decimal | str = "0.55",
    source_count: Decimal | str = "3",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> AverageWorkweekSurpriseInput:
    return AverageWorkweekSurpriseInput(
        market_id=market_id,
        release_at=release_at,
        actual_hours=Decimal(actual_hours),
        consensus_hours=Decimal(consensus_hours),
        previous_hours=Decimal(previous_hours),
        market_probability=Decimal(market_probability),
        threshold_probability=Decimal(threshold_probability),
        source_count=Decimal(source_count),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_average_workweek_digest_sorts_rows_normalizes_utc_and_emits_deterministic_reasons() -> None:
    report = build_market_research_average_workweek_surprise_digest(
        [
            _input(
                market_id="average-workweek-negative",
                release_at=datetime(2026, 8, 7, 12, 30, tzinfo=UTC),
                actual_hours="34.1",
                consensus_hours="34.4",
                previous_hours="34.3",
                market_probability="0.48",
                threshold_probability="0.55",
                source_count="2",
            ),
            _input(),
            _input(
                market_id="average-workweek-inline",
                release_at=datetime(2026, 7, 3, 13, 30, tzinfo=UTC),
                actual_hours="34.3",
                consensus_hours="34.3",
                previous_hours="34.4",
                market_probability="0.55",
                threshold_probability="0.55",
                source_count="1",
            ),
        ],
        config=AverageWorkweekSurpriseDigestConfig(
            config_version="average-workweek-surprise-test-v0",
        ),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    assert report.config_version == "average-workweek-surprise-test-v0"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_average_workweek_surprise_markets"
    assert report.input_count == Decimal("3")
    assert report.positive_surprise_count == Decimal("1")
    assert report.negative_surprise_count == Decimal("1")
    assert report.inline_count == Decimal("1")
    assert report.total_source_count == Decimal("6")
    assert report.stale_evidence_count == Decimal("0.000000")
    assert report.missing_evidence_count == Decimal("0.000000")
    assert report.max_evidence_age_seconds == Decimal("0.000000")
    assert report.positive_surprise_ratio == Decimal("0.333333")
    assert report.negative_surprise_ratio == Decimal("0.333333")
    assert report.market_probability_edge_ratio == Decimal("0.333333")
    assert report.largest_abs_surprise_market_id == "average-workweek-negative"
    assert report.largest_abs_surprise_ratio == Decimal("0.008721")
    assert report.reason_codes == (
        "average_workweek_surprise_negative_present",
        "average_workweek_surprise_positive_present",
        "average_workweek_surprise_probability_edge_present",
    )
    assert tuple(row.market_id for row in report.surprise_rows) == (
        "average-workweek-above-consensus",
        "average-workweek-inline",
        "average-workweek-negative",
    )
    assert report.surprise_rows[0].release_at == datetime(2026, 7, 3, 13, 30, tzinfo=UTC)
    assert report.surprise_rows[0].surprise_hours == Decimal("0.2")
    assert report.surprise_rows[0].surprise_ratio == Decimal("0.005830")
    assert report.surprise_rows[0].market_probability_edge == Decimal("0.09")
    assert report.surprise_rows[0].surprise_direction == "positive"
    assert report.surprise_rows[1].surprise_direction == "inline"
    assert report.surprise_rows[2].surprise_direction == "negative"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(
        type(getattr(report, field_name)) is Decimal
        for field_name in (
            "input_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
            "total_source_count",
            "stale_evidence_count",
            "missing_evidence_count",
            "max_evidence_age_seconds",
            "positive_surprise_ratio",
            "negative_surprise_ratio",
            "market_probability_edge_ratio",
            "largest_abs_surprise_ratio",
        )
    )
    assert all(
        type(getattr(report.surprise_rows[0], field_name)) is Decimal
        for field_name in (
            "actual_hours",
            "consensus_hours",
            "previous_hours",
            "market_probability",
            "threshold_probability",
            "source_count",
            "surprise_hours",
            "surprise_ratio",
            "market_probability_edge",
        )
    )


def test_empty_average_workweek_digest_is_blocked_with_decimal_zero_counts() -> None:
    report = build_market_research_average_workweek_surprise_digest(
        (),
        config=AverageWorkweekSurpriseDigestConfig(),
        generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "collect_average_workweek_surprise_inputs"
    assert report.input_count == Decimal("0")
    assert report.positive_surprise_count == Decimal("0")
    assert report.negative_surprise_count == Decimal("0")
    assert report.inline_count == Decimal("0")
    assert report.total_source_count == Decimal("0")
    assert report.stale_evidence_count == Decimal("0.000000")
    assert report.missing_evidence_count == Decimal("0.000000")
    assert report.max_evidence_age_seconds == Decimal("0.000000")
    assert report.positive_surprise_ratio is None
    assert report.negative_surprise_ratio is None
    assert report.market_probability_edge_ratio is None
    assert report.largest_abs_surprise_market_id is None
    assert report.largest_abs_surprise_ratio is None
    assert report.surprise_rows == ()
    assert report.reason_codes == ("average_workweek_surprise_digest_empty",)


def test_average_workweek_dataclasses_are_frozen_and_reject_non_decimal_public_numbers() -> None:
    item = _input()
    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="actual_hours must be a Decimal"):
        AverageWorkweekSurpriseInput(
            market_id="bad",
            release_at=datetime(2026, 7, 3, tzinfo=UTC),
            actual_hours=34.5,  # type: ignore[arg-type]
            consensus_hours=Decimal("34.3"),
            previous_hours=Decimal("34.4"),
            market_probability=Decimal("0.50"),
            threshold_probability=Decimal("0.50"),
            source_count=Decimal("1"),
        )

    with pytest.raises(ValueError, match="source_count must be an integral Decimal"):
        _input(source_count="1.5")

    with pytest.raises(ValueError, match="config must be an AverageWorkweekSurpriseDigestConfig"):
        build_market_research_average_workweek_surprise_digest(
            [item],
            config=object(),  # type: ignore[arg-type]
            generated_at=datetime(2026, 7, 3, tzinfo=UTC),
        )

    report = build_market_research_average_workweek_surprise_digest(
        [item],
        config=AverageWorkweekSurpriseDigestConfig(),
        generated_at=datetime(2026, 7, 3, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.surprise_rows[0].market_id = "changed"  # type: ignore[misc]


def test_average_workweek_rejects_naive_datetime_false_flags_probability_bounds_and_bad_collections() -> None:
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        _input(release_at=datetime(2026, 7, 3))

    with pytest.raises(ValueError, match="AverageWorkweekSurpriseInput must be paper_only"):
        AverageWorkweekSurpriseInput(
            market_id="unsafe",
            release_at=datetime(2026, 7, 3, tzinfo=UTC),
            actual_hours=Decimal("34.5"),
            consensus_hours=Decimal("34.3"),
            previous_hours=Decimal("34.4"),
            market_probability=Decimal("0.50"),
            threshold_probability=Decimal("0.50"),
            source_count=Decimal("1"),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="AverageWorkweekSurpriseInput must be report_only"):
        _input(report_only=False)

    with pytest.raises(ValueError, match="AverageWorkweekSurpriseInput must be readonly"):
        _input(readonly=False)

    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        _input(market_probability="1.01")

    with pytest.raises(ValueError, match="inputs must be a list or tuple"):
        build_market_research_average_workweek_surprise_digest(
            "bad",  # type: ignore[arg-type]
            config=AverageWorkweekSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 3, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="inputs must contain AverageWorkweekSurpriseInput values"):
        build_market_research_average_workweek_surprise_digest(
            [object()],  # type: ignore[list-item]
            config=AverageWorkweekSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 3, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="max_evidence_age_seconds must be positive"):
        AverageWorkweekSurpriseDigestConfig(
            max_evidence_age_seconds=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="min_source_count must be an integral Decimal"):
        AverageWorkweekSurpriseDigestConfig(
            min_source_count=Decimal("1.500000"),
        )

    with pytest.raises(ValueError, match="market_id/release_at values must be unique"):
        build_market_research_average_workweek_surprise_digest(
            [_input(), _input()],
            config=AverageWorkweekSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 3, 15, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="market_id must be public"):
        _input(market_id="average-workweek-secret-input")


def test_average_workweek_digest_payload_uses_six_decimal_strings_and_is_deterministic() -> None:
    inputs = (
        _input(
            market_id="average-workweek-later",
            release_at=datetime(2026, 7, 3, 9, 30, tzinfo=SOURCE_TZ),
            actual_hours="34.0",
            consensus_hours="34.2",
            previous_hours="34.3",
            market_probability="0.45",
            threshold_probability="0.55",
            source_count="2",
        ),
        _input(),
    )
    config = AverageWorkweekSurpriseDigestConfig()
    generated_at = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
    report = build_market_research_average_workweek_surprise_digest(
        inputs,
        config=config,
        generated_at=generated_at,
    )
    reversed_report = build_market_research_average_workweek_surprise_digest(
        tuple(reversed(inputs)),
        config=config,
        generated_at=generated_at,
    )

    payload = market_research_average_workweek_surprise_digest_payload(report)
    reversed_payload = market_research_average_workweek_surprise_digest_payload(reversed_report)

    assert payload == reversed_payload
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["input_count"] == "2.000000"
    assert payload["total_source_count"] == "5.000000"
    assert payload["positive_surprise_ratio"] == "0.500000"
    assert payload["max_evidence_age_seconds"] == "9000.000000"
    assert payload["surprise_rows"][0]["actual_hours"] == "34.500000"
    assert payload["surprise_rows"][0]["source_count"] == "3.000000"
    assert payload["surprise_rows"][0]["surprise_hours"] == "0.200000"
    assert payload["surprise_rows"][0]["surprise_ratio"] == "0.005830"
    assert payload["surprise_rows"][0]["release_at"] == "2026-07-03T13:30:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _payload_has_no_decimal_values(payload)


def test_average_workweek_digest_marks_stale_and_missing_evidence() -> None:
    report = build_market_research_average_workweek_surprise_digest(
        (
            _input(
                market_id="average-workweek-stale",
                release_at=datetime(2026, 7, 3, 8, 30, tzinfo=SOURCE_TZ),
                actual_hours="34.3",
                consensus_hours="34.3",
                market_probability="0.55",
                threshold_probability="0.55",
                source_count="2",
            ),
            _input(
                market_id="average-workweek-missing-source",
                release_at=datetime(2026, 7, 3, 15, 30, tzinfo=UTC),
                actual_hours="34.5",
                consensus_hours="34.3",
                market_probability="0.64",
                threshold_probability="0.55",
                source_count="0",
            ),
        ),
        config=AverageWorkweekSurpriseDigestConfig(
            max_evidence_age_seconds=Decimal("3600.000000"),
            min_source_count=Decimal("1.000000"),
        ),
        generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=UTC),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "repair_average_workweek_surprise_evidence"
    assert report.stale_evidence_count == Decimal("1.000000")
    assert report.missing_evidence_count == Decimal("1.000000")
    assert report.max_evidence_age_seconds == Decimal("9000.000000")
    assert report.reason_codes == (
        "average_workweek_surprise_positive_present",
        "average_workweek_surprise_probability_edge_present",
        "average_workweek_surprise_stale_evidence_present",
        "average_workweek_surprise_missing_evidence_present",
    )


def test_average_workweek_digest_is_pure_in_memory_report_only_surface() -> None:
    import polymarket_alpha_lab.market_research_average_workweek_surprise_digest as digest

    forbidden_names = (
        "account",
        "auth",
        "cancel",
        "db",
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
    assert digest.__all__ == (
        "AverageWorkweekSurpriseDigestConfig",
        "AverageWorkweekSurpriseInput",
        "AverageWorkweekSurpriseRow",
        "AverageWorkweekSurpriseDigestReport",
        "build_market_research_average_workweek_surprise_digest",
        "market_research_average_workweek_surprise_digest_payload",
    )
    source = Path(
        "src/polymarket_alpha_lab/market_research_average_workweek_surprise_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_import_roots = (
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "supabase",
        "urllib",
        "web3",
    )
    banned_calls = {
        "cancel",
        "commit",
        "compile",
        "connect",
        "delete",
        "eval",
        "exec",
        "open",
        "post",
        "put",
        "request",
        "send",
        "submit",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = tuple(alias.name for alias in node.names)
            module = getattr(node, "module", "") or ""
            assert not any(name.startswith(banned_import_roots) for name in imported)
            assert not any(module.startswith(name) for name in banned_import_roots)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_calls

    lowered = source.lower()
    for fragment in (
        "cancel_order",
        "httpx",
        "place_order",
        "private_key",
        "psycopg",
        "replace_order",
        "requests.",
        "socket.",
        "sqlite",
        "supabase",
        "wallet",
    ):
        assert fragment not in lowered

    public_numeric_fields = {
        field.name
        for cls in (
            AverageWorkweekSurpriseDigestConfig,
            AverageWorkweekSurpriseInput,
            digest.AverageWorkweekSurpriseRow,
            digest.AverageWorkweekSurpriseDigestReport,
        )
        for field in fields(cls)
        if any(
            token in field.name
            for token in (
                "count",
                "edge",
                "hours",
                "probability",
                "ratio",
                "seconds",
            )
        )
    }
    assert public_numeric_fields
    assert all(
        getattr(
            digest.AverageWorkweekSurpriseDigestConfig(),
            name,
            getattr(_input(), name, None),
        )
        is None
        or type(
            getattr(
                digest.AverageWorkweekSurpriseDigestConfig(),
                name,
                getattr(_input(), name, None),
            ),
        )
        is Decimal
        for name in public_numeric_fields
        if name not in {"surprise_rows"}
    )


def _payload_has_no_decimal_values(value: object) -> bool:
    if type(value) is dict:
        return all(_payload_has_no_decimal_values(item) for item in value.values())
    if type(value) is list:
        return all(_payload_has_no_decimal_values(item) for item in value)
    return type(value) is not Decimal
