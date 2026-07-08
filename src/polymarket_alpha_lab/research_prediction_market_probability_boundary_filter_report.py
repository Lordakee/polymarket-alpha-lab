"""Pure report-only probability boundary filter for research escalation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any


CONFIG_VERSION = "research_prediction_market_probability_boundary_filter_report"
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

PUBLIC_STATUSES = ("pass", "watch", "block")
PASS = "pass"
WATCH = "watch"
BLOCK = "block"

UNSAFE_PUBLIC_FRAGMENTS = (
    "_id",
    "id_",
    "slug",
    "question",
    "source",
    "storage",
    "auth",
    "trad" + "ing",
)


@dataclass(frozen=True)
class ResearchPredictionMarketProbabilityBoundaryFilterConfig:
    config_version: str = CONFIG_VERSION
    boundary_watch_distance: Decimal = Decimal("0.100000")
    boundary_block_distance: Decimal = Decimal("0.030000")
    thin_watch_depth_usd: Decimal = Decimal("1000.000000")
    thin_block_depth_usd: Decimal = Decimal("250.000000")
    stale_watch_hours: Decimal = Decimal("12.000000")
    stale_block_hours: Decimal = Decimal("72.000000")
    ambiguity_watch_score: Decimal = Decimal("0.600000")
    ambiguity_block_score: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPredictionMarketProbabilityBoundaryFilterConfig:
            raise TypeError(
                "ResearchPredictionMarketProbabilityBoundaryFilterConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPredictionMarketProbabilityBoundaryFilterConfig:
            raise ValueError(
                "config must be exactly ResearchPredictionMarketProbabilityBoundaryFilterConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "boundary_watch_distance",
            "boundary_block_distance",
            "ambiguity_watch_score",
            "ambiguity_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "thin_watch_depth_usd",
            "thin_block_depth_usd",
            "stale_watch_hours",
            "stale_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.boundary_block_distance > self.boundary_watch_distance:
            raise ValueError(
                "boundary_block_distance must be at most boundary_watch_distance",
            )
        if self.thin_block_depth_usd > self.thin_watch_depth_usd:
            raise ValueError("thin_block_depth_usd must be at most thin_watch_depth_usd")
        if self.stale_block_hours < self.stale_watch_hours:
            raise ValueError("stale_block_hours must be at least stale_watch_hours")
        if self.ambiguity_block_score < self.ambiguity_watch_score:
            raise ValueError(
                "ambiguity_block_score must be at least ambiguity_watch_score",
            )
        _require_hard_flags("probability boundary filter config", self)


@dataclass(frozen=True)
class ResearchPredictionMarketProbabilityBoundaryFilterCandidate:
    cohort: str
    public_probability: Decimal
    public_depth_usd: Decimal
    last_update_age_hours: Decimal
    ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPredictionMarketProbabilityBoundaryFilterCandidate:
            raise TypeError(
                "ResearchPredictionMarketProbabilityBoundaryFilterCandidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPredictionMarketProbabilityBoundaryFilterCandidate:
            raise ValueError(
                "candidate must be exactly ResearchPredictionMarketProbabilityBoundaryFilterCandidate",
            )
        _require_public_string("cohort", self.cohort)
        object.__setattr__(
            self,
            "public_probability",
            _normalize_probability("public_probability", self.public_probability),
        )
        for field_name in ("public_depth_usd", "last_update_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_probability("ambiguity_score", self.ambiguity_score),
        )
        _require_hard_flags("probability boundary filter candidate", self)


@dataclass(frozen=True)
class ResearchPredictionMarketProbabilityBoundaryFilterRow:
    cohort: str
    public_probability: Decimal
    public_depth_usd: Decimal
    last_update_age_hours: Decimal
    ambiguity_score: Decimal
    boundary_distance: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPredictionMarketProbabilityBoundaryFilterRow:
            raise TypeError(
                "ResearchPredictionMarketProbabilityBoundaryFilterRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPredictionMarketProbabilityBoundaryFilterRow:
            raise ValueError("row must be exactly ResearchPredictionMarketProbabilityBoundaryFilterRow")
        _require_public_string("cohort", self.cohort)
        object.__setattr__(
            self,
            "public_probability",
            _normalize_probability("public_probability", self.public_probability),
        )
        for field_name in ("public_depth_usd", "last_update_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("ambiguity_score", "boundary_distance"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=self.public_status == PASS),
        )
        _validate_row_consistency(self)
        _require_hard_flags("probability boundary filter row", self)


@dataclass(frozen=True)
class ResearchPredictionMarketProbabilityBoundaryFilterReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lowest_boundary_distance: Decimal
    weakest_depth_usd: Decimal
    highest_staleness_hours: Decimal
    highest_ambiguity_score: Decimal
    rows: tuple[ResearchPredictionMarketProbabilityBoundaryFilterRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPredictionMarketProbabilityBoundaryFilterReport:
            raise TypeError(
                "ResearchPredictionMarketProbabilityBoundaryFilterReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPredictionMarketProbabilityBoundaryFilterReport:
            raise ValueError(
                "report must be exactly ResearchPredictionMarketProbabilityBoundaryFilterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_boundary_distance",
            "weakest_depth_usd",
            "highest_staleness_hours",
            "highest_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_payload_digest == "":
            object.__setattr__(self, "derived_payload_digest", _report_payload_digest(self))
        _require_sha256_digest("derived_payload_digest", self.derived_payload_digest)
        _validate_report_consistency(self)
        _require_hard_flags("probability boundary filter report", self)
        _require_report_payload_digest(self)
        _reject_unsafe_public_payload(_payload_value(asdict(self)))


def build_research_prediction_market_probability_boundary_filter_report(
    candidates: tuple[ResearchPredictionMarketProbabilityBoundaryFilterCandidate, ...],
    *,
    generated_at: datetime,
    config: ResearchPredictionMarketProbabilityBoundaryFilterConfig,
) -> ResearchPredictionMarketProbabilityBoundaryFilterReport:
    if type(candidates) is not tuple:
        raise ValueError("candidates must be a tuple")
    if type(config) is not ResearchPredictionMarketProbabilityBoundaryFilterConfig:
        raise ValueError(
            "config must be a ResearchPredictionMarketProbabilityBoundaryFilterConfig",
        )
    rows = tuple(
        sorted(
            (_build_row(candidate=candidate, config=config) for candidate in candidates),
            key=lambda row: row.cohort,
        ),
    )
    return ResearchPredictionMarketProbabilityBoundaryFilterReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        candidate_count=Decimal(len(rows)),
        pass_count=_count_status(rows, PASS),
        watch_count=_count_status(rows, WATCH),
        block_count=_count_status(rows, BLOCK),
        lowest_boundary_distance=_minimum(row.boundary_distance for row in rows),
        weakest_depth_usd=_minimum(row.public_depth_usd for row in rows),
        highest_staleness_hours=_maximum(row.last_update_age_hours for row in rows),
        highest_ambiguity_score=_maximum(row.ambiguity_score for row in rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_prediction_market_probability_boundary_filter_payload(
    report: ResearchPredictionMarketProbabilityBoundaryFilterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPredictionMarketProbabilityBoundaryFilterReport:
        _validate_report_consistency(report)
        _require_report_payload_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchPredictionMarketProbabilityBoundaryFilterReport or object",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    *,
    candidate: ResearchPredictionMarketProbabilityBoundaryFilterCandidate,
    config: ResearchPredictionMarketProbabilityBoundaryFilterConfig,
) -> ResearchPredictionMarketProbabilityBoundaryFilterRow:
    if type(candidate) is not ResearchPredictionMarketProbabilityBoundaryFilterCandidate:
        raise ValueError(
            "candidates must contain ResearchPredictionMarketProbabilityBoundaryFilterCandidate values",
        )
    boundary_distance = _boundary_distance(candidate.public_probability)
    reason_codes = _row_reason_codes(
        boundary_distance=boundary_distance,
        public_depth_usd=candidate.public_depth_usd,
        last_update_age_hours=candidate.last_update_age_hours,
        ambiguity_score=candidate.ambiguity_score,
        config=config,
    )
    public_status = _public_status(reason_codes)
    return ResearchPredictionMarketProbabilityBoundaryFilterRow(
        cohort=candidate.cohort,
        public_probability=candidate.public_probability,
        public_depth_usd=candidate.public_depth_usd,
        last_update_age_hours=candidate.last_update_age_hours,
        ambiguity_score=candidate.ambiguity_score,
        boundary_distance=boundary_distance,
        public_status=public_status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    boundary_distance: Decimal,
    public_depth_usd: Decimal,
    last_update_age_hours: Decimal,
    ambiguity_score: Decimal,
    config: ResearchPredictionMarketProbabilityBoundaryFilterConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if boundary_distance <= config.boundary_block_distance:
        codes.append("near_probability_boundary_block")
    elif boundary_distance <= config.boundary_watch_distance:
        codes.append("near_probability_boundary_watch")
    if public_depth_usd <= config.thin_block_depth_usd:
        codes.append("thin_event_block")
    elif public_depth_usd <= config.thin_watch_depth_usd:
        codes.append("thin_event_watch")
    if last_update_age_hours >= config.stale_block_hours:
        codes.append("stale_event_block")
    elif last_update_age_hours >= config.stale_watch_hours:
        codes.append("stale_event_watch")
    if ambiguity_score >= config.ambiguity_block_score:
        codes.append("ambiguous_event_block")
    elif ambiguity_score >= config.ambiguity_watch_score:
        codes.append("ambiguous_event_watch")
    return _normalize_reason_codes(tuple(codes), allow_empty=True)


def _public_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return BLOCK
    if reason_codes:
        return WATCH
    return PASS


def _boundary_distance(public_probability: Decimal) -> Decimal:
    return _quantize(min(public_probability, ONE - public_probability))


def _reason_code_counts(
    rows: tuple[ResearchPredictionMarketProbabilityBoundaryFilterRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, Decimal(counter[code])) for code in sorted(counter))


def _count_status(
    rows: tuple[ResearchPredictionMarketProbabilityBoundaryFilterRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.public_status == status))


def _minimum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(min(items))


def _maximum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(max(items))


def _normalize_rows(
    value: object,
) -> tuple[ResearchPredictionMarketProbabilityBoundaryFilterRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchPredictionMarketProbabilityBoundaryFilterRow for row in rows):
        raise ValueError(
            "rows must contain ResearchPredictionMarketProbabilityBoundaryFilterRow values",
        )
    if rows != tuple(sorted(rows, key=lambda row: row.cohort)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts values must be pairs")
        code, count = item
        _require_public_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_reason_codes(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_public_string("reason_codes", code)
    return tuple(sorted(codes))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be one line")
    _reject_unsafe_public_text(value)


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_row_consistency(
    row: ResearchPredictionMarketProbabilityBoundaryFilterRow,
) -> None:
    if row.boundary_distance != _boundary_distance(row.public_probability):
        raise ValueError("boundary_distance must match public_probability")
    if row.public_status != _public_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchPredictionMarketProbabilityBoundaryFilterReport,
) -> None:
    rows = report.rows
    if report.candidate_count != Decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count_status(rows, PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(rows, WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(rows, BLOCK):
        raise ValueError("block_count must match rows")
    if report.lowest_boundary_distance != _minimum(row.boundary_distance for row in rows):
        raise ValueError("lowest_boundary_distance must match rows")
    if report.weakest_depth_usd != _minimum(row.public_depth_usd for row in rows):
        raise ValueError("weakest_depth_usd must match rows")
    if report.highest_staleness_hours != _maximum(row.last_update_age_hours for row in rows):
        raise ValueError("highest_staleness_hours must match rows")
    if report.highest_ambiguity_score != _maximum(row.ambiguity_score for row in rows):
        raise ValueError("highest_ambiguity_score must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_report_payload_digest(
    report: ResearchPredictionMarketProbabilityBoundaryFilterReport,
) -> None:
    if report.derived_payload_digest != _report_payload_digest(report):
        raise ValueError("derived_payload_digest does not match report payload")


def _report_payload_digest(
    report: ResearchPredictionMarketProbabilityBoundaryFilterReport,
) -> str:
    payload = _payload_value(asdict(report))
    payload["derived_payload_digest"] = ""
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["derived_payload_digest"] = ""
    encoded = json.dumps(digest_payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(payload)
    _validate_payload_statuses(payload)
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")
    digest = payload.get("derived_payload_digest")
    _require_sha256_digest("derived_payload_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("derived_payload_digest does not match report payload")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "public_status":
                _require_public_status("public_status", item)
            else:
                _validate_payload_statuses(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_key(key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(value)
    elif isinstance(value, float):
        raise ValueError("unsafe public payload contains float")


def _reject_unsafe_public_key(key: str) -> None:
    if type(key) is not str:
        raise ValueError("unsafe public payload key")
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload key")


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public text")


__all__ = (
    "ResearchPredictionMarketProbabilityBoundaryFilterCandidate",
    "ResearchPredictionMarketProbabilityBoundaryFilterConfig",
    "ResearchPredictionMarketProbabilityBoundaryFilterReport",
    "ResearchPredictionMarketProbabilityBoundaryFilterRow",
    "build_research_prediction_market_probability_boundary_filter_report",
    "research_prediction_market_probability_boundary_filter_payload",
)
