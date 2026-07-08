"""Deterministic report-only event information asymmetry scorecard."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION = (
    "research-event-information-asymmetry-scorecard-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_SOURCE_DIVERSITY_BLOCK = "source_diversity_block"
REASON_FRESHNESS_BLOCK = "freshness_block"
REASON_CONTRADICTION_BLOCK = "contradiction_block"
REASON_RESOLUTION_CLARITY_BLOCK = "resolution_clarity_block"
REASON_TEAM_EXPERTISE_BLOCK = "team_expertise_block"
REASON_ASYMMETRY_SCORE_BLOCK = "asymmetry_score_block"
REASON_SOURCE_DIVERSITY_WATCH = "source_diversity_watch"
REASON_FRESHNESS_WATCH = "freshness_watch"
REASON_CONTRADICTION_WATCH = "contradiction_watch"
REASON_RESOLUTION_CLARITY_WATCH = "resolution_clarity_watch"
REASON_TEAM_EXPERTISE_WATCH = "team_expertise_watch"
REASON_ASYMMETRY_SCORE_WATCH = "asymmetry_score_watch"
REASON_INFORMATION_QUALITY_PASS = "information_quality_pass"

_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_SOURCE_DIVERSITY_BLOCK,
    REASON_FRESHNESS_BLOCK,
    REASON_CONTRADICTION_BLOCK,
    REASON_RESOLUTION_CLARITY_BLOCK,
    REASON_TEAM_EXPERTISE_BLOCK,
    REASON_ASYMMETRY_SCORE_BLOCK,
    REASON_SOURCE_DIVERSITY_WATCH,
    REASON_FRESHNESS_WATCH,
    REASON_CONTRADICTION_WATCH,
    REASON_RESOLUTION_CLARITY_WATCH,
    REASON_TEAM_EXPERTISE_WATCH,
    REASON_ASYMMETRY_SCORE_WATCH,
    REASON_INFORMATION_QUALITY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code
    for reason_code in _REASON_CODE_SEQUENCE
    if reason_code != REASON_EMPTY_INPUT
)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_SOURCE_DIVERSITY_BLOCK,
        REASON_FRESHNESS_BLOCK,
        REASON_CONTRADICTION_BLOCK,
        REASON_RESOLUTION_CLARITY_BLOCK,
        REASON_TEAM_EXPERTISE_BLOCK,
        REASON_ASYMMETRY_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DOMAIN_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "private key",
    "http://",
    "https://",
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryScorecardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION
    )
    min_source_diversity_score: Decimal = Decimal("0.600000")
    pass_source_diversity_score: Decimal = Decimal("0.800000")
    watch_freshness_age_hours: Decimal = Decimal("24.000000")
    block_freshness_age_hours: Decimal = Decimal("72.000000")
    watch_contradiction_score: Decimal = Decimal("0.300000")
    block_contradiction_score: Decimal = Decimal("0.650000")
    min_resolution_clarity_score: Decimal = Decimal("0.550000")
    pass_resolution_clarity_score: Decimal = Decimal("0.800000")
    min_team_expertise_score: Decimal = Decimal("0.500000")
    pass_team_expertise_score: Decimal = Decimal("0.750000")
    watch_asymmetry_score: Decimal = Decimal("0.500000")
    block_asymmetry_score: Decimal = Decimal("0.750000")
    source_diversity_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.200000")
    resolution_clarity_weight: Decimal = Decimal("0.200000")
    team_expertise_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventInformationAsymmetryScorecardConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_source_diversity_score",
            "pass_source_diversity_score",
            "watch_contradiction_score",
            "block_contradiction_score",
            "min_resolution_clarity_score",
            "pass_resolution_clarity_score",
            "min_team_expertise_score",
            "pass_team_expertise_score",
            "watch_asymmetry_score",
            "block_asymmetry_score",
            "source_diversity_weight",
            "freshness_weight",
            "contradiction_weight",
            "resolution_clarity_weight",
            "team_expertise_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_freshness_age_hours", "block_freshness_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_source_diversity_score > self.pass_source_diversity_score:
            raise ValueError(
                "min_source_diversity_score must not exceed pass_source_diversity_score",
            )
        if self.watch_freshness_age_hours > self.block_freshness_age_hours:
            raise ValueError(
                "watch_freshness_age_hours must not exceed block_freshness_age_hours",
            )
        if self.watch_contradiction_score > self.block_contradiction_score:
            raise ValueError(
                "watch_contradiction_score must not exceed block_contradiction_score",
            )
        if self.min_resolution_clarity_score > self.pass_resolution_clarity_score:
            raise ValueError(
                "min_resolution_clarity_score must not exceed "
                "pass_resolution_clarity_score",
            )
        if self.min_team_expertise_score > self.pass_team_expertise_score:
            raise ValueError(
                "min_team_expertise_score must not exceed pass_team_expertise_score",
            )
        if self.watch_asymmetry_score > self.block_asymmetry_score:
            raise ValueError(
                "watch_asymmetry_score must not exceed block_asymmetry_score",
            )
        weight_sum = _quantize(
            self.source_diversity_weight
            + self.freshness_weight
            + self.contradiction_weight
            + self.resolution_clarity_weight
            + self.team_expertise_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("asymmetry score weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryInput(_FinalPublicDataclass):
    domain_key: str
    source_diversity_score: Decimal
    freshness_age_hours: Decimal
    contradiction_score: Decimal
    resolution_clarity_score: Decimal
    team_expertise_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventInformationAsymmetryInput, "input")
        object.__setattr__(
            self,
            "domain_key",
            _require_private_key("domain_key", self.domain_key),
        )
        for field_name in (
            "source_diversity_score",
            "contradiction_score",
            "resolution_clarity_score",
            "team_expertise_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_hours",
            _require_nonnegative_decimal("freshness_age_hours", self.freshness_age_hours),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryPublicNote(_FinalPublicDataclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventInformationAsymmetryPublicNote,
            "public note",
        )
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public note", self)
        _reject_unsafe_public_payload("public note", self)


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryRow(_FinalPublicDataclass):
    domain_digest: str
    source_diversity_score: Decimal
    source_diversity_gap_score: Decimal
    freshness_age_hours: Decimal
    freshness_gap_score: Decimal
    contradiction_score: Decimal
    resolution_clarity_score: Decimal
    resolution_clarity_gap_score: Decimal
    team_expertise_score: Decimal
    team_expertise_gap_score: Decimal
    asymmetry_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchEventInformationAsymmetryScorecardConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchEventInformationAsymmetryScorecardConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchEventInformationAsymmetryRow, "row")
        object.__setattr__(
            self,
            "domain_digest",
            _require_domain_digest("domain_digest", self.domain_digest),
        )
        for field_name in (
            "source_diversity_score",
            "source_diversity_gap_score",
            "freshness_gap_score",
            "contradiction_score",
            "resolution_clarity_score",
            "resolution_clarity_gap_score",
            "team_expertise_score",
            "team_expertise_gap_score",
            "asymmetry_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_hours",
            _require_nonnegative_decimal("freshness_age_hours", self.freshness_age_hours),
        )
        _require_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventInformationAsymmetryReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_asymmetry_score: Decimal
    max_asymmetry_score: Decimal
    min_source_diversity_score: Decimal
    max_freshness_age_hours: Decimal
    max_contradiction_score: Decimal
    min_resolution_clarity_score: Decimal
    min_team_expertise_score: Decimal
    rows: tuple[ResearchEventInformationAsymmetryRow, ...]
    reason_code_counts: tuple[ResearchEventInformationAsymmetryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_notes: tuple[ResearchEventInformationAsymmetryPublicNote, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventInformationAsymmetryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("public_status", self.public_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_asymmetry_score",
            "max_asymmetry_score",
            "min_source_diversity_score",
            "max_contradiction_score",
            "min_resolution_clarity_score",
            "min_team_expertise_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_freshness_age_hours",
            _require_nonnegative_decimal(
                "max_freshness_age_hours",
                self.max_freshness_age_hours,
            ),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_event_information_asymmetry_scorecard_payload(self)


def build_research_event_information_asymmetry_scorecard(
    inputs: Sequence[ResearchEventInformationAsymmetryInput],
    *,
    generated_at: datetime,
    config: ResearchEventInformationAsymmetryScorecardConfig | None = None,
    public_notes: Sequence[ResearchEventInformationAsymmetryPublicNote] = (),
) -> ResearchEventInformationAsymmetryReport:
    """Build a pure public report on event-domain information asymmetry."""

    cfg = config or ResearchEventInformationAsymmetryScorecardConfig()
    if type(cfg) is not ResearchEventInformationAsymmetryScorecardConfig:
        raise ValueError("config must be a ResearchEventInformationAsymmetryScorecardConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchEventInformationAsymmetryReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "public_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_asymmetry_score": _average_ratio(
            tuple(row.asymmetry_score for row in rows),
        ),
        "max_asymmetry_score": max(
            (row.asymmetry_score for row in rows),
            default=_ZERO,
        ),
        "min_source_diversity_score": min(
            (row.source_diversity_score for row in rows),
            default=_ZERO,
        ),
        "max_freshness_age_hours": max(
            (row.freshness_age_hours for row in rows),
            default=_ZERO,
        ),
        "max_contradiction_score": max(
            (row.contradiction_score for row in rows),
            default=_ZERO,
        ),
        "min_resolution_clarity_score": min(
            (row.resolution_clarity_score for row in rows),
            default=_ZERO,
        ),
        "min_team_expertise_score": min(
            (row.team_expertise_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "public_notes": _normalize_public_notes(public_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventInformationAsymmetryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_information_asymmetry_scorecard_payload(
    value: ResearchEventInformationAsymmetryReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchEventInformationAsymmetryReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchEventInformationAsymmetryReport or dict")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchEventInformationAsymmetryInput,
    config: ResearchEventInformationAsymmetryScorecardConfig,
) -> ResearchEventInformationAsymmetryRow:
    source_gap = _inverse_ratio(row.source_diversity_score)
    freshness_gap = _freshness_gap_score(row.freshness_age_hours, config)
    resolution_gap = _inverse_ratio(row.resolution_clarity_score)
    team_gap = _inverse_ratio(row.team_expertise_score)
    asymmetry_score = _asymmetry_score(
        source_diversity_gap_score=source_gap,
        freshness_gap_score=freshness_gap,
        contradiction_score=row.contradiction_score,
        resolution_clarity_gap_score=resolution_gap,
        team_expertise_gap_score=team_gap,
        config=config,
    )
    reason_codes = _row_reason_codes(
        source_diversity_score=row.source_diversity_score,
        freshness_age_hours=row.freshness_age_hours,
        contradiction_score=row.contradiction_score,
        resolution_clarity_score=row.resolution_clarity_score,
        team_expertise_score=row.team_expertise_score,
        asymmetry_score=asymmetry_score,
        config=config,
    )
    return ResearchEventInformationAsymmetryRow(
        domain_digest=_domain_digest(row.domain_key),
        source_diversity_score=row.source_diversity_score,
        source_diversity_gap_score=source_gap,
        freshness_age_hours=row.freshness_age_hours,
        freshness_gap_score=freshness_gap,
        contradiction_score=row.contradiction_score,
        resolution_clarity_score=row.resolution_clarity_score,
        resolution_clarity_gap_score=resolution_gap,
        team_expertise_score=row.team_expertise_score,
        team_expertise_gap_score=team_gap,
        asymmetry_score=asymmetry_score,
        public_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    source_diversity_score: Decimal,
    freshness_age_hours: Decimal,
    contradiction_score: Decimal,
    resolution_clarity_score: Decimal,
    team_expertise_score: Decimal,
    asymmetry_score: Decimal,
    config: ResearchEventInformationAsymmetryScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_diversity_score < config.min_source_diversity_score:
        reason_codes.append(REASON_SOURCE_DIVERSITY_BLOCK)
    elif source_diversity_score < config.pass_source_diversity_score:
        reason_codes.append(REASON_SOURCE_DIVERSITY_WATCH)
    if freshness_age_hours >= config.block_freshness_age_hours:
        reason_codes.append(REASON_FRESHNESS_BLOCK)
    elif freshness_age_hours > config.watch_freshness_age_hours:
        reason_codes.append(REASON_FRESHNESS_WATCH)
    if contradiction_score >= config.block_contradiction_score:
        reason_codes.append(REASON_CONTRADICTION_BLOCK)
    elif contradiction_score > config.watch_contradiction_score:
        reason_codes.append(REASON_CONTRADICTION_WATCH)
    if resolution_clarity_score < config.min_resolution_clarity_score:
        reason_codes.append(REASON_RESOLUTION_CLARITY_BLOCK)
    elif resolution_clarity_score < config.pass_resolution_clarity_score:
        reason_codes.append(REASON_RESOLUTION_CLARITY_WATCH)
    if team_expertise_score < config.min_team_expertise_score:
        reason_codes.append(REASON_TEAM_EXPERTISE_BLOCK)
    elif team_expertise_score < config.pass_team_expertise_score:
        reason_codes.append(REASON_TEAM_EXPERTISE_WATCH)
    if asymmetry_score >= config.block_asymmetry_score:
        reason_codes.append(REASON_ASYMMETRY_SCORE_BLOCK)
    elif asymmetry_score > config.watch_asymmetry_score:
        reason_codes.append(REASON_ASYMMETRY_SCORE_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_INFORMATION_QUALITY_PASS)
    return tuple(
        reason_code
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_INFORMATION_QUALITY_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchEventInformationAsymmetryRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(rows: tuple[ResearchEventInformationAsymmetryRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _row_sort_key(row: ResearchEventInformationAsymmetryRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.public_status), row.asymmetry_score, row.domain_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchEventInformationAsymmetryRow, ...],
) -> tuple[ResearchEventInformationAsymmetryReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, _ZERO) + _ONE
    return tuple(
        ResearchEventInformationAsymmetryReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _freshness_gap_score(
    freshness_age_hours: Decimal,
    config: ResearchEventInformationAsymmetryScorecardConfig,
) -> Decimal:
    if freshness_age_hours >= config.block_freshness_age_hours:
        return _ONE
    return _clamp_ratio(freshness_age_hours / config.block_freshness_age_hours)


def _asymmetry_score(
    *,
    source_diversity_gap_score: Decimal,
    freshness_gap_score: Decimal,
    contradiction_score: Decimal,
    resolution_clarity_gap_score: Decimal,
    team_expertise_gap_score: Decimal,
    config: ResearchEventInformationAsymmetryScorecardConfig,
) -> Decimal:
    weighted_gap = (
        source_diversity_gap_score * config.source_diversity_weight
        + freshness_gap_score * config.freshness_weight
        + contradiction_score * config.contradiction_weight
        + resolution_clarity_gap_score * config.resolution_clarity_weight
        + team_expertise_gap_score * config.team_expertise_weight
    )
    return _clamp_ratio(weighted_gap)


def _validate_row(
    row: ResearchEventInformationAsymmetryRow,
    config: ResearchEventInformationAsymmetryScorecardConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchEventInformationAsymmetryScorecardConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchEventInformationAsymmetryScorecardConfig",
            )
        if row.source_diversity_gap_score != _inverse_ratio(row.source_diversity_score):
            raise ValueError("source_diversity_gap_score must match source_diversity_score")
        expected_freshness = _freshness_gap_score(row.freshness_age_hours, config)
        if row.freshness_gap_score != expected_freshness:
            raise ValueError("freshness_gap_score must match freshness_age_hours")
        if row.resolution_clarity_gap_score != _inverse_ratio(row.resolution_clarity_score):
            raise ValueError(
                "resolution_clarity_gap_score must match resolution_clarity_score",
            )
        if row.team_expertise_gap_score != _inverse_ratio(row.team_expertise_score):
            raise ValueError("team_expertise_gap_score must match team_expertise_score")
        expected_asymmetry = _asymmetry_score(
            source_diversity_gap_score=row.source_diversity_gap_score,
            freshness_gap_score=row.freshness_gap_score,
            contradiction_score=row.contradiction_score,
            resolution_clarity_gap_score=row.resolution_clarity_gap_score,
            team_expertise_gap_score=row.team_expertise_gap_score,
            config=config,
        )
        if row.asymmetry_score != expected_asymmetry:
            raise ValueError("asymmetry_score must match component scores")
        expected_reasons = _row_reason_codes(
            source_diversity_score=row.source_diversity_score,
            freshness_age_hours=row.freshness_age_hours,
            contradiction_score=row.contradiction_score,
            resolution_clarity_score=row.resolution_clarity_score,
            team_expertise_score=row.team_expertise_score,
            asymmetry_score=row.asymmetry_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.public_status != _row_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    if (
        row.reason_codes == (REASON_INFORMATION_QUALITY_PASS,)
        and row.public_status != STATUS_PASS
    ):
        raise ValueError("pass reason must map to pass status")


def _validate_report(report: ResearchEventInformationAsymmetryReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_asymmetry_score != _average_ratio(
        tuple(row.asymmetry_score for row in report.rows),
    ):
        raise ValueError("average_asymmetry_score must match rows")
    if report.max_asymmetry_score != max(
        (row.asymmetry_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_asymmetry_score must match rows")
    if report.min_source_diversity_score != min(
        (row.source_diversity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_source_diversity_score must match rows")
    if report.max_freshness_age_hours != max(
        (row.freshness_age_hours for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_freshness_age_hours must match rows")
    if report.max_contradiction_score != max(
        (row.contradiction_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_score must match rows")
    if report.min_resolution_clarity_score != min(
        (row.resolution_clarity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_resolution_clarity_score must match rows")
    if report.min_team_expertise_score != min(
        (row.team_expertise_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_team_expertise_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchEventInformationAsymmetryReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchEventInformationAsymmetryInput],
) -> tuple[ResearchEventInformationAsymmetryInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventInformationAsymmetryInput:
            raise ValueError("inputs must contain ResearchEventInformationAsymmetryInput")
        _require_hard_flags("input", row)
        digest = _domain_digest(row.domain_key)
        if digest in seen:
            raise ValueError("inputs must be unique by domain digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventInformationAsymmetryRow, ...],
) -> tuple[ResearchEventInformationAsymmetryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventInformationAsymmetryRow:
            raise ValueError("rows must contain ResearchEventInformationAsymmetryRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    domain_digests = tuple(row.domain_digest for row in normalized)
    if len(set(domain_digests)) != len(domain_digests):
        raise ValueError("rows must have unique domain digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchEventInformationAsymmetryReasonCodeCount, ...],
) -> tuple[ResearchEventInformationAsymmetryReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventInformationAsymmetryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventInformationAsymmetryReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    expected_order = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in tuple(row.reason_code for row in normalized)
    )
    if tuple(row.reason_code for row in normalized) != expected_order:
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_public_notes(
    public_notes: Sequence[ResearchEventInformationAsymmetryPublicNote],
) -> tuple[ResearchEventInformationAsymmetryPublicNote, ...]:
    if type(public_notes) not in (list, tuple):
        raise ValueError("public_notes must be a list or tuple")
    normalized = tuple(public_notes)
    for note in normalized:
        if type(note) is not ResearchEventInformationAsymmetryPublicNote:
            raise ValueError(
                "public_notes must contain ResearchEventInformationAsymmetryPublicNote",
            )
        _require_hard_flags("public note", note)
    keys = tuple(note.key for note in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_notes must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_notes must have unique keys")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_INFORMATION_QUALITY_PASS in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    normalized = tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _report_payload(report: ResearchEventInformationAsymmetryReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        public_status=report.public_status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_asymmetry_score=report.average_asymmetry_score,
        max_asymmetry_score=report.max_asymmetry_score,
        min_source_diversity_score=report.min_source_diversity_score,
        max_freshness_age_hours=report.max_freshness_age_hours,
        max_contradiction_score=report.max_contradiction_score,
        min_resolution_clarity_score=report.min_resolution_clarity_score,
        min_team_expertise_score=report.min_team_expertise_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        public_notes=report.public_notes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    public_status: str,
    row_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_asymmetry_score: Decimal,
    max_asymmetry_score: Decimal,
    min_source_diversity_score: Decimal,
    max_freshness_age_hours: Decimal,
    max_contradiction_score: Decimal,
    min_resolution_clarity_score: Decimal,
    min_team_expertise_score: Decimal,
    rows: tuple[ResearchEventInformationAsymmetryRow, ...],
    reason_code_counts: tuple[ResearchEventInformationAsymmetryReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
    public_notes: tuple[ResearchEventInformationAsymmetryPublicNote, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "public_status": public_status,
        "row_count": _json_ready(row_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "average_asymmetry_score": _json_ready(average_asymmetry_score),
        "max_asymmetry_score": _json_ready(max_asymmetry_score),
        "min_source_diversity_score": _json_ready(min_source_diversity_score),
        "max_freshness_age_hours": _json_ready(max_freshness_age_hours),
        "max_contradiction_score": _json_ready(max_contradiction_score),
        "min_resolution_clarity_score": _json_ready(min_resolution_clarity_score),
        "min_team_expertise_score": _json_ready(min_team_expertise_score),
        "rows": [_row_payload(row) for row in rows],
        "reason_code_counts": [_reason_count_payload(row) for row in reason_code_counts],
        "reason_codes": list(reason_codes),
        "public_notes": [_public_note_payload(note) for note in public_notes],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: ResearchEventInformationAsymmetryRow) -> dict[str, object]:
    return {
        "domain_digest": row.domain_digest,
        "source_diversity_score": _json_ready(row.source_diversity_score),
        "source_diversity_gap_score": _json_ready(row.source_diversity_gap_score),
        "freshness_age_hours": _json_ready(row.freshness_age_hours),
        "freshness_gap_score": _json_ready(row.freshness_gap_score),
        "contradiction_score": _json_ready(row.contradiction_score),
        "resolution_clarity_score": _json_ready(row.resolution_clarity_score),
        "resolution_clarity_gap_score": _json_ready(row.resolution_clarity_gap_score),
        "team_expertise_score": _json_ready(row.team_expertise_score),
        "team_expertise_gap_score": _json_ready(row.team_expertise_gap_score),
        "asymmetry_score": _json_ready(row.asymmetry_score),
        "public_status": row.public_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_count_payload(
    row: ResearchEventInformationAsymmetryReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": row.reason_code,
        "count": _json_ready(row.count),
        "row_ratio": _json_ready(row.row_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_note_payload(
    note: ResearchEventInformationAsymmetryPublicNote,
) -> dict[str, object]:
    return {
        "key": note.key,
        "value": note.value,
        "paper_only": note.paper_only,
        "report_only": note.report_only,
        "readonly": note.readonly,
    }


def _report_digest(report: ResearchEventInformationAsymmetryReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "public_status": report.public_status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_asymmetry_score": report.average_asymmetry_score,
            "max_asymmetry_score": report.max_asymmetry_score,
            "min_source_diversity_score": report.min_source_diversity_score,
            "max_freshness_age_hours": report.max_freshness_age_hours,
            "max_contradiction_score": report.max_contradiction_score,
            "min_resolution_clarity_score": report.min_resolution_clarity_score,
            "min_team_expertise_score": report.min_team_expertise_score,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "public_notes": report.public_notes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        public_status=_require_mapping_value(values, "public_status", str),
        row_count=_require_mapping_value(values, "row_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        average_asymmetry_score=_require_mapping_value(
            values,
            "average_asymmetry_score",
            Decimal,
        ),
        max_asymmetry_score=_require_mapping_value(
            values,
            "max_asymmetry_score",
            Decimal,
        ),
        min_source_diversity_score=_require_mapping_value(
            values,
            "min_source_diversity_score",
            Decimal,
        ),
        max_freshness_age_hours=_require_mapping_value(
            values,
            "max_freshness_age_hours",
            Decimal,
        ),
        max_contradiction_score=_require_mapping_value(
            values,
            "max_contradiction_score",
            Decimal,
        ),
        min_resolution_clarity_score=_require_mapping_value(
            values,
            "min_resolution_clarity_score",
            Decimal,
        ),
        min_team_expertise_score=_require_mapping_value(
            values,
            "min_team_expertise_score",
            Decimal,
        ),
        rows=_require_mapping_value(values, "rows", tuple),
        reason_code_counts=_require_mapping_value(values, "reason_code_counts", tuple),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        public_notes=_require_mapping_value(values, "public_notes", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _validate_payload_digest(payload: dict[str, object]) -> None:
    if _DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(_DIGEST_FIELD, payload[_DIGEST_FIELD])
    digest_payload = dict(payload)
    digest_payload.pop(_DIGEST_FIELD)
    if payload[_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchEventInformationAsymmetryReport:
        return _report_payload(value)
    if type(value) is ResearchEventInformationAsymmetryRow:
        return _row_payload(value)
    if type(value) is ResearchEventInformationAsymmetryReasonCodeCount:
        return _reason_count_payload(value)
    if type(value) is ResearchEventInformationAsymmetryPublicNote:
        return _public_note_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchEventInformationAsymmetryScorecardConfig,
            ResearchEventInformationAsymmetryPublicNote,
            ResearchEventInformationAsymmetryRow,
            ResearchEventInformationAsymmetryReasonCodeCount,
            ResearchEventInformationAsymmetryReport,
        ):
            if type(value) is ResearchEventInformationAsymmetryInput:
                return
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if field.name == "validation_config":
                continue
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            if key.endswith("status") and type(item) is str and item not in _STATUS_VALUES:
                raise ValueError(f"{item_path} must be pass, watch, or block")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_domain_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DOMAIN_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _domain_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION",
    "ResearchEventInformationAsymmetryInput",
    "ResearchEventInformationAsymmetryPublicNote",
    "ResearchEventInformationAsymmetryReasonCodeCount",
    "ResearchEventInformationAsymmetryReport",
    "ResearchEventInformationAsymmetryRow",
    "ResearchEventInformationAsymmetryScorecardConfig",
    "build_research_event_information_asymmetry_scorecard",
    "research_event_information_asymmetry_scorecard_payload",
)
