"""Pure report for cricket signal memory quality before forecast handoff."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_CRICKET_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION = (
    "research-domain-cricket-signal-memory-quality-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

FAMILIES = ("squad", "pitch", "weather", "toss", "form_context")
FAMILY_RANK = {family: index for index, family in enumerate(FAMILIES)}

NO_INPUTS_REASON = "cricket_signal_memory_quality_no_inputs"
PASS_REASON = "cricket_signal_memory_quality_pass"
WATCH_REASON = "cricket_signal_memory_quality_watch"
FRESH_REASON = "cricket_signal_memory_quality_fresh"
NO_CONFLICT_REASON = "cricket_signal_memory_quality_no_conflict"
MEMORY_SCORE_BLOCK_REASON = "cricket_signal_memory_quality_memory_score_block"
CONFLICT_WATCH_REASON = "cricket_signal_memory_quality_conflict_watch"
CONFLICT_BLOCK_REASON = "cricket_signal_memory_quality_conflict_block"

REASON_CODES = tuple(
    sorted(
        (
            NO_INPUTS_REASON,
            PASS_REASON,
            WATCH_REASON,
            FRESH_REASON,
            NO_CONFLICT_REASON,
            MEMORY_SCORE_BLOCK_REASON,
            CONFLICT_WATCH_REASON,
            CONFLICT_BLOCK_REASON,
            "cricket_signal_memory_quality_squad_missing",
            "cricket_signal_memory_quality_squad_stale",
            "cricket_signal_memory_quality_squad_conflicting",
            "cricket_signal_memory_quality_pitch_missing",
            "cricket_signal_memory_quality_pitch_stale",
            "cricket_signal_memory_quality_pitch_conflicting",
            "cricket_signal_memory_quality_weather_missing",
            "cricket_signal_memory_quality_weather_stale",
            "cricket_signal_memory_quality_weather_conflicting",
            "cricket_signal_memory_quality_toss_missing",
            "cricket_signal_memory_quality_toss_stale",
            "cricket_signal_memory_quality_toss_conflicting",
            "cricket_signal_memory_quality_form_context_missing",
            "cricket_signal_memory_quality_form_context_stale",
            "cricket_signal_memory_quality_form_context_conflicting",
        ),
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "candidate",
    "can" + "didate",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion",
    "u" + "rl",
    "h" + "ttp",
    "source" + "_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "au" + "th",
    "net" + "work",
    "data" + "base",
    "posi" + "tion",
    "si" + "ze",
    "siz" + "ing",
    "rec" + "ommend",
    "b" + "uy",
    "s" + "ell",
    "li" + "ve",
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_CRICKET_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
    "ResearchDomainCricketSignalMemoryQualityConfig",
    "ResearchDomainCricketSignalMemoryQualityInput",
    "ResearchDomainCricketSignalMemoryQualityReasonCodeCount",
    "ResearchDomainCricketSignalMemoryQualityReport",
    "ResearchDomainCricketSignalMemoryQualityRow",
    "build_research_domain_cricket_signal_memory_quality_report",
    "research_domain_cricket_signal_memory_quality_report_digest",
    "research_domain_cricket_signal_memory_quality_report_payload",
    "validate_research_domain_cricket_signal_memory_quality_public_payload",
)


@dataclass(frozen=True)
class ResearchDomainCricketSignalMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_CRICKET_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
    )
    stale_squad_after_seconds: Decimal = Decimal("86400.000000")
    stale_pitch_after_seconds: Decimal = Decimal("86400.000000")
    stale_weather_after_seconds: Decimal = Decimal("21600.000000")
    stale_toss_after_seconds: Decimal = Decimal("3600.000000")
    stale_form_context_after_seconds: Decimal = Decimal("86400.000000")
    conflict_block_threshold_count: Decimal = Decimal("2.000000")
    stale_memory_penalty: Decimal = Decimal("0.250000")
    conflict_penalty: Decimal = Decimal("0.350000")
    min_pass_quality_score: Decimal = Decimal("0.700000")
    min_watch_quality_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCricketSignalMemoryQualityConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "stale_squad_after_seconds",
            "stale_pitch_after_seconds",
            "stale_weather_after_seconds",
            "stale_toss_after_seconds",
            "stale_form_context_after_seconds",
            "conflict_block_threshold_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
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
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_quality_score <= self.min_watch_quality_score:
            raise ValueError("min_pass_quality_score must exceed min_watch_quality_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainCricketSignalMemoryQualityInput:
    event_bucket: str
    team_memory_bucket: str
    input_family: str
    memory_present: bool
    observed_at: datetime | None
    evidence_count: Decimal
    conflicting_evidence_count: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCricketSignalMemoryQualityInput,
            "input",
        )
        for field_name in ("event_bucket", "team_memory_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        _require_family("input_family", self.input_family)
        if type(self.memory_present) is not bool:
            raise TypeError("memory_present must be exactly bool")
        object.__setattr__(
            self,
            "observed_at",
            _as_optional_utc("observed_at", self.observed_at),
        )
        for field_name in ("evidence_count", "conflicting_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        if self.memory_present and self.observed_at is None:
            raise ValueError("observed_at is required when memory_present is True")
        if not self.memory_present:
            if self.observed_at is not None:
                raise ValueError("observed_at must be omitted when memory_present is False")
            if self.evidence_count != ZERO:
                raise ValueError("evidence_count must be zero when memory is missing")
            if self.conflicting_evidence_count != ZERO:
                raise ValueError(
                    "conflicting_evidence_count must be zero when memory is missing",
                )
            if self.confidence_score != ZERO:
                raise ValueError("confidence_score must be zero when memory is missing")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainCricketSignalMemoryQualityRow:
    event_bucket: str
    team_memory_bucket: str
    input_family: str
    public_status: str
    freshness_status: str
    conflict_status: str
    memory_present: bool
    observed_at: datetime | None
    memory_age_seconds: Decimal | None
    freshness_limit_seconds: Decimal
    evidence_count: Decimal
    conflicting_evidence_count: Decimal
    confidence_score: Decimal
    stale_memory_penalty: Decimal
    conflict_penalty_score: Decimal
    quality_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCricketSignalMemoryQualityRow,
            "row",
        )
        for field_name in ("event_bucket", "team_memory_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        _require_family("input_family", self.input_family)
        for field_name in ("public_status", "freshness_status", "conflict_status"):
            _require_status(field_name, getattr(self, field_name))
        if type(self.memory_present) is not bool:
            raise TypeError("memory_present must be exactly bool")
        object.__setattr__(
            self,
            "observed_at",
            _as_optional_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_optional_nonnegative_decimal(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "freshness_limit_seconds",
            _require_positive_decimal(
                "freshness_limit_seconds",
                self.freshness_limit_seconds,
            ),
        )
        for field_name in ("evidence_count", "conflicting_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confidence_score",
            "stale_memory_penalty",
            "conflict_penalty_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainCricketSignalMemoryQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCricketSignalMemoryQualityReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _require_ratio_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainCricketSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_count: Decimal
    conflict_count: Decimal
    missing_count: Decimal
    average_quality_score: Decimal
    squad_missing_count: Decimal
    squad_stale_count: Decimal
    squad_conflict_count: Decimal
    pitch_missing_count: Decimal
    pitch_stale_count: Decimal
    pitch_conflict_count: Decimal
    weather_missing_count: Decimal
    weather_stale_count: Decimal
    weather_conflict_count: Decimal
    toss_missing_count: Decimal
    toss_stale_count: Decimal
    toss_conflict_count: Decimal
    form_context_missing_count: Decimal
    form_context_stale_count: Decimal
    form_context_conflict_count: Decimal
    rows: tuple[ResearchDomainCricketSignalMemoryQualityRow, ...]
    reason_code_counts: tuple[ResearchDomainCricketSignalMemoryQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCricketSignalMemoryQualityReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("report_status", self.report_status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_count",
            "conflict_count",
            "missing_count",
            "squad_missing_count",
            "squad_stale_count",
            "squad_conflict_count",
            "pitch_missing_count",
            "pitch_stale_count",
            "pitch_conflict_count",
            "weather_missing_count",
            "weather_stale_count",
            "weather_conflict_count",
            "toss_missing_count",
            "toss_stale_count",
            "toss_conflict_count",
            "form_context_missing_count",
            "form_context_stale_count",
            "form_context_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quality_score",
            _require_ratio_decimal("average_quality_score", self.average_quality_score),
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
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _digest_payload(_public_payload_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_cricket_signal_memory_quality_report_payload(self)

    @property
    def digest(self) -> str:
        return research_domain_cricket_signal_memory_quality_report_digest(self)


def build_research_domain_cricket_signal_memory_quality_report(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityInput, ...],
    *,
    config: ResearchDomainCricketSignalMemoryQualityConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainCricketSignalMemoryQualityReport:
    cfg = config or ResearchDomainCricketSignalMemoryQualityConfig()
    if type(cfg) is not ResearchDomainCricketSignalMemoryQualityConfig:
        raise TypeError(
            "config must be exactly ResearchDomainCricketSignalMemoryQualityConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows, generated_at=generated_at_utc)
    if not input_rows:
        reason_counts = (
            ResearchDomainCricketSignalMemoryQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                input_ratio=ZERO,
            ),
        )
        return ResearchDomainCricketSignalMemoryQualityReport(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            report_status=STATUS_BLOCK,
            input_count=ZERO,
            row_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            stale_count=ZERO,
            conflict_count=ZERO,
            missing_count=ZERO,
            average_quality_score=ZERO,
            squad_missing_count=ZERO,
            squad_stale_count=ZERO,
            squad_conflict_count=ZERO,
            pitch_missing_count=ZERO,
            pitch_stale_count=ZERO,
            pitch_conflict_count=ZERO,
            weather_missing_count=ZERO,
            weather_stale_count=ZERO,
            weather_conflict_count=ZERO,
            toss_missing_count=ZERO,
            toss_stale_count=ZERO,
            toss_conflict_count=ZERO,
            form_context_missing_count=ZERO,
            form_context_stale_count=ZERO,
            form_context_conflict_count=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        sorted(
            (
                _row_from_input(row, config=cfg, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_counts = _reason_code_counts(report_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    return ResearchDomainCricketSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=_summary_status(report_rows),
        input_count=_count_decimal(len(input_rows)),
        row_count=_count_decimal(len(report_rows)),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        stale_count=_count_if(report_rows, lambda row: _is_stale_row(row)),
        conflict_count=_count_if(report_rows, lambda row: row.conflicting_evidence_count > ZERO),
        missing_count=_count_if(report_rows, lambda row: not row.memory_present),
        average_quality_score=_average(row.quality_score for row in report_rows),
        squad_missing_count=_family_count(report_rows, "squad", "missing"),
        squad_stale_count=_family_count(report_rows, "squad", "stale"),
        squad_conflict_count=_family_count(report_rows, "squad", "conflict"),
        pitch_missing_count=_family_count(report_rows, "pitch", "missing"),
        pitch_stale_count=_family_count(report_rows, "pitch", "stale"),
        pitch_conflict_count=_family_count(report_rows, "pitch", "conflict"),
        weather_missing_count=_family_count(report_rows, "weather", "missing"),
        weather_stale_count=_family_count(report_rows, "weather", "stale"),
        weather_conflict_count=_family_count(report_rows, "weather", "conflict"),
        toss_missing_count=_family_count(report_rows, "toss", "missing"),
        toss_stale_count=_family_count(report_rows, "toss", "stale"),
        toss_conflict_count=_family_count(report_rows, "toss", "conflict"),
        form_context_missing_count=_family_count(report_rows, "form_context", "missing"),
        form_context_stale_count=_family_count(report_rows, "form_context", "stale"),
        form_context_conflict_count=_family_count(report_rows, "form_context", "conflict"),
        rows=report_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_domain_cricket_signal_memory_quality_report_payload(
    report: ResearchDomainCricketSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainCricketSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise TypeError(
            "report must be exactly ResearchDomainCricketSignalMemoryQualityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_domain_cricket_signal_memory_quality_public_payload(payload)
    return payload


def validate_research_domain_cricket_signal_memory_quality_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _DictFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def research_domain_cricket_signal_memory_quality_report_digest(
    report: ResearchDomainCricketSignalMemoryQualityReport,
) -> str:
    if type(report) is not ResearchDomainCricketSignalMemoryQualityReport:
        raise TypeError(
            "report must be exactly ResearchDomainCricketSignalMemoryQualityReport",
        )
    return _digest_payload(_public_payload_without_digest(report))


def _row_from_input(
    row: ResearchDomainCricketSignalMemoryQualityInput,
    *,
    config: ResearchDomainCricketSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainCricketSignalMemoryQualityRow:
    if type(row) is not ResearchDomainCricketSignalMemoryQualityInput:
        raise TypeError(
            "row must be exactly ResearchDomainCricketSignalMemoryQualityInput",
        )
    _require_hard_flags("input", row)
    age = _optional_age_seconds(generated_at, row.observed_at)
    limit = _freshness_limit(row.input_family, config)
    is_stale = age is not None and age > limit
    conflict_penalty_score = _bounded_ratio(
        row.conflicting_evidence_count * config.conflict_penalty,
    )
    stale_penalty = config.stale_memory_penalty if is_stale else ZERO
    quality_score = (
        ZERO
        if not row.memory_present
        else _bounded_ratio(row.confidence_score - stale_penalty - conflict_penalty_score)
    )
    conflict_status = _conflict_status(row, config)
    freshness_status = _freshness_status(row.memory_present, is_stale)
    public_status = _row_status(
        quality_score=quality_score,
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        public_status=public_status,
        is_stale=is_stale,
        conflict_status=conflict_status,
        quality_score=quality_score,
        config=config,
    )
    return ResearchDomainCricketSignalMemoryQualityRow(
        event_bucket=row.event_bucket,
        team_memory_bucket=row.team_memory_bucket,
        input_family=row.input_family,
        public_status=public_status,
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        memory_present=row.memory_present,
        observed_at=row.observed_at,
        memory_age_seconds=age,
        freshness_limit_seconds=limit,
        evidence_count=row.evidence_count,
        conflicting_evidence_count=row.conflicting_evidence_count,
        confidence_score=row.confidence_score,
        stale_memory_penalty=stale_penalty,
        conflict_penalty_score=conflict_penalty_score,
        quality_score=quality_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchDomainCricketSignalMemoryQualityInput,
    *,
    public_status: str,
    is_stale: bool,
    conflict_status: str,
    quality_score: Decimal,
    config: ResearchDomainCricketSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not row.memory_present:
        reasons.append(f"cricket_signal_memory_quality_{row.input_family}_missing")
    elif is_stale:
        reasons.append(f"cricket_signal_memory_quality_{row.input_family}_stale")
    elif row.conflicting_evidence_count == ZERO:
        reasons.append(FRESH_REASON)

    if row.conflicting_evidence_count > ZERO:
        reasons.append(f"cricket_signal_memory_quality_{row.input_family}_conflicting")
        if conflict_status == STATUS_BLOCK:
            reasons.append(CONFLICT_BLOCK_REASON)
        else:
            reasons.append(CONFLICT_WATCH_REASON)
    elif row.memory_present:
        reasons.append(NO_CONFLICT_REASON)

    if quality_score < config.min_watch_quality_score:
        reasons.append(MEMORY_SCORE_BLOCK_REASON)
    elif public_status == STATUS_WATCH:
        reasons.append(WATCH_REASON)
    elif public_status == STATUS_PASS:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _freshness_status(memory_present: bool, is_stale: bool) -> str:
    if not memory_present:
        return STATUS_BLOCK
    if is_stale:
        return STATUS_WATCH
    return STATUS_PASS


def _conflict_status(
    row: ResearchDomainCricketSignalMemoryQualityInput,
    config: ResearchDomainCricketSignalMemoryQualityConfig,
) -> str:
    if row.conflicting_evidence_count >= config.conflict_block_threshold_count:
        return STATUS_BLOCK
    if row.conflicting_evidence_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _row_status(
    *,
    quality_score: Decimal,
    freshness_status: str,
    conflict_status: str,
    config: ResearchDomainCricketSignalMemoryQualityConfig,
) -> str:
    if conflict_status == STATUS_BLOCK:
        return STATUS_BLOCK
    if freshness_status == STATUS_BLOCK:
        return STATUS_BLOCK
    if quality_score < config.min_watch_quality_score:
        return STATUS_BLOCK
    if (
        freshness_status == STATUS_WATCH
        or conflict_status == STATUS_WATCH
        or quality_score < config.min_pass_quality_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _summary_status(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityRow, ...],
) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _freshness_limit(
    input_family: str,
    config: ResearchDomainCricketSignalMemoryQualityConfig,
) -> Decimal:
    if input_family == "squad":
        return config.stale_squad_after_seconds
    if input_family == "pitch":
        return config.stale_pitch_after_seconds
    if input_family == "weather":
        return config.stale_weather_after_seconds
    if input_family == "toss":
        return config.stale_toss_after_seconds
    if input_family == "form_context":
        return config.stale_form_context_after_seconds
    raise ValueError("input_family must be supported")


def _row_sort_key(
    row: ResearchDomainCricketSignalMemoryQualityRow,
) -> tuple[int, Decimal, int, str, str]:
    return (
        STATUS_RANK[row.public_status],
        -row.quality_score,
        FAMILY_RANK[row.input_family],
        row.event_bucket,
        row.team_memory_bucket,
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainCricketSignalMemoryQualityReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count_decimal(len(rows))
    return tuple(
        ResearchDomainCricketSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            input_ratio=_ratio(_count_decimal(count), denominator),
        )
        for reason_code, count in sorted(counts.items())
    )


def _family_count(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityRow, ...],
    family: str,
    condition: str,
) -> Decimal:
    if condition == "missing":
        return _count_if(
            rows,
            lambda row: row.input_family == family and not row.memory_present,
        )
    if condition == "stale":
        return _count_if(
            rows,
            lambda row: row.input_family == family and _is_stale_row(row),
        )
    if condition == "conflict":
        return _count_if(
            rows,
            lambda row: row.input_family == family
            and row.conflicting_evidence_count > ZERO,
        )
    raise ValueError("condition must be supported")


def _status_count(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count_if(rows, lambda row: row.public_status == status)


def _count_if(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityRow, ...],
    predicate: Any,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if predicate(row)))


def _is_stale_row(row: ResearchDomainCricketSignalMemoryQualityRow) -> bool:
    return row.memory_age_seconds is not None and (
        row.memory_age_seconds > row.freshness_limit_seconds
    )


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(sum(items, ZERO), _count_decimal(len(items)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _bounded_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise TypeError("count value must be exactly int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _normalize_input_rows(
    rows: tuple[ResearchDomainCricketSignalMemoryQualityInput, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchDomainCricketSignalMemoryQualityInput, ...]:
    if not isinstance(rows, tuple):
        raise TypeError("rows must be a tuple")
    normalized: list[ResearchDomainCricketSignalMemoryQualityInput] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchDomainCricketSignalMemoryQualityInput:
            raise TypeError(
                "row must be exactly ResearchDomainCricketSignalMemoryQualityInput",
            )
        _require_hard_flags("input", row)
        if row.observed_at is not None and row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.event_bucket, row.team_memory_bucket, row.input_family)
        if key in seen:
            raise ValueError("input rows must be unique by public bucket and family")
        seen.add(key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchDomainCricketSignalMemoryQualityRow, ...]:
    if not isinstance(rows, tuple):
        raise TypeError("rows must be a tuple")
    normalized: list[ResearchDomainCricketSignalMemoryQualityRow] = []
    for row in rows:
        if type(row) is not ResearchDomainCricketSignalMemoryQualityRow:
            raise TypeError("row must be exactly ResearchDomainCricketSignalMemoryQualityRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchDomainCricketSignalMemoryQualityReasonCodeCount, ...]:
    if not isinstance(rows, tuple):
        raise TypeError("reason_code_counts must be a tuple")
    normalized: list[ResearchDomainCricketSignalMemoryQualityReasonCodeCount] = []
    for row in rows:
        if type(row) is not ResearchDomainCricketSignalMemoryQualityReasonCodeCount:
            raise TypeError(
                "reason_code_count must be exactly "
                "ResearchDomainCricketSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.reason_code))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_reason_code("reason_codes", value))
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(sorted(set(normalized)))


def _validate_row(row: ResearchDomainCricketSignalMemoryQualityRow) -> None:
    if row.memory_present and row.observed_at is None:
        raise ValueError("observed_at is required when memory_present is True")
    if not row.memory_present and row.memory_age_seconds is not None:
        raise ValueError("memory_age_seconds must be omitted when memory is missing")
    expected_conflict_status = STATUS_PASS
    if row.conflicting_evidence_count > ZERO:
        expected_conflict_status = (
            STATUS_BLOCK if CONFLICT_BLOCK_REASON in row.reason_codes else STATUS_WATCH
        )
    if row.conflict_status != expected_conflict_status:
        raise ValueError("conflict_status is inconsistent with reason_codes")
    expected_freshness_status = (
        STATUS_BLOCK
        if not row.memory_present
        else STATUS_WATCH
        if _is_stale_row(row)
        else STATUS_PASS
    )
    if row.freshness_status != expected_freshness_status:
        raise ValueError("freshness_status is inconsistent with memory age")


def _validate_report(report: ResearchDomainCricketSignalMemoryQualityReport) -> None:
    rows = report.rows
    if report.input_count != _count_decimal(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    expected_counts = {
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "stale_count": _count_if(rows, lambda row: _is_stale_row(row)),
        "conflict_count": _count_if(rows, lambda row: row.conflicting_evidence_count > ZERO),
        "missing_count": _count_if(rows, lambda row: not row.memory_present),
        "squad_missing_count": _family_count(rows, "squad", "missing"),
        "squad_stale_count": _family_count(rows, "squad", "stale"),
        "squad_conflict_count": _family_count(rows, "squad", "conflict"),
        "pitch_missing_count": _family_count(rows, "pitch", "missing"),
        "pitch_stale_count": _family_count(rows, "pitch", "stale"),
        "pitch_conflict_count": _family_count(rows, "pitch", "conflict"),
        "weather_missing_count": _family_count(rows, "weather", "missing"),
        "weather_stale_count": _family_count(rows, "weather", "stale"),
        "weather_conflict_count": _family_count(rows, "weather", "conflict"),
        "toss_missing_count": _family_count(rows, "toss", "missing"),
        "toss_stale_count": _family_count(rows, "toss", "stale"),
        "toss_conflict_count": _family_count(rows, "toss", "conflict"),
        "form_context_missing_count": _family_count(rows, "form_context", "missing"),
        "form_context_stale_count": _family_count(rows, "form_context", "stale"),
        "form_context_conflict_count": _family_count(rows, "form_context", "conflict"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_quality_score != _average(row.quality_score for row in rows):
        raise ValueError("average_quality_score must match rows")
    expected_status = STATUS_BLOCK if not rows else _summary_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    expected_reason_counts = _reason_code_counts(rows) if rows else report.reason_code_counts
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _public_payload_without_digest(
    report: ResearchDomainCricketSignalMemoryQualityReport,
) -> dict[str, Any]:
    return _json_ready(report, omit_digest=True)


def _json_ready(value: Any, *, omit_digest: bool = False) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if omit_digest and field.name == "derived_validation_digest":
                continue
            ready[field.name] = _json_ready(getattr(value, field.name), omit_digest=omit_digest)
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise TypeError("Decimal values must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise TypeError("datetime values must be exactly datetime")
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, float) or type(value) is int:
        raise TypeError("JSON value must use Decimal-derived strings")
    if isinstance(value, dict):
        ready_dict: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("JSON object keys must be strings")
            ready_dict[key] = _json_ready(item, omit_digest=omit_digest)
        return ready_dict
    if isinstance(value, (list, tuple)):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    raise TypeError("value is not JSON serializable")


def _digest_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _optional_age_seconds(end: datetime, start: datetime | None) -> Decimal | None:
    if start is None:
        return None
    delta = end - start
    if delta.total_seconds() < 0:
        raise ValueError("observed_at must not be after generated_at")
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical public string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value for {field_name}")
    return value


def _require_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FAMILIES:
        raise ValueError(f"{field_name} must be a supported cricket memory family")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
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
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return _quantize(normalized)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


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
