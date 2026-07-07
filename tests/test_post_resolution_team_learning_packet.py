from __future__ import annotations

import ast
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.post_resolution_team_learning_packet import (
    PostResolutionTeamLearningFact,
    PostResolutionTeamLearningReport,
    PostResolutionTeamLearningRow,
    build_post_resolution_team_learning_packet,
    post_resolution_team_learning_packet_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def fact(**overrides: object) -> PostResolutionTeamLearningFact:
    values = {
        "team_id": "macro-research",
        "candidate_reference": "candidate-alpha-redacted",
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.570000"),
        "resolved_outcome_probability": d("0.600000"),
        "evidence_quality_score": d("0.860000"),
        "resolution_quality_score": d("0.900000"),
        "cost_drag": d("0.005000"),
        "reason_codes": ("strong_evidence", "clean_resolution"),
        "resolved_at": "2026-07-01T00:00:00Z",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return PostResolutionTeamLearningFact(**values)


def report(*facts: PostResolutionTeamLearningFact) -> PostResolutionTeamLearningReport:
    return build_post_resolution_team_learning_packet(facts)


def test_good_calibration_builds_pass_learning_row_and_payload() -> None:
    packet = report(fact())

    assert is_dataclass(packet)
    assert packet.report_status == "pass"
    assert packet.reason_counts == (
        ("clean_resolution", d("1.000000")),
        ("strong_evidence", d("1.000000")),
    )
    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True

    assert len(packet.rows) == 1
    row = packet.rows[0]
    assert is_dataclass(row)
    assert row.team_id == "macro-research"
    assert row.candidate_reference == "candidate-alpha-redacted"
    assert row.calibration_error == d("0.020000")
    assert row.market_team_delta == d("0.050000")
    assert row.status == "pass"
    assert row.hard_flags == ()
    assert row.next_memory_action == "reinforce_team_memory"

    payload = post_resolution_team_learning_packet_payload(packet)
    assert payload == packet.payload
    assert "rows" not in payload
    assert payload["row_count"] == "1.000000"
    assert payload["status_counts"] == [{"status": "pass", "count": "1.000000"}]
    assert payload["average_calibration_error"] == "0.020000"
    assert payload["average_forecast_minus_market_probability_delta"] == "0.050000"
    assert (
        payload["average_absolute_forecast_minus_market_probability_delta"]
        == "0.050000"
    )
    assert payload["metric_semantics"] == {
        "calibration_error": (
            "abs(forecast_probability - resolved_outcome_probability)"
        ),
        "market_team_delta": "forecast_probability - market_probability",
    }
    assert payload["reason_counts"] == [
        {"reason_code": "clean_resolution", "count": "1.000000"},
        {"reason_code": "strong_evidence", "count": "1.000000"},
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_float(payload)
    rendered = json.dumps(payload, sort_keys=True)
    for forbidden_key in (
        "rows",
        "team_id",
        "candidate_reference",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "macro-research",
        "candidate-alpha-redacted",
    ):
        assert forbidden_key not in rendered


def test_signed_delta_and_absolute_error_semantics_are_locked_down() -> None:
    packet = report(
        fact(
            forecast_probability=d("0.250000"),
            market_probability=d("0.400000"),
            resolved_outcome_probability=d("0.800000"),
            reason_codes=("underconfidence",),
        ),
    )

    row = packet.rows[0]
    assert row.calibration_error == d("0.550000")
    assert row.market_team_delta == d("-0.150000")
    assert row.status == "block"
    assert row.hard_flags == ("severe_calibration_error",)
    assert row.next_memory_action == "debias_underconfidence_memory"

    payload = post_resolution_team_learning_packet_payload(packet)
    assert payload["average_calibration_error"] == "0.550000"
    assert payload["average_forecast_minus_market_probability_delta"] == "-0.150000"
    assert (
        payload["average_absolute_forecast_minus_market_probability_delta"]
        == "0.150000"
    )


def test_public_status_vocabulary_uses_block_only() -> None:
    packet = report(
        fact(
            forecast_probability=d("0.900000"),
            resolved_outcome_probability=d("0.000000"),
            reason_codes=("overconfidence",),
        ),
    )

    payload = post_resolution_team_learning_packet_payload(packet)

    assert packet.report_status == "block"
    assert packet.rows[0].status == "block"
    assert payload["report_status"] == "block"
    assert payload["status_counts"] == [{"status": "block", "count": "1.000000"}]
    assert "block" + "ed" not in json.dumps(payload, sort_keys=True)


def test_public_payload_aggregates_multiple_rows_without_row_identifiers() -> None:
    packet = report(
        fact(
            team_id="zeta-team",
            candidate_reference="candidate-bravo-redacted",
            forecast_probability=d("0.620000"),
            market_probability=d("0.570000"),
            resolved_outcome_probability=d("0.600000"),
            reason_codes=("duplicate_reason", "zeta_reason"),
        ),
        fact(
            team_id="alpha-team",
            candidate_reference="candidate-alpha-redacted",
            forecast_probability=d("0.300000"),
            market_probability=d("0.450000"),
            resolved_outcome_probability=d("0.250000"),
            reason_codes=("alpha_reason", "duplicate_reason"),
        ),
    )

    payload = post_resolution_team_learning_packet_payload(packet)

    assert payload["row_count"] == "2.000000"
    assert payload["status_counts"] == [{"status": "pass", "count": "2.000000"}]
    assert payload["average_calibration_error"] == "0.035000"
    assert payload["average_forecast_minus_market_probability_delta"] == "-0.050000"
    assert (
        payload["average_absolute_forecast_minus_market_probability_delta"]
        == "0.100000"
    )
    assert payload["reason_counts"] == [
        {"reason_code": "alpha_reason", "count": "1.000000"},
        {"reason_code": "duplicate_reason", "count": "2.000000"},
        {"reason_code": "zeta_reason", "count": "1.000000"},
    ]

    rendered = json.dumps(payload, sort_keys=True)
    for forbidden_value in (
        "zeta-team",
        "alpha-team",
        "candidate-bravo-redacted",
        "candidate-alpha-redacted",
        "resolved_at",
    ):
        assert forbidden_value not in rendered


def test_overconfidence_blocks_and_records_memory_action() -> None:
    packet = report(
        fact(
            forecast_probability=d("0.900000"),
            market_probability=d("0.550000"),
            resolved_outcome_probability=d("0.000000"),
            reason_codes=("overconfidence",),
        ),
    )

    row = packet.rows[0]
    assert packet.report_status == "block"
    assert row.calibration_error == d("0.900000")
    assert row.market_team_delta == d("0.350000")
    assert row.status == "block"
    assert row.hard_flags == ("severe_calibration_error",)
    assert row.next_memory_action == "debias_overconfidence_memory"
    assert packet.reason_counts == (("overconfidence", d("1.000000")),)


def test_low_evidence_or_resolution_quality_blocks_learning_memory() -> None:
    packet = report(
        fact(
            candidate_reference="candidate-low-quality-redacted",
            evidence_quality_score=d("0.490000"),
            resolution_quality_score=d("0.450000"),
            reason_codes=("thin_evidence", "resolution_disputed"),
        ),
    )

    row = packet.rows[0]
    assert packet.report_status == "block"
    assert row.status == "block"
    assert row.hard_flags == (
        "evidence_quality_below_floor",
        "resolution_quality_below_floor",
    )
    assert row.next_memory_action == "quarantine_low_quality_resolution"
    assert packet.reason_counts == (
        ("resolution_disputed", d("1.000000")),
        ("thin_evidence", d("1.000000")),
    )


def test_cost_drag_creates_watch_learning_action_without_hard_flag() -> None:
    packet = report(
        fact(
            candidate_reference="candidate-cost-drag-redacted",
            cost_drag=d("0.035000"),
            reason_codes=("fees_exceeded_plan", "slippage"),
        ),
    )

    row = packet.rows[0]
    assert packet.report_status == "watch"
    assert row.status == "watch"
    assert row.hard_flags == ()
    assert row.next_memory_action == "tighten_cost_drag_memory"
    assert packet.reason_counts == (
        ("fees_exceeded_plan", d("1.000000")),
        ("slippage", d("1.000000")),
    )


def test_rows_and_reason_counts_are_sorted_deterministically() -> None:
    packet = report(
        fact(
            team_id="zeta-team",
            candidate_reference="candidate-bravo-redacted",
            resolved_at="2026-07-03T00:00:00Z",
            reason_codes=("duplicate_reason", "zeta_reason"),
        ),
        fact(
            team_id="alpha-team",
            candidate_reference="candidate-charlie-redacted",
            resolved_at="2026-07-02T00:00:00Z",
            reason_codes=("duplicate_reason",),
        ),
        fact(
            team_id="alpha-team",
            candidate_reference="candidate-alpha-redacted",
            resolved_at="2026-07-01T00:00:00Z",
            reason_codes=("alpha_reason",),
        ),
    )

    assert tuple(row.candidate_reference for row in packet.rows) == (
        "candidate-alpha-redacted",
        "candidate-charlie-redacted",
        "candidate-bravo-redacted",
    )
    assert packet.reason_counts == (
        ("alpha_reason", d("1.000000")),
        ("duplicate_reason", d("2.000000")),
        ("zeta_reason", d("1.000000")),
    )
    assert post_resolution_team_learning_packet_payload(packet)["reason_counts"] == [
        {"reason_code": "alpha_reason", "count": "1.000000"},
        {"reason_code": "duplicate_reason", "count": "2.000000"},
        {"reason_code": "zeta_reason", "count": "1.000000"},
    ]


def test_decimal_only_frozen_dataclasses_and_hard_boundary_flags() -> None:
    packet = report(fact())
    row = packet.rows[0]

    for value in (fact(), row, packet):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="forecast_probability"):
        fact(forecast_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability"):
        fact(market_probability=_DecimalSubclass("0.570000"))
    with pytest.raises(ValueError, match="cost_drag"):
        fact(cost_drag=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        fact(reason_codes=("same_reason", "same_reason"))
    with pytest.raises(ValueError, match="paper_only"):
        fact(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(packet, readonly=False)
    with pytest.raises(ValueError, match="payload"):
        replace(packet, payload={})


def test_dataclass_types_are_exact_and_do_not_support_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class FactSubclass(PostResolutionTeamLearningFact):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class RowSubclass(PostResolutionTeamLearningRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReportSubclass(PostResolutionTeamLearningReport):
            pass


def test_unsafe_values_and_payload_downgrades_are_rejected() -> None:
    with pytest.raises(ValueError, match="candidate_reference"):
        fact(candidate_reference=" candidate-alpha-redacted ")
    with pytest.raises(ValueError, match="candidate_reference"):
        fact(candidate_reference="candidate-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        fact(candidate_reference="private key candidate")
    with pytest.raises(ValueError, match="unsafe"):
        fact(candidate_reference="market-slug-redacted")
    with pytest.raises(ValueError, match="unsafe"):
        fact(team_id="team-wallet")
    with pytest.raises(ValueError, match="unsafe"):
        post_resolution_team_learning_packet_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_id": "raw-market-id",
            },
        )
    for unsafe_payload in (
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "rows": [],
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "team_id": "macro-research",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "candidate_reference": "candidate-alpha-redacted",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "market_slug": "raw-market-slug",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "slug": "raw-market-slug",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "question": "Will this leak?",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "source_reference": "raw-source-reference",
        },
    ):
        with pytest.raises(ValueError, match="unsafe"):
            post_resolution_team_learning_packet_payload(unsafe_payload)
    with pytest.raises(ValueError, match="readonly"):
        post_resolution_team_learning_packet_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        post_resolution_team_learning_packet_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "score": 0.1},
        )
    with pytest.raises(ValueError, match="Decimal"):
        post_resolution_team_learning_packet_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "count": 1},
        )


