"""Pure scenario-tree report for caller-supplied probability evidence.

The module is deterministic and side-effect free. Callers provide candidate
event evidence; the policy returns report-only rows, summaries, and status
labels without any external reads or writes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchProbabilisticScenarioEvidence",
    "ResearchProbabilisticScenarioTreeConfig",
    "ResearchProbabilisticScenarioTreeEventSummary",
    "ResearchProbabilisticScenarioTreeReasonCodeCount",
    "ResearchProbabilisticScenarioTreeReport",
    "ResearchProbabilisticScenarioTreeRow",
    "build_research_probabilistic_scenario_tree_report",
    "research_probabilistic_scenario_tree_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-probabilistic-scenario-tree-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
PUBLIC_KEY_BLOCKLIST = frozenset(
    ("raw", "market", "source", "question", "dsn", "table", "token"),
)
PUBLIC_TEXT_BLOCKLIST = frozenset(
    (
        "api_key",
        "auth",
        "bearer",
        "database_url",
        "dsn",
        "private_key",
        "raw_",
        "secret",
        "table=",
        "token",
    ),
)


@dataclass(frozen=True)
class ResearchProbabilisticScenarioTreeConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_scenario_count: Decimal = Decimal("2")
    pass_min_evidence_weight: Decimal = Decimal("0.700000")
    watch_min_evidence_weight: Decimal = Decimal("0.400000")
    pass_max_probability_interval_width: Decimal = Decimal("0.200000")
    watch_max_probability_interval_width: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_scenario_count",
            _require_positive_whole_decimal(
                "min_scenario_count",
                self.min_scenario_count,
            ),
        )
        for field_name in (
            "pass_min_evidence_weight",
            "watch_min_evidence_weight",
            "pass_max_probability_interval_width",
            "watch_max_probability_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_evidence_weight <= self.watch_min_evidence_weight:
            raise ValueError(
                "pass_min_evidence_weight must be greater than watch_min_evidence_weight",
            )
        if (
            self.pass_max_probability_interval_width
            >= self.watch_max_probability_interval_width
        ):
            raise ValueError(
                "pass_max_probability_interval_width must be less than "
                "watch_max_probability_interval_width",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchProbabilisticScenarioEvidence:
    event_id: str
    scenario_id: str
    evidence_id: str
    evidence_family: str
    evidence_weight: Decimal
    probability_low: Decimal
    probability_high: Decimal
    observed_at: datetime
    blocking_condition: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_id", "scenario_id", "evidence_id", "evidence_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_weight",
            _require_positive_decimal("evidence_weight", self.evidence_weight),
        )
        object.__setattr__(
            self,
            "probability_low",
            _require_probability_decimal("probability_low", self.probability_low),
        )
        object.__setattr__(
            self,
            "probability_high",
            _require_probability_decimal("probability_high", self.probability_high),
        )
        if self.probability_high < self.probability_low:
            raise ValueError("probability_high must be greater than or equal to probability_low")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.blocking_condition) is not bool:
            raise ValueError("blocking_condition must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchProbabilisticScenarioTreeRow:
    event_id: str
    scenario_id: str
    evidence_count: Decimal
    evidence_weight_total: Decimal
    probability_low: Decimal
    probability_high: Decimal
    probability_midpoint: Decimal
    probability_interval_width: Decimal
    blocking_condition_count: Decimal
    evidence_ids: tuple[str, ...]
    evidence_families: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("scenario_id", self.scenario_id)
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_whole_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "evidence_weight_total",
            _require_positive_decimal("evidence_weight_total", self.evidence_weight_total),
        )
        for field_name in (
            "probability_low",
            "probability_high",
            "probability_midpoint",
            "probability_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.probability_high < self.probability_low:
            raise ValueError("probability_high must be greater than or equal to probability_low")
        if self.probability_midpoint != _probability_midpoint(
            self.probability_low,
            self.probability_high,
        ):
            raise ValueError("probability_midpoint must match interval")
        if self.probability_interval_width != _quantize(
            self.probability_high - self.probability_low,
        ):
            raise ValueError("probability_interval_width must match interval")
        object.__setattr__(
            self,
            "blocking_condition_count",
            _require_nonnegative_whole_decimal(
                "blocking_condition_count",
                self.blocking_condition_count,
            ),
        )
        for field_name in ("evidence_ids", "evidence_families"):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=False,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_status_consistency(self)


@dataclass(frozen=True)
class ResearchProbabilisticScenarioTreeEventSummary:
    event_id: str
    scenario_count: Decimal
    evidence_count: Decimal
    probability_low_sum: Decimal
    probability_high_sum: Decimal
    probability_midpoint_sum: Decimal
    residual_probability_midpoint: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_id", self.event_id)
        for field_name in ("scenario_count", "evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_low_sum",
            "probability_high_sum",
            "probability_midpoint_sum",
            "residual_probability_midpoint",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("event_summary", self)


@dataclass(frozen=True)
class ResearchProbabilisticScenarioTreeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchProbabilisticScenarioTreeReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    scenario_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...]
    event_summaries: tuple[ResearchProbabilisticScenarioTreeEventSummary, ...]
    reason_code_counts: tuple[ResearchProbabilisticScenarioTreeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "scenario_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "event_summaries",
            _normalize_event_summaries(self.event_summaries),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_probabilistic_scenario_tree_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchProbabilisticScenarioTreeConfig,
    generated_at: datetime,
) -> ResearchProbabilisticScenarioTreeReport:
    if type(config) is not ResearchProbabilisticScenarioTreeConfig:
        raise ValueError("config must be a ResearchProbabilisticScenarioTreeConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        _reject_future_observed_at(item, generated_at_utc)

    if not evidence_items:
        return ResearchProbabilisticScenarioTreeReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            event_count=ZERO,
            scenario_count=ZERO,
            evidence_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            blocked_count=ZERO,
            status="block",
            rows=(),
            event_summaries=(),
            reason_code_counts=(
                ResearchProbabilisticScenarioTreeReasonCodeCount(
                    reason_code="no_candidate_probability_evidence",
                    count=ONE,
                ),
            ),
            reason_codes=("no_candidate_probability_evidence",),
        )

    grouped: dict[tuple[str, str], list[ResearchProbabilisticScenarioEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault((item.event_id, item.scenario_id), []).append(item)

    base_rows = tuple(
        _row_from_items(
            event_id=event_id,
            scenario_id=scenario_id,
            evidence_rows=tuple(items),
            config=config,
            event_reason_codes=(),
        )
        for (event_id, scenario_id), items in grouped.items()
    )
    event_reasons = _event_reason_code_map(base_rows, config)
    rows = tuple(
        sorted(
            (
                _row_from_items(
                    event_id=row.event_id,
                    scenario_id=row.scenario_id,
                    evidence_rows=tuple(grouped[(row.event_id, row.scenario_id)]),
                    config=config,
                    event_reason_codes=event_reasons[row.event_id],
                )
                for row in base_rows
            ),
            key=_row_sort_key,
        ),
    )
    event_summaries = _event_summaries(rows, config)
    reason_codes = _summary_reason_codes(rows)

    return ResearchProbabilisticScenarioTreeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len({item.event_id for item in evidence_items})),
        scenario_count=_decimal_count(len(rows)),
        evidence_count=_decimal_count(len(evidence_items)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "block")),
        status=_summary_status(reason_codes),
        rows=rows,
        event_summaries=event_summaries,
        reason_code_counts=_reason_code_counts(rows, event_summaries, reason_codes),
        reason_codes=reason_codes,
    )


def research_probabilistic_scenario_tree_report_payload(
    report: ResearchProbabilisticScenarioTreeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilisticScenarioTreeReport:
        raise ValueError("report must be a ResearchProbabilisticScenarioTreeReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _row_from_items(
    *,
    event_id: str,
    scenario_id: str,
    evidence_rows: tuple[ResearchProbabilisticScenarioEvidence, ...],
    config: ResearchProbabilisticScenarioTreeConfig,
    event_reason_codes: tuple[str, ...],
) -> ResearchProbabilisticScenarioTreeRow:
    sorted_items = tuple(
        sorted(
            evidence_rows,
            key=lambda item: (
                item.evidence_id,
                item.evidence_family,
            ),
        ),
    )
    total_weight = _quantize(sum((item.evidence_weight for item in sorted_items), ZERO))
    probability_low = _weighted_probability(
        tuple((item.probability_low, item.evidence_weight) for item in sorted_items),
        total_weight,
    )
    probability_high = _weighted_probability(
        tuple((item.probability_high, item.evidence_weight) for item in sorted_items),
        total_weight,
    )
    probability_midpoint = _probability_midpoint(probability_low, probability_high)
    probability_interval_width = _quantize(probability_high - probability_low)
    blocking_count = sum(1 for item in sorted_items if item.blocking_condition)
    reason_codes = _row_reason_codes(
        evidence_weight_total=total_weight,
        probability_interval_width=probability_interval_width,
        blocking_condition_count=blocking_count,
        input_reason_codes=tuple(
            reason_code for item in sorted_items for reason_code in item.reason_codes
        ),
        event_reason_codes=event_reason_codes,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchProbabilisticScenarioTreeRow(
        event_id=event_id,
        scenario_id=scenario_id,
        evidence_count=_decimal_count(len(sorted_items)),
        evidence_weight_total=total_weight,
        probability_low=probability_low,
        probability_high=probability_high,
        probability_midpoint=probability_midpoint,
        probability_interval_width=probability_interval_width,
        blocking_condition_count=_decimal_count(blocking_count),
        evidence_ids=tuple(item.evidence_id for item in sorted_items),
        evidence_families=tuple(sorted({item.evidence_family for item in sorted_items})),
        status=status,
        reason_codes=reason_codes,
    )


def _event_reason_code_map(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
    config: ResearchProbabilisticScenarioTreeConfig,
) -> dict[str, tuple[str, ...]]:
    by_event: dict[str, list[ResearchProbabilisticScenarioTreeRow]] = {}
    for row in rows:
        by_event.setdefault(row.event_id, []).append(row)
    return {
        event_id: _event_reason_codes(tuple(items), config)
        for event_id, items in by_event.items()
    }


def _event_summaries(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
    config: ResearchProbabilisticScenarioTreeConfig,
) -> tuple[ResearchProbabilisticScenarioTreeEventSummary, ...]:
    by_event: dict[str, list[ResearchProbabilisticScenarioTreeRow]] = {}
    for row in rows:
        by_event.setdefault(row.event_id, []).append(row)
    return tuple(
        _event_summary(event_id, tuple(by_event[event_id]), config)
        for event_id in sorted(by_event)
    )


def _event_summary(
    event_id: str,
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
    config: ResearchProbabilisticScenarioTreeConfig,
) -> ResearchProbabilisticScenarioTreeEventSummary:
    probability_low_sum = _quantize(sum((row.probability_low for row in rows), ZERO))
    probability_high_sum = _quantize(sum((row.probability_high for row in rows), ZERO))
    probability_midpoint_sum = _quantize(
        sum((row.probability_midpoint for row in rows), ZERO),
    )
    residual_probability_midpoint = (
        _quantize(ONE - probability_midpoint_sum)
        if probability_midpoint_sum < ONE
        else ZERO
    )
    reason_codes = _event_reason_codes(rows, config)
    return ResearchProbabilisticScenarioTreeEventSummary(
        event_id=event_id,
        scenario_count=_decimal_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        probability_low_sum=probability_low_sum,
        probability_high_sum=probability_high_sum,
        probability_midpoint_sum=probability_midpoint_sum,
        residual_probability_midpoint=residual_probability_midpoint,
        status=_event_status(reason_codes),
        reason_codes=reason_codes,
    )


def _event_reason_codes(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
    config: ResearchProbabilisticScenarioTreeConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    probability_low_sum = _quantize(sum((row.probability_low for row in rows), ZERO))
    probability_high_sum = _quantize(sum((row.probability_high for row in rows), ZERO))
    if any(row.blocking_condition_count > ZERO for row in rows):
        reason_codes.append("blocking_condition_present")
    if Decimal(len(rows)) < config.min_scenario_count:
        reason_codes.append("too_few_mutually_exclusive_scenarios")
    if probability_low_sum > ONE:
        reason_codes.append("mutual_exclusivity_probability_overlap")
    elif probability_high_sum < ONE:
        reason_codes.append("residual_probability_unallocated")
    else:
        reason_codes.append("mutually_exclusive_scenarios_supported")
    return tuple(sorted(set(reason_codes)))


def _row_reason_codes(
    *,
    evidence_weight_total: Decimal,
    probability_interval_width: Decimal,
    blocking_condition_count: int,
    input_reason_codes: tuple[str, ...],
    event_reason_codes: tuple[str, ...],
    config: ResearchProbabilisticScenarioTreeConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if blocking_condition_count > 0:
        reason_codes.append("blocking_condition_present")
    if "mutual_exclusivity_probability_overlap" in event_reason_codes:
        reason_codes.append("mutual_exclusivity_probability_overlap")
    if "too_few_mutually_exclusive_scenarios" in event_reason_codes:
        reason_codes.append("too_few_mutually_exclusive_scenarios")
    if evidence_weight_total >= config.pass_min_evidence_weight:
        reason_codes.append("evidence_weight_pass")
    elif evidence_weight_total >= config.watch_min_evidence_weight:
        reason_codes.append("evidence_weight_watch")
    else:
        reason_codes.append("evidence_weight_block")
    if probability_interval_width <= config.pass_max_probability_interval_width:
        reason_codes.append("probability_interval_pass")
    elif probability_interval_width <= config.watch_max_probability_interval_width:
        reason_codes.append("probability_interval_watch")
    else:
        reason_codes.append("probability_interval_block")
    reason_codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    reason_codes.append(_status_reason_code(reason_codes))
    return tuple(sorted(set(reason_codes)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes) or any(
        reason_code
        in {
            "blocking_condition_present",
            "mutual_exclusivity_probability_overlap",
            "too_few_mutually_exclusive_scenarios",
        }
        for reason_code in reason_codes
    ):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _event_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in {
            "blocking_condition_present",
            "mutual_exclusivity_probability_overlap",
            "too_few_mutually_exclusive_scenarios",
        }
        for reason_code in reason_codes
    ):
        return "block"
    if "residual_probability_unallocated" in reason_codes:
        return "watch"
    return "pass"


def _status_reason_code(reason_codes: list[str]) -> str:
    status = _row_status(tuple(reason_codes))
    return f"scenario_tree_{status}"


def _summary_reason_codes(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_candidate_probability_evidence",)
    status = _summary_status_from_rows(rows)
    return (f"scenario_tree_{status}",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_candidate_probability_evidence",):
        return "block"
    if "scenario_tree_block" in reason_codes:
        return "block"
    if "scenario_tree_watch" in reason_codes:
        return "watch"
    if "scenario_tree_pass" in reason_codes:
        return "pass"
    raise ValueError("reason_codes must support status")


def _summary_status_from_rows(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
    event_summaries: tuple[ResearchProbabilisticScenarioTreeEventSummary, ...],
    summary_reason_codes: tuple[str, ...],
) -> tuple[ResearchProbabilisticScenarioTreeReasonCodeCount, ...]:
    counts = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    counts.update(
        reason_code
        for event_summary in event_summaries
        for reason_code in event_summary.reason_codes
    )
    counts.update(summary_reason_codes)
    return tuple(
        ResearchProbabilisticScenarioTreeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchProbabilisticScenarioEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    normalized: list[ResearchProbabilisticScenarioEvidence] = []
    for value in values:
        if type(value) is not ResearchProbabilisticScenarioEvidence:
            raise ValueError(
                "evidence_rows must contain ResearchProbabilisticScenarioEvidence",
            )
        _require_hard_flags("evidence", value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(
    values: object,
) -> tuple[ResearchProbabilisticScenarioTreeRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchProbabilisticScenarioTreeRow] = []
    for value in values:
        if type(value) is not ResearchProbabilisticScenarioTreeRow:
            raise ValueError("rows must contain ResearchProbabilisticScenarioTreeRow")
        rows.append(value)
    return tuple(rows)


def _normalize_event_summaries(
    values: object,
) -> tuple[ResearchProbabilisticScenarioTreeEventSummary, ...]:
    if type(values) is not tuple:
        raise ValueError("event_summaries must be a tuple")
    summaries: list[ResearchProbabilisticScenarioTreeEventSummary] = []
    for value in values:
        if type(value) is not ResearchProbabilisticScenarioTreeEventSummary:
            raise ValueError(
                "event_summaries must contain ResearchProbabilisticScenarioTreeEventSummary",
            )
        summaries.append(value)
    return tuple(summaries)


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchProbabilisticScenarioTreeReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchProbabilisticScenarioTreeReasonCodeCount] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchProbabilisticScenarioTreeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchProbabilisticScenarioTreeReasonCodeCount",
            )
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(value.reason_code)
        normalized.append(value)
    return tuple(normalized)


def _validate_row_status_consistency(row: ResearchProbabilisticScenarioTreeRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchProbabilisticScenarioTreeReport) -> None:
    if report.event_count != _decimal_count(
        len({event_summary.event_id for event_summary in report.event_summaries}),
    ):
        raise ValueError("event_count must match event_summaries")
    if report.scenario_count != _decimal_count(len(report.rows)):
        raise ValueError("scenario_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("blocked_count must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _status_count(
    rows: tuple[ResearchProbabilisticScenarioTreeRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchProbabilisticScenarioTreeRow,
) -> tuple[str, Decimal, str]:
    return (row.event_id, -row.probability_midpoint, row.scenario_id)


def _weighted_probability(
    probability_weights: tuple[tuple[Decimal, Decimal], ...],
    total_weight: Decimal,
) -> Decimal:
    weighted_sum = sum(
        (probability * weight for probability, weight in probability_weights),
        ZERO,
    )
    return _quantize(weighted_sum / total_weight)


def _probability_midpoint(low: Decimal, high: Decimal) -> Decimal:
    return _quantize((low + high) / Decimal("2"))


def _reject_future_observed_at(
    evidence: ResearchProbabilisticScenarioEvidence,
    generated_at: datetime,
) -> None:
    if evidence.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    for character in value:
        if not (
            character.isascii()
            and (character.islower() or character.isdigit() or character in "-_")
        ):
            raise ValueError(f"{field_name} must contain only safe characters")
    _reject_private_text(field_name, value)


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_private_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_TEXT_BLOCKLIST):
        raise ValueError(f"{field_name} must not contain sensitive text")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("payload_datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if isinstance(value, (str, int, bool)) or value is None:
        if isinstance(value, str):
            _reject_private_text("payload", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in PUBLIC_KEY_BLOCKLIST):
                raise ValueError(f"unsafe public payload key: {key}")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_private_text("payload", value)


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")
