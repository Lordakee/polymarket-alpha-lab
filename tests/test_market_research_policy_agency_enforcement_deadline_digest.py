from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_policy_agency_enforcement_deadline_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_AGENCY_ENFORCEMENT_DEADLINE_DIGEST_CONFIG_VERSION,
    MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig,
    MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow,
    MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount,
    MarketResearchPolicyAgencyEnforcementDeadlineDigestReport,
    MarketResearchPolicyAgencyEnforcementDeadlineDigestRow,
    build_market_research_policy_agency_enforcement_deadline_digest,
    market_research_policy_agency_enforcement_deadline_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_policy_agency_enforcement_deadline_digest.py",
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
) -> MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLICY_AGENCY_ENFORCEMENT_DEADLINE_DIGEST_CONFIG_VERSION
        ),
        "fresh_deadline_notice_max_age_seconds": d("86400.000000"),
        "min_public_source_count": d("2"),
        "min_cross_source_confirmation": d("0.600000"),
        "materiality_watch_threshold": d("0.150000"),
        "materiality_block_threshold": d("0.350000"),
        "imminent_deadline_max_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig(**values)


def input_row(
    research_key: str = "research.deadline.finance",
    *,
    condition_id: str = "condition_finance_deadline",
    policy_area: str = "finance_deadline",
    agency_name: str = "public-finance-agency",
    public_deadline_reference: str = "public-agency-deadline-notice",
    deadline_announced_at: datetime | None = None,
    enforcement_deadline_at: datetime | None = None,
    public_source_count: Decimal = d("3"),
    cross_source_confirmation: Decimal = d("0.850000"),
    enforcement_materiality_score: Decimal = d("0.050000"),
    market_probability_before: Decimal = d("0.410000"),
    market_probability_after: Decimal = d("0.430000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow:
    return MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        policy_area=policy_area,
        agency_name=agency_name,
        public_deadline_reference=public_deadline_reference,
        deadline_announced_at=deadline_announced_at
        or GENERATED_AT - timedelta(minutes=30),
        enforcement_deadline_at=enforcement_deadline_at
        or GENERATED_AT + timedelta(hours=12),
        public_source_count=public_source_count,
        cross_source_confirmation=cross_source_confirmation,
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
    cfg: MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicyAgencyEnforcementDeadlineDigestReport:
    return build_market_research_policy_agency_enforcement_deadline_digest(
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
        if isinstance(item, Decimal) or item is None:
            continue
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(item) is Decimal
        if field.name.endswith("_seconds") or field.name.endswith("_score"):
            assert type(item) is Decimal
        if field.name.endswith("_change"):
            assert type(item) is Decimal


def test_agency_enforcement_deadline_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    sensitive_reference = "https://vendor.example/deadline?token=secret-123"
    summary = report(
        (
            input_row(
                "research.deadline.energy",
                condition_id="condition_energy_deadline",
                policy_area="energy_deadline",
                agency_name="public-energy-agency",
                public_deadline_reference="public-energy-deadline-docket",
                deadline_announced_at=GENERATED_AT - timedelta(hours=30),
                enforcement_deadline_at=GENERATED_AT + timedelta(hours=3),
                public_source_count=d("1"),
                cross_source_confirmation=d("0.500000"),
                enforcement_materiality_score=d("0.200000"),
                market_probability_before=d("0.520000"),
                market_probability_after=d("0.570000"),
            ),
            input_row(
                "research.deadline.health",
                condition_id="condition_health_deadline_missed",
                policy_area="health_deadline",
                agency_name="public-health-agency",
                public_deadline_reference=sensitive_reference,
                deadline_announced_at=GENERATED_AT - timedelta(hours=4),
                enforcement_deadline_at=GENERATED_AT - timedelta(hours=1),
                public_source_count=d("2"),
                cross_source_confirmation=d("0.800000"),
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
        DEFAULT_MARKET_RESEARCH_POLICY_AGENCY_ENFORCEMENT_DEADLINE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_agency_enforcement_deadline_digest"
    )
    assert summary.deadline_count == d("3.000000")
    assert summary.ready_deadline_count == d("1.000000")
    assert summary.watch_deadline_count == d("1.000000")
    assert summary.blocked_deadline_count == d("1.000000")
    assert summary.missed_deadline_count == d("1.000000")
    assert summary.imminent_deadline_count == d("0.000000")
    assert summary.material_deadline_count == d("2.000000")
    assert summary.stale_deadline_notice_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.low_confirmation_count == d("1.000000")
    assert summary.probability_shift_count == d("1.000000")
    assert summary.average_materiality_score == d("0.223333")
    assert summary.min_seconds_until_deadline == d("0.000000")
    assert summary.max_deadline_notice_age_seconds == d("108000.000000")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.deadline_status, row.policy_area) for row in summary.rows) == (
        ("blocked", "health_deadline"),
        ("watch", "energy_deadline"),
        ("ready", "finance_deadline"),
    )

    blocked = summary.rows[0]
    assert blocked.deadline_notice_age_seconds == d("14400.000000")
    assert blocked.seconds_until_deadline == ZERO
    assert blocked.deadline_overdue_seconds == d("3600.000000")
    assert blocked.probability_change == d("0.150000")
    assert blocked.redacted_deadline_reference == (
        f"sha256:{sha256(sensitive_reference.encode('utf-8')).hexdigest()[:12]}"
    )
    assert blocked.reason_codes == (
        "market_research_policy_agency_enforcement_deadline_digest_material_block",
        "market_research_policy_agency_enforcement_deadline_digest_probability_shift",
        "market_research_policy_agency_enforcement_deadline_digest_missed_deadline",
    )

    watch = summary.rows[1]
    assert watch.deadline_notice_age_seconds == d("108000.000000")
    assert watch.seconds_until_deadline == d("10800.000000")
    assert watch.deadline_overdue_seconds == ZERO
    assert watch.redacted_deadline_reference == "public-energy-deadline-docket"
    assert watch.reason_codes == (
        "market_research_policy_agency_enforcement_deadline_digest_low_confirmation",
        "market_research_policy_agency_enforcement_deadline_digest_material_watch",
        "market_research_policy_agency_enforcement_deadline_digest_stale_deadline_notice",
        "market_research_policy_agency_enforcement_deadline_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.deadline_status == "ready"
    assert ready.deadline_notice_age_seconds == d("1800.000000")
    assert ready.redacted_deadline_reference == "public-agency-deadline-notice"
    assert ready.reason_codes == (
        "market_research_policy_agency_enforcement_deadline_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_material_block"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_probability_shift"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_missed_deadline"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_low_confirmation"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_material_watch"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_stale_deadline_notice"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_thin_sources"
            ),
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code="market_research_policy_agency_enforcement_deadline_digest_ready",
            count=d("1.000000"),
            deadline_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "secret-123",
        "vendor.example",
        "https://",
        "credential",
        "token=",
    ):
        assert value not in public


def test_imminent_enforcement_deadline_is_watch_report_only() -> None:
    summary = report(
        (
            input_row(
                enforcement_deadline_at=GENERATED_AT + timedelta(minutes=45),
            ),
        ),
    )

    assert summary.digest_status == "watch"
    assert summary.next_step == (
        "watch_report_only_market_research_policy_agency_enforcement_deadline_digest"
    )
    assert summary.imminent_deadline_count == d("1.000000")
    assert summary.rows[0].deadline_status == "watch"
    assert summary.rows[0].seconds_until_deadline == d("2700.000000")
    assert summary.rows[0].deadline_overdue_seconds == ZERO
    assert summary.rows[0].reason_codes == (
        "market_research_policy_agency_enforcement_deadline_digest_imminent_deadline",
    )


def test_empty_agency_enforcement_deadline_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_agency_enforcement_deadline_digest"
    )
    assert summary.deadline_count == ZERO
    assert summary.ready_deadline_count == ZERO
    assert summary.watch_deadline_count == ZERO
    assert summary.blocked_deadline_count == ZERO
    assert summary.missed_deadline_count == ZERO
    assert summary.average_materiality_score == ZERO
    assert summary.min_seconds_until_deadline == ZERO
    assert summary.max_deadline_notice_age_seconds == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_agency_enforcement_deadline_digest_no_inputs"
            ),
            count=d("1.000000"),
            deadline_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_agency_enforcement_deadline_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_agency_enforcement_deadline_digest_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = market_research_policy_agency_enforcement_deadline_digest_payload(summary)

    assert payload["deadline_count"] == "1.000000"
    assert payload["average_materiality_score"] == "0.050000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["rows"][0]["seconds_until_deadline"] == "43200.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "public_deadline_reference" not in repr(payload)
    assert "secret" not in repr(payload).lower()


def test_agency_enforcement_deadline_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig)
    assert is_dataclass(MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow)
    assert is_dataclass(MarketResearchPolicyAgencyEnforcementDeadlineDigestRow)
    assert is_dataclass(MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount)
    assert is_dataclass(MarketResearchPolicyAgencyEnforcementDeadlineDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("agency-enforcement-deadline-v0"))
    with pytest.raises(ValueError, match="fresh_deadline_notice_max_age_seconds"):
        config(fresh_deadline_notice_max_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_cross_source_confirmation"):
        config(min_cross_source_confirmation=Decimal("NaN"))
    with pytest.raises(ValueError, match="materiality_watch_threshold"):
        config(materiality_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="materiality_block_threshold"):
        config(
            materiality_watch_threshold=d("0.500000"),
            materiality_block_threshold=d("0.350000"),
        )
    with pytest.raises(ValueError, match="imminent_deadline_max_seconds"):
        config(imminent_deadline_max_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_order_surface")
    with pytest.raises(ValueError, match="agency_name"):
        input_row(agency_name="private-agency")
    with pytest.raises(ValueError, match="deadline_announced_at"):
        input_row(deadline_announced_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="enforcement_deadline_at"):
        input_row(
            deadline_announced_at=GENERATED_AT - timedelta(hours=1),
            enforcement_deadline_at=GENERATED_AT - timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="enforcement_deadline_at"):
        input_row(
            enforcement_deadline_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cross_source_confirmation"):
        input_row(cross_source_confirmation=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="enforcement_materiality_score"):
        input_row(enforcement_materiality_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_policy_agency_enforcement_deadline_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_policy_agency_enforcement_deadline_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_agency_enforcement_deadline_digest_ready",
                "market_research_policy_agency_enforcement_deadline_digest_material_watch",
            ),
        )
    with pytest.raises(ValueError, match="deadline_status"):
        replace(ready, deadline_status="blocked")
    with pytest.raises(ValueError, match="probability_change"):
        replace(ready, probability_change=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_deadline_reference"):
        replace(ready, redacted_deadline_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_deadline_count"):
        replace(report((input_row(),)), ready_deadline_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.deadline.zeta", policy_area="zeta_deadline"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_execution_surfaces() -> None:
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
        "private_key",
        "api_key",
        "wallet://",
        "exchange_mutation",
        "database",
        "network",
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
