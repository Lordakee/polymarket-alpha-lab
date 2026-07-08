from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_multichannel_evidence_consensus_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("86400.000000"),
        "agreement_watch_threshold": d("0.600000"),
        "agreement_pass_threshold": d("0.750000"),
        "contradiction_watch_threshold": d("0.250000"),
        "contradiction_block_threshold": d("0.500000"),
        "stale_family_watch_ratio": d("0.250000"),
        "stale_family_block_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceMultichannelEvidenceConsensusConfig(**values)


def evidence(
    evidence_family: str,
    stance: str,
    *,
    observed_at: datetime | None = None,
    evidence_count: Decimal = d("1.000000"),
) -> Any:
    module = api()
    return module.ResearchSourceMultichannelEvidenceConsensusInput(
        evidence_family=evidence_family,
        stance=stance,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        evidence_count=evidence_count,
    )


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_multichannel_evidence_consensus_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_input_blocks_with_hard_flags_and_digest() -> None:
    module = api()
    consensus_report = report()

    assert type(consensus_report) is module.ResearchSourceMultichannelEvidenceConsensusReport
    assert is_dataclass(consensus_report)
    assert consensus_report.generated_at == GENERATED_AT
    assert consensus_report.status == "block"
    assert consensus_report.evidence_family_count == d("0.000000")
    assert consensus_report.evidence_count == d("0.000000")
    assert consensus_report.family_rows == ()
    assert consensus_report.reason_codes == (
        "multichannel_evidence_consensus_no_evidence",
    )
    assert len(consensus_report.derived_validation_digest) == 64
    int(consensus_report.derived_validation_digest, 16)
    assert consensus_report.paper_only is True
    assert consensus_report.report_only is True
    assert consensus_report.readonly is True


def test_multichannel_evidence_consensus_aggregates_sanitized_families() -> None:
    consensus_report = report(
        evidence("official", "supports", evidence_count=d("2.000000")),
        evidence("web", "supports", observed_at=GENERATED_AT - timedelta(hours=2)),
        evidence("news", "supports", observed_at=GENERATED_AT - timedelta(hours=3)),
        evidence("social", "neutral", observed_at=GENERATED_AT - timedelta(minutes=10)),
    )

    assert consensus_report.status == "pass"
    assert consensus_report.consensus_stance == "supports"
    assert consensus_report.evidence_family_count == d("4.000000")
    assert consensus_report.evidence_count == d("5.000000")
    assert consensus_report.support_count == d("4.000000")
    assert consensus_report.neutral_count == d("1.000000")
    assert consensus_report.contradiction_count == d("0.000000")
    assert consensus_report.consensus_family_count == d("3.000000")
    assert consensus_report.family_agreement_score == d("0.750000")
    assert consensus_report.contradiction_pressure_score == d("0.000000")
    assert consensus_report.average_freshness_score == d("0.967391")
    assert consensus_report.stale_family_ratio == d("0.000000")
    assert consensus_report.reason_codes == (
        "multichannel_evidence_consensus_pass",
    )

    assert tuple(row.evidence_family for row in consensus_report.family_rows) == (
        "news",
        "official",
        "social",
        "web",
    )
    official = consensus_report.family_rows[1]
    assert official.evidence_family == "official"
    assert official.evidence_count == d("2.000000")
    assert official.family_stance == "supports"
    assert official.family_agreement_score == d("1.000000")
    assert official.latest_age_seconds == d("1800.000000")
    assert official.freshness_score == d("1.000000")
    assert official.contradiction_pressure_score == d("0.000000")
    assert official.status == "pass"


def test_watch_and_block_statuses_are_public_and_threshold_driven() -> None:
    module = api()
    watch_report = report(
        evidence("official", "supports"),
        evidence("web", "supports"),
        evidence("news", "supports"),
        evidence("social", "contradicts"),
    )
    block_report = report(
        evidence("official", "supports"),
        evidence("web", "contradicts"),
        evidence("news", "neutral"),
        evidence("social", "neutral"),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert watch_report.status == "watch"
    assert watch_report.contradiction_pressure_score == d("0.250000")
    assert watch_report.reason_codes == (
        "multichannel_evidence_consensus_contradiction_pressure_watch",
    )
    assert block_report.status == "block"
    assert block_report.family_agreement_score == d("0.500000")
    assert block_report.reason_codes == (
        "multichannel_evidence_consensus_low_family_agreement_block",
        "multichannel_evidence_consensus_contradiction_pressure_watch",
    )


def test_public_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    rows = (
        evidence("social", "neutral", observed_at=GENERATED_AT - timedelta(minutes=10)),
        evidence("official", "supports", evidence_count=d("2.000000")),
        evidence("web", "supports", observed_at=GENERATED_AT - timedelta(hours=2)),
        evidence("news", "supports", observed_at=GENERATED_AT - timedelta(hours=3)),
    )

    payload = module.research_source_multichannel_evidence_consensus_report_payload(
        report(*rows),
    )
    reversed_payload = module.research_source_multichannel_evidence_consensus_report_payload(
        report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_multichannel_evidence_consensus_report_payload(
        payload,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["family_rows"][0]["freshness_score"] == "0.913043"
    assert not any(type(value) in (float, int) for value in walk_payload_values(payload))

    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "https://",
        "http://",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in rendered

    tampered = dict(payload)
    tampered["status"] = "pass" if payload["status"] != "pass" else "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_multichannel_evidence_consensus_report_payload(
            tampered,
        )
    unsafe = dict(payload)
    unsafe["source_text"] = "raw copied text"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_source_multichannel_evidence_consensus_report_payload(unsafe)


def test_validation_rejects_bad_types_enums_future_times_and_flag_downgrades() -> None:
    module = api()
    with pytest.raises(ValueError, match="fresh_age_seconds must be a Decimal"):
        config(fresh_age_seconds=3600)
    with pytest.raises(ValueError, match="agreement_watch_threshold must be a Decimal"):
        config(agreement_watch_threshold=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="evidence_family"):
        evidence("blog", "supports")
    with pytest.raises(ValueError, match="stance"):
        evidence("official", "bullish")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence("official", "supports", observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        report(evidence("official", "supports", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="evidence_count must be a Decimal"):
        evidence("official", "supports", evidence_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence("official", "supports"), paper_only=False)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_multichannel_evidence_consensus_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    consensus_report = report(evidence("official", "supports"))

    with pytest.raises(FrozenInstanceError):
        consensus_report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        consensus_report.family_rows[0].status = "block"
    with pytest.raises(ValueError, match="evidence_count"):
        replace(consensus_report, evidence_count=d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(consensus_report, derived_validation_digest="0" * 64)


def test_module_scope_is_pure_report_only_without_execution_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_MULTICHANNEL_EVIDENCE_CONSENSUS_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceMultichannelEvidenceConsensusConfig",
        "ResearchSourceMultichannelEvidenceConsensusInput",
        "ResearchSourceMultichannelEvidenceConsensusFamilyRow",
        "ResearchSourceMultichannelEvidenceConsensusReport",
        "build_research_source_multichannel_evidence_consensus_report",
        "research_source_multichannel_evidence_consensus_report_payload",
        "validate_research_source_multichannel_evidence_consensus_report_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "wallet",
        "private_key",
        "credential",
        "recommendation",
        "sizing",
        "trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
