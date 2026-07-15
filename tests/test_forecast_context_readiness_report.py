from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 11, 14, 30, tzinfo=UTC)


def api():
    return import_module("polymarket_alpha_lab.forecast_context_readiness_report")


def source(**overrides: object):
    values: dict[str, object] = {
        "source_label": "official_settlement_rules",
        "source_family": "official_rules",
        "citation": "official_rules_doc_2026_07_11",
        "published_at": GENERATED_AT - timedelta(hours=2),
        "captured_at": GENERATED_AT - timedelta(minutes=15),
        "stance": "neutral",
    }
    values.update(overrides)
    return api().ForecastContextSource(**values)


def readiness_input(**overrides: object):
    values: dict[str, object] = {
        "model_basis": "llm_glm_v0",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "context_captured_at": GENERATED_AT - timedelta(minutes=10),
        "sources": (
            source(source_family="official_rules", stance="neutral"),
            source(
                source_label="market_snapshot",
                source_family="market_data",
                citation="polymarket_snapshot_2026_07_11_1420z",
                stance="market_data",
            ),
        ),
        "fallback_path": "low_confidence_forecast",
    }
    values.update(overrides)
    return api().ForecastContextReadinessInput(**values)


def build_report(*inputs: object):
    module = api()
    return module.build_forecast_context_readiness_report(
        inputs or (readiness_input(),),
        generated_at=GENERATED_AT,
        config=module.ForecastContextReadinessConfig(),
    )


def row_at_model_basis_floor(model_basis: str, minimum: int):
    sources = tuple(
        source(
            source_label=f"public_context_{index}",
            source_family=f"public_family_{index}",
            citation=f"public_citation_{index}",
        )
        for index in range(minimum)
    )
    return build_report(
        readiness_input(model_basis=model_basis, sources=sources),
    ).rows[0]


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_ready_context_passes_for_naive_book_llm_and_superforecaster_models() -> None:
    report = build_report(
        readiness_input(
            model_basis="yes_ask_naive_v0",
            sources=(source(source_family="order_book", stance="market_data"),),
            fallback_path="low_confidence_forecast",
        ),
        readiness_input(
            model_basis="book_imbalance_v0",
            sources=(source(source_family="order_book", stance="market_data"),),
            fallback_path="low_confidence_forecast",
        ),
        readiness_input(model_basis="llm_glm_v0"),
        readiness_input(
            model_basis="superforecaster_prompt_v0",
            sources=(
                source(source_family="official_rules"),
                source(
                    source_label="base_rate_dataset",
                    source_family="base_rate",
                    citation="base_rate_sample_2026_07_11",
                    stance="neutral",
                ),
                source(
                    source_label="independent_news_check",
                    source_family="independent_research",
                    citation="independent_research_digest_2026_07_11",
                    stance="neutral",
                ),
            ),
            fallback_path="human_review_queue",
        ),
    )

    assert tuple(row.model_basis for row in report.rows) == (
        "yes_ask_naive_v0",
        "book_imbalance_v0",
        "llm_glm_v0",
        "superforecaster_prompt_v0",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "pass", "pass", "pass")
    for row in report.rows:
        assert row.readiness_score == Decimal("1.000000")
        assert "context_complete" in row.reason_codes
        assert "source_citations_ready" in row.reason_codes
        assert "source_timestamps_ready" in row.reason_codes
        assert "fallback_path_ready" in row.reason_codes
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True

    payload = report.payload
    assert payload["status"] == "pass"
    assert payload["rows"][2]["model_basis"] == "llm_glm_v0"
    assert payload["rows"][3]["source_count"] == "3"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_missing_source_citations_timestamps_and_fallback_block_forecast_readiness() -> None:
    report = build_report(
        readiness_input(
            model_basis="llm_glm_v0",
            context_captured_at=None,
            sources=(
                source(
                    citation=None,
                    published_at=None,
                    captured_at=None,
                    source_family="official_rules",
                ),
            ),
            fallback_path=None,
        ),
    )

    row = report.rows[0]
    assert row.status == "block"
    assert row.source_count == Decimal("1")
    assert row.cited_source_count == Decimal("0")
    assert row.timestamped_source_count == Decimal("0")
    assert row.fallback_path is None
    assert row.reason_codes == (
        "source_count_below_minimum",
        "source_family_count_below_minimum",
        "source_citation_missing",
        "source_timestamp_missing",
        "context_timestamp_missing",
        "fallback_path_missing",
        "public_status_block",
    )
    assert report.status == "block"


