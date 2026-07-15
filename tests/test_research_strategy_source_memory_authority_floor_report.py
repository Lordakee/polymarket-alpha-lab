from __future__ import annotations

import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_source_memory_authority_floor_report import (
    DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION,
    SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES,
    ResearchStrategySourceMemoryAuthorityFloorConfig,
    ResearchStrategySourceMemoryAuthorityFloorInput,
    ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount,
    ResearchStrategySourceMemoryAuthorityFloorReport,
    ResearchStrategySourceMemoryAuthorityFloorRow,
    build_research_strategy_source_memory_authority_floor_report,
    research_strategy_source_memory_authority_floor_report_digest,
    research_strategy_source_memory_authority_floor_report_payload,
    validate_research_strategy_source_memory_authority_floor_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategySourceMemoryAuthorityFloorConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
        ),
        "min_pass_memory_signal_strength": d("0.750000"),
        "min_watch_memory_signal_strength": d("0.500000"),
        "min_pass_authority_score": d("0.800000"),
        "min_watch_authority_score": d("0.550000"),
        "max_pass_memory_age_seconds": d("86400.000000"),
        "max_watch_memory_age_seconds": d("259200.000000"),
        "max_pass_contradiction_pressure": d("0.150000"),
        "max_watch_contradiction_pressure": d("0.350000"),
        "min_pass_corroboration_count": d("2.000000"),
        "min_watch_corroboration_count": d("1.000000"),
        "memory_signal_weight": d("0.300000"),
        "authority_score_weight": d("0.300000"),
        "freshness_weight": d("0.150000"),
        "corroboration_weight": d("0.150000"),
        "contradiction_relief_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategySourceMemoryAuthorityFloorConfig(**values)


