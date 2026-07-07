"""Resolution-source risk premium reducer for paper reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "StrategyMarketResolutionSourceRiskPremiumV2Candidate",
    "StrategyMarketResolutionSourceRiskPremiumV2Config",
    "StrategyMarketResolutionSourceRiskPremiumV2Report",
    "StrategyMarketResolutionSourceRiskPremiumV2Row",
    "build_strategy_market_resolution_source_risk_premium_v2_report",
    "strategy_market_resolution_source_risk_premium_v2_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-market-resolution-source-risk-premium-v2"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
OFFICIAL_SOURCE_TARGET_COUNT = Decimal("2.000000")
AMBIGUITY_REASON_THRESHOLD = Decimal("0.500000")
ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")
STATUS_SORT_PRIORITY = {"block": 0, "watch": 1, "pass": 2}
TERMINAL_REASON_BY_STATUS = {
    "pass": "resolution_source_risk_pass",
    "watch": "resolution_source_risk_watch",
    "block": "resolution_source_risk_block",
}
DECIMAL_CONTEXT = Context(prec=64)


@dataclass(frozen=True)
class StrategyMarketResolutionSourceRiskPremiumV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    official_source_gap_weight: Decimal = Decimal("0.020000")
    proxy_source_weight: Decimal = Decimal("0.010000")
    ambiguity_weight: Decimal = Decimal("0.030000")
    missing_rule_source_weight: Decimal = Decimal("0.015000")
    watch_risk_premium: Decimal = Decimal("0.020000")
    block_risk_premium: Decimal = Decimal("0.050000")
    high_risk_premium_threshold: Decimal = Decimal("0.040000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "official_source_gap_weight",
            "proxy_source_weight",
            "ambiguity_weight",
            "missing_rule_source_weight",
            "watch_risk_premium",
            "block_risk_premium",
            "high_risk_premium_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_risk_premium < self.watch_risk_premium:
            raise ValueError("block_risk_premium must cover watch_risk_premium")
        require_paper_only_flags("resolution source risk premium config", self)
        reject_unsafe_surface_fields("resolution source risk premium config", self)


@dataclass(frozen=True)
class StrategyMarketResolutionSourceRiskPremiumV2Candidate:
    candidate_id: str
    market_id: str
    event_slug: str
    category: str
    base_edge: Decimal
    polymarket_rule_source_count: Decimal
    official_source_count: Decimal
    proxy_source_count: Decimal
    ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "event_slug", "category"):
            _require_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "base_edge", _normalize_decimal("base_edge", self.base_edge))
        for field_name in (
            "polymarket_rule_source_count",
            "official_source_count",
            "proxy_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_unit_decimal("ambiguity_score", self.ambiguity_score),
        )
        require_paper_only_flags("resolution source risk premium candidate", self)
        reject_unsafe_surface_fields("resolution source risk premium candidate", self)


@dataclass(frozen=True)
class StrategyMarketResolutionSourceRiskPremiumV2Row:
    candidate_id: str
    market_id: str
    event_slug: str
    category: str
    base_edge: Decimal
    polymarket_rule_source_count: Decimal
    official_source_count: Decimal
    proxy_source_count: Decimal
    ambiguity_score: Decimal
    resolution_source_risk_premium: Decimal
    risk_adjusted_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "event_slug", "category"):
            _require_identifier(field_name, getattr(self, field_name))
        for field_name in ("base_edge", "risk_adjusted_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "polymarket_rule_source_count",
            "official_source_count",
            "proxy_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_unit_decimal("ambiguity_score", self.ambiguity_score),
        )
        object.__setattr__(
            self,
            "resolution_source_risk_premium",
            _normalize_nonnegative_decimal(
                "resolution_source_risk_premium",
                self.resolution_source_risk_premium,
            ),
        )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        require_paper_only_flags("resolution source risk premium row", self)
        reject_unsafe_surface_fields("resolution source risk premium row", self)


@dataclass(frozen=True)
class StrategyMarketResolutionSourceRiskPremiumV2Report:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_risk_premium_count: Decimal
    proxy_source_count: Decimal
    missing_official_source_count: Decimal
    max_risk_premium: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    validation_digest: str
    rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_risk_premium_count",
            "proxy_source_count",
            "missing_official_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_risk_premium",
            _normalize_nonnegative_decimal("max_risk_premium", self.max_risk_premium),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_digest("validation_digest", self.validation_digest)
        if self.validation_digest != _derived_validation_digest(self):
            raise ValueError("validation_digest must match report payload")
        require_paper_only_flags("resolution source risk premium report", self)
        reject_unsafe_surface_fields("resolution source risk premium report", self)


def build_strategy_market_resolution_source_risk_premium_v2_report(
    candidates: Iterable[object],
    *,
    config: StrategyMarketResolutionSourceRiskPremiumV2Config,
) -> StrategyMarketResolutionSourceRiskPremiumV2Report:
    if type(config) is not StrategyMarketResolutionSourceRiskPremiumV2Config:
        raise ValueError(
            "config must be a StrategyMarketResolutionSourceRiskPremiumV2Config",
        )
    require_paper_only_flags("resolution source risk premium config", config)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in source_candidates),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(reason_code for reason_code, _ in reason_code_counts)
    report_values = {
        "config_version": config.config_version,
        "candidate_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "high_risk_premium_count": _high_risk_premium_count(rows, config),
        "proxy_source_count": _proxy_row_count(rows),
        "missing_official_source_count": _missing_official_source_count(rows),
        "max_risk_premium": _max_risk_premium(rows),
        "report_status": _report_status(rows),
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": rows,
    }
    return StrategyMarketResolutionSourceRiskPremiumV2Report(
        **report_values,
        validation_digest=_derived_validation_digest_from_values(report_values),
    )


def strategy_market_resolution_source_risk_premium_v2_payload(
    report: StrategyMarketResolutionSourceRiskPremiumV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyMarketResolutionSourceRiskPremiumV2Report:
        raise ValueError(
            "report must be a StrategyMarketResolutionSourceRiskPremiumV2Report",
        )
    require_paper_only_flags("resolution source risk premium report", report)
    reject_unsafe_surface_fields("resolution source risk premium payload", report)
    return _report_payload(report, include_validation_digest=True)


def _row_from_candidate(
    candidate: StrategyMarketResolutionSourceRiskPremiumV2Candidate,
    *,
    config: StrategyMarketResolutionSourceRiskPremiumV2Config,
) -> StrategyMarketResolutionSourceRiskPremiumV2Row:
    risk_premium = _risk_premium(candidate, config)
    risk_adjusted_edge = _subtract_decimal(candidate.base_edge, risk_premium)
    status = _row_status(
        risk_premium=risk_premium,
        risk_adjusted_edge=risk_adjusted_edge,
        config=config,
    )
    return StrategyMarketResolutionSourceRiskPremiumV2Row(
        candidate_id=candidate.candidate_id,
        market_id=candidate.market_id,
        event_slug=candidate.event_slug,
        category=candidate.category,
        base_edge=candidate.base_edge,
        polymarket_rule_source_count=candidate.polymarket_rule_source_count,
        official_source_count=candidate.official_source_count,
        proxy_source_count=candidate.proxy_source_count,
        ambiguity_score=candidate.ambiguity_score,
        resolution_source_risk_premium=risk_premium,
        risk_adjusted_edge=risk_adjusted_edge,
        status=status,
        reason_codes=_row_reason_codes(candidate, status),
    )


def _risk_premium(
    candidate: StrategyMarketResolutionSourceRiskPremiumV2Candidate,
    config: StrategyMarketResolutionSourceRiskPremiumV2Config,
) -> Decimal:
    official_gap_component = (
        config.official_source_gap_weight
        if candidate.official_source_count < OFFICIAL_SOURCE_TARGET_COUNT
        else ZERO
    )
    proxy_component = _mul_decimal(candidate.proxy_source_count, config.proxy_source_weight)
    ambiguity_component = _mul_decimal(candidate.ambiguity_score, config.ambiguity_weight)
    missing_rule_component = (
        config.missing_rule_source_weight
        if candidate.polymarket_rule_source_count == ZERO
        else ZERO
    )
    return _add_decimal(
        official_gap_component,
        proxy_component,
        ambiguity_component,
        missing_rule_component,
    )


def _row_status(
    *,
    risk_premium: Decimal,
    risk_adjusted_edge: Decimal,
    config: StrategyMarketResolutionSourceRiskPremiumV2Config,
) -> str:
    if risk_adjusted_edge < ZERO or risk_premium >= config.block_risk_premium:
        return "block"
    if risk_premium >= config.watch_risk_premium:
        return "watch"
    return "pass"


def _row_reason_codes(
    candidate: StrategyMarketResolutionSourceRiskPremiumV2Candidate,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.polymarket_rule_source_count == ZERO:
        reason_codes.append("missing_polymarket_rule_source")
    if candidate.official_source_count == ZERO:
        reason_codes.append("missing_official_resolution_source")
    elif candidate.official_source_count < OFFICIAL_SOURCE_TARGET_COUNT:
        reason_codes.append("official_resolution_source_gap")
    if candidate.proxy_source_count > ZERO:
        reason_codes.append("uses_proxy_resolution_source")
    if candidate.ambiguity_score >= AMBIGUITY_REASON_THRESHOLD:
        reason_codes.append("ambiguous_resolution_criteria")
    reason_codes.append(TERMINAL_REASON_BY_STATUS[status])
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyMarketResolutionSourceRiskPremiumV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    rows: list[StrategyMarketResolutionSourceRiskPremiumV2Candidate] = []
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyMarketResolutionSourceRiskPremiumV2Candidate:
            raise ValueError(
                "candidates must contain StrategyMarketResolutionSourceRiskPremiumV2Candidate",
            )
        require_paper_only_flags("resolution source risk premium candidate", candidate)
        if candidate.candidate_id in seen:
            raise ValueError("duplicate candidate_id")
        seen.add(candidate.candidate_id)
        rows.append(candidate)
    return tuple(rows)


def _normalize_rows(
    rows: object,
) -> tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyMarketResolutionSourceRiskPremiumV2Row:
            raise ValueError("rows must contain StrategyMarketResolutionSourceRiskPremiumV2Row")
        require_paper_only_flags("resolution source risk premium row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(row: StrategyMarketResolutionSourceRiskPremiumV2Row) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_SORT_PRIORITY[row.status],
        -row.resolution_source_risk_premium,
        row.candidate_id,
        row.market_id,
    )


def _status_count(
    rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _high_risk_premium_count(
    rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...],
    config: StrategyMarketResolutionSourceRiskPremiumV2Config,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if row.resolution_source_risk_premium >= config.high_risk_premium_threshold
        ),
    )


def _proxy_row_count(rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...]) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.proxy_source_count > ZERO))


def _missing_official_source_count(
    rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.official_source_count == ZERO))


def _max_risk_premium(rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...]) -> Decimal:
    if not rows:
        return _zero()
    return max(row.resolution_source_risk_premium for row in rows)


def _report_status(rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple((reason_code, _count_decimal(counts[reason_code])) for reason_code in sorted(counts))


def _validate_row(row: StrategyMarketResolutionSourceRiskPremiumV2Row) -> None:
    if row.risk_adjusted_edge != _subtract_decimal(
        row.base_edge,
        row.resolution_source_risk_premium,
    ):
        raise ValueError("risk_adjusted_edge must match base_edge less risk premium")
    terminal_reason = TERMINAL_REASON_BY_STATUS[row.status]
    if terminal_reason not in row.reason_codes:
        raise ValueError("reason_codes must include the status reason")


def _validate_report(report: StrategyMarketResolutionSourceRiskPremiumV2Report) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.proxy_source_count != _proxy_row_count(report.rows):
        raise ValueError("proxy_source_count must match rows")
    if report.missing_official_source_count != _missing_official_source_count(report.rows):
        raise ValueError("missing_official_source_count must match rows")
    if report.max_risk_premium != _max_risk_premium(report.rows):
        raise ValueError("max_risk_premium must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(reason_code for reason_code, _ in expected_reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.candidate_count == ZERO:
        if (
            report.pass_count != ZERO
            or report.watch_count != ZERO
            or report.block_count != ZERO
            or report.high_risk_premium_count != ZERO
            or report.proxy_source_count != ZERO
            or report.missing_official_source_count != ZERO
            or report.max_risk_premium != ZERO.quantize(QUANTUM)
            or report.reason_codes != ()
            or report.reason_code_counts != ()
            or report.report_status != "empty"
        ):
            raise ValueError("empty report must use empty status and zero values")


def _normalize_reason_code_counts(
    values: object,
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        pairs = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        reason_code, count = pair
        _require_reason_code("reason_code_counts", reason_code)
        if previous is not None and reason_code <= previous:
            raise ValueError("reason_code_counts must be sorted and unique")
        normalized_count = _normalize_count_decimal("reason_code_counts", count)
        if normalized_count <= ZERO:
            raise ValueError("reason_code_counts must be positive")
        normalized.append((reason_code, normalized_count))
        previous = reason_code
    return tuple(normalized)


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    parts = value.split("_")
    if any(not part or not part.isalnum() or part != part.lower() for part in parts):
        raise ValueError(f"{field_name} must contain canonical reason codes")


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical identifier")
    if value.lower() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a canonical identifier")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a canonical identifier")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    hexdigits = set("0123456789abcdef")
    if any(character not in hexdigits for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _add_decimal(first: Decimal, second: Decimal, *rest: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = first + second
        for value in rest:
            total += value
        return total.quantize(QUANTUM)


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _mul_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


def _derived_validation_digest(
    report: StrategyMarketResolutionSourceRiskPremiumV2Report,
) -> str:
    return _derived_validation_digest_from_values(
        {
            "config_version": report.config_version,
            "candidate_count": report.candidate_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "high_risk_premium_count": report.high_risk_premium_count,
            "proxy_source_count": report.proxy_source_count,
            "missing_official_source_count": report.missing_official_source_count,
            "max_risk_premium": report.max_risk_premium,
            "report_status": report.report_status,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
            "rows": report.rows,
        },
    )


def _derived_validation_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_from_values(values, include_validation_digest=False)
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(rendered.encode("utf-8")).hexdigest()


def _report_payload(
    report: StrategyMarketResolutionSourceRiskPremiumV2Report,
    *,
    include_validation_digest: bool,
) -> dict[str, object]:
    values = {
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "high_risk_premium_count": report.high_risk_premium_count,
        "proxy_source_count": report.proxy_source_count,
        "missing_official_source_count": report.missing_official_source_count,
        "max_risk_premium": report.max_risk_premium,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "reason_code_counts": report.reason_code_counts,
        "rows": report.rows,
    }
    payload = _report_payload_from_values(
        values,
        include_validation_digest=include_validation_digest,
    )
    if include_validation_digest:
        payload["validation_digest"] = report.validation_digest
    return payload


def _report_payload_from_values(
    values: dict[str, object],
    *,
    include_validation_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "config_version": values["config_version"],
        "candidate_count": _count_payload(values["candidate_count"]),
        "pass_count": _count_payload(values["pass_count"]),
        "watch_count": _count_payload(values["watch_count"]),
        "block_count": _count_payload(values["block_count"]),
        "high_risk_premium_count": _count_payload(values["high_risk_premium_count"]),
        "proxy_source_count": _count_payload(values["proxy_source_count"]),
        "missing_official_source_count": _count_payload(
            values["missing_official_source_count"],
        ),
        "max_risk_premium": _decimal_payload(values["max_risk_premium"]),
        "report_status": values["report_status"],
        "reason_codes": list(_as_reason_codes(values["reason_codes"])),
        "reason_code_counts": [
            [reason_code, _count_payload(count)]
            for reason_code, count in _as_reason_code_counts(values["reason_code_counts"])
        ],
        "rows": [_row_payload(row) for row in _as_rows(values["rows"])],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_validation_digest:
        payload["validation_digest"] = ""
    _reject_float_values(payload)
    return payload


def _row_payload(row: StrategyMarketResolutionSourceRiskPremiumV2Row) -> dict[str, object]:
    return {
        "candidate_id": row.candidate_id,
        "market_id": row.market_id,
        "event_slug": row.event_slug,
        "category": row.category,
        "base_edge": _decimal_payload(row.base_edge),
        "polymarket_rule_source_count": _count_payload(row.polymarket_rule_source_count),
        "official_source_count": _count_payload(row.official_source_count),
        "proxy_source_count": _count_payload(row.proxy_source_count),
        "ambiguity_score": _decimal_payload(row.ambiguity_score),
        "resolution_source_risk_premium": _decimal_payload(
            row.resolution_source_risk_premium,
        ),
        "risk_adjusted_edge": _decimal_payload(row.risk_adjusted_edge),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _as_rows(value: object) -> tuple[StrategyMarketResolutionSourceRiskPremiumV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    return value


def _as_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return value


def _as_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    return value


def _decimal_payload(value: object) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: object) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))


def _reject_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_float_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_float_values(item)


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        return _decimal_payload(value)
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value
