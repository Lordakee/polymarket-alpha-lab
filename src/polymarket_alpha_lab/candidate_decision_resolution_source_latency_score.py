"""Pure report-only resolution-source latency scoring for candidate research."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_CANDIDATE_DECISION_RESOLUTION_SOURCE_LATENCY_SCORE_CONFIG_VERSION = (
    "candidate-decision-resolution-source-latency-score-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_PRIORITY = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}

NO_CANDIDATES_REASON = "resolution_source_latency_no_candidates"
PASS_REASON = "resolution_source_latency_pass"
OFFICIAL_LATENCY_BLOCK_REASON = "official_source_latency_minutes_block"
INDEPENDENT_LATENCY_BLOCK_REASON = "independent_source_latency_minutes_block"
SETTLEMENT_DELAY_BLOCK_REASON = "settlement_delay_hours_block"
LATENCY_VARIABILITY_BLOCK_REASON = "latency_variability_score_block"
SOURCE_RELIABILITY_BLOCK_REASON = "source_reliability_score_block"
AMBIGUITY_BLOCK_REASON = "ambiguity_score_block"
LATENCY_SCORE_BLOCK_REASON = "latency_score_below_watch_threshold"
OFFICIAL_LATENCY_WATCH_REASON = "official_source_latency_minutes_watch"
INDEPENDENT_LATENCY_WATCH_REASON = "independent_source_latency_minutes_watch"
SETTLEMENT_DELAY_WATCH_REASON = "settlement_delay_hours_watch"
LATENCY_VARIABILITY_WATCH_REASON = "latency_variability_score_watch"
SOURCE_RELIABILITY_WATCH_REASON = "source_reliability_score_watch"
AMBIGUITY_WATCH_REASON = "ambiguity_score_watch"
LATENCY_SCORE_WATCH_REASON = "latency_score_below_pass_threshold"

REASON_CODE_SEQUENCE = (
    NO_CANDIDATES_REASON,
    OFFICIAL_LATENCY_BLOCK_REASON,
    INDEPENDENT_LATENCY_BLOCK_REASON,
    SETTLEMENT_DELAY_BLOCK_REASON,
    LATENCY_VARIABILITY_BLOCK_REASON,
    SOURCE_RELIABILITY_BLOCK_REASON,
    AMBIGUITY_BLOCK_REASON,
    LATENCY_SCORE_BLOCK_REASON,
    OFFICIAL_LATENCY_WATCH_REASON,
    INDEPENDENT_LATENCY_WATCH_REASON,
    SETTLEMENT_DELAY_WATCH_REASON,
    LATENCY_VARIABILITY_WATCH_REASON,
    SOURCE_RELIABILITY_WATCH_REASON,
    AMBIGUITY_WATCH_REASON,
    LATENCY_SCORE_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    (
        OFFICIAL_LATENCY_BLOCK_REASON,
        INDEPENDENT_LATENCY_BLOCK_REASON,
        SETTLEMENT_DELAY_BLOCK_REASON,
        LATENCY_VARIABILITY_BLOCK_REASON,
        SOURCE_RELIABILITY_BLOCK_REASON,
        AMBIGUITY_BLOCK_REASON,
        LATENCY_SCORE_BLOCK_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        OFFICIAL_LATENCY_WATCH_REASON,
        INDEPENDENT_LATENCY_WATCH_REASON,
        SETTLEMENT_DELAY_WATCH_REASON,
        LATENCY_VARIABILITY_WATCH_REASON,
        SOURCE_RELIABILITY_WATCH_REASON,
        AMBIGUITY_WATCH_REASON,
        LATENCY_SCORE_WATCH_REASON,
    ),
)

SAFE_PUBLIC_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_latency_score",
        "min_latency_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "redacted_candidate_ref",
        "official_source_latency_minutes",
        "independent_source_latency_minutes",
        "settlement_delay_hours",
        "latency_variability_score",
        "source_reliability_score",
        "ambiguity_score",
        "latency_score",
        "hard_blocker_codes",
        "reason_code",
        "count",
        "candidate_ratio",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
RAW_CANDIDATE_KEY_COMPACTS = frozenset(
    (
        "candidateid",
        "rawcandidateid",
        "rawcandidateref",
        "candidatereference",
        "candidateslug",
    ),
)
MARKET_KEY_COMPACTS = frozenset(
    (
        "marketid",
        "rawmarketid",
        "marketslug",
        "marketquestion",
        "conditionid",
        "question",
        "slug",
    ),
)
SOURCE_KEY_COMPACTS = frozenset(
    (
        "sourceref",
        "sourcerefs",
        "sourceurl",
        "sourceurls",
        "sourceuri",
        "sourceuris",
        "sourcetext",
        "sourceexcerpt",
        "sourcetitle",
        "url",
        "uri",
        "dsn",
        "schema",
        "table",
        "tablename",
    ),
)
UNSAFE_KEY_COMPACTS = frozenset(
    (
        "au" + "th",
        "api" + "key",
        "private" + "key",
        "sec" + "ret",
        "to" + "ken",
        "wal" + "let",
        "or" + "der",
        "tr" + "ade",
        "b" + "uy",
        "s" + "ell",
        "rec" + "ommend",
        "rec" + "ommendation",
        "positionsizing",
        "positionsize",
    ),
)
STATUS_ALIAS_VALUES = frozenset(
    (
        "ready",
        "block" + "ed",
        "match" + "ed",
        "support" + "ed",
    ),
)
UNSAFE_VALUE_TERMS = (
    "au" + "th",
    "api" + "_key",
    "api" + "-key",
    "private" + "_key",
    "private" + "-key",
    "private " + "key",
    "sec" + "ret",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "position" + "_size",
    "position" + "-size",
    "position" + " size",
    "position" + " sizing",
)
SOURCE_VALUE_TERMS = (
    "http://",
    "https://",
    "www.",
    "://",
    ".com",
    ".org",
    ".net",
    ".io",
    ".co",
    ".test",
    ".app",
    ".dev",
    ".ai",
    ".gov",
    ".edu",
    "source_ref:",
    "source:",
    "source-report:",
    "dsn=",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "supa" + "base",
    "table:",
    "table=",
    "_table",
    " table ",
)


@dataclass(frozen=True)
class CandidateDecisionResolutionSourceLatencyScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_RESOLUTION_SOURCE_LATENCY_SCORE_CONFIG_VERSION
    )
    min_pass_latency_score: Decimal = Decimal("0.800000")
    min_watch_latency_score: Decimal = Decimal("0.500000")
    max_pass_official_source_latency_minutes: Decimal = Decimal("30.000000")
    max_watch_official_source_latency_minutes: Decimal = Decimal("240.000000")
    max_pass_independent_source_latency_minutes: Decimal = Decimal("60.000000")
    max_watch_independent_source_latency_minutes: Decimal = Decimal("360.000000")
    max_pass_settlement_delay_hours: Decimal = Decimal("24.000000")
    max_watch_settlement_delay_hours: Decimal = Decimal("72.000000")
    max_pass_latency_variability_score: Decimal = Decimal("0.200000")
    max_watch_latency_variability_score: Decimal = Decimal("0.600000")
    min_pass_source_reliability_score: Decimal = Decimal("0.800000")
    min_watch_source_reliability_score: Decimal = Decimal("0.500000")
    max_pass_ambiguity_score: Decimal = Decimal("0.100000")
    max_watch_ambiguity_score: Decimal = Decimal("0.400000")
    official_source_latency_weight: Decimal = Decimal("0.250000")
    independent_source_latency_weight: Decimal = Decimal("0.200000")
    settlement_delay_weight: Decimal = Decimal("0.150000")
    latency_variability_weight: Decimal = Decimal("0.150000")
    source_reliability_weight: Decimal = Decimal("0.150000")
    ambiguity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionSourceLatencyScoreConfig:
            raise ValueError(
                "config must be a "
                "CandidateDecisionResolutionSourceLatencyScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_RESOLUTION_SOURCE_LATENCY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_latency_score",
            "min_watch_latency_score",
            "max_pass_latency_variability_score",
            "max_watch_latency_variability_score",
            "min_pass_source_reliability_score",
            "min_watch_source_reliability_score",
            "max_pass_ambiguity_score",
            "max_watch_ambiguity_score",
            "official_source_latency_weight",
            "independent_source_latency_weight",
            "settlement_delay_weight",
            "latency_variability_weight",
            "source_reliability_weight",
            "ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_official_source_latency_minutes",
            "max_watch_official_source_latency_minutes",
            "max_pass_independent_source_latency_minutes",
            "max_watch_independent_source_latency_minutes",
            "max_pass_settlement_delay_hours",
            "max_watch_settlement_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_paper_only_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionSourceLatencyScoreInput:
    redacted_candidate_ref: str
    official_source_latency_minutes: Decimal
    independent_source_latency_minutes: Decimal
    settlement_delay_hours: Decimal
    latency_variability_score: Decimal
    source_reliability_score: Decimal
    ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionSourceLatencyScoreInput:
            raise ValueError(
                "input must be a CandidateDecisionResolutionSourceLatencyScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "official_source_latency_minutes",
            "independent_source_latency_minutes",
            "settlement_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latency_variability_score",
            "source_reliability_score",
            "ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_paper_only_flags("input", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionSourceLatencyScoreRow:
    generated_at: datetime
    redacted_candidate_ref: str
    official_source_latency_minutes: Decimal
    independent_source_latency_minutes: Decimal
    settlement_delay_hours: Decimal
    latency_variability_score: Decimal
    source_reliability_score: Decimal
    ambiguity_score: Decimal
    latency_score: Decimal
    status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionSourceLatencyScoreRow:
            raise ValueError(
                "row must be a CandidateDecisionResolutionSourceLatencyScoreRow",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "official_source_latency_minutes",
            "independent_source_latency_minutes",
            "settlement_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latency_variability_score",
            "source_reliability_score",
            "ambiguity_score",
            "latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(self.hard_blocker_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_paper_only_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_digest_from_values(_row_payload_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        if self.derived_validation_digest != _row_digest_from_values(
            _row_payload_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match row payload")


@dataclass(frozen=True)
class CandidateDecisionResolutionSourceLatencyReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionSourceLatencyReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "CandidateDecisionResolutionSourceLatencyReasonCodeCount",
            )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_unit_decimal("candidate_ratio", self.candidate_ratio),
        )
        _require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionSourceLatencyScoreReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_latency_score: Decimal
    min_latency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        CandidateDecisionResolutionSourceLatencyReasonCodeCount,
        ...,
    ]
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionSourceLatencyScoreReport:
            raise ValueError(
                "report must be a CandidateDecisionResolutionSourceLatencyScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_latency_score", "min_latency_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_paper_only_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_payload_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_payload_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_candidate_decision_resolution_source_latency_score_report(
    candidates: Iterable[object],
    *,
    config: CandidateDecisionResolutionSourceLatencyScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionResolutionSourceLatencyScoreReport:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        candidate_rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    if type(config) is not CandidateDecisionResolutionSourceLatencyScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionResolutionSourceLatencyScoreConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_paper_only_flags("config", config)

    seen_refs: set[str] = set()
    rows: list[CandidateDecisionResolutionSourceLatencyScoreRow] = []
    for candidate in candidate_rows:
        if type(candidate) is not CandidateDecisionResolutionSourceLatencyScoreInput:
            raise ValueError(
                "candidates must contain "
                "CandidateDecisionResolutionSourceLatencyScoreInput",
            )
        _require_paper_only_flags("input", candidate)
        if candidate.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(candidate.redacted_candidate_ref)
        rows.append(_row_from_candidate(candidate, config=config, generated_at=generated_at_utc))

    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return CandidateDecisionResolutionSourceLatencyScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        max_latency_score=_max_latency_score(sorted_rows),
        min_latency_score=_min_latency_score(sorted_rows),
        status=_report_status(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
        reason_code_counts=_reason_code_counts(sorted_rows),
        rows=sorted_rows,
    )


def validate_candidate_decision_resolution_source_latency_score_report(
    report: CandidateDecisionResolutionSourceLatencyScoreReport,
) -> bool:
    if type(report) is not CandidateDecisionResolutionSourceLatencyScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionResolutionSourceLatencyScoreReport",
        )
    _require_paper_only_flags("report", report)
    _validate_report(report)
    return True


def candidate_decision_resolution_source_latency_score_payload(
    report: CandidateDecisionResolutionSourceLatencyScoreReport,
) -> dict[str, Any]:
    validate_candidate_decision_resolution_source_latency_score_report(report)
    payload = _report_payload(report)
    validate_candidate_decision_resolution_source_latency_score_public_payload(payload)
    return payload


def validate_candidate_decision_resolution_source_latency_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_public_payload_flags(payload)
    return True


def _row_from_candidate(
    candidate: CandidateDecisionResolutionSourceLatencyScoreInput,
    *,
    config: CandidateDecisionResolutionSourceLatencyScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionResolutionSourceLatencyScoreRow:
    latency_score = _latency_score(candidate, config)
    reason_codes = _candidate_reason_codes(candidate, config, latency_score)
    hard_blocker_codes = tuple(
        reason_code for reason_code in reason_codes if reason_code in BLOCK_REASON_CODES
    )
    status = _status_from_reason_codes(reason_codes)
    return CandidateDecisionResolutionSourceLatencyScoreRow(
        generated_at=generated_at,
        redacted_candidate_ref=candidate.redacted_candidate_ref,
        official_source_latency_minutes=candidate.official_source_latency_minutes,
        independent_source_latency_minutes=(
            candidate.independent_source_latency_minutes
        ),
        settlement_delay_hours=candidate.settlement_delay_hours,
        latency_variability_score=candidate.latency_variability_score,
        source_reliability_score=candidate.source_reliability_score,
        ambiguity_score=candidate.ambiguity_score,
        latency_score=latency_score,
        status=status,
        hard_blocker_codes=hard_blocker_codes,
        reason_codes=reason_codes,
    )


def _latency_score(
    candidate: CandidateDecisionResolutionSourceLatencyScoreInput,
    config: CandidateDecisionResolutionSourceLatencyScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _lower_is_better_component(
                candidate.official_source_latency_minutes,
                config.max_pass_official_source_latency_minutes,
                config.max_watch_official_source_latency_minutes,
            )
            * config.official_source_latency_weight
        )
        score += (
            _lower_is_better_component(
                candidate.independent_source_latency_minutes,
                config.max_pass_independent_source_latency_minutes,
                config.max_watch_independent_source_latency_minutes,
            )
            * config.independent_source_latency_weight
        )
        score += (
            _lower_is_better_component(
                candidate.settlement_delay_hours,
                config.max_pass_settlement_delay_hours,
                config.max_watch_settlement_delay_hours,
            )
            * config.settlement_delay_weight
        )
        score += (
            _lower_is_better_component(
                candidate.latency_variability_score,
                config.max_pass_latency_variability_score,
                config.max_watch_latency_variability_score,
            )
            * config.latency_variability_weight
        )
        score += (
            _higher_is_better_component(
                candidate.source_reliability_score,
                config.min_pass_source_reliability_score,
                config.min_watch_source_reliability_score,
            )
            * config.source_reliability_weight
        )
        score += (
            _lower_is_better_component(
                candidate.ambiguity_score,
                config.max_pass_ambiguity_score,
                config.max_watch_ambiguity_score,
            )
            * config.ambiguity_weight
        )
        return _quantize(score)


def _candidate_reason_codes(
    candidate: CandidateDecisionResolutionSourceLatencyScoreInput,
    config: CandidateDecisionResolutionSourceLatencyScoreConfig,
    latency_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_maximum_reason(
        reasons,
        candidate.official_source_latency_minutes,
        pass_threshold=config.max_pass_official_source_latency_minutes,
        watch_threshold=config.max_watch_official_source_latency_minutes,
        watch_reason=OFFICIAL_LATENCY_WATCH_REASON,
        block_reason=OFFICIAL_LATENCY_BLOCK_REASON,
    )
    _append_maximum_reason(
        reasons,
        candidate.independent_source_latency_minutes,
        pass_threshold=config.max_pass_independent_source_latency_minutes,
        watch_threshold=config.max_watch_independent_source_latency_minutes,
        watch_reason=INDEPENDENT_LATENCY_WATCH_REASON,
        block_reason=INDEPENDENT_LATENCY_BLOCK_REASON,
    )
    _append_maximum_reason(
        reasons,
        candidate.settlement_delay_hours,
        pass_threshold=config.max_pass_settlement_delay_hours,
        watch_threshold=config.max_watch_settlement_delay_hours,
        watch_reason=SETTLEMENT_DELAY_WATCH_REASON,
        block_reason=SETTLEMENT_DELAY_BLOCK_REASON,
    )
    _append_maximum_reason(
        reasons,
        candidate.latency_variability_score,
        pass_threshold=config.max_pass_latency_variability_score,
        watch_threshold=config.max_watch_latency_variability_score,
        watch_reason=LATENCY_VARIABILITY_WATCH_REASON,
        block_reason=LATENCY_VARIABILITY_BLOCK_REASON,
    )
    _append_minimum_reason(
        reasons,
        candidate.source_reliability_score,
        pass_threshold=config.min_pass_source_reliability_score,
        watch_threshold=config.min_watch_source_reliability_score,
        watch_reason=SOURCE_RELIABILITY_WATCH_REASON,
        block_reason=SOURCE_RELIABILITY_BLOCK_REASON,
    )
    _append_maximum_reason(
        reasons,
        candidate.ambiguity_score,
        pass_threshold=config.max_pass_ambiguity_score,
        watch_threshold=config.max_watch_ambiguity_score,
        watch_reason=AMBIGUITY_WATCH_REASON,
        block_reason=AMBIGUITY_BLOCK_REASON,
    )
    if not any(reason in BLOCK_REASON_CODES for reason in reasons):
        if latency_score < config.min_watch_latency_score:
            reasons.append(LATENCY_SCORE_BLOCK_REASON)
        elif latency_score < config.min_pass_latency_score:
            reasons.append(LATENCY_SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _sort_reason_codes(tuple(reasons))


def _append_maximum_reason(
    reasons: list[str],
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_threshold:
        reasons.append(block_reason)
    elif value > pass_threshold:
        reasons.append(watch_reason)


def _append_minimum_reason(
    reasons: list[str],
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < watch_threshold:
        reasons.append(block_reason)
    elif value < pass_threshold:
        reasons.append(watch_reason)


def _lower_is_better_component(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return ONE
    if value >= watch_threshold:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(ONE - ((value - pass_threshold) / (watch_threshold - pass_threshold)))


def _higher_is_better_component(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value >= pass_threshold:
        return ONE
    if value <= watch_threshold:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit((value - watch_threshold) / (pass_threshold - watch_threshold))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _sort_reason_codes(tuple(dict.fromkeys(reason_codes)))


def _reason_code_counts(
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...],
) -> tuple[CandidateDecisionResolutionSourceLatencyReasonCodeCount, ...]:
    if not rows:
        return ()
    candidate_count = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        CandidateDecisionResolutionSourceLatencyReasonCodeCount(
            reason_code=reason_code,
            count=count,
            candidate_ratio=_quantize(count / candidate_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: _reason_code_sort_key(item[0]),
        )
    )


def _status_count(
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_latency_score(
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.latency_score for row in rows)


def _min_latency_score(
    rows: tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.latency_score for row in rows)


def _row_sort_key(
    row: CandidateDecisionResolutionSourceLatencyScoreRow,
) -> tuple[Decimal, str]:
    return (STATUS_PRIORITY[row.status], row.redacted_candidate_ref)


def _validate_config(
    config: CandidateDecisionResolutionSourceLatencyScoreConfig,
) -> None:
    if config.min_pass_latency_score < config.min_watch_latency_score:
        raise ValueError("min_pass_latency_score must be at least watch threshold")
    if (
        config.max_pass_official_source_latency_minutes
        > config.max_watch_official_source_latency_minutes
    ):
        raise ValueError(
            "max_pass_official_source_latency_minutes must not exceed watch threshold",
        )
    if (
        config.max_pass_independent_source_latency_minutes
        > config.max_watch_independent_source_latency_minutes
    ):
        raise ValueError(
            "max_pass_independent_source_latency_minutes must not exceed watch threshold",
        )
    if config.max_pass_settlement_delay_hours > config.max_watch_settlement_delay_hours:
        raise ValueError("max_pass_settlement_delay_hours must not exceed watch threshold")
    if (
        config.max_pass_latency_variability_score
        > config.max_watch_latency_variability_score
    ):
        raise ValueError(
            "max_pass_latency_variability_score must not exceed watch threshold",
        )
    if (
        config.min_pass_source_reliability_score
        < config.min_watch_source_reliability_score
    ):
        raise ValueError(
            "min_pass_source_reliability_score must be at least watch threshold",
        )
    if config.max_pass_ambiguity_score > config.max_watch_ambiguity_score:
        raise ValueError("max_pass_ambiguity_score must not exceed watch threshold")
    if (
        config.max_watch_official_source_latency_minutes
        <= config.max_pass_official_source_latency_minutes
    ):
        raise ValueError(
            "max_watch_official_source_latency_minutes must exceed pass threshold",
        )
    if (
        config.max_watch_independent_source_latency_minutes
        <= config.max_pass_independent_source_latency_minutes
    ):
        raise ValueError(
            "max_watch_independent_source_latency_minutes must exceed pass threshold",
        )
    if config.max_watch_settlement_delay_hours <= config.max_pass_settlement_delay_hours:
        raise ValueError("max_watch_settlement_delay_hours must exceed pass threshold")
    if (
        config.max_watch_latency_variability_score
        <= config.max_pass_latency_variability_score
    ):
        raise ValueError(
            "max_watch_latency_variability_score must exceed pass threshold",
        )
    if (
        config.min_pass_source_reliability_score
        <= config.min_watch_source_reliability_score
    ):
        raise ValueError(
            "min_pass_source_reliability_score must exceed watch threshold",
        )
    if config.max_watch_ambiguity_score <= config.max_pass_ambiguity_score:
        raise ValueError("max_watch_ambiguity_score must exceed pass threshold")
    weight_sum = _quantize(
        config.official_source_latency_weight
        + config.independent_source_latency_weight
        + config.settlement_delay_weight
        + config.latency_variability_weight
        + config.source_reliability_weight
        + config.ambiguity_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_report(
    report: CandidateDecisionResolutionSourceLatencyScoreReport,
) -> None:
    expected_candidate_count = _count_decimal(len(report.rows))
    if report.candidate_count != expected_candidate_count:
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_latency_score != _max_latency_score(report.rows):
        raise ValueError("max_latency_score must match rows")
    if report.min_latency_score != _min_latency_score(report.rows):
        raise ValueError("min_latency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted deterministically")


def _report_payload(
    report: CandidateDecisionResolutionSourceLatencyScoreReport,
) -> dict[str, Any]:
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(
    report: CandidateDecisionResolutionSourceLatencyScoreReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "max_latency_score": _decimal_payload(report.max_latency_score),
        "min_latency_score": _decimal_payload(report.min_latency_score),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(reason_count)
            for reason_count in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(
    row: CandidateDecisionResolutionSourceLatencyScoreRow,
) -> dict[str, Any]:
    payload = _row_payload_without_digest(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _row_payload_without_digest(
    row: CandidateDecisionResolutionSourceLatencyScoreRow,
) -> dict[str, Any]:
    return {
        "generated_at": row.generated_at.isoformat(),
        "redacted_candidate_ref": row.redacted_candidate_ref,
        "official_source_latency_minutes": _decimal_payload(
            row.official_source_latency_minutes,
        ),
        "independent_source_latency_minutes": _decimal_payload(
            row.independent_source_latency_minutes,
        ),
        "settlement_delay_hours": _decimal_payload(row.settlement_delay_hours),
        "latency_variability_score": _decimal_payload(row.latency_variability_score),
        "source_reliability_score": _decimal_payload(row.source_reliability_score),
        "ambiguity_score": _decimal_payload(row.ambiguity_score),
        "latency_score": _decimal_payload(row.latency_score),
        "status": row.status,
        "hard_blocker_codes": list(row.hard_blocker_codes),
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    reason_count: CandidateDecisionResolutionSourceLatencyReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": reason_count.reason_code,
        "count": _decimal_payload(reason_count.count),
        "candidate_ratio": _decimal_payload(reason_count.candidate_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_digest_from_values(payload: dict[str, Any]) -> str:
    return _json_sha256(payload)


def _row_digest_from_values(payload: dict[str, Any]) -> str:
    return _json_sha256(payload)


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(payload: object) -> None:
    _walk_public_payload(payload)


def _walk_public_payload(payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_public_key(key)
            _walk_public_payload(value)
        return
    if type(payload) is list:
        for value in payload:
            _walk_public_payload(value)
        return
    _reject_public_value(payload)


def _reject_public_key(key: str) -> None:
    compact_key = _compact(key)
    if key in SAFE_PUBLIC_KEYS:
        return
    if compact_key in RAW_CANDIDATE_KEY_COMPACTS:
        raise ValueError("raw candidate fields are not allowed in public payload")
    if compact_key in MARKET_KEY_COMPACTS:
        raise ValueError("market fields are not allowed in public payload")
    if compact_key in SOURCE_KEY_COMPACTS:
        raise ValueError("source references are not allowed in public payload")
    if any(term in compact_key for term in UNSAFE_KEY_COMPACTS):
        raise ValueError("unsafe live surface field in public payload")


def _reject_public_value(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) in (Decimal, datetime, float, int):
        raise ValueError("public payload numeric values must be decimal strings")
    if type(value) is not str:
        raise ValueError("public payload values must be JSON scalars")
    lowered = value.lower()
    if lowered in STATUS_ALIAS_VALUES:
        raise ValueError("public status values must be pass, watch, or block")
    if lowered.startswith("candidate_ref_"):
        _require_redacted_candidate_ref(value)
        return
    if "candidate_id" in lowered or "raw_candidate" in lowered or "candidate:" in lowered:
        raise ValueError("raw candidate values are not allowed in public payload")
    if any(term in lowered for term in UNSAFE_VALUE_TERMS):
        raise ValueError("unsafe live surface value in public payload")
    if any(term in lowered for term in SOURCE_VALUE_TERMS):
        raise ValueError("source references are not allowed in public payload")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _normalize_rows(
    value: object,
) -> tuple[CandidateDecisionResolutionSourceLatencyScoreRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not CandidateDecisionResolutionSourceLatencyScoreRow:
            raise ValueError(
                "rows must contain CandidateDecisionResolutionSourceLatencyScoreRow",
            )
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[CandidateDecisionResolutionSourceLatencyReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in value:
        if type(reason_count) is not CandidateDecisionResolutionSourceLatencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CandidateDecisionResolutionSourceLatencyReasonCodeCount",
            )
    return value


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    for reason_code in value:
        _require_reason_code(reason_code)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return _sort_reason_codes(value)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_code_sort_key))


def _reason_code_sort_key(reason_code: str) -> tuple[Decimal, str]:
    try:
        priority = Decimal(str(REASON_CODE_SEQUENCE.index(reason_code)))
    except ValueError:
        priority = Decimal(str(len(REASON_CODE_SEQUENCE)))
    return (priority, reason_code)


def _require_reason_code(value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("reason_code must be canonical text")
    lowered = value.lower()
    if lowered in STATUS_ALIAS_VALUES:
        raise ValueError("reason_code must not be a status alias")
    return value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal = _normalize_nonnegative_decimal(name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal


def _normalize_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if not decimal.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(decimal)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(str(value)))


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be a Decimal")
    return str(_quantize(value))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_redacted_candidate_ref(value: object) -> str:
    if type(value) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    if len(value) != len("candidate_ref_") + 64:
        raise ValueError("raw candidate reference is not allowed")
    if not value.startswith("candidate_ref_"):
        raise ValueError("raw candidate reference is not allowed")
    suffix = value[len("candidate_ref_") :]
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError("raw candidate reference is not allowed")
    return value


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be canonical text")


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_paper_only_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _compact(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_RESOLUTION_SOURCE_LATENCY_SCORE_CONFIG_VERSION",
    "CandidateDecisionResolutionSourceLatencyReasonCodeCount",
    "CandidateDecisionResolutionSourceLatencyScoreConfig",
    "CandidateDecisionResolutionSourceLatencyScoreInput",
    "CandidateDecisionResolutionSourceLatencyScoreReport",
    "CandidateDecisionResolutionSourceLatencyScoreRow",
    "build_candidate_decision_resolution_source_latency_score_report",
    "candidate_decision_resolution_source_latency_score_payload",
    "validate_candidate_decision_resolution_source_latency_score_public_payload",
    "validate_candidate_decision_resolution_source_latency_score_report",
)
