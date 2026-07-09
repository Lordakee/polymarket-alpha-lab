"""Report-only tail guard for caller-supplied probability spread snapshots."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION = (
    "research-market-probability-spread-tail-guard-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUS_SEQUENCE = ("pass", "watch", "block")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "database",
    "dsn",
    "live",
    "market_id",
    "market_slug",
    "network",
    "order",
    "private",
    "question",
    "secret",
    "source_text",
    "source_url",
    "table_name",
    "token",
    "trade",
    "wallet",
)
_REASON_CODE_SEQUENCE = (
    "candidate_probability_input",
    "spread_tail_guard_no_candidates",
    "spread_tail_guard_pass",
    "spread_tail_guard_block",
    "spread_tail_guard_source_stale_block",
    "spread_tail_guard_spread_block",
    "spread_tail_guard_spread_watch",
    "spread_tail_guard_tail_block",
    "spread_tail_guard_tail_watch",
    "spread_tail_guard_watch",
    "spread_tail_guard_source_stale_watch",
)


@dataclass(frozen=True)
class ResearchMarketProbabilitySpreadTailGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION
    )
    watch_spread_threshold: Decimal = Decimal("0.080000")
    block_spread_threshold: Decimal = Decimal("0.150000")
    watch_tail_probability_threshold: Decimal = Decimal("0.100000")
    block_tail_probability_threshold: Decimal = Decimal("0.300000")
    watch_source_age_seconds: Decimal = Decimal("1800.000000")
    block_source_age_seconds: Decimal = Decimal("3600.000000")
    spread_weight: Decimal = Decimal("0.450000")
    tail_weight: Decimal = Decimal("0.350000")
    source_age_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySpreadTailGuardConfig:
            raise TypeError(
                "ResearchMarketProbabilitySpreadTailGuardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilitySpreadTailGuardConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_spread_threshold",
            "block_spread_threshold",
            "watch_tail_probability_threshold",
            "block_tail_probability_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_source_age_seconds", "block_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("spread_weight", "tail_weight", "source_age_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySpreadTailGuardCandidate:
    candidate_id: str
    probability_midpoint: Decimal
    probability_spread: Decimal
    left_tail_probability: Decimal
    right_tail_probability: Decimal
    source_observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySpreadTailGuardCandidate:
            raise TypeError(
                "ResearchMarketProbabilitySpreadTailGuardCandidate does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilitySpreadTailGuardCandidate,
            "candidate",
        )
        _require_candidate_identifier("candidate_id", self.candidate_id)
        for field_name in (
            "probability_midpoint",
            "probability_spread",
            "left_tail_probability",
            "right_tail_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySpreadTailGuardRow:
    public_candidate_ref: str
    probability_midpoint: Decimal
    probability_spread: Decimal
    left_tail_probability: Decimal
    right_tail_probability: Decimal
    tail_probability: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    tail_guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySpreadTailGuardRow:
            raise TypeError(
                "ResearchMarketProbabilitySpreadTailGuardRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilitySpreadTailGuardRow, "row")
        _require_public_identifier("public_candidate_ref", self.public_candidate_ref)
        for field_name in (
            "probability_midpoint",
            "probability_spread",
            "left_tail_probability",
            "right_tail_probability",
            "tail_probability",
            "tail_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySpreadTailGuardReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_probability_spread: Decimal
    max_tail_probability: Decimal
    max_source_age_seconds: Decimal
    max_tail_guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketProbabilitySpreadTailGuardRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySpreadTailGuardReport:
            raise TypeError(
                "ResearchMarketProbabilitySpreadTailGuardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilitySpreadTailGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_probability_spread",
            "max_tail_probability",
            "max_tail_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchMarketProbabilitySpreadTailGuardReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_market_probability_spread_tail_guard_report(
    candidates: Iterable[object],
    *,
    config: ResearchMarketProbabilitySpreadTailGuardConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilitySpreadTailGuardReport:
    if type(config) is not ResearchMarketProbabilitySpreadTailGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilitySpreadTailGuardConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_candidates(candidates)
    for item in normalized:
        if item.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_candidate(item, config=config, generated_at=generated_at)
                for item in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "candidate_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "max_probability_spread": _max_row_decimal(rows, "probability_spread"),
        "max_tail_probability": _max_row_decimal(rows, "tail_probability"),
        "max_source_age_seconds": _max_row_decimal(rows, "source_age_seconds"),
        "max_tail_guard_score": _max_row_decimal(rows, "tail_guard_score"),
        "status": _report_status(rows),
        "reason_codes": reason_codes,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketProbabilitySpreadTailGuardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_probability_spread_tail_guard_payload(
    report: ResearchMarketProbabilitySpreadTailGuardReport,
) -> dict[str, object]:
    if type(report) is not ResearchMarketProbabilitySpreadTailGuardReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilitySpreadTailGuardReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def _row_from_candidate(
    candidate: ResearchMarketProbabilitySpreadTailGuardCandidate,
    *,
    config: ResearchMarketProbabilitySpreadTailGuardConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilitySpreadTailGuardRow:
    source_age_seconds = _seconds_between(generated_at, candidate.source_observed_at)
    tail_probability = max(
        candidate.left_tail_probability,
        candidate.right_tail_probability,
    )
    status = _candidate_status(
        probability_spread=candidate.probability_spread,
        tail_probability=tail_probability,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    reason_codes = _candidate_reason_codes(
        status=status,
        probability_spread=candidate.probability_spread,
        tail_probability=tail_probability,
        source_age_seconds=source_age_seconds,
        config=config,
        input_reason_codes=candidate.reason_codes,
    )
    return ResearchMarketProbabilitySpreadTailGuardRow(
        public_candidate_ref=_public_candidate_ref(candidate.candidate_id),
        probability_midpoint=candidate.probability_midpoint,
        probability_spread=candidate.probability_spread,
        left_tail_probability=candidate.left_tail_probability,
        right_tail_probability=candidate.right_tail_probability,
        tail_probability=tail_probability,
        source_observed_at=candidate.source_observed_at,
        source_age_seconds=source_age_seconds,
        tail_guard_score=_tail_guard_score(
            probability_spread=candidate.probability_spread,
            tail_probability=tail_probability,
            source_age_seconds=source_age_seconds,
            config=config,
        ),
        status=status,
        reason_codes=reason_codes,
    )


def _tail_guard_score(
    *,
    probability_spread: Decimal,
    tail_probability: Decimal,
    source_age_seconds: Decimal,
    config: ResearchMarketProbabilitySpreadTailGuardConfig,
) -> Decimal:
    raw_score = (
        probability_spread * config.spread_weight
        + tail_probability * config.tail_weight
        + (source_age_seconds / config.block_source_age_seconds) * config.source_age_weight
    )
    return _clamp_probability(raw_score)


def _candidate_status(
    *,
    probability_spread: Decimal,
    tail_probability: Decimal,
    source_age_seconds: Decimal,
    config: ResearchMarketProbabilitySpreadTailGuardConfig,
) -> str:
    if (
        probability_spread >= config.block_spread_threshold
        or tail_probability >= config.block_tail_probability_threshold
        or source_age_seconds >= config.block_source_age_seconds
    ):
        return "block"
    if (
        probability_spread >= config.watch_spread_threshold
        or tail_probability >= config.watch_tail_probability_threshold
        or source_age_seconds >= config.watch_source_age_seconds
    ):
        return "watch"
    return "pass"


def _candidate_reason_codes(
    *,
    status: str,
    probability_spread: Decimal,
    tail_probability: Decimal,
    source_age_seconds: Decimal,
    config: ResearchMarketProbabilitySpreadTailGuardConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = list(input_reason_codes)
    if status == "pass":
        reason_codes.append("spread_tail_guard_pass")
    elif status == "watch":
        reason_codes.append("spread_tail_guard_watch")
    else:
        reason_codes.append("spread_tail_guard_block")

    if source_age_seconds >= config.block_source_age_seconds:
        reason_codes.append("spread_tail_guard_source_stale_block")
    elif source_age_seconds >= config.watch_source_age_seconds:
        reason_codes.append("spread_tail_guard_source_stale_watch")

    if probability_spread >= config.block_spread_threshold:
        reason_codes.append("spread_tail_guard_spread_block")
    elif probability_spread >= config.watch_spread_threshold:
        reason_codes.append("spread_tail_guard_spread_watch")

    if tail_probability >= config.block_tail_probability_threshold:
        reason_codes.append("spread_tail_guard_tail_block")
    elif tail_probability >= config.watch_tail_probability_threshold:
        reason_codes.append("spread_tail_guard_tail_watch")

    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _report_status(
    rows: tuple[ResearchMarketProbabilitySpreadTailGuardRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilitySpreadTailGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("spread_tail_guard_no_candidates",)
    report_status = _report_status(rows)
    values: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code.startswith("candidate_"):
                continue
            if report_status != "pass" and reason_code == "spread_tail_guard_pass":
                continue
            values.append(reason_code)
    return _normalize_reason_codes(tuple(values), allow_empty=False)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[ResearchMarketProbabilitySpreadTailGuardCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    normalized: list[ResearchMarketProbabilitySpreadTailGuardCandidate] = []
    seen_ids: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketProbabilitySpreadTailGuardCandidate:
            raise ValueError(
                "candidates must contain "
                "ResearchMarketProbabilitySpreadTailGuardCandidate values",
            )
        _require_hard_flags("candidate", value)
        if value.candidate_id in seen_ids:
            raise ValueError("duplicate candidate detected")
        seen_ids.add(value.candidate_id)
        normalized.append(value)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.source_observed_at,
                _public_candidate_ref(item.candidate_id),
            ),
        ),
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketProbabilitySpreadTailGuardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilitySpreadTailGuardRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilitySpreadTailGuardRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status, score, and public ref")
    return rows


def _row_sort_key(
    row: ResearchMarketProbabilitySpreadTailGuardRow,
) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.status], -row.tail_guard_score, row.public_candidate_ref)


def _validate_config(config: ResearchMarketProbabilitySpreadTailGuardConfig) -> None:
    if config.block_spread_threshold <= config.watch_spread_threshold:
        raise ValueError("block_spread_threshold must exceed watch_spread_threshold")
    if config.block_tail_probability_threshold <= config.watch_tail_probability_threshold:
        raise ValueError(
            "block_tail_probability_threshold must exceed "
            "watch_tail_probability_threshold",
        )
    if config.block_source_age_seconds <= config.watch_source_age_seconds:
        raise ValueError("block_source_age_seconds must exceed watch_source_age_seconds")
    weight_sum = _quantize(
        config.spread_weight + config.tail_weight + config.source_age_weight,
    )
    if weight_sum != _ONE:
        raise ValueError("weight fields must sum to 1")


def _validate_row(row: ResearchMarketProbabilitySpreadTailGuardRow) -> None:
    if row.tail_probability != max(row.left_tail_probability, row.right_tail_probability):
        raise ValueError("tail_probability must match max tail input")
    if row.status == "pass" and "spread_tail_guard_pass" not in row.reason_codes:
        raise ValueError("pass rows must include spread_tail_guard_pass")
    if row.status == "watch" and "spread_tail_guard_watch" not in row.reason_codes:
        raise ValueError("watch rows must include spread_tail_guard_watch")
    if row.status == "block" and "spread_tail_guard_block" not in row.reason_codes:
        raise ValueError("block rows must include spread_tail_guard_block")


def _validate_report(report: ResearchMarketProbabilitySpreadTailGuardReport) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_probability_spread != _max_row_decimal(report.rows, "probability_spread"):
        raise ValueError("max_probability_spread must match rows")
    if report.max_tail_probability != _max_row_decimal(report.rows, "tail_probability"):
        raise ValueError("max_tail_probability must match rows")
    if report.max_source_age_seconds != _max_row_decimal(report.rows, "source_age_seconds"):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_tail_guard_score != _max_row_decimal(report.rows, "tail_guard_score"):
        raise ValueError("max_tail_guard_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchMarketProbabilitySpreadTailGuardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_row_decimal(
    rows: tuple[ResearchMarketProbabilitySpreadTailGuardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("source_observed_at must not be after generated_at")
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000"),
    )


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_candidate_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_SEQUENCE:
        raise ValueError(f"{field_name} must be one of {_STATUS_SEQUENCE}")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_reason_codes(
    reason_codes: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    ordered = tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )
    if not allow_empty and not ordered:
        raise ValueError("reason_codes must be nonempty")
    return ordered


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _public_candidate_ref(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"candidate_ref_{digest}"


def _report_values_without_digest(
    report: ResearchMarketProbabilitySpreadTailGuardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for payload_key, item in value.items():
            if type(payload_key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[payload_key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for payload_key, item in value.items():
            if type(payload_key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(payload_key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                payload_key if not path else f"{path}.{payload_key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(value: str, path: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{value} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if "://" in normalized or "@" in normalized:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in normalized for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION",
    "ResearchMarketProbabilitySpreadTailGuardCandidate",
    "ResearchMarketProbabilitySpreadTailGuardConfig",
    "ResearchMarketProbabilitySpreadTailGuardReport",
    "ResearchMarketProbabilitySpreadTailGuardRow",
    "build_research_market_probability_spread_tail_guard_report",
    "research_market_probability_spread_tail_guard_payload",
)
