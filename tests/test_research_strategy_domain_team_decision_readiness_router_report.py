from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_domain_team_decision_readiness_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _join(*parts: str) -> str:
    return "".join(parts)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def config(**overrides: object):
    module = api()
    return module.ResearchStrategyDomainTeamDecisionReadinessRouterConfig(**overrides)


def packet(
    seed: str,
    *,
    domain_label: str = "politics",
    team_label: str = "politics-primary",
    observed_at: datetime = datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
    domain_alignment_score: Decimal = d("0.900000"),
    evidence_completeness_score: Decimal = d("0.900000"),
    available_review_capacity_ratio: Decimal = d("0.900000"),
    open_dependency_count: Decimal = d("0.000000"),
    decision_age_seconds: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyDomainTeamDecisionReadinessRouterInput(
        packet_digest=digest(seed),
        domain_label=domain_label,
        team_label=team_label,
        observed_at=observed_at,
        domain_alignment_score=domain_alignment_score,
        evidence_completeness_score=evidence_completeness_score,
        available_review_capacity_ratio=available_review_capacity_ratio,
        open_dependency_count=open_dependency_count,
        decision_age_seconds=decision_age_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*packets, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_domain_team_decision_readiness_router_report(
        packets,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_router_report_prioritizes_packets_and_digest_payload() -> None:
    rows = (
        packet("pass", domain_label="sports-soccer", team_label="soccer-primary"),
        packet(
            "block",
            observed_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
            domain_alignment_score=d("0.400000"),
            evidence_completeness_score=d("0.400000"),
            available_review_capacity_ratio=d("0.200000"),
            open_dependency_count=d("3.000000"),
            decision_age_seconds=d("259200.000000"),
        ),
        packet(
            "watch",
            domain_label="crypto-btc",
            team_label="crypto-primary",
            observed_at=datetime(2026, 7, 7, 11, 0, tzinfo=UTC),
            domain_alignment_score=d("0.600000"),
            evidence_completeness_score=d("0.800000"),
            available_review_capacity_ratio=d("0.400000"),
            open_dependency_count=d("1.000000"),
            decision_age_seconds=d("90000.000000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert report.status == "block"
    assert tuple(row.packet_digest for row in report.rows) == (
        digest("block"),
        digest("watch"),
        digest("pass"),
    )
    assert tuple(row.router_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert report.packet_count == d("3")
    assert report.block_packet_count == d("1")
    assert report.watch_packet_count == d("1")
    assert report.pass_packet_count == d("1")
    assert report.average_readiness_score == d("0.433333")
    assert report.lowest_readiness_score == d("0.000000")
    assert report.max_routing_pressure_score == d("1.000000")
    assert report.max_decision_age_seconds == d("259200.000000")
    assert report.max_open_dependency_count == d("3.000000")

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.readiness_score == d("0.000000")
    assert blocked.routing_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "strategy_domain_team_decision_readiness_domain_alignment_block",
        "strategy_domain_team_decision_readiness_evidence_completeness_block",
        "strategy_domain_team_decision_readiness_review_capacity_block",
        "strategy_domain_team_decision_readiness_dependency_block",
        "strategy_domain_team_decision_readiness_age_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.readiness_score == d("0.400000")
    assert watched.routing_pressure_score == d("0.600000")
    assert watched.reason_codes == (
        "strategy_domain_team_decision_readiness_domain_alignment_watch",
        "strategy_domain_team_decision_readiness_review_capacity_watch",
        "strategy_domain_team_decision_readiness_dependency_watch",
        "strategy_domain_team_decision_readiness_age_watch",
    )
    assert report.rows[2].status == "pass"
    assert report.rows[2].reason_codes == (
        "strategy_domain_team_decision_readiness_clear",
    )

    payload = api().research_strategy_domain_team_decision_readiness_router_report_payload(
        report,
    )
    reversed_payload = (
        api().research_strategy_domain_team_decision_readiness_router_report_payload(
            reversed_report,
        )
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["packet_digest"] == digest("block")
    assert payload["rows"][0]["routing_pressure_score"] == "1.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    encoded_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-alpha",
        "market-123",
        "will team win",
        "https://example.test/source",
        "postgres://user:pass@host/db",
    ):
        assert forbidden not in encoded_payload


def test_report_only_shape_digest_validation_and_public_scope() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_DECISION_READINESS_ROUTER_CONFIG_VERSION",
        "STATUSES",
        "ResearchStrategyDomainTeamDecisionReadinessRouterConfig",
        "ResearchStrategyDomainTeamDecisionReadinessRouterInput",
        "ResearchStrategyDomainTeamDecisionReadinessRouterReport",
        "ResearchStrategyDomainTeamDecisionReadinessRouterRow",
        "build_research_strategy_domain_team_decision_readiness_router_report",
        "research_strategy_domain_team_decision_readiness_router_report_digest",
        "research_strategy_domain_team_decision_readiness_router_report_payload",
        "validate_research_strategy_domain_team_decision_readiness_router_report_digest",
        "validate_research_strategy_domain_team_decision_readiness_router_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(packet("public"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True
    assert module.validate_research_strategy_domain_team_decision_readiness_router_report_digest(
        report,
    )

    payload = (
        module.research_strategy_domain_team_decision_readiness_router_report_payload(
            report,
        )
    )
    assert module.validate_research_strategy_domain_team_decision_readiness_router_report_payload(
        payload,
    )
    assert (
        module.research_strategy_domain_team_decision_readiness_router_report_digest(
            report,
        )
        == payload["derived_validation_digest"]
    )

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="domain_alignment_score must be a Decimal"):
        packet("float", domain_alignment_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="packet_digest"):
        module.ResearchStrategyDomainTeamDecisionReadinessRouterInput(
            packet_digest="raw-candidate-alpha",
            domain_label="politics",
            team_label="politics-primary",
            observed_at=GENERATED_AT,
            domain_alignment_score=d("0.900000"),
            evidence_completeness_score=d("0.900000"),
            available_review_capacity_ratio=d("0.900000"),
            open_dependency_count=d("0.000000"),
            decision_age_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        packet("naive", observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            packet("zone"),
            generated_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="packet_digest values must be unique"):
        build_report(packet("dup"), packet("dup"))
    with pytest.raises(ValueError, match="paper_only"):
        packet("paper", paper_only=False)
    with pytest.raises(ValueError, match="dependency_count"):
        config(
            open_dependency_watch_count=d("3.000000"),
            open_dependency_block_count=d("1.000000"),
        )

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_domain_team_decision_readiness_router_report_payload(
            tampered,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_research_strategy_domain_team_decision_readiness_router_report_payload(
            flag_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_payload["rows"][0]["source_url"] = "https://example.test/source"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_strategy_domain_team_decision_readiness_router_report_payload(
            unsafe_payload,
        )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        _join("reco", "mmendation"),
        _join("siz", "ing"),
        _join("b", "uy"),
        _join("s", "ell"),
        _join("wal", "let"),
        _join("ord", "er"),
        _join("li", "ve"),
        _join("trad", "ing"),
        _join("data", "base"),
        _join("net", "work"),
        _join("auth"),
        _join("token"),
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


def test_empty_input_is_pass_report_only_payload() -> None:
    module = api()

    report = build_report()

    assert report.status == "pass"
    assert report.packet_count == d("0")
    assert report.pass_packet_count == d("0")
    assert report.watch_packet_count == d("0")
    assert report.block_packet_count == d("0")
    assert report.average_readiness_score == d("0.000000")
    assert report.lowest_readiness_score == d("0.000000")
    assert report.max_routing_pressure_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("strategy_domain_team_decision_readiness_empty",)

    payload = (
        module.research_strategy_domain_team_decision_readiness_router_report_payload(
            report,
        )
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload.__setitem__("unexpected_field", "unexpected-value"),
        lambda payload: payload.pop("status"),
        lambda payload: payload["rows"][0].__setitem__(
            "unexpected_field",
            "unexpected-value",
        ),
        lambda payload: payload["rows"][0].pop("readiness_score"),
        lambda payload: payload.__setitem__("packet_count", "1"),
        lambda payload: payload.__setitem__(
            "generated_at",
            "2026-07-08T12:00:00Z",
        ),
        lambda payload: payload.__setitem__("config_version", "unsupported-v1"),
    ),
    ids=(
        "unknown-report-field",
        "missing-report-field",
        "unknown-row-field",
        "missing-row-field",
        "noncanonical-decimal",
        "noncanonical-datetime",
        "unsupported-config-version",
    ),
)
def test_public_payload_validation_rejects_resigned_schema_drift(mutate) -> None:
    module = api()
    payload = module.research_strategy_domain_team_decision_readiness_router_report_payload(
        build_report(packet("strict-schema")),
    )
    mutate(payload)
    resign(payload)

    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_strategy_domain_team_decision_readiness_router_report_payload(
            payload,
        )

    with pytest.raises(ValueError, match="public payload"):
        module.research_strategy_domain_team_decision_readiness_router_report_payload(
            payload,
        )


def test_public_payload_validation_rejects_resigned_inconsistent_values() -> None:
    module = api()
    payload = module.research_strategy_domain_team_decision_readiness_router_report_payload(
        build_report(packet("strict-values")),
    )
    payload["status"] = "watch"
    resign(payload)

    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_strategy_domain_team_decision_readiness_router_report_payload(
            payload,
        )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