def test_public_payload_helper_rejects_non_aggregate_smuggling_fields() -> None:
    for unsafe_payload in (
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "market_reference": "candidate-alpha-redacted",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "notes": "Will this leak?",
        },
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "arbitrary_metric": "1.000000",
        },
    ):
        with pytest.raises(ValueError, match="payload"):
            post_resolution_team_learning_packet_payload(unsafe_payload)


def test_public_reason_counts_cannot_smuggle_candidate_or_market_identifiers() -> None:
    payload = dict(post_resolution_team_learning_packet_payload(report(fact())))
    for reason_code in (
        "candidate-alpha-redacted",
        "market-alpha",
        "market_alpha",
        "question_text",
        "source_url",
        "sourceurl",
        "raw_url",
    ):
        tampered = dict(payload)
        tampered["reason_counts"] = [
            {"reason_code": reason_code, "count": "1.000000"},
        ]
        with pytest.raises(ValueError, match="payload"):
            post_resolution_team_learning_packet_payload(tampered)


def test_fact_reason_codes_reject_private_identifier_surfaces() -> None:
    for reason_code in (
        "candidate-alpha-redacted",
        "market-alpha",
        "market_alpha",
        "question_text",
        "source_reference",
        "sourceurl",
        "raw_url",
    ):
        with pytest.raises(ValueError, match="reason_codes"):
            fact(reason_codes=(reason_code,))


