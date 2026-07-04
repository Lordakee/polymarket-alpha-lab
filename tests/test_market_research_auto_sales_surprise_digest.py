from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_auto_sales_surprise_digest import (
    AutoSalesSurpriseInput,
    AutoSalesSurpriseObservation,
    AutoSalesSurpriseReport,
    build_market_research_auto_sales_surprise_digest,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_OBSERVED_AT = datetime(2026, 7, 3, 8, 30, tzinfo=SOURCE_TZ)


def d(value: str) -> Decimal:
    return Decimal(value)


def _observation(
    release_id: str,
    *,
    actual: str,
    consensus: str,
    previous: str,
    observed_at: datetime = SOURCE_OBSERVED_AT,
) -> AutoSalesSurpriseObservation:
    return AutoSalesSurpriseObservation(
        release_id=release_id,
        market_slug=f"us-auto-sales-{release_id}",
        observed_at=observed_at,
        actual_sales=Decimal(actual),
        consensus_sales=Decimal(consensus),
        previous_sales=Decimal(previous),
        source_name="commerce_release",
    )


def test_auto_sales_surprise_digest_reduces_inputs_deterministically() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation(
                "2026-06",
                actual="16.2",
                consensus="15.8",
                previous="15.9",
            ),
            _observation(
                "2026-05",
                actual="15.1",
                consensus="15.7",
                previous="15.4",
            ),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("0.03"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "auto-sales-surprise-test-v0"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_auto_sales_surprise"
    assert [row.release_id for row in report.observations] == ["2026-05", "2026-06"]
    assert report.observation_count == Decimal("2")
    assert report.material_surprise_count == Decimal("1")
    assert report.positive_surprise_count == Decimal("0")
    assert report.negative_surprise_count == Decimal("1")
    assert report.largest_abs_surprise_ratio == Decimal("0.038217")
    assert report.average_surprise_ratio == Decimal("-0.006450")
    assert report.reason_codes == (
        "auto_sales_material_negative_surprise",
        "auto_sales_watch",
    )
    assert report.reason_code_counts == (
        ("auto_sales_material_negative_surprise", Decimal("1")),
        ("auto_sales_watch", Decimal("1")),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.observed_at.tzinfo is UTC for row in report.observations)
    assert all(type(value) is Decimal for value in (
        report.observation_count,
        report.material_surprise_count,
        report.positive_surprise_count,
        report.negative_surprise_count,
        report.largest_abs_surprise_ratio,
        report.average_surprise_ratio,
    ))
    assert all(
        value.as_tuple().exponent == -6
        for value in (
            report.observation_count,
            report.material_surprise_count,
            report.positive_surprise_count,
            report.negative_surprise_count,
            report.largest_abs_surprise_ratio,
            report.average_surprise_ratio,
        )
    )


def test_auto_sales_surprise_digest_passes_when_surprises_are_immaterial() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation(
                "2026-06",
                actual="15.95",
                consensus="15.90",
                previous="15.80",
            ),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("0.03"),
        ),
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == "continue_monitoring_auto_sales"
    assert report.reason_codes == ("auto_sales_no_material_surprise",)
    assert report.reason_code_counts == (
        ("auto_sales_no_material_surprise", Decimal("1")),
    )


def test_auto_sales_surprise_digest_counts_material_positive_surprise() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation(
                "2026-06",
                actual="16.4",
                consensus="15.8",
                previous="15.9",
            ),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
    )

    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_auto_sales_surprise"
    assert report.material_surprise_count == d("1.000000")
    assert report.positive_surprise_count == d("1.000000")
    assert report.negative_surprise_count == d("0.000000")
    assert report.largest_abs_surprise_ratio == d("0.037975")
    assert report.average_surprise_ratio == d("0.037975")
    assert report.reason_codes == (
        "auto_sales_material_positive_surprise",
        "auto_sales_watch",
    )
    assert report.reason_code_counts == (
        ("auto_sales_material_positive_surprise", d("1.000000")),
        ("auto_sales_watch", d("1.000000")),
    )


