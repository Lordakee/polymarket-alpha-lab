"""Pure report-only market fee and spread stress reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_STRESS_CONFIG_VERSION",
    "MarketFeeSpreadStressConfig",
    "MarketFeeSpreadStressObservation",
    "MarketFeeSpreadStressReasonCodeCount",
    "MarketFeeSpreadStressReport",
    "MarketFeeSpreadStressRow",
    "build_research_market_fee_spread_stress_report",
    "research_market_fee_spread_stress_report_payload",
    "validate_research_market_fee_spread_stress_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_SPREAD_STRESS_CONFIG_VERSION = (
    "research-market-fee-spread-stress-report-v1"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64)

BLOCKED_STATUS = "block"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
MECHANICS_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "=",
    "api" "_" "key",
    "au" "th",
    "dsn",
    "market_id",
    "market_slug",
    "order",
    "private" "_" "key",
    "question",
    "raw_candidate_id",
    "raw_market_reference",
    "raw_source_reference",
    "recommend",
    "secret",
    "sizing",
    "source_text",
    "source_url",
    "table_name",
    "token",
    "tra" "de",
    "wal" "let",
)

_REPORT_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "mechanics_status",
        "input_count",
        "row_count",
        "blocked_count",
        "watch_count",
        "pass_count",
        "stale_book_count",
        "max_stress_score",
        "average_stress_score",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_REPORT_COUNT_PAYLOAD_FIELDS = frozenset(
    {
        "input_count",
        "row_count",
        "blocked_count",
        "watch_count",
        "pass_count",
        "stale_book_count",
    },
)
_REPORT_PROBABILITY_PAYLOAD_FIELDS = frozenset(
    {
        "max_stress_score",
        "average_stress_score",
    },
)
_ROW_PAYLOAD_KEYS = frozenset(
    {
        "candidate_digest",
        "book_observed_at",
        "book_age_seconds",
        "taker_fee_bps",
        "spread_width_bps",
        "depth_concentration",
        "settlement_uncertainty",
        "taker_fee_pressure",
        "spread_pressure",
        "staleness_pressure",
        "stress_score",
        "mechanics_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_ROW_NONNEGATIVE_DECIMAL_PAYLOAD_FIELDS = frozenset(
    {
        "book_age_seconds",
        "taker_fee_bps",
        "spread_width_bps",
    },
)
_ROW_PROBABILITY_PAYLOAD_FIELDS = frozenset(
    {
        "depth_concentration",
        "settlement_uncertainty",
        "taker_fee_pressure",
        "spread_pressure",
        "staleness_pressure",
        "stress_score",
    },
)
_REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    {
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    },
)


@dataclass(frozen=True)
class MarketFeeSpreadStressConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_FEE_SPREAD_STRESS_CONFIG_VERSION
    max_book_age_seconds: Decimal = Decimal("120.000000")
    watch_stress_score_threshold: Decimal = Decimal("0.350000")
    blocked_stress_score_threshold: Decimal = Decimal("0.650000")
    high_taker_fee_bps: Decimal = Decimal("50.000000")
    wide_spread_width_bps: Decimal = Decimal("300.000000")
    watch_taker_fee_bps: Decimal = Decimal("20.000000")
    watch_spread_width_bps: Decimal = Decimal("100.000000")
    watch_depth_concentration: Decimal = Decimal("0.500000")
    watch_settlement_uncertainty: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketFeeSpreadStressConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_book_age_seconds",
            _normalize_positive_decimal("max_book_age_seconds", self.max_book_age_seconds),
        )
        for field_name in (
            "watch_stress_score_threshold",
            "blocked_stress_score_threshold",
            "watch_depth_concentration",
            "watch_settlement_uncertainty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_taker_fee_bps",
            "wide_spread_width_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_taker_fee_bps",
            "watch_spread_width_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_stress_score_threshold <= self.watch_stress_score_threshold:
            raise ValueError(
                "blocked_stress_score_threshold must exceed "
                "watch_stress_score_threshold",
            )
        if self.watch_taker_fee_bps > self.high_taker_fee_bps:
            raise ValueError("watch_taker_fee_bps must not exceed high_taker_fee_bps")
        if self.watch_spread_width_bps > self.wide_spread_width_bps:
            raise ValueError(
                "watch_spread_width_bps must not exceed wide_spread_width_bps",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketFeeSpreadStressObservation:
    raw_candidate_id: str
    raw_market_reference: str
    raw_source_reference: str
    book_observed_at: datetime
    taker_fee_bps: Decimal
    spread_width_bps: Decimal
    depth_concentration: Decimal
    settlement_uncertainty: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketFeeSpreadStressObservation, "observation")
        for field_name in (
            "raw_candidate_id",
            "raw_market_reference",
            "raw_source_reference",
        ):
            _require_raw_reference(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "book_observed_at",
            _as_utc("book_observed_at", self.book_observed_at),
        )
        for field_name in ("taker_fee_bps", "spread_width_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_concentration", "settlement_uncertainty"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketFeeSpreadStressRow:
    candidate_digest: str
    book_observed_at: datetime
    book_age_seconds: Decimal
    taker_fee_bps: Decimal
    spread_width_bps: Decimal
    depth_concentration: Decimal
    settlement_uncertainty: Decimal
    taker_fee_pressure: Decimal
    spread_pressure: Decimal
    staleness_pressure: Decimal
    stress_score: Decimal
    mechanics_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketFeeSpreadStressRow, "row")
        _require_sha256_digest("candidate_digest", self.candidate_digest)
        object.__setattr__(
            self,
            "book_observed_at",
            _as_utc("book_observed_at", self.book_observed_at),
        )
        for field_name in (
            "book_age_seconds",
            "taker_fee_bps",
            "spread_width_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_concentration",
            "settlement_uncertainty",
            "taker_fee_pressure",
            "spread_pressure",
            "staleness_pressure",
            "stress_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_mechanics_status("mechanics_status", self.mechanics_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketFeeSpreadStressReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketFeeSpreadStressReasonCodeCount, "reason_count")
        _require_public_identifier("reason_code", self.reason_code)
        if _contains_unsafe_public_term(self.reason_code):
            raise ValueError("reason_code has unsafe public payload")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketFeeSpreadStressReport:
    generated_at: datetime
    config_version: str
    mechanics_status: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_book_count: Decimal
    max_stress_score: Decimal
    average_stress_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketFeeSpreadStressReasonCodeCount, ...]
    rows: tuple[MarketFeeSpreadStressRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketFeeSpreadStressReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_mechanics_status("mechanics_status", self.mechanics_status)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_book_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_stress_score", "average_stress_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )


def build_research_market_fee_spread_stress_report(
    observations: Iterable[MarketFeeSpreadStressObservation],
    *,
    config: MarketFeeSpreadStressConfig,
    generated_at: datetime,
) -> MarketFeeSpreadStressReport:
    if type(config) is not MarketFeeSpreadStressConfig:
        raise ValueError("config must be a MarketFeeSpreadStressConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(value, config=config, generated_at=generated_at)
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    return MarketFeeSpreadStressReport(
        generated_at=generated_at,
        config_version=config.config_version,
        mechanics_status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_book_count=_reason_count(rows, "fee_spread_book_stale"),
        max_stress_score=_max_row_decimal(rows, "stress_score"),
        average_stress_score=_average_row_decimal(rows, "stress_score"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_spread_stress_report_payload(
    report: MarketFeeSpreadStressReport,
) -> dict[str, Any]:
    if type(report) is not MarketFeeSpreadStressReport:
        raise ValueError("report must be a MarketFeeSpreadStressReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_spread_stress_report_payload(payload)
    return payload


def validate_research_market_fee_spread_stress_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    _validate_public_payload_shape(payload)
    return payload


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_key_set("payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_datetime_payload("generated_at", payload["generated_at"])
    if payload["config_version"] != DEFAULT_RESEARCH_MARKET_FEE_SPREAD_STRESS_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_mechanics_status("mechanics_status", payload["mechanics_status"])
    for field_name in _REPORT_COUNT_PAYLOAD_FIELDS:
        _require_count_payload(field_name, payload[field_name])
    for field_name in _REPORT_PROBABILITY_PAYLOAD_FIELDS:
        _require_probability_payload(field_name, payload[field_name])
    _require_reason_code_payloads("reason_codes", payload["reason_codes"])
    reason_code_counts = _require_reason_code_count_payloads(
        payload["reason_code_counts"],
    )
    rows = _require_row_payloads(payload["rows"])
    _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _validate_public_payload_aggregates(payload, rows, reason_code_counts)


def _require_payload_key_set(
    label: str,
    value: object,
    expected_keys: frozenset[str],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} must have deterministic public payload keys")


def _require_datetime_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    normalized = parsed.astimezone(UTC)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_count_payload(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal_payload(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal string")
    return normalized


def _require_probability_payload(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal_payload(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        normalized = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if value.startswith("-") or not normalized.is_finite():
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    quantized = _quantize_decimal(normalized)
    if quantized != normalized or f"{quantized:.6f}" != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return quantized


def _require_reason_code_payloads(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes: list[str] = []
    for reason_code in value:
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        reason_codes.append(reason_code)
    normalized = tuple(reason_codes)
    if normalized != tuple(sorted(normalized)) or len(frozenset(normalized)) != len(
        normalized,
    ):
        raise ValueError(f"{field_name} must be sorted unique reason codes")
    return normalized


def _require_reason_code_count_payloads(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    normalized: list[tuple[str, Decimal]] = []
    for index, item in enumerate(value):
        label = f"reason_code_counts[{index}]"
        _require_payload_key_set(label, item, _REASON_CODE_COUNT_PAYLOAD_KEYS)
        _require_public_payload_flags(label, item)
        reason_code = item["reason_code"]
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        normalized.append(
            (
                reason_code,
                _require_count_payload(f"{label}.count", item["count"]),
            ),
        )
    sorted_counts = tuple(sorted(normalized, key=lambda item: (-item[1], item[0])))
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return tuple(normalized)


def _require_row_payloads(value: object) -> tuple[dict[str, Any], ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        label = f"rows[{index}]"
        _require_payload_key_set(label, item, _ROW_PAYLOAD_KEYS)
        _require_public_payload_flags(label, item)
        _require_sha256_digest(f"{label}.candidate_digest", item["candidate_digest"])
        _require_datetime_payload(f"{label}.book_observed_at", item["book_observed_at"])
        for field_name in _ROW_NONNEGATIVE_DECIMAL_PAYLOAD_FIELDS:
            _require_nonnegative_decimal_payload(
                f"{label}.{field_name}",
                item[field_name],
            )
        for field_name in _ROW_PROBABILITY_PAYLOAD_FIELDS:
            _require_probability_payload(f"{label}.{field_name}", item[field_name])
        _require_mechanics_status(f"{label}.mechanics_status", item["mechanics_status"])
        reason_codes = _require_reason_code_payloads(
            f"{label}.reason_codes",
            item["reason_codes"],
        )
        if f"fee_spread_status_{item['mechanics_status']}" not in reason_codes:
            raise ValueError("mechanics_status must match reason_codes")
        rows.append(item)
    if tuple(rows) != tuple(sorted(rows, key=_payload_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return tuple(rows)


def _require_public_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _validate_public_payload_aggregates(
    payload: dict[str, Any],
    rows: tuple[dict[str, Any], ...],
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> None:
    row_count = _count_decimal(len(rows))
    if _require_count_payload("row_count", payload["row_count"]) != row_count:
        raise ValueError("row_count must match rows")
    if _require_count_payload("input_count", payload["input_count"]) != row_count:
        raise ValueError("input_count must match rows")
    for status, field_name in (
        (BLOCKED_STATUS, "blocked_count"),
        (WATCH_STATUS, "watch_count"),
        (PASS_STATUS, "pass_count"),
    ):
        if _require_count_payload(field_name, payload[field_name]) != _payload_status_count(
            rows,
            status,
        ):
            raise ValueError(f"{field_name} must match rows")
    if _require_count_payload(
        "stale_book_count",
        payload["stale_book_count"],
    ) != _payload_reason_count(rows, "fee_spread_book_stale"):
        raise ValueError("stale_book_count must match rows")
    if _require_probability_payload(
        "max_stress_score",
        payload["max_stress_score"],
    ) != _payload_max_stress_score(rows):
        raise ValueError("max_stress_score must match rows")
    if _require_probability_payload(
        "average_stress_score",
        payload["average_stress_score"],
    ) != _payload_average_stress_score(rows):
        raise ValueError("average_stress_score must match rows")
    if payload["mechanics_status"] != _payload_report_status(rows):
        raise ValueError("mechanics_status must match rows")
    if tuple(payload["reason_codes"]) != _payload_report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if reason_code_counts != _payload_reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _payload_row_sort_key(row: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row["mechanics_status"]],
        -_require_probability_payload("stress_score", row["stress_score"]),
        row["candidate_digest"],
    )


def _payload_status_count(rows: tuple[dict[str, Any], ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row["mechanics_status"] == status))


def _payload_reason_count(rows: tuple[dict[str, Any], ...], code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row["reason_codes"]))


def _payload_max_stress_score(rows: tuple[dict[str, Any], ...]) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(_require_probability_payload("stress_score", row["stress_score"]) for row in rows)


def _payload_average_stress_score(rows: tuple[dict[str, Any], ...]) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    total = ZERO
    for row in rows:
        total = _quantize_decimal(
            total + _require_probability_payload("stress_score", row["stress_score"]),
        )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _payload_report_status(rows: tuple[dict[str, Any], ...]) -> str:
    if any(row["mechanics_status"] == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row["mechanics_status"] == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _payload_report_reason_codes(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    if not rows:
        return ("fee_spread_stress_report_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row["reason_codes"])
    return _normalize_reason_codes(tuple(reason_codes))


def _payload_reason_code_counts(
    rows: tuple[dict[str, Any], ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row["reason_codes"]:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _row_from_observation(
    value: MarketFeeSpreadStressObservation,
    *,
    config: MarketFeeSpreadStressConfig,
    generated_at: datetime,
) -> MarketFeeSpreadStressRow:
    book_age_seconds = _seconds_between(
        generated_at,
        value.book_observed_at,
        "book_observed_at",
    )
    book_fresh = book_age_seconds <= config.max_book_age_seconds
    taker_fee_pressure = _ratio_pressure(value.taker_fee_bps, config.high_taker_fee_bps)
    spread_pressure = _ratio_pressure(value.spread_width_bps, config.wide_spread_width_bps)
    staleness_pressure = _ratio_pressure(book_age_seconds, config.max_book_age_seconds)
    stress_score = _stress_score(
        taker_fee_pressure=taker_fee_pressure,
        spread_pressure=spread_pressure,
        depth_concentration=value.depth_concentration,
        settlement_uncertainty=value.settlement_uncertainty,
        staleness_pressure=staleness_pressure,
    )
    if not book_fresh or stress_score >= config.blocked_stress_score_threshold:
        status = BLOCKED_STATUS
    elif stress_score >= config.watch_stress_score_threshold:
        status = WATCH_STATUS
    else:
        status = PASS_STATUS
    return MarketFeeSpreadStressRow(
        candidate_digest=_candidate_digest(value.raw_candidate_id),
        book_observed_at=value.book_observed_at,
        book_age_seconds=book_age_seconds,
        taker_fee_bps=value.taker_fee_bps,
        spread_width_bps=value.spread_width_bps,
        depth_concentration=value.depth_concentration,
        settlement_uncertainty=value.settlement_uncertainty,
        taker_fee_pressure=taker_fee_pressure,
        spread_pressure=spread_pressure,
        staleness_pressure=staleness_pressure,
        stress_score=stress_score,
        mechanics_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            book_fresh=book_fresh,
            status=status,
            taker_fee_bps=value.taker_fee_bps,
            spread_width_bps=value.spread_width_bps,
            depth_concentration=value.depth_concentration,
            settlement_uncertainty=value.settlement_uncertainty,
            config=config,
        ),
    )


def _stress_score(
    *,
    taker_fee_pressure: Decimal,
    spread_pressure: Decimal,
    depth_concentration: Decimal,
    settlement_uncertainty: Decimal,
    staleness_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            min(
                (
                    taker_fee_pressure
                    + spread_pressure
                    + depth_concentration
                    + settlement_uncertainty
                    + staleness_pressure
                )
                / FIVE,
                ONE,
            ),
        )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    book_fresh: bool,
    status: str,
    taker_fee_bps: Decimal,
    spread_width_bps: Decimal,
    depth_concentration: Decimal,
    settlement_uncertainty: Decimal,
    config: MarketFeeSpreadStressConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(
        "fee_spread_source_fresh" if book_fresh else "fee_spread_book_stale",
    )
    reason_codes.append(f"fee_spread_status_{status}")
    if taker_fee_bps >= config.watch_taker_fee_bps:
        reason_codes.append("fee_spread_taker_fee_elevated")
    if spread_width_bps >= config.watch_spread_width_bps:
        reason_codes.append("fee_spread_spread_width_elevated")
    if depth_concentration >= config.watch_depth_concentration:
        reason_codes.append("fee_spread_depth_concentrated")
    if settlement_uncertainty >= config.watch_settlement_uncertainty:
        reason_codes.append("fee_spread_settlement_uncertainty_elevated")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[MarketFeeSpreadStressObservation],
) -> tuple[MarketFeeSpreadStressObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not MarketFeeSpreadStressObservation:
            raise ValueError(
                "observations must contain MarketFeeSpreadStressObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketFeeSpreadStressRow],
) -> tuple[MarketFeeSpreadStressRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketFeeSpreadStressRow:
            raise ValueError("rows must contain MarketFeeSpreadStressRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[MarketFeeSpreadStressReasonCodeCount],
) -> tuple[MarketFeeSpreadStressReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not MarketFeeSpreadStressReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketFeeSpreadStressReasonCodeCount",
            )
        _require_hard_flags(count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: MarketFeeSpreadStressRow) -> None:
    status_reason = f"fee_spread_status_{row.mechanics_status}"
    if status_reason not in row.reason_codes:
        raise ValueError("mechanics_status must match reason_codes")


def _validate_report_consistency(report: MarketFeeSpreadStressReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.stale_book_count != _reason_count(report.rows, "fee_spread_book_stale"):
        raise ValueError("stale_book_count must match rows")
    if report.max_stress_score != _max_row_decimal(report.rows, "stress_score"):
        raise ValueError("max_stress_score must match rows")
    if report.average_stress_score != _average_row_decimal(report.rows, "stress_score"):
        raise ValueError("average_stress_score must match rows")
    if report.mechanics_status != _report_status(report.rows):
        raise ValueError("mechanics_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[MarketFeeSpreadStressRow, ...]) -> str:
    if any(row.mechanics_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.mechanics_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketFeeSpreadStressRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("fee_spread_stress_report_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[MarketFeeSpreadStressRow, ...],
) -> tuple[MarketFeeSpreadStressReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                MarketFeeSpreadStressReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[MarketFeeSpreadStressRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.mechanics_status == status))


def _reason_count(rows: tuple[MarketFeeSpreadStressRow, ...], code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row.reason_codes))


def _max_row_decimal(rows: tuple[MarketFeeSpreadStressRow, ...], field_name: str) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[MarketFeeSpreadStressRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _seconds_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError(f"{earlier_name} must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _ratio_pressure(value: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(min(value / denominator, ONE))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_raw_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_mechanics_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MECHANICS_STATUSES:
        raise ValueError(f"{field_name} must be a known mechanics status")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    _require_nested_payload_hard_flags(value)


def _require_nested_payload_hard_flags(value: object, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} must have string keys")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _require_nested_payload_hard_flags(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_nested_payload_hard_flags(item, f"{path}[{index}]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _require_nested_payload_hard_flags(item, f"{path}[{index}]")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _row_sort_key(row: MarketFeeSpreadStressRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.mechanics_status],
        -row.stress_score,
        row.candidate_digest,
    )


def _candidate_digest(raw_candidate_id: str) -> str:
    return hashlib.sha256(raw_candidate_id.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(report: MarketFeeSpreadStressReport) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(report: MarketFeeSpreadStressReport) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived_validation_digest payload", digest_payload)
    encoded_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    normalized = lowered.replace("-", "_").replace(" ", "_")
    compact = _compact_public_text(lowered)
    for term in _UNSAFE_PUBLIC_TERMS:
        normalized_term = term.lower().replace("-", "_").replace(" ", "_")
        compact_term = _compact_public_text(normalized_term)
        if term in lowered or normalized_term in normalized:
            return True
        if compact_term and compact_term in compact:
            return True
    return False


def _compact_public_text(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _reject_unsafe_public_payload(value_label: str, value: object, path: str = "") -> None:
    current_path = path or value_label
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(value_label, asdict(value), current_path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{value_label} has unsafe public payload")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"{value_label} has unsafe public payload at {current_path}")
            _reject_unsafe_public_payload(value_label, item, f"{current_path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(value_label, item, f"{current_path}[{index}]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(value_label, item, f"{current_path}[{index}]")
        return
    if type(value) is str and _contains_unsafe_public_term(value):
        raise ValueError(f"{value_label} has unsafe public payload at {current_path}")


def _reject_public_numeric_payload(value_label: str, value: object, path: str = "") -> None:
    current_path = path or value_label
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (Decimal, float, int)):
        raise ValueError(f"{value_label} has non-string numeric value at {current_path}")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{value_label} has non-string numeric key at {current_path}")
            _reject_public_numeric_payload(value_label, item, f"{current_path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_public_numeric_payload(value_label, item, f"{current_path}[{index}]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_public_numeric_payload(value_label, item, f"{current_path}[{index}]")


def _json_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value
