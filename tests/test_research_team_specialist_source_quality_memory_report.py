from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import importlib
from pathlib import Path
from typing import Any, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_source_quality_memory_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_source_quality_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "min_pass_source_quality_ratio": d("0.800000"),
        "min_watch_source_quality_ratio": d("0.600000"),
        "min_pass_memory_recall_ratio": d("0.750000"),
        "min_watch_memory_recall_ratio": d("0.500000"),
        "max_pass_stale_memory_ratio": d("0.100000"),
        "max_watch_stale_memory_ratio": d("0.250000"),
        "min_pass_quality_memory_alignment_ratio": d("0.700000"),
        "min_watch_quality_memory_alignment_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistSourceQualityMemoryConfig(**values)


def observation(
    team_ref: str = "team.alpha",
    specialist_ref: str = "specialist.macro",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    source_quality_check_count: Decimal = d("10.000000"),
    source_quality_pass_count: Decimal = d("9.000000"),
    memory_recall_check_count: Decimal = d("10.000000"),
    memory_recall_pass_count: Decimal = d("8.000000"),
    memory_item_count: Decimal = d("10.000000"),
    stale_memory_item_count: Decimal = d("1.000000"),
    quality_memory_link_count: Decimal = d("10.000000"),
    validated_quality_memory_link_count: Decimal = d("8.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchTeamSpecialistSourceQualityMemoryObservation(
        team_ref=team_ref,
        specialist_ref=specialist_ref,
        observed_at=observed_at,
        source_quality_check_count=source_quality_check_count,
        source_quality_pass_count=source_quality_pass_count,
        memory_recall_check_count=memory_recall_check_count,
        memory_recall_pass_count=memory_recall_pass_count,
        memory_item_count=memory_item_count,
        stale_memory_item_count=stale_memory_item_count,
        quality_memory_link_count=quality_memory_link_count,
        validated_quality_memory_link_count=validated_quality_memory_link_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_source_quality_memory_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(payload)


def key_first(payload: dict[str, Any], key: str) -> dict[str, Any]:
    return {key: payload[key], **{name: value for name, value in payload.items() if name != key}}


def observation_with_ratios(
    team_ref: str,
    specialist_ref: str,
    *,
    source_quality_ratio: Decimal = d("0.900000"),
    memory_recall_ratio: Decimal = d("0.800000"),
    stale_memory_ratio: Decimal = d("0.100000"),
    quality_memory_alignment_ratio: Decimal = d("0.800000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
):
    denominator = d("1000000.000000")
    return observation(
        team_ref,
        specialist_ref,
        observed_at=observed_at,
        source_quality_check_count=denominator,
        source_quality_pass_count=source_quality_ratio * denominator,
        memory_recall_check_count=denominator,
        memory_recall_pass_count=memory_recall_ratio * denominator,
        memory_item_count=denominator,
        stale_memory_item_count=stale_memory_ratio * denominator,
        quality_memory_link_count=denominator,
        validated_quality_memory_link_count=quality_memory_alignment_ratio
        * denominator,
    )


def public_dataclass_values(value: object) -> dict[str, object]:
    return {item.name: getattr(value, item.name) for item in fields(value)}


def test_empty_observations_block_as_readonly_report_only_memory_gap() -> None:
    module = api()

    source_quality_memory = report()

    assert type(source_quality_memory) is module.ResearchTeamSpecialistSourceQualityMemoryReport
    assert module.RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert source_quality_memory.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_CONFIG_VERSION
    )
    assert source_quality_memory.status == "block"
    assert source_quality_memory.next_review_step == (
        "block_source_quality_memory_reuse_until_review"
    )
    assert source_quality_memory.observation_count == d("0.000000")
    assert source_quality_memory.team_count == d("0.000000")
    assert source_quality_memory.specialist_count == d("0.000000")
    assert source_quality_memory.source_quality_check_count == d("0.000000")
    assert source_quality_memory.source_quality_pass_count == d("0.000000")
    assert source_quality_memory.memory_recall_check_count == d("0.000000")
    assert source_quality_memory.memory_recall_pass_count == d("0.000000")
    assert source_quality_memory.memory_item_count == d("0.000000")
    assert source_quality_memory.stale_memory_item_count == d("0.000000")
    assert source_quality_memory.quality_memory_link_count == d("0.000000")
    assert source_quality_memory.validated_quality_memory_link_count == d("0.000000")
    assert source_quality_memory.pass_count == d("0.000000")
    assert source_quality_memory.watch_count == d("0.000000")
    assert source_quality_memory.block_count == d("0.000000")
    assert source_quality_memory.source_quality_ratio == d("0.000000")
    assert source_quality_memory.memory_recall_ratio == d("0.000000")
    assert source_quality_memory.stale_memory_ratio == d("0.000000")
    assert source_quality_memory.quality_memory_alignment_ratio == d("0.000000")
    assert source_quality_memory.source_quality_memory_score == d("0.000000")
    assert source_quality_memory.rows == ()
    assert source_quality_memory.reason_codes == ("source_quality_memory_no_observations",)
    assert source_quality_memory.reason_code_counts == (
        module.ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount(
            reason_code="source_quality_memory_no_observations",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert source_quality_memory.paper_only is True
    assert source_quality_memory.report_only is True
    assert source_quality_memory.readonly is True
    assert len(source_quality_memory.derived_validation_digest) == 64

    payload = module.research_team_specialist_source_quality_memory_report_payload(
        source_quality_memory,
    )
    assert module.research_team_specialist_source_quality_memory_report_payload(
        json.loads(json.dumps(payload)),
    ) == payload


def test_report_aggregates_statuses_and_quality_memory_scores() -> None:
    source_quality_memory = report(
        observation(
            "team.gamma",
            "specialist.blocked",
            source_quality_pass_count=d("4.000000"),
            memory_recall_pass_count=d("4.000000"),
            stale_memory_item_count=d("4.000000"),
            validated_quality_memory_link_count=d("4.000000"),
        ),
        observation(
            "team.beta",
            "specialist.watch",
            source_quality_pass_count=d("7.000000"),
            memory_recall_pass_count=d("6.000000"),
            stale_memory_item_count=d("2.000000"),
            validated_quality_memory_link_count=d("6.000000"),
        ),
        observation(
            "team.alpha",
            "specialist.pass",
            source_quality_pass_count=d("9.000000"),
            memory_recall_pass_count=d("8.000000"),
            stale_memory_item_count=d("1.000000"),
            validated_quality_memory_link_count=d("8.000000"),
        ),
    )

    assert source_quality_memory.status == "block"
    assert source_quality_memory.next_review_step == (
        "block_source_quality_memory_reuse_until_review"
    )
    assert source_quality_memory.observation_count == d("3.000000")
    assert source_quality_memory.team_count == d("3.000000")
    assert source_quality_memory.specialist_count == d("3.000000")
    assert source_quality_memory.source_quality_check_count == d("30.000000")
    assert source_quality_memory.source_quality_pass_count == d("20.000000")
    assert source_quality_memory.memory_recall_check_count == d("30.000000")
    assert source_quality_memory.memory_recall_pass_count == d("18.000000")
    assert source_quality_memory.memory_item_count == d("30.000000")
    assert source_quality_memory.stale_memory_item_count == d("7.000000")
    assert source_quality_memory.quality_memory_link_count == d("30.000000")
    assert source_quality_memory.validated_quality_memory_link_count == d("18.000000")
    assert source_quality_memory.pass_count == d("1.000000")
    assert source_quality_memory.watch_count == d("1.000000")
    assert source_quality_memory.block_count == d("1.000000")
    assert source_quality_memory.source_quality_ratio == d("0.666667")
    assert source_quality_memory.memory_recall_ratio == d("0.600000")
    assert source_quality_memory.stale_memory_ratio == d("0.233333")
    assert source_quality_memory.quality_memory_alignment_ratio == d("0.600000")
    assert source_quality_memory.source_quality_memory_score == d("0.658333")
    assert source_quality_memory.reason_codes == (
        "source_quality_memory_block_present",
        "source_quality_memory_watch_present",
        "source_quality_gap_present",
        "memory_recall_gap_present",
        "stale_memory_gap_present",
        "quality_memory_alignment_gap_present",
    )

    assert tuple((row.team_ref, row.specialist_ref, row.status) for row in source_quality_memory.rows) == (
        ("team.gamma", "specialist.blocked", "block"),
        ("team.beta", "specialist.watch", "watch"),
        ("team.alpha", "specialist.pass", "pass"),
    )
    blocked, watched, passed = source_quality_memory.rows
    assert blocked.source_quality_ratio == d("0.400000")
    assert blocked.memory_recall_ratio == d("0.400000")
    assert blocked.stale_memory_ratio == d("0.400000")
    assert blocked.quality_memory_alignment_ratio == d("0.400000")
    assert blocked.source_quality_memory_score == d("0.450000")
    assert blocked.reason_codes == (
        "source_quality_block",
        "memory_recall_block",
        "stale_memory_block",
        "quality_memory_alignment_block",
    )
    assert watched.source_quality_memory_score == d("0.675000")
    assert watched.reason_codes == (
        "source_quality_watch",
        "memory_recall_watch",
        "stale_memory_watch",
        "quality_memory_alignment_watch",
    )
    assert passed.reason_codes == ("source_quality_memory_clear",)
    assert source_quality_memory.reason_code_counts[0].reason_code == "source_quality_block"
    assert source_quality_memory.reason_code_counts[0].count == d("1.000000")
    assert source_quality_memory.reason_code_counts[0].row_ratio == d("0.333333")


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    module = api()
    first = report(
        observation("team.beta", "specialist.watch"),
        observation("team.alpha", "specialist.pass"),
    )
    second = report(
        observation("team.alpha", "specialist.pass"),
        observation("team.beta", "specialist.watch"),
    )

    first_payload = module.research_team_specialist_source_quality_memory_report_payload(first)
    second_payload = module.research_team_specialist_source_quality_memory_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert module.research_team_specialist_source_quality_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["team_ref"] == "team.alpha"
    assert first_payload["rows"][0]["source_quality_memory_score"] == "0.850000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.850000"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_source_quality_memory_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_specialist_source_quality_memory_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "specialist_ref": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_specialist_source_quality_memory_report_payload(unsafe_value)


def test_public_payload_requires_exact_plain_schema_and_supported_config_version() -> None:
    module = api()
    canonical = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation()),
    )

    missing_top_level = json.loads(json.dumps(canonical))
    missing_top_level.pop("team_count")
    resign(missing_top_level)

    extra_top_level = json.loads(json.dumps(canonical))
    extra_top_level["unexpected_field"] = "unexpected"
    resign(extra_top_level)

    missing_row_field = json.loads(json.dumps(canonical))
    missing_row_field["rows"][0].pop("status")
    resign(missing_row_field)

    missing_reason_count_field = json.loads(json.dumps(canonical))
    missing_reason_count_field["reason_code_counts"][0].pop("count")
    resign(missing_reason_count_field)

    tuple_rows = json.loads(json.dumps(canonical))
    tuple_rows["rows"] = tuple(tuple_rows["rows"])
    resign(tuple_rows)

    noncanonical_decimal = json.loads(json.dumps(canonical))
    noncanonical_decimal["observation_count"] = "1"
    resign(noncanonical_decimal)

    unsupported_config_version = json.loads(json.dumps(canonical))
    unsupported_config_version["config_version"] = (
        "research-team-specialist-source-quality-memory-report-v1"
    )
    resign(unsupported_config_version)

    for forged_payload, error_match in (
        (missing_top_level, "required|exact public fields"),
        (extra_top_level, "unexpected|exact public fields"),
        (missing_row_field, "required|exact public fields"),
        (missing_reason_count_field, "required|exact public fields"),
        (tuple_rows, "list|plain"),
        (noncanonical_decimal, "Decimal-derived|canonical"),
        (unsupported_config_version, "config_version"),
    ):
        with pytest.raises(ValueError, match=error_match):
            module.research_team_specialist_source_quality_memory_report_payload(
                forged_payload,
            )


def test_payload_rebuild_recalculates_row_and_report_derivations() -> None:
    module = api()
    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation()),
    )
    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["status"] = "watch"
    forged["rows"][0]["reason_codes"] = ["source_quality_watch"]
    forged["status"] = "watch"
    forged["next_review_step"] = "review_source_quality_memory_before_reuse"
    forged["pass_count"] = "0.000000"
    forged["watch_count"] = "1.000000"
    forged["reason_codes"] = [
        "source_quality_memory_watch_present",
        "source_quality_gap_present",
    ]
    forged["reason_code_counts"] = [
        {
            "reason_code": "source_quality_watch",
            "count": "1.000000",
            "row_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    resign(forged)

    with pytest.raises(ValueError, match="reason_codes|status"):
        module.research_team_specialist_source_quality_memory_report_payload(forged)


def test_public_mapping_round_trips_and_binds_custom_config() -> None:
    module = api()
    cfg = config(
        min_pass_source_quality_ratio=d("0.950000"),
        min_watch_source_quality_ratio=d("0.850000"),
    )
    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation(), cfg=cfg),
    )

    assert payload["rows"][0]["status"] == "watch"
    assert module.research_team_specialist_source_quality_memory_report_payload(
        json.loads(json.dumps(payload)),
    ) == payload

    forged = json.loads(json.dumps(payload))
    forged["min_pass_source_quality_ratio"] = "0.800000"
    forged["min_watch_source_quality_ratio"] = "0.600000"
    resign(forged)
    with pytest.raises(ValueError, match="reason_codes|status"):
        module.research_team_specialist_source_quality_memory_report_payload(forged)