def test_conflicting_evidence_requires_explicit_resolution_before_forecast() -> None:
    unresolved = build_report(
        readiness_input(
            model_basis="superforecaster_prompt_v0",
            sources=(
                source(source_family="official_rules", stance="supports_yes"),
                source(
                    source_label="counter_evidence",
                    source_family="independent_research",
                    citation="counter_digest_2026_07_11",
                    stance="supports_no",
                ),
                source(
                    source_label="base_rate_dataset",
                    source_family="base_rate",
                    citation="base_rate_sample_2026_07_11",
                    stance="neutral",
                ),
            ),
            conflict_resolution=None,
            fallback_path="human_review_queue",
        ),
    )
    assert unresolved.rows[0].status == "block"
    assert "conflicting_evidence_unresolved" in unresolved.rows[0].reason_codes

    resolved = build_report(
        readiness_input(
            model_basis="superforecaster_prompt_v0",
            sources=(
                source(source_family="official_rules", stance="supports_yes"),
                source(
                    source_label="counter_evidence",
                    source_family="independent_research",
                    citation="counter_digest_2026_07_11",
                    stance="supports_no",
                ),
                source(
                    source_label="base_rate_dataset",
                    source_family="base_rate",
                    citation="base_rate_sample_2026_07_11",
                    stance="neutral",
                ),
            ),
            conflict_resolution="official_rules_outweigh_counter_digest",
            fallback_path="human_review_queue",
        ),
    )
    assert resolved.rows[0].status == "watch"
    assert resolved.rows[0].conflicting_evidence_count == Decimal("1")
    assert "conflicting_evidence_resolved" in resolved.rows[0].reason_codes
    assert resolved.status == "watch"


def test_unsafe_public_context_is_redacted_and_blocks_prompt_readiness() -> None:
    report = build_report(
        readiness_input(
            model_basis="llm_glm_v0",
            sources=(
                source(citation="api_token=secret"),
                source(
                    source_label="market_snapshot",
                    source_family="market_data",
                    citation="polymarket_snapshot_2026_07_11_1420z",
                    stance="market_data",
                ),
            ),
            fallback_path="skip_llm_forecast",
        ),
    )

    row = report.rows[0]
    assert row.status == "block"
    assert row.sources[0].citation == "<redacted>"
    assert "unsafe_public_content_redacted" in row.reason_codes
    assert "api_token" not in json.dumps(report.payload, sort_keys=True).lower()


def test_readiness_dataclasses_are_frozen_and_hard_readonly_flags_are_required() -> None:
    module = api()
    report = build_report()

    assert module.ForecastContextSource.__dataclass_params__.frozen
    assert module.ForecastContextReadinessInput.__dataclass_params__.frozen
    assert module.ForecastContextReadinessRow.__dataclass_params__.frozen
    assert module.ForecastContextReadinessReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report.rows[0], paper_only=False)


def test_rejects_unknown_models_and_non_tuple_sources() -> None:
    with pytest.raises(ValueError, match="model_basis must be a supported forecast basis"):
        readiness_input(model_basis="strategy_aggregator_v0")
    with pytest.raises(ValueError, match="sources must be a tuple"):
        readiness_input(sources=[source()])
    with pytest.raises(ValueError, match="stance must be one of"):
        source(stance="maybe")


