from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_policy_filibuster_vote_count_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_FILIBUSTER_VOTE_COUNT_DIGEST_CONFIG_VERSION,
    MarketResearchPolicyFilibusterVoteCountDigestConfig,
    MarketResearchPolicyFilibusterVoteCountDigestInputRow,
    MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount,
    MarketResearchPolicyFilibusterVoteCountDigestReport,
    MarketResearchPolicyFilibusterVoteCountDigestRow,
    build_market_research_policy_filibuster_vote_count_digest,
    market_research_policy_filibuster_vote_count_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_policy_filibuster_vote_count_digest.py",
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
) -> MarketResearchPolicyFilibusterVoteCountDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLICY_FILIBUSTER_VOTE_COUNT_DIGEST_CONFIG_VERSION
        ),
        "cloture_vote_threshold": d("60"),
        "watch_vote_margin": d("3"),
        "blocked_vote_margin": d("1"),
        "max_snapshot_age_seconds": d("7200.000000"),
        "min_public_source_count": d("2"),
        "min_cross_source_agreement": d("0.600000"),
    }
    values.update(overrides)
    return MarketResearchPolicyFilibusterVoteCountDigestConfig(**values)


def input_row(
    research_key: str = "research.filibuster.finance",
    *,
    condition_id: str = "condition_filibuster_finance",
    bill_key: str = "finance-reform",
    chamber: str = "senate",
    public_vote_reference: str = "public-senate-cloture-memo",
    observed_at: datetime | None = None,
    committed_yes_count: Decimal = d("62"),
    lean_yes_count: Decimal = d("2"),
    undecided_count: Decimal = d("1"),
    committed_no_count: Decimal = d("35"),
    public_source_count: Decimal = d("3"),
    cross_source_agreement: Decimal = d("0.850000"),
    market_probability_before: Decimal = d("0.410000"),
    market_probability_after: Decimal = d("0.430000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPolicyFilibusterVoteCountDigestInputRow:
    return MarketResearchPolicyFilibusterVoteCountDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        bill_key=bill_key,
        chamber=chamber,
        public_vote_reference=public_vote_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        committed_yes_count=committed_yes_count,
        lean_yes_count=lean_yes_count,
        undecided_count=undecided_count,
        committed_no_count=committed_no_count,
        public_source_count=public_source_count,
        cross_source_agreement=cross_source_agreement,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchPolicyFilibusterVoteCountDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicyFilibusterVoteCountDigestReport:
    return build_market_research_policy_filibuster_vote_count_digest(
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
        if field.name.endswith("_seconds") or field.name.endswith("_margin"):
            assert type(item) is Decimal
        if field.name.endswith("_change"):
            assert type(item) is Decimal


def test_filibuster_vote_count_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    sensitive_reference = "https://vendor.example/whip?token=secret-123"
    summary = report(
        (
            input_row(
                "research.filibuster.energy",
                condition_id="condition_filibuster_energy",
                bill_key="energy-permitting",
                public_vote_reference="public-energy-cloture-notice",
                observed_at=GENERATED_AT - timedelta(hours=3),
                committed_yes_count=d("59"),
                lean_yes_count=d("2"),
                undecided_count=d("5"),
                committed_no_count=d("34"),
                public_source_count=d("1"),
                cross_source_agreement=d("0.500000"),
                market_probability_before=d("0.520000"),
                market_probability_after=d("0.570000"),
            ),
            input_row(
                "research.filibuster.health",
                condition_id="condition_filibuster_health",
                bill_key="health-subsidy",
                public_vote_reference=sensitive_reference,
                observed_at=GENERATED_AT - timedelta(hours=1),
                committed_yes_count=d("58"),
                lean_yes_count=d("1"),
                undecided_count=d("2"),
                committed_no_count=d("39"),
                public_source_count=d("2"),
                cross_source_agreement=d("0.800000"),
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
        DEFAULT_MARKET_RESEARCH_POLICY_FILIBUSTER_VOTE_COUNT_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_filibuster_vote_count_digest"
    )
    assert summary.vote_count == d("3.000000")
    assert summary.ready_vote_count == d("1.000000")
    assert summary.watch_vote_count == d("1.000000")
    assert summary.blocked_vote_count == d("1.000000")
    assert summary.below_threshold_count == d("2.000000")
    assert summary.stale_snapshot_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.low_agreement_count == d("1.000000")
    assert summary.probability_shift_count == d("1.000000")
    assert summary.max_vote_shortfall == d("1.000000")
    assert summary.average_vote_margin == d("1.333333")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.vote_status, row.bill_key) for row in summary.rows) == (
        ("blocked", "health-subsidy"),
        ("watch", "energy-permitting"),
        ("ready", "finance-reform"),
    )

    blocked = summary.rows[0]
    assert blocked.snapshot_age_seconds == d("3600.000000")
    assert blocked.total_yes_count == d("59.000000")
    assert blocked.vote_margin == d("-1.000000")
    assert blocked.vote_shortfall == d("1.000000")
    assert blocked.probability_change == d("0.150000")
    assert blocked.redacted_vote_reference == (
        f"sha256:{sha256(sensitive_reference.encode('utf-8')).hexdigest()[:12]}"
    )
    assert blocked.reason_codes == (
        "market_research_policy_filibuster_vote_count_digest_below_threshold_block",
        "market_research_policy_filibuster_vote_count_digest_probability_shift",
    )

    watch = summary.rows[1]
    assert watch.snapshot_age_seconds == d("10800.000000")
    assert watch.total_yes_count == d("61.000000")
    assert watch.vote_margin == d("1.000000")
    assert watch.vote_shortfall == ZERO
    assert watch.redacted_vote_reference == "public-energy-cloture-notice"
    assert watch.reason_codes == (
        "market_research_policy_filibuster_vote_count_digest_below_threshold_watch",
        "market_research_policy_filibuster_vote_count_digest_low_agreement",
        "market_research_policy_filibuster_vote_count_digest_stale_snapshot",
        "market_research_policy_filibuster_vote_count_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.vote_status == "ready"
    assert ready.snapshot_age_seconds == d("1800.000000")
    assert ready.total_yes_count == d("64.000000")
    assert ready.vote_margin == d("4.000000")
    assert ready.vote_shortfall == ZERO
    assert ready.redacted_vote_reference == "public-senate-cloture-memo"
    assert ready.reason_codes == (
        "market_research_policy_filibuster_vote_count_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_filibuster_vote_count_digest_below_threshold_block"
            ),
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
        ),
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_filibuster_vote_count_digest_probability_shift"
            ),
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
        ),
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_filibuster_vote_count_digest_below_threshold_watch"
            ),
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
        ),
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_filibuster_vote_count_digest_low_agreement"
            ),
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
        ),
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_filibuster_vote_count_digest_stale_snapshot"
            ),
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
        ),
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_filibuster_vote_count_digest_thin_sources"
            ),
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
        ),
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code="market_research_policy_filibuster_vote_count_digest_ready",
            count=d("1.000000"),
            vote_ratio=d("0.333333"),
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