@pytest.mark.parametrize("target", ("report", "row", "reason_code_count"))
def test_resigned_public_mapping_requires_canonical_key_order(target: str) -> None:
    module = api()
    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation()),
    )
    if target == "report":
        payload = key_first(payload, "status")
    elif target == "row":
        payload["rows"][0] = key_first(payload["rows"][0], "status")
    else:
        payload["reason_code_counts"][0] = key_first(
            payload["reason_code_counts"][0],
            "count",
        )
    resign(payload)

    with pytest.raises(ValueError, match="canonical key sequence"):
        module.research_team_specialist_source_quality_memory_report_payload(payload)


@pytest.mark.parametrize(
    ("scope", "field_name", "replacement"),
    tuple(
        ("row", field_name, "99.000000")
        for field_name in (
            "snapshot_age_seconds",
            "source_quality_check_count",
            "source_quality_pass_count",
            "memory_recall_check_count",
            "memory_recall_pass_count",
            "memory_item_count",
            "stale_memory_item_count",
            "quality_memory_link_count",
            "validated_quality_memory_link_count",
        )
    )
    + tuple(
        ("row", field_name, "0.123456")
        for field_name in (
            "source_quality_ratio",
            "memory_recall_ratio",
            "stale_memory_ratio",
            "quality_memory_alignment_ratio",
            "source_quality_memory_score",
        )
    )
    + (
        ("row", "status", "block"),
        ("row", "reason_codes", ["source_quality_block"]),
    )
    + tuple(
        ("report", field_name, "99.000000")
        for field_name in (
            "observation_count",
            "team_count",
            "specialist_count",
            "source_quality_check_count",
            "source_quality_pass_count",
            "memory_recall_check_count",
            "memory_recall_pass_count",
            "memory_item_count",
            "stale_memory_item_count",
            "quality_memory_link_count",
            "validated_quality_memory_link_count",
            "pass_count",
            "watch_count",
            "block_count",
        )
    )
    + tuple(
        ("report", field_name, "0.123456")
        for field_name in (
            "source_quality_ratio",
            "memory_recall_ratio",
            "stale_memory_ratio",
            "quality_memory_alignment_ratio",
            "source_quality_memory_score",
        )
    )
    + (
        ("report", "status", "block"),
        (
            "report",
            "next_review_step",
            "block_source_quality_memory_reuse_until_review",
        ),
        ("report", "reason_codes", ["source_quality_memory_no_observations"]),
        ("reason_code_count", "count", "99.000000"),
        ("reason_code_count", "row_ratio", "0.500000"),
    ),
)
def test_resigned_mapping_rederives_every_public_derived_field(
    scope: str,
    field_name: str,
    replacement: object,
) -> None:
    module = api()
    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation()),
    )
    target = payload
    if scope == "row":
        target = payload["rows"][0]
    elif scope == "reason_code_count":
        target = payload["reason_code_counts"][0]
    target[field_name] = replacement
    resign(payload)

    with pytest.raises(ValueError):
        module.research_team_specialist_source_quality_memory_report_payload(payload)


