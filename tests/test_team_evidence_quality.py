from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from typing import Any

import pytest

from polymarket_alpha_lab.team_evidence_quality import (
    TeamEvidenceQualityConfig,
    TeamEvidenceQualityReport,
    TeamEvidenceQualityRow,
    build_team_evidence_quality_report,
)
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastEvidenceDbRow,
    team_forecast_evidence_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 58, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _payload_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _row_values(row: TeamForecastEvidenceDbRow) -> dict[str, Any]:
    return {field.name: getattr(row, field.name) for field in fields(row)}


def _payload_copy(row: TeamForecastEvidenceDbRow) -> dict[str, Any]:
    return json.loads(json.dumps(row.payload_json, allow_nan=False))


def _bypassed_row(row: TeamForecastEvidenceDbRow, **overrides: Any) -> TeamForecastEvidenceDbRow:
    malformed = object.__new__(TeamForecastEvidenceDbRow)
    kwargs = _row_values(row)
    kwargs.update(overrides)
    for key, value in kwargs.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _bypassed_row_with_payload(
    row: TeamForecastEvidenceDbRow,
    payload_json: dict[str, Any],
    **overrides: Any,
) -> TeamForecastEvidenceDbRow:
    return _bypassed_row(
        row,
        payload_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
        **overrides,
    )


def _evidence_packet(
    *,
    evidence_id: str = "evidence-btc-1",
    team_id: str = "crypto_btc",
    market_slug: str = "bitcoin-above-120k",
    source_id: str = "source-etf-flow-dashboard",
    source_type: str = "market_data",
    data_timestamp: datetime = DATA_TIMESTAMP,
    data_freshness_seconds: int = 120,
    evidence_type: str = "etf_flow",
    evidence_text: str = "US spot ETF net flow improved over the last session.",
    weight: Decimal = d("0.420000"),
    reason_codes: tuple[str, ...] = ("team_crypto_btc", "flow_support"),
) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id=evidence_id,
        team_id=team_id,
        market_slug=market_slug,
        source_id=source_id,
        source_type=source_type,
        data_timestamp=data_timestamp,
        data_freshness_seconds=data_freshness_seconds,
        evidence_type=evidence_type,
        evidence_text=evidence_text,
        weight=weight,
        reason_codes=reason_codes,
    )


def _evidence_row(
    *,
    packet: TeamForecastEvidencePacket | None = None,
    forecast_id: str = "forecast-btc-1",
    config_version: str = "team-forecast-evidence-v0",
    generated_at: datetime = GENERATED_AT,
) -> TeamForecastEvidenceDbRow:
    return team_forecast_evidence_to_db_row(
        packet or _evidence_packet(),
        forecast_id=forecast_id,
        config_version=config_version,
        generated_at=generated_at,
    )


def test_build_report_scores_complete_recovered_evidence_packet() -> None:
    config = TeamEvidenceQualityConfig(stale_after_seconds=3600)
    row = _evidence_row()

    report = build_team_evidence_quality_report(
        [row],
        config=config,
        generated_at=GENERATED_AT,
    )

    assert type(report) is TeamEvidenceQualityReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-evidence-quality-v0"
    assert report.status == "evidence_quality_pass"
    assert report.total_count == 1
    assert report.pass_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.average_quality_score == d("0.855000")
    assert report.counts_by_team_id == {
        "crypto_btc": {"total": 1, "pass": 1, "watch": 0, "blocked": 0},
    }
    assert report.counts_by_market_slug == {
        "bitcoin-above-120k": {"total": 1, "pass": 1, "watch": 0, "blocked": 0},
    }
    assert report.reason_code_counts == {"evidence_quality_complete": 1}
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    quality_row = report.rows[0]
    assert type(quality_row) is TeamEvidenceQualityRow
    assert quality_row.forecast_id == "forecast-btc-1"
    assert quality_row.evidence_id == "evidence-btc-1"
    assert quality_row.team_id == "crypto_btc"
    assert quality_row.market_slug == "bitcoin-above-120k"
    assert quality_row.source_id == "source-etf-flow-dashboard"
    assert quality_row.status == "evidence_quality_pass"
    assert quality_row.quality_score == d("0.855000")
    assert quality_row.reason_codes == ("evidence_quality_complete",)
    assert quality_row.evidence_generated_at == GENERATED_AT
    assert quality_row.data_timestamp == DATA_TIMESTAMP
    assert quality_row.paper_only is True
    assert quality_row.report_only is True
    assert quality_row.readonly is True