@pytest.mark.parametrize(
    ("field_name", "value", "minimum"),
    (
        ("microstructure_min_source_count", "0", "1"),
        ("microstructure_min_source_family_count", "0", "1"),
        ("default_min_source_count", "1", "2"),
        ("default_min_source_family_count", "1", "2"),
        ("superforecaster_min_source_count", "2", "3"),
        ("superforecaster_min_source_family_count", "2", "3"),
    ),
)
def test_config_rejects_forecast_quorum_values_below_model_basis_floors(
    field_name: str,
    value: str,
    minimum: str,
) -> None:
    module = api()

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be at least {minimum}",
    ):
        module.ForecastContextReadinessConfig(
            **{field_name: Decimal(value)},
        )


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("llm_glm_v0", "2"),
        ("superforecaster_prompt_v0", "3"),
    ),
)
def test_direct_row_construction_rejects_relabeling_microstructure_quorum_below_model_floor(
    model_basis: str,
    minimum: str,
) -> None:
    module = api()
    microstructure_row = build_report(
        readiness_input(
            model_basis="yes_ask_naive_v0",
            sources=(source(source_family="order_book", stance="market_data"),),
        ),
    ).rows[0]
    values = dict(vars(microstructure_row))
    values["model_basis"] = model_basis

    with pytest.raises(
        ValueError,
        match=rf"minimum_source_count must be at least {minimum}",
    ):
        module.ForecastContextReadinessRow(**values)


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("llm_glm_v0", "2"),
        ("superforecaster_prompt_v0", "3"),
    ),
)
def test_replace_rejects_relabeling_microstructure_quorum_below_model_floor(
    model_basis: str,
    minimum: str,
) -> None:
    microstructure_row = build_report(
        readiness_input(
            model_basis="yes_ask_naive_v0",
            sources=(source(source_family="order_book", stance="market_data"),),
        ),
    ).rows[0]

    with pytest.raises(
        ValueError,
        match=rf"minimum_source_count must be at least {minimum}",
    ):
        replace(microstructure_row, model_basis=model_basis)


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("llm_glm_v0", "2"),
        ("superforecaster_prompt_v0", "3"),
    ),
)
def test_payloads_recheck_model_floor_after_row_model_basis_tampering(
    model_basis: str,
    minimum: str,
) -> None:
    module = api()
    report = build_report(
        readiness_input(
            model_basis="yes_ask_naive_v0",
            sources=(source(source_family="order_book", stance="market_data"),),
        ),
    )
    object.__setattr__(report.rows[0], "model_basis", model_basis)

    with pytest.raises(
        ValueError,
        match=rf"minimum_source_count must be at least {minimum}",
    ):
        report.rows[0].payload
    with pytest.raises(
        ValueError,
        match=rf"minimum_source_count must be at least {minimum}",
    ):
        report.payload
    with pytest.raises(
        ValueError,
        match=rf"minimum_source_count must be at least {minimum}",
    ):
        module.forecast_context_readiness_report_payload(report)


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("yes_ask_naive_v0", 1),
        ("book_imbalance_v0", 1),
        ("llm_glm_v0", 2),
        ("superforecaster_prompt_v0", 3),
    ),
)
@pytest.mark.parametrize(
    "field_name",
    ("minimum_source_count", "minimum_source_family_count"),
)
def test_direct_row_construction_enforces_each_model_basis_quorum_floor(
    model_basis: str,
    minimum: int,
    field_name: str,
) -> None:
    module = api()
    row = row_at_model_basis_floor(model_basis, minimum)
    values = dict(vars(row))
    values[field_name] = Decimal(minimum - 1)

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be at least {minimum}",
    ):
        module.ForecastContextReadinessRow(**values)


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("yes_ask_naive_v0", 1),
        ("book_imbalance_v0", 1),
        ("llm_glm_v0", 2),
        ("superforecaster_prompt_v0", 3),
    ),
)
@pytest.mark.parametrize(
    "field_name",
    ("minimum_source_count", "minimum_source_family_count"),
)
def test_replace_enforces_each_model_basis_quorum_floor(
    model_basis: str,
    minimum: int,
    field_name: str,
) -> None:
    row = row_at_model_basis_floor(model_basis, minimum)

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be at least {minimum}",
    ):
        replace(row, **{field_name: Decimal(minimum - 1)})


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("yes_ask_naive_v0", 1),
        ("book_imbalance_v0", 1),
        ("llm_glm_v0", 2),
        ("superforecaster_prompt_v0", 3),
    ),
)
@pytest.mark.parametrize(
    "field_name",
    ("minimum_source_count", "minimum_source_family_count"),
)
def test_all_serializers_enforce_each_model_basis_quorum_floor(
    model_basis: str,
    minimum: int,
    field_name: str,
) -> None:
    module = api()
    report = build_report(
        readiness_input(
            model_basis=model_basis,
            sources=row_at_model_basis_floor(model_basis, minimum).sources,
        ),
    )
    object.__setattr__(report.rows[0], field_name, Decimal(minimum - 1))

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be at least {minimum}",
    ):
        report.rows[0].payload
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be at least {minimum}",
    ):
        report.payload
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be at least {minimum}",
    ):
        module.forecast_context_readiness_report_payload(report)


