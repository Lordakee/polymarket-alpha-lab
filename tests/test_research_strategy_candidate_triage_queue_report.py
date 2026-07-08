from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_candidate_triage_queue_report import (
    DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION,
    ResearchStrategyCandidateTriageQueueConfig,
    ResearchStrategyCandidateTriageQueueInput,
    ResearchStrategyCandidateTriageQueueReasonCodeCount,
    ResearchStrategyCandidateTriageQueueReport,
    ResearchStrategyCandidateTriageQueueRow,
    build_research_strategy_candidate_triage_queue_report,
    research_strategy_candidate_triage_queue_report_digest,
    research_strategy_candidate_triage_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_candidate_triage_queue_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyCandidateTriageQueueConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION
        ),
        "evidence_gap_watch": d("0.500000"),
        "evidence_gap_block": d("0.850000"),
        "cost_surface_watch": d("0.350000"),
        "cost_surface_block": d("0.750000"),
        "calibration_drift_watch": d("0.100000"),
        "calibration_drift_block": d("0.250000"),
        "team_assignment_watch": d("0.500000"),
        "team_assignment_block": d("0.800000"),
        "stale_data_watch_seconds": d("86400.000000"),
        "stale_data_block_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return ResearchStrategyCandidateTriageQueueConfig(**values)


