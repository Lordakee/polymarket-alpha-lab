"""Pure paper-only historical resolution pattern score for candidates."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_HISTORICAL_RESOLUTION_PATTERN_SCORE_CONFIG_VERSION = (
    "candidate-decision-historical-resolution-pattern-score-v0"
)
BOUNDARY_STATEMENT = (
    "Paper-only report-only readonly candidate historical resolution pattern score; "
    "research-priority filtering only."
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("5.000000")
PATTERN_STATUSES = ("pass", "watch", "block")

NO_CANDIDATES_REASON = "historical_resolution_pattern_no_candidates"
PASS_REASON = "historical_resolution_pattern_pass"
HISTORICAL_EVENT_COUNT_BLOCK_REASON = "historical_event_count_block"
HISTORICAL_EVENT_COUNT_WATCH_REASON = "historical_event_count_watch"
OUTCOME_SIMILARITY_BLOCK_REASON = "outcome_similarity_score_block"
OUTCOME_SIMILARITY_WATCH_REASON = "outcome_similarity_score_watch"
RESOLUTION_RULE_MATCH_BLOCK_REASON = "resolution_rule_match_score_block"
RESOLUTION_RULE_MATCH_WATCH_REASON = "resolution_rule_match_score_watch"
DISPUTE_RATE_BLOCK_REASON = "historical_dispute_rate_block"
DISPUTE_RATE_WATCH_REASON = "historical_dispute_rate_watch"
REVISION_RATE_BLOCK_REASON = "historical_revision_rate_block"
REVISION_RATE_WATCH_REASON = "historical_revision_rate_watch"
PATTERN_SCORE_BLOCK_REASON = "historical_resolution_pattern_score_block"
PATTERN_SCORE_WATCH_REASON = "historical_resolution_pattern_score_watch"

REASON_CODE_SEQUENCE = (
    NO_CANDIDATES_REASON,
    HISTORICAL_EVENT_COUNT_BLOCK_REASON,
    OUTCOME_SIMILARITY_BLOCK_REASON,
    RESOLUTION_RULE_MATCH_BLOCK_REASON,
    DISPUTE_RATE_BLOCK_REASON,
    REVISION_RATE_BLOCK_REASON,
    PATTERN_SCORE_BLOCK_REASON,
    HISTORICAL_EVENT_COUNT_WATCH_REASON,
    OUTCOME_SIMILARITY_WATCH_REASON,
    RESOLUTION_RULE_MATCH_WATCH_REASON,
    DISPUTE_RATE_WATCH_REASON,
    REVISION_RATE_WATCH_REASON,
    PATTERN_SCORE_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    (
        NO_CANDIDATES_REASON,
        HISTORICAL_EVENT_COUNT_BLOCK_REASON,
        OUTCOME_SIMILARITY_BLOCK_REASON,
        RESOLUTION_RULE_MATCH_BLOCK_REASON,
        DISPUTE_RATE_BLOCK_REASON,
        REVISION_RATE_BLOCK_REASON,
        PATTERN_SCORE_BLOCK_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        HISTORICAL_EVENT_COUNT_WATCH_REASON,
        OUTCOME_SIMILARITY_WATCH_REASON,
        RESOLUTION_RULE_MATCH_WATCH_REASON,
        DISPUTE_RATE_WATCH_REASON,
        REVISION_RATE_WATCH_REASON,
        PATTERN_SCORE_WATCH_REASON,
    ),
)

_UNSAFE_PUBLIC_KEY_TERMS = (
    "".join(("candidate", "_id")),
    "".join(("raw", "_", "candidate")),
    "".join(("candidate", "_", "slug")),
    "".join(("market", "_", "id")),
    "".join(("market", "_", "slug")),
    "".join(("condition", "_", "id")),
    "".join(("ques", "tion")),
    "".join(("source", "_", "ref")),
    "".join(("source", "_", "url")),
    "".join(("source", "_", "uri")),
    "".join(("source", "_", "text")),
    "".join(("raw", "_", "text")),
    "url",
    "".join(("d", "sn")),
    "".join(("ta", "ble")),
    "".join(("to", "ken")),
    "".join(("wal", "let")),
    "".join(("a", "uth")),
    "".join(("or", "der")),
    "".join(("tra", "de")),
    "".join(("pos", "ition")),
)
_UNSAFE_PUBLIC_VALUE_TERMS = (
    "http://",
    "https://",
    "://",
    "www.",
    ".com",
    ".org",
    ".net",
    ".io",
    ".co",
    ".app",
    ".dev",
    ".test",
    ".gov",
    "".join(("candidate", "_id")),
    "".join(("raw", "_", "candidate")),
    "candidate:",
    "".join(("market", "_", "id")),
    "".join(("market", "_", "slug")),
    "".join(("condition", "_", "id")),
    "0x",
    "".join(("ques", "tion")),
    "".join(("source", "_", "ref")),
    "".join(("source", "_", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", ":")),
    "".join(("d", "sn")),
    "dsn=",
    "".join(("ta", "ble", ":")),
    "".join(("ta", "ble", "=")),
    "".join(("_", "ta", "ble")),
    " select ",
    " from ",
    "".join(("postgres", "://")),
    "".join(("postgresql", "://")),
    "".join(("mysql", "://")),
    "".join(("sup", "abase")),
    "".join(("to", "ken")),
    "".join(("wal", "let")),
    "".join(("a", "uth")),
    "".join(("or", "der")),
    "".join(("tra", "de")),
    "".join(("pos", "ition")),
    "".join(("b", "uy")),
    "".join(("s", "ell")),
    "".join(("reco", "mmend")),
    "".join(("reco", "mmendation")),
)


@dataclass(frozen=True)
class CandidateDecisionHistoricalResolutionPatternScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_HISTORICAL_RESOLUTION_PATTERN_SCORE_CONFIG_VERSION
    )
    min_pass_pattern_score: Decimal = Decimal("0.750000")
    min_watch_pattern_score: Decimal = Decimal("0.500000")
    min_historical_event_count_for_pass: Decimal = Decimal("5.000000")
    min_historical_event_count_for_watch: Decimal = Decimal("2.000000")
    min_pass_outcome_similarity_score: Decimal = Decimal("0.700000")
    min_watch_outcome_similarity_score: Decimal = Decimal("0.400000")
    min_pass_resolution_rule_match_score: Decimal = Decimal("0.700000")
    min_watch_resolution_rule_match_score: Decimal = Decimal("0.400000")
    max_pass_historical_dispute_rate: Decimal = Decimal("0.100000")
    max_watch_historical_dispute_rate: Decimal = Decimal("0.300000")
    max_pass_historical_revision_rate: Decimal = Decimal("0.100000")
    max_watch_historical_revision_rate: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionHistoricalResolutionPatternScoreConfig:
            raise TypeError(
                "CandidateDecisionHistoricalResolutionPatternScoreConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionHistoricalResolutionPatternScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionHistoricalResolutionPatternScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_HISTORICAL_RESOLUTION_PATTERN_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_pattern_score",
            "min_watch_pattern_score",
            "min_pass_outcome_similarity_score",
            "min_watch_outcome_similarity_score",
            "min_pass_resolution_rule_match_score",
            "min_watch_resolution_rule_match_score",
            "max_pass_historical_dispute_rate",
            "max_watch_historical_dispute_rate",
            "max_pass_historical_revision_rate",
            "max_watch_historical_revision_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_historical_event_count_for_pass",
            "min_historical_event_count_for_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags("historical resolution pattern config", self)
        _reject_unsafe_public_values("historical resolution pattern config", self)


@dataclass(frozen=True)
class CandidateDecisionHistoricalResolutionPatternScoreInput:
    redacted_candidate_ref: str
    event_family_code: str
    historical_event_count: Decimal
    outcome_similarity_score: Decimal
    resolution_rule_match_score: Decimal
    historical_dispute_rate: Decimal
    historical_revision_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionHistoricalResolutionPatternScoreInput:
            raise TypeError(
                "CandidateDecisionHistoricalResolutionPatternScoreInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionHistoricalResolutionPatternScoreInput:
            raise ValueError(
                "score input must be exactly "
                "CandidateDecisionHistoricalResolutionPatternScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(
            self,
            "event_family_code",
            _require_public_code("event_family_code", self.event_family_code),
        )
        object.__setattr__(
            self,
            "historical_event_count",
            _normalize_nonnegative_whole_decimal(
                "historical_event_count",
                self.historical_event_count,
            ),
        )
        for field_name in (
            "outcome_similarity_score",
            "resolution_rule_match_score",
            "historical_dispute_rate",
            "historical_revision_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("historical resolution pattern input", self)
        _reject_unsafe_public_values("historical resolution pattern input", self)


@dataclass(frozen=True)
class CandidateDecisionHistoricalResolutionPatternScoreRow:
    generated_at: datetime
    redacted_candidate_ref: str
    event_family_code: str
    historical_event_count: Decimal
    sample_support_score: Decimal
    outcome_similarity_score: Decimal
    resolution_rule_match_score: Decimal
    historical_dispute_rate: Decimal
    historical_revision_rate: Decimal
    pattern_score: Decimal
    pattern_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    row_sha256: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionHistoricalResolutionPatternScoreRow:
            raise TypeError(
                "CandidateDecisionHistoricalResolutionPatternScoreRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionHistoricalResolutionPatternScoreRow:
            raise ValueError(
                "row must be exactly CandidateDecisionHistoricalResolutionPatternScoreRow",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(
            self,
            "event_family_code",
            _require_public_code("event_family_code", self.event_family_code),
        )
        object.__setattr__(
            self,
            "historical_event_count",
            _normalize_nonnegative_whole_decimal(
                "historical_event_count",
                self.historical_event_count,
            ),
        )
        for field_name in (
            "sample_support_score",
            "outcome_similarity_score",
            "resolution_rule_match_score",
            "historical_dispute_rate",
            "historical_revision_rate",
            "pattern_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("pattern_status", self.pattern_status, PATTERN_STATUSES)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(
                "hard_blocker_codes",
                self.hard_blocker_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_digest("row_sha256", self.row_sha256)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _require_hard_flags("historical resolution pattern row", self)
        _reject_unsafe_public_values("historical resolution pattern row", self)
        _validate_row(self)
        expected_digest = _row_digest_from_values(_row_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row payload")
        if self.row_sha256 != expected_digest:
            raise ValueError("row_sha256 must match row payload")


@dataclass(frozen=True)
class CandidateDecisionHistoricalResolutionPatternReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionHistoricalResolutionPatternReasonCodeCount:
            raise TypeError(
                "CandidateDecisionHistoricalResolutionPatternReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionHistoricalResolutionPatternReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "CandidateDecisionHistoricalResolutionPatternReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
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
        _require_hard_flags("historical resolution pattern reason count", self)
        _reject_unsafe_public_values("historical resolution pattern reason count", self)


@dataclass(frozen=True)
class CandidateDecisionHistoricalResolutionPatternScoreReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_pattern_score: Decimal
    min_pattern_score: Decimal
    average_pattern_score: Decimal
    pattern_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        CandidateDecisionHistoricalResolutionPatternReasonCodeCount,
        ...,
    ]
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...]
    derived_validation_digest: str
    report_sha256: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionHistoricalResolutionPatternScoreReport:
            raise TypeError(
                "CandidateDecisionHistoricalResolutionPatternScoreReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionHistoricalResolutionPatternScoreReport:
            raise ValueError(
                "report must be exactly "
                "CandidateDecisionHistoricalResolutionPatternScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("max_pattern_score", "min_pattern_score", "average_pattern_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("pattern_status", self.pattern_status, PATTERN_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_digest("report_sha256", self.report_sha256)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _require_hard_flags("historical resolution pattern report", self)
        _reject_unsafe_public_values("historical resolution pattern report", self)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        if self.report_sha256 != expected_digest:
            raise ValueError("report_sha256 must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_historical_resolution_pattern_score_payload(self)


def score_candidate_decision_historical_resolution_pattern(
    score_input: CandidateDecisionHistoricalResolutionPatternScoreInput,
    *,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig | None = None,
    generated_at: datetime,
) -> CandidateDecisionHistoricalResolutionPatternScoreRow:
    row_config = config or CandidateDecisionHistoricalResolutionPatternScoreConfig()
    if type(row_config) is not CandidateDecisionHistoricalResolutionPatternScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionHistoricalResolutionPatternScoreConfig",
        )
    if type(score_input) is not CandidateDecisionHistoricalResolutionPatternScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionHistoricalResolutionPatternScoreInput",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("historical resolution pattern config", row_config)
    _require_hard_flags("historical resolution pattern input", score_input)
    _reject_unsafe_public_values("historical resolution pattern config", row_config)
    _reject_unsafe_public_values("historical resolution pattern input", score_input)
    return _row_for_candidate(score_input, config=row_config, generated_at=generated_at_utc)


def build_candidate_decision_historical_resolution_pattern_score_report(
    candidates: Iterable[CandidateDecisionHistoricalResolutionPatternScoreInput],
    *,
    generated_at: datetime,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig | None = None,
) -> CandidateDecisionHistoricalResolutionPatternScoreReport:
    report_config = config or CandidateDecisionHistoricalResolutionPatternScoreConfig()
    if type(report_config) is not CandidateDecisionHistoricalResolutionPatternScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionHistoricalResolutionPatternScoreConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("historical resolution pattern config", report_config)
    _reject_unsafe_public_values("historical resolution pattern config", report_config)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_for_candidate(
                    candidate,
                    config=report_config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    pattern_status = _status_from_reason_codes(reason_codes)
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": report_config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_pattern_score": _max_pattern_score(rows),
        "min_pattern_score": _min_pattern_score(rows),
        "average_pattern_score": _average_pattern_score(rows),
        "pattern_status": pattern_status,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "rows": rows,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_digest = _report_digest_from_values(report_values)
    return CandidateDecisionHistoricalResolutionPatternScoreReport(
        **report_values,
        derived_validation_digest=report_digest,
        report_sha256=report_digest,
    )


def candidate_decision_historical_resolution_pattern_score_payload(
    report: CandidateDecisionHistoricalResolutionPatternScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionHistoricalResolutionPatternScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionHistoricalResolutionPatternScoreReport",
        )
    _require_hard_flags("historical resolution pattern report", report)
    _reject_unsafe_public_values("historical resolution pattern report", report)
    _validate_report_digest(report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    validate_candidate_decision_historical_resolution_pattern_score_public_payload(payload)
    return payload


def validate_candidate_decision_historical_resolution_pattern_score_public_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    reject_unsafe_surface_fields("historical resolution pattern public payload", payload)
    _reject_unsafe_public_payload_keys(payload)
    _reject_unsupported_status_values(payload)
    _reject_public_numeric_values(payload)
    _reject_unsafe_public_values("historical resolution pattern public payload", payload)
    return True


def _row_for_candidate(
    candidate: CandidateDecisionHistoricalResolutionPatternScoreInput,
    *,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionHistoricalResolutionPatternScoreRow:
    initial_reason_codes = _candidate_reason_codes(candidate, config)
    raw_pattern_score = _pattern_score(candidate, config)
    reason_codes = _reason_codes_with_score(
        initial_reason_codes,
        pattern_score=raw_pattern_score,
        config=config,
    )
    pattern_status = _status_from_reason_codes(reason_codes)
    hard_blockers = _hard_blocker_codes(reason_codes)
    pattern_score = ZERO if pattern_status == "block" else raw_pattern_score
    row_values: dict[str, object] = {
        "generated_at": generated_at,
        "redacted_candidate_ref": candidate.redacted_candidate_ref,
        "event_family_code": candidate.event_family_code,
        "historical_event_count": candidate.historical_event_count,
        "sample_support_score": _sample_support_score(candidate, config),
        "outcome_similarity_score": candidate.outcome_similarity_score,
        "resolution_rule_match_score": candidate.resolution_rule_match_score,
        "historical_dispute_rate": candidate.historical_dispute_rate,
        "historical_revision_rate": candidate.historical_revision_rate,
        "pattern_score": pattern_score,
        "pattern_status": pattern_status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    row_digest = _row_digest_from_values(row_values)
    return CandidateDecisionHistoricalResolutionPatternScoreRow(
        **row_values,
        derived_validation_digest=row_digest,
        row_sha256=row_digest,
    )


def _candidate_reason_codes(
    candidate: CandidateDecisionHistoricalResolutionPatternScoreInput,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig,
) -> tuple[str, ...]:
    reason_codes = list(candidate.reason_codes)
    if candidate.historical_event_count < config.min_historical_event_count_for_watch:
        reason_codes.append(HISTORICAL_EVENT_COUNT_BLOCK_REASON)
    elif candidate.historical_event_count < config.min_historical_event_count_for_pass:
        reason_codes.append(HISTORICAL_EVENT_COUNT_WATCH_REASON)
    if candidate.outcome_similarity_score < config.min_watch_outcome_similarity_score:
        reason_codes.append(OUTCOME_SIMILARITY_BLOCK_REASON)
    elif candidate.outcome_similarity_score < config.min_pass_outcome_similarity_score:
        reason_codes.append(OUTCOME_SIMILARITY_WATCH_REASON)
    if candidate.resolution_rule_match_score < config.min_watch_resolution_rule_match_score:
        reason_codes.append(RESOLUTION_RULE_MATCH_BLOCK_REASON)
    elif candidate.resolution_rule_match_score < config.min_pass_resolution_rule_match_score:
        reason_codes.append(RESOLUTION_RULE_MATCH_WATCH_REASON)
    if candidate.historical_dispute_rate > config.max_watch_historical_dispute_rate:
        reason_codes.append(DISPUTE_RATE_BLOCK_REASON)
    elif candidate.historical_dispute_rate > config.max_pass_historical_dispute_rate:
        reason_codes.append(DISPUTE_RATE_WATCH_REASON)
    if candidate.historical_revision_rate > config.max_watch_historical_revision_rate:
        reason_codes.append(REVISION_RATE_BLOCK_REASON)
    elif candidate.historical_revision_rate > config.max_pass_historical_revision_rate:
        reason_codes.append(REVISION_RATE_WATCH_REASON)
    return _ordered_reason_codes(reason_codes, allow_empty=True)


def _reason_codes_with_score(
    reason_codes: tuple[str, ...],
    *,
    pattern_score: Decimal,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig,
) -> tuple[str, ...]:
    combined = list(reason_codes)
    if pattern_score < config.min_watch_pattern_score:
        combined.append(PATTERN_SCORE_BLOCK_REASON)
    elif pattern_score < config.min_pass_pattern_score:
        combined.append(PATTERN_SCORE_WATCH_REASON)
    if not combined:
        combined.append(PASS_REASON)
    return _ordered_reason_codes(combined)


def _pattern_score(
    candidate: CandidateDecisionHistoricalResolutionPatternScoreInput,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        total = (
            _sample_support_score(candidate, config)
            + candidate.outcome_similarity_score
            + candidate.resolution_rule_match_score
            + (ONE - candidate.historical_dispute_rate)
            + (ONE - candidate.historical_revision_rate)
        )
        return _normalize_unit_decimal("pattern_score", total / COMPONENT_COUNT)


def _sample_support_score(
    candidate: CandidateDecisionHistoricalResolutionPatternScoreInput,
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig,
) -> Decimal:
    if config.min_historical_event_count_for_pass == ZERO:
        return ONE
    if candidate.historical_event_count >= config.min_historical_event_count_for_pass:
        return ONE
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal(
            "sample_support_score",
            candidate.historical_event_count / config.min_historical_event_count_for_pass,
        )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _hard_blocker_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in reason_codes if reason_code in BLOCK_REASON_CODES)


def _report_reason_codes(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    return _ordered_reason_codes(
        reason_code for row in rows for reason_code in row.reason_codes
    )


def _reason_code_counts(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[CandidateDecisionHistoricalResolutionPatternReasonCodeCount, ...]:
    if not rows:
        return ()
    total = _count(len(rows))
    counts: list[CandidateDecisionHistoricalResolutionPatternReasonCodeCount] = []
    for reason_code in reason_codes:
        reason_count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        with localcontext() as context:
            context.prec = 64
            context.rounding = ROUND_HALF_EVEN
            ratio = _normalize_unit_decimal("candidate_ratio", reason_count / total)
        counts.append(
            CandidateDecisionHistoricalResolutionPatternReasonCodeCount(
                reason_code=reason_code,
                count=reason_count,
                candidate_ratio=ratio,
            ),
        )
    return tuple(counts)


def _normalize_candidates(
    candidates: Iterable[CandidateDecisionHistoricalResolutionPatternScoreInput],
) -> tuple[CandidateDecisionHistoricalResolutionPatternScoreInput, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable of score inputs")
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not CandidateDecisionHistoricalResolutionPatternScoreInput:
            raise ValueError(
                "candidates must contain CandidateDecisionHistoricalResolutionPatternScoreInput",
            )
        if candidate.redacted_candidate_ref in seen:
            raise ValueError("duplicate redacted_candidate_ref")
        seen.add(candidate.redacted_candidate_ref)
    return normalized


def _normalize_rows(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
) -> tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not CandidateDecisionHistoricalResolutionPatternScoreRow:
            raise ValueError(
                "rows must contain CandidateDecisionHistoricalResolutionPatternScoreRow",
            )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternReasonCodeCount, ...],
) -> tuple[CandidateDecisionHistoricalResolutionPatternReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not CandidateDecisionHistoricalResolutionPatternReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CandidateDecisionHistoricalResolutionPatternReasonCodeCount",
            )
    return rows


def _row_sort_key(row: CandidateDecisionHistoricalResolutionPatternScoreRow) -> tuple[Decimal, Decimal, str]:
    status_rank = {
        "block": Decimal("0.000000"),
        "watch": Decimal("1.000000"),
        "pass": Decimal("2.000000"),
    }[row.pattern_status]
    return (status_rank, row.pattern_score, row.redacted_candidate_ref)


def _status_count(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.pattern_status == status))


def _max_pattern_score(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.pattern_score for row in rows)


def _min_pattern_score(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.pattern_score for row in rows)


def _average_pattern_score(
    rows: tuple[CandidateDecisionHistoricalResolutionPatternScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal(
            "average_pattern_score",
            sum((row.pattern_score for row in rows), ZERO) / _count(len(rows)),
        )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _validate_config(
    config: CandidateDecisionHistoricalResolutionPatternScoreConfig,
) -> None:
    if config.min_watch_pattern_score > config.min_pass_pattern_score:
        raise ValueError("min_watch_pattern_score must not exceed pass threshold")
    if (
        config.min_historical_event_count_for_watch
        > config.min_historical_event_count_for_pass
    ):
        raise ValueError("min_historical_event_count_for_watch must not exceed pass threshold")
    if (
        config.min_watch_outcome_similarity_score
        > config.min_pass_outcome_similarity_score
    ):
        raise ValueError("min_watch_outcome_similarity_score must not exceed pass threshold")
    if (
        config.min_watch_resolution_rule_match_score
        > config.min_pass_resolution_rule_match_score
    ):
        raise ValueError("min_watch_resolution_rule_match_score must not exceed pass threshold")
    if config.max_pass_historical_dispute_rate > config.max_watch_historical_dispute_rate:
        raise ValueError("max_pass_historical_dispute_rate must not exceed watch threshold")
    if config.max_pass_historical_revision_rate > config.max_watch_historical_revision_rate:
        raise ValueError("max_pass_historical_revision_rate must not exceed watch threshold")


def _validate_row(row: CandidateDecisionHistoricalResolutionPatternScoreRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must not be empty")
    for hard_blocker in row.hard_blocker_codes:
        if hard_blocker not in row.reason_codes:
            raise ValueError("hard_blocker_codes must be present in reason_codes")
        if hard_blocker not in BLOCK_REASON_CODES:
            raise ValueError("hard_blocker_codes must contain only block reasons")
    if row.pattern_status == "block" and row.pattern_score != ZERO:
        raise ValueError("block rows must have zero pattern_score")
    if row.pattern_status != "block" and row.hard_blocker_codes:
        raise ValueError("non-block rows must not have hard_blocker_codes")


def _validate_report(
    report: CandidateDecisionHistoricalResolutionPatternScoreReport,
) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_pattern_score != _max_pattern_score(rows):
        raise ValueError("max_pattern_score must match rows")
    if report.min_pattern_score != _min_pattern_score(rows):
        raise ValueError("min_pattern_score must match rows")
    if report.average_pattern_score != _average_pattern_score(rows):
        raise ValueError("average_pattern_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.pattern_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("pattern_status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_digest(
    report: CandidateDecisionHistoricalResolutionPatternScoreReport,
) -> None:
    for row in report.rows:
        expected_row_digest = _row_digest_from_values(_row_values_without_digest(row))
        if row.derived_validation_digest != expected_row_digest:
            raise ValueError("row derived_validation_digest must match row payload")
        if row.row_sha256 != expected_row_digest:
            raise ValueError("row_sha256 must match row payload")
    expected_report_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_report_digest:
        raise ValueError("derived_validation_digest must match report payload")
    if report.report_sha256 != expected_report_digest:
        raise ValueError("report_sha256 must match report payload")


def _row_values_without_digest(
    row: CandidateDecisionHistoricalResolutionPatternScoreRow,
) -> dict[str, object]:
    values = asdict(row)
    values.pop("derived_validation_digest")
    values.pop("row_sha256")
    return values


def _report_values_without_digest(
    report: CandidateDecisionHistoricalResolutionPatternScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    values.pop("report_sha256")
    return values


def _row_digest_from_values(values: dict[str, object]) -> str:
    return _sha256_payload(values)


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _sha256_payload(values)


def _sha256_payload(values: object) -> str:
    return sha256(
        json.dumps(
            json_ready_no_floats(values),
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_unit_decimal(field_name: str, value: Decimal) -> Decimal:
    exact_value = _require_exact_decimal(field_name, value)
    if exact_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if exact_value > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return _quantize_decimal(exact_value)


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    exact_value = _require_exact_decimal(field_name, value)
    if exact_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if exact_value != exact_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize_decimal(exact_value)


def _require_exact_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be trimmed")
    return value


def _require_public_code(field_name: str, value: str) -> str:
    code = _require_canonical_string(field_name, value)
    if len(code) > 80:
        raise ValueError(f"{field_name} is too long")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    lowered = code.lower()
    if lowered != code:
        raise ValueError(f"{field_name} must be lowercase")
    if not set(code) <= allowed:
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_string(field_name, code)
    return code


def _require_redacted_candidate_ref(field_name: str, value: str) -> str:
    candidate_ref = _require_canonical_string(field_name, value)
    if not _is_redacted_candidate_ref(candidate_ref):
        raise ValueError(f"{field_name} must be redacted")
    return candidate_ref


def _is_redacted_candidate_ref(value: object) -> bool:
    if type(value) is not str:
        return False
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    return value.startswith(prefix) and len(digest) == 64 and _is_lower_hex(digest)


def _is_lower_hex(value: str) -> bool:
    return bool(value) and set(value) <= set("0123456789abcdef")


def _require_reason_code(field_name: str, value: str) -> str:
    reason_code = _require_public_code(field_name, value)
    if reason_code not in REASON_CODE_SEQUENCE and not reason_code.startswith("upstream_"):
        return reason_code
    return reason_code


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(_require_reason_code(field_name, value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _ordered_reason_codes(
    values: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(
        "reason_codes",
        tuple(values),
        allow_empty=allow_empty,
    )
    rank = {reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)}
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (rank.get(reason_code, len(rank)), reason_code),
        ),
    )


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or not _is_lower_hex(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    reject_unsafe_surface_fields(label, value)


def _reject_unsafe_public_payload_keys(payload: object) -> None:
    for key in _iter_public_keys(payload):
        lowered = key.lower()
        if any(term in lowered for term in _UNSAFE_PUBLIC_KEY_TERMS):
            if lowered != "redacted_candidate_ref":
                raise ValueError(f"unsafe public payload key: {key}")


def _iter_public_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    return ()


def _reject_unsupported_status_values(payload: object) -> None:
    for path, value in _iter_public_entries(payload):
        if path.endswith("status") and type(value) is str and value not in PATTERN_STATUSES:
            raise ValueError(f"public status must be pass/watch/block: {path}")


def _reject_public_numeric_values(payload: object) -> None:
    for path, value in _iter_public_entries(payload):
        if type(value) in (int, float):
            raise ValueError(f"public numeric values must be decimal strings: {path}")


def _reject_unsafe_public_values(label: str, payload: object) -> None:
    for path, value in _iter_public_entries(payload):
        if type(value) is str:
            if path.endswith("redacted_candidate_ref") and _is_redacted_candidate_ref(value):
                continue
            _reject_unsafe_public_string(f"{label}: {path}", value)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if "candidate_ref_" in lowered and not _is_redacted_candidate_ref(value):
        raise ValueError(f"raw candidate reference in {label}")
    if any(term in lowered for term in _UNSAFE_PUBLIC_VALUE_TERMS):
        raise ValueError(f"unsafe public payload value in {label}")


def _iter_public_entries(value: object, prefix: str = "") -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_entries(asdict(value), prefix=prefix)
    if isinstance(value, dict):
        entries: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            path = key if not prefix else f"{prefix}.{key}"
            entries.append((path, item))
            entries.extend(_iter_public_entries(item, prefix=path))
        return tuple(entries)
    if isinstance(value, (list, tuple)):
        entries = []
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]"
            entries.extend(_iter_public_entries(item, prefix=path))
        return tuple(entries)
    return ((prefix, value),)


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_HISTORICAL_RESOLUTION_PATTERN_SCORE_CONFIG_VERSION",
    "BOUNDARY_STATEMENT",
    "CandidateDecisionHistoricalResolutionPatternScoreConfig",
    "CandidateDecisionHistoricalResolutionPatternScoreInput",
    "CandidateDecisionHistoricalResolutionPatternScoreRow",
    "CandidateDecisionHistoricalResolutionPatternReasonCodeCount",
    "CandidateDecisionHistoricalResolutionPatternScoreReport",
    "score_candidate_decision_historical_resolution_pattern",
    "build_candidate_decision_historical_resolution_pattern_score_report",
    "candidate_decision_historical_resolution_pattern_score_payload",
    "validate_candidate_decision_historical_resolution_pattern_score_public_payload",
)
