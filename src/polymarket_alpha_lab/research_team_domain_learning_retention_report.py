"""Pure report for domain-team learning retention over time."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_RETENTION_CONFIG_VERSION = (
    "research-team-domain-learning-retention-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_domain_learning_retention",
    STATUS_WATCH: "watch_report_only_domain_learning_retention",
    STATUS_BLOCK: "block_report_only_domain_learning_retention",
}

NO_INPUTS_REASON = "domain_learning_retention_no_inputs"
PASS_REASON = "domain_learning_retention_pass"
WATCH_REASON = "domain_learning_retention_watch"
BLOCK_REASON = "domain_learning_retention_block"
CALIBRATION_GAP_REASON = "domain_learning_retention_calibration_carryforward_gap"
CORRECTION_GAP_REASON = "domain_learning_retention_correction_follow_through_gap"
STALE_MEMORY_WATCH_REASON = "domain_learning_retention_stale_memory_watch"
STALE_MEMORY_BLOCK_REASON = "domain_learning_retention_stale_memory_block"
EVIDENCE_REUSE_GAP_REASON = "domain_learning_retention_evidence_reuse_gap"
PEER_REVIEW_GAP_REASON = "domain_learning_retention_peer_review_gap"
REVIEW_LATENCY_GAP_REASON = "domain_learning_retention_review_latency_gap"
REVIEW_LATENCY_BLOCK_REASON = "domain_learning_retention_review_latency_block"
REASON_CODES = tuple(
    sorted(
        (
            NO_INPUTS_REASON,
            PASS_REASON,
            WATCH_REASON,
            BLOCK_REASON,
            CALIBRATION_GAP_REASON,
            CORRECTION_GAP_REASON,
            STALE_MEMORY_WATCH_REASON,
            STALE_MEMORY_BLOCK_REASON,
            EVIDENCE_REUSE_GAP_REASON,
            PEER_REVIEW_GAP_REASON,
            REVIEW_LATENCY_GAP_REASON,
            REVIEW_LATENCY_BLOCK_REASON,
        ),
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX = Decimal("6.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class ResearchTeamDomainLearningRetentionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_RETENTION_CONFIG_VERSION
    )
    pass_retention_score: Decimal = Decimal("0.800000")
    watch_retention_score: Decimal = Decimal("0.600000")
    pass_dimension_score: Decimal = Decimal("0.800000")
    stale_memory_watch_penalty_score: Decimal = Decimal("0.250000")
    stale_memory_block_penalty_score: Decimal = Decimal("0.500000")
    pass_review_latency_seconds: Decimal = Decimal("7200.000000")
    block_review_latency_seconds: Decimal = Decimal("21600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainLearningRetentionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningRetentionConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_retention_score",
            "watch_retention_score",
            "pass_dimension_score",
            "stale_memory_watch_penalty_score",
            "stale_memory_block_penalty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_review_latency_seconds",
            "block_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_retention_score <= self.watch_retention_score:
            raise ValueError("pass_retention_score must exceed watch_retention_score")
        if self.stale_memory_block_penalty_score <= self.stale_memory_watch_penalty_score:
            raise ValueError(
                "stale_memory_block_penalty_score must exceed "
                "stale_memory_watch_penalty_score",
            )
        if self.block_review_latency_seconds <= self.pass_review_latency_seconds:
            raise ValueError(
                "block_review_latency_seconds must exceed pass_review_latency_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningRetentionInputRow:
    domain_team: str
    learning_window: str
    evaluated_at: datetime
    calibration_carryforward_score: Decimal
    correction_follow_through_score: Decimal
    stale_memory_penalty_score: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_coverage_score: Decimal
    review_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainLearningRetentionInputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningRetentionInputRow, "input row")
        for field_name in ("domain_team", "learning_window"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in (
            "calibration_carryforward_score",
            "correction_follow_through_score",
            "stale_memory_penalty_score",
            "evidence_reuse_quality_score",
            "peer_review_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_latency_seconds",
            _require_nonnegative_decimal(
                "review_latency_seconds",
                self.review_latency_seconds,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningRetentionReportRow:
    domain_team: str
    learning_window: str
    public_status: str
    evaluated_at: datetime
    calibration_carryforward_score: Decimal
    correction_follow_through_score: Decimal
    stale_memory_penalty_score: Decimal
    stale_memory_retention_score: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_coverage_score: Decimal
    review_latency_seconds: Decimal
    review_latency_score: Decimal
    retention_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainLearningRetentionReportRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningRetentionReportRow, "row")
        for field_name in ("domain_team", "learning_window"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        _require_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in (
            "calibration_carryforward_score",
            "correction_follow_through_score",
            "stale_memory_penalty_score",
            "stale_memory_retention_score",
            "evidence_reuse_quality_score",
            "peer_review_coverage_score",
            "review_latency_score",
            "retention_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_latency_seconds",
            _require_nonnegative_decimal(
                "review_latency_seconds",
                self.review_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningRetentionReasonCodeCount:
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainLearningRetentionReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainLearningRetentionReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningRetentionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    learning_retention_gate_label: str
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_retention_score: Decimal
    average_calibration_carryforward_score: Decimal
    average_correction_follow_through_score: Decimal
    average_stale_memory_retention_score: Decimal
    average_evidence_reuse_quality_score: Decimal
    average_peer_review_coverage_score: Decimal
    average_review_latency_score: Decimal
    max_review_latency_seconds: Decimal
    stale_memory_penalty_count: Decimal
    peer_review_gap_count: Decimal
    review_latency_gap_count: Decimal
    rows: tuple[ResearchTeamDomainLearningRetentionReportRow, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainLearningRetentionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainLearningRetentionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningRetentionReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        if self.learning_retention_gate_label != NEXT_STEPS[self.report_status]:
            raise ValueError("learning_retention_gate_label must match report_status")
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_penalty_count",
            "peer_review_gap_count",
            "review_latency_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_review_latency_seconds",
            _require_nonnegative_decimal(
                "max_review_latency_seconds",
                self.max_review_latency_seconds,
            ),
        )
        for field_name in (
            "average_retention_score",
            "average_calibration_carryforward_score",
            "average_correction_follow_through_score",
            "average_stale_memory_retention_score",
            "average_evidence_reuse_quality_score",
            "average_peer_review_coverage_score",
            "average_review_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(_payload_value(self, include_digest=True))
        expected_digest = _report_digest_from_payload(self, include_digest=False)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_learning_retention_report_payload(self)


def build_research_team_domain_learning_retention_report(
    rows: tuple[ResearchTeamDomainLearningRetentionInputRow, ...],
    *,
    config: ResearchTeamDomainLearningRetentionConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamDomainLearningRetentionReport:
    cfg = config or ResearchTeamDomainLearningRetentionConfig()
    if type(cfg) is not ResearchTeamDomainLearningRetentionConfig:
        raise TypeError(
            "config must be exactly ResearchTeamDomainLearningRetentionConfig",
        )
    cfg = ResearchTeamDomainLearningRetentionConfig(**_field_values(cfg))
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    if not input_rows:
        reason_counts = (
            ResearchTeamDomainLearningRetentionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_ratio=ZERO,
            ),
        )
        return _make_report(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            report_status=STATUS_BLOCK,
            learning_retention_gate_label=NEXT_STEPS[STATUS_BLOCK],
            domain_team_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            average_retention_score=ZERO,
            average_calibration_carryforward_score=ZERO,
            average_correction_follow_through_score=ZERO,
            average_stale_memory_retention_score=ZERO,
            average_evidence_reuse_quality_score=ZERO,
            average_peer_review_coverage_score=ZERO,
            average_review_latency_score=ZERO,
            max_review_latency_seconds=ZERO,
            stale_memory_penalty_count=ZERO,
            peer_review_gap_count=ZERO,
            review_latency_gap_count=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        sorted(
            (
                _report_row(row, config=cfg, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=lambda row: (
                STATUS_RANK[row.public_status],
                row.domain_team,
                row.learning_window,
            ),
        ),
    )
    reason_counts = _reason_code_counts(report_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    status = _summary_status(report_rows)
    return _make_report(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=status,
        learning_retention_gate_label=NEXT_STEPS[status],
        domain_team_count=_count_decimal(report_rows),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        average_retention_score=_average(row.retention_score for row in report_rows),
        average_calibration_carryforward_score=_average(
            row.calibration_carryforward_score for row in report_rows
        ),
        average_correction_follow_through_score=_average(
            row.correction_follow_through_score for row in report_rows
        ),
        average_stale_memory_retention_score=_average(
            row.stale_memory_retention_score for row in report_rows
        ),
        average_evidence_reuse_quality_score=_average(
            row.evidence_reuse_quality_score for row in report_rows
        ),
        average_peer_review_coverage_score=_average(
            row.peer_review_coverage_score for row in report_rows
        ),
        average_review_latency_score=_average(
            row.review_latency_score for row in report_rows
        ),
        max_review_latency_seconds=max(row.review_latency_seconds for row in report_rows),
        stale_memory_penalty_count=_count_if(
            report_rows,
            lambda row: row.stale_memory_penalty_score
            >= cfg.stale_memory_watch_penalty_score,
        ),
        peer_review_gap_count=_count_if(
            report_rows,
            lambda row: row.peer_review_coverage_score < cfg.pass_dimension_score,
        ),
        review_latency_gap_count=_count_if(
            report_rows,
            lambda row: row.review_latency_seconds > cfg.pass_review_latency_seconds,
        ),
        rows=report_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_team_domain_learning_retention_report_payload(
    report: ResearchTeamDomainLearningRetentionReport,
) -> dict[str, Any]:
    _validate_public_report(report)
    payload = _payload_value(report, include_digest=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def research_team_domain_learning_retention_report_digest(
    report: ResearchTeamDomainLearningRetentionReport,
) -> str:
    return _validate_public_report(report)


def _make_report(**values: Any) -> ResearchTeamDomainLearningRetentionReport:
    digest_values = {
        **values,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _report_digest_from_mapping(digest_values)
    return ResearchTeamDomainLearningRetentionReport(
        **values,
        derived_validation_digest=digest,
    )


def _report_row(
    row: ResearchTeamDomainLearningRetentionInputRow,
    *,
    config: ResearchTeamDomainLearningRetentionConfig,
    generated_at: datetime,
) -> ResearchTeamDomainLearningRetentionReportRow:
    if row.evaluated_at > generated_at:
        raise ValueError("evaluated_at must not be after generated_at")
    stale_memory_retention_score = ONE - row.stale_memory_penalty_score
    review_latency_score = _review_latency_score(row.review_latency_seconds, config)
    retention_score = _average(
        (
            row.calibration_carryforward_score,
            row.correction_follow_through_score,
            stale_memory_retention_score,
            row.evidence_reuse_quality_score,
            row.peer_review_coverage_score,
            review_latency_score,
        ),
    )
    reason_codes = _row_reason_codes(
        row=row,
        config=config,
        retention_score=retention_score,
    )
    status = _row_status(
        retention_score=retention_score,
        reason_codes=reason_codes,
        config=config,
    )
    return ResearchTeamDomainLearningRetentionReportRow(
        domain_team=row.domain_team,
        learning_window=row.learning_window,
        public_status=status,
        evaluated_at=row.evaluated_at,
        calibration_carryforward_score=row.calibration_carryforward_score,
        correction_follow_through_score=row.correction_follow_through_score,
        stale_memory_penalty_score=row.stale_memory_penalty_score,
        stale_memory_retention_score=_decimal(stale_memory_retention_score),
        evidence_reuse_quality_score=row.evidence_reuse_quality_score,
        peer_review_coverage_score=row.peer_review_coverage_score,
        review_latency_seconds=row.review_latency_seconds,
        review_latency_score=review_latency_score,
        retention_score=retention_score,
        reason_codes=_status_reason_codes(status, reason_codes),
    )


def _review_latency_score(
    review_latency_seconds: Decimal,
    config: ResearchTeamDomainLearningRetentionConfig,
) -> Decimal:
    if review_latency_seconds <= config.pass_review_latency_seconds:
        return ONE
    if review_latency_seconds >= config.block_review_latency_seconds:
        return ZERO
    numerator = review_latency_seconds - config.pass_review_latency_seconds
    denominator = config.block_review_latency_seconds - config.pass_review_latency_seconds
    return _decimal(ONE - _ratio(numerator, denominator))


def _row_reason_codes(
    *,
    row: ResearchTeamDomainLearningRetentionInputRow,
    config: ResearchTeamDomainLearningRetentionConfig,
    retention_score: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if row.calibration_carryforward_score < config.pass_dimension_score:
        reasons.add(CALIBRATION_GAP_REASON)
    if row.correction_follow_through_score < config.pass_dimension_score:
        reasons.add(CORRECTION_GAP_REASON)
    if row.evidence_reuse_quality_score < config.pass_dimension_score:
        reasons.add(EVIDENCE_REUSE_GAP_REASON)
    if row.peer_review_coverage_score < config.pass_dimension_score:
        reasons.add(PEER_REVIEW_GAP_REASON)
    if row.stale_memory_penalty_score >= config.stale_memory_block_penalty_score:
        reasons.add(STALE_MEMORY_BLOCK_REASON)
    elif row.stale_memory_penalty_score >= config.stale_memory_watch_penalty_score:
        reasons.add(STALE_MEMORY_WATCH_REASON)
    if row.review_latency_seconds >= config.block_review_latency_seconds:
        reasons.add(REVIEW_LATENCY_BLOCK_REASON)
    elif row.review_latency_seconds > config.pass_review_latency_seconds:
        reasons.add(REVIEW_LATENCY_GAP_REASON)
    if retention_score < config.watch_retention_score:
        reasons.add(BLOCK_REASON)
    elif retention_score < config.pass_retention_score or reasons:
        reasons.add(WATCH_REASON)
    else:
        reasons.add(PASS_REASON)
    return _normalize_reason_codes(tuple(sorted(reasons)))


def _row_status(
    *,
    retention_score: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchTeamDomainLearningRetentionConfig,
) -> str:
    if (
        BLOCK_REASON in reason_codes
        or STALE_MEMORY_BLOCK_REASON in reason_codes
        or REVIEW_LATENCY_BLOCK_REASON in reason_codes
        or retention_score < config.watch_retention_score
    ):
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes or retention_score < config.pass_retention_score:
        return STATUS_WATCH
    return STATUS_PASS


def _status_reason_codes(
    status: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons = set(reason_codes)
    if status == STATUS_BLOCK:
        reasons.discard(WATCH_REASON)
        reasons.add(BLOCK_REASON)
    elif status == STATUS_WATCH:
        reasons.add(WATCH_REASON)
    else:
        reasons = {PASS_REASON}
    return _normalize_reason_codes(tuple(sorted(reasons)))


def _summary_status(
    rows: tuple[ResearchTeamDomainLearningRetentionReportRow, ...],
) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainLearningRetentionReportRow, ...],
) -> tuple[ResearchTeamDomainLearningRetentionReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    team_count = _count_decimal(rows)
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchTeamDomainLearningRetentionReasonCodeCount(
            reason_code=reason_code,
            count=count,
            team_ratio=_ratio(count, team_count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_input_rows(
    rows: tuple[ResearchTeamDomainLearningRetentionInputRow, ...],
) -> tuple[ResearchTeamDomainLearningRetentionInputRow, ...]:
    if type(rows) is not tuple:
        raise TypeError("rows must be a tuple")
    normalized: list[ResearchTeamDomainLearningRetentionInputRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainLearningRetentionInputRow:
            raise TypeError(
                "rows must contain exactly ResearchTeamDomainLearningRetentionInputRow",
            )
        row = ResearchTeamDomainLearningRetentionInputRow(**_field_values(row))
        key = (row.domain_team, row.learning_window)
        if key in seen_keys:
            raise ValueError("domain_team and learning_window must be unique")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamDomainLearningRetentionReportRow, ...]:
    if type(rows) not in (tuple, list):
        raise TypeError("rows must be a tuple")
    normalized: list[ResearchTeamDomainLearningRetentionReportRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is dict:
            row = ResearchTeamDomainLearningRetentionReportRow(**row)
        elif type(row) is ResearchTeamDomainLearningRetentionReportRow:
            row = ResearchTeamDomainLearningRetentionReportRow(**_field_values(row))
        else:
            raise TypeError(
                "rows must contain exactly ResearchTeamDomainLearningRetentionReportRow",
            )
        key = (row.domain_team, row.learning_window)
        if key in seen_keys:
            raise ValueError("domain_team and learning_window must be unique")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                STATUS_RANK[row.public_status],
                row.domain_team,
                row.learning_window,
            ),
        ),
    )


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchTeamDomainLearningRetentionReasonCodeCount, ...]:
    if type(reason_code_counts) not in (tuple, list):
        raise TypeError("reason_code_counts must be a tuple")
    normalized: list[ResearchTeamDomainLearningRetentionReasonCodeCount] = []
    seen: set[str] = set()
    for item in reason_code_counts:
        if type(item) is dict:
            item = ResearchTeamDomainLearningRetentionReasonCodeCount(**item)
        elif type(item) is ResearchTeamDomainLearningRetentionReasonCodeCount:
            item = ResearchTeamDomainLearningRetentionReasonCodeCount(
                **_field_values(item),
            )
        else:
            raise TypeError(
                "reason_code_counts must contain exactly "
                "ResearchTeamDomainLearningRetentionReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise TypeError("reason_codes must be a tuple")
    normalized = tuple(value)
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _validate_row(row: ResearchTeamDomainLearningRetentionReportRow) -> None:
    if row.public_status not in STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    if row.reason_codes == ():
        raise ValueError("row reason_codes must not be empty")
    if NO_INPUTS_REASON in row.reason_codes:
        raise ValueError("reason_codes must not include no-inputs for a row")
    if row.public_status == STATUS_PASS:
        if row.reason_codes != (PASS_REASON,):
            raise ValueError("reason_codes must match public_status")
    elif row.public_status == STATUS_WATCH:
        if WATCH_REASON not in row.reason_codes:
            raise ValueError("reason_codes must match public_status")
        if BLOCK_REASON in row.reason_codes:
            raise ValueError("reason_codes must match public_status")
        if STALE_MEMORY_BLOCK_REASON in row.reason_codes:
            raise ValueError("reason_codes must match public_status")
        if REVIEW_LATENCY_BLOCK_REASON in row.reason_codes:
            raise ValueError("reason_codes must match public_status")
        if PASS_REASON in row.reason_codes:
            raise ValueError("reason_codes must match public_status")
    else:
        if BLOCK_REASON not in row.reason_codes:
            raise ValueError("reason_codes must match public_status")
        if WATCH_REASON in row.reason_codes or PASS_REASON in row.reason_codes:
            raise ValueError("reason_codes must match public_status")

    expected_stale_memory_retention_score = _decimal(
        ONE - row.stale_memory_penalty_score,
    )
    if row.stale_memory_retention_score != expected_stale_memory_retention_score:
        raise ValueError(
            "stale_memory_retention_score must match stale_memory_penalty_score",
        )
    expected_retention_score = _average(
        (
            row.calibration_carryforward_score,
            row.correction_follow_through_score,
            row.stale_memory_retention_score,
            row.evidence_reuse_quality_score,
            row.peer_review_coverage_score,
            row.review_latency_score,
        ),
    )
    if row.retention_score != expected_retention_score:
        raise ValueError("retention_score must match row dimensions")


def _validate_report(report: ResearchTeamDomainLearningRetentionReport) -> None:
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must be canonical")
    if report.reason_code_counts != _normalize_reason_code_counts(
        report.reason_code_counts,
    ):
        raise ValueError("reason_code_counts must be canonical")
    row_count = _count_decimal(report.rows)
    if report.domain_team_count != row_count:
        raise ValueError("domain_team_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    expected_report_status = (
        STATUS_BLOCK if report.rows == () else _summary_status(report.rows)
    )
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match rows")
    _require_matching_report_decimal(
        "average_retention_score",
        report.average_retention_score,
        _average(row.retention_score for row in report.rows),
    )
    _require_matching_report_decimal(
        "average_calibration_carryforward_score",
        report.average_calibration_carryforward_score,
        _average(row.calibration_carryforward_score for row in report.rows),
    )
    _require_matching_report_decimal(
        "average_correction_follow_through_score",
        report.average_correction_follow_through_score,
        _average(row.correction_follow_through_score for row in report.rows),
    )
    _require_matching_report_decimal(
        "average_stale_memory_retention_score",
        report.average_stale_memory_retention_score,
        _average(row.stale_memory_retention_score for row in report.rows),
    )
    _require_matching_report_decimal(
        "average_evidence_reuse_quality_score",
        report.average_evidence_reuse_quality_score,
        _average(row.evidence_reuse_quality_score for row in report.rows),
    )
    _require_matching_report_decimal(
        "average_peer_review_coverage_score",
        report.average_peer_review_coverage_score,
        _average(row.peer_review_coverage_score for row in report.rows),
    )
    _require_matching_report_decimal(
        "average_review_latency_score",
        report.average_review_latency_score,
        _average(row.review_latency_score for row in report.rows),
    )
    expected_max_review_latency_seconds = (
        ZERO
        if report.rows == ()
        else max(row.review_latency_seconds for row in report.rows)
    )
    _require_matching_report_decimal(
        "max_review_latency_seconds",
        report.max_review_latency_seconds,
        expected_max_review_latency_seconds,
    )
    _require_matching_report_decimal(
        "stale_memory_penalty_count",
        report.stale_memory_penalty_count,
        _count_if(
            report.rows,
            lambda row: STALE_MEMORY_WATCH_REASON in row.reason_codes
            or STALE_MEMORY_BLOCK_REASON in row.reason_codes,
        ),
    )
    _require_matching_report_decimal(
        "peer_review_gap_count",
        report.peer_review_gap_count,
        _count_if(
            report.rows,
            lambda row: PEER_REVIEW_GAP_REASON in row.reason_codes,
        ),
    )
    _require_matching_report_decimal(
        "review_latency_gap_count",
        report.review_latency_gap_count,
        _count_if(
            report.rows,
            lambda row: REVIEW_LATENCY_GAP_REASON in row.reason_codes
            or REVIEW_LATENCY_BLOCK_REASON in row.reason_codes,
        ),
    )
    expected_reason_code_counts = _expected_reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _require_matching_report_decimal(
    name: str,
    value: Decimal,
    expected: Decimal,
) -> None:
    if value != expected:
        raise ValueError(f"{name} must match rows")


def _expected_reason_code_counts(
    rows: tuple[ResearchTeamDomainLearningRetentionReportRow, ...],
) -> tuple[ResearchTeamDomainLearningRetentionReasonCodeCount, ...]:
    if rows == ():
        return (
            ResearchTeamDomainLearningRetentionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_ratio=ZERO,
            ),
        )
    return _reason_code_counts(rows)


def _count_decimal(value: tuple[object, ...]) -> Decimal:
    return _decimal(Decimal(len(value)))


def _status_count(
    rows: tuple[ResearchTeamDomainLearningRetentionReportRow, ...],
    status: str,
) -> Decimal:
    return _count_if(rows, lambda row: row.public_status == status)


def _count_if(
    rows: tuple[ResearchTeamDomainLearningRetentionReportRow, ...],
    predicate: Any,
) -> Decimal:
    count = ZERO
    for row in rows:
        if predicate(row):
            count += ONE
    return _decimal(count)


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    total = ZERO
    for item in items:
        total += _require_decimal("average item", item)
    return _ratio(total, _decimal(Decimal(len(items))))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    normalized = value.astimezone(UTC)
    if normalized.microsecond != 0:
        raise ValueError(f"{name} must be a whole second")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be public")
    if not value.isascii() or not all(
        "a" <= ch <= "z" or "0" <= ch <= "9" or ch in "._-" for ch in value
    ):
        raise ValueError(f"{name} must be public")
    if value.startswith((".", "_", "-")) or value.endswith((".", "_", "-")):
        raise ValueError(f"{name} must be public")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} must be public")
    return value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{name} must be exactly str")
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _decimal(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return _decimal(value)


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be in the unit interval")
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{name} must be exactly str")
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _payload_value(value: Any, *, include_digest: bool) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            if field.name == "derived_validation_digest" and not include_digest:
                continue
            payload[field.name] = _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return payload
    if isinstance(value, Decimal):
        return str(_require_decimal("payload Decimal", value))
    if type(value) is datetime:
        return _format_datetime(value)
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError("payload contains unsafe public value")
        return value
    if type(value) is bool:
        return value
    if type(value) in (tuple, list):
        return tuple(_payload_value(item, include_digest=include_digest) for item in value)
    if type(value) is dict:
        payload = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if key == "derived_validation_digest" and not include_digest:
                continue
            if _has_unsafe_fragment(key):
                raise ValueError("payload contains unsafe public key")
            payload[key] = _payload_value(item, include_digest=include_digest)
        return payload
    raise ValueError("payload value is not report serializable")


def _format_datetime(value: datetime) -> str:
    normalized = _as_utc("payload datetime", value)
    return normalized.isoformat().replace("+00:00", "Z")


def _report_digest_from_payload(
    report: ResearchTeamDomainLearningRetentionReport,
    *,
    include_digest: bool,
) -> str:
    payload = _payload_value(report, include_digest=include_digest)
    return _digest_payload(payload)


def _validate_public_report(
    report: ResearchTeamDomainLearningRetentionReport,
) -> str:
    if type(report) is not ResearchTeamDomainLearningRetentionReport:
        raise TypeError(
            "report must be exactly ResearchTeamDomainLearningRetentionReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    _reject_unsafe_public_payload(_payload_value(report, include_digest=True))
    expected_digest = _report_digest_from_payload(report, include_digest=False)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return expected_digest


def _report_digest_from_mapping(values: dict[str, Any]) -> str:
    payload = _payload_value(values, include_digest=False)
    return _digest_payload(payload)


def _digest_payload(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(text.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError("payload contains unsafe public value")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    normalized = lowered.translate(str.maketrans("", "", "._-"))
    return any(fragment in lowered for fragment in _unsafe_fragments()) or any(
        fragment in normalized for fragment in _normalized_unsafe_fragments()
    )


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "candidate",
        "market",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source",
        "url",
        "http",
        "text",
        "source_text",
        "source_id",
        "raw_",
        "auth",
        "api_key",
        "credential",
        "password",
        "secret",
        "session",
        "cookie",
        "database",
        "dsn",
        "postgres",
        "supabase",
        "sql_",
        "network",
        "endpoint",
        "socket",
        "table",
        "file_",
        "sizing",
        "recommendation",
        _part("to", "ken"),
        _part("wal", "let"),
        _part("or", "der"),
        "trading",
        _part("tr", "ade"),
        "execution",
        "execute",
        "live",
    )


def _normalized_unsafe_fragments() -> tuple[str, ...]:
    return (
        "candidate",
        "market",
        "marketid",
        "marketslug",
        "slug",
        "question",
        "source",
        "url",
        "http",
        "text",
        "sourcetext",
        "sourceid",
        "rawcandidate",
        "auth",
        "apikey",
        "credential",
        "password",
        "secret",
        "session",
        "cookie",
        "database",
        "dsn",
        "postgres",
        "supabase",
        "sqlquery",
        "network",
        "endpoint",
        "socket",
        "table",
        "filepath",
        "sizing",
        "recommendation",
        _part("to", "ken"),
        _part("wal", "let"),
        _part("or", "der"),
        "trading",
        _part("tr", "ade"),
        "execution",
        "execute",
        "live",
    )


def _part(*values: str) -> str:
    return "".join(values)


def _field_values(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise TypeError("value must be a dataclass instance")
    return {field.name: getattr(value, field.name) for field in fields(value)}


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_RETENTION_CONFIG_VERSION",
    "ResearchTeamDomainLearningRetentionConfig",
    "ResearchTeamDomainLearningRetentionInputRow",
    "ResearchTeamDomainLearningRetentionReasonCodeCount",
    "ResearchTeamDomainLearningRetentionReport",
    "ResearchTeamDomainLearningRetentionReportRow",
    "build_research_team_domain_learning_retention_report",
    "research_team_domain_learning_retention_report_digest",
    "research_team_domain_learning_retention_report_payload",
)