@pytest.mark.parametrize(
    ("model_basis", "minimum"),
    (
        ("yes_ask_naive_v0", 1),
        ("book_imbalance_v0", 1),
        ("llm_glm_v0", 2),
        ("superforecaster_prompt_v0", 3),
    ),
)
def test_public_row_paths_allow_quorum_thresholds_above_model_basis_floor(
    model_basis: str,
    minimum: int,
) -> None:
    module = api()
    report = build_report(
        readiness_input(model_basis=model_basis, sources=()),
    )
    row = report.rows[0]
    stricter = Decimal(minimum + 1)
    values = dict(vars(row))
    values["minimum_source_count"] = stricter
    values["minimum_source_family_count"] = stricter

    constructed = module.ForecastContextReadinessRow(**values)
    replaced = replace(
        row,
        minimum_source_count=stricter,
        minimum_source_family_count=stricter,
    )
    assert constructed.minimum_source_count == stricter
    assert constructed.minimum_source_family_count == stricter
    assert replaced.minimum_source_count == stricter
    assert replaced.minimum_source_family_count == stricter

    object.__setattr__(row, "minimum_source_count", stricter)
    object.__setattr__(row, "minimum_source_family_count", stricter)
    assert row.payload["minimum_source_count"] == str(stricter)
    assert row.payload["minimum_source_family_count"] == str(stricter)
    assert report.payload["rows"][0]["minimum_source_count"] == str(stricter)
    serialized = module.forecast_context_readiness_report_payload(report)
    assert serialized["rows"][0]["minimum_source_family_count"] == str(stricter)


class DatetimeSubclass(datetime):
    pass


class MissingOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None


@pytest.mark.parametrize(
    "bad_datetime",
    (
        datetime(2026, 7, 11, 14, 30),
        DatetimeSubclass(2026, 7, 11, 14, 30, tzinfo=UTC),
        datetime(2026, 7, 11, 14, 30, tzinfo=MissingOffsetTimezone()),
    ),
)
@pytest.mark.parametrize(
    "target",
    (
        "published_at",
        "captured_at",
        "context_captured_at",
        "row_context_captured_at",
        "generated_at",
    ),
)
def test_all_datetime_fields_require_exact_timezone_aware_datetime_values(
    target: str,
    bad_datetime: datetime,
) -> None:
    module = api()

    with pytest.raises(ValueError, match="must be an exact timezone-aware datetime"):
        if target in ("published_at", "captured_at"):
            source(**{target: bad_datetime})
        elif target == "context_captured_at":
            readiness_input(context_captured_at=bad_datetime)
        elif target == "row_context_captured_at":
            replace(build_report().rows[0], context_captured_at=bad_datetime)
        else:
            module.build_forecast_context_readiness_report(
                (readiness_input(),),
                generated_at=bad_datetime,
                config=module.ForecastContextReadinessConfig(),
            )


def test_datetime_fields_are_normalized_to_utc_and_context_is_in_row_payload() -> None:
    offset = timezone(timedelta(hours=5, minutes=30))
    input_value = readiness_input(
        context_captured_at=(GENERATED_AT - timedelta(minutes=10)).astimezone(offset),
        sources=(
            source(
                published_at=(GENERATED_AT - timedelta(hours=2)).astimezone(offset),
                captured_at=(GENERATED_AT - timedelta(minutes=15)).astimezone(offset),
            ),
        ),
    )
    module = api()

    report = module.build_forecast_context_readiness_report(
        (input_value,),
        generated_at=GENERATED_AT.astimezone(offset),
        config=module.ForecastContextReadinessConfig(),
    )

    row = report.rows[0]
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert row.context_captured_at == GENERATED_AT - timedelta(minutes=10)
    assert row.context_captured_at.tzinfo is UTC
    assert row.sources[0].published_at == GENERATED_AT - timedelta(hours=2)
    assert row.sources[0].published_at.tzinfo is UTC
    assert row.sources[0].captured_at == GENERATED_AT - timedelta(minutes=15)
    assert row.sources[0].captured_at.tzinfo is UTC
    assert row.payload["context_captured_at"] == "2026-07-11T14:20:00+00:00"
    assert report.payload["rows"][0]["context_captured_at"] == (
        "2026-07-11T14:20:00+00:00"
    )