def test_resigned_mapping_rederives_timestamp_age_and_row_order() -> None:
    module = api()
    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(
            observation("team.a", "specialist.a"),
            observation("team.b", "specialist.b"),
        ),
    )
    payload["rows"].reverse()
    resign(payload)
    with pytest.raises(ValueError, match="deterministic"):
        module.research_team_specialist_source_quality_memory_report_payload(payload)

    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation()),
    )
    payload["generated_at"] = "2026-07-09T12:01:00+00:00"
    resign(payload)
    with pytest.raises(ValueError, match="snapshot_age_seconds"):
        module.research_team_specialist_source_quality_memory_report_payload(payload)


@pytest.mark.parametrize("digest", ("0" * 63, "A" * 64, "g" * 64))
def test_public_mapping_requires_strict_lowercase_sha256(digest: str) -> None:
    module = api()
    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(observation()),
    )
    payload["derived_validation_digest"] = digest

    with pytest.raises(ValueError, match="lowercase sha256"):
        module.research_team_specialist_source_quality_memory_report_payload(payload)


def test_direct_typed_reconstruction_uses_the_supplied_config() -> None:
    module = api()
    cfg = config(
        min_pass_source_quality_ratio=d("0.950000"),
        min_watch_source_quality_ratio=d("0.850000"),
    )
    built = report(observation(), cfg=cfg)
    row = built.rows[0]

    rebuilt_row = module.ResearchTeamSpecialistSourceQualityMemoryRow(
        **public_dataclass_values(row),
        validation_config=cfg,
    )
    rebuilt_report = module.ResearchTeamSpecialistSourceQualityMemoryReport(
        **public_dataclass_values(built),
        validation_config=cfg,
    )

    assert rebuilt_row == row
    assert rebuilt_report == built
    assert rebuilt_row.status == "watch"
    assert rebuilt_row.reason_codes == ("source_quality_watch",)

    with pytest.raises(ValueError, match="reason_codes|status"):
        module.ResearchTeamSpecialistSourceQualityMemoryRow(
            **public_dataclass_values(row),
            validation_config=config(),
        )
    with pytest.raises(ValueError, match="validation_config|rows|reason_codes|status"):
        module.ResearchTeamSpecialistSourceQualityMemoryReport(
            **public_dataclass_values(built),
            validation_config=config(),
        )


