"""Pure report-only market-universe discovery scoring for research candidates.

The module is deterministic and side-effect free. Callers provide typed market
candidate summaries; the policy returns report-only scores, statuses, and public
payloads that exclude raw market/source material and connection details.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "MarketUniverseDiscoveryCandidate",
    "MarketUniverseDiscoveryConfig",
    "MarketUniverseDiscoveryReasonCodeCount",
    "MarketUniverseDiscoveryReport",
    "MarketUniverseDiscoveryRow",
    "build_research_market_universe_discovery_report",
    "research_market_universe_discovery_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-universe-discovery-report-v0"
DOMAINS = ("crypto", "economics", "politics", "sports", "technology", "weather")
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
PUBLIC_BLOCKED_FIELD_NAMES = frozenset(
    (
        "raw_market",
        "raw_candidate",
        "raw_source",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table",
        "token",
        "secret",
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "sqlite://",
        "wal" "let",
        "au" "th",
        "private" "_" "key",
        "or" "der",
        "trade",
        "buy",
        "sell",
        "ad" "vice",
    ),
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class MarketUniverseDiscoveryConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_domain_coverage_score: Decimal = Decimal("0.650000")
    min_liquidity_score: Decimal = Decimal("0.600000")
    min_settlement_clarity_score: Decimal = Decimal("0.700000")
    min_source_availability_score: Decimal = Decimal("0.650000")
    min_source_family_count: Decimal = Decimal("2")
    pass_candidate_score: Decimal = Decimal("0.750000")
    watch_candidate_score: Decimal = Decimal("0.450000")
    domain_coverage_weight: Decimal = Decimal("0.250000")
    liquidity_weight: Decimal = Decimal("0.300000")
    settlement_clarity_weight: Decimal = Decimal("0.250000")
    source_availability_weight: Decimal = Decimal("0.200000")
    manual_review_penalty: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_domain_coverage_score",
            "min_liquidity_score",
            "min_settlement_clarity_score",
            "min_source_availability_score",
            "pass_candidate_score",
            "watch_candidate_score",
            "domain_coverage_weight",
            "liquidity_weight",
            "settlement_clarity_weight",
            "source_availability_weight",
            "manual_review_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_positive_whole_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        if self.pass_candidate_score <= self.watch_candidate_score:
            raise ValueError("pass_candidate_score must be greater than watch_candidate_score")
        weight_sum = _quantize(
            self.domain_coverage_weight
            + self.liquidity_weight
            + self.settlement_clarity_weight
            + self.source_availability_weight,
        )
        if weight_sum != ONE:
            raise ValueError("candidate score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketUniverseDiscoveryCandidate:
    candidate_id: str
    domain: str
    liquidity_score: Decimal
    settlement_clarity_score: Decimal
    source_availability_score: Decimal
    domain_coverage_score: Decimal
    source_family_count: Decimal
    settlement_requires_manual_review: bool = False
    reason_codes: tuple[str, ...] = ()
    raw_market: str | None = None
    raw_candidate: str | None = None
    raw_source: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    dsn: str | None = None
    table: str | None = None
    token: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_enum("domain", self.domain, DOMAINS)
        for field_name in (
            "liquidity_score",
            "settlement_clarity_score",
            "source_availability_score",
            "domain_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_whole_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        if type(self.settlement_requires_manual_review) is not bool:
            raise ValueError("settlement_requires_manual_review must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        for field_name in PUBLIC_BLOCKED_FIELD_NAMES:
            _require_optional_string(field_name, getattr(self, field_name))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class MarketUniverseDiscoveryRow:
    candidate_id: str
    domain: str
    liquidity_score: Decimal
    settlement_clarity_score: Decimal
    source_availability_score: Decimal
    domain_coverage_score: Decimal
    source_family_count: Decimal
    candidate_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    settlement_requires_manual_review: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_enum("domain", self.domain, DOMAINS)
        for field_name in (
            "liquidity_score",
            "settlement_clarity_score",
            "source_availability_score",
            "domain_coverage_score",
            "candidate_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_whole_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.settlement_requires_manual_review) is not bool:
            raise ValueError("settlement_requires_manual_review must be a bool")
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketUniverseDiscoveryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketUniverseDiscoveryReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_candidate_score: Decimal | None
    status: str
    rows: tuple[MarketUniverseDiscoveryRow, ...]
    reason_code_counts: tuple[MarketUniverseDiscoveryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_candidate_score",
            _require_optional_probability_decimal(
                "average_candidate_score",
                self.average_candidate_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_universe_discovery_report(
    candidates: Iterable[object],
    *,
    config: MarketUniverseDiscoveryConfig,
    generated_at: datetime,
) -> MarketUniverseDiscoveryReport:
    if type(config) is not MarketUniverseDiscoveryConfig:
        raise ValueError("config must be a MarketUniverseDiscoveryConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_items = _normalize_candidates(candidates)
    rows = tuple(
        _row_from_candidate(candidate=item, config=config)
        for item in sorted(candidate_items, key=lambda value: value.candidate_id)
    )
    reason_codes = _summary_reason_codes(rows)
    return MarketUniverseDiscoveryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_candidate_score=_average_candidate_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_universe_discovery_report_payload(
    report: MarketUniverseDiscoveryReport,
) -> dict[str, Any]:
    if type(report) is not MarketUniverseDiscoveryReport:
        raise ValueError("report must be a MarketUniverseDiscoveryReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload("report", payload, allow_json_containers=True)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_candidate(
    *,
    candidate: MarketUniverseDiscoveryCandidate,
    config: MarketUniverseDiscoveryConfig,
) -> MarketUniverseDiscoveryRow:
    candidate_score = _candidate_score(candidate, config)
    reason_codes = _row_reason_codes(candidate, candidate_score, config)
    status = _row_status(candidate_score, reason_codes, config)
    reason_codes = tuple(
        sorted(
            {
                *reason_codes,
                f"market_universe_candidate_{status}",
            },
        ),
    )
    return MarketUniverseDiscoveryRow(
        candidate_id=candidate.candidate_id,
        domain=candidate.domain,
        liquidity_score=candidate.liquidity_score,
        settlement_clarity_score=candidate.settlement_clarity_score,
        source_availability_score=candidate.source_availability_score,
        domain_coverage_score=candidate.domain_coverage_score,
        source_family_count=candidate.source_family_count,
        candidate_score=candidate_score,
        status=status,
        reason_codes=reason_codes,
        settlement_requires_manual_review=candidate.settlement_requires_manual_review,
    )


def _candidate_score(
    candidate: MarketUniverseDiscoveryCandidate,
    config: MarketUniverseDiscoveryConfig,
) -> Decimal:
    score = (
        candidate.domain_coverage_score * config.domain_coverage_weight
        + candidate.liquidity_score * config.liquidity_weight
        + candidate.settlement_clarity_score * config.settlement_clarity_weight
        + candidate.source_availability_score * config.source_availability_weight
    )
    if candidate.settlement_requires_manual_review:
        score -= config.manual_review_penalty
    return _quantize(max(ZERO, min(ONE, score)))


def _row_status(
    candidate_score: Decimal,
    reason_codes: tuple[str, ...],
    config: MarketUniverseDiscoveryConfig,
) -> str:
    if candidate_score < config.watch_candidate_score:
        return "blocked"
    if any(code.startswith("insufficient_") for code in reason_codes):
        return "watch"
    if "not_enough_source_families" in reason_codes:
        return "watch"
    if "settlement_manual_review_required" in reason_codes:
        return "watch"
    if candidate_score < config.pass_candidate_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    candidate: MarketUniverseDiscoveryCandidate,
    candidate_score: Decimal,
    config: MarketUniverseDiscoveryConfig,
) -> tuple[str, ...]:
    del candidate_score
    reason_codes: set[str] = set()
    reason_codes.add(
        "domain_coverage_supported"
        if candidate.domain_coverage_score >= config.min_domain_coverage_score
        else "insufficient_domain_coverage",
    )
    reason_codes.add(
        "liquidity_supported"
        if candidate.liquidity_score >= config.min_liquidity_score
        else "insufficient_liquidity",
    )
    reason_codes.add(
        "settlement_clarity_supported"
        if candidate.settlement_clarity_score >= config.min_settlement_clarity_score
        else "insufficient_settlement_clarity",
    )
    reason_codes.add(
        "source_availability_supported"
        if candidate.source_availability_score >= config.min_source_availability_score
        else "insufficient_source_availability",
    )
    if candidate.source_family_count < config.min_source_family_count:
        reason_codes.add("not_enough_source_families")
    if candidate.settlement_requires_manual_review:
        reason_codes.add("settlement_manual_review_required")
    for reason_code in candidate.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[MarketUniverseDiscoveryCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    return tuple(_coerce_candidate(value) for value in values)


def _coerce_candidate(value: object) -> MarketUniverseDiscoveryCandidate:
    if type(value) is MarketUniverseDiscoveryCandidate:
        _require_hard_flags("candidate", value)
        return value
    _require_hard_flags("candidate", value)
    return MarketUniverseDiscoveryCandidate(
        candidate_id=_field_value(value, "candidate_id"),
        domain=_field_value(value, "domain"),
        liquidity_score=_field_value(value, "liquidity_score"),
        settlement_clarity_score=_field_value(value, "settlement_clarity_score"),
        source_availability_score=_field_value(value, "source_availability_score"),
        domain_coverage_score=_field_value(value, "domain_coverage_score"),
        source_family_count=_field_value(value, "source_family_count"),
        settlement_requires_manual_review=_field_value(
            value,
            "settlement_requires_manual_review",
            default=False,
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        raw_market=_field_value(value, "raw_market", default=None),
        raw_candidate=_field_value(value, "raw_candidate", default=None),
        raw_source=_field_value(value, "raw_source", default=None),
        source_url=_field_value(value, "source_url", default=None),
        source_text=_field_value(value, "source_text", default=None),
        dsn=_field_value(value, "dsn", default=None),
        table=_field_value(value, "table", default=None),
        token=_field_value(value, "token", default=None),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[MarketUniverseDiscoveryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_market_universe_candidates",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("market_universe_discovery_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_market_universe_candidates",):
        return "blocked"
    if "market_universe_candidate_blocked" in reason_codes:
        return "blocked"
    if "market_universe_candidate_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[MarketUniverseDiscoveryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketUniverseDiscoveryReasonCodeCount, ...]:
    if not rows:
        return (
            MarketUniverseDiscoveryReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketUniverseDiscoveryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_candidate_score(rows: tuple[MarketUniverseDiscoveryRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.candidate_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(rows: tuple[MarketUniverseDiscoveryRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[MarketUniverseDiscoveryRow, ...],
) -> tuple[MarketUniverseDiscoveryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketUniverseDiscoveryRow:
            raise ValueError("rows must contain MarketUniverseDiscoveryRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.candidate_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by candidate_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[MarketUniverseDiscoveryReasonCodeCount, ...],
) -> tuple[MarketUniverseDiscoveryReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not MarketUniverseDiscoveryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketUniverseDiscoveryReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: MarketUniverseDiscoveryRow) -> None:
    if row.status == "pass" and row.candidate_score < Decimal("0.750000"):
        raise ValueError("candidate_score must support pass status")
    if row.status == "watch" and (
        row.candidate_score < Decimal("0.450000")
        or row.candidate_score >= Decimal("0.750000")
        and not any(
            code.startswith("insufficient_")
            or code in (
                "not_enough_source_families",
                "settlement_manual_review_required",
            )
            for code in row.reason_codes
        )
    ):
        raise ValueError("candidate_score must support watch status")
    if row.status == "blocked" and row.candidate_score >= Decimal("0.450000"):
        raise ValueError("candidate_score must support blocked status")


def _validate_report_consistency(report: MarketUniverseDiscoveryReport) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_candidate_score != _average_candidate_score(report.rows):
        raise ValueError("average_candidate_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, object] = {}
        for field in fields(value):
            if field.name in PUBLIC_BLOCKED_FIELD_NAMES:
                continue
            payload[field.name] = _payload_value(getattr(value, field.name))
        return payload
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_optional_string(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{key} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value or _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
