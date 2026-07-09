"""Pure local report-only decay scorecard for specialist authority."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any, Sequence, get_args, get_origin, get_type_hints


DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_SCORECARD_CONFIG_VERSION = (
    "research-team-specialist-source-authority-decay-scorecard-report-v0"
)
RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_HARD_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_AGGREGATE_IDENTIFIER_FIELDS = frozenset(
    ("team_key", "specialist_key", "authority_family"),
)
_STATUS_RANK = {"block": Decimal("0.000000"), "watch": Decimal("1.000000"), "pass": Decimal("2.000000")}

EMPTY_REASON = "authority_decay_empty"
PASS_REASON = "authority_decay_pass"
SCORE_WATCH_REASON = "authority_decay_score_watch"
SCORE_BLOCK_REASON = "authority_decay_score_block"
AGE_WATCH_REASON = "authority_age_watch"
CONFLICT_WATCH_REASON = "authority_conflict_watch"
CONFLICT_BLOCK_REASON = "authority_conflict_block"
_REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    SCORE_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    SCORE_WATCH_REASON,
    AGE_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    PASS_REASON,
)
_ROW_REASON_CODES = tuple(reason for reason in _REASON_CODE_SEQUENCE if reason != EMPTY_REASON)
_UNSAFE_PUBLIC_TERMS = (
    "can" + "didate",
    "mar" + "ket",
    "sl" + "ug",
    "quest" + "ion",
    "u" + "rl",
    "source_" + "id",
    "source_" + "url",
    "source_" + "text",
    "raw_" + "text",
    "http://",
    "https://",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "au" + "th_credential",
    "private" + "_" + "key",
    "wall" + "et",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "trad" + "ing",
    "siz" + "ing",
    "reco" + "mmend" + "ation",
    "net" + "work",
    "data" + "base",
    "exe" + "cution",
    "sec" + "ret",
    "cred" + "ential",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_SCORECARD_CONFIG_VERSION
    )
    pass_specialist_authority_score: Decimal = Decimal("0.700000")
    block_specialist_authority_score: Decimal = Decimal("0.400000")
    watch_freshness_decay_score: Decimal = Decimal("0.500000")
    watch_conflict_score: Decimal = Decimal("0.200000")
    block_conflict_score: Decimal = Decimal("0.500000")
    decay_adjusted_authority_weight: Decimal = Decimal(
        "0.676470588235294117647058823529411765",
    )
    corroboration_weight: Decimal = Decimal(
        "0.148529411764705882352941176470588235",
    )
    conflict_resistance_weight: Decimal = Decimal(
        "0.170588235294117647058823529411764706",
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig:
            raise TypeError(
                "ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_specialist_authority_score",
            "block_specialist_authority_score",
            "watch_freshness_decay_score",
            "watch_conflict_score",
            "block_conflict_score",
            "decay_adjusted_authority_weight",
            "corroboration_weight",
            "conflict_resistance_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_specialist_authority_score > self.pass_specialist_authority_score:
            raise ValueError(
                "block_specialist_authority_score must be at most "
                "pass_specialist_authority_score",
            )
        if self.watch_conflict_score > self.block_conflict_score:
            raise ValueError("watch_conflict_score must be at most block_conflict_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceAuthorityDecayObservation:
    team_key: str
    specialist_key: str
    authority_family: str
    observed_at: datetime
    authority_score: Decimal
    source_decay_half_life_seconds: Decimal
    corroboration_score: Decimal
    conflict_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceAuthorityDecayObservation:
            raise TypeError(
                "ResearchTeamSpecialistSourceAuthorityDecayObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistSourceAuthorityDecayObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchTeamSpecialistSourceAuthorityDecayObservation",
            )
        for field_name in ("team_key", "specialist_key", "authority_family"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_decay_half_life_seconds",
            _require_positive_decimal(
                "source_decay_half_life_seconds",
                self.source_decay_half_life_seconds,
            ),
        )
        for field_name in ("authority_score", "corroboration_score", "conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceAuthorityDecayScorecardRow:
    team_key: str
    specialist_key: str
    authority_family: str
    observed_at: datetime
    source_age_seconds: Decimal
    source_decay_half_life_seconds: Decimal
    authority_score: Decimal
    freshness_decay_score: Decimal
    decay_adjusted_authority_score: Decimal
    corroboration_score: Decimal
    conflict_score: Decimal
    specialist_authority_score: Decimal
    authority_decay_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceAuthorityDecayScorecardRow:
            raise TypeError(
                "ResearchTeamSpecialistSourceAuthorityDecayScorecardRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardRow:
            raise ValueError(
                "row must be exactly "
                "ResearchTeamSpecialistSourceAuthorityDecayScorecardRow",
            )
        for field_name in ("team_key", "specialist_key", "authority_family"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "source_decay_half_life_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.source_decay_half_life_seconds <= _ZERO:
            raise ValueError("source_decay_half_life_seconds must be positive")
        for field_name in (
            "authority_score",
            "freshness_decay_score",
            "decay_adjusted_authority_score",
            "corroboration_score",
            "conflict_score",
            "specialist_authority_score",
            "authority_decay_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount",
            )
        if type(self.reason_code) is not str or self.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    authority_family_count: Decimal
    average_specialist_authority_score: Decimal
    lowest_decay_adjusted_authority_score: Decimal
    highest_authority_decay_risk_score: Decimal
    oldest_source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount, ...]
    rows: tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
            raise TypeError(
                "ResearchTeamSpecialistSourceAuthorityDecayScorecardReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchTeamSpecialistSourceAuthorityDecayScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "team_count",
            "specialist_count",
            "authority_family_count",
            "oldest_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_specialist_authority_score",
            "lowest_decay_adjusted_authority_score",
            "highest_authority_decay_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_specialist_source_authority_decay_scorecard_report_payload(
            self,
        )


def build_research_team_specialist_source_authority_decay_scorecard_report(
    observations: Sequence[ResearchTeamSpecialistSourceAuthorityDecayObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig | None = None,
) -> ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
    if config is None:
        config = ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig()
    if type(config) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = _scorecard_rows(
        _normalize_observations(observations),
        generated_at=generated_at,
        config=config,
    )
    return ResearchTeamSpecialistSourceAuthorityDecayScorecardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        team_count=_decimal_count(len({row.team_key for row in rows})),
        specialist_count=_decimal_count(len({row.specialist_key for row in rows})),
        authority_family_count=_decimal_count(len({row.authority_family for row in rows})),
        average_specialist_authority_score=_average(
            tuple(row.specialist_authority_score for row in rows),
        ),
        lowest_decay_adjusted_authority_score=min(
            (row.decay_adjusted_authority_score for row in rows),
            default=_ZERO,
        ).quantize(_QUANT),
        highest_authority_decay_risk_score=max(
            (row.authority_decay_risk_score for row in rows),
            default=_ZERO,
        ).quantize(_QUANT),
        oldest_source_age_seconds=max(
            (row.source_age_seconds for row in rows),
            default=_ZERO,
        ).quantize(_QUANT),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_source_authority_decay_scorecard_report_payload(
    report: ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
        raise ValueError(
            "report must be a ResearchTeamSpecialistSourceAuthorityDecayScorecardReport",
        )
    validate_research_team_specialist_source_authority_decay_scorecard_report_digest(
        report,
    )
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
        payload,
    )
    return payload


def research_team_specialist_source_authority_decay_scorecard_report_digest(
    report: ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
        raise ValueError(
            "report must be a ResearchTeamSpecialistSourceAuthorityDecayScorecardReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_team_specialist_source_authority_decay_scorecard_report_digest(
    report: ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
) -> None:
    if type(report) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
        raise ValueError(
            "report must be a ResearchTeamSpecialistSourceAuthorityDecayScorecardReport",
        )
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _verify_public_digest(payload)
    parsed_report = _record_from_public_payload(
        ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
        payload,
        field_path="public payload",
        record_label="report",
    )
    if _json_ready(parsed_report) != payload:
        raise ValueError("public payload must use canonical report serialization")


def _scorecard_rows(
    observations: tuple[ResearchTeamSpecialistSourceAuthorityDecayObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
) -> tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...]:
    rows = tuple(
        _scorecard_row(observation, generated_at=generated_at, config=config)
        for observation in observations
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _scorecard_row(
    observation: ResearchTeamSpecialistSourceAuthorityDecayObservation,
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
) -> ResearchTeamSpecialistSourceAuthorityDecayScorecardRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    source_age_seconds = _age_seconds(generated_at, observation.observed_at)
    freshness_decay_score = _freshness_decay_score(
        source_age_seconds,
        observation.source_decay_half_life_seconds,
    )
    decay_adjusted_authority_score = _clamp_ratio(
        observation.authority_score * freshness_decay_score,
    )
    specialist_authority_score = _specialist_authority_score(
        decay_adjusted_authority_score=decay_adjusted_authority_score,
        corroboration_score=observation.corroboration_score,
        conflict_score=observation.conflict_score,
        config=config,
    )
    authority_decay_risk_score = _clamp_ratio(_ONE - specialist_authority_score)
    status = _row_status(
        specialist_authority_score=specialist_authority_score,
        freshness_decay_score=freshness_decay_score,
        conflict_score=observation.conflict_score,
        config=config,
    )
    return ResearchTeamSpecialistSourceAuthorityDecayScorecardRow(
        team_key=observation.team_key,
        specialist_key=observation.specialist_key,
        authority_family=observation.authority_family,
        observed_at=observation.observed_at,
        source_age_seconds=source_age_seconds,
        source_decay_half_life_seconds=observation.source_decay_half_life_seconds,
        authority_score=observation.authority_score,
        freshness_decay_score=freshness_decay_score,
        decay_adjusted_authority_score=decay_adjusted_authority_score,
        corroboration_score=observation.corroboration_score,
        conflict_score=observation.conflict_score,
        specialist_authority_score=specialist_authority_score,
        authority_decay_risk_score=authority_decay_risk_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            specialist_authority_score=specialist_authority_score,
            freshness_decay_score=freshness_decay_score,
            conflict_score=observation.conflict_score,
            config=config,
        ),
    )


def _freshness_decay_score(
    source_age_seconds: Decimal,
    source_decay_half_life_seconds: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        if source_age_seconds >= source_decay_half_life_seconds:
            return _ZERO
        return _clamp_ratio(_ONE - (source_age_seconds / source_decay_half_life_seconds))


def _specialist_authority_score(
    *,
    decay_adjusted_authority_score: Decimal,
    corroboration_score: Decimal,
    conflict_score: Decimal,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        value = (
            decay_adjusted_authority_score * config.decay_adjusted_authority_weight
            + corroboration_score * config.corroboration_weight
            + (_ONE - conflict_score) * config.conflict_resistance_weight
        )
        return _clamp_ratio(value)


def _row_status(
    *,
    specialist_authority_score: Decimal,
    freshness_decay_score: Decimal,
    conflict_score: Decimal,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
) -> str:
    if (
        specialist_authority_score < config.block_specialist_authority_score
        or conflict_score >= config.block_conflict_score
    ):
        return "block"
    if (
        specialist_authority_score < config.pass_specialist_authority_score
        or freshness_decay_score <= config.watch_freshness_decay_score
        or conflict_score >= config.watch_conflict_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    specialist_authority_score: Decimal,
    freshness_decay_score: Decimal,
    conflict_score: Decimal,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    reasons: list[str] = []
    if specialist_authority_score < config.block_specialist_authority_score:
        reasons.append(SCORE_BLOCK_REASON)
    elif specialist_authority_score < config.pass_specialist_authority_score:
        reasons.append(SCORE_WATCH_REASON)
    if status != "block" and freshness_decay_score <= config.watch_freshness_decay_score:
        reasons.append(AGE_WATCH_REASON)
    if conflict_score >= config.block_conflict_score:
        reasons.append(CONFLICT_BLOCK_REASON)
    elif conflict_score >= config.watch_conflict_score:
        reasons.append(CONFLICT_WATCH_REASON)
    return _normalize_reason_codes(tuple(reasons), _ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons), _REASON_CODE_SEQUENCE)


def _status_count(
    rows: tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...],
) -> tuple[ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_ONE,
            ),
        )
    return tuple(
        ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code != EMPTY_REASON
        and any(reason_code in row.reason_codes for row in rows)
    )


def _validate_row(row: ResearchTeamSpecialistSourceAuthorityDecayScorecardRow) -> None:
    expected_decay_adjusted = _clamp_ratio(
        row.authority_score * row.freshness_decay_score,
    )
    if row.decay_adjusted_authority_score != expected_decay_adjusted:
        raise ValueError("decay_adjusted_authority_score must match row inputs")
    expected_risk = _clamp_ratio(_ONE - row.specialist_authority_score)
    if row.authority_decay_risk_score != expected_risk:
        raise ValueError("authority_decay_risk_score must match row score")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use the pass reason")
    if row.status == "watch" and not any(
        reason.endswith("_watch") for reason in row.reason_codes
    ):
        raise ValueError("watch rows must include a watch reason")
    if row.status == "block" and not any(
        reason.endswith("_block") for reason in row.reason_codes
    ):
        raise ValueError("block rows must include a block reason")


def _validate_report(
    report: ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.team_count != _decimal_count(len({row.team_key for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _decimal_count(
        len({row.specialist_key for row in report.rows}),
    ):
        raise ValueError("specialist_count must match rows")
    if report.authority_family_count != _decimal_count(
        len({row.authority_family for row in report.rows}),
    ):
        raise ValueError("authority_family_count must match rows")
    if report.average_specialist_authority_score != _average(
        tuple(row.specialist_authority_score for row in report.rows),
    ):
        raise ValueError("average_specialist_authority_score must match rows")
    if report.lowest_decay_adjusted_authority_score != min(
        (row.decay_adjusted_authority_score for row in report.rows),
        default=_ZERO,
    ).quantize(_QUANT):
        raise ValueError("lowest_decay_adjusted_authority_score must match rows")
    if report.highest_authority_decay_risk_score != max(
        (row.authority_decay_risk_score for row in report.rows),
        default=_ZERO,
    ).quantize(_QUANT):
        raise ValueError("highest_authority_decay_risk_score must match rows")
    if report.oldest_source_age_seconds != max(
        (row.source_age_seconds for row in report.rows),
        default=_ZERO,
    ).quantize(_QUANT):
        raise ValueError("oldest_source_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_observations(
    value: Sequence[ResearchTeamSpecialistSourceAuthorityDecayObservation],
) -> tuple[ResearchTeamSpecialistSourceAuthorityDecayObservation, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("observations must be a sequence")
    observations = tuple(value)
    for observation in observations:
        if type(observation) is not ResearchTeamSpecialistSourceAuthorityDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamSpecialistSourceAuthorityDecayObservation",
            )
        _require_hard_flags("observation", observation)
    keys = tuple(
        (item.team_key, item.specialist_key, item.authority_family)
        for item in observations
    )
    if len(set(keys)) != len(keys):
        raise ValueError(
            "team_key, specialist_key, and authority_family triples must be unique",
        )
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item.team_key,
                item.specialist_key,
                item.authority_family,
                item.observed_at,
            ),
        ),
    )


def _normalize_rows(
    value: Sequence[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow],
) -> tuple[ResearchTeamSpecialistSourceAuthorityDecayScorecardRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSpecialistSourceAuthorityDecayScorecardRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistSourceAuthorityDecayScorecardRow",
            )
        _require_hard_flags("row", row)
    keys = tuple((row.team_key, row.specialist_key, row.authority_family) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError(
            "rows team_key, specialist_key, and authority_family triples must be unique",
        )
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: Sequence[ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount],
) -> tuple[ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    counts = tuple(value)
    for count in counts:
        if type(count) is not ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(
        sorted(
            counts,
            key=lambda count: _REASON_CODE_SEQUENCE.index(count.reason_code),
        ),
    )


def _row_sort_key(
    row: ResearchTeamSpecialistSourceAuthorityDecayScorecardRow,
) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        _STATUS_RANK[row.status],
        _ONE - row.authority_decay_risk_score,
        row.team_key,
        row.specialist_key,
        row.authority_family,
        row.observed_at.isoformat(),
    )


def _normalize_reason_codes(
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    seen: set[str] = set()
    for reason in value:
        if type(reason) is not str or reason not in allowed:
            raise ValueError("reason_codes must contain known reason codes")
        seen.add(reason)
    return tuple(reason for reason in allowed if reason in seen)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if (
        field_name in _PUBLIC_AGGREGATE_IDENTIFIER_FIELDS
        and _looks_like_opaque_reference(value)
    ):
        raise ValueError(f"{field_name} must be a public-safe aggregate identifier")
    return value


def _looks_like_opaque_reference(value: str) -> bool:
    if value.isdecimal() or "-" in value:
        return True
    lowered = value.lower()
    hexadecimal_characters = set("0123456789abcdef")
    if (
        lowered.startswith("0x")
        and len(lowered) >= 18
        and all(character in hexadecimal_characters for character in lowered[2:])
    ):
        return True
    return len(value) >= 24 and value.isalnum()


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(
            Decimal(delta.days) * _SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND),
        )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, _ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("public payload must not contain floats")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not public JSON serializable")


def _record_from_public_payload(
    record_type: type[Any],
    value: object,
    *,
    field_path: str,
    record_label: str,
) -> Any:
    if type(value) is not dict:
        raise ValueError(f"{field_path} must be a JSON object")
    expected_fields = {item.name for item in fields(record_type)}
    if set(value) != expected_fields:
        raise ValueError(f"{field_path} must match {record_label} fields")
    type_hints = get_type_hints(record_type)
    parsed_fields = {
        item.name: _value_from_public_payload(
            value[item.name],
            type_hints[item.name],
            field_path=f"{field_path}.{item.name}",
        )
        for item in fields(record_type)
    }
    return record_type(**parsed_fields)


def _value_from_public_payload(
    value: object,
    expected_type: Any,
    *,
    field_path: str,
) -> Any:
    if expected_type is Decimal:
        if type(value) is not str:
            raise ValueError(f"{field_path} must be a Decimal string")
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{field_path} must be a Decimal string") from exc
    if expected_type is datetime:
        if type(value) is not str:
            raise ValueError(f"{field_path} must be an ISO-8601 datetime string")
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f"{field_path} must be an ISO-8601 datetime string",
            ) from exc
    if expected_type is str:
        if type(value) is not str:
            raise ValueError(f"{field_path} must be a string")
        return value
    if expected_type is bool:
        if type(value) is not bool:
            raise ValueError(f"{field_path} must be a boolean")
        return value
    if get_origin(expected_type) is tuple:
        if type(value) is not list:
            raise ValueError(f"{field_path} must be a JSON array")
        item_type, tuple_marker = get_args(expected_type)
        if tuple_marker is not Ellipsis:
            raise ValueError(f"{field_path} has an unsupported tuple type")
        return tuple(
            _value_from_public_payload(
                item,
                item_type,
                field_path=f"{field_path}.{index}",
            )
            for index, item in enumerate(value)
        )
    if is_dataclass(expected_type):
        return _record_from_public_payload(
            expected_type,
            value,
            field_path=field_path,
            record_label="record",
        )
    raise ValueError(f"{field_path} has an unsupported public payload type")


def _require_or_set_digest(
    report: ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
) -> None:
    expected_digest = _report_digest_from_public_payload(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
        return
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _report_digest_from_public_payload(
    report: ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(payload)
    return _payload_digest(payload)


def _payload_digest(payload_without_digest: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode(),
    ).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    if digest != _payload_digest(unsigned):
        raise ValueError("derived_validation_digest must match public payload")


def _reject_unsafe_public_payload(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string("public key", key)
            _reject_unsafe_public_payload(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _reject_unsafe_public_payload(value)
        return
    if isinstance(payload, str):
        _reject_unsafe_public_string("public value", payload)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public {label}")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_SCORECARD_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_STATUSES",
    "ResearchTeamSpecialistSourceAuthorityDecayObservation",
    "ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount",
    "ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig",
    "ResearchTeamSpecialistSourceAuthorityDecayScorecardReport",
    "ResearchTeamSpecialistSourceAuthorityDecayScorecardRow",
    "build_research_team_specialist_source_authority_decay_scorecard_report",
    "research_team_specialist_source_authority_decay_scorecard_report_digest",
    "research_team_specialist_source_authority_decay_scorecard_report_payload",
    "validate_research_team_specialist_source_authority_decay_scorecard_public_payload",
    "validate_research_team_specialist_source_authority_decay_scorecard_report_digest",
)
