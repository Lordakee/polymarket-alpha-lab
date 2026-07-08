"""Pure report-only aggregation for team memory calibration drift."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_DRIFT_CONFIG_VERSION",
    "ResearchTeamMemoryCalibrationDriftConfig",
    "ResearchTeamMemoryCalibrationDriftReasonCodeCount",
    "ResearchTeamMemoryCalibrationDriftReport",
    "ResearchTeamMemoryCalibrationDriftRow",
    "ResearchTeamMemoryCalibrationFact",
    "build_research_team_memory_calibration_drift_report",
    "research_team_memory_calibration_drift_report_digest",
    "research_team_memory_calibration_drift_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_DRIFT_CONFIG_VERSION = (
    "research-team-memory-calibration-drift-report-v0"
)

NO_FACTS_REASON = "no_team_memory_calibration_facts"
INSUFFICIENT_SAMPLE_REASON = "insufficient_recent_outcome_sample_count"
CALIBRATION_ERROR_BLOCK_REASON = "calibration_error_block"
STALE_MEMORY_BLOCK_REASON = "stale_memory_pressure_block"
FEEDBACK_BACKLOG_BLOCK_REASON = "unresolved_feedback_backlog_block"
MANUAL_RECHECK_BLOCK_REASON = "manual_recheck_urgency_block"
CALIBRATION_ERROR_WATCH_REASON = "calibration_error_watch"
STALE_MEMORY_WATCH_REASON = "stale_memory_pressure_watch"
FEEDBACK_BACKLOG_WATCH_REASON = "unresolved_feedback_backlog_watch"
MANUAL_RECHECK_WATCH_REASON = "manual_recheck_urgency_watch"
BLOCK_REASON = "memory_calibration_drift_block"
WATCH_REASON = "memory_calibration_drift_watch"
PASS_REASON = "memory_calibration_drift_pass"

REASON_CODES = (
    NO_FACTS_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    STALE_MEMORY_BLOCK_REASON,
    FEEDBACK_BACKLOG_BLOCK_REASON,
    MANUAL_RECHECK_BLOCK_REASON,
    CALIBRATION_ERROR_WATCH_REASON,
    STALE_MEMORY_WATCH_REASON,
    FEEDBACK_BACKLOG_WATCH_REASON,
    MANUAL_RECHECK_WATCH_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (
    INSUFFICIENT_SAMPLE_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    STALE_MEMORY_BLOCK_REASON,
    FEEDBACK_BACKLOG_BLOCK_REASON,
    MANUAL_RECHECK_BLOCK_REASON,
    BLOCK_REASON,
    NO_FACTS_REASON,
)
WATCH_REASONS = (
    CALIBRATION_ERROR_WATCH_REASON,
    STALE_MEMORY_WATCH_REASON,
    FEEDBACK_BACKLOG_WATCH_REASON,
    MANUAL_RECHECK_WATCH_REASON,
    WATCH_REASON,
)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {status: index for index, status in enumerate(STATUSES)}
ZERO = Decimal("0")
ONE_COUNT = Decimal("1")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
SAFE_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_KEY_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "question",
    "raw_candidate",
    "raw_market",
    "slug",
    "source_text",
    "source_url",
    "dsn",
    "table",
    "token",
    "private",
    "wallet",
    "account",
    "auth",
    "order",
    "recommendation",
    "sizing",
)
UNSAFE_TEXT_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "candidate_id",
    "market_id",
    "market_slug",
    "dsn",
    "token",
    "bearer ",
    "private",
    "wallet",
    "order",
    "recommendation",
    "sizing",
)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationDriftConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_DRIFT_CONFIG_VERSION
    min_recent_outcome_sample_count: Decimal = Decimal("12")
    calibration_error_watch_threshold: Decimal = Decimal("0.075000")
    calibration_error_block_threshold: Decimal = Decimal("0.150000")
    stale_memory_pressure_watch_threshold: Decimal = Decimal("0.450000")
    stale_memory_pressure_block_threshold: Decimal = Decimal("0.800000")
    unresolved_feedback_backlog_watch_threshold: Decimal = Decimal("3")
    unresolved_feedback_backlog_block_threshold: Decimal = Decimal("8")
    manual_recheck_urgency_watch_threshold: Decimal = Decimal("0.500000")
    manual_recheck_urgency_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryCalibrationDriftConfig:
            raise TypeError(
                "ResearchTeamMemoryCalibrationDriftConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryCalibrationDriftConfig:
            raise ValueError(
                "config must be exactly ResearchTeamMemoryCalibrationDriftConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_recent_outcome_sample_count",
            _require_positive_whole_decimal(
                "min_recent_outcome_sample_count",
                self.min_recent_outcome_sample_count,
            ),
        )
        for field_name in (
            "calibration_error_watch_threshold",
            "calibration_error_block_threshold",
            "stale_memory_pressure_watch_threshold",
            "stale_memory_pressure_block_threshold",
            "manual_recheck_urgency_watch_threshold",
            "manual_recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_feedback_backlog_watch_threshold",
            "unresolved_feedback_backlog_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_below_block(
            "calibration_error",
            self.calibration_error_watch_threshold,
            self.calibration_error_block_threshold,
        )
        _require_watch_below_block(
            "stale_memory_pressure",
            self.stale_memory_pressure_watch_threshold,
            self.stale_memory_pressure_block_threshold,
        )
        _require_watch_below_block(
            "unresolved_feedback_backlog",
            self.unresolved_feedback_backlog_watch_threshold,
            self.unresolved_feedback_backlog_block_threshold,
        )
        _require_watch_below_block(
            "manual_recheck_urgency",
            self.manual_recheck_urgency_watch_threshold,
            self.manual_recheck_urgency_block_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationFact:
    domain_team: str
    recent_outcome_sample_count: Decimal
    calibration_error: Decimal
    stale_memory_pressure: Decimal
    unresolved_feedback_backlog: Decimal
    manual_recheck_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryCalibrationFact:
            raise TypeError(
                "ResearchTeamMemoryCalibrationFact does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryCalibrationFact:
            raise ValueError(
                "fact must be exactly ResearchTeamMemoryCalibrationFact",
            )
        _require_public_identifier("domain_team", self.domain_team)
        object.__setattr__(
            self,
            "recent_outcome_sample_count",
            _require_nonnegative_whole_decimal(
                "recent_outcome_sample_count",
                self.recent_outcome_sample_count,
            ),
        )
        for field_name in (
            "calibration_error",
            "stale_memory_pressure",
            "manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_feedback_backlog",
            _require_nonnegative_whole_decimal(
                "unresolved_feedback_backlog",
                self.unresolved_feedback_backlog,
            ),
        )
        _require_hard_flags("fact", self)
        _reject_unsafe_public_payload("fact", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationDriftRow:
    domain_team: str
    recent_outcome_sample_count: Decimal
    calibration_error: Decimal
    stale_memory_pressure: Decimal
    unresolved_feedback_backlog: Decimal
    manual_recheck_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryCalibrationDriftRow:
            raise TypeError(
                "ResearchTeamMemoryCalibrationDriftRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryCalibrationDriftRow:
            raise ValueError("row must be exactly ResearchTeamMemoryCalibrationDriftRow")
        _require_public_identifier("domain_team", self.domain_team)
        object.__setattr__(
            self,
            "recent_outcome_sample_count",
            _require_nonnegative_whole_decimal(
                "recent_outcome_sample_count",
                self.recent_outcome_sample_count,
            ),
        )
        for field_name in (
            "calibration_error",
            "stale_memory_pressure",
            "manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_feedback_backlog",
            _require_nonnegative_whole_decimal(
                "unresolved_feedback_backlog",
                self.unresolved_feedback_backlog,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryCalibrationDriftReasonCodeCount:
            raise TypeError(
                "ResearchTeamMemoryCalibrationDriftReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryCalibrationDriftReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchTeamMemoryCalibrationDriftReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationDriftReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_team_count: Decimal
    recent_outcome_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_error: Decimal | None
    average_stale_memory_pressure: Decimal | None
    total_unresolved_feedback_backlog: Decimal
    max_manual_recheck_urgency: Decimal | None
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryCalibrationDriftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryCalibrationDriftReport:
            raise TypeError(
                "ResearchTeamMemoryCalibrationDriftReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryCalibrationDriftReport:
            raise ValueError(
                "report must be exactly ResearchTeamMemoryCalibrationDriftReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "domain_team_count",
            "recent_outcome_sample_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_unresolved_feedback_backlog",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_error",
            "average_stale_memory_pressure",
            "max_manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_memory_calibration_drift_report(
    facts: Iterable[object],
    *,
    config: ResearchTeamMemoryCalibrationDriftConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryCalibrationDriftReport:
    if type(config) is not ResearchTeamMemoryCalibrationDriftConfig:
        raise ValueError("config must be a ResearchTeamMemoryCalibrationDriftConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_facts = _normalize_facts(facts)
    rows = tuple(
        sorted(
            (_row_from_fact(fact, config=config) for fact in normalized_facts),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": status,
        "domain_team_count": _decimal_count(len(rows)),
        "recent_outcome_sample_count": sum(
            (row.recent_outcome_sample_count for row in rows),
            ZERO,
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_calibration_error": _weighted_row_average(
            rows,
            "calibration_error",
        ),
        "average_stale_memory_pressure": _weighted_row_average(
            rows,
            "stale_memory_pressure",
        ),
        "total_unresolved_feedback_backlog": sum(
            (row.unresolved_feedback_backlog for row in rows),
            ZERO,
        ),
        "max_manual_recheck_urgency": _max_row_decimal(
            rows,
            "manual_recheck_urgency",
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamMemoryCalibrationDriftReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_memory_calibration_drift_report_payload(
    report: ResearchTeamMemoryCalibrationDriftReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamMemoryCalibrationDriftReport:
        _require_hard_flags("report", report)
        payload = _payload_value(asdict(report))
    elif isinstance(report, Mapping):
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamMemoryCalibrationDriftReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    _require_hard_flags("report payload", _MappingFlags(payload))
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_memory_calibration_drift_report_digest(
    report: ResearchTeamMemoryCalibrationDriftReport | Mapping[str, object],
) -> str:
    payload = research_team_memory_calibration_drift_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


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


def _row_from_fact(
    fact: ResearchTeamMemoryCalibrationFact,
    *,
    config: ResearchTeamMemoryCalibrationDriftConfig,
) -> ResearchTeamMemoryCalibrationDriftRow:
    reason_codes = _row_reason_codes(fact, config=config)
    return ResearchTeamMemoryCalibrationDriftRow(
        domain_team=fact.domain_team,
        recent_outcome_sample_count=fact.recent_outcome_sample_count,
        calibration_error=fact.calibration_error,
        stale_memory_pressure=fact.stale_memory_pressure,
        unresolved_feedback_backlog=fact.unresolved_feedback_backlog,
        manual_recheck_urgency=fact.manual_recheck_urgency,
        status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    fact: ResearchTeamMemoryCalibrationFact,
    *,
    config: ResearchTeamMemoryCalibrationDriftConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if fact.recent_outcome_sample_count < config.min_recent_outcome_sample_count:
        reason_codes.append(INSUFFICIENT_SAMPLE_REASON)
    if fact.calibration_error >= config.calibration_error_block_threshold:
        reason_codes.append(CALIBRATION_ERROR_BLOCK_REASON)
    elif fact.calibration_error >= config.calibration_error_watch_threshold:
        reason_codes.append(CALIBRATION_ERROR_WATCH_REASON)
    if fact.stale_memory_pressure >= config.stale_memory_pressure_block_threshold:
        reason_codes.append(STALE_MEMORY_BLOCK_REASON)
    elif fact.stale_memory_pressure >= config.stale_memory_pressure_watch_threshold:
        reason_codes.append(STALE_MEMORY_WATCH_REASON)
    if (
        fact.unresolved_feedback_backlog
        >= config.unresolved_feedback_backlog_block_threshold
    ):
        reason_codes.append(FEEDBACK_BACKLOG_BLOCK_REASON)
    elif (
        fact.unresolved_feedback_backlog
        >= config.unresolved_feedback_backlog_watch_threshold
    ):
        reason_codes.append(FEEDBACK_BACKLOG_WATCH_REASON)
    if fact.manual_recheck_urgency >= config.manual_recheck_urgency_block_threshold:
        reason_codes.append(MANUAL_RECHECK_BLOCK_REASON)
    elif fact.manual_recheck_urgency >= config.manual_recheck_urgency_watch_threshold:
        reason_codes.append(MANUAL_RECHECK_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    else:
        status = _status_for_reason_codes(tuple(reason_codes))
        reason_codes.append(BLOCK_REASON if status == "block" else WATCH_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _normalize_facts(
    facts: Iterable[object],
) -> tuple[ResearchTeamMemoryCalibrationFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        values = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    normalized: list[ResearchTeamMemoryCalibrationFact] = []
    seen_domain_teams: set[str] = set()
    for value in values:
        if type(value) is not ResearchTeamMemoryCalibrationFact:
            raise ValueError("facts must contain ResearchTeamMemoryCalibrationFact items")
        _require_hard_flags("fact", value)
        if value.domain_team in seen_domain_teams:
            raise ValueError("domain_team values must be unique")
        seen_domain_teams.add(value.domain_team)
        normalized.append(value)
    return tuple(normalized)


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_FACTS_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemoryCalibrationDriftReasonCodeCount, ...]:
    if reason_codes == (NO_FACTS_REASON,):
        return (
            ResearchTeamMemoryCalibrationDriftReasonCodeCount(
                reason_code=NO_FACTS_REASON,
                count=ONE_COUNT,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchTeamMemoryCalibrationDriftReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_report(report: ResearchTeamMemoryCalibrationDriftReport) -> None:
    if report.domain_team_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_team_count must match rows")
    if report.recent_outcome_sample_count != sum(
        (row.recent_outcome_sample_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("recent_outcome_sample_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_calibration_error != _weighted_row_average(
        report.rows,
        "calibration_error",
    ):
        raise ValueError("average_calibration_error must match rows")
    if report.average_stale_memory_pressure != _weighted_row_average(
        report.rows,
        "stale_memory_pressure",
    ):
        raise ValueError("average_stale_memory_pressure must match rows")
    if report.total_unresolved_feedback_backlog != sum(
        (row.unresolved_feedback_backlog for row in report.rows),
        ZERO,
    ):
        raise ValueError("total_unresolved_feedback_backlog must match rows")
    if report.max_manual_recheck_urgency != _max_row_decimal(
        report.rows,
        "manual_recheck_urgency",
    ):
        raise ValueError("max_manual_recheck_urgency must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...],
) -> tuple[ResearchTeamMemoryCalibrationDriftRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_domain_teams: set[str] = set()
    for row in normalized_rows:
        if type(row) is not ResearchTeamMemoryCalibrationDriftRow:
            raise ValueError("rows must contain ResearchTeamMemoryCalibrationDriftRow")
        _require_hard_flags("row", row)
        if row.domain_team in seen_domain_teams:
            raise ValueError("rows domain_team values must be unique")
        seen_domain_teams.add(row.domain_team)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized_rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamMemoryCalibrationDriftReasonCodeCount, ...],
) -> tuple[ResearchTeamMemoryCalibrationDriftReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not ResearchTeamMemoryCalibrationDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemoryCalibrationDriftReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized_counts != tuple(
        sorted(normalized_counts, key=lambda count: REASON_CODE_RANK[count.reason_code])
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized_counts


def _row_sort_key(row: ResearchTeamMemoryCalibrationDriftRow) -> tuple[int, str]:
    return (STATUS_RANK[row.status], row.domain_team)


def _status_count(
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _weighted_row_average(
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    total_weight = sum((row.recent_outcome_sample_count for row in rows), ZERO)
    if total_weight == ZERO:
        return _average_decimal(tuple(getattr(row, field_name) for row in rows))
    weighted_total = sum(
        (
            getattr(row, field_name) * row.recent_outcome_sample_count
            for row in rows
        ),
        ZERO,
    )
    return _quantize_ratio(weighted_total / total_weight)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _max_row_decimal(
    rows: tuple[ResearchTeamMemoryCalibrationDriftRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return max(getattr(row, field_name) for row in rows)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _require_watch_below_block(
    metric_name: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold >= block_threshold:
        raise ValueError(f"{metric_name} watch threshold must be below block threshold")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = value.lower()
    if normalized != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_RANK:
        raise ValueError(f"{field_name} must be a known reason code")
    if any(character not in SAFE_REASON_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    stable_codes = tuple(
        reason_code for reason_code in REASON_CODES if reason_code in reason_codes
    )
    if stable_codes != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value.quantize(COUNT_QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != _ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


_ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchTeamMemoryCalibrationDriftReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload(
        "digest payload",
        payload,
        allow_json_containers=True,
    )
    return _digest_from_unsigned_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(unsigned)


def _digest_from_unsigned_payload(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return _payload_mapping(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_mapping(value: Mapping[Any, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        payload[key] = _payload_value(item)
    return payload


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_unsafe_key(key):
                raise ValueError(f"unsafe field in {label}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple) or (allow_json_containers and isinstance(value, list)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_text(value):
        raise ValueError(f"{label} has unsafe value")


def _has_unsafe_key(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_KEY_FRAGMENTS)


def _has_unsafe_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)
