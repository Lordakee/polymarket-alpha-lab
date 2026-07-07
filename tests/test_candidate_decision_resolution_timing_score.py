from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_resolution_timing_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_CANDIDATE_DECISION_RESOLUTION_TIMING_SCORE_CONFIG_VERSION,
        "min_pass_timing_score": d("0.750000"),
        "min_watch_timing_score": d("0.500000"),
        "max_pass_time_to_close_days": d("14.000000"),
        "max_watch_time_to_close_days": d("30.000000"),
        "max_pass_expected_resolution_lag_days": d("2.000000"),
        "max_watch_expected_resolution_lag_days": d("7.000000"),
        "max_pass_dispute_window_days": d("1.000000"),
        "max_watch_dispute_window_days": d("3.000000"),
        "max_pass_cash_lockup_days": d("7.000000"),
        "max_watch_cash_lockup_days": d("21.000000"),
        "min_pass_event_clock_confidence": d("0.800000"),
        "min_watch_event_clock_confidence": d("0.500000"),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionTimingScoreConfig(**values)


def candidate(
    redacted_candidate_ref: str = (
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    ),
    **overrides: object,
):
    module = api()
    values = {
        "redacted_candidate_ref": redacted_candidate_ref,
        "time_to_close_days": d("5.000000"),
        "expected_resolution_lag_days": d("1.000000"),
        "dispute_window_days": d("0.500000"),
        "cash_lockup_days": d("6.000000"),
        "finalization_time_is_clear": True,
        "official_result_available": True,
        "event_clock_confidence": d("0.900000"),
        "source_report_refs": ("resolution-calendar:abc123",),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionTimingScoreInput(**values)


def report(*candidates: object, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_resolution_timing_score_report(
        candidates,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def walk_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            walk_public_payload(child)
    elif isinstance(value, list):
        for child in value:
            walk_public_payload(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))


def test_near_term_clear_resolution_passes_and_rolls_up_counts() -> None:
    module = api()
    timing_report = report(
        candidate(
            "candidate_ref_1111111111111111111111111111111111111111111111111111111111111111",
        ),
    )

    assert type(timing_report) is module.CandidateDecisionResolutionTimingScoreReport
    assert timing_report.generated_at == GENERATED_AT
    assert timing_report.config_version == (
        "candidate-decision-resolution-timing-score-v0"
    )
    assert timing_report.timing_status == "pass"
    assert timing_report.candidate_count == d("1.000000")
    assert timing_report.pass_count == d("1.000000")
    assert timing_report.watch_count == d("0.000000")
    assert timing_report.blocked_count == d("0.000000")
    assert timing_report.max_timing_score == d("0.850000")
    assert timing_report.min_timing_score == d("0.850000")
    assert timing_report.reason_codes == ("resolution_timing_pass",)

    row = timing_report.rows[0]
    assert row.redacted_candidate_ref == (
        "candidate_ref_1111111111111111111111111111111111111111111111111111111111111111"
    )
    assert row.timing_score == d("0.850000")
    assert row.timing_status == "pass"
    assert row.reason_codes == ("resolution_timing_pass",)
    assert row.hard_blocker_codes == ()
    assert row.source_report_refs == ("resolution-calendar:abc123",)
    assert len(row.derived_validation_digest) == 64
    assert len(timing_report.derived_validation_digest) == 64

    payload = module.candidate_decision_resolution_timing_score_payload(timing_report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["timing_score"] == "0.850000"
    walk_public_payload(payload)


def test_public_payload_omits_source_refs_and_validator_rejects_source_surfaces() -> None:
    module = api()
    timing_report = report(
        candidate(
            "candidate_ref_2222222222222222222222222222222222222222222222222222222222222222",
            source_report_refs=(
                "official-result-check:abc123",
                "resolution-calendar:def456",
            ),
        ),
    )

    payload = module.candidate_decision_resolution_timing_score_payload(timing_report)

    assert "source_report_refs" not in payload["rows"][0]
    with pytest.raises(ValueError, match="source refs"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"rows": [{"source_report_refs": ["resolution-calendar:def456"]}]},
        )
    with pytest.raises(ValueError, match="source refs"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"rows": [{"source_url": "https://example.test/official-result"}]},
        )
    with pytest.raises(ValueError, match="public payload must be a JSON object"):
        module.validate_candidate_decision_resolution_timing_score_public_payload([])


def test_public_payload_validator_rejects_hidden_refs_status_aliases_and_numbers() -> None:
    module = api()

    unsafe_payloads = (
        ({"timing_status": "blocked"}, "timing_status"),
        ({"support_status": "ready"}, "support_status"),
        ({"redacted_candidate_ref": "candidate_ref_not-a-digest"}, "redacted_candidate_ref"),
        ({"raw_candidate_ref": "redacted"}, "raw candidate"),
        ({"safe_key": "candidate_ref_not-a-digest"}, "raw candidate"),
        ({"safe_key": "resolution-calendar:def456"}, "source refs"),
        ({"source_text": "official result text"}, "source refs"),
        ({"safe_key": "example.test/official-result"}, "source refs"),
        ({"safe_key": "records_table"}, "source refs"),
        ({"safe_key": "private-key"}, "unsafe live surface"),
        ({"safe_key": "order id 123"}, "unsafe live surface"),
        ({"candidate_count": 1.0}, "decimal strings"),
        ({"candidate_count": 1}, "decimal strings"),
    )

    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_resolution_timing_score_public_payload(
                payload,
            )


def test_unclear_finalization_and_official_result_unavailable_block_candidate() -> None:
    timing_report = report(
        candidate(
            "candidate_ref_3333333333333333333333333333333333333333333333333333333333333333",
            finalization_time_is_clear=False,
            official_result_available=False,
        ),
    )

    assert timing_report.timing_status == "block"
    assert timing_report.blocked_count == d("1.000000")
    assert timing_report.reason_codes == (
        "finalization_time_unclear_block",
        "official_result_unavailable_block",
    )
    row = timing_report.rows[0]
    assert row.finalization_time_is_clear is False
    assert row.official_result_available is False
    assert row.timing_status == "block"
    assert row.timing_score == d("0.000000")
    assert row.hard_blocker_codes == (
        "finalization_time_unclear_block",
        "official_result_unavailable_block",
    )


def test_long_cash_lockup_is_watch_not_blocked() -> None:
    timing_report = report(
        candidate(
            "candidate_ref_4444444444444444444444444444444444444444444444444444444444444444",
            cash_lockup_days=d("18.000000"),
        ),
    )

    assert timing_report.timing_status == "watch"
    assert timing_report.pass_count == d("0.000000")
    assert timing_report.watch_count == d("1.000000")
    row = timing_report.rows[0]
    assert row.timing_status == "watch"
    assert row.timing_score == d("0.692857")
    assert row.reason_codes == ("cash_lockup_days_watch",)
    assert row.hard_blocker_codes == ()


def test_compounded_watch_timing_risk_blocks_below_watch_score_floor() -> None:
    timing_report = report(
        candidate(
            "candidate_ref_5555555555555555555555555555555555555555555555555555555555555555",
            time_to_close_days=d("30.000000"),
            expected_resolution_lag_days=d("7.000000"),
            dispute_window_days=d("3.000000"),
            cash_lockup_days=d("21.000000"),
            event_clock_confidence=d("0.500000"),
        ),
    )

    assert timing_report.timing_status == "block"
    assert timing_report.blocked_count == d("1.000000")
    row = timing_report.rows[0]
    assert row.timing_score == d("0.000000")
    assert row.timing_status == "block"
    assert row.reason_codes == (
        "timing_score_below_watch_threshold",
        "time_to_close_days_watch",
        "expected_resolution_lag_days_watch",
        "dispute_window_days_watch",
        "cash_lockup_days_watch",
        "event_clock_confidence_watch",
    )
    assert row.hard_blocker_codes == ("timing_score_below_watch_threshold",)


def test_missing_timing_confidence_blocks_candidate() -> None:
    timing_report = report(
        candidate(
            "candidate_ref_6666666666666666666666666666666666666666666666666666666666666666",
            event_clock_confidence=None,
        ),
    )

    assert timing_report.timing_status == "block"
    assert timing_report.blocked_count == d("1.000000")
    assert timing_report.max_timing_score == d("0.000000")
    assert timing_report.min_timing_score == d("0.000000")
    row = timing_report.rows[0]
    assert row.timing_status == "block"
    assert row.timing_score == d("0.000000")
    assert row.reason_codes == ("event_clock_confidence_missing",)
    assert row.hard_blocker_codes == ("event_clock_confidence_missing",)


def test_dispute_lag_blocks_and_reason_code_counts_are_aggregated() -> None:
    timing_report = report(
        candidate(
            "candidate_ref_7777777777777777777777777777777777777777777777777777777777777777",
            expected_resolution_lag_days=d("8.000000"),
            dispute_window_days=d("5.000000"),
        ),
        candidate(
            "candidate_ref_8888888888888888888888888888888888888888888888888888888888888888",
            cash_lockup_days=d("18.000000"),
        ),
    )

    assert timing_report.timing_status == "block"
    assert timing_report.pass_count == d("0.000000")
    assert timing_report.watch_count == d("1.000000")
    assert timing_report.blocked_count == d("1.000000")
    assert timing_report.reason_codes == (
        "expected_resolution_lag_days_block",
        "dispute_window_days_block",
        "cash_lockup_days_watch",
    )
    assert tuple(
        (row.reason_code, row.count, row.candidate_ratio)
        for row in timing_report.reason_code_counts
    ) == (
        ("expected_resolution_lag_days_block", d("1.000000"), d("0.500000")),
        ("dispute_window_days_block", d("1.000000"), d("0.500000")),
        ("cash_lockup_days_watch", d("1.000000"), d("0.500000")),
    )

    blocked, watched = timing_report.rows
    assert blocked.redacted_candidate_ref == (
        "candidate_ref_7777777777777777777777777777777777777777777777777777777777777777"
    )
    assert blocked.timing_status == "block"
    assert blocked.timing_score == d("0.000000")
    assert blocked.hard_blocker_codes == (
        "expected_resolution_lag_days_block",
        "dispute_window_days_block",
    )
    assert watched.redacted_candidate_ref == (
        "candidate_ref_8888888888888888888888888888888888888888888888888888888888888888"
    )


def test_deterministic_sorting_prioritizes_blocked_watch_low_scores_then_ref() -> None:
    timing_report = report(
        candidate(
            "candidate_ref_dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        ),
        candidate(
            "candidate_ref_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            cash_lockup_days=d("18.000000"),
        ),
        candidate(
            "candidate_ref_1111111111111111111111111111111111111111111111111111111111111111",
            expected_resolution_lag_days=d("8.000000"),
        ),
        candidate(
            "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            cash_lockup_days=d("18.000000"),
        ),
        candidate(
            "candidate_ref_2222222222222222222222222222222222222222222222222222222222222222",
            dispute_window_days=d("5.000000"),
        ),
        candidate(
            "candidate_ref_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        ),
    )

    assert tuple(row.redacted_candidate_ref for row in timing_report.rows) == (
        "candidate_ref_1111111111111111111111111111111111111111111111111111111111111111",
        "candidate_ref_2222222222222222222222222222222222222222222222222222222222222222",
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "candidate_ref_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "candidate_ref_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "candidate_ref_dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    )

    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(
            timing_report,
            rows=tuple(reversed(timing_report.rows)),
            derived_validation_digest=timing_report.derived_validation_digest,
        )


def test_public_records_are_frozen_decimal_only_and_enforce_hard_flags() -> None:
    module = api()
    timing_report = report(
        candidate(
            "candidate_ref_9999999999999999999999999999999999999999999999999999999999999999",
        ),
    )
    public_records = (
        config(),
        candidate(
            "candidate_ref_abababababababababababababababababababababababababababababababab",
        ),
        timing_report.rows[0],
        timing_report.reason_code_counts[0],
        timing_report,
    )

    for record in public_records:
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
            elif type(value) in (int, float):
                raise AssertionError(f"{field.name} must not be {type(value).__name__}")

    with pytest.raises(FrozenInstanceError):
        timing_report.rows[0].timing_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(
            candidate(
                "candidate_ref_cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
            ),
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(timing_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(timing_report, paper_only=False)

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_RESOLUTION_TIMING_SCORE_CONFIG_VERSION",
        "BOUNDARY_STATEMENT",
        "CandidateDecisionResolutionTimingScoreConfig",
        "CandidateDecisionResolutionTimingScoreInput",
        "CandidateDecisionResolutionTimingScoreRow",
        "CandidateDecisionResolutionTimingReasonCodeCount",
        "CandidateDecisionResolutionTimingScoreReport",
        "build_candidate_decision_resolution_timing_score_report",
        "candidate_decision_resolution_timing_score_payload",
        "validate_candidate_decision_resolution_timing_score_public_payload",
    )


def test_unsafe_values_and_unredacted_candidate_refs_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        candidate("market-0xabc123")
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        candidate("candidate:unhashed-slug")
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        candidate("candidate_ref_not-a-digest")
    with pytest.raises(ValueError, match="raw market"):
        candidate(source_report_refs=("will biden win?",))
    with pytest.raises(ValueError, match="source refs"):
        candidate(source_report_refs=("https://example.test/official-result",))
    with pytest.raises(ValueError, match="time_to_close_days"):
        candidate(time_to_close_days=d("-0.000001"))
    with pytest.raises(ValueError, match="event_clock_confidence"):
        candidate(event_clock_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="cash_lockup_days"):
        candidate(cash_lockup_days=8)
    with pytest.raises(ValueError, match="finalization_time_is_clear"):
        candidate(finalization_time_is_clear="yes")
    with pytest.raises(ValueError, match="official_result_available"):
        candidate(official_result_available=1)
    with pytest.raises(ValueError, match="event_clock_confidence"):
        candidate(event_clock_confidence=0.9)
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="candidate-decision-resolution-timing-score-test")
    with pytest.raises(ValueError, match="duplicate redacted_candidate_ref"):
        report(
            candidate(
                "candidate_ref_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            ),
            candidate(
                "candidate_ref_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            ),
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"wallet_id": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "submit order"},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "buy/sell recommendation"},
        )
    with pytest.raises(ValueError, match="raw market"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "0xabc123"},
        )
    with pytest.raises(ValueError, match="raw market"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "will biden win?"},
        )
    with pytest.raises(ValueError, match="source refs"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "select candidate_id from private_table"},
        )
    with pytest.raises(ValueError, match="raw candidate"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"candidate_id": "secret-candidate"},
        )
    with pytest.raises(ValueError, match="raw candidate"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "candidate_id=secret-candidate"},
        )
    with pytest.raises(ValueError, match="raw candidate"):
        module.validate_candidate_decision_resolution_timing_score_public_payload(
            {"safe_key": "candidate:unhashed-slug"},
        )


def test_static_module_has_pure_boundary_and_no_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_resolution_timing_score.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "Paper-only report-only readonly" in module.BOUNDARY_STATEMENT
    assert "decision-support gates only" in module.BOUNDARY_STATEMENT
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        ".write(",
        "private_key",
        "position_size",
        "position sizing",
        "recommendation",
        "recommend ",
        "execute_trade",
        "place_order",
        "wallet",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
