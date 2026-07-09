from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_playbook_revision_impact_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "calibration_delta_block_floor": d("-0.050000"),
        "calibration_delta_watch_floor": d("0.000000"),
        "evidence_reuse_delta_block_floor": d("-0.100000"),
        "evidence_reuse_delta_watch_floor": d("0.000000"),
        "review_latency_watch_increase_seconds": d("900.000000"),
        "review_latency_block_increase_seconds": d("3600.000000"),
        "blocker_pressure_watch_ratio": d("0.250000"),
        "blocker_pressure_block_ratio": d("0.500000"),
        "pass_impact_pressure_ceiling": d("0.150000"),
        "watch_impact_pressure_ceiling": d("0.500000"),
        "calibration_delta_weight": d("0.300000"),
        "evidence_reuse_weight": d("0.250000"),
        "review_latency_weight": d("0.200000"),
        "unresolved_blocker_weight": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainPlaybookRevisionImpactConfig(**values)


def revision_signal(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "revision_ref": "revision-alpha",
        "team_label": "research-team-alpha",
        "domain_label": "macro-calendar",
        "observed_at": OBSERVED_AT,
        "pre_calibration_score": d("0.700000"),
        "post_calibration_score": d("0.760000"),
        "pre_evidence_reuse_ratio": d("0.500000"),
        "post_evidence_reuse_ratio": d("0.650000"),
        "pre_review_latency_seconds": d("7200.000000"),
        "post_review_latency_seconds": d("5400.000000"),
        "unresolved_blocker_count": d("0"),
        "total_blocker_count": d("4"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainPlaybookRevisionImpactInput(**values)


def build_report(
    *signals: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_domain_playbook_revision_impact_report(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_revision_impact_scores_positive_negative_deltas_latency_and_blocker_pressure() -> None:
    module = api()

    report = build_report(
        revision_signal(
            revision_ref="revision-pass",
            team_label="rates-team",
            domain_label="central-bank",
        ),
        revision_signal(
            revision_ref="revision-watch",
            team_label="elections-team",
            domain_label="turnout-model",
            post_calibration_score=d("0.690000"),
            post_evidence_reuse_ratio=d("0.470000"),
            post_review_latency_seconds=d("8400.000000"),
            unresolved_blocker_count=d("1"),
            total_blocker_count=d("4"),
        ),
        revision_signal(
            revision_ref="revision-block",
            team_label="macro-team",
            domain_label="labor-data",
            post_calibration_score=d("0.620000"),
            post_evidence_reuse_ratio=d("0.350000"),
            post_review_latency_seconds=d("12000.000000"),
            unresolved_blocker_count=d("3"),
            total_blocker_count=d("4"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION
    )
    assert module.RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.revision_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.positive_calibration_delta_count == d("1")
    assert report.negative_calibration_delta_count == d("2")
    assert report.positive_evidence_reuse_delta_count == d("1")
    assert report.negative_evidence_reuse_delta_count == d("2")
    assert report.review_latency_improved_count == d("1")
    assert report.review_latency_regressed_count == d("2")
    assert report.unresolved_blocker_pressure_count == d("2")
    assert report.average_calibration_delta == d("-0.010000")
    assert report.average_evidence_reuse_delta == d("-0.010000")
    assert report.average_review_latency_change_seconds == d("1400.000000")
    assert report.average_unresolved_blocker_pressure == d("0.333333")
    assert report.max_impact_pressure_score == d("1.000000")
    assert report.average_impact_pressure_score == d("0.442222")
    assert report.status == "block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.reason_codes == (
        "domain_playbook_revision_impact_block",
        "domain_playbook_revision_impact_watch",
        "calibration_delta_block",
        "evidence_reuse_delta_block",
        "review_latency_regression_block",
        "unresolved_blocker_pressure_block",
        "calibration_delta_watch",
        "evidence_reuse_delta_watch",
        "review_latency_regression_watch",
        "unresolved_blocker_pressure_watch",
    )

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.revision_ref_digest == "sha256:" + sha256(b"revision-block").hexdigest()
    assert blocked.calibration_delta == d("-0.080000")
    assert blocked.evidence_reuse_delta == d("-0.150000")
    assert blocked.review_latency_change_seconds == d("4800.000000")
    assert blocked.unresolved_blocker_pressure == d("0.750000")
    assert blocked.impact_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "calibration_delta_block",
        "evidence_reuse_delta_block",
        "review_latency_regression_block",
        "unresolved_blocker_pressure_block",
    )
    assert watched.impact_pressure_score == d("0.326667")
    assert watched.reason_codes == (
        "calibration_delta_watch",
        "evidence_reuse_delta_watch",
        "review_latency_regression_watch",
        "unresolved_blocker_pressure_watch",
    )
    assert passed.calibration_delta == d("0.060000")
    assert passed.evidence_reuse_delta == d("0.150000")
    assert passed.review_latency_change_seconds == d("-1800.000000")
    assert passed.impact_pressure_score == d("0.000000")
    assert passed.reason_codes == ("domain_playbook_revision_impact_clear",)
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert_decimal_only_numerics(report)


def test_public_payload_is_deterministic_redacted_json_safe_and_digest_checked() -> None:
    module = api()
    watch = revision_signal(
        revision_ref="revision-watch",
        team_label="elections-team",
        domain_label="turnout-model",
        observed_at=datetime(2026, 7, 8, 4, 45, tzinfo=timezone(timedelta(hours=-7))),
        post_calibration_score=d("0.690000"),
        post_evidence_reuse_ratio=d("0.470000"),
        post_review_latency_seconds=d("8400.000000"),
        unresolved_blocker_count=d("1"),
        total_blocker_count=d("4"),
    )
    passing = revision_signal(
        revision_ref="revision-pass",
        team_label="rates-team",
        domain_label="central-bank",
    )

    report_a = build_report(
        watch,
        passing,
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    report_b = build_report(passing, watch)
    payload_a = module.research_team_domain_playbook_revision_impact_report_payload(
        report_a,
    )
    payload_b = module.research_team_domain_playbook_revision_impact_report_payload(
        report_b,
    )

    assert payload_a == report_a.public_payload
    assert payload_a == payload_b
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["revision_count"] == "2"
    assert payload_a["rows"][0]["revision_ref_digest"] == (
        "sha256:" + sha256(b"revision-watch").hexdigest()
    )
    assert payload_a["rows"][0]["observed_at"] == "2026-07-08T11:45:00+00:00"
    assert payload_a["rows"][0]["impact_pressure_score"] == "0.326667"
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert_no_int_or_float_values(payload_a)
    json.dumps(payload_a, sort_keys=True)

    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )
    payload_text = repr(payload_a).lower()
    assert "revision-watch" not in payload_text
    assert "revision-pass" not in payload_text
    assert not any(fragment in payload_text for fragment in forbidden_fragments)
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload_a)
        for fragment in forbidden_fragments
    )

    tampered = dict(payload_a)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_playbook_revision_impact_report_payload(tampered)

    row_tampered = dict(payload_a)
    row_tampered["rows"] = [dict(row) for row in payload_a["rows"]]
    row_tampered["rows"][0]["impact_pressure_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_playbook_revision_impact_report_payload(row_tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, pass_count=d("2"))


def test_public_payload_requires_exact_report_and_row_schemas() -> None:
    module = api()
    payload = module.research_team_domain_playbook_revision_impact_report_payload(
        build_report(revision_signal()),
    )

    extra_report_field = dict(payload)
    extra_report_field["summary_label"] = "plain"
    extra_report_field = recompute_payload_digests(extra_report_field)

    missing_report_field = dict(payload)
    del missing_report_field["status"]
    missing_report_field = recompute_payload_digests(missing_report_field)

    extra_row_field = dict(payload)
    extra_row_field["rows"] = [dict(row) for row in payload["rows"]]
    extra_row_field["rows"][0]["public_note"] = "plain"
    extra_row_field = recompute_payload_digests(extra_row_field)

    missing_row_field = dict(payload)
    missing_row_field["rows"] = [dict(row) for row in payload["rows"]]
    del missing_row_field["rows"][0]["status"]
    missing_row_field = recompute_payload_digests(missing_row_field)

    for invalid_payload in (
        extra_report_field,
        missing_report_field,
        extra_row_field,
        missing_row_field,
    ):
        with pytest.raises(ValueError, match="schema"):
            module.research_team_domain_playbook_revision_impact_report_payload(
                invalid_payload,
            )


def test_empty_report_passes_with_hard_flags_and_no_rows() -> None:
    module = api()

    report = build_report()

    assert report.status == "pass"
    assert report.revision_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.max_impact_pressure_score == d("0.000000")
    assert report.average_impact_pressure_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("domain_playbook_revision_impact_empty",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_custom_config_validation_and_status_thresholds() -> None:
    module = api()

    permissive = config(
        pass_impact_pressure_ceiling=d("0.400000"),
        watch_impact_pressure_ceiling=d("0.800000"),
    )
    watched_signal = revision_signal(
        post_calibration_score=d("0.690000"),
        post_evidence_reuse_ratio=d("0.470000"),
        post_review_latency_seconds=d("8400.000000"),
        unresolved_blocker_count=d("1"),
        total_blocker_count=d("4"),
    )
    report = build_report(watched_signal, cfg=permissive)

    assert report.status == "pass"
    assert report.pass_count == d("1")
    assert report.rows[0].status == "pass"
    assert report.rows[0].impact_pressure_score == d("0.326667")

    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(unresolved_blocker_weight=d("0.240000"))
    with pytest.raises(ValueError, match="must be less than watch floor"):
        config(calibration_delta_block_floor=d("0.000000"))
    with pytest.raises(ValueError, match="must exceed watch increase"):
        config(review_latency_block_increase_seconds=d("900.000000"))
    with pytest.raises(ValueError, match="must exceed watch ratio"):
        config(blocker_pressure_block_ratio=d("0.250000"))
    with pytest.raises(ValueError, match="must not exceed watch ceiling"):
        config(pass_impact_pressure_ceiling=d("0.600000"))
    with pytest.raises(ValueError, match="Decimal"):
        config(calibration_delta_weight=_DecimalSubclass("0.300000"))


def test_rejects_unsafe_public_surfaces_non_decimal_numbers_and_flag_downgrades() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_STATUSES",
        "RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REASON_CODES",
        "ResearchTeamDomainPlaybookRevisionImpactConfig",
        "ResearchTeamDomainPlaybookRevisionImpactInput",
        "ResearchTeamDomainPlaybookRevisionImpactReport",
        "ResearchTeamDomainPlaybookRevisionImpactRow",
        "build_research_team_domain_playbook_revision_impact_report",
        "research_team_domain_playbook_revision_impact_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        item = revision_signal()
        item.revision_ref = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        revision_signal(pre_calibration_score=0.7)
    with pytest.raises(ValueError, match="Decimal"):
        revision_signal(pre_calibration_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="safe public"):
        revision_signal(revision_ref="candidate-alpha")
    with pytest.raises(ValueError, match="safe public"):
        revision_signal(domain_label="market-slug-alpha")
    with pytest.raises(ValueError, match="observed_at"):
        revision_signal(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="must not exceed total_blocker_count"):
        revision_signal(unresolved_blocker_count=d("5"), total_blocker_count=d("4"))
    with pytest.raises(ValueError, match="must be positive"):
        revision_signal(total_blocker_count=d("0"))
    with pytest.raises(ValueError, match="must be on or before generated_at"):
        build_report(revision_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    payload = module.research_team_domain_playbook_revision_impact_report_payload(
        build_report(revision_signal()),
    )
    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_domain_playbook_revision_impact_report_payload(unsafe)

    unsafe_number = dict(payload)
    unsafe_number["revision_count"] = 1
    with pytest.raises(ValueError, match="string values"):
        module.research_team_domain_playbook_revision_impact_report_payload(unsafe_number)


def test_module_scope_has_no_external_or_decision_action_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_team_domain_playbook_revision_impact_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def assert_decimal_only_numerics(value: Any) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected non-Decimal numeric value: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_int_or_float_values(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if type(value) is dict:
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if type(value) is list:
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def recompute_payload_digests(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    for row in normalized.get("rows", []):
        row["derived_validation_digest"] = canonical_payload_digest(row)
    normalized["derived_validation_digest"] = canonical_payload_digest(normalized)
    return normalized


def canonical_payload_digest(payload: dict[str, Any]) -> str:
    def without_digests(value: Any) -> Any:
        if type(value) is dict:
            return {
                key: without_digests(item)
                for key, item in value.items()
                if key != "derived_validation_digest"
            }
        if type(value) is list:
            return [without_digests(item) for item in value]
        return value

    encoded = json.dumps(
        without_digests(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
