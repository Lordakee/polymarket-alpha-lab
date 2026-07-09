"""Readonly research source authority scrapling consensus decay report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_CONSENSUS_DECAY_CONFIG_VERSION = (
    "research-source-authority-scrapling-consensus-decay-v0"
)

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STATUSES = ("pass", "watch", "block")
STATUS_SORT_ORDER = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}

NO_OBSERVATIONS_REASON = "no_scrapling_consensus_observations"
LOW_AUTHORITY_REASON = "source_authority_below_watch_threshold"
INSUFFICIENT_CONSENSUS_REASON = "insufficient_independent_consensus"
STALE_OBSERVATIONS_REASON = "scrapling_consensus_observations_stale"
SCORE_BELOW_WATCH_REASON = "scrapling_consensus_decay_below_watch_threshold"
BLOCK_REASON = "scrapling_consensus_decay_block"
WATCH_REASON = "scrapling_consensus_decay_watch"
PASS_REASON = "scrapling_consensus_decay_pass"

ROW_REASON_CODES = (
    LOW_AUTHORITY_REASON,
    INSUFFICIENT_CONSENSUS_REASON,
    STALE_OBSERVATIONS_REASON,
    SCORE_BELOW_WATCH_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    NO_OBSERVATIONS_REASON,
    LOW_AUTHORITY_REASON,
    INSUFFICIENT_CONSENSUS_REASON,
    STALE_OBSERVATIONS_REASON,
    SCORE_BELOW_WATCH_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "fresh_age_seconds",
        "stale_age_seconds",
        "min_consensus_source_family_count",
        "pass_score_threshold",
        "watch_score_threshold",
        "authority_weight",
        "consensus_weight",
        "recency_weight",
        "candidate_count",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_scrapling_consensus_decay_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "candidate_digest",
        "evidence_count",
        "source_count",
        "source_family_count",
        "latest_observed_at",
        "latest_source_age_seconds",
        "average_authority_score",
        "consensus_score",
        "recency_score",
        "scrapling_consensus_decay_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PAYLOAD_KEYS = frozenset(
    ("reason_code", "count", "paper_only", "report_only", "readonly"),
)

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "account",
        "api_key",
        "authorization",
        "balance",
        "broker",
        "cancel",
        "client_secret",
        "database",
        "dsn",
        "exchange_mutation",
        "live",
        "market_id",
        "market_slug",
        "oauth",
        "order",
        "position",
        "private_key",
        "question",
        "recommendation",
        "secret",
        "signing",
        "sizing",
        "source_text",
        "source_url",
        "submit",
        "table_name",
        "token",
        "trade",
        "trading",
        "wallet",
    ),
)
UNSAFE_PRIVATE_REFERENCE_FRAGMENTS = UNSAFE_PUBLIC_FRAGMENTS | frozenset(
    ("://", "\n", "\r", "\t"),
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_CONSENSUS_DECAY_CONFIG_VERSION",
    "ResearchSourceAuthorityScraplingConsensusDecayConfig",
    "ResearchSourceAuthorityScraplingConsensusDecayObservation",
    "ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount",
    "ResearchSourceAuthorityScraplingConsensusDecayReport",
    "ResearchSourceAuthorityScraplingConsensusDecayRow",
    "build_research_source_authority_scrapling_consensus_decay_report",
    "research_source_authority_scrapling_consensus_decay_report_payload",
    "validate_research_source_authority_scrapling_consensus_decay_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingConsensusDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_CONSENSUS_DECAY_CONFIG_VERSION
    )
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    min_consensus_source_family_count: Decimal = Decimal("2.000000")
    pass_score_threshold: Decimal = Decimal("0.700000")
    watch_score_threshold: Decimal = Decimal("0.400000")
    authority_weight: Decimal = Decimal("0.450000")
    consensus_weight: Decimal = Decimal("0.350000")
    recency_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityScraplingConsensusDecayConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_consensus_source_family_count",
            _require_positive_whole_decimal(
                "min_consensus_source_family_count",
                self.min_consensus_source_family_count,
            ),
        )
        for field_name in ("pass_score_threshold", "watch_score_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("authority_weight", "consensus_weight", "recency_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        if self.pass_score_threshold <= self.watch_score_threshold:
            raise ValueError("pass_score_threshold must exceed watch_score_threshold")
        if (
            self.authority_weight + self.consensus_weight + self.recency_weight
        ) != ONE:
            raise ValueError("authority_weight, consensus_weight, and recency_weight must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingConsensusDecayObservation:
    candidate_reference: str
    source_reference: str
    source_family: str
    authority_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityScraplingConsensusDecayObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "candidate_reference",
            _require_private_reference("candidate_reference", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "source_reference",
            _require_private_reference("source_reference", self.source_reference),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_source_family("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "authority_score",
            _require_probability_decimal("authority_score", self.authority_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingConsensusDecayRow:
    candidate_digest: str
    evidence_count: Decimal
    source_count: Decimal
    source_family_count: Decimal
    latest_observed_at: datetime
    latest_source_age_seconds: Decimal
    average_authority_score: Decimal
    consensus_score: Decimal
    recency_score: Decimal
    scrapling_consensus_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityScraplingConsensusDecayRow, "row")
        object.__setattr__(
            self,
            "candidate_digest",
            _require_digest_reference("candidate_digest", self.candidate_digest),
        )
        for field_name in ("evidence_count", "source_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "average_authority_score",
            "consensus_score",
            "recency_score",
            "scrapling_consensus_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_known_value("reason_code", self.reason_code, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingConsensusDecayReport:
    generated_at: datetime
    config_version: str
    fresh_age_seconds: Decimal
    stale_age_seconds: Decimal
    min_consensus_source_family_count: Decimal
    pass_score_threshold: Decimal
    watch_score_threshold: Decimal
    authority_weight: Decimal
    consensus_weight: Decimal
    recency_weight: Decimal
    candidate_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_scrapling_consensus_decay_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityScraplingConsensusDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_consensus_source_family_count",
            _require_positive_whole_decimal(
                "min_consensus_source_family_count",
                self.min_consensus_source_family_count,
            ),
        )
        for field_name in (
            "pass_score_threshold",
            "watch_score_threshold",
            "authority_weight",
            "consensus_weight",
            "recency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "candidate_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_scrapling_consensus_decay_score",
            _require_optional_probability_decimal(
                "average_scrapling_consensus_decay_score",
                self.average_scrapling_consensus_decay_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_source_authority_scrapling_consensus_decay_report(
    observations: list[ResearchSourceAuthorityScraplingConsensusDecayObservation]
    | tuple[ResearchSourceAuthorityScraplingConsensusDecayObservation, ...],
    *,
    config: ResearchSourceAuthorityScraplingConsensusDecayConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityScraplingConsensusDecayReport:
    if type(config) is not ResearchSourceAuthorityScraplingConsensusDecayConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityScraplingConsensusDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")

    grouped: dict[str, list[ResearchSourceAuthorityScraplingConsensusDecayObservation]] = {}
    for observation in normalized_observations:
        grouped.setdefault(observation.candidate_reference, []).append(observation)

    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate_reference,
                    tuple(grouped[candidate_reference]),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate_reference in grouped
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchSourceAuthorityScraplingConsensusDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
        min_consensus_source_family_count=config.min_consensus_source_family_count,
        pass_score_threshold=config.pass_score_threshold,
        watch_score_threshold=config.watch_score_threshold,
        authority_weight=config.authority_weight,
        consensus_weight=config.consensus_weight,
        recency_weight=config.recency_weight,
        candidate_count=_count(len(rows)),
        observation_count=_count(len(normalized_observations)),
        pass_count=_count(sum(Decimal("1") for row in rows if row.status == "pass")),
        watch_count=_count(sum(Decimal("1") for row in rows if row.status == "watch")),
        block_count=_count(sum(Decimal("1") for row in rows if row.status == "block")),
        average_scrapling_consensus_decay_score=_average_score(rows),
        status=_summary_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_source_authority_scrapling_consensus_decay_report_payload(
    report: ResearchSourceAuthorityScraplingConsensusDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityScraplingConsensusDecayReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityScraplingConsensusDecayReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_authority_scrapling_consensus_decay_public_payload(payload)
    return payload


def validate_research_source_authority_scrapling_consensus_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _validate_public_payload_shape(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    if digest != _digest_payload(without_digest):
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_candidate(
    candidate_reference: str,
    observations: tuple[ResearchSourceAuthorityScraplingConsensusDecayObservation, ...],
    *,
    config: ResearchSourceAuthorityScraplingConsensusDecayConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityScraplingConsensusDecayRow:
    latest_observed_at = max(observation.observed_at for observation in observations)
    latest_source_age_seconds = _seconds_between(latest_observed_at, generated_at)
    source_references = tuple({observation.source_reference for observation in observations})
    source_families = tuple({observation.source_family for observation in observations})
    average_authority_score = _average_decimal(
        tuple(observation.authority_score for observation in observations),
    )
    consensus_score = _ratio(
        _count(len(source_families)),
        config.min_consensus_source_family_count,
    )
    if consensus_score > ONE:
        consensus_score = ONE
    recency_score = _recency_score(
        latest_source_age_seconds,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
    )
    score = _weighted_score(
        average_authority_score=average_authority_score,
        consensus_score=consensus_score,
        recency_score=recency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        average_authority_score=average_authority_score,
        source_family_count=_count(len(source_families)),
        latest_source_age_seconds=latest_source_age_seconds,
        score=score,
        config=config,
    )
    return ResearchSourceAuthorityScraplingConsensusDecayRow(
        candidate_digest=_digest_reference(candidate_reference),
        evidence_count=_count(len(observations)),
        source_count=_count(len(source_references)),
        source_family_count=_count(len(source_families)),
        latest_observed_at=latest_observed_at,
        latest_source_age_seconds=latest_source_age_seconds,
        average_authority_score=average_authority_score,
        consensus_score=consensus_score,
        recency_score=recency_score,
        scrapling_consensus_decay_score=score,
        status=_row_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    average_authority_score: Decimal,
    source_family_count: Decimal,
    latest_source_age_seconds: Decimal,
    score: Decimal,
    config: ResearchSourceAuthorityScraplingConsensusDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    block = False
    watch = False

    if average_authority_score < config.watch_score_threshold:
        reasons.append(LOW_AUTHORITY_REASON)
        block = True
    if latest_source_age_seconds > config.stale_age_seconds:
        reasons.append(STALE_OBSERVATIONS_REASON)
        watch = True
    if score < config.watch_score_threshold:
        reasons.append(SCORE_BELOW_WATCH_REASON)
        block = True
    if (
        not block
        and source_family_count < config.min_consensus_source_family_count
    ):
        reasons.append(INSUFFICIENT_CONSENSUS_REASON)
        watch = True

    if block:
        reasons.append(BLOCK_REASON)
    elif watch or score < config.pass_score_threshold:
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _normalize_observations(
    observations: list[ResearchSourceAuthorityScraplingConsensusDecayObservation]
    | tuple[ResearchSourceAuthorityScraplingConsensusDecayObservation, ...],
) -> tuple[ResearchSourceAuthorityScraplingConsensusDecayObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized: list[ResearchSourceAuthorityScraplingConsensusDecayObservation] = []
    for observation in observations:
        if type(observation) is not ResearchSourceAuthorityScraplingConsensusDecayObservation:
            raise ValueError(
                "observation must be a ResearchSourceAuthorityScraplingConsensusDecayObservation",
            )
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...],
) -> tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchSourceAuthorityScraplingConsensusDecayRow] = []
    for row in rows:
        if type(row) is not ResearchSourceAuthorityScraplingConsensusDecayRow:
            raise ValueError("row must be a ResearchSourceAuthorityScraplingConsensusDecayRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: tuple[
        ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount:
            raise ValueError(
                "reason_code_count must be a "
                "ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        normalized.append(count)
    return tuple(normalized)


def _validate_row_consistency(
    row: ResearchSourceAuthorityScraplingConsensusDecayRow,
) -> None:
    if row.status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status is inconsistent with reason_codes")
    if row.evidence_count < ONE:
        raise ValueError("evidence_count must be positive")
    if row.source_count > row.evidence_count:
        raise ValueError("source_count must not exceed evidence_count")
    if row.source_family_count > row.evidence_count:
        raise ValueError("source_family_count must not exceed evidence_count")


def _validate_report_consistency(
    report: ResearchSourceAuthorityScraplingConsensusDecayReport,
) -> None:
    rows = report.rows
    expected_values = {
        "candidate_count": _count(len(rows)),
        "observation_count": sum((row.evidence_count for row in rows), ZERO),
        "pass_count": _count(sum(Decimal("1") for row in rows if row.status == "pass")),
        "watch_count": _count(sum(Decimal("1") for row in rows if row.status == "watch")),
        "block_count": _count(sum(Decimal("1") for row in rows if row.status == "block")),
        "average_scrapling_consensus_decay_score": _average_score(rows),
        "status": _summary_status(rows),
        "reason_codes": _summary_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows, _summary_reason_codes(rows)),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _summary_status(
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
            ),
        )
    return tuple(
        ResearchSourceAuthorityScraplingConsensusDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(Decimal("1") for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    if PASS_REASON in reason_codes:
        return "pass"
    raise ValueError("reason_codes must include a terminal status reason")


def _row_sort_key(
    row: ResearchSourceAuthorityScraplingConsensusDecayRow,
) -> tuple[Decimal, str]:
    return (STATUS_SORT_ORDER[row.status], row.candidate_digest)


def _average_score(
    rows: tuple[ResearchSourceAuthorityScraplingConsensusDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.scrapling_consensus_decay_score for row in rows))


def _weighted_score(
    *,
    average_authority_score: Decimal,
    consensus_score: Decimal,
    recency_score: Decimal,
    config: ResearchSourceAuthorityScraplingConsensusDecayConfig,
) -> Decimal:
    return _normalize_decimal(
        "scrapling_consensus_decay_score",
        average_authority_score * config.authority_weight
        + consensus_score * config.consensus_weight
        + recency_score * config.recency_weight,
    )


def _recency_score(
    latest_source_age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if latest_source_age_seconds <= fresh_age_seconds:
        return ONE
    if latest_source_age_seconds >= stale_age_seconds:
        return ZERO
    score = (stale_age_seconds - latest_source_age_seconds) / (
        stale_age_seconds - fresh_age_seconds
    )
    return _require_probability_decimal("recency_score", score)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("average", sum(values, ZERO) / _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_decimal("ratio", numerator / denominator)


def _count(value: int | Decimal) -> Decimal:
    return _require_nonnegative_decimal("count", Decimal(value))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _normalize_decimal("seconds", microseconds / MICROSECONDS_PER_SECOND)


def _derived_validation_digest(
    report: ResearchSourceAuthorityScraplingConsensusDecayReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: ResearchSourceAuthorityScraplingConsensusDecayReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _digest_reference(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


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


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_keys("public payload", payload, REPORT_PAYLOAD_KEYS)
    for field_name in (
        "fresh_age_seconds",
        "stale_age_seconds",
        "min_consensus_source_family_count",
        "pass_score_threshold",
        "watch_score_threshold",
        "authority_weight",
        "consensus_weight",
        "recency_weight",
        "candidate_count",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_string(field_name, payload[field_name])
    if payload["average_scrapling_consensus_decay_score"] is not None:
        _require_decimal_string(
            "average_scrapling_consensus_decay_score",
            payload["average_scrapling_consensus_decay_score"],
        )
    _require_status("status", payload["status"])
    _normalize_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for item in payload["reason_code_counts"]:
        _validate_public_reason_code_count_payload(item)
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for item in payload["rows"]:
        _validate_public_row_payload(item)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys("row payload", value, ROW_PAYLOAD_KEYS)
    _require_digest_reference("candidate_digest", value["candidate_digest"])
    for field_name in (
        "evidence_count",
        "source_count",
        "source_family_count",
        "latest_source_age_seconds",
        "average_authority_score",
        "consensus_score",
        "recency_score",
        "scrapling_consensus_decay_score",
    ):
        _require_decimal_string(field_name, value[field_name])
    _require_public_identifier("latest_observed_at", value["latest_observed_at"])
    _require_status("status", value["status"])
    _normalize_reason_codes("reason_codes", value["reason_codes"], ROW_REASON_CODES)
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_public_reason_code_count_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_keys("reason_code_count payload", value, REASON_COUNT_PAYLOAD_KEYS)
    _require_known_value("reason_code", value["reason_code"], REPORT_REASON_CODES)
    _require_decimal_string("count", value["count"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_keys(
    label: str,
    value: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    keys = set(value)
    if keys != allowed_keys:
        raise ValueError(f"{label} must use the public readonly schema")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PRIVATE_REFERENCE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe private reference")
    return value


def _require_source_family(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be a canonical lowercase token")
    token = value.replace("-", "").replace("_", "")
    if not token.isalnum():
        raise ValueError(f"{field_name} must be a canonical lowercase token")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe value")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_known_value(field_name, value, STATUSES)


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...] | list[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_known_value(field_name, reason_code, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_digest_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a sha256 redaction")
    _require_digest(field_name, value[len(prefix) :])
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
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
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
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
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