def item(
    candidate_key: str = "candidate-alpha",
    *,
    team_key: str = "team-alpha",
    evidence_gap_score: Decimal = d("0.100000"),
    cost_surface_score: Decimal = d("0.100000"),
    calibration_drift_score: Decimal = d("0.010000"),
    team_assignment_gap_score: Decimal = d("0.100000"),
    data_observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    evidence_gap_codes: tuple[str, ...] = ("evidence_packet_available",),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyCandidateTriageQueueInput:
    return ResearchStrategyCandidateTriageQueueInput(
        candidate_key=candidate_key,
        team_key=team_key,
        evidence_gap_score=evidence_gap_score,
        cost_surface_score=cost_surface_score,
        calibration_drift_score=calibration_drift_score,
        team_assignment_gap_score=team_assignment_gap_score,
        data_observed_at=data_observed_at,
        evidence_gap_codes=evidence_gap_codes,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyCandidateTriageQueueInput,
    cfg: ResearchStrategyCandidateTriageQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCandidateTriageQueueReport:
    return build_research_strategy_candidate_triage_queue_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_float(item_value)
    if isinstance(value, list):
        for item_value in value:
            assert_no_float(item_value)


def test_pass_report_uses_decimal_payload_strings_and_digest() -> None:
    triage = report(item("candidate-pass"))

    assert is_dataclass(triage)
    assert triage.generated_at == GENERATED_AT
    assert triage.generated_at.tzinfo is UTC
    assert triage.config_version == (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION
    )
    assert triage.candidate_count == d("1.000000")
    assert triage.pass_count == d("1.000000")
    assert triage.watch_count == ZERO
    assert triage.block_count == ZERO
    assert triage.status == "pass"
    assert triage.reason_codes == ("research_strategy_candidate_triage_queue_clear",)
    assert triage.paper_only is True
    assert triage.report_only is True
    assert triage.readonly is True

    row = triage.rows[0]
    assert row.triage_rank == d("1.000000")
    assert row.candidate_key == "candidate-pass"
    assert row.status == "pass"
    assert row.data_age_seconds == d("3600.000000")
    assert row.triage_score == d("0.350000")
    assert row.reason_codes == (
        "evidence_packet_available",
        "triage_clear",
    )

    payload = research_strategy_candidate_triage_queue_report_payload(triage)
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["triage_score"] == "0.350000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["public_digest"] == (
        research_strategy_candidate_triage_queue_report_digest(triage)
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_and_block_rows_roll_up_with_public_status_values() -> None:
    triage = report(
        item(
            "candidate-watch",
            evidence_gap_score=d("0.600000"),
            data_observed_at=GENERATED_AT - timedelta(days=2),
        ),
        item(
            "candidate-block",
            cost_surface_score=d("0.800000"),
            calibration_drift_score=d("0.300000"),
        ),
    )

    assert triage.status == "block"
    assert triage.pass_count == ZERO
    assert triage.watch_count == d("1.000000")
    assert triage.block_count == d("1.000000")
    assert triage.evidence_gap_watch_count == d("1.000000")
    assert triage.cost_surface_watch_count == d("1.000000")
    assert triage.calibration_drift_watch_count == d("1.000000")
    assert triage.stale_data_count == d("1.000000")
    assert triage.reason_codes == (
        "research_strategy_candidate_triage_queue_block",
        "calibration_drift_block",
        "cost_surface_block",
        "data_stale_watch",
        "evidence_gap_watch",
    )
    assert tuple(row.candidate_key for row in triage.rows) == (
        "candidate-block",
        "candidate-watch",
    )
    assert triage.rows[0].status == "block"
    assert triage.rows[0].reason_codes == (
        "calibration_drift_block",
        "cost_surface_block",
        "evidence_packet_available",
    )
    assert triage.rows[1].status == "watch"
    assert triage.rows[1].reason_codes == (
        "data_stale_watch",
        "evidence_gap_watch",
        "evidence_packet_available",
    )


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    triage = report()

    assert triage.status == "block"
    assert triage.candidate_count == ZERO
    assert triage.pass_count == ZERO
    assert triage.watch_count == ZERO
    assert triage.block_count == ZERO
    assert triage.mean_triage_score == ZERO
    assert triage.max_triage_score == ZERO
    assert triage.reason_codes == (
        "research_strategy_candidate_triage_queue_no_inputs",
    )
    assert triage.reason_code_counts == (
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="research_strategy_candidate_triage_queue_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert triage.rows == ()


def test_utc_normalization_for_generated_and_data_times() -> None:
    triage = report(
        item(
            data_observed_at=datetime(
                2026,
                7,
                8,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert triage.generated_at == GENERATED_AT
    assert triage.rows[0].data_observed_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )
    assert triage.rows[0].data_age_seconds == d("3600.000000")


def test_decimal_type_rejection_and_public_numerics_are_decimal_only() -> None:
    triage = report(item("candidate-decimal"))

    with pytest.raises(ValueError, match="evidence_gap_watch"):
        config(evidence_gap_watch=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_surface_score"):
        item(cost_surface_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="calibration_drift_score"):
        item(calibration_drift_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="data_observed_at"):
        item(data_observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(item("aware-data"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="data_observed_at"):
        item(
            data_observed_at=datetime(
                2026,
                7,
                8,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="data_observed_at"):
        report(item(data_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        item(reason_codes=["manual_review"])  # type: ignore[arg-type]

    for public_value in (triage, *triage.rows, *triage.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_triage_score",
        "max_triage_score",
    ):
        assert type(getattr(triage, field_name)) is Decimal


def test_public_leak_rejection_at_construction_and_payload_boundary() -> None:
    for unsafe_value in (
        "raw_candidate_id:abc",
        "market:123",
        "market_slug:event",
        "question:will-it-happen",
        "source_url:https://example.invalid",
        "source_ref:packet",
        "source_text:verbatim",
        "dsn=postgres://example",
        "table:name",
        "token=secret",
        "wallet-address",
        "order-ticket",
        "buy-now",
        "sell-now",
        "recommended-step",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            item(candidate_key=unsafe_value)

    triage = report(item("candidate-safe"))
    object.__setattr__(triage.rows[0], "team_key", "source_url:https://example.invalid")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_candidate_triage_queue_report_payload(triage)


def test_hard_flags_frozen_dataclasses_and_payload_revalidation() -> None:
    triage = report(item("candidate-frozen"))

    assert is_dataclass(ResearchStrategyCandidateTriageQueueConfig)
    assert is_dataclass(ResearchStrategyCandidateTriageQueueInput)
    assert is_dataclass(ResearchStrategyCandidateTriageQueueRow)
    assert is_dataclass(ResearchStrategyCandidateTriageQueueReasonCodeCount)
    assert is_dataclass(ResearchStrategyCandidateTriageQueueReport)
    with pytest.raises(FrozenInstanceError):
        triage.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage.rows[0].triage_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        item(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(triage, readonly=False)

    object.__setattr__(triage.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_candidate_triage_queue_report_payload(triage)


def test_deterministic_payload_and_reason_code_counts() -> None:
    first = report(
        item(
            "zeta-watch",
            evidence_gap_score=d("0.600000"),
            reason_codes=("manual_review_watch",),
        ),
        item(
            "beta-block",
            cost_surface_score=d("0.800000"),
            calibration_drift_score=d("0.300000"),
        ),
        item("alpha-pass"),
    )
    second = report(
        item("alpha-pass"),
        item(
            "beta-block",
            cost_surface_score=d("0.800000"),
            calibration_drift_score=d("0.300000"),
        ),
        item(
            "zeta-watch",
            evidence_gap_score=d("0.600000"),
            reason_codes=("manual_review_watch",),
        ),
    )

    assert research_strategy_candidate_triage_queue_report_payload(first) == (
        research_strategy_candidate_triage_queue_report_payload(second)
    )
    assert research_strategy_candidate_triage_queue_report_digest(first) == (
        research_strategy_candidate_triage_queue_report_digest(second)
    )
    assert tuple(row.candidate_key for row in first.rows) == (
        "beta-block",
        "zeta-watch",
        "alpha-pass",
    )
    assert first.reason_code_counts == (
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="evidence_packet_available",
            count=d("3.000000"),
        ),
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="calibration_drift_block",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="cost_surface_block",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="evidence_gap_watch",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="manual_review_watch",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code="triage_clear",
            count=d("1.000000"),
        ),
    )


def test_report_digest_consistency_validation_and_public_exports() -> None:
    triage = report(item("candidate-consistent"))

    assert triage.public_digest == (
        research_strategy_candidate_triage_queue_report_digest(triage)
    )
    assert (
        research_strategy_candidate_triage_queue_report_payload(triage)["public_digest"]
        == triage.public_digest
    )
    with pytest.raises(ValueError, match="public_digest"):
        replace(triage, public_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(triage, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(triage, status="block")
    with pytest.raises(ValueError, match="mean_triage_score"):
        replace(triage, mean_triage_score=d("9.000000"))

    import polymarket_alpha_lab.research_strategy_candidate_triage_queue_report as triage_module

    assert triage_module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION",
        "ResearchStrategyCandidateTriageQueueConfig",
        "ResearchStrategyCandidateTriageQueueInput",
        "ResearchStrategyCandidateTriageQueueReasonCodeCount",
        "ResearchStrategyCandidateTriageQueueReport",
        "ResearchStrategyCandidateTriageQueueRow",
        "build_research_strategy_candidate_triage_queue_report",
        "research_strategy_candidate_triage_queue_report_digest",
        "research_strategy_candidate_triage_queue_report_payload",
    )


def test_static_forbidden_public_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "dsn",
        "table",
        "token",
        "position",
        "buy",
        "sell",
        "recommend",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
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
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
