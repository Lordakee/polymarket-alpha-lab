from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_evidence_recheck_freshness_gate_report import (
    ResearchSourceEvidenceRecheckFreshnessGateConfig,
    ResearchSourceEvidenceRecheckFreshnessGateInput,
    ResearchSourceEvidenceRecheckFreshnessGateReport,
    ResearchSourceEvidenceRecheckFreshnessGateRow,
    build_research_source_evidence_recheck_freshness_gate_report,
    research_source_evidence_recheck_freshness_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
_DEFAULT_TIME = object()


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEvidenceShape:
    evidence_ref: str
    observed_at: datetime
    last_rechecked_at: datetime | None
    next_recheck_due_at: datetime
    source_confirmed_at: datetime | None
    contradiction_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceEvidenceRecheckFreshnessGateConfig:
    values = {
        "config_version": "research-source-evidence-recheck-freshness-gate-v0",
        "fresh_evidence_age_seconds": d("3600"),
        "watch_evidence_age_seconds": d("7200"),
        "block_evidence_age_seconds": d("172800"),
        "source_confirmation_stale_after_seconds": d("5400"),
    }
    values.update(overrides)
    return ResearchSourceEvidenceRecheckFreshnessGateConfig(**values)


def evidence(
    ref: str,
    *,
    observed_at: datetime | object = _DEFAULT_TIME,
    last_rechecked_at: datetime | None | object = _DEFAULT_TIME,
    next_recheck_due_at: datetime | object = _DEFAULT_TIME,
    source_confirmed_at: datetime | None | object = _DEFAULT_TIME,
    contradiction_flag: bool = False,
) -> ResearchSourceEvidenceRecheckFreshnessGateInput:
    return ResearchSourceEvidenceRecheckFreshnessGateInput(
        evidence_ref=ref,
        observed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if observed_at is _DEFAULT_TIME
            else observed_at
        ),
        last_rechecked_at=(
            GENERATED_AT - timedelta(minutes=15)
            if last_rechecked_at is _DEFAULT_TIME
            else last_rechecked_at
        ),
        next_recheck_due_at=(
            GENERATED_AT + timedelta(minutes=45)
            if next_recheck_due_at is _DEFAULT_TIME
            else next_recheck_due_at
        ),
        source_confirmed_at=(
            GENERATED_AT - timedelta(minutes=20)
            if source_confirmed_at is _DEFAULT_TIME
            else source_confirmed_at
        ),
        contradiction_flag=contradiction_flag,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceEvidenceRecheckFreshnessGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceEvidenceRecheckFreshnessGateReport:
    return build_research_source_evidence_recheck_freshness_gate_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_report_without_rows() -> None:
    freshness_report = report(())

    assert type(freshness_report) is ResearchSourceEvidenceRecheckFreshnessGateReport
    assert freshness_report.generated_at == GENERATED_AT
    assert freshness_report.config_version == (
        "research-source-evidence-recheck-freshness-gate-v0"
    )
    assert freshness_report.total_evidence_count == d("0.000000")
    assert freshness_report.pass_count == d("0.000000")
    assert freshness_report.watch_count == d("0.000000")
    assert freshness_report.block_count == d("0.000000")
    assert freshness_report.overdue_recheck_count == d("0.000000")
    assert freshness_report.missing_recheck_count == d("0.000000")
    assert freshness_report.stale_source_confirmation_count == d("0.000000")
    assert freshness_report.contradiction_count == d("0.000000")
    assert freshness_report.pass_ratio == d("0.000000")
    assert freshness_report.gate_status == "block"
    assert freshness_report.reason_codes == ("no_source_evidence_rechecks",)
    assert freshness_report.rows == ()
    assert freshness_report.paper_only is True
    assert freshness_report.report_only is True
    assert freshness_report.readonly is True
    assert len(freshness_report.payload_sha256) == 64


def test_builds_pass_watch_and_block_rows_with_decimal_ages() -> None:
    freshness_report = report(
        (
            evidence(
                "candidate-raw-77-market-secret-slug-question-https://source.example/raw",
                observed_at=GENERATED_AT - timedelta(days=3),
                last_rechecked_at=None,
                next_recheck_due_at=GENERATED_AT - timedelta(hours=1),
                source_confirmed_at=None,
                contradiction_flag=True,
            ),
            evidence(
                "private-watch-ref",
                observed_at=GENERATED_AT - timedelta(hours=3, minutes=30),
                last_rechecked_at=GENERATED_AT - timedelta(hours=3),
                next_recheck_due_at=GENERATED_AT - timedelta(minutes=10),
                source_confirmed_at=GENERATED_AT - timedelta(hours=2),
            ),
            evidence("private-pass-ref"),
        ),
    )

    assert freshness_report.gate_status == "block"
    assert freshness_report.total_evidence_count == d("3.000000")
    assert freshness_report.pass_count == d("1.000000")
    assert freshness_report.watch_count == d("1.000000")
    assert freshness_report.block_count == d("1.000000")
    assert freshness_report.overdue_recheck_count == d("2.000000")
    assert freshness_report.missing_recheck_count == d("1.000000")
    assert freshness_report.stale_source_confirmation_count == d("2.000000")
    assert freshness_report.contradiction_count == d("1.000000")
    assert freshness_report.pass_ratio == d("0.333333")
    assert freshness_report.reason_codes == (
        "contradiction_requires_recheck",
        "evidence_recheck_freshness_block",
        "evidence_recheck_freshness_watch",
        "evidence_stale",
        "missing_prior_recheck",
        "recheck_overdue",
        "source_confirmation_missing",
        "source_confirmation_stale",
    )

    row_statuses = tuple(row.gate_status for row in freshness_report.rows)
    assert row_statuses == ("block", "watch", "pass")

    blocked, watched, passed = freshness_report.rows
    assert type(blocked) is ResearchSourceEvidenceRecheckFreshnessGateRow
    assert blocked.row_index == d("1.000000")
    assert blocked.evidence_age_seconds == d("259200.000000")
    assert blocked.recheck_age_seconds is None
    assert blocked.recheck_overdue_seconds == d("3600.000000")
    assert blocked.source_confirmation_age_seconds is None
    assert blocked.contradiction_flag is True
    assert blocked.gate_status == "block"
    assert blocked.reason_codes == (
        "contradiction_requires_recheck",
        "evidence_recheck_freshness_block",
        "evidence_stale",
        "missing_prior_recheck",
        "recheck_overdue",
        "source_confirmation_missing",
    )

    assert watched.row_index == d("2.000000")
    assert watched.evidence_age_seconds == d("12600.000000")
    assert watched.recheck_age_seconds == d("10800.000000")
    assert watched.recheck_overdue_seconds == d("600.000000")
    assert watched.source_confirmation_age_seconds == d("7200.000000")
    assert watched.gate_status == "watch"
    assert watched.reason_codes == (
        "evidence_recheck_freshness_watch",
        "evidence_stale",
        "recheck_overdue",
        "source_confirmation_stale",
    )

    assert passed.row_index == d("3.000000")
    assert passed.evidence_age_seconds == d("1800.000000")
    assert passed.recheck_age_seconds == d("900.000000")
    assert passed.recheck_overdue_seconds == d("0.000000")
    assert passed.source_confirmation_age_seconds == d("1200.000000")
    assert passed.gate_status == "pass"
    assert passed.reason_codes == ("evidence_recheck_freshness_pass",)


def test_payload_is_public_deterministic_and_sha256_checked() -> None:
    freshness_report = report(
        (
            evidence("private-b-ref"),
            evidence(
                "candidate-raw-a-market-slug-question-https://source.example/text",
                observed_at=GENERATED_AT - timedelta(days=3),
                last_rechecked_at=None,
                next_recheck_due_at=GENERATED_AT - timedelta(hours=1),
                source_confirmed_at=None,
            ),
        ),
    )

    payload = research_source_evidence_recheck_freshness_gate_report_payload(
        freshness_report,
    )
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    payload_without_digest = dict(payload)
    digest = payload_without_digest.pop("payload_sha256")
    expected = hashlib.sha256(
        json.dumps(
            payload_without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert digest == expected
    assert payload["rows"][0]["evidence_age_seconds"] == "259200.000000"
    assert payload["rows"][0]["recheck_age_seconds"] is None
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert "candidate-raw-a" not in encoded
    assert "market-slug-question" not in encoded
    assert "source.example" not in encoded
    assert "evidence_ref" not in encoded

    with pytest.raises(ValueError, match="payload_sha256"):
        replace(freshness_report, payload_sha256="0" * 64)


def test_validation_rejects_bad_types_statuses_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="fresh_evidence_age_seconds"):
        config(fresh_evidence_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_evidence_age_seconds"):
        config(watch_evidence_age_seconds=_DecimalSubclass("7200"))
    with pytest.raises(ValueError, match="block_evidence_age_seconds"):
        config(block_evidence_age_seconds=d("7000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence("private-pass-ref"),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (evidence("private-pass-ref"),),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_ref"):
        evidence(" private-ref")
    with pytest.raises(ValueError, match="observed_at"):
        evidence("private-ref", observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report(
            (
                evidence(
                    "private-ref",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="next_recheck_due_at"):
        evidence(
            "private-ref",
            observed_at=GENERATED_AT - timedelta(hours=1),
            next_recheck_due_at=GENERATED_AT - timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="last_rechecked_at"):
        evidence(
            "private-ref",
            observed_at=GENERATED_AT - timedelta(hours=1),
            last_rechecked_at=GENERATED_AT - timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="contradiction_flag"):
        replace(evidence("private-ref"), contradiction_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence("private-ref"), paper_only=False)


def test_supplied_shapes_are_coerced_and_public_dataclasses_are_frozen() -> None:
    freshness_report = report(
        (
            SuppliedEvidenceShape(
                evidence_ref="shape-ref",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                last_rechecked_at=GENERATED_AT - timedelta(minutes=15),
                next_recheck_due_at=GENERATED_AT + timedelta(minutes=45),
                source_confirmed_at=GENERATED_AT - timedelta(minutes=20),
            ),
        ),
    )

    assert freshness_report.gate_status == "pass"
    with pytest.raises(FrozenInstanceError):
        freshness_report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        freshness_report.rows[0].gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="gate_status"):
        replace(freshness_report.rows[0], gate_status="blocked")
    with pytest.raises(ValueError, match="pass_count"):
        replace(freshness_report, pass_count=d("2.000000"))


def test_owned_module_has_no_runtime_side_effect_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_evidence_recheck_freshness_gate_report.py"
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
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "redis",
        "live_trading",
        "private_key",
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