def test_source_published_at_must_not_be_later_than_captured_at() -> None:
    with pytest.raises(
        ValueError,
        match="published_at must not be later than captured_at",
    ):
        source(
            published_at=GENERATED_AT - timedelta(minutes=5),
            captured_at=GENERATED_AT - timedelta(minutes=10),
        )


@pytest.mark.parametrize("field_name", ("published_at", "captured_at"))
def test_source_times_must_not_be_later_than_context_capture(field_name: str) -> None:
    context_captured_at = GENERATED_AT - timedelta(minutes=10)
    source_overrides: dict[str, object] = {
        "published_at": None,
        "captured_at": None,
        field_name: context_captured_at + timedelta(seconds=1),
    }

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be later than context_captured_at",
    ):
        readiness_input(
            context_captured_at=context_captured_at,
            sources=(source(**source_overrides),),
        )


def test_context_capture_must_not_be_later_than_report_generation() -> None:
    context_captured_at = GENERATED_AT + timedelta(seconds=1)

    with pytest.raises(
        ValueError,
        match="context_captured_at must not be later than generated_at",
    ):
        build_report(
            readiness_input(
                context_captured_at=context_captured_at,
                sources=(
                    source(
                        published_at=context_captured_at - timedelta(minutes=2),
                        captured_at=context_captured_at - timedelta(minutes=1),
                    ),
                ),
            ),
        )


@pytest.mark.parametrize("field_name", ("published_at", "captured_at"))
def test_source_times_must_not_be_later_than_report_generation(
    field_name: str,
) -> None:
    source_overrides: dict[str, object] = {
        "published_at": None,
        "captured_at": None,
        field_name: GENERATED_AT + timedelta(seconds=1),
    }

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be later than generated_at",
    ):
        build_report(
            readiness_input(
                context_captured_at=None,
                sources=(source(**source_overrides),),
            ),
        )


def test_direct_report_construction_rechecks_all_row_times_against_generation() -> None:
    module = api()
    report = build_report()

    with pytest.raises(
        ValueError,
        match="context_captured_at must not be later than generated_at",
    ):
        replace(
            report,
            generated_at=report.rows[0].context_captured_at - timedelta(seconds=1),
        )

    row_without_context = build_report(
        readiness_input(context_captured_at=None),
    ).rows[0]
    with pytest.raises(
        ValueError,
        match="captured_at must not be later than generated_at",
    ):
        module.ForecastContextReadinessReport(
            generated_at=GENERATED_AT - timedelta(minutes=30),
            config_version=report.config_version,
            status=report.status,
            rows=(row_without_context,),
            reason_codes=report.reason_codes,
        )


def test_public_payload_rechecks_row_times_after_object_tampering() -> None:
    module = api()
    report = build_report()
    object.__setattr__(
        report.rows[0],
        "context_captured_at",
        report.generated_at + timedelta(seconds=1),
    )

    with pytest.raises(
        ValueError,
        match="context_captured_at must not be later than generated_at",
    ):
        report.payload
    with pytest.raises(
        ValueError,
        match="context_captured_at must not be later than generated_at",
    ):
        module.forecast_context_readiness_report_payload(report)


