"""Pure paper-only strategy portfolio category correlation risk digest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_CORRELATION_RISK_DIGEST_CONFIG_VERSION = (
    "strategy-portfolio-category-correlation-risk-digest-v0"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
EMPTY_REASON_CODE = "strategy_portfolio_category_correlation_risk_digest_empty"
CLEAR_REASON_CODE = "strategy_portfolio_category_correlation_risk_digest_clear"
PASS_REASON_CODE = "category_correlation_risk_pass"
ROW_REASON_CODES = (
    "category_exposure_blocked",
    "category_exposure_watch",
    "category_rotation_blocked",
    "category_rotation_watch",
    PASS_REASON_CODE,
    "correlation_risk_blocked",
    "correlation_risk_watch",
    "shared_catalyst_exposure_blocked",
    "shared_catalyst_exposure_watch",
)
REPORT_REASON_CODES = tuple(
    sorted((*ROW_REASON_CODES, CLEAR_REASON_CODE, EMPTY_REASON_CODE)),
)
SENSITIVE_REFERENCE_MARKERS = (
    "://",
    "tok" + "en=",
    "api" + "_key=",
    "sec" + "ret",
    "priv" + "ate",
    "wal" + "let",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
)
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "aut" + "h",
    "priv" + "ate_key",
    "wal" + "let",
    "account",
    "balance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
    "bro" + "ker",
    "tra" + "de",
    "ex" + "ecute",
)
RAW_PUBLIC_REFERENCE_FIELD = "public_reference"


@dataclass(frozen=True)
class StrategyPortfolioCategoryCorrelationRiskDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_CORRELATION_RISK_DIGEST_CONFIG_VERSION
    )
    category_watch_share: Decimal = Decimal("0.300000")
    category_block_share: Decimal = Decimal("0.600000")
    shared_catalyst_watch_share: Decimal = Decimal("0.300000")
    shared_catalyst_block_share: Decimal = Decimal("0.550000")
    category_rotation_watch_count: Decimal = Decimal("2")
    category_rotation_block_count: Decimal = Decimal("3")
    correlation_risk_watch_score: Decimal = Decimal("0.450000")
    correlation_risk_block_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_watch_share",
            "category_block_share",
            "shared_catalyst_watch_share",
            "shared_catalyst_block_share",
            "correlation_risk_watch_score",
            "correlation_risk_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "category_rotation_watch_count",
            "category_rotation_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "category_share",
            self.category_watch_share,
            self.category_block_share,
        )
        _require_threshold_pair(
            "shared_catalyst_share",
            self.shared_catalyst_watch_share,
            self.shared_catalyst_block_share,
        )
        _require_threshold_pair(
            "category_rotation_count",
            self.category_rotation_watch_count,
            self.category_rotation_block_count,
        )
        _require_threshold_pair(
            "correlation_risk_score",
            self.correlation_risk_watch_score,
            self.correlation_risk_block_score,
        )
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryCorrelationRiskInput:
    position_id: str
    market_slug: str
    category: str
    catalyst_id: str
    observed_at: datetime
    notional: Decimal
    category_rotation_count: Decimal
    correlation_score: Decimal
    public_reference: str = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "position_id",
            "market_slug",
            "category",
            "catalyst_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "notional",
            _normalize_nonnegative_value("notional", self.notional),
        )
        object.__setattr__(
            self,
            "category_rotation_count",
            _normalize_nonnegative_count(
                "category_rotation_count",
                self.category_rotation_count,
            ),
        )
        object.__setattr__(
            self,
            "correlation_score",
            _normalize_probability("correlation_score", self.correlation_score),
        )
        _require_canonical_string("public_reference", self.public_reference)
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryCorrelationRiskDigestRow:
    rank: Decimal
    position_id: str
    market_slug: str
    category: str
    catalyst_id: str
    observed_at: datetime
    notional: Decimal
    category_exposure_notional: Decimal
    category_exposure_share: Decimal
    shared_catalyst_exposure_notional: Decimal
    shared_catalyst_exposure_share: Decimal
    category_rotation_count: Decimal
    correlation_score: Decimal
    risk_score: Decimal
    risk_status: str
    redacted_public_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        for field_name in (
            "position_id",
            "market_slug",
            "category",
            "catalyst_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "notional",
            "category_exposure_notional",
            "shared_catalyst_exposure_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "category_rotation_count",
            _normalize_nonnegative_count(
                "category_rotation_count",
                self.category_rotation_count,
            ),
        )
        for field_name in (
            "category_exposure_share",
            "shared_catalyst_exposure_share",
            "correlation_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("risk_status", self.risk_status, STATUSES)
        _require_safe_public_string(
            "redacted_public_reference",
            self.redacted_public_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_paper_flags("row", self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryCorrelationRiskDigestReport:
    generated_at: datetime
    config_version: str
    position_count: Decimal
    category_count: Decimal
    catalyst_count: Decimal
    total_notional: Decimal
    max_category_exposure_share: Decimal
    max_shared_catalyst_exposure_share: Decimal
    max_category_rotation_count: Decimal
    max_correlation_score: Decimal
    blocked_position_count: Decimal
    watch_position_count: Decimal
    pass_position_count: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "position_count",
            "category_count",
            "catalyst_count",
            "blocked_position_count",
            "watch_position_count",
            "pass_position_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_category_rotation_count",
            _normalize_nonnegative_count(
                "max_category_rotation_count",
                self.max_category_rotation_count,
            ),
        )
        object.__setattr__(
            self,
            "total_notional",
            _normalize_nonnegative_value("total_notional", self.total_notional),
        )
        for field_name in (
            "max_category_exposure_share",
            "max_shared_catalyst_exposure_share",
            "max_correlation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_paper_flags("report", self)


def build_strategy_portfolio_category_correlation_risk_digest(
    records: Iterable[StrategyPortfolioCategoryCorrelationRiskInput],
    *,
    config: StrategyPortfolioCategoryCorrelationRiskDigestConfig,
    generated_at: datetime,
) -> StrategyPortfolioCategoryCorrelationRiskDigestReport:
    if type(config) is not StrategyPortfolioCategoryCorrelationRiskDigestConfig:
        raise ValueError(
            "config must be a StrategyPortfolioCategoryCorrelationRiskDigestConfig",
        )
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(records)
    _reject_future_inputs(inputs, generated_at_utc)
    total_notional = _sum_values(row.notional for row in inputs)
    category_totals = _notional_totals_by(inputs, "category")
    catalyst_totals = _notional_totals_by(inputs, "catalyst_id")
    rows = _rank_rows(
        tuple(
            _unranked_row(
                row,
                category_notional=category_totals[row.category],
                catalyst_notional=catalyst_totals[row.catalyst_id],
                total_notional=total_notional,
                config=config,
            )
            for row in inputs
        ),
    )
    return StrategyPortfolioCategoryCorrelationRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        position_count=_count(len(rows)),
        category_count=_count(len({row.category for row in rows})),
        catalyst_count=_count(len({row.catalyst_id for row in rows})),
        total_notional=total_notional,
        max_category_exposure_share=_max_value(rows, "category_exposure_share"),
        max_shared_catalyst_exposure_share=_max_value(
            rows,
            "shared_catalyst_exposure_share",
        ),
        max_category_rotation_count=_max_value(rows, "category_rotation_count"),
        max_correlation_score=_max_value(rows, "correlation_score"),
        blocked_position_count=_status_count(rows, BLOCKED_STATUS),
        watch_position_count=_status_count(rows, WATCH_STATUS),
        pass_position_count=_status_count(rows, PASS_STATUS),
        digest_status=_digest_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_portfolio_category_correlation_risk_digest_payload(
    report: StrategyPortfolioCategoryCorrelationRiskDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyPortfolioCategoryCorrelationRiskDigestReport:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyPortfolioCategoryCorrelationRiskDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _unranked_row(
    row: StrategyPortfolioCategoryCorrelationRiskInput,
    *,
    category_notional: Decimal,
    catalyst_notional: Decimal,
    total_notional: Decimal,
    config: StrategyPortfolioCategoryCorrelationRiskDigestConfig,
) -> StrategyPortfolioCategoryCorrelationRiskDigestRow:
    category_share = _ratio(category_notional, total_notional)
    catalyst_share = _ratio(catalyst_notional, total_notional)
    risk_score = _q(max(category_share, catalyst_share, row.correlation_score))
    status = _row_status(
        category_share=category_share,
        catalyst_share=catalyst_share,
        rotation_count=row.category_rotation_count,
        correlation_score=row.correlation_score,
        config=config,
    )
    return StrategyPortfolioCategoryCorrelationRiskDigestRow(
        rank=Decimal("1"),
        position_id=row.position_id,
        market_slug=row.market_slug,
        category=row.category,
        catalyst_id=row.catalyst_id,
        observed_at=row.observed_at,
        notional=row.notional,
        category_exposure_notional=category_notional,
        category_exposure_share=category_share,
        shared_catalyst_exposure_notional=catalyst_notional,
        shared_catalyst_exposure_share=catalyst_share,
        category_rotation_count=row.category_rotation_count,
        correlation_score=row.correlation_score,
        risk_score=risk_score,
        risk_status=status,
        redacted_public_reference=_redact_public_reference(row.public_reference),
        reason_codes=_row_reason_codes(
            category_share=category_share,
            catalyst_share=catalyst_share,
            rotation_count=row.category_rotation_count,
            correlation_score=row.correlation_score,
            status=status,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...],
) -> tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...]:
    rows_by_rank = sorted(rows, key=_row_sort_key)
    return tuple(
        StrategyPortfolioCategoryCorrelationRiskDigestRow(
            rank=_count(index),
            position_id=row.position_id,
            market_slug=row.market_slug,
            category=row.category,
            catalyst_id=row.catalyst_id,
            observed_at=row.observed_at,
            notional=row.notional,
            category_exposure_notional=row.category_exposure_notional,
            category_exposure_share=row.category_exposure_share,
            shared_catalyst_exposure_notional=row.shared_catalyst_exposure_notional,
            shared_catalyst_exposure_share=row.shared_catalyst_exposure_share,
            category_rotation_count=row.category_rotation_count,
            correlation_score=row.correlation_score,
            risk_score=row.risk_score,
            risk_status=row.risk_status,
            redacted_public_reference=row.redacted_public_reference,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(rows_by_rank, start=1)
    )


def _row_status(
    *,
    category_share: Decimal,
    catalyst_share: Decimal,
    rotation_count: Decimal,
    correlation_score: Decimal,
    config: StrategyPortfolioCategoryCorrelationRiskDigestConfig,
) -> str:
    if (
        category_share >= config.category_block_share
        or catalyst_share >= config.shared_catalyst_block_share
        or rotation_count >= config.category_rotation_block_count
        or correlation_score >= config.correlation_risk_block_score
    ):
        return BLOCKED_STATUS
    if (
        category_share >= config.category_watch_share
        or catalyst_share >= config.shared_catalyst_watch_share
        or rotation_count >= config.category_rotation_watch_count
        or correlation_score >= config.correlation_risk_watch_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    category_share: Decimal,
    catalyst_share: Decimal,
    rotation_count: Decimal,
    correlation_score: Decimal,
    status: str,
    config: StrategyPortfolioCategoryCorrelationRiskDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if category_share >= config.category_block_share:
        reason_codes.append("category_exposure_blocked")
    elif category_share >= config.category_watch_share:
        reason_codes.append("category_exposure_watch")
    if catalyst_share >= config.shared_catalyst_block_share:
        reason_codes.append("shared_catalyst_exposure_blocked")
    elif catalyst_share >= config.shared_catalyst_watch_share:
        reason_codes.append("shared_catalyst_exposure_watch")
    if rotation_count >= config.category_rotation_block_count:
        reason_codes.append("category_rotation_blocked")
    elif rotation_count >= config.category_rotation_watch_count:
        reason_codes.append("category_rotation_watch")
    if correlation_score >= config.correlation_risk_block_score:
        reason_codes.append("correlation_risk_blocked")
    elif correlation_score >= config.correlation_risk_watch_score:
        reason_codes.append("correlation_risk_watch")
    if not reason_codes and status == PASS_STATUS:
        reason_codes.append(PASS_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    risk_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    )
    if not risk_codes:
        return (CLEAR_REASON_CODE,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(set(risk_codes))),
        REPORT_REASON_CODES,
    )


def _digest_status(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.risk_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.risk_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _validate_row(row: StrategyPortfolioCategoryCorrelationRiskDigestRow) -> None:
    expected_risk_score = _q(
        max(
            row.category_exposure_share,
            row.shared_catalyst_exposure_share,
            row.correlation_score,
        ),
    )
    if row.risk_score != expected_risk_score:
        raise ValueError("risk_score must match row inputs")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.risk_status != expected_status:
        raise ValueError("risk_status must match reason_codes")


def _validate_report(
    report: StrategyPortfolioCategoryCorrelationRiskDigestReport,
) -> None:
    if report.position_count != _count(len(report.rows)):
        raise ValueError("position_count must match rows")
    if report.category_count != _count(len({row.category for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.catalyst_count != _count(len({row.catalyst_id for row in report.rows})):
        raise ValueError("catalyst_count must match rows")
    if report.total_notional != _sum_values(row.notional for row in report.rows):
        raise ValueError("total_notional must match rows")
    if report.max_category_exposure_share != _max_value(
        report.rows,
        "category_exposure_share",
    ):
        raise ValueError("max_category_exposure_share must match rows")
    if report.max_shared_catalyst_exposure_share != _max_value(
        report.rows,
        "shared_catalyst_exposure_share",
    ):
        raise ValueError("max_shared_catalyst_exposure_share must match rows")
    if report.max_category_rotation_count != _max_value(
        report.rows,
        "category_rotation_count",
    ):
        raise ValueError("max_category_rotation_count must match rows")
    if report.max_correlation_score != _max_value(report.rows, "correlation_score"):
        raise ValueError("max_correlation_score must match rows")
    if report.blocked_position_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_position_count must match rows")
    if report.watch_position_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_position_count must match rows")
    if report.pass_position_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_position_count must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    value: Iterable[StrategyPortfolioCategoryCorrelationRiskInput],
) -> tuple[StrategyPortfolioCategoryCorrelationRiskInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("records must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("records must be an iterable") from exc
    position_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyPortfolioCategoryCorrelationRiskInput:
            raise ValueError("records must contain exact input rows")
        _require_paper_flags("input", row)
        if row.position_id in position_ids:
            raise ValueError("position_id values must be unique")
        position_ids.add(row.position_id)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("digest report rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyPortfolioCategoryCorrelationRiskDigestRow:
            raise ValueError("digest report must contain exact rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by risk status and score")
    return rows


def _reject_future_inputs(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _notional_totals_by(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskInput, ...],
    field_name: str,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        key = getattr(row, field_name)
        totals[key] = _q(totals.get(key, ZERO) + row.notional)
    return totals


def _row_sort_key(
    row: StrategyPortfolioCategoryCorrelationRiskDigestRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (_status_rank(row.risk_status), -row.risk_score, -row.notional, row.position_id)


def _status_rank(status: str) -> int:
    if status == BLOCKED_STATUS:
        return 0
    if status == WATCH_STATUS:
        return 1
    return 2


def _status_count(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.risk_status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return BLOCKED_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _max_value(
    rows: tuple[StrategyPortfolioCategoryCorrelationRiskDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        if field_name == "category_rotation_count":
            return ZERO_COUNT
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_values(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _q(total + value)
    return total


def _redact_public_reference(public_reference: str) -> str:
    if _contains_sensitive_reference(public_reference) or _has_unsafe_surface_fragment(
        public_reference,
    ):
        return "<redacted>"
    return public_reference


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value)
            for key, nested_value in asdict(value).items()
            if key != RAW_PUBLIC_REFERENCE_FIELD
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == RAW_PUBLIC_REFERENCE_FIELD:
                raise ValueError(f"unsafe surface field in payload: {key}")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_sensitive_reference(value) or _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if key == RAW_PUBLIC_REFERENCE_FIELD or _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_sensitive_reference(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS)


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_safe_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_sensitive_reference(value) or _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_value(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _q(value)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be at least zero")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be at least zero")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unknown reason code")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_threshold_pair(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"{field_name} watch threshold must not exceed block threshold")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _q(numerator / denominator)


def _q(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_CORRELATION_RISK_DIGEST_CONFIG_VERSION",
    "StrategyPortfolioCategoryCorrelationRiskDigestConfig",
    "StrategyPortfolioCategoryCorrelationRiskDigestReport",
    "StrategyPortfolioCategoryCorrelationRiskDigestRow",
    "StrategyPortfolioCategoryCorrelationRiskInput",
    "build_strategy_portfolio_category_correlation_risk_digest",
    "strategy_portfolio_category_correlation_risk_digest_payload",
)
