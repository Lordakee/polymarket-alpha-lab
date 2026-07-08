from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_claim_materiality_shift_report import (
    CLAIM_MATERIALITY_SHIFT_STATUSES,
    DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION,
    ResearchEventClaimMaterialityShiftConfig,
    ResearchEventClaimMaterialityShiftInput,
    ResearchEventClaimMaterialityShiftReasonCodeCount,
    ResearchEventClaimMaterialityShiftReport,
    ResearchEventClaimMaterialityShiftRow,
    build_research_event_claim_materiality_shift_report,
    research_event_claim_materiality_shift_report_digest,
    research_event_claim_materiality_shift_report_payload,
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


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def config(**overrides: object) -> ResearchEventClaimMaterialityShiftConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_EVENT_CLAIM_MATERIALITY_SHIFT_CONFIG_VERSION,
        "fresh_source_age_seconds": d("21600.000000"),
        "stale_source_age_seconds": d("172800.000000"),
        "min_pass_corroboration_count": d("2.000000"),
        "watch_materiality_score": d("0.400000"),
        "block_materiality_score": d("0.700000"),
        "watch_contradiction_pressure": d("0.300000"),
        "block_contradiction_pressure": d("0.650000"),
        "watch_manual_review_urgency": d("0.400000"),
        "block_manual_review_urgency": d("0.700000"),
    }
    values.update(overrides)
    return ResearchEventClaimMaterialityShiftConfig(**values)


