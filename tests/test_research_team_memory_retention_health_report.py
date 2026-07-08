from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

import pytest

from polymarket_alpha_lab.research_team_memory_retention_health_report import (
    DEFAULT_RESEARCH_TEAM_MEMORY_RETENTION_HEALTH_REPORT_CONFIG_VERSION,
    ResearchTeamMemoryRetentionHealthConfig,
    ResearchTeamMemoryRetentionHealthReasonCodeCount,
    ResearchTeamMemoryRetentionHealthReport,
    ResearchTeamMemoryRetentionHealthRow,
    ResearchTeamMemoryRetentionHealthSnapshot,
    build_research_team_memory_retention_health_report,
    research_team_memory_retention_health_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_memory_retention_health_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    memory_item_count: Decimal = d("10.000000"),
    fresh_memory_item_count: Decimal = d("8.000000"),
    reused_memory_item_count: Decimal = d("4.000000"),
    calibration_feedback_count: Decimal = d("3.000000"),
    coverage_gap_count: Decimal = d("0.000000"),
    open_review_backlog_count: Decimal = d("1.000000"),
    high_priority_review_backlog_count: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = ("research_team_memory_retention_health_observed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamMemoryRetentionHealthSnapshot:
    return ResearchTeamMemoryRetentionHealthSnapshot(
        team_id=team_id,
        category_id=category_id,
        observed_at=observed_at,
        memory_item_count=memory_item_count,
        fresh_memory_item_count=fresh_memory_item_count,
        reused_memory_item_count=reused_memory_item_count,
        calibration_feedback_count=calibration_feedback_count,
        coverage_gap_count=coverage_gap_count,
        open_review_backlog_count=open_review_backlog_count,
        high_priority_review_backlog_count=high_priority_review_backlog_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *snapshots: ResearchTeamMemoryRetentionHealthSnapshot,
    config: ResearchTeamMemoryRetentionHealthConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamMemoryRetentionHealthReport:
    return build_research_team_memory_retention_health_report(
        snapshots,
        config=config or ResearchTeamMemoryRetentionHealthConfig(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_report_blocks_as_readonly_report_only_memory_gap() -> None:
    report = build_report()

    assert report.config_version == (
        DEFAULT_RESEARCH_TEAM_MEMORY_RETENTION_HEALTH_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.next_review_step == "block_memory_reuse_until_retention_review"
    assert report.snapshot_count == d("0.000000")
    assert report.team_category_count == d("0.000000")
    assert report.memory_item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.memory_freshness_ratio == d("0.000000")
    assert report.memory_reuse_ratio == d("0.000000")
    assert report.calibration_feedback_ratio == d("0.000000")
    assert report.coverage_gap_ratio == d("0.000000")
    assert report.review_backlog_pressure == d("0.000000")
    assert report.retention_health_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_team_memory_retention_health_no_team_memory",
    )
    assert report.reason_code_counts == (
        ResearchTeamMemoryRetentionHealthReasonCodeCount(
            reason_code="research_team_memory_retention_health_no_team_memory",
            count=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_specialist_memory_health_scores_freshness_reuse_feedback_gaps_and_backlog() -> None:
    report = build_report(
        snapshot(),
        snapshot(
            team_id="politics",
            category_id="politics",
            fresh_memory_item_count=d("5.000000"),
            reused_memory_item_count=d("1.000000"),
            calibration_feedback_count=d("1.000000"),
            coverage_gap_count=d("2.000000"),
            open_review_backlog_count=d("3.000000"),
            high_priority_review_backlog_count=d("1.000000"),
        ),
        snapshot(
            team_id="crypto_eth",
            category_id="finance.crypto.eth",
            observed_at=GENERATED_AT - timedelta(days=20),
            fresh_memory_item_count=d("2.000000"),
            reused_memory_item_count=d("0.000000"),
            calibration_feedback_count=d("0.000000"),
            coverage_gap_count=d("5.000000"),
            open_review_backlog_count=d("6.000000"),
            high_priority_review_backlog_count=d("4.000000"),
        ),
    )

    assert report.status == "block"
    assert report.next_review_step == "block_memory_reuse_until_retention_review"
    assert report.snapshot_count == d("3.000000")
    assert report.team_category_count == d("3.000000")
    assert report.memory_item_count == d("30.000000")
    assert report.fresh_memory_item_count == d("15.000000")
    assert report.reused_memory_item_count == d("5.000000")
    assert report.calibration_feedback_count == d("4.000000")
    assert report.coverage_gap_count == d("7.000000")
    assert report.open_review_backlog_count == d("10.000000")
    assert report.high_priority_review_backlog_count == d("5.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.memory_freshness_ratio == d("0.500000")
    assert report.memory_reuse_ratio == d("0.166667")
    assert report.calibration_feedback_ratio == d("0.133333")
    assert report.coverage_gap_ratio == d("0.233333")
    assert report.review_backlog_pressure == d("0.333333")
    assert report.retention_health_score == d("0.446667")
    assert report.reason_codes == (
        "research_team_memory_retention_health_snapshot_stale",
        "research_team_memory_retention_health_low_freshness",
        "research_team_memory_retention_health_low_reuse",
        "research_team_memory_retention_health_missing_calibration_feedback",
        "research_team_memory_retention_health_coverage_gap",
        "research_team_memory_retention_health_review_backlog_pressure",
    )

    assert tuple((row.team_id, row.category_id, row.health_status) for row in report.rows) == (
        ("crypto_btc", "finance.crypto.btc", "pass"),
        ("crypto_eth", "finance.crypto.eth", "block"),
        ("politics", "politics", "watch"),
    )
    passed, blocked, watched = report.rows
    assert passed.snapshot_age_seconds == d("7200.000000")
    assert passed.retention_health_score == d("0.680000")
    assert passed.reason_codes == ("research_team_memory_retention_health_passed",)
    assert blocked.snapshot_age_seconds == d("1728000.000000")
    assert blocked.memory_freshness_ratio == d("0.200000")
    assert blocked.review_backlog_pressure == d("0.600000")
    assert blocked.retention_health_score == d("0.220000")
    assert blocked.reason_codes == report.reason_codes
    assert watched.retention_health_score == d("0.440000")
    assert watched.reason_codes == (
        "research_team_memory_retention_health_low_freshness",
        "research_team_memory_retention_health_low_reuse",
        "research_team_memory_retention_health_missing_calibration_feedback",
        "research_team_memory_retention_health_coverage_gap",
        "research_team_memory_retention_health_review_backlog_pressure",
    )


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    first = build_report(
        snapshot(team_id="politics", category_id="politics"),
        snapshot(team_id="crypto_eth", category_id="finance.crypto.eth"),
    )
    second = build_report(
        snapshot(team_id="crypto_eth", category_id="finance.crypto.eth"),
        snapshot(team_id="politics", category_id="politics"),
    )

    first_payload = research_team_memory_retention_health_report_payload(first)
    second_payload = research_team_memory_retention_health_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["snapshot_count"] == "2.000000"
    assert first_payload["rows"][0]["team_id"] == "crypto_eth"
    assert first_payload["rows"][0]["retention_health_score"] == "0.680000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert "reference" not in encoded.lower()
    assert "source_id" not in encoded.lower()
    assert "wallet" not in encoded.lower()
    assert_payload_is_plain_json(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_memory_retention_health_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_memory_retention_health_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "team_id": "wallet-linked-team"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_memory_retention_health_report_payload(unsafe_value)


def test_validation_freezing_flags_utc_decimal_only_and_consistency_checks() -> None:
    normalized = snapshot(observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=EASTERN))
    report = build_report(normalized)

    assert normalized.observed_at == datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
    assert report.generated_at == GENERATED_AT
    assert report.status in {"pass", "watch", "block"}
    assert all(row.health_status in {"pass", "watch", "block"} for row in report.rows)

    for public_type in (
        ResearchTeamMemoryRetentionHealthConfig,
        ResearchTeamMemoryRetentionHealthSnapshot,
        ResearchTeamMemoryRetentionHealthRow,
        ResearchTeamMemoryRetentionHealthReasonCodeCount,
        ResearchTeamMemoryRetentionHealthReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for field in fields(public_type):
            if is_numeric_public_field(field.name):
                assert annotation_allows_decimal_only(hints[field.name]), (
                    public_type.__name__,
                    field.name,
                    hints[field.name],
                )

    for instance in (
        ResearchTeamMemoryRetentionHealthConfig(),
        normalized,
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        for field in fields(instance):
            if is_numeric_public_field(field.name):
                value = getattr(instance, field.name)
                assert type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        normalized.team_id = "politics"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=NoOffsetTZ()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        snapshot(observed_at=DateTimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="memory_item_count must be a Decimal"):
        snapshot(memory_item_count=DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="readonly"):
        snapshot(readonly=False)
    with pytest.raises(ValueError, match="team/category values must be unique"):
        build_report(snapshot(), snapshot())
    with pytest.raises(ValueError, match="config"):
        build_research_team_memory_retention_health_report(
            (snapshot(),),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="snapshot"):
        build_research_team_memory_retention_health_report(
            (object(),),  # type: ignore[arg-type]
            config=ResearchTeamMemoryRetentionHealthConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="memory_freshness_ratio"):
        replace(report.rows[0], memory_freshness_ratio=d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_owned_module_is_static_report_only_without_side_effect_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for term in (
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "sqlite3",
        "psycopg",
        "supabase",
        "open(",
        "write_text",
        "write_bytes",
        "live_trading",
        "trade_execution",
    ):
        assert term not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


class NoOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class DateTimeSubclass(datetime):
    pass


class DecimalSubclass(Decimal):
    pass


def assert_payload_is_plain_json(value: object) -> None:
    if type(value) in (Decimal, float, int):
        pytest.fail(f"payload contains non-string public numeric value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_is_plain_json(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_is_plain_json(child)


def is_numeric_public_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
        or field_name.endswith("_pressure")
        or field_name.endswith("_seconds")
    )


def annotation_allows_decimal_only(annotation: object) -> bool:
    if annotation is Decimal:
        return True
    origin = get_origin(annotation)
    if origin is None:
        return False
    return set(get_args(annotation)) <= {Decimal, type(None)}
