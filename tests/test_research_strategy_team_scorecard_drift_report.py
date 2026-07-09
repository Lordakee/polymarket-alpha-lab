from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_team_scorecard_drift_report import (
    DEFAULT_RESEARCH_STRATEGY_TEAM_SCORECARD_DRIFT_CONFIG_VERSION,
    ResearchStrategyTeamScorecardDriftConfig,
    ResearchStrategyTeamScorecardDriftInput,
    ResearchStrategyTeamScorecardDriftReasonCount,
    ResearchStrategyTeamScorecardDriftReport,
    ResearchStrategyTeamScorecardDriftRow,
    build_research_strategy_team_scorecard_drift_report,
    research_strategy_team_scorecard_drift_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyTeamScorecardDriftConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_TEAM_SCORECARD_DRIFT_CONFIG_VERSION,
        "watch_score_drop": d("0.100000"),
        "block_score_drop": d("0.250000"),
        "max_snapshot_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamScorecardDriftConfig(**values)


def snapshot(
    subject_ref: str = "raw-subject-alpha",
    *,
    baseline_score: Decimal = d("0.800000"),
    current_score: Decimal = d("0.790000"),
    baseline_status: str = "pass",
    current_status: str = "pass",
    baseline_observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    current_observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    reason_codes: tuple[str, ...] = ("scorecard_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyTeamScorecardDriftInput:
    return ResearchStrategyTeamScorecardDriftInput(
        subject_ref=subject_ref,
        baseline_score=baseline_score,
        current_score=current_score,
        baseline_status=baseline_status,
        current_status=current_status,
        baseline_observed_at=baseline_observed_at,
        current_observed_at=current_observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *snapshots: ResearchStrategyTeamScorecardDriftInput,
    cfg: ResearchStrategyTeamScorecardDriftConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyTeamScorecardDriftReport:
    return build_research_strategy_team_scorecard_drift_report(
        snapshots,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_drift_report_redacts_subject_refs_and_validates_digest() -> None:
    digest = report(
        snapshot(
            "raw-subject-alpha",
            baseline_score=d("0.800000"),
            current_score=d("0.790000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == DEFAULT_RESEARCH_STRATEGY_TEAM_SCORECARD_DRIFT_CONFIG_VERSION
    assert digest.row_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("0.000000")
    assert digest.block_count == d("0.000000")
    assert digest.status == "pass"
    assert digest.reason_codes == ("scorecard_drift_clear",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.rows[0]
    assert row.subject_key == _subject_key("raw-subject-alpha")
    assert row.drift_status == "pass"
    assert row.baseline_score == d("0.800000")
    assert row.current_score == d("0.790000")
    assert row.score_delta == d("-0.010000")
    assert row.score_drop == d("0.010000")
    assert row.status_drift == d("0.000000")
    assert row.snapshot_age_seconds == d("900.000000")
    assert row.reason_codes == ("scorecard_drift_clear", "scorecard_input_available")

    payload = research_strategy_team_scorecard_drift_payload(digest)
    assert payload == digest.payload
    assert payload["derived_validation_digest"] == _payload_digest(payload)
    assert payload["rows"][0]["subject_key"] == _subject_key("raw-subject-alpha")
    assert "raw-subject-alpha" not in json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_watch_and_block_drift_rows_are_sorted_and_rolled_up() -> None:
    digest = report(
        snapshot(
            "subject-pass",
            baseline_score=d("0.700000"),
            current_score=d("0.690000"),
            reason_codes=("stable_review",),
        ),
        snapshot(
            "subject-watch",
            baseline_score=d("0.900000"),
            current_score=d("0.740000"),
            baseline_observed_at=GENERATED_AT - timedelta(days=3),
            current_observed_at=GENERATED_AT - timedelta(days=2),
            reason_codes=("manual_review_required",),
        ),
        snapshot(
            "subject-block",
            baseline_score=d("0.850000"),
            current_score=d("0.540000"),
            current_status="block",
            reason_codes=("large_score_gap",),
        ),
    )

    assert digest.status == "block"
    assert digest.row_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.maximum_score_drop == d("0.310000")
    assert digest.average_score_delta == d("-0.160000")
    assert digest.stale_snapshot_count == d("1.000000")
    assert digest.reason_codes == (
        "scorecard_drift_block",
        "score_drop_block",
        "score_drop_watch",
        "snapshot_stale_watch",
        "status_regression_block",
    )
    assert tuple(row.drift_status for row in digest.rows) == ("block", "watch", "pass")
    assert tuple(row.subject_key for row in digest.rows) == (
        _subject_key("subject-block"),
        _subject_key("subject-watch"),
        _subject_key("subject-pass"),
    )
    assert tuple(row.reason_codes for row in digest.rows) == (
        ("large_score_gap", "score_drop_block", "status_regression_block"),
        ("manual_review_required", "score_drop_watch", "snapshot_stale_watch"),
        ("scorecard_drift_clear", "stable_review"),
    )
    assert digest.reason_code_counts == (
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="large_score_gap",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="manual_review_required",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="score_drop_block",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="score_drop_watch",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="scorecard_drift_clear",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="snapshot_stale_watch",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="stable_review",
            count=d("1.000000"),
        ),
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code="status_regression_block",
            count=d("1.000000"),
        ),
    )


def test_utc_normalization_and_strict_boundary_validation() -> None:
    digest = report(
        snapshot(
            baseline_observed_at=datetime(
                2026,
                7,
                8,
                5,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            current_observed_at=datetime(
                2026,
                7,
                8,
                7,
                45,
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

    assert digest.generated_at == GENERATED_AT
    assert digest.rows[0].baseline_observed_at == datetime(2026, 7, 8, 9, 0, tzinfo=UTC)
    assert digest.rows[0].current_observed_at == datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
    assert digest.rows[0].snapshot_age_seconds == d("900.000000")

    with pytest.raises(ValueError, match="baseline_observed_at"):
        snapshot(baseline_observed_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="current_observed_at"):
        report(snapshot(current_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="current_observed_at"):
        snapshot(current_observed_at=GENERATED_AT - timedelta(hours=3))


def test_frozen_dataclasses_decimal_only_numerics_and_hard_flags() -> None:
    digest = report(snapshot("frozen-subject"))

    assert is_dataclass(ResearchStrategyTeamScorecardDriftConfig)
    assert is_dataclass(ResearchStrategyTeamScorecardDriftInput)
    assert is_dataclass(ResearchStrategyTeamScorecardDriftRow)
    assert is_dataclass(ResearchStrategyTeamScorecardDriftReasonCount)
    assert is_dataclass(ResearchStrategyTeamScorecardDriftReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].score_drop = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)
    with pytest.raises(ValueError, match="baseline_score"):
        snapshot(baseline_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_score"):
        snapshot(current_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_score_drop"):
        config(watch_score_drop=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))

    for item in (digest, *digest.rows, *digest.reason_code_counts):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name


def test_payload_helper_rejects_public_identifier_leaks_and_bad_digests() -> None:
    digest = report(snapshot("public-payload-subject"))
    payload = digest.payload
    corrupted_payload = dict(payload)
    corrupted_payload["row_count"] = "2.000000"

    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_team_scorecard_drift_payload(corrupted_payload)
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_team_scorecard_drift_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "candidate_id": "raw-subject-alpha",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_team_scorecard_drift_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"subject_key": _term("http", "://example.test/raw")}],
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_team_scorecard_drift_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [
                    {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                ],
            },
        )


def test_payload_helper_rejects_redigested_contract_tampering() -> None:
    digest = report(snapshot("redigested-contract-subject"))
    payload = digest.payload

    forged_report_status = json.loads(json.dumps(payload))
    forged_report_status["status"] = "blocked"
    forged_report_status["derived_validation_digest"] = _payload_digest(
        forged_report_status,
    )
    with pytest.raises(ValueError, match="status|derived_validation_digest"):
        research_strategy_team_scorecard_drift_payload(forged_report_status)

    forged_row_status = json.loads(json.dumps(payload))
    forged_row_status["rows"][0]["drift_status"] = "blocked"
    forged_row_status["derived_validation_digest"] = _payload_digest(forged_row_status)
    with pytest.raises(ValueError, match="drift_status|status|derived_validation_digest"):
        research_strategy_team_scorecard_drift_payload(forged_row_status)

    forged_count = json.loads(json.dumps(payload))
    forged_count["row_count"] = "2.000000"
    forged_count["derived_validation_digest"] = _payload_digest(forged_count)
    with pytest.raises(ValueError, match="row_count|derived_validation_digest"):
        research_strategy_team_scorecard_drift_payload(forged_count)

    forged_reason_counts = json.loads(json.dumps(payload))
    forged_reason_counts["reason_code_counts"] = []
    forged_reason_counts["derived_validation_digest"] = _payload_digest(
        forged_reason_counts,
    )
    with pytest.raises(ValueError, match="reason_code_counts|derived_validation_digest"):
        research_strategy_team_scorecard_drift_payload(forged_reason_counts)


def test_report_consistency_checks_and_supported_status_vocabulary() -> None:
    digest = report(snapshot("consistent-subject"))

    with pytest.raises(ValueError, match="row_count"):
        replace(digest, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="blocked")
    with pytest.raises(ValueError, match="status"):
        snapshot(current_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="snapshots must not contain duplicate"):
        report(snapshot("duplicate-subject"), snapshot("duplicate-subject"))

    payload = digest.payload
    status_values = {payload["status"]}
    status_values.update(row["drift_status"] for row in payload["rows"])
    assert status_values <= {"pass", "watch", "block"}


def test_static_module_surface_excludes_mutating_and_private_interfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_strategy_team_scorecard_drift_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "order",
        "sign",
        "private_key",
        "investment_advice",
        "live_trading",
        "sizing",
        "recommendation",
        "requests.",
        "urllib",
        "sqlite",
        "sqlalchemy",
        "open(",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
    assert not re.search(r"\b(auth|wallet|broker|order|sign|sizing)\b", lowered)


def _subject_key(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _payload_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _term(*pieces: str) -> str:
    return "".join(pieces)
