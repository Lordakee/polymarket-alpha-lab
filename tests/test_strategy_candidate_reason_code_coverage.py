from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
FRESH_REASONING_AT = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)


def _api():
    return import_module("polymarket_alpha_lab.strategy_candidate_reason_code_coverage")


def _config(**overrides):
    values = {
        "config_version": "strategy-candidate-reason-code-coverage-v0",
        "required_team_codes": ("macro_team", "sports_team"),
        "required_category_codes": ("macro", "sports"),
        "max_reasoning_age_seconds": Decimal("86400"),
        "min_evidence_link_count": Decimal("2"),
    }
    values.update(overrides)
    return _api().StrategyCandidateReasonCodeCoverageConfig(**values)


def _descriptor(**overrides):
    values = {
        "candidate_id": "fed-cuts-july-2026",
        "team_code": "macro_team",
        "category_code": "macro",
        "reason_codes": ("positive_edge", "liquid_market"),
        "evidence_links": (
            "https://example.test/fed/meeting-minutes",
            "https://example.test/fed/futures-implied",
        ),
        "reasoning_updated_at": FRESH_REASONING_AT,
    }
    values.update(overrides)
    return _api().StrategyCandidateReasonCodeDescriptor(**values)


def _coverage(*descriptors, **config_overrides):
    return _api().build_strategy_candidate_reason_code_coverage_report(
        descriptors,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_reason_code_coverage_reports_ready_clean_payload_without_recommendations() -> None:
    api = _api()

    report = _coverage(
        _descriptor(candidate_id="fed-cuts-july-2026"),
        _descriptor(
            candidate_id="world-cup-final-2026",
            team_code="sports_team",
            category_code="sports",
            reason_codes=("deep_order_book",),
            evidence_links=(
                "https://example.test/sports/injury-report",
                "https://example.test/sports/market-depth",
            ),
        ),
    )

    assert type(report) is api.StrategyCandidateReasonCodeCoverageReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-candidate-reason-code-coverage-v0"
    assert report.coverage_status == "ready"
    assert report.candidate_count == Decimal("2")
    assert report.reason_code_total_count == Decimal("3")
    assert report.distinct_reason_code_count == Decimal("3")
    assert report.missing_reason_code_count == Decimal("0")
    assert report.duplicate_reason_code_count == Decimal("0")
    assert report.weak_evidence_link_count == Decimal("0")
    assert report.stale_reasoning_count == Decimal("0")
    assert report.covered_team_count == Decimal("2")
    assert report.required_team_count == Decimal("2")
    assert report.missing_team_count == Decimal("0")
    assert report.covered_category_count == Decimal("2")
    assert report.required_category_count == Decimal("2")
    assert report.missing_category_count == Decimal("0")
    assert report.clean_candidate_share == Decimal("1.000000")
    assert report.team_coverage_status == "covered"
    assert report.category_coverage_status == "covered"
    assert report.candidate_rows == (
        api.StrategyCandidateReasonCodeCoverageCandidateRow(
            candidate_id="fed-cuts-july-2026",
            team_code="macro_team",
            category_code="macro",
            reason_code_count=Decimal("2"),
            distinct_reason_code_count=Decimal("2"),
            duplicate_reason_code_count=Decimal("0"),
            evidence_link_count=Decimal("2"),
            weak_evidence_link=False,
            reasoning_age_seconds=Decimal("7200"),
            stale_reasoning=False,
            candidate_status="clean",
        ),
        api.StrategyCandidateReasonCodeCoverageCandidateRow(
            candidate_id="world-cup-final-2026",
            team_code="sports_team",
            category_code="sports",
            reason_code_count=Decimal("1"),
            distinct_reason_code_count=Decimal("1"),
            duplicate_reason_code_count=Decimal("0"),
            evidence_link_count=Decimal("2"),
            weak_evidence_link=False,
            reasoning_age_seconds=Decimal("7200"),
            stale_reasoning=False,
            candidate_status="clean",
        ),
    )
    assert report.team_rows == (
        api.StrategyCandidateReasonCodeCoverageTeamRow(
            team_code="macro_team",
            candidate_count=Decimal("1"),
            coverage_status="covered",
        ),
        api.StrategyCandidateReasonCodeCoverageTeamRow(
            team_code="sports_team",
            candidate_count=Decimal("1"),
            coverage_status="covered",
        ),
    )
    assert report.category_rows == (
        api.StrategyCandidateReasonCodeCoverageCategoryRow(
            category_code="macro",
            candidate_count=Decimal("1"),
            coverage_status="covered",
        ),
        api.StrategyCandidateReasonCodeCoverageCategoryRow(
            category_code="sports",
            candidate_count=Decimal("1"),
            coverage_status="covered",
        ),
    )
    assert report.reason_codes == ("strategy_candidate_reason_code_coverage_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = api.strategy_candidate_reason_code_coverage_payload(report)
    assert payload["candidate_count"] == "2"
    assert payload["clean_candidate_share"] == "1.000000"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_rows"][0]["reasoning_age_seconds"] == "7200"
    assert "recommended" not in repr(payload).lower()
    assert "recommendation" not in repr(payload).lower()


def test_reason_code_coverage_blocks_missing_duplicates_weak_stale_and_gaps() -> None:
    api = _api()

    report = _coverage(
        _descriptor(
            candidate_id="alpha",
            reason_codes=(),
            evidence_links=("https://example.test/one",),
            reasoning_updated_at=GENERATED_AT - timedelta(days=2),
        ),
        _descriptor(
            candidate_id="beta",
            reason_codes=("duplicate_signal", "duplicate_signal"),
            evidence_links=(
                "https://example.test/two",
                "https://example.test/three",
            ),
        ),
    )

    assert report.coverage_status == "blocked"
    assert report.candidate_count == Decimal("2")
    assert report.missing_reason_code_count == Decimal("1")
    assert report.duplicate_reason_code_count == Decimal("1")
    assert report.weak_evidence_link_count == Decimal("1")
    assert report.stale_reasoning_count == Decimal("1")
    assert report.clean_candidate_share == Decimal("0.000000")
    assert report.team_coverage_status == "missing"
    assert report.category_coverage_status == "missing"
    assert report.missing_team_codes == ("sports_team",)
    assert report.missing_category_codes == ("sports",)
    assert report.reason_codes == (
        "missing_candidate_reason_codes",
        "duplicate_candidate_reason_codes",
        "weak_candidate_evidence_links",
        "stale_candidate_reasoning",
        "missing_team_coverage",
        "missing_category_coverage",
    )
    assert tuple(row.candidate_status for row in report.candidate_rows) == (
        "blocked",
        "blocked",
    )
    assert report.candidate_rows[0].reasoning_age_seconds == Decimal("172800")
    assert report.team_rows == (
        api.StrategyCandidateReasonCodeCoverageTeamRow(
            team_code="macro_team",
            candidate_count=Decimal("2"),
            coverage_status="covered",
        ),
        api.StrategyCandidateReasonCodeCoverageTeamRow(
            team_code="sports_team",
            candidate_count=Decimal("0"),
            coverage_status="missing",
        ),
    )
    assert report.category_rows == (
        api.StrategyCandidateReasonCodeCoverageCategoryRow(
            category_code="macro",
            candidate_count=Decimal("2"),
            coverage_status="covered",
        ),
        api.StrategyCandidateReasonCodeCoverageCategoryRow(
            category_code="sports",
            candidate_count=Decimal("0"),
            coverage_status="missing",
        ),
    )


def test_reason_code_coverage_watch_status_for_partial_non_blocking_gaps() -> None:
    report = _coverage(
        _descriptor(candidate_id="alpha"),
        _descriptor(
            candidate_id="beta",
            team_code="sports_team",
            category_code="sports",
            reason_codes=("sports_reason",),
        ),
        required_team_codes=("macro_team",),
        required_category_codes=("macro",),
        min_evidence_link_count=Decimal("3"),
    )

    assert report.coverage_status == "watch"
    assert report.weak_evidence_link_count == Decimal("2")
    assert report.missing_team_count == Decimal("0")
    assert report.missing_category_count == Decimal("0")
    assert report.clean_candidate_share == Decimal("0.000000")
    assert report.reason_codes == ("weak_candidate_evidence_links",)


def test_reason_code_coverage_empty_inputs_block_with_decimal_zeroes() -> None:
    report = _coverage()

    assert report.coverage_status == "blocked"
    assert report.candidate_count == Decimal("0")
    assert report.reason_code_total_count == Decimal("0")
    assert report.distinct_reason_code_count == Decimal("0")
    assert report.clean_candidate_share == Decimal("0.000000")
    assert report.missing_team_codes == ("macro_team", "sports_team")
    assert report.missing_category_codes == ("macro", "sports")
    assert report.reason_codes == (
        "missing_strategy_candidate_descriptors",
        "missing_team_coverage",
        "missing_category_coverage",
    )


def test_reason_code_coverage_validates_frozen_flags_utc_and_payload_types() -> None:
    api = _api()

    descriptor = _descriptor(
        reasoning_updated_at=datetime(
            2026,
            7,
            2,
            12,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )
    assert descriptor.reasoning_updated_at == datetime(2026, 7, 2, 10, 0, tzinfo=UTC)

    with pytest.raises(FrozenInstanceError):
        descriptor.team_code = "other_team"  # type: ignore[misc]

    with pytest.raises(ValueError, match="future"):
        _coverage(_descriptor(reasoning_updated_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="timezone-aware"):
        _coverage(_descriptor(reasoning_updated_at=datetime(2026, 7, 2, 10, 0)))

    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)

    with pytest.raises(ValueError, match="descriptors"):
        api.build_strategy_candidate_reason_code_coverage_report(
            (_descriptor(), object()),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    report = _coverage(_descriptor())
    assert asdict(report)["candidate_count"] == Decimal("1")
    payload = api.strategy_candidate_reason_code_coverage_payload(report)
    assert isinstance(payload, dict)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_reason_code_coverage_adds_tamper_evident_derived_validation() -> None:
    report = _coverage(_descriptor())

    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    payload = _api().strategy_candidate_reason_code_coverage_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.pop("derived_validation_digest")
    values["distinct_reason_code_count"] = Decimal("99")
    with pytest.raises(ValueError, match="distinct_reason_code_count"):
        _api().StrategyCandidateReasonCodeCoverageReport(**values)


def test_reason_code_coverage_rejects_unsafe_public_payload(monkeypatch) -> None:
    api = _api()
    report = _coverage(_descriptor())

    def unsafe_payload(_value):
        return {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "wallet_balance": "0",
        }

    monkeypatch.setattr(api, "json_ready_no_floats", unsafe_payload)
    with pytest.raises(ValueError, match="unsafe live surface field"):
        api.strategy_candidate_reason_code_coverage_payload(report)

    def network_payload(_value):
        return {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "network_url": "https://example.test/live",
        }

    monkeypatch.setattr(api, "json_ready_no_floats", network_payload)
    with pytest.raises(ValueError, match="unsafe live surface field"):
        api.strategy_candidate_reason_code_coverage_payload(report)

    def missing_flag_payload(_value):
        return {
            "report_only": True,
            "readonly": True,
        }

    monkeypatch.setattr(api, "json_ready_no_floats", missing_flag_payload)
    with pytest.raises(ValueError, match="payload paper_only"):
        api.strategy_candidate_reason_code_coverage_payload(report)
