"""Paper position ledger and executable NAV marks."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from typing import Any, Iterator

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper import PaperOrder, simulate_order_book_fill

PRICE_QUANTUM = Decimal("0.001")
PRICE_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
MARK_STATUSES = frozenset(
    {
        "fully_executable",
        "partially_executable",
        "no_exit_depth",
    }
)


@dataclass(frozen=True)
class PaperPosition:
    source_packet_ids: tuple[str, ...]
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    market_raw_archive_path: str
    last_order_book_raw_archive_path: str
    last_order_book_raw_payload_sha256: str
    last_order_book_snapshot_sha256: str
    opened_at: datetime
    updated_at: datetime
    open_size: Decimal
    cost_basis: Decimal
    average_entry_price: Decimal
    realized_pnl: Decimal
    entry_trade_count: int
    exit_trade_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_packet_ids",
            _normalize_string_tuple("source_packet_ids", self.source_packet_ids),
        )
        object.__setattr__(
            self,
            "risk_tags",
            _normalize_string_tuple("risk_tags", self.risk_tags),
        )
        object.__setattr__(self, "opened_at", _as_utc(self.opened_at))
        object.__setattr__(self, "updated_at", _as_utc(self.updated_at))

        for field_name in (
            "condition_id",
            "token_id",
            "market_slug",
            "question",
            "outcome_name",
            "strategy_type",
            "rule_text_hash",
            "resolution_source",
            "market_raw_archive_path",
            "last_order_book_raw_archive_path",
        ):
            _require_nonblank_string(field_name, getattr(self, field_name))
        _require_nonblank_string("market_url", self.market_url)
        _require_sha256("last_order_book_raw_payload_sha256", self.last_order_book_raw_payload_sha256)
        _require_sha256("last_order_book_snapshot_sha256", self.last_order_book_snapshot_sha256)

        if self.opened_at > self.updated_at:
            raise ValueError("opened_at must not be after updated_at")
        _require_positive_decimal("open_size", self.open_size)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")
        _require_decimal("average_entry_price", self.average_entry_price)
        _require_price_domain("average_entry_price", self.average_entry_price)
        _require_finite_decimal("realized_pnl", self.realized_pnl)
        _require_nonnegative_int("entry_trade_count", self.entry_trade_count)
        _require_nonnegative_int("exit_trade_count", self.exit_trade_count)
        if self.entry_trade_count <= 0:
            raise ValueError("entry_trade_count must be positive")


@dataclass(frozen=True)
class PaperPortfolio:
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    positions: tuple[PaperPosition, ...]

    def __post_init__(self) -> None:
        _require_positive_decimal("starting_cash", self.starting_cash)
        _require_nonnegative_decimal("cash_balance", self.cash_balance)
        _require_finite_decimal("realized_pnl", self.realized_pnl)
        object.__setattr__(self, "positions", _normalize_position_tuple(self.positions))
        expected_starting_cash = _portfolio_starting_cash_identity(
            cash_balance=self.cash_balance,
            total_cost_basis=_exact_sum(position.cost_basis for position in self.positions),
            realized_pnl=self.realized_pnl,
        )
        if self.starting_cash != expected_starting_cash:
            raise ValueError("portfolio accounting identity is inconsistent")


@dataclass(frozen=True)
class PaperPositionMark:
    condition_id: str
    token_id: str
    market_slug: str
    outcome_name: str
    open_size: Decimal
    cost_basis: Decimal
    average_entry_price: Decimal
    order_book_captured_at: datetime
    order_book_snapshot_sha256: str
    exit_filled_size: Decimal
    exit_unfilled_size: Decimal
    exit_average_price: Decimal | None
    exit_worst_price: Decimal | None
    exit_value: Decimal
    midpoint_price: Decimal | None
    midpoint_value: Decimal | None
    best_bid: Decimal | None
    best_ask: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None
    mark_status: str

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "token_id",
            "market_slug",
            "outcome_name",
        ):
            _require_nonblank_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "order_book_captured_at",
            _as_utc(self.order_book_captured_at),
        )
        _require_sha256("order_book_snapshot_sha256", self.order_book_snapshot_sha256)
        _require_positive_decimal("open_size", self.open_size)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")
        _require_decimal("average_entry_price", self.average_entry_price)
        _require_price_domain("average_entry_price", self.average_entry_price)
        _require_nonnegative_decimal("exit_filled_size", self.exit_filled_size)
        _require_nonnegative_decimal("exit_unfilled_size", self.exit_unfilled_size)
        _require_nonnegative_decimal("exit_value", self.exit_value)
        if self.exit_value > self.exit_filled_size:
            raise ValueError("exit_value must not exceed exit_filled_size")
        for field_name in (
            "exit_average_price",
            "exit_worst_price",
            "midpoint_price",
            "best_bid",
            "best_ask",
        ):
            _require_price_domain(field_name, getattr(self, field_name))
        _require_optional_finite_decimal("midpoint_value", self.midpoint_value)
        if self.midpoint_value is not None and self.midpoint_value < 0:
            raise ValueError("midpoint_value must be nonnegative")
        if self.midpoint_value is not None and self.midpoint_value > self.open_size:
            raise ValueError("midpoint_value must not exceed open_size")
        _require_optional_finite_decimal("spread", self.spread)
        _require_optional_finite_decimal("slippage_estimate", self.slippage_estimate)
        if self.slippage_estimate is not None and self.slippage_estimate < 0:
            raise ValueError("slippage_estimate must be nonnegative")
        if self.mark_status not in MARK_STATUSES:
            raise ValueError("mark_status must be a known mark status")
        if _add(self.exit_filled_size, self.exit_unfilled_size) != self.open_size:
            raise ValueError("exit_filled_size plus exit_unfilled_size must equal open_size")
        if self.mark_status == "fully_executable" and self.exit_unfilled_size != 0:
            raise ValueError("exit_unfilled_size must be zero for fully_executable marks")
        if self.mark_status == "partially_executable" and (
            self.exit_filled_size <= 0 or self.exit_unfilled_size <= 0
        ):
            raise ValueError("partially_executable marks require filled and unfilled size")
        if self.mark_status == "no_exit_depth" and self.exit_filled_size != 0:
            raise ValueError("exit_filled_size must be zero for no_exit_depth marks")
        if self.exit_filled_size == 0 and self.exit_value != 0:
            raise ValueError("exit_value must be zero when exit_filled_size is zero")
        if self.exit_filled_size == 0:
            if self.exit_average_price is not None or self.exit_worst_price is not None:
                raise ValueError("exit prices must be absent when exit_filled_size is zero")
        elif self.exit_average_price is None or self.exit_worst_price is None:
            raise ValueError("exit prices are required when exit_filled_size is positive")


@dataclass(frozen=True)
class PaperNavSnapshot:
    marked_at: datetime
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    unrealized_exit_pnl: Decimal
    marks: tuple[PaperPositionMark, ...]
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "marked_at", _as_utc(self.marked_at))
        object.__setattr__(self, "marks", _normalize_mark_tuple(self.marks))
        _require_positive_decimal("starting_cash", self.starting_cash)
        _require_nonnegative_decimal("cash_balance", self.cash_balance)
        _require_finite_decimal("realized_pnl", self.realized_pnl)
        _require_nonnegative_decimal("exit_nav", self.exit_nav)
        _require_optional_finite_decimal("midpoint_nav", self.midpoint_nav)
        if self.midpoint_nav is not None and self.midpoint_nav < 0:
            raise ValueError("midpoint_nav must be nonnegative")
        _require_nonnegative_decimal("total_cost_basis", self.total_cost_basis)
        _require_finite_decimal("unrealized_exit_pnl", self.unrealized_exit_pnl)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")

        expected_exit_nav = _add(
            self.cash_balance,
            _exact_sum(mark.exit_value for mark in self.marks),
        )
        if self.exit_nav != expected_exit_nav:
            raise ValueError("exit_nav must equal cash_balance plus mark exit values")

        if all(mark.midpoint_value is not None for mark in self.marks):
            expected_midpoint_nav = _add(
                self.cash_balance,
                _exact_sum(
                    mark.midpoint_value for mark in self.marks if mark.midpoint_value is not None
                ),
            )
            if self.midpoint_nav != expected_midpoint_nav:
                raise ValueError("midpoint_nav must equal cash_balance plus midpoint values")
        elif self.midpoint_nav is not None:
            raise ValueError("midpoint_nav must be None when any mark lacks midpoint_value")

        expected_cost_basis = _exact_sum(mark.cost_basis for mark in self.marks)
        if self.total_cost_basis != expected_cost_basis:
            raise ValueError("total_cost_basis must equal summed mark cost_basis")
        expected_unrealized = _exact_sum(
            _subtract(mark.exit_value, mark.cost_basis) for mark in self.marks
        )
        if self.unrealized_exit_pnl != expected_unrealized:
            raise ValueError("unrealized_exit_pnl must equal summed mark exit PnL")
        expected_starting_cash = _portfolio_starting_cash_identity(
            cash_balance=self.cash_balance,
            total_cost_basis=self.total_cost_basis,
            realized_pnl=self.realized_pnl,
        )
        if self.starting_cash != expected_starting_cash:
            raise ValueError("snapshot accounting identity is inconsistent")


@dataclass(frozen=True)
class PaperNavLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, snapshot: PaperNavSnapshot) -> None:
        if not isinstance(snapshot, PaperNavSnapshot):
            raise ValueError("snapshot must be a PaperNavSnapshot")
        line = json.dumps(_json_ready(asdict(snapshot)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    @staticmethod
    def read(path: Path | str) -> tuple[PaperNavSnapshot, ...]:
        """Read a NAV JSONL log back into fully-typed snapshots.

        Reverses ``append``'s ``_json_ready(asdict(...))`` serialization using
        the shared recursive ``json_recovery.from_jsonable`` helper.
        ``PaperNavSnapshot`` has a validating ``__post_init__`` that checks the
        nested ``marks: tuple[PaperPositionMark, ...]`` via ``isinstance`` and
        enforces accounting identities -- a flat coercion would raise. The
        helper reconstructs each ``PaperPositionMark`` (Decimal/datetime/
        optional fields) so ``__post_init__`` re-validates each snapshot. Blank
        lines are skipped; a non-JSON line raises ``ValueError`` with the line
        number. An empty file yields an empty tuple.
        """
        target = Path(path)
        records: list[PaperNavSnapshot] = []
        with target.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"nav log line {line_number} is not valid JSON: {exc}"
                    ) from exc
                records.append(from_jsonable(PaperNavSnapshot, row))
        return tuple(records)


def build_paper_portfolio(
    records: Iterable[PaperTradeRecord],
    *,
    starting_cash: Decimal,
) -> PaperPortfolio:
    _require_positive_decimal("starting_cash", starting_cash)
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable of PaperTradeRecord values")
    try:
        record_tuple = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be an iterable of PaperTradeRecord values") from exc

    seen_packet_ids: set[str] = set()
    metadata_by_token: dict[str, PaperTradeRecord] = {}
    for record in record_tuple:
        if not isinstance(record, PaperTradeRecord):
            raise ValueError("record must be a PaperTradeRecord")
        _validate_trade_record(record)
        if record.packet_id in seen_packet_ids:
            raise ValueError("duplicate packet_id in paper trade records")
        seen_packet_ids.add(record.packet_id)
        metadata_anchor = metadata_by_token.get(record.token_id)
        if metadata_anchor is None:
            metadata_by_token[record.token_id] = record
        else:
            _validate_record_metadata_consistency(metadata_anchor, record)

    cash_balance = starting_cash
    realized_pnl = Decimal("0")
    positions_by_token: dict[str, PaperPosition] = {}

    for record in record_tuple:
        quantity = record.fill_filled_size
        price = record.fill_average_price
        notional = _multiply(quantity, price)
        existing = positions_by_token.get(record.token_id)

        if record.order_side == "buy":
            if notional > cash_balance:
                raise ValueError("cash balance is insufficient for buy fill")
            cash_balance = _subtract(cash_balance, notional)
            if existing is None:
                positions_by_token[record.token_id] = _position_from_buy_record(record, notional)
            else:
                _validate_metadata_consistency(existing, record)
                new_size = _add(existing.open_size, quantity)
                new_cost_basis = _add(existing.cost_basis, notional)
                positions_by_token[record.token_id] = replace(
                    existing,
                    source_packet_ids=(*existing.source_packet_ids, record.packet_id),
                    risk_tags=_merge_string_tuples(existing.risk_tags, record.risk_tags),
                    last_order_book_raw_archive_path=record.order_book_raw_archive_path,
                    last_order_book_raw_payload_sha256=record.order_book_raw_payload_sha256,
                    last_order_book_snapshot_sha256=record.order_book_snapshot_sha256,
                    updated_at=_as_utc(record.decision_timestamp_utc),
                    open_size=new_size,
                    cost_basis=new_cost_basis,
                    average_entry_price=_quantize_price(_divide(new_cost_basis, new_size)),
                    entry_trade_count=existing.entry_trade_count + 1,
                )
            continue

        if existing is None:
            raise ValueError("sell requires an open position")
        _validate_metadata_consistency(existing, record)
        if quantity > existing.open_size:
            raise ValueError("sell filled_size exceeds open_size")

        cash_balance = _add(cash_balance, notional)
        cost_relieved = _proportional_cost_basis(
            cost_basis=existing.cost_basis,
            sold_size=quantity,
            open_size=existing.open_size,
        )
        realized_delta = _subtract(notional, cost_relieved)
        realized_pnl = _add(realized_pnl, realized_delta)
        new_size = _subtract(existing.open_size, quantity)
        if new_size == 0:
            del positions_by_token[record.token_id]
            continue

        new_cost_basis = _subtract(existing.cost_basis, cost_relieved)
        positions_by_token[record.token_id] = replace(
            existing,
            source_packet_ids=(*existing.source_packet_ids, record.packet_id),
            risk_tags=_merge_string_tuples(existing.risk_tags, record.risk_tags),
            last_order_book_raw_archive_path=record.order_book_raw_archive_path,
            last_order_book_raw_payload_sha256=record.order_book_raw_payload_sha256,
            last_order_book_snapshot_sha256=record.order_book_snapshot_sha256,
            updated_at=_as_utc(record.decision_timestamp_utc),
            open_size=new_size,
            cost_basis=new_cost_basis,
            average_entry_price=_quantize_price(_divide(new_cost_basis, new_size)),
            realized_pnl=_add(existing.realized_pnl, realized_delta),
            exit_trade_count=existing.exit_trade_count + 1,
        )

    return PaperPortfolio(
        starting_cash=starting_cash,
        cash_balance=cash_balance,
        realized_pnl=realized_pnl,
        positions=tuple(positions_by_token.values()),
    )


def mark_paper_nav(
    portfolio: PaperPortfolio,
    books_by_token_id: Mapping[str, OrderBookSnapshot],
    *,
    marked_at: datetime,
) -> PaperNavSnapshot:
    if not isinstance(portfolio, PaperPortfolio):
        raise ValueError("portfolio must be a PaperPortfolio")
    if not isinstance(books_by_token_id, Mapping):
        raise ValueError("books_by_token_id must be a mapping")

    for token_id, book in books_by_token_id.items():
        if not isinstance(token_id, str) or not token_id.strip():
            raise ValueError("books_by_token_id keys must be token id strings")
        if not isinstance(book, OrderBookSnapshot):
            raise ValueError("books_by_token_id values must be OrderBookSnapshot values")
        if token_id != book.token_id:
            raise ValueError("books_by_token_id key must match book token_id")

    marks: list[PaperPositionMark] = []
    for position in portfolio.positions:
        book = books_by_token_id.get(position.token_id)
        if book is None:
            raise ValueError(f"missing order book for token_id {position.token_id}")
        if book.token_id != position.token_id:
            raise ValueError("order book token_id must match position token_id")

        order = PaperOrder(token_id=position.token_id, side="sell", size=position.open_size)
        exit_fill = simulate_order_book_fill(order, book)
        exact_filled_size, exit_value = _bid_depth_notional(position.open_size, book)
        if exact_filled_size != exit_fill.filled_size:
            raise ValueError("exit filled size mismatch")

        if exit_fill.filled_size == 0:
            mark_status = "no_exit_depth"
        elif exit_fill.unfilled_size > 0:
            mark_status = "partially_executable"
        else:
            mark_status = "fully_executable"

        midpoint_value = (
            None
            if exit_fill.midpoint is None
            else _multiply(position.open_size, exit_fill.midpoint)
        )
        marks.append(
            PaperPositionMark(
                condition_id=position.condition_id,
                token_id=position.token_id,
                market_slug=position.market_slug,
                outcome_name=position.outcome_name,
                open_size=position.open_size,
                cost_basis=position.cost_basis,
                average_entry_price=position.average_entry_price,
                order_book_captured_at=exit_fill.order_book_captured_at,
                order_book_snapshot_sha256=exit_fill.order_book_snapshot_sha256,
                exit_filled_size=exit_fill.filled_size,
                exit_unfilled_size=exit_fill.unfilled_size,
                exit_average_price=exit_fill.average_price,
                exit_worst_price=exit_fill.worst_price,
                exit_value=exit_value,
                midpoint_price=exit_fill.midpoint,
                midpoint_value=midpoint_value,
                best_bid=exit_fill.best_bid,
                best_ask=exit_fill.best_ask,
                spread=exit_fill.spread,
                slippage_estimate=exit_fill.slippage_estimate,
                mark_status=mark_status,
            )
        )

    mark_tuple = tuple(marks)
    exit_nav = _add(portfolio.cash_balance, _exact_sum(mark.exit_value for mark in mark_tuple))
    midpoint_nav = (
        _add(
            portfolio.cash_balance,
            _exact_sum(
                mark.midpoint_value
                for mark in mark_tuple
                if mark.midpoint_value is not None
            ),
        )
        if all(mark.midpoint_value is not None for mark in mark_tuple)
        else None
    )
    total_cost_basis = _exact_sum(mark.cost_basis for mark in mark_tuple)
    unrealized_exit_pnl = _exact_sum(_subtract(mark.exit_value, mark.cost_basis) for mark in mark_tuple)
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=portfolio.starting_cash,
        cash_balance=portfolio.cash_balance,
        realized_pnl=portfolio.realized_pnl,
        exit_nav=exit_nav,
        midpoint_nav=midpoint_nav,
        total_cost_basis=total_cost_basis,
        unrealized_exit_pnl=unrealized_exit_pnl,
        marks=mark_tuple,
    )


def _position_from_buy_record(record: PaperTradeRecord, cost_basis: Decimal) -> PaperPosition:
    return PaperPosition(
        source_packet_ids=(record.packet_id,),
        condition_id=record.condition_id,
        token_id=record.token_id,
        market_slug=record.market_slug,
        market_url=record.market_url,
        question=record.question,
        outcome_name=record.outcome_name,
        strategy_type=record.strategy_type,
        risk_tags=record.risk_tags,
        rule_text_hash=record.rule_text_hash,
        resolution_source=record.resolution_source,
        market_raw_archive_path=record.market_raw_archive_path,
        last_order_book_raw_archive_path=record.order_book_raw_archive_path,
        last_order_book_raw_payload_sha256=record.order_book_raw_payload_sha256,
        last_order_book_snapshot_sha256=record.order_book_snapshot_sha256,
        opened_at=record.decision_timestamp_utc,
        updated_at=record.decision_timestamp_utc,
        open_size=record.fill_filled_size,
        cost_basis=cost_basis,
        average_entry_price=_quantize_price(_divide(cost_basis, record.fill_filled_size)),
        realized_pnl=Decimal("0"),
        entry_trade_count=1,
        exit_trade_count=0,
    )


def _validate_metadata_consistency(position: PaperPosition, record: PaperTradeRecord) -> None:
    for field_name in (
        "condition_id",
        "market_slug",
        "market_url",
        "question",
        "outcome_name",
        "strategy_type",
        "rule_text_hash",
        "resolution_source",
    ):
        if getattr(position, field_name) != getattr(record, field_name):
            raise ValueError(f"metadata mismatch for token_id {record.token_id}: {field_name}")


def _validate_record_metadata_consistency(
    anchor: PaperTradeRecord,
    record: PaperTradeRecord,
) -> None:
    for field_name in (
        "condition_id",
        "market_slug",
        "market_url",
        "question",
        "outcome_name",
        "strategy_type",
        "rule_text_hash",
        "resolution_source",
    ):
        if getattr(anchor, field_name) != getattr(record, field_name):
            raise ValueError(f"metadata mismatch for token_id {record.token_id}: {field_name}")


def _validate_trade_record(record: PaperTradeRecord) -> None:
    for field_name in (
        "packet_id",
        "condition_id",
        "token_id",
        "market_slug",
        "question",
        "outcome_name",
        "strategy_type",
        "market_raw_archive_path",
        "order_book_raw_archive_path",
        "rule_text_hash",
        "resolution_source",
    ):
        _require_nonblank_string(field_name, getattr(record, field_name))
    _require_nonblank_string("market_url", record.market_url)
    _require_sha256("order_book_raw_payload_sha256", record.order_book_raw_payload_sha256)
    _require_sha256("order_book_snapshot_sha256", record.order_book_snapshot_sha256)
    _normalize_string_tuple("risk_tags", record.risk_tags)
    _as_utc(record.decision_timestamp_utc)
    _as_utc(record.order_book_captured_at)
    if record.order_side not in ("buy", "sell"):
        raise ValueError("order_side must be buy or sell")
    _require_positive_decimal("order_requested_size", record.order_requested_size)
    _require_positive_decimal("fill_filled_size", record.fill_filled_size)
    _require_nonnegative_decimal("fill_unfilled_size", record.fill_unfilled_size)
    if _add(record.fill_filled_size, record.fill_unfilled_size) != record.order_requested_size:
        raise ValueError("fill accounting must match requested size")
    expected_fill_status = "complete" if record.fill_unfilled_size == 0 else "partial"
    if record.fill_status != expected_fill_status:
        raise ValueError("fill_status must match fill accounting")
    _require_decimal("fill_average_price", record.fill_average_price)
    _require_decimal("fill_worst_price", record.fill_worst_price)
    _require_price_domain("fill_average_price", record.fill_average_price)
    _require_price_domain("fill_worst_price", record.fill_worst_price)
    for field_name in (
        "fill_best_bid",
        "fill_best_ask",
        "fill_midpoint",
    ):
        _require_price_domain(field_name, getattr(record, field_name))
    for field_name in ("fill_spread", "fill_slippage_estimate"):
        _require_optional_finite_decimal(field_name, getattr(record, field_name))


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime values are required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must include at least one value")
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain nonblank strings")
        if item != item.strip():
            raise ValueError(f"{field_name} must contain canonical strings")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _merge_string_tuples(left: Iterable[str], right: Iterable[str]) -> tuple[str, ...]:
    merged = (*_normalize_string_tuple("risk_tags", left), *_normalize_string_tuple("risk_tags", right))
    return tuple(dict.fromkeys(merged))


def _normalize_position_tuple(value: Iterable[PaperPosition]) -> tuple[PaperPosition, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("positions must be a sequence of PaperPosition values")
    try:
        positions = tuple(value)
    except TypeError as exc:
        raise ValueError("positions must be a sequence of PaperPosition values") from exc
    seen: set[str] = set()
    for position in positions:
        if not isinstance(position, PaperPosition):
            raise ValueError("positions must contain PaperPosition values")
        if position.token_id in seen:
            raise ValueError("positions must have unique token_id values")
        seen.add(position.token_id)
    return tuple(sorted(positions, key=_position_sort_key))


def _normalize_mark_tuple(value: Iterable[PaperPositionMark]) -> tuple[PaperPositionMark, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("marks must be a sequence of PaperPositionMark values")
    try:
        marks = tuple(value)
    except TypeError as exc:
        raise ValueError("marks must be a sequence of PaperPositionMark values") from exc
    seen: set[str] = set()
    for mark in marks:
        if not isinstance(mark, PaperPositionMark):
            raise ValueError("marks must contain PaperPositionMark values")
        if mark.token_id in seen:
            raise ValueError("marks must have unique token_id values")
        seen.add(mark.token_id)
    return tuple(sorted(marks, key=_mark_sort_key))


def _position_sort_key(position: PaperPosition) -> tuple[str, str, str, str, str]:
    return (
        position.condition_id,
        position.token_id,
        position.market_slug,
        position.outcome_name,
        position.strategy_type,
    )


def _mark_sort_key(mark: PaperPositionMark) -> tuple[str, str, str, str]:
    return (mark.condition_id, mark.token_id, mark.market_slug, mark.outcome_name)


def _require_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")


def _require_nonblank_string(field_name: str, value: str) -> None:
    _require_string(field_name, value)
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_price_domain(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    _require_finite_decimal(field_name, value)
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be in [0, 1]")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _is_sha256(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(field_name: str, value: str) -> None:
    if not _is_sha256(value):
        raise ValueError(f"{field_name} must be a lowercase 64-character SHA-256 digest")


def _quantize_price(value: Decimal) -> Decimal:
    with localcontext(PRICE_CONTEXT):
        return value.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _add(left: Decimal, right: Decimal) -> Decimal:
    with _exact_decimal_context(left, right):
        return left + right


def _subtract(left: Decimal, right: Decimal) -> Decimal:
    with _exact_decimal_context(left, right):
        return left - right


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    with _exact_decimal_context(left, right):
        return left * right


def _divide(left: Decimal, right: Decimal) -> Decimal:
    with _exact_decimal_context(left, right, PRICE_QUANTUM):
        return left / right


def _proportional_cost_basis(
    *,
    cost_basis: Decimal,
    sold_size: Decimal,
    open_size: Decimal,
) -> Decimal:
    _require_nonnegative_decimal("cost_basis", cost_basis)
    _require_positive_decimal("sold_size", sold_size)
    _require_positive_decimal("open_size", open_size)
    if sold_size > open_size:
        raise ValueError("sold_size must not exceed open_size")
    return _divide(_multiply(cost_basis, sold_size), open_size)


def _portfolio_starting_cash_identity(
    *,
    cash_balance: Decimal,
    total_cost_basis: Decimal,
    realized_pnl: Decimal,
) -> Decimal:
    return _subtract(_add(cash_balance, total_cost_basis), realized_pnl)


def _exact_sum(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    for index, item in enumerate(items):
        _require_finite_decimal(f"sum value {index}", item)
    with _exact_decimal_context(*items):
        total = Decimal("0")
        for item in items:
            total += item
        return total


def _bid_depth_notional(
    requested_size: Decimal,
    book: OrderBookSnapshot,
) -> tuple[Decimal, Decimal]:
    _require_positive_decimal("requested_size", requested_size)
    filled_size = Decimal("0")
    notional = Decimal("0")
    for level in book.bids:
        if not _is_executable_level(level):
            continue
        remaining_size = _subtract(requested_size, filled_size)
        if remaining_size <= 0:
            break
        level_fill_size = min(remaining_size, level.size)
        filled_size = _add(filled_size, level_fill_size)
        notional = _add(notional, _multiply(level_fill_size, level.price))
    return filled_size, notional


def _is_executable_level(level: OrderBookLevel) -> bool:
    return (
        level.size.is_finite()
        and level.price.is_finite()
        and level.size > 0
        and level.price > 0
    )


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("nav log Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("nav log values must not be floats")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("nav log object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("nav log values must be JSON serializable")


@contextmanager
def _exact_decimal_context(*values: Decimal) -> Iterator[None]:
    with localcontext(Context(prec=_exact_decimal_precision(values), rounding=ROUND_HALF_EVEN)):
        yield


def _exact_decimal_precision(values: tuple[Decimal, ...]) -> int:
    finite_values = [value for value in values if value.is_finite()]
    if not finite_values:
        return 28
    required_digits = sum(
        _integer_digit_count(value) + _fractional_digit_count(value)
        for value in finite_values
    )
    return max(28, required_digits + len(finite_values) + 2)


def _integer_digit_count(value: Decimal) -> int:
    if value.is_zero():
        return 1
    return max(value.adjusted() + 1, 0)


def _fractional_digit_count(value: Decimal) -> int:
    return max(-value.as_tuple().exponent, 0)