def test_row_rejects_forged_derived_fields_replayed_from_context() -> None:
    blocked_report = build_report(
        readiness_input(
            context_captured_at=None,
            sources=(),
            fallback_path=None,
        ),
    )
    row = blocked_report.rows[0]

    assert row.minimum_source_count == Decimal("2")
    assert row.minimum_source_family_count == Decimal("2")
    forged_pass_reasons = (
        "context_complete",
        "source_citations_ready",
        "source_timestamps_ready",
        "fallback_path_ready",
        "public_status_pass",
    )
    with pytest.raises(ValueError, match="status must match row context"):
        replace(
            row,
            status="pass",
            readiness_score=Decimal("1"),
            reason_codes=forged_pass_reasons,
        )

    mismatched_counts = {
        "source_count": Decimal("1"),
        "cited_source_count": Decimal("1"),
        "timestamped_source_count": Decimal("1"),
        "source_family_count": Decimal("1"),
        "conflicting_evidence_count": Decimal("1"),
    }
    for field_name, forged_value in mismatched_counts.items():
        with pytest.raises(ValueError, match=rf"{field_name} must match row context"):
            replace(row, **{field_name: forged_value})

    with pytest.raises(ValueError, match="readiness_score must match row context"):
        replace(row, readiness_score=Decimal("0.5"))
    with pytest.raises(ValueError, match="reason_codes must match row context"):
        replace(
            row,
            reason_codes=(
                "source_count_below_minimum",
                "public_status_block",
            ),
        )


