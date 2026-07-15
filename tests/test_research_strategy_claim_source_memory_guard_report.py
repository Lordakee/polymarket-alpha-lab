from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_claim_source_memory_guard_report import (
    CLAIM_SOURCE_MEMORY_GUARD_STATUSES,
    DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_MEMORY_GUARD_REPORT_CONFIG_VERSION,
    ResearchStrategyClaimSourceMemoryGuardConfig,
    ResearchStrategyClaimSourceMemoryGuardInput,
    ResearchStrategyClaimSourceMemoryGuardReasonCodeCount,
    ResearchStrategyClaimSourceMemoryGuardReport,
    ResearchStrategyClaimSourceMemoryGuardRow,
    build_research_strategy_claim_source_memory_guard_report,
    research_strategy_claim_source_memory_guard_report_digest,
    research_strategy_claim_source_memory_guard_report_public_payload,
    validate_research_strategy_claim_source_memory_guard_report_payload_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyClaimSourceMemoryGuardConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_MEMORY_GUARD_REPORT_CONFIG_VERSION
        ),
        "min_pass_fresh_memory_score": d("0.750000"),
        "min_watch_fresh_memory_score": d("0.500000"),
        "max_pass_source_overlap_ratio": d("0.150000"),
        "max_watch_source_overlap_ratio": d("0.350000"),
        "min_pass_distinct_source_count": d("3.000000"),
        "min_watch_distinct_source_count": d("2.000000"),
        "max_pass_memory_age_seconds": d("86400.000000"),
        "max_watch_memory_age_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return ResearchStrategyClaimSourceMemoryGuardConfig(**values)


