from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

import pytest

from polymarket_alpha_lab.team_specialist_source_rotation_plan_v2 import (
    DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_PLAN_V2_CONFIG_VERSION,
    TeamSpecialistSourceRotationPlanV2Config,
    TeamSpecialistSourceRotationPlanV2Input,
    TeamSpecialistSourceRotationPlanV2ReasonCodeCount,
    TeamSpecialistSourceRotationPlanV2Report,
    TeamSpecialistSourceRotationPlanV2TeamPlan,
    build_team_specialist_source_rotation_plan_v2_report,
    team_specialist_source_rotation_plan_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_source_rotation_plan_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _FloatSubclass(float):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _source(
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    domain_id: str = "crypto",
    source_id: str = "source-a",
    source_family: str = "filings",
    source_fatigue_score: Decimal = d("0.200000"),
    reliability_decay_score: Decimal = d("0.030000"),
    contradiction_concentration: Decimal = d("0.050000"),
    latency_drift_seconds: Decimal = d("20.000000"),
    domain_calibration_error: Decimal = d("0.020000"),
    upcoming_event_load_count: Decimal = d("1.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    reason_codes: tuple[str, ...] = ("source_rotation_memory_observed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamSpecialistSourceRotationPlanV2Input:
    return TeamSpecialistSourceRotationPlanV2Input(
        team_id=team_id,
        category_id=category_id,
        domain_id=domain_id,
        source_id=source_id,
        source_family=source_family,
        source_fatigue_score=source_fatigue_score,
        reliability_decay_score=reliability_decay_score,
        contradiction_concentration=contradiction_concentration,
        latency_drift_seconds=latency_drift_seconds,
        domain_calibration_error=domain_calibration_error,
        upcoming_event_load_count=upcoming_event_load_count,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *sources: TeamSpecialistSourceRotationPlanV2Input,
    config: TeamSpecialistSourceRotationPlanV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> TeamSpecialistSourceRotationPlanV2Report:
    return build_team_specialist_source_rotation_plan_v2_report(
        sources,
        config=config or TeamSpecialistSourceRotationPlanV2Config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_readonly_report_with_digest() -> None:
    report = _report()

    assert report.config_version == DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_PLAN_V2_CONFIG_VERSION
    assert report.plan_status == "blocked"
    assert report.recommended_next_step == "rotate_source_mix_before_memory_use"
    assert report.team_plan_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.mean_rotation_pressure_score == d("0.000000")
    assert report.max_latency_drift_seconds == d("0.000000")
    assert report.max_upcoming_event_load_count == d("0.000000")
    assert report.source_rotation_plans == ()
    assert report.reason_codes == ("team_specialist_source_rotation_plan_v2_empty",)
    assert report.reason_code_counts == (
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
            reason_code="team_specialist_source_rotation_plan_v2_empty",
            count=d("1.000000"),
        ),
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rotation_plan_scores_source_fatigue_reliability_contradiction_latency_calibration_and_load() -> None:
    report = _report(
        _source(
            team_id="politics",
            category_id="politics",
            domain_id="elections",
            source_id="source-blocked",
            source_family="polling",
            source_fatigue_score=d("0.900000"),
            reliability_decay_score=d("0.300000"),
            contradiction_concentration=d("0.800000"),
            latency_drift_seconds=d("1000.000000"),
            domain_calibration_error=d("0.200000"),
            upcoming_event_load_count=d("8.000000"),
        ),
        _source(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            domain_id="crypto",
            source_id="source-pass",
            source_family="filings",
            observed_at=datetime(2026, 7, 6, 7, 45, tzinfo=EASTERN),
        ),
    )

    assert report.plan_status == "blocked"
    assert report.recommended_next_step == "rotate_source_mix_before_memory_use"
    assert report.team_plan_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.max_latency_drift_seconds == d("1000.000000")
    assert report.max_upcoming_event_load_count == d("8.000000")

    blocked = report.source_rotation_plans[0]
    assert blocked.team_id == "politics"
    assert blocked.plan_status == "blocked"
    assert blocked.source_rotation_action == "rotate_source_now"
    assert blocked.rotation_pressure_score == d("0.700000")
    assert blocked.reason_codes == (
        "domain_calibration_error_blocked",
        "source_contradiction_concentration_blocked",
        "source_fatigue_blocked",
        "source_latency_drift_blocked",
        "source_reliability_decay_blocked",
        "upcoming_event_load_blocked",
    )

    healthy = report.source_rotation_plans[1]
    assert healthy.team_id == "crypto_btc"
    assert healthy.plan_status == "pass"
    assert healthy.source_rotation_action == "retain_source_mix"
    assert healthy.observed_at == datetime(2026, 7, 6, 11, 45, tzinfo=UTC)
    assert healthy.observation_age_seconds == d("900.000000")
    assert healthy.reason_codes == ("source_rotation_plan_ready",)


def test_watch_tier_and_deterministic_reason_counts_are_preserved() -> None:
    report = _report(
        _source(
            team_id="sports_soccer",
            category_id="sports.soccer",
            domain_id="soccer",
            source_id="source-watch",
            source_family="fixtures",
            source_fatigue_score=d("0.700000"),
            latency_drift_seconds=d("500.000000"),
            upcoming_event_load_count=d("4.000000"),
        ),
        _source(
            team_id="macro_rates",
            category_id="finance.macro.rates",
            domain_id="rates",
            source_id="source-blocked",
            source_family="calendar",
            reliability_decay_score=d("0.300000"),
        ),
        _source(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            domain_id="crypto",
            source_id="source-pass",
        ),
    )

    assert [(row.plan_status, row.team_id, row.source_id) for row in report.source_rotation_plans] == [
        ("blocked", "macro_rates", "source-blocked"),
        ("watch", "sports_soccer", "source-watch"),
        ("pass", "crypto_btc", "source-pass"),
    ]
    assert report.reason_codes == (
        "team_specialist_source_rotation_plan_v2_blocked",
        "source_fatigue_watch",
        "source_latency_drift_watch",
        "source_reliability_decay_blocked",
        "upcoming_event_load_watch",
    )
    assert report.reason_code_counts == (
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
            reason_code="source_fatigue_watch",
            count=d("1.000000"),
        ),
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
            reason_code="source_latency_drift_watch",
            count=d("1.000000"),
        ),
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
            reason_code="source_reliability_decay_blocked",
            count=d("1.000000"),
        ),
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
            reason_code="upcoming_event_load_watch",
            count=d("1.000000"),
        ),
    )


def test_payload_uses_decimal_strings_and_rejects_digest_tampering() -> None:
    report = _report(_source())
    payload = team_specialist_source_rotation_plan_v2_payload(report)

    assert payload["team_plan_count"] == "1.000000"
    assert payload["source_rotation_plans"][0]["source_fatigue_score"] == "0.200000"
    assert payload["source_rotation_plans"][0]["observation_age_seconds"] == "900.000000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    _assert_no_floats(payload)

    tampered = dict(payload)
    tampered["team_plan_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        team_specialist_source_rotation_plan_v2_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_dataclasses_are_frozen_and_numeric_surface_is_decimal_only() -> None:
    report = _report(_source())

    assert is_dataclass(TeamSpecialistSourceRotationPlanV2Config)
    assert is_dataclass(TeamSpecialistSourceRotationPlanV2Input)
    assert is_dataclass(TeamSpecialistSourceRotationPlanV2TeamPlan)
    assert is_dataclass(TeamSpecialistSourceRotationPlanV2ReasonCodeCount)
    assert is_dataclass(TeamSpecialistSourceRotationPlanV2Report)
    with pytest.raises(FrozenInstanceError):
        report.plan_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.source_rotation_plans[0].rotation_pressure_score = d("1.000000")  # type: ignore[misc]

    dataclass_types = (
        TeamSpecialistSourceRotationPlanV2Config,
        TeamSpecialistSourceRotationPlanV2Input,
        TeamSpecialistSourceRotationPlanV2TeamPlan,
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount,
        TeamSpecialistSourceRotationPlanV2Report,
    )
    for dataclass_type in dataclass_types:
        hints = get_type_hints(dataclass_type, include_extras=True)
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name.endswith("_error")
                or field.name.endswith("_concentration")
                or field.name.endswith("_load_count")
            ):
                annotation = hints[field.name]
                args = get_args(annotation)
                assert annotation is Decimal or (
                    get_origin(annotation) is type(Decimal | None)
                    and Decimal in args
                    and type(None) in args
                )

    with pytest.raises(ValueError, match="source_fatigue_score must be a Decimal"):
        _source(source_fatigue_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reliability_decay_score must be a Decimal"):
        _source(reliability_decay_score=_FloatSubclass(1.0))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="upcoming_event_load_count must be a Decimal"):
        _source(upcoming_event_load_count=_DecimalSubclass("1"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        _source(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_source(), readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        TeamSpecialistSourceRotationPlanV2Config(report_only=False)


def test_validates_time_bounds_counts_duplicates_config_and_public_unsafe_terms() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _source(observed_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="generated_at"):
        build_team_specialist_source_rotation_plan_v2_report(
            (_source(),),
            config=TeamSpecialistSourceRotationPlanV2Config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at"):
        _report(_source(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="upcoming_event_load_count"):
        _source(upcoming_event_load_count=d("1.500000"))

    with pytest.raises(ValueError, match="duplicate"):
        _report(_source(), _source())

    with pytest.raises(ValueError, match="fatigue_watch_threshold"):
        TeamSpecialistSourceRotationPlanV2Config(
            fatigue_watch_threshold=d("0.900000"),
            fatigue_block_threshold=d("0.800000"),
        )

    for unsafe_fragment in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            team_specialist_source_rotation_plan_v2_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "derived_validation_digest": "x",
                    f"{unsafe_fragment}_field": "redacted",
                },
            )
        with pytest.raises(ValueError, match="unsafe"):
            team_specialist_source_rotation_plan_v2_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "derived_validation_digest": "x",
                    "summary": f"mentions {unsafe_fragment}",
                },
            )

    with pytest.raises(ValueError, match="readonly"):
        team_specialist_source_rotation_plan_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
                "derived_validation_digest": "x",
            },
        )


def test_module_scope_is_report_only_without_io_or_action_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "websocket",
        "psycopg",
        "sqlite",
        "supabase",
        "os.environ",
        "subprocess",
        "socket",
        "asyncio",
        "open(",
        "path(",
        "write",
        "private_key",
        "api_key",
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden not in lowered

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, list | tuple):
        for item in value:
            _assert_no_floats(item)