def test_public_reason_and_payload_text_reject_private_or_action_surfaces() -> None:
    payload = dict(post_resolution_team_learning_packet_payload(report(fact())))
    for reason_code in (
        "database_table",
        "local_dsn",
        "private_token",
        "account_surface",
        "order_surface",
        "trade_surface",
        "buy_signal",
        "sell_signal",
        "recommendation_language",
        "position_sizing",
    ):
        tampered = dict(payload)
        tampered["reason_counts"] = [
            {"reason_code": reason_code, "count": "1.000000"},
        ]
        with pytest.raises(ValueError, match="payload"):
            post_resolution_team_learning_packet_payload(tampered)
        with pytest.raises(ValueError, match="reason_codes"):
            fact(reason_codes=(reason_code,))

    unsafe_payload = {
        **payload,
        "metric_semantics": {
            **payload["metric_semantics"],
            "calibration_error": "writes to memory table",
        },
    }
    with pytest.raises(ValueError, match="payload"):
        post_resolution_team_learning_packet_payload(unsafe_payload)


def test_identifier_and_reason_variants_reject_private_market_source_surfaces() -> None:
    payload = dict(post_resolution_team_learning_packet_payload(report(fact())))
    for reason_code in (
        "auth_surface",
        "marketid_alpha",
        "marketslug_alpha",
        "source_text",
        "sourcetext",
    ):
        tampered = dict(payload)
        tampered["reason_counts"] = [
            {"reason_code": reason_code, "count": "1.000000"},
        ]
        with pytest.raises(ValueError, match="payload"):
            post_resolution_team_learning_packet_payload(tampered)
        with pytest.raises(ValueError, match="reason_codes"):
            fact(reason_codes=(reason_code,))

    for overrides in (
        {"candidate_reference": "private-key-candidate-redacted"},
        {"candidate_reference": "auth-token-candidate-redacted"},
        {"candidate_reference": "source-text-candidate-redacted"},
        {"team_id": "auth-team"},
        {"team_id": "order-submit-team"},
    ):
        with pytest.raises(ValueError, match="unsafe"):
            fact(**overrides)