@pytest.mark.parametrize(
    (
        "metric",
        "boundary_value",
        "boundary_status",
        "boundary_reasons",
        "worse_value",
        "worse_status",
        "worse_reasons",
    ),
    (
        (
            "source_quality",
            "0.800000",
            "pass",
            ("source_quality_memory_clear",),
            "0.799999",
            "watch",
            ("source_quality_watch",),
        ),
        (
            "source_quality",
            "0.600000",
            "watch",
            ("source_quality_watch",),
            "0.599999",
            "block",
            ("source_quality_block",),
        ),
        (
            "memory_recall",
            "0.750000",
            "pass",
            ("source_quality_memory_clear",),
            "0.749999",
            "watch",
            ("memory_recall_watch",),
        ),
        (
            "memory_recall",
            "0.500000",
            "watch",
            ("memory_recall_watch",),
            "0.499999",
            "block",
            ("memory_recall_block",),
        ),
        (
            "stale_memory",
            "0.100000",
            "pass",
            ("source_quality_memory_clear",),
            "0.100001",
            "watch",
            ("stale_memory_watch",),
        ),
        (
            "stale_memory",
            "0.250000",
            "watch",
            ("stale_memory_watch",),
            "0.250001",
            "block",
            ("stale_memory_block",),
        ),
        (
            "quality_memory_alignment",
            "0.700000",
            "pass",
            ("source_quality_memory_clear",),
            "0.699999",
            "watch",
            ("quality_memory_alignment_watch",),
        ),
        (
            "quality_memory_alignment",
            "0.500000",
            "watch",
            ("quality_memory_alignment_watch",),
            "0.499999",
            "block",
            ("quality_memory_alignment_block",),
        ),
    ),
)
def test_all_eight_threshold_boundaries_are_config_revalidated(
    metric: str,
    boundary_value: str,
    boundary_status: str,
    boundary_reasons: tuple[str, ...],
    worse_value: str,
    worse_status: str,
    worse_reasons: tuple[str, ...],
) -> None:
    module = api()
    cfg = config()

    def row_for(value: str, specialist_ref: str):
        ratios = {
            "source_quality_ratio": d("0.900000"),
            "memory_recall_ratio": d("0.800000"),
            "stale_memory_ratio": d("0.100000"),
            "quality_memory_alignment_ratio": d("0.800000"),
        }
        ratios[f"{metric}_ratio"] = d(value)
        built_row = report(
            observation_with_ratios(
                "team.threshold",
                specialist_ref,
                **ratios,
            ),
            cfg=cfg,
        ).rows[0]
        return module.ResearchTeamSpecialistSourceQualityMemoryRow(
            **public_dataclass_values(built_row),
            validation_config=cfg,
        )

    boundary_row = row_for(boundary_value, "specialist.boundary")
    worse_row = row_for(worse_value, "specialist.worse")

    assert boundary_row.status == boundary_status
    assert boundary_row.reason_codes == boundary_reasons
    assert worse_row.status == worse_status
    assert worse_row.reason_codes == worse_reasons


