from __future__ import annotations

import ast
import hashlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_event_information_gap_budget_report import (
    DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION,
    ResearchStrategyEventInformationGapBudgetConfig,
    ResearchStrategyEventInformationGapBudgetInput,
    ResearchStrategyEventInformationGapBudgetReport,
    ResearchStrategyEventInformationGapBudgetRow,
    build_research_strategy_event_information_gap_budget_report,
    research_strategy_event_information_gap_budget_report_digest,
    research_strategy_event_information_gap_budget_report_payload,
    validate_research_strategy_event_information_gap_budget_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_event_information_gap_budget_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DictSubclass(dict[str, Any]):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyEventInformationGapBudgetConfig:
    values = {
        "source_freshness_gap_weight": d("0.300000"),
        "authority_gap_weight": d("0.300000"),
        "team_coverage_gap_weight": d("0.200000"),
        "resolution_proximity_weight": d("0.200000"),
        "watch_component_gap_threshold": d("0.400000"),
        "block_component_gap_threshold": d("0.750000"),
        "watch_information_gap_pressure_threshold": d("0.350000"),
        "block_information_gap_pressure_threshold": d("0.700000"),
        "watch_diagnostic_budget_share_threshold": d("0.250000"),
        "block_diagnostic_budget_share_threshold": d("0.400000"),
    }
    values.update(overrides)
    return ResearchStrategyEventInformationGapBudgetConfig(**values)


def unresolved_event(
    event_ref: str = "private-event-alpha",
    *,
    source_freshness_gap_score: Decimal = d("0.100000"),
    authority_gap_score: Decimal = d("0.100000"),
    team_coverage_gap_score: Decimal = d("0.100000"),
    resolution_proximity_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEventInformationGapBudgetInput:
    return ResearchStrategyEventInformationGapBudgetInput(
        event_ref=event_ref,
        source_freshness_gap_score=source_freshness_gap_score,
        authority_gap_score=authority_gap_score,
        team_coverage_gap_score=team_coverage_gap_score,
        resolution_proximity_score=resolution_proximity_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *events: ResearchStrategyEventInformationGapBudgetInput,
    cfg: ResearchStrategyEventInformationGapBudgetConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEventInformationGapBudgetReport:
    return build_research_strategy_event_information_gap_budget_report(
        events,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = deepcopy(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = deepcopy(payload)
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_public_numeric_scalars(value: object) -> None:
    assert type(value) not in (int, float, Decimal)
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_information_gap_budget_allocates_diagnostic_priority_deterministically() -> None:
    routine = unresolved_event("private-routine")
    watch = unresolved_event(
        "private-watch",
        source_freshness_gap_score=d("0.600000"),
        authority_gap_score=d("0.500000"),
        team_coverage_gap_score=d("0.400000"),
        resolution_proximity_score=d("0.500000"),
    )
    block = unresolved_event(
        "private-block",
        source_freshness_gap_score=d("0.900000"),
        authority_gap_score=d("0.800000"),
        team_coverage_gap_score=d("0.700000"),
        resolution_proximity_score=d("0.900000"),
    )

    first = report(routine, watch, block)
    second = report(block, routine, watch)

    assert is_dataclass(first)
    assert first == second
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION
    )
    assert first.event_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.total_information_gap_pressure == d("1.440000")
    assert first.max_information_gap_pressure == d("0.830000")
    assert first.average_information_gap_pressure == d("0.480000")
    assert first.max_diagnostic_budget_share == d("0.576389")
    assert first.status == "block"
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked = first.rows[0]
    assert blocked.source_freshness_gap_score == d("0.900000")
    assert blocked.authority_gap_score == d("0.800000")
    assert blocked.team_coverage_gap_score == d("0.700000")
    assert blocked.resolution_proximity_score == d("0.900000")
    assert blocked.information_gap_pressure == d("0.830000")
    assert blocked.diagnostic_budget_share == d("0.576389")
    assert blocked.reason_codes == (
        "source_freshness_gap_block",
        "authority_gap_block",
        "resolution_proximity_block",
        "information_gap_pressure_block",
        "diagnostic_budget_share_block",
        "team_coverage_gap_watch",
    )

    watched = first.rows[1]
    assert watched.information_gap_pressure == d("0.510000")
    assert watched.diagnostic_budget_share == d("0.354167")
    assert watched.reason_codes == (
        "source_freshness_gap_watch",
        "authority_gap_watch",
        "team_coverage_gap_watch",
        "resolution_proximity_watch",
        "information_gap_pressure_watch",
        "diagnostic_budget_share_watch",
    )
    assert first.rows[2].reason_codes == ("information_gap_priority_pass",)
    assert first.reason_codes == (
        "source_freshness_gap_block",
        "authority_gap_block",
        "resolution_proximity_block",
        "information_gap_pressure_block",
        "diagnostic_budget_share_block",
        "source_freshness_gap_watch",
        "authority_gap_watch",
        "team_coverage_gap_watch",
        "resolution_proximity_watch",
        "information_gap_pressure_watch",
        "diagnostic_budget_share_watch",
    )

    payload = research_strategy_event_information_gap_budget_report_payload(first)
    assert payload == research_strategy_event_information_gap_budget_report_payload(
        second,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert "private-routine" not in encoded
    assert "private-watch" not in encoded
    assert "private-block" not in encoded
    assert payload["event_count"] == "3.000000"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["diagnostic_budget_share"] == "0.576389"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert_sha256(first.derived_validation_digest)
    assert canonical_digest(payload) == first.derived_validation_digest
    assert research_strategy_event_information_gap_budget_report_digest(first) == (
        first.derived_validation_digest
    )
    assert validate_research_strategy_event_information_gap_budget_report_payload(
        payload,
    )


def test_empty_information_gap_budget_blocks_without_event_references() -> None:
    result = report()

    assert result.event_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.total_information_gap_pressure == ZERO
    assert result.max_information_gap_pressure is None
    assert result.average_information_gap_pressure is None
    assert result.max_diagnostic_budget_share is None
    assert result.status == "block"
    assert result.reason_codes == ("information_gap_budget_no_unresolved_events",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.derived_validation_digest)


def test_information_gap_budget_is_decimal_only_frozen_and_strictly_report_only() -> None:
    result = report(unresolved_event("private-frozen"))

    assert is_dataclass(ResearchStrategyEventInformationGapBudgetConfig)
    assert is_dataclass(ResearchStrategyEventInformationGapBudgetInput)
    assert is_dataclass(ResearchStrategyEventInformationGapBudgetRow)
    assert is_dataclass(ResearchStrategyEventInformationGapBudgetReport)
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].diagnostic_budget_share = ZERO  # type: ignore[misc]
    with pytest.raises(TypeError, match="may not be subclassed"):
        type(
            "BadInput",
            (ResearchStrategyEventInformationGapBudgetInput,),
            {},
        )

    with pytest.raises(ValueError, match="paper_only"):
        unresolved_event(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="source_freshness_gap_score"):
        unresolved_event(source_freshness_gap_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_gap_score"):
        unresolved_event(authority_gap_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_coverage_gap_score"):
        unresolved_event(
            team_coverage_gap_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="event_ref values must be unique"):
        report(
            unresolved_event("private-duplicate"),
            unresolved_event("private-duplicate"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            unresolved_event("private-time"),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            unresolved_event("private-time"),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="weights must sum"):
        config(resolution_proximity_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_component_gap_threshold"):
        config(block_component_gap_threshold=d("0.400000"))

    for item in (result, *result.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) not in (int, float), field.name


def test_validator_rejects_tampering_and_forged_resigned_derived_logic() -> None:
    result = report(
        unresolved_event(
            "private-block",
            source_freshness_gap_score=d("0.900000"),
            authority_gap_score=d("0.800000"),
            team_coverage_gap_score=d("0.700000"),
            resolution_proximity_score=d("0.900000"),
        ),
        unresolved_event("private-pass"),
    )
    row = result.rows[0]

    with pytest.raises(ValueError, match="information_gap_pressure"):
        replace(
            row,
            information_gap_pressure=row.information_gap_pressure + d("0.100000"),
        )
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="pass")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            row,
            status="pass",
            reason_codes=("information_gap_priority_pass",),
        )
    with pytest.raises(ValueError, match="event_count must match"):
        replace(result, event_count=d("3.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    payload = research_strategy_event_information_gap_budget_report_payload(result)
    with pytest.raises(ValueError, match="readonly"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="numeric scalar"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            {**payload, "event_count": 2},
        )
    with pytest.raises(ValueError, match="unsafe"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            {**payload, "candidate" "_" "id": "private-block"},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            {**payload, "derived_validation_digest": "0" * 64},
        )

    forged = deepcopy(payload)
    forged["rows"][0]["status"] = "pass"
    forged["rows"][0]["reason_codes"] = ["information_gap_priority_pass"]
    forged["derived_validation_digest"] = canonical_digest(forged)
    assert_sha256(forged["derived_validation_digest"])
    with pytest.raises(ValueError, match="reason_codes must match"):
        validate_research_strategy_event_information_gap_budget_report_payload(forged)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("source_freshness_gap_score", d("-0.0000004")),
        ("authority_gap_score", d("1.0000004")),
        ("team_coverage_gap_score", d("-0.0000004")),
        ("resolution_proximity_score", d("1.0000004")),
    ),
)
def test_raw_ratio_bounds_are_checked_before_quantization(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be between"):
        unresolved_event(**{field_name: value})


@pytest.mark.parametrize(
    "field_name",
    (
        "source_freshness_gap_score",
        "authority_gap_score",
        "team_coverage_gap_score",
        "resolution_proximity_score",
    ),
)
def test_signed_zero_and_non_finite_inputs_are_rejected(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must not be signed zero"):
        unresolved_event(**{field_name: d("-0.000000")})

    for invalid in (d("NaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match=f"{field_name} must be finite"):
            unresolved_event(**{field_name: invalid})


def test_decimal_arithmetic_uses_a_fresh_fixed_local_context() -> None:
    import polymarket_alpha_lab.research_strategy_event_information_gap_budget_report as module

    expected = research_strategy_event_information_gap_budget_report_payload(
        report(
            unresolved_event(
                "private-fixed-context",
                source_freshness_gap_score=d("0.5000005"),
                authority_gap_score=d("0.5000005"),
                team_coverage_gap_score=d("0.5000005"),
                resolution_proximity_score=d("0.5000005"),
            ),
        ),
    )
    original_context = module.DECIMAL_CONTEXT.copy()
    original_precision = module.DECIMAL_CONTEXT_PRECISION
    original_rounding = module.DECIMAL_CONTEXT_ROUNDING
    try:
        module.DECIMAL_CONTEXT.prec = 12
        module.DECIMAL_CONTEXT.rounding = ROUND_UP
        module.DECIMAL_CONTEXT_PRECISION = 12
        module.DECIMAL_CONTEXT_ROUNDING = ROUND_UP
        with localcontext() as context:
            context.prec = 7
            context.rounding = ROUND_DOWN
            actual = research_strategy_event_information_gap_budget_report_payload(
                report(
                    unresolved_event(
                        "private-fixed-context",
                        source_freshness_gap_score=d("0.5000005"),
                        authority_gap_score=d("0.5000005"),
                        team_coverage_gap_score=d("0.5000005"),
                        resolution_proximity_score=d("0.5000005"),
                    ),
                ),
            )
    finally:
        module.DECIMAL_CONTEXT = original_context
        module.DECIMAL_CONTEXT_PRECISION = original_precision
        module.DECIMAL_CONTEXT_ROUNDING = original_rounding

    assert actual == expected
    assert actual["rows"][0]["information_gap_pressure"] == "0.500000"


def test_public_dataclasses_are_frozen_slotted_and_exact() -> None:
    public_types = (
        ResearchStrategyEventInformationGapBudgetConfig,
        ResearchStrategyEventInformationGapBudgetInput,
        ResearchStrategyEventInformationGapBudgetRow,
        ResearchStrategyEventInformationGapBudgetReport,
    )

    for public_type in public_types:
        assert public_type.__dataclass_params__.frozen is True
        assert "__slots__" in public_type.__dict__
        assert "__dict__" not in public_type.__slots__


def test_oversized_finite_decimals_use_the_value_error_boundary() -> None:
    empty = report()

    with pytest.raises(ValueError, match="event_count"):
        replace(empty, event_count=d("1e1000"))
    with pytest.raises(ValueError, match="total_information_gap_pressure"):
        replace(empty, total_information_gap_pressure=d("1e1000"))

    payload = research_strategy_event_information_gap_budget_report_payload(empty)
    payload["event_count"] = "1e1000"
    with pytest.raises(ValueError, match="event_count"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            resign_payload(payload),
        )


def test_resigned_payload_requires_canonical_utc_datetime_spelling() -> None:
    payload = research_strategy_event_information_gap_budget_report_payload(
        report(unresolved_event("private-canonical-utc")),
    )

    for generated_at in (
        "2026-07-09T12:00:00Z",
        "2026-07-09T13:00:00+01:00",
        "2026-07-09T12:00:00.000000+00:00",
    ):
        forged = deepcopy(payload)
        forged["generated_at"] = generated_at
        with pytest.raises(ValueError, match="canonical UTC"):
            validate_research_strategy_event_information_gap_budget_report_payload(
                resign_payload(forged),
            )


@pytest.mark.parametrize(
    "public_type",
    (
        ResearchStrategyEventInformationGapBudgetConfig,
        ResearchStrategyEventInformationGapBudgetInput,
        ResearchStrategyEventInformationGapBudgetRow,
        ResearchStrategyEventInformationGapBudgetReport,
    ),
)
def test_all_public_dataclasses_are_frozen_and_non_subclassable(
    public_type: type[object],
) -> None:
    with pytest.raises(TypeError, match="may not be subclassed"):
        type(f"Bad{public_type.__name__}", (public_type,), {})


def test_payload_requires_exact_canonical_key_order_even_when_resigned() -> None:
    payload = research_strategy_event_information_gap_budget_report_payload(
        report(unresolved_event("private-canonical-schema")),
    )
    reordered_report = {
        key: deepcopy(payload[key])
        for key in reversed(tuple(payload))
    }
    with pytest.raises(ValueError, match="canonical keys"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            resign_payload(reordered_report),
        )

    reordered_row = deepcopy(payload)
    row = reordered_row["rows"][0]
    reordered_row["rows"][0] = {
        key: deepcopy(row[key])
        for key in reversed(tuple(row))
    }
    with pytest.raises(ValueError, match="canonical keys"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            resign_payload(reordered_row),
        )


def test_payload_requires_an_exact_dict_container() -> None:
    payload = research_strategy_event_information_gap_budget_report_payload(
        report(unresolved_event("private-exact-dict")),
    )
    subclassed_payload = _DictSubclass(payload)

    with pytest.raises(ValueError, match="report payload must be a JSON object"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            subclassed_payload,
        )
    with pytest.raises(ValueError, match="report payload must be a JSON object"):
        research_strategy_event_information_gap_budget_report_payload(
            subclassed_payload,
        )


def test_stable_public_tie_break_and_private_reference_redaction() -> None:
    alpha_ref = "https://private.example/a?api_key=alpha-secret"
    zulu_ref = "https://private.example/z?token=zulu-secret"
    alpha = unresolved_event(
        alpha_ref,
        source_freshness_gap_score=d("0.600000"),
        authority_gap_score=d("0.400000"),
        team_coverage_gap_score=d("0.500000"),
        resolution_proximity_score=d("0.500000"),
    )
    zulu = unresolved_event(
        zulu_ref,
        source_freshness_gap_score=d("0.400000"),
        authority_gap_score=d("0.600000"),
        team_coverage_gap_score=d("0.500000"),
        resolution_proximity_score=d("0.500000"),
    )

    built = report(zulu, alpha)
    assert built == report(alpha, zulu)
    assert built.rows[0].source_freshness_gap_score == d("0.600000")
    assert built.rows[1].source_freshness_gap_score == d("0.400000")

    payload = research_strategy_event_information_gap_budget_report_payload(built)
    encoded = json.dumps(payload, sort_keys=True)
    assert alpha_ref not in encoded
    assert zulu_ref not in encoded
    assert "alpha-secret" not in encoded
    assert "zulu-secret" not in encoded

    forged = deepcopy(payload)
    forged["rows"] = list(reversed(forged["rows"]))
    for index, row in enumerate(forged["rows"], start=1):
        row["row_number"] = f"{index}.000000"
    with pytest.raises(ValueError, match="sorted deterministically"):
        validate_research_strategy_event_information_gap_budget_report_payload(
            resign_payload(forged),
        )


def test_resigned_payload_recomputes_each_diagnostic_budget_share() -> None:
    payload = research_strategy_event_information_gap_budget_report_payload(
        report(
            unresolved_event("private-share-alpha"),
            unresolved_event("private-share-beta"),
        ),
    )
    forged = deepcopy(payload)
    forged["rows"][0]["diagnostic_budget_share"] = "0.600000"
    forged["rows"][1]["diagnostic_budget_share"] = "0.400000"
    forged["max_diagnostic_budget_share"] = "0.600000"

    with pytest.raises(
        ValueError,
        match="diagnostic_budget_share must match total information gap pressure",
    ):
        validate_research_strategy_event_information_gap_budget_report_payload(
            resign_payload(forged),
        )


def test_public_surface_is_canonical_pure_and_has_no_action_semantics() -> None:
    import polymarket_alpha_lab.research_strategy_event_information_gap_budget_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVENT_INFORMATION_GAP_BUDGET_REPORT_CONFIG_VERSION",
        "ResearchStrategyEventInformationGapBudgetConfig",
        "ResearchStrategyEventInformationGapBudgetInput",
        "ResearchStrategyEventInformationGapBudgetReport",
        "ResearchStrategyEventInformationGapBudgetRow",
        "build_research_strategy_event_information_gap_budget_report",
        "research_strategy_event_information_gap_budget_report_digest",
        "research_strategy_event_information_gap_budget_report_payload",
        "validate_research_strategy_event_information_gap_budget_report_payload",
    )
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "reco" "mmend",
        "siz" "ing",
        "b" "uy",
        "s" "ell",
        "wal" "let",
        "or" "der",
        "li" "ve " "trading",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    forbidden_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            roots = {alias.name.split(".")[0] for alias in node.names}
            assert not (roots & forbidden_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_calls
