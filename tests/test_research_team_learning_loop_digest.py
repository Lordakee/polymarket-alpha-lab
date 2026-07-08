from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_learning_loop_digest import (
    DEFAULT_RESEARCH_TEAM_LEARNING_LOOP_DIGEST_CONFIG_VERSION,
    ResearchTeamLearningLoopDigestConfig,
    ResearchTeamLearningLoopDigestInput,
    ResearchTeamLearningLoopDigestReasonCodeCount,
    ResearchTeamLearningLoopDigestReport,
    ResearchTeamLearningLoopDigestRow,
    build_research_team_learning_loop_digest,
    research_team_learning_loop_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    team_key: str = "macro",
    *,
    specialty_key: str = "event_timing",
    learning_label: str = "calibration_loop",
    observed_at: datetime | None = None,
    postmortem_count: Decimal = d("2.000000"),
    calibration_drift_count: Decimal = d("0.000000"),
    information_gap_count: Decimal = d("1.000000"),
    closed_information_gap_count: Decimal = d("1.000000"),
    calibration_error_delta: Decimal = d("-0.020000"),
    confidence_score: Decimal = d("0.900000"),
    lesson_summary: str = "Use base-rate bins before escalating uncertainty.",
    trace_marker: str = "",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamLearningLoopDigestInput:
    return ResearchTeamLearningLoopDigestInput(
        team_key=team_key,
        specialty_key=specialty_key,
        learning_label=learning_label,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=2),
        postmortem_count=postmortem_count,
        calibration_drift_count=calibration_drift_count,
        information_gap_count=information_gap_count,
        closed_information_gap_count=closed_information_gap_count,
        calibration_error_delta=calibration_error_delta,
        confidence_score=confidence_score,
        lesson_summary=lesson_summary,
        trace_marker=trace_marker,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchTeamLearningLoopDigestInput, ...],
    *,
    cfg: ResearchTeamLearningLoopDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamLearningLoopDigestReport:
    return build_research_team_learning_loop_digest(
        rows,
        config=cfg or ResearchTeamLearningLoopDigestConfig(),
        generated_at=generated_at,
    )


