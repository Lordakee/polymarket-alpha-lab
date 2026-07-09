"""Public-safe report-only calibration feedback loop health summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_CALIBRATION_FEEDBACK_LOOP_HEALTH_REPORT_CONFIG_VERSION = (
    "research-team-calibration-feedback-loop-health-report-v0"
)
PUBLIC_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT_PREC = 28
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")

_RESOLVED_OUTCOME_FOLLOW_UP_WEIGHT = Decimal("0.200000")
_CORRECTION_ADOPTION_WEIGHT = Decimal("0.200000")
_STALE_MEMORY_REDUCTION_WEIGHT = Decimal("0.150000")
_EVIDENCE_REUSE_QUALITY_WEIGHT = Decimal("0.150000")
_PEER_REVIEW_COVERAGE_WEIGHT = Decimal("0.150000")
_REVIEW_LATENCY_WEIGHT = Decimal("0.150000")

_DIMENSION_PREFIXES = (
    "resolved_outcome_follow_up",
    "correction_adoption",
    "stale_memory_reduction",
    "evidence_reuse_quality",
    "peer_review_coverage",
    "review_latency",
)
_ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code
    for prefix in ("calibration_feedback_loop_health", *_DIMENSION_PREFIXES)
    for reason_code in (
        f"{prefix}_pass",
        f"{prefix}_watch",
        f"{prefix}_block",
    )
)
_REPORT_REASON_CODE_SEQUENCE = (
    "calibration_feedback_loop_health_report_pass",
    "calibration_feedback_loop_health_report_watch",
    "calibration_feedback_loop_health_report_block",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate_id",
    "candidateid",
    "candidate",
    "market",
    "market_id",
    "marketid",
    "market_slug",
    "marketslug",
    "market_question",
    "marketquestion",
    "slug",
    "question",
    "source_url",
    "source_text",
    "source",
    "text",
    "url",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database_url",
    "dsn",
    "table_name",
    "table",
    "token",
    "secret",
    "credential",
    "password",
    "private_key",
    "api_key",
    "auth",
    "wallet",
    "order",
    "trade",
    "live",
    "route",
    "routing",
    "execute",
    "execution",
    "place",
    "position",
    "buy",
    "sell",
    "recommend",
    "recommendation",
    "size",
    "sizing",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_CALIBRATION_FEEDBACK_LOOP_HEALTH_REPORT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamCalibrationFeedbackLoopHealthConfig",
    "ResearchTeamCalibrationFeedbackLoopHealthObservation",
    "ResearchTeamCalibrationFeedbackLoopHealthRow",
    "ResearchTeamCalibrationFeedbackLoopHealthReport",
    "build_research_team_calibration_feedback_loop_health_report",
    "research_team_calibration_feedback_loop_health_payload",
    "format_research_team_calibration_feedback_loop_health_digest",
)


@dataclass(frozen=True)
class ResearchTeamCalibrationFeedbackLoopHealthConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_CALIBRATION_FEEDBACK_LOOP_HEALTH_REPORT_CONFIG_VERSION
    )
    pass_health_score_threshold: Decimal = Decimal("0.800000")
    block_health_score_threshold: Decimal = Decimal("0.500000")
    max_review_latency_seconds: Decimal = Decimal("345600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCalibrationFeedbackLoopHealthConfig:
            raise ValueError(
                "config must be exactly ResearchTeamCalibrationFeedbackLoopHealthConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in ("pass_health_score_threshold", "block_health_score_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_health_score_threshold > self.pass_health_score_threshold:
            raise ValueError(
                "pass_health_score_threshold must be at least "
                "block_health_score_threshold",
            )
        object.__setattr__(
            self,
            "max_review_latency_seconds",
            _require_positive_decimal(
                "max_review_latency_seconds",
                self.max_review_latency_seconds,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamCalibrationFeedbackLoopHealthObservation:
    feedback_loop_id: str
    team_id: str
    resolved_outcome_follow_up_ratio: Decimal
    correction_adoption_ratio: Decimal
    stale_memory_reduction_ratio: Decimal
    evidence_reuse_quality_ratio: Decimal
    peer_review_coverage_ratio: Decimal
    average_review_latency_seconds: Decimal
    reviewed_resolution_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCalibrationFeedbackLoopHealthObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchTeamCalibrationFeedbackLoopHealthObservation",
            )
        for field_name in ("feedback_loop_id", "team_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolved_outcome_follow_up_ratio",
            "correction_adoption_ratio",
            "stale_memory_reduction_ratio",
            "evidence_reuse_quality_ratio",
            "peer_review_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_review_latency_seconds",
            _require_nonnegative_decimal(
                "average_review_latency_seconds",
                self.average_review_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reviewed_resolution_count",
            _require_nonnegative_count_decimal(
                "reviewed_resolution_count",
                self.reviewed_resolution_count,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamCalibrationFeedbackLoopHealthRow:
    feedback_loop_id: str
    team_id: str
    resolved_outcome_follow_up_ratio: Decimal
    correction_adoption_ratio: Decimal
    stale_memory_reduction_ratio: Decimal
    evidence_reuse_quality_ratio: Decimal
    peer_review_coverage_ratio: Decimal
    average_review_latency_seconds: Decimal
    review_latency_score: Decimal
    reviewed_resolution_count: Decimal
    health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCalibrationFeedbackLoopHealthRow:
            raise ValueError("row must be exactly ResearchTeamCalibrationFeedbackLoopHealthRow")
        for field_name in ("feedback_loop_id", "team_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolved_outcome_follow_up_ratio",
            "correction_adoption_ratio",
            "stale_memory_reduction_ratio",
            "evidence_reuse_quality_ratio",
            "peer_review_coverage_ratio",
            "review_latency_score",
            "health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_review_latency_seconds",
            _require_nonnegative_decimal(
                "average_review_latency_seconds",
                self.average_review_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reviewed_resolution_count",
            _require_nonnegative_count_decimal(
                "reviewed_resolution_count",
                self.reviewed_resolution_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamCalibrationFeedbackLoopHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    loop_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_reviewed_resolution_count: Decimal
    min_health_score: Decimal
    average_health_score: Decimal
    average_review_latency_seconds: Decimal
    rows: tuple[ResearchTeamCalibrationFeedbackLoopHealthRow, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCalibrationFeedbackLoopHealthReport:
            raise ValueError(
                "report must be exactly ResearchTeamCalibrationFeedbackLoopHealthReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_status("health_status", self.health_status)
        for field_name in ("loop_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_reviewed_resolution_count",
            _require_nonnegative_count_decimal(
                "total_reviewed_resolution_count",
                self.total_reviewed_resolution_count,
            ),
        )
        for field_name in ("min_health_score", "average_health_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_review_latency_seconds",
            _require_nonnegative_decimal(
                "average_review_latency_seconds",
                self.average_review_latency_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        else:
            _require_public_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")


def build_research_team_calibration_feedback_loop_health_report(
    observations: Sequence[ResearchTeamCalibrationFeedbackLoopHealthObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig | None = None,
) -> ResearchTeamCalibrationFeedbackLoopHealthReport:
    cfg = config or ResearchTeamCalibrationFeedbackLoopHealthConfig()
    if type(cfg) is not ResearchTeamCalibrationFeedbackLoopHealthConfig:
        raise ValueError(
            "config must be a ResearchTeamCalibrationFeedbackLoopHealthConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted((_row_from_observation(row, cfg) for row in normalized), key=_row_sort_key),
    )
    health_status = _report_status(rows)
    return ResearchTeamCalibrationFeedbackLoopHealthReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        health_status=health_status,
        loop_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        total_reviewed_resolution_count=_sum_decimal(
            row.reviewed_resolution_count for row in rows
        ),
        min_health_score=min((row.health_score for row in rows), default=_ZERO),
        average_health_score=_average_decimal(row.health_score for row in rows),
        average_review_latency_seconds=_average_decimal(
            row.average_review_latency_seconds for row in rows
        ),
        rows=rows,
        reason_codes=(f"calibration_feedback_loop_health_report_{health_status}",),
    )


def research_team_calibration_feedback_loop_health_payload(
    report: ResearchTeamCalibrationFeedbackLoopHealthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamCalibrationFeedbackLoopHealthReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamCalibrationFeedbackLoopHealthReport or payload",
    )


def format_research_team_calibration_feedback_loop_health_digest(
    report: ResearchTeamCalibrationFeedbackLoopHealthReport,
) -> str:
    if type(report) is not ResearchTeamCalibrationFeedbackLoopHealthReport:
        raise ValueError("report must be a ResearchTeamCalibrationFeedbackLoopHealthReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    return (
        "research-team-calibration-feedback-loop-health: "
        f"generated_at={report.generated_at.isoformat()} "
        f"status={report.health_status} "
        f"loops={report.loop_count} "
        f"pass={report.pass_count} "
        f"watch={report.watch_count} "
        f"block={report.block_count} "
        f"reviewed_resolutions={report.total_reviewed_resolution_count} "
        f"min_score={report.min_health_score} "
        f"average_score={report.average_health_score} "
        f"average_review_latency_seconds={report.average_review_latency_seconds} "
        f"reason_codes={','.join(report.reason_codes)} "
        f"public_digest={report.public_digest} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}\n"
    )


def _row_from_observation(
    observation: ResearchTeamCalibrationFeedbackLoopHealthObservation,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig,
) -> ResearchTeamCalibrationFeedbackLoopHealthRow:
    review_latency_score = _review_latency_score(
        observation.average_review_latency_seconds,
        config,
    )
    health_score = _health_score(
        resolved_outcome_follow_up_ratio=observation.resolved_outcome_follow_up_ratio,
        correction_adoption_ratio=observation.correction_adoption_ratio,
        stale_memory_reduction_ratio=observation.stale_memory_reduction_ratio,
        evidence_reuse_quality_ratio=observation.evidence_reuse_quality_ratio,
        peer_review_coverage_ratio=observation.peer_review_coverage_ratio,
        review_latency_score=review_latency_score,
    )
    status = _score_status(health_score, config)
    return ResearchTeamCalibrationFeedbackLoopHealthRow(
        feedback_loop_id=observation.feedback_loop_id,
        team_id=observation.team_id,
        resolved_outcome_follow_up_ratio=observation.resolved_outcome_follow_up_ratio,
        correction_adoption_ratio=observation.correction_adoption_ratio,
        stale_memory_reduction_ratio=observation.stale_memory_reduction_ratio,
        evidence_reuse_quality_ratio=observation.evidence_reuse_quality_ratio,
        peer_review_coverage_ratio=observation.peer_review_coverage_ratio,
        average_review_latency_seconds=observation.average_review_latency_seconds,
        review_latency_score=review_latency_score,
        reviewed_resolution_count=observation.reviewed_resolution_count,
        health_score=health_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            resolved_outcome_follow_up_ratio=observation.resolved_outcome_follow_up_ratio,
            correction_adoption_ratio=observation.correction_adoption_ratio,
            stale_memory_reduction_ratio=observation.stale_memory_reduction_ratio,
            evidence_reuse_quality_ratio=observation.evidence_reuse_quality_ratio,
            peer_review_coverage_ratio=observation.peer_review_coverage_ratio,
            review_latency_score=review_latency_score,
            config=config,
        ),
    )


def _review_latency_score(
    average_review_latency_seconds: Decimal,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig,
) -> Decimal:
    return _clamp_ratio(
        _ONE
        - _ratio_or_zero(
            average_review_latency_seconds,
            config.max_review_latency_seconds,
        ),
    )


def _health_score(
    *,
    resolved_outcome_follow_up_ratio: Decimal,
    correction_adoption_ratio: Decimal,
    stale_memory_reduction_ratio: Decimal,
    evidence_reuse_quality_ratio: Decimal,
    peer_review_coverage_ratio: Decimal,
    review_latency_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        resolved_outcome_follow_up_ratio * _RESOLVED_OUTCOME_FOLLOW_UP_WEIGHT
        + correction_adoption_ratio * _CORRECTION_ADOPTION_WEIGHT
        + stale_memory_reduction_ratio * _STALE_MEMORY_REDUCTION_WEIGHT
        + evidence_reuse_quality_ratio * _EVIDENCE_REUSE_QUALITY_WEIGHT
        + peer_review_coverage_ratio * _PEER_REVIEW_COVERAGE_WEIGHT
        + review_latency_score * _REVIEW_LATENCY_WEIGHT,
    )


def _score_status(
    score: Decimal,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig,
) -> str:
    if score <= config.block_health_score_threshold:
        return "block"
    if score < config.pass_health_score_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    resolved_outcome_follow_up_ratio: Decimal,
    correction_adoption_ratio: Decimal,
    stale_memory_reduction_ratio: Decimal,
    evidence_reuse_quality_ratio: Decimal,
    peer_review_coverage_ratio: Decimal,
    review_latency_score: Decimal,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig,
) -> tuple[str, ...]:
    return _normalize_row_reason_codes(
        (
            f"calibration_feedback_loop_health_{status}",
            _dimension_reason(
                "resolved_outcome_follow_up",
                resolved_outcome_follow_up_ratio,
                config,
            ),
            _dimension_reason("correction_adoption", correction_adoption_ratio, config),
            _dimension_reason(
                "stale_memory_reduction",
                stale_memory_reduction_ratio,
                config,
            ),
            _dimension_reason(
                "evidence_reuse_quality",
                evidence_reuse_quality_ratio,
                config,
            ),
            _dimension_reason(
                "peer_review_coverage",
                peer_review_coverage_ratio,
                config,
            ),
            _dimension_reason("review_latency", review_latency_score, config),
        ),
    )


def _dimension_reason(
    prefix: str,
    value: Decimal,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig,
) -> str:
    return f"{prefix}_{_score_status(value, config)}"


def _normalize_observations(
    observations: Sequence[ResearchTeamCalibrationFeedbackLoopHealthObservation],
) -> tuple[ResearchTeamCalibrationFeedbackLoopHealthObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchTeamCalibrationFeedbackLoopHealthObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamCalibrationFeedbackLoopHealthObservation",
            )
    return tuple(sorted(normalized, key=lambda item: (item.feedback_loop_id, item.team_id)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamCalibrationFeedbackLoopHealthRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamCalibrationFeedbackLoopHealthRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamCalibrationFeedbackLoopHealthRow",
        ) from exc
    for row in normalized:
        if type(row) is not ResearchTeamCalibrationFeedbackLoopHealthRow:
            raise ValueError(
                "rows must contain ResearchTeamCalibrationFeedbackLoopHealthRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchTeamCalibrationFeedbackLoopHealthRow,
) -> tuple[int, Decimal, str, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (status_rank[row.status], row.health_score, row.feedback_loop_id, row.team_id)


def _report_status(rows: tuple[ResearchTeamCalibrationFeedbackLoopHealthRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamCalibrationFeedbackLoopHealthRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_report(report: ResearchTeamCalibrationFeedbackLoopHealthReport) -> None:
    if report.loop_count != _count(len(report.rows)):
        raise ValueError("loop_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.health_status != _report_status(report.rows):
        raise ValueError("health_status must match rows")
    if report.total_reviewed_resolution_count != _sum_decimal(
        row.reviewed_resolution_count for row in report.rows
    ):
        raise ValueError("total_reviewed_resolution_count must match rows")
    if report.min_health_score != min((row.health_score for row in report.rows), default=_ZERO):
        raise ValueError("min_health_score must match rows")
    if report.average_health_score != _average_decimal(row.health_score for row in report.rows):
        raise ValueError("average_health_score must match rows")
    if report.average_review_latency_seconds != _average_decimal(
        row.average_review_latency_seconds for row in report.rows
    ):
        raise ValueError("average_review_latency_seconds must match rows")
    if report.reason_codes != (
        f"calibration_feedback_loop_health_report_{report.health_status}",
    ):
        raise ValueError("reason_codes must match health_status")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        value,
        _ROW_REASON_CODE_SEQUENCE,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        value,
        _REPORT_REASON_CODE_SEQUENCE,
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"reason_code must be one of {allowed}")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=allowed.index))


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of {PUBLIC_STATUSES}")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < _QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must set {field_name}=True")


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in _FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must set {field_name}=True")
    _validate_nested_payload_flags("payload", payload)


def _validate_nested_payload_flags(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _validate_nested_payload_flags(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_nested_payload_flags(f"{label}[{index}]", item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "public_digest":
                continue
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if key != "public_digest":
                _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(_unsafe_term_matches(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} must not expose raw identifiers or execution terms")


def _unsafe_term_matches(value: str, term: str) -> bool:
    if "://" in term or "_" in term:
        return term in value
    if term in {
        "auth",
        "buy",
        "candidate",
        "execute",
        "live",
        "market",
        "order",
        "place",
        "question",
        "recommend",
        "route",
        "sell",
        "size",
        "slug",
        "source",
        "text",
        "token",
        "trade",
        "wallet",
    }:
        return term in value
    return re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", value) is not None


def _public_digest_for_report(
    report: ResearchTeamCalibrationFeedbackLoopHealthReport,
) -> str:
    values = asdict(report)
    values.pop("public_digest", None)
    return _public_digest(values)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("public_digest")
    _require_public_digest("public_digest", digest)
    values = dict(payload)
    values.pop("public_digest", None)
    expected = _public_digest(values)
    if digest != expected:
        raise ValueError("public_digest must match payload")


def _public_digest(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return f"{value:.6f}"
    return value


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    total = _ZERO
    for value in values:
        total = _decimal(total + value)
    return total


def _average_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return _decimal(_sum_decimal(normalized) / Decimal(len(normalized)))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _decimal(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PREC
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)
