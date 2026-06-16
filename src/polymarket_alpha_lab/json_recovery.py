"""Recursive frozen-dataclass recovery from ``_json_ready`` JSON dicts.

Unlike Stage 5's ``PaperTradeRecord`` (flat -- no ``__post_init__``), the
Stage 6 targets (``PaperStrategyCycleReport``, ``PaperNavSnapshot``) have
validating ``__post_init__`` methods that check nested fields via
``isinstance``. A flat ``Report(**coerced_row)`` with nested-as-dict values
RAISES on ``__post_init__``. ``from_jsonable`` reconstructs the FULL nested
dataclass tree so each ``__post_init__`` re-validates successfully.

This helper is intentionally generic and depends on NO ``polymarket_alpha_lab``
module: it resolves every field type via ``typing.get_type_hints(cls)`` (never
the raw string annotation, because ``from __future__ import annotations`` makes
``field.type`` a string) using the class's own module globals, then dispatches
per resolved type.

C3 -- enumerated PaperProjectScreeningReport subtree coverage
-------------------------------------------------------------
Every field type in the full subtree reachable from
``PaperStrategyCycleReport.screening_report`` and ``PaperNavSnapshot.marks`` is
handled by ``_coerce_value``. The dispatch below covers each case:

PaperStrategyCycleReport
  - generated_at: datetime                          -> datetime (ISO str)
  - config_version: str                             -> passthrough
  - scan/considered/snapshot_ready/cost_aware_count: int -> passthrough
  - blocked_counts: tuple[tuple[str, int], ...]      -> C2 nested non-dataclass
    tuple-of-tuples (list-of-lists -> tuple-of-tuples; inner str/int passthrough)
  - screening_report: PaperProjectScreeningReport | None -> optional dataclass
    -> recurse (or None)
  - paper_only/report_only: bool                    -> passthrough

PaperProjectScreeningReport
  - generated_at: datetime                          -> datetime
  - config_version: str                             -> passthrough
  - candidate/ready/watch/defer/blocked_count: int  -> passthrough
  - gate_results: tuple[PaperProjectScreeningGateResult, ...]
    -> tuple of dataclass -> recurse each
  - candidates: tuple[PaperProjectScreeningCandidate, ...] -> recurse each
  - queue_items: tuple[PaperProjectScreeningQueueItem, ...] -> recurse each
  - paper_only/report_only: bool                    -> passthrough

PaperProjectScreeningGateResult
  - gate_name/status/reason_code/message: str       -> passthrough
  - observed_value/threshold: Decimal | int | str | None
    -> multi-type union: None passes through, otherwise passthrough unchanged
    (real data uses int; __post_init__ accepts Decimal/int/str/None, so a
    serialized Decimal-as-str reading back as str still validates -- only the
    Decimal-vs-str type fidelity is relaxed, never validity)

PaperProjectScreeningCandidate
  - market_slug/question/source_status/scoring_side/screening_status: str -> passthrough
  - valid_depth: bool                               -> passthrough
  - net_edge_per_share/total_cost_per_share/ask_size: Decimal | None -> optional Decimal
  - edge/confidence/depth component + spread/resolution_risk/cost penalty +
    screening_score: Decimal                        -> Decimal (str)
  - reason_codes: tuple[str, ...]                   -> flat list -> tuple[str, ...]

PaperProjectScreeningQueueItem
  - queue_position: int                             -> passthrough
  - market_slug/question/research_bucket/source_status/scoring_side: str -> passthrough
  - screening_score: Decimal                        -> Decimal (str)
  - reason_codes: tuple[str, ...]                   -> flat list -> tuple[str, ...]

PaperNavSnapshot
  - marked_at: datetime                             -> datetime
  - starting_cash/cash_balance/realized_pnl/exit_nav/total_cost_basis/
    unrealized_exit_pnl: Decimal                    -> Decimal (str)
  - midpoint_nav: Decimal | None                    -> optional Decimal
  - marks: tuple[PaperPositionMark, ...]            -> tuple of dataclass -> recurse
  - paper_only: bool                                -> passthrough

PaperPositionMark
  - condition_id/token_id/market_slug/outcome_name: str -> passthrough
  - open_size/cost_basis/average_entry_price/exit_filled_size/exit_unfilled_size/
    exit_value: Decimal                             -> Decimal (str)
  - order_book_captured_at: datetime                -> datetime
  - order_book_snapshot_sha256: str                 -> passthrough
  - exit_average_price/exit_worst_price/midpoint_price/midpoint_value/
    best_bid/best_ask/spread/slippage_estimate: Decimal | None -> optional Decimal
  - mark_status: str                                -> passthrough

Conclusion: the recursive dispatcher covers (a) nested dataclasses
(``screening_report``, each mark), (b) ``tuple[dataclass, ...]`` (candidates,
queue_items, gate_results, marks), (c) C2 nested non-dataclass tuples
(``blocked_counts: tuple[tuple[str, int], ...]`` -> deep list->tuple at every
level), (d) flat ``tuple[str, ...]`` (``reason_codes``), (e) ``Decimal`` /
``Decimal | None``, (f) ``datetime``, and (g) multi-type-union / scalar
passthrough. No field in the subtree falls outside these cases.
"""