def claim_shift(
    public_event_key: str = "event.alpha",
    *,
    event_family: str = "macro_policy",
    claim_cluster_label: str = "resolution_scope",
    changed_claim_count: Decimal = d("1.000000"),
    materiality_score: Decimal = d("0.100000"),
    source_age_seconds: Decimal = d("3600.000000"),
    corroboration_count: Decimal = d("3.000000"),
    contradiction_pressure: Decimal = d("0.050000"),
    manual_review_urgency: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventClaimMaterialityShiftInput:
    return ResearchEventClaimMaterialityShiftInput(
        public_event_key=public_event_key,
        event_family=event_family,
        claim_cluster_label=claim_cluster_label,
        changed_claim_count=changed_claim_count,
        materiality_score=materiality_score,
        source_age_seconds=source_age_seconds,
        corroboration_count=corroboration_count,
        contradiction_pressure=contradiction_pressure,
        manual_review_urgency=manual_review_urgency,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchEventClaimMaterialityShiftInput, ...],
    *,
    cfg: ResearchEventClaimMaterialityShiftConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventClaimMaterialityShiftReport:
    return build_research_event_claim_materiality_shift_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_claim_materiality_shift_report_aggregates_pass_watch_and_block() -> None:
    summary = report(
        (
            claim_shift("event.pass"),
            claim_shift(
                "event.watch",
                claim_cluster_label="outcome_language",
                changed_claim_count=d("2.000000"),
                materiality_score=d("0.450000"),
                source_age_seconds=d("90000.000000"),
                corroboration_count=d("1.000000"),
                contradiction_pressure=d("0.350000"),
                manual_review_urgency=d("0.450000"),
            ),
            claim_shift(
                "event.block",
                claim_cluster_label="resolution_boundary",
                changed_claim_count=d("3.000000"),
                materiality_score=d("0.800000"),
                source_age_seconds=d("200000.000000"),
                corroboration_count=d("0.000000"),
                contradiction_pressure=d("0.700000"),
                manual_review_urgency=d("0.900000"),
            ),
        ),
    )

    assert type(summary) is ResearchEventClaimMaterialityShiftReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert CLAIM_MATERIALITY_SHIFT_STATUSES == ("pass", "watch", "block")
    assert summary.status == "block"
    assert summary.public_next_step == "pause_report_only_materiality_review"
    assert summary.event_count == d("3.000000")
    assert summary.changed_claim_count == d("6.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_materiality_score == d("0.450000")
    assert summary.average_source_recency_score == d("0.515873")
    assert summary.total_corroboration_count == d("4.000000")
    assert summary.max_contradiction_pressure == d("0.700000")
    assert summary.max_manual_review_urgency == d("0.900000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.public_event_key for row in summary.rows) == (
        "event.block",
        "event.watch",
        "event.pass",
    )

    blocked = summary.rows[0]
    assert type(blocked) is ResearchEventClaimMaterialityShiftRow
    assert blocked.status == "block"
    assert blocked.source_recency_score == d("0.000000")
    assert blocked.corroboration_score == d("0.000000")
    assert blocked.reason_codes == (
        "materiality_shift_block",
        "source_recency_stale",
        "corroboration_missing",
        "contradiction_pressure_block",
        "manual_review_urgency_block",
    )

    watched = summary.rows[1]
    assert watched.status == "watch"
    assert watched.source_recency_score == d("0.547619")
    assert watched.corroboration_score == d("0.500000")
    assert watched.reason_codes == (
        "materiality_shift_watch",
        "source_recency_aging",
        "corroboration_thin",
        "contradiction_pressure_watch",
        "manual_review_urgency_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.source_recency_score == d("1.000000")
    assert passed.corroboration_score == d("1.000000")
    assert passed.reason_codes == (
        "materiality_shift_pass",
        "source_recency_current",
        "corroboration_sufficient",
        "contradiction_pressure_low",
        "manual_review_urgency_low",
    )

    assert summary.reason_code_counts[0] == ResearchEventClaimMaterialityShiftReasonCodeCount(
        reason_code="materiality_shift_block",
        count=d("1.000000"),
        event_ratio=d("0.333333"),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_claim_materiality_shift_empty_inputs_block_report_only() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.public_next_step == "pause_report_only_materiality_review"
    assert summary.event_count == d("0.000000")
    assert summary.changed_claim_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("materiality_shift_no_inputs",)
    assert summary.reason_code_counts == (
        ResearchEventClaimMaterialityShiftReasonCodeCount(
            reason_code="materiality_shift_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_claim_materiality_shift_payload_digest_is_public_and_deterministic() -> None:
    first = report(
        (
            claim_shift("event.zeta"),
            claim_shift(
                "event.alpha",
                materiality_score=d("0.450000"),
                source_age_seconds=d("90000.000000"),
                corroboration_count=d("1.000000"),
                contradiction_pressure=d("0.350000"),
                manual_review_urgency=d("0.450000"),
            ),
        ),
    )
    second = report(
        (
            claim_shift(
                "event.alpha",
                materiality_score=d("0.450000"),
                source_age_seconds=d("90000.000000"),
                corroboration_count=d("1.000000"),
                contradiction_pressure=d("0.350000"),
                manual_review_urgency=d("0.450000"),
            ),
            claim_shift("event.zeta"),
        ),
    )

    first_payload = research_event_claim_materiality_shift_report_payload(first)
    second_payload = research_event_claim_materiality_shift_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True, separators=(",", ":"))
    lower_encoded = encoded.lower()

    assert first_payload == second_payload
    assert first.payload == first_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["event_count"] == "2.000000"
    assert first_payload["rows"][0]["source_recency_score"] == "0.547619"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first.digest == research_event_claim_materiality_shift_report_digest(first)
    assert first.digest == first.derived_validation_digest
    assert sha256(
        json.dumps(
            {key: value for key, value in first_payload.items() if key != "derived_validation_digest"},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest() == first.digest
    assert research_event_claim_materiality_shift_report_payload(dict(first_payload)) == (
        first_payload
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert "raw_market" not in lower_encoded
    assert "raw_source" not in lower_encoded
    assert "market_id" not in lower_encoded
    assert "market_slug" not in lower_encoded
    assert "source_identifier" not in lower_encoded
    assert "source_url" not in lower_encoded
    assert "source_ref" not in lower_encoded
    assert "source_text" not in lower_encoded
    assert "wallet" not in lower_encoded
    assert "auth" not in lower_encoded
    assert "order" not in lower_encoded
    assert "trade" not in lower_encoded
    assert "position" not in lower_encoded
    assert "recommend" not in lower_encoded

    tampered = dict(first_payload)
    tampered["event_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_claim_materiality_shift_report_payload(tampered)


def test_claim_materiality_shift_validates_types_thresholds_strings_and_flags() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        claim_shift(changed_claim_count=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="exactly Decimal"):
        claim_shift(materiality_score=_DecimalSubclass("0.100000"))
    with pytest.raises(TypeError, match="exactly str"):
        claim_shift(_StringSubclass("event.alpha"))
    with pytest.raises(ValueError, match="whole count"):
        claim_shift(changed_claim_count=d("1.500000"))
    with pytest.raises(ValueError, match="ratio"):
        claim_shift(materiality_score=d("1.100000"))
    with pytest.raises(ValueError, match="timezone"):
        report((claim_shift(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(TypeError, match="exactly datetime"):
        report(
            (claim_shift(),),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="stale_source_age_seconds"):
        config(stale_source_age_seconds=d("21600.000000"))
    with pytest.raises(ValueError, match="block_materiality_score"):
        config(block_materiality_score=d("0.400000"))
    with pytest.raises(ValueError, match="unsafe public"):
        claim_shift(public_event_key="market_id-123")
    with pytest.raises(ValueError, match="unsafe public"):
        claim_shift(public_event_key="source_url-private")
    with pytest.raises(ValueError, match="unsafe public"):
        claim_shift(public_event_key="wallet-secret")
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        claim_shift(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        claim_shift(readonly=False)

    summary = report((claim_shift(),))
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(summary, status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)


@pytest.mark.parametrize(
    "unsafe_public_value",
    (
        "candidate_id-123",
        "raw_candidate-123",
        "https://example.invalid/source",
        "http://example.invalid/source",
        "api_key-alpha",
        "private_key-alpha",
        "live_trading",
        "sizing-alpha",
    ),
)
def test_claim_materiality_shift_rejects_forbidden_public_surface_values(
    unsafe_public_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        claim_shift(public_event_key=unsafe_public_value)


def test_claim_materiality_shift_module_is_readonly_and_frozen() -> None:
    summary = report((claim_shift(),))

    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].materiality_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="changed_claim_count"):
        replace(summary, changed_claim_count=d("99.000000"))

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_claim_materiality_shift_report.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "builtins",
        "io",
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

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    assert imported_roots.isdisjoint(forbidden_import_roots)
    public = repr(asdict(summary)).lower() + repr(summary.payload).lower()
    for token in (
        "market_id",
        "market_slug",
        "raw_market",
        "raw_source",
        "source_identifier",
        "source_url",
        "source_ref",
        "source_text",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert token not in public


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for element in value.values() for item in _walk_payload_values(element))
    if isinstance(value, list):
        return tuple(item for element in value for item in _walk_payload_values(element))
    return (value,)