def input_row(
    private_candidate_ref: str = "candidate://secret-alpha?token=not-public",
    public_research_bucket: str = "resolution-memory",
    *,
    memory_signal_strength: Decimal = d("0.880000"),
    authority_score: Decimal = d("0.900000"),
    memory_age_seconds: Decimal = d("21600.000000"),
    corroboration_count: Decimal = d("3.000000"),
    contradiction_pressure: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategySourceMemoryAuthorityFloorInput:
    return ResearchStrategySourceMemoryAuthorityFloorInput(
        private_candidate_ref=private_candidate_ref,
        public_research_bucket=public_research_bucket,
        memory_signal_strength=memory_signal_strength,
        authority_score=authority_score,
        memory_age_seconds=memory_age_seconds,
        corroboration_count=corroboration_count,
        contradiction_pressure=contradiction_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategySourceMemoryAuthorityFloorInput,
    cfg: ResearchStrategySourceMemoryAuthorityFloorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySourceMemoryAuthorityFloorReport:
    return build_research_strategy_source_memory_authority_floor_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    import hashlib

    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    floor_report = report()

    assert type(floor_report) is ResearchStrategySourceMemoryAuthorityFloorReport
    assert is_dataclass(floor_report)
    assert SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES == ("pass", "watch", "block")
    assert floor_report.generated_at == GENERATED_AT
    assert (
        floor_report.config_version
        == "research-strategy-source-memory-authority-floor-report-v0"
    )
    assert floor_report.input_count == ZERO
    assert floor_report.pass_count == ZERO
    assert floor_report.watch_count == ZERO
    assert floor_report.block_count == ZERO
    assert floor_report.average_authority_floor_score is None
    assert floor_report.min_memory_signal_strength == ZERO
    assert floor_report.min_authority_score == ZERO
    assert floor_report.max_memory_age_seconds == ZERO
    assert floor_report.max_contradiction_pressure == ZERO
    assert floor_report.status == "block"
    assert floor_report.reason_codes == ("no_source_memory_authority_inputs",)
    assert floor_report.reason_code_counts == (
        ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount(
            reason_code="no_source_memory_authority_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert floor_report.rows == ()
    assert floor_report.paper_only is True
    assert floor_report.report_only is True
    assert floor_report.readonly is True

    payload = research_strategy_source_memory_authority_floor_report_payload(
        floor_report,
    )
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert research_strategy_source_memory_authority_floor_report_digest(
        floor_report,
    ) == payload["derived_validation_digest"]
    assert validate_research_strategy_source_memory_authority_floor_report_payload(
        payload,
    )
    assert_no_public_numbers(payload)
    assert_no_forbidden_public_surface(payload)


def test_source_memory_authority_floor_scores_pass_watch_and_block_rows() -> None:
    floor_report = report(
        input_row(
            "candidate://secret-watch?source_url=https://example.invalid",
            "resolution-memory",
            memory_signal_strength=d("0.650000"),
            authority_score=d("0.760000"),
            memory_age_seconds=d("172800.000000"),
            corroboration_count=d("1.000000"),
            contradiction_pressure=d("0.250000"),
        ),
        input_row(
            "candidate://secret-block?dsn=postgres://hidden/table",
            "breaking-update-memory",
            memory_signal_strength=d("0.420000"),
            authority_score=d("0.400000"),
            memory_age_seconds=d("400000.000000"),
            corroboration_count=d("0.000000"),
            contradiction_pressure=d("0.600000"),
            reason_codes=("manual_escalation",),
        ),
        input_row(
            "candidate://secret-pass?raw_text=do-not-leak",
            "resolution-memory",
            reason_codes=("analyst_checked",),
        ),
    )

    assert floor_report.input_count == d("3.000000")
    assert floor_report.pass_count == d("1.000000")
    assert floor_report.watch_count == d("1.000000")
    assert floor_report.block_count == d("1.000000")
    assert floor_report.average_authority_floor_score == d("0.608500")
    assert floor_report.min_memory_signal_strength == d("0.420000")
    assert floor_report.min_authority_score == d("0.400000")
    assert floor_report.max_memory_age_seconds == d("400000.000000")
    assert floor_report.max_contradiction_pressure == d("0.600000")
    assert floor_report.status == "block"
    assert floor_report.reason_codes == (
        "source_memory_authority_floor_block",
        "memory_signal_strength_block",
        "authority_score_block",
        "memory_age_block",
        "corroboration_count_block",
        "contradiction_pressure_block",
        "source_memory_authority_floor_watch",
        "memory_signal_strength_watch",
        "authority_score_watch",
        "memory_age_watch",
        "corroboration_count_watch",
        "contradiction_pressure_watch",
    )

    block_row, pass_row, watch_row = floor_report.rows
    assert type(block_row) is ResearchStrategySourceMemoryAuthorityFloorRow
    assert tuple(row.public_research_bucket for row in floor_report.rows) == (
        "breaking-update-memory",
        "resolution-memory",
        "resolution-memory",
    )
    assert block_row.authority_floor_score == d("0.286000")
    assert block_row.freshness_score == ZERO
    assert block_row.corroboration_score == ZERO
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "source_memory_authority_floor_block",
        "memory_signal_strength_block",
        "authority_score_block",
        "memory_age_block",
        "corroboration_count_block",
        "contradiction_pressure_block",
        "input_manual_escalation",
    )
    assert pass_row.authority_floor_score == d("0.916500")
    assert pass_row.freshness_score == d("0.916667")
    assert pass_row.corroboration_score == d("1.000000")
    assert pass_row.status == "pass"
    assert "source_memory_authority_floor_pass" in pass_row.reason_codes
    assert "input_analyst_checked" in pass_row.reason_codes
    assert watch_row.authority_floor_score == d("0.623000")
    assert watch_row.freshness_score == d("0.333333")
    assert watch_row.corroboration_score == d("0.500000")
    assert watch_row.status == "watch"
    assert "memory_signal_strength_watch" in watch_row.reason_codes
    assert "authority_score_watch" in watch_row.reason_codes


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    first = report(
        input_row(
            "candidate://secret-z?token=hidden",
            "z-bucket",
            reason_codes=("zeta", "alpha"),
        ),
        input_row("candidate://secret-a?market=hidden", "a-bucket"),
    )
    second = report(
        input_row("candidate://secret-a?market=hidden", "a-bucket"),
        input_row(
            "candidate://secret-z?token=hidden",
            "z-bucket",
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = research_strategy_source_memory_authority_floor_report_payload(first)
    second_payload = research_strategy_source_memory_authority_floor_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert research_strategy_source_memory_authority_floor_report_digest(first) == (
        research_strategy_source_memory_authority_floor_report_digest(second)
    )
    assert len(research_strategy_source_memory_authority_floor_report_digest(first)) == 64
    int(research_strategy_source_memory_authority_floor_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first_payload["rows"][0]["row_label"].startswith(
        "redacted-source-memory-authority-floor-",
    )
    assert first_payload["rows"][0]["authority_floor_score"] == "0.916500"
    assert first_payload["rows"][0]["corroboration_count"] == "3.000000"
    assert ": 0." not in encoded
    assert "candidate://secret" not in encoded
    assert "token=hidden" not in encoded
    assert "market=hidden" not in encoded
    assert_no_public_numbers(first_payload)
    assert_no_forbidden_public_surface(first_payload)

    tampered = replace(first)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_source_memory_authority_floor_report_payload(tampered)

    unsigned = dict(first_payload)
    unsigned["status"] = "block"
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        unsigned,
    )


def test_resigned_payload_requires_exact_schema_and_canonical_scalars() -> None:
    payload = research_strategy_source_memory_authority_floor_report_payload(
        report(input_row()),
    )

    extra_top_level = dict(payload, unexpected="value")
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(extra_top_level),
    )

    missing_top_level = dict(payload)
    missing_top_level.pop("rows")
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(missing_top_level),
    )

    extra_row = dict(payload)
    extra_row["rows"] = [dict(payload["rows"][0], unexpected="value")]  # type: ignore[index]
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(extra_row),
    )

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["input_count"] = "1.0"
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(noncanonical_decimal),
    )

    noncanonical_datetime = dict(payload)
    noncanonical_datetime["generated_at"] = "2026-07-09T12:00:00Z"
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(noncanonical_datetime),
    )


