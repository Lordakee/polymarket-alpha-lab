"""Pure report-only specialist memory retention decay reducer."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_DECAY_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-retention-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SPECIALIST_MEMORY_RETENTION_DECAY_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
COMPONENT_COUNT = Decimal("4.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_SNAPSHOTS_REASON = "specialist_memory_retention_decay_no_snapshots"
CLEAR_REASON = "specialist_memory_retention_decay_clear"
LAST_CALIBRATION_AGE_BLOCK_REASON = "last_calibration_age_block"
LAST_CALIBRATION_AGE_WATCH_REASON = "last_calibration_age_watch"
ERROR_ATTRIBUTION_REUSE_BLOCK_REASON = "error_attribution_reuse_block"
ERROR_ATTRIBUTION_REUSE_WATCH_REASON = "error_attribution_reuse_watch"
FEEDBACK_ABSORPTION_BLOCK_REASON = "feedback_absorption_block"
FEEDBACK_ABSORPTION_WATCH_REASON = "feedback_absorption_watch"
STALE_PLAYBOOK_PRESSURE_BLOCK_REASON = "stale_playbook_pressure_block"
STALE_PLAYBOOK_PRESSURE_WATCH_REASON = "stale_playbook_pressure_watch"

ROW_REASON_CODE_SEQUENCE = (
    LAST_CALIBRATION_AGE_BLOCK_REASON,
    LAST_CALIBRATION_AGE_WATCH_REASON,
    ERROR_ATTRIBUTION_REUSE_BLOCK_REASON,
    ERROR_ATTRIBUTION_REUSE_WATCH_REASON,
    FEEDBACK_ABSORPTION_BLOCK_REASON,
    FEEDBACK_ABSORPTION_WATCH_REASON,
    STALE_PLAYBOOK_PRESSURE_BLOCK_REASON,
    STALE_PLAYBOOK_PRESSURE_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_SNAPSHOTS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "specialist_memory_retention_decay_report_clear"
REPORT_BLOCK_PRESENT_REASON = "specialist_memory_retention_decay_block_present"
REPORT_WATCH_PRESENT_REASON = "specialist_memory_retention_decay_watch_present"
REPORT_LAST_CALIBRATION_AGE_GAP_REASON = "last_calibration_age_gap_present"
REPORT_ERROR_ATTRIBUTION_REUSE_GAP_REASON = "error_attribution_reuse_gap_present"
REPORT_FEEDBACK_ABSORPTION_GAP_REASON = "feedback_absorption_gap_present"
REPORT_STALE_PLAYBOOK_PRESSURE_REASON = "stale_playbook_pressure_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_SNAPSHOTS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_LAST_CALIBRATION_AGE_GAP_REASON,
    REPORT_ERROR_ATTRIBUTION_REUSE_GAP_REASON,
    REPORT_FEEDBACK_ABSORPTION_GAP_REASON,
    REPORT_STALE_PLAYBOOK_PRESSURE_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "reuse_specialist_memory_retention_decay",
    STATUS_WATCH: "review_specialist_memory_retention_decay_before_reuse",
    STATUS_BLOCK: "block_specialist_memory_retention_until_review",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket"),
    _join_parts("s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("u", "rl"),
    _join_parts("ht", "tp"),
    _join_parts("sou", "rce", "_", "text"),
    _join_parts("sou", "rce", "_", "id"),
    _join_parts("d", "sn"),
    _join_parts("d", "b", "_"),
    _join_parts("_", "d", "b"),
    _join_parts("ta", "ble"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("li", "ve"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("exec", "ution"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    _join_parts("priv", "ate"),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_DECAY_REPORT_CONFIG_VERSION",
    "SPECIALIST_MEMORY_RETENTION_DECAY_STATUSES",
    "ResearchTeamSpecialistMemoryRetentionDecayConfig",
    "ResearchTeamSpecialistMemoryRetentionDecayDomainRow",
    "ResearchTeamSpecialistMemoryRetentionDecayReasonCount",
    "ResearchTeamSpecialistMemoryRetentionDecayReport",
    "ResearchTeamSpecialistMemoryRetentionDecayRow",
    "ResearchTeamSpecialistMemoryRetentionDecaySnapshot",
    "build_research_team_specialist_memory_retention_decay_report",
    "research_team_specialist_memory_retention_decay_report_digest",
    "research_team_specialist_memory_retention_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_last_calibration_age_seconds: Decimal = Decimal("604800.000000")
    max_watch_last_calibration_age_seconds: Decimal = Decimal("2592000.000000")
    min_pass_error_attribution_reuse_ratio: Decimal = Decimal("0.700000")
    min_watch_error_attribution_reuse_ratio: Decimal = Decimal("0.500000")
    min_pass_feedback_absorption_ratio: Decimal = Decimal("0.700000")
    min_watch_feedback_absorption_ratio: Decimal = Decimal("0.500000")
    max_pass_stale_playbook_pressure_ratio: Decimal = Decimal("0.100000")
    max_watch_stale_playbook_pressure_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDecayConfig:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDecayConfig rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryRetentionDecayConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported config version")
        for name in (
            "max_pass_last_calibration_age_seconds",
            "max_watch_last_calibration_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "min_pass_error_attribution_reuse_ratio",
            "min_watch_error_attribution_reuse_ratio",
            "min_pass_feedback_absorption_ratio",
            "min_watch_feedback_absorption_ratio",
            "max_pass_stale_playbook_pressure_ratio",
            "max_watch_stale_playbook_pressure_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if (
            self.max_pass_last_calibration_age_seconds
            > self.max_watch_last_calibration_age_seconds
        ):
            raise ValueError("max_pass_last_calibration_age_seconds must not exceed watch")
        if (
            self.min_watch_error_attribution_reuse_ratio
            > self.min_pass_error_attribution_reuse_ratio
        ):
            raise ValueError("min_watch_error_attribution_reuse_ratio must not exceed pass")
        if (
            self.min_watch_feedback_absorption_ratio
            > self.min_pass_feedback_absorption_ratio
        ):
            raise ValueError("min_watch_feedback_absorption_ratio must not exceed pass")
        if (
            self.max_pass_stale_playbook_pressure_ratio
            > self.max_watch_stale_playbook_pressure_ratio
        ):
            raise ValueError("max_pass_stale_playbook_pressure_ratio must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDecaySnapshot:
    domain_label: str
    specialist_label: str
    last_calibrated_at: datetime
    long_term_memory_count: Decimal
    error_attribution_opportunity_count: Decimal
    reused_error_attribution_count: Decimal
    feedback_event_count: Decimal
    absorbed_feedback_count: Decimal
    playbook_reference_count: Decimal
    stale_playbook_reference_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDecaySnapshot:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDecaySnapshot rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionDecaySnapshot,
            "snapshot",
        )
        for name in ("domain_label", "specialist_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(
            self,
            "last_calibrated_at",
            _as_utc("last_calibrated_at", self.last_calibrated_at),
        )
        for name in (
            "long_term_memory_count",
            "error_attribution_opportunity_count",
            "feedback_event_count",
            "playbook_reference_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "reused_error_attribution_count",
            "absorbed_feedback_count",
            "stale_playbook_reference_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _check_snapshot_counts(self)
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDecayRow:
    domain_label: str
    specialist_label: str
    last_calibrated_at: datetime
    last_calibration_age_seconds: Decimal
    long_term_memory_count: Decimal
    error_attribution_opportunity_count: Decimal
    reused_error_attribution_count: Decimal
    feedback_event_count: Decimal
    absorbed_feedback_count: Decimal
    playbook_reference_count: Decimal
    stale_playbook_reference_count: Decimal
    calibration_recency_ratio: Decimal
    error_attribution_reuse_ratio: Decimal
    feedback_absorption_ratio: Decimal
    stale_playbook_pressure_ratio: Decimal
    retention_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDecayRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDecayRow rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryRetentionDecayRow, "row")
        for name in ("domain_label", "specialist_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(
            self,
            "last_calibrated_at",
            _as_utc("last_calibrated_at", self.last_calibrated_at),
        )
        object.__setattr__(
            self,
            "last_calibration_age_seconds",
            _require_nonnegative_decimal(
                "last_calibration_age_seconds",
                self.last_calibration_age_seconds,
            ),
        )
        for name in (
            "long_term_memory_count",
            "error_attribution_opportunity_count",
            "feedback_event_count",
            "playbook_reference_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "reused_error_attribution_count",
            "absorbed_feedback_count",
            "stale_playbook_reference_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "calibration_recency_ratio",
            "error_attribution_reuse_ratio",
            "feedback_absorption_ratio",
            "stale_playbook_pressure_ratio",
            "retention_decay_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _check_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDecayDomainRow:
    domain_label: str
    specialist_count: Decimal
    long_term_memory_count: Decimal
    max_last_calibration_age_seconds: Decimal
    error_attribution_opportunity_count: Decimal
    reused_error_attribution_count: Decimal
    feedback_event_count: Decimal
    absorbed_feedback_count: Decimal
    playbook_reference_count: Decimal
    stale_playbook_reference_count: Decimal
    error_attribution_reuse_ratio: Decimal
    feedback_absorption_ratio: Decimal
    stale_playbook_pressure_ratio: Decimal
    average_retention_decay_score: Decimal
    worst_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDecayDomainRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDecayDomainRow rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionDecayDomainRow,
            "domain row",
        )
        object.__setattr__(
            self,
            "domain_label",
            _require_public_label("domain_label", self.domain_label),
        )
        for name in (
            "specialist_count",
            "long_term_memory_count",
            "error_attribution_opportunity_count",
            "feedback_event_count",
            "playbook_reference_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "max_last_calibration_age_seconds",
            "reused_error_attribution_count",
            "absorbed_feedback_count",
            "stale_playbook_reference_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "error_attribution_reuse_ratio",
            "feedback_absorption_ratio",
            "stale_playbook_pressure_ratio",
            "average_retention_decay_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "worst_status",
            _require_status("worst_status", self.worst_status),
        )
        _check_domain_row(self)
        _require_hard_flags("domain row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDecayReasonCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDecayReasonCount:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDecayReasonCount rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionDecayReasonCount,
            "reason count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    snapshot_count: Decimal
    domain_count: Decimal
    specialist_count: Decimal
    long_term_memory_count: Decimal
    max_last_calibration_age_seconds: Decimal
    error_attribution_opportunity_count: Decimal
    reused_error_attribution_count: Decimal
    feedback_event_count: Decimal
    absorbed_feedback_count: Decimal
    playbook_reference_count: Decimal
    stale_playbook_reference_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    calibration_recency_ratio: Decimal
    error_attribution_reuse_ratio: Decimal
    feedback_absorption_ratio: Decimal
    stale_playbook_pressure_ratio: Decimal
    average_retention_decay_score: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...]
    domain_rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayDomainRow, ...]
    reason_counts: tuple[ResearchTeamSpecialistMemoryRetentionDecayReasonCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDecayReport:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDecayReport rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryRetentionDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "next_review_step",
            _require_public_label("next_review_step", self.next_review_step),
        )
        for name in (
            "snapshot_count",
            "domain_count",
            "specialist_count",
            "long_term_memory_count",
            "max_last_calibration_age_seconds",
            "error_attribution_opportunity_count",
            "reused_error_attribution_count",
            "feedback_event_count",
            "absorbed_feedback_count",
            "playbook_reference_count",
            "stale_playbook_reference_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "calibration_recency_ratio",
            "error_attribution_reuse_ratio",
            "feedback_absorption_ratio",
            "stale_playbook_pressure_ratio",
            "average_retention_decay_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "domain_rows", _normalize_domain_rows(self.domain_rows))
        object.__setattr__(self, "reason_counts", _normalize_reason_counts(self.reason_counts))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _check_report(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_team_specialist_memory_retention_decay_report_payload(self)


def build_research_team_specialist_memory_retention_decay_report(
    snapshots: Iterable[ResearchTeamSpecialistMemoryRetentionDecaySnapshot],
    *,
    config: ResearchTeamSpecialistMemoryRetentionDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryRetentionDecayReport:
    cfg = config or ResearchTeamSpecialistMemoryRetentionDecayConfig()
    if type(cfg) is not ResearchTeamSpecialistMemoryRetentionDecayConfig:
        raise ValueError(
            "config must be exactly ResearchTeamSpecialistMemoryRetentionDecayConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(
        snapshots,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_from_snapshot(
                    snapshot,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for snapshot in normalized_snapshots
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchTeamSpecialistMemoryRetentionDecayReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        snapshot_count=_count_decimal(len(normalized_snapshots)),
        domain_count=_count_decimal(len({row.domain_label for row in rows})),
        specialist_count=_count_decimal(
            len({(row.domain_label, row.specialist_label) for row in rows}),
        ),
        long_term_memory_count=_sum_decimal(row.long_term_memory_count for row in rows),
        max_last_calibration_age_seconds=_max_decimal(
            row.last_calibration_age_seconds for row in rows
        ),
        error_attribution_opportunity_count=_sum_decimal(
            row.error_attribution_opportunity_count for row in rows
        ),
        reused_error_attribution_count=_sum_decimal(
            row.reused_error_attribution_count for row in rows
        ),
        feedback_event_count=_sum_decimal(row.feedback_event_count for row in rows),
        absorbed_feedback_count=_sum_decimal(row.absorbed_feedback_count for row in rows),
        playbook_reference_count=_sum_decimal(row.playbook_reference_count for row in rows),
        stale_playbook_reference_count=_sum_decimal(
            row.stale_playbook_reference_count for row in rows
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        calibration_recency_ratio=_average_decimal(
            tuple(row.calibration_recency_ratio for row in rows)
        ),
        error_attribution_reuse_ratio=_aggregate_error_attribution_reuse_ratio(rows),
        feedback_absorption_ratio=_aggregate_feedback_absorption_ratio(rows),
        stale_playbook_pressure_ratio=_aggregate_stale_playbook_pressure_ratio(rows),
        average_retention_decay_score=_average_retention_decay_score(rows),
        rows=rows,
        domain_rows=_domain_rows(rows),
        reason_counts=_reason_counts(rows),
        reason_codes=_report_reason_codes(rows, len(normalized_snapshots)),
    )


def research_team_specialist_memory_retention_decay_report_payload(
    value: ResearchTeamSpecialistMemoryRetentionDecayReport | dict[str, Any],
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _check_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _check_payload_digest(payload)
    _validate_public_report_payload_schema(payload)
    return payload


def research_team_specialist_memory_retention_decay_report_digest(
    report: ResearchTeamSpecialistMemoryRetentionDecayReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistMemoryRetentionDecayReport:
        raise ValueError(
            "report must be exactly ResearchTeamSpecialistMemoryRetentionDecayReport",
        )
    return report.derived_validation_digest


def _row_from_snapshot(
    snapshot: ResearchTeamSpecialistMemoryRetentionDecaySnapshot,
    *,
    config: ResearchTeamSpecialistMemoryRetentionDecayConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryRetentionDecayRow:
    last_calibration_age_seconds = _age_seconds(generated_at, snapshot.last_calibrated_at)
    calibration_recency_ratio = _calibration_recency_ratio(
        last_calibration_age_seconds,
        config,
    )
    error_attribution_reuse_ratio = _safe_divide(
        snapshot.reused_error_attribution_count,
        snapshot.error_attribution_opportunity_count,
    )
    feedback_absorption_ratio = _safe_divide(
        snapshot.absorbed_feedback_count,
        snapshot.feedback_event_count,
    )
    stale_playbook_pressure_ratio = _safe_divide(
        snapshot.stale_playbook_reference_count,
        snapshot.playbook_reference_count,
    )
    reason_codes = _row_reason_codes(
        last_calibration_age_seconds=last_calibration_age_seconds,
        error_attribution_reuse_ratio=error_attribution_reuse_ratio,
        feedback_absorption_ratio=feedback_absorption_ratio,
        stale_playbook_pressure_ratio=stale_playbook_pressure_ratio,
        config=config,
    )
    return ResearchTeamSpecialistMemoryRetentionDecayRow(
        domain_label=snapshot.domain_label,
        specialist_label=snapshot.specialist_label,
        last_calibrated_at=snapshot.last_calibrated_at,
        last_calibration_age_seconds=last_calibration_age_seconds,
        long_term_memory_count=snapshot.long_term_memory_count,
        error_attribution_opportunity_count=snapshot.error_attribution_opportunity_count,
        reused_error_attribution_count=snapshot.reused_error_attribution_count,
        feedback_event_count=snapshot.feedback_event_count,
        absorbed_feedback_count=snapshot.absorbed_feedback_count,
        playbook_reference_count=snapshot.playbook_reference_count,
        stale_playbook_reference_count=snapshot.stale_playbook_reference_count,
        calibration_recency_ratio=calibration_recency_ratio,
        error_attribution_reuse_ratio=error_attribution_reuse_ratio,
        feedback_absorption_ratio=feedback_absorption_ratio,
        stale_playbook_pressure_ratio=stale_playbook_pressure_ratio,
        retention_decay_score=_retention_decay_score(
            calibration_recency_ratio=calibration_recency_ratio,
            error_attribution_reuse_ratio=error_attribution_reuse_ratio,
            feedback_absorption_ratio=feedback_absorption_ratio,
            stale_playbook_pressure_ratio=stale_playbook_pressure_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _calibration_recency_ratio(
    last_calibration_age_seconds: Decimal,
    config: ResearchTeamSpecialistMemoryRetentionDecayConfig,
) -> Decimal:
    if last_calibration_age_seconds >= config.max_watch_last_calibration_age_seconds:
        return ZERO
    return _clamped_ratio(
        ONE - _safe_divide(last_calibration_age_seconds, config.max_watch_last_calibration_age_seconds),
    )


def _row_reason_codes(
    *,
    last_calibration_age_seconds: Decimal,
    error_attribution_reuse_ratio: Decimal,
    feedback_absorption_ratio: Decimal,
    stale_playbook_pressure_ratio: Decimal,
    config: ResearchTeamSpecialistMemoryRetentionDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if last_calibration_age_seconds > config.max_watch_last_calibration_age_seconds:
        reason_codes.append(LAST_CALIBRATION_AGE_BLOCK_REASON)
    elif last_calibration_age_seconds > config.max_pass_last_calibration_age_seconds:
        reason_codes.append(LAST_CALIBRATION_AGE_WATCH_REASON)
    if error_attribution_reuse_ratio < config.min_watch_error_attribution_reuse_ratio:
        reason_codes.append(ERROR_ATTRIBUTION_REUSE_BLOCK_REASON)
    elif error_attribution_reuse_ratio < config.min_pass_error_attribution_reuse_ratio:
        reason_codes.append(ERROR_ATTRIBUTION_REUSE_WATCH_REASON)
    if feedback_absorption_ratio < config.min_watch_feedback_absorption_ratio:
        reason_codes.append(FEEDBACK_ABSORPTION_BLOCK_REASON)
    elif feedback_absorption_ratio < config.min_pass_feedback_absorption_ratio:
        reason_codes.append(FEEDBACK_ABSORPTION_WATCH_REASON)
    if stale_playbook_pressure_ratio > config.max_watch_stale_playbook_pressure_ratio:
        reason_codes.append(STALE_PLAYBOOK_PRESSURE_BLOCK_REASON)
    elif stale_playbook_pressure_ratio > config.max_pass_stale_playbook_pressure_ratio:
        reason_codes.append(STALE_PLAYBOOK_PRESSURE_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
    snapshot_count: int,
) -> tuple[str, ...]:
    if snapshot_count == 0:
        return (NO_SNAPSHOTS_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if _row_reason_count(
        rows,
        (LAST_CALIBRATION_AGE_BLOCK_REASON, LAST_CALIBRATION_AGE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_LAST_CALIBRATION_AGE_GAP_REASON)
    if _row_reason_count(
        rows,
        (ERROR_ATTRIBUTION_REUSE_BLOCK_REASON, ERROR_ATTRIBUTION_REUSE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_ERROR_ATTRIBUTION_REUSE_GAP_REASON)
    if _row_reason_count(
        rows,
        (FEEDBACK_ABSORPTION_BLOCK_REASON, FEEDBACK_ABSORPTION_WATCH_REASON),
    ):
        reason_codes.append(REPORT_FEEDBACK_ABSORPTION_GAP_REASON)
    if _row_reason_count(
        rows,
        (STALE_PLAYBOOK_PRESSURE_BLOCK_REASON, STALE_PLAYBOOK_PRESSURE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_STALE_PLAYBOOK_PRESSURE_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _reason_counts(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDecayReasonCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistMemoryRetentionDecayReasonCount(
                reason_code=NO_SNAPSHOTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_total = _count_decimal(len(rows))
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    return tuple(
        ResearchTeamSpecialistMemoryRetentionDecayReasonCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
            row_ratio=_safe_divide(_count_decimal(counter[reason_code]), row_total),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _domain_rows(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDecayDomainRow, ...]:
    domain_labels = sorted({row.domain_label for row in rows})
    return tuple(_domain_row_for_label(domain_label, rows) for domain_label in domain_labels)


def _domain_row_for_label(
    domain_label: str,
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> ResearchTeamSpecialistMemoryRetentionDecayDomainRow:
    domain_rows = tuple(row for row in rows if row.domain_label == domain_label)
    error_attribution_opportunity_count = _sum_decimal(
        row.error_attribution_opportunity_count for row in domain_rows
    )
    reused_error_attribution_count = _sum_decimal(
        row.reused_error_attribution_count for row in domain_rows
    )
    feedback_event_count = _sum_decimal(row.feedback_event_count for row in domain_rows)
    absorbed_feedback_count = _sum_decimal(row.absorbed_feedback_count for row in domain_rows)
    playbook_reference_count = _sum_decimal(
        row.playbook_reference_count for row in domain_rows
    )
    stale_playbook_reference_count = _sum_decimal(
        row.stale_playbook_reference_count for row in domain_rows
    )
    return ResearchTeamSpecialistMemoryRetentionDecayDomainRow(
        domain_label=domain_label,
        specialist_count=_count_decimal(len({row.specialist_label for row in domain_rows})),
        long_term_memory_count=_sum_decimal(
            row.long_term_memory_count for row in domain_rows
        ),
        max_last_calibration_age_seconds=_max_decimal(
            row.last_calibration_age_seconds for row in domain_rows
        ),
        error_attribution_opportunity_count=error_attribution_opportunity_count,
        reused_error_attribution_count=reused_error_attribution_count,
        feedback_event_count=feedback_event_count,
        absorbed_feedback_count=absorbed_feedback_count,
        playbook_reference_count=playbook_reference_count,
        stale_playbook_reference_count=stale_playbook_reference_count,
        error_attribution_reuse_ratio=_safe_divide(
            reused_error_attribution_count,
            error_attribution_opportunity_count,
        ),
        feedback_absorption_ratio=_safe_divide(
            absorbed_feedback_count,
            feedback_event_count,
        ),
        stale_playbook_pressure_ratio=_safe_divide(
            stale_playbook_reference_count,
            playbook_reference_count,
        ),
        average_retention_decay_score=_average_decimal(
            tuple(row.retention_decay_score for row in domain_rows)
        ),
        worst_status=_report_status(domain_rows),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_count(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _row_sort_key(
    row: ResearchTeamSpecialistMemoryRetentionDecayRow,
) -> tuple[int, str, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.domain_label,
        row.specialist_label,
    )


def _normalize_snapshots(
    snapshots: Iterable[ResearchTeamSpecialistMemoryRetentionDecaySnapshot],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistMemoryRetentionDecaySnapshot, ...]:
    normalized = tuple(snapshots)
    for snapshot in normalized:
        if type(snapshot) is not ResearchTeamSpecialistMemoryRetentionDecaySnapshot:
            raise ValueError(
                "snapshots must contain exactly "
                "ResearchTeamSpecialistMemoryRetentionDecaySnapshot",
            )
        _require_hard_flags("snapshot", snapshot)
        if snapshot.last_calibrated_at > generated_at:
            raise ValueError("last_calibrated_at must not be after generated_at")
    keys = tuple((item.domain_label, item.specialist_label) for item in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("domain_label and specialist_label pairs must be unique")
    return tuple(sorted(normalized, key=lambda item: (item.domain_label, item.specialist_label)))


def _normalize_rows(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryRetentionDecayRow:
            raise ValueError(
                "rows must contain exactly ResearchTeamSpecialistMemoryRetentionDecayRow",
            )
        _require_hard_flags("row", row)
    keys = tuple((row.domain_label, row.specialist_label) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError("rows domain_label and specialist_label pairs must be unique")
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_domain_rows(
    values: tuple[ResearchTeamSpecialistMemoryRetentionDecayDomainRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDecayDomainRow, ...]:
    if type(values) is not tuple:
        raise ValueError("domain_rows must be a tuple")
    for value in values:
        if type(value) is not ResearchTeamSpecialistMemoryRetentionDecayDomainRow:
            raise ValueError(
                "domain_rows must contain exactly "
                "ResearchTeamSpecialistMemoryRetentionDecayDomainRow",
            )
        _require_hard_flags("domain row", value)
    labels = tuple(value.domain_label for value in values)
    if len(set(labels)) != len(labels):
        raise ValueError("domain_rows domain_label values must be unique")
    return tuple(sorted(values, key=lambda value: value.domain_label))


def _normalize_reason_counts(
    counts: tuple[ResearchTeamSpecialistMemoryRetentionDecayReasonCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDecayReasonCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamSpecialistMemoryRetentionDecayReasonCount:
            raise ValueError(
                "reason_counts must contain exactly "
                "ResearchTeamSpecialistMemoryRetentionDecayReasonCount",
            )
        _require_hard_flags("reason count", count)
    reason_codes = tuple(count.reason_code for count in counts)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_counts reason_code values must be unique")
    return tuple(
        sorted(counts, key=lambda count: COUNT_REASON_CODE_SEQUENCE.index(count.reason_code))
    )


def _normalize_reason_codes(
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


def _check_snapshot_counts(
    snapshot: ResearchTeamSpecialistMemoryRetentionDecaySnapshot,
) -> None:
    if (
        snapshot.reused_error_attribution_count
        > snapshot.error_attribution_opportunity_count
    ):
        raise ValueError(
            "reused_error_attribution_count must not exceed "
            "error_attribution_opportunity_count",
        )
    if snapshot.absorbed_feedback_count > snapshot.feedback_event_count:
        raise ValueError("absorbed_feedback_count must not exceed feedback_event_count")
    if snapshot.stale_playbook_reference_count > snapshot.playbook_reference_count:
        raise ValueError(
            "stale_playbook_reference_count must not exceed playbook_reference_count",
        )


def _check_row(row: ResearchTeamSpecialistMemoryRetentionDecayRow) -> None:
    if row.reused_error_attribution_count > row.error_attribution_opportunity_count:
        raise ValueError(
            "reused_error_attribution_count must not exceed "
            "error_attribution_opportunity_count",
        )
    if row.absorbed_feedback_count > row.feedback_event_count:
        raise ValueError("absorbed_feedback_count must not exceed feedback_event_count")
    if row.stale_playbook_reference_count > row.playbook_reference_count:
        raise ValueError(
            "stale_playbook_reference_count must not exceed playbook_reference_count",
        )
    expected_ratios = {
        "error_attribution_reuse_ratio": _safe_divide(
            row.reused_error_attribution_count,
            row.error_attribution_opportunity_count,
        ),
        "feedback_absorption_ratio": _safe_divide(
            row.absorbed_feedback_count,
            row.feedback_event_count,
        ),
        "stale_playbook_pressure_ratio": _safe_divide(
            row.stale_playbook_reference_count,
            row.playbook_reference_count,
        ),
    }
    for name, expected in expected_ratios.items():
        if getattr(row, name) != expected:
            raise ValueError(f"{name} must match row counts")
    expected_score = _retention_decay_score(
        calibration_recency_ratio=row.calibration_recency_ratio,
        error_attribution_reuse_ratio=row.error_attribution_reuse_ratio,
        feedback_absorption_ratio=row.feedback_absorption_ratio,
        stale_playbook_pressure_ratio=row.stale_playbook_pressure_ratio,
    )
    if row.retention_decay_score != expected_score:
        raise ValueError("retention_decay_score must match row ratios")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _check_domain_row(value: ResearchTeamSpecialistMemoryRetentionDecayDomainRow) -> None:
    if value.reused_error_attribution_count > value.error_attribution_opportunity_count:
        raise ValueError(
            "reused_error_attribution_count must not exceed "
            "error_attribution_opportunity_count",
        )
    if value.absorbed_feedback_count > value.feedback_event_count:
        raise ValueError("absorbed_feedback_count must not exceed feedback_event_count")
    if value.stale_playbook_reference_count > value.playbook_reference_count:
        raise ValueError(
            "stale_playbook_reference_count must not exceed playbook_reference_count",
        )
    expected_ratios = {
        "error_attribution_reuse_ratio": _safe_divide(
            value.reused_error_attribution_count,
            value.error_attribution_opportunity_count,
        ),
        "feedback_absorption_ratio": _safe_divide(
            value.absorbed_feedback_count,
            value.feedback_event_count,
        ),
        "stale_playbook_pressure_ratio": _safe_divide(
            value.stale_playbook_reference_count,
            value.playbook_reference_count,
        ),
    }
    for name, expected in expected_ratios.items():
        if getattr(value, name) != expected:
            raise ValueError(f"{name} must match domain counts")


def _check_report(report: ResearchTeamSpecialistMemoryRetentionDecayReport) -> None:
    expected_counts = {
        "snapshot_count": _count_decimal(len(report.rows)),
        "domain_count": _count_decimal(len({row.domain_label for row in report.rows})),
        "specialist_count": _count_decimal(
            len({(row.domain_label, row.specialist_label) for row in report.rows}),
        ),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
    }
    for name, expected in expected_counts.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    expected_sums = {
        "long_term_memory_count": _sum_decimal(
            row.long_term_memory_count for row in report.rows
        ),
        "max_last_calibration_age_seconds": _max_decimal(
            row.last_calibration_age_seconds for row in report.rows
        ),
        "error_attribution_opportunity_count": _sum_decimal(
            row.error_attribution_opportunity_count for row in report.rows
        ),
        "reused_error_attribution_count": _sum_decimal(
            row.reused_error_attribution_count for row in report.rows
        ),
        "feedback_event_count": _sum_decimal(row.feedback_event_count for row in report.rows),
        "absorbed_feedback_count": _sum_decimal(
            row.absorbed_feedback_count for row in report.rows
        ),
        "playbook_reference_count": _sum_decimal(
            row.playbook_reference_count for row in report.rows
        ),
        "stale_playbook_reference_count": _sum_decimal(
            row.stale_playbook_reference_count for row in report.rows
        ),
    }
    for name, expected in expected_sums.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    expected_ratios = {
        "calibration_recency_ratio": _average_decimal(
            tuple(row.calibration_recency_ratio for row in report.rows)
        ),
        "error_attribution_reuse_ratio": _aggregate_error_attribution_reuse_ratio(
            report.rows,
        ),
        "feedback_absorption_ratio": _aggregate_feedback_absorption_ratio(report.rows),
        "stale_playbook_pressure_ratio": _aggregate_stale_playbook_pressure_ratio(
            report.rows,
        ),
        "average_retention_decay_score": _average_retention_decay_score(report.rows),
    }
    for name, expected in expected_ratios.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.domain_rows != _domain_rows(report.rows):
        raise ValueError("domain_rows must match rows")
    if report.reason_counts != _reason_counts(report.rows):
        raise ValueError("reason_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.snapshot_count)):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")


def _aggregate_error_attribution_reuse_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.reused_error_attribution_count for row in rows),
        _sum_decimal(row.error_attribution_opportunity_count for row in rows),
    )


def _aggregate_feedback_absorption_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.absorbed_feedback_count for row in rows),
        _sum_decimal(row.feedback_event_count for row in rows),
    )


def _aggregate_stale_playbook_pressure_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.stale_playbook_reference_count for row in rows),
        _sum_decimal(row.playbook_reference_count for row in rows),
    )


def _average_retention_decay_score(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionDecayRow, ...],
) -> Decimal:
    return _average_decimal(tuple(row.retention_decay_score for row in rows))


def _retention_decay_score(
    *,
    calibration_recency_ratio: Decimal,
    error_attribution_reuse_ratio: Decimal,
    feedback_absorption_ratio: Decimal,
    stale_playbook_pressure_ratio: Decimal,
) -> Decimal:
    return _quantize_decimal(
        (
            calibration_recency_ratio
            + error_attribution_reuse_ratio
            + feedback_absorption_ratio
            + (ONE - stale_playbook_pressure_ratio)
        )
        / COMPONENT_COUNT,
    )


def _require_supported_payload_input(value: object) -> None:
    if type(value) is dict:
        return
    if type(value) is ResearchTeamSpecialistMemoryRetentionDecayReport:
        _require_hard_flags("payload input", value)
        return
    raise ValueError(
        "report must be exactly "
        "ResearchTeamSpecialistMemoryRetentionDecayReport or dict",
    )


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _check_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _check_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, child in enumerate(item):
                    if type(child) is dict:
                        _check_payload_flags(child, f"{field_path}.{key}.{index}")


def _check_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        raise ValueError("derived_validation_digest is required")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    if digest != _digest_payload(payload):
        raise ValueError("derived_validation_digest must match payload")


def _validate_public_report_payload_schema(payload: dict[str, Any]) -> None:
    rebuilt = _dataclass_from_public_payload(
        payload,
        ResearchTeamSpecialistMemoryRetentionDecayReport,
        "payload",
    )
    if _payload_value(rebuilt) != payload:
        raise ValueError("public report payload must use canonical values")


def _dataclass_from_public_payload(
    value: object,
    expected_type: type[Any],
    path: str,
) -> object:
    if type(value) is not dict:
        raise ValueError(f"{path} must be a dict")
    expected_fields = fields(expected_type)
    expected_keys = frozenset(item.name for item in expected_fields)
    if frozenset(value) != expected_keys:
        raise ValueError(f"{_public_schema_name(expected_type)} must match")

    nested_types = {
        "rows": ResearchTeamSpecialistMemoryRetentionDecayRow,
        "domain_rows": ResearchTeamSpecialistMemoryRetentionDecayDomainRow,
        "reason_counts": ResearchTeamSpecialistMemoryRetentionDecayReasonCount,
    }
    parsed: dict[str, object] = {}
    for item in expected_fields:
        name = item.name
        field_path = f"{path}.{name}"
        field_value = value[name]
        if name in nested_types:
            if type(field_value) is not list:
                raise ValueError(f"{field_path} must be a list")
            parsed[name] = tuple(
                _dataclass_from_public_payload(
                    child,
                    nested_types[name],
                    f"{field_path}.{index}",
                )
                for index, child in enumerate(field_value)
            )
        elif name == "reason_codes":
            parsed[name] = _string_tuple_from_public_payload(field_value, field_path)
        elif name in ("generated_at", "last_calibrated_at"):
            parsed[name] = _datetime_from_public_payload(field_value, field_path)
        elif name == "count" or name.endswith(("_count", "_ratio", "_score", "_seconds")):
            parsed[name] = _decimal_from_public_payload(field_value, field_path)
        elif name in ("paper_only", "report_only", "readonly"):
            if field_value is not True:
                raise ValueError(f"{field_path} must be True")
            parsed[name] = field_value
        else:
            if type(field_value) is not str:
                raise ValueError(f"{field_path} must be a string")
            parsed[name] = field_value
    return expected_type(**parsed)


def _public_schema_name(expected_type: type[Any]) -> str:
    if expected_type is ResearchTeamSpecialistMemoryRetentionDecayReport:
        return "public report schema"
    if expected_type is ResearchTeamSpecialistMemoryRetentionDecayRow:
        return "public row schema"
    if expected_type is ResearchTeamSpecialistMemoryRetentionDecayDomainRow:
        return "public domain row schema"
    if expected_type is ResearchTeamSpecialistMemoryRetentionDecayReasonCount:
        return "public reason count schema"
    raise ValueError("unsupported public payload schema")


def _decimal_from_public_payload(value: object, path: str) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
        normalized = _quantize_decimal(parsed)
    except InvalidOperation as exc:
        raise ValueError(f"{path} must be a canonical Decimal string") from exc
    if not parsed.is_finite() or format(normalized, "f") != value:
        raise ValueError(f"{path} must be a canonical Decimal string")
    return parsed


def _datetime_from_public_payload(value: object, path: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical datetime string") from exc
    normalized = _as_utc(path, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{path} must be a canonical datetime string")
    return normalized


def _string_tuple_from_public_payload(value: object, path: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{path} must contain strings")
    return tuple(value)


def _derived_validation_digest(
    report: ResearchTeamSpecialistMemoryRetentionDecayReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _age_seconds(generated_at: datetime, prior_at: datetime) -> Decimal:
    if prior_at > generated_at:
        return ZERO
    delta = generated_at - prior_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize_decimal(seconds)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _safe_divide(_sum_decimal(values), _count_decimal(len(values)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    gathered = tuple(values)
    if not gathered:
        return ZERO
    return _quantize_decimal(max(gathered))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _require_decimal("ratio", value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return _quantize_decimal(normalized)


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(_require_decimal(name, value))
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{name} must be at most 1")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(_require_decimal(name, value))
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(_require_decimal(name, value))
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "":
        raise ValueError(f"{name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be single line")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} contains unsafe public payload text")
    return value


def _require_status(name: str, value: object) -> str:
    return _require_member(name, value, SPECIALIST_MEMORY_RETENTION_DECAY_STATUSES)


def _require_member(name: str, value: object, members: tuple[str, ...]) -> str:
    label = _require_public_label(name, value)
    if label not in members:
        raise ValueError(f"{name} must be one of {', '.join(members)}")
    return label


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_exact_type(value: object, expected: type[object], name: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{name} must be exactly {expected.__name__}")


def _reject_unsafe_public_payload(value: object, path: str = "payload") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_payload(getattr(value, item.name), f"{path}.{item.name}")
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload at {path}")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path} must not contain float values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload at {path}.{key}")
            _reject_unsafe_public_payload(item, f"{path}.{key}")
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(item, f"{path}.{index}")
        return
    raise ValueError(f"{path} is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
