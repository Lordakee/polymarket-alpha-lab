"""Report-only rollup for sanitized team event-domain memory health."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_EVENT_DOMAIN_MEMORY_ROLLUP_REPORT_CONFIG_VERSION = (
    "research-team-event-domain-memory-rollup-report-v0"
)
EVENT_DOMAIN_MEMORY_ROLLUP_STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PASS_ROW_REASON_CODE = "event_domain_memory_pass"
EMPTY_REPORT_REASON_CODE = "event_domain_memory_rollup_empty"
BLOCK_REASON_CODES = (
    "calibration_freshness_block",
    "feedback_absorption_block",
    "evidence_coverage_block",
    "review_backlog_block",
    "event_domain_memory_health_block",
)
WATCH_REASON_CODES = (
    "calibration_freshness_watch",
    "feedback_absorption_watch",
    "evidence_coverage_watch",
    "review_backlog_watch",
    "event_domain_memory_health_watch",
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PRIORITY = BLOCK_REASON_CODES + WATCH_REASON_CODES
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate" "_" "id",
        "market" "_" "id",
        "market" "_" "slug",
        "ques" "tion",
        "source" "_" "url",
        "source" "_" "text",
        "src" "_" "url",
        "src" "_" "text",
        "dsn",
        "table" "_" "name",
        "tok" "en",
        "wal" "let",
        "acc" "ount",
        "or" "der",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "clob",
        "au" "th",
        "net" "work",
        "reco" "mmend",
        "siz" "ing",
        "ad" "vice",
        "tr" "ade",
        "li" "ve",
        "tr" "ading",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_EVENT_DOMAIN_MEMORY_ROLLUP_REPORT_CONFIG_VERSION",
    "EVENT_DOMAIN_MEMORY_ROLLUP_STATUSES",
    "ResearchTeamEventDomainMemoryRollupConfig",
    "ResearchTeamEventDomainMemoryRollupInput",
    "ResearchTeamEventDomainMemoryRollupReport",
    "ResearchTeamEventDomainMemoryRollupRow",
    "build_research_team_event_domain_memory_rollup_report",
    "research_team_event_domain_memory_rollup_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamEventDomainMemoryRollupConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_EVENT_DOMAIN_MEMORY_ROLLUP_REPORT_CONFIG_VERSION
    )
    pass_health_threshold: Decimal = Decimal("0.850000")
    watch_health_threshold: Decimal = Decimal("0.650000")
    calibration_watch_threshold: Decimal = Decimal("0.700000")
    calibration_block_threshold: Decimal = Decimal("0.400000")
    feedback_watch_threshold: Decimal = Decimal("0.700000")
    feedback_block_threshold: Decimal = Decimal("0.400000")
    evidence_watch_threshold: Decimal = Decimal("0.700000")
    evidence_block_threshold: Decimal = Decimal("0.400000")
    review_backlog_watch_count: Decimal = Decimal("5")
    review_backlog_block_count: Decimal = Decimal("12")
    calibration_weight: Decimal = Decimal("0.300000")
    feedback_weight: Decimal = Decimal("0.250000")
    evidence_weight: Decimal = Decimal("0.300000")
    backlog_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamEventDomainMemoryRollupConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamEventDomainMemoryRollupConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_EVENT_DOMAIN_MEMORY_ROLLUP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "pass_health_threshold",
            "watch_health_threshold",
            "calibration_watch_threshold",
            "calibration_block_threshold",
            "feedback_watch_threshold",
            "feedback_block_threshold",
            "evidence_watch_threshold",
            "evidence_block_threshold",
            "calibration_weight",
            "feedback_weight",
            "evidence_weight",
            "backlog_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("review_backlog_watch_count", "review_backlog_block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamEventDomainMemoryRollupInput:
    domain_key: str
    calibration_freshness_ratio: Decimal
    feedback_absorption_ratio: Decimal
    evidence_coverage_ratio: Decimal
    review_backlog_count: Decimal
    observed_at: datetime
    sanitized_memory_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamEventDomainMemoryRollupInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamEventDomainMemoryRollupInput, "input")
        _require_domain_key("domain_key", self.domain_key)
        for field_name in (
            "calibration_freshness_ratio",
            "feedback_absorption_ratio",
            "evidence_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_backlog_count",
            _require_count_decimal("review_backlog_count", self.review_backlog_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.sanitized_memory_confirmed is not True:
            raise ValueError("sanitized_memory_confirmed must be True")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamEventDomainMemoryRollupRow:
    domain_key: str
    calibration_freshness_ratio: Decimal
    feedback_absorption_ratio: Decimal
    evidence_coverage_ratio: Decimal
    review_backlog_count: Decimal
    backlog_health_score: Decimal
    domain_memory_health_score: Decimal
    row_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamEventDomainMemoryRollupRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamEventDomainMemoryRollupRow, "row")
        _require_domain_key("domain_key", self.domain_key)
        for field_name in (
            "calibration_freshness_ratio",
            "feedback_absorption_ratio",
            "evidence_coverage_ratio",
            "backlog_health_score",
            "domain_memory_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_backlog_count",
            _require_count_decimal("review_backlog_count", self.review_backlog_count),
        )
        _require_status("row_status", self.row_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamEventDomainMemoryRollupReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    fresh_calibration_domain_count: Decimal
    feedback_absorbed_domain_count: Decimal
    evidence_ready_domain_count: Decimal
    max_review_backlog_count: Decimal
    average_domain_memory_health_score: Decimal
    lowest_domain_memory_health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamEventDomainMemoryRollupRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamEventDomainMemoryRollupReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamEventDomainMemoryRollupReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_EVENT_DOMAIN_MEMORY_ROLLUP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "fresh_calibration_domain_count",
            "feedback_absorbed_domain_count",
            "evidence_ready_domain_count",
            "max_review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_domain_memory_health_score",
            "lowest_domain_memory_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report_status(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_event_domain_memory_rollup_report_payload(self)


def build_research_team_event_domain_memory_rollup_report(
    domain_items: Iterable[ResearchTeamEventDomainMemoryRollupInput],
    *,
    config: ResearchTeamEventDomainMemoryRollupConfig,
    generated_at: datetime,
) -> ResearchTeamEventDomainMemoryRollupReport:
    if type(config) is not ResearchTeamEventDomainMemoryRollupConfig:
        raise ValueError("config must be a ResearchTeamEventDomainMemoryRollupConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(domain_items)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.row_status for row in rows))
    return ResearchTeamEventDomainMemoryRollupReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        fresh_calibration_domain_count=_count(
            sum(
                1
                for row in rows
                if row.calibration_freshness_ratio >= config.calibration_watch_threshold
            ),
        ),
        feedback_absorbed_domain_count=_count(
            sum(
                1
                for row in rows
                if row.feedback_absorption_ratio >= config.feedback_watch_threshold
            ),
        ),
        evidence_ready_domain_count=_count(
            sum(
                1
                for row in rows
                if row.evidence_coverage_ratio >= config.evidence_watch_threshold
            ),
        ),
        max_review_backlog_count=_max_count(
            tuple(row.review_backlog_count for row in rows),
        ),
        average_domain_memory_health_score=_average_score(rows),
        lowest_domain_memory_health_score=_lowest_score(rows),
        status=status,
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_team_event_domain_memory_rollup_report_payload(
    report: ResearchTeamEventDomainMemoryRollupReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamEventDomainMemoryRollupReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchTeamEventDomainMemoryRollupReport")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_input(
    item: ResearchTeamEventDomainMemoryRollupInput,
    *,
    config: ResearchTeamEventDomainMemoryRollupConfig,
    generated_at: datetime,
) -> ResearchTeamEventDomainMemoryRollupRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    backlog_health_score = _backlog_health_score(
        item.review_backlog_count,
        config=config,
    )
    health_score = _domain_memory_health_score(
        item,
        backlog_health_score=backlog_health_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        health_score=health_score,
        config=config,
    )
    return ResearchTeamEventDomainMemoryRollupRow(
        domain_key=item.domain_key,
        calibration_freshness_ratio=item.calibration_freshness_ratio,
        feedback_absorption_ratio=item.feedback_absorption_ratio,
        evidence_coverage_ratio=item.evidence_coverage_ratio,
        review_backlog_count=item.review_backlog_count,
        backlog_health_score=backlog_health_score,
        domain_memory_health_score=health_score,
        row_status=_row_status(reason_codes),
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _backlog_health_score(
    review_backlog_count: Decimal,
    *,
    config: ResearchTeamEventDomainMemoryRollupConfig,
) -> Decimal:
    if review_backlog_count >= config.review_backlog_block_count:
        return ZERO_RATIO
    if review_backlog_count <= config.review_backlog_watch_count:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        span = config.review_backlog_block_count - config.review_backlog_watch_count
        used = review_backlog_count - config.review_backlog_watch_count
        return (ONE_RATIO - (used / span)).quantize(RATIO_QUANTUM)


def _domain_memory_health_score(
    item: ResearchTeamEventDomainMemoryRollupInput,
    *,
    backlog_health_score: Decimal,
    config: ResearchTeamEventDomainMemoryRollupConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            item.calibration_freshness_ratio * config.calibration_weight
            + item.feedback_absorption_ratio * config.feedback_weight
            + item.evidence_coverage_ratio * config.evidence_weight
            + backlog_health_score * config.backlog_weight
        ).quantize(RATIO_QUANTUM)


def _row_reason_codes(
    item: ResearchTeamEventDomainMemoryRollupInput,
    *,
    health_score: Decimal,
    config: ResearchTeamEventDomainMemoryRollupConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.calibration_freshness_ratio < config.calibration_block_threshold:
        reason_codes.append("calibration_freshness_block")
    elif item.calibration_freshness_ratio < config.calibration_watch_threshold:
        reason_codes.append("calibration_freshness_watch")

    if item.feedback_absorption_ratio < config.feedback_block_threshold:
        reason_codes.append("feedback_absorption_block")
    elif item.feedback_absorption_ratio < config.feedback_watch_threshold:
        reason_codes.append("feedback_absorption_watch")

    if item.evidence_coverage_ratio < config.evidence_block_threshold:
        reason_codes.append("evidence_coverage_block")
    elif item.evidence_coverage_ratio < config.evidence_watch_threshold:
        reason_codes.append("evidence_coverage_watch")

    if item.review_backlog_count >= config.review_backlog_block_count:
        reason_codes.append("review_backlog_block")
    elif item.review_backlog_count >= config.review_backlog_watch_count:
        reason_codes.append("review_backlog_watch")

    if not reason_codes:
        if health_score < config.watch_health_threshold:
            reason_codes.append("event_domain_memory_health_block")
        elif health_score < config.pass_health_threshold:
            reason_codes.append("event_domain_memory_health_watch")

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamEventDomainMemoryRollupRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.row_status for row in rows))
    reason_codes = [f"event_domain_memory_rollup_{status}"]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _row_sort_key(
    row: ResearchTeamEventDomainMemoryRollupRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.row_status],
        row.domain_memory_health_score,
        row.domain_key,
    )


def _status_count(
    rows: tuple[ResearchTeamEventDomainMemoryRollupRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == status))


def _average_score(rows: tuple[ResearchTeamEventDomainMemoryRollupRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum(
                (row.domain_memory_health_score for row in rows),
                ZERO_RATIO,
            )
            / Decimal(len(rows))
        ).quantize(RATIO_QUANTUM)


def _lowest_score(rows: tuple[ResearchTeamEventDomainMemoryRollupRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(row.domain_memory_health_score for row in rows).quantize(RATIO_QUANTUM)


def _max_count(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_COUNT
    return max(values).quantize(COUNT_QUANTUM)


def _normalize_inputs(
    domain_items: Iterable[ResearchTeamEventDomainMemoryRollupInput],
) -> tuple[ResearchTeamEventDomainMemoryRollupInput, ...]:
    if isinstance(domain_items, (str, bytes)):
        raise ValueError("domain_items must be an iterable")
    try:
        items = tuple(domain_items)
    except TypeError as exc:
        raise ValueError("domain_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamEventDomainMemoryRollupInput:
            raise ValueError(
                "domain_items must contain ResearchTeamEventDomainMemoryRollupInput",
            )
        _require_hard_flags("input", item)
        if item.domain_key in seen:
            raise ValueError("domain_key values must be unique")
        seen.add(item.domain_key)
    return items


def _validate_config(config: ResearchTeamEventDomainMemoryRollupConfig) -> None:
    if config.pass_health_threshold < config.watch_health_threshold:
        raise ValueError("pass_health_threshold must be at least watch threshold")
    if config.calibration_watch_threshold < config.calibration_block_threshold:
        raise ValueError("calibration watch threshold must be at least block threshold")
    if config.feedback_watch_threshold < config.feedback_block_threshold:
        raise ValueError("feedback watch threshold must be at least block threshold")
    if config.evidence_watch_threshold < config.evidence_block_threshold:
        raise ValueError("evidence watch threshold must be at least block threshold")
    if config.review_backlog_block_count < config.review_backlog_watch_count:
        raise ValueError("review backlog block threshold must be at least watch threshold")
    if config.review_backlog_block_count <= ZERO_COUNT:
        raise ValueError("review backlog block threshold must be positive")
    if (
        _quantize_ratio(
            config.calibration_weight
            + config.feedback_weight
            + config.evidence_weight
            + config.backlog_weight,
        )
        != ONE_RATIO
    ):
        raise ValueError("domain memory health weights must sum to one")


def _validate_row(row: ResearchTeamEventDomainMemoryRollupRow) -> None:
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    if row.row_status == "pass" and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require event_domain_memory_pass")
    if row.row_status != "pass" and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("non-pass rows must not contain pass reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamEventDomainMemoryRollupReport,
) -> None:
    rows = report.rows
    checks = {
        "domain_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_review_backlog_count": _max_count(
            tuple(row.review_backlog_count for row in rows),
        ),
        "average_domain_memory_health_score": _average_score(rows),
        "lowest_domain_memory_health_score": _lowest_score(rows),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.domain_count:
        raise ValueError("status counts must match domain_count")
    _validate_report_status(report)
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_status(report: ResearchTeamEventDomainMemoryRollupReport) -> None:
    expected_status = _rollup_status(tuple(row.row_status for row in report.rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _require_rows(
    rows: tuple[ResearchTeamEventDomainMemoryRollupRow, ...],
) -> tuple[ResearchTeamEventDomainMemoryRollupRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamEventDomainMemoryRollupRow:
            raise ValueError(
                "rows must contain ResearchTeamEventDomainMemoryRollupRow",
            )
        _require_hard_flags("row", row)
        if row.domain_key in seen:
            raise ValueError("rows must contain unique domain_key values")
        seen.add(row.domain_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and health")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_domain_key(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{field_name} must be public-safe")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{field_name} must be public-safe")


def _require_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(reason_codes, require_nonempty=True)
    for reason_code in normalized:
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(reason_codes, require_nonempty=True)
    for reason_code in normalized:
        if not (
            reason_code in REPORT_REASON_PRIORITY
            or reason_code == EMPTY_REPORT_REASON_CODE
            or reason_code.startswith("event_domain_memory_rollup_")
        ):
            raise ValueError("reason_code must be supported")
    return normalized


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code.lower() != reason_code:
            raise ValueError("reason_code must be lowercase")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in EVENT_DOMAIN_MEMORY_ROLLUP_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(normalized)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamEventDomainMemoryRollupReport,
) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(
    report: ResearchTeamEventDomainMemoryRollupReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            {field.name: getattr(value, field.name) for field in fields(value)},
            path,
        )
        return
    if type(value) is str:
        if _contains_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload at {path or label}")
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _contains_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload at {item_path}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    compacted = "".join(
        character if character.isalnum() else "_"
        for character in lowered
    )
    collapsed = "_".join(part for part in compacted.split("_") if part)
    return (
        "://" in lowered
        or "?" in lowered
        or "@" in lowered
        or any(
            fragment in lowered or fragment in collapsed
            for fragment in UNSAFE_PUBLIC_FRAGMENTS
        )
    )
