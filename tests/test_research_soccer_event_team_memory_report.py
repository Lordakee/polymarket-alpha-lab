from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

import pytest

from polymarket_alpha_lab.research_soccer_event_team_memory_report import (
    DEFAULT_RESEARCH_SOCCER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION,
    ResearchSoccerEventTeamMemoryObservation,
    ResearchSoccerEventTeamMemoryReasonCodeCount,
    ResearchSoccerEventTeamMemoryReport,
    ResearchSoccerEventTeamMemoryReportConfig,
    ResearchSoccerEventTeamMemoryRow,
    build_research_soccer_event_team_memory_report,
    research_soccer_event_team_memory_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_soccer_event_team_memory_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    soccer_event_bucket: str = "league-cup-knockout",
    team_memory_bucket: str = "favorite-with-rotation-risk",
    specialist_memory_score: Decimal = d("0.880000"),
    calibration_sample_size: Decimal = d("30.000000"),
    calibration_error: Decimal = d("0.040000"),
    injury_update_count: Decimal = d("6.000000"),
    fresh_injury_update_count: Decimal = d("6.000000"),
    news_update_count: Decimal = d("4.000000"),
    fresh_news_update_count: Decimal = d("4.000000"),
    source_count: Decimal = d("5.000000"),
    stale_source_count: Decimal = d("0.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    reason_codes: tuple[str, ...] = ("soccer_event_team_memory_observed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSoccerEventTeamMemoryObservation:
    return ResearchSoccerEventTeamMemoryObservation(
        soccer_event_bucket=soccer_event_bucket,
        team_memory_bucket=team_memory_bucket,
        specialist_memory_score=specialist_memory_score,
        calibration_sample_size=calibration_sample_size,
        calibration_error=calibration_error,
        injury_update_count=injury_update_count,
        fresh_injury_update_count=fresh_injury_update_count,
        news_update_count=news_update_count,
        fresh_news_update_count=fresh_news_update_count,
        source_count=source_count,
        stale_source_count=stale_source_count,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: ResearchSoccerEventTeamMemoryObservation,
    config: ResearchSoccerEventTeamMemoryReportConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSoccerEventTeamMemoryReport:
    return build_research_soccer_event_team_memory_report(
        observations,
        config=config or ResearchSoccerEventTeamMemoryReportConfig(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_digest() -> None:
    memory_report = report()

    assert (
        memory_report.config_version
        == DEFAULT_RESEARCH_SOCCER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    assert memory_report.report_status == "block"
    assert memory_report.recommended_next_step == "collect_soccer_specialist_memory"
    assert memory_report.row_count == d("0.000000")
    assert memory_report.observation_count == d("0.000000")
    assert memory_report.pass_count == d("0.000000")
    assert memory_report.watch_count == d("0.000000")
    assert memory_report.block_count == d("0.000000")
    assert memory_report.average_calibration_readiness_score == d("0.000000")
    assert memory_report.minimum_source_freshness_score == d("0.000000")
    assert memory_report.maximum_calibration_error == d("0.000000")
    assert memory_report.rows == ()
    assert memory_report.reason_codes == ("soccer_event_team_memory_report_empty",)
    assert memory_report.reason_code_counts == (
        ResearchSoccerEventTeamMemoryReasonCodeCount(
            reason_code="soccer_event_team_memory_report_empty",
            count=d("1.000000"),
        ),
    )
    assert len(memory_report.derived_validation_digest) == 64
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True


def test_aggregates_injury_news_source_freshness_and_calibration_readiness() -> None:
    memory_report = report(
        observation(
            soccer_event_bucket="international-friendly",
            team_memory_bucket="rotation-heavy-underdog",
            specialist_memory_score=d("0.300000"),
            calibration_sample_size=d("8.000000"),
            calibration_error=d("0.240000"),
            injury_update_count=d("5.000000"),
            fresh_injury_update_count=d("1.000000"),
            news_update_count=d("3.000000"),
            fresh_news_update_count=d("0.000000"),
            source_count=d("4.000000"),
            stale_source_count=d("3.000000"),
            observed_at=datetime(2026, 7, 8, 7, 45, tzinfo=EASTERN),
        ),
        observation(),
    )

    assert memory_report.report_status == "block"
    assert memory_report.recommended_next_step == "refresh_soccer_team_memory_before_calibration"
    assert memory_report.row_count == d("2.000000")
    assert memory_report.observation_count == d("2.000000")
    assert memory_report.pass_count == d("1.000000")
    assert memory_report.watch_count == d("0.000000")
    assert memory_report.block_count == d("1.000000")
    assert memory_report.average_calibration_readiness_score == d("0.681250")
    assert memory_report.minimum_source_freshness_score == d("0.150000")
    assert memory_report.maximum_calibration_error == d("0.240000")

    blocked = memory_report.rows[0]
    assert blocked.soccer_event_bucket == "international-friendly"
    assert blocked.team_memory_bucket == "rotation-heavy-underdog"
    assert blocked.memory_status == "block"
    assert blocked.injury_freshness_share == d("0.200000")
    assert blocked.news_freshness_share == d("0.000000")
    assert blocked.source_freshness_share == d("0.250000")
    assert blocked.aggregated_freshness_score == d("0.150000")
    assert blocked.calibration_sample_size_score == d("0.400000")
    assert blocked.calibration_quality_score == d("0.760000")
    assert blocked.calibration_readiness_score == d("0.402500")
    assert blocked.latest_observed_at == datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
    assert blocked.reason_codes == (
        "calibration_error_block",
        "injury_freshness_block",
        "news_freshness_block",
        "soccer_event_team_memory_block",
        "source_freshness_block",
        "specialist_memory_score_block",
    )

    passing = memory_report.rows[1]
    assert passing.memory_status == "pass"
    assert passing.aggregated_freshness_score == d("1.000000")
    assert passing.calibration_readiness_score == d("0.960000")
    assert passing.reason_codes == ("soccer_event_team_memory_pass",)


def test_payload_is_public_safe_decimal_stringed_deterministic_and_digest_checked() -> None:
    first = report(observation(), observation(soccer_event_bucket="promotion-playoff"))
    second = report(observation(soccer_event_bucket="promotion-playoff"), observation())

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = research_soccer_event_team_memory_report_payload(first)
    assert payload == first.payload
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["row_count"] == "2.000000"
    assert payload["rows"][0]["calibration_readiness_score"] == "0.960000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_numeric_scalars(payload)
    assert_no_raw_identifier_surface(payload)

    tampered = dict(payload)
    tampered["row_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_soccer_event_team_memory_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    unsafe_payload = dict(payload)
    unsafe_payload["match_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_soccer_event_team_memory_report_payload(unsafe_payload)


def test_public_dataclasses_are_frozen_decimal_only_and_validate_bounds() -> None:
    memory_report = report(observation())

    for dataclass_type in (
        ResearchSoccerEventTeamMemoryReportConfig,
        ResearchSoccerEventTeamMemoryObservation,
        ResearchSoccerEventTeamMemoryRow,
        ResearchSoccerEventTeamMemoryReasonCodeCount,
        ResearchSoccerEventTeamMemoryReport,
    ):
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        memory_report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        memory_report.rows[0].calibration_readiness_score = d("1.000000")  # type: ignore[misc]

    dataclass_types = (
        ResearchSoccerEventTeamMemoryReportConfig,
        ResearchSoccerEventTeamMemoryObservation,
        ResearchSoccerEventTeamMemoryRow,
        ResearchSoccerEventTeamMemoryReasonCodeCount,
        ResearchSoccerEventTeamMemoryReport,
    )
    for dataclass_type in dataclass_types:
        hints = get_type_hints(dataclass_type, include_extras=True)
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_share")
                or field.name.endswith("_error")
                or field.name.endswith("_size")
            ):
                annotation = hints[field.name]
                args = get_args(annotation)
                assert annotation is Decimal or (
                    get_origin(annotation) is type(Decimal | None)
                    and Decimal in args
                    and type(None) in args
                )

    with pytest.raises(ValueError, match="specialist_memory_score must be a Decimal"):
        observation(specialist_memory_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="calibration_sample_size must be a Decimal"):
        observation(calibration_sample_size=_DecimalSubclass("1"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_injury_update_count"):
        observation(fresh_injury_update_count=d("7.000000"))
    with pytest.raises(ValueError, match="stale_source_count"):
        observation(stale_source_count=d("6.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_research_soccer_event_team_memory_report(
            (observation(),),
            config=ResearchSoccerEventTeamMemoryReportConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_module_scope_is_report_only_without_io_or_identifier_side_effects() -> None:
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
        "wallet",
        "order",
        "live",
        "trade",
        "signing",
        "mutation",
        "match_id",
        "event_id",
        "team_id",
        "team_name",
        "source_id",
        "source_reference",
        "market_slug",
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
                "delete",
                "send",
                "sign",
            }

    assert imported_modules <= {
        "__future__",
        "collections",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def assert_no_numeric_scalars(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_no_numeric_scalars(child)
        return
    if isinstance(value, list):
        for child in value:
            assert_no_numeric_scalars(child)
        return
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"payload must not expose numeric scalar {value!r}")


def assert_no_raw_identifier_surface(value: object) -> None:
    forbidden_fragments = (
        "match_id",
        "event_id",
        "team_id",
        "team_name",
        "source_id",
        "source_reference",
        "market_slug",
    )
    rendered = repr(value).lower()
    for fragment in forbidden_fragments:
        assert fragment not in rendered
