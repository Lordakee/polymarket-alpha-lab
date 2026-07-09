"""Pure report-only reducer for domain team playbook adherence."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_ADHERENCE_REPORT_CONFIG_VERSION = (
    "research-team-domain-playbook-adherence-report-v0"
)
DOMAIN_PLAYBOOK_ADHERENCE_STATUSES = ("pass", "watch", "block")
DOMAIN_PLAYBOOK_ADHERENCE_REASON_CODES = (
    "no_domain_playbook_adherence_inputs",
    "playbook_steps_incomplete",
    "playbook_steps_watch",
    "required_source_coverage_gap",
    "required_source_coverage_watch",
    "calibration_note_gap",
    "calibration_note_watch",
    "stale_memory_override_missing_documentation",
    "stale_memory_override_watch",
    "review_latency_sla_breach",
    "review_latency_watch",
    "exception_documentation_gap",
    "exception_documentation_watch",
    "domain_playbook_adherence_block",
    "domain_playbook_adherence_watch",
    "domain_playbook_adherence_pass",
)

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_PRIORITY = DOMAIN_PLAYBOOK_ADHERENCE_REASON_CODES[1:]
_UNSAFE_PUBLIC_LABEL_FRAGMENTS = frozenset(
    (
        "candidate" "_" "id",
        "market" "_" "id",
        "market" "_" "slug",
        "ques" "tion",
        "source" "_" "url",
        "source" "_" "text",
        "d" "sn",
        "table" "_" "name",
        "private" "_" "token",
        "wal" "let",
        "acc" "ount",
        "or" "der",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "cl" "ob",
        "au" "th",
        "net" "work",
        "reco" "mmend",
        "siz" "ing",
        "tr" "ade",
        "li" "ve",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_ADHERENCE_REPORT_CONFIG_VERSION",
    "DOMAIN_PLAYBOOK_ADHERENCE_STATUSES",
    "DOMAIN_PLAYBOOK_ADHERENCE_REASON_CODES",
    "ResearchTeamDomainPlaybookAdherenceConfig",
    "ResearchTeamDomainPlaybookAdherenceInput",
    "ResearchTeamDomainPlaybookAdherenceReport",
    "ResearchTeamDomainPlaybookAdherenceRow",
    "build_research_team_domain_playbook_adherence_report",
    "research_team_domain_playbook_adherence_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookAdherenceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_ADHERENCE_REPORT_CONFIG_VERSION
    )
    playbook_step_pass_threshold: Decimal = Decimal("0.900000")
    playbook_step_watch_threshold: Decimal = Decimal("0.700000")
    source_coverage_pass_threshold: Decimal = Decimal("0.900000")
    source_coverage_watch_threshold: Decimal = Decimal("0.700000")
    calibration_note_pass_threshold: Decimal = Decimal("0.800000")
    calibration_note_watch_threshold: Decimal = Decimal("0.500000")
    documentation_pass_threshold: Decimal = Decimal("0.900000")
    documentation_watch_threshold: Decimal = Decimal("0.700000")
    review_latency_watch_seconds: Decimal = Decimal("7200.000000")
    review_latency_block_seconds: Decimal = Decimal("14400.000000")
    adherence_pass_threshold: Decimal = Decimal("0.850000")
    adherence_watch_threshold: Decimal = Decimal("0.650000")
    playbook_step_weight: Decimal = Decimal("0.250000")
    source_coverage_weight: Decimal = Decimal("0.200000")
    calibration_note_weight: Decimal = Decimal("0.150000")
    stale_override_weight: Decimal = Decimal("0.150000")
    exception_documentation_weight: Decimal = Decimal("0.150000")
    review_latency_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookAdherenceConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamDomainPlaybookAdherenceConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "playbook_step_pass_threshold",
            "playbook_step_watch_threshold",
            "source_coverage_pass_threshold",
            "source_coverage_watch_threshold",
            "calibration_note_pass_threshold",
            "calibration_note_watch_threshold",
            "documentation_pass_threshold",
            "documentation_watch_threshold",
            "adherence_pass_threshold",
            "adherence_watch_threshold",
            "playbook_step_weight",
            "source_coverage_weight",
            "calibration_note_weight",
            "stale_override_weight",
            "exception_documentation_weight",
            "review_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("review_latency_watch_seconds", "review_latency_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "playbook_step",
            self.playbook_step_pass_threshold,
            self.playbook_step_watch_threshold,
        )
        _require_threshold_sequence(
            "source_coverage",
            self.source_coverage_pass_threshold,
            self.source_coverage_watch_threshold,
        )
        _require_threshold_sequence(
            "calibration_note",
            self.calibration_note_pass_threshold,
            self.calibration_note_watch_threshold,
        )
        _require_threshold_sequence(
            "documentation",
            self.documentation_pass_threshold,
            self.documentation_watch_threshold,
        )
        _require_threshold_sequence(
            "adherence",
            self.adherence_pass_threshold,
            self.adherence_watch_threshold,
        )
        if self.review_latency_watch_seconds <= _ZERO:
            raise ValueError("review_latency_watch_seconds must be positive")
        if self.review_latency_block_seconds <= self.review_latency_watch_seconds:
            raise ValueError(
                "review_latency_block_seconds must exceed review_latency_watch_seconds",
            )
        if _quantize(
            self.playbook_step_weight
            + self.source_coverage_weight
            + self.calibration_note_weight
            + self.stale_override_weight
            + self.exception_documentation_weight
            + self.review_latency_weight,
        ) != _ONE:
            raise ValueError("adherence weights must sum to one")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookAdherenceInput:
    team_label: str
    domain_label: str
    playbook_step_count: Decimal
    followed_playbook_step_count: Decimal
    required_source_count: Decimal
    cited_required_source_count: Decimal
    required_calibration_note_count: Decimal
    calibration_note_count: Decimal
    stale_memory_override_count: Decimal
    documented_stale_memory_override_count: Decimal
    exception_count: Decimal
    documented_exception_count: Decimal
    review_started_at: datetime
    review_completed_at: datetime
    redaction_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookAdherenceInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("adherence_input", self, ResearchTeamDomainPlaybookAdherenceInput)
        for field_name in ("team_label", "domain_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "playbook_step_count",
            "followed_playbook_step_count",
            "required_source_count",
            "cited_required_source_count",
            "required_calibration_note_count",
            "calibration_note_count",
            "stale_memory_override_count",
            "documented_stale_memory_override_count",
            "exception_count",
            "documented_exception_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.playbook_step_count <= _ZERO_COUNT:
            raise ValueError("playbook_step_count must be positive")
        if self.required_source_count <= _ZERO_COUNT:
            raise ValueError("required_source_count must be positive")
        _require_count_at_most(
            "followed_playbook_step_count",
            self.followed_playbook_step_count,
            "playbook_step_count",
            self.playbook_step_count,
        )
        _require_count_at_most(
            "cited_required_source_count",
            self.cited_required_source_count,
            "required_source_count",
            self.required_source_count,
        )
        _require_count_at_most(
            "calibration_note_count",
            self.calibration_note_count,
            "required_calibration_note_count",
            self.required_calibration_note_count,
        )
        _require_count_at_most(
            "documented_stale_memory_override_count",
            self.documented_stale_memory_override_count,
            "stale_memory_override_count",
            self.stale_memory_override_count,
        )
        _require_count_at_most(
            "documented_exception_count",
            self.documented_exception_count,
            "exception_count",
            self.exception_count,
        )
        object.__setattr__(
            self,
            "review_started_at",
            _as_utc("review_started_at", self.review_started_at),
        )
        object.__setattr__(
            self,
            "review_completed_at",
            _as_utc("review_completed_at", self.review_completed_at),
        )
        if self.review_completed_at < self.review_started_at:
            raise ValueError("review_completed_at must be at or after review_started_at")
        if self.redaction_confirmed is not True:
            raise ValueError("redaction_confirmed must be True")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("adherence_input", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookAdherenceRow:
    team_label: str
    domain_label: str
    playbook_step_count: Decimal
    followed_playbook_step_count: Decimal
    playbook_step_adherence_ratio: Decimal
    required_source_count: Decimal
    cited_required_source_count: Decimal
    required_source_coverage_ratio: Decimal
    required_calibration_note_count: Decimal
    calibration_note_count: Decimal
    calibration_note_ratio: Decimal
    stale_memory_override_count: Decimal
    documented_stale_memory_override_count: Decimal
    stale_override_documentation_ratio: Decimal
    exception_count: Decimal
    documented_exception_count: Decimal
    exception_documentation_ratio: Decimal
    review_latency_seconds: Decimal
    review_latency_score: Decimal
    playbook_adherence_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookAdherenceRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamDomainPlaybookAdherenceRow)
        for field_name in ("team_label", "domain_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "playbook_step_count",
            "followed_playbook_step_count",
            "required_source_count",
            "cited_required_source_count",
            "required_calibration_note_count",
            "calibration_note_count",
            "stale_memory_override_count",
            "documented_stale_memory_override_count",
            "exception_count",
            "documented_exception_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "playbook_step_adherence_ratio",
            "required_source_coverage_ratio",
            "calibration_note_ratio",
            "stale_override_documentation_ratio",
            "exception_documentation_ratio",
            "review_latency_score",
            "playbook_adherence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_latency_seconds",
            _normalize_nonnegative_decimal("review_latency_seconds", self.review_latency_seconds),
        )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookAdherenceReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    team_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_playbook_step_adherence_ratio: Decimal
    average_required_source_coverage_ratio: Decimal
    average_calibration_note_ratio: Decimal
    average_stale_override_documentation_ratio: Decimal
    average_exception_documentation_ratio: Decimal
    average_review_latency_seconds: Decimal
    average_playbook_adherence_score: Decimal
    rows: tuple[ResearchTeamDomainPlaybookAdherenceRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookAdherenceReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamDomainPlaybookAdherenceReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "team_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_playbook_step_adherence_ratio",
            "average_required_source_coverage_ratio",
            "average_calibration_note_ratio",
            "average_stale_override_documentation_ratio",
            "average_exception_documentation_ratio",
            "average_playbook_adherence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_review_latency_seconds",
            _normalize_nonnegative_decimal(
                "average_review_latency_seconds",
                self.average_review_latency_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_surface("payload", payload)
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        _validate_payload_schema(payload)
        return payload


def build_research_team_domain_playbook_adherence_report(
    inputs: Iterable[ResearchTeamDomainPlaybookAdherenceInput],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainPlaybookAdherenceConfig | None = None,
) -> ResearchTeamDomainPlaybookAdherenceReport:
    if config is None:
        config = ResearchTeamDomainPlaybookAdherenceConfig()
    _require_exact_type("config", config, ResearchTeamDomainPlaybookAdherenceConfig)
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.review_completed_at > generated_at:
            raise ValueError("generated_at must be at or after review_completed_at")
    rows = tuple(
        sorted(
            (_row_from_input(value, config) for value in normalized),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamDomainPlaybookAdherenceReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        team_count=_decimal_count(len({row.team_label for row in rows})),
        domain_count=_decimal_count(len({row.domain_label for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_playbook_step_adherence_ratio=_average_score(
            tuple(row.playbook_step_adherence_ratio for row in rows),
        ),
        average_required_source_coverage_ratio=_average_score(
            tuple(row.required_source_coverage_ratio for row in rows),
        ),
        average_calibration_note_ratio=_average_score(
            tuple(row.calibration_note_ratio for row in rows),
        ),
        average_stale_override_documentation_ratio=_average_score(
            tuple(row.stale_override_documentation_ratio for row in rows),
        ),
        average_exception_documentation_ratio=_average_score(
            tuple(row.exception_documentation_ratio for row in rows),
        ),
        average_review_latency_seconds=_average_score(
            tuple(row.review_latency_seconds for row in rows),
        ),
        average_playbook_adherence_score=_average_score(
            tuple(row.playbook_adherence_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_domain_playbook_adherence_report_payload(
    report: ResearchTeamDomainPlaybookAdherenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainPlaybookAdherenceReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        _validate_payload_schema(payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamDomainPlaybookAdherenceReport or payload",
    )


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


def _row_from_input(
    value: ResearchTeamDomainPlaybookAdherenceInput,
    config: ResearchTeamDomainPlaybookAdherenceConfig,
) -> ResearchTeamDomainPlaybookAdherenceRow:
    playbook_ratio = _bounded_ratio(
        value.followed_playbook_step_count,
        value.playbook_step_count,
    )
    source_ratio = _bounded_ratio(
        value.cited_required_source_count,
        value.required_source_count,
    )
    calibration_ratio = _bounded_ratio(
        value.calibration_note_count,
        value.required_calibration_note_count,
    )
    stale_documentation_ratio = _bounded_ratio(
        value.documented_stale_memory_override_count,
        value.stale_memory_override_count,
    )
    exception_documentation_ratio = _bounded_ratio(
        value.documented_exception_count,
        value.exception_count,
    )
    review_latency_seconds = _seconds_between(value.review_started_at, value.review_completed_at)
    review_latency_score = _review_latency_score(review_latency_seconds, config)
    adherence_score = _adherence_score(
        playbook_step_score=playbook_ratio,
        source_coverage_score=source_ratio,
        calibration_note_score=calibration_ratio,
        stale_override_score=stale_documentation_ratio,
        exception_documentation_score=exception_documentation_ratio,
        review_latency_score=review_latency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        playbook_step_score=playbook_ratio,
        source_coverage_score=source_ratio,
        calibration_note_score=calibration_ratio,
        stale_override_score=stale_documentation_ratio,
        exception_documentation_score=exception_documentation_ratio,
        review_latency_seconds=review_latency_seconds,
        adherence_score=adherence_score,
        config=config,
    )
    return ResearchTeamDomainPlaybookAdherenceRow(
        team_label=value.team_label,
        domain_label=value.domain_label,
        playbook_step_count=value.playbook_step_count,
        followed_playbook_step_count=value.followed_playbook_step_count,
        playbook_step_adherence_ratio=playbook_ratio,
        required_source_count=value.required_source_count,
        cited_required_source_count=value.cited_required_source_count,
        required_source_coverage_ratio=source_ratio,
        required_calibration_note_count=value.required_calibration_note_count,
        calibration_note_count=value.calibration_note_count,
        calibration_note_ratio=calibration_ratio,
        stale_memory_override_count=value.stale_memory_override_count,
        documented_stale_memory_override_count=value.documented_stale_memory_override_count,
        stale_override_documentation_ratio=stale_documentation_ratio,
        exception_count=value.exception_count,
        documented_exception_count=value.documented_exception_count,
        exception_documentation_ratio=exception_documentation_ratio,
        review_latency_seconds=review_latency_seconds,
        review_latency_score=review_latency_score,
        playbook_adherence_score=adherence_score,
        row_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _review_latency_score(
    review_latency_seconds: Decimal,
    config: ResearchTeamDomainPlaybookAdherenceConfig,
) -> Decimal:
    if review_latency_seconds <= config.review_latency_watch_seconds:
        return _ONE
    if review_latency_seconds >= config.review_latency_block_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        elapsed_over_watch = review_latency_seconds - config.review_latency_watch_seconds
        latency_band = config.review_latency_block_seconds - config.review_latency_watch_seconds
        return _quantize(_ONE - (elapsed_over_watch / latency_band))


def _adherence_score(
    *,
    playbook_step_score: Decimal,
    source_coverage_score: Decimal,
    calibration_note_score: Decimal,
    stale_override_score: Decimal,
    exception_documentation_score: Decimal,
    review_latency_score: Decimal,
    config: ResearchTeamDomainPlaybookAdherenceConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (playbook_step_score * config.playbook_step_weight)
            + (source_coverage_score * config.source_coverage_weight)
            + (calibration_note_score * config.calibration_note_weight)
            + (stale_override_score * config.stale_override_weight)
            + (exception_documentation_score * config.exception_documentation_weight)
            + (review_latency_score * config.review_latency_weight),
        )


def _row_reason_codes(
    *,
    playbook_step_score: Decimal,
    source_coverage_score: Decimal,
    calibration_note_score: Decimal,
    stale_override_score: Decimal,
    exception_documentation_score: Decimal,
    review_latency_seconds: Decimal,
    adherence_score: Decimal,
    config: ResearchTeamDomainPlaybookAdherenceConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        score=playbook_step_score,
        watch_threshold=config.playbook_step_watch_threshold,
        pass_threshold=config.playbook_step_pass_threshold,
        block_reason="playbook_steps_incomplete",
        watch_reason="playbook_steps_watch",
    )
    _append_threshold_reason(
        reasons,
        score=source_coverage_score,
        watch_threshold=config.source_coverage_watch_threshold,
        pass_threshold=config.source_coverage_pass_threshold,
        block_reason="required_source_coverage_gap",
        watch_reason="required_source_coverage_watch",
    )
    _append_threshold_reason(
        reasons,
        score=calibration_note_score,
        watch_threshold=config.calibration_note_watch_threshold,
        pass_threshold=config.calibration_note_pass_threshold,
        block_reason="calibration_note_gap",
        watch_reason="calibration_note_watch",
    )
    _append_threshold_reason(
        reasons,
        score=stale_override_score,
        watch_threshold=config.documentation_watch_threshold,
        pass_threshold=config.documentation_pass_threshold,
        block_reason="stale_memory_override_missing_documentation",
        watch_reason="stale_memory_override_watch",
    )
    _append_threshold_reason(
        reasons,
        score=exception_documentation_score,
        watch_threshold=config.documentation_watch_threshold,
        pass_threshold=config.documentation_pass_threshold,
        block_reason="exception_documentation_gap",
        watch_reason="exception_documentation_watch",
    )
    if review_latency_seconds >= config.review_latency_block_seconds:
        reasons.append("review_latency_sla_breach")
    elif review_latency_seconds > config.review_latency_watch_seconds:
        reasons.append("review_latency_watch")
    if (
        any(
            reason
            in {
                "playbook_steps_incomplete",
                "required_source_coverage_gap",
                "calibration_note_gap",
                "stale_memory_override_missing_documentation",
                "exception_documentation_gap",
                "review_latency_sla_breach",
            }
            for reason in reasons
        )
        or adherence_score < config.adherence_watch_threshold
    ):
        reasons.append("domain_playbook_adherence_block")
    elif reasons or adherence_score < config.adherence_pass_threshold:
        reasons.append("domain_playbook_adherence_watch")
    else:
        reasons.append("domain_playbook_adherence_pass")
    return tuple(reason for reason in _ROW_REASON_PRIORITY if reason in reasons)


def _append_threshold_reason(
    reasons: list[str],
    *,
    score: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if score < watch_threshold:
        reasons.append(block_reason)
    elif score < pass_threshold:
        reasons.append(watch_reason)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "domain_playbook_adherence_block" in reason_codes:
        return "block"
    if "domain_playbook_adherence_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamDomainPlaybookAdherenceRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainPlaybookAdherenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_domain_playbook_adherence_inputs",)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "domain_playbook_adherence_pass"
    )
    if not present:
        return ("domain_playbook_adherence_pass",)
    return tuple(reason_code for reason_code in _ROW_REASON_PRIORITY if reason_code in present)


def _normalize_inputs(
    values: Iterable[ResearchTeamDomainPlaybookAdherenceInput],
) -> tuple[ResearchTeamDomainPlaybookAdherenceInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for value in normalized:
        _require_exact_type("adherence_input", value, ResearchTeamDomainPlaybookAdherenceInput)
        _require_hard_flags(value)
        _reject_unsafe_public_surface("adherence_input", value)
        key = (value.team_label, value.domain_label)
        if key in seen_keys:
            raise ValueError("inputs must use unique team and domain labels")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchTeamDomainPlaybookAdherenceRow],
) -> tuple[ResearchTeamDomainPlaybookAdherenceRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamDomainPlaybookAdherenceRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamDomainPlaybookAdherenceRow values",
        ) from exc
    for row in rows:
        _require_exact_type("row", row, ResearchTeamDomainPlaybookAdherenceRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set((row.team_label, row.domain_label) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_row_consistency(row: ResearchTeamDomainPlaybookAdherenceRow) -> None:
    if row.playbook_step_count <= _ZERO_COUNT:
        raise ValueError("playbook_step_count must be positive")
    if row.required_source_count <= _ZERO_COUNT:
        raise ValueError("required_source_count must be positive")
    _require_count_at_most(
        "followed_playbook_step_count",
        row.followed_playbook_step_count,
        "playbook_step_count",
        row.playbook_step_count,
    )
    _require_count_at_most(
        "cited_required_source_count",
        row.cited_required_source_count,
        "required_source_count",
        row.required_source_count,
    )
    _require_count_at_most(
        "calibration_note_count",
        row.calibration_note_count,
        "required_calibration_note_count",
        row.required_calibration_note_count,
    )
    _require_count_at_most(
        "documented_stale_memory_override_count",
        row.documented_stale_memory_override_count,
        "stale_memory_override_count",
        row.stale_memory_override_count,
    )
    _require_count_at_most(
        "documented_exception_count",
        row.documented_exception_count,
        "exception_count",
        row.exception_count,
    )
    if row.playbook_step_adherence_ratio != _bounded_ratio(
        row.followed_playbook_step_count,
        row.playbook_step_count,
    ):
        raise ValueError("playbook_step_adherence_ratio must match counts")
    if row.required_source_coverage_ratio != _bounded_ratio(
        row.cited_required_source_count,
        row.required_source_count,
    ):
        raise ValueError("required_source_coverage_ratio must match counts")
    if row.calibration_note_ratio != _bounded_ratio(
        row.calibration_note_count,
        row.required_calibration_note_count,
    ):
        raise ValueError("calibration_note_ratio must match counts")
    if row.stale_override_documentation_ratio != _bounded_ratio(
        row.documented_stale_memory_override_count,
        row.stale_memory_override_count,
    ):
        raise ValueError("stale_override_documentation_ratio must match counts")
    if row.exception_documentation_ratio != _bounded_ratio(
        row.documented_exception_count,
        row.exception_count,
    ):
        raise ValueError("exception_documentation_ratio must match counts")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchTeamDomainPlaybookAdherenceReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _decimal_count(len({row.team_label for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.domain_count != _decimal_count(len({row.domain_label for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.average_playbook_step_adherence_ratio != _average_score(
        tuple(row.playbook_step_adherence_ratio for row in report.rows),
    ):
        raise ValueError("average_playbook_step_adherence_ratio must match rows")
    if report.average_required_source_coverage_ratio != _average_score(
        tuple(row.required_source_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_required_source_coverage_ratio must match rows")
    if report.average_calibration_note_ratio != _average_score(
        tuple(row.calibration_note_ratio for row in report.rows),
    ):
        raise ValueError("average_calibration_note_ratio must match rows")
    if report.average_stale_override_documentation_ratio != _average_score(
        tuple(row.stale_override_documentation_ratio for row in report.rows),
    ):
        raise ValueError("average_stale_override_documentation_ratio must match rows")
    if report.average_exception_documentation_ratio != _average_score(
        tuple(row.exception_documentation_ratio for row in report.rows),
    ):
        raise ValueError("average_exception_documentation_ratio must match rows")
    if report.average_review_latency_seconds != _average_score(
        tuple(row.review_latency_seconds for row in report.rows),
    ):
        raise ValueError("average_review_latency_seconds must match rows")
    if report.average_playbook_adherence_score != _average_score(
        tuple(row.playbook_adherence_score for row in report.rows),
    ):
        raise ValueError("average_playbook_adherence_score must match rows")


def _row_sort_key(
    row: ResearchTeamDomainPlaybookAdherenceRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.row_status],
        row.playbook_adherence_score,
        row.required_source_coverage_ratio,
        -row.review_latency_seconds,
        row.team_label,
        row.domain_label,
    )


def _status_count(
    rows: tuple[ResearchTeamDomainPlaybookAdherenceRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ONE
    with localcontext(_DECIMAL_CONTEXT):
        ratio = _quantize(numerator / denominator)
    if ratio > _ONE:
        return _ONE
    return ratio


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in DOMAIN_PLAYBOOK_ADHERENCE_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
    return normalized


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_PLAYBOOK_ADHERENCE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal_with_quantum(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        if quantum == _COUNT_QUANTUM:
            raise ValueError(f"{field_name} must be a whole Decimal")
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_threshold_sequence(
    label: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold < watch_threshold:
        raise ValueError(f"{label} pass threshold must be at least watch threshold")


def _require_count_at_most(
    numerator_name: str,
    numerator: Decimal,
    denominator_name: str,
    denominator: Decimal,
) -> None:
    if numerator > denominator:
        raise ValueError(f"{numerator_name} must be at most {denominator_name}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
            raise ValueError(f"unsafe public-safe label in {label}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get(_DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be present")
    if current != _derived_digest(payload) or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    try:
        rebuilt = _report_from_payload_dict(payload)
    except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
        raise ValueError("payload schema mismatch") from exc
    if _payload_value(rebuilt) != payload:
        raise ValueError("payload schema mismatch")


def _report_from_payload_dict(
    payload: dict[str, Any],
) -> ResearchTeamDomainPlaybookAdherenceReport:
    _require_payload_keys(
        "report",
        payload,
        ResearchTeamDomainPlaybookAdherenceReport,
    )
    return ResearchTeamDomainPlaybookAdherenceReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        status=_string_from_payload("status", payload["status"]),
        input_count=_decimal_from_payload("input_count", payload["input_count"]),
        row_count=_decimal_from_payload("row_count", payload["row_count"]),
        team_count=_decimal_from_payload("team_count", payload["team_count"]),
        domain_count=_decimal_from_payload("domain_count", payload["domain_count"]),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        average_playbook_step_adherence_ratio=_decimal_from_payload(
            "average_playbook_step_adherence_ratio",
            payload["average_playbook_step_adherence_ratio"],
        ),
        average_required_source_coverage_ratio=_decimal_from_payload(
            "average_required_source_coverage_ratio",
            payload["average_required_source_coverage_ratio"],
        ),
        average_calibration_note_ratio=_decimal_from_payload(
            "average_calibration_note_ratio",
            payload["average_calibration_note_ratio"],
        ),
        average_stale_override_documentation_ratio=_decimal_from_payload(
            "average_stale_override_documentation_ratio",
            payload["average_stale_override_documentation_ratio"],
        ),
        average_exception_documentation_ratio=_decimal_from_payload(
            "average_exception_documentation_ratio",
            payload["average_exception_documentation_ratio"],
        ),
        average_review_latency_seconds=_decimal_from_payload(
            "average_review_latency_seconds",
            payload["average_review_latency_seconds"],
        ),
        average_playbook_adherence_score=_decimal_from_payload(
            "average_playbook_adherence_score",
            payload["average_playbook_adherence_score"],
        ),
        rows=_rows_from_payload(payload["rows"]),
        reason_codes=_string_tuple_from_payload("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_string_from_payload(
            _DIGEST_FIELD,
            payload[_DIGEST_FIELD],
        ),
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


def _row_from_payload_dict(
    payload: object,
) -> ResearchTeamDomainPlaybookAdherenceRow:
    if type(payload) is not dict:
        raise ValueError("payload schema mismatch")
    _require_payload_keys("row", payload, ResearchTeamDomainPlaybookAdherenceRow)
    return ResearchTeamDomainPlaybookAdherenceRow(
        team_label=_string_from_payload("team_label", payload["team_label"]),
        domain_label=_string_from_payload("domain_label", payload["domain_label"]),
        playbook_step_count=_decimal_from_payload(
            "playbook_step_count",
            payload["playbook_step_count"],
        ),
        followed_playbook_step_count=_decimal_from_payload(
            "followed_playbook_step_count",
            payload["followed_playbook_step_count"],
        ),
        playbook_step_adherence_ratio=_decimal_from_payload(
            "playbook_step_adherence_ratio",
            payload["playbook_step_adherence_ratio"],
        ),
        required_source_count=_decimal_from_payload(
            "required_source_count",
            payload["required_source_count"],
        ),
        cited_required_source_count=_decimal_from_payload(
            "cited_required_source_count",
            payload["cited_required_source_count"],
        ),
        required_source_coverage_ratio=_decimal_from_payload(
            "required_source_coverage_ratio",
            payload["required_source_coverage_ratio"],
        ),
        required_calibration_note_count=_decimal_from_payload(
            "required_calibration_note_count",
            payload["required_calibration_note_count"],
        ),
        calibration_note_count=_decimal_from_payload(
            "calibration_note_count",
            payload["calibration_note_count"],
        ),
        calibration_note_ratio=_decimal_from_payload(
            "calibration_note_ratio",
            payload["calibration_note_ratio"],
        ),
        stale_memory_override_count=_decimal_from_payload(
            "stale_memory_override_count",
            payload["stale_memory_override_count"],
        ),
        documented_stale_memory_override_count=_decimal_from_payload(
            "documented_stale_memory_override_count",
            payload["documented_stale_memory_override_count"],
        ),
        stale_override_documentation_ratio=_decimal_from_payload(
            "stale_override_documentation_ratio",
            payload["stale_override_documentation_ratio"],
        ),
        exception_count=_decimal_from_payload(
            "exception_count",
            payload["exception_count"],
        ),
        documented_exception_count=_decimal_from_payload(
            "documented_exception_count",
            payload["documented_exception_count"],
        ),
        exception_documentation_ratio=_decimal_from_payload(
            "exception_documentation_ratio",
            payload["exception_documentation_ratio"],
        ),
        review_latency_seconds=_decimal_from_payload(
            "review_latency_seconds",
            payload["review_latency_seconds"],
        ),
        review_latency_score=_decimal_from_payload(
            "review_latency_score",
            payload["review_latency_score"],
        ),
        playbook_adherence_score=_decimal_from_payload(
            "playbook_adherence_score",
            payload["playbook_adherence_score"],
        ),
        row_status=_string_from_payload("row_status", payload["row_status"]),
        reason_codes=_string_tuple_from_payload("reason_codes", payload["reason_codes"]),
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


def _rows_from_payload(value: object) -> tuple[ResearchTeamDomainPlaybookAdherenceRow, ...]:
    if type(value) is not list:
        raise ValueError("payload schema mismatch")
    return tuple(_row_from_payload_dict(item) for item in value)


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected = {field.name for field in fields(expected_type)}
    if set(payload) != expected:
        raise ValueError(f"{label} payload schema mismatch")


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} payload schema mismatch")
    return tuple(_string_from_payload(field_name, item) for item in value)


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} payload schema mismatch")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} payload schema mismatch")
    return Decimal(value)


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} payload schema mismatch")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} payload schema mismatch") from exc
    return _as_utc(field_name, parsed)


def _true_from_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} payload schema mismatch")
    return True


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("unsupported payload value")
