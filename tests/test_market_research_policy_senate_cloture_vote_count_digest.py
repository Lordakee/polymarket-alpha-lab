from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_policy_senate_cloture_vote_count_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION,
    MarketResearchPolicySenateClotureVoteCountDigestConfig,
    MarketResearchPolicySenateClotureVoteCountDigestInputRow,
    MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount,
    MarketResearchPolicySenateClotureVoteCountDigestReport,
    MarketResearchPolicySenateClotureVoteCountDigestRow,
    build_market_research_policy_senate_cloture_vote_count_digest,
    market_research_policy_senate_cloture_vote_count_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_senate_cloture_vote_count_digest.py",
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
) -> MarketResearchPolicySenateClotureVoteCountDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION
        ),
        "cloture_vote_threshold": d("60"),
        "watch_vote_margin": d("3"),
        "blocked_vote_margin": d("1"),
        "max_snapshot_age_seconds": d("7200.000000"),
        "min_public_source_count": d("2"),
        "min_cross_source_agreement": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchPolicySenateClotureVoteCountDigestConfig(**values)


def input_row(
    research_key: str = "research.senate_cloture.infrastructure",
    *,
    condition_id: str = "condition_senate_cloture_infrastructure",
    motion_key: str = "infrastructure-motion",
    chamber: str = "senate",
    public_vote_reference: str = "public-senate-cloture-whip-memo",
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
) -> MarketResearchPolicySenateClotureVoteCountDigestInputRow:
    return MarketResearchPolicySenateClotureVoteCountDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        motion_key=motion_key,
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
    cfg: MarketResearchPolicySenateClotureVoteCountDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicySenateClotureVoteCountDigestReport:
    return build_market_research_policy_senate_cloture_vote_count_digest(
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


def assert_public_numerics_are_decimal(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal, field.name


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    summary = report(())

    assert isinstance(summary, MarketResearchPolicySenateClotureVoteCountDigestReport)
    assert is_dataclass(summary)
    assert summary.__dataclass_params__.frozen
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_POLICY_SENATE_CLOTURE_VOTE_COUNT_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_senate_cloture_vote_count_digest"
    )
    assert summary.vote_count == ZERO
    assert summary.ready_vote_count == ZERO
    assert summary.watch_vote_count == ZERO
    assert summary.blocked_vote_count == ZERO
    assert summary.below_threshold_count == ZERO
    assert summary.stale_snapshot_count == ZERO
    assert summary.thin_source_count == ZERO
    assert summary.low_agreement_count == ZERO
    assert summary.probability_shift_count == ZERO
    assert summary.max_vote_shortfall == ZERO
    assert summary.average_vote_margin == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_senate_cloture_vote_count_digest_no_inputs"
            ),
            count=ONE,
            vote_ratio=ONE,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_senate_cloture_vote_count_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_high_risk_cloture_vote_count_blocks_probability_event_screening() -> None:
    sensitive_reference = "https://whip.example/senate?token=secret-123"

    summary = report(
        (
            input_row(
                "research.senate_cloture.defense",
                condition_id="condition_senate_cloture_defense",
                motion_key="defense-motion",
                public_vote_reference=sensitive_reference,
                observed_at=GENERATED_AT - timedelta(hours=3),
                committed_yes_count=d("57"),
                lean_yes_count=d("1"),
                undecided_count=d("6"),
                committed_no_count=d("36"),
                public_source_count=d("1"),
                cross_source_agreement=d("0.500000"),
                market_probability_before=d("0.280000"),
                market_probability_after=d("0.450000"),
            ),
            input_row(
                "research.senate_cloture.energy",
                condition_id="condition_senate_cloture_energy",
                motion_key="energy-motion",
                public_vote_reference="public-energy-cloture-calendar",
                committed_yes_count=d("59"),
                lean_yes_count=d("2"),
                undecided_count=d("3"),
                committed_no_count=d("36"),
                public_source_count=d("3"),
                cross_source_agreement=d("0.800000"),
            ),
            input_row(
                public_vote_reference="public-senate-cloture-whip-memo",
                public_source_count=d("4"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_senate_cloture_vote_count_digest"
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
    assert summary.max_vote_shortfall == d("2.000000")
    assert summary.average_vote_margin == d("1.000000")
    assert summary.average_public_source_count == d("2.666667")

    assert tuple((row.vote_status, row.motion_key) for row in summary.rows) == (
        ("blocked", "defense-motion"),
        ("watch", "energy-motion"),
        ("ready", "infrastructure-motion"),
    )

    blocked, watched, ready = summary.rows
    assert blocked.snapshot_age_seconds == d("10800.000000")
    assert blocked.total_yes_count == d("58.000000")
    assert blocked.vote_margin == d("-2.000000")
    assert blocked.vote_shortfall == d("2.000000")
    assert blocked.probability_change == d("0.170000")
    assert blocked.redacted_vote_reference == (
        f"sha256:{sha256(sensitive_reference.encode('utf-8')).hexdigest()[:12]}"
    )
    assert blocked.reason_codes == (
        "market_research_policy_senate_cloture_vote_count_digest_below_threshold_block",
        "market_research_policy_senate_cloture_vote_count_digest_probability_shift",
        "market_research_policy_senate_cloture_vote_count_digest_low_agreement",
        "market_research_policy_senate_cloture_vote_count_digest_stale_snapshot",
        "market_research_policy_senate_cloture_vote_count_digest_thin_sources",
    )

    assert watched.snapshot_age_seconds == d("1800.000000")
    assert watched.total_yes_count == d("61.000000")
    assert watched.vote_margin == d("1.000000")
    assert watched.vote_shortfall == ZERO
    assert watched.redacted_vote_reference == "public-energy-cloture-calendar"
    assert watched.reason_codes == (
        "market_research_policy_senate_cloture_vote_count_digest_below_threshold_watch",
    )

    assert ready.vote_status == "ready"
    assert ready.total_yes_count == d("64.000000")
    assert ready.vote_margin == d("4.000000")
    assert ready.reason_codes == (
        "market_research_policy_senate_cloture_vote_count_digest_ready",
    )

    assert tuple(item.reason_code for item in summary.reason_code_counts) == (
        "market_research_policy_senate_cloture_vote_count_digest_below_threshold_block",
        "market_research_policy_senate_cloture_vote_count_digest_probability_shift",
        "market_research_policy_senate_cloture_vote_count_digest_below_threshold_watch",
        "market_research_policy_senate_cloture_vote_count_digest_low_agreement",
        "market_research_policy_senate_cloture_vote_count_digest_stale_snapshot",
        "market_research_policy_senate_cloture_vote_count_digest_thin_sources",
        "market_research_policy_senate_cloture_vote_count_digest_ready",
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = input_row(
        "research.senate_cloture.z_watch",
        condition_id="condition_senate_cloture_z_watch",
        motion_key="z-watch-motion",
        committed_yes_count=d("59"),
        lean_yes_count=d("2"),
    )
    second = input_row(
        "research.senate_cloture.a_block",
        condition_id="condition_senate_cloture_a_block",
        motion_key="a-block-motion",
        committed_yes_count=d("56"),
        lean_yes_count=d("1"),
        market_probability_before=d("0.230000"),
        market_probability_after=d("0.360000"),
    )
    third = input_row(
        "research.senate_cloture.a_watch",
        condition_id="condition_senate_cloture_a_watch",
        motion_key="a-watch-motion",
        committed_yes_count=d("58"),
        lean_yes_count=d("2"),
    )

    forward = report((first, second, third))
    reverse = report((third, second, first))

    assert forward == reverse
    assert tuple(row.motion_key for row in forward.rows) == (
        "a-block-motion",
        "a-watch-motion",
        "z-watch-motion",
    )
    assert all(row.reason_codes == tuple(sorted(row.reason_codes)) for row in forward.rows)
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "market_research_policy_senate_cloture_vote_count_digest_below_threshold_block",
        "market_research_policy_senate_cloture_vote_count_digest_probability_shift",
        "market_research_policy_senate_cloture_vote_count_digest_below_threshold_watch",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    assert is_dataclass(MarketResearchPolicySenateClotureVoteCountDigestConfig)
    assert is_dataclass(MarketResearchPolicySenateClotureVoteCountDigestInputRow)
    assert is_dataclass(MarketResearchPolicySenateClotureVoteCountDigestRow)
    assert is_dataclass(MarketResearchPolicySenateClotureVoteCountDigestReasonCodeCount)
    assert is_dataclass(MarketResearchPolicySenateClotureVoteCountDigestReport)

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("senate-cloture-v0"))
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
        input_row(observed_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC))
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
    with pytest.raises(ValueError, match="public_vote_reference"):
        input_row(public_vote_reference="")
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_policy_senate_cloture_vote_count_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="duplicate research keys"):
        report((input_row(), input_row()))
    with pytest.raises(ValueError, match="observed_at"):
        report((input_row(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    ready_row = report((input_row(),)).rows[0]
    with pytest.raises(ValueError, match="total_yes_count"):
        replace(ready_row, total_yes_count=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready_row,
            reason_codes=(
                "market_research_policy_senate_cloture_vote_count_digest_ready",
                "market_research_policy_senate_cloture_vote_count_digest_low_agreement",
            ),
        )
    with pytest.raises(ValueError, match="vote_status"):
        replace(ready_row, vote_status="blocked")

    unordered = report(
        (
            input_row("research.senate_cloture.z", condition_id="condition_z"),
            input_row("research.senate_cloture.a", condition_id="condition_a"),
        ),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_hard_flags_are_enforced_on_config_inputs_rows_counts_and_report() -> None:
    summary = report((input_row(),))

    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in summary.rows)
    assert all(
        row.paper_only and row.report_only and row.readonly
        for row in summary.reason_code_counts
    )

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)


def test_non_default_thresholds_can_downgrade_near_threshold_vote_count_risk() -> None:
    cfg = config(watch_vote_margin=d("1"), blocked_vote_margin=d("0"))

    summary = report(
        (
            input_row(
                committed_yes_count=d("59"),
                lean_yes_count=d("2"),
                public_source_count=d("3"),
                cross_source_agreement=d("0.900000"),
            ),
        ),
        cfg=cfg,
    )

    assert summary.digest_status == "ready"
    assert summary.next_step == (
        "allow_report_only_market_research_policy_senate_cloture_vote_count_digest"
    )
    assert summary.ready_vote_count == d("1.000000")
    assert summary.watch_vote_count == ZERO
    assert summary.blocked_vote_count == ZERO
    assert summary.rows[0].vote_status == "ready"
    assert summary.rows[0].reason_codes == (
        "market_research_policy_senate_cloture_vote_count_digest_ready",
    )
    assert summary.reason_codes == (
        "market_research_policy_senate_cloture_vote_count_digest_ready",
    )


def test_payload_uses_string_numerics_redacts_and_exposes_no_live_surfaces() -> None:
    sensitive_reference = "https://whip.example/senate?token=secret-123"
    summary = report((input_row(public_vote_reference=sensitive_reference),))

    payload = market_research_policy_senate_cloture_vote_count_digest_payload(summary)

    assert payload["vote_count"] == "1.000000"
    assert payload["average_vote_margin"] == "4.000000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T14:30:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "public_vote_reference" not in repr(payload)
    assert "secret-123" not in repr(payload)
    assert "whip.example" not in repr(payload)
    assert "token=" not in repr(payload)
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in walk_values(payload))

    for public_record in (
        config(),
        input_row(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert_public_numerics_are_decimal(public_record)

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
        "submit_order",
        "cancel_order",
        "replace_order",
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
