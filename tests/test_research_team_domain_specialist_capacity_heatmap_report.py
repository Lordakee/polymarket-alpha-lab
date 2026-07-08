from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_specialist_capacity_heatmap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 19, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_specialist_capacity_heatmap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-team-domain-specialist-capacity-heatmap-report-v0"
        ),
        "watch_active_review_load_ratio": d("0.750000"),
        "block_active_review_load_ratio": d("1.000000"),
        "watch_backlog_urgency_ratio": d("0.500000"),
        "block_backlog_urgency_ratio": d("0.800000"),
        "watch_calibration_age_seconds": d("604800.000000"),
        "block_calibration_age_seconds": d("1209600.000000"),
        "watch_evidence_gap_pressure": d("0.250000"),
        "block_evidence_gap_pressure": d("0.500000"),
        "watch_cross_domain_conflict_count": d("2.000000"),
        "block_cross_domain_conflict_count": d("4.000000"),
        "active_review_load_weight": d("0.250000"),
        "backlog_urgency_weight": d("0.200000"),
        "calibration_freshness_weight": d("0.200000"),
        "evidence_gap_pressure_weight": d("0.200000"),
        "cross_domain_conflict_weight": d("0.150000"),
        "watch_heatmap_score": d("0.500000"),
        "block_heatmap_score": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistCapacityHeatmapConfig(**values)


