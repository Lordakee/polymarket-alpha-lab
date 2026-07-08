"""Readonly paper report for MMA signal memory quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_MMA_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION = (
    "research-domain-mma-signal-memory-quality-report-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

MMA_MEMORY_INPUT_FAMILIES = (
    "fighter",
    "injury",
    "weight_cut",
    "camp",
    "matchup_context",
)
MMA_SIGNAL_MEMORY_QUALITY_STATUSES = ("pass", "watch", "block")
MMA_ROW_STATUSES = ("block", "watch", "pass")
MMA_ROW_REASON_CODES = (
    "missing_mma_memory",
    "stale_mma_memory",
    "conflicting_mma_memory",
    "mma_memory_ready",
)
MMA_SIGNAL_MEMORY_QUALITY_REASON_CODES = (
    "no_mma_memory_inputs_supplied",
    "missing_mma_memory_present",
    "stale_mma_memory_present",
    "conflicting_mma_memory_present",
    "mma_memory_ready",
)
UNSAFE_PUBLIC_TERMS = (
    "au" "th",
    "buy",
    "candidate",
    "database",
    "dsn",
    "http",
    "li" "ve",
    "mar" "ket",
    "net" "work",
    "or" "der",
    "position",
    "ques" "tion",
    "reco" "mmend",
    "sell",
    "siz" "ing",
    "sl" "ug",
    "source" "_" "text",
    "table",
    "to" "ken",
    "tr" "ade",
    "url",
    "wal" "let",
)


@dataclass(frozen=True)
class ResearchDomainMmaSignalMemoryQualityConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_MMA_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
    stale_fighter_after_seconds: Decimal = Decimal("604800.000000")
    stale_injury_after_seconds: Decimal = Decimal("172800.000000")
    stale_weight_cut_after_seconds: Decimal = Decimal("259200.000000")
    stale_camp_after_seconds: Decimal = Decimal("1209600.000000")
    stale_matchup_context_after_seconds: Decimal = Decimal("604800.000000")
    conflict_block_threshold_count: Decimal = Decimal("1")
    stale_memory_penalty: Decimal = Decimal("0.250000")
    conflict_penalty: Decimal = Decimal("0.400000")
    min_pass_quality_score: Decimal = Decimal("0.700000")
    min_watch_quality_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainMmaSignalMemoryQualityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchDomainMmaSignalMemoryQualityConfig)
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "stale_fighter_after_seconds",
            "stale_injury_after_seconds",
            "stale_weight_cut_after_seconds",
            "stale_camp_after_seconds",
            "stale_matchup_context_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflict_block_threshold_count",
            _normalize_positive_count(
                "conflict_block_threshold_count",
                self.conflict_block_threshold_count,
            ),
        )
        for field_name in (
            "stale_memory_penalty",
            "conflict_penalty",
            "min_pass_quality_score",
            "min_watch_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        if self.min_watch_quality_score > self.min_pass_quality_score:
            raise ValueError("min_watch_quality_score must not exceed min_pass_quality_score")
        _require_hard_flags("ResearchDomainMmaSignalMemoryQualityConfig", self)
        _reject_unsafe_public_payload("mma signal memory quality config", self)


@dataclass(frozen=True)
class ResearchDomainMmaSignalMemoryInput:
    memory_label: str
    team_label: str
    event_label: str
    input_family: str
    memory_present: bool
    observed_at: datetime | None
    evidence_count: Decimal
    conflicting_evidence_count: Decimal
    confidence_score: Decimal
    redaction_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchDomainMmaSignalMemoryInput does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("memory_input", self, ResearchDomainMmaSignalMemoryInput)
        for field_name in ("memory_label", "team_label", "event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("input_family", self.input_family, MMA_MEMORY_INPUT_FAMILIES)
        if type(self.memory_present) is not bool:
            raise ValueError("memory_present must be a bool")
        object.__setattr__(
            self,
            "observed_at",
            _normalize_observed_at(
                field_name="observed_at",
                value=self.observed_at,
                memory_present=self.memory_present,
            ),
        )
        for field_name in ("evidence_count", "conflicting_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _normalize_score("confidence_score", self.confidence_score),
        )
        if self.redaction_confirmed is not True:
            raise ValueError("redaction_confirmed must be True")
        _validate_input(self)
        _require_hard_flags("ResearchDomainMmaSignalMemoryInput", self)
        _reject_unsafe_public_payload("mma signal memory input", self)


@dataclass(frozen=True)
class ResearchDomainMmaSignalMemoryQualityRow:
    memory_label: str
    team_label: str
    event_label: str
    input_family: str
    row_status: str
    memory_present: bool
    memory_age_seconds: Decimal | None
    freshness_limit_seconds: Decimal
    evidence_count: Decimal
    conflicting_evidence_count: Decimal
    confidence_score: Decimal
    stale_memory_penalty: Decimal
    conflict_penalty: Decimal
    quality_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainMmaSignalMemoryQualityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchDomainMmaSignalMemoryQualityRow)
        for field_name in ("memory_label", "team_label", "event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("input_family", self.input_family, MMA_MEMORY_INPUT_FAMILIES)
        _require_member("row_status", self.row_status, MMA_ROW_STATUSES)
        if type(self.memory_present) is not bool:
            raise ValueError("memory_present must be a bool")
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "freshness_limit_seconds",
            _normalize_positive_seconds(
                "freshness_limit_seconds",
                self.freshness_limit_seconds,
            ),
        )
        for field_name in ("evidence_count", "conflicting_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confidence_score",
            "stale_memory_penalty",
            "conflict_penalty",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=MMA_ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        _validate_row(self)
        _require_hard_flags("ResearchDomainMmaSignalMemoryQualityRow", self)
        _reject_unsafe_public_payload("mma signal memory quality row", self)


@dataclass(frozen=True)
class ResearchDomainMmaSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_count: Decimal
    conflict_count: Decimal
    missing_count: Decimal
    average_quality_score: Decimal
    rows: tuple[ResearchDomainMmaSignalMemoryQualityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainMmaSignalMemoryQualityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchDomainMmaSignalMemoryQualityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, MMA_SIGNAL_MEMORY_QUALITY_STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_count",
            "conflict_count",
            "missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quality_score",
            _normalize_score("average_quality_score", self.average_quality_score),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=MMA_SIGNAL_MEMORY_QUALITY_REASON_CODES,
                allow_empty=False,
            ),
        )
        _validate_report(self)
        _require_hard_flags("ResearchDomainMmaSignalMemoryQualityReport", self)
        _reject_unsafe_public_payload("mma signal memory quality report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("mma signal memory quality payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_domain_mma_signal_memory_quality_report(
    rows: list[ResearchDomainMmaSignalMemoryInput]
    | tuple[ResearchDomainMmaSignalMemoryInput, ...],
    *,
    config: ResearchDomainMmaSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainMmaSignalMemoryQualityReport:
    if type(config) is not ResearchDomainMmaSignalMemoryQualityConfig:
        raise ValueError("config must be a ResearchDomainMmaSignalMemoryQualityConfig")
    _require_hard_flags("ResearchDomainMmaSignalMemoryQualityConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    report_rows = tuple(
        sorted(
            (
                _row_for_input(row, config=config, generated_at=generated_at_utc)
                for row in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    pass_count = _status_count(report_rows, "pass")
    watch_count = _status_count(report_rows, "watch")
    block_count = _status_count(report_rows, "block")

    return ResearchDomainMmaSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(block_count, watch_count, len(report_rows)),
        input_count=_count(len(source_rows)),
        row_count=_count(len(report_rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        stale_count=_reason_count(report_rows, "stale_mma_memory"),
        conflict_count=_reason_count(report_rows, "conflicting_mma_memory"),
        missing_count=_reason_count(report_rows, "missing_mma_memory"),
        average_quality_score=_average_score(
            tuple(row.quality_score for row in report_rows),
        ),
        rows=report_rows,
        reason_codes=_report_reason_codes(report_rows, len(source_rows)),
    )


def research_domain_mma_signal_memory_quality_report_payload(
    report: ResearchDomainMmaSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainMmaSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("mma signal memory quality report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("mma signal memory quality payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError("report must be a ResearchDomainMmaSignalMemoryQualityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("mma signal memory quality payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _normalize_source_rows(
    value: object,
) -> tuple[ResearchDomainMmaSignalMemoryInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDomainMmaSignalMemoryInput:
            raise ValueError("rows must contain ResearchDomainMmaSignalMemoryInput values")
        _require_hard_flags("ResearchDomainMmaSignalMemoryInput", row)
        _reject_unsafe_public_payload("mma signal memory input", row)
        if row.memory_label in seen_labels:
            raise ValueError("memory_label values must be unique")
        seen_labels.add(row.memory_label)
    return rows


def _row_for_input(
    row: ResearchDomainMmaSignalMemoryInput,
    *,
    config: ResearchDomainMmaSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainMmaSignalMemoryQualityRow:
    freshness_limit = _freshness_limit(row.input_family, config)
    age_seconds = (
        _age_seconds("observed_at", row.observed_at, generated_at)
        if row.observed_at is not None
        else None
    )
    stale_penalty = (
        config.stale_memory_penalty
        if age_seconds is not None and age_seconds > freshness_limit
        else ZERO_SCORE
    )
    conflict_penalty = (
        config.conflict_penalty
        if row.conflicting_evidence_count >= config.conflict_block_threshold_count
        else ZERO_SCORE
    )
    quality_score = (
        ZERO_SCORE
        if not row.memory_present
        else _clamped_score(row.confidence_score - stale_penalty - conflict_penalty)
    )
    reason_codes = _row_reason_codes(
        memory_present=row.memory_present,
        stale_penalty=stale_penalty,
        conflict_penalty=conflict_penalty,
    )

    return ResearchDomainMmaSignalMemoryQualityRow(
        memory_label=row.memory_label,
        team_label=row.team_label,
        event_label=row.event_label,
        input_family=row.input_family,
        row_status=_row_status(
            quality_score,
            reason_codes=reason_codes,
            config=config,
        ),
        memory_present=row.memory_present,
        memory_age_seconds=age_seconds,
        freshness_limit_seconds=freshness_limit,
        evidence_count=row.evidence_count,
        conflicting_evidence_count=row.conflicting_evidence_count,
        confidence_score=row.confidence_score,
        stale_memory_penalty=stale_penalty,
        conflict_penalty=conflict_penalty,
        quality_score=quality_score,
        reason_codes=reason_codes,
    )


def _freshness_limit(
    input_family: str,
    config: ResearchDomainMmaSignalMemoryQualityConfig,
) -> Decimal:
    if input_family == "fighter":
        return config.stale_fighter_after_seconds
    if input_family == "injury":
        return config.stale_injury_after_seconds
    if input_family == "weight_cut":
        return config.stale_weight_cut_after_seconds
    if input_family == "camp":
        return config.stale_camp_after_seconds
    if input_family == "matchup_context":
        return config.stale_matchup_context_after_seconds
    raise ValueError("input_family must be supported")


def _row_reason_codes(
    *,
    memory_present: bool,
    stale_penalty: Decimal,
    conflict_penalty: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not memory_present:
        codes.append("missing_mma_memory")
    if stale_penalty > ZERO_SCORE:
        codes.append("stale_mma_memory")
    if conflict_penalty > ZERO_SCORE:
        codes.append("conflicting_mma_memory")
    if not codes:
        codes.append("mma_memory_ready")
    return tuple(code for code in MMA_ROW_REASON_CODES if code in codes)


def _row_status(
    quality_score: Decimal,
    *,
    reason_codes: tuple[str, ...],
    config: ResearchDomainMmaSignalMemoryQualityConfig,
) -> str:
    if "missing_mma_memory" in reason_codes or "conflicting_mma_memory" in reason_codes:
        return "block"
    if "stale_mma_memory" in reason_codes:
        return "watch"
    if quality_score >= config.min_pass_quality_score:
        return "pass"
    if quality_score >= config.min_watch_quality_score:
        return "watch"
    return "block"


def _report_reason_codes(
    rows: tuple[ResearchDomainMmaSignalMemoryQualityRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_mma_memory_inputs_supplied",)
    codes: list[str] = []
    if _reason_count(rows, "missing_mma_memory") > ZERO_COUNT:
        codes.append("missing_mma_memory_present")
    if _reason_count(rows, "stale_mma_memory") > ZERO_COUNT:
        codes.append("stale_mma_memory_present")
    if _reason_count(rows, "conflicting_mma_memory") > ZERO_COUNT:
        codes.append("conflicting_mma_memory_present")
    if not codes:
        codes.append("mma_memory_ready")
    return tuple(code for code in MMA_SIGNAL_MEMORY_QUALITY_REASON_CODES if code in codes)


def _report_status(block_count: Decimal, watch_count: Decimal, row_count: int) -> str:
    if row_count == 0 or block_count > ZERO_COUNT:
        return "block"
    if watch_count > ZERO_COUNT:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchDomainMmaSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(Decimal("1") for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[ResearchDomainMmaSignalMemoryQualityRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(Decimal("1") for row in rows if reason_code in row.reason_codes))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        average = sum(values, ZERO_SCORE) / _count(len(values))
    return _normalize_score("average_quality_score", average)


def _row_sort_key(
    row: ResearchDomainMmaSignalMemoryQualityRow,
) -> tuple[int, int, str, str]:
    return (
        _row_priority(row),
        MMA_MEMORY_INPUT_FAMILIES.index(row.input_family),
        row.event_label,
        row.memory_label,
    )


def _row_priority(row: ResearchDomainMmaSignalMemoryQualityRow) -> int:
    if "conflicting_mma_memory" in row.reason_codes:
        return 0
    if "missing_mma_memory" in row.reason_codes:
        return 1
    if "stale_mma_memory" in row.reason_codes:
        return 2
    return 3


def _validate_input(row: ResearchDomainMmaSignalMemoryInput) -> None:
    if row.conflicting_evidence_count > row.evidence_count:
        raise ValueError("conflicting_evidence_count must not exceed evidence_count")
    if row.memory_present and row.observed_at is None:
        raise ValueError("observed_at is required when memory_present is True")
    if row.memory_present and row.evidence_count <= ZERO_COUNT:
        raise ValueError("evidence_count must be positive when memory_present is True")
    if not row.memory_present:
        if row.observed_at is not None:
            raise ValueError("observed_at must be omitted when memory_present is False")
        if row.evidence_count != ZERO_COUNT:
            raise ValueError("evidence_count must be zero when memory_present is False")
        if row.conflicting_evidence_count != ZERO_COUNT:
            raise ValueError(
                "conflicting_evidence_count must be zero when memory_present is False",
            )
        if row.confidence_score != ZERO_SCORE:
            raise ValueError("confidence_score must be zero when memory_present is False")


def _validate_row(row: ResearchDomainMmaSignalMemoryQualityRow) -> None:
    if row.conflicting_evidence_count > row.evidence_count:
        raise ValueError("conflicting_evidence_count must not exceed evidence_count")
    if row.memory_present and row.memory_age_seconds is None:
        raise ValueError("memory_age_seconds is required when memory_present is True")
    if not row.memory_present and row.memory_age_seconds is not None:
        raise ValueError("memory_age_seconds must be omitted when memory_present is False")
    if row.memory_present and row.evidence_count <= ZERO_COUNT:
        raise ValueError("evidence_count must be positive when memory_present is True")
    if not row.memory_present and row.quality_score != ZERO_SCORE:
        raise ValueError("quality_score must be zero when memory_present is False")
    expected_reasons = _row_reason_codes(
        memory_present=row.memory_present,
        stale_penalty=row.stale_memory_penalty,
        conflict_penalty=row.conflict_penalty,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row memory conditions")


def _validate_report(report: ResearchDomainMmaSignalMemoryQualityReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.stale_count != _reason_count(report.rows, "stale_mma_memory"):
        raise ValueError("stale_count must match rows")
    if report.conflict_count != _reason_count(report.rows, "conflicting_mma_memory"):
        raise ValueError("conflict_count must match rows")
    if report.missing_count != _reason_count(report.rows, "missing_mma_memory"):
        raise ValueError("missing_count must match rows")
    if report.average_quality_score != _average_score(
        tuple(row.quality_score for row in report.rows),
    ):
        raise ValueError("average_quality_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, len(report.rows)):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.block_count, report.watch_count, len(report.rows)):
        raise ValueError("status must match rows")


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchDomainMmaSignalMemoryQualityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDomainMmaSignalMemoryQualityRow:
            raise ValueError(
                "rows must contain ResearchDomainMmaSignalMemoryQualityRow values",
            )
        _require_hard_flags("ResearchDomainMmaSignalMemoryQualityRow", row)
        if row.memory_label in seen_labels:
            raise ValueError("memory_label values must be unique")
        seen_labels.add(row.memory_label)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in codes) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _normalize_observed_at(
    *,
    field_name: str,
    value: object,
    memory_present: bool,
) -> datetime | None:
    if value is None:
        return None
    if not memory_present:
        raise ValueError(f"{field_name} must be omitted when memory_present is False")
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(field_name: str, observed_at: datetime, generated_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError(f"{field_name} must be on or before generated_at")
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _normalize_nonnegative_seconds(f"{field_name}_age_seconds", seconds)


def _count(value: int | Decimal) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO_SCORE or normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _clamped_score(value: Decimal) -> Decimal:
    if value <= ZERO_SCORE:
        return ZERO_SCORE
    if value >= ONE_SCORE:
        return ONE_SCORE
    return _normalize_score("quality_score", value)


def _require_exact_type(field_name: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be a {expected.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} public numeric values must use Decimal strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is str or type(value) is bool:
        return value
    raise ValueError("value is not JSON serializable")


def _report_digest(report: ResearchDomainMmaSignalMemoryQualityReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest_string("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_MMA_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
    "MMA_SIGNAL_MEMORY_QUALITY_STATUSES",
    "MMA_SIGNAL_MEMORY_QUALITY_REASON_CODES",
    "ResearchDomainMmaSignalMemoryInput",
    "ResearchDomainMmaSignalMemoryQualityConfig",
    "ResearchDomainMmaSignalMemoryQualityReport",
    "ResearchDomainMmaSignalMemoryQualityRow",
    "build_research_domain_mma_signal_memory_quality_report",
    "research_domain_mma_signal_memory_quality_report_payload",
)
