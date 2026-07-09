from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_domain_memory_drift_watch_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_memory_drift_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-memory-drift-watch-report-v0",
        "max_pass_stale_memory_reuse_ratio": d("0.050000"),
        "max_watch_stale_memory_reuse_ratio": d("0.150000"),
        "max_pass_calibration_drift_score": d("0.050000"),
        "max_watch_calibration_drift_score": d("0.120000"),
        "min_pass_correction_follow_through_ratio": d("0.900000"),
        "min_watch_correction_follow_through_ratio": d("0.700000"),
        "min_pass_evidence_reuse_quality_score": d("0.850000"),
        "min_watch_evidence_reuse_quality_score": d("0.650000"),
        "min_pass_peer_review_depth_score": d("0.800000"),
        "min_watch_peer_review_depth_score": d("0.600000"),
        "max_pass_review_latency_seconds": d("86400.000000"),
        "max_watch_review_latency_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryDriftWatchConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "domain_category": "politics",
        "team_key": "policy_team",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "stale_memory_reuse_ratio": d("0.010000"),
        "calibration_drift_score": d("0.020000"),
        "correction_follow_through_ratio": d("0.950000"),
        "evidence_reuse_quality_score": d("0.920000"),
        "peer_review_depth_score": d("0.900000"),
        "review_latency_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryDriftWatchObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_memory_drift_watch_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk(nested))
    return (value,)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "url",
        "text",
        "dsn",
        "table_name",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            assert item is True
            continue
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_public_api_declares_report_only_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_DRIFT_WATCH_REPORT_CONFIG_VERSION == (
        "research-team-domain-memory-drift-watch-report-v0"
    )
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")
    assert module.PUBLIC_DOMAIN_CATEGORIES == (
        "politics",
        "crypto",
        "equities",
        "commodities",
        "football",
        "basketball",
        "other",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_DRIFT_WATCH_REPORT_CONFIG_VERSION",
        "PUBLIC_DOMAIN_CATEGORIES",
        "PUBLIC_STATUSES",
        "ResearchTeamDomainMemoryDriftWatchConfig",
        "ResearchTeamDomainMemoryDriftWatchObservation",
        "ResearchTeamDomainMemoryDriftWatchRow",
        "ResearchTeamDomainMemoryDriftWatchReasonCodeCount",
        "ResearchTeamDomainMemoryDriftWatchReport",
        "build_research_team_domain_memory_drift_watch_report",
        "research_team_domain_memory_drift_watch_report_payload",
        "research_team_domain_memory_drift_watch_report_digest",
    )

    defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamDomainMemoryDriftWatchConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True


