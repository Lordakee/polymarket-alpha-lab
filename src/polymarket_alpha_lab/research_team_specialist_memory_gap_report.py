"""Pure public specialist memory gap report reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_GAP_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-gap-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
PUBLIC_STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

CLEAR_REASON = "specialist_memory_gap_clear"
NO_OBSERVATIONS_REASON = "specialist_memory_gap_no_observations"
DOMAIN_COVERAGE_WATCH_REASON = "domain_coverage_watch"
DOMAIN_COVERAGE_BLOCK_REASON = "domain_coverage_block"
STALE_MEMORY_WATCH_REASON = "stale_memory_watch"
STALE_MEMORY_BLOCK_REASON = "stale_memory_block"
CALIBRATION_DRIFT_WATCH_REASON = "calibration_drift_watch"
CALIBRATION_DRIFT_BLOCK_REASON = "calibration_drift_block"
SOURCE_COVERAGE_WATCH_REASON = "source_coverage_watch"
SOURCE_COVERAGE_BLOCK_REASON = "source_coverage_block"
REVIEW_CAPACITY_WATCH_REASON = "review_capacity_watch"
REVIEW_CAPACITY_BLOCK_REASON = "review_capacity_block"

ROW_REASON_CODE_SEQUENCE = (
    DOMAIN_COVERAGE_BLOCK_REASON,
    DOMAIN_COVERAGE_WATCH_REASON,
    STALE_MEMORY_BLOCK_REASON,
    STALE_MEMORY_WATCH_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    SOURCE_COVERAGE_BLOCK_REASON,
    SOURCE_COVERAGE_WATCH_REASON,
    REVIEW_CAPACITY_BLOCK_REASON,
    REVIEW_CAPACITY_WATCH_REASON,
    CLEAR_REASON,
)

REPORT_CLEAR_REASON = "specialist_memory_gap_report_clear"
REPORT_BLOCK_PRESENT_REASON = "specialist_memory_gap_block_present"
REPORT_WATCH_PRESENT_REASON = "specialist_memory_gap_watch_present"
REPORT_DOMAIN_COVERAGE_GAP_REASON = "domain_coverage_gap_present"
REPORT_STALE_MEMORY_GAP_REASON = "stale_memory_gap_present"
REPORT_CALIBRATION_DRIFT_GAP_REASON = "calibration_drift_gap_present"
REPORT_SOURCE_COVERAGE_GAP_REASON = "source_coverage_gap_present"
REPORT_REVIEW_CAPACITY_GAP_REASON = "review_capacity_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_DOMAIN_COVERAGE_GAP_REASON,
    REPORT_STALE_MEMORY_GAP_REASON,
    REPORT_CALIBRATION_DRIFT_GAP_REASON,
    REPORT_SOURCE_COVERAGE_GAP_REASON,
    REPORT_REVIEW_CAPACITY_GAP_REASON,
    REPORT_CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


PRIVATE_LABEL_FRAGMENTS = (
    _join_parts("ev", "ent", "_", "id"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "s", "lug"),
    _join_parts("sour", "ce", "_", "id"),
    _join_parts("raw", "_", "ev", "ent"),
    _join_parts("raw", "_", "mar", "ket"),
    _join_parts("raw", "_", "sour", "ce"),
    _join_parts("s", "lug"),
    _join_parts("u", "rl"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("to", "ken"),
    "secret",
    "private",
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_GAP_REPORT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamSpecialistMemoryGapConfig",
    "ResearchTeamSpecialistMemoryGapObservation",
    "ResearchTeamSpecialistMemoryGapReasonCodeCount",
    "ResearchTeamSpecialistMemoryGapReport",
    "ResearchTeamSpecialistMemoryGapRow",
    "build_research_team_specialist_memory_gap_report",
    "research_team_specialist_memory_gap_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryGapConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_GAP_REPORT_CONFIG_VERSION
    min_pass_domain_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_domain_coverage_ratio: Decimal = Decimal("0.600000")
    stale_memory_watch_age_seconds: Decimal = Decimal("2419200.000000")
    stale_memory_block_age_seconds: Decimal = Decimal("5184000.000000")
    calibration_watch_drift_score: Decimal = Decimal("0.080000")
    calibration_block_drift_score: Decimal = Decimal("0.150000")
    min_pass_source_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_source_coverage_ratio: Decimal = Decimal("0.500000")
    review_watch_utilization: Decimal = Decimal("0.850000")
    review_block_utilization: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryGapConfig:
            raise TypeError(
                "ResearchTeamSpecialistMemoryGapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryGapConfig:
            raise ValueError(
                "config must be exactly ResearchTeamSpecialistMemoryGapConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for name in (
            "min_pass_domain_coverage_ratio",
            "min_watch_domain_coverage_ratio",
            "calibration_watch_drift_score",
            "calibration_block_drift_score",
            "min_pass_source_coverage_ratio",
            "min_watch_source_coverage_ratio",
            "review_watch_utilization",
            "review_block_utilization",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        for name in ("stale_memory_watch_age_seconds", "stale_memory_block_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        if self.min_watch_domain_coverage_ratio > self.min_pass_domain_coverage_ratio:
            raise ValueError("min_watch_domain_coverage_ratio must not exceed pass")
        if self.stale_memory_block_age_seconds < self.stale_memory_watch_age_seconds:
            raise ValueError("stale_memory_block_age_seconds must meet watch")
        if self.calibration_block_drift_score < self.calibration_watch_drift_score:
            raise ValueError("calibration_block_drift_score must meet watch")
        if self.min_watch_source_coverage_ratio > self.min_pass_source_coverage_ratio:
            raise ValueError("min_watch_source_coverage_ratio must not exceed pass")
        if self.review_block_utilization < self.review_watch_utilization:
            raise ValueError("review_block_utilization must meet watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryGapObservation:
    domain_group: str
    specialist_group: str
    domain_memory_count: Decimal
    domain_target_count: Decimal
    stale_memory_age_seconds: Decimal
    calibration_drift_score: Decimal
    source_coverage_ratio: Decimal
    pending_review_count: Decimal
    review_capacity_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryGapObservation:
            raise TypeError(
                "ResearchTeamSpecialistMemoryGapObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryGapObservation:
            raise ValueError(
                "observation must be exactly ResearchTeamSpecialistMemoryGapObservation",
            )
        for name in ("domain_group", "specialist_group"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        for name in (
            "domain_memory_count",
            "stale_memory_age_seconds",
            "pending_review_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "domain_target_count",
            _require_positive_decimal("domain_target_count", self.domain_target_count),
        )
        for name in ("calibration_drift_score", "source_coverage_ratio"):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "review_capacity_count",
            _require_positive_decimal("review_capacity_count", self.review_capacity_count),
        )
        if self.domain_memory_count > self.domain_target_count:
            raise ValueError("domain_memory_count must not exceed domain_target_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryGapRow:
    domain_group: str
    specialist_group: str
    domain_memory_count: Decimal
    domain_target_count: Decimal
    domain_coverage_ratio: Decimal
    stale_memory_age_seconds: Decimal
    calibration_drift_score: Decimal
    source_coverage_ratio: Decimal
    pending_review_count: Decimal
    review_capacity_count: Decimal
    review_capacity_utilization: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryGapRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryGapRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryGapRow:
            raise ValueError("row must be exactly ResearchTeamSpecialistMemoryGapRow")
        for name in ("domain_group", "specialist_group"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        for name in (
            "domain_memory_count",
            "stale_memory_age_seconds",
            "pending_review_count",
            "review_capacity_utilization",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "domain_target_count",
            _require_positive_decimal("domain_target_count", self.domain_target_count),
        )
        object.__setattr__(
            self,
            "review_capacity_count",
            _require_positive_decimal("review_capacity_count", self.review_capacity_count),
        )
        for name in (
            "domain_coverage_ratio",
            "calibration_drift_score",
            "source_coverage_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "public_status",
            _require_status("public_status", self.public_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        if self.domain_memory_count > self.domain_target_count:
            raise ValueError("domain_memory_count must not exceed domain_target_count")
        if self.public_status != _status_from_reasons(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryGapReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryGapReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistMemoryGapReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryGapReasonCodeCount:
            raise ValueError(
                "reason count must be exactly ResearchTeamSpecialistMemoryGapReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryGapReport:
    generated_at: datetime
    config_version: str
    public_status: str
    observation_count: Decimal
    domain_group_count: Decimal
    specialist_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    domain_coverage_gap_count: Decimal
    stale_memory_gap_count: Decimal
    calibration_drift_gap_count: Decimal
    source_coverage_gap_count: Decimal
    review_capacity_gap_count: Decimal
    average_domain_coverage_ratio: Decimal
    max_stale_memory_age_seconds: Decimal
    max_calibration_drift_score: Decimal
    average_source_coverage_ratio: Decimal
    weighted_review_capacity_utilization: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistMemoryGapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryGapReport:
            raise TypeError(
                "ResearchTeamSpecialistMemoryGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryGapReport:
            raise ValueError("report must be exactly ResearchTeamSpecialistMemoryGapReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "public_status",
            _require_status("public_status", self.public_status),
        )
        for name in (
            "observation_count",
            "domain_group_count",
            "specialist_group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "domain_coverage_gap_count",
            "stale_memory_gap_count",
            "calibration_drift_gap_count",
            "source_coverage_gap_count",
            "review_capacity_gap_count",
            "max_stale_memory_age_seconds",
            "weighted_review_capacity_utilization",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "average_domain_coverage_ratio",
            "max_calibration_drift_score",
            "average_source_coverage_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        digest = _report_payload_digest(self)
        if self.payload_digest:
            _require_digest("payload_digest", self.payload_digest)
            if self.payload_digest != digest:
                raise ValueError("payload_digest must match report contents")
        object.__setattr__(self, "payload_digest", digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_specialist_memory_gap_report_payload(self)


def build_research_team_specialist_memory_gap_report(
    rows: Iterable[ResearchTeamSpecialistMemoryGapObservation],
    *,
    config: ResearchTeamSpecialistMemoryGapConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryGapReport:
    cfg = config or ResearchTeamSpecialistMemoryGapConfig()
    if type(cfg) is not ResearchTeamSpecialistMemoryGapConfig:
        raise ValueError("config must be exactly ResearchTeamSpecialistMemoryGapConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(rows)
    report_rows = tuple(
        sorted(
            (_build_row(row, config=cfg) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamSpecialistMemoryGapReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        public_status=_report_status(report_rows),
        observation_count=_count_decimal(len(input_rows)),
        domain_group_count=_count_decimal(len({row.domain_group for row in report_rows})),
        specialist_group_count=_count_decimal(
            len({(row.domain_group, row.specialist_group) for row in report_rows}),
        ),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        domain_coverage_gap_count=_reason_count_any(
            report_rows,
            (DOMAIN_COVERAGE_BLOCK_REASON, DOMAIN_COVERAGE_WATCH_REASON),
        ),
        stale_memory_gap_count=_reason_count_any(
            report_rows,
            (STALE_MEMORY_BLOCK_REASON, STALE_MEMORY_WATCH_REASON),
        ),
        calibration_drift_gap_count=_reason_count_any(
            report_rows,
            (CALIBRATION_DRIFT_BLOCK_REASON, CALIBRATION_DRIFT_WATCH_REASON),
        ),
        source_coverage_gap_count=_reason_count_any(
            report_rows,
            (SOURCE_COVERAGE_BLOCK_REASON, SOURCE_COVERAGE_WATCH_REASON),
        ),
        review_capacity_gap_count=_reason_count_any(
            report_rows,
            (REVIEW_CAPACITY_BLOCK_REASON, REVIEW_CAPACITY_WATCH_REASON),
        ),
        average_domain_coverage_ratio=_average_decimal(
            tuple(row.domain_coverage_ratio for row in report_rows),
        ),
        max_stale_memory_age_seconds=max(
            (row.stale_memory_age_seconds for row in report_rows),
            default=ZERO,
        ),
        max_calibration_drift_score=max(
            (row.calibration_drift_score for row in report_rows),
            default=ZERO,
        ),
        average_source_coverage_ratio=_average_decimal(
            tuple(row.source_coverage_ratio for row in report_rows),
        ),
        weighted_review_capacity_utilization=_weighted_review_capacity_utilization(
            report_rows,
        ),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows),
        reason_codes=_report_reasons(report_rows, len(input_rows)),
    )


def research_team_specialist_memory_gap_report_payload(
    report: ResearchTeamSpecialistMemoryGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSpecialistMemoryGapReport:
        raise ValueError("report must be exactly ResearchTeamSpecialistMemoryGapReport")
    payload = _json_ready(_report_payload_parts(report, include_digest=True))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _build_row(
    row: ResearchTeamSpecialistMemoryGapObservation,
    *,
    config: ResearchTeamSpecialistMemoryGapConfig,
) -> ResearchTeamSpecialistMemoryGapRow:
    domain_coverage_ratio = _safe_divide(row.domain_memory_count, row.domain_target_count)
    review_capacity_utilization = _safe_divide(
        row.pending_review_count,
        row.review_capacity_count,
    )
    reasons = _row_reasons(
        domain_coverage_ratio=domain_coverage_ratio,
        stale_memory_age_seconds=row.stale_memory_age_seconds,
        calibration_drift_score=row.calibration_drift_score,
        source_coverage_ratio=row.source_coverage_ratio,
        review_capacity_utilization=review_capacity_utilization,
        config=config,
    )
    return ResearchTeamSpecialistMemoryGapRow(
        domain_group=row.domain_group,
        specialist_group=row.specialist_group,
        domain_memory_count=row.domain_memory_count,
        domain_target_count=row.domain_target_count,
        domain_coverage_ratio=domain_coverage_ratio,
        stale_memory_age_seconds=row.stale_memory_age_seconds,
        calibration_drift_score=row.calibration_drift_score,
        source_coverage_ratio=row.source_coverage_ratio,
        pending_review_count=row.pending_review_count,
        review_capacity_count=row.review_capacity_count,
        review_capacity_utilization=review_capacity_utilization,
        public_status=_status_from_reasons(reasons),
        reason_codes=reasons,
    )


def _row_reasons(
    *,
    domain_coverage_ratio: Decimal,
    stale_memory_age_seconds: Decimal,
    calibration_drift_score: Decimal,
    source_coverage_ratio: Decimal,
    review_capacity_utilization: Decimal,
    config: ResearchTeamSpecialistMemoryGapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if domain_coverage_ratio < config.min_watch_domain_coverage_ratio:
        reasons.append(DOMAIN_COVERAGE_BLOCK_REASON)
    elif domain_coverage_ratio < config.min_pass_domain_coverage_ratio:
        reasons.append(DOMAIN_COVERAGE_WATCH_REASON)
    if stale_memory_age_seconds >= config.stale_memory_block_age_seconds:
        reasons.append(STALE_MEMORY_BLOCK_REASON)
    elif stale_memory_age_seconds >= config.stale_memory_watch_age_seconds:
        reasons.append(STALE_MEMORY_WATCH_REASON)
    if calibration_drift_score >= config.calibration_block_drift_score:
        reasons.append(CALIBRATION_DRIFT_BLOCK_REASON)
    elif calibration_drift_score >= config.calibration_watch_drift_score:
        reasons.append(CALIBRATION_DRIFT_WATCH_REASON)
    if source_coverage_ratio < config.min_watch_source_coverage_ratio:
        reasons.append(SOURCE_COVERAGE_BLOCK_REASON)
    elif source_coverage_ratio < config.min_pass_source_coverage_ratio:
        reasons.append(SOURCE_COVERAGE_WATCH_REASON)
    if review_capacity_utilization >= config.review_block_utilization:
        reasons.append(REVIEW_CAPACITY_BLOCK_REASON)
    elif review_capacity_utilization >= config.review_watch_utilization:
        reasons.append(REVIEW_CAPACITY_WATCH_REASON)
    return tuple(reasons) or (CLEAR_REASON,)


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason.endswith("_watch") for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...]) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reasons(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
    input_count: int,
) -> tuple[str, ...]:
    if input_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reasons: list[str] = []
    if any(row.public_status == STATUS_BLOCK for row in rows):
        reasons.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.public_status == STATUS_WATCH for row in rows):
        reasons.append(REPORT_WATCH_PRESENT_REASON)
    if _reason_count_any(rows, (DOMAIN_COVERAGE_BLOCK_REASON, DOMAIN_COVERAGE_WATCH_REASON)):
        reasons.append(REPORT_DOMAIN_COVERAGE_GAP_REASON)
    if _reason_count_any(rows, (STALE_MEMORY_BLOCK_REASON, STALE_MEMORY_WATCH_REASON)):
        reasons.append(REPORT_STALE_MEMORY_GAP_REASON)
    if _reason_count_any(
        rows,
        (CALIBRATION_DRIFT_BLOCK_REASON, CALIBRATION_DRIFT_WATCH_REASON),
    ):
        reasons.append(REPORT_CALIBRATION_DRIFT_GAP_REASON)
    if _reason_count_any(rows, (SOURCE_COVERAGE_BLOCK_REASON, SOURCE_COVERAGE_WATCH_REASON)):
        reasons.append(REPORT_SOURCE_COVERAGE_GAP_REASON)
    if _reason_count_any(rows, (REVIEW_CAPACITY_BLOCK_REASON, REVIEW_CAPACITY_WATCH_REASON)):
        reasons.append(REPORT_REVIEW_CAPACITY_GAP_REASON)
    return tuple(reasons) or (REPORT_CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryGapReasonCodeCount, ...]:
    row_total = _count_decimal(len(rows))
    counts: list[ResearchTeamSpecialistMemoryGapReasonCodeCount] = []
    for reason in ROW_REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason)
        if count > ZERO:
            counts.append(
                ResearchTeamSpecialistMemoryGapReasonCodeCount(
                    reason_code=reason,
                    count=count,
                    row_ratio=_safe_divide(count, row_total) if row_total > ZERO else ZERO,
                ),
            )
    return tuple(counts)


def _reason_count(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
    reason: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason in row.reason_codes))


def _reason_count_any(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)),
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _weighted_review_capacity_utilization(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
) -> Decimal:
    pending = _sum_decimal(row.pending_review_count for row in rows)
    capacity = _sum_decimal(row.review_capacity_count for row in rows)
    return _safe_divide(pending, capacity) if capacity > ZERO else ZERO


def _row_sort_key(row: ResearchTeamSpecialistMemoryGapRow) -> tuple[int, str, str]:
    return (
        PUBLIC_STATUS_SORT_SEQUENCE.index(row.public_status),
        row.domain_group,
        row.specialist_group,
    )


def _normalize_observations(
    rows: Iterable[ResearchTeamSpecialistMemoryGapObservation],
) -> tuple[ResearchTeamSpecialistMemoryGapObservation, ...]:
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistMemoryGapObservation:
            raise ValueError(
                "rows must contain exactly ResearchTeamSpecialistMemoryGapObservation",
            )
    keys = tuple((row.domain_group, row.specialist_group) for row in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("domain_group and specialist_group pairs must be unique")
    return normalized


def _require_rows(
    rows: tuple[ResearchTeamSpecialistMemoryGapRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryGapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryGapRow:
            raise ValueError("rows must contain exactly ResearchTeamSpecialistMemoryGapRow")
    return tuple(sorted(rows, key=_row_sort_key))


def _require_reason_counts(
    counts: tuple[ResearchTeamSpecialistMemoryGapReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryGapReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamSpecialistMemoryGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchTeamSpecialistMemoryGapReasonCodeCount",
            )
    return counts


def _validate_report(report: ResearchTeamSpecialistMemoryGapReport) -> None:
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _report_reasons(report.rows, int(report.observation_count)):
        raise ValueError("reason_codes must match rows")
    expected = {
        "observation_count": _count_decimal(len(report.rows)),
        "domain_group_count": _count_decimal(len({row.domain_group for row in report.rows})),
        "specialist_group_count": _count_decimal(
            len({(row.domain_group, row.specialist_group) for row in report.rows}),
        ),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
    }
    for name, value in expected.items():
        if getattr(report, name) != value:
            raise ValueError(f"{name} must match rows")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.microsecond != 0:
        raise ValueError(f"{name} must be a whole second")
    return value.astimezone(UTC)


def _require_public_label(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{name} must not have surrounding whitespace")
    if len(value) > 96:
        raise ValueError(f"{name} must be short")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(char not in allowed for char in value):
        raise ValueError(f"{name} must be a public-safe aggregate label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in PRIVATE_LABEL_FRAGMENTS):
        raise ValueError(f"{name} must be a public-safe aggregate label")
    return value


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{name} exceeds required decimal precision")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_status(name: str, value: str) -> str:
    return _require_member(name, value, PUBLIC_STATUSES)


def _require_member(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")
    return value


def _normalize_reasons(
    name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must be unique")
    for value in values:
        _require_member(name, value, allowed)
    return tuple(sorted(values, key=allowed.index))


def _require_hard_flags(label: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name) is not True:
            raise ValueError(f"{label} {name} must be True")


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    int(value, 16)
    return value


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(DECIMAL_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
        return total.quantize(DECIMAL_QUANTUM)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _safe_divide(_sum_decimal(values), _count_decimal(len(values)))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(DECIMAL_QUANTUM)


def _report_payload_parts(
    report: ResearchTeamSpecialistMemoryGapReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    parts = asdict(report)
    if not include_digest:
        parts.pop("payload_digest")
    return parts


def _report_payload_digest(report: ResearchTeamSpecialistMemoryGapReport) -> str:
    payload = _json_ready(_report_payload_parts(report, include_digest=False))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(value[key]) for key in sorted(value)}
    return value
