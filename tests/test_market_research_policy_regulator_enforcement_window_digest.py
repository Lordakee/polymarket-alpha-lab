from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_policy_regulator_enforcement_window_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_REGULATOR_ENFORCEMENT_WINDOW_DIGEST_CONFIG_VERSION,
    MarketResearchPolicyRegulatorEnforcementWindowDigestConfig,
    MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow,
    MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount,
    MarketResearchPolicyRegulatorEnforcementWindowDigestReport,
    MarketResearchPolicyRegulatorEnforcementWindowDigestRow,
    build_market_research_policy_regulator_enforcement_window_digest,
    market_research_policy_regulator_enforcement_window_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_regulator_enforcement_window_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchPolicyRegulatorEnforcementWindowDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLICY_REGULATOR_ENFORCEMENT_WINDOW_DIGEST_CONFIG_VERSION
        ),
        "near_window_seconds": d("604800.000000"),
        "stale_evidence_after_seconds": d("21600.000000"),
        "min_public_source_count": d("2.000000"),
        "min_independent_source_family_count": d("2.000000"),
        "min_cross_source_agreement": d("0.650000"),
        "materiality_watch_threshold": d("0.150000"),
        "materiality_block_threshold": d("0.350000"),
    }
    values.update(overrides)
    return MarketResearchPolicyRegulatorEnforcementWindowDigestConfig(**values)


def input_row(
    research_key: str = "research.enforcement.finance",
    *,
    condition_id: str = "condition_finance_enforcement",
    policy_area: str = "finance_enforcement",
    regulator_name: str = "public-finance-regulator",
    public_notice_reference: str = "public-regulator-notice",
    enforcement_window_starts_at: datetime | None = None,
    enforcement_window_ends_at: datetime | None = None,
    observed_at: datetime | None = None,
    public_source_count: Decimal = d("3.000000"),
    independent_source_family_count: Decimal = d("2.000000"),
    cross_source_agreement: Decimal = d("0.850000"),
    enforcement_materiality_score: Decimal = d("0.050000"),
    market_probability_before: Decimal = d("0.410000"),
    market_probability_after: Decimal = d("0.430000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow:
    return MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        policy_area=policy_area,
        regulator_name=regulator_name,
        public_notice_reference=public_notice_reference,
        enforcement_window_starts_at=(
            enforcement_window_starts_at or GENERATED_AT + timedelta(days=14)
        ),
        enforcement_window_ends_at=(
            enforcement_window_ends_at or GENERATED_AT + timedelta(days=21)
        ),
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        public_source_count=public_source_count,
        independent_source_family_count=independent_source_family_count,
        cross_source_agreement=cross_source_agreement,
        enforcement_materiality_score=enforcement_materiality_score,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchPolicyRegulatorEnforcementWindowDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicyRegulatorEnforcementWindowDigestReport:
    return build_market_research_policy_regulator_enforcement_window_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_seconds",
                "_score",
                "_change",
            ),
        ) or field.name.startswith(("average_", "max_", "min_")):
            assert type(item) is Decimal, field.name


