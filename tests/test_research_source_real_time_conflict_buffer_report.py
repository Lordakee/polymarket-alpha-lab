from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_real_time_conflict_buffer_report import (
    DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION,
    ResearchSourceRealTimeConflictBufferConfig,
    ResearchSourceRealTimeConflictBufferInput,
    ResearchSourceRealTimeConflictBufferReport,
    ResearchSourceRealTimeConflictBufferRow,
    build_research_source_real_time_conflict_buffer_report,
    research_source_real_time_conflict_buffer_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceRealTimeConflictBufferConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION
        ),
        "fresh_update_age_seconds": d("300.000000"),
        "stale_update_age_seconds": d("3600.000000"),
        "min_corroborating_family_count": d("3.000000"),
        "weak_authority_score": d("0.500000"),
        "high_contradiction_pressure": d("0.700000"),
        "low_extraction_confidence": d("0.600000"),
        "watch_buffer_risk_score": d("0.350000"),
        "blocked_buffer_risk_score": d("0.700000"),
        "recency_weight": d("0.250000"),
        "authority_weight": d("0.200000"),
        "corroboration_weight": d("0.200000"),
        "contradiction_weight": d("0.250000"),
        "extraction_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchSourceRealTimeConflictBufferConfig(**values)


def conflict(
    conflict_key: str,
    *,
    update_age_seconds: Decimal = d("120.000000"),
    authority_tier: str = "official",
    corroborating_family_count: Decimal = d("3.000000"),
    contradicting_family_count: Decimal = d("0.000000"),
    contradiction_pressure: Decimal = d("0.000000"),
    extraction_confidence: Decimal = d("0.950000"),
) -> ResearchSourceRealTimeConflictBufferInput:
    return ResearchSourceRealTimeConflictBufferInput(
        conflict_key=conflict_key,
        update_age_seconds=update_age_seconds,
        authority_tier=authority_tier,
        corroborating_family_count=corroborating_family_count,
        contradicting_family_count=contradicting_family_count,
        contradiction_pressure=contradiction_pressure,
        extraction_confidence=extraction_confidence,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceRealTimeConflictBufferConfig | None = None,
) -> ResearchSourceRealTimeConflictBufferReport:
    return build_research_source_real_time_conflict_buffer_report(
        rows,
        config=cfg or config(),
    )


