from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, Inexact, localcontext
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_team_specialist_calibration_memory_floor_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_specialist_calibration_memory_floor_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION
        ),
        "min_pass_calibration_memory_floor_score": d("0.750000"),
        "min_watch_calibration_memory_floor_score": d("0.500000"),
        "min_pass_calibration_score": d("0.750000"),
        "min_watch_calibration_score": d("0.500000"),
        "min_pass_memory_recall_score": d("0.750000"),
        "min_watch_memory_recall_score": d("0.500000"),
        "max_pass_memory_age_seconds": d("604800.000000"),
        "max_watch_memory_age_seconds": d("2592000.000000"),
        "max_pass_uncalibrated_specialist_ratio": d("0.200000"),
        "max_watch_uncalibrated_specialist_ratio": d("0.500000"),
        "calibration_score_weight": d("0.400000"),
        "memory_recall_weight": d("0.400000"),
        "memory_recency_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationMemoryFloorConfig(**values)


def observation(
    team_label: str = "macro_rates",
    specialist_label: str = "policy_resolution_team",
    *,
    calibration_score: Decimal = d("0.900000"),
    memory_recall_score: Decimal = d("0.800000"),
    memory_age_seconds: Decimal = d("86400.000000"),
    uncalibrated_specialist_ratio: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchTeamSpecialistCalibrationMemoryFloorObservation(
        team_label=team_label,
        specialist_label=specialist_label,
        calibration_score=calibration_score,
        memory_recall_score=memory_recall_score,
        memory_age_seconds=memory_age_seconds,
        uncalibrated_specialist_ratio=uncalibrated_specialist_ratio,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialist_calibration_memory_floor_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {
            "paper_only",
            "report_only",
            "readonly",
            "reason_code_counts",
            "reason_codes",
            "rows",
        }:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if any(
            token in field.name
            for token in (
                "age",
                "count",
                "floor",
                "rank",
                "ratio",
                "score",
                "seconds",
                "weight",
            )
        ):
            assert type(item) is Decimal


def test_calibration_memory_floor_scores_sorts_and_summarizes_specialists() -> None:
    items = (
        observation("macro_rates", "policy_resolution_team"),
        observation(
            "weather_events",
            "storm_settlement_team",
            calibration_score=d("0.650000"),
            memory_recall_score=d("0.700000"),
            memory_age_seconds=d("1209600.000000"),
            uncalibrated_specialist_ratio=d("0.300000"),
        ),
        observation(
            "election_rules",
            "settlement_history_team",
            calibration_score=d("0.350000"),
            memory_recall_score=d("0.400000"),
            memory_age_seconds=d("3456000.000000"),
            uncalibrated_specialist_ratio=d("0.800000"),
        ),
    )

    report = build_report(*items)
    reversed_report = build_report(*reversed(items))

    assert api().CALIBRATION_MEMORY_FLOOR_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.next_step == "block_report_only_team_specialist_calibration_memory_floor"
    assert report.team_specialist_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.floor_breach_count == d("2.000000")
    assert report.floor_breach_ratio == d("0.666667")
    assert report.average_calibration_memory_floor_score == d("0.606667")
    assert report.lowest_calibration_memory_floor_score == d("0.300000")
    assert report.max_memory_age_seconds == d("3456000.000000")
    assert report.max_uncalibrated_specialist_ratio == d("0.800000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.floor_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.team_label == "election_rules"
    assert blocked.memory_recency_score == d("0.000000")
    assert blocked.calibration_memory_floor_score == d("0.300000")
    assert blocked.reason_codes == (
        "team_specialist_calibration_memory_floor_below_watch",
        "team_specialist_calibration_score_below_watch",
        "team_specialist_memory_recall_below_watch",
        "team_specialist_memory_age_above_watch",
        "team_specialist_uncalibrated_ratio_above_watch",
    )
    assert watched.memory_recency_score == d("0.533333")
    assert watched.calibration_memory_floor_score == d("0.646667")
    assert watched.reason_codes == (
        "team_specialist_calibration_memory_floor_between_watch_and_pass",
        "team_specialist_calibration_score_watch",
        "team_specialist_memory_recall_watch",
        "team_specialist_memory_age_watch",
        "team_specialist_uncalibrated_ratio_watch",
    )
    assert passed.calibration_memory_floor_score == d("0.873333")
    assert passed.reason_codes == ("team_specialist_calibration_memory_floor_pass",)

    payload = api().research_team_specialist_calibration_memory_floor_report_payload(
        report,
    )
    reversed_payload = api().research_team_specialist_calibration_memory_floor_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["calibration_memory_floor_score"] == "0.300000"
    assert payload["rows"][1]["memory_recency_score"] == "0.533333"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    json.dumps(payload, sort_keys=True)


def test_empty_report_is_blocked_report_only_and_tamper_evident() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.next_step == "block_report_only_team_specialist_calibration_memory_floor"
    assert report.team_specialist_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.floor_breach_count == ZERO
    assert report.floor_breach_ratio == ZERO
    assert report.average_calibration_memory_floor_score is None
    assert report.lowest_calibration_memory_floor_score is None
    assert report.max_memory_age_seconds is None
    assert report.max_uncalibrated_specialist_ratio is None
    assert report.rows == ()
    assert report.reason_codes == (
        "team_specialist_calibration_memory_floor_no_inputs",
    )
    assert report.reason_code_counts == (
        module.ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount(
            reason_code="team_specialist_calibration_memory_floor_no_inputs",
            count=d("1.000000"),
            team_specialist_ratio=d("1.000000"),
        ),
    )

    payload = module.research_team_specialist_calibration_memory_floor_report_payload(
        report,
    )
    assert module.research_team_specialist_calibration_memory_floor_report_digest(
        report,
    ) == payload["derived_validation_digest"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_calibration_memory_floor_report_payload(
            tampered,
        )


def test_report_only_contracts_validate_decimals_flags_and_manual_drift() -> None:
    module = api()
    cfg = config()
    source = observation()
    report = build_report(source)

    for item in (
        cfg,
        source,
        report,
        *report.rows,
        *report.reason_code_counts,
    ):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_decimal_numeric_fields(item)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("config-v1"))
    with pytest.raises(ValueError, match="calibration_score"):
        observation(calibration_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_recall_score"):
        observation(memory_recall_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="uncalibrated_specialist_ratio"):
        observation(uncalibrated_specialist_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="memory_age_seconds"):
        observation(memory_age_seconds=d("-0.000001"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            observed_at=_DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="weights"):
        config(memory_recency_weight=d("0.300000"))
    with pytest.raises(ValueError, match="min_pass_calibration_memory_floor_score"):
        config(min_pass_calibration_memory_floor_score=d("0.400000"))
    with pytest.raises(ValueError, match="max_watch_memory_age_seconds"):
        config(
            max_pass_memory_age_seconds=d("300.000000"),
            max_watch_memory_age_seconds=d("200.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            source,
            generated_at=datetime(
                2026,
                7,
                9,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="team and specialist labels must be unique"):
        build_report(source, source)

    with pytest.raises(ValueError, match="calibration_memory_floor_score"):
        replace(report.rows[0], calibration_memory_floor_score=d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.rows[0],
            reason_codes=("team_specialist_memory_age_watch",),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="block")
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_team_specialist_calibration_memory_floor_report_payload(object())


def test_public_payload_excludes_sensitive_identifiers_and_runtime_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION",
        "CALIBRATION_MEMORY_FLOOR_STATUSES",
        "ResearchTeamSpecialistCalibrationMemoryFloorConfig",
        "ResearchTeamSpecialistCalibrationMemoryFloorObservation",
        "ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount",
        "ResearchTeamSpecialistCalibrationMemoryFloorReport",
        "ResearchTeamSpecialistCalibrationMemoryFloorRow",
        "build_research_team_specialist_calibration_memory_floor_report",
        "research_team_specialist_calibration_memory_floor_report_digest",
        "research_team_specialist_calibration_memory_floor_report_payload",
    )

    payload = module.research_team_specialist_calibration_memory_floor_report_payload(
        build_report(observation()),
    )
    lowered = repr(payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in lowered

    for unsafe_key in (
        "candidate_id",
        "market_slug",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet_address",
        "order_id",
        "trade_id",
        "sizing_model",
        "recommendation",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="public aggregate labels"):
            module.research_team_specialist_calibration_memory_floor_report_payload(
                forged_payload,
            )

    with pytest.raises(ValueError, match="public aggregate label"):
        observation("macro_market", "policy_resolution_team")
    with pytest.raises(ValueError, match="public aggregate label"):
        observation("macro_rates", "source_text_team")

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "execute",
            "executemany",
            "float",
            "open",
            "request",
            "send",
            "write",
            "write_text",
        },
    )
    assert not any(
        fragment in value.lower()
        for value in attribute_names
        for fragment in (
            "wallet",
            "order",
            "trade",
            "auth",
            "token",
            "position",
        )
    )


def test_decimal_contract_is_signed_zero_safe_and_context_independent() -> None:
    module = api()
    source = observation(
        calibration_score=d("-0.000000"),
        memory_recall_score=d("-0.000000"),
        memory_age_seconds=d("-0.000000"),
        uncalibrated_specialist_ratio=d("-0.000000"),
    )
    for field_name in (
        "calibration_score",
        "memory_recall_score",
        "memory_age_seconds",
        "uncalibrated_specialist_ratio",
    ):
        value = getattr(source, field_name)
        assert value == ZERO
        assert not value.is_signed()

    with localcontext() as hostile:
        hostile.prec = 3
        hostile.traps[Inexact] = True
        cfg = config(
            calibration_score_weight=d("0.333333"),
            memory_recall_weight=d("0.333333"),
            memory_recency_weight=d("0.333334"),
        )
        report = build_report(
            observation("alpha_team", "one_specialist"),
            observation("beta_team", "two_specialist"),
            cfg=cfg,
        )
    assert report.team_specialist_count == d("2.000000")

    with pytest.raises(ValueError, match="calibration_score"):
        observation(calibration_score=d("1E+999999"))
    with pytest.raises(ValueError, match="memory_age_seconds"):
        observation(memory_age_seconds=d("-0.000001"))


def test_api_boundaries_revalidate_object_setattr_mutations() -> None:
    module = api()

    cfg = config()
    object.__setattr__(cfg, "min_watch_calibration_score", d("1.000001"))
    with pytest.raises(ValueError, match="min_watch_calibration_score"):
        build_report(observation(), cfg=cfg)

    source = observation()
    object.__setattr__(source, "memory_age_seconds", d("-1.000000"))
    with pytest.raises(ValueError, match="memory_age_seconds"):
        build_report(source)

    report = build_report(observation())
    object.__setattr__(report.rows[0], "status", "block")
    object.__setattr__(report, "derived_validation_digest", canonical_digest(
        module._json_ready(report),  # type: ignore[attr-defined]
    ))
    with pytest.raises(ValueError, match="status"):
        module.research_team_specialist_calibration_memory_floor_report_payload(report)

    report = build_report(observation())
    object.__setattr__(report.reason_code_counts[0], "count", d("2.000000"))
    materialized = module._json_ready(report)  # type: ignore[attr-defined]
    materialized["derived_validation_digest"] = canonical_digest(materialized)
    object.__setattr__(
        report,
        "derived_validation_digest",
        materialized["derived_validation_digest"],
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_team_specialist_calibration_memory_floor_report_payload(report)


def test_public_mapping_requires_exact_canonical_schema_and_key_order() -> None:
    module = api()
    payload = module.research_team_specialist_calibration_memory_floor_report_payload(
        build_report(observation()),
    )

    reordered = {key: payload[key] for key in reversed(tuple(payload))}
    with pytest.raises(ValueError, match="schema|key order"):
        module.research_team_specialist_calibration_memory_floor_report_payload(reordered)

    extra = dict(payload)
    extra["benign"] = "aggregate"
    resign(extra)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_specialist_calibration_memory_floor_report_payload(extra)

    nested_reordered = dict(payload)
    row = payload["rows"][0]
    nested_reordered["rows"] = [{key: row[key] for key in reversed(tuple(row))}]
    resign(nested_reordered)
    with pytest.raises(ValueError, match="rows.*schema|key order"):
        module.research_team_specialist_calibration_memory_floor_report_payload(
            nested_reordered,
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("status", "watch"),
        ("next_step", "watch_report_only_team_specialist_calibration_memory_floor"),
        ("team_specialist_count", "2.000000"),
        ("pass_count", "0.000000"),
        ("watch_count", "1.000000"),
        ("block_count", "1.000000"),
        ("floor_breach_count", "1.000000"),
        ("floor_breach_ratio", "1.000000"),
        ("average_calibration_memory_floor_score", "0.100000"),
        ("lowest_calibration_memory_floor_score", "0.100000"),
        ("max_memory_age_seconds", "1.000000"),
        ("max_uncalibrated_specialist_ratio", "0.900000"),
        ("reason_codes", ["team_specialist_memory_age_watch"]),
    ),
)
def test_public_mapping_rederives_resigned_report_fields(
    field_name: str,
    forged_value: object,
) -> None:
    module = api()
    payload = module.research_team_specialist_calibration_memory_floor_report_payload(
        build_report(observation()),
    )
    forged = dict(payload)
    forged[field_name] = forged_value
    resign(forged)
    with pytest.raises(ValueError):
        module.research_team_specialist_calibration_memory_floor_report_payload(forged)


def test_public_mapping_rederives_nested_rows_counts_and_order() -> None:
    module = api()
    report = build_report(
        observation("alpha_team", "one_specialist"),
        observation(
            "beta_team",
            "two_specialist",
            calibration_score=d("0.300000"),
        ),
    )
    payload = module.research_team_specialist_calibration_memory_floor_report_payload(report)

    for field_name, forged_value in (
        ("floor_rank", "9.000000"),
        ("calibration_score", "0.310000"),
        ("memory_recall_score", "0.310000"),
        ("memory_age_seconds", "1.000000"),
        ("memory_recency_score", "0.100000"),
        ("uncalibrated_specialist_ratio", "0.900000"),
        ("calibration_memory_floor_score", "0.100000"),
        ("status", "pass"),
        ("reason_codes", ["team_specialist_calibration_memory_floor_pass"]),
    ):
        forged = dict(payload)
        forged["rows"] = [dict(row) for row in payload["rows"]]
        forged["rows"][0][field_name] = forged_value
        resign(forged)
        with pytest.raises(ValueError):
            module.research_team_specialist_calibration_memory_floor_report_payload(forged)

    forged = dict(payload)
    forged["rows"] = list(reversed(payload["rows"]))
    resign(forged)
    with pytest.raises(ValueError, match="rank|order"):
        module.research_team_specialist_calibration_memory_floor_report_payload(forged)

    forged = dict(payload)
    forged["reason_code_counts"] = [
        dict(item) for item in payload["reason_code_counts"]
    ]
    forged["reason_code_counts"][0]["count"] = "2.000000"
    resign(forged)
    with pytest.raises(ValueError, match="reason_code_counts|count"):
        module.research_team_specialist_calibration_memory_floor_report_payload(forged)

    for field_name, forged_value in (
        ("reason_code", "team_specialist_memory_age_watch"),
        ("team_specialist_ratio", "0.100000"),
    ):
        forged = dict(payload)
        forged["reason_code_counts"] = [
            dict(item) for item in payload["reason_code_counts"]
        ]
        forged["reason_code_counts"][0][field_name] = forged_value
        resign(forged)
        with pytest.raises(ValueError, match="reason_code_counts|reason_code"):
            module.research_team_specialist_calibration_memory_floor_report_payload(
                forged,
            )

    forged = dict(payload)
    forged["reason_code_counts"] = list(reversed(payload["reason_code_counts"]))
    resign(forged)
    with pytest.raises(ValueError, match="reason_code_counts|ordered"):
        module.research_team_specialist_calibration_memory_floor_report_payload(forged)

    malformed_digest = dict(payload)
    malformed_digest["derived_validation_digest"] = "A" * 64
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        module.research_team_specialist_calibration_memory_floor_report_payload(
            malformed_digest,
        )


def test_public_mapping_rejects_resigned_version_and_future_observation() -> None:
    module = api()
    payload = module.research_team_specialist_calibration_memory_floor_report_payload(
        build_report(observation()),
    )

    forged = dict(payload)
    forged["config_version"] = "research-team-specialist-calibration-memory-floor-v2"
    resign(forged)
    with pytest.raises(ValueError, match="config_version"):
        module.research_team_specialist_calibration_memory_floor_report_payload(forged)

    forged = dict(payload)
    forged["rows"] = [dict(payload["rows"][0])]
    forged["rows"][0]["observed_at"] = "2026-07-09T12:00:01+00:00"
    resign(forged)
    with pytest.raises(ValueError, match="observed_at"):
        module.research_team_specialist_calibration_memory_floor_report_payload(forged)


def test_tie_break_includes_observation_time_and_rejects_duplicate_identity() -> None:
    older = observation(
        "same_team",
        "older_specialist",
        observed_at=OBSERVED_AT - timedelta(seconds=1),
    )
    newer = observation("same_team", "newer_specialist", observed_at=OBSERVED_AT)
    report = build_report(newer, older)
    assert tuple(row.observed_at for row in report.rows) == (
        older.observed_at,
        newer.observed_at,
    )

    duplicate = replace(report.rows[0], floor_rank=d("2.000000"))
    with pytest.raises(ValueError, match="team and specialist labels must be unique"):
        replace(report, rows=(report.rows[0], duplicate), team_specialist_count=d("2.000000"))


def test_all_public_dataclasses_are_frozen_final_and_exact_type() -> None:
    module = api()
    report = build_report(observation())
    instances = (
        config(),
        observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for instance in instances:
        with pytest.raises(FrozenInstanceError):
            instance.paper_only = False
        with pytest.raises(TypeError, match="subclass is not allowed"):
            type("ForbiddenSubclass", (type(instance),), {})

    assert all(type(instance).__module__ == module.__name__ for instance in instances)
