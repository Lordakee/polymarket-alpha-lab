from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_error_taxonomy_rollup_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    return module.ResearchTeamDomainErrorTaxonomyRollupConfig(**overrides)


def observation(
    domain_label: str,
    specialist_label: str,
    error_family_label: str,
    *,
    resolution_miss_count: Decimal = ZERO,
    source_blindspot_count: Decimal = ZERO,
    calibration_drift_score: Decimal = d("0.020000"),
    review_feedback_required_count: Decimal = d("1.000000"),
    review_feedback_absorbed_count: Decimal = d("1.000000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchTeamDomainErrorTaxonomyObservation(
        domain_label=domain_label,
        specialist_label=specialist_label,
        error_family_label=error_family_label,
        resolution_miss_count=resolution_miss_count,
        source_blindspot_count=source_blindspot_count,
        calibration_drift_score=calibration_drift_score,
        review_feedback_required_count=review_feedback_required_count,
        review_feedback_absorbed_count=review_feedback_absorbed_count,
        observed_at=observed_at,
    )


def build_report(
    *observations: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_domain_error_taxonomy_rollup_report(
        observations,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_rolls_up_domain_specialist_error_taxonomy_into_learning_signals() -> None:
    records = (
        observation("sports_rules", "settlement_team", "boundary_conditions"),
        observation(
            "macro_policy",
            "calendar_team",
            "resolution_rule_gap",
            resolution_miss_count=d("1.000000"),
            source_blindspot_count=d("1.000000"),
            calibration_drift_score=d("0.040000"),
            review_feedback_required_count=d("2.000000"),
            review_feedback_absorbed_count=d("2.000000"),
        ),
        observation(
            "macro_policy",
            "calendar_team",
            "resolution_rule_gap",
            resolution_miss_count=d("1.000000"),
            calibration_drift_score=d("0.080000"),
            review_feedback_required_count=d("2.000000"),
            review_feedback_absorbed_count=d("1.000000"),
        ),
        observation(
            "crypto_protocols",
            "oracle_team",
            "authority_gap",
            resolution_miss_count=d("4.000000"),
            source_blindspot_count=d("3.000000"),
            calibration_drift_score=d("0.200000"),
            review_feedback_required_count=d("5.000000"),
            review_feedback_absorbed_count=d("2.000000"),
        ),
    )

    report = build_report(*records)
    reversed_report = build_report(*reversed(records))

    assert api().RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.report_status == "block"
    assert report.source_observation_count == d("4.000000")
    assert report.taxonomy_row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_resolution_miss_count == d("6.000000")
    assert report.total_source_blindspot_count == d("4.000000")
    assert report.total_review_feedback_required_count == d("10.000000")
    assert report.total_review_feedback_absorbed_count == d("6.000000")
    assert report.overall_review_feedback_absorption_ratio == d("0.600000")
    assert report.max_calibration_drift_score == d("0.200000")
    assert report.max_learning_signal_score == d("1.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.rollup_rank for row in report.rows) == (d("1.000000"), d("2.000000"), d("3.000000"))
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.domain_label == "crypto_protocols"
    assert blocked.learning_signal_score == d("1.000000")
    assert blocked.review_feedback_absorption_ratio == d("0.400000")
    assert blocked.reason_codes == (
        "domain_error_taxonomy_resolution_miss_block",
        "domain_error_taxonomy_source_blindspot_block",
        "domain_error_taxonomy_calibration_drift_block",
        "domain_error_taxonomy_review_feedback_absorption_block",
    )
    assert watched.resolution_miss_count == d("2.000000")
    assert watched.source_blindspot_count == d("1.000000")
    assert watched.calibration_drift_score == d("0.080000")
    assert watched.review_feedback_required_count == d("4.000000")
    assert watched.review_feedback_absorbed_count == d("3.000000")
    assert watched.review_feedback_absorption_ratio == d("0.750000")
    assert watched.reason_codes == (
        "domain_error_taxonomy_resolution_miss_watch",
        "domain_error_taxonomy_source_blindspot_watch",
        "domain_error_taxonomy_calibration_drift_watch",
        "domain_error_taxonomy_review_feedback_absorption_watch",
    )
    assert passed.reason_codes == ("domain_error_taxonomy_learning_signal_clear",)
    assert (
        api().ResearchTeamDomainErrorTaxonomyReasonCodeCount(
            reason_code="domain_error_taxonomy_review_feedback_absorption_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = report.public_payload
    reversed_payload = reversed_report.public_payload

    assert payload == reversed_payload
    assert payload == api().research_team_domain_error_taxonomy_rollup_report_payload(report)
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_team_domain_error_taxonomy_rollup_report_digest(report) == payload["derived_validation_digest"]
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["learning_signal_score"] == "1.000000"
    assert _float_paths(payload) == ()


def test_drift_and_feedback_threshold_boundaries_drive_pass_watch_block() -> None:
    report = build_report(
        observation(
            "domain_a",
            "team_a",
            "drift_clear",
            calibration_drift_score=d("0.050000"),
            review_feedback_required_count=d("10.000000"),
            review_feedback_absorbed_count=d("9.000000"),
        ),
        observation(
            "domain_b",
            "team_b",
            "drift_watch",
            calibration_drift_score=d("0.120000"),
            review_feedback_required_count=d("10.000000"),
            review_feedback_absorbed_count=d("7.000000"),
        ),
        observation(
            "domain_c",
            "team_c",
            "drift_block",
            calibration_drift_score=d("0.120001"),
            review_feedback_required_count=d("10.000000"),
            review_feedback_absorbed_count=d("6.999990"),
        ),
    )

    rows_by_error = {row.error_family_label: row for row in report.rows}
    assert rows_by_error["drift_clear"].status == "pass"
    assert rows_by_error["drift_clear"].reason_codes == (
        "domain_error_taxonomy_learning_signal_clear",
    )
    assert rows_by_error["drift_watch"].status == "watch"
    assert rows_by_error["drift_watch"].reason_codes == (
        "domain_error_taxonomy_calibration_drift_watch",
        "domain_error_taxonomy_review_feedback_absorption_watch",
    )
    assert rows_by_error["drift_block"].status == "block"
    assert rows_by_error["drift_block"].reason_codes == (
        "domain_error_taxonomy_calibration_drift_block",
        "domain_error_taxonomy_review_feedback_absorption_block",
    )


def test_public_surface_is_frozen_decimal_only_and_leak_preventing() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_STATUSES",
        "ResearchTeamDomainErrorTaxonomyRollupConfig",
        "ResearchTeamDomainErrorTaxonomyObservation",
        "ResearchTeamDomainErrorTaxonomyReasonCodeCount",
        "ResearchTeamDomainErrorTaxonomyRollupReport",
        "ResearchTeamDomainErrorTaxonomyRollupRow",
        "build_research_team_domain_error_taxonomy_rollup_report",
        "research_team_domain_error_taxonomy_rollup_report_digest",
        "research_team_domain_error_taxonomy_rollup_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert getattr(value, "__dataclass_params__").frozen is True

    empty = build_report()
    assert empty.report_status == "pass"
    assert empty.reason_codes == ("domain_error_taxonomy_rollup_empty",)
    assert empty.rows == ()
    assert empty.reason_code_counts == ()
    assert empty.public_payload["paper_only"] is True
    assert empty.public_payload["report_only"] is True
    assert empty.public_payload["readonly"] is True

    populated = build_report(observation("sports_tennis", "rules_team", "injury_boundary"))
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        observation("macro_rates", "policy_team", "calendar_miss"),
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_rank")):
                assert type(field_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="resolution_miss_count must be a Decimal"):
        observation(
            "macro_rates",
            "policy_team",
            "calendar_miss",
            resolution_miss_count=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(
            "macro_rates",
            "policy_team",
            "calendar_miss",
            observed_at=datetime(2026, 7, 8, 10, 0),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        observation("macro_http_ref", "policy_team", "calendar_miss")
    with pytest.raises(ValueError, match="unsafe"):
        observation("macro_rates", "candidate_raw_ref", "calendar_miss")

    payload = populated.public_payload
    leaked_payload = json.loads(json.dumps(payload))
    leaked_payload["rows"][0]["market_slug"] = "private-market"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_domain_error_taxonomy_rollup_report_payload(leaked_payload)
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate-raw-123",
        "market-raw-123",
        "http://private.example",
        "postgresql://private",
        "orders_table",
        "private_token_value",
        "wallet",
        "trade",
        "recommendation",
    ):
        assert forbidden not in encoded

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
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


def test_custom_config_validation_and_digest_tamper_detection() -> None:
    module = api()
    cfg = config(
        max_pass_resolution_miss_count=d("1.000000"),
        max_watch_resolution_miss_count=d("3.000000"),
        max_pass_source_blindspot_count=d("1.000000"),
        max_watch_source_blindspot_count=d("3.000000"),
        max_pass_calibration_drift_score=d("0.100000"),
        max_watch_calibration_drift_score=d("0.200000"),
        min_pass_review_feedback_absorption_ratio=d("0.800000"),
        min_watch_review_feedback_absorption_ratio=d("0.600000"),
    )
    report = build_report(
        observation(
            "macro_rates",
            "policy_team",
            "calendar_miss",
            resolution_miss_count=d("1.000000"),
            source_blindspot_count=d("1.000000"),
            calibration_drift_score=d("0.100000"),
            review_feedback_required_count=d("5.000000"),
            review_feedback_absorbed_count=d("4.000000"),
        ),
        cfg=cfg,
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.report_status == "pass"
    assert report.generated_at == GENERATED_AT
    assert report.rows[0].status == "pass"

    payload = report.public_payload
    tampered_payload = json.loads(json.dumps(payload))
    tampered_payload["rows"][0]["resolution_miss_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_error_taxonomy_rollup_report_payload(
            tampered_payload,
        )
    with pytest.raises(ValueError, match="max_watch_resolution_miss_count"):
        config(
            max_pass_resolution_miss_count=d("5.000000"),
            max_watch_resolution_miss_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_review_feedback_absorption_ratio"):
        config(
            min_pass_review_feedback_absorption_ratio=d("0.500000"),
            min_watch_review_feedback_absorption_ratio=d("0.700000"),
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