def test_regulator_enforcement_window_digest_reduces_rows_redacts_and_sorts() -> None:
    sensitive_reference = "https://vendor.example/regulator?access=hidden-123"
    summary = report(
        (
            input_row(
                "research.enforcement.energy",
                condition_id="condition_energy_enforcement",
                policy_area="energy_enforcement",
                regulator_name="public-energy-regulator",
                public_notice_reference="public-energy-regulator-notice",
                enforcement_window_starts_at=GENERATED_AT + timedelta(days=3),
                enforcement_window_ends_at=GENERATED_AT + timedelta(days=10),
                observed_at=GENERATED_AT - timedelta(hours=8),
                public_source_count=d("1.000000"),
                independent_source_family_count=d("1.000000"),
                cross_source_agreement=d("0.550000"),
                enforcement_materiality_score=d("0.200000"),
                market_probability_before=d("0.520000"),
                market_probability_after=d("0.580000"),
            ),
            input_row(
                "research.enforcement.health",
                condition_id="condition_health_enforcement",
                policy_area="health_enforcement",
                regulator_name="public-health-regulator",
                public_notice_reference=sensitive_reference,
                enforcement_window_starts_at=GENERATED_AT - timedelta(days=1),
                enforcement_window_ends_at=GENERATED_AT + timedelta(days=4),
                observed_at=GENERATED_AT - timedelta(hours=2),
                public_source_count=d("3.000000"),
                independent_source_family_count=d("2.000000"),
                cross_source_agreement=d("0.900000"),
                enforcement_materiality_score=d("0.420000"),
                market_probability_before=d("0.250000"),
                market_probability_after=d("0.400000"),
            ),
            input_row(),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_POLICY_REGULATOR_ENFORCEMENT_WINDOW_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_regulator_enforcement_window_digest"
    )
    assert summary.window_count == d("3.000000")
    assert summary.ready_window_count == d("1.000000")
    assert summary.watch_window_count == d("1.000000")
    assert summary.blocked_window_count == d("1.000000")
    assert summary.active_window_count == d("1.000000")
    assert summary.upcoming_window_count == d("2.000000")
    assert summary.closed_window_count == ZERO
    assert summary.near_window_count == d("1.000000")
    assert summary.material_window_count == d("2.000000")
    assert summary.stale_evidence_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.thin_source_family_count == d("1.000000")
    assert summary.low_agreement_count == d("1.000000")
    assert summary.probability_shift_count == d("1.000000")
    assert summary.average_materiality_score == d("0.223333")
    assert summary.max_observation_age_seconds == d("28800.000000")
    assert summary.min_seconds_until_window_start == d("-86400.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.window_status, row.policy_area) for row in summary.rows) == (
        ("blocked", "health_enforcement"),
        ("watch", "energy_enforcement"),
        ("ready", "finance_enforcement"),
    )

    blocked = summary.rows[0]
    assert blocked.window_state == "active"
    assert blocked.seconds_until_window_start == d("-86400.000000")
    assert blocked.seconds_until_window_end == d("345600.000000")
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.probability_change == d("0.150000")
    assert blocked.redacted_notice_reference == (
        f"sha256:{sha256(sensitive_reference.encode('utf-8')).hexdigest()[:12]}"
    )
    assert blocked.reason_codes == (
        "market_research_policy_regulator_enforcement_window_digest_active_window",
        "market_research_policy_regulator_enforcement_window_digest_material_block",
        "market_research_policy_regulator_enforcement_window_digest_probability_shift",
    )

    watch = summary.rows[1]
    assert watch.window_state == "upcoming"
    assert watch.seconds_until_window_start == d("259200.000000")
    assert watch.redacted_notice_reference == "public-energy-regulator-notice"
    assert watch.reason_codes == (
        "market_research_policy_regulator_enforcement_window_digest_near_window",
        "market_research_policy_regulator_enforcement_window_digest_material_watch",
        "market_research_policy_regulator_enforcement_window_digest_low_agreement",
        "market_research_policy_regulator_enforcement_window_digest_stale_evidence",
        "market_research_policy_regulator_enforcement_window_digest_thin_sources",
        "market_research_policy_regulator_enforcement_window_digest_thin_source_families",
    )

    ready = summary.rows[2]
    assert ready.window_status == "ready"
    assert ready.window_state == "upcoming"
    assert ready.seconds_until_window_start == d("1209600.000000")
    assert ready.redacted_notice_reference == "public-regulator-notice"
    assert ready.reason_codes == (
        "market_research_policy_regulator_enforcement_window_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_active_window"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_near_window"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_material_block"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_material_watch"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_probability_shift"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_low_agreement"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_stale_evidence"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_thin_sources"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_"
                "thin_source_families"
            ),
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code="market_research_policy_regulator_enforcement_window_digest_ready",
            count=d("1.000000"),
            window_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in ("hidden-123", "vendor.example", "https://", "credential"):
        assert value not in public


def test_empty_regulator_enforcement_window_digest_is_blocked_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_regulator_enforcement_window_digest"
    )
    assert summary.window_count == ZERO
    assert summary.ready_window_count == ZERO
    assert summary.watch_window_count == ZERO
    assert summary.blocked_window_count == ZERO
    assert summary.active_window_count == ZERO
    assert summary.upcoming_window_count == ZERO
    assert summary.closed_window_count == ZERO
    assert summary.average_materiality_score == ZERO
    assert summary.max_observation_age_seconds == ZERO
    assert summary.min_seconds_until_window_start is None
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_regulator_enforcement_window_digest_no_inputs"
            ),
            count=d("1.000000"),
            window_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_regulator_enforcement_window_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_regulator_enforcement_window_digest_payload_uses_decimal_strings() -> None:
    summary = report((input_row(),))
    payload = market_research_policy_regulator_enforcement_window_digest_payload(summary)

    assert payload["window_count"] == "1.000000"
    assert payload["average_materiality_score"] == "0.050000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["rows"][0]["seconds_until_window_start"] == "1209600.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "public_notice_reference" not in repr(payload)
    assert "hidden" not in repr(payload).lower()