def signal(domain_label: str = "macro_policy", **overrides: object):
    module = api()
    values = {
        "team_label": "macro_team",
        "domain_label": domain_label,
        "specialist_label": f"{domain_label}_alpha",
        "active_review_count": d("2.000000"),
        "review_capacity_count": d("8.000000"),
        "urgent_backlog_count": d("1.000000"),
        "backlog_item_count": d("10.000000"),
        "latest_calibration_at": GENERATED_AT - timedelta(days=1),
        "required_evidence_count": d("10.000000"),
        "observed_evidence_count": d("10.000000"),
        "cross_domain_conflict_count": d("0.000000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistCapacityHeatmapSignal(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_specialist_capacity_heatmap_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return hashlib.sha256(encoded).hexdigest()


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload(item))
        return tuple(nested)
    return (value,)


def assert_decimal_fields_are_plain(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal, field.name


def assert_no_forbidden_public_surface(value: object) -> None:
    forbidden = (
        "raw",
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
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = key.lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_rolls_up_specialist_capacity_by_domain_into_heatmap_rows() -> None:
    report = build_report(
        signal(
            "macro_policy",
            team_label="macro_team_a",
            specialist_label="macro_policy_a",
            active_review_count=d("2.000000"),
            review_capacity_count=d("8.000000"),
            urgent_backlog_count=d("1.000000"),
            backlog_item_count=d("10.000000"),
            latest_calibration_at=GENERATED_AT - timedelta(days=1),
            required_evidence_count=d("10.000000"),
            observed_evidence_count=d("10.000000"),
        ),
        signal(
            "macro_policy",
            team_label="macro_team_b",
            specialist_label="macro_policy_b",
            active_review_count=d("1.000000"),
            review_capacity_count=d("7.000000"),
            urgent_backlog_count=d("0.000000"),
            backlog_item_count=d("5.000000"),
            latest_calibration_at=GENERATED_AT - timedelta(days=2),
            required_evidence_count=d("8.000000"),
            observed_evidence_count=d("8.000000"),
        ),
        signal(
            "sports_injury",
            team_label="sports_team",
            specialist_label="sports_injury_a",
            active_review_count=d("8.000000"),
            review_capacity_count=d("10.000000"),
            urgent_backlog_count=d("3.000000"),
            backlog_item_count=d("5.000000"),
            latest_calibration_at=GENERATED_AT - timedelta(seconds=700000),
            required_evidence_count=d("10.000000"),
            observed_evidence_count=d("7.000000"),
            cross_domain_conflict_count=d("2.000000"),
        ),
        signal(
            "crypto_protocols",
            team_label="crypto_team",
            specialist_label="crypto_protocols_a",
            active_review_count=d("13.000000"),
            review_capacity_count=d("10.000000"),
            urgent_backlog_count=d("8.000000"),
            backlog_item_count=d("10.000000"),
            latest_calibration_at=GENERATED_AT - timedelta(seconds=1500000),
            required_evidence_count=d("12.000000"),
            observed_evidence_count=d("4.000000"),
            cross_domain_conflict_count=d("5.000000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.heatmap_mode == "paper_capacity_heatmap_block"
    assert report.domain_count == d("3.000000")
    assert report.team_count == d("4.000000")
    assert report.specialist_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_capacity_score == d("0.585326")
    assert report.max_capacity_score == d("1.000000")
    assert report.average_active_review_load_ratio == d("0.766667")
    assert report.max_active_review_load_ratio == d("1.300000")
    assert report.average_backlog_urgency_ratio == d("0.488889")
    assert report.max_backlog_urgency_ratio == d("0.800000")
    assert report.max_calibration_age_seconds == d("1500000.000000")
    assert report.max_evidence_gap_pressure == d("0.666667")
    assert report.total_cross_domain_conflict_count == d("7.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.domain_label for row in report.rows) == (
        "crypto_protocols",
        "sports_injury",
        "macro_policy",
    )
    assert blocked.active_review_load_ratio == d("1.300000")
    assert blocked.backlog_urgency_ratio == d("0.800000")
    assert blocked.calibration_age_seconds == d("1500000.000000")
    assert blocked.evidence_gap_pressure == d("0.666667")
    assert blocked.capacity_score == d("1.000000")
    assert blocked.reason_codes == (
        "capacity_heatmap_active_review_load_block",
        "capacity_heatmap_backlog_urgency_block",
        "capacity_heatmap_calibration_freshness_block",
        "capacity_heatmap_evidence_gap_pressure_block",
        "capacity_heatmap_cross_domain_conflict_volume_block",
        "capacity_heatmap_score_block",
    )
    assert watched.capacity_score == d("0.660741")
    assert watched.reason_codes == (
        "capacity_heatmap_active_review_load_watch",
        "capacity_heatmap_backlog_urgency_watch",
        "capacity_heatmap_calibration_freshness_watch",
        "capacity_heatmap_evidence_gap_pressure_watch",
        "capacity_heatmap_cross_domain_conflict_volume_watch",
        "capacity_heatmap_score_watch",
    )
    assert passed.team_count == d("2.000000")
    assert passed.specialist_count == d("2.000000")
    assert passed.capacity_score == d("0.095238")
    assert passed.reason_codes == ("capacity_heatmap_domain_clear",)

    reason_counts = {item.reason_code: item for item in report.reason_code_counts}
    assert reason_counts["capacity_heatmap_active_review_load_block"].count == d(
        "1.000000",
    )
    assert reason_counts["capacity_heatmap_domain_clear"].domain_ratio == d("0.333333")


def test_mixed_watch_and_block_reason_codes_are_deterministically_ordered() -> None:
    report = build_report(
        signal(
            "mixed_capacity",
            active_review_count=d("8.000000"),
            review_capacity_count=d("10.000000"),
            urgent_backlog_count=d("8.000000"),
            backlog_item_count=d("10.000000"),
        ),
    )

    reason_codes = report.rows[0].reason_codes
    assert report.status == "block"
    assert "capacity_heatmap_backlog_urgency_block" in reason_codes
    assert "capacity_heatmap_active_review_load_watch" in reason_codes
    assert reason_codes.index(
        "capacity_heatmap_backlog_urgency_block",
    ) < reason_codes.index("capacity_heatmap_active_review_load_watch")


def test_public_payload_is_deterministic_tamper_evident_and_sanitized() -> None:
    module = api()
    items = (
        signal("macro_policy", team_label="macro_a", specialist_label="macro_a_one"),
        signal(
            "sports_injury",
            team_label="sports_a",
            specialist_label="sports_a_one",
            active_review_count=d("8.000000"),
            review_capacity_count=d("10.000000"),
            urgent_backlog_count=d("3.000000"),
            backlog_item_count=d("5.000000"),
            latest_calibration_at=GENERATED_AT - timedelta(seconds=700000),
            required_evidence_count=d("10.000000"),
            observed_evidence_count=d("7.000000"),
            cross_domain_conflict_count=d("2.000000"),
        ),
    )

    left = build_report(*items)
    right = build_report(*reversed(items))
    payload = module.research_team_domain_specialist_capacity_heatmap_report_payload(left)

    assert left.derived_validation_digest == right.derived_validation_digest
    assert payload == right.public_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_team_domain_specialist_capacity_heatmap_report_digest(left) == (
        payload["derived_validation_digest"]
    )
    assert payload["generated_at"] == "2026-07-08T20:00:00+00:00"
    assert payload["rows"][0]["domain_label"] == "sports_injury"
    assert "team_label" not in json.dumps(payload, sort_keys=True)
    assert "specialist_label" not in json.dumps(payload, sort_keys=True)
    assert all(type(item) is not Decimal for item in walk_payload(payload))
    assert all(type(item) not in (int, float) for item in walk_payload(payload))
    assert_no_forbidden_public_surface(payload)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_capacity_heatmap_report_payload(tampered)

    forged = dict(payload)
    forged["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_capacity_heatmap_report_payload(forged)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    input_signal = signal()
    report = build_report(input_signal, cfg=cfg)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_CAPACITY_HEATMAP_CONFIG_VERSION",
        "CAPACITY_HEATMAP_STATUSES",
        "ResearchTeamDomainSpecialistCapacityHeatmapConfig",
        "ResearchTeamDomainSpecialistCapacityHeatmapReasonCodeCount",
        "ResearchTeamDomainSpecialistCapacityHeatmapReport",
        "ResearchTeamDomainSpecialistCapacityHeatmapRow",
        "ResearchTeamDomainSpecialistCapacityHeatmapSignal",
        "build_research_team_domain_specialist_capacity_heatmap_report",
        "research_team_domain_specialist_capacity_heatmap_report_digest",
        "research_team_domain_specialist_capacity_heatmap_report_payload",
    )
    assert module.CAPACITY_HEATMAP_STATUSES == ("pass", "watch", "block")

    for item in (cfg, input_signal, report, *report.rows, *report.reason_code_counts):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_decimal_fields_are_plain(item)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclass"):
        type("BadSignal", (module.ResearchTeamDomainSpecialistCapacityHeatmapSignal,), {})
    with pytest.raises(ValueError, match="Decimal"):
        signal(active_review_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        signal(active_review_count=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="latest_calibration_at"):
        signal(latest_calibration_at=datetime(2026, 7, 8, 19, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(signal(), generated_at=_DatetimeSubclass(2026, 7, 8, 20, 0))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_rejects_leaky_inputs_payloads_duplicates_and_inconsistent_counts() -> None:
    module = api()

    for field_name, unsafe_value in (
        ("domain_label", "market_slug"),
        ("domain_label", "question_text"),
        ("team_label", "wallet_auth"),
        ("specialist_label", "source_url"),
    ):
        with pytest.raises(ValueError, match="public aggregate label"):
            signal(**{field_name: unsafe_value})

    with pytest.raises(ValueError, match="unique"):
        build_report(signal(), signal())
    with pytest.raises(ValueError, match="urgent_backlog_count"):
        signal(urgent_backlog_count=d("11.000000"))
    with pytest.raises(ValueError, match="observed_evidence_count"):
        signal(observed_evidence_count=d("11.000000"))
    with pytest.raises(ValueError, match="latest_calibration_at"):
        build_report(signal(latest_calibration_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observed_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    payload = build_report(signal()).public_payload
    for key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "auth_token",
        "wallet_address",
        "order_id",
        "trade_id",
        "live_url",
        "position_sizing",
        "recommendation_id",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_domain_specialist_capacity_heatmap_report_payload(unsafe)

    numeric = dict(payload)
    numeric["domain_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_specialist_capacity_heatmap_report_payload(numeric)


def test_custom_config_validation_and_thresholds() -> None:
    strict_cfg = config(
        watch_active_review_load_ratio=d("0.400000"),
        block_active_review_load_ratio=d("0.900000"),
        watch_backlog_urgency_ratio=d("0.200000"),
        block_backlog_urgency_ratio=d("0.700000"),
        watch_calibration_age_seconds=d("300000.000000"),
        block_calibration_age_seconds=d("900000.000000"),
        watch_evidence_gap_pressure=d("0.050000"),
        block_evidence_gap_pressure=d("0.400000"),
        watch_cross_domain_conflict_count=d("1.000000"),
        block_cross_domain_conflict_count=d("3.000000"),
    )
    report = build_report(
        signal(
            "policy_ops",
            active_review_count=d("5.000000"),
            review_capacity_count=d("10.000000"),
            urgent_backlog_count=d("2.000000"),
            backlog_item_count=d("10.000000"),
            latest_calibration_at=GENERATED_AT - timedelta(seconds=400000),
            required_evidence_count=d("10.000000"),
            observed_evidence_count=d("9.000000"),
            cross_domain_conflict_count=d("1.000000"),
        ),
        cfg=strict_cfg,
    )

    assert report.status == "watch"
    assert report.rows[0].reason_codes == (
        "capacity_heatmap_active_review_load_watch",
        "capacity_heatmap_backlog_urgency_watch",
        "capacity_heatmap_calibration_freshness_watch",
        "capacity_heatmap_evidence_gap_pressure_watch",
        "capacity_heatmap_cross_domain_conflict_volume_watch",
    )

    with pytest.raises(ValueError, match="watch_active_review_load_ratio"):
        config(
            watch_active_review_load_ratio=d("1.100000"),
            block_active_review_load_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="weights must sum"):
        config(active_review_load_weight=d("0.300000"))
    with pytest.raises(ValueError, match="watch_heatmap_score"):
        config(watch_heatmap_score=d("0.900000"), block_heatmap_score=d("0.800000"))


def test_module_has_no_external_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
        "py_clob_client",
    }
    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "send",
        "submit",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "insert",
        "upsert",
        "order",
        "trade",
        "buy",
        "sell",
        "write",
        "write_text",
        "write_bytes",
        "open",
        "float",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in banned_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in banned_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    exported_surface = "\n".join(api().__all__).lower()
    for forbidden in (
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
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in exported_surface