def test_build_report_aggregates_watch_and_blocked_rows() -> None:
    config = TeamEvidenceQualityConfig(stale_after_seconds=3600)
    pass_row = _evidence_row()
    stale_row = _evidence_row(
        packet=_evidence_packet(
            evidence_id="evidence-politics-1",
            team_id="politics",
            market_slug="election-turnout-high",
            source_id="source-poll-average",
            source_type="polling",
            evidence_type="poll_average",
            evidence_text="The latest poll average moved upward.",
            reason_codes=("team_politics", "polling_shift"),
        ),
        forecast_id="forecast-politics-1",
        generated_at=GENERATED_AT - timedelta(hours=3),
    )
    missing_identity_row = _bypassed_row(pass_row, evidence_id="")

    report = build_team_evidence_quality_report(
        [pass_row, stale_row, missing_identity_row],
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report.status == "evidence_quality_blocked"
    assert report.total_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert [row.status for row in report.rows] == [
        "evidence_quality_pass",
        "evidence_quality_watch",
        "evidence_quality_blocked",
    ]
    assert report.rows[1].reason_codes == ("evidence_quality_stale",)
    assert report.rows[2].reason_codes == ("evidence_quality_missing_identity",)
    assert report.reason_code_counts == {
        "evidence_quality_complete": 1,
        "evidence_quality_missing_identity": 1,
        "evidence_quality_stale": 1,
    }
    assert report.counts_by_team_id == {
        "crypto_btc": {"total": 2, "pass": 1, "watch": 0, "blocked": 1},
        "politics": {"total": 1, "pass": 0, "watch": 1, "blocked": 0},
    }
    assert report.counts_by_market_slug == {
        "bitcoin-above-120k": {"total": 2, "pass": 1, "watch": 0, "blocked": 1},
        "election-turnout-high": {"total": 1, "pass": 0, "watch": 1, "blocked": 0},
    }


def test_missing_source_metadata_and_reason_text_are_watch_not_blocked() -> None:
    row = _evidence_row()
    payload_json = _payload_copy(row)
    payload_json["evidence"]["source_id"] = ""
    payload_json["evidence"]["evidence_text"] = ""
    payload_json["evidence"]["reason_codes"] = []
    watch_row = _bypassed_row_with_payload(row, payload_json, source_id="")

    report = build_team_evidence_quality_report(
        [watch_row],
        config=TeamEvidenceQualityConfig(stale_after_seconds=3600),
        generated_at=GENERATED_AT,
    )

    assert report.status == "evidence_quality_watch"
    assert report.rows[0].status == "evidence_quality_watch"
    assert report.rows[0].quality_score == d("0.355000")
    assert report.rows[0].reason_codes == (
        "evidence_quality_missing_reason_text",
        "evidence_quality_missing_source_metadata",
    )


@pytest.mark.parametrize(
    "bad_rows",
    (
        (_evidence_row() for _ in range(1)),
        {"row": _evidence_row()},
        "not-rows",
        [_evidence_packet()],
    ),
)
def test_build_report_rejects_non_exact_evidence_row_inputs(bad_rows: object) -> None:
    with pytest.raises(ValueError, match="evidence_rows"):
        build_team_evidence_quality_report(
            bad_rows,  # type: ignore[arg-type]
            config=TeamEvidenceQualityConfig(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_build_report_rejects_false_hard_flags(flag_name: str) -> None:
    row = _evidence_row()
    bad_row = _bypassed_row(row, **{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        build_team_evidence_quality_report(
            [bad_row],
            config=TeamEvidenceQualityConfig(),
            generated_at=GENERATED_AT,
        )


def test_build_report_rejects_invalid_config_and_generated_at() -> None:
    row = _evidence_row()

    with pytest.raises(ValueError, match="config"):
        build_team_evidence_quality_report(
            [row],
            config="bad",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_team_evidence_quality_report(
            [row],
            config=TeamEvidenceQualityConfig(),
            generated_at="2026-07-01",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(TeamEvidenceQualityConfig(), paper_only=False)