from __future__ import annotations

from dataclasses import is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, get_args, get_origin, get_type_hints

__all__ = ("from_jsonable",)


def from_jsonable(cls: type, row: dict[str, Any]) -> Any:
    """Recursively reconstruct a frozen dataclass from a ``_json_ready`` dict.

    Resolves field types via ``get_type_hints(cls)`` and dispatches each value
    through ``_coerce_value``. Constructs ``cls(**reconstructed)`` so the
    dataclass ``__post_init__`` re-validates the reconstructed tree.
    """
    hints = get_type_hints(cls)
    reconstructed: dict[str, Any] = {}
    for name, value in row.items():
        reconstructed[name] = _coerce_value(value, hints.get(name))
    return cls(**reconstructed)


def _coerce_value(value: Any, type_hint: Any) -> Any:
    """Reverse ``_json_ready`` for one value keyed to its resolved type hint."""
    if value is None or type_hint is None:
        return value
    target = _unwrap_optional(type_hint)
    # (a)/(b) dataclass (nested or element of a tuple[X, ...]) -> recurse.
    if isinstance(target, type) and is_dataclass(target):
        if not isinstance(value, dict):
            raise ValueError(
                f"expected a JSON object for dataclass "
                f"{getattr(target, '__name__', target)}, got {type(value).__name__}",
            )
        return from_jsonable(target, value)
    origin = get_origin(target)
    # (c)/(d) tuple[X, ...] or fixed-arity tuple -> deep list->tuple at every
    # level (C2: nested non-dataclass tuples like tuple[str, int] recurse too).
    if origin is tuple:
        args = get_args(target)
        if len(args) == 2 and args[1] is Ellipsis:
            element_type = args[0]
            return tuple(_coerce_value(element, element_type) for element in value)
        return tuple(
            _coerce_value(element, element_type)
            for element, element_type in zip(value, args, strict=False)
        )
    # (e) Decimal: str -> Decimal with is_finite guard; reject float.
    if target is Decimal:
        return _as_decimal(value)
    # (f) datetime: ISO str -> datetime.
    if target is datetime:
        return datetime.fromisoformat(value)
    # (g) multi-type union (e.g. Decimal | int | str) or plain scalar ->
    # pass through unchanged.
    return value


def _unwrap_optional(type_hint: Any) -> Any:
    """Unwrap ``X | None`` to ``X``; leave multi-type unions and others as-is.

    Returns the single non-None member for ``X | None``. For unions with more
    than one non-None member (e.g. ``Decimal | int | str | None``) the original
    union is returned so the caller falls through to passthrough -- this
    preserves int/str fidelity for ``observed_value``/``threshold`` gate fields
    whose real values are always ints.
    """
    args = get_args(type_hint)
    if not args:
        return type_hint
    none_type = type(None)
    if none_type in args:
        non_none = tuple(arg for arg in args if arg is not none_type)
        if len(non_none) == 1:
            return non_none[0]
    return type_hint


def _as_decimal(value: Any) -> Decimal:
    """Coerce a JSON value into a finite Decimal, rejecting floats."""
    if isinstance(value, bool):
        raise ValueError("Decimal value must not be a bool")
    if isinstance(value, float):
        raise ValueError("Decimal value must not be a float")
    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError("Decimal value must be finite")
    return decimal
