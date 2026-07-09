"""Paper-only liquidity exit-friction report for manual research review."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-market-liquidity-exit-friction-report-v1"

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
EXIT_FRICTION_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
PUBLIC_METADATA_FORBIDDEN_FRAGMENTS = (
    "candidate",
    "market-id",
    "market_id",
    "market-slug",
    "market_slug",
    "question",
    "://",
    "url=",
    "source-url",
    "source_url",
    "source text",
    "source_text",
    "dsn",
    "table=",
    "table:",
    "token",
    "secret",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
)

MISSING_SNAPSHOTS_REASON = "missing_liquidity_snapshots"
BID_DEPTH_BLOCK_REASON = "bid_depth_block"
ASK_DEPTH_IMBALANCE_WATCH_REASON = "ask_depth_imbalance_watch"
ASK_DEPTH_IMBALANCE_BLOCK_REASON = "ask_depth_imbalance_block"
SPREAD_WATCH_REASON = "spread_watch"
SPREAD_BLOCK_REASON = "spread_block"
DEPTH_DECAY_WATCH_REASON = "depth_decay_watch"
DEPTH_DECAY_BLOCK_REASON = "depth_decay_block"
SETTLEMENT_WINDOW_WATCH_REASON = "settlement_window_watch"
SETTLEMENT_WINDOW_BLOCK_REASON = "settlement_window_block"
VOLATILITY_WATCH_REASON = "volatility_watch"
VOLATILITY_BLOCK_REASON = "volatility_block"
FEE_DRAG_WATCH_REASON = "fee_drag_watch"
FEE_DRAG_BLOCK_REASON = "fee_drag_block"
SCORE_PASS_REASON = "score_pass"
SCORE_WATCH_REASON = "score_watch"
SCORE_BLOCK_REASON = "score_block"
REASON_CODES = (
    MISSING_SNAPSHOTS_REASON,
    BID_DEPTH_BLOCK_REASON,
    ASK_DEPTH_IMBALANCE_WATCH_REASON,
    ASK_DEPTH_IMBALANCE_BLOCK_REASON,
    SPREAD_WATCH_REASON,
    SPREAD_BLOCK_REASON,
    DEPTH_DECAY_WATCH_REASON,
    DEPTH_DECAY_BLOCK_REASON,
    SETTLEMENT_WINDOW_WATCH_REASON,
    SETTLEMENT_WINDOW_BLOCK_REASON,
    VOLATILITY_WATCH_REASON,
    VOLATILITY_BLOCK_REASON,
    FEE_DRAG_WATCH_REASON,
    FEE_DRAG_BLOCK_REASON,
    SCORE_PASS_REASON,
    SCORE_WATCH_REASON,
    SCORE_BLOCK_REASON,
)

MONEY_QUANT = Decimal("0.0000")
RATIO_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1.000000")

BID_DEPTH_WEIGHT = Decimal("0.250000")
ASK_HEAVY_IMBALANCE_WEIGHT = Decimal("0.112500")
BID_HEAVY_IMBALANCE_WEIGHT = Decimal("0.025000")
SPREAD_WEIGHT = Decimal("0.200000")
DEPTH_DECAY_WEIGHT = Decimal("0.150000")
SETTLEMENT_WINDOW_WEIGHT = Decimal("0.100000")
VOLATILITY_WEIGHT = Decimal("0.100000")
FEE_DRAG_WEIGHT = Decimal("0.100000")

WATCH_FACTOR_RATIO = Decimal("0.500000")
BLOCK_FACTOR_RATIO = Decimal("1.000000")
ASK_IMBALANCE_BLOCK_RATIO = Decimal("0.900000")


@dataclass(frozen=True)
class ResearchMarketLiquidityExitFrictionConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_exit_friction_threshold: Decimal = Decimal("0.350000")
    block_exit_friction_threshold: Decimal = Decimal("0.700000")
    reference_bid_depth: Decimal = Decimal("100.0000")
    wide_spread_threshold: Decimal = Decimal("0.040000")
    steep_depth_decay_threshold: Decimal = Decimal("0.500000")
    long_settlement_window_hours: Decimal = Decimal("48.000000")
    high_volatility_threshold: Decimal = Decimal("0.200000")
    high_fee_drag_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitFrictionConfig, "config")
        _require_public_metadata_string("config_version", self.config_version)
        for field_name in (
            "pass_exit_friction_threshold",
            "block_exit_friction_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.pass_exit_friction_threshold > self.block_exit_friction_threshold:
            raise ValueError(
                "pass_exit_friction_threshold must be <= block_exit_friction_threshold",
            )
        object.__setattr__(
            self,
            "reference_bid_depth",
            _normalize_positive_money("reference_bid_depth", self.reference_bid_depth),
        )
        for field_name in (
            "wide_spread_threshold",
            "steep_depth_decay_threshold",
            "high_volatility_threshold",
            "high_fee_drag_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "long_settlement_window_hours",
            _normalize_positive_decimal(
                "long_settlement_window_hours",
                self.long_settlement_window_hours,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitFrictionSnapshot:
    review_reference: str
    observed_at: datetime
    bid_depth: Decimal
    ask_depth: Decimal
    spread: Decimal
    depth_decay: Decimal
    settlement_window_hours: Decimal
    volatility: Decimal
    fee_drag: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityExitFrictionSnapshot,
            "snapshot",
        )
        _require_canonical_string("review_reference", self.review_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("bid_depth", "ask_depth"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_money(field_name, getattr(self, field_name)),
            )
        for field_name in ("spread", "depth_decay", "volatility", "fee_drag"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_window_hours",
            _normalize_nonnegative_decimal(
                "settlement_window_hours",
                self.settlement_window_hours,
            ),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitFrictionReportRow:
    review_digest: str
    observed_at: datetime
    bid_depth: Decimal
    ask_depth: Decimal
    spread: Decimal
    depth_decay: Decimal
    settlement_window_hours: Decimal
    volatility: Decimal
    fee_drag: Decimal
    bid_depth_score: Decimal
    ask_depth_imbalance_score: Decimal
    spread_score: Decimal
    depth_decay_score: Decimal
    settlement_window_score: Decimal
    volatility_score: Decimal
    fee_drag_score: Decimal
    exit_friction_score: Decimal
    exit_friction_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityExitFrictionReportRow,
            "report row",
        )
        _require_validation_digest("review_digest", self.review_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("bid_depth", "ask_depth"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_money(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_window_hours",
            _normalize_nonnegative_decimal(
                "settlement_window_hours",
                self.settlement_window_hours,
            ),
        )
        for field_name in (
            "spread",
            "depth_decay",
            "volatility",
            "fee_drag",
            "bid_depth_score",
            "ask_depth_imbalance_score",
            "spread_score",
            "depth_decay_score",
            "settlement_window_score",
            "volatility_score",
            "fee_drag_score",
            "exit_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("exit_friction_status", self.exit_friction_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitFrictionReport:
    generated_at: datetime
    config_version: str
    source_snapshot_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_exit_friction_score: Decimal
    exit_friction_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    rows: tuple[ResearchMarketLiquidityExitFrictionReportRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitFrictionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_snapshot_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "highest_exit_friction_score",
            _normalize_ratio(
                "highest_exit_friction_score",
                self.highest_exit_friction_score,
            ),
        )
        _require_status("exit_friction_status", self.exit_friction_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_validation_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_market_liquidity_exit_friction_report(
    snapshots: (
        list[ResearchMarketLiquidityExitFrictionSnapshot]
        | tuple[ResearchMarketLiquidityExitFrictionSnapshot, ...]
    ),
    *,
    config: ResearchMarketLiquidityExitFrictionConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityExitFrictionReport:
    if type(config) is not ResearchMarketLiquidityExitFrictionConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityExitFrictionConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        sorted(
            (
                _row_from_snapshot(snapshot, config=config)
                for snapshot in source_snapshots
            ),
            key=_row_sort_key,
        ),
    )
    pass_count = _status_count(rows, PASS_STATUS)
    watch_count = _status_count(rows, WATCH_STATUS)
    block_count = _status_count(rows, BLOCK_STATUS)
    highest_score = rows[0].exit_friction_score if rows else _zero_ratio()
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)
    digest_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "source_snapshot_count": Decimal(len(source_snapshots)),
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "highest_exit_friction_score": highest_score,
        "exit_friction_status": status,
        "reason_codes": reason_codes,
        "rows": tuple(asdict(row) for row in rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketLiquidityExitFrictionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_snapshot_count=Decimal(len(source_snapshots)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        highest_exit_friction_score=highest_score,
        exit_friction_status=status,
        reason_codes=reason_codes,
        derived_validation_digest=_derived_validation_digest_for_values(digest_values),
        rows=rows,
    )


def research_market_liquidity_exit_friction_report_payload(
    report: ResearchMarketLiquidityExitFrictionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityExitFrictionReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityExitFrictionReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _row_from_snapshot(
    snapshot: ResearchMarketLiquidityExitFrictionSnapshot,
    *,
    config: ResearchMarketLiquidityExitFrictionConfig,
) -> ResearchMarketLiquidityExitFrictionReportRow:
    bid_depth_score = _bid_depth_score(snapshot.bid_depth, config.reference_bid_depth)
    ask_depth_imbalance_score = _ask_depth_imbalance_score(
        snapshot.bid_depth,
        snapshot.ask_depth,
    )
    spread_score = _weighted_threshold_score(
        snapshot.spread,
        config.wide_spread_threshold,
        SPREAD_WEIGHT,
    )
    depth_decay_score = _weighted_threshold_score(
        snapshot.depth_decay,
        config.steep_depth_decay_threshold,
        DEPTH_DECAY_WEIGHT,
    )
    settlement_window_score = _weighted_threshold_score(
        snapshot.settlement_window_hours,
        config.long_settlement_window_hours,
        SETTLEMENT_WINDOW_WEIGHT,
    )
    volatility_score = _weighted_threshold_score(
        snapshot.volatility,
        config.high_volatility_threshold,
        VOLATILITY_WEIGHT,
    )
    fee_drag_score = _weighted_threshold_score(
        snapshot.fee_drag,
        config.high_fee_drag_threshold,
        FEE_DRAG_WEIGHT,
    )
    exit_friction_score = _quantize_ratio(
        min(
            DECIMAL_ONE,
            bid_depth_score
            + ask_depth_imbalance_score
            + spread_score
            + depth_decay_score
            + settlement_window_score
            + volatility_score
            + fee_drag_score,
        ),
    )
    status = _score_status(exit_friction_score, config)
    return ResearchMarketLiquidityExitFrictionReportRow(
        review_digest=_review_digest(snapshot.review_reference),
        observed_at=snapshot.observed_at,
        bid_depth=snapshot.bid_depth,
        ask_depth=snapshot.ask_depth,
        spread=snapshot.spread,
        depth_decay=snapshot.depth_decay,
        settlement_window_hours=snapshot.settlement_window_hours,
        volatility=snapshot.volatility,
        fee_drag=snapshot.fee_drag,
        bid_depth_score=bid_depth_score,
        ask_depth_imbalance_score=ask_depth_imbalance_score,
        spread_score=spread_score,
        depth_decay_score=depth_decay_score,
        settlement_window_score=settlement_window_score,
        volatility_score=volatility_score,
        fee_drag_score=fee_drag_score,
        exit_friction_score=exit_friction_score,
        exit_friction_status=status,
        reason_codes=_row_reason_codes(
            snapshot,
            config=config,
            exit_friction_status=status,
        ),
    )


def _review_digest(review_reference: str) -> str:
    return sha256(review_reference.encode("utf-8")).hexdigest()


def _bid_depth_score(bid_depth: Decimal, reference_bid_depth: Decimal) -> Decimal:
    if bid_depth >= reference_bid_depth:
        return _zero_ratio()
    return _quantize_ratio(
        ((reference_bid_depth - bid_depth) / reference_bid_depth) * BID_DEPTH_WEIGHT,
    )


def _ask_depth_imbalance_score(bid_depth: Decimal, ask_depth: Decimal) -> Decimal:
    total_depth = bid_depth + ask_depth
    if total_depth == DECIMAL_ZERO or bid_depth == ask_depth:
        return _zero_ratio()
    if ask_depth > bid_depth:
        return _quantize_ratio(
            ((ask_depth - bid_depth) / total_depth) * ASK_HEAVY_IMBALANCE_WEIGHT,
        )
    return _quantize_ratio(
        ((bid_depth - ask_depth) / total_depth) * BID_HEAVY_IMBALANCE_WEIGHT,
    )


def _weighted_threshold_score(
    observed_value: Decimal,
    threshold: Decimal,
    weight: Decimal,
) -> Decimal:
    threshold_ratio = min(DECIMAL_ONE, observed_value / threshold)
    return _quantize_ratio(threshold_ratio * weight)


def _score_status(
    exit_friction_score: Decimal,
    config: ResearchMarketLiquidityExitFrictionConfig,
) -> str:
    if exit_friction_score >= config.block_exit_friction_threshold:
        return BLOCK_STATUS
    if exit_friction_score >= config.pass_exit_friction_threshold:
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[ResearchMarketLiquidityExitFrictionReportRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.exit_friction_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.exit_friction_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    snapshot: ResearchMarketLiquidityExitFrictionSnapshot,
    *,
    config: ResearchMarketLiquidityExitFrictionConfig,
    exit_friction_status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    bid_depth_ratio = snapshot.bid_depth / config.reference_bid_depth
    if bid_depth_ratio < config.pass_exit_friction_threshold:
        reasons.append(BID_DEPTH_BLOCK_REASON)
    ask_imbalance_ratio = _ask_heavy_imbalance_ratio(
        snapshot.bid_depth,
        snapshot.ask_depth,
    )
    if ask_imbalance_ratio >= ASK_IMBALANCE_BLOCK_RATIO:
        reasons.append(ASK_DEPTH_IMBALANCE_BLOCK_REASON)
    elif ask_imbalance_ratio >= WATCH_FACTOR_RATIO:
        reasons.append(ASK_DEPTH_IMBALANCE_WATCH_REASON)
    reasons.extend(
        _factor_reason(
            snapshot.spread,
            config.wide_spread_threshold,
            SPREAD_WATCH_REASON,
            SPREAD_BLOCK_REASON,
        ),
    )
    reasons.extend(
        _factor_reason(
            snapshot.depth_decay,
            config.steep_depth_decay_threshold,
            DEPTH_DECAY_WATCH_REASON,
            DEPTH_DECAY_BLOCK_REASON,
        ),
    )
    reasons.extend(
        _factor_reason(
            snapshot.settlement_window_hours,
            config.long_settlement_window_hours,
            SETTLEMENT_WINDOW_WATCH_REASON,
            SETTLEMENT_WINDOW_BLOCK_REASON,
        ),
    )
    reasons.extend(
        _factor_reason(
            snapshot.volatility,
            config.high_volatility_threshold,
            VOLATILITY_WATCH_REASON,
            VOLATILITY_BLOCK_REASON,
        ),
    )
    reasons.extend(
        _factor_reason(
            snapshot.fee_drag,
            config.high_fee_drag_threshold,
            FEE_DRAG_WATCH_REASON,
            FEE_DRAG_BLOCK_REASON,
        ),
    )
    if exit_friction_status == BLOCK_STATUS:
        reasons.append(SCORE_BLOCK_REASON)
    elif exit_friction_status == WATCH_STATUS:
        reasons.append(SCORE_WATCH_REASON)
    else:
        reasons.append(SCORE_PASS_REASON)
    return _dedupe_reason_codes(reasons)


def _ask_heavy_imbalance_ratio(bid_depth: Decimal, ask_depth: Decimal) -> Decimal:
    if ask_depth <= bid_depth:
        return _zero_ratio()
    total_depth = bid_depth + ask_depth
    if total_depth == DECIMAL_ZERO:
        return _zero_ratio()
    return _quantize_ratio((ask_depth - bid_depth) / total_depth)


def _factor_reason(
    observed_value: Decimal,
    threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    factor_ratio = observed_value / threshold
    if factor_ratio >= BLOCK_FACTOR_RATIO:
        return (block_reason,)
    if factor_ratio >= WATCH_FACTOR_RATIO:
        return (watch_reason,)
    return ()


def _dedupe_reason_codes(reason_codes: list[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for reason_code in reason_codes:
        if reason_code not in deduped:
            deduped.append(reason_code)
    return tuple(deduped)


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityExitFrictionReportRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_SNAPSHOTS_REASON,)
    reasons: list[str] = []
    for row in rows:
        if row.exit_friction_status != status:
            continue
        for reason_code in row.reason_codes:
            if reason_code not in reasons:
                reasons.append(reason_code)
    if not reasons:
        raise ValueError("exit_friction_status must match at least one row")
    return tuple(reasons)


def _row_sort_key(
    row: ResearchMarketLiquidityExitFrictionReportRow,
) -> tuple[Decimal, datetime, str]:
    return (-row.exit_friction_score, row.observed_at, row.review_digest)


def _status_count(
    rows: tuple[ResearchMarketLiquidityExitFrictionReportRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.exit_friction_status == status))


def _normalize_snapshots(
    value: (
        list[ResearchMarketLiquidityExitFrictionSnapshot]
        | tuple[ResearchMarketLiquidityExitFrictionSnapshot, ...]
    ),
) -> tuple[ResearchMarketLiquidityExitFrictionSnapshot, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    for snapshot in snapshots:
        if type(snapshot) is not ResearchMarketLiquidityExitFrictionSnapshot:
            raise ValueError(
                "snapshots must contain ResearchMarketLiquidityExitFrictionSnapshot values",
            )
        _require_hard_flags("snapshot", snapshot)
    return snapshots


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchMarketLiquidityExitFrictionReportRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchMarketLiquidityExitFrictionReportRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityExitFrictionReportRow values",
            )
        _require_hard_flags("report row", row)
    if len({(row.review_digest, row.observed_at) for row in rows}) != len(rows):
        raise ValueError("rows must be unique by review digest and observed time")
    return rows


def _validate_row(row: ResearchMarketLiquidityExitFrictionReportRow) -> None:
    score_total = _quantize_ratio(
        min(
            DECIMAL_ONE,
            row.bid_depth_score
            + row.ask_depth_imbalance_score
            + row.spread_score
            + row.depth_decay_score
            + row.settlement_window_score
            + row.volatility_score
            + row.fee_drag_score,
        ),
    )
    if row.exit_friction_score != score_total:
        raise ValueError("exit_friction_score must match component scores")
    if row.exit_friction_status == PASS_STATUS and SCORE_PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows require score_pass reason")
    if row.exit_friction_status == WATCH_STATUS and SCORE_WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows require score_watch reason")
    if row.exit_friction_status == BLOCK_STATUS and SCORE_BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows require score_block reason")


def _validate_report(report: ResearchMarketLiquidityExitFrictionReport) -> None:
    if report.source_snapshot_count != Decimal(len(report.rows)):
        raise ValueError("source_snapshot_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("report rows must be sorted")
    expected_highest = report.rows[0].exit_friction_score if report.rows else _zero_ratio()
    if report.highest_exit_friction_score != expected_highest:
        raise ValueError("highest_exit_friction_score must match rows")
    if report.exit_friction_status != _report_status(report.rows):
        raise ValueError("exit_friction_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.exit_friction_status):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(
    report: ResearchMarketLiquidityExitFrictionReport,
) -> str:
    return _derived_validation_digest_for_values(asdict(report))


def _derived_validation_digest_for_values(values: dict[str, Any]) -> str:
    payload = {
        key: item for key, item in values.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_money(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(MONEY_QUANT)


def _normalize_positive_money(field_name: str, value: object) -> Decimal:
    quantized = _normalize_money(field_name, value)
    if quantized <= DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_nonnegative_money(field_name: str, value: object) -> Decimal:
    quantized = _normalize_money(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(RATIO_QUANT)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_decimal(field_name, value)
    if quantized <= DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    quantized = _normalize_decimal(field_name, value)
    if quantized < DECIMAL_ZERO or quantized > DECIMAL_ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _normalize_positive_ratio(field_name: str, value: object) -> Decimal:
    quantized = _normalize_ratio(field_name, value)
    if quantized <= DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT)


def _zero_ratio() -> Decimal:
    return DECIMAL_ZERO.quantize(RATIO_QUANT)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_metadata_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(
        fragment in lowered
        for fragment in PUBLIC_METADATA_FORBIDDEN_FRAGMENTS
    ):
        raise ValueError(f"{field_name} must not contain raw identifiers")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXIT_FRICTION_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_validation_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known exit-friction reasons")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "EXIT_FRICTION_STATUSES",
    "ResearchMarketLiquidityExitFrictionConfig",
    "ResearchMarketLiquidityExitFrictionSnapshot",
    "ResearchMarketLiquidityExitFrictionReportRow",
    "ResearchMarketLiquidityExitFrictionReport",
    "build_research_market_liquidity_exit_friction_report",
    "research_market_liquidity_exit_friction_report_payload",
)
