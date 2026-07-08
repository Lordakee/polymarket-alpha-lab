"""Public-safe technology event specialist memory readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TECHNOLOGY_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-technology-event-team-memory-report-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PAPER_ACTION_BY_STATUS = {
    "pass": "paper_technology_event_team_memory_monitor",
    "watch": "paper_technology_event_team_memory_watch",
    "block": "paper_technology_event_team_memory_block",
}
PASS_ROW_REASON_CODE = "technology_event_team_memory_ready"
EMPTY_REPORT_REASON_CODE = "technology_event_team_memory_no_inputs"
BLOCK_REASON_CODES = (
    "technology_specialist_coverage_block",
    "technology_playbook_coverage_block",
    "source_freshness_block",
    "evidence_reuse_block",
    "calibration_sample_block",
    "calibration_error_block",
)
WATCH_REASON_CODES = (
    "technology_specialist_coverage_watch",
    "technology_playbook_coverage_watch",
    "source_freshness_watch",
    "evidence_reuse_watch",
    "calibration_sample_watch",
    "calibration_error_watch",
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PRIORITY = BLOCK_REASON_CODES + WATCH_REASON_CODES
HEX_CHARS = frozenset("0123456789abcdef")


def _join(left: str, right: str) -> str:
    return left + right


UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "candidate_id",
        "source_id",
        "source_reference",
        "source_url",
        "raw_event_identifier",
        "raw_source_identifier",
        "raw_text",
        _join("wal", "let_address"),
        _join("or", "der_id"),
        _join("tra", "de_id"),
        _join("li", "ve_url"),
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "event id",
        "event slug",
        "market id",
        "market slug",
        "candidate id",
        "source id",
        "source reference",
        "source url",
        "raw event identifier",
        "raw source identifier",
        "raw source text",
        "private-url",
        "://",
        _join("wal", "let"),
        _join("bro", "ker"),
        _join("sig", "ning"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("acc", "ount"),
        _join("net", "work"),
        _join("data", "base"),
        _join("li", "ve"),
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_TECHNOLOGY_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "ResearchTechnologyEventTeamMemoryConfig",
    "ResearchTechnologyEventTeamMemoryInput",
    "ResearchTechnologyEventTeamMemoryReasonCodeCount",
    "ResearchTechnologyEventTeamMemoryReport",
    "ResearchTechnologyEventTeamMemoryRow",
    "build_research_technology_event_team_memory_report",
    "research_technology_event_team_memory_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTechnologyEventTeamMemoryConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TECHNOLOGY_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    watch_min_specialist_count: Decimal = Decimal("2")
    block_min_specialist_count: Decimal = Decimal("1")
    watch_min_playbook_count: Decimal = Decimal("2")
    block_min_playbook_count: Decimal = Decimal("1")
    watch_min_calibration_sample_count: Decimal = Decimal("30")
    block_min_calibration_sample_count: Decimal = Decimal("10")
    watch_max_latest_source_age_hours: Decimal = Decimal("24.000000")
    block_max_latest_source_age_hours: Decimal = Decimal("72.000000")
    watch_min_source_freshness_ratio: Decimal = Decimal("0.800000")
    block_min_source_freshness_ratio: Decimal = Decimal("0.400000")
    watch_min_evidence_reuse_ratio: Decimal = Decimal("0.700000")
    block_min_evidence_reuse_ratio: Decimal = Decimal("0.300000")
    watch_max_calibration_error_ratio: Decimal = Decimal("0.120000")
    block_max_calibration_error_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTechnologyEventTeamMemoryConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TECHNOLOGY_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_min_specialist_count",
            "block_min_specialist_count",
            "watch_min_playbook_count",
            "block_min_playbook_count",
            "watch_min_calibration_sample_count",
            "block_min_calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_max_latest_source_age_hours",
            "block_max_latest_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_source_freshness_ratio",
            "block_min_source_freshness_ratio",
            "watch_min_evidence_reuse_ratio",
            "block_min_evidence_reuse_ratio",
            "watch_max_calibration_error_ratio",
            "block_max_calibration_error_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTechnologyEventTeamMemoryInput(_FinalPublicDataclass):
    team_label: str
    event_family_label: str
    specialist_count: Decimal
    playbook_count: Decimal
    calibration_sample_count: Decimal
    latest_source_age_hours: Decimal
    source_freshness_ratio: Decimal
    evidence_reuse_ratio: Decimal
    calibration_error_ratio: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTechnologyEventTeamMemoryInput, "input")
        _require_safe_public_string("team_label", self.team_label)
        _require_safe_public_string("event_family_label", self.event_family_label)
        for field_name in (
            "specialist_count",
            "playbook_count",
            "calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_age_hours",
            _require_nonnegative_decimal(
                "latest_source_age_hours",
                self.latest_source_age_hours,
            ),
        )
        for field_name in (
            "source_freshness_ratio",
            "evidence_reuse_ratio",
            "calibration_error_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTechnologyEventTeamMemoryRow(_FinalPublicDataclass):
    team_label: str
    event_family_label: str
    memory_status: str
    specialist_count: Decimal
    playbook_count: Decimal
    calibration_sample_count: Decimal
    latest_source_age_hours: Decimal
    source_freshness_ratio: Decimal
    evidence_reuse_ratio: Decimal
    calibration_error_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTechnologyEventTeamMemoryRow, "row")
        _require_safe_public_string("team_label", self.team_label)
        _require_safe_public_string("event_family_label", self.event_family_label)
        _require_status("memory_status", self.memory_status)
        for field_name in (
            "specialist_count",
            "playbook_count",
            "calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_age_hours",
            _require_nonnegative_decimal(
                "latest_source_age_hours",
                self.latest_source_age_hours,
            ),
        )
        for field_name in (
            "source_freshness_ratio",
            "evidence_reuse_ratio",
            "calibration_error_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTechnologyEventTeamMemoryReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTechnologyEventTeamMemoryReasonCodeCount,
            "count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("count", self)


@dataclass(frozen=True)
class ResearchTechnologyEventTeamMemoryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_specialist_count: Decimal
    min_playbook_count: Decimal
    min_calibration_sample_count: Decimal
    max_latest_source_age_hours: Decimal
    min_source_freshness_ratio: Decimal
    min_evidence_reuse_ratio: Decimal
    max_calibration_error_ratio: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTechnologyEventTeamMemoryReasonCodeCount, ...]
    rows: tuple[ResearchTechnologyEventTeamMemoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTechnologyEventTeamMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TECHNOLOGY_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_specialist_count",
            "min_playbook_count",
            "min_calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_source_age_hours",
            _require_nonnegative_decimal(
                "max_latest_source_age_hours",
                self.max_latest_source_age_hours,
            ),
        )
        for field_name in (
            "min_source_freshness_ratio",
            "min_evidence_reuse_ratio",
            "max_calibration_error_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
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
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_technology_event_team_memory_report(
    memory_items: Iterable[ResearchTechnologyEventTeamMemoryInput],
    *,
    config: ResearchTechnologyEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchTechnologyEventTeamMemoryReport:
    if type(config) is not ResearchTechnologyEventTeamMemoryConfig:
        raise ValueError("config must be a ResearchTechnologyEventTeamMemoryConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_items)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.memory_status for row in rows))
    return ResearchTechnologyEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        min_specialist_count=_min_decimal(
            tuple(row.specialist_count for row in rows),
            count=True,
        ),
        min_playbook_count=_min_decimal(
            tuple(row.playbook_count for row in rows),
            count=True,
        ),
        min_calibration_sample_count=_min_decimal(
            tuple(row.calibration_sample_count for row in rows),
            count=True,
        ),
        max_latest_source_age_hours=_max_decimal(
            tuple(row.latest_source_age_hours for row in rows),
        ),
        min_source_freshness_ratio=_min_decimal(
            tuple(row.source_freshness_ratio for row in rows),
        ),
        min_evidence_reuse_ratio=_min_decimal(
            tuple(row.evidence_reuse_ratio for row in rows),
        ),
        max_calibration_error_ratio=_max_decimal(
            tuple(row.calibration_error_ratio for row in rows),
        ),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_technology_event_team_memory_report_payload(
    report: ResearchTechnologyEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTechnologyEventTeamMemoryReport:
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
    raise ValueError("report must be a ResearchTechnologyEventTeamMemoryReport")


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


def _normalize_inputs(
    memory_items: Iterable[ResearchTechnologyEventTeamMemoryInput],
) -> tuple[ResearchTechnologyEventTeamMemoryInput, ...]:
    if isinstance(memory_items, (str, bytes)):
        raise ValueError("memory_items must be an iterable")
    try:
        items = tuple(memory_items)
    except TypeError as exc:
        raise ValueError("memory_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTechnologyEventTeamMemoryInput:
            raise ValueError(
                "memory_items must contain ResearchTechnologyEventTeamMemoryInput",
            )
        _require_hard_flags("input", item)
        if item.team_label in seen:
            raise ValueError("team_label values must be unique")
        seen.add(item.team_label)
    return items


def _row_from_input(
    item: ResearchTechnologyEventTeamMemoryInput,
    *,
    config: ResearchTechnologyEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchTechnologyEventTeamMemoryRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchTechnologyEventTeamMemoryRow(
        team_label=item.team_label,
        event_family_label=item.event_family_label,
        memory_status=_row_status(reason_codes),
        specialist_count=item.specialist_count,
        playbook_count=item.playbook_count,
        calibration_sample_count=item.calibration_sample_count,
        latest_source_age_hours=item.latest_source_age_hours,
        source_freshness_ratio=item.source_freshness_ratio,
        evidence_reuse_ratio=item.evidence_reuse_ratio,
        calibration_error_ratio=item.calibration_error_ratio,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTechnologyEventTeamMemoryInput,
    *,
    config: ResearchTechnologyEventTeamMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.specialist_count < config.block_min_specialist_count:
        reason_codes.append("technology_specialist_coverage_block")
    elif item.specialist_count < config.watch_min_specialist_count:
        reason_codes.append("technology_specialist_coverage_watch")

    if item.playbook_count < config.block_min_playbook_count:
        reason_codes.append("technology_playbook_coverage_block")
    elif item.playbook_count < config.watch_min_playbook_count:
        reason_codes.append("technology_playbook_coverage_watch")

    if (
        item.latest_source_age_hours >= config.block_max_latest_source_age_hours
        or item.source_freshness_ratio < config.block_min_source_freshness_ratio
    ):
        reason_codes.append("source_freshness_block")
    elif (
        item.latest_source_age_hours >= config.watch_max_latest_source_age_hours
        or item.source_freshness_ratio < config.watch_min_source_freshness_ratio
    ):
        reason_codes.append("source_freshness_watch")

    if item.evidence_reuse_ratio < config.block_min_evidence_reuse_ratio:
        reason_codes.append("evidence_reuse_block")
    elif item.evidence_reuse_ratio < config.watch_min_evidence_reuse_ratio:
        reason_codes.append("evidence_reuse_watch")

    if item.calibration_sample_count < config.block_min_calibration_sample_count:
        reason_codes.append("calibration_sample_block")
    elif item.calibration_sample_count < config.watch_min_calibration_sample_count:
        reason_codes.append("calibration_sample_watch")

    if item.calibration_error_ratio >= config.block_max_calibration_error_ratio:
        reason_codes.append("calibration_error_block")
    elif item.calibration_error_ratio >= config.watch_max_calibration_error_ratio:
        reason_codes.append("calibration_error_watch")

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
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTechnologyEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.memory_status for row in rows))
    reason_codes = [
        f"technology_event_team_memory_queue_{'clear' if status == 'pass' else status}",
    ]
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


def _reason_code_counts(
    rows: tuple[ResearchTechnologyEventTeamMemoryRow, ...],
) -> tuple[ResearchTechnologyEventTeamMemoryReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority_map = {
        reason_code: index
        for index, reason_code in enumerate(
            (PASS_ROW_REASON_CODE,) + BLOCK_REASON_CODES + WATCH_REASON_CODES,
        )
    }
    return tuple(
        ResearchTechnologyEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=count,
            team_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority_map.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(row: ResearchTechnologyEventTeamMemoryRow) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.memory_status],
        -_row_severity_score(row),
        row.team_label,
    )


def _row_severity_score(row: ResearchTechnologyEventTeamMemoryRow) -> Decimal:
    severity = STATUS_WEIGHT[row.memory_status]
    severity += row.latest_source_age_hours / Decimal("1000.000000")
    severity += ONE_RATIO - row.source_freshness_ratio
    severity += ONE_RATIO - row.evidence_reuse_ratio
    severity += row.calibration_error_ratio
    return severity


def _status_count(
    rows: tuple[ResearchTechnologyEventTeamMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.memory_status == status))


def _validate_config(config: ResearchTechnologyEventTeamMemoryConfig) -> None:
    min_pairs = (
        ("block_min_specialist_count", "watch_min_specialist_count"),
        ("block_min_playbook_count", "watch_min_playbook_count"),
        ("block_min_calibration_sample_count", "watch_min_calibration_sample_count"),
    )
    for block_name, watch_name in min_pairs:
        if getattr(config, block_name) > getattr(config, watch_name):
            raise ValueError(f"{block_name} must not exceed {watch_name}")
    if config.block_max_latest_source_age_hours < config.watch_max_latest_source_age_hours:
        raise ValueError(
            "block_max_latest_source_age_hours must be at least "
            "watch_max_latest_source_age_hours",
        )
    coverage_pairs = (
        ("block_min_source_freshness_ratio", "watch_min_source_freshness_ratio"),
        ("block_min_evidence_reuse_ratio", "watch_min_evidence_reuse_ratio"),
    )
    for block_name, watch_name in coverage_pairs:
        if getattr(config, block_name) > getattr(config, watch_name):
            raise ValueError(f"{block_name} must not exceed {watch_name}")
    if config.block_max_calibration_error_ratio < config.watch_max_calibration_error_ratio:
        raise ValueError(
            "block_max_calibration_error_ratio must be at least "
            "watch_max_calibration_error_ratio",
        )


def _validate_row(row: ResearchTechnologyEventTeamMemoryRow) -> None:
    if row.memory_status != _row_status(row.reason_codes):
        raise ValueError("memory_status must match reason_codes")
    if row.memory_status == "pass" and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require technology_event_team_memory_ready")
    if row.memory_status != "pass" and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("queued rows must not contain ready reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTechnologyEventTeamMemoryReport,
) -> None:
    rows = report.rows
    checks = {
        "team_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "min_specialist_count": _min_decimal(
            tuple(row.specialist_count for row in rows),
            count=True,
        ),
        "min_playbook_count": _min_decimal(
            tuple(row.playbook_count for row in rows),
            count=True,
        ),
        "min_calibration_sample_count": _min_decimal(
            tuple(row.calibration_sample_count for row in rows),
            count=True,
        ),
        "max_latest_source_age_hours": _max_decimal(
            tuple(row.latest_source_age_hours for row in rows),
        ),
        "min_source_freshness_ratio": _min_decimal(
            tuple(row.source_freshness_ratio for row in rows),
        ),
        "min_evidence_reuse_ratio": _min_decimal(
            tuple(row.evidence_reuse_ratio for row in rows),
        ),
        "max_calibration_error_ratio": _max_decimal(
            tuple(row.calibration_error_ratio for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _rollup_status(tuple(row.memory_status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTechnologyEventTeamMemoryRow, ...],
) -> tuple[ResearchTechnologyEventTeamMemoryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTechnologyEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchTechnologyEventTeamMemoryRow")
        _require_hard_flags("row", row)
        if row.team_label in seen:
            raise ValueError("rows must contain unique team_label values")
        seen.add(row.team_label)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and team_label")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTechnologyEventTeamMemoryReasonCodeCount, ...],
) -> tuple[ResearchTechnologyEventTeamMemoryReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTechnologyEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTechnologyEventTeamMemoryReasonCodeCount",
            )
        _require_hard_flags("count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_safe_public_string(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _require_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(value, require_nonempty=True)
    allowed_prefixes = (
        "technology_event_team_memory_queue_clear",
        "technology_event_team_memory_queue_watch",
        "technology_event_team_memory_queue_block",
        EMPTY_REPORT_REASON_CODE,
    )
    for reason_code in normalized:
        if reason_code in ROW_REASON_CODES or reason_code in allowed_prefixes:
            continue
        raise ValueError("reason_codes contains unknown reason_code")
    return normalized


def _require_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    if len(frozenset(value)) != len(value):
        raise ValueError("reason_codes values must be unique")
    for item in value:
        _require_public_string("reason_code", item)
        if item not in ROW_REASON_CODES and item not in (
            "technology_event_team_memory_queue_clear",
            "technology_event_team_memory_queue_watch",
            "technology_event_team_memory_queue_block",
            EMPTY_REPORT_REASON_CODE,
        ):
            raise ValueError("reason_codes contains unknown reason_code")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values)


def _derived_validation_digest(report: ResearchTechnologyEventTeamMemoryReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned["derived_validation_digest"] = ""
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("floating point values are not allowed")
    if type(value) is int:
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_sha256(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(label, key, key_context=True)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(
    label: str,
    value: str,
    *,
    key_context: bool = False,
) -> None:
    lowered = value.lower()
    fragments = UNSAFE_PUBLIC_KEY_FRAGMENTS if key_context else UNSAFE_PUBLIC_VALUE_FRAGMENTS
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"unsafe public value in {label}")
