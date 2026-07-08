from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_evidence_contradiction_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "unresolved_age_watch_seconds": d("3600.000000"),
        "unresolved_age_block_seconds": d("7200.000000"),
        "source_class_quorum_watch_floor": d("0.750000"),
        "source_class_quorum_block_floor": d("0.500000"),
        "corroboration_age_watch_seconds": d("1800.000000"),
        "corroboration_age_block_seconds": d("4800.000000"),
        "parse_reliability_watch_floor": d("0.800000"),
        "parse_reliability_block_floor": d("0.600000"),
        "retry_backlog_watch_count": d("2.000000"),
        "retry_backlog_block_count": d("6.000000"),
        "manual_escalation_urgency_watch_score": d("0.500000"),
        "manual_escalation_urgency_block_score": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchSourceEvidenceContradictionSlaConfig(**values)


def input_row(
    contradiction_key: str,
    source_class: str,
    *,
    unresolved_contradiction_age_seconds: Decimal = d("900.000000"),
    required_source_class_count: Decimal = d("3.000000"),
    observed_source_class_count: Decimal = d("3.000000"),
    last_corroborated_age_seconds: Decimal = d("600.000000"),
    parse_reliability_score: Decimal = d("0.950000"),
    retry_backlog_count: Decimal = d("0.000000"),
    manual_escalation_urgency_score: Decimal = d("0.100000"),
) -> Any:
    module = api()
    return module.ResearchSourceEvidenceContradictionSlaInput(
        contradiction_key=contradiction_key,
        source_class=source_class,
        unresolved_contradiction_age_seconds=unresolved_contradiction_age_seconds,
        required_source_class_count=required_source_class_count,
        observed_source_class_count=observed_source_class_count,
        last_corroborated_age_seconds=last_corroborated_age_seconds,
        parse_reliability_score=parse_reliability_score,
        retry_backlog_count=retry_backlog_count,
        manual_escalation_urgency_score=manual_escalation_urgency_score,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_evidence_contradiction_sla_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_contradiction_sla_report_builds_empty_pass_readonly_report() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceEvidenceContradictionSlaReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.contradiction_count == d("0.000000")
    assert report.sla_rows == ()
    assert report.reason_codes == (
        "research_source_evidence_contradiction_sla_no_unresolved_contradictions",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_contradiction_sla_report_aggregates_and_ranks_sla_pressure() -> None:
    report = build_report(
        input_row(
            "bucket-stable",
            "official-primary",
        ),
        input_row(
            "bucket-block",
            "official-primary",
            unresolved_contradiction_age_seconds=d("9000.000000"),
            required_source_class_count=d("3.000000"),
            observed_source_class_count=d("1.000000"),
            last_corroborated_age_seconds=d("5000.000000"),
            parse_reliability_score=d("0.550000"),
            retry_backlog_count=d("8.000000"),
            manual_escalation_urgency_score=d("0.900000"),
        ),
        input_row(
            "bucket-watch-b",
            "secondary-class",
            unresolved_contradiction_age_seconds=d("3600.000000"),
            required_source_class_count=d("4.000000"),
            observed_source_class_count=d("3.000000"),
            last_corroborated_age_seconds=d("1800.000000"),
            parse_reliability_score=d("0.750000"),
            retry_backlog_count=d("2.000000"),
            manual_escalation_urgency_score=d("0.500000"),
        ),
        input_row(
            "bucket-watch-a",
            "secondary-class",
            unresolved_contradiction_age_seconds=d("3600.000000"),
            required_source_class_count=d("4.000000"),
            observed_source_class_count=d("3.000000"),
            last_corroborated_age_seconds=d("1800.000000"),
            parse_reliability_score=d("0.750000"),
            retry_backlog_count=d("2.000000"),
            manual_escalation_urgency_score=d("0.500000"),
        ),
    )

    assert tuple(row.status for row in report.sla_rows) == (
        "block",
        "watch",
        "watch",
        "pass",
    )
    assert tuple(row.contradiction_key for row in report.sla_rows) == (
        "bucket-block",
        "bucket-watch-a",
        "bucket-watch-b",
        "bucket-stable",
    )

    blocked = report.sla_rows[0]
    assert blocked.source_class_quorum_ratio == d("0.333333")
    assert blocked.sla_pressure_score == d("0.835833")
    assert blocked.reason_codes == (
        "research_source_evidence_contradiction_sla_unresolved_age_breach",
        "research_source_evidence_contradiction_sla_source_class_quorum_gap",
        "research_source_evidence_contradiction_sla_corroboration_stale",
        "research_source_evidence_contradiction_sla_parse_reliability_low",
        "research_source_evidence_contradiction_sla_retry_backlog_high",
        "research_source_evidence_contradiction_sla_manual_escalation_urgent",
    )

    assert report.status == "block"
    assert report.contradiction_count == d("4.000000")
    assert report.block_contradiction_count == d("1.000000")
    assert report.watch_contradiction_count == d("2.000000")
    assert report.max_unresolved_contradiction_age_seconds == d("9000.000000")
    assert report.min_source_class_quorum_ratio == d("0.333333")
    assert report.max_corroboration_age_seconds == d("5000.000000")
    assert report.min_parse_reliability_score == d("0.550000")
    assert report.max_retry_backlog_count == d("8.000000")
    assert report.max_manual_escalation_urgency_score == d("0.900000")
    assert report.reason_codes == blocked.reason_codes


def test_contradiction_sla_report_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(input_row("bucket-pass", "official-primary"))
    watch_report = build_report(
        input_row(
            "bucket-watch",
            "official-primary",
            unresolved_contradiction_age_seconds=d("3600.000000"),
        ),
    )
    block_report = build_report(
        input_row(
            "bucket-block",
            "official-primary",
            parse_reliability_score=d("0.500000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert pass_report.status == "pass"
    assert pass_report.sla_rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.sla_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.sla_rows[0].status == "block"


def test_contradiction_sla_report_rejects_non_decimal_numeric_inputs() -> None:
    module = api()
    with pytest.raises(ValueError, match="unresolved_age_watch_seconds must be a Decimal"):
        config(unresolved_age_watch_seconds=3600)
    with pytest.raises(ValueError, match="parse_reliability_watch_floor must be a Decimal"):
        config(parse_reliability_watch_floor=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="retry_backlog_count must be a Decimal"):
        input_row(
            "bucket-a",
            "official-primary",
            retry_backlog_count=2,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="manual_escalation_urgency_score must be a Decimal"):
        input_row(
            "bucket-a",
            "official-primary",
            manual_escalation_urgency_score=0.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_evidence_contradiction_sla_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )


def test_contradiction_sla_payload_is_public_safe_deterministic_and_digest_verified() -> None:
    module = api()
    rows = (
        input_row(
            "bucket-block",
            "official-primary",
            unresolved_contradiction_age_seconds=d("9000.000000"),
            required_source_class_count=d("3.000000"),
            observed_source_class_count=d("1.000000"),
            last_corroborated_age_seconds=d("5000.000000"),
            parse_reliability_score=d("0.550000"),
            retry_backlog_count=d("8.000000"),
            manual_escalation_urgency_score=d("0.900000"),
        ),
        input_row("bucket-pass", "secondary-class"),
    )

    payload = module.research_source_evidence_contradiction_sla_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_source_evidence_contradiction_sla_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["sla_rows"][0]["sla_pressure_score"] == "0.835833"
    assert json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        replace(build_report(*rows), status="pass")

    def assert_public_safe(value: object) -> None:
        forbidden_keys = (
            "url",
            "text",
            "market",
            "candidate",
            "dsn",
            "table",
            "token",
            "source_id",
            "raw",
        )
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(fragment in key.lower() for fragment in forbidden_keys)
                assert_public_safe(item)
        elif isinstance(value, list):
            for item in value:
                assert_public_safe(item)
        else:
            assert type(value) is not float
            assert type(value) is not int
            if isinstance(value, str):
                lowered = value.lower()
                assert not lowered.startswith(("http://", "https://"))
                assert "postgres://" not in lowered
                assert "postgresql://" not in lowered
                assert "token=" not in lowered

    assert_public_safe(payload)


def test_contradiction_sla_report_exports_frozen_public_dataclasses() -> None:
    module = api()
    report = build_report(input_row("bucket-a", "official-primary"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONTRADICTION_SLA_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceEvidenceContradictionSlaConfig",
        "ResearchSourceEvidenceContradictionSlaInput",
        "ResearchSourceEvidenceContradictionSlaReport",
        "ResearchSourceEvidenceContradictionSlaRow",
        "build_research_source_evidence_contradiction_sla_report",
        "research_source_evidence_contradiction_sla_report_payload",
    )
    assert is_dataclass(config())
    assert is_dataclass(input_row("bucket-a", "official-primary"))
    assert is_dataclass(report)
    assert is_dataclass(report.sla_rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.sla_rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().parse_reliability_watch_floor = d("0.500000")


def test_contradiction_sla_report_scope_is_pure_report_only_public_payload() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "source_url",
        "source_text",
        "raw_source",
        "market_id",
        "candidate_id",
        "dsn",
        "table_name",
        "private_token",
        "recommendation",
        "sizing",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "trade",
        "private_key",
        "credential",
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

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