@pytest.mark.parametrize(
    ("left", "right", "expected_order"),
    (
        (
            {"source_quality_ratio": d("0.600000")},
            {"source_quality_ratio": d("0.700000")},
            ("specialist.z", "specialist.a"),
        ),
        (
            {
                "source_quality_ratio": d("0.600000"),
                "quality_memory_alignment_ratio": d("0.900000"),
            },
            {
                "source_quality_ratio": d("0.700000"),
                "quality_memory_alignment_ratio": d("0.800000"),
            },
            ("specialist.z", "specialist.a"),
        ),
        (
            {
                "memory_recall_ratio": d("0.600000"),
                "quality_memory_alignment_ratio": d("0.900000"),
            },
            {
                "memory_recall_ratio": d("0.700000"),
                "quality_memory_alignment_ratio": d("0.800000"),
            },
            ("specialist.z", "specialist.a"),
        ),
        (
            {
                "stale_memory_ratio": d("0.300000"),
                "quality_memory_alignment_ratio": d("0.900000"),
            },
            {
                "stale_memory_ratio": d("0.200000"),
                "quality_memory_alignment_ratio": d("0.800000"),
            },
            ("specialist.z", "specialist.a"),
        ),
        (
            {"observed_at": GENERATED_AT - timedelta(hours=2)},
            {"observed_at": GENERATED_AT - timedelta(hours=1)},
            ("specialist.z", "specialist.a"),
        ),
    ),
)
def test_row_order_uses_complete_metric_and_age_tie_breaks(
    left: dict[str, object],
    right: dict[str, object],
    expected_order: tuple[str, str],
) -> None:
    cfg = config(
        min_pass_source_quality_ratio=d("0.100000"),
        min_watch_source_quality_ratio=d("0.050000"),
        min_pass_memory_recall_ratio=d("0.100000"),
        min_watch_memory_recall_ratio=d("0.050000"),
        max_pass_stale_memory_ratio=d("0.900000"),
        max_watch_stale_memory_ratio=d("1.000000"),
        min_pass_quality_memory_alignment_ratio=d("0.100000"),
        min_watch_quality_memory_alignment_ratio=d("0.050000"),
    )
    left_values = {
        "source_quality_ratio": d("0.800000"),
        "memory_recall_ratio": d("0.800000"),
        "stale_memory_ratio": d("0.100000"),
        "quality_memory_alignment_ratio": d("0.800000"),
        "observed_at": GENERATED_AT - timedelta(minutes=30),
    }
    right_values = dict(left_values)
    left_values.update(left)
    right_values.update(right)

    built = report(
        observation_with_ratios(
            "team.tie",
            "specialist.z",
            **left_values,
        ),
        observation_with_ratios(
            "team.tie",
            "specialist.a",
            **right_values,
        ),
        cfg=cfg,
    )

    assert tuple(row.specialist_ref for row in built.rows) == expected_order


