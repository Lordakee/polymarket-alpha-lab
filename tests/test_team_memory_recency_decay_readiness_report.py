from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_PATH = "src/polymarket_alpha_lab/team_memory_recency_decay_readiness_report.py"


class _DecimalSubclass(Decimal):
    pass


class _FloatSubclass(float):
    pass


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_recency_decay_readiness_report",
    )


def _config(api: Any, **overrides: object) -> Any:
    values = {
        "allow_memory_age_days": Decimal("7"),
        "block_memory_age_days": Decimal("30"),
        "min_calibration_sample_count": Decimal("20"),
        "block_recent_error_rate": Decimal("0.250000"),
        "throttle_recent_error_rate": Decimal("0.100000"),
        "max_source_feedback_age_days": Decimal("14"),
    }
    values.update(overrides)
    return api.TeamMemoryRecencyDecayReadinessConfig(**values)


def _row(
    api: Any,
    team_id: str,
    category_id: str,
    *,
    memory_age_days: Decimal,
    calibration_sample_count: Decimal,
    recent_error_rate: Decimal,
    source_feedback_age_days: Decimal,
) -> Any:
    return api.TeamMemoryRecencyDecayReadinessInputRow(
        team_id=team_id,
        category_id=category_id,
        memory_age_days=memory_age_days,
        calibration_sample_count=calibration_sample_count,
        recent_error_rate=recent_error_rate,
        source_feedback_age_days=source_feedback_age_days,
    )


