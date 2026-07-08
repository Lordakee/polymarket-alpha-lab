"""Pure public-safe report-only blocker summary for manual research review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_CONFIG_VERSION = (
    "research-candidate-manual-review-blocker-report-v0"
)

STATUSES = ("pass", "watch", "block")
RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS = (
    "aggregate_evidence_gap",
    "source_freshness_gap",
    "rule_ambiguity",
    "cost_input_quality_gap",
    "team_capacity_gap",
    "settlement_risk",
)

ZERO = Decimal("0")
ONE = Decimal("1.000000")
RATIO_QUANT = Decimal("0.000001")

PASS_REPORT_REASON = "manual_review_blocker_report_pass"
WATCH_DIMENSIONS_REPORT_REASON = "manual_review_blocker_report_watch_dimensions"
BLOCK_DIMENSIONS_REPORT_REASON = "manual_review_blocker_report_block_dimensions"
WATCH_SCORE_REPORT_REASON = "manual_review_blocker_score_watch"
BLOCK_SCORE_REPORT_REASON = "manual_review_blocker_score_block"

DIMENSION_REASON_CODES = tuple(
    f"{dimension}_{status}"
    for dimension in RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS
    for status in STATUSES
)
REPORT_REASON_CODES = (
    PASS_REPORT_REASON,
    WATCH_DIMENSIONS_REPORT_REASON,
    BLOCK_DIMENSIONS_REPORT_REASON,
    WATCH_SCORE_REPORT_REASON,
    BLOCK_SCORE_REPORT_REASON,
)
REASON_CODES = DIMENSION_REASON_CODES + REPORT_REASON_CODES

DIMENSION_FIELDS = (
    (
        "aggregate_evidence_gap",
        "aggregate_evidence_gap_score",
        "aggregate_evidence_gap_weight",
    ),
    (
        "source_freshness_gap",
        "source_freshness_gap_score",
        "source_freshness_gap_weight",
    ),
    ("rule_ambiguity", "rule_ambiguity_score", "rule_ambiguity_weight"),
    (
        "cost_input_quality_gap",
        "cost_input_quality_gap_score",
        "cost_input_quality_gap_weight",
    ),
    ("team_capacity_gap", "team_capacity_gap_score", "team_capacity_gap_weight"),
    ("settlement_risk", "settlement_risk_score", "settlement_risk_weight"),
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate" "_id",
    "event" "_id",
    "market" "_id",
    "market" "_slug",
    "source" "_id",
    "wal" "let",
    "au" "th",
    "ord" "er",
    "tra" "de",
    "li" "ve",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "position" "_size",
    "position" " sizing",
)


@dataclass(frozen=True)
class ResearchCandidateManualReviewBlockerConfig:
    config_version: str = (
        DEFAULT_RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_CONFIG_VERSION
    )
    watch_blocker_score: Decimal = Decimal("0.300000")
    block_blocker_score: Decimal = Decimal("0.700000")
    dimension_watch_threshold: Decimal = Decimal("0.300000")
    dimension_block_threshold: Decimal = Decimal("0.700000")
    aggregate_evidence_gap_weight: Decimal = Decimal("0.250000")
    source_freshness_gap_weight: Decimal = Decimal("0.150000")
    rule_ambiguity_weight: Decimal = Decimal("0.200000")
    cost_input_quality_gap_weight: Decimal = Decimal("0.150000")
    team_capacity_gap_weight: Decimal = Decimal("0.100000")
    settlement_risk_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_blocker_score",
            "block_blocker_score",
            "dimension_watch_threshold",
            "dimension_block_threshold",
            "aggregate_evidence_gap_weight",
            "source_freshness_gap_weight",
            "rule_ambiguity_weight",
            "cost_input_quality_gap_weight",
            "team_capacity_gap_weight",
            "settlement_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_blocker_score >= self.block_blocker_score:
            raise ValueError(
                "watch_blocker_score must be less than block_blocker_score",
            )
        if self.dimension_watch_threshold >= self.dimension_block_threshold:
            raise ValueError(
                "dimension_watch_threshold must be less than dimension_block_threshold",
            )
        if _quantize(sum((getattr(self, field[2]) for field in DIMENSION_FIELDS), ZERO)) != ONE:
            raise ValueError("component weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateManualReviewBlockerAggregate:
    aggregate_evidence_gap_score: Decimal
    source_freshness_gap_score: Decimal
    rule_ambiguity_score: Decimal
    cost_input_quality_gap_score: Decimal
    team_capacity_gap_score: Decimal
    settlement_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for _, score_field, _ in DIMENSION_FIELDS:
            object.__setattr__(
                self,
                score_field,
                _normalize_ratio(score_field, getattr(self, score_field)),
            )
        _require_hard_flags("aggregate", self)


@dataclass(frozen=True)
class ResearchCandidateManualReviewBlockerDimensionRow:
    dimension: str
    blocker_score: Decimal
    component_weight: Decimal
    weighted_blocker_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_dimension("dimension", self.dimension)
        object.__setattr__(
            self,
            "blocker_score",
            _normalize_ratio("blocker_score", self.blocker_score),
        )
        object.__setattr__(
            self,
            "component_weight",
            _normalize_ratio("component_weight", self.component_weight),
        )
        object.__setattr__(
            self,
            "weighted_blocker_score",
            _normalize_ratio("weighted_blocker_score", self.weighted_blocker_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("dimension row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchCandidateManualReviewBlockerReasonCodeCount:
    reason_code: str
    count: Decimal
    dimension_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "dimension_ratio",
            _normalize_ratio("dimension_ratio", self.dimension_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCandidateManualReviewBlockerReport:
    generated_at: datetime
    config_version: str
    dimension_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    aggregate_blocker_score: Decimal
    max_dimension_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchCandidateManualReviewBlockerReasonCodeCount, ...]
    report_digest: str
    rows: tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("dimension_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_blocker_score",
            _normalize_ratio("aggregate_blocker_score", self.aggregate_blocker_score),
        )
        object.__setattr__(
            self,
            "max_dimension_score",
            _normalize_ratio("max_dimension_score", self.max_dimension_score),
        )
        _require_status("status", self.status)
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
        _require_digest("report_digest", self.report_digest)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_candidate_manual_review_blocker_report(
    aggregate: ResearchCandidateManualReviewBlockerAggregate,
    *,
    config: ResearchCandidateManualReviewBlockerConfig,
    generated_at: datetime,
) -> ResearchCandidateManualReviewBlockerReport:
    if type(aggregate) is not ResearchCandidateManualReviewBlockerAggregate:
        raise ValueError(
            "aggregate must be a ResearchCandidateManualReviewBlockerAggregate",
        )
    if type(config) is not ResearchCandidateManualReviewBlockerConfig:
        raise ValueError("config must be a ResearchCandidateManualReviewBlockerConfig")
    _require_hard_flags("aggregate", aggregate)
    _require_hard_flags("config", config)
    rows = _build_rows(aggregate, config)
    aggregate_score = _aggregate_score(rows)
    status = _report_status(rows, aggregate_score, config)
    reason_codes = _report_reason_codes(rows, aggregate_score, config, status)
    values = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "dimension_count": Decimal(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "aggregate_blocker_score": aggregate_score,
        "max_dimension_score": max((row.blocker_score for row in rows), default=ZERO),
        "status": status,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchCandidateManualReviewBlockerReport(
        report_digest=_report_digest_for_values(values),
        **values,
    )


def research_candidate_manual_review_blocker_report_payload(
    report: ResearchCandidateManualReviewBlockerReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCandidateManualReviewBlockerReport:
        _require_hard_flags("report", report)
        return _json_ready(asdict(report))
    if type(report) is not dict:
        raise ValueError("report must be a ResearchCandidateManualReviewBlockerReport")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _require_digest("report_digest", payload.get("report_digest"))
    if payload["report_digest"] != _report_digest_for_values(payload):
        raise ValueError("report_digest must match payload fields")
    return payload


def _build_rows(
    aggregate: ResearchCandidateManualReviewBlockerAggregate,
    config: ResearchCandidateManualReviewBlockerConfig,
) -> tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...]:
    return tuple(_build_row(aggregate, config, item) for item in DIMENSION_FIELDS)


def _build_row(
    aggregate: ResearchCandidateManualReviewBlockerAggregate,
    config: ResearchCandidateManualReviewBlockerConfig,
    item: tuple[str, str, str],
) -> ResearchCandidateManualReviewBlockerDimensionRow:
    dimension, score_field, weight_field = item
    score = getattr(aggregate, score_field)
    weight = getattr(config, weight_field)
    return ResearchCandidateManualReviewBlockerDimensionRow(
        dimension=dimension,
        blocker_score=score,
        component_weight=weight,
        weighted_blocker_score=_quantize(score * weight),
        status=_dimension_status(score, config),
        reason_codes=(_dimension_reason(dimension, _dimension_status(score, config)),),
    )


def _dimension_status(
    score: Decimal,
    config: ResearchCandidateManualReviewBlockerConfig,
) -> str:
    if score >= config.dimension_block_threshold:
        return "block"
    if score >= config.dimension_watch_threshold:
        return "watch"
    return "pass"


def _dimension_reason(dimension: str, status: str) -> str:
    return f"{dimension}_{status}"


def _aggregate_score(
    rows: tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...],
) -> Decimal:
    return _quantize(sum((row.weighted_blocker_score for row in rows), ZERO))


def _report_status(
    rows: tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...],
    aggregate_score: Decimal,
    config: ResearchCandidateManualReviewBlockerConfig,
) -> str:
    if any(row.status == "block" for row in rows) or aggregate_score >= config.block_blocker_score:
        return "block"
    if any(row.status == "watch" for row in rows) or aggregate_score >= config.watch_blocker_score:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...],
    aggregate_score: Decimal,
    config: ResearchCandidateManualReviewBlockerConfig,
    status: str,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REPORT_REASON,)
    reasons: list[str] = []
    if any(row.status == "block" for row in rows):
        reasons.append(BLOCK_DIMENSIONS_REPORT_REASON)
    if any(row.status == "watch" for row in rows):
        reasons.append(WATCH_DIMENSIONS_REPORT_REASON)
    if aggregate_score >= config.block_blocker_score:
        reasons.append(BLOCK_SCORE_REPORT_REASON)
    elif aggregate_score >= config.watch_blocker_score:
        reasons.append(WATCH_SCORE_REPORT_REASON)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchCandidateManualReviewBlockerReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
    for reason_code in report_reason_codes:
        counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
    denominator = Decimal(len(rows)) if rows else Decimal("1")
    return tuple(
        ResearchCandidateManualReviewBlockerReasonCodeCount(
            reason_code=reason_code,
            count=count,
            dimension_ratio=_quantize(count / denominator),
        )
        for reason_code, count in sorted(counts.items(), key=lambda value: value[0])
    )


def _status_count(
    rows: tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchCandidateManualReviewBlockerDimensionRow) -> None:
    if row.weighted_blocker_score != _quantize(row.blocker_score * row.component_weight):
        raise ValueError("weighted_blocker_score must match row fields")
    if row.reason_codes != (_dimension_reason(row.dimension, row.status),):
        raise ValueError("reason_codes must match row fields")


def _validate_report(report: ResearchCandidateManualReviewBlockerReport) -> None:
    rows = report.rows
    if report.dimension_count != Decimal(len(rows)):
        raise ValueError("dimension_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.aggregate_blocker_score != _aggregate_score(rows):
        raise ValueError("aggregate_blocker_score must match rows")
    if report.max_dimension_score != max((row.blocker_score for row in rows), default=ZERO):
        raise ValueError("max_dimension_score must match rows")
    if tuple(row.dimension for row in rows) != RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS:
        raise ValueError("rows must match dimension sequence")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.report_digest != _report_digest(report):
        raise ValueError("report_digest must match report fields")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchCandidateManualReviewBlockerDimensionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchCandidateManualReviewBlockerDimensionRow:
            raise ValueError(
                "rows must contain ResearchCandidateManualReviewBlockerDimensionRow",
            )
        _require_hard_flags("dimension row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchCandidateManualReviewBlockerReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    for item in counts:
        if type(item) is not ResearchCandidateManualReviewBlockerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCandidateManualReviewBlockerReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    if tuple(sorted(counts, key=lambda item: item.reason_code)) != counts:
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(RATIO_QUANT)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT)


def _require_dimension(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS:
        raise ValueError(f"{field_name} must be a known dimension")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain raw public identifiers")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload must not contain binary numeric values")
    if type(value) is str:
        _require_public_string("payload string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_string("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _report_digest(report: ResearchCandidateManualReviewBlockerReport) -> str:
    return _report_digest_for_values(asdict(report))


def _report_digest_for_values(values: dict[str, Any]) -> str:
    payload = {key: value for key, value in values.items() if key != "report_digest"}
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_CONFIG_VERSION",
    "RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS",
    "STATUSES",
    "ResearchCandidateManualReviewBlockerAggregate",
    "ResearchCandidateManualReviewBlockerConfig",
    "ResearchCandidateManualReviewBlockerDimensionRow",
    "ResearchCandidateManualReviewBlockerReasonCodeCount",
    "ResearchCandidateManualReviewBlockerReport",
    "build_research_candidate_manual_review_blocker_report",
    "research_candidate_manual_review_blocker_report_payload",
)