def test_row_order_uses_team_and_specialist_as_final_tie_breaks() -> None:
    by_team = report(
        observation("team.b", "specialist.a"),
        observation("team.a", "specialist.z"),
    )
    by_specialist = report(
        observation("team.a", "specialist.b"),
        observation("team.a", "specialist.a"),
    )

    assert tuple(row.team_ref for row in by_team.rows) == ("team.a", "team.b")
    assert tuple(row.specialist_ref for row in by_specialist.rows) == (
        "specialist.a",
        "specialist.b",
    )


def test_decimal_normalization_is_isolated_from_the_caller_context() -> None:
    with localcontext() as caller_context:
        caller_context.prec = 4
        caller_context.rounding = ROUND_DOWN
        cfg = config(min_pass_source_quality_ratio=d("0.812345"))
        source = observation(
            source_quality_check_count=d("1234567.123456"),
            source_quality_pass_count=d("1234567.123455"),
        )

    assert cfg.min_pass_source_quality_ratio == d("0.812345")
    assert source.source_quality_check_count == d("1234567.123456")
    assert source.source_quality_pass_count == d("1234567.123455")


def test_decimal_validation_rejects_signed_zero_and_raw_bound_erosion() -> None:
    module = api()

    for signed_zero in ("-0", "-0.000000"):
        with pytest.raises(ValueError, match="signed zero"):
            config(min_watch_source_quality_ratio=d(signed_zero))
        with pytest.raises(ValueError, match="signed zero"):
            observation(source_quality_pass_count=d(signed_zero))

    with pytest.raises(ValueError, match="between 0 and 1"):
        config(min_pass_source_quality_ratio=d("1.0000004"))
    with pytest.raises(ValueError, match="must not exceed check count"):
        observation(
            source_quality_check_count=d("10.0000000"),
            source_quality_pass_count=d("10.0000004"),
        )

    for overrides, error_match in (
        (
            {
                "min_pass_source_quality_ratio": d("0.8000000"),
                "min_watch_source_quality_ratio": d("0.8000004"),
            },
            "min_watch_source_quality_ratio",
        ),
        (
            {
                "min_pass_memory_recall_ratio": d("0.7500000"),
                "min_watch_memory_recall_ratio": d("0.7500004"),
            },
            "min_watch_memory_recall_ratio",
        ),
        (
            {
                "max_pass_stale_memory_ratio": d("0.2500004"),
                "max_watch_stale_memory_ratio": d("0.2500000"),
            },
            "max_pass_stale_memory_ratio",
        ),
        (
            {
                "min_pass_quality_memory_alignment_ratio": d("0.7000000"),
                "min_watch_quality_memory_alignment_ratio": d("0.7000004"),
            },
            "min_watch_quality_memory_alignment_ratio",
        ),
        (
            {
                "min_pass_source_quality_ratio": d("0.8"),
                "min_watch_source_quality_ratio": d("0.8" + ("0" * 64) + "1"),
            },
            "min_watch_source_quality_ratio",
        ),
    ):
        with pytest.raises(ValueError, match=error_match):
            config(**overrides)

    payload = module.research_team_specialist_source_quality_memory_report_payload(
        report(),
    )
    payload["observation_count"] = "-0.000000"
    resign(payload)
    with pytest.raises(ValueError, match="signed zero"):
        module.research_team_specialist_source_quality_memory_report_payload(payload)


