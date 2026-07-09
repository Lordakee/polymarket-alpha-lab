"""Report-only source evidence authority memory decay reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-source-evidence-authority-memory-decay-report-v0"
)
RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_evidence_authority_memory_decay_empty"
CLEAR_REASON = "source_evidence_authority_memory_decay_clear"
AUTHORITY_RELIABILITY_WATCH_REASON = "authority_reliability_watch"
AUTHORITY_RELIABILITY_BLOCK_REASON = "authority_reliability_block"
EVIDENCE_AGE_WATCH_REASON = "evidence_age_watch"
EVIDENCE_AGE_BLOCK_REASON = "evidence_age_block"
MEMORY_AGE_WATCH_REASON = "memory_age_watch"
MEMORY_AGE_BLOCK_REASON = "memory_age_block"
CROSS_EVIDENCE_WATCH_REASON = "cross_evidence_watch"
CROSS_EVIDENCE_BLOCK_REASON = "cross_evidence_block"
INDEPENDENT_AUTHORITY_WATCH_REASON = "independent_authority_watch"
INDEPENDENT_AUTHORITY_BLOCK_REASON = "independent_authority_block"
CONFLICT_PRESSURE_WATCH_REASON = "conflict_pressure_watch"
CONFLICT_PRESSURE_BLOCK_REASON = "conflict_pressure_block"
MEMORY_ALIGNMENT_WATCH_REASON = "memory_alignment_watch"
MEMORY_ALIGNMENT_BLOCK_REASON = "memory_alignment_block"

ROW_REASON_CODES = (
    AUTHORITY_RELIABILITY_BLOCK_REASON,
    EVIDENCE_AGE_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    CROSS_EVIDENCE_BLOCK_REASON,
    INDEPENDENT_AUTHORITY_BLOCK_REASON,
    CONFLICT_PRESSURE_BLOCK_REASON,
    MEMORY_ALIGNMENT_BLOCK_REASON,
    AUTHORITY_RELIABILITY_WATCH_REASON,
    EVIDENCE_AGE_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    CROSS_EVIDENCE_WATCH_REASON,
    INDEPENDENT_AUTHORITY_WATCH_REASON,
    CONFLICT_PRESSURE_WATCH_REASON,
    MEMORY_ALIGNMENT_WATCH_REASON,
    CLEAR_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SEVEN = Decimal("7.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DEFAULT_EVIDENCE_SCORE_BLOCK_SECONDS = Decimal("10800.000000")
DEFAULT_MEMORY_SCORE_BLOCK_SECONDS = Decimal("21600.000000")
DEFAULT_COVERAGE_SCORE_WATCH_COUNT = Decimal("2.000000")
SHA256_HEX_LENGTH = 64


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    _join_parts("que", "stion"),
    _join_parts("ur", "l"),
    _join_parts("te", "xt"),
    "dsn",
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    "://",
    "http",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "endation"),
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_STATUSES",
    "ResearchSourceEvidenceAuthorityMemoryDecayConfig",
    "ResearchSourceEvidenceAuthorityMemoryDecayInput",
    "ResearchSourceEvidenceAuthorityMemoryDecayReport",
    "ResearchSourceEvidenceAuthorityMemoryDecayRow",
    "build_research_source_evidence_authority_memory_decay_report",
    "research_source_evidence_authority_memory_decay_report_digest",
    "research_source_evidence_authority_memory_decay_report_payload",
    "validate_research_source_evidence_authority_memory_decay_public_payload",
    "validate_research_source_evidence_authority_memory_decay_report_digest",
)


@dataclass(frozen=True)
class ResearchSourceEvidenceAuthorityMemoryDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    authority_reliability_watch_below: Decimal = Decimal("0.700000")
    authority_reliability_block_below: Decimal = Decimal("0.400000")
    evidence_age_watch_seconds: Decimal = Decimal("3600.000000")
    evidence_age_block_seconds: Decimal = Decimal("10800.000000")
    memory_age_watch_seconds: Decimal = Decimal("7200.000000")
    memory_age_block_seconds: Decimal = Decimal("21600.000000")
    cross_evidence_watch_count: Decimal = Decimal("2.000000")
    independent_authority_watch_count: Decimal = Decimal("2.000000")
    conflict_watch_threshold: Decimal = Decimal("0.300000")
    conflict_block_threshold: Decimal = Decimal("0.600000")
    memory_alignment_watch_below: Decimal = Decimal("0.700000")
    memory_alignment_block_below: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceAuthorityMemoryDecayConfig:
            raise TypeError(
                "ResearchSourceEvidenceAuthorityMemoryDecayConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceAuthorityMemoryDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceEvidenceAuthorityMemoryDecayConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_reliability_watch_below",
            "authority_reliability_block_below",
            "conflict_watch_threshold",
            "conflict_block_threshold",
            "memory_alignment_watch_below",
            "memory_alignment_block_below",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_age_watch_seconds",
            "evidence_age_block_seconds",
            "memory_age_watch_seconds",
            "memory_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cross_evidence_watch_count",
            "independent_authority_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceAuthorityMemoryDecayInput:
    evidence_digest: str
    authority_digest: str
    observed_at: datetime
    authority_reliability_score: Decimal
    evidence_age_seconds: Decimal
    memory_age_seconds: Decimal
    cross_evidence_count: Decimal
    independent_authority_count: Decimal
    conflict_score: Decimal
    memory_alignment_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceAuthorityMemoryDecayInput:
            raise TypeError(
                "ResearchSourceEvidenceAuthorityMemoryDecayInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceAuthorityMemoryDecayInput:
            raise ValueError(
                "input must be exactly ResearchSourceEvidenceAuthorityMemoryDecayInput",
            )
        _require_sha256("evidence_digest", self.evidence_digest)
        _require_sha256("authority_digest", self.authority_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_reliability_score",
            "conflict_score",
            "memory_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_seconds", "memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("cross_evidence_count", "independent_authority_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceAuthorityMemoryDecayRow:
    evidence_digest: str
    authority_digest: str
    observed_at: datetime
    observation_age_seconds: Decimal
    authority_reliability_score: Decimal
    authority_reliability_band: str
    evidence_age_seconds: Decimal
    evidence_freshness_band: str
    memory_age_seconds: Decimal
    memory_decay_band: str
    cross_evidence_count: Decimal
    cross_evidence_band: str
    independent_authority_count: Decimal
    independent_authority_band: str
    conflict_score: Decimal
    conflict_band: str
    memory_alignment_score: Decimal
    memory_alignment_band: str
    authority_memory_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceAuthorityMemoryDecayRow:
            raise TypeError(
                "ResearchSourceEvidenceAuthorityMemoryDecayRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceAuthorityMemoryDecayRow:
            raise ValueError(
                "row must be exactly ResearchSourceEvidenceAuthorityMemoryDecayRow",
            )
        _require_sha256("evidence_digest", self.evidence_digest)
        _require_sha256("authority_digest", self.authority_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_reliability_score",
            "conflict_score",
            "memory_alignment_score",
            "authority_memory_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_age_seconds",
            "evidence_age_seconds",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("cross_evidence_count", "independent_authority_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_one_of(
            "authority_reliability_band",
            self.authority_reliability_band,
            ("trusted", "thin", "weak"),
        )
        _require_one_of(
            "evidence_freshness_band",
            self.evidence_freshness_band,
            ("fresh", "stale", "expired"),
        )
        _require_one_of(
            "memory_decay_band",
            self.memory_decay_band,
            ("fresh", "stale", "expired"),
        )
        _require_one_of(
            "cross_evidence_band",
            self.cross_evidence_band,
            ("covered", "thin", "missing"),
        )
        _require_one_of(
            "independent_authority_band",
            self.independent_authority_band,
            ("covered", "thin", "missing"),
        )
        _require_one_of("conflict_band", self.conflict_band, ("clear", "elevated", "conflicted"))
        _require_one_of(
            "memory_alignment_band",
            self.memory_alignment_band,
            ("aligned", "loose", "broken"),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceAuthorityMemoryDecayReport:
    generated_at: datetime
    config_version: str
    evidence_count: Decimal
    pass_evidence_count: Decimal
    watch_evidence_count: Decimal
    block_evidence_count: Decimal
    weak_authority_count: Decimal
    stale_evidence_count: Decimal
    decayed_memory_count: Decimal
    thin_cross_evidence_count: Decimal
    thin_independent_authority_count: Decimal
    conflict_pressure_count: Decimal
    memory_alignment_gap_count: Decimal
    highest_authority_memory_decay_score: Decimal
    oldest_evidence_age_seconds: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceAuthorityMemoryDecayReport:
            raise TypeError(
                "ResearchSourceEvidenceAuthorityMemoryDecayReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceAuthorityMemoryDecayReport:
            raise ValueError(
                "report must be exactly ResearchSourceEvidenceAuthorityMemoryDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_count",
            "pass_evidence_count",
            "watch_evidence_count",
            "block_evidence_count",
            "weak_authority_count",
            "stale_evidence_count",
            "decayed_memory_count",
            "thin_cross_evidence_count",
            "thin_independent_authority_count",
            "conflict_pressure_count",
            "memory_alignment_gap_count",
            "oldest_evidence_age_seconds",
            "oldest_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_authority_memory_decay_score",
            _require_ratio(
                "highest_authority_memory_decay_score",
                self.highest_authority_memory_decay_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_public_payload(self),
            )
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_public_payload(self):
                raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_evidence_authority_memory_decay_report_payload(self)


def build_research_source_evidence_authority_memory_decay_report(
    inputs: list[ResearchSourceEvidenceAuthorityMemoryDecayInput]
    | tuple[ResearchSourceEvidenceAuthorityMemoryDecayInput, ...],
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceEvidenceAuthorityMemoryDecayReport:
    if config is None:
        config = ResearchSourceEvidenceAuthorityMemoryDecayConfig()
    if type(config) is not ResearchSourceEvidenceAuthorityMemoryDecayConfig:
        raise ValueError(
            "config must be a ResearchSourceEvidenceAuthorityMemoryDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _decay_rows(
        _normalize_inputs(inputs),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchSourceEvidenceAuthorityMemoryDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        evidence_count=_count(len(rows)),
        pass_evidence_count=_status_count(rows, "pass"),
        watch_evidence_count=_status_count(rows, "watch"),
        block_evidence_count=_status_count(rows, "block"),
        weak_authority_count=_reason_count(
            rows,
            (AUTHORITY_RELIABILITY_WATCH_REASON, AUTHORITY_RELIABILITY_BLOCK_REASON),
        ),
        stale_evidence_count=_reason_count(
            rows,
            (EVIDENCE_AGE_WATCH_REASON, EVIDENCE_AGE_BLOCK_REASON),
        ),
        decayed_memory_count=_reason_count(
            rows,
            (MEMORY_AGE_WATCH_REASON, MEMORY_AGE_BLOCK_REASON),
        ),
        thin_cross_evidence_count=_reason_count(
            rows,
            (CROSS_EVIDENCE_WATCH_REASON, CROSS_EVIDENCE_BLOCK_REASON),
        ),
        thin_independent_authority_count=_reason_count(
            rows,
            (INDEPENDENT_AUTHORITY_WATCH_REASON, INDEPENDENT_AUTHORITY_BLOCK_REASON),
        ),
        conflict_pressure_count=_reason_count(
            rows,
            (CONFLICT_PRESSURE_WATCH_REASON, CONFLICT_PRESSURE_BLOCK_REASON),
        ),
        memory_alignment_gap_count=_reason_count(
            rows,
            (MEMORY_ALIGNMENT_WATCH_REASON, MEMORY_ALIGNMENT_BLOCK_REASON),
        ),
        highest_authority_memory_decay_score=max(
            (row.authority_memory_decay_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_memory_age_seconds=max(
            (row.memory_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_evidence_authority_memory_decay_report_payload(
    report: ResearchSourceEvidenceAuthorityMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceEvidenceAuthorityMemoryDecayReport:
        validate_research_source_evidence_authority_memory_decay_report_digest(report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_source_evidence_authority_memory_decay_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_research_source_evidence_authority_memory_decay_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_source_evidence_authority_memory_decay_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchSourceEvidenceAuthorityMemoryDecayReport")


def research_source_evidence_authority_memory_decay_report_digest(
    report: ResearchSourceEvidenceAuthorityMemoryDecayReport,
) -> str:
    if type(report) is not ResearchSourceEvidenceAuthorityMemoryDecayReport:
        raise ValueError("report must be a ResearchSourceEvidenceAuthorityMemoryDecayReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_evidence_authority_memory_decay_report_digest(
    report: ResearchSourceEvidenceAuthorityMemoryDecayReport,
) -> None:
    if type(report) is not ResearchSourceEvidenceAuthorityMemoryDecayReport:
        raise ValueError("report must be a ResearchSourceEvidenceAuthorityMemoryDecayReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def validate_research_source_evidence_authority_memory_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics("public payload", payload)
    _reject_flag_downgrades("public payload", payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _validate_public_digest_values(payload)
    _validate_status_values_in_payload(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _payload_validation_digest(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")


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
    value: object,
) -> tuple[ResearchSourceEvidenceAuthorityMemoryDecayInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceEvidenceAuthorityMemoryDecayInput:
            raise ValueError(
                "inputs must contain ResearchSourceEvidenceAuthorityMemoryDecayInput",
            )
        _require_hard_flags("input", row)
        if row.evidence_digest in seen:
            raise ValueError("inputs must be unique by evidence_digest")
        seen.add(row.evidence_digest)
    return tuple(sorted(rows, key=lambda row: row.evidence_digest))


def _decay_rows(
    inputs: tuple[ResearchSourceEvidenceAuthorityMemoryDecayInput, ...],
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...]:
    return tuple(
        sorted(
            (_decay_row(row, config=config, generated_at=generated_at) for row in inputs),
            key=_row_sort_key,
        ),
    )


def _decay_row(
    row: ResearchSourceEvidenceAuthorityMemoryDecayInput,
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchSourceEvidenceAuthorityMemoryDecayRow:
    observation_age_seconds = _duration_seconds(row.observed_at, generated_at)
    if observation_age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    reason_codes = _row_reason_codes(row, config=config)
    return ResearchSourceEvidenceAuthorityMemoryDecayRow(
        evidence_digest=row.evidence_digest,
        authority_digest=row.authority_digest,
        observed_at=row.observed_at,
        observation_age_seconds=observation_age_seconds,
        authority_reliability_score=row.authority_reliability_score,
        authority_reliability_band=_authority_reliability_band(row, config=config),
        evidence_age_seconds=row.evidence_age_seconds,
        evidence_freshness_band=_age_band(
            row.evidence_age_seconds,
            watch_seconds=config.evidence_age_watch_seconds,
            block_seconds=config.evidence_age_block_seconds,
        ),
        memory_age_seconds=row.memory_age_seconds,
        memory_decay_band=_age_band(
            row.memory_age_seconds,
            watch_seconds=config.memory_age_watch_seconds,
            block_seconds=config.memory_age_block_seconds,
        ),
        cross_evidence_count=row.cross_evidence_count,
        cross_evidence_band=_coverage_band(
            row.cross_evidence_count,
            watch_count=config.cross_evidence_watch_count,
        ),
        independent_authority_count=row.independent_authority_count,
        independent_authority_band=_coverage_band(
            row.independent_authority_count,
            watch_count=config.independent_authority_watch_count,
        ),
        conflict_score=row.conflict_score,
        conflict_band=_conflict_band(row, config=config),
        memory_alignment_score=row.memory_alignment_score,
        memory_alignment_band=_memory_alignment_band(row, config=config),
        authority_memory_decay_score=_authority_memory_decay_score(row),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceEvidenceAuthorityMemoryDecayInput,
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.authority_reliability_score < config.authority_reliability_block_below:
        reasons.append(AUTHORITY_RELIABILITY_BLOCK_REASON)
    elif row.authority_reliability_score < config.authority_reliability_watch_below:
        reasons.append(AUTHORITY_RELIABILITY_WATCH_REASON)
    if row.evidence_age_seconds >= config.evidence_age_block_seconds:
        reasons.append(EVIDENCE_AGE_BLOCK_REASON)
    elif row.evidence_age_seconds > config.evidence_age_watch_seconds:
        reasons.append(EVIDENCE_AGE_WATCH_REASON)
    if row.memory_age_seconds >= config.memory_age_block_seconds:
        reasons.append(MEMORY_AGE_BLOCK_REASON)
    elif row.memory_age_seconds > config.memory_age_watch_seconds:
        reasons.append(MEMORY_AGE_WATCH_REASON)
    if row.cross_evidence_count < ONE:
        reasons.append(CROSS_EVIDENCE_BLOCK_REASON)
    elif row.cross_evidence_count < config.cross_evidence_watch_count:
        reasons.append(CROSS_EVIDENCE_WATCH_REASON)
    if row.independent_authority_count < ONE:
        reasons.append(INDEPENDENT_AUTHORITY_BLOCK_REASON)
    elif row.independent_authority_count < config.independent_authority_watch_count:
        reasons.append(INDEPENDENT_AUTHORITY_WATCH_REASON)
    if row.conflict_score >= config.conflict_block_threshold:
        reasons.append(CONFLICT_PRESSURE_BLOCK_REASON)
    elif row.conflict_score >= config.conflict_watch_threshold:
        reasons.append(CONFLICT_PRESSURE_WATCH_REASON)
    if row.memory_alignment_score < config.memory_alignment_block_below:
        reasons.append(MEMORY_ALIGNMENT_BLOCK_REASON)
    elif row.memory_alignment_score < config.memory_alignment_watch_below:
        reasons.append(MEMORY_ALIGNMENT_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _authority_memory_decay_score(
    row: ResearchSourceEvidenceAuthorityMemoryDecayInput
    | ResearchSourceEvidenceAuthorityMemoryDecayRow,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            (ONE - row.authority_reliability_score)
            + _age_decay(row.evidence_age_seconds, DEFAULT_EVIDENCE_SCORE_BLOCK_SECONDS)
            + _age_decay(row.memory_age_seconds, DEFAULT_MEMORY_SCORE_BLOCK_SECONDS)
            + _coverage_decay(row.cross_evidence_count)
            + _coverage_decay(row.independent_authority_count)
            + row.conflict_score
            + (ONE - row.memory_alignment_score)
        ) / SEVEN
        return min(max(score, ZERO), ONE).quantize(QUANT)


def _age_decay(value: Decimal, block_seconds: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / block_seconds, ONE).quantize(QUANT)


def _coverage_decay(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value >= DEFAULT_COVERAGE_SCORE_WATCH_COUNT:
            return ZERO
        return ((DEFAULT_COVERAGE_SCORE_WATCH_COUNT - value) / TWO).quantize(QUANT)


def _authority_reliability_band(
    row: ResearchSourceEvidenceAuthorityMemoryDecayInput,
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig,
) -> str:
    if row.authority_reliability_score < config.authority_reliability_block_below:
        return "weak"
    if row.authority_reliability_score < config.authority_reliability_watch_below:
        return "thin"
    return "trusted"


def _age_band(value: Decimal, *, watch_seconds: Decimal, block_seconds: Decimal) -> str:
    if value >= block_seconds:
        return "expired"
    if value > watch_seconds:
        return "stale"
    return "fresh"


def _coverage_band(value: Decimal, *, watch_count: Decimal) -> str:
    if value < ONE:
        return "missing"
    if value < watch_count:
        return "thin"
    return "covered"


def _conflict_band(
    row: ResearchSourceEvidenceAuthorityMemoryDecayInput,
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig,
) -> str:
    if row.conflict_score >= config.conflict_block_threshold:
        return "conflicted"
    if row.conflict_score >= config.conflict_watch_threshold:
        return "elevated"
    return "clear"


def _memory_alignment_band(
    row: ResearchSourceEvidenceAuthorityMemoryDecayInput,
    *,
    config: ResearchSourceEvidenceAuthorityMemoryDecayConfig,
) -> str:
    if row.memory_alignment_score < config.memory_alignment_block_below:
        return "broken"
    if row.memory_alignment_score < config.memory_alignment_watch_below:
        return "loose"
    return "aligned"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes if reason != CLEAR_REASON}
    if not seen:
        return (CLEAR_REASON,)
    return tuple(reason for reason in ROW_REASON_CODES if reason in seen and reason != CLEAR_REASON)


def _row_sort_key(row: ResearchSourceEvidenceAuthorityMemoryDecayRow) -> tuple[int, str]:
    return ({"block": 0, "watch": 1, "pass": 2}[row.status], row.evidence_digest)


def _status_count(
    rows: tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _validate_config(config: ResearchSourceEvidenceAuthorityMemoryDecayConfig) -> None:
    if (
        config.authority_reliability_block_below
        >= config.authority_reliability_watch_below
    ):
        raise ValueError(
            "authority_reliability_block_below must be below "
            "authority_reliability_watch_below",
        )
    if config.evidence_age_block_seconds <= config.evidence_age_watch_seconds:
        raise ValueError("evidence_age_block_seconds must exceed evidence_age_watch_seconds")
    if config.memory_age_block_seconds <= config.memory_age_watch_seconds:
        raise ValueError("memory_age_block_seconds must exceed memory_age_watch_seconds")
    if config.conflict_block_threshold <= config.conflict_watch_threshold:
        raise ValueError("conflict_block_threshold must exceed conflict_watch_threshold")
    if config.memory_alignment_block_below >= config.memory_alignment_watch_below:
        raise ValueError(
            "memory_alignment_block_below must be below memory_alignment_watch_below",
        )


def _validate_row(row: ResearchSourceEvidenceAuthorityMemoryDecayRow) -> None:
    if row.authority_memory_decay_score != _authority_memory_decay_score(row):
        raise ValueError("authority_memory_decay_score must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceEvidenceAuthorityMemoryDecayReport) -> None:
    rows = report.rows
    if report.evidence_count != _count(len(rows)):
        raise ValueError("evidence_count must match rows")
    if report.pass_evidence_count != _status_count(rows, "pass"):
        raise ValueError("pass_evidence_count must match rows")
    if report.watch_evidence_count != _status_count(rows, "watch"):
        raise ValueError("watch_evidence_count must match rows")
    if report.block_evidence_count != _status_count(rows, "block"):
        raise ValueError("block_evidence_count must match rows")
    if report.weak_authority_count != _reason_count(
        rows,
        (AUTHORITY_RELIABILITY_WATCH_REASON, AUTHORITY_RELIABILITY_BLOCK_REASON),
    ):
        raise ValueError("weak_authority_count must match rows")
    if report.stale_evidence_count != _reason_count(
        rows,
        (EVIDENCE_AGE_WATCH_REASON, EVIDENCE_AGE_BLOCK_REASON),
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.decayed_memory_count != _reason_count(
        rows,
        (MEMORY_AGE_WATCH_REASON, MEMORY_AGE_BLOCK_REASON),
    ):
        raise ValueError("decayed_memory_count must match rows")
    if report.thin_cross_evidence_count != _reason_count(
        rows,
        (CROSS_EVIDENCE_WATCH_REASON, CROSS_EVIDENCE_BLOCK_REASON),
    ):
        raise ValueError("thin_cross_evidence_count must match rows")
    if report.thin_independent_authority_count != _reason_count(
        rows,
        (INDEPENDENT_AUTHORITY_WATCH_REASON, INDEPENDENT_AUTHORITY_BLOCK_REASON),
    ):
        raise ValueError("thin_independent_authority_count must match rows")
    if report.conflict_pressure_count != _reason_count(
        rows,
        (CONFLICT_PRESSURE_WATCH_REASON, CONFLICT_PRESSURE_BLOCK_REASON),
    ):
        raise ValueError("conflict_pressure_count must match rows")
    if report.memory_alignment_gap_count != _reason_count(
        rows,
        (MEMORY_ALIGNMENT_WATCH_REASON, MEMORY_ALIGNMENT_BLOCK_REASON),
    ):
        raise ValueError("memory_alignment_gap_count must match rows")
    if report.highest_authority_memory_decay_score != max(
        (row.authority_memory_decay_score for row in rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_authority_memory_decay_score must match rows")
    if report.oldest_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_evidence_age_seconds must match rows")
    if report.oldest_memory_age_seconds != max(
        (row.memory_age_seconds for row in rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceEvidenceAuthorityMemoryDecayRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceEvidenceAuthorityMemoryDecayRow:
            raise ValueError("rows must contain ResearchSourceEvidenceAuthorityMemoryDecayRow")
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in normalized:
        _require_one_of(field_name, value, allowed)
    return tuple(reason for reason in allowed if reason in normalized)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days).quantize(QUANT) * SECONDS_PER_DAY
            + Decimal(delta.seconds).quantize(QUANT)
            + (
                Decimal(delta.microseconds).quantize(QUANT)
                / MICROSECONDS_PER_SECOND
            )
        ).quantize(QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public field")
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha-256 hex digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha-256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a sha-256 hex digest")
    return value


def _require_one_of(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_one_of(
        field_name,
        value,
        RESEARCH_SOURCE_EVIDENCE_AUTHORITY_MEMORY_DECAY_STATUSES,
    )


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    ready = _json_probe(value)
    _reject_unsafe_public_value(label, ready)


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public field")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_value(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_value(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public field")


def _reject_public_numerics(label: str, value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(label, item)
        return
    if type(value) in (Decimal, int, float):
        raise ValueError(f"{label} must not contain numeric values")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        requires_flags = "status" in value or any(
            flag_name in value for flag_name in ("paper_only", "report_only", "readonly")
        )
        if requires_flags:
            _require_hard_flags(label, _PayloadFlags(value))
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _validate_public_digest_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_digest"):
                _require_sha256(key, item)
            _validate_public_digest_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_public_digest_values(item)


def _validate_status_values_in_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_status_values_in_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_status_values_in_payload(item)


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return value.quantize(QUANT).to_eng_string()
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _json_probe(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_probe(asdict(value))
    if isinstance(value, dict):
        return {key: _json_probe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_probe(item) for item in value]
    return value


def _report_digest_from_public_payload(
    report: ResearchSourceEvidenceAuthorityMemoryDecayReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode()).hexdigest()