def test_regulator_enforcement_window_digest_validates_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchPolicyRegulatorEnforcementWindowDigestConfig)
    assert is_dataclass(MarketResearchPolicyRegulatorEnforcementWindowDigestInputRow)
    assert is_dataclass(MarketResearchPolicyRegulatorEnforcementWindowDigestRow)
    assert is_dataclass(
        MarketResearchPolicyRegulatorEnforcementWindowDigestReasonCodeCount,
    )
    assert is_dataclass(MarketResearchPolicyRegulatorEnforcementWindowDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("regulator-enforcement-v0"))
    with pytest.raises(ValueError, match="near_window_seconds"):
        config(near_window_seconds=604800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_evidence_after_seconds"):
        config(stale_evidence_after_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="min_cross_source_agreement"):
        config(min_cross_source_agreement=Decimal("NaN"))
    with pytest.raises(ValueError, match="materiality_block_threshold"):
        config(
            materiality_watch_threshold=d("0.500000"),
            materiality_block_threshold=d("0.350000"),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_surface")
    with pytest.raises(ValueError, match="regulator_name"):
        input_row(regulator_name="credential-regulator")
    with pytest.raises(ValueError, match="enforcement_window_starts_at"):
        input_row(enforcement_window_starts_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="enforcement_window_ends_at"):
        input_row(
            enforcement_window_starts_at=GENERATED_AT + timedelta(days=2),
            enforcement_window_ends_at=GENERATED_AT + timedelta(days=1),
        )
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_family_count"):
        input_row(independent_source_family_count=d("1.500000"))
    with pytest.raises(ValueError, match="cross_source_agreement"):
        input_row(cross_source_agreement=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="enforcement_materiality_score"):
        input_row(enforcement_materiality_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_policy_regulator_enforcement_window_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_policy_regulator_enforcement_window_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_regulator_enforcement_window_digest_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_regulator_enforcement_window_digest_ready",
                "market_research_policy_regulator_enforcement_window_digest_near_window",
            ),
        )
    with pytest.raises(ValueError, match="window_status"):
        replace(ready, window_status="blocked")
    with pytest.raises(ValueError, match="probability_change"):
        replace(ready, probability_change=d("9.999999"))
    with pytest.raises(ValueError, match="seconds_until_window_start"):
        replace(ready, seconds_until_window_start=d("1.000000"))
    with pytest.raises(ValueError, match="window_state"):
        replace(ready, window_state="active")
    with pytest.raises(ValueError, match="redacted_notice_reference"):
        replace(ready, redacted_notice_reference="https://host.example/access=hidden")

    with pytest.raises(ValueError, match="ready_window_count"):
        replace(report((input_row(),)), ready_window_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.enforcement.zeta", policy_area="zeta_enforcement"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_regulator_enforcement_window_digest_normalizes_offset_datetimes() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    starts_at = datetime(2026, 7, 5, 15, 0, tzinfo=timezone(timedelta(hours=3)))
    ends_at = datetime(2026, 7, 7, 15, 0, tzinfo=timezone(timedelta(hours=3)))
    observed_at = datetime(2026, 7, 4, 10, 30, tzinfo=timezone(timedelta(hours=2)))

    summary = report(
        (
            input_row(
                enforcement_window_starts_at=starts_at,
                enforcement_window_ends_at=ends_at,
                observed_at=observed_at,
            ),
        ),
        generated_at=generated_at,
    )

    row = summary.rows[0]
    assert summary.generated_at == GENERATED_AT
    assert row.enforcement_window_starts_at == datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
    assert row.enforcement_window_ends_at == datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    assert row.observed_at == datetime(2026, 7, 4, 8, 30, tzinfo=UTC)
    assert row.seconds_until_window_start == d("86400.000000")
    assert row.seconds_until_window_end == d("259200.000000")
    assert row.observation_age_seconds == d("12600.000000")


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_regulator_enforcement_window_digest_has_no_io_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
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
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "api_key",
        "wallet://",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