def test_empty_filibuster_vote_count_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_filibuster_vote_count_digest"
    )
    assert summary.vote_count == ZERO
    assert summary.ready_vote_count == ZERO
    assert summary.watch_vote_count == ZERO
    assert summary.blocked_vote_count == ZERO
    assert summary.below_threshold_count == ZERO
    assert summary.max_vote_shortfall == ZERO
    assert summary.average_vote_margin == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount(
            reason_code="market_research_policy_filibuster_vote_count_digest_no_inputs",
            count=d("1.000000"),
            vote_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_filibuster_vote_count_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_filibuster_vote_count_digest_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = market_research_policy_filibuster_vote_count_digest_payload(summary)

    assert payload["vote_count"] == "1.000000"
    assert payload["average_vote_margin"] == "4.000000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "public_vote_reference" not in repr(payload)
    assert "secret" not in repr(payload).lower()


def test_filibuster_vote_count_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchPolicyFilibusterVoteCountDigestConfig)
    assert is_dataclass(MarketResearchPolicyFilibusterVoteCountDigestInputRow)
    assert is_dataclass(MarketResearchPolicyFilibusterVoteCountDigestRow)
    assert is_dataclass(MarketResearchPolicyFilibusterVoteCountDigestReasonCodeCount)
    assert is_dataclass(MarketResearchPolicyFilibusterVoteCountDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("filibuster-v0"))
    with pytest.raises(ValueError, match="cloture_vote_threshold"):
        config(cloture_vote_threshold=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_vote_margin"):
        config(watch_vote_margin=_DecimalSubclass("3"))
    with pytest.raises(ValueError, match="blocked_vote_margin"):
        config(watch_vote_margin=d("1"), blocked_vote_margin=d("3"))
    with pytest.raises(ValueError, match="max_snapshot_age_seconds"):
        config(max_snapshot_age_seconds=Decimal("NaN"))
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_cross_source_agreement"):
        config(min_cross_source_agreement=d("1.000001"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_order_surface")
    with pytest.raises(ValueError, match="chamber"):
        input_row(chamber="private-senate")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="committed_yes_count"):
        input_row(committed_yes_count=58)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lean_yes_count"):
        input_row(lean_yes_count=d("1.5"))
    with pytest.raises(ValueError, match="cross_source_agreement"):
        input_row(cross_source_agreement=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_policy_filibuster_vote_count_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_policy_filibuster_vote_count_digest(
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
                "market_research_policy_filibuster_vote_count_digest_ready",
                "market_research_policy_filibuster_vote_count_digest_low_agreement",
            ),
        )
    with pytest.raises(ValueError, match="vote_status"):
        replace(ready, vote_status="blocked")
    with pytest.raises(ValueError, match="probability_change"):
        replace(ready, probability_change=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_vote_reference"):
        replace(ready, redacted_vote_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_vote_count"):
        replace(report((input_row(),)), ready_vote_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.filibuster.zeta", bill_key="zeta-bill"),
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
