from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, Inexact, ROUND_DOWN, localcontext
from hashlib import sha256
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_specialist_source_memory_decay_report import (
    ResearchStrategySpecialistSourceMemoryDecayConfig,
    ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount,
    ResearchStrategySpecialistSourceMemoryDecayReport,
    ResearchStrategySpecialistSourceMemoryDecayRow,
    ResearchStrategySpecialistSourceMemoryObservation,
    build_research_strategy_specialist_source_memory_decay_report,
    research_strategy_specialist_source_memory_decay_report_digest,
    research_strategy_specialist_source_memory_decay_report_payload,
    validate_research_strategy_specialist_source_memory_decay_report_digest,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySpecialistSourceMemoryDecayConfig:
    values = {
        "config_version": "research-strategy-specialist-source-memory-decay-report-v0",
        "fresh_memory_age_seconds": d("3600"),
        "stale_memory_age_seconds": d("86400"),
        "watch_decay_score": d("0.300000"),
        "block_decay_score": d("0.650000"),
        "recency_weight": d("0.650000"),
        "recall_weight": d("0.350000"),
        "contradiction_penalty": d("0.200000"),
        "min_recall_reliability_score": d("0.700000"),
    }
    values.update(overrides)
    return ResearchStrategySpecialistSourceMemoryDecayConfig(**values)


def observation(
    index: int,
    *,
    source_memory_id: str | None = None,
    candidate_id: str | None = None,
    market_id: str | None = None,
    market_slug: str | None = None,
    market_question: str | None = None,
    source_url: str | None = None,
    source_text: str | None = None,
    memory_observed_at: datetime | None = None,
    last_recalled_at: datetime | None = None,
    successful_recall_count: Decimal = d("4"),
    failed_recall_count: Decimal = d("0"),
    contradiction_count: Decimal = d("0"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategySpecialistSourceMemoryObservation:
    return ResearchStrategySpecialistSourceMemoryObservation(
        source_memory_id=source_memory_id or f"source-memory-private-{index:03d}",
        candidate_id=candidate_id or f"candidate-private-{index:03d}",
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_url=source_url,
        source_text=source_text,
        memory_observed_at=(
            memory_observed_at
            if memory_observed_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        last_recalled_at=last_recalled_at,
        successful_recall_count=successful_recall_count,
        failed_recall_count=failed_recall_count,
        contradiction_count=contradiction_count,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategySpecialistSourceMemoryDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySpecialistSourceMemoryDecayReport:
    return build_research_strategy_specialist_source_memory_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_status_report_only_payload() -> None:
    decay_report = report(())

    assert type(decay_report) is ResearchStrategySpecialistSourceMemoryDecayReport
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.config_version == (
        "research-strategy-specialist-source-memory-decay-report-v0"
    )
    assert decay_report.memory_count == d("0")
    assert decay_report.pass_count == d("0")
    assert decay_report.watch_count == d("0")
    assert decay_report.block_count == d("0")
    assert decay_report.average_decay_score is None
    assert decay_report.status == "block"
    assert decay_report.reason_codes == ("no_source_memory_observations",)
    assert decay_report.reason_code_counts == (
        ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount(
            reason_code="no_source_memory_observations",
            count=d("1"),
        ),
    )
    assert decay_report.rows == ()
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True


def test_fresh_recalled_memory_passes_with_decimal_only_scores() -> None:
    decay_report = report((observation(1),))
    row = decay_report.rows[0]

    assert type(row) is ResearchStrategySpecialistSourceMemoryDecayRow
    assert decay_report.status == "pass"
    assert decay_report.memory_count == d("1")
    assert decay_report.pass_count == d("1")
    assert decay_report.watch_count == d("0")
    assert decay_report.block_count == d("0")
    assert decay_report.average_decay_score == d("0.000000")
    assert row.memory_alias == "memory-001"
    assert row.last_memory_touch_at == GENERATED_AT - timedelta(minutes=30)
    assert row.memory_age_seconds == d("1800")
    assert row.successful_recall_count == d("4")
    assert row.failed_recall_count == d("0")
    assert row.contradiction_count == d("0")
    assert row.recall_observation_count == d("4")
    assert row.recency_retention_score == d("1.000000")
    assert row.recall_reliability_score == d("1.000000")
    assert row.contradiction_penalty_score == d("0.000000")
    assert row.memory_retention_score == d("1.000000")
    assert row.decay_score == d("0.000000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "fresh_source_memory",
        "recall_reliability_pass",
        "source_memory_decay_pass",
    )


def test_aging_and_stale_memory_drive_watch_and_block_statuses() -> None:
    decay_report = report(
        (
            observation(
                1,
                memory_observed_at=GENERATED_AT - timedelta(hours=12),
                successful_recall_count=d("2"),
                failed_recall_count=d("1"),
                reason_codes=("manually_reviewed",),
            ),
            observation(
                2,
                memory_observed_at=GENERATED_AT - timedelta(days=2),
                successful_recall_count=d("0"),
                failed_recall_count=d("2"),
                contradiction_count=d("1"),
            ),
        ),
    )

    rows_by_status = {row.status: row for row in decay_report.rows}

    assert decay_report.status == "block"
    assert decay_report.memory_count == d("2")
    assert decay_report.pass_count == d("0")
    assert decay_report.watch_count == d("1")
    assert decay_report.block_count == d("1")
    assert decay_report.average_decay_score == d("0.720834")

    watch_row = rows_by_status["watch"]
    assert watch_row.memory_age_seconds == d("43200")
    assert watch_row.recency_retention_score == d("0.500000")
    assert watch_row.recall_reliability_score == d("0.666667")
    assert watch_row.memory_retention_score == d("0.558333")
    assert watch_row.decay_score == d("0.441667")
    assert watch_row.reason_codes == (
        "aging_source_memory",
        "input_manually_reviewed",
        "recall_reliability_weak",
        "source_memory_decay_watch",
    )

    block_row = rows_by_status["block"]
    assert block_row.memory_age_seconds == d("172800")
    assert block_row.recency_retention_score == d("0.000000")
    assert block_row.recall_reliability_score == d("0.000000")
    assert block_row.contradiction_penalty_score == d("0.200000")
    assert block_row.memory_retention_score == d("0.000000")
    assert block_row.decay_score == d("1.000000")
    assert block_row.reason_codes == (
        "contradictions_present",
        "recall_reliability_weak",
        "source_memory_decay_block",
        "stale_source_memory",
    )


def test_payload_and_digest_are_deterministic_and_redact_private_source_fields() -> None:
    raw_values = {
        "candidate_id": "candidate-secret-123",
        "market_id": "market-secret-456",
        "market_slug": "will-secret-market-resolve",
        "market_question": "Will the hidden question resolve yes?",
        "source_url": "https://secret.example.test/source",
        "source_text": "raw transcript should never appear",
    }
    decay_report = report((observation(9, **raw_values),))

    payload = research_strategy_specialist_source_memory_decay_report_payload(
        decay_report,
    )
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    encoded = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":"))
    digest = research_strategy_specialist_source_memory_decay_report_digest(decay_report)

    assert payload["rows"][0]["memory_alias"] == "memory-001"
    assert payload["rows"][0]["decay_score"] == "0.000000"
    assert digest == sha256(encoded.encode("utf-8")).hexdigest()
    assert (
        validate_research_strategy_specialist_source_memory_decay_report_digest(
            decay_report,
            digest,
        )
        == digest
    )
    with pytest.raises(ValueError, match="digest"):
        validate_research_strategy_specialist_source_memory_decay_report_digest(
            decay_report,
            "0" * 64,
        )
    with pytest.raises(ValueError, match="sha256"):
        validate_research_strategy_specialist_source_memory_decay_report_digest(
            decay_report,
            "not-a-digest",
        )

    for forbidden_value in raw_values.values():
        assert forbidden_value not in encoded
    for forbidden_key in raw_values:
        assert forbidden_key not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_validation_rejects_bad_types_future_times_unsafe_reasons_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_decay_score"):
        config(watch_decay_score=d("0.700000"))
    with pytest.raises(ValueError, match="recency_weight"):
        config(recency_weight=d("0.500000"))
    with pytest.raises(ValueError, match="recall_weight"):
        config(recall_weight=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_penalty"):
        config(contradiction_penalty=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="memory_observed_at"):
        observation(1, memory_observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="memory_observed_at"):
        report((observation(1, memory_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_memory_id"):
        observation(1, source_memory_id=" private-memory")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("token_surface",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    decay_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        decay_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decay_report.rows[0].decay_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="decay_score"):
        replace(decay_report.rows[0], decay_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(decay_report, status="block")


def test_owned_module_has_no_io_execution_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_specialist_source_memory_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
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
        "auth",
        "wallet",
        "order",
        "trade",
        "recommend",
        "position_size",
        "live_trading",
    )

    assert all(term not in source for term in forbidden_terms)


def test_public_dataclasses_are_frozen_slotted_final_and_exact() -> None:
    public_types = (
        ResearchStrategySpecialistSourceMemoryDecayConfig,
        ResearchStrategySpecialistSourceMemoryObservation,
        ResearchStrategySpecialistSourceMemoryDecayRow,
        ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount,
        ResearchStrategySpecialistSourceMemoryDecayReport,
    )

    for public_type in public_types:
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        assert getattr(public_type, "__final__", False) is True
        assert hasattr(public_type, "__slots__")
        with pytest.raises(TypeError):
            type(f"Invalid{public_type.__name__}", (public_type,), {})

    value = observation(1)
    assert not hasattr(value, "__dict__")


def test_decimal_arithmetic_is_independent_of_ambient_context_and_signed_zero_is_rejected() -> None:
    baseline = report(
        (
            observation(
                1,
                memory_observed_at=GENERATED_AT - timedelta(hours=12),
                successful_recall_count=d("2"),
                failed_recall_count=d("1"),
            ),
            observation(
                2,
                memory_observed_at=GENERATED_AT - timedelta(days=2),
                successful_recall_count=d("0"),
                failed_recall_count=d("2"),
                contradiction_count=d("1"),
            ),
        ),
    )
    hostile = Context(prec=3, rounding=ROUND_DOWN)
    hostile.traps[Inexact] = True
    with localcontext(hostile):
        constrained = report(
            (
                observation(
                    1,
                    memory_observed_at=GENERATED_AT - timedelta(hours=12),
                    successful_recall_count=d("2"),
                    failed_recall_count=d("1"),
                ),
                observation(
                    2,
                    memory_observed_at=GENERATED_AT - timedelta(days=2),
                    successful_recall_count=d("0"),
                    failed_recall_count=d("2"),
                    contradiction_count=d("1"),
                ),
            ),
        )

    assert constrained == baseline
    with pytest.raises(ValueError, match="signed zero"):
        config(watch_decay_score=d("-0.000000"))
    with pytest.raises(ValueError, match="signed zero"):
        observation(1, successful_recall_count=d("-0"))


def test_payload_has_exact_nested_schema_and_revalidates_resigned_derived_values() -> None:
    module = __import__(
        "polymarket_alpha_lab.research_strategy_specialist_source_memory_decay_report",
        fromlist=["validate_research_strategy_specialist_source_memory_decay_report_payload"],
    )
    decay_report = report((observation(1),), cfg=config(stale_memory_age_seconds=d("7200")))
    payload = module.research_strategy_specialist_source_memory_decay_report_payload(
        decay_report,
    )

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "config",
        "memory_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_decay_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["config"]) == tuple(field.name for field in fields(decay_report.config))

    tampered = deepcopy(payload)
    tampered["rows"][0]["recency_retention_score"] = "0.500000"
    unsigned = dict(tampered)
    unsigned.pop("derived_validation_digest")
    tampered["derived_validation_digest"] = module.sha256(
        module.json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="recency_retention_score"):
        module.validate_research_strategy_specialist_source_memory_decay_report_payload(
            tampered,
        )


def test_builder_revalidates_tampered_config_and_observation_objects() -> None:
    tampered_config = config()
    object.__setattr__(tampered_config, "watch_decay_score", d("NaN"))
    with pytest.raises(ValueError, match="watch_decay_score.*finite"):
        report((observation(1),), cfg=tampered_config)

    tampered_observation = observation(1)
    object.__setattr__(tampered_observation, "successful_recall_count", d("NaN"))
    with pytest.raises(ValueError, match="successful_recall_count.*finite"):
        report((tampered_observation,))


def test_payload_rejects_unknown_missing_and_noncanonical_numeric_schema_values() -> None:
    module = __import__(
        "polymarket_alpha_lab.research_strategy_specialist_source_memory_decay_report",
        fromlist=["validate_research_strategy_specialist_source_memory_decay_report_payload"],
    )
    payload = module.research_strategy_specialist_source_memory_decay_report_payload(
        report((observation(1),)),
    )

    missing = deepcopy(payload)
    missing.pop("status")
    with pytest.raises(ValueError, match="exact public fields"):
        module.validate_research_strategy_specialist_source_memory_decay_report_payload(
            missing,
        )

    unknown = deepcopy(payload)
    unknown["extension"] = "pass"
    with pytest.raises(ValueError, match="exact public fields"):
        module.validate_research_strategy_specialist_source_memory_decay_report_payload(
            unknown,
        )

    numeric = deepcopy(payload)
    numeric["rows"][0]["decay_score"] = 0.0
    with pytest.raises(ValueError, match="Decimal"):
        module.validate_research_strategy_specialist_source_memory_decay_report_payload(
            numeric,
        )


def test_resigned_payload_revalidates_reason_rollups_and_config_derivations() -> None:
    module = __import__(
        "polymarket_alpha_lab.research_strategy_specialist_source_memory_decay_report",
        fromlist=["validate_research_strategy_specialist_source_memory_decay_report_payload"],
    )
    payload = module.research_strategy_specialist_source_memory_decay_report_payload(
        report((observation(1),)),
    )

    tampered_counts = deepcopy(payload)
    tampered_counts["reason_code_counts"] = []
    unsigned = dict(tampered_counts)
    unsigned.pop("derived_validation_digest")
    tampered_counts["derived_validation_digest"] = module.sha256(
        module.json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_strategy_specialist_source_memory_decay_report_payload(
            tampered_counts,
        )

    tampered_config = deepcopy(payload)
    tampered_config["config"]["stale_memory_age_seconds"] = "1800.000000"
    unsigned = dict(tampered_config)
    unsigned.pop("derived_validation_digest")
    tampered_config["derived_validation_digest"] = module.sha256(
        module.json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="stale_memory_age_seconds"):
        module.validate_research_strategy_specialist_source_memory_decay_report_payload(
            tampered_config,
        )


def test_duplicate_memory_keys_and_reason_codes_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate memory keys"):
        report((observation(1), observation(1)))
    with pytest.raises(ValueError, match="duplicates"):
        observation(1, reason_codes=("manually_reviewed", "manually_reviewed"))


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
