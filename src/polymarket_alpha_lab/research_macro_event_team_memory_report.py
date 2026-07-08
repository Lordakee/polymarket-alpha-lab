"""Public-safe macro event specialist memory readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MACRO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-macro-event-team-memory-report-v0"
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
    "pass": "paper_macro_event_team_memory_monitor",
    "watch": "paper_macro_event_team_memory_watch",
    "block": "paper_macro_event_team_memory_block",
}
PASS_ROW_REASON_CODE = "macro_event_team_memory_ready"
EMPTY_REPORT_REASON_CODE = "macro_event_team_memory_no_inputs"
BLOCK_REASON_CODES = (
    "specialist_coverage_block",
    "playbook_coverage_block",
    "calibration_sample_block",
    "memory_staleness_block",
    "evidence_gap_block",
    "evidence_family_coverage_block",
    "analog_case_block",
)
WATCH_REASON_CODES = (
    "specialist_coverage_watch",
    "playbook_coverage_watch",
    "calibration_sample_watch",
    "memory_staleness_watch",
    "evidence_gap_watch",
    "evidence_family_coverage_watch",
    "analog_case_watch",
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
        "market_slug",
        "source_id",
        "source_reference",
        "source_url",
        "raw_event_identifier",
        "raw_source_identifier",
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
        "market slug",
        "source id",
        "source reference",
        "source url",
        "raw event identifier",
        "raw source identifier",
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
    "DEFAULT_RESEARCH_MACRO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "ResearchMacroEventTeamMemoryConfig",
    "ResearchMacroEventTeamMemoryInput",
    "ResearchMacroEventTeamMemoryReasonCodeCount",
    "ResearchMacroEventTeamMemoryReport",
    "ResearchMacroEventTeamMemoryRow",
    "build_research_macro_event_team_memory_report",
    "research_macro_event_team_memory_report_payload",
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
class ResearchMacroEventTeamMemoryConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MACRO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    watch_min_specialist_count: Decimal = Decimal("2")
    block_min_specialist_count: Decimal = Decimal("1")
    watch_min_playbook_count: Decimal = Decimal("2")
    block_min_playbook_count: Decimal = Decimal("1")
    watch_min_calibration_sample_count: Decimal = Decimal("30")
    block_min_calibration_sample_count: Decimal = Decimal("10")
    watch_stale_memory_hours: Decimal = Decimal("72.000000")
    block_stale_memory_hours: Decimal = Decimal("240.000000")
    watch_unresolved_evidence_gap_ratio: Decimal = Decimal("0.150000")
    block_unresolved_evidence_gap_ratio: Decimal = Decimal("0.350000")
    watch_min_evidence_family_coverage_ratio: Decimal = Decimal("0.700000")
    block_min_evidence_family_coverage_ratio: Decimal = Decimal("0.450000")
    watch_min_analog_case_count: Decimal = Decimal("3")
    block_min_analog_case_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMacroEventTeamMemoryConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MACRO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_min_specialist_count",
            "block_min_specialist_count",
            "watch_min_playbook_count",
            "block_min_playbook_count",
            "watch_min_calibration_sample_count",
            "block_min_calibration_sample_count",
            "watch_min_analog_case_count",
            "block_min_analog_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_stale_memory_hours", "block_stale_memory_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_unresolved_evidence_gap_ratio",
            "block_unresolved_evidence_gap_ratio",
            "watch_min_evidence_family_coverage_ratio",
            "block_min_evidence_family_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMacroEventTeamMemoryInput(_FinalPublicDataclass):
    team_key: str
    macro_domain: str
    specialist_count: Decimal
    playbook_count: Decimal
    calibration_sample_count: Decimal
    stale_memory_hours: Decimal
    unresolved_evidence_gap_ratio: Decimal
    evidence_family_coverage_ratio: Decimal
    analog_case_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMacroEventTeamMemoryInput, "input")
        _require_safe_public_string("team_key", self.team_key)
        _require_safe_public_string("macro_domain", self.macro_domain)
        for field_name in (
            "specialist_count",
            "playbook_count",
            "calibration_sample_count",
            "analog_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_memory_hours",
            _require_nonnegative_decimal("stale_memory_hours", self.stale_memory_hours),
        )
        for field_name in (
            "unresolved_evidence_gap_ratio",
            "evidence_family_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMacroEventTeamMemoryRow(_FinalPublicDataclass):
    team_key: str
    macro_domain: str
    memory_status: str
    specialist_count: Decimal
    playbook_count: Decimal
    calibration_sample_count: Decimal
    stale_memory_hours: Decimal
    unresolved_evidence_gap_ratio: Decimal
    evidence_family_coverage_ratio: Decimal
    analog_case_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMacroEventTeamMemoryRow, "row")
        _require_safe_public_string("team_key", self.team_key)
        _require_safe_public_string("macro_domain", self.macro_domain)
        _require_status("memory_status", self.memory_status)
        for field_name in (
            "specialist_count",
            "playbook_count",
            "calibration_sample_count",
            "analog_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_memory_hours",
            _require_nonnegative_decimal("stale_memory_hours", self.stale_memory_hours),
        )
        for field_name in (
            "unresolved_evidence_gap_ratio",
            "evidence_family_coverage_ratio",
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
class ResearchMacroEventTeamMemoryReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMacroEventTeamMemoryReasonCodeCount, "count")
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("count", self)


@dataclass(frozen=True)
class ResearchMacroEventTeamMemoryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_specialist_count: Decimal
    min_playbook_count: Decimal
    min_calibration_sample_count: Decimal
    max_stale_memory_hours: Decimal
    max_unresolved_evidence_gap_ratio: Decimal
    min_evidence_family_coverage_ratio: Decimal
    min_analog_case_count: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMacroEventTeamMemoryReasonCodeCount, ...]
    rows: tuple[ResearchMacroEventTeamMemoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMacroEventTeamMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MACRO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
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
            "min_analog_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stale_memory_hours",
            _require_nonnegative_decimal(
                "max_stale_memory_hours",
                self.max_stale_memory_hours,
            ),
        )
        for field_name in (
            "max_unresolved_evidence_gap_ratio",
            "min_evidence_family_coverage_ratio",
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


def build_research_macro_event_team_memory_report(
    memory_items: Iterable[ResearchMacroEventTeamMemoryInput],
    *,
    config: ResearchMacroEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchMacroEventTeamMemoryReport:
    if type(config) is not ResearchMacroEventTeamMemoryConfig:
        raise ValueError("config must be a ResearchMacroEventTeamMemoryConfig")
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
    return ResearchMacroEventTeamMemoryReport(
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
        max_stale_memory_hours=_max_decimal(tuple(row.stale_memory_hours for row in rows)),
        max_unresolved_evidence_gap_ratio=_max_decimal(
            tuple(row.unresolved_evidence_gap_ratio for row in rows),
        ),
        min_evidence_family_coverage_ratio=_min_decimal(
            tuple(row.evidence_family_coverage_ratio for row in rows),
        ),
        min_analog_case_count=_min_decimal(
            tuple(row.analog_case_count for row in rows),
            count=True,
        ),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_macro_event_team_memory_report_payload(
    report: ResearchMacroEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMacroEventTeamMemoryReport:
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
    raise ValueError("report must be a ResearchMacroEventTeamMemoryReport")


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
    memory_items: Iterable[ResearchMacroEventTeamMemoryInput],
) -> tuple[ResearchMacroEventTeamMemoryInput, ...]:
    if isinstance(memory_items, (str, bytes)):
        raise ValueError("memory_items must be an iterable")
    try:
        items = tuple(memory_items)
    except TypeError as exc:
        raise ValueError("memory_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchMacroEventTeamMemoryInput:
            raise ValueError("memory_items must contain ResearchMacroEventTeamMemoryInput")
        _require_hard_flags("input", item)
        if item.team_key in seen:
            raise ValueError("team_key values must be unique")
        seen.add(item.team_key)
    return items


def _row_from_input(
    item: ResearchMacroEventTeamMemoryInput,
    *,
    config: ResearchMacroEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchMacroEventTeamMemoryRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchMacroEventTeamMemoryRow(
        team_key=item.team_key,
        macro_domain=item.macro_domain,
        memory_status=_row_status(reason_codes),
        specialist_count=item.specialist_count,
        playbook_count=item.playbook_count,
        calibration_sample_count=item.calibration_sample_count,
        stale_memory_hours=item.stale_memory_hours,
        unresolved_evidence_gap_ratio=item.unresolved_evidence_gap_ratio,
        evidence_family_coverage_ratio=item.evidence_family_coverage_ratio,
        analog_case_count=item.analog_case_count,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMacroEventTeamMemoryInput,
    *,
    config: ResearchMacroEventTeamMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.specialist_count < config.block_min_specialist_count:
        reason_codes.append("specialist_coverage_block")
    elif item.specialist_count < config.watch_min_specialist_count:
        reason_codes.append("specialist_coverage_watch")

    if item.playbook_count < config.block_min_playbook_count:
        reason_codes.append("playbook_coverage_block")
    elif item.playbook_count < config.watch_min_playbook_count:
        reason_codes.append("playbook_coverage_watch")

    if item.calibration_sample_count < config.block_min_calibration_sample_count:
        reason_codes.append("calibration_sample_block")
    elif item.calibration_sample_count < config.watch_min_calibration_sample_count:
        reason_codes.append("calibration_sample_watch")

    if item.stale_memory_hours >= config.block_stale_memory_hours:
        reason_codes.append("memory_staleness_block")
    elif item.stale_memory_hours >= config.watch_stale_memory_hours:
        reason_codes.append("memory_staleness_watch")

    if item.unresolved_evidence_gap_ratio >= config.block_unresolved_evidence_gap_ratio:
        reason_codes.append("evidence_gap_block")
    elif item.unresolved_evidence_gap_ratio >= config.watch_unresolved_evidence_gap_ratio:
        reason_codes.append("evidence_gap_watch")

    if (
        item.evidence_family_coverage_ratio
        < config.block_min_evidence_family_coverage_ratio
    ):
        reason_codes.append("evidence_family_coverage_block")
    elif (
        item.evidence_family_coverage_ratio
        < config.watch_min_evidence_family_coverage_ratio
    ):
        reason_codes.append("evidence_family_coverage_watch")

    if item.analog_case_count < config.block_min_analog_case_count:
        reason_codes.append("analog_case_block")
    elif item.analog_case_count < config.watch_min_analog_case_count:
        reason_codes.append("analog_case_watch")

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
    rows: tuple[ResearchMacroEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.memory_status for row in rows))
    reason_codes = [
        f"macro_event_team_memory_queue_{'clear' if status == 'pass' else status}",
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
    rows: tuple[ResearchMacroEventTeamMemoryRow, ...],
) -> tuple[ResearchMacroEventTeamMemoryReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(
            (PASS_ROW_REASON_CODE,) + BLOCK_REASON_CODES + WATCH_REASON_CODES,
        )
    }
    return tuple(
        ResearchMacroEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=count,
            team_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(row: ResearchMacroEventTeamMemoryRow) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.memory_status],
        -_row_severity_score(row),
        row.team_key,
    )


def _row_severity_score(row: ResearchMacroEventTeamMemoryRow) -> Decimal:
    severity = STATUS_WEIGHT[row.memory_status]
    severity += row.unresolved_evidence_gap_ratio
    severity += ONE_RATIO - row.evidence_family_coverage_ratio
    return severity


def _status_count(
    rows: tuple[ResearchMacroEventTeamMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.memory_status == status))


def _validate_config(config: ResearchMacroEventTeamMemoryConfig) -> None:
    min_pairs = (
        ("block_min_specialist_count", "watch_min_specialist_count"),
        ("block_min_playbook_count", "watch_min_playbook_count"),
        ("block_min_calibration_sample_count", "watch_min_calibration_sample_count"),
        ("block_min_analog_case_count", "watch_min_analog_case_count"),
    )
    for block_name, watch_name in min_pairs:
        if getattr(config, block_name) > getattr(config, watch_name):
            raise ValueError(f"{block_name} must not exceed {watch_name}")
    if config.block_stale_memory_hours < config.watch_stale_memory_hours:
        raise ValueError("block_stale_memory_hours must be at least watch_stale_memory_hours")
    if (
        config.block_unresolved_evidence_gap_ratio
        < config.watch_unresolved_evidence_gap_ratio
    ):
        raise ValueError(
            "block_unresolved_evidence_gap_ratio must be at least "
            "watch_unresolved_evidence_gap_ratio",
        )
    if (
        config.block_min_evidence_family_coverage_ratio
        > config.watch_min_evidence_family_coverage_ratio
    ):
        raise ValueError(
            "block_min_evidence_family_coverage_ratio must not exceed "
            "watch_min_evidence_family_coverage_ratio",
        )


def _validate_row(row: ResearchMacroEventTeamMemoryRow) -> None:
    if row.memory_status != _row_status(row.reason_codes):
        raise ValueError("memory_status must match reason_codes")
    if row.memory_status == "pass" and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require macro_event_team_memory_ready")
    if row.memory_status != "pass" and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("queued rows must not contain ready reason_codes")


def _validate_report_materialized_fields(
    report: ResearchMacroEventTeamMemoryReport,
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
        "max_stale_memory_hours": _max_decimal(
            tuple(row.stale_memory_hours for row in rows),
        ),
        "max_unresolved_evidence_gap_ratio": _max_decimal(
            tuple(row.unresolved_evidence_gap_ratio for row in rows),
        ),
        "min_evidence_family_coverage_ratio": _min_decimal(
            tuple(row.evidence_family_coverage_ratio for row in rows),
        ),
        "min_analog_case_count": _min_decimal(
            tuple(row.analog_case_count for row in rows),
            count=True,
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
    rows: tuple[ResearchMacroEventTeamMemoryRow, ...],
) -> tuple[ResearchMacroEventTeamMemoryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMacroEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchMacroEventTeamMemoryRow")
        _require_hard_flags("row", row)
        if row.team_key in seen:
            raise ValueError("rows must contain unique team_key values")
        seen.add(row.team_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and team_key")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchMacroEventTeamMemoryReasonCodeCount, ...],
) -> tuple[ResearchMacroEventTeamMemoryReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMacroEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMacroEventTeamMemoryReasonCodeCount",
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
        "macro_event_team_memory_queue_clear",
        "macro_event_team_memory_queue_watch",
        "macro_event_team_memory_queue_block",
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
            "macro_event_team_memory_queue_clear",
            "macro_event_team_memory_queue_watch",
            "macro_event_team_memory_queue_block",
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


def _derived_validation_digest(report: ResearchMacroEventTeamMemoryReport) -> str:
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
