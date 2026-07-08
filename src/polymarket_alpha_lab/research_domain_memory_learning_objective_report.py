"""Pure report for domain memory learning objectives."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION = (
    "research-domain-memory-learning-objective-report-v1"
)
RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_STATUSES = ("pass", "watch", "block")

_PUBLIC_DATACLASS_NAMES = (
    "ResearchDomainMemoryLearningObjectiveConfig",
    "ResearchDomainMemoryLearningObjectiveInputRow",
    "ResearchDomainMemoryLearningObjectiveRow",
    "ResearchDomainMemoryLearningObjectiveReasonCodeCount",
    "ResearchDomainMemoryLearningObjectiveReport",
)
_ROW_REASON_CODES = (
    "research_domain_memory_learning_objective_confidence_overreach",
    "research_domain_memory_learning_objective_calibration_block",
    "research_domain_memory_learning_objective_calibration_watch",
    "research_domain_memory_learning_objective_evidence_gap_block",
    "research_domain_memory_learning_objective_evidence_gap_watch",
    "research_domain_memory_learning_objective_stale_memory_block",
    "research_domain_memory_learning_objective_stale_memory_watch",
    "research_domain_memory_learning_objective_thin_memory_sample",
    "research_domain_memory_learning_objective_passed",
)
_REPORT_REASON_CODES = (
    "research_domain_memory_learning_objective_block_present",
    "research_domain_memory_learning_objective_watch_present",
    "research_domain_memory_learning_objective_confidence_overreach",
    "research_domain_memory_learning_objective_calibration_block",
    "research_domain_memory_learning_objective_calibration_watch",
    "research_domain_memory_learning_objective_evidence_gap_block",
    "research_domain_memory_learning_objective_evidence_gap_watch",
    "research_domain_memory_learning_objective_stale_memory_block",
    "research_domain_memory_learning_objective_stale_memory_watch",
    "research_domain_memory_learning_objective_thin_memory_sample",
    "research_domain_memory_learning_objective_clear",
    "research_domain_memory_learning_objective_empty",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "market:",
    "source:",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "network",
    "database",
    "persist",
    "mutation",
    "buy",
    "sell",
    "submit",
    "cancel",
    "replace",
    "recommend",
)
_DECIMAL_CONTEXT = Context(prec=64)
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANTUM = Decimal("0.000001")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in _PUBLIC_DATACLASS_NAMES:
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class ResearchDomainMemoryLearningObjectiveConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION
    )
    confidence_overreach_weight: Decimal = Decimal("0.250000")
    calibration_gap_weight: Decimal = Decimal("0.350000")
    evidence_gap_weight: Decimal = Decimal("0.250000")
    stale_memory_weight: Decimal = Decimal("0.150000")
    high_confidence_floor: Decimal = Decimal("0.700000")
    watch_calibration_error_ratio: Decimal = Decimal("0.150000")
    block_calibration_error_ratio: Decimal = Decimal("0.300000")
    watch_evidence_gap_count: Decimal = Decimal("2.000000")
    block_evidence_gap_count: Decimal = Decimal("4.000000")
    watch_stale_memory_ratio: Decimal = Decimal("0.300000")
    block_stale_memory_ratio: Decimal = Decimal("0.600000")
    min_memory_sample_count: Decimal = Decimal("3.000000")
    watch_objective_score: Decimal = Decimal("0.250000")
    block_objective_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainMemoryLearningObjectiveConfig, "config")
        _require_plain_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "confidence_overreach_weight",
            "calibration_gap_weight",
            "evidence_gap_weight",
            "stale_memory_weight",
            "high_confidence_floor",
            "watch_calibration_error_ratio",
            "block_calibration_error_ratio",
            "watch_evidence_gap_count",
            "block_evidence_gap_count",
            "watch_stale_memory_ratio",
            "block_stale_memory_ratio",
            "min_memory_sample_count",
            "watch_objective_score",
            "block_objective_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("high_confidence_floor", self.high_confidence_floor)
        for field_name in (
            "confidence_overreach_weight",
            "calibration_gap_weight",
            "evidence_gap_weight",
            "stale_memory_weight",
            "watch_calibration_error_ratio",
            "block_calibration_error_ratio",
            "watch_stale_memory_ratio",
            "block_stale_memory_ratio",
            "watch_objective_score",
            "block_objective_score",
        ):
            _require_ratio(field_name, getattr(self, field_name))
        _require_weight_total(
            self.confidence_overreach_weight,
            self.calibration_gap_weight,
            self.evidence_gap_weight,
            self.stale_memory_weight,
        )
        if self.watch_calibration_error_ratio > self.block_calibration_error_ratio:
            raise ValueError(
                "watch_calibration_error_ratio must not exceed "
                "block_calibration_error_ratio",
            )
        if self.watch_evidence_gap_count > self.block_evidence_gap_count:
            raise ValueError(
                "watch_evidence_gap_count must not exceed block_evidence_gap_count",
            )
        if self.watch_stale_memory_ratio > self.block_stale_memory_ratio:
            raise ValueError(
                "watch_stale_memory_ratio must not exceed block_stale_memory_ratio",
            )
        if self.watch_objective_score > self.block_objective_score:
            raise ValueError("watch_objective_score must not exceed block_objective_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchDomainMemoryLearningObjectiveInputRow(_FinalPublicDataclass):
    team_key: str
    domain: str
    subdomain: str
    past_confidence_score: Decimal
    calibration_error_ratio: Decimal
    evidence_gap_count: Decimal
    stale_memory_ratio: Decimal
    memory_sample_count: Decimal
    last_memory_reviewed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainMemoryLearningObjectiveInputRow,
            "input_row",
        )
        for field_name in ("team_key", "domain", "subdomain"):
            _require_plain_string(field_name, getattr(self, field_name))
        for field_name in (
            "past_confidence_score",
            "calibration_error_ratio",
            "evidence_gap_count",
            "stale_memory_ratio",
            "memory_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "past_confidence_score",
            "calibration_error_ratio",
            "stale_memory_ratio",
        ):
            _require_ratio(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_memory_reviewed_at",
            _as_utc("last_memory_reviewed_at", self.last_memory_reviewed_at),
        )
        _require_hard_flags("input_row", self)
        _reject_unsafe_public_payload("input_row", asdict(self))


@dataclass(frozen=True)
class ResearchDomainMemoryLearningObjectiveRow(_FinalPublicDataclass):
    team_key: str
    domain: str
    subdomain: str
    past_confidence_score: Decimal
    calibration_error_ratio: Decimal
    evidence_gap_count: Decimal
    stale_memory_ratio: Decimal
    memory_sample_count: Decimal
    last_memory_reviewed_at: datetime
    confidence_overreach_component: Decimal
    calibration_gap_component: Decimal
    evidence_gap_component: Decimal
    stale_memory_component: Decimal
    objective_score: Decimal
    objective_status: str
    learning_objectives: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainMemoryLearningObjectiveRow, "row")
        for field_name in ("team_key", "domain", "subdomain"):
            _require_plain_string(field_name, getattr(self, field_name))
        for field_name in (
            "past_confidence_score",
            "calibration_error_ratio",
            "evidence_gap_count",
            "stale_memory_ratio",
            "memory_sample_count",
            "confidence_overreach_component",
            "calibration_gap_component",
            "evidence_gap_component",
            "stale_memory_component",
            "objective_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "past_confidence_score",
            "calibration_error_ratio",
            "stale_memory_ratio",
            "confidence_overreach_component",
            "calibration_gap_component",
            "evidence_gap_component",
            "stale_memory_component",
            "objective_score",
        ):
            _require_ratio(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_memory_reviewed_at",
            _as_utc("last_memory_reviewed_at", self.last_memory_reviewed_at),
        )
        _require_status("objective_status", self.objective_status)
        object.__setattr__(
            self,
            "learning_objectives",
            _normalize_objectives(self.learning_objectives),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


@dataclass(frozen=True)
class ResearchDomainMemoryLearningObjectiveReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainMemoryLearningObjectiveReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code(self.reason_code, _REPORT_REASON_CODES)
        object.__setattr__(self, "count", _normalize_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_nonnegative_decimal("row_ratio", self.row_ratio),
        )
        _require_ratio("row_ratio", self.row_ratio)
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", asdict(self))


@dataclass(frozen=True)
class ResearchDomainMemoryLearningObjectiveReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    subdomain_count: Decimal
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_objective_score: Decimal
    max_objective_score: Decimal
    objective_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDomainMemoryLearningObjectiveReasonCodeCount, ...]
    rows: tuple[ResearchDomainMemoryLearningObjectiveRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainMemoryLearningObjectiveReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_plain_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "domain_count",
            "subdomain_count",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_objective_score",
            "max_objective_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("average_objective_score", self.average_objective_score)
        _require_ratio("max_objective_score", self.max_objective_score)
        _require_status("objective_status", self.objective_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_memory_learning_objective_report_payload(self)


def build_research_domain_memory_learning_objective_report(
    rows: object,
    *,
    config: ResearchDomainMemoryLearningObjectiveConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainMemoryLearningObjectiveReport:
    if config is None:
        config = ResearchDomainMemoryLearningObjectiveConfig()
    if type(config) is not ResearchDomainMemoryLearningObjectiveConfig:
        raise ValueError("config must be a ResearchDomainMemoryLearningObjectiveConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    for row in input_rows:
        if row.last_memory_reviewed_at > generated_at_utc:
            raise ValueError("last_memory_reviewed_at must be on or before generated_at")

    output_rows = tuple(
        ResearchDomainMemoryLearningObjectiveRow(
            **parts,
            derived_validation_digest=_digest_public(parts),
        )
        for parts in sorted(
            (_row_parts(row, config) for row in input_rows),
            key=_row_sort_key,
        )
    )
    reason_codes = _report_reason_codes(output_rows)
    report_parts = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "domain_count": _count(len({row.domain for row in output_rows})),
        "subdomain_count": _count(
            len({(row.domain, row.subdomain) for row in output_rows}),
        ),
        "input_count": _count(len(input_rows)),
        "pass_count": _count(sum(1 for row in output_rows if row.objective_status == "pass")),
        "watch_count": _count(sum(1 for row in output_rows if row.objective_status == "watch")),
        "block_count": _count(sum(1 for row in output_rows if row.objective_status == "block")),
        "average_objective_score": _average_score(output_rows),
        "max_objective_score": _max_score(output_rows),
        "objective_status": _report_status(output_rows),
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(reason_codes, output_rows),
        "rows": output_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainMemoryLearningObjectiveReport(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def research_domain_memory_learning_objective_report_payload(
    report: ResearchDomainMemoryLearningObjectiveReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainMemoryLearningObjectiveReport:
        raise ValueError("report must be a ResearchDomainMemoryLearningObjectiveReport")
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_domain_memory_learning_objective_report_digest(
    report: ResearchDomainMemoryLearningObjectiveReport,
) -> str:
    if type(report) is not ResearchDomainMemoryLearningObjectiveReport:
        raise ValueError("report must be a ResearchDomainMemoryLearningObjectiveReport")
    return _report_digest(report)


def _row_parts(
    row: ResearchDomainMemoryLearningObjectiveInputRow,
    config: ResearchDomainMemoryLearningObjectiveConfig,
) -> dict[str, object]:
    confidence_overreach_component = (
        row.past_confidence_score
        if (
            row.past_confidence_score >= config.high_confidence_floor
            and row.calibration_error_ratio >= config.watch_calibration_error_ratio
        )
        else _ZERO
    )
    calibration_gap_component = row.calibration_error_ratio
    evidence_gap_component = _safe_ratio(
        row.evidence_gap_count,
        config.block_evidence_gap_count,
    )
    stale_memory_component = row.stale_memory_ratio
    objective_score = _weighted_score(
        confidence_overreach_component,
        calibration_gap_component,
        evidence_gap_component,
        stale_memory_component,
        config,
    )
    reason_codes = _row_reason_codes(
        confidence_overreach_component=confidence_overreach_component,
        row=row,
        config=config,
    )
    objective_status = _row_status(objective_score, reason_codes, config)
    return {
        "team_key": row.team_key,
        "domain": row.domain,
        "subdomain": row.subdomain,
        "past_confidence_score": row.past_confidence_score,
        "calibration_error_ratio": row.calibration_error_ratio,
        "evidence_gap_count": row.evidence_gap_count,
        "stale_memory_ratio": row.stale_memory_ratio,
        "memory_sample_count": row.memory_sample_count,
        "last_memory_reviewed_at": row.last_memory_reviewed_at,
        "confidence_overreach_component": confidence_overreach_component,
        "calibration_gap_component": calibration_gap_component,
        "evidence_gap_component": evidence_gap_component,
        "stale_memory_component": stale_memory_component,
        "objective_score": objective_score,
        "objective_status": objective_status,
        "learning_objectives": _learning_objectives(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_reason_codes(
    *,
    confidence_overreach_component: Decimal,
    row: ResearchDomainMemoryLearningObjectiveInputRow,
    config: ResearchDomainMemoryLearningObjectiveConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if confidence_overreach_component > _ZERO:
        reason_codes.append("research_domain_memory_learning_objective_confidence_overreach")
    if row.calibration_error_ratio >= config.block_calibration_error_ratio:
        reason_codes.append("research_domain_memory_learning_objective_calibration_block")
    elif row.calibration_error_ratio >= config.watch_calibration_error_ratio:
        reason_codes.append("research_domain_memory_learning_objective_calibration_watch")
    if row.evidence_gap_count >= config.block_evidence_gap_count:
        reason_codes.append("research_domain_memory_learning_objective_evidence_gap_block")
    elif row.evidence_gap_count >= config.watch_evidence_gap_count:
        reason_codes.append("research_domain_memory_learning_objective_evidence_gap_watch")
    if row.stale_memory_ratio >= config.block_stale_memory_ratio:
        reason_codes.append("research_domain_memory_learning_objective_stale_memory_block")
    elif row.stale_memory_ratio >= config.watch_stale_memory_ratio:
        reason_codes.append("research_domain_memory_learning_objective_stale_memory_watch")
    if row.memory_sample_count < config.min_memory_sample_count:
        reason_codes.append("research_domain_memory_learning_objective_thin_memory_sample")
    if not reason_codes:
        reason_codes.append("research_domain_memory_learning_objective_passed")
    return tuple(reason_codes)


def _learning_objectives(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if reason_codes == ("research_domain_memory_learning_objective_passed",):
        return ("maintain_current_learning_review_cadence",)
    objectives: list[str] = []
    if any("confidence_overreach" in code or "calibration" in code for code in reason_codes):
        objectives.append("calibrate_confidence_to_resolved_outcomes")
    if any("evidence_gap" in code for code in reason_codes):
        objectives.append("close_public_evidence_gap_checklist")
    if any("stale_memory" in code for code in reason_codes):
        objectives.append("refresh_stale_domain_memory")
    if "research_domain_memory_learning_objective_thin_memory_sample" in reason_codes:
        objectives.append("expand_public_outcome_sample")
    return tuple(objectives)


def _row_status(
    objective_score: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchDomainMemoryLearningObjectiveConfig,
) -> str:
    if (
        objective_score >= config.block_objective_score
        or "research_domain_memory_learning_objective_calibration_block" in reason_codes
        or "research_domain_memory_learning_objective_evidence_gap_block" in reason_codes
        or "research_domain_memory_learning_objective_stale_memory_block" in reason_codes
    ):
        return "block"
    if objective_score >= config.watch_objective_score or reason_codes != (
        "research_domain_memory_learning_objective_passed",
    ):
        return "watch"
    return "pass"


def _row_sort_key(parts: dict[str, object]) -> tuple[int, Decimal, str, str, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_rank[str(parts["objective_status"])],
        -parts["objective_score"],  # type: ignore[operator]
        str(parts["domain"]),
        str(parts["subdomain"]),
        str(parts["team_key"]),
    )


def _report_status(rows: tuple[ResearchDomainMemoryLearningObjectiveRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.objective_status == "block" for row in rows):
        return "block"
    if any(row.objective_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainMemoryLearningObjectiveRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_domain_memory_learning_objective_empty",)
    reason_codes: list[str] = []
    if any(row.objective_status == "block" for row in rows):
        reason_codes.append("research_domain_memory_learning_objective_block_present")
    if any(row.objective_status == "watch" for row in rows):
        reason_codes.append("research_domain_memory_learning_objective_watch_present")
    for code in _ROW_REASON_CODES:
        if code == "research_domain_memory_learning_objective_passed":
            continue
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    if not reason_codes:
        reason_codes.append("research_domain_memory_learning_objective_clear")
    return tuple(reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchDomainMemoryLearningObjectiveRow, ...],
) -> tuple[ResearchDomainMemoryLearningObjectiveReasonCodeCount, ...]:
    row_count = _count(len(rows))
    counts: list[ResearchDomainMemoryLearningObjectiveReasonCodeCount] = []
    for code in reason_codes:
        if code == "research_domain_memory_learning_objective_empty":
            count = _ONE
        elif code == "research_domain_memory_learning_objective_clear":
            count = _count(len(rows))
        elif code == "research_domain_memory_learning_objective_block_present":
            count = _count(sum(1 for row in rows if row.objective_status == "block"))
        elif code == "research_domain_memory_learning_objective_watch_present":
            count = _count(sum(1 for row in rows if row.objective_status == "watch"))
        else:
            count = _count(sum(1 for row in rows if code in row.reason_codes))
        counts.append(
            ResearchDomainMemoryLearningObjectiveReasonCodeCount(
                reason_code=code,
                count=count,
                row_ratio=_safe_ratio(count, row_count),
            ),
        )
    return tuple(counts)


def _validate_report(report: ResearchDomainMemoryLearningObjectiveReport) -> None:
    row_count = _count(len(report.rows))
    if report.input_count != row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != row_count:
        raise ValueError("status counts must match rows")
    if report.domain_count != _count(len({row.domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.subdomain_count != _count(
        len({(row.domain, row.subdomain) for row in report.rows}),
    ):
        raise ValueError("subdomain_count must match rows")
    if report.average_objective_score != _average_score(report.rows):
        raise ValueError("average_objective_score must match rows")
    if report.max_objective_score != _max_score(report.rows):
        raise ValueError("max_objective_score must match rows")
    if report.objective_status != _report_status(report.rows):
        raise ValueError("objective_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchDomainMemoryLearningObjectiveInputRow, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of input rows")
    normalized: list[ResearchDomainMemoryLearningObjectiveInputRow] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchDomainMemoryLearningObjectiveInputRow:
            raise ValueError(
                "rows must contain ResearchDomainMemoryLearningObjectiveInputRow",
            )
        _require_hard_flags("input_row", row)
        key = (row.team_key, row.domain, row.subdomain)
        if key in seen:
            raise ValueError("duplicate team/domain/subdomain")
        seen.add(key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchDomainMemoryLearningObjectiveRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDomainMemoryLearningObjectiveRow:
            raise ValueError("rows must contain ResearchDomainMemoryLearningObjectiveRow")
        _require_hard_flags("row", row)
    if tuple(sorted(rows, key=lambda row: _row_instance_sort_key(row))) != rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _row_instance_sort_key(
    row: ResearchDomainMemoryLearningObjectiveRow,
) -> tuple[int, Decimal, str, str, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_rank[row.objective_status],
        -row.objective_score,
        row.domain,
        row.subdomain,
        row.team_key,
    )


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchDomainMemoryLearningObjectiveReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchDomainMemoryLearningObjectiveReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainMemoryLearningObjectiveReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    return values


def _normalize_objectives(values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("learning_objectives must be a non-empty tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_plain_string("learning_objectives", value)
        if value in seen:
            raise ValueError("learning_objectives must not contain duplicates")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} must contain plain str values")
        _require_reason_code(value, allowed_values)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _require_reason_code(value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"unsupported reason_code: {value}")


def _average_score(rows: tuple[ResearchDomainMemoryLearningObjectiveRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return _decimal(sum((row.objective_score for row in rows), _ZERO) / _count(len(rows)))


def _max_score(rows: tuple[ResearchDomainMemoryLearningObjectiveRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.objective_score for row in rows)


def _weighted_score(
    confidence_overreach_component: Decimal,
    calibration_gap_component: Decimal,
    evidence_gap_component: Decimal,
    stale_memory_component: Decimal,
    config: ResearchDomainMemoryLearningObjectiveConfig,
) -> Decimal:
    return _decimal(
        confidence_overreach_component * config.confidence_overreach_weight
        + calibration_gap_component * config.calibration_gap_weight
        + evidence_gap_component * config.evidence_gap_weight
        + stale_memory_component * config.stale_memory_weight,
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ZERO
    return min(_ONE, _decimal(numerator / denominator))


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _decimal(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM, rounding=ROUND_HALF_UP)


def _require_ratio(field_name: str, value: Decimal) -> None:
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")


def _require_weight_total(*values: Decimal) -> None:
    if _decimal(sum(values, _ZERO)) != _ONE:
        raise ValueError("confidence weights must sum to 1.000000")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_plain_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc


def _row_digest(row: ResearchDomainMemoryLearningObjectiveRow) -> str:
    return _digest_without(row, ("derived_validation_digest",))


def _report_digest(report: ResearchDomainMemoryLearningObjectiveReport) -> str:
    return _digest_without(report, ("derived_validation_digest",))


def _digest_without(value: object, excluded_fields: tuple[str, ...]) -> str:
    payload: dict[str, object] = {}
    for field in fields(value):
        if field.name not in excluded_fields:
            payload[field.name] = getattr(value, field.name)
    return _digest_public(payload)


def _digest_public(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_ready(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    if isinstance(value, Decimal):
        return f"{_decimal(value):.6f}"
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                walk(str(key))
                walk(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            lowered = node.lower()
            if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public text")
        elif isinstance(node, float):
            raise ValueError(f"{label} must not contain float values")

    walk(_json_ready(value))


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_CONFIG_VERSION",
    "RESEARCH_DOMAIN_MEMORY_LEARNING_OBJECTIVE_STATUSES",
    "ResearchDomainMemoryLearningObjectiveConfig",
    "ResearchDomainMemoryLearningObjectiveInputRow",
    "ResearchDomainMemoryLearningObjectiveRow",
    "ResearchDomainMemoryLearningObjectiveReasonCodeCount",
    "ResearchDomainMemoryLearningObjectiveReport",
    "build_research_domain_memory_learning_objective_report",
    "research_domain_memory_learning_objective_report_payload",
    "research_domain_memory_learning_objective_report_digest",
)