def test_row_carries_custom_build_thresholds_and_payload_replays_them() -> None:
    module = api()
    report = module.build_forecast_context_readiness_report(
        (readiness_input(),),
        generated_at=GENERATED_AT,
        config=module.ForecastContextReadinessConfig(
            default_min_source_count=Decimal("3"),
            default_min_source_family_count=Decimal("3"),
        ),
    )
    row = report.rows[0]

    assert row.status == "block"
    assert row.minimum_source_count == Decimal("3")
    assert row.minimum_source_family_count == Decimal("3")
    assert row.payload["minimum_source_count"] == "3"
    assert row.payload["minimum_source_family_count"] == "3"
    with pytest.raises(ValueError, match="status must match row context"):
        replace(
            row,
            minimum_source_count=Decimal("2"),
            minimum_source_family_count=Decimal("2"),
        )

    object.__setattr__(row, "minimum_source_count", Decimal("2"))
    object.__setattr__(row, "minimum_source_family_count", Decimal("2"))
    with pytest.raises(ValueError, match="status must match row context"):
        report.payload


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("sources", (), "source_count must match row context"),
        ("context_captured_at", None, "status must match row context"),
        ("fallback_path", None, "status must match row context"),
    ),
)
def test_payload_replays_raw_row_context_after_object_setattr(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    report = build_report()
    object.__setattr__(report.rows[0], field_name, forged_value)

    with pytest.raises(ValueError, match=error_match):
        report.rows[0].payload
    with pytest.raises(ValueError, match=error_match):
        report.payload


def test_payload_replays_conflict_resolution_after_object_setattr() -> None:
    report = build_report(
        readiness_input(
            model_basis="superforecaster_prompt_v0",
            sources=(
                source(source_family="official_rules", stance="supports_yes"),
                source(
                    source_label="counter_evidence",
                    source_family="independent_research",
                    citation="counter_digest_2026_07_11",
                    stance="supports_no",
                ),
                source(
                    source_label="base_rate_dataset",
                    source_family="base_rate",
                    citation="base_rate_sample_2026_07_11",
                    stance="neutral",
                ),
            ),
            conflict_resolution="official_rules_outweigh_counter_digest",
        ),
    )
    assert report.rows[0].status == "watch"
    object.__setattr__(report.rows[0], "conflict_resolution", None)

    with pytest.raises(ValueError, match="status must match row context"):
        report.rows[0].payload
    with pytest.raises(ValueError, match="status must match row context"):
        report.payload


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        (
            "source_label",
            "api_token=TOPSECRET",
            "source_label must already be normalized public text",
        ),
        (
            "source_family",
            " external_research ",
            "source_family must contain canonical strings",
        ),
        (
            "source_family",
            "api_token=TOPSECRET",
            "source_family must already be normalized public text",
        ),
        (
            "source_family",
            7,
            "source_family must contain canonical strings",
        ),
        (
            "citation",
            " citation_with_spaces ",
            "citation must contain canonical strings",
        ),
        (
            "citation",
            "password=TOPSECRET",
            "citation must already be normalized public text",
        ),
        ("citation", 7, "citation must contain canonical strings"),
        ("stance", "maybe", "stance must be one of"),
        (
            "published_at",
            datetime(2026, 7, 11, 12, 30),
            "published_at must be an exact timezone-aware datetime",
        ),
        (
            "captured_at",
            DatetimeSubclass(2026, 7, 11, 14, 15, tzinfo=UTC),
            "captured_at must be an exact timezone-aware datetime",
        ),
        (
            "published_at",
            datetime(
                2026,
                7,
                11,
                13,
                30,
                tzinfo=timezone(timedelta(hours=1)),
            ),
            "published_at must already be normalized to UTC",
        ),
        (
            "published_at",
            GENERATED_AT - timedelta(minutes=14),
            "published_at must not be later than captured_at",
        ),
    ),
)
def test_all_payload_paths_reject_tampered_nested_sources(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    module = api()
    report = build_report()
    nested_source = report.rows[0].sources[0]
    object.__setattr__(nested_source, field_name, forged_value)

    with pytest.raises(ValueError, match=error_match):
        module._source_payload(nested_source)
    with pytest.raises(ValueError, match=error_match):
        report.rows[0].payload
    with pytest.raises(ValueError, match=error_match):
        report.payload
    with pytest.raises(ValueError, match=error_match):
        module.forecast_context_readiness_report_payload(report)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("source_count", Decimal("3"), "source_count must match row context"),
        ("cited_source_count", Decimal("1"), "cited_source_count must match row context"),
        (
            "timestamped_source_count",
            Decimal("1"),
            "timestamped_source_count must match row context",
        ),
        (
            "source_family_count",
            Decimal("3"),
            "source_family_count must match row context",
        ),
        (
            "conflicting_evidence_count",
            Decimal("1"),
            "conflicting_evidence_count must match row context",
        ),
        (
            "readiness_score",
            Decimal("0.5"),
            "readiness_score must match row context",
        ),
        ("status", "watch", "status must match row context"),
        (
            "reason_codes",
            ("context_complete", "public_status_pass"),
            "reason_codes must match row context",
        ),
    ),
)
def test_row_and_report_payloads_reject_object_setattr_derived_forgery(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    module = api()
    report = build_report()
    object.__setattr__(report.rows[0], field_name, forged_value)

    with pytest.raises(ValueError, match=error_match):
        report.rows[0].payload
    with pytest.raises(ValueError, match=error_match):
        report.payload
    with pytest.raises(ValueError, match=error_match):
        module.forecast_context_readiness_report_payload(report)


def test_report_rejects_forged_aggregate_status_and_reason_codes() -> None:
    module = api()
    report = build_report(
        readiness_input(
            context_captured_at=None,
            sources=(),
            fallback_path=None,
        ),
    )

    with pytest.raises(ValueError, match="status must match rows"):
        replace(
            report,
            status="pass",
            reason_codes=("context_complete", "public_status_pass"),
        )
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(
            report,
            reason_codes=("source_count_below_minimum", "public_status_block"),
        )

    object.__setattr__(report, "status", "pass")
    object.__setattr__(
        report,
        "reason_codes",
        ("context_complete", "public_status_pass"),
    )
    with pytest.raises(ValueError, match="status must match rows"):
        report.payload
    with pytest.raises(ValueError, match="status must match rows"):
        module.forecast_context_readiness_report_payload(report)


def test_public_dataclasses_cannot_be_subclassed() -> None:
    module = api()

    for public_dataclass in (
        module.ForecastContextReadinessConfig,
        module.ForecastContextSource,
        module.ForecastContextReadinessInput,
        module.ForecastContextReadinessRow,
        module.ForecastContextReadinessReport,
    ):
        with pytest.raises(TypeError, match="subclassing is not allowed"):
            type(f"Forbidden{public_dataclass.__name__}", (public_dataclass,), {})


def test_forecast_context_readiness_imports_stay_within_phase_1_boundary() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "forecast_context_readiness_report.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")

    allowed_modules = {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
    }
    forbidden_prefixes = (
        "http",
        "urllib",
        "requests",
        "supabase",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.strategy",
        "polymarket_alpha_lab.team_memory",
        "polymarket_alpha_lab.scraping",
        "polymarket_alpha_lab.execution",
        "polymarket_alpha_lab.auth",
    )
    assert set(imported_modules) <= allowed_modules
    assert not any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported_modules
        for prefix in forbidden_prefixes
    )