def test_auto_sales_surprise_digest_blocks_on_missing_consensus_denominator() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation(
                "2026-06",
                actual="15.95",
                consensus="0",
                previous="15.80",
            ),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("0.03"),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "repair_auto_sales_consensus_inputs"
    assert report.reason_codes == (
        "auto_sales_blocked_missing_consensus",
        "auto_sales_no_material_surprise",
    )
    assert report.reason_code_counts == (
        ("auto_sales_blocked_missing_consensus", Decimal("1")),
        ("auto_sales_no_material_surprise", Decimal("1")),
    )
    assert report.average_surprise_ratio == Decimal("0")


def test_auto_sales_surprise_empty_digest_blocks_as_missing_evidence() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "repair_auto_sales_consensus_inputs"
    assert report.observation_count == d("0.000000")
    assert report.material_surprise_count == d("0.000000")
    assert report.reason_codes == ("auto_sales_blocked_missing_evidence",)
    assert report.reason_code_counts == (
        ("auto_sales_blocked_missing_evidence", d("1.000000")),
    )
    assert report.observations == ()


def test_auto_sales_surprise_stale_observation_is_watch_reason() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation(
                "2026-06",
                actual="15.95",
                consensus="15.90",
                previous="15.80",
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
            max_observation_age_seconds=d("3600.000000"),
        ),
    )

    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_auto_sales_surprise"
    assert report.reason_codes == (
        "auto_sales_no_material_surprise",
        "auto_sales_stale_observation",
        "auto_sales_watch",
    )
    assert report.reason_code_counts == (
        ("auto_sales_no_material_surprise", d("1.000000")),
        ("auto_sales_stale_observation", d("1.000000")),
        ("auto_sales_watch", d("1.000000")),
    )


def test_auto_sales_surprise_payload_serializes_six_decimal_strings_and_utc() -> None:
    digest = importlib.import_module(
        "polymarket_alpha_lab.market_research_auto_sales_surprise_digest",
    )
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation(
                "2026-06",
                actual="16.2",
                consensus="15.8",
                previous="15.9",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
    )

    assert hasattr(digest, "market_research_auto_sales_surprise_digest_payload")
    payload = digest.market_research_auto_sales_surprise_digest_payload(report)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["largest_abs_surprise_ratio"] == "0.025316"
    assert payload["average_surprise_ratio"] == "0.025316"
    assert payload["observations"][0]["actual_sales"] == "16.200000"
    assert payload["observations"][0]["observed_at"] == "2026-07-03T12:30:00+00:00"
    assert payload["reason_code_counts"][0][1] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, (float, Decimal)) for value in _walk_values(payload))


def test_auto_sales_surprise_dataclasses_are_frozen_and_normalize_utc() -> None:
    observation = _observation(
        "2026-06",
        actual="16.2",
        consensus="15.8",
        previous="15.9",
    )

    assert observation.observed_at == datetime(2026, 7, 3, 12, 30, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        observation.paper_only = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("actual_sales", 16),
        ("actual_sales", "16"),
        ("consensus_sales", 15.8),
        ("previous_sales", None),
    ),
)
def test_auto_sales_surprise_observation_requires_decimal_public_numbers(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        "release_id": "2026-06",
        "market_slug": "us-auto-sales-2026-06",
        "observed_at": GENERATED_AT,
        "actual_sales": Decimal("16.2"),
        "consensus_sales": Decimal("15.8"),
        "previous_sales": Decimal("15.9"),
        "source_name": "commerce_release",
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        AutoSalesSurpriseObservation(**kwargs)


def test_auto_sales_surprise_rejects_naive_datetime_and_false_safety_flags() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            "2026-06",
            actual="16.2",
            consensus="15.8",
            previous="15.9",
            observed_at=datetime(2026, 7, 3, 12, 30),
        )

    with pytest.raises(ValueError, match="paper_only"):
        AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("0.03"),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="report_only"):
        AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("0.03"),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("0.03"),
            readonly=False,
        )