def test_learning_loop_digest_reduces_pass_watch_and_block_rows() -> None:
    summary = report(
        (
            item(
                "gamma",
                specialty_key="gap_review",
                learning_label="block_loop",
                postmortem_count=d("1.000000"),
                calibration_drift_count=d("3.000000"),
                information_gap_count=d("3.000000"),
                closed_information_gap_count=d("1.000000"),
                calibration_error_delta=d("0.200000"),
                confidence_score=d("0.400000"),
                lesson_summary="Raw candidate cid-17 and market slug were isolated.",
                trace_marker="candidate_id=cid-17",
            ),
            item(
                "alpha",
                specialty_key="timing",
                learning_label="pass_loop",
            ),
            item(
                "beta",
                specialty_key="calibration",
                learning_label="watch_loop",
                postmortem_count=d("1.000000"),
                calibration_drift_count=d("1.000000"),
                information_gap_count=d("2.000000"),
                closed_information_gap_count=d("1.000000"),
                calibration_error_delta=d("0.080000"),
                confidence_score=d("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, ResearchTeamLearningLoopDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_TEAM_LEARNING_LOOP_DIGEST_CONFIG_VERSION
    assert summary.digest_status == "block"
    assert summary.next_step == "block_public_learning_loop_digest"
    assert summary.team_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.postmortem_count == d("4.000000")
    assert summary.calibration_drift_count == d("4.000000")
    assert summary.information_gap_count == d("6.000000")
    assert summary.closed_information_gap_count == d("3.000000")
    assert summary.open_information_gap_count == d("3.000000")
    assert summary.information_gap_closure_ratio == d("0.500000")
    assert summary.average_confidence_score == d("0.666667")
    assert summary.max_calibration_error_delta == d("0.200000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.team_key for row in summary.digest_rows) == (
        "alpha",
        "beta",
        "gamma",
    )
    pass_row, watch_row, block_row = summary.digest_rows
    assert pass_row.team_status == "pass"
    assert pass_row.open_information_gap_count == d("0.000000")
    assert pass_row.information_gap_closure_ratio == d("1.000000")
    assert pass_row.reason_codes == (
        "research_team_learning_loop_calibration_ok",
        "research_team_learning_loop_confidence_pass",
        "research_team_learning_loop_information_gap_closed",
        "research_team_learning_loop_pass",
        "research_team_learning_loop_postmortem_learning",
    )
    assert watch_row.team_status == "watch"
    assert watch_row.reason_codes == (
        "research_team_learning_loop_calibration_drift_watch",
        "research_team_learning_loop_confidence_watch",
        "research_team_learning_loop_information_gap_watch",
        "research_team_learning_loop_postmortem_learning",
        "research_team_learning_loop_watch",
    )
    assert block_row.team_status == "block"
    assert block_row.reason_codes == (
        "research_team_learning_loop_block",
        "research_team_learning_loop_calibration_drift_block",
        "research_team_learning_loop_confidence_block",
        "research_team_learning_loop_information_gap_block",
        "research_team_learning_loop_postmortem_learning",
    )

    assert all(row.learning_key.startswith("sha256:") for row in summary.digest_rows)
    assert all(row.public_lesson_digest.startswith("sha256:") for row in summary.digest_rows)
    assert summary.reason_codes == tuple(
        count.reason_code for count in summary.reason_code_counts
    )


def test_learning_loop_empty_inputs_returns_public_block_digest() -> None:
    summary = report(())

    assert summary.digest_status == "block"
    assert summary.next_step == "block_public_learning_loop_digest"
    assert summary.team_count == d("0.000000")
    assert summary.digest_rows == ()
    assert summary.reason_codes == ("research_team_learning_loop_no_inputs",)
    assert summary.reason_code_counts == (
        ResearchTeamLearningLoopDigestReasonCodeCount(
            reason_code="research_team_learning_loop_no_inputs",
            count=d("1.000000"),
            team_ratio=d("0.000000"),
        ),
    )


def test_learning_loop_rejects_non_decimal_types_and_mutation() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        item(postmortem_count=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Decimal"):
        item(confidence_score=_DecimalSubclass("0.900000"))

    with pytest.raises(TypeError, match="datetime"):
        item(observed_at="2026-07-08T10:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        item(observed_at=_DateTimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC))

    with pytest.raises(TypeError, match="str"):
        item(team_key=_StringSubclass("macro"))

    with pytest.raises(ValueError, match="UTC-aware"):
        item(observed_at=datetime(2026, 7, 8, 10, 0))

    with pytest.raises(ValueError, match="whole second"):
        item(observed_at=datetime(2026, 7, 8, 10, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(ValueError, match="paper_only"):
        item(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        item(readonly=False)

    with pytest.raises(ValueError, match="whole count"):
        item(information_gap_count=d("1.500000"))

    with pytest.raises(ValueError, match="unit interval"):
        item(confidence_score=d("1.000001"))

    with pytest.raises(ValueError, match="closed information gaps"):
        item(information_gap_count=d("1.000000"), closed_information_gap_count=d("2.000000"))

    with pytest.raises(ValueError, match="observed_at"):
        report((item(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    frozen = item()
    with pytest.raises(FrozenInstanceError):
        frozen.confidence_score = d("0.100000")  # type: ignore[misc]

    summary = report((item(),))
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]

    assert replace(frozen, postmortem_count=d("3.000000")).postmortem_count == d("3.000000")


def test_learning_loop_rejects_public_leaks_and_redacts_private_notes() -> None:
    raw_note = (
        "raw candidate id CAND-7 market id MKT-9 market slug fed-rates "
        "market question Will it happen source ref sec-1 source url "
        "https://example.test/private?token=secret source text says buy sell "
        "recommend position wallet order trade dsn table"
    )
    summary = report(
        (
            item(
                "alpha",
                lesson_summary=raw_note,
                trace_marker="wallet=0x1111111111111111111111111111111111111111",
            ),
        ),
    )
    payload = research_team_learning_loop_digest_payload(summary)
    public = repr(payload).lower()
    for token in (
        "cand-7",
        "mkt-9",
        "fed-rates",
        "will it happen",
        "sec-1",
        "example.test",
        "private?",
        "secret",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "dsn",
        "table",
        "token",
    ):
        assert token not in public

    with pytest.raises(ValueError, match="unsafe"):
        item(team_key="market_slug")

    with pytest.raises(ValueError, match="unsafe"):
        item(learning_label="buy_signal")

    row = summary.digest_rows[0]
    with pytest.raises(ValueError, match="public digest"):
        replace(row, public_lesson_digest="https://example.test/private")

    with pytest.raises(ValueError, match="team_status"):
        replace(row, team_status="blocked")


def test_learning_loop_payload_is_deterministic_and_decimal_string_only() -> None:
    first = report(
        (
            item("beta", learning_label="watch_loop", calibration_drift_count=d("1.000000")),
            item("alpha", learning_label="pass_loop"),
        ),
    )
    second = report(
        (
            item("alpha", learning_label="pass_loop"),
            item("beta", learning_label="watch_loop", calibration_drift_count=d("1.000000")),
        ),
    )

    first_payload = research_team_learning_loop_digest_payload(first)
    second_payload = research_team_learning_loop_digest_payload(second)

    assert first_payload == second_payload
    assert [row["team_key"] for row in first_payload["digest_rows"]] == ["alpha", "beta"]
    assert first_payload["team_count"] == "2.000000"
    assert first_payload["digest_rows"][0]["confidence_score"] == "0.900000"
    assert _contains_no_decimal_or_float(first_payload)


def test_learning_loop_report_and_digest_consistency_is_enforced() -> None:
    summary = report(
        (
            item("alpha", learning_label="pass_loop"),
            item(
                "beta",
                learning_label="watch_loop",
                calibration_drift_count=d("1.000000"),
            ),
        ),
    )
    payload = research_team_learning_loop_digest_payload(summary)

    assert summary.digest_status == "watch"
    assert payload["digest_status"] == summary.digest_status
    assert payload["reason_codes"] == [
        count.reason_code for count in summary.reason_code_counts
    ]
    assert payload["pass_count"] == "1.000000"
    assert payload["watch_count"] == "1.000000"
    assert payload["block_count"] == "0.000000"

    with pytest.raises(ValueError, match="team_count"):
        replace(summary, team_count=d("99.000000"))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())

    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=("research_team_learning_loop_pass",))

    with pytest.raises(ValueError, match="reason_code"):
        replace(
            summary.digest_rows[0],
            reason_codes=(
                "research_team_learning_loop_pass",
                "research_team_learning_loop_pass",
            ),
        )

    with pytest.raises(TypeError, match="report"):
        research_team_learning_loop_digest_payload(object())  # type: ignore[arg-type]


def test_learning_loop_module_is_paper_only_with_no_runtime_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_learning_loop_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in source.lower() for term in forbidden_terms)

    for cls in (
        ResearchTeamLearningLoopDigestConfig,
        ResearchTeamLearningLoopDigestInput,
        ResearchTeamLearningLoopDigestRow,
        ResearchTeamLearningLoopDigestReasonCodeCount,
        ResearchTeamLearningLoopDigestReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True


def _contains_no_decimal_or_float(value: object) -> bool:
    if isinstance(value, (Decimal, float)):
        return False
    if isinstance(value, dict):
        return all(_contains_no_decimal_or_float(item) for item in value.values())
    if isinstance(value, list):
        return all(_contains_no_decimal_or_float(item) for item in value)
    return True
