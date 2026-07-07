"""Pure outcome-label quality report for caller-supplied settled events."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any


__all__ = (
    "ResearchOutcomeLabelQualityConfig",
    "ResearchOutcomeLabelQualityMemoryWritePlan",
    "ResearchOutcomeLabelQualityObservation",
    "ResearchOutcomeLabelQualityReasonCodeCount",
    "ResearchOutcomeLabelQualityReport",
    "ResearchOutcomeLabelQualityRow",
    "build_research_outcome_label_quality_report",
    "research_outcome_label_quality_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-outcome-label-quality-report-v0"
DEFAULT_MEMORY_PLAN_VERSION = "local-memory-plan-v0"
STATUSES = ("pass", "watch", "block")
ORIGIN_KINDS = (
    "curator_review",
    "official_resolution",
    "settlement_audit",
    "venue_notice",
)
DISPUTE_STATUSES = ("none", "open", "resolved")
MEMORY_BACKENDS = ("local_supabase_postgres",)
MEMORY_OPERATIONS = ("queue_outcome_label_memory_upsert",)
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
)
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=28)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchOutcomeLabelQualityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_origin_count: Decimal = Decimal("2")
    pass_consistency_ratio: Decimal = Decimal("1.000000")
    watch_consistency_ratio: Decimal = Decimal("0.500000")
    min_review_usability_score: Decimal = Decimal("0.700000")
    memory_plan_version: str = DEFAULT_MEMORY_PLAN_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_origin_count",
            _require_positive_whole_decimal("min_origin_count", self.min_origin_count),
        )
        for field_name in (
            "pass_consistency_ratio",
            "watch_consistency_ratio",
            "min_review_usability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_consistency_ratio < self.watch_consistency_ratio:
            raise ValueError(
                "pass_consistency_ratio must be >= watch_consistency_ratio",
            )
        _require_public_string("memory_plan_version", self.memory_plan_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchOutcomeLabelQualityObservation:
    event_id: str
    outcome_id: str
    observation_id: str
    origin_fingerprint: str | None
    origin_kind: str
    observed_at: datetime
    label_digest: str | None
    settlement_label_digest: str | None
    settled: bool = True
    dispute_flag: bool = False
    dispute_status: str = "none"
    review_usability_score: Decimal = Decimal("0.800000")
    memory_write_eligible: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_id", "outcome_id", "observation_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "origin_fingerprint",
            _require_optional_public_string(
                "origin_fingerprint",
                self.origin_fingerprint,
            ),
        )
        _require_enum("origin_kind", self.origin_kind, ORIGIN_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "label_digest",
            _require_optional_public_string("label_digest", self.label_digest),
        )
        object.__setattr__(
            self,
            "settlement_label_digest",
            _require_optional_public_string(
                "settlement_label_digest",
                self.settlement_label_digest,
            ),
        )
        for field_name in ("settled", "dispute_flag", "memory_write_eligible"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_enum("dispute_status", self.dispute_status, DISPUTE_STATUSES)
        if self.dispute_status != "none" and not self.dispute_flag:
            raise ValueError("dispute_status requires dispute_flag")
        object.__setattr__(
            self,
            "review_usability_score",
            _require_probability_decimal(
                "review_usability_score",
                self.review_usability_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchOutcomeLabelQualityMemoryWritePlan:
    plan_id: str
    backend: str
    operation: str
    plan_version: str
    dry_run_only: bool
    eligible: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("plan_id", self.plan_id)
        _require_enum("backend", self.backend, MEMORY_BACKENDS)
        _require_enum("operation", self.operation, MEMORY_OPERATIONS)
        _require_public_string("plan_version", self.plan_version)
        for field_name in ("dry_run_only", "eligible"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        if self.dry_run_only is not True:
            raise ValueError("dry_run_only must be True")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("memory_write_plan", self)


@dataclass(frozen=True)
class ResearchOutcomeLabelQualityRow:
    event_id: str
    outcome_id: str
    observation_count: Decimal
    origin_count: Decimal
    matching_label_count: Decimal
    mismatching_label_count: Decimal
    missing_label_count: Decimal
    dispute_flag_count: Decimal
    open_dispute_count: Decimal
    review_usable_observation_count: Decimal
    label_consistency_ratio: Decimal
    review_usability_score: Decimal
    memory_write_planned_count: Decimal
    latest_observed_at: datetime
    observation_ids: tuple[str, ...]
    origin_fingerprints: tuple[str, ...]
    origin_kinds: tuple[str, ...]
    memory_write_plans: tuple[ResearchOutcomeLabelQualityMemoryWritePlan, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_id", "outcome_id"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "observation_count",
            "origin_count",
            "matching_label_count",
            "mismatching_label_count",
            "missing_label_count",
            "dispute_flag_count",
            "open_dispute_count",
            "review_usable_observation_count",
            "memory_write_planned_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("label_consistency_ratio", "review_usability_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("observation_ids", "origin_fingerprints", "origin_kinds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=True,
                ),
            )
        object.__setattr__(
            self,
            "memory_write_plans",
            _normalize_memory_write_plans(self.memory_write_plans),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchOutcomeLabelQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchOutcomeLabelQualityReport:
    generated_at: datetime
    config_version: str
    event_outcome_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_write_planned_count: Decimal
    status: str
    rows: tuple[ResearchOutcomeLabelQualityRow, ...]
    reason_code_counts: tuple[ResearchOutcomeLabelQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_outcome_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "memory_write_planned_count",
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


def build_research_outcome_label_quality_report(
    observations: Iterable[object],
    *,
    config: ResearchOutcomeLabelQualityConfig,
    generated_at: datetime,
) -> ResearchOutcomeLabelQualityReport:
    if type(config) is not ResearchOutcomeLabelQualityConfig:
        raise ValueError("config must be a ResearchOutcomeLabelQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_items = _normalize_observations(observations)
    for item in observation_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be <= generated_at")

    grouped: dict[tuple[str, str], list[ResearchOutcomeLabelQualityObservation]] = {}
    for item in observation_items:
        grouped.setdefault((item.event_id, item.outcome_id), []).append(item)

    rows = tuple(
        _row_from_observations(
            event_id=event_id,
            outcome_id=outcome_id,
            observations=tuple(grouped[(event_id, outcome_id)]),
            config=config,
            row_index=index,
        )
        for index, (event_id, outcome_id) in enumerate(sorted(grouped), start=1)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchOutcomeLabelQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_outcome_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        memory_write_planned_count=sum(
            (row.memory_write_planned_count for row in rows),
            ZERO,
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_outcome_label_quality_report_payload(
    report: ResearchOutcomeLabelQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchOutcomeLabelQualityReport:
        raise ValueError("report must be a ResearchOutcomeLabelQualityReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _row_from_observations(
    *,
    event_id: str,
    outcome_id: str,
    observations: tuple[ResearchOutcomeLabelQualityObservation, ...],
    config: ResearchOutcomeLabelQualityConfig,
    row_index: int,
) -> ResearchOutcomeLabelQualityRow:
    ordered = tuple(sorted(observations, key=lambda item: item.observation_id))
    observation_count = _decimal_count(len(ordered))
    origin_fingerprints = tuple(
        sorted(
            {
                item.origin_fingerprint
                for item in ordered
                if item.origin_fingerprint is not None
            },
        ),
    )
    origin_kinds = tuple(sorted({item.origin_kind for item in ordered}))
    matching_count = _decimal_count(
        sum(
            1
            for item in ordered
            if item.label_digest is not None
            and item.settlement_label_digest is not None
            and item.label_digest == item.settlement_label_digest
        ),
    )
    mismatching_count = _decimal_count(
        sum(
            1
            for item in ordered
            if item.label_digest is not None
            and item.settlement_label_digest is not None
            and item.label_digest != item.settlement_label_digest
        ),
    )
    missing_count = _decimal_count(
        sum(
            1
            for item in ordered
            if item.label_digest is None or item.settlement_label_digest is None
        ),
    )
    dispute_flag_count = _decimal_count(sum(1 for item in ordered if item.dispute_flag))
    open_dispute_count = _decimal_count(
        sum(1 for item in ordered if item.dispute_status == "open"),
    )
    review_usable_count = _decimal_count(
        sum(
            1
            for item in ordered
            if item.review_usability_score >= config.min_review_usability_score
        ),
    )
    label_consistency_ratio = _ratio(matching_count, matching_count + mismatching_count)
    review_usability_score = _average_probability(
        tuple(item.review_usability_score for item in ordered),
    )
    all_settled = all(item.settled for item in ordered)
    all_memory_eligible = all(item.memory_write_eligible for item in ordered)
    status = _row_status(
        all_settled=all_settled,
        all_memory_eligible=all_memory_eligible,
        origin_count=_decimal_count(len(origin_fingerprints)),
        label_consistency_ratio=label_consistency_ratio,
        review_usability_score=review_usability_score,
        mismatching_count=mismatching_count,
        missing_count=missing_count,
        dispute_flag_count=dispute_flag_count,
        open_dispute_count=open_dispute_count,
        config=config,
    )
    memory_write_ready = status == "pass" and all_memory_eligible
    memory_write_plans = (
        (
            ResearchOutcomeLabelQualityMemoryWritePlan(
                plan_id=f"memory-plan-{row_index:03d}",
                backend="local_supabase_postgres",
                operation="queue_outcome_label_memory_upsert",
                plan_version=config.memory_plan_version,
                dry_run_only=True,
                eligible=True,
                reason_codes=("memory_write_plan_ready",),
            ),
        )
        if memory_write_ready
        else ()
    )

    reason_codes = _row_reason_codes(
        observations=ordered,
        all_settled=all_settled,
        origin_count=_decimal_count(len(origin_fingerprints)),
        matching_count=matching_count,
        mismatching_count=mismatching_count,
        missing_count=missing_count,
        dispute_flag_count=dispute_flag_count,
        open_dispute_count=open_dispute_count,
        review_usability_score=review_usability_score,
        memory_write_ready=memory_write_ready,
        status=status,
        config=config,
    )

    return ResearchOutcomeLabelQualityRow(
        event_id=event_id,
        outcome_id=outcome_id,
        observation_count=observation_count,
        origin_count=_decimal_count(len(origin_fingerprints)),
        matching_label_count=matching_count,
        mismatching_label_count=mismatching_count,
        missing_label_count=missing_count,
        dispute_flag_count=dispute_flag_count,
        open_dispute_count=open_dispute_count,
        review_usable_observation_count=review_usable_count,
        label_consistency_ratio=label_consistency_ratio,
        review_usability_score=review_usability_score,
        memory_write_planned_count=_decimal_count(len(memory_write_plans)),
        latest_observed_at=max(item.observed_at for item in ordered),
        observation_ids=tuple(item.observation_id for item in ordered),
        origin_fingerprints=origin_fingerprints,
        origin_kinds=origin_kinds,
        memory_write_plans=memory_write_plans,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    all_settled: bool,
    all_memory_eligible: bool,
    origin_count: Decimal,
    label_consistency_ratio: Decimal,
    review_usability_score: Decimal,
    mismatching_count: Decimal,
    missing_count: Decimal,
    dispute_flag_count: Decimal,
    open_dispute_count: Decimal,
    config: ResearchOutcomeLabelQualityConfig,
) -> str:
    if (
        not all_settled
        or open_dispute_count > ZERO
        or mismatching_count > ZERO
        or missing_count > ZERO
        or label_consistency_ratio < config.watch_consistency_ratio
    ):
        return "block"
    if (
        origin_count < config.min_origin_count
        or dispute_flag_count > ZERO
        or review_usability_score < config.min_review_usability_score
        or label_consistency_ratio < config.pass_consistency_ratio
        or not all_memory_eligible
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observations: tuple[ResearchOutcomeLabelQualityObservation, ...],
    all_settled: bool,
    origin_count: Decimal,
    matching_count: Decimal,
    mismatching_count: Decimal,
    missing_count: Decimal,
    dispute_flag_count: Decimal,
    open_dispute_count: Decimal,
    review_usability_score: Decimal,
    memory_write_ready: bool,
    status: str,
    config: ResearchOutcomeLabelQualityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for item in observations:
        reason_codes.extend(f"input_{reason_code}" for reason_code in item.reason_codes)
    if not all_settled:
        reason_codes.append("outcome_not_settled")
    if origin_count >= config.min_origin_count:
        reason_codes.append("label_origin_coverage_pass")
    else:
        reason_codes.append("not_enough_label_origin_coverage")
    if matching_count > ZERO and mismatching_count == ZERO and missing_count == ZERO:
        reason_codes.append("settlement_label_consistent")
    if mismatching_count > ZERO:
        reason_codes.append("settlement_label_mismatch")
    if missing_count > ZERO:
        reason_codes.append("label_digest_missing")
    if dispute_flag_count > ZERO:
        reason_codes.append("dispute_flags_present")
    if open_dispute_count > ZERO:
        reason_codes.append("open_dispute_present")
    if review_usability_score >= config.min_review_usability_score:
        reason_codes.append("review_usable")
    else:
        reason_codes.append("review_not_usable")
    reason_codes.append(
        "memory_write_plan_ready" if memory_write_ready else "memory_write_plan_block",
    )
    reason_codes.append(f"outcome_label_quality_{status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _summary_status(rows: tuple[ResearchOutcomeLabelQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchOutcomeLabelQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_outcome_label_observations",)
    return (f"outcome_label_quality_{_summary_status(rows)}",)


def _reason_code_counts(
    rows: tuple[ResearchOutcomeLabelQualityRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchOutcomeLabelQualityReasonCodeCount, ...]:
    if not rows:
        return tuple(
            ResearchOutcomeLabelQualityReasonCodeCount(
                reason_code=reason_code,
                count=Decimal("1"),
            )
            for reason_code in report_reason_codes
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchOutcomeLabelQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchOutcomeLabelQualityObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable of observation objects")
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(value: object) -> ResearchOutcomeLabelQualityObservation:
    if type(value) is ResearchOutcomeLabelQualityObservation:
        return value
    return ResearchOutcomeLabelQualityObservation(
        event_id=_field_value(value, "event_id"),
        outcome_id=_field_value(value, "outcome_id"),
        observation_id=_field_value(value, "observation_id"),
        origin_fingerprint=_field_value(value, "origin_fingerprint"),
        origin_kind=_field_value(value, "origin_kind"),
        observed_at=_field_value(value, "observed_at"),
        label_digest=_field_value(value, "label_digest"),
        settlement_label_digest=_field_value(value, "settlement_label_digest"),
        settled=_field_value(value, "settled", default=True),
        dispute_flag=_field_value(value, "dispute_flag", default=False),
        dispute_status=_field_value(value, "dispute_status", default="none"),
        review_usability_score=_field_value(
            value,
            "review_usability_score",
            default=Decimal("0.800000"),
        ),
        memory_write_eligible=_field_value(
            value,
            "memory_write_eligible",
            default=True,
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only", default=True),
        report_only=_field_value(value, "report_only", default=True),
        readonly=_field_value(value, "readonly", default=True),
    )


def _field_value(
    value: object,
    field_name: str,
    *,
    default: object = _MISSING,
) -> Any:
    if isinstance(value, dict) and field_name in value:
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _normalize_rows(value: object) -> tuple[ResearchOutcomeLabelQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchOutcomeLabelQualityRow:
            raise ValueError("rows must contain ResearchOutcomeLabelQualityRow values")
    return value


def _normalize_memory_write_plans(
    value: object,
) -> tuple[ResearchOutcomeLabelQualityMemoryWritePlan, ...]:
    if type(value) is not tuple:
        raise ValueError("memory_write_plans must be a tuple")
    for plan in value:
        if type(plan) is not ResearchOutcomeLabelQualityMemoryWritePlan:
            raise ValueError(
                "memory_write_plans must contain "
                "ResearchOutcomeLabelQualityMemoryWritePlan values",
            )
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchOutcomeLabelQualityReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchOutcomeLabelQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchOutcomeLabelQualityReasonCodeCount values",
            )
    return value


def _validate_row_consistency(row: ResearchOutcomeLabelQualityRow) -> None:
    if row.origin_count > row.observation_count:
        raise ValueError("origin_count must be <= observation_count")
    if (
        row.matching_label_count
        + row.mismatching_label_count
        + row.missing_label_count
        != row.observation_count
    ):
        raise ValueError("label counts must match observation_count")
    for field_name in (
        "dispute_flag_count",
        "open_dispute_count",
        "review_usable_observation_count",
    ):
        if getattr(row, field_name) > row.observation_count:
            raise ValueError(f"{field_name} must be <= observation_count")
    if row.memory_write_planned_count != _decimal_count(len(row.memory_write_plans)):
        raise ValueError("memory_write_planned_count must match memory_write_plans")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchOutcomeLabelQualityReport) -> None:
    if report.event_outcome_count != _decimal_count(len(report.rows)):
        raise ValueError("event_outcome_count must match rows")
    if report.observation_count != sum(
        (row.observation_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.memory_write_planned_count != sum(
        (row.memory_write_planned_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("memory_write_planned_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchOutcomeLabelQualityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    terminal_codes = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code.startswith("outcome_label_quality_")
    )
    if terminal_codes == ("outcome_label_quality_pass",):
        return "pass"
    if terminal_codes == ("outcome_label_quality_watch",):
        return "watch"
    if terminal_codes == ("outcome_label_quality_block",):
        return "block"
    raise ValueError("reason_codes must include exactly one terminal status")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _require_probability_decimal("ratio", numerator / denominator)


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _require_probability_decimal(
            "average_probability",
            sum(values, ZERO) / _decimal_count(len(values)),
        )


def _as_utc(field_name: str, value: object) -> datetime:
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
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized.quantize(RATIO_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    return value


def _require_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_string(field_name, value)


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    _require_enum(field_name, value, STATUSES)


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
        normalized.append(_require_public_string(field_name, value))
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


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
    _require_public_string(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must use lowercase snake case")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
