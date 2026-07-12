from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.probability_screen_research_gap_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def gap(**overrides: object) -> Any:
    module = api()
    values = {
        "case_digest": digest("candidate-alpha"),
        "source_gap_count": d("0.000000"),
        "contradiction_count": d("0.000000"),
        "resolution_rule_gap": d("0.000000"),
        "official_anchor_staleness": d("0.000000"),
        "manual_urgency": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ProbabilityScreenResearchGapPriorityInput(**values)


def report(rows: list[object] | tuple[object, ...]) -> Any:
    module = api()
    return module.build_probability_screen_research_gap_priority_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_report_prioritizes_gap_inputs_and_recommends_manual_next_steps() -> None:
    module = api()
    source_gap = gap(
        case_digest=digest("source-gap"),
        source_gap_count=d("3.000000"),
        contradiction_count=d("1.000000"),
        official_anchor_staleness=d("0.500000"),
        manual_urgency=d("0.400000"),
    )
    contradiction = gap(
        case_digest=digest("contradiction"),
        source_gap_count=d("1.000000"),
        contradiction_count=d("2.000000"),
        resolution_rule_gap=d("1.000000"),
        official_anchor_staleness=d("1.000000"),
        manual_urgency=d("1.000000"),
    )
    stale_anchor = gap(
        case_digest=digest("stale-anchor"),
        source_gap_count=d("1.000000"),
        official_anchor_staleness=d("4.000000"),
        manual_urgency=d("0.200000"),
    )
    ready = gap(
        case_digest=digest("ready"),
        source_gap_count=d("1.000000"),
        manual_urgency=d("0.100000"),
    )

    priority_report = report([ready, source_gap, stale_anchor, contradiction])
    repeated_report = report([contradiction, stale_anchor, source_gap, ready])

    assert type(priority_report) is module.ProbabilityScreenResearchGapPriorityReport
    assert is_dataclass(priority_report)
    assert priority_report.generated_at == GENERATED_AT
    assert priority_report.config_version == (
        module.DEFAULT_PROBABILITY_SCREEN_RESEARCH_GAP_PRIORITY_CONFIG_VERSION
    )
    assert priority_report.report_status == "block"
    assert priority_report.case_count == d("4.000000")
    assert priority_report.high_priority_count == d("1.000000")
    assert priority_report.medium_priority_count == d("2.000000")
    assert priority_report.low_priority_count == d("1.000000")
    assert priority_report.mean_gap_priority == d("4.687500")
    assert priority_report.max_gap_priority == d("8.500000")
    assert [row.case_digest for row in priority_report.rows] == [
        digest("contradiction"),
        digest("stale-anchor"),
        digest("source-gap"),
        digest("ready"),
    ]

    assert priority_report.rows[0].gap_priority == d("8.500000")
    assert priority_report.rows[0].priority_status == "block"
    assert priority_report.rows[0].manual_next_step == (
        "resolve_contradictions_with_official_anchor"
    )
    assert priority_report.rows[0].reason_codes == (
        "research_gap_priority_block",
        "contradiction_block",
        "resolution_rule_missing",
        "official_anchor_stale",
        "manual_urgency_high",
    )
    assert priority_report.rows[1].gap_priority == d("4.700000")
    assert priority_report.rows[1].priority_status == "watch"
    assert priority_report.rows[1].manual_next_step == "refresh_official_anchor"
    assert priority_report.rows[1].reason_codes == (
        "research_gap_priority_watch",
        "source_gap_present",
        "official_anchor_stale",
    )
    assert priority_report.rows[2].gap_priority == d("4.450000")
    assert priority_report.rows[2].manual_next_step == "collect_missing_sources"
    assert priority_report.rows[2].reason_codes == (
        "research_gap_priority_watch",
        "source_gap_block",
        "contradiction_present",
        "official_anchor_watch",
    )
    assert priority_report.rows[3].gap_priority == d("1.100000")
    assert priority_report.rows[3].priority_status == "pass"
    assert priority_report.rows[3].manual_next_step == "ready_for_probability_screen"
    assert priority_report.rows[3].reason_codes == (
        "research_gap_priority_pass",
        "source_gap_present",
    )
    assert priority_report.reason_code_counts == (
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="contradiction_block",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="contradiction_present",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="manual_urgency_high",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="official_anchor_stale",
            row_count=d("2.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="official_anchor_watch",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="research_gap_priority_block",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="research_gap_priority_pass",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="research_gap_priority_watch",
            row_count=d("2.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="resolution_rule_missing",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="source_gap_block",
            row_count=d("1.000000"),
        ),
        module.ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code="source_gap_present",
            row_count=d("2.000000"),
        ),
    )
    assert (
        priority_report.derived_validation_digest
        == repeated_report.derived_validation_digest
    )
    assert len(priority_report.derived_validation_digest) == 64
    assert priority_report.paper_only is True
    assert priority_report.report_only is True
    assert priority_report.readonly is True


def test_empty_report_is_pass_with_zero_decimal_counts() -> None:
    priority_report = report([])

    assert priority_report.report_status == "pass"
    assert priority_report.rows == ()
    assert priority_report.reason_code_counts == ()
    assert priority_report.case_count == d("0.000000")
    assert priority_report.high_priority_count == d("0.000000")
    assert priority_report.medium_priority_count == d("0.000000")
    assert priority_report.low_priority_count == d("0.000000")
    assert priority_report.mean_gap_priority == d("0.000000")
    assert priority_report.max_gap_priority == d("0.000000")


def test_custom_config_drives_priority_status_and_digest() -> None:
    module = api()
    custom_config = module.ProbabilityScreenResearchGapPriorityConfig(
        medium_priority_threshold=d("3.000000"),
        high_priority_threshold=d("6.000000"),
        source_gap_weight=d("2.000000"),
    )

    priority_report = module.build_probability_screen_research_gap_priority_report(
        [
            gap(
                case_digest=digest("custom-config"),
                source_gap_count=d("2.000000"),
            ),
        ],
        generated_at=GENERATED_AT,
        config=custom_config,
    )

    assert priority_report.report_status == "watch"
    assert priority_report.rows[0].gap_priority == d("4.000000")
    assert priority_report.rows[0].priority_status == "watch"
    assert priority_report.rows[0].reason_codes == (
        "research_gap_priority_watch",
        "source_gap_block",
    )
    assert len(priority_report.derived_validation_digest) == 64


def test_payload_is_json_safe_immutable_public_and_decimal_only() -> None:
    module = api()
    raw_private_reference = (
        "candidate-alpha market-alpha slug-alpha question-alpha "
        "https://example.invalid/path token-alpha"
    )
    priority_report = report(
        [
            gap(
                case_digest=digest(raw_private_reference),
                source_gap_count=d("2.000000"),
                manual_urgency=d("0.700000"),
            ),
        ],
    )

    payload = module.probability_screen_research_gap_priority_report_payload(
        priority_report,
    )
    rendered_payload = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-11T12:00:00+00:00"
    assert payload["case_count"] == "1.000000"
    assert payload["rows"][0]["case_digest"] == digest(raw_private_reference)
    assert payload["rows"][0]["source_gap_count"] == "2.000000"
    assert payload["rows"][0]["gap_priority"] == "2.700000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_float(payload)
    assert raw_private_reference not in rendered_payload
    assert "candidate-alpha" not in rendered_payload
    assert "market-alpha" not in rendered_payload
    assert "slug-alpha" not in rendered_payload
    assert "question-alpha" not in rendered_payload
    assert "https://example.invalid/path" not in rendered_payload
    assert "token-alpha" not in rendered_payload
    _assert_public_payload_safe(payload)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["case_count"] = "9.000000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]


def test_validation_is_strict_frozen_digest_backed_and_readonly() -> None:
    module = api()
    base_gap = gap()
    priority_report = report(
        [
            base_gap,
            gap(
                case_digest=digest("case-beta"),
                contradiction_count=d("1.000000"),
            ),
        ],
    )

    assert module.__all__ == (
        "DEFAULT_PROBABILITY_SCREEN_RESEARCH_GAP_PRIORITY_CONFIG_VERSION",
        "ProbabilityScreenResearchGapPriorityConfig",
        "ProbabilityScreenResearchGapPriorityInput",
        "ProbabilityScreenResearchGapPriorityRow",
        "ProbabilityScreenResearchGapPriorityReasonCodeCount",
        "ProbabilityScreenResearchGapPriorityReport",
        "build_probability_screen_research_gap_priority_report",
        "probability_screen_research_gap_priority_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        base_gap.case_digest = digest("mutated")  # type: ignore[misc]
    with pytest.raises(ValueError, match="case_digest"):
        gap(case_digest=_StringSubclass(digest("case-alpha")))
    with pytest.raises(ValueError, match="case_digest"):
        gap(case_digest="not-a-digest")
    with pytest.raises(ValueError, match="source_gap_count"):
        gap(source_gap_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="manual_urgency"):
        gap(manual_urgency=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="manual_urgency"):
        gap(manual_urgency=d("1.500000"))
    with pytest.raises(ValueError, match="source_gap_count"):
        gap(source_gap_count=d("-1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_probability_screen_research_gap_priority_report(
            [base_gap],
            generated_at=_DateTimeSubclass(2026, 7, 11, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(base_gap, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(priority_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(priority_report, derived_validation_digest="0" * 64)

    blocked_row = report(
        [
            gap(
                case_digest=digest("row-validation"),
                contradiction_count=d("2.000000"),
            ),
        ],
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=("research_gap_priority_block", "source_gap_block"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="rows"):
        module.ProbabilityScreenResearchGapPriorityReport(
            generated_at=priority_report.generated_at,
            config_version=priority_report.config_version,
            report_status=priority_report.report_status,
            case_count=priority_report.case_count,
            high_priority_count=priority_report.high_priority_count,
            medium_priority_count=priority_report.medium_priority_count,
            low_priority_count=priority_report.low_priority_count,
            mean_gap_priority=priority_report.mean_gap_priority,
            max_gap_priority=priority_report.max_gap_priority,
            rows=tuple(reversed(priority_report.rows)),
            reason_code_counts=priority_report.reason_code_counts,
            derived_validation_digest=priority_report.derived_validation_digest,
        )


def test_source_file_exposes_no_persistence_live_auth_wallet_or_order_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "probability_screen_research_gap_priority_report.py"
    )
    tree = ast.parse(source_path.read_text())
    banned_identifier_fragments = (
        "network",
        "socket",
        "requests",
        "urllib",
        "auth",
        "wallet",
        "account",
        "broker",
        "trade",
        "trading",
        "order",
        "database",
        "sqlite",
        "postgres",
        "dsn",
        "token",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in banned_identifier_fragments)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in banned_identifier_fragments)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.lower() for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                names.append(node.module.lower())
            assert not any(
                fragment in name
                for name in names
                for fragment in banned_identifier_fragments
            )


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _assert_public_payload_safe(value: object) -> None:
    banned_payload_fragments = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in banned_payload_fragments)
            _assert_public_payload_safe(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_payload_safe(item)
