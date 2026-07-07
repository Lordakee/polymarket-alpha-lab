from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module("polymarket_alpha_lab.research_data_source_quality_matrix")


def _config(**overrides: object) -> Any:
    api = _api()
    values = {
        "min_pass_quality_score": d("0.750000"),
        "min_watch_quality_score": d("0.500000"),
        "min_pass_reliability_score": d("0.750000"),
        "min_watch_reliability_score": d("0.500000"),
        "min_pass_audit_trail_score": d("0.750000"),
        "min_watch_audit_trail_score": d("0.500000"),
        "max_pass_refresh_frequency_minutes": d("1440.000000"),
        "max_watch_refresh_frequency_minutes": d("10080.000000"),
        "max_pass_coverage_gap_ratio": d("0.100000"),
        "max_watch_coverage_gap_ratio": d("0.350000"),
    }
    values.update(overrides)
    return api.ResearchDataSourceQualityMatrixConfig(**values)


def _observation(
    *,
    family: str = "independent",
    reliability_score: Decimal = d("0.800000"),
    audit_trail_score: Decimal = d("0.800000"),
    refresh_frequency_minutes: Decimal = d("120.000000"),
    coverage_gap_ratio: Decimal = d("0.050000"),
) -> Any:
    api = _api()
    return api.ResearchDataSourceQualityObservation(
        data_source_family=family,
        reliability_score=reliability_score,
        audit_trail_score=audit_trail_score,
        refresh_frequency_minutes=refresh_frequency_minutes,
        coverage_gap_ratio=coverage_gap_ratio,
    )


def _report(observations: tuple[Any, ...]) -> Any:
    api = _api()
    return api.build_research_data_source_quality_matrix(
        observations,
        config=_config(),
    )


