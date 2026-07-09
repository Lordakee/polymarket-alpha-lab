from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
DECISION_DUE_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
CONFIG_VERSION = "research-strategy-domain-decision-evidence-decay-report-v0"


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_domain_decision_evidence_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    api = module()
    values = {
        "config_version": CONFIG_VERSION,
        "max_evidence_age_seconds": d("7200.000000"),
        "watch_decay_ratio_threshold": d("0.500000"),
        "block_decay_ratio_threshold": d("0.900000"),
        "contradiction_block_threshold": d("0.800000"),
        "min_source_reliability": d("0.500000"),
    }
    values.update(overrides)
    return api.ResearchStrategyDomainDecisionEvidenceDecayConfig(**values)


def evidence(
    domain_key: str = "policy_event",
    *,
    evidence_family: str = "statistical",
    evidence_observed_at: datetime = OBSERVED_AT,
    decision_due_at: datetime = DECISION_DUE_AT,
    evidence_confidence: Decimal = d("0.800000"),
    source_reliability: Decimal = d("0.900000"),
    contradiction_pressure: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    api = module()
    return api.ResearchStrategyDomainDecisionEvidenceDecayInput(
        domain_key=domain_key,
        evidence_family=evidence_family,
        evidence_observed_at=evidence_observed_at,
        decision_due_at=decision_due_at,
        evidence_confidence=evidence_confidence,
        source_reliability=source_reliability,
        contradiction_pressure=contradiction_pressure,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    api = module()
    return api.build_research_strategy_domain_decision_evidence_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_scores_domain_evidence_decay_without_raw_candidate_surfaces() -> None:
    api = module()
    report = build_report(
        evidence(
            "policy_event",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=30),
            decision_due_at=GENERATED_AT + timedelta(hours=2),
            evidence_confidence=d("0.800000"),
            source_reliability=d("0.900000"),
            contradiction_pressure=d("0.100000"),
        ),
        evidence(
            "volume_dislocation",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=90),
            decision_due_at=GENERATED_AT + timedelta(hours=1),
            evidence_confidence=d("0.700000"),
            source_reliability=d("0.800000"),
            contradiction_pressure=d("0.100000"),
        ),
        evidence(
            "event_path",
            evidence_observed_at=GENERATED_AT - timedelta(hours=3),
            decision_due_at=GENERATED_AT + timedelta(minutes=30),
            evidence_confidence=d("0.600000"),
            source_reliability=d("0.700000"),
            contradiction_pressure=d("0.100000"),
        ),
    )

    assert type(report) is api.ResearchStrategyDomainDecisionEvidenceDecayReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.source_domain_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_decay_ratio == d("1.000000")
    assert report.min_effective_confidence == d("0.000000")
    assert report.max_evidence_age_seconds == d("10800.000000")
    assert report.min_decision_horizon_seconds == d("1800.000000")
    assert report.status == "block"
    assert report.reason_codes == ("evidence_decay_block_present",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.domain_key for row in report.rows) == (
        "event_path",
        "volume_dislocation",
        "policy_event",
    )
    block_row, watch_row, pass_row = report.rows
    assert block_row.status == "block"
    assert block_row.evidence_age_seconds == d("10800.000000")
    assert block_row.decay_ratio == d("1.000000")
    assert block_row.freshness_score == d("0.000000")
    assert block_row.effective_confidence == d("0.000000")
    assert block_row.reason_codes == ("evidence_decay_block",)
    assert watch_row.status == "watch"
    assert watch_row.decay_ratio == d("0.750000")
    assert watch_row.effective_confidence == d("0.126000")
    assert watch_row.reason_codes == ("evidence_decay_watch",)
    assert pass_row.status == "pass"
    assert pass_row.decay_ratio == d("0.250000")
    assert pass_row.effective_confidence == d("0.486000")
    assert pass_row.reason_codes == ("domain_evidence_fresh",)

    payload = api.research_strategy_domain_decision_evidence_decay_report_payload(report)
    assert payload["source_domain_count"] == "3"
    assert payload["rows"][0]["domain_key"] == "event_path"
    assert payload["rows"][0]["decay_ratio"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)

    public_json = json.dumps(payload, sort_keys=True)
    for raw_surface in (
        "candidate-alpha",
        "market-alpha",
        "condition-id",
        "raw-question",
        "https://",
        "postgres://",
        "wallet",
        "order",
        "trade",
    ):
        assert raw_surface not in public_json


def test_empty_report_is_pass_report_only_and_json_ready() -> None:
    api = module()
    report = build_report()

    assert report.source_domain_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.max_decay_ratio == d("0.000000")
    assert report.min_effective_confidence == d("0.000000")
    assert report.max_evidence_age_seconds == d("0.000000")
    assert report.min_decision_horizon_seconds == d("0.000000")
    assert report.status == "pass"
    assert report.reason_codes == ("no_domain_evidence_supplied",)
    assert report.rows == ()
    assert report.derived_validation_digest

    payload = api.research_strategy_domain_decision_evidence_decay_report_payload(report)
    assert payload["status"] == "pass"
    assert payload["rows"] == []
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert not _contains_float(payload)