def test_builds_allow_throttle_block_report_with_reason_rollups() -> None:
    api = _api()

    report = api.build_team_memory_recency_decay_readiness_report(
        (
            _row(
                api,
                "politics",
                "politics",
                memory_age_days=Decimal("3"),
                calibration_sample_count=Decimal("40"),
                recent_error_rate=Decimal("0.050000"),
                source_feedback_age_days=Decimal("2"),
            ),
            _row(
                api,
                "crypto_btc",
                "finance.crypto.btc",
                memory_age_days=Decimal("12"),
                calibration_sample_count=Decimal("21"),
                recent_error_rate=Decimal("0.120000"),
                source_feedback_age_days=Decimal("16"),
            ),
            _row(
                api,
                "soccer",
                "sports.soccer",
                memory_age_days=Decimal("45"),
                calibration_sample_count=Decimal("8"),
                recent_error_rate=Decimal("0.310000"),
                source_feedback_age_days=Decimal("40"),
            ),
        ),
        config=_config(api),
    )

    assert type(report) is api.TeamMemoryRecencyDecayReadinessReport
    assert (
        report.config_version
        == api.DEFAULT_TEAM_MEMORY_RECENCY_DECAY_READINESS_CONFIG_VERSION
    )
    assert report.memory_recency_status == "block"
    assert report.team_count == Decimal("3.000000")
    assert report.allow_count == Decimal("1.000000")
    assert report.throttle_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.manual_follow_up_count == Decimal("2.000000")
    assert report.max_memory_age_days == Decimal("45.000000")
    assert report.max_recent_error_rate == Decimal("0.310000")
    assert report.max_source_feedback_age_days == Decimal("40.000000")
    assert report.reason_codes == (
        "team_memory_recency_decay_block_memory_stale",
        "team_memory_recency_decay_block_low_calibration_samples",
        "team_memory_recency_decay_block_error_rate",
        "team_memory_recency_decay_block_source_feedback_stale",
        "team_memory_recency_decay_throttle_memory_aging",
        "team_memory_recency_decay_throttle_error_rate",
        "team_memory_recency_decay_throttle_source_feedback_aging",
        "team_memory_recency_decay_allow_current",
    )
    assert report.reason_code_counts == (
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_block_memory_stale",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_block_low_calibration_samples",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_block_error_rate",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_block_source_feedback_stale",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_throttle_memory_aging",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_throttle_error_rate",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_throttle_source_feedback_aging",
            count=Decimal("1.000000"),
        ),
        api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
            reason_code="team_memory_recency_decay_allow_current",
            count=Decimal("1.000000"),
        ),
    )

    assert tuple(
        (row.memory_recency_status, row.category_id, row.team_id, row.manual_follow_up)
        for row in report.rows
    ) == (
        ("block", "sports.soccer", "soccer", True),
        ("throttle", "finance.crypto.btc", "crypto_btc", True),
        ("allow", "politics", "politics", False),
    )
    assert report.rows[0].reason_codes == (
        "team_memory_recency_decay_block_memory_stale",
        "team_memory_recency_decay_block_low_calibration_samples",
        "team_memory_recency_decay_block_error_rate",
        "team_memory_recency_decay_block_source_feedback_stale",
    )
    assert report.rows[1].reason_codes == (
        "team_memory_recency_decay_throttle_memory_aging",
        "team_memory_recency_decay_throttle_error_rate",
        "team_memory_recency_decay_throttle_source_feedback_aging",
    )
    assert report.rows[2].reason_codes == (
        "team_memory_recency_decay_allow_current",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_returns_blocked_readonly_decimal_zero_report() -> None:
    api = _api()

    report = api.build_team_memory_recency_decay_readiness_report(
        (),
        config=api.TeamMemoryRecencyDecayReadinessConfig(),
    )

    assert report == api.TeamMemoryRecencyDecayReadinessReport(
        config_version=api.DEFAULT_TEAM_MEMORY_RECENCY_DECAY_READINESS_CONFIG_VERSION,
        memory_recency_status="block",
        team_count=Decimal("0.000000"),
        allow_count=Decimal("0.000000"),
        throttle_count=Decimal("0.000000"),
        block_count=Decimal("0.000000"),
        manual_follow_up_count=Decimal("0.000000"),
        max_memory_age_days=Decimal("0.000000"),
        max_recent_error_rate=Decimal("0.000000"),
        max_source_feedback_age_days=Decimal("0.000000"),
        rows=(),
        reason_code_counts=(
            api.TeamMemoryRecencyDecayReadinessReasonCodeCount(
                reason_code="team_memory_recency_decay_no_observations",
                count=Decimal("1.000000"),
            ),
        ),
        reason_codes=("team_memory_recency_decay_no_observations",),
    )


def test_payload_is_json_ready_without_floats_or_unsafe_surfaces() -> None:
    api = _api()
    report = api.build_team_memory_recency_decay_readiness_report(
        (
            _row(
                api,
                "politics",
                "politics",
                memory_age_days=Decimal("3"),
                calibration_sample_count=Decimal("40"),
                recent_error_rate=Decimal("0.050000"),
                source_feedback_age_days=Decimal("2"),
            ),
        ),
        config=_config(api),
    )

    payload = api.team_memory_recency_decay_readiness_report_payload(report)

    assert payload["team_count"] == "1.000000"
    assert payload["rows"][0]["memory_age_days"] == "3.000000"
    assert payload["rows"][0]["manual_follow_up"] is False
    assert "action" not in json.dumps(payload, sort_keys=True).lower()
    assert "advice" not in json.dumps(payload, sort_keys=True).lower()

    def walk(value: object) -> None:
        if isinstance(value, float):
            raise AssertionError(f"float leaked into payload: {value!r}")
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    encoded = json.dumps(payload, sort_keys=True)
    assert json.loads(encoded) == payload


def test_validates_decimal_inputs_thresholds_and_hard_flags() -> None:
    api = _api()

    with pytest.raises(ValueError, match="memory_age_days must be a Decimal"):
        _row(
            api,
            "politics",
            "politics",
            memory_age_days=_DecimalSubclass("1"),
            calibration_sample_count=Decimal("40"),
            recent_error_rate=Decimal("0.050000"),
            source_feedback_age_days=Decimal("2"),
        )
    with pytest.raises(ValueError, match="recent_error_rate must be a Decimal"):
        _row(
            api,
            "politics",
            "politics",
            memory_age_days=Decimal("1"),
            calibration_sample_count=Decimal("40"),
            recent_error_rate=_FloatSubclass(0.1),
            source_feedback_age_days=Decimal("2"),
        )
    with pytest.raises(ValueError, match="recent_error_rate must not exceed one"):
        _row(
            api,
            "politics",
            "politics",
            memory_age_days=Decimal("1"),
            calibration_sample_count=Decimal("40"),
            recent_error_rate=Decimal("1.100000"),
            source_feedback_age_days=Decimal("2"),
        )
    with pytest.raises(ValueError, match="allow_memory_age_days must not exceed block"):
        _config(
            api,
            allow_memory_age_days=Decimal("31"),
            block_memory_age_days=Decimal("30"),
        )
    with pytest.raises(ValueError, match="throttle_recent_error_rate must not exceed block"):
        _config(
            api,
            throttle_recent_error_rate=Decimal("0.300000"),
            block_recent_error_rate=Decimal("0.250000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(_config(api), paper_only=False)


def test_public_contract_is_frozen_decimal_only_and_in_memory() -> None:
    api = _api()
    report = api.build_team_memory_recency_decay_readiness_report(
        (
            _row(
                api,
                "politics",
                "politics",
                memory_age_days=Decimal("3"),
                calibration_sample_count=Decimal("40"),
                recent_error_rate=Decimal("0.050000"),
                source_feedback_age_days=Decimal("2"),
            ),
        ),
        config=_config(api),
    )

    public_types = {
        "TeamMemoryRecencyDecayReadinessConfig",
        "TeamMemoryRecencyDecayReadinessInputRow",
        "TeamMemoryRecencyDecayReadinessRow",
        "TeamMemoryRecencyDecayReadinessReasonCodeCount",
        "TeamMemoryRecencyDecayReadinessReport",
    }
    for name in public_types:
        cls = getattr(api, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.memory_recency_status = "allow"  # type: ignore[misc]

    for field_name in (
        "team_count",
        "allow_count",
        "throttle_count",
        "block_count",
        "manual_follow_up_count",
        "max_memory_age_days",
        "max_recent_error_rate",
        "max_source_feedback_age_days",
    ):
        assert type(getattr(report, field_name)) is Decimal

    for row in report.rows:
        for field_name in (
            "memory_age_days",
            "calibration_sample_count",
            "recent_error_rate",
            "source_feedback_age_days",
        ):
            assert type(getattr(row, field_name)) is Decimal

    tree = ast.parse(open(MODULE_PATH, encoding="utf-8").read())
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not (imports & forbidden_import_roots)

    text = open(MODULE_PATH, encoding="utf-8").read().lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "trade",
        "broker",
        "credential",
        "secret",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "upsert",
        "execute",
        "commit",
        "cursor",
    ):
        assert forbidden not in text