def _walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.append(key)
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _assert_json_ready(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert type(key) is str
            _assert_json_ready(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_json_ready(nested)
        return
    assert value is None or type(value) in (str, bool)


def _assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (Decimal, int, float):
        pytest.fail(f"public payload numeric value was not serialized: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_public_numeric_scalars(nested)
    if isinstance(value, list):
        for nested in value:
            _assert_no_public_numeric_scalars(nested)


def test_quality_matrix_combines_reliability_audit_freshness_and_coverage() -> None:
    report = _report(
        (
            _observation(
                family="official",
                reliability_score=d("0.900000"),
                audit_trail_score=d("0.900000"),
                refresh_frequency_minutes=d("60.000000"),
                coverage_gap_ratio=d("0.000000"),
            ),
            _observation(
                family="independent",
                reliability_score=d("0.720000"),
                audit_trail_score=d("0.800000"),
                refresh_frequency_minutes=d("2000.000000"),
                coverage_gap_ratio=d("0.200000"),
            ),
            _observation(
                family="community",
                reliability_score=d("0.490000"),
                audit_trail_score=d("0.600000"),
                refresh_frequency_minutes=d("12000.000000"),
                coverage_gap_ratio=d("0.400000"),
            ),
        ),
    )

    assert report.status == "block"
    assert report.observation_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_composite_quality_score == d("0.703709")
    assert report.max_refresh_frequency_minutes == d("12000.000000")
    assert report.max_coverage_gap_ratio == d("0.400000")
    assert report.reason_codes == (
        "low_reliability_block",
        "stale_refresh_block",
        "coverage_gap_block",
        "low_reliability_watch",
        "stale_refresh_watch",
        "coverage_gap_watch",
        "data_source_quality_matrix_pass",
    )

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.matrix_key for row in report.rows) == (
        "redacted-data-source-001",
        "redacted-data-source-002",
        "redacted-data-source-003",
    )
    block_row, watch_row, pass_row = report.rows
    assert block_row.composite_quality_score == d("0.400000")
    assert block_row.reason_codes == (
        "low_reliability_block",
        "stale_refresh_block",
        "coverage_gap_block",
        "low_composite_block",
    )
    assert watch_row.refresh_frequency_score == d("0.801587")
    assert watch_row.coverage_score == d("0.800000")
    assert watch_row.composite_quality_score == d("0.772317")
    assert watch_row.reason_codes == (
        "low_reliability_watch",
        "stale_refresh_watch",
        "coverage_gap_watch",
    )
    assert pass_row.refresh_frequency_score == d("0.994048")
    assert pass_row.composite_quality_score == d("0.938810")
    assert pass_row.reason_codes == ("data_source_quality_matrix_pass",)
    assert all(
        type(value) is Decimal
        for value in (
            report.observation_count,
            report.average_composite_quality_score,
            block_row.composite_quality_score,
            watch_row.refresh_frequency_score,
            pass_row.coverage_score,
        )
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_quality_matrix_payload_is_public_redacted_and_deterministic() -> None:
    api = _api()
    observations = (
        _observation(family="official", reliability_score=d("0.950000")),
        _observation(
            family="community",
            reliability_score=d("0.510000"),
            audit_trail_score=d("0.510000"),
            refresh_frequency_minutes=d("9000.000000"),
            coverage_gap_ratio=d("0.340000"),
        ),
    )

    forward_payload = api.research_data_source_quality_matrix_payload(_report(observations))
    reverse_payload = api.research_data_source_quality_matrix_payload(
        _report(tuple(reversed(observations))),
    )

    assert forward_payload == reverse_payload
    assert len(forward_payload["derived_validation_digest"]) == 64
    assert forward_payload["paper_only"] is True
    assert forward_payload["report_only"] is True
    assert forward_payload["readonly"] is True
    assert forward_payload["rows"][0]["paper_only"] is True
    _assert_json_ready(forward_payload)
    _assert_no_public_numeric_scalars(forward_payload)
    json.dumps(forward_payload, sort_keys=True)

    forbidden_fragments = (
        "raw-candidate-42",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    public_surface = "\n".join(_walk_strings(forward_payload)).lower()
    for fragment in forbidden_fragments:
        assert fragment not in public_surface


def test_quality_matrix_rejects_unsafe_public_payload_mutations() -> None:
    api = _api()
    payload = api.research_data_source_quality_matrix_payload(
        _report((_observation(),)),
    )

    bad_key_payload = dict(payload)
    bad_key_payload["market_slug"] = "raw-market"
    with pytest.raises(ValueError, match="unsafe"):
        api.research_data_source_quality_matrix_payload(bad_key_payload)

    bad_value_payload = dict(payload)
    bad_value_payload["reason_codes"] = ["recommendation_to_buy"]
    with pytest.raises(ValueError, match="unsafe"):
        api.research_data_source_quality_matrix_payload(bad_value_payload)

    bad_url_payload = dict(payload)
    bad_url_payload["rows"] = [dict(payload["rows"][0], matrix_key="https://example.test")]
    with pytest.raises(ValueError, match="unsafe"):
        api.research_data_source_quality_matrix_payload(bad_url_payload)


def test_quality_matrix_enforces_exact_decimal_frozen_dataclasses_and_flags() -> None:
    api = _api()

    with pytest.raises(ValueError, match="Decimal"):
        _config(min_pass_quality_score=1)
    with pytest.raises(ValueError, match="Decimal"):
        _config(min_pass_quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="paper_only"):
        api.ResearchDataSourceQualityObservation(
            data_source_family="official",
            reliability_score=d("0.900000"),
            audit_trail_score=d("0.900000"),
            refresh_frequency_minutes=d("60.000000"),
            coverage_gap_ratio=d("0.000000"),
            paper_only=False,
        )

    row = _report((_observation(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class InvalidObservation(api.ResearchDataSourceQualityObservation):
            pass


def test_quality_matrix_has_no_network_or_persistence_imports() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_data_source_quality_matrix.py"
    )
    module_text = module_path.read_text()

    forbidden_imports = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in module_text