def test_typed_and_resigned_payloads_revalidate_derived_fields() -> None:
    populated = report(input_row())

    tampered_report = replace(populated)
    object.__setattr__(tampered_report, "pass_count", d("0.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        research_strategy_source_memory_authority_floor_report_payload(
            tampered_report,
        )

    payload = research_strategy_source_memory_authority_floor_report_payload(populated)
    forged_row = dict(payload)
    forged_row["rows"] = [  # type: ignore[index]
        dict(payload["rows"][0], authority_floor_score="0.000000"),  # type: ignore[index]
    ]
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(forged_row),
    )

    forged_counts = dict(payload)
    forged_counts["pass_count"] = "0.000000"
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(forged_counts),
    )


def test_signed_zero_is_rejected_and_public_dataclasses_are_slotted() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        config(min_pass_memory_signal_strength=d("-0.000000"))
    with pytest.raises(ValueError, match="signed zero"):
        input_row(memory_age_seconds=d("-0.000000"))

    payload = research_strategy_source_memory_authority_floor_report_payload(
        report(input_row()),
    )
    signed_zero = dict(payload, input_count="-0.000000")
    assert not validate_research_strategy_source_memory_authority_floor_report_payload(
        resign_payload(signed_zero),
    )

    tampered_report = replace(report())
    object.__setattr__(tampered_report, "input_count", d("-0.000000"))
    with pytest.raises(ValueError, match="signed zero"):
        research_strategy_source_memory_authority_floor_report_payload(
            tampered_report,
        )

    instances = (
        config(),
        input_row(),
        report(input_row()).rows[0],
        report(input_row()).reason_code_counts[0],
        report(input_row()),
    )
    classes = tuple(type(instance) for instance in instances)
    for cls, instance in zip(classes, instances, strict=True):
        assert hasattr(cls, "__slots__")
        assert "__dict__" not in cls.__slots__
        assert not hasattr(instance, "__dict__")


def test_builder_revalidates_mutated_config_and_input_instances() -> None:
    mutated_config = config()
    object.__setattr__(mutated_config, "min_pass_memory_signal_strength", d("2.000000"))
    with pytest.raises(ValueError, match="min_pass_memory_signal_strength"):
        report(input_row(), cfg=mutated_config)

    mutated_input = input_row()
    object.__setattr__(mutated_input, "private_candidate_ref", "")
    with pytest.raises(ValueError, match="private_candidate_ref"):
        report(mutated_input)


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_report() -> None:
    populated = report(input_row())

    for value in (
        config(),
        input_row(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_strength",
                    "_seconds",
                    "_pressure",
                    "_ratio",
                    "_weight",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].authority_floor_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_signal_weight"):
        config(memory_signal_weight=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score_weight"):
        config(authority_score_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="private_candidate_ref"):
        input_row("")
    with pytest.raises(ValueError, match="public_research_bucket"):
        input_row(public_research_bucket="https://example.invalid/raw")
    with pytest.raises(ValueError, match="memory_signal_strength"):
        input_row(memory_signal_strength=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_count"):
        input_row(corroboration_count=d("1.500000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        input_row(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_effectful_trading_or_raw_public_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_source_memory_authority_floor_report.py"
    )
    text = module_path.read_text(encoding="utf-8").casefold()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "wallet",
        "private_key",
        "authorization",
        "bearer",
        "api_key",
        "place_order",
        "submit_order",
        "live_trading",
        "position_size",
        "sizing",
        "recommendation",
    )
    forbidden_word_patterns = (
        r"\bdb\b",
        r"\bdatabase\b",
        r"\bnetwork\b",
        r"\bauth\b",
        r"\border\b",
        r"\blive\s+trading\b",
        r"\brecommend\b",
    )

    assert all(term not in text for term in forbidden_terms)
    assert not any(re.search(pattern, text) for pattern in forbidden_word_patterns)


def assert_no_public_numbers(value: object) -> None:
    if type(value) in {int, float, Decimal}:
        raise AssertionError(f"public payload leaked raw numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def assert_no_forbidden_public_surface(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    forbidden_fragments = (
        "raw_candidate",
        "candidate://",
        "candidate_ref",
        "market_id",
        "market_slug",
        "market=hidden",
        "source_url",
        "source_text",
        "raw_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "postgres://",
        "table",
        "token",
        "wallet",
        "private_key",
    )
    assert all(fragment not in rendered for fragment in forbidden_fragments)