def test_public_payload_helper_rejects_impossible_hard_flag_aggregates() -> None:
    payload = dict(post_resolution_team_learning_packet_payload(report(fact())))

    payload["hard_flag_counts"] = [
        {"hard_flag": "severe_calibration_error", "count": "1.000000"},
    ]
    with pytest.raises(ValueError, match="hard_flag_counts"):
        post_resolution_team_learning_packet_payload(payload)

    block_without_flags = dict(payload)
    block_without_flags["report_status"] = "block"
    block_without_flags["status_counts"] = [
        {"status": "block", "count": "1.000000"},
    ]
    block_without_flags["hard_flag_counts"] = []
    block_without_flags["next_memory_action_counts"] = [
        {
            "next_memory_action": "debias_overconfidence_memory",
            "count": "1.000000",
        },
    ]
    with pytest.raises(ValueError, match="hard_flag_counts"):
        post_resolution_team_learning_packet_payload(block_without_flags)


def test_public_payload_helper_rejects_impossible_memory_action_aggregates() -> None:
    pass_payload = dict(post_resolution_team_learning_packet_payload(report(fact())))
    pass_payload["next_memory_action_counts"] = [
        {
            "next_memory_action": "debias_overconfidence_memory",
            "count": "1.000000",
        },
    ]
    with pytest.raises(ValueError, match="next_memory_action_counts"):
        post_resolution_team_learning_packet_payload(pass_payload)

    block_payload = dict(
        post_resolution_team_learning_packet_payload(
            report(
                fact(
                    forecast_probability=d("0.900000"),
                    resolved_outcome_probability=d("0.000000"),
                    reason_codes=("overconfidence",),
                ),
            ),
        ),
    )
    block_payload["next_memory_action_counts"] = [
        {"next_memory_action": "reinforce_team_memory", "count": "1.000000"},
    ]
    with pytest.raises(ValueError, match="next_memory_action_counts"):
        post_resolution_team_learning_packet_payload(block_payload)


def test_empty_learning_packet_is_public_safe_noop_payload() -> None:
    packet = report()
    payload = post_resolution_team_learning_packet_payload(packet)

    assert packet.report_status == "pass"
    assert packet.rows == ()
    assert packet.reason_counts == ()
    assert payload["row_count"] == "0.000000"
    assert payload["status_counts"] == []
    assert payload["reason_counts"] == []
    assert payload["hard_flag_counts"] == []
    assert payload["next_memory_action_counts"] == []
    for field_name in (
        "average_calibration_error",
        "average_forecast_minus_market_probability_delta",
        "average_absolute_forecast_minus_market_probability_delta",
        "average_evidence_quality_score",
        "average_resolution_quality_score",
        "average_cost_drag",
    ):
        assert payload[field_name] == "0.000000"


def test_static_module_surface_is_pure_readonly_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/post_resolution_team_learning_packet.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "private_key",
        "live_trading",
        "place_order",
        "signed_payload",
        "postgres",
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "subprocess",
        "socket",
        "open(",
        "getenv",
        "environ",
        "http",
        "://",
    ):
        assert forbidden not in lowered
    assert not re.search(r"\b(auth|broker|signing)\b", lowered)

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
            assert node.func.id != "eval"
            assert node.func.id != "exec"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])
    assert imported_modules <= {"__future__", "dataclasses", "decimal", "typing"}


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
