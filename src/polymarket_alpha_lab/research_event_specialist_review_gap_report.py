"""Pure report-only aggregate event specialist review gap report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_SPECIALIST_REVIEW_GAP_CONFIG_VERSION = (
    "research-event-specialist-review-gap-report-v1"
)

SPECIALIST_REVIEW_LANES = (
    "domain",
    "rules",
    "evidence",
    "probability",
    "resolution",
)
STATUSES = ("pass", "watch", "block")

_PASS = "pass"
_WATCH = "watch"
_BLOCK = "block"
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HALF = Decimal("0.500000")
_DAY_SECONDS = Decimal("86400.000000")
_PUBLIC_LABEL_RE = re.compile(r"^[a-z][a-z0-9-]{1,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_STATUS_SORT = {
    _BLOCK: Decimal("0.000000"),
    _WATCH: Decimal("1.000000"),
    _PASS: Decimal("2.000000"),
}
_LANE_RANK = {
    lane: Decimal(index).quantize(_QUANT)
    for index, lane in enumerate(SPECIALIST_REVIEW_LANES)
}
_ROW_REASON_SEQUENCE = (
    "specialist_lane_missing_block",
    "review_age_block",
    "dissent_pressure_block",
    "evidence_coverage_block",
    "manual_escalation_block",
    "specialist_lane_missing_watch",
    "review_age_watch",
    "dissent_pressure_watch",
    "evidence_coverage_watch",
    "manual_escalation_watch",
    "specialist_review_gap_clear",
)
_EMPTY_REASON_CODE = "specialist_review_gap_empty"
_REASON_CODE_RANK = {
    code: Decimal(index).quantize(_QUANT)
    for index, code in enumerate((*_ROW_REASON_SEQUENCE, _EMPTY_REASON_CODE))
}
_UNSAFE_PUBLIC_TERMS = tuple(
    "".join(parts)
    for parts in (
        ("raw",),
        ("candidate",),
        ("market",),
        ("slug",),
        ("question",),
        ("url",),
        ("text",),
        ("source",),
        ("dsn",),
        ("table",),
        ("database",),
        ("net", "work"),
        ("au", "th"),
        ("secret",),
        ("token",),
        ("private",),
        ("key",),
        ("wal", "let"),
        ("or", "der"),
        ("li", "ve"),
        ("trad", "e"),
        ("trad", "ing"),
        ("position",),
        ("b", "uy"),
        ("s", "ell"),
        ("reco", "mmendation"),
        ("siz", "ing"),
    )
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
class ResearchEventSpecialistReviewGapConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_EVENT_SPECIALIST_REVIEW_GAP_CONFIG_VERSION
    missing_lane_watch_count: Decimal = Decimal("1.000000")
    missing_lane_block_count: Decimal = Decimal("3.000000")
    review_age_watch_seconds: Decimal = _DAY_SECONDS
    review_age_block_seconds: Decimal = Decimal("172800.000000")
    dissent_watch_count: Decimal = Decimal("1.000000")
    dissent_block_count: Decimal = Decimal("3.000000")
    evidence_coverage_watch_floor: Decimal = Decimal("0.800000")
    evidence_coverage_block_floor: Decimal = Decimal("0.500000")
    manual_escalation_watch_threshold: Decimal = Decimal("0.400000")
    manual_escalation_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSpecialistReviewGapConfig, "config")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SPECIALIST_REVIEW_GAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "missing_lane_watch_count",
            "missing_lane_block_count",
            "dissent_watch_count",
            "dissent_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_age_watch_seconds",
            "review_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_coverage_watch_floor",
            "evidence_coverage_block_floor",
            "manual_escalation_watch_threshold",
            "manual_escalation_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSpecialistReviewGapObservation(_FinalPublicDataclass):
    event_bucket: str
    completed_specialist_lanes: tuple[str, ...]
    reviewed_at: datetime
    dissenting_specialist_count: Decimal
    evidence_coverage_ratio: Decimal
    manual_escalation_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventSpecialistReviewGapObservation,
            "observation",
        )
        _require_public_aggregate_label("event_bucket", self.event_bucket)
        object.__setattr__(
            self,
            "completed_specialist_lanes",
            _normalize_completed_lanes(self.completed_specialist_lanes),
        )
        object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        object.__setattr__(
            self,
            "dissenting_specialist_count",
            _normalize_count(
                "dissenting_specialist_count",
                self.dissenting_specialist_count,
            ),
        )
        object.__setattr__(
            self,
            "evidence_coverage_ratio",
            _normalize_ratio("evidence_coverage_ratio", self.evidence_coverage_ratio),
        )
        object.__setattr__(
            self,
            "manual_escalation_score",
            _normalize_ratio("manual_escalation_score", self.manual_escalation_score),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSpecialistReviewGapRow(_FinalPublicDataclass):
    event_bucket: str
    completed_specialist_lane_count: Decimal
    missing_specialist_lane_count: Decimal
    missing_specialist_lanes: tuple[str, ...]
    review_age_seconds: Decimal
    dissenting_specialist_count: Decimal
    evidence_coverage_ratio: Decimal
    manual_escalation_score: Decimal
    lane_gap_pressure: Decimal
    review_age_pressure: Decimal
    dissent_pressure: Decimal
    evidence_gap_pressure: Decimal
    manual_escalation_pressure: Decimal
    gap_pressure_score: Decimal
    status: str
    manual_escalation_urgency: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSpecialistReviewGapRow, "row")
        _require_public_aggregate_label("event_bucket", self.event_bucket)
        for field_name in (
            "completed_specialist_lane_count",
            "missing_specialist_lane_count",
            "dissenting_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_specialist_lanes",
            _normalize_missing_lanes(self.missing_specialist_lanes),
        )
        object.__setattr__(
            self,
            "review_age_seconds",
            _normalize_nonnegative_decimal("review_age_seconds", self.review_age_seconds),
        )
        for field_name in (
            "evidence_coverage_ratio",
            "manual_escalation_score",
            "lane_gap_pressure",
            "review_age_pressure",
            "dissent_pressure",
            "evidence_gap_pressure",
            "manual_escalation_pressure",
            "gap_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_status("manual_escalation_urgency", self.manual_escalation_urgency)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventSpecialistReviewGapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    event_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_specialist_lane_count: Decimal
    stale_review_count: Decimal
    dissent_pressure_count: Decimal
    evidence_coverage_gap_count: Decimal
    manual_escalation_count: Decimal
    max_review_age_seconds: Decimal
    total_dissenting_specialist_count: Decimal
    min_evidence_coverage_ratio: Decimal
    max_manual_escalation_score: Decimal
    average_gap_pressure_score: Decimal
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchEventSpecialistReviewGapRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSpecialistReviewGapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SPECIALIST_REVIEW_GAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        _require_status("status", self.status)
        for field_name in (
            "event_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_specialist_lane_count",
            "stale_review_count",
            "dissent_pressure_count",
            "evidence_coverage_gap_count",
            "manual_escalation_count",
            "total_dissenting_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_review_age_seconds",
            _normalize_nonnegative_decimal(
                "max_review_age_seconds",
                self.max_review_age_seconds,
            ),
        )
        for field_name in (
            "min_evidence_coverage_ratio",
            "max_manual_escalation_score",
            "average_gap_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_event_specialist_review_gap_report(
    observations: Iterable[ResearchEventSpecialistReviewGapObservation],
    *,
    config: ResearchEventSpecialistReviewGapConfig,
    generated_at: datetime,
) -> ResearchEventSpecialistReviewGapReport:
    _require_exact_type(config, ResearchEventSpecialistReviewGapConfig, "config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _validate_observation_times(normalized, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    _reject_duplicate_rows(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_bucket_count": _count(len(rows)),
        "pass_count": _status_count(rows, _PASS),
        "watch_count": _status_count(rows, _WATCH),
        "block_count": _status_count(rows, _BLOCK),
        "missing_specialist_lane_count": _sum_decimals(
            tuple(row.missing_specialist_lane_count for row in rows),
        ),
        "stale_review_count": _count(
            sum(
                1
                for row in rows
                if any(
                    code in row.reason_codes
                    for code in ("review_age_watch", "review_age_block")
                )
            ),
        ),
        "dissent_pressure_count": _count(
            sum(
                1
                for row in rows
                if any(
                    code in row.reason_codes
                    for code in ("dissent_pressure_watch", "dissent_pressure_block")
                )
            ),
        ),
        "evidence_coverage_gap_count": _count(
            sum(
                1
                for row in rows
                if any(
                    code in row.reason_codes
                    for code in ("evidence_coverage_watch", "evidence_coverage_block")
                )
            ),
        ),
        "manual_escalation_count": _count(
            sum(
                1
                for row in rows
                if any(
                    code in row.reason_codes
                    for code in ("manual_escalation_watch", "manual_escalation_block")
                )
            ),
        ),
        "max_review_age_seconds": _max_decimal(
            tuple(row.review_age_seconds for row in rows),
        ),
        "total_dissenting_specialist_count": _sum_decimals(
            tuple(row.dissenting_specialist_count for row in rows),
        ),
        "min_evidence_coverage_ratio": _min_ratio(
            tuple(row.evidence_coverage_ratio for row in rows),
        ),
        "max_manual_escalation_score": _max_ratio(
            tuple(row.manual_escalation_score for row in rows),
        ),
        "average_gap_pressure_score": _average(
            tuple(row.gap_pressure_score for row in rows),
        ),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventSpecialistReviewGapReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_specialist_review_gap_report_payload(
    report: ResearchEventSpecialistReviewGapReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchEventSpecialistReviewGapReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        expected_digest = _digest_from_payload(payload)
        if payload["derived_validation_digest"] != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    if isinstance(report, Mapping):
        _reject_public_numeric_scalars("report payload", report)
        _reject_unsafe_public_payload(
            "report payload",
            report,
            allow_json_containers=True,
        )
        _require_hard_flags("report payload", _MappingFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        if "derived_validation_digest" not in payload:
            raise ValueError("derived_validation_digest is required")
        if payload["derived_validation_digest"] != _digest_from_payload(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchEventSpecialistReviewGapReport")


def research_event_specialist_review_gap_report_digest(
    report: ResearchEventSpecialistReviewGapReport | Mapping[str, object],
) -> str:
    payload = research_event_specialist_review_gap_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_event_specialist_review_gap_report_payload(
    payload: Mapping[str, object],
) -> bool:
    research_event_specialist_review_gap_report_payload(payload)
    return True


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_observation(
    observation: ResearchEventSpecialistReviewGapObservation,
    *,
    config: ResearchEventSpecialistReviewGapConfig,
    generated_at: datetime,
) -> ResearchEventSpecialistReviewGapRow:
    _require_exact_type(
        observation,
        ResearchEventSpecialistReviewGapObservation,
        "observation",
    )
    missing_lanes = tuple(
        lane for lane in SPECIALIST_REVIEW_LANES if lane not in observation.completed_specialist_lanes
    )
    missing_lane_count = _count(len(missing_lanes))
    completed_lane_count = _count(len(observation.completed_specialist_lanes))
    review_age_seconds = _age_seconds(generated_at, observation.reviewed_at)
    lane_gap_pressure = _lane_gap_pressure(missing_lane_count, config)
    review_age_pressure = _safe_pressure_ratio(
        review_age_seconds,
        config.review_age_block_seconds,
    )
    dissent_pressure = _safe_pressure_ratio(
        observation.dissenting_specialist_count,
        config.dissent_block_count,
    )
    evidence_gap_pressure = _clamp_ratio(_ONE - observation.evidence_coverage_ratio)
    manual_escalation_pressure = observation.manual_escalation_score
    reason_codes = _row_reason_codes(
        missing_lane_count=missing_lane_count,
        review_age_seconds=review_age_seconds,
        dissenting_specialist_count=observation.dissenting_specialist_count,
        evidence_coverage_ratio=observation.evidence_coverage_ratio,
        manual_escalation_score=observation.manual_escalation_score,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchEventSpecialistReviewGapRow(
        event_bucket=observation.event_bucket,
        completed_specialist_lane_count=completed_lane_count,
        missing_specialist_lane_count=missing_lane_count,
        missing_specialist_lanes=missing_lanes,
        review_age_seconds=review_age_seconds,
        dissenting_specialist_count=observation.dissenting_specialist_count,
        evidence_coverage_ratio=observation.evidence_coverage_ratio,
        manual_escalation_score=observation.manual_escalation_score,
        lane_gap_pressure=lane_gap_pressure,
        review_age_pressure=review_age_pressure,
        dissent_pressure=dissent_pressure,
        evidence_gap_pressure=evidence_gap_pressure,
        manual_escalation_pressure=manual_escalation_pressure,
        gap_pressure_score=_average(
            (
                lane_gap_pressure,
                review_age_pressure,
                dissent_pressure,
                evidence_gap_pressure,
                manual_escalation_pressure,
            ),
        ),
        status=status,
        manual_escalation_urgency=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_lane_count: Decimal,
    review_age_seconds: Decimal,
    dissenting_specialist_count: Decimal,
    evidence_coverage_ratio: Decimal,
    manual_escalation_score: Decimal,
    config: ResearchEventSpecialistReviewGapConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_lane_count >= config.missing_lane_block_count:
        codes.append("specialist_lane_missing_block")
    elif missing_lane_count >= config.missing_lane_watch_count:
        codes.append("specialist_lane_missing_watch")
    if review_age_seconds >= config.review_age_block_seconds:
        codes.append("review_age_block")
    elif review_age_seconds >= config.review_age_watch_seconds:
        codes.append("review_age_watch")
    if dissenting_specialist_count >= config.dissent_block_count:
        codes.append("dissent_pressure_block")
    elif dissenting_specialist_count >= config.dissent_watch_count:
        codes.append("dissent_pressure_watch")
    if evidence_coverage_ratio <= config.evidence_coverage_block_floor:
        codes.append("evidence_coverage_block")
    elif evidence_coverage_ratio < config.evidence_coverage_watch_floor:
        codes.append("evidence_coverage_watch")
    if manual_escalation_score >= config.manual_escalation_block_threshold:
        codes.append("manual_escalation_block")
    elif manual_escalation_score >= config.manual_escalation_watch_threshold:
        codes.append("manual_escalation_watch")
    if not codes:
        return ("specialist_review_gap_clear",)
    selected = set(codes)
    return tuple(code for code in _ROW_REASON_SEQUENCE if code in selected)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return _BLOCK
    if any(code.endswith("_watch") for code in reason_codes):
        return _WATCH
    return _PASS


def _row_sort_key(row: ResearchEventSpecialistReviewGapRow) -> tuple[Decimal, str]:
    return (_STATUS_SORT[row.status], row.event_bucket)


def _report_status(rows: tuple[ResearchEventSpecialistReviewGapRow, ...]) -> str:
    if any(row.status == _BLOCK for row in rows):
        return _BLOCK
    if any(row.status == _WATCH for row in rows):
        return _WATCH
    return _PASS


def _reason_code_counts(
    rows: tuple[ResearchEventSpecialistReviewGapRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return ((_EMPTY_REASON_CODE, _count(1)),)
    counts: Counter[str] = Counter(
        code for row in rows for code in row.reason_codes
    )
    return tuple(
        (code, _count(counts[code]))
        for code in _ROW_REASON_SEQUENCE
        if counts[code] > 0
    )


def _validate_config(config: ResearchEventSpecialistReviewGapConfig) -> None:
    for watch_field, block_field in (
        ("missing_lane_watch_count", "missing_lane_block_count"),
        ("review_age_watch_seconds", "review_age_block_seconds"),
        ("dissent_watch_count", "dissent_block_count"),
        ("manual_escalation_watch_threshold", "manual_escalation_block_threshold"),
    ):
        if getattr(config, block_field) <= getattr(config, watch_field):
            raise ValueError(f"{block_field} must exceed {watch_field}")
    if config.evidence_coverage_block_floor >= config.evidence_coverage_watch_floor:
        raise ValueError(
            "evidence_coverage_watch_floor must exceed evidence_coverage_block_floor",
        )


def _validate_observation_times(
    observations: tuple[ResearchEventSpecialistReviewGapObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not exceed generated_at")


def _validate_row(row: ResearchEventSpecialistReviewGapRow) -> None:
    if row.completed_specialist_lane_count + row.missing_specialist_lane_count != _count(
        len(SPECIALIST_REVIEW_LANES),
    ):
        raise ValueError("specialist lane counts must match configured lanes")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_escalation_urgency != row.status:
        raise ValueError("manual_escalation_urgency must match status")


def _validate_report(report: ResearchEventSpecialistReviewGapReport) -> None:
    rows = report.rows
    if report.event_bucket_count != _count(len(rows)):
        raise ValueError("event_bucket_count must match rows")
    if report.pass_count != _status_count(rows, _PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, _WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, _BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.missing_specialist_lane_count != _sum_decimals(
        tuple(row.missing_specialist_lane_count for row in rows),
    ):
        raise ValueError("missing_specialist_lane_count must match rows")
    if report.stale_review_count != _reason_row_count(
        rows,
        ("review_age_watch", "review_age_block"),
    ):
        raise ValueError("stale_review_count must match rows")
    if report.dissent_pressure_count != _reason_row_count(
        rows,
        ("dissent_pressure_watch", "dissent_pressure_block"),
    ):
        raise ValueError("dissent_pressure_count must match rows")
    if report.evidence_coverage_gap_count != _reason_row_count(
        rows,
        ("evidence_coverage_watch", "evidence_coverage_block"),
    ):
        raise ValueError("evidence_coverage_gap_count must match rows")
    if report.manual_escalation_count != _reason_row_count(
        rows,
        ("manual_escalation_watch", "manual_escalation_block"),
    ):
        raise ValueError("manual_escalation_count must match rows")
    if report.max_review_age_seconds != _max_decimal(
        tuple(row.review_age_seconds for row in rows),
    ):
        raise ValueError("max_review_age_seconds must match rows")
    if report.total_dissenting_specialist_count != _sum_decimals(
        tuple(row.dissenting_specialist_count for row in rows),
    ):
        raise ValueError("total_dissenting_specialist_count must match rows")
    if report.min_evidence_coverage_ratio != _min_ratio(
        tuple(row.evidence_coverage_ratio for row in rows),
    ):
        raise ValueError("min_evidence_coverage_ratio must match rows")
    if report.max_manual_escalation_score != _max_ratio(
        tuple(row.manual_escalation_score for row in rows),
    ):
        raise ValueError("max_manual_escalation_score must match rows")
    if report.average_gap_pressure_score != _average(
        tuple(row.gap_pressure_score for row in rows),
    ):
        raise ValueError("average_gap_pressure_score must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _reason_row_count(
    rows: tuple[ResearchEventSpecialistReviewGapRow, ...],
    codes: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(code in row.reason_codes for code in codes)))


def _normalize_observations(
    observations: Iterable[ResearchEventSpecialistReviewGapObservation],
) -> tuple[ResearchEventSpecialistReviewGapObservation, ...]:
    if isinstance(observations, str | bytes):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in items:
        _require_exact_type(
            observation,
            ResearchEventSpecialistReviewGapObservation,
            "observation",
        )
        _require_hard_flags("observation", observation)
    return items


def _normalize_rows(
    rows: Iterable[ResearchEventSpecialistReviewGapRow],
) -> tuple[ResearchEventSpecialistReviewGapRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        _require_exact_type(row, ResearchEventSpecialistReviewGapRow, "row")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    return tuple(sorted(items, key=_row_sort_key))


def _normalize_completed_lanes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("completed_specialist_lanes must be a tuple")
    seen: set[str] = set()
    for lane in value:
        if lane not in _LANE_RANK:
            raise ValueError("completed_specialist_lanes must contain supported lanes")
        if lane in seen:
            raise ValueError("completed_specialist_lanes must not contain duplicates")
        seen.add(lane)
    return tuple(lane for lane in SPECIALIST_REVIEW_LANES if lane in seen)


def _normalize_missing_lanes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("missing_specialist_lanes must be a tuple")
    seen: set[str] = set()
    for lane in value:
        if lane not in _LANE_RANK:
            raise ValueError("missing_specialist_lanes must contain supported lanes")
        if lane in seen:
            raise ValueError("missing_specialist_lanes must not contain duplicates")
        seen.add(lane)
    return tuple(lane for lane in SPECIALIST_REVIEW_LANES if lane in seen)


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        if item not in _REASON_CODE_RANK:
            raise ValueError(f"{field_name} contains unsupported reason code")
    return tuple(
        code for code in _ROW_REASON_SEQUENCE if code in set(value)
    ) or (_EMPTY_REASON_CODE,)


def _normalize_reason_code_counts(
    value: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code, count = item
        if reason_code not in _REASON_CODE_RANK:
            raise ValueError("reason_code_counts contains unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append((reason_code, _normalize_count("reason_code_count", count)))
    return tuple(sorted(normalized, key=lambda item: _REASON_CODE_RANK[item[0]]))


def _reject_duplicate_rows(
    rows: tuple[ResearchEventSpecialistReviewGapRow, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.event_bucket in seen:
            raise ValueError("duplicate event_bucket entries are not allowed")
        seen.add(row.event_bucket)


def _status_count(
    rows: tuple[ResearchEventSpecialistReviewGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = _ZERO
    for value in values:
        total = _normalize_nonnegative_decimal("sum", total + value)
    return total


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_nonnegative_decimal("max", max(values))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_ratio("max_ratio", max(values))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ONE
    return _normalize_ratio("min_ratio", min(values))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.prec = 64
        return _normalize_ratio("average", sum(values, _ZERO) / _count(len(values)))


def _age_seconds(generated_at: datetime, reviewed_at: datetime) -> Decimal:
    delta = generated_at - reviewed_at
    microseconds = (
        ((delta.days * 86400) + delta.seconds) * 1000000
    ) + delta.microseconds
    return _normalize_nonnegative_decimal(
        "review_age_seconds",
        Decimal(microseconds) / Decimal("1000000"),
    )


def _lane_gap_pressure(
    missing_lane_count: Decimal,
    config: ResearchEventSpecialistReviewGapConfig,
) -> Decimal:
    if missing_lane_count <= _ZERO:
        return _ZERO
    if missing_lane_count >= config.missing_lane_block_count:
        return _ONE
    return _HALF


def _safe_pressure_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ONE
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(value / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if value >= _ONE:
        return _ONE
    return _normalize_ratio("ratio", value)


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(_QUANT)


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be public canonical text")
    if _contains_unsafe_public_term(value):
        raise ValueError(f"{field_name} must be public canonical text")


def _require_public_aggregate_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be public aggregate label")
    if _contains_unsafe_public_term(value):
        raise ValueError(f"{field_name} must be public aggregate label")


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value.quantize(_QUANT))
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    raise ValueError("report payload contains unsupported value")


def _iter_public_entries(value: object) -> Iterable[tuple[str, str]]:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield from _iter_public_entries({field.name: getattr(value, field.name)})
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield ("key", str(key))
            yield from _iter_public_entries(nested)
        return
    if isinstance(value, tuple | list):
        for item in value:
            yield from _iter_public_entries(item)
        return
    if type(value) is str:
        yield ("value", value)


def _reject_unsafe_public_payload(
    label: str,
    payload: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if allow_json_containers and type(payload) not in (dict, list, tuple):
        raise ValueError(f"unsafe public payload in {label}")
    for _kind, item in _iter_public_entries(payload):
        if _contains_unsafe_public_term(item):
            raise ValueError(f"unsafe public payload entry in {label}")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


def _reject_public_numeric_scalars(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"unsafe public payload numeric scalar in {label}")
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_public_numeric_scalars(label, nested)
        return
    if isinstance(value, tuple | list):
        for nested in value:
            _reject_public_numeric_scalars(label, nested)


def _report_values_without_digest(
    report: ResearchEventSpecialistReviewGapReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SPECIALIST_REVIEW_GAP_CONFIG_VERSION",
    "SPECIALIST_REVIEW_LANES",
    "STATUSES",
    "ResearchEventSpecialistReviewGapConfig",
    "ResearchEventSpecialistReviewGapObservation",
    "ResearchEventSpecialistReviewGapReport",
    "ResearchEventSpecialistReviewGapRow",
    "build_research_event_specialist_review_gap_report",
    "research_event_specialist_review_gap_report_digest",
    "research_event_specialist_review_gap_report_payload",
    "validate_research_event_specialist_review_gap_report_payload",
)
