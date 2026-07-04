"""Pure Phase 1 crypto governance vote quorum digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import re
from typing import Any


DEFAULT_CRYPTO_GOVERNANCE_VOTE_QUORUM_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-governance-vote-quorum-digest-v0"
)

DIGEST_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "governance_vote_quorum_source_conflict",
    "governance_vote_quorum_stale_source",
    "governance_vote_quorum_far_below_threshold",
    "governance_vote_quorum_below_threshold",
    "governance_vote_quorum_near_close",
    "governance_vote_quorum_participation_low",
    "governance_vote_quorum_met",
    "governance_vote_quorum_source_fresh",
    "governance_vote_quorum_source_consensus",
    "governance_vote_quorum_source_coverage_met",
)
REPORT_REASON_CODES = (
    "governance_vote_quorum_source_conflict_present",
    "governance_vote_quorum_stale_source_present",
    "governance_vote_quorum_gap_present",
    "governance_vote_quorum_near_close_present",
    "governance_vote_quorum_digest_clear",
    "governance_vote_quorum_digest_empty",
)

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_REDACTION_MARKERS = (
    "sec" + "ret",
    "to" + "ken",
    "cred" + "ential",
    "pri" + "vate",
    "pass" + "word",
    "wal" + "let",
    "au" + "th",
    "sig" + "n",
    "api" + "-" + "key",
)
_REDACTED_PREFIX = "redacted"


@dataclass(frozen=True)
class CryptoGovernanceVoteQuorumDigestConfig:
    config_version: str = DEFAULT_CRYPTO_GOVERNANCE_VOTE_QUORUM_DIGEST_CONFIG_VERSION
    min_quorum_progress_ratio: Decimal = Decimal("0.900000")
    low_participation_ratio: Decimal = Decimal("0.500000")
    near_close_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoGovernanceVoteQuorumDigestConfig:
            raise TypeError(
                "CryptoGovernanceVoteQuorumDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CryptoGovernanceVoteQuorumDigestConfig:
            raise ValueError(
                "config must be exactly CryptoGovernanceVoteQuorumDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CRYPTO_GOVERNANCE_VOTE_QUORUM_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_quorum_progress_ratio",
            _require_positive_ratio(
                "min_quorum_progress_ratio",
                self.min_quorum_progress_ratio,
            ),
        )
        object.__setattr__(
            self,
            "low_participation_ratio",
            _require_positive_ratio(
                "low_participation_ratio",
                self.low_participation_ratio,
            ),
        )
        object.__setattr__(
            self,
            "near_close_seconds",
            _require_nonnegative_decimal("near_close_seconds", self.near_close_seconds),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CryptoGovernanceVoteQuorumObservation:
    proposal_id: str
    protocol_id: str
    market_slug: str
    vote_snapshot_at: datetime
    voting_close_at: datetime
    votes_for: Decimal
    votes_against: Decimal
    votes_abstain: Decimal
    quorum_required_votes: Decimal
    eligible_votes: Decimal
    source_count: Decimal
    source_labels: tuple[str, ...]
    stale_source_count: Decimal = ZERO
    conflicting_source_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoGovernanceVoteQuorumObservation:
            raise TypeError(
                "CryptoGovernanceVoteQuorumObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CryptoGovernanceVoteQuorumObservation:
            raise ValueError(
                "observation must be exactly CryptoGovernanceVoteQuorumObservation",
            )
        for field_name in ("proposal_id", "protocol_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "vote_snapshot_at",
            _as_utc("vote_snapshot_at", self.vote_snapshot_at),
        )
        object.__setattr__(
            self,
            "voting_close_at",
            _as_utc("voting_close_at", self.voting_close_at),
        )
        for field_name in (
            "votes_for",
            "votes_against",
            "votes_abstain",
            "quorum_required_votes",
            "eligible_votes",
            "source_count",
            "stale_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quorum_required_votes",
            _require_positive_decimal(
                "quorum_required_votes",
                self.quorum_required_votes,
            ),
        )
        object.__setattr__(
            self,
            "eligible_votes",
            _require_positive_decimal("eligible_votes", self.eligible_votes),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_labels",
            _normalize_string_tuple("source_labels", self.source_labels),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class CryptoGovernanceVoteQuorumDigestRow:
    proposal_id: str
    protocol_id: str
    market_slug: str
    vote_snapshot_at: datetime
    voting_close_at: datetime
    votes_for: Decimal
    votes_against: Decimal
    votes_abstain: Decimal
    total_participating_votes: Decimal
    quorum_required_votes: Decimal
    eligible_votes: Decimal
    quorum_progress_ratio: Decimal
    quorum_gap_votes: Decimal
    quorum_gap_ratio: Decimal
    participation_ratio: Decimal
    source_count: Decimal
    source_labels: tuple[str, ...]
    stale_source_count: Decimal
    conflicting_source_count: Decimal
    seconds_until_close: Decimal
    hours_until_close: Decimal
    quorum_met: bool
    near_close: bool
    quorum_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoGovernanceVoteQuorumDigestRow:
            raise TypeError(
                "CryptoGovernanceVoteQuorumDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CryptoGovernanceVoteQuorumDigestRow:
            raise ValueError("row must be exactly CryptoGovernanceVoteQuorumDigestRow")
        for field_name in ("proposal_id", "protocol_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "vote_snapshot_at",
            _as_utc("vote_snapshot_at", self.vote_snapshot_at),
        )
        object.__setattr__(
            self,
            "voting_close_at",
            _as_utc("voting_close_at", self.voting_close_at),
        )
        for field_name in (
            "votes_for",
            "votes_against",
            "votes_abstain",
            "total_participating_votes",
            "quorum_required_votes",
            "eligible_votes",
            "quorum_gap_votes",
            "source_count",
            "stale_source_count",
            "conflicting_source_count",
            "seconds_until_close",
            "hours_until_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quorum_progress_ratio",
            "quorum_gap_ratio",
            "participation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_labels",
            _normalize_string_tuple("source_labels", self.source_labels),
        )
        _require_bool("quorum_met", self.quorum_met)
        _require_bool("near_close", self.near_close)
        _require_member("quorum_status", self.quorum_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CryptoGovernanceVoteQuorumReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoGovernanceVoteQuorumReasonCodeCount:
            raise TypeError(
                "CryptoGovernanceVoteQuorumReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CryptoGovernanceVoteQuorumReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly CryptoGovernanceVoteQuorumReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class CryptoGovernanceVoteQuorumDigestReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    quorum_met_count: Decimal
    quorum_gap_count: Decimal
    conflicting_source_count: Decimal
    stale_source_count: Decimal
    near_close_count: Decimal
    average_quorum_progress_ratio: Decimal
    max_quorum_gap_ratio: Decimal
    blocked_observation_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    quorum_rows: tuple[CryptoGovernanceVoteQuorumDigestRow, ...]
    reason_code_counts: tuple[CryptoGovernanceVoteQuorumReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoGovernanceVoteQuorumDigestReport:
            raise TypeError(
                "CryptoGovernanceVoteQuorumDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CryptoGovernanceVoteQuorumDigestReport:
            raise ValueError(
                "report must be exactly CryptoGovernanceVoteQuorumDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CRYPTO_GOVERNANCE_VOTE_QUORUM_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "quorum_met_count",
            "quorum_gap_count",
            "conflicting_source_count",
            "stale_source_count",
            "near_close_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_quorum_progress_ratio",
            "max_quorum_gap_ratio",
            "blocked_observation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "quorum_rows", _normalize_rows(self.quorum_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_governance_vote_quorum_digest(
    inputs: Iterable[CryptoGovernanceVoteQuorumObservation],
    *,
    config: CryptoGovernanceVoteQuorumDigestConfig,
    generated_at: datetime,
) -> CryptoGovernanceVoteQuorumDigestReport:
    if type(config) is not CryptoGovernanceVoteQuorumDigestConfig:
        raise ValueError("config must be exactly CryptoGovernanceVoteQuorumDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        _row_for_observation(item, config=config, generated_at=generated_at_utc)
        for item in normalized_inputs
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(sorted_rows))
    blocked_count = _count_decimal(
        sum(1 for row in sorted_rows if row.quorum_status == "blocked"),
    )
    reason_codes = _report_reason_codes(sorted_rows)
    digest_status = _digest_status(sorted_rows)

    return CryptoGovernanceVoteQuorumDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=observation_count,
        pass_count=_count_decimal(
            sum(1 for row in sorted_rows if row.quorum_status == "pass"),
        ),
        watch_count=_count_decimal(
            sum(1 for row in sorted_rows if row.quorum_status == "watch"),
        ),
        blocked_count=blocked_count,
        quorum_met_count=_count_decimal(sum(1 for row in sorted_rows if row.quorum_met)),
        quorum_gap_count=_count_decimal(
            sum(1 for row in sorted_rows if not row.quorum_met),
        ),
        conflicting_source_count=_count_decimal(
            sum(1 for row in sorted_rows if row.conflicting_source_count > ZERO),
        ),
        stale_source_count=_count_decimal(
            sum(1 for row in sorted_rows if row.stale_source_count > ZERO),
        ),
        near_close_count=_count_decimal(sum(1 for row in sorted_rows if row.near_close)),
        average_quorum_progress_ratio=_ratio(
            _sum_decimal(row.quorum_progress_ratio for row in sorted_rows),
            observation_count,
        ),
        max_quorum_gap_ratio=max(
            (row.quorum_gap_ratio for row in sorted_rows),
            default=ZERO,
        ),
        blocked_observation_ratio=_ratio(blocked_count, observation_count),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        quorum_rows=sorted_rows,
        reason_code_counts=_reason_code_counts(sorted_rows, reason_codes, observation_count),
        reason_codes=reason_codes,
    )


def market_research_crypto_governance_vote_quorum_digest_payload(
    report: CryptoGovernanceVoteQuorumDigestReport,
) -> dict[str, Any]:
    if type(report) is not CryptoGovernanceVoteQuorumDigestReport:
        raise ValueError(
            "report must be exactly CryptoGovernanceVoteQuorumDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_observation(
    observation: CryptoGovernanceVoteQuorumObservation,
    *,
    config: CryptoGovernanceVoteQuorumDigestConfig,
    generated_at: datetime,
) -> CryptoGovernanceVoteQuorumDigestRow:
    total_participating_votes = _sum_decimal(
        (observation.votes_for, observation.votes_against, observation.votes_abstain),
    )
    quorum_progress_ratio = _ratio(
        _min_decimal(total_participating_votes, observation.quorum_required_votes),
        observation.quorum_required_votes,
    )
    quorum_gap_votes = _max_decimal(
        ZERO,
        observation.quorum_required_votes - total_participating_votes,
    )
    quorum_gap_ratio = _ratio(quorum_gap_votes, observation.quorum_required_votes)
    participation_ratio = _ratio(total_participating_votes, observation.eligible_votes)
    seconds_until_close = _seconds_between(generated_at, observation.voting_close_at)
    hours_until_close = _ratio(seconds_until_close, SECONDS_PER_HOUR)
    quorum_met = total_participating_votes >= observation.quorum_required_votes
    near_close = seconds_until_close <= config.near_close_seconds
    status = _row_status(
        quorum_progress_ratio=quorum_progress_ratio,
        participation_ratio=participation_ratio,
        quorum_met=quorum_met,
        near_close=near_close,
        observation=observation,
        config=config,
    )
    return CryptoGovernanceVoteQuorumDigestRow(
        proposal_id=observation.proposal_id,
        protocol_id=observation.protocol_id,
        market_slug=observation.market_slug,
        vote_snapshot_at=observation.vote_snapshot_at,
        voting_close_at=observation.voting_close_at,
        votes_for=observation.votes_for,
        votes_against=observation.votes_against,
        votes_abstain=observation.votes_abstain,
        total_participating_votes=total_participating_votes,
        quorum_required_votes=observation.quorum_required_votes,
        eligible_votes=observation.eligible_votes,
        quorum_progress_ratio=quorum_progress_ratio,
        quorum_gap_votes=quorum_gap_votes,
        quorum_gap_ratio=quorum_gap_ratio,
        participation_ratio=participation_ratio,
        source_count=observation.source_count,
        source_labels=observation.source_labels,
        stale_source_count=observation.stale_source_count,
        conflicting_source_count=observation.conflicting_source_count,
        seconds_until_close=seconds_until_close,
        hours_until_close=hours_until_close,
        quorum_met=quorum_met,
        near_close=near_close,
        quorum_status=status,
        reason_codes=_row_reason_codes(
            quorum_met=quorum_met,
            quorum_progress_ratio=quorum_progress_ratio,
            participation_ratio=participation_ratio,
            near_close=near_close,
            observation=observation,
            config=config,
        ),
    )


def _row_status(
    *,
    quorum_progress_ratio: Decimal,
    participation_ratio: Decimal,
    quorum_met: bool,
    near_close: bool,
    observation: CryptoGovernanceVoteQuorumObservation,
    config: CryptoGovernanceVoteQuorumDigestConfig,
) -> str:
    if observation.conflicting_source_count > ZERO or observation.stale_source_count > ZERO:
        return "blocked"
    if quorum_progress_ratio < config.low_participation_ratio:
        return "blocked"
    if quorum_met and observation.source_count >= config.min_source_count:
        return "pass"
    if (
        quorum_progress_ratio >= config.min_quorum_progress_ratio
        or near_close
        or participation_ratio < config.low_participation_ratio
    ):
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    quorum_met: bool,
    quorum_progress_ratio: Decimal,
    participation_ratio: Decimal,
    near_close: bool,
    observation: CryptoGovernanceVoteQuorumObservation,
    config: CryptoGovernanceVoteQuorumDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.conflicting_source_count > ZERO:
        reasons.append("governance_vote_quorum_source_conflict")
    if observation.stale_source_count > ZERO:
        reasons.append("governance_vote_quorum_stale_source")
    if quorum_met:
        reasons.append("governance_vote_quorum_met")
    elif quorum_progress_ratio < config.low_participation_ratio:
        reasons.append("governance_vote_quorum_far_below_threshold")
    else:
        reasons.append("governance_vote_quorum_below_threshold")
    if near_close:
        reasons.append("governance_vote_quorum_near_close")
    if participation_ratio < config.low_participation_ratio:
        reasons.append("governance_vote_quorum_participation_low")
    if observation.stale_source_count == ZERO:
        reasons.append("governance_vote_quorum_source_fresh")
    if observation.conflicting_source_count == ZERO:
        reasons.append("governance_vote_quorum_source_consensus")
    if observation.source_count >= config.min_source_count:
        reasons.append("governance_vote_quorum_source_coverage_met")
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _report_reason_codes(
    rows: tuple[CryptoGovernanceVoteQuorumDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("governance_vote_quorum_digest_empty",)
    reasons: list[str] = []
    if any(row.conflicting_source_count > ZERO for row in rows):
        reasons.append("governance_vote_quorum_source_conflict_present")
    if any(row.stale_source_count > ZERO for row in rows):
        reasons.append("governance_vote_quorum_stale_source_present")
    if any(not row.quorum_met for row in rows):
        reasons.append("governance_vote_quorum_gap_present")
    if any(row.near_close for row in rows):
        reasons.append("governance_vote_quorum_near_close_present")
    if not reasons:
        reasons.append("governance_vote_quorum_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    rows: tuple[CryptoGovernanceVoteQuorumDigestRow, ...],
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[CryptoGovernanceVoteQuorumReasonCodeCount, ...]:
    if reason_codes == ("governance_vote_quorum_digest_empty",):
        return (
            CryptoGovernanceVoteQuorumReasonCodeCount(
                reason_code="governance_vote_quorum_digest_empty",
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    counts = {
        "governance_vote_quorum_source_conflict_present": _count_decimal(
            sum(1 for row in rows if row.conflicting_source_count > ZERO),
        ),
        "governance_vote_quorum_stale_source_present": _count_decimal(
            sum(1 for row in rows if row.stale_source_count > ZERO),
        ),
        "governance_vote_quorum_gap_present": _count_decimal(
            sum(1 for row in rows if not row.quorum_met),
        ),
        "governance_vote_quorum_near_close_present": _count_decimal(
            sum(1 for row in rows if row.near_close),
        ),
        "governance_vote_quorum_digest_clear": observation_count,
    }
    return tuple(
        CryptoGovernanceVoteQuorumReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            observation_ratio=_ratio(counts[reason_code], observation_count),
        )
        for reason_code in reason_codes
    )


def _digest_status(rows: tuple[CryptoGovernanceVoteQuorumDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.quorum_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quorum_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_crypto_governance_vote_quorum_digest"
    if status == "watch":
        return "monitor_report_only_market_research_crypto_governance_vote_quorum_digest"
    return "block_report_only_market_research_crypto_governance_vote_quorum_digest"


def _validate_observation(observation: CryptoGovernanceVoteQuorumObservation) -> None:
    total = _sum_decimal(
        (observation.votes_for, observation.votes_against, observation.votes_abstain),
    )
    if observation.votes_abstain > total - observation.votes_abstain:
        raise ValueError("votes_abstain must not exceed total participating non-abstain votes")
    if total > observation.eligible_votes:
        raise ValueError("total participating votes must not exceed eligible_votes")
    if observation.stale_source_count > observation.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if observation.conflicting_source_count > observation.source_count:
        raise ValueError("conflicting_source_count must not exceed source_count")
    if _count_decimal(len(observation.source_labels)) != observation.source_count:
        raise ValueError("source_labels must match source_count")


def _validate_row(row: CryptoGovernanceVoteQuorumDigestRow) -> None:
    expected_total = _sum_decimal((row.votes_for, row.votes_against, row.votes_abstain))
    if row.total_participating_votes != expected_total:
        raise ValueError("total_participating_votes must match votes")
    if row.quorum_progress_ratio != _ratio(
        _min_decimal(row.total_participating_votes, row.quorum_required_votes),
        row.quorum_required_votes,
    ):
        raise ValueError("quorum_progress_ratio must match vote totals")
    if row.quorum_gap_votes != _max_decimal(
        ZERO,
        row.quorum_required_votes - row.total_participating_votes,
    ):
        raise ValueError("quorum_gap_votes must match vote totals")
    if row.quorum_gap_ratio != _ratio(row.quorum_gap_votes, row.quorum_required_votes):
        raise ValueError("quorum_gap_ratio must match vote totals")
    if row.participation_ratio != _ratio(row.total_participating_votes, row.eligible_votes):
        raise ValueError("participation_ratio must match vote totals")
    if row.quorum_met is not (row.total_participating_votes >= row.quorum_required_votes):
        raise ValueError("quorum_met must match vote totals")
    if _count_decimal(len(row.source_labels)) != row.source_count:
        raise ValueError("source_labels must match source_count")


def _validate_report(report: CryptoGovernanceVoteQuorumDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.quorum_rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.quorum_rows if row.quorum_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.quorum_rows if row.quorum_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count_decimal(
        sum(1 for row in report.quorum_rows if row.quorum_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.quorum_met_count != _count_decimal(
        sum(1 for row in report.quorum_rows if row.quorum_met),
    ):
        raise ValueError("quorum_met_count must match rows")
    if report.reason_codes != _report_reason_codes(report.quorum_rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _digest_status(report.quorum_rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")


def _normalize_inputs(
    inputs: Iterable[CryptoGovernanceVoteQuorumObservation],
) -> tuple[CryptoGovernanceVoteQuorumObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain crypto governance quorum observations")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must contain crypto governance quorum observations",
        ) from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not CryptoGovernanceVoteQuorumObservation:
            raise ValueError(
                "inputs must contain CryptoGovernanceVoteQuorumObservation",
            )
        if item.proposal_id in seen:
            raise ValueError("inputs must not contain duplicate proposal_id values")
        seen.add(item.proposal_id)
    return normalized


def _normalize_rows(
    value: object,
) -> tuple[CryptoGovernanceVoteQuorumDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("quorum_rows must contain crypto governance quorum rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("quorum_rows must contain crypto governance quorum rows") from exc
    for row in rows:
        if type(row) is not CryptoGovernanceVoteQuorumDigestRow:
            raise ValueError(
                "quorum_rows must contain CryptoGovernanceVoteQuorumDigestRow",
            )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("quorum_rows must be sorted deterministically")
    if len({row.proposal_id for row in rows}) != len(rows):
        raise ValueError("quorum_rows must not contain duplicate proposal_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[CryptoGovernanceVoteQuorumReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not CryptoGovernanceVoteQuorumReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain CryptoGovernanceVoteQuorumReasonCodeCount",
            )
    if counts != tuple(
        sorted(counts, key=lambda item: REPORT_REASON_CODES.index(item.reason_code))
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(items))


def _row_sort_key(row: CryptoGovernanceVoteQuorumDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.quorum_status],
        -row.quorum_gap_ratio,
        row.protocol_id,
        row.proposal_id,
    )


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _redact_text(value: str) -> str:
    lowered = value.lower()
    if not any(marker in lowered for marker in _REDACTION_MARKERS):
        return value
    return f"{_REDACTED_PREFIX}_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        )
    if seconds < ZERO:
        return ZERO
    return _quantize(seconds)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left <= right else right


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


__all__ = (
    "DEFAULT_CRYPTO_GOVERNANCE_VOTE_QUORUM_DIGEST_CONFIG_VERSION",
    "CryptoGovernanceVoteQuorumDigestConfig",
    "CryptoGovernanceVoteQuorumObservation",
    "CryptoGovernanceVoteQuorumDigestRow",
    "CryptoGovernanceVoteQuorumReasonCodeCount",
    "CryptoGovernanceVoteQuorumDigestReport",
    "build_market_research_crypto_governance_vote_quorum_digest",
    "market_research_crypto_governance_vote_quorum_digest_payload",
)