def input_row(
    claim_digest: str = HEX_A,
    source_memory_digest: str = HEX_D,
    *,
    observed_at: datetime | None = None,
    fresh_memory_score: Decimal = d("0.900000"),
    source_overlap_ratio: Decimal = d("0.050000"),
    distinct_source_count: Decimal = d("4.000000"),
    memory_age_seconds: Decimal = d("21600.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyClaimSourceMemoryGuardInput:
    return ResearchStrategyClaimSourceMemoryGuardInput(
        claim_digest=claim_digest,
        source_memory_digest=source_memory_digest,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=5)
        ),
        fresh_memory_score=fresh_memory_score,
        source_overlap_ratio=source_overlap_ratio,
        distinct_source_count=distinct_source_count,
        memory_age_seconds=memory_age_seconds,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategyClaimSourceMemoryGuardInput,
    cfg: ResearchStrategyClaimSourceMemoryGuardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyClaimSourceMemoryGuardReport:
    return build_research_strategy_claim_source_memory_guard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_payload_with_valid_digest() -> None:
    guard_report = report()
    payload = research_strategy_claim_source_memory_guard_report_public_payload(
        guard_report,
    )

    assert type(guard_report) is ResearchStrategyClaimSourceMemoryGuardReport
    assert is_dataclass(guard_report)
    assert CLAIM_SOURCE_MEMORY_GUARD_STATUSES == ("pass", "watch", "block")
    assert guard_report.generated_at == GENERATED_AT
    assert (
        guard_report.config_version
        == "research-strategy-claim-source-memory-guard-report-v0"
    )
    assert guard_report.input_count == ZERO
    assert guard_report.pass_count == ZERO
    assert guard_report.watch_count == ZERO
    assert guard_report.block_count == ZERO
    assert guard_report.average_memory_guard_score is None
    assert guard_report.min_fresh_memory_score == ZERO
    assert guard_report.max_source_overlap_ratio == ZERO
    assert guard_report.max_stale_memory_risk == ZERO
    assert guard_report.min_distinct_source_count == ZERO
    assert guard_report.status == "block"
    assert guard_report.reason_codes == ("no_claim_source_memory_inputs",)
    assert guard_report.reason_code_counts == (
        ResearchStrategyClaimSourceMemoryGuardReasonCodeCount(
            reason_code="no_claim_source_memory_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert guard_report.rows == ()
    assert guard_report.paper_only is True
    assert guard_report.report_only is True
    assert guard_report.readonly is True
    assert payload["validation_digest"] == guard_report.validation_digest
    assert validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        payload,
    )


def test_rows_statuses_scores_reason_counts_are_deterministic() -> None:
    guard_report = report(
        input_row(
            HEX_B,
            HEX_C,
            fresh_memory_score=d("0.700000"),
            source_overlap_ratio=d("0.250000"),
            distinct_source_count=d("3.000000"),
            memory_age_seconds=d("172800.000000"),
        ),
        input_row(
            HEX_A,
            HEX_D,
            reason_codes=("manual_check_complete",),
        ),
        input_row(
            HEX_C,
            HEX_B,
            fresh_memory_score=d("0.420000"),
            source_overlap_ratio=d("0.600000"),
            distinct_source_count=d("1.000000"),
            memory_age_seconds=d("400000.000000"),
            reason_codes=("analyst_escalated",),
        ),
    )

    assert guard_report.status == "block"
    assert guard_report.input_count == d("3.000000")
    assert guard_report.pass_count == d("1.000000")
    assert guard_report.watch_count == d("1.000000")
    assert guard_report.block_count == d("1.000000")
    assert guard_report.average_memory_guard_score == d("0.641944")
    assert guard_report.min_fresh_memory_score == d("0.420000")
    assert guard_report.max_source_overlap_ratio == d("0.600000")
    assert guard_report.max_stale_memory_risk == d("1.000000")
    assert guard_report.min_distinct_source_count == d("1.000000")
    assert tuple(row.claim_digest for row in guard_report.rows) == (HEX_C, HEX_B, HEX_A)
    assert tuple(row.status for row in guard_report.rows) == ("block", "watch", "pass")

    block_row, watch_row, pass_row = guard_report.rows
    assert type(block_row) is ResearchStrategyClaimSourceMemoryGuardRow
    assert block_row.memory_guard_score == d("0.288333")
    assert block_row.stale_memory_risk == d("1.000000")
    assert block_row.source_coverage_score == d("0.333333")
    assert block_row.reason_codes == (
        "claim_source_memory_guard_block",
        "distinct_source_count_block",
        "fresh_memory_score_block",
        "input_analyst_escalated",
        "manual_review_claim_source_memory_block",
        "memory_age_block",
        "source_overlap_ratio_block",
    )
    assert watch_row.memory_guard_score == d("0.695833")
    assert watch_row.reason_codes == (
        "claim_source_memory_guard_watch",
        "distinct_source_count_pass",
        "fresh_memory_score_watch",
        "manual_review_claim_source_memory_watch",
        "memory_age_watch",
        "source_overlap_ratio_watch",
    )
    assert pass_row.memory_guard_score == d("0.941667")
    assert pass_row.reason_codes == (
        "claim_source_memory_guard_pass",
        "distinct_source_count_pass",
        "fresh_memory_score_pass",
        "input_manual_check_complete",
        "manual_review_claim_source_memory_pass",
        "memory_age_pass",
        "source_overlap_ratio_pass",
    )
    assert guard_report.reason_codes == (
        "claim_source_memory_guard_block",
        "fresh_memory_score_block",
        "source_overlap_ratio_block",
        "distinct_source_count_block",
        "memory_age_block",
        "fresh_memory_score_watch",
        "source_overlap_ratio_watch",
        "memory_age_watch",
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in guard_report.reason_code_counts
    ) == tuple(
        sorted(
            (
                ("claim_source_memory_guard_block", d("1.000000")),
                ("claim_source_memory_guard_pass", d("1.000000")),
                ("claim_source_memory_guard_watch", d("1.000000")),
                ("distinct_source_count_block", d("1.000000")),
                ("distinct_source_count_pass", d("2.000000")),
                ("fresh_memory_score_block", d("1.000000")),
                ("fresh_memory_score_pass", d("1.000000")),
                ("fresh_memory_score_watch", d("1.000000")),
                ("input_analyst_escalated", d("1.000000")),
                ("input_manual_check_complete", d("1.000000")),
                ("manual_review_claim_source_memory_block", d("1.000000")),
                ("manual_review_claim_source_memory_pass", d("1.000000")),
                ("manual_review_claim_source_memory_watch", d("1.000000")),
                ("memory_age_block", d("1.000000")),
                ("memory_age_pass", d("1.000000")),
                ("memory_age_watch", d("1.000000")),
                ("source_overlap_ratio_block", d("1.000000")),
                ("source_overlap_ratio_pass", d("1.000000")),
                ("source_overlap_ratio_watch", d("1.000000")),
            ),
        ),
    )


@dataclass(frozen=True)
class ExternalInputEnvelope:
    claim_digest: str
    source_memory_digest: str
    observed_at: datetime
    fresh_memory_score: Decimal
    source_overlap_ratio: Decimal
    distinct_source_count: Decimal
    memory_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    original_candidate: str
    market_slug: str
    source_url: str
    source_text: str
    dsn: str
    table_name: str
    token_value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_public_payload_is_deterministic_decimal_strings_redacted_and_sha256_validated() -> None:
    private = ExternalInputEnvelope(
        claim_digest=HEX_A,
        source_memory_digest=HEX_D,
        observed_at=GENERATED_AT - timedelta(seconds=1),
        fresh_memory_score=d("0.900000"),
        source_overlap_ratio=d("0.050000"),
        distinct_source_count=d("4.000000"),
        memory_age_seconds=d("21600.000000"),
        reason_codes=("zeta", "alpha"),
        original_candidate="raw-candidate-should-stay-private",
        market_slug="private-market-slug",
        source_url="https://example.test/private",
        source_text="private source body text",
        dsn="postgres://hidden",
        table_name="private table",
        token_value="secret-token",
    )
    first = build_research_strategy_claim_source_memory_guard_report(
        (
            input_row(HEX_B, HEX_C),
            private,
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )
    second = build_research_strategy_claim_source_memory_guard_report(
        (
            replace(private, reason_codes=("alpha", "zeta")),
            input_row(HEX_B, HEX_C),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )
    first_payload = research_strategy_claim_source_memory_guard_report_public_payload(
        first,
    )
    second_payload = research_strategy_claim_source_memory_guard_report_public_payload(
        second,
    )
    payload_without_digest = dict(first_payload)
    validation_digest = payload_without_digest.pop("validation_digest")
    encoded_body = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    encoded_payload = json.dumps(first_payload, ensure_ascii=True, sort_keys=True)

    assert first_payload == second_payload
    assert research_strategy_claim_source_memory_guard_report_digest(first) == (
        research_strategy_claim_source_memory_guard_report_digest(second)
    )
    assert len(research_strategy_claim_source_memory_guard_report_digest(first)) == 64
    assert validation_digest == hashlib.sha256(
        encoded_body.encode("utf-8"),
    ).hexdigest()
    assert validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        first_payload,
    )
    assert first_payload["rows"][0]["fresh_memory_score"] == "0.900000"
    assert first_payload["rows"][0]["distinct_source_count"] == "4.000000"
    assert not any(type(value) in {int, float} for value in _walk(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk(first_payload))
    for unsafe in (
        "raw-candidate-should-stay-private",
        "private-market-slug",
        "https://example.test/private",
        "private source body text",
        "postgres://hidden",
        "private table",
        "secret-token",
    ):
        assert unsafe not in encoded_payload
    for unsafe_key in (
        "original_candidate",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    ):
        assert unsafe_key not in encoded_payload

    tampered = dict(first_payload)
    tampered["max_source_overlap_ratio"] = "0.999999"
    assert not validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        tampered,
    )


def test_validation_rejects_non_decimal_values_times_flags_and_inconsistent_rows() -> None:
    guard_report = report(input_row())

    for value in (
        config(),
        input_row(),
        guard_report,
        *guard_report.rows,
        *guard_report.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "validation_digest",
            }:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_ratio",
                    "_seconds",
                    "_risk",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        guard_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        guard_report.rows[0].memory_guard_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="min_pass_fresh_memory_score"):
        config(min_pass_fresh_memory_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_pass_source_overlap_ratio"):
        config(max_pass_source_overlap_ratio=DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="min_watch_distinct_source_count"):
        config(
            min_pass_distinct_source_count=d("2.000000"),
            min_watch_distinct_source_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="claim_digest"):
        input_row(claim_digest=HEX_A.upper())
    with pytest.raises(ValueError, match="source_memory_digest"):
        input_row(source_memory_digest="not-a-digest")
    with pytest.raises(ValueError, match="fresh_memory_score"):
        input_row(fresh_memory_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_overlap_ratio"):
        input_row(source_overlap_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="distinct_source_count"):
        input_row(distinct_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=DatetimeSubclass(2026, 7, 9, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(guard_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(guard_report.rows[0], status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(guard_report, status="watch")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(guard_report, validation_digest="0" * 64)


def test_public_dataclasses_are_frozen_slotted_final_and_exact() -> None:
    classes = (
        ResearchStrategyClaimSourceMemoryGuardConfig,
        ResearchStrategyClaimSourceMemoryGuardInput,
        ResearchStrategyClaimSourceMemoryGuardRow,
        ResearchStrategyClaimSourceMemoryGuardReasonCodeCount,
        ResearchStrategyClaimSourceMemoryGuardReport,
    )

    for cls in classes:
        assert getattr(cls, "__final__", False) is True
        assert hasattr(cls, "__slots__")
        assert "__dict__" not in cls.__slots__
        with pytest.raises(TypeError):
            type(f"{cls.__name__}Subclass", (cls,), {})


def test_decimal_math_is_context_independent_and_signed_zero_is_rejected() -> None:
    expected = report(input_row())

    with localcontext() as context:
        context.prec = 4
        context.rounding = ROUND_DOWN
        constrained = report(input_row())

    assert constrained == expected
    assert constrained.validation_digest == expected.validation_digest

    with pytest.raises(ValueError, match="min_pass_fresh_memory_score"):
        config(min_pass_fresh_memory_score=d("-0.000000"))
    with pytest.raises(ValueError, match="fresh_memory_score"):
        input_row(fresh_memory_score=d("-0.000000"))


def test_build_revalidates_mutated_config_and_input_objects() -> None:
    forged_config = config()
    object.__setattr__(forged_config, "min_watch_fresh_memory_score", d("0.900000"))
    with pytest.raises(ValueError, match="min_watch_fresh_memory_score"):
        report(input_row(), cfg=forged_config)

    forged_input = input_row()
    object.__setattr__(forged_input, "reason_codes", ["forged_reason"])
    with pytest.raises(ValueError, match="reason_codes"):
        report(forged_input)


def test_digest_revalidates_mutated_rows_and_re_signed_payloads() -> None:
    guard_report = report(input_row())
    object.__setattr__(guard_report.rows[0], "memory_guard_score", d("0.100000"))

    with pytest.raises(ValueError, match="memory_guard_score"):
        research_strategy_claim_source_memory_guard_report_digest(guard_report)

    valid_payload = research_strategy_claim_source_memory_guard_report_public_payload(
        report(input_row()),
    )
    forged_row = json.loads(json.dumps(valid_payload))
    forged_row["rows"][0]["memory_guard_score"] = "0.100000"
    _resign(forged_row)
    assert not validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        forged_row,
    )


def test_re_signed_payloads_require_exact_canonical_schemas() -> None:
    payload = research_strategy_claim_source_memory_guard_report_public_payload(
        report(input_row()),
    )

    extra_top_level = json.loads(json.dumps(payload))
    extra_top_level["unexpected"] = "value"
    _resign(extra_top_level)
    assert not validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        extra_top_level,
    )

    extra_nested = json.loads(json.dumps(payload))
    extra_nested["rows"][0]["unexpected"] = "value"
    _resign(extra_nested)
    assert not validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        extra_nested,
    )

    reordered = dict(reversed(tuple(payload.items())))
    _resign(reordered)
    assert not validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        reordered,
    )


def test_threshold_boundaries_are_inclusive_until_the_next_status() -> None:
    watch = input_row(
        fresh_memory_score=d("0.500000"),
        source_overlap_ratio=d("0.350000"),
        distinct_source_count=d("2.000000"),
        memory_age_seconds=d("259200.000000"),
    )
    assert report(watch).rows[0].status == "watch"

    pass_row = input_row(
        fresh_memory_score=d("0.750000"),
        source_overlap_ratio=d("0.150000"),
        distinct_source_count=d("3.000000"),
        memory_age_seconds=d("86400.000000"),
    )
    assert report(pass_row).rows[0].status == "pass"

    block = input_row(memory_age_seconds=d("259200.000001"))
    assert report(block).rows[0].status == "block"


def test_equal_status_and_digest_rows_have_deterministic_tie_breakers() -> None:
    earlier = input_row(
        observed_at=GENERATED_AT - timedelta(minutes=10),
        fresh_memory_score=d("0.800000"),
    )
    later = input_row(
        observed_at=GENERATED_AT - timedelta(minutes=5),
        fresh_memory_score=d("0.900000"),
    )

    first = research_strategy_claim_source_memory_guard_report_public_payload(
        report(earlier, later),
    )
    second = research_strategy_claim_source_memory_guard_report_public_payload(
        report(later, earlier),
    )

    assert first == second


def test_owned_module_has_no_execution_or_private_surface_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_claim_source_memory_guard_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "database",
        "db",
        "network",
        "wallet",
        "auth",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "market_slug",
        "source_url",
        "source_text",
        "candidate",
        "dsn",
        "table",
        "token",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        values.extend(value.keys())
        for item_value in value.values():
            values.extend(_walk(item_value))
    elif isinstance(value, list):
        for item_value in value:
            values.extend(_walk(item_value))
    else:
        values.append(value)
    return tuple(values)


def _resign(payload: dict[str, object]) -> None:
    body = dict(payload)
    body.pop("validation_digest", None)
    encoded = json.dumps(body, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    payload["validation_digest"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
