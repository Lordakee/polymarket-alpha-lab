"""Pure report-only research source freshness refresh scheduler."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_FRESHNESS_SCHEDULER_CONFIG_VERSION = (
    "research-source-freshness-scheduler-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SOURCE_LAG_WEIGHT = Decimal("0.400000")
EVIDENCE_STALENESS_WEIGHT = Decimal("0.350000")
REVISION_FREQUENCY_WEIGHT = Decimal("0.150000")
TEAM_SLA_PRESSURE_WEIGHT = Decimal("0.100000")

STATUSES = ("pass", "watch", "block")
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
REPORT_PLANS = {
    "pass": "freshness_clear_for_research_report",
    "watch": "monitor_freshness_before_research_report",
    "block": "refresh_required_before_research_report",
}
ROW_ACTIONS = {
    "pass": "no_refresh_needed",
    "watch": "review_refresh_timing",
    "block": "refresh_first",
}
REASON_CODES = (
    "refresh_schedule_no_inputs",
    "refresh_schedule_status_pass",
    "refresh_schedule_status_watch",
    "refresh_schedule_status_block",
    "source_lag_over_sla",
    "evidence_stale_against_sla",
    "frequent_revision_cycle",
    "compressed_team_sla",
)
DETAIL_REASON_CODES = REASON_CODES[4:]
UNSAFE_TEXT_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_FRESHNESS_SCHEDULER_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchSourceFreshnessScheduleReport",
    "ResearchSourceFreshnessScheduleRow",
    "ResearchSourceFreshnessSchedulerConfig",
    "ResearchSourceFreshnessSchedulerInput",
    "STATUSES",
    "build_research_source_freshness_schedule_report",
    "research_source_freshness_schedule_payload",
)


@dataclass(frozen=True)
class ResearchSourceFreshnessSchedulerConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_FRESHNESS_SCHEDULER_CONFIG_VERSION
    watch_priority_score: Decimal = Decimal("0.050000")
    block_priority_score: Decimal = Decimal("0.750000")
    standard_team_sla_hours: Decimal = Decimal("24")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFreshnessSchedulerConfig:
            raise ValueError(
                "config must be a ResearchSourceFreshnessSchedulerConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_FRESHNESS_SCHEDULER_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "watch_priority_score",
            _normalize_probability("watch_priority_score", self.watch_priority_score),
        )
        object.__setattr__(
            self,
            "block_priority_score",
            _normalize_probability("block_priority_score", self.block_priority_score),
        )
        object.__setattr__(
            self,
            "standard_team_sla_hours",
            _normalize_positive_decimal(
                "standard_team_sla_hours",
                self.standard_team_sla_hours,
            ),
        )
        if self.watch_priority_score >= self.block_priority_score:
            raise ValueError("watch_priority_score must be below block_priority_score")
        _require_hard_flags("scheduler config", self)


@dataclass(frozen=True)
class ResearchSourceFreshnessSchedulerInput:
    source_ref: str
    source_lag_hours: Decimal
    revision_frequency_hours: Decimal
    evidence_age_hours: Decimal
    team_sla_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFreshnessSchedulerInput:
            raise ValueError("source must be a ResearchSourceFreshnessSchedulerInput")
        _require_canonical_string("source_ref", self.source_ref)
        _reject_unsafe_text("source_ref", self.source_ref)
        for field_name in ("source_lag_hours", "evidence_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("revision_frequency_hours", "team_sla_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("scheduler input", self)


@dataclass(frozen=True)
class ResearchSourceFreshnessScheduleRow:
    refresh_slot_ref: str
    priority_rank: Decimal
    priority_score: Decimal
    source_lag_score: Decimal
    evidence_staleness_score: Decimal
    revision_frequency_score: Decimal
    team_sla_pressure_score: Decimal
    source_lag_hours: Decimal
    revision_frequency_hours: Decimal
    evidence_age_hours: Decimal
    team_sla_hours: Decimal
    status: str
    refresh_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFreshnessScheduleRow:
            raise ValueError("row must be a ResearchSourceFreshnessScheduleRow")
        _require_refresh_slot_ref(self.refresh_slot_ref)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        for field_name in (
            "priority_score",
            "source_lag_score",
            "evidence_staleness_score",
            "revision_frequency_score",
            "team_sla_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_lag_hours", "evidence_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("revision_frequency_hours", "team_sla_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("status", self.status, STATUSES)
        _require_choice("refresh_action", self.refresh_action, tuple(ROW_ACTIONS.values()))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("schedule row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchSourceFreshnessScheduleReport:
    config_version: str
    status: str
    refresh_plan: str
    input_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    source_lag_over_sla_count: Decimal
    evidence_stale_against_sla_count: Decimal
    frequent_revision_cycle_count: Decimal
    compressed_team_sla_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchSourceFreshnessScheduleRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFreshnessScheduleReport:
            raise ValueError("report must be a ResearchSourceFreshnessScheduleReport")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_FRESHNESS_SCHEDULER_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_choice("status", self.status, STATUSES)
        _require_choice("refresh_plan", self.refresh_plan, tuple(REPORT_PLANS.values()))
        for field_name in (
            "input_count",
            "block_count",
            "watch_count",
            "pass_count",
            "source_lag_over_sla_count",
            "evidence_stale_against_sla_count",
            "frequent_revision_cycle_count",
            "compressed_team_sla_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_probability("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("schedule report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)
        _reject_unsafe_public_payload("schedule report payload", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _report_public_payload_values(self)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = self.derived_validation_digest
        _reject_unsafe_public_payload("schedule payload", payload)
        return payload


def build_research_source_freshness_schedule_report(
    rows: object,
    *,
    config: ResearchSourceFreshnessSchedulerConfig | None = None,
) -> ResearchSourceFreshnessScheduleReport:
    if config is None:
        config = ResearchSourceFreshnessSchedulerConfig()
    if type(config) is not ResearchSourceFreshnessSchedulerConfig:
        raise ValueError("config must be a ResearchSourceFreshnessSchedulerConfig")
    _require_hard_flags("scheduler config", config)
    inputs = _normalize_input_rows(rows)
    unranked_rows = tuple(
        (source.source_ref, _unranked_row(source, config=config))
        for source in inputs
    )
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, (_source_ref, row) in enumerate(
            sorted(unranked_rows, key=_unranked_sort_key),
        )
    )
    status = _report_status(ranked_rows)
    return ResearchSourceFreshnessScheduleReport(
        config_version=config.config_version,
        status=status,
        refresh_plan=REPORT_PLANS[status],
        input_count=_count(len(inputs)),
        block_count=_status_count(ranked_rows, "block"),
        watch_count=_status_count(ranked_rows, "watch"),
        pass_count=_status_count(ranked_rows, "pass"),
        source_lag_over_sla_count=_reason_count(ranked_rows, "source_lag_over_sla"),
        evidence_stale_against_sla_count=_reason_count(
            ranked_rows,
            "evidence_stale_against_sla",
        ),
        frequent_revision_cycle_count=_reason_count(
            ranked_rows,
            "frequent_revision_cycle",
        ),
        compressed_team_sla_count=_reason_count(ranked_rows, "compressed_team_sla"),
        highest_priority_score=_max_priority_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_source_freshness_schedule_payload(
    report: ResearchSourceFreshnessScheduleReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceFreshnessScheduleReport:
        raise ValueError("report must be a ResearchSourceFreshnessScheduleReport")
    _require_hard_flags("schedule report", report)
    _validate_report(report)
    return report.payload


def _unranked_row(
    source: ResearchSourceFreshnessSchedulerInput,
    *,
    config: ResearchSourceFreshnessSchedulerConfig,
) -> ResearchSourceFreshnessScheduleRow:
    source_lag_score = _excess_against_sla_score(
        source.source_lag_hours,
        source.team_sla_hours,
    )
    evidence_staleness_score = _excess_against_sla_score(
        source.evidence_age_hours,
        source.team_sla_hours,
    )
    revision_frequency_score = _revision_frequency_score(
        source.revision_frequency_hours,
        source.team_sla_hours,
    )
    team_sla_pressure_score = _team_sla_pressure_score(
        source.team_sla_hours,
        config.standard_team_sla_hours,
    )
    priority_score = _priority_score(
        source_lag_score=source_lag_score,
        evidence_staleness_score=evidence_staleness_score,
        revision_frequency_score=revision_frequency_score,
        team_sla_pressure_score=team_sla_pressure_score,
    )
    status = _row_status(priority_score, config)
    return ResearchSourceFreshnessScheduleRow(
        refresh_slot_ref="refresh-slot-000001",
        priority_rank=ONE,
        priority_score=priority_score,
        source_lag_score=source_lag_score,
        evidence_staleness_score=evidence_staleness_score,
        revision_frequency_score=revision_frequency_score,
        team_sla_pressure_score=team_sla_pressure_score,
        source_lag_hours=source.source_lag_hours,
        revision_frequency_hours=source.revision_frequency_hours,
        evidence_age_hours=source.evidence_age_hours,
        team_sla_hours=source.team_sla_hours,
        status=status,
        refresh_action=ROW_ACTIONS[status],
        reason_codes=_row_reason_codes(
            status=status,
            source_lag_score=source_lag_score,
            evidence_staleness_score=evidence_staleness_score,
            revision_frequency_score=revision_frequency_score,
            team_sla_pressure_score=team_sla_pressure_score,
        ),
    )


def _ranked_row(
    row: ResearchSourceFreshnessScheduleRow,
    *,
    rank: int,
) -> ResearchSourceFreshnessScheduleRow:
    return replace(
        row,
        refresh_slot_ref=f"refresh-slot-{rank:06d}",
        priority_rank=_count(rank),
    )


def _unranked_sort_key(
    item: tuple[str, ResearchSourceFreshnessScheduleRow],
) -> tuple[Decimal, str]:
    source_ref, row = item
    return (-row.priority_score, source_ref)


def _excess_against_sla_score(value: Decimal, sla: Decimal) -> Decimal:
    if value <= sla:
        return ZERO
    return _clamp_probability(_ratio(value - sla, sla))


def _revision_frequency_score(revision_frequency_hours: Decimal, sla: Decimal) -> Decimal:
    if revision_frequency_hours >= sla:
        return ZERO
    return _clamp_probability(_ratio(sla - revision_frequency_hours, sla))


def _team_sla_pressure_score(team_sla_hours: Decimal, standard_sla_hours: Decimal) -> Decimal:
    if team_sla_hours >= standard_sla_hours:
        return ZERO
    return _clamp_probability(
        _ratio(standard_sla_hours - team_sla_hours, standard_sla_hours),
    )


def _priority_score(
    *,
    source_lag_score: Decimal,
    evidence_staleness_score: Decimal,
    revision_frequency_score: Decimal,
    team_sla_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (
                source_lag_score * SOURCE_LAG_WEIGHT
                + evidence_staleness_score * EVIDENCE_STALENESS_WEIGHT
                + revision_frequency_score * REVISION_FREQUENCY_WEIGHT
                + team_sla_pressure_score * TEAM_SLA_PRESSURE_WEIGHT
            ).quantize(SCORE_QUANT),
        )


def _row_status(
    priority_score: Decimal,
    config: ResearchSourceFreshnessSchedulerConfig,
) -> str:
    if priority_score >= config.block_priority_score:
        return "block"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_lag_score: Decimal,
    evidence_staleness_score: Decimal,
    revision_frequency_score: Decimal,
    team_sla_pressure_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"refresh_schedule_status_{status}"]
    if source_lag_score > ZERO:
        codes.append("source_lag_over_sla")
    if evidence_staleness_score > ZERO:
        codes.append("evidence_stale_against_sla")
    if revision_frequency_score > ZERO:
        codes.append("frequent_revision_cycle")
    if team_sla_pressure_score > ZERO:
        codes.append("compressed_team_sla")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchSourceFreshnessScheduleRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("refresh_schedule_no_inputs",)
    status = _report_status(rows)
    codes = [f"refresh_schedule_status_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in DETAIL_REASON_CODES:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[ResearchSourceFreshnessScheduleRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchSourceFreshnessScheduleRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceFreshnessScheduleRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_priority_score(rows: tuple[ResearchSourceFreshnessScheduleRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _validate_row(row: ResearchSourceFreshnessScheduleRow) -> None:
    expected_priority_score = _priority_score(
        source_lag_score=row.source_lag_score,
        evidence_staleness_score=row.evidence_staleness_score,
        revision_frequency_score=row.revision_frequency_score,
        team_sla_pressure_score=row.team_sla_pressure_score,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match freshness schedule drivers")
    expected_reason_codes = _row_reason_codes(
        status=row.status,
        source_lag_score=row.source_lag_score,
        evidence_staleness_score=row.evidence_staleness_score,
        revision_frequency_score=row.revision_frequency_score,
        team_sla_pressure_score=row.team_sla_pressure_score,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match freshness schedule drivers")
    if row.refresh_action != ROW_ACTIONS[row.status]:
        raise ValueError("refresh_action must match status")
    detail_codes = tuple(code for code in row.reason_codes if code in DETAIL_REASON_CODES)
    if row.status == "pass" and detail_codes:
        raise ValueError("pass rows must not include detail reason codes")
    if row.status != "pass" and not detail_codes:
        raise ValueError("non-pass rows must include detail reason codes")


def _validate_report(report: ResearchSourceFreshnessScheduleReport) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.refresh_plan != REPORT_PLANS[report.status]:
        raise ValueError("refresh_plan must match status")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.source_lag_over_sla_count != _reason_count(
        report.rows,
        "source_lag_over_sla",
    ):
        raise ValueError("source_lag_over_sla_count must match rows")
    if report.evidence_stale_against_sla_count != _reason_count(
        report.rows,
        "evidence_stale_against_sla",
    ):
        raise ValueError("evidence_stale_against_sla_count must match rows")
    if report.frequent_revision_cycle_count != _reason_count(
        report.rows,
        "frequent_revision_cycle",
    ):
        raise ValueError("frequent_revision_cycle_count must match rows")
    if report.compressed_team_sla_count != _reason_count(
        report.rows,
        "compressed_team_sla",
    ):
        raise ValueError("compressed_team_sla_count must match rows")
    if report.highest_priority_score != _max_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchSourceFreshnessSchedulerInput, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of scheduler inputs")
    normalized = tuple(rows)
    seen_source_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceFreshnessSchedulerInput:
            raise ValueError("rows must be ResearchSourceFreshnessSchedulerInput values")
        _require_hard_flags("scheduler input", row)
        if row.source_ref in seen_source_refs:
            raise ValueError("rows must be unique by source_ref")
        seen_source_refs.add(row.source_ref)
    return normalized


def _normalize_rows(rows: object) -> tuple[ResearchSourceFreshnessScheduleRow, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of schedule rows")
    normalized = tuple(rows)
    seen_slots: set[str] = set()
    expected_rank = 1
    for row in normalized:
        if type(row) is not ResearchSourceFreshnessScheduleRow:
            raise ValueError("rows must be ResearchSourceFreshnessScheduleRow values")
        _require_hard_flags("schedule row", row)
        if row.refresh_slot_ref in seen_slots:
            raise ValueError("rows must be unique by refresh_slot_ref")
        seen_slots.add(row.refresh_slot_ref)
        if row.priority_rank != _count(expected_rank):
            raise ValueError("priority_rank values must be contiguous")
        expected_rank += 1
    return normalized


def _report_public_payload_values(
    report: ResearchSourceFreshnessScheduleReport,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "status": report.status,
        "refresh_plan": report.refresh_plan,
        "input_count": str(report.input_count),
        "block_count": str(report.block_count),
        "watch_count": str(report.watch_count),
        "pass_count": str(report.pass_count),
        "source_lag_over_sla_count": str(report.source_lag_over_sla_count),
        "evidence_stale_against_sla_count": str(
            report.evidence_stale_against_sla_count,
        ),
        "frequent_revision_cycle_count": str(report.frequent_revision_cycle_count),
        "compressed_team_sla_count": str(report.compressed_team_sla_count),
        "highest_priority_score": str(report.highest_priority_score),
        "rows": [_row_public_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: ResearchSourceFreshnessScheduleRow) -> dict[str, Any]:
    return {
        "refresh_slot_ref": row.refresh_slot_ref,
        "priority_rank": str(row.priority_rank),
        "priority_score": str(row.priority_score),
        "source_lag_score": str(row.source_lag_score),
        "evidence_staleness_score": str(row.evidence_staleness_score),
        "revision_frequency_score": str(row.revision_frequency_score),
        "team_sla_pressure_score": str(row.team_sla_pressure_score),
        "source_lag_hours": str(row.source_lag_hours),
        "revision_frequency_hours": str(row.revision_frequency_hours),
        "evidence_age_hours": str(row.evidence_age_hours),
        "team_sla_hours": str(row.team_sla_hours),
        "status": row.status,
        "refresh_action": row.refresh_action,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: ResearchSourceFreshnessScheduleReport,
) -> str:
    payload = _report_public_payload_values(report)
    return _derived_validation_digest(payload)


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(("research_source_freshness_scheduler|" + encoded).encode()).hexdigest()


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return +value
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a valid Decimal") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(SCORE_QUANT)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _count(value: int) -> Decimal:
    return Decimal(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(f"{field_name} must be printable ASCII")


def _require_refresh_slot_ref(value: object) -> None:
    _require_canonical_string("refresh_slot_ref", value)
    prefix = "refresh-slot-"
    if not value.startswith(prefix):
        raise ValueError("refresh_slot_ref must use refresh-slot prefix")
    suffix = value[len(prefix) :]
    if len(suffix) != 6 or not suffix.isdigit():
        raise ValueError("refresh_slot_ref must include a six digit sequence")


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("reason_codes must be an iterable of strings")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_choice("reason_codes", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_sha256(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe text in {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("public payload values must be JSON scalars or containers")
