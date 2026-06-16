"""Paper-only execution leaf (Stage 4 Task 1).

Turns a screening-ready ``PaperProjectScreeningCandidate`` plus its in-cycle
context (``NormalizedMarket``, the chosen side's ``OrderBookSnapshot``, the
raw archive entries, the cost-aware report, and a ``PaperExecutionConfig``)
into an auditable ``PaperTradeRecord`` via the pure ``simulate_order_book_fill``
helper. No live/auth/wallet/order-placement surfaces -- only paper simulate +
journal append. Runs inline inside ``run_strategy_cycle`` (Task 2), never from
replayed JSONL.

Execution logic, validation rules, and public API are authoritative in
``docs/superpowers/specs/2026-06-16-paper-execution-v0.md``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.domain import NormalizedMarket, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill, PaperOrder, simulate_order_book_fill
from polymarket_alpha_lab.project_screening import PaperProjectScreeningCandidate
from polymarket_alpha_lab.research import ResearchPacket

if TYPE_CHECKING:
    # MINOR (a): ``RawArchiveEntry`` is referenced ONLY for the annotation of
    # ``raw_book_archive_entry`` / ``market_raw_archive_entry``. At runtime
    # the function duck-types any object exposing ``.payload_path`` and
    # ``.payload_sha256``; ``archive`` is never imported at runtime so this
    # leaf stays a dependency-light in-memory boundary (scope-enforced).
    from polymarket_alpha_lab.archive import RawArchiveEntry


__all__ = (
    "PaperExecutionConfig",
    "PaperExecutionResult",
    "PaperExecutionLog",
    "execute_paper_trade_from_screening",
)


ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
PRICE_QUANTUM = Decimal("0.001")

YES_NAMES = {"yes", "true", "long"}
NO_NAMES = {"no", "false", "short"}

SKIPPED_REASONS = (
    "not_screening_ready",
    "invalid_depth",
    "unresolvable_token",
    "no_executable_depth",
    "no_bid",
)


# --------------------------------------------------------------------------
# Public config.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PaperExecutionConfig:
    """Frozen configuration for the paper execution leaf."""

    config_version: str
    strategy_type: str = "book_imbalance_screening_paper"
    paper_budget_size: Decimal = Decimal("10.0000")
    sizing_limiter: str = "screening_book_depth"
    planned_exit_rule: str = "hold_to_resolution"
    account_equity_before_trade: Decimal = Decimal("10000.0000")
    thesis_template: str = "Paper edge from screening reasons: {reason_codes}."
    invalidating_conditions_template: str = (
        "Official resolution source changes materially."
    )
    rule_text: str = "Buy screening-ready paper candidates against executable ask depth."
    resolution_source_fallback: str = "polymarket_event_resolution"

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("strategy_type", self.strategy_type)
        _require_positive_decimal("paper_budget_size", self.paper_budget_size)
        _require_canonical_string("sizing_limiter", self.sizing_limiter)
        _require_canonical_string("planned_exit_rule", self.planned_exit_rule)
        # codex IMPORTANT: from_packet_and_fill rejects nonpositive equity; fail
        # fast here so a misconfigured cycle never reaches the journal layer.
        _require_positive_decimal("account_equity_before_trade", self.account_equity_before_trade)
        _require_canonical_string("thesis_template", self.thesis_template)
        _require_canonical_string(
            "invalidating_conditions_template",
            self.invalidating_conditions_template,
        )
        _require_canonical_string("rule_text", self.rule_text)
        _require_canonical_string(
            "resolution_source_fallback",
            self.resolution_source_fallback,
        )


# --------------------------------------------------------------------------
# Public result.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PaperExecutionResult:
    """Frozen, paper-only/report-only result of one paper execution attempt."""

    generated_at: datetime
    market_slug: str
    condition_id: str
    token_id: str
    side: str
    fill: PaperFill | None
    record: PaperTradeRecord | None
    skipped_reason: str | None
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("condition_id", self.condition_id)
        if not isinstance(self.token_id, str):
            raise ValueError("token_id must be a string")
        if not isinstance(self.side, str):
            raise ValueError("side must be a string")
        # paper_only/report_only hard-enforced with `is` (spec validation rules).
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.skipped_reason is not None:
            _require_canonical_string("skipped_reason", self.skipped_reason)
        # INVARIANT: skipped_reason is None  <=>  (fill is not None and record is not None).
        executed = self.fill is not None and self.record is not None
        if (self.skipped_reason is None) != executed:
            raise ValueError(
                "skipped_reason must be None iff both fill and record are present"
            )
        if self.skipped_reason is not None and self.skipped_reason not in SKIPPED_REASONS:
            raise ValueError("skipped_reason must be a known paper execution skip reason")


# --------------------------------------------------------------------------
# Public log.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PaperExecutionLog:
    """Append-only JSONL log of ``PaperExecutionResult`` values."""

    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, result: PaperExecutionResult) -> None:
        if not isinstance(result, PaperExecutionResult):
            raise ValueError("result must be a PaperExecutionResult")
        _validate_result_tree(result)
        line = json.dumps(_json_ready(asdict(result)), allow_nan=False, sort_keys=True) + "\n"
        path = _normalize_log_path(self.path)
        _validate_log_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


# --------------------------------------------------------------------------
# Pure entry point.
# --------------------------------------------------------------------------


def execute_paper_trade_from_screening(
    *,
    candidate: PaperProjectScreeningCandidate,
    cost_aware_report: PaperCostAwareEventStrategyReport,
    market: NormalizedMarket,
    book: OrderBookSnapshot,
    raw_book_archive_entry: "RawArchiveEntry",
    market_raw_archive_entry: "RawArchiveEntry",
    config: PaperExecutionConfig,
    generated_at: datetime,
) -> PaperExecutionResult:
    """Execute one paper trade from a screening-ready candidate.

    Pure in-memory: walks ``simulate_order_book_fill`` against ``book`` and
    journals a ``PaperTradeRecord``. The ORDER is always a BUY of the chosen
    outcome token (``side`` is the outcome, not the order direction).
    """
    if not isinstance(candidate, PaperProjectScreeningCandidate):
        raise ValueError("candidate must be a PaperProjectScreeningCandidate")
    if not isinstance(cost_aware_report, PaperCostAwareEventStrategyReport):
        raise ValueError("cost_aware_report must be a PaperCostAwareEventStrategyReport")
    if not isinstance(market, NormalizedMarket):
        raise ValueError("market must be a NormalizedMarket")
    if not isinstance(book, OrderBookSnapshot):
        raise ValueError("book must be an OrderBookSnapshot")
    if not isinstance(config, PaperExecutionConfig):
        raise ValueError("config must be a PaperExecutionConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    market_slug = candidate.market_slug
    condition_id = market.market.condition_id
    side = candidate.scoring_side

    def _skip(reason: str) -> PaperExecutionResult:
        return PaperExecutionResult(
            generated_at=generated_at,
            market_slug=market_slug,
            condition_id=condition_id,
            token_id="",
            side=side,
            fill=None,
            record=None,
            skipped_reason=reason,
        )

    # Gate (codex IMPORTANT): check BOTH statuses + valid_depth.
    if (
        candidate.screening_status != "screening_ready"
        or candidate.source_status != "paper_review_ready"
    ):
        return _skip("not_screening_ready")
    if not candidate.valid_depth:
        return _skip("invalid_depth")

    # Resolve the chosen outcome token (mirror cost_aware_snapshot_builder).
    yes_token, no_token = _resolve_yes_no_tokens(market)
    token = yes_token if side == "yes" else no_token
    if token is None:
        return _skip("unresolvable_token")

    # codex CRITICAL #2: a YES or NO token trade is ALWAYS a BUY of that token
    # against its ask book. PaperSide = Literal["buy","sell"] -- never "sell".
    executable_depth = _executable_ask_depth(book)
    max_executable_size = executable_depth
    order_size = min(config.paper_budget_size, executable_depth)
    if order_size <= 0:
        return _skip("no_executable_depth")

    order = PaperOrder(token_id=token.token_id, side="buy", size=order_size)
    fill = simulate_order_book_fill(order, book)

    side_result = (
        cost_aware_report.yes_result if side == "yes" else cost_aware_report.no_result
    )
    fair_probability_yes = cost_aware_report.fair_probability_yes
    model_probability = (
        fair_probability_yes if side == "yes" else (ONE - fair_probability_yes)
    )

    bid = book.bids[0].price if book.bids else None
    # claude IMPORTANT: screening_ready/valid_depth only constrains the ASK side,
    # so an asks-only book yields bid=None. ResearchPacket requires bid +
    # midpoint, and from_packet_and_fill raises on incomplete packet -- which
    # would crash the whole cycle (violating per-market isolation). Skip instead.
    if bid is None:
        return PaperExecutionResult(
            generated_at=generated_at,
            market_slug=market_slug,
            condition_id=condition_id,
            token_id=token.token_id,
            side=side,
            fill=None,
            record=None,
            skipped_reason="no_bid",
        )

    ask = side_result.executable_price
    midpoint = (bid + ask) / TWO
    theoretical_edge = model_probability - ask
    slippage_estimate = _research_slippage(book)
    cost_adjusted_edge = side_result.net_edge_per_share
    resolution_source = market.resolution_source or config.resolution_source_fallback

    # codex CRITICAL #3: ResearchPacket field is `created_at` (NOT generated_at),
    # `source_score` is REQUIRED (stringified screening_score), `rule_text_hash`
    # is the sha256 of the canonical rule_text. No __post_init__ on ResearchPacket
    # -> direct instantiation with all 29 fields is compliant.
    rule_text_hash = hashlib.sha256(config.rule_text.encode("utf-8")).hexdigest()
    packet = ResearchPacket(
        packet_id=f"paper-exec-{candidate.market_slug}-{side}",
        created_at=generated_at,
        condition_id=market.market.condition_id,
        token_id=token.token_id,
        market_slug=candidate.market_slug,
        question=candidate.question,
        source_score=str(candidate.screening_score),
        raw_archive_path=str(market_raw_archive_entry.payload_path),
        market_url=f"https://polymarket.com/event/{candidate.market_slug}",
        outcome_name=side.upper(),
        strategy_type=config.strategy_type,
        model_probability=model_probability,
        bid=bid,
        ask=ask,
        midpoint=midpoint,
        expected_entry_price=ask,
        fair_value_estimate=model_probability,
        theoretical_edge=theoretical_edge,
        spread=cost_aware_report.spread,
        slippage_estimate=slippage_estimate,
        cost_adjusted_edge=cost_adjusted_edge,
        confidence=cost_aware_report.confidence,
        max_executable_size=max_executable_size,
        risk_tags=(config.strategy_type,),
        thesis=config.thesis_template.format(
            reason_codes=",".join(candidate.reason_codes),
        ),
        invalidating_conditions=config.invalidating_conditions_template,
        rule_text=config.rule_text,
        rule_text_hash=rule_text_hash,
        resolution_source=resolution_source,
    )

    record = PaperTradeRecord.from_packet_and_fill(
        packet=packet,
        fill=fill,
        decision_timestamp=generated_at,
        order_book_raw_archive_path=str(raw_book_archive_entry.payload_path),
        order_book_raw_payload_sha256=raw_book_archive_entry.payload_sha256,
        account_equity_before_trade=config.account_equity_before_trade,
        sizing_limiter=config.sizing_limiter,
        planned_exit_rule=config.planned_exit_rule,
    )

    return PaperExecutionResult(
        generated_at=generated_at,
        market_slug=market_slug,
        condition_id=condition_id,
        token_id=token.token_id,
        side=side,
        fill=fill,
        record=record,
        skipped_reason=None,
    )


# --------------------------------------------------------------------------
# Internal helpers.
# --------------------------------------------------------------------------


def _resolve_yes_no_tokens(
    market: NormalizedMarket,
) -> tuple[Any | None, Any | None]:
    """Mirror cost_aware_snapshot_builder YES/NO resolution + outcome_index fallback."""
    yes_token = next(
        (
            token
            for token in market.tokens
            if token.outcome_name.strip().lower() in YES_NAMES
        ),
        None,
    )
    no_token = next(
        (
            token
            for token in market.tokens
            if token.outcome_name.strip().lower() in NO_NAMES
        ),
        None,
    )
    if yes_token is None or no_token is None:
        indexed = {token.outcome_index: token for token in market.tokens}
        yes_token = yes_token if yes_token is not None else indexed.get(0)
        no_token = no_token if no_token is not None else indexed.get(1)
    return yes_token, no_token


def _executable_ask_depth(book: OrderBookSnapshot) -> Decimal:
    """Sum of ask level sizes that ``simulate_order_book_fill`` would walk."""
    total = ZERO
    for level in book.asks:
        if _is_executable_level(level):
            total += level.size
    return total


def _research_slippage(book: OrderBookSnapshot) -> Decimal:
    """Midpoint-to-worst-executable-ask walk (0 when no executable asks/midpoint)."""
    worst_ask: Decimal | None = None
    for level in book.asks:
        if _is_executable_level(level):
            worst_ask = level.price
    if worst_ask is None:
        return _quantize_price(ZERO)
    midpoint = book.midpoint
    if midpoint is None:
        return _quantize_price(ZERO)
    return _quantize_price(worst_ask - midpoint)


def _is_executable_level(level: Any) -> bool:
    return (
        level.size.is_finite()
        and level.price.is_finite()
        and level.size > 0
        and level.price > 0
    )


def _quantize_price(value: Decimal) -> Decimal:
    _require_finite_decimal("price", value)
    return value.quantize(PRICE_QUANTUM)


def _validate_result_tree(result: PaperExecutionResult) -> None:
    PaperExecutionResult(
        generated_at=result.generated_at,
        market_slug=result.market_slug,
        condition_id=result.condition_id,
        token_id=result.token_id,
        side=result.side,
        fill=result.fill,
        record=result.record,
        skipped_reason=result.skipped_reason,
        paper_only=result.paper_only,
        report_only=result.report_only,
    )


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
