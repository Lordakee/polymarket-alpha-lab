"""Pure candidate tail-risk digest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_DIGEST_CONFIG_VERSION = (
    "strategy-candidate-tail-risk-digest-v0"
)

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")

_PASS_REASON = "strategy_candidate_tail_risk_pass"
_EMPTY_REASON = "strategy_candidate_tail_risk_digest_empty"
_TAIL_SCORE_WATCH_REASON = "tail_risk_score_watch"
_TAIL_SCORE_BLOCK_REASON = "tail_risk_score_block"
_BINARY_WATCH_REASON = "binary_resolution_ambiguity_watch"
_BINARY_BLOCK_REASON = "binary_resolution_ambiguity_block"
_LIQUIDITY_WATCH_REASON = "liquidity_slippage_tail_watch"
_LIQUIDITY_BLOCK_REASON = "liquidity_slippage_tail_block"
_CORRELATED_WATCH_REASON = "correlated_catalyst_exposure_watch"
_CORRELATED_BLOCK_REASON = "correlated_catalyst_exposure_block"
_LATE_WATCH_REASON = "late_information_shock_watch"
_LATE_BLOCK_REASON = "late_information_shock_block"
_MAX_LOSS_WATCH_REASON = "maximum_loss_concentration_watch"
_MAX_LOSS_BLOCK_REASON = "maximum_loss_concentration_block"

_REASON_PRIORITY = (
    _BINARY_BLOCK_REASON,
    _LIQUIDITY_BLOCK_REASON,
    _CORRELATED_BLOCK_REASON,
    _LATE_BLOCK_REASON,
    _MAX_LOSS_BLOCK_REASON,
    _TAIL_SCORE_BLOCK_REASON,
    _BINARY_WATCH_REASON,
    _LIQUIDITY_WATCH_REASON,
    _CORRELATED_WATCH_REASON,
    _LATE_WATCH_REASON,
    _MAX_LOSS_WATCH_REASON,
    _TAIL_SCORE_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_REASONS = frozenset(
    (
        _BINARY_BLOCK_REASON,
        _LIQUIDITY_BLOCK_REASON,
        _CORRELATED_BLOCK_REASON,
        _LATE_BLOCK_REASON,
        _MAX_LOSS_BLOCK_REASON,
        _TAIL_SCORE_BLOCK_REASON,
    ),
)
_WATCH_REASONS = frozenset(
    (
        _BINARY_WATCH_REASON,
        _LIQUIDITY_WATCH_REASON,
        _CORRELATED_WATCH_REASON,
        _LATE_WATCH_REASON,
        _MAX_LOSS_WATCH_REASON,
        _TAIL_SCORE_WATCH_REASON,
    ),
)
_FEATURE_SPECS = (
    (
        "binary_resolution_ambiguity_score",
        _BINARY_WATCH_REASON,
        _BINARY_BLOCK_REASON,
    ),
    (
        "liquidity_slippage_tail_score",
        _LIQUIDITY_WATCH_REASON,
        _LIQUIDITY_BLOCK_REASON,
    ),
    (
        "correlated_catalyst_exposure_score",
        _CORRELATED_WATCH_REASON,
        _CORRELATED_BLOCK_REASON,
    ),
    (
        "late_information_shock_score",
        _LATE_WATCH_REASON,
        _LATE_BLOCK_REASON,
    ),
    (
        "maximum_loss_concentration_score",
        _MAX_LOSS_WATCH_REASON,
        _MAX_LOSS_BLOCK_REASON,
    ),
)


@dataclass(frozen=True)
class StrategyCandidateTailRiskDigestConfig:
    config_version: str = DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_DIGEST_CONFIG_VERSION
    watch_feature_score: Decimal = Decimal("0.350000")
    block_feature_score: Decimal = Decimal("0.700000")
    watch_tail_risk_score: Decimal = Decimal("0.400000")
    block_tail_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "watch_feature_score",
            "block_feature_score",
            "watch_tail_risk_score",
            "block_tail_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "block_feature_score",
            self.watch_feature_score,
            self.block_feature_score,
        )
        _require_threshold_sequence(
            "block_tail_risk_score",
            self.watch_tail_risk_score,
            self.block_tail_risk_score,
        )
        require_paper_only_flags("tail risk config", self)


@dataclass(frozen=True)
class StrategyCandidateTailRiskRecord:
    candidate_reference: str
    market_reference: str
    observed_at: datetime
    binary_resolution_ambiguity_score: Decimal
    liquidity_slippage_tail_score: Decimal
    correlated_catalyst_exposure_score: Decimal
    late_information_shock_score: Decimal
    maximum_loss_concentration_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "candidate_reference",
            _redacted_reference("candidate_ref_", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "market_reference",
            _redacted_reference("market_ref_", self.market_reference),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name, _, _ in _FEATURE_SPECS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("tail risk record", self)


@dataclass(frozen=True)
class StrategyCandidateTailRiskDigestRow:
    redacted_candidate_reference: str
    redacted_market_reference: str
    observed_at: datetime
    binary_resolution_ambiguity_score: Decimal
    liquidity_slippage_tail_score: Decimal
    correlated_catalyst_exposure_score: Decimal
    late_information_shock_score: Decimal
    maximum_loss_concentration_score: Decimal
    tail_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
            "candidate_ref_",
        )
        _require_redacted_reference(
            "redacted_market_reference",
            self.redacted_market_reference,
            "market_ref_",
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name, _, _ in _FEATURE_SPECS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "tail_risk_score",
            _normalize_unit_decimal("tail_risk_score", self.tail_risk_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("tail risk row", self)


@dataclass(frozen=True)
class StrategyCandidateTailRiskDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_tail_risk_score: Decimal
    max_binary_resolution_ambiguity_score: Decimal
    max_liquidity_slippage_tail_score: Decimal
    max_correlated_catalyst_exposure_score: Decimal
    max_late_information_shock_score: Decimal
    max_maximum_loss_concentration_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateTailRiskDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_tail_risk_score",
            "max_binary_resolution_ambiguity_score",
            "max_liquidity_slippage_tail_score",
            "max_correlated_catalyst_exposure_score",
            "max_late_information_shock_score",
            "max_maximum_loss_concentration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("tail risk report", self)


def build_strategy_candidate_tail_risk_digest(
    records: Iterable[object],
    *,
    config: StrategyCandidateTailRiskDigestConfig,
    generated_at: datetime,
) -> StrategyCandidateTailRiskDigestReport:
    if type(config) is not StrategyCandidateTailRiskDigestConfig:
        raise ValueError("config must be a StrategyCandidateTailRiskDigestConfig")
    require_paper_only_flags("tail risk config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_record(
                    record,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for record in _normalize_records(records)
            ),
            key=_row_key,
        ),
    )
    return StrategyCandidateTailRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        max_tail_risk_score=_max_decimal(row.tail_risk_score for row in rows),
        max_binary_resolution_ambiguity_score=_max_decimal(
            row.binary_resolution_ambiguity_score for row in rows
        ),
        max_liquidity_slippage_tail_score=_max_decimal(
            row.liquidity_slippage_tail_score for row in rows
        ),
        max_correlated_catalyst_exposure_score=_max_decimal(
            row.correlated_catalyst_exposure_score for row in rows
        ),
        max_late_information_shock_score=_max_decimal(
            row.late_information_shock_score for row in rows
        ),
        max_maximum_loss_concentration_score=_max_decimal(
            row.maximum_loss_concentration_score for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_tail_risk_digest_payload(
    report: StrategyCandidateTailRiskDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateTailRiskDigestReport:
        raise ValueError("report must be a StrategyCandidateTailRiskDigestReport")
    require_paper_only_flags("tail risk report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    require_paper_only_flags("tail risk payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_record(
    record: StrategyCandidateTailRiskRecord,
    *,
    config: StrategyCandidateTailRiskDigestConfig,
    generated_at: datetime,
) -> StrategyCandidateTailRiskDigestRow:
    if record.observed_at > generated_at:
        raise ValueError("observed_at must not follow generated_at")
    tail_risk_score = _tail_risk_score(record)
    reason_codes = list(record.reason_codes)
    scored_reason_codes = _scored_reason_codes(
        record,
        tail_risk_score=tail_risk_score,
        config=config,
    )
    reason_codes.extend(scored_reason_codes)
    if not scored_reason_codes:
        reason_codes.append(_PASS_REASON)
    stable_reason_codes = _stable_reason_codes("reason_codes", tuple(reason_codes))
    return StrategyCandidateTailRiskDigestRow(
        redacted_candidate_reference=record.candidate_reference,
        redacted_market_reference=record.market_reference,
        observed_at=record.observed_at,
        binary_resolution_ambiguity_score=record.binary_resolution_ambiguity_score,
        liquidity_slippage_tail_score=record.liquidity_slippage_tail_score,
        correlated_catalyst_exposure_score=record.correlated_catalyst_exposure_score,
        late_information_shock_score=record.late_information_shock_score,
        maximum_loss_concentration_score=record.maximum_loss_concentration_score,
        tail_risk_score=tail_risk_score,
        status=_status_from_reason_codes(stable_reason_codes),
        reason_codes=stable_reason_codes,
    )


def _scored_reason_codes(
    record: StrategyCandidateTailRiskRecord,
    *,
    tail_risk_score: Decimal,
    config: StrategyCandidateTailRiskDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for field_name, watch_reason, block_reason in _FEATURE_SPECS:
        value = getattr(record, field_name)
        if value >= config.block_feature_score:
            reason_codes.append(block_reason)
        elif value >= config.watch_feature_score:
            reason_codes.append(watch_reason)
    has_block_reason = any(reason_code in _BLOCK_REASONS for reason_code in reason_codes)
    has_watch_reason = any(reason_code in _WATCH_REASONS for reason_code in reason_codes)
    if tail_risk_score >= config.block_tail_risk_score and not has_block_reason:
        reason_codes.append(_TAIL_SCORE_BLOCK_REASON)
    elif tail_risk_score >= config.watch_tail_risk_score and not (
        has_block_reason or has_watch_reason
    ):
        reason_codes.append(_TAIL_SCORE_WATCH_REASON)
    return tuple(reason_codes)


def _normalize_records(
    records: Iterable[object],
) -> tuple[StrategyCandidateTailRiskRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be iterable")
    try:
        items = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be iterable") from exc
    seen_references: set[str] = set()
    for item in items:
        if type(item) is not StrategyCandidateTailRiskRecord:
            raise ValueError(
                "records must contain StrategyCandidateTailRiskRecord values",
            )
        require_paper_only_flags("tail risk record", item)
        if item.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference")
        seen_references.add(item.candidate_reference)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCandidateTailRiskDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateTailRiskDigestRow:
            raise ValueError(
                "rows must contain StrategyCandidateTailRiskDigestRow values",
            )
        require_paper_only_flags("tail risk row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must be sorted")
    if len({row.redacted_candidate_reference for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: StrategyCandidateTailRiskDigestRow) -> None:
    if row.tail_risk_score != _tail_risk_score(row):
        raise ValueError("tail_risk_score must match feature scores")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and _PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")
    if row.status == "watch" and not any(
        reason_code in _WATCH_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must include watch reason")
    if row.status == "block" and not any(
        reason_code in _BLOCK_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must include block reason")


def _validate_report(report: StrategyCandidateTailRiskDigestReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_tail_risk_score != _max_decimal(
        row.tail_risk_score for row in rows
    ):
        raise ValueError("max_tail_risk_score must match rows")
    for report_field_name, row_field_name in (
        (
            "max_binary_resolution_ambiguity_score",
            "binary_resolution_ambiguity_score",
        ),
        (
            "max_liquidity_slippage_tail_score",
            "liquidity_slippage_tail_score",
        ),
        (
            "max_correlated_catalyst_exposure_score",
            "correlated_catalyst_exposure_score",
        ),
        ("max_late_information_shock_score", "late_information_shock_score"),
        (
            "max_maximum_loss_concentration_score",
            "maximum_loss_concentration_score",
        ),
    ):
        if getattr(report, report_field_name) != _max_decimal(
            getattr(row, row_field_name) for row in rows
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _tail_risk_score(value: object) -> Decimal:
    return max(
        getattr(value, "binary_resolution_ambiguity_score"),
        getattr(value, "liquidity_slippage_tail_score"),
        getattr(value, "correlated_catalyst_exposure_score"),
        getattr(value, "late_information_shock_score"),
        getattr(value, "maximum_loss_concentration_score"),
    )


def _report_status(rows: tuple[StrategyCandidateTailRiskDigestRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateTailRiskDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in _WATCH_REASONS or reason_code in _BLOCK_REASONS
    }
    if not observed:
        return (_PASS_REASON,)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_key(
    row: StrategyCandidateTailRiskDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, datetime, str, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.tail_risk_score,
        -row.maximum_loss_concentration_score,
        -row.liquidity_slippage_tail_score,
        row.observed_at,
        row.redacted_candidate_reference,
        row.redacted_market_reference,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
        if reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        reason_index = _REASON_PRIORITY.index(reason_code)
        if reason_index <= previous_index:
            raise ValueError("reason_codes must use priority sequence")
        seen.add(reason_code)
        previous_index = reason_index
    return reason_codes


def _stable_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_text(field_name, item)
    return tuple(sorted(set(value)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_threshold_sequence(
    threshold_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{threshold_name} must be at least watch threshold")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be block, watch, or pass")


def _redacted_reference(prefix: str, value: str) -> str:
    digest = sha256(f"{prefix}\0{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _require_redacted_reference(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be redacted")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    suffix = value[len(prefix) :]
    if len(suffix) != 16 or any(char not in _HEX_CHARS for char in suffix):
        raise ValueError(f"{field_name} must be redacted")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_DIGEST_CONFIG_VERSION",
    "StrategyCandidateTailRiskDigestConfig",
    "StrategyCandidateTailRiskDigestReport",
    "StrategyCandidateTailRiskDigestRow",
    "StrategyCandidateTailRiskRecord",
    "build_strategy_candidate_tail_risk_digest",
    "strategy_candidate_tail_risk_digest_payload",
)
