"""Pure report-only market liquidity regime shift research report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Sequence


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityRegimeShiftConfig",
    "ResearchMarketLiquidityRegimeShiftInput",
    "ResearchMarketLiquidityRegimeShiftReasonCodeCount",
    "ResearchMarketLiquidityRegimeShiftReport",
    "ResearchMarketLiquidityRegimeShiftRow",
    "build_research_market_liquidity_regime_shift_report",
    "research_market_liquidity_regime_shift_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-regime-shift-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_DEPTH_BLOCK = "depth_deterioration_block"
REASON_SPREAD_BLOCK = "spread_widening_block"
REASON_FRESHNESS_BLOCK = "book_freshness_block"
REASON_FEE_BLOCK = "fee_friction_block"
REASON_MANUAL_BLOCK = "manual_review_urgency_block"
REASON_REGIME_BLOCK = "regime_shift_score_block"
REASON_DEPTH_WATCH = "depth_deterioration_watch"
REASON_SPREAD_WATCH = "spread_widening_watch"
REASON_FRESHNESS_WATCH = "book_freshness_watch"
REASON_FEE_WATCH = "fee_friction_watch"
REASON_MANUAL_WATCH = "manual_review_urgency_watch"
REASON_REGIME_WATCH = "regime_shift_score_watch"
REASON_STABLE_PASS = "liquidity_regime_stable_pass"

REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_DEPTH_BLOCK,
    REASON_SPREAD_BLOCK,
    REASON_FRESHNESS_BLOCK,
    REASON_FEE_BLOCK,
    REASON_MANUAL_BLOCK,
    REASON_REGIME_BLOCK,
    REASON_DEPTH_WATCH,
    REASON_SPREAD_WATCH,
    REASON_FRESHNESS_WATCH,
    REASON_FEE_WATCH,
    REASON_MANUAL_WATCH,
    REASON_REGIME_WATCH,
    REASON_STABLE_PASS,
)
ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code != REASON_EMPTY_INPUT
)
BLOCK_REASON_CODES = frozenset(
    (
        REASON_DEPTH_BLOCK,
        REASON_SPREAD_BLOCK,
        REASON_FRESHNESS_BLOCK,
        REASON_FEE_BLOCK,
        REASON_MANUAL_BLOCK,
        REASON_REGIME_BLOCK,
    ),
)
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DIGEST_FIELD = "derived_validation_digest"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate-id",
    "candidate=",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "slug=",
    "question=",
    "question_text",
    "source_url",
    "source_text",
    "source_id",
    "source-id",
    "dsn",
    "postgres://",
    "table_name",
    "private_token",
    "private-key",
    "private_key",
    "api_key",
    "credential",
    "auth",
    "wallet",
    "order",
    "live",
    "trade",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "position",
    "secret",
    "token=",
    "http://",
    "https://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchMarketLiquidityRegimeShiftConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION
    )
    depth_deterioration_watch_threshold: Decimal = Decimal("0.200000")
    depth_deterioration_block_threshold: Decimal = Decimal("0.500000")
    spread_widening_watch_threshold: Decimal = Decimal("0.250000")
    spread_widening_block_threshold: Decimal = Decimal("0.750000")
    book_age_watch_seconds: Decimal = Decimal("120.000000")
    book_age_block_seconds: Decimal = Decimal("900.000000")
    fee_rate_watch_threshold: Decimal = Decimal("0.010000")
    fee_rate_block_threshold: Decimal = Decimal("0.030000")
    manual_review_watch_threshold: Decimal = Decimal("0.350000")
    manual_review_block_threshold: Decimal = Decimal("0.700000")
    regime_shift_watch_threshold: Decimal = Decimal("0.350000")
    regime_shift_block_threshold: Decimal = Decimal("0.700000")
    depth_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    fee_weight: Decimal = Decimal("0.150000")
    manual_review_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityRegimeShiftConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "depth_deterioration_watch_threshold",
            "depth_deterioration_block_threshold",
            "spread_widening_watch_threshold",
            "spread_widening_block_threshold",
            "fee_rate_watch_threshold",
            "fee_rate_block_threshold",
            "manual_review_watch_threshold",
            "manual_review_block_threshold",
            "regime_shift_watch_threshold",
            "regime_shift_block_threshold",
            "depth_weight",
            "spread_weight",
            "freshness_weight",
            "fee_weight",
            "manual_review_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("book_age_watch_seconds", "book_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityRegimeShiftInput(_FinalPublicDataclass):
    analysis_key: str
    current_depth_units: Decimal
    baseline_depth_units: Decimal
    current_spread_rate: Decimal
    baseline_spread_rate: Decimal
    book_age_seconds: Decimal
    fee_rate: Decimal
    manual_review_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityRegimeShiftInput, "input")
        object.__setattr__(
            self,
            "analysis_key",
            _require_private_string("analysis_key", self.analysis_key),
        )
        object.__setattr__(
            self,
            "current_depth_units",
            _require_nonnegative_decimal("current_depth_units", self.current_depth_units),
        )
        object.__setattr__(
            self,
            "baseline_depth_units",
            _require_positive_decimal("baseline_depth_units", self.baseline_depth_units),
        )
        object.__setattr__(
            self,
            "baseline_spread_rate",
            _require_positive_ratio_decimal(
                "baseline_spread_rate",
                self.baseline_spread_rate,
            ),
        )
        object.__setattr__(
            self,
            "current_spread_rate",
            _require_ratio_decimal("current_spread_rate", self.current_spread_rate),
        )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
        )
        object.__setattr__(
            self,
            "fee_rate",
            _require_ratio_decimal("fee_rate", self.fee_rate),
        )
        object.__setattr__(
            self,
            "manual_review_urgency_score",
            _require_ratio_decimal(
                "manual_review_urgency_score",
                self.manual_review_urgency_score,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityRegimeShiftRow(_FinalPublicDataclass):
    liquidity_ref: str
    current_depth_units: Decimal
    baseline_depth_units: Decimal
    current_spread_rate: Decimal
    baseline_spread_rate: Decimal
    book_age_seconds: Decimal
    fee_rate: Decimal
    manual_review_urgency_score: Decimal
    depth_deterioration_score: Decimal
    spread_widening_score: Decimal
    freshness_score: Decimal
    fee_friction_score: Decimal
    regime_shift_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityRegimeShiftRow, "row")
        object.__setattr__(
            self,
            "liquidity_ref",
            _require_public_ref("liquidity_ref", self.liquidity_ref),
        )
        object.__setattr__(
            self,
            "current_depth_units",
            _require_nonnegative_decimal("current_depth_units", self.current_depth_units),
        )
        object.__setattr__(
            self,
            "baseline_depth_units",
            _require_positive_decimal("baseline_depth_units", self.baseline_depth_units),
        )
        object.__setattr__(
            self,
            "baseline_spread_rate",
            _require_positive_ratio_decimal(
                "baseline_spread_rate",
                self.baseline_spread_rate,
            ),
        )
        object.__setattr__(
            self,
            "current_spread_rate",
            _require_ratio_decimal("current_spread_rate", self.current_spread_rate),
        )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
        )
        object.__setattr__(self, "fee_rate", _require_ratio_decimal("fee_rate", self.fee_rate))
        object.__setattr__(
            self,
            "manual_review_urgency_score",
            _require_ratio_decimal(
                "manual_review_urgency_score",
                self.manual_review_urgency_score,
            ),
        )
        for field_name in (
            "depth_deterioration_score",
            "spread_widening_score",
            "freshness_score",
            "fee_friction_score",
            "regime_shift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityRegimeShiftReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityRegimeShiftReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityRegimeShiftReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_regime_shift_score: Decimal
    max_regime_shift_score: Decimal
    max_depth_deterioration_score: Decimal
    max_spread_widening_score: Decimal
    max_book_age_seconds: Decimal
    max_fee_rate: Decimal
    max_manual_review_urgency_score: Decimal
    rows: tuple[ResearchMarketLiquidityRegimeShiftRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityRegimeShiftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityRegimeShiftReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_regime_shift_score",
            "max_regime_shift_score",
            "max_depth_deterioration_score",
            "max_spread_widening_score",
            "max_fee_rate",
            "max_manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_book_age_seconds",
            _require_nonnegative_decimal(
                "max_book_age_seconds",
                self.max_book_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_sha256(DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_market_liquidity_regime_shift_report_payload(self)


def build_research_market_liquidity_regime_shift_report(
    inputs: Sequence[ResearchMarketLiquidityRegimeShiftInput],
    *,
    generated_at: datetime,
    config: ResearchMarketLiquidityRegimeShiftConfig | None = None,
) -> ResearchMarketLiquidityRegimeShiftReport:
    cfg = config or ResearchMarketLiquidityRegimeShiftConfig()
    if type(cfg) is not ResearchMarketLiquidityRegimeShiftConfig:
        raise ValueError("config must be a ResearchMarketLiquidityRegimeShiftConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in _normalize_inputs(inputs)),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchMarketLiquidityRegimeShiftReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_regime_shift_score": _average_decimal(
            tuple(row.regime_shift_score for row in rows),
        ),
        "max_regime_shift_score": max(
            (row.regime_shift_score for row in rows),
            default=ZERO,
        ),
        "max_depth_deterioration_score": max(
            (row.depth_deterioration_score for row in rows),
            default=ZERO,
        ),
        "max_spread_widening_score": max(
            (row.spread_widening_score for row in rows),
            default=ZERO,
        ),
        "max_book_age_seconds": max(
            (row.book_age_seconds for row in rows),
            default=ZERO,
        ),
        "max_fee_rate": max((row.fee_rate for row in rows), default=ZERO),
        "max_manual_review_urgency_score": max(
            (row.manual_review_urgency_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketLiquidityRegimeShiftReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_liquidity_regime_shift_report_payload(
    value: ResearchMarketLiquidityRegimeShiftReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchMarketLiquidityRegimeShiftReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
        _require_hard_flags("payload", _PayloadFlags(payload))
    else:
        raise ValueError(
            "value must be a ResearchMarketLiquidityRegimeShiftReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_public_numeric_values(payload)
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_input(
    row: ResearchMarketLiquidityRegimeShiftInput,
    config: ResearchMarketLiquidityRegimeShiftConfig,
) -> ResearchMarketLiquidityRegimeShiftRow:
    depth_deterioration_score = _depth_deterioration_score(
        row.current_depth_units,
        row.baseline_depth_units,
    )
    spread_widening_score = _spread_widening_score(
        row.current_spread_rate,
        row.baseline_spread_rate,
    )
    freshness_score = _freshness_score(row.book_age_seconds, config)
    fee_friction_score = _fee_friction_score(row.fee_rate, config)
    regime_shift_score = _regime_shift_score(
        depth_deterioration_score=depth_deterioration_score,
        spread_widening_score=spread_widening_score,
        freshness_score=freshness_score,
        fee_friction_score=fee_friction_score,
        manual_review_urgency_score=row.manual_review_urgency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        depth_deterioration_score=depth_deterioration_score,
        spread_widening_score=spread_widening_score,
        book_age_seconds=row.book_age_seconds,
        fee_rate=row.fee_rate,
        manual_review_urgency_score=row.manual_review_urgency_score,
        regime_shift_score=regime_shift_score,
        config=config,
    )
    return ResearchMarketLiquidityRegimeShiftRow(
        liquidity_ref=_liquidity_ref(row.analysis_key),
        current_depth_units=row.current_depth_units,
        baseline_depth_units=row.baseline_depth_units,
        current_spread_rate=row.current_spread_rate,
        baseline_spread_rate=row.baseline_spread_rate,
        book_age_seconds=row.book_age_seconds,
        fee_rate=row.fee_rate,
        manual_review_urgency_score=row.manual_review_urgency_score,
        depth_deterioration_score=depth_deterioration_score,
        spread_widening_score=spread_widening_score,
        freshness_score=freshness_score,
        fee_friction_score=fee_friction_score,
        regime_shift_score=regime_shift_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    depth_deterioration_score: Decimal,
    spread_widening_score: Decimal,
    book_age_seconds: Decimal,
    fee_rate: Decimal,
    manual_review_urgency_score: Decimal,
    regime_shift_score: Decimal,
    config: ResearchMarketLiquidityRegimeShiftConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if depth_deterioration_score >= config.depth_deterioration_block_threshold:
        reason_codes.append(REASON_DEPTH_BLOCK)
    elif depth_deterioration_score >= config.depth_deterioration_watch_threshold:
        reason_codes.append(REASON_DEPTH_WATCH)
    if spread_widening_score >= config.spread_widening_block_threshold:
        reason_codes.append(REASON_SPREAD_BLOCK)
    elif spread_widening_score >= config.spread_widening_watch_threshold:
        reason_codes.append(REASON_SPREAD_WATCH)
    if book_age_seconds >= config.book_age_block_seconds:
        reason_codes.append(REASON_FRESHNESS_BLOCK)
    elif book_age_seconds >= config.book_age_watch_seconds:
        reason_codes.append(REASON_FRESHNESS_WATCH)
    if fee_rate >= config.fee_rate_block_threshold:
        reason_codes.append(REASON_FEE_BLOCK)
    elif fee_rate >= config.fee_rate_watch_threshold:
        reason_codes.append(REASON_FEE_WATCH)
    if manual_review_urgency_score >= config.manual_review_block_threshold:
        reason_codes.append(REASON_MANUAL_BLOCK)
    elif manual_review_urgency_score >= config.manual_review_watch_threshold:
        reason_codes.append(REASON_MANUAL_WATCH)
    if regime_shift_score >= config.regime_shift_block_threshold:
        reason_codes.append(REASON_REGIME_BLOCK)
    elif regime_shift_score >= config.regime_shift_watch_threshold:
        reason_codes.append(REASON_REGIME_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_STABLE_PASS)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_STABLE_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchMarketLiquidityRegimeShiftRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketLiquidityRegimeShiftRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchMarketLiquidityRegimeShiftRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), -row.regime_shift_score, row.liquidity_ref)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityRegimeShiftRow, ...],
) -> tuple[ResearchMarketLiquidityRegimeShiftReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _depth_deterioration_score(
    current_depth_units: Decimal,
    baseline_depth_units: Decimal,
) -> Decimal:
    return _clamp_ratio((baseline_depth_units - current_depth_units) / baseline_depth_units)


def _spread_widening_score(
    current_spread_rate: Decimal,
    baseline_spread_rate: Decimal,
) -> Decimal:
    return _clamp_ratio((current_spread_rate - baseline_spread_rate) / baseline_spread_rate)


def _freshness_score(
    book_age_seconds: Decimal,
    config: ResearchMarketLiquidityRegimeShiftConfig,
) -> Decimal:
    return _clamp_ratio(book_age_seconds / config.book_age_block_seconds)


def _fee_friction_score(
    fee_rate: Decimal,
    config: ResearchMarketLiquidityRegimeShiftConfig,
) -> Decimal:
    return _clamp_ratio(fee_rate / config.fee_rate_block_threshold)


def _regime_shift_score(
    *,
    depth_deterioration_score: Decimal,
    spread_widening_score: Decimal,
    freshness_score: Decimal,
    fee_friction_score: Decimal,
    manual_review_urgency_score: Decimal,
    config: ResearchMarketLiquidityRegimeShiftConfig,
) -> Decimal:
    return _clamp_ratio(
        depth_deterioration_score * config.depth_weight
        + spread_widening_score * config.spread_weight
        + freshness_score * config.freshness_weight
        + fee_friction_score * config.fee_weight
        + manual_review_urgency_score * config.manual_review_weight,
    )


def _validate_config(config: ResearchMarketLiquidityRegimeShiftConfig) -> None:
    if (
        config.depth_deterioration_watch_threshold
        > config.depth_deterioration_block_threshold
    ):
        raise ValueError("depth threshold ordering is invalid")
    if config.spread_widening_watch_threshold > config.spread_widening_block_threshold:
        raise ValueError("spread threshold ordering is invalid")
    if config.book_age_watch_seconds > config.book_age_block_seconds:
        raise ValueError("book freshness threshold ordering is invalid")
    if config.fee_rate_watch_threshold > config.fee_rate_block_threshold:
        raise ValueError("fee threshold ordering is invalid")
    if config.manual_review_watch_threshold > config.manual_review_block_threshold:
        raise ValueError("manual review threshold ordering is invalid")
    if config.regime_shift_watch_threshold > config.regime_shift_block_threshold:
        raise ValueError("regime shift threshold ordering is invalid")
    weight_sum = _quantize(
        config.depth_weight
        + config.spread_weight
        + config.freshness_weight
        + config.fee_weight
        + config.manual_review_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(row: ResearchMarketLiquidityRegimeShiftRow) -> None:
    expected_depth = _depth_deterioration_score(
        row.current_depth_units,
        row.baseline_depth_units,
    )
    if row.depth_deterioration_score != expected_depth:
        raise ValueError("depth_deterioration_score must match row inputs")
    expected_spread = _spread_widening_score(
        row.current_spread_rate,
        row.baseline_spread_rate,
    )
    if row.spread_widening_score != expected_spread:
        raise ValueError("spread_widening_score must match row inputs")
    expected_freshness = _freshness_score(
        row.book_age_seconds,
        ResearchMarketLiquidityRegimeShiftConfig(),
    )
    if row.freshness_score != expected_freshness:
        raise ValueError("freshness_score must match row inputs")
    expected_fee = _fee_friction_score(row.fee_rate, ResearchMarketLiquidityRegimeShiftConfig())
    if row.fee_friction_score != expected_fee:
        raise ValueError("fee_friction_score must match row inputs")
    expected_regime = _regime_shift_score(
        depth_deterioration_score=row.depth_deterioration_score,
        spread_widening_score=row.spread_widening_score,
        freshness_score=row.freshness_score,
        fee_friction_score=row.fee_friction_score,
        manual_review_urgency_score=row.manual_review_urgency_score,
        config=ResearchMarketLiquidityRegimeShiftConfig(),
    )
    if row.regime_shift_score != expected_regime:
        raise ValueError("regime_shift_score must match row inputs")
    expected_reason_codes = _row_reason_codes(
        depth_deterioration_score=row.depth_deterioration_score,
        spread_widening_score=row.spread_widening_score,
        book_age_seconds=row.book_age_seconds,
        fee_rate=row.fee_rate,
        manual_review_urgency_score=row.manual_review_urgency_score,
        regime_shift_score=row.regime_shift_score,
        config=ResearchMarketLiquidityRegimeShiftConfig(),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketLiquidityRegimeShiftReport) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_regime_shift_score != _average_decimal(
        tuple(row.regime_shift_score for row in rows),
    ):
        raise ValueError("average_regime_shift_score must match rows")
    if report.max_regime_shift_score != max(
        (row.regime_shift_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_regime_shift_score must match rows")
    if report.max_depth_deterioration_score != max(
        (row.depth_deterioration_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_depth_deterioration_score must match rows")
    if report.max_spread_widening_score != max(
        (row.spread_widening_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_widening_score must match rows")
    if report.max_book_age_seconds != max(
        (row.book_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_fee_rate != max((row.fee_rate for row in rows), default=ZERO):
        raise ValueError("max_fee_rate must match rows")
    if report.max_manual_review_urgency_score != max(
        (row.manual_review_urgency_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_manual_review_urgency_score must match rows")
    expected_counts = _reason_code_counts(rows)
    expected_reason_codes = tuple(row.reason_code for row in expected_counts)
    if not rows:
        expected_counts = (
            ResearchMarketLiquidityRegimeShiftReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        expected_reason_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_inputs(
    inputs: Sequence[ResearchMarketLiquidityRegimeShiftInput],
) -> tuple[ResearchMarketLiquidityRegimeShiftInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("input rows must be a sequence")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("input rows must be a sequence") from exc
    for row in rows:
        if type(row) is not ResearchMarketLiquidityRegimeShiftInput:
            raise ValueError("input rows must contain ResearchMarketLiquidityRegimeShiftInput")
        _require_hard_flags("input", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityRegimeShiftRow, ...],
) -> tuple[ResearchMarketLiquidityRegimeShiftRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityRegimeShiftRow:
            raise ValueError("rows must contain ResearchMarketLiquidityRegimeShiftRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchMarketLiquidityRegimeShiftReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityRegimeShiftReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityRegimeShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityRegimeShiftReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, ROW_REASON_CODE_SEQUENCE)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, REASON_CODE_SEQUENCE)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_private_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or len(value) > 160:
        raise ValueError(f"{name} must be a bounded public string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} has unsafe public value")
    return value


def _require_public_ref(name: str, value: object) -> str:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{name} must be a sha256 public reference")
    _require_sha256(name, value.removeprefix("sha256:"))
    return value


def _require_sha256(name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a SHA-256 digest")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of pass/watch/block")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be a supported reason code")
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_positive_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_ratio_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(name, value)


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value <= ZERO:
            return ZERO
        if value >= ONE:
            return ONE
        return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _liquidity_ref(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _report_digest(report: ResearchMarketLiquidityRegimeShiftReport) -> str:
    return _payload_validation_digest(_report_payload(report, include_digest=False))


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _payload_validation_digest(_json_ready(values))


def _payload_validation_digest(payload: dict[str, object]) -> str:
    unsigned_payload = {
        key: value for key, value in payload.items() if key != DIGEST_FIELD
    }
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(DIGEST_FIELD)
    _require_sha256(DIGEST_FIELD, digest)
    if digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _report_payload(
    report: ResearchMarketLiquidityRegimeShiftReport,
    *,
    include_digest: bool = True,
) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    if not include_digest:
        payload.pop(DIGEST_FIELD, None)
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str or value is None:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON value must not be numeric")
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


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None or type(value) is str:
        return
    if type(value) is int or type(value) is float or type(value) is Decimal:
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
        return
    raise ValueError("public payload contains an unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, dict):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"unsafe public payload in {label}")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _public_field_names(value: object) -> tuple[str, ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a dataclass instance")
    return tuple(field.name for field in fields(value))