def test_digest_payload_rejects_tampering_flags_and_unsafe_surfaces() -> None:
    api = module()
    report = build_report(evidence())
    payload = api.research_strategy_domain_decision_evidence_decay_report_payload(report)

    tampered_count = dict(payload)
    tampered_count["source_domain_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(tampered_count)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "not-a-sha256-digest"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(tampered_digest)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(downgraded)

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "auth_token",
        "wallet_address",
        "order_id",
        "trade_size",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            api.research_strategy_domain_decision_evidence_decay_report_payload(
                {**payload, unsafe_key: "redacted"},
            )

    unsafe_row = dict(payload["rows"][0])
    unsafe_row["domain_key"] = "candidate-alpha"
    with pytest.raises(ValueError, match="unsafe"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(
            {**payload, "rows": [unsafe_row]},
        )


def test_resigned_payload_rejects_inconsistent_and_noncanonical_values() -> None:
    api = module()
    report = build_report(evidence())
    payload = api.research_strategy_domain_decision_evidence_decay_report_payload(report)

    inconsistent_count = dict(payload)
    inconsistent_count["source_domain_count"] = "2"
    _resign_payload(api, inconsistent_count)
    with pytest.raises(ValueError, match="source_domain_count"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(
            inconsistent_count,
        )

    noncanonical_ratio = dict(payload)
    noncanonical_ratio["max_decay_ratio"] = "0.2500000"
    _resign_payload(api, noncanonical_ratio)
    with pytest.raises(ValueError, match="max_decay_ratio"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(
            noncanonical_ratio,
        )

    inconsistent_row = dict(payload["rows"][0])
    inconsistent_row["effective_confidence"] = "0.999999"
    inconsistent_row_payload = {**payload, "rows": [inconsistent_row]}
    _resign_payload(api, inconsistent_row_payload)
    with pytest.raises(ValueError, match="effective_confidence"):
        api.research_strategy_domain_decision_evidence_decay_report_payload(
            inconsistent_row_payload,
        )


def test_dataclasses_are_frozen_decimal_only_strict_utc_and_flag_guarded() -> None:
    api = module()
    report = build_report(evidence())

    assert is_dataclass(api.ResearchStrategyDomainDecisionEvidenceDecayConfig)
    assert is_dataclass(api.ResearchStrategyDomainDecisionEvidenceDecayInput)
    assert is_dataclass(api.ResearchStrategyDomainDecisionEvidenceDecayRow)
    assert is_dataclass(api.ResearchStrategyDomainDecisionEvidenceDecayReport)
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].decay_ratio = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        evidence(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        config(max_evidence_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="evidence_confidence"):
        evidence(evidence_confidence=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_confidence"):
        evidence(evidence_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="timezone-aware"):
        evidence(evidence_observed_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        evidence(
            evidence_observed_at=datetime(
                2026,
                7,
                9,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(evidence(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="decision_due_at"):
        build_report(
            evidence(decision_due_at=GENERATED_AT - timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="block_decay_ratio_threshold"):
        config(block_decay_ratio_threshold=d("0.400000"))


def test_row_reason_codes_are_consistent_and_custom_thresholds_are_supported() -> None:
    api = module()
    report = build_report(evidence())

    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], reason_codes=("evidence_decay_watch",))

    with pytest.raises(ValueError, match="duplicate"):
        replace(
            report,
            source_domain_count=d("2"),
            pass_count=d("2"),
            rows=(report.rows[0], report.rows[0]),
            derived_validation_digest="",
        )

    custom_report = build_report(
        evidence(evidence_observed_at=GENERATED_AT - timedelta(minutes=30)),
        cfg=config(
            watch_decay_ratio_threshold=d("0.200000"),
            block_decay_ratio_threshold=d("0.800000"),
        ),
    )

    assert custom_report.status == "watch"
    assert custom_report.reason_codes == ("evidence_decay_watch_present",)
    assert custom_report.rows[0].status == "watch"
    assert custom_report.rows[0].reason_codes == ("evidence_decay_watch",)


def test_module_scope_is_pure_report_only_without_sensitive_surfaces() -> None:
    api = module()
    source = inspect.getsource(api)
    tree = ast.parse(source)
    report = build_report(evidence())

    assert set(api.DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES) == {
        "pass",
        "watch",
        "block",
    }
    assert {
        "candidate",
        "market",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "execution",
        "sizing",
        "recommend",
    }.issubset(set(api.UNSAFE_PUBLIC_SURFACE_FRAGMENTS))

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                called_names.add(call_name.rsplit(".", maxsplit=1)[-1])

    assert imported_modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
    assert {
        "connect",
        "execute",
        "executemany",
        "open",
        "print",
        "read_text",
        "request",
        "send",
        "write_text",
    }.isdisjoint(called_names)

    field_names = {field.name for field in fields(report)}
    field_names.update(field.name for field in fields(report.rows[0]))
    assert {
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet_address",
        "order_id",
        "trade_size",
        "recommendation",
    }.isdisjoint(field_names)

    for field_name in (
        "source_domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_decay_ratio",
        "min_effective_confidence",
        "max_evidence_age_seconds",
        "min_decision_horizon_seconds",
    ):
        assert type(getattr(report, field_name)) is Decimal
    for field_name in (
        "evidence_age_seconds",
        "decision_horizon_seconds",
        "evidence_confidence",
        "source_reliability",
        "contradiction_pressure",
        "freshness_score",
        "decay_ratio",
        "effective_confidence",
    ):
        assert type(getattr(report.rows[0], field_name)) is Decimal


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_float(item) for item in value)
    return False


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _resign_payload(api: Any, payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = api._payload_derived_validation_digest(payload)
