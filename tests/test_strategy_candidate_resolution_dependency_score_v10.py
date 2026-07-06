from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_candidate_resolution_dependency_score_v10 import (
    StrategyCandidateResolutionDependencyScoreV10Input,
    StrategyCandidateResolutionDependencyScoreV10Report,
    build_strategy_candidate_resolution_dependency_score_v10_report,
    strategy_candidate_resolution_dependency_score_v10_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_candidate_resolution_dependency_score_v10.py",
)


class StrategyCandidateResolutionDependencyScoreV10InputSubclass(
    StrategyCandidateResolutionDependencyScoreV10Input,
):
    pass


class StrategyCandidateResolutionDependencyScoreV10ReportSubclass(
    StrategyCandidateResolutionDependencyScoreV10Report,
):
    pass


def _report(
    *,
    market_id: str = "market-1",
    dependency_count: Decimal = Decimal("0"),
    critical_dependency_count: Decimal = Decimal("0"),
    official_source_score: Decimal = Decimal("1"),
    source_dependency_penalty: Decimal = Decimal("0"),
    time_to_resolution_minutes: Decimal = Decimal("1440"),
    rule_change_status: str = "stable",
) -> StrategyCandidateResolutionDependencyScoreV10Report:
    return build_strategy_candidate_resolution_dependency_score_v10_report(
        market_id=market_id,
        dependency_count=dependency_count,
        critical_dependency_count=critical_dependency_count,
        official_source_score=official_source_score,
        source_dependency_penalty=source_dependency_penalty,
        time_to_resolution_minutes=time_to_resolution_minutes,
        rule_change_status=rule_change_status,
    )


def test_dependency_score_passes_when_resolution_has_no_external_dependency() -> None:
    report = _report()

    assert report.market_id == "market-1"
    assert report.dependency_status == "pass"
    assert report.dependency_score == Decimal("0.000000")
    assert report.required_followups == ()
    assert report.reason_codes == ("dependency_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    for value in (
        report.dependency_count,
        report.critical_dependency_count,
        report.official_source_score,
        report.source_dependency_penalty,
        report.time_to_resolution_minutes,
        report.dependency_score,
    ):
        assert type(value) is Decimal


def test_dependency_score_watches_moderate_dependency_before_resolution() -> None:
    report = _report(
        market_id="market-watch",
        dependency_count=Decimal("3"),
        critical_dependency_count=Decimal("0"),
        official_source_score=Decimal("0.60"),
        source_dependency_penalty=Decimal("0.40"),
        time_to_resolution_minutes=Decimal("120"),
        rule_change_status="pending_review",
    )

    assert report.dependency_status == "watch"
    assert report.dependency_score == Decimal("0.460000")
    assert report.required_followups == (
        "refresh_official_resolution_source",
        "complete_resolution_check_before_close",
        "review_resolution_rule_change_status",
    )
    assert report.reason_codes == (
        "external_dependency_present",
        "official_source_gap",
        "near_resolution_window",
        "resolution_rule_change_pending_review",
    )


def test_dependency_score_blocks_critical_dependency_with_weak_official_source() -> None:
    report = _report(
        market_id="market-blocked",
        dependency_count=Decimal("2"),
        critical_dependency_count=Decimal("1"),
        official_source_score=Decimal("0.40"),
        source_dependency_penalty=Decimal("0.10"),
        time_to_resolution_minutes=Decimal("720"),
        rule_change_status="stable",
    )

    assert report.dependency_status == "blocked"
    assert report.dependency_score == Decimal("0.390000")
    assert report.required_followups == (
        "confirm_critical_external_dependency",
        "refresh_official_resolution_source",
    )
    assert report.reason_codes == (
        "external_dependency_present",
        "critical_dependency_present",
        "official_source_gap",
    )


def test_dependency_score_clamps_high_risk_unacknowledged_rule_change() -> None:
    report = _report(
        dependency_count=Decimal("10"),
        critical_dependency_count=Decimal("3"),
        official_source_score=Decimal("0"),
        source_dependency_penalty=Decimal("1"),
        time_to_resolution_minutes=Decimal("30"),
        rule_change_status="unacknowledged_change",
    )

    assert report.dependency_status == "blocked"
    assert report.dependency_score == Decimal("1.000000")
    assert report.required_followups == (
        "confirm_critical_external_dependency",
        "refresh_official_resolution_source",
        "reduce_source_dependency_penalty",
        "complete_resolution_check_before_close",
        "review_resolution_rule_change_status",
    )
    assert report.reason_codes == (
        "external_dependency_present",
        "critical_dependency_present",
        "official_source_gap",
        "source_dependency_penalty_high",
        "resolution_imminent",
        "resolution_rule_change_unacknowledged",
    )