def test_report_decimal_math_uses_a_fixed_local_context() -> None:
    source = observation(
        source_quality_check_count=d("1234567.123456"),
        source_quality_pass_count=d("1004110.604937"),
        memory_recall_check_count=d("9876543.210987"),
        memory_recall_pass_count=d("7654321.098765"),
        memory_item_count=d("3456789.012345"),
        stale_memory_item_count=d("432109.876543"),
        quality_memory_link_count=d("2345678.901234"),
        validated_quality_memory_link_count=d("1765432.109876"),
    )
    baseline = report(source)

    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        constrained = report(source)

    assert constrained == baseline
    assert constrained.payload == baseline.payload


def test_validation_freezing_flags_decimal_only_statuses_and_consistency() -> None:
    module = api()
    source_quality_memory = report(observation())

    assert source_quality_memory.generated_at == GENERATED_AT
    assert source_quality_memory.rows[0].observed_at == GENERATED_AT - timedelta(minutes=30)
    assert source_quality_memory.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in source_quality_memory.rows)

    for public_type in (
        module.ResearchTeamSpecialistSourceQualityMemoryConfig,
        module.ResearchTeamSpecialistSourceQualityMemoryObservation,
        module.ResearchTeamSpecialistSourceQualityMemoryRow,
        module.ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount,
        module.ResearchTeamSpecialistSourceQualityMemoryReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        config(),
        observation(),
        source_quality_memory.rows[0],
        source_quality_memory.reason_code_counts[0],
        source_quality_memory,
    ):
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        source_quality_memory.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_quality_check_count must be exactly Decimal"):
        observation(source_quality_check_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="source_quality_check_count must be positive"):
        observation(source_quality_check_count=d("0.000000"))
    with pytest.raises(ValueError, match="source_quality_pass_count must not exceed"):
        observation(source_quality_pass_count=d("11.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="pairs must be unique"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="min_watch_source_quality_ratio"):
        config(
            min_pass_source_quality_ratio=d("0.700000"),
            min_watch_source_quality_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("config-v1"))
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(source_quality_memory.rows[0], status="ready")
    with pytest.raises(ValueError, match="source_quality_ratio must match row counts"):
        replace(source_quality_memory.rows[0], source_quality_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(source_quality_memory, derived_validation_digest="0" * 64)


def test_public_dataclasses_are_exact_final_types() -> None:
    module = api()

    for public_type in (
        module.ResearchTeamSpecialistSourceQualityMemoryConfig,
        module.ResearchTeamSpecialistSourceQualityMemoryObservation,
        module.ResearchTeamSpecialistSourceQualityMemoryRow,
        module.ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount,
        module.ResearchTeamSpecialistSourceQualityMemoryReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{public_type.__name__}", (public_type,), {})


def test_public_boundaries_revalidate_object_setattr_mutations() -> None:
    module = api()

    mutated_config = config()
    object.__setattr__(mutated_config, "min_watch_source_quality_ratio", 0)
    with pytest.raises(ValueError, match="must be exactly Decimal"):
        report(observation(), cfg=mutated_config)

    mutated_observation = observation()
    object.__setattr__(mutated_observation, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report(mutated_observation)

    row_report = report(observation())
    object.__setattr__(row_report.rows[0], "team_ref", " team.alpha")
    row_report_values = public_dataclass_values(row_report)
    row_report_values["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="team_ref must be a nonempty public label"):
        module.ResearchTeamSpecialistSourceQualityMemoryReport(
            **row_report_values,
            validation_config=config(),
        )

    count_report = report(observation())
    object.__setattr__(count_report.reason_code_counts[0], "count", "1.000000")
    count_report_values = public_dataclass_values(count_report)
    count_report_values["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="count must be exactly Decimal"):
        module.ResearchTeamSpecialistSourceQualityMemoryReport(
            **count_report_values,
            validation_config=config(),
        )


def test_report_payload_and_digest_revalidate_nested_object_setattr_mutations() -> None:
    module = api()

    row_report = report(observation())
    object.__setattr__(row_report.rows[0], "team_ref", " team.alpha")
    with pytest.raises(ValueError, match="team_ref must be a nonempty public label"):
        module.research_team_specialist_source_quality_memory_report_payload(row_report)

    count_report = report(observation())
    object.__setattr__(count_report.reason_code_counts[0], "count", "1.000000")
    with pytest.raises(ValueError, match="count must be exactly Decimal"):
        module.research_team_specialist_source_quality_memory_report_digest(count_report)

    config_report = report(observation())
    object.__setattr__(
        config_report._validation_config,
        "min_watch_source_quality_ratio",
        0,
    )
    with pytest.raises(ValueError, match="must be exactly Decimal"):
        module.research_team_specialist_source_quality_memory_report_payload(config_report)


def test_module_scope_is_static_report_only_public_safe_without_action_surfaces() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
        "requests",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "open(",
        "recommend",
        "recommendation",
        "position sizing",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {"connect", "execute", "open", "request", "write_bytes", "write_text"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (Decimal, float, int):
        pytest.fail(f"payload contains raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    elif type(value) is list:
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_no_forbidden_public_payload_surface(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded


def is_numeric_public_field(name: str) -> bool:
    return (
        name.endswith("_count")
        or name.endswith("_ratio")
        or name.endswith("_score")
        or name.endswith("_seconds")
    )
