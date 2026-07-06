from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "strategy_candidate_source_quorum_repair_priority_v10"
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-candidate-source-quorum-repair-priority-v10",
        "required_independent_sources": d("3"),
        "max_source_age_hours": d("12.000000"),
        "urgent_resolution_hours": d("6.000000"),
        "near_resolution_hours": d("24.000000"),
        "source_disagreement_watch_threshold": d("0.150000"),
        "confidence_impact_threshold": d("0.100000"),
        "high_priority_score_threshold": d("0.350000"),
        "critical_priority_score_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.StrategyCandidateSourceQuorumRepairPriorityV10Config(**values)


def candidate(
    *,
    candidate_id: str = "candidate-alpha",
    market_slug: str = "macro-event",
    independent_sources: str = "3",
    disagreement: str = "0.030000",
    age_hours: str = "2.000000",
    resolution_hours: str = "72.000000",
    confidence_impact: str = "0.020000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyCandidateSourceQuorumRepairPriorityV10Input(
        candidate_id=candidate_id,
        market_slug=market_slug,
        independent_source_count=d(independent_sources),
        source_disagreement=Decimal(disagreement),
        source_age_hours=d(age_hours),
        time_to_resolution_hours=d(resolution_hours),
        confidence_impact=d(confidence_impact),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_source_quorum_repair_priority_v10(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_target_module_exists_before_behavior_checks() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_report_scores_repair_priority_from_quorum_disagreement_recency_resolution_and_confidence() -> None:
    digest = report(
        candidate(
            candidate_id="candidate-critical",
            market_slug="election-event",
            independent_sources="1",
            disagreement="0.280000",
            age_hours="30.000000",
            resolution_hours="2.000000",
            confidence_impact="0.180000",
        ),
        candidate(
            candidate_id="candidate-high",
            market_slug="policy-event",
            independent_sources="2",
            disagreement="0.160000",
            age_hours="20.000000",
            resolution_hours="10.000000",
            confidence_impact="0.110000",
        ),
        candidate(),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == (
        "strategy-candidate-source-quorum-repair-priority-v10"
    )
    assert digest.input_count == d("3")
    assert digest.candidate_count == d("3")
    assert digest.critical_priority_count == d("1")
    assert digest.high_priority_count == d("1")
    assert digest.medium_priority_count == d("0")
    assert digest.low_priority_count == d("1")
    assert digest.max_repair_priority_score == d("0.616333")
    assert digest.mean_repair_priority_score == d("0.360722")
    assert digest.priority_status == "critical"
    assert digest.reason_codes == (
        "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
        "candidate_source_quorum_repair_priority_v10_source_disagreement",
        "candidate_source_quorum_repair_priority_v10_stale_sources",
        "candidate_source_quorum_repair_priority_v10_resolution_urgency",
        "candidate_source_quorum_repair_priority_v10_confidence_impact",
        "candidate_source_quorum_repair_priority_v10_high_priority_present",
        "candidate_source_quorum_repair_priority_v10_critical_priority_present",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    critical, high, low = digest.rows
    assert critical.candidate_id == "candidate-critical"
    assert critical.missing_independent_source_count == d("2")
    assert critical.source_recency_pressure == d("1.000000")
    assert critical.resolution_urgency == d("1.000000")
    assert critical.repair_priority_score == d("0.616333")
    assert critical.priority_band == "critical"
    assert critical.repair_action == "pause_probability_signal"
    assert critical.reason_codes == (
        "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
        "candidate_source_quorum_repair_priority_v10_source_disagreement",
        "candidate_source_quorum_repair_priority_v10_stale_sources",
        "candidate_source_quorum_repair_priority_v10_resolution_urgency",
        "candidate_source_quorum_repair_priority_v10_confidence_impact",
    )

    assert high.candidate_id == "candidate-high"
    assert high.missing_independent_source_count == d("1")
    assert high.resolution_urgency == d("0.777778")
    assert high.repair_priority_score == d("0.431833")
    assert high.priority_band == "high"
    assert high.repair_action == "repair_source_quorum"

    assert low.candidate_id == "candidate-alpha"
    assert low.missing_independent_source_count == d("0")
    assert low.source_recency_pressure == d("0.166667")
    assert low.resolution_urgency == d("0.000000")
    assert low.repair_priority_score == d("0.034000")
    assert low.priority_band == "low"
    assert low.repair_action == "monitor_sources"
    assert low.reason_codes == (
        "candidate_source_quorum_repair_priority_v10_repair_not_needed",
    )


def test_empty_input_returns_clear_readonly_report() -> None:
    digest = report()

    assert digest.input_count == d("0")
    assert digest.candidate_count == d("0")
    assert digest.priority_status == "clear"
    assert digest.max_repair_priority_score == d("0.000000")
    assert digest.mean_repair_priority_score == d("0.000000")
    assert digest.reason_codes == (
        "candidate_source_quorum_repair_priority_v10_clear",
    )
    assert digest.rows == ()


def test_payload_serializes_decimal_strings_iso_time_and_no_floats() -> None:
    module = api()
    digest = report(
        candidate(
            candidate_id="candidate-high",
            market_slug="policy-event",
            independent_sources="2",
            disagreement="0.160000",
            age_hours="20.000000",
            resolution_hours="10.000000",
            confidence_impact="0.110000",
        ),
    )

    payload = module.strategy_candidate_source_quorum_repair_priority_v10_payload(
        digest,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["mean_repair_priority_score"] == "0.431833"
    assert payload["rows"][0]["repair_priority_score"] == "0.431833"
    assert payload["rows"][0]["source_recency_pressure"] == "1.000000"
    assert payload["rows"][0]["reason_codes"] == [
        "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
        "candidate_source_quorum_repair_priority_v10_source_disagreement",
        "candidate_source_quorum_repair_priority_v10_stale_sources",
        "candidate_source_quorum_repair_priority_v10_resolution_urgency",
        "candidate_source_quorum_repair_priority_v10_confidence_impact",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"0.431833"' in encoded
    assert all(type(value) is not float for value in _walk(payload))


def test_validation_rejects_non_decimal_precision_bad_flags_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="required_independent_sources"):
        config(required_independent_sources=d("0"))
    with pytest.raises(ValueError, match="required_independent_sources"):
        config(required_independent_sources=d("2.500000"))
    with pytest.raises(ValueError, match="max_source_age_hours"):
        config(max_source_age_hours=12)
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "strategy-candidate-source-quorum-repair-priority-v10",
            ),
        )
    with pytest.raises(ValueError, match="near_resolution_hours"):
        config(
            urgent_resolution_hours=d("24.000000"),
            near_resolution_hours=d("6.000000"),
        )
    with pytest.raises(ValueError, match="critical_priority_score_threshold"):
        config(
            high_priority_score_threshold=d("0.700000"),
            critical_priority_score_threshold=d("0.600000"),
        )

    with pytest.raises(ValueError, match="independent_source_count"):
        candidate(independent_sources="2.500000")
    with pytest.raises(ValueError, match="source_disagreement must be a Decimal"):
        module.StrategyCandidateSourceQuorumRepairPriorityV10Input(
            candidate_id="candidate-non-decimal",
            market_slug="event",
            independent_source_count=d("3"),
            source_disagreement="0.100000",
            source_age_hours=d("1.000000"),
            time_to_resolution_hours=d("12.000000"),
            confidence_impact=d("0.020000"),
        )
    with pytest.raises(ValueError, match="source_disagreement"):
        candidate(disagreement="1.000001")
    with pytest.raises(ValueError, match="source_age_hours"):
        candidate(age_hours="-1.000000")
    with pytest.raises(ValueError, match="time_to_resolution_hours"):
        candidate(resolution_hours="-1.000000")
    with pytest.raises(ValueError, match="confidence_impact"):
        candidate(confidence_impact="NaN")
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id="")
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate candidate"):
        report(
            candidate(candidate_id="dup", market_slug="same-event"),
            candidate(candidate_id="dup", market_slug="same-event"),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_source_quorum_repair_priority_v10(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    digest = report(candidate())
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].priority_band = "critical"  # type: ignore[misc]
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2"))
    with pytest.raises(ValueError, match="repair_priority_score"):
        replace(
            digest.rows[0],
            repair_priority_score=d("0.999999"),
            priority_band="critical",
            repair_action="pause_probability_signal",
        )
    with pytest.raises(ValueError, match="source_recency_pressure"):
        replace(digest.rows[0], source_recency_pressure=d("0.999999"))
    with pytest.raises(ValueError, match="resolution_urgency"):
        replace(digest.rows[0], resolution_urgency=d("0.999999"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            digest.rows[0],
            reason_codes=(
                "candidate_source_quorum_repair_priority_v10_missing_independent_sources",
            ),
        )

    with pytest.raises(ValueError, match="source_disagreement"):
        module.StrategyCandidateSourceQuorumRepairPriorityV10Input(
            candidate_id="candidate-subclass",
            market_slug="event",
            independent_source_count=d("3"),
            source_disagreement=_DecimalSubclass("0.100000"),
            source_age_hours=d("1.000000"),
            time_to_resolution_hours=d("12.000000"),
            confidence_impact=d("0.020000"),
        )


def test_public_types_are_frozen_and_public_numeric_fields_are_decimal() -> None:
    module = api()
    digest = report(candidate())

    for exported_name in module.__all__:
        exported_value = getattr(module, exported_name)
        if isinstance(exported_value, type):
            assert is_dataclass(exported_value)
            assert exported_value.__dataclass_params__.frozen is True

    for value in (config(), candidate(), digest.rows[0], digest):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_hours")
                or field.name.endswith("_impact")
                or field.name.endswith("_score")
                or field.name.endswith("_pressure")
                or field.name.endswith("_urgency")
                or field.name.endswith("_threshold")
                or field.name == "source_disagreement"
            ):
                assert field.type == "Decimal"
                assert type(getattr(value, field.name)) is Decimal


def test_module_scope_stays_pure_readonly_and_without_float_literals() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/"
        "strategy_candidate_source_quorum_repair_priority_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "place_order",
        "private_key",
        "signing",
        "requests",
        "httpx",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "open", "float"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "open",
                    "request",
                    "read_text",
                    "write_text",
                }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in {
                    "httpx",
                    "os",
                    "pathlib",
                    "psycopg",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "supabase",
                }
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in {
                "httpx",
                "os",
                "pathlib",
                "psycopg",
                "requests",
                "socket",
                "sqlite3",
                "subprocess",
                "supabase",
            }
