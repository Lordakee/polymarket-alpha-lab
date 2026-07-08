"""Pure report-only variance report for specialist review quality."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_VARIANCE_CONFIG_VERSION = (
    "research-team-review-quality-variance-report-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HALF = Decimal("0.500000")
_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "buy",
    "candidate",
    "dsn",
    "event",
    "live",
    "market",
    "order",
    "position",
    "question",
    "raw",
    "recommend",
    "sell",
    "sizing",
    "slug",
    "source",
    "table",
    "text",
    "token",
    "trade",
    "url",
    "wallet",
)
_REASON_CODE_SEQUENCE = (
    "review_quality_variance_report_pass",
    "review_quality_variance_report_block_rows",
    "review_quality_variance_report_watch_rows",
    "review_quality_variance_empty_input",
    "review_quality_variance_pass",
    "review_quality_variance_watch",
    "review_quality_variance_block",
    "calibration_pass",
    "calibration_watch",
    "calibration_low",
    "evidence_completeness_pass",
    "evidence_completeness_watch",
    "evidence_completeness_low",
    "contradiction_handling_pass",
    "contradiction_handling_watch",
    "contradiction_handling_low",
    "review_latency_fresh",
    "review_latency_watch",
    "review_latency_slow",
    "memory_freshness_fresh",
    "memory_freshness_watch",
    "memory_freshness_stale",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_VARIANCE_CONFIG_VERSION",
    "ResearchTeamReviewQualityReasonCodeCount",
    "ResearchTeamReviewQualityVarianceConfig",
    "ResearchTeamReviewQualityVarianceReport",
    "ResearchTeamReviewQualityVarianceRow",
    "SpecialistTeamReviewQualitySnapshot",
    "build_research_team_review_quality_variance_report",
    "research_team_review_quality_variance_report_digest",
    "research_team_review_quality_variance_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamReviewQualityVarianceConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_VARIANCE_CONFIG_VERSION
    min_pass_calibration_score: Decimal = Decimal("0.800000")
    min_watch_calibration_score: Decimal = Decimal("0.600000")
    min_pass_evidence_completeness_score: Decimal = Decimal("0.850000")
    min_watch_evidence_completeness_score: Decimal = Decimal("0.650000")
    max_pass_contradiction_miss_rate: Decimal = Decimal("0.050000")
    max_watch_contradiction_miss_rate: Decimal = Decimal("0.250000")
    max_pass_review_latency_hours: Decimal = Decimal("12.000000")
    max_watch_review_latency_hours: Decimal = Decimal("36.000000")
    max_pass_memory_age_days: Decimal = Decimal("7.000000")
    max_watch_memory_age_days: Decimal = Decimal("21.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityVarianceConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for field_name in (
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "min_pass_evidence_completeness_score",
            "min_watch_evidence_completeness_score",
            "max_pass_contradiction_miss_rate",
            "max_watch_contradiction_miss_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_review_latency_hours",
            "max_watch_review_latency_hours",
            "max_pass_memory_age_days",
            "max_watch_memory_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class SpecialistTeamReviewQualitySnapshot(_FinalPublicDataclass):
    specialist_team_key: str
    reviewed_packet_count: Decimal
    calibrated_packet_count: Decimal
    evidence_required_count: Decimal
    evidence_complete_count: Decimal
    contradiction_flag_count: Decimal
    contradiction_resolved_count: Decimal
    mean_review_latency_hours: Decimal
    mean_memory_age_days: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamReviewQualitySnapshot, "snapshot")
        object.__setattr__(
            self,
            "specialist_team_key",
            _require_public_identifier("specialist_team_key", self.specialist_team_key),
        )
        for field_name in (
            "reviewed_packet_count",
            "calibrated_packet_count",
            "evidence_required_count",
            "evidence_complete_count",
            "contradiction_flag_count",
            "contradiction_resolved_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_review_latency_hours", "mean_memory_age_days"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
            )
        if self.reviewed_packet_count <= _ZERO:
            raise ValueError("reviewed_packet_count must be positive")
        if self.evidence_required_count <= _ZERO:
            raise ValueError("evidence_required_count must be positive")
        if self.calibrated_packet_count > self.reviewed_packet_count:
            raise ValueError("calibrated_packet_count must not exceed reviewed_packet_count")
        if self.evidence_complete_count > self.evidence_required_count:
            raise ValueError(
                "evidence_complete_count must not exceed evidence_required_count",
            )
        if self.contradiction_resolved_count > self.contradiction_flag_count:
            raise ValueError(
                "contradiction_resolved_count must not exceed contradiction_flag_count",
            )
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamReviewQualityVarianceRow(_FinalPublicDataclass):
    specialist_team_key: str
    reviewed_packet_count: Decimal
    calibration_score: Decimal
    evidence_completeness_score: Decimal
    contradiction_handling_score: Decimal
    contradiction_miss_rate: Decimal
    mean_review_latency_hours: Decimal
    mean_memory_age_days: Decimal
    quality_variance_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityVarianceRow, "row")
        object.__setattr__(
            self,
            "specialist_team_key",
            _require_public_identifier("specialist_team_key", self.specialist_team_key),
        )
        object.__setattr__(
            self,
            "reviewed_packet_count",
            _require_nonnegative_count_decimal(
                "reviewed_packet_count",
                self.reviewed_packet_count,
            ),
        )
        for field_name in (
            "calibration_score",
            "evidence_completeness_score",
            "contradiction_handling_score",
            "contradiction_miss_rate",
            "quality_variance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_review_latency_hours", "mean_memory_age_days"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
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
class ResearchTeamReviewQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityReasonCodeCount, "count")
        object.__setattr__(
            self,
            "reason_code",
            _require_supported_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamReviewQualityVarianceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_calibration_score: Decimal
    mean_evidence_completeness_score: Decimal
    mean_contradiction_handling_score: Decimal
    mean_review_latency_hours: Decimal
    mean_memory_age_days: Decimal
    mean_quality_variance_score: Decimal
    max_quality_variance_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamReviewQualityReasonCodeCount, ...]
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityVarianceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_calibration_score",
            "mean_evidence_completeness_score",
            "mean_contradiction_handling_score",
            "mean_quality_variance_score",
            "max_quality_variance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_review_latency_hours", "mean_memory_age_days"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.public_digest:
            _require_sha256_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report fields")
        object.__setattr__(self, "public_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_team_review_quality_variance_report(
    snapshots: Sequence[SpecialistTeamReviewQualitySnapshot],
    *,
    generated_at: datetime,
    config: ResearchTeamReviewQualityVarianceConfig | None = None,
) -> ResearchTeamReviewQualityVarianceReport:
    if config is None:
        config = ResearchTeamReviewQualityVarianceConfig()
    if type(config) is not ResearchTeamReviewQualityVarianceConfig:
        raise ValueError("config must be a ResearchTeamReviewQualityVarianceConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(_row_from_snapshot(snapshot, config) for snapshot in normalized_snapshots)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": (
            _decimal_count(1) if not rows else _decimal_count(_status_count(rows, "block"))
        ),
        "mean_calibration_score": _mean_row_decimal(
            rows,
            "calibration_score",
            ratio=True,
        ),
        "mean_evidence_completeness_score": _mean_row_decimal(
            rows,
            "evidence_completeness_score",
            ratio=True,
        ),
        "mean_contradiction_handling_score": _mean_row_decimal(
            rows,
            "contradiction_handling_score",
            ratio=True,
        ),
        "mean_review_latency_hours": _mean_row_decimal(
            rows,
            "mean_review_latency_hours",
        ),
        "mean_memory_age_days": _mean_row_decimal(rows, "mean_memory_age_days"),
        "mean_quality_variance_score": _mean_row_decimal(
            rows,
            "quality_variance_score",
            ratio=True,
        ),
        "max_quality_variance_score": _max_row_decimal(
            rows,
            "quality_variance_score",
            ratio=True,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": (),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["reason_code_counts"] = _reason_code_counts(
        values["reason_codes"],
        rows,
    )
    return ResearchTeamReviewQualityVarianceReport(
        **values,
        public_digest=_digest_from_values(values),
    )


def research_team_review_quality_variance_report_payload(
    report: ResearchTeamReviewQualityVarianceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamReviewQualityVarianceReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamReviewQualityVarianceReport or payload",
    )


def research_team_review_quality_variance_report_digest(
    report: ResearchTeamReviewQualityVarianceReport | dict[str, Any],
) -> str:
    payload = research_team_review_quality_variance_report_payload(report)
    return _payload_digest(payload)


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


def _row_from_snapshot(
    snapshot: SpecialistTeamReviewQualitySnapshot,
    config: ResearchTeamReviewQualityVarianceConfig,
) -> ResearchTeamReviewQualityVarianceRow:
    calibration_score = _ratio_or_zero(
        snapshot.calibrated_packet_count,
        snapshot.reviewed_packet_count,
    )
    evidence_score = _ratio_or_zero(
        snapshot.evidence_complete_count,
        snapshot.evidence_required_count,
    )
    contradiction_miss_rate = _contradiction_miss_rate(snapshot)
    contradiction_handling_score = _clamp_ratio(_ONE - contradiction_miss_rate)
    variance_score = _quality_variance_score(
        calibration_score=calibration_score,
        evidence_completeness_score=evidence_score,
        contradiction_miss_rate=contradiction_miss_rate,
        review_latency_hours=snapshot.mean_review_latency_hours,
        memory_age_days=snapshot.mean_memory_age_days,
        config=config,
    )
    status = _row_status(
        calibration_score=calibration_score,
        evidence_completeness_score=evidence_score,
        contradiction_miss_rate=contradiction_miss_rate,
        review_latency_hours=snapshot.mean_review_latency_hours,
        memory_age_days=snapshot.mean_memory_age_days,
        config=config,
    )
    return ResearchTeamReviewQualityVarianceRow(
        specialist_team_key=snapshot.specialist_team_key,
        reviewed_packet_count=snapshot.reviewed_packet_count,
        calibration_score=calibration_score,
        evidence_completeness_score=evidence_score,
        contradiction_handling_score=contradiction_handling_score,
        contradiction_miss_rate=contradiction_miss_rate,
        mean_review_latency_hours=snapshot.mean_review_latency_hours,
        mean_memory_age_days=snapshot.mean_memory_age_days,
        quality_variance_score=variance_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            calibration_score=calibration_score,
            evidence_completeness_score=evidence_score,
            contradiction_miss_rate=contradiction_miss_rate,
            review_latency_hours=snapshot.mean_review_latency_hours,
            memory_age_days=snapshot.mean_memory_age_days,
            config=config,
        ),
    )


def _quality_variance_score(
    *,
    calibration_score: Decimal,
    evidence_completeness_score: Decimal,
    contradiction_miss_rate: Decimal,
    review_latency_hours: Decimal,
    memory_age_days: Decimal,
    config: ResearchTeamReviewQualityVarianceConfig,
) -> Decimal:
    return _ratio(
        _higher_is_better_variance(
            calibration_score,
            config.min_pass_calibration_score,
            config.min_watch_calibration_score,
        )
        + _higher_is_better_variance(
            evidence_completeness_score,
            config.min_pass_evidence_completeness_score,
            config.min_watch_evidence_completeness_score,
        )
        + _lower_ratio_is_better_variance(
            contradiction_miss_rate,
            config.max_pass_contradiction_miss_rate,
            config.max_watch_contradiction_miss_rate,
        )
        + _lower_measure_is_better_variance(
            review_latency_hours,
            config.max_pass_review_latency_hours,
            config.max_watch_review_latency_hours,
        )
        + _lower_measure_is_better_variance(
            memory_age_days,
            config.max_pass_memory_age_days,
            config.max_watch_memory_age_days,
        ),
        Decimal("5.000000"),
    )


def _higher_is_better_variance(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value >= pass_threshold:
        return _ZERO
    if value >= watch_threshold:
        return _clamp_ratio(
            ((pass_threshold - value) / (pass_threshold - watch_threshold)) * _HALF,
        )
    return _clamp_ratio(_HALF + ((watch_threshold - value) / watch_threshold) * _HALF)


def _lower_ratio_is_better_variance(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return _ZERO
    if value <= watch_threshold:
        return _clamp_ratio(
            ((value - pass_threshold) / (watch_threshold - pass_threshold)) * _HALF,
        )
    return _clamp_ratio(
        _HALF + ((value - watch_threshold) / (_ONE - watch_threshold)) * _HALF,
    )


def _lower_measure_is_better_variance(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return _ZERO
    if value <= watch_threshold:
        return _clamp_ratio(
            ((value - pass_threshold) / (watch_threshold - pass_threshold)) * _HALF,
        )
    return _clamp_ratio(_HALF + ((value - watch_threshold) / watch_threshold) * _HALF)


def _row_status(
    *,
    calibration_score: Decimal,
    evidence_completeness_score: Decimal,
    contradiction_miss_rate: Decimal,
    review_latency_hours: Decimal,
    memory_age_days: Decimal,
    config: ResearchTeamReviewQualityVarianceConfig,
) -> str:
    if (
        calibration_score < config.min_watch_calibration_score
        or evidence_completeness_score < config.min_watch_evidence_completeness_score
        or contradiction_miss_rate > config.max_watch_contradiction_miss_rate
        or review_latency_hours > config.max_watch_review_latency_hours
        or memory_age_days > config.max_watch_memory_age_days
    ):
        return "block"
    if (
        calibration_score < config.min_pass_calibration_score
        or evidence_completeness_score < config.min_pass_evidence_completeness_score
        or contradiction_miss_rate > config.max_pass_contradiction_miss_rate
        or review_latency_hours > config.max_pass_review_latency_hours
        or memory_age_days > config.max_pass_memory_age_days
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    calibration_score: Decimal,
    evidence_completeness_score: Decimal,
    contradiction_miss_rate: Decimal,
    review_latency_hours: Decimal,
    memory_age_days: Decimal,
    config: ResearchTeamReviewQualityVarianceConfig,
) -> tuple[str, ...]:
    reason_codes = [f"review_quality_variance_{status}"]
    reason_codes.append(
        _high_metric_reason(
            "calibration",
            calibration_score,
            config.min_pass_calibration_score,
            config.min_watch_calibration_score,
            low_reason="calibration_low",
        ),
    )
    reason_codes.append(
        _high_metric_reason(
            "evidence_completeness",
            evidence_completeness_score,
            config.min_pass_evidence_completeness_score,
            config.min_watch_evidence_completeness_score,
            low_reason="evidence_completeness_low",
        ),
    )
    reason_codes.append(
        _low_metric_reason(
            "contradiction_handling",
            contradiction_miss_rate,
            config.max_pass_contradiction_miss_rate,
            config.max_watch_contradiction_miss_rate,
            high_reason="contradiction_handling_low",
        ),
    )
    reason_codes.append(
        _low_metric_reason(
            "review_latency",
            review_latency_hours,
            config.max_pass_review_latency_hours,
            config.max_watch_review_latency_hours,
            pass_reason="review_latency_fresh",
            watch_reason="review_latency_watch",
            high_reason="review_latency_slow",
        ),
    )
    reason_codes.append(
        _low_metric_reason(
            "memory_freshness",
            memory_age_days,
            config.max_pass_memory_age_days,
            config.max_watch_memory_age_days,
            pass_reason="memory_freshness_fresh",
            watch_reason="memory_freshness_watch",
            high_reason="memory_freshness_stale",
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _high_metric_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    *,
    low_reason: str,
) -> str:
    if value >= pass_threshold:
        return f"{prefix}_pass"
    if value >= watch_threshold:
        return f"{prefix}_watch"
    return low_reason


def _low_metric_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    *,
    pass_reason: str | None = None,
    watch_reason: str | None = None,
    high_reason: str,
) -> str:
    if value <= pass_threshold:
        return pass_reason if pass_reason is not None else f"{prefix}_pass"
    if value <= watch_threshold:
        return watch_reason if watch_reason is not None else f"{prefix}_watch"
    return high_reason


def _report_status(rows: tuple[ResearchTeamReviewQualityVarianceRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("review_quality_variance_empty_input",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append("review_quality_variance_report_block_rows")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("review_quality_variance_report_watch_rows")
    if not reason_codes:
        reason_codes.append("review_quality_variance_report_pass")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    report_reason_codes: object,
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...],
) -> tuple[ResearchTeamReviewQualityReasonCodeCount, ...]:
    if not isinstance(report_reason_codes, tuple):
        raise ValueError("report_reason_codes must be a tuple")
    counter: Counter[str] = Counter(report_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamReviewQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _contradiction_miss_rate(
    snapshot: SpecialistTeamReviewQualitySnapshot,
) -> Decimal:
    if snapshot.contradiction_flag_count == _ZERO:
        return _ZERO
    misses = snapshot.contradiction_flag_count - snapshot.contradiction_resolved_count
    return _ratio(misses, snapshot.contradiction_flag_count)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize_decimal(value)


def _mean_row_decimal(
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...],
    field_name: str,
    *,
    ratio: bool = False,
) -> Decimal:
    if not rows:
        return _ZERO
    value = sum((getattr(row, field_name) for row in rows), start=_ZERO) / _decimal_count(
        len(rows),
    )
    if ratio:
        return _clamp_ratio(value)
    return _quantize_decimal(value)


def _max_row_decimal(
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...],
    field_name: str,
    *,
    ratio: bool = False,
) -> Decimal:
    if not rows:
        return _ZERO
    value = max(getattr(row, field_name) for row in rows)
    if ratio:
        return _clamp_ratio(value)
    return _quantize_decimal(value)


def _status_count(
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_snapshots(
    snapshots: Sequence[SpecialistTeamReviewQualitySnapshot],
) -> tuple[SpecialistTeamReviewQualitySnapshot, ...]:
    normalized: list[SpecialistTeamReviewQualitySnapshot] = []
    seen_keys: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not SpecialistTeamReviewQualitySnapshot:
            raise ValueError("snapshots must contain SpecialistTeamReviewQualitySnapshot")
        _require_hard_flags("snapshot", snapshot)
        if snapshot.specialist_team_key in seen_keys:
            raise ValueError("specialist_team_key values must be unique")
        seen_keys.add(snapshot.specialist_team_key)
        normalized.append(snapshot)
    return tuple(sorted(normalized, key=lambda item: item.specialist_team_key))


def _normalize_rows(
    rows: tuple[ResearchTeamReviewQualityVarianceRow, ...],
) -> tuple[ResearchTeamReviewQualityVarianceRow, ...]:
    normalized: list[ResearchTeamReviewQualityVarianceRow] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamReviewQualityVarianceRow:
            raise ValueError("rows must contain ResearchTeamReviewQualityVarianceRow")
        _require_hard_flags("row", row)
        if row.specialist_team_key in seen_keys:
            raise ValueError("specialist_team_key values must be unique")
        seen_keys.add(row.specialist_team_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda item: item.specialist_team_key))


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamReviewQualityReasonCodeCount, ...],
) -> tuple[ResearchTeamReviewQualityReasonCodeCount, ...]:
    normalized: list[ResearchTeamReviewQualityReasonCodeCount] = []
    seen_reason_codes: set[str] = set()
    for item in counts:
        if type(item) is not ResearchTeamReviewQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTeamReviewQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reason_codes.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(normalized, key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code)),
    )


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        reason_code = _require_supported_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(
        sorted(normalized, key=lambda reason_code: _REASON_CODE_SEQUENCE.index(reason_code)),
    )


def _require_supported_reason_code(field_name: str, value: str) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _validate_config(config: ResearchTeamReviewQualityVarianceConfig) -> None:
    if config.min_pass_calibration_score <= config.min_watch_calibration_score:
        raise ValueError(
            "min_pass_calibration_score must exceed min_watch_calibration_score",
        )
    if (
        config.min_pass_evidence_completeness_score
        <= config.min_watch_evidence_completeness_score
    ):
        raise ValueError(
            "min_pass_evidence_completeness_score must exceed "
            "min_watch_evidence_completeness_score",
        )
    if config.max_pass_contradiction_miss_rate >= config.max_watch_contradiction_miss_rate:
        raise ValueError(
            "max_pass_contradiction_miss_rate must be less than "
            "max_watch_contradiction_miss_rate",
        )
    if config.max_pass_review_latency_hours >= config.max_watch_review_latency_hours:
        raise ValueError(
            "max_pass_review_latency_hours must be less than "
            "max_watch_review_latency_hours",
        )
    if config.max_pass_memory_age_days >= config.max_watch_memory_age_days:
        raise ValueError(
            "max_pass_memory_age_days must be less than max_watch_memory_age_days",
        )


def _validate_row(row: ResearchTeamReviewQualityVarianceRow) -> None:
    if row.status == "pass" and row.reason_codes[0] != "review_quality_variance_pass":
        raise ValueError("pass row reason_codes must start with pass reason")
    if row.status == "watch" and row.reason_codes[0] != "review_quality_variance_watch":
        raise ValueError("watch row reason_codes must start with watch reason")
    if row.status == "block" and row.reason_codes[0] != "review_quality_variance_block":
        raise ValueError("block row reason_codes must start with block reason")


def _validate_report(report: ResearchTeamReviewQualityVarianceReport) -> None:
    rows = report.rows
    if report.team_count != _decimal_count(len(rows)):
        raise ValueError("team_count must match rows")
    expected_block_count = _decimal_count(1) if not rows else _decimal_count(
        _status_count(rows, "block"),
    )
    expected_counts = {
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": expected_block_count,
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_means = {
        "mean_calibration_score": _mean_row_decimal(
            rows,
            "calibration_score",
            ratio=True,
        ),
        "mean_evidence_completeness_score": _mean_row_decimal(
            rows,
            "evidence_completeness_score",
            ratio=True,
        ),
        "mean_contradiction_handling_score": _mean_row_decimal(
            rows,
            "contradiction_handling_score",
            ratio=True,
        ),
        "mean_review_latency_hours": _mean_row_decimal(
            rows,
            "mean_review_latency_hours",
        ),
        "mean_memory_age_days": _mean_row_decimal(rows, "mean_memory_age_days"),
        "mean_quality_variance_score": _mean_row_decimal(
            rows,
            "quality_variance_score",
            ratio=True,
        ),
        "max_quality_variance_score": _max_row_decimal(
            rows,
            "quality_variance_score",
            ratio=True,
        ),
    }
    for field_name, expected in expected_means.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: str) -> str:
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_value(field_name, value)
    return value


def _require_public_label(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_value(field_name, value)
    return value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return value.quantize(_QUANT)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_measure_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    quantized = _quantize_decimal(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchTeamReviewQualityVarianceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_digest", None)
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return _json_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    values = dict(payload)
    values.pop("public_digest", None)
    return _json_digest(values)


def _json_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    if public_digest != _payload_digest(payload):
        raise ValueError("public_digest must match payload fields")


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return format(value.quantize(_QUANT), "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if _contains_unsafe_public_term(key_text):
                raise ValueError(f"unsafe public payload key in {label}: {key_text}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    if _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value for {field_name}")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)