def test_builds_pass_watch_and_block_domain_memory_drift_rows() -> None:
    report = build_report(
        signal(domain_category="politics", team_key="policy_team"),
        signal(
            domain_category="crypto",
            team_key="chain_team",
            observed_at=GENERATED_AT - timedelta(hours=1),
            stale_memory_reuse_ratio=d("0.100000"),
            calibration_drift_score=d("0.080000"),
            correction_follow_through_ratio=d("0.800000"),
            evidence_reuse_quality_score=d("0.750000"),
            peer_review_depth_score=d("0.700000"),
            review_latency_seconds=d("172800.000000"),
        ),
        signal(
            domain_category="equities",
            team_key="index_team",
            observed_at=GENERATED_AT - timedelta(hours=2),
            stale_memory_reuse_ratio=d("0.200000"),
            calibration_drift_score=d("0.150000"),
            correction_follow_through_ratio=d("0.500000"),
            evidence_reuse_quality_score=d("0.500000"),
            peer_review_depth_score=d("0.500000"),
            review_latency_seconds=d("345600.000000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-domain-memory-drift-watch-report-v0"
    assert report.status == "block"
    assert report.domain_team_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.drift_team_count == d("2.000000")
    assert report.stale_memory_reuse_team_count == d("2.000000")
    assert report.calibration_drift_team_count == d("2.000000")
    assert report.correction_gap_team_count == d("2.000000")
    assert report.evidence_reuse_gap_team_count == d("2.000000")
    assert report.peer_review_gap_team_count == d("2.000000")
    assert report.review_latency_gap_team_count == d("2.000000")
    assert report.average_stale_memory_reuse_ratio == d("0.103333")
    assert report.average_calibration_drift_score == d("0.083333")
    assert report.average_correction_follow_through_ratio == d("0.750000")
    assert report.average_evidence_reuse_quality_score == d("0.723333")
    assert report.average_peer_review_depth_score == d("0.700000")
    assert report.max_review_latency_seconds == d("345600.000000")

    blocked, watched, passed = report.rows
    assert tuple((row.status, row.domain_category) for row in report.rows) == (
        ("block", "equities"),
        ("watch", "crypto"),
        ("pass", "politics"),
    )
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.reason_codes == (
        "domain_memory_drift_stale_memory_reuse_block",
        "domain_memory_drift_calibration_drift_block",
        "domain_memory_drift_correction_follow_through_block",
        "domain_memory_drift_evidence_reuse_quality_block",
        "domain_memory_drift_peer_review_depth_block",
        "domain_memory_drift_review_latency_block",
    )
    assert watched.reason_codes == (
        "domain_memory_drift_stale_memory_reuse_watch",
        "domain_memory_drift_calibration_drift_watch",
        "domain_memory_drift_correction_follow_through_watch",
        "domain_memory_drift_evidence_reuse_quality_watch",
        "domain_memory_drift_peer_review_depth_watch",
        "domain_memory_drift_review_latency_watch",
    )
    assert passed.reason_codes == ("domain_memory_drift_clear",)
    assert blocked.validation_digest.startswith("sha256:")
    assert report.validation_digest.startswith("sha256:")


def test_empty_report_blocks_without_live_or_private_surfaces() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.domain_team_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("domain_memory_drift_report_no_inputs",)
    assert report.reason_code_counts == (
        module.ResearchTeamDomainMemoryDriftWatchReasonCodeCount(
            reason_code="domain_memory_drift_report_no_inputs",
            count=d("1.000000"),
            team_ratio=d("1.000000"),
        ),
    )


def test_payload_is_deterministic_decimal_stringed_public_safe_and_digest_checked() -> None:
    module = api()
    left = signal(domain_category="politics", team_key="policy_team")
    right = signal(
        domain_category="crypto",
        team_key="chain_team",
        observed_at=datetime(2026, 7, 8, 4, 0, tzinfo=timezone(timedelta(hours=-7))),
        stale_memory_reuse_ratio=d("0.100000"),
        calibration_drift_score=d("0.080000"),
        correction_follow_through_ratio=d("0.800000"),
        evidence_reuse_quality_score=d("0.750000"),
        peer_review_depth_score=d("0.700000"),
        review_latency_seconds=d("172800.000000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_team_domain_memory_drift_watch_report_payload(report_a)
    digest = module.research_team_domain_memory_drift_watch_report_digest(report_a)

    assert payload == module.research_team_domain_memory_drift_watch_report_payload(
        report_b,
    )
    assert report_a.validation_digest == report_b.validation_digest
    assert payload["domain_team_count"] == "2.000000"
    assert payload["average_stale_memory_reuse_ratio"] == "0.055000"
    assert payload["rows"][0]["observation_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["team_digest"].startswith("sha256:")
    assert payload["validation_digest"] == report_a.validation_digest
    assert digest == module.research_team_domain_memory_drift_watch_report_digest(payload)
    assert digest["validation_digest"] == payload["validation_digest"]
    assert not any(type(value) is int for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))
    assert not any(isinstance(value, Decimal) for value in walk(payload))
    assert_public_payload_has_no_forbidden_surface(payload)
    public_json = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert "policy_team" not in public_json
    assert "chain_team" not in public_json

    tampered_status = dict(payload)
    tampered_status["status"] = "review"
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.research_team_domain_memory_drift_watch_report_payload(tampered_status)

    tampered_digest = dict(payload)
    tampered_digest["validation_digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(ValueError, match="validation_digest must match report contents"):
        module.research_team_domain_memory_drift_watch_report_payload(tampered_digest)

    unsafe = dict(payload)
    unsafe["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_domain_memory_drift_watch_report_payload(unsafe)


def test_payload_rejects_recomputed_digests_for_noncanonical_content() -> None:
    module = api()
    payload = module.research_team_domain_memory_drift_watch_report_payload(
        build_report(signal()),
    )

    def resigned_payload(
        *,
        report_updates: dict[str, object] | None = None,
        row_updates: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        candidate = json.loads(json.dumps(payload))
        if row_updates:
            candidate["rows"][0].update(row_updates)
        if report_updates:
            candidate.update(report_updates)
        candidate["rows"][0]["validation_digest"] = (
            module._validation_digest_for_payload(candidate["rows"][0])
        )
        candidate["validation_digest"] = module._validation_digest_for_payload(candidate)
        return candidate

    with pytest.raises(ValueError, match="row paper_only must be True"):
        module.research_team_domain_memory_drift_watch_report_payload(
            resigned_payload(row_updates={"paper_only": False}),
        )

    with pytest.raises(ValueError, match="pass_count must match rows"):
        module.research_team_domain_memory_drift_watch_report_payload(
            resigned_payload(report_updates={"pass_count": "999.000000"}),
        )

    with pytest.raises(ValueError, match="report payload fields must match schema"):
        module.research_team_domain_memory_drift_watch_report_payload(
            resigned_payload(report_updates={"source_label": "internal memo"}),
        )


def test_validates_decimals_statuses_flags_and_frozen_dataclasses() -> None:
    module = api()
    cfg = config()
    item = signal()
    report = build_report(item)

    for value in (cfg, item, report.rows[0], report.reason_code_counts[0], report):
        assert_decimal_public_fields(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="stale_memory_reuse_ratio must be exactly Decimal"):
        signal(stale_memory_reuse_ratio=0.1)
    with pytest.raises(ValueError, match="review_latency_seconds must be exactly Decimal"):
        signal(review_latency_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="review")
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamDomainMemoryDriftWatchConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="unsafe public payload"):
        signal(team_key="market_team")


def test_module_stays_report_only_without_storage_network_or_live_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "web3",
        "websocket",
    )
    forbidden_call_fragments = (
        "connect",
        "delete",
        "execute",
        "insert",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    )
    forbidden_attribute_fragments = (
        "private_key",
        "place_order",
        "submit_order",
        "wallet",
    )

    assert float_constants == []
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        fragment in call.lower()
        for call in call_names
        for fragment in forbidden_call_fragments
    )
    assert not any(
        fragment in attribute.lower()
        for attribute in attribute_names
        for fragment in forbidden_attribute_fragments
    )
