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


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_authority_resolution_memory_floor_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_authority_resolution_memory_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")

RAW_PRIVATE_VALUES = (
    "candidate-alpha-private-id",
    "market-yes-slug-and-question",
    "https://authority.example/private-resolution?token=secret-alpha",
    "raw source text says final outcome is yes",
    "postgres://user:pass@example.test:5432/private_resolution",
    "resolution_event_table",
    "wallet=0xabc order=123 trade=456",
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-event-authority-resolution-memory-floor-report-v0",
        "memory_age_watch_seconds": d("3600.000000"),
        "memory_age_block_seconds": d("86400.000000"),
        "floor_watch_score": d("0.700000"),
        "floor_block_score": d("0.500000"),
        "gap_block_count": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchEventAuthorityResolutionMemoryFloorConfig(**values)


def input_item(
    index: int,
    *,
    event_bucket: str | None = None,
    resolution_bucket: str | None = None,
    observed_at: datetime | None = None,
    authority_resolution_checked_at: datetime | None = None,
    authority_memory_score: Decimal = d("0.950000"),
    rule_alignment_score: Decimal = d("0.930000"),
    evidence_consensus_score: Decimal = d("0.900000"),
    finality_confidence_score: Decimal = d("0.920000"),
    unresolved_gap_count: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchEventAuthorityResolutionMemoryFloorInput(
        event_bucket=event_bucket or f"event-{index:03d}",
        resolution_bucket=resolution_bucket or f"resolution-{index:03d}",
        private_subject_ref=f"{RAW_PRIVATE_VALUES[0]}-{index}",
        private_venue_ref=f"{RAW_PRIVATE_VALUES[1]}-{index}",
        private_evidence_ref=(
            f"{RAW_PRIVATE_VALUES[2]}; {RAW_PRIVATE_VALUES[3]}; "
            f"{RAW_PRIVATE_VALUES[4]}; {RAW_PRIVATE_VALUES[5]}"
        ),
        private_memory_ref=f"{RAW_PRIVATE_VALUES[6]}-{index}",
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(hours=2)
        ),
        authority_resolution_checked_at=(
            authority_resolution_checked_at
            if authority_resolution_checked_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        authority_memory_score=authority_memory_score,
        rule_alignment_score=rule_alignment_score,
        evidence_consensus_score=evidence_consensus_score,
        finality_confidence_score=finality_confidence_score,
        unresolved_gap_count=unresolved_gap_count,
        reason_codes=reason_codes,
    )


def build_report(
    items: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_event_authority_resolution_memory_floor_report(
        items,
        generated_at=generated_at,
        config=config if config is not None else cfg(),
    )


def test_report_scores_pass_watch_block_without_public_raw_leakage() -> None:
    module = api()

    result = build_report(
        (
            input_item(
                1,
                event_bucket="event-pass",
                resolution_bucket="resolution-pass",
            ),
            input_item(
                2,
                event_bucket="event-watch",
                resolution_bucket="resolution-watch",
                authority_resolution_checked_at=GENERATED_AT - timedelta(hours=2),
                authority_memory_score=d("0.650000"),
                unresolved_gap_count=d("1.000000"),
                reason_codes=("manual_watch",),
            ),
            input_item(
                3,
                event_bucket="event-block",
                resolution_bucket="resolution-block",
                authority_resolution_checked_at=GENERATED_AT - timedelta(days=2),
                authority_memory_score=d("0.400000"),
                rule_alignment_score=d("0.450000"),
                evidence_consensus_score=d("0.300000"),
                finality_confidence_score=d("0.550000"),
                unresolved_gap_count=d("2.000000"),
                reason_codes=("manual_block",),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-event-authority-resolution-memory-floor-report-v0"
    )
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.status == "block"
    assert result.min_resolution_memory_floor_score == d("0.300000")
    assert result.average_resolution_memory_floor_score == d("0.616667")
    assert result.max_memory_age_seconds == d("172800.000000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    block_row, watch_row, pass_row = result.rows
    assert block_row.status == "block"
    assert block_row.event_digest.startswith("sha256:")
    assert block_row.authority_digest.startswith("sha256:")
    assert block_row.resolution_digest.startswith("sha256:")
    assert block_row.memory_age_seconds == d("172800.000000")
    assert block_row.memory_age_pressure_score == d("1.000000")
    assert block_row.resolution_memory_floor_score == d("0.300000")
    assert block_row.reason_codes == (
        "authority_resolution_memory_floor_block",
        "authority_memory_score_block",
        "rule_alignment_score_block",
        "evidence_consensus_score_block",
        "finality_confidence_score_watch",
        "memory_age_block",
        "unresolved_gap_block",
        "input_manual_block",
    )

    assert watch_row.status == "watch"
    assert watch_row.memory_age_seconds == d("7200.000000")
    assert watch_row.memory_age_pressure_score == d("0.083333")
    assert watch_row.resolution_memory_floor_score == d("0.650000")
    assert watch_row.reason_codes == (
        "authority_resolution_memory_floor_watch",
        "authority_memory_score_watch",
        "memory_age_watch",
        "unresolved_gap_watch",
        "input_manual_watch",
    )

    assert pass_row.status == "pass"
    assert pass_row.memory_age_seconds == d("1800.000000")
    assert pass_row.resolution_memory_floor_score == d("0.900000")
    assert pass_row.reason_codes == ("authority_resolution_memory_floor_pass",)

    assert_public_numeric_values_are_decimal(result)

    payload = module.research_event_authority_resolution_memory_floor_report_payload(
        result,
    )
    payload_again = module.research_event_authority_resolution_memory_floor_report_payload(
        build_report(tuple(reversed(result.rows)), config=cfg()),
    )
    encoded = json.dumps(payload, sort_keys=True).lower()
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert payload == payload_again
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["item_count"] == "3.000000"
    assert payload["rows"][0]["resolution_memory_floor_score"] == "0.300000"
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert_no_raw_payload_terms(payload)
    for private_value in RAW_PRIVATE_VALUES:
        assert private_value.lower() not in encoded


def test_empty_report_is_block_readonly_and_decimal_zeroed() -> None:
    result = build_report(())

    assert result.item_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.min_resolution_memory_floor_score == ZERO
    assert result.average_resolution_memory_floor_score == ZERO
    assert result.max_memory_age_seconds == ZERO
    assert result.status == "block"
    assert result.reason_codes == ("authority_resolution_memory_floor_report_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    sample_config = cfg()
    sample_input = input_item(1)
    sample_report = build_report((sample_input,))
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_input, sample_row, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="memory_age_watch_seconds"):
        cfg(memory_age_watch_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_memory_score"):
        input_item(1, authority_memory_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="authority_memory_score"):
        input_item(1, authority_memory_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="floor_block_score"):
        cfg(floor_watch_score=d("0.400000"), floor_block_score=d("0.500000"))
    with pytest.raises(ValueError, match="gap_block_count"):
        cfg(gap_block_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_item(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="observed_at"):
        build_report((input_item(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="authority_resolution_checked_at"):
        build_report(
            (
                input_item(
                    1,
                    authority_resolution_checked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_authority_resolution_memory_floor_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=cfg(),
        )
    with pytest.raises(ValueError, match="status"):
        replace(sample_row, status="blocked")


def test_tamper_evident_digest_and_payload_validation() -> None:
    module = api()
    result = build_report(
        (input_item(1), input_item(2, authority_memory_score=d("0.650000"))),
    )
    row = result.rows[0]

    with pytest.raises(ValueError, match="resolution_memory_floor_score"):
        replace(
            row,
            resolution_memory_floor_score=(
                row.resolution_memory_floor_score + d("0.000001")
            ),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(result, pass_count=result.pass_count + d("1.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    payload = module.research_event_authority_resolution_memory_floor_report_payload(
        result,
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_event_authority_resolution_memory_floor_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_event_authority_resolution_memory_floor_report_payload(
            {**payload, "raw_candidate": "candidate-alpha"},
        )
    with pytest.raises(ValueError, match="Decimal\\|string"):
        module.research_event_authority_resolution_memory_floor_report_payload(
            {**payload, "item_count": 1.0},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_authority_resolution_memory_floor_report_payload(
            {**payload, "item_count": "4.000000"},
        )


def test_module_is_report_only_and_has_no_live_side_effect_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    lowered = MODULE_PATH.read_text(encoding="utf-8").lower()

    def joined(*pieces: str) -> str:
        return "".join(pieces)

    allowed_import_roots = {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "submit",
        "post",
        "send",
        "login",
        "place_order",
        "cancel",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_terms = (
        joined("d", "b"),
        joined("net", "work"),
        joined("wal", "let"),
        joined("or", "der"),
        joined("live", " trading"),
        joined("si", "zing"),
        joined("recommen", "dation"),
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert {
                alias.name.split(".")[0] for alias in node.names
            } <= allowed_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed_import_roots
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in lowered] == []


def test_public_api_is_exactly_the_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION",
        "ResearchEventAuthorityResolutionMemoryFloorConfig",
        "ResearchEventAuthorityResolutionMemoryFloorInput",
        "ResearchEventAuthorityResolutionMemoryFloorReport",
        "ResearchEventAuthorityResolutionMemoryFloorRow",
        "build_research_event_authority_resolution_memory_floor_report",
        "research_event_authority_resolution_memory_floor_report_digest",
        "research_event_authority_resolution_memory_floor_report_payload",
        "validate_research_event_authority_resolution_memory_floor_public_payload",
    )


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_raw_payload_terms(value: object) -> None:
    blocked_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert [term for term in blocked_terms if term in lowered_key] == []
            assert_no_raw_payload_terms(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_raw_payload_terms(item)
    elif isinstance(value, str):
        lowered_value = value.lower()
        assert [term for term in blocked_terms if term in lowered_value] == []


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
