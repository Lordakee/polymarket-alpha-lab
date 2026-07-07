from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_evidence_rebuttal_balance_report import (
    ResearchEvidenceRebuttalBalanceConfig,
    ResearchEvidenceRebuttalBalanceEvidenceRow,
    ResearchEvidenceRebuttalBalanceReasonCodeCount,
    ResearchEvidenceRebuttalBalanceReport,
    ResearchEvidenceRebuttalBalanceRow,
    build_research_evidence_rebuttal_balance_report,
    research_evidence_rebuttal_balance_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEvidenceShape:
    research_key: str
    stance: str
    strength: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    raw_id: str = "raw-evidence-001"
    source_url: str = "https://internal.example/research/raw-evidence-001"
    source_text: str = "private research note"
    source_dsn: str = "postgresql://private"
    source_table: str = "internal_packet_sources"
    source_token: str = "secret-token"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEvidenceRebuttalBalanceConfig:
    values = {
        "config_version": "research-evidence-rebuttal-balance-report-v0",
        "min_directional_evidence_count": d("2"),
        "max_pass_absolute_balance_gap": d("0.200000"),
        "max_watch_absolute_balance_gap": d("0.500000"),
    }
    values.update(overrides)
    return ResearchEvidenceRebuttalBalanceConfig(**values)


def evidence(
    index: int,
    *,
    research_key: str = "market_alpha",
    stance: str = "support",
    strength: Decimal = d("0.500000"),
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchEvidenceRebuttalBalanceEvidenceRow:
    return ResearchEvidenceRebuttalBalanceEvidenceRow(
        research_key=research_key,
        stance=stance,
        strength=strength,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=index)
        ),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEvidenceRebuttalBalanceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEvidenceRebuttalBalanceReport:
    return build_research_evidence_rebuttal_balance_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_decimal_zero_report() -> None:
    balance_report = report(())

    assert type(balance_report) is ResearchEvidenceRebuttalBalanceReport
    assert balance_report.generated_at == GENERATED_AT
    assert balance_report.config_version == "research-evidence-rebuttal-balance-report-v0"
    assert balance_report.status == "blocked"
    assert balance_report.research_count == d("0")
    assert balance_report.evidence_count == d("0")
    assert balance_report.pass_count == d("0")
    assert balance_report.watch_count == d("0")
    assert balance_report.blocked_count == d("0")
    assert balance_report.average_balance_score == d("0.000000")
    assert balance_report.max_absolute_balance_gap == d("0.000000")
    assert balance_report.reason_codes == ("no_research_evidence",)
    assert balance_report.reason_code_counts == (
        ResearchEvidenceRebuttalBalanceReasonCodeCount(
            reason_code="no_research_evidence",
            count=d("1"),
        ),
    )
    assert balance_report.rows == ()
    assert balance_report.paper_only is True
    assert balance_report.report_only is True
    assert balance_report.readonly is True


def test_balanced_support_and_rebuttal_evidence_pass_with_decimal_metrics() -> None:
    balance_report = report(
        (
            evidence(
                30,
                stance="neutral",
                strength=d("0.200000"),
                reason_codes=("manually_reviewed",),
            ),
            evidence(10, stance="support", strength=d("0.600000")),
            evidence(20, stance="rebuttal", strength=d("0.600000")),
        ),
    )

    assert balance_report.status == "pass"
    assert balance_report.research_count == d("1")
    assert balance_report.evidence_count == d("3")
    assert balance_report.pass_count == d("1")
    assert balance_report.watch_count == d("0")
    assert balance_report.blocked_count == d("0")
    assert balance_report.average_balance_score == d("1.000000")
    assert balance_report.max_absolute_balance_gap == d("0.000000")
    assert balance_report.reason_codes == ("evidence_rebuttal_balance_pass",)

    row = balance_report.rows[0]
    assert type(row) is ResearchEvidenceRebuttalBalanceRow
    assert row.research_key == "market_alpha"
    assert row.status == "pass"
    assert row.evidence_count == d("3")
    assert row.support_count == d("1")
    assert row.rebuttal_count == d("1")
    assert row.neutral_count == d("1")
    assert row.support_weight == d("0.600000")
    assert row.rebuttal_weight == d("0.600000")
    assert row.neutral_weight == d("0.200000")
    assert row.directional_weight == d("1.200000")
    assert row.support_share == d("0.500000")
    assert row.rebuttal_share == d("0.500000")
    assert row.absolute_balance_gap == d("0.000000")
    assert row.balance_score == d("1.000000")
    assert row.latest_observed_at == GENERATED_AT - timedelta(minutes=10)
    assert row.latest_evidence_age_seconds == d("600.000000")
    assert row.reason_codes == (
        "balanced_evidence",
        "evidence_rebuttal_balance_pass",
        "input_manually_reviewed",
        "neutral_evidence_present",
    )


def test_imbalanced_evidence_watches_and_one_sided_evidence_blocks() -> None:
    balance_report = report(
        (
            evidence(1, research_key="watch_case", stance="support", strength=d("0.750000")),
            evidence(2, research_key="watch_case", stance="rebuttal", strength=d("0.250000")),
            evidence(3, research_key="block_case", stance="support", strength=d("1.000000")),
            evidence(4, research_key="block_case", stance="support", strength=d("0.500000")),
        ),
    )

    assert tuple(row.research_key for row in balance_report.rows) == (
        "block_case",
        "watch_case",
    )
    assert balance_report.status == "blocked"
    assert balance_report.watch_count == d("1")
    assert balance_report.blocked_count == d("1")

    blocked_row, watch_row = balance_report.rows
    assert blocked_row.status == "blocked"
    assert blocked_row.absolute_balance_gap == d("1.000000")
    assert blocked_row.balance_score == d("0.000000")
    assert "one_sided_evidence" in blocked_row.reason_codes

    assert watch_row.status == "watch"
    assert watch_row.support_share == d("0.750000")
    assert watch_row.rebuttal_share == d("0.250000")
    assert watch_row.absolute_balance_gap == d("0.500000")
    assert watch_row.balance_score == d("0.500000")
    assert "moderate_evidence_imbalance" in watch_row.reason_codes


def test_payload_is_deterministic_decimal_only_and_omits_raw_source_material() -> None:
    supplied = SuppliedEvidenceShape(
        research_key="market_alpha",
        stance="support",
        strength=d("0.500000"),
        observed_at=GENERATED_AT - timedelta(minutes=2),
        reason_codes=("reviewed",),
    )
    balance_report = report(
        (
            evidence(3, research_key="z_market", stance="support", strength=d("0.600000")),
            evidence(4, research_key="z_market", stance="rebuttal", strength=d("0.600000")),
            supplied,
            evidence(1, research_key="market_alpha", stance="rebuttal", strength=d("0.500000")),
        ),
    )

    payload = research_evidence_rebuttal_balance_report_payload(balance_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.research_key for row in balance_report.rows) == (
        "market_alpha",
        "z_market",
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["balance_score"] == str(
        balance_report.rows[0].balance_score,
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    for forbidden in (
        "raw-evidence-001",
        "internal.example",
        "private research note",
        "postgresql://private",
        "internal_packet_sources",
        "secret-token",
        "raw_id",
        "source_url",
        "source_text",
        "source_dsn",
        "source_table",
        "source_token",
    ):
        assert forbidden not in encoded


def test_validation_rejects_bad_types_unknown_enums_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="max_pass_absolute_balance_gap"):
        config(max_pass_absolute_balance_gap=d("0.600000"))
    with pytest.raises(ValueError, match="strength"):
        evidence(1, strength=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="strength"):
        evidence(1, strength=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="research_key"):
        evidence(1, research_key="Market Alpha")
    with pytest.raises(ValueError, match="research_key"):
        evidence(1, research_key="raw_id")
    with pytest.raises(ValueError, match="stance"):
        evidence(1, stance="against")
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("source_url",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    balance_report = report(
        (
            evidence(1, stance="support", strength=d("0.500000")),
            evidence(2, stance="rebuttal", strength=d("0.500000")),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        balance_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        balance_report.rows[0].balance_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="balance_score"):
        replace(balance_report.rows[0], balance_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(balance_report, status="watch")


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_evidence_rebuttal_balance_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