def test_buffers_conflicts_into_block_watch_and_pass_rows() -> None:
    buffer_report = report(
        (
            conflict("case-pass"),
            conflict(
                "case-watch",
                update_age_seconds=d("1800.000000"),
                authority_tier="independent",
                corroborating_family_count=d("2.000000"),
                contradicting_family_count=d("1.000000"),
                contradiction_pressure=d("0.400000"),
                extraction_confidence=d("0.800000"),
            ),
            conflict(
                "case-block",
                update_age_seconds=d("7200.000000"),
                authority_tier="unverified",
                corroborating_family_count=d("1.000000"),
                contradicting_family_count=d("3.000000"),
                contradiction_pressure=d("0.900000"),
                extraction_confidence=d("0.300000"),
            ),
        ),
    )

    assert type(buffer_report) is ResearchSourceRealTimeConflictBufferReport
    assert buffer_report.report_status == "block"
    assert buffer_report.input_count == d("3.000000")
    assert buffer_report.blocked_count == d("1.000000")
    assert buffer_report.watch_count == d("1.000000")
    assert buffer_report.pass_count == d("1.000000")
    assert buffer_report.stale_update_count == d("1.000000")
    assert buffer_report.weak_authority_count == d("2.000000")
    assert buffer_report.low_corroboration_count == d("2.000000")
    assert buffer_report.high_contradiction_count == d("1.000000")
    assert buffer_report.low_extraction_confidence_count == d("1.000000")
    assert buffer_report.highest_buffer_risk_score == d("0.838333")
    assert tuple(row.conflict_key for row in buffer_report.rows) == (
        "case-block",
        "case-watch",
        "case-pass",
    )
    assert tuple(row.buffer_status for row in buffer_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.priority_rank for row in buffer_report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked = buffer_report.rows[0]
    assert type(blocked) is ResearchSourceRealTimeConflictBufferRow
    assert blocked.recency_risk_score == d("1.000000")
    assert blocked.authority_score == d("0.200000")
    assert blocked.authority_risk_score == d("0.800000")
    assert blocked.corroboration_score == d("0.333333")
    assert blocked.corroboration_gap_score == d("0.666667")
    assert blocked.extraction_gap_score == d("0.700000")
    assert blocked.buffer_risk_score == d("0.838333")
    assert blocked.reason_codes == (
        "real_time_conflict_buffer_status_block",
        "real_time_conflict_update_stale",
        "real_time_conflict_authority_weak",
        "real_time_conflict_corroboration_low",
        "real_time_conflict_pressure_high",
        "real_time_conflict_extraction_low",
    )

    assert buffer_report.rows[1].buffer_risk_score == d("0.400303")
    assert buffer_report.rows[2].buffer_risk_score == d("0.005000")


def test_recency_authority_and_custom_thresholds_drive_buffer_status() -> None:
    cfg = config(
        stale_update_age_seconds=d("900.000000"),
        blocked_buffer_risk_score=d("0.600000"),
        watch_buffer_risk_score=d("0.250000"),
        weak_authority_score=d("0.650000"),
    )

    buffer_report = report(
        (
            conflict(
                "case-stale-primary",
                update_age_seconds=d("901.000000"),
                authority_tier="primary",
                corroborating_family_count=d("3.000000"),
                contradiction_pressure=d("0.100000"),
                extraction_confidence=d("0.900000"),
            ),
            conflict(
                "case-fresh-low-authority",
                update_age_seconds=d("60.000000"),
                authority_tier="independent",
                corroborating_family_count=d("3.000000"),
                contradiction_pressure=d("0.100000"),
                extraction_confidence=d("0.900000"),
            ),
        ),
        cfg=cfg,
    )

    assert tuple(row.conflict_key for row in buffer_report.rows) == (
        "case-stale-primary",
        "case-fresh-low-authority",
    )
    assert buffer_report.rows[0].buffer_status == "watch"
    assert buffer_report.rows[0].recency_risk_score == d("1.000000")
    assert buffer_report.rows[0].reason_codes == (
        "real_time_conflict_buffer_status_watch",
        "real_time_conflict_update_stale",
    )
    assert buffer_report.rows[1].buffer_status == "pass"
    assert buffer_report.rows[1].authority_score == d("0.500000")
    assert buffer_report.rows[1].reason_codes == (
        "real_time_conflict_buffer_status_pass",
        "real_time_conflict_authority_weak",
    )


def test_public_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    first = report(
        (
            conflict("case-b", authority_tier="primary"),
            conflict(
                "case-a",
                update_age_seconds=d("7200.000000"),
                authority_tier="unverified",
                corroborating_family_count=d("1.000000"),
                contradicting_family_count=d("2.000000"),
                contradiction_pressure=d("0.800000"),
                extraction_confidence=d("0.400000"),
            ),
        ),
    )
    second = report(
        (
            conflict(
                "case-a",
                update_age_seconds=d("7200.000000"),
                authority_tier="unverified",
                corroborating_family_count=d("1.000000"),
                contradicting_family_count=d("2.000000"),
                contradiction_pressure=d("0.800000"),
                extraction_confidence=d("0.400000"),
            ),
            conflict("case-b", authority_tier="primary"),
        ),
    )

    first_payload = research_source_real_time_conflict_buffer_report_payload(first)
    second_payload = research_source_real_time_conflict_buffer_report_payload(second)
    first_encoded = json.dumps(first_payload, sort_keys=True, separators=(",", ":"))
    second_encoded = json.dumps(second_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first_encoded == second_encoded
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert _sha256_without_digest(first_payload) == first.derived_validation_digest
    assert first_payload["rows"][0]["derived_validation_digest"] == (
        first.rows[0].derived_validation_digest
    )
    assert not any(type(value) in (int, float) for value in _walk_payload_values(first_payload))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, report_status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first.rows[0], buffer_status="watch")


def test_public_payload_and_inputs_reject_sensitive_surfaces() -> None:
    with pytest.raises(ValueError, match="conflict_key"):
        conflict("candidate-raw-123")
    with pytest.raises(ValueError, match="conflict_key"):
        conflict("market-0xabc")
    with pytest.raises(ValueError, match="conflict_key"):
        conflict("https-case")
    with pytest.raises(ValueError, match="conflict_key"):
        conflict("token-case")

    buffer_report = report((conflict("case-safe"),))
    payload = research_source_real_time_conflict_buffer_report_payload(buffer_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert _unsafe_payload_matches(payload) == ()
    assert "candidate" not in encoded.lower()
    assert "market" not in encoded.lower()
    assert "question" not in encoded.lower()
    assert "source_url" not in encoded.lower()
    assert "source_text" not in encoded.lower()


def test_custom_config_validation_flags_and_frozen_dataclasses() -> None:
    with pytest.raises(ValueError, match="weights"):
        config(extraction_weight=d("0.200000"))
    with pytest.raises(ValueError, match="fresh_update_age_seconds"):
        config(fresh_update_age_seconds=d("300.000000"), stale_update_age_seconds=d("299.000000"))
    with pytest.raises(ValueError, match="blocked_buffer_risk_score"):
        config(watch_buffer_risk_score=d("0.700000"), blocked_buffer_risk_score=d("0.700000"))
    with pytest.raises(ValueError, match="fresh_update_age_seconds"):
        config(fresh_update_age_seconds=300)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="extraction_confidence"):
        conflict("case-subclass", extraction_confidence=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="authority_tier"):
        conflict("case-tier", authority_tier="rumor")
    with pytest.raises(ValueError, match="contradicting_family_count"):
        conflict(
            "case-counts",
            corroborating_family_count=d("1.000000"),
            contradicting_family_count=d("1.500000"),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(conflict("case-flags"), readonly=False)

    buffer_report = report((conflict("case-frozen"),))
    with pytest.raises(FrozenInstanceError):
        buffer_report.report_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        buffer_report.rows[0].buffer_risk_score = d("1.000000")  # type: ignore[misc]


def test_owned_module_has_no_io_trading_sizing_or_sensitive_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_real_time_conflict_buffer_report.py"
    )
    lower_source = module_path.read_text(encoding="utf-8").lower()
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
        "insert ",
        "update ",
        "delete ",
        "commit(",
        "execute(",
        "source_url",
        "source_text",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )

    assert all(term not in lower_source for term in forbidden_terms)


def _sha256_without_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _unsafe_payload_matches(value: object) -> tuple[str, ...]:
    unsafe_terms = (
        "candidate",
        "raw",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    matches: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            matches.extend(_unsafe_string_matches(str(key), unsafe_terms))
            matches.extend(_unsafe_payload_matches(item))
    elif isinstance(value, list):
        for item in value:
            matches.extend(_unsafe_payload_matches(item))
    elif isinstance(value, str):
        matches.extend(_unsafe_string_matches(value, unsafe_terms))
    return tuple(matches)


def _unsafe_string_matches(value: str, unsafe_terms: tuple[str, ...]) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value.lower():
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(token for token in tokens if token in unsafe_terms)