def test_auto_sales_surprise_validation_rejects_nonfinite_and_unsafe_values() -> None:
    with pytest.raises(ValueError, match="material_surprise_threshold"):
        AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=Decimal("NaN"),
        )
    with pytest.raises(ValueError, match="max_observation_age_seconds"):
        AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            max_observation_age_seconds=Decimal("Infinity"),
        )
    with pytest.raises(ValueError, match="source_name"):
        AutoSalesSurpriseObservation(
            release_id="2026-06",
            market_slug="us-auto-sales-2026-06",
            observed_at=GENERATED_AT,
            actual_sales=d("16.200000"),
            consensus_sales=d("15.800000"),
            previous_sales=d("15.900000"),
            source_name="vendor_token_secret",
        )
    with pytest.raises(ValueError, match="observations"):
        build_market_research_auto_sales_surprise_digest(
            (_observation("2026-06", actual="16.2", consensus="15.8", previous="15.9"),)
            * 2,
            generated_at=GENERATED_AT,
            config=AutoSalesSurpriseInput(
                config_version="auto-sales-surprise-test-v0",
                material_surprise_threshold=d("0.030000"),
            ),
        )


def test_auto_sales_surprise_report_consistency_validation() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation("2026-06", actual="16.4", consensus="15.8", previous="15.9"),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
    )

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="allow_live_auto_sales_trade")
    with pytest.raises(ValueError, match="observations"):
        replace(report, observations=tuple(reversed((report.observations * 2))))
    with pytest.raises(ValueError, match="report"):
        digest = importlib.import_module(
            "polymarket_alpha_lab.market_research_auto_sales_surprise_digest",
        )
        digest.market_research_auto_sales_surprise_digest_payload(object())


def test_auto_sales_surprise_digest_is_pure_in_memory_report_only_surface() -> None:
    digest = importlib.import_module(
        "polymarket_alpha_lab.market_research_auto_sales_surprise_digest",
    )
    source = digest.__loader__.get_source(digest.__name__)
    assert source is not None
    tree = ast.parse(source)
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation("2026-06", actual="16.2", consensus="15.8", previous="15.9"),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
    )
    serialized_report = repr(asdict(report)).lower()

    forbidden_names = (
        "auth",
        "db",
        "network",
        "open",
        "order",
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
        "AutoSalesSurpriseInput",
        "AutoSalesSurpriseObservation",
        "AutoSalesSurpriseReport",
        "build_market_research_auto_sales_surprise_digest",
        "market_research_auto_sales_surprise_digest_payload",
    )

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
        "cancel",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "getenv",
        "open",
        "replace",
        "rollback",
        "send",
        "submit",
        "trade",
        "write",
    }
    forbidden_report_tokens = (
        "auth",
        "key",
        "private",
        "secret",
        "token",
        "wallet",
    )

    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)
    assert not any(token in serialized_report for token in forbidden_report_tokens)


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in _walk_values(nested))
    return (value,)


def test_auto_sales_surprise_public_numeric_fields_are_decimals() -> None:
    report = build_market_research_auto_sales_surprise_digest(
        (
            _observation("2026-06", actual="16.2", consensus="15.8", previous="15.9"),
        ),
        generated_at=GENERATED_AT,
        config=AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
    )
    for value in (
        AutoSalesSurpriseInput(
            config_version="auto-sales-surprise-test-v0",
            material_surprise_threshold=d("0.030000"),
        ),
        report.observations[0],
        report,
    ):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if (
                field.name.endswith("_sales")
                or field.name.endswith("_ratio")
                or field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_threshold")
            ):
                assert type(field_value) is Decimal, field.name