def test_dependency_score_payload_is_report_only_and_preserves_decimals() -> None:
    report = _report(
        market_id="market-payload",
        dependency_count=Decimal("3"),
        critical_dependency_count=Decimal("0"),
        official_source_score=Decimal("0.60"),
        source_dependency_penalty=Decimal("0.40"),
        time_to_resolution_minutes=Decimal("120"),
        rule_change_status="pending_review",
    )

    payload = strategy_candidate_resolution_dependency_score_v10_payload(report)

    assert payload == report.payload
    assert payload == {
        "market_id": "market-payload",
        "dependency_count": Decimal("3"),
        "critical_dependency_count": Decimal("0"),
        "official_source_score": Decimal("0.60"),
        "source_dependency_penalty": Decimal("0.40"),
        "time_to_resolution_minutes": Decimal("120"),
        "rule_change_status": "pending_review",
        "dependency_status": "watch",
        "dependency_score": Decimal("0.460000"),
        "required_followups": [
            "refresh_official_resolution_source",
            "complete_resolution_check_before_close",
            "review_resolution_rule_change_status",
        ],
        "reason_codes": [
            "external_dependency_present",
            "official_source_gap",
            "near_resolution_window",
            "resolution_rule_change_pending_review",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("market_id", "", "market_id"),
        ("market_id", " market-1 ", "market_id"),
        ("dependency_count", 1, "dependency_count"),
        ("dependency_count", Decimal("-1"), "dependency_count"),
        ("dependency_count", Decimal("1.5"), "dependency_count"),
        ("critical_dependency_count", Decimal("-1"), "critical_dependency_count"),
        ("official_source_score", Decimal("1.01"), "official_source_score"),
        ("source_dependency_penalty", Decimal("-0.01"), "source_dependency_penalty"),
        ("time_to_resolution_minutes", Decimal("-1"), "time_to_resolution_minutes"),
        ("rule_change_status", "changed", "rule_change_status"),
        ("paper_only", False, "paper_only"),
        ("report_only", False, "report_only"),
        ("readonly", False, "readonly"),
    ),
)
def test_dependency_score_input_validates_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "market_id": "market-1",
        "dependency_count": Decimal("1"),
        "critical_dependency_count": Decimal("0"),
        "official_source_score": Decimal("1"),
        "source_dependency_penalty": Decimal("0"),
        "time_to_resolution_minutes": Decimal("1440"),
        "rule_change_status": "stable",
        field_name: bad_value,
    }

    with pytest.raises(ValueError, match=message):
        StrategyCandidateResolutionDependencyScoreV10Input(**kwargs)


def test_dependency_score_rejects_critical_count_above_dependency_count() -> None:
    with pytest.raises(ValueError, match="critical_dependency_count"):
        _report(
            dependency_count=Decimal("1"),
            critical_dependency_count=Decimal("2"),
        )


def test_dependency_score_outputs_are_frozen_and_consistent() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.dependency_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="dependency_status"):
        replace(report, dependency_status="blocked")
    with pytest.raises(ValueError, match="dependency_score"):
        replace(report, dependency_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="required_followups"):
        replace(report, required_followups=("refresh_official_resolution_source",))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=["dependency_clear"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_dependency_score_rejects_subclasses() -> None:
    input_row = StrategyCandidateResolutionDependencyScoreV10Input(
        market_id="market-1",
        dependency_count=Decimal("0"),
        critical_dependency_count=Decimal("0"),
        official_source_score=Decimal("1"),
        source_dependency_penalty=Decimal("0"),
        time_to_resolution_minutes=Decimal("1440"),
        rule_change_status="stable",
    )
    report = _report()

    with pytest.raises(ValueError, match="input"):
        StrategyCandidateResolutionDependencyScoreV10InputSubclass(**input_row.__dict__)
    with pytest.raises(ValueError, match="report"):
        StrategyCandidateResolutionDependencyScoreV10ReportSubclass(**report.__dict__)


def test_dependency_score_module_scope_stays_pure_readonly() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "typing",
    }

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for banned_term in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
        "private_key",
        "wallet",
        "auth",
        "clob",
        "gamma",
        "supabase",
    ):
        assert banned_term not in source
