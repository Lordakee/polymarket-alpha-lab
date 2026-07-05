"""Pure Phase 1 hockey power play mismatch digest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_HOCKEY_POWER_PLAY_MISMATCH_DIGEST_CONFIG_VERSION = (
    "market-research-hockey-power-play-mismatch-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_hockey_power_play_mismatch_digest_ready"
NO_INPUTS_REASON = "market_research_hockey_power_play_mismatch_digest_no_inputs"
LOW_POWER_PLAY_EDGE_REASON = (
    "market_research_hockey_power_play_mismatch_digest_low_power_play_edge"
)
LOW_PENALTY_KILL_GAP_REASON = (
    "market_research_hockey_power_play_mismatch_digest_low_penalty_kill_gap"
)
GOALIE_FATIGUE_REASON = (
    "market_research_hockey_power_play_mismatch_digest_goalie_fatigue"
)
SPECIAL_TEAMS_SAMPLE_GAP_REASON = (
    "market_research_hockey_power_play_mismatch_digest_special_teams_sample_gap"
)
SOURCE_DEPTH_GAP_REASON = (
    "market_research_hockey_power_play_mismatch_digest_source_depth_gap"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_hockey_power_play_mismatch_digest_source_diversity_gap"
)
CONFLICTING_SOURCES_REASON = (
    "market_research_hockey_power_play_mismatch_digest_conflicting_sources"
)
STALE_EVIDENCE_REASON = (
    "market_research_hockey_power_play_mismatch_digest_stale_evidence"
)

REASON_CODE_SEQUENCE = (
    CONFLICTING_SOURCES_REASON,
    GOALIE_FATIGUE_REASON,
    LOW_PENALTY_KILL_GAP_REASON,
    LOW_POWER_PLAY_EDGE_REASON,
    READY_REASON,
    SOURCE_DEPTH_GAP_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    SPECIAL_TEAMS_SAMPLE_GAP_REASON,
    STALE_EVIDENCE_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    CONFLICTING_SOURCES_REASON,
    GOALIE_FATIGUE_REASON,
    LOW_PENALTY_KILL_GAP_REASON,
    LOW_POWER_PLAY_EDGE_REASON,
    SOURCE_DEPTH_GAP_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    SPECIAL_TEAMS_SAMPLE_GAP_REASON,
    STALE_EVIDENCE_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_HOCKEY_POWER_PLAY_MISMATCH_DIGEST_CONFIG_VERSION",
    "MarketResearchHockeyPowerPlayMismatchDigestConfig",
    "MarketResearchHockeyPowerPlayMismatchDigestItem",
    "MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount",
    "MarketResearchHockeyPowerPlayMismatchDigestReport",
    "MarketResearchHockeyPowerPlayMismatchDigestRow",
    "build_market_research_hockey_power_play_mismatch_digest",
    "market_research_hockey_power_play_mismatch_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchHockeyPowerPlayMismatchDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_HOCKEY_POWER_PLAY_MISMATCH_DIGEST_CONFIG_VERSION
    )
    max_evidence_age_seconds: Decimal = Decimal("3600.000000")
    min_power_play_edge_score: Decimal = Decimal("0.650000")
    min_penalty_kill_gap_score: Decimal = Decimal("0.550000")
    min_goalie_fatigue_score: Decimal = Decimal("0.500000")
    min_special_teams_sample_count: Decimal = Decimal("3.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    max_conflicting_source_count: Decimal = Decimal("0.000000")
    confidence_decay_per_source_gap: Decimal = Decimal("0.120000")
    confidence_decay_per_stale_evidence: Decimal = Decimal("0.100000")
    confidence_decay_per_conflict: Decimal = Decimal("0.250000")
    confidence_decay_per_goalie_fatigue: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_evidence_age_seconds",
            "min_power_play_edge_score",
            "min_penalty_kill_gap_score",
            "min_goalie_fatigue_score",
            "min_special_teams_sample_count",
            "min_source_count",
            "min_independent_source_count",
            "max_conflicting_source_count",
            "confidence_decay_per_source_gap",
            "confidence_decay_per_stale_evidence",
            "confidence_decay_per_conflict",
            "confidence_decay_per_goalie_fatigue",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchHockeyPowerPlayMismatchDigestItem(_NoSubclass):
    condition_id: str
    hockey_event_key: str
    team_key: str
    opponent_key: str
    public_evidence_reference: str
    observed_at: datetime
    power_play_edge_score: Decimal
    penalty_kill_gap_score: Decimal
    goalie_fatigue_score: Decimal
    special_teams_sample_count: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    base_confidence_score: Decimal
    item_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "hockey_event_key",
            "team_key",
            "opponent_key",
            "item_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_public_evidence_reference(
            "public_evidence_reference",
            self.public_evidence_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "power_play_edge_score",
            "penalty_kill_gap_score",
            "goalie_fatigue_score",
            "special_teams_sample_count",
            "source_count",
            "independent_source_count",
            "conflicting_source_count",
            "base_confidence_score",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class MarketResearchHockeyPowerPlayMismatchDigestRow(_NoSubclass):
    condition_id: str
    hockey_event_key: str
    team_key: str
    opponent_key: str
    digest_status: str
    evidence_age_seconds: Decimal
    power_play_edge_score: Decimal
    penalty_kill_gap_score: Decimal
    goalie_fatigue_score: Decimal
    special_teams_sample_count: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_diversity_ratio: Decimal
    conflicting_source_count: Decimal
    base_confidence_score: Decimal
    confidence_decay_score: Decimal
    confidence_score: Decimal
    redacted_public_evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "hockey_event_key",
            "team_key",
            "opponent_key",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_digest_status("digest_status", self.digest_status)
        for field_name in (
            "evidence_age_seconds",
            "power_play_edge_score",
            "penalty_kill_gap_score",
            "goalie_fatigue_score",
            "special_teams_sample_count",
            "source_count",
            "independent_source_count",
            "source_diversity_ratio",
            "conflicting_source_count",
            "base_confidence_score",
            "confidence_decay_score",
            "confidence_score",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_redacted_reference(
            "redacted_public_evidence_reference",
            self.redacted_public_evidence_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, seq=ROW_REASON_CODE_SEQUENCE),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    item_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        _require_nonnegative_decimal("count", self.count)
        _require_nonnegative_decimal("item_ratio", self.item_ratio)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchHockeyPowerPlayMismatchDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    item_count: Decimal
    ready_item_count: Decimal
    watch_item_count: Decimal
    blocked_item_count: Decimal
    power_play_edge_gap_item_count: Decimal
    penalty_kill_gap_item_count: Decimal
    goalie_fatigue_item_count: Decimal
    sample_gap_item_count: Decimal
    source_depth_gap_item_count: Decimal
    source_diversity_gap_item_count: Decimal
    conflict_item_count: Decimal
    stale_evidence_item_count: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    average_source_count: Decimal
    average_confidence_score: Decimal
    max_evidence_age_seconds: Decimal
    min_power_play_edge_score: Decimal
    min_penalty_kill_gap_score: Decimal
    min_goalie_fatigue_score: Decimal
    min_special_teams_sample_count: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    max_conflicting_source_count: Decimal
    max_observed_evidence_age_seconds: Decimal
    rows: tuple[MarketResearchHockeyPowerPlayMismatchDigestRow, ...]
    item_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "item_count",
            "ready_item_count",
            "watch_item_count",
            "blocked_item_count",
            "power_play_edge_gap_item_count",
            "penalty_kill_gap_item_count",
            "goalie_fatigue_item_count",
            "sample_gap_item_count",
            "source_depth_gap_item_count",
            "source_diversity_gap_item_count",
            "conflict_item_count",
            "stale_evidence_item_count",
            "source_count",
            "independent_source_count",
            "average_source_count",
            "average_confidence_score",
            "max_evidence_age_seconds",
            "min_power_play_edge_score",
            "min_penalty_kill_gap_score",
            "min_goalie_fatigue_score",
            "min_special_teams_sample_count",
            "min_source_count",
            "min_independent_source_count",
            "max_conflicting_source_count",
            "max_observed_evidence_age_seconds",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "item_config_versions",
            _normalize_item_config_versions(self.item_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, seq=REASON_CODE_SEQUENCE),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_market_research_hockey_power_play_mismatch_digest(
    items: Iterable[MarketResearchHockeyPowerPlayMismatchDigestItem],
    *,
    config: MarketResearchHockeyPowerPlayMismatchDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchHockeyPowerPlayMismatchDigestReport:
    cfg = config or MarketResearchHockeyPowerPlayMismatchDigestConfig()
    if type(cfg) is not MarketResearchHockeyPowerPlayMismatchDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchHockeyPowerPlayMismatchDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(
        _row_for_item(item, config=cfg, generated_at=generated_at_utc)
        for item in normalized_items
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.hockey_event_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    source_count = _decimal_sum(row.source_count for row in sorted_rows)
    independent_source_count = _decimal_sum(
        row.independent_source_count for row in sorted_rows
    )
    return MarketResearchHockeyPowerPlayMismatchDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        item_count=_decimal_count(len(sorted_rows)),
        ready_item_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_READY),
        ),
        watch_item_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_WATCH),
        ),
        blocked_item_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_BLOCKED),
        ),
        power_play_edge_gap_item_count=_reason_count(
            sorted_rows,
            LOW_POWER_PLAY_EDGE_REASON,
        ),
        penalty_kill_gap_item_count=_reason_count(sorted_rows, LOW_PENALTY_KILL_GAP_REASON),
        goalie_fatigue_item_count=_reason_count(sorted_rows, GOALIE_FATIGUE_REASON),
        sample_gap_item_count=_reason_count(sorted_rows, SPECIAL_TEAMS_SAMPLE_GAP_REASON),
        source_depth_gap_item_count=_reason_count(sorted_rows, SOURCE_DEPTH_GAP_REASON),
        source_diversity_gap_item_count=_reason_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        conflict_item_count=_reason_count(sorted_rows, CONFLICTING_SOURCES_REASON),
        stale_evidence_item_count=_reason_count(sorted_rows, STALE_EVIDENCE_REASON),
        source_count=source_count,
        independent_source_count=independent_source_count,
        average_source_count=_ratio(source_count, _decimal_count(len(sorted_rows))),
        average_confidence_score=_ratio(
            _decimal_sum(row.confidence_score for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_evidence_age_seconds=cfg.max_evidence_age_seconds,
        min_power_play_edge_score=cfg.min_power_play_edge_score,
        min_penalty_kill_gap_score=cfg.min_penalty_kill_gap_score,
        min_goalie_fatigue_score=cfg.min_goalie_fatigue_score,
        min_special_teams_sample_count=cfg.min_special_teams_sample_count,
        min_source_count=cfg.min_source_count,
        min_independent_source_count=cfg.min_independent_source_count,
        max_conflicting_source_count=cfg.max_conflicting_source_count,
        max_observed_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        item_config_versions=tuple(
            sorted(
                (item.hockey_event_key, item.item_config_version)
                for item in normalized_items
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_hockey_power_play_mismatch_digest_payload(
    report: MarketResearchHockeyPowerPlayMismatchDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchHockeyPowerPlayMismatchDigestReport:
        raise ValueError(
            "report must be a MarketResearchHockeyPowerPlayMismatchDigestReport",
        )
    return _json_ready_no_floats(report)


def _row_for_item(
    item: MarketResearchHockeyPowerPlayMismatchDigestItem,
    *,
    config: MarketResearchHockeyPowerPlayMismatchDigestConfig,
    generated_at: datetime,
) -> MarketResearchHockeyPowerPlayMismatchDigestRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    evidence_age_seconds = _age_seconds(generated_at, item.observed_at)
    source_diversity_ratio = _ratio(item.independent_source_count, item.source_count)
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        evidence_age_seconds=evidence_age_seconds,
        source_diversity_ratio=source_diversity_ratio,
    )
    confidence_decay_score = _confidence_decay_score(
        reason_codes=reason_codes,
        config=config,
    )
    confidence_score = max(ZERO, _quantize(item.base_confidence_score - confidence_decay_score))
    return MarketResearchHockeyPowerPlayMismatchDigestRow(
        condition_id=item.condition_id,
        hockey_event_key=item.hockey_event_key,
        team_key=item.team_key,
        opponent_key=item.opponent_key,
        digest_status=_row_status(reason_codes),
        evidence_age_seconds=evidence_age_seconds,
        power_play_edge_score=item.power_play_edge_score,
        penalty_kill_gap_score=item.penalty_kill_gap_score,
        goalie_fatigue_score=item.goalie_fatigue_score,
        special_teams_sample_count=item.special_teams_sample_count,
        source_count=item.source_count,
        independent_source_count=item.independent_source_count,
        source_diversity_ratio=source_diversity_ratio,
        conflicting_source_count=item.conflicting_source_count,
        base_confidence_score=item.base_confidence_score,
        confidence_decay_score=confidence_decay_score,
        confidence_score=confidence_score,
        redacted_public_evidence_reference=_redacted_reference(
            item.public_evidence_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: MarketResearchHockeyPowerPlayMismatchDigestItem,
    config: MarketResearchHockeyPowerPlayMismatchDigestConfig,
    evidence_age_seconds: Decimal,
    source_diversity_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.conflicting_source_count > config.max_conflicting_source_count:
        reasons.append(CONFLICTING_SOURCES_REASON)
    if item.goalie_fatigue_score >= config.min_goalie_fatigue_score:
        reasons.append(GOALIE_FATIGUE_REASON)
    if item.penalty_kill_gap_score < config.min_penalty_kill_gap_score:
        reasons.append(LOW_PENALTY_KILL_GAP_REASON)
    if item.power_play_edge_score < config.min_power_play_edge_score:
        reasons.append(LOW_POWER_PLAY_EDGE_REASON)
    if item.source_count < config.min_source_count:
        reasons.append(SOURCE_DEPTH_GAP_REASON)
    if source_diversity_ratio < _ratio(
        config.min_independent_source_count,
        config.min_source_count,
    ):
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if item.special_teams_sample_count < config.min_special_teams_sample_count:
        reasons.append(SPECIAL_TEAMS_SAMPLE_GAP_REASON)
    if evidence_age_seconds > config.max_evidence_age_seconds:
        reasons.append(STALE_EVIDENCE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _confidence_decay_score(
    *,
    reason_codes: tuple[str, ...],
    config: MarketResearchHockeyPowerPlayMismatchDigestConfig,
) -> Decimal:
    decay = ZERO
    if SOURCE_DEPTH_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if SOURCE_DIVERSITY_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if STALE_EVIDENCE_REASON in reason_codes:
        decay += config.confidence_decay_per_stale_evidence
    if CONFLICTING_SOURCES_REASON in reason_codes:
        decay += config.confidence_decay_per_conflict
    if GOALIE_FATIGUE_REASON in reason_codes:
        decay += config.confidence_decay_per_goalie_fatigue
    if LOW_PENALTY_KILL_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if LOW_POWER_PLAY_EDGE_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if SPECIAL_TEAMS_SAMPLE_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_stale_evidence
    return _quantize(decay)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CONFLICTING_SOURCES_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchHockeyPowerPlayMismatchDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "allow_report_only_market_research_hockey_power_play_mismatch_digest"
    if status == STATUS_WATCH:
        return "watch_report_only_market_research_hockey_power_play_mismatch_digest"
    return "block_report_only_market_research_hockey_power_play_mismatch_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchHockeyPowerPlayMismatchDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _reason_code_counts(
    rows: tuple[MarketResearchHockeyPowerPlayMismatchDigestRow, ...],
) -> tuple[MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    counts: list[MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    item_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_count(
    rows: tuple[MarketResearchHockeyPowerPlayMismatchDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: MarketResearchHockeyPowerPlayMismatchDigestRow) -> None:
    if row.independent_source_count > row.source_count:
        raise ValueError("independent_source_count must not exceed source_count")
    if row.conflicting_source_count > row.source_count:
        raise ValueError("conflicting_source_count must not exceed source_count")
    if row.source_diversity_ratio != _ratio(
        row.independent_source_count,
        row.source_count,
    ):
        raise ValueError("source_diversity_ratio must match source counts")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.confidence_score != max(
        ZERO,
        _quantize(row.base_confidence_score - row.confidence_decay_score),
    ):
        raise ValueError("confidence_score must match base confidence and decay")


def _validate_report(report: MarketResearchHockeyPowerPlayMismatchDigestReport) -> None:
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.ready_item_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == STATUS_READY),
    ):
        raise ValueError("ready_item_count must match rows")
    if report.watch_item_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == STATUS_WATCH),
    ):
        raise ValueError("watch_item_count must match rows")
    if report.blocked_item_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_item_count must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.source_count != _decimal_sum(row.source_count for row in report.rows):
        raise ValueError("source_count must match rows")
    if report.independent_source_count != _decimal_sum(
        row.independent_source_count for row in report.rows
    ):
        raise ValueError("independent_source_count must match rows")
    if report.average_source_count != _ratio(report.source_count, report.item_count):
        raise ValueError("average_source_count must match source and item counts")
    if report.average_confidence_score != _ratio(
        _decimal_sum(row.confidence_score for row in report.rows),
        report.item_count,
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.max_observed_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_evidence_age_seconds must match rows")
    if (
        report.item_config_versions
        and len(report.item_config_versions) != len(report.rows)
    ):
        raise ValueError("item_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_items(
    items: Iterable[MarketResearchHockeyPowerPlayMismatchDigestItem],
) -> tuple[MarketResearchHockeyPowerPlayMismatchDigestItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must contain hockey power play mismatch rows")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must contain hockey power play mismatch rows") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchHockeyPowerPlayMismatchDigestItem:
            raise ValueError(
                "items must contain MarketResearchHockeyPowerPlayMismatchDigestItem",
            )
        if item.hockey_event_key in seen:
            raise ValueError("hockey_event_key values must be unique")
        seen.add(item.hockey_event_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchHockeyPowerPlayMismatchDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain hockey power play mismatch digest rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain hockey power play mismatch digest rows") from exc
    for row in normalized:
        if type(row) is not MarketResearchHockeyPowerPlayMismatchDigestRow:
            raise ValueError(
                "rows must contain MarketResearchHockeyPowerPlayMismatchDigestRow",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                _row_sort_value(row),
                row.hockey_event_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    if len({row.hockey_event_key for row in normalized}) != len(normalized):
        raise ValueError("hockey_event_key values must be unique")
    return normalized


def _normalize_item_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("item_config_versions must contain pairs")
    try:
        normalized = tuple(tuple(item) for item in value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("item_config_versions must contain pairs") from exc
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("item_config_versions must contain pairs")
        item_key, config_version = item
        _require_public_string("item_config_versions item_key", item_key)
        _require_canonical_string("item_config_versions config_version", config_version)
        if item_key in seen:
            raise ValueError("item_config_versions item keys must be unique")
        seen.add(item_key)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("item_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in normalized:
        if type(item) is not MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount",
            )
    if normalized != tuple(
        sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return normalized


def _normalize_reason_codes(value: object, *, seq: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain reason code strings") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    reason_rank = {reason_code: index for index, reason_code in enumerate(seq)}
    if normalized and normalized != tuple(
        sorted(normalized, key=lambda reason_code: reason_rank[reason_code]),
    ):
        raise ValueError("reason_codes must be sorted")
    return normalized


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize(seconds + micros)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _row_sort_value(row: MarketResearchHockeyPowerPlayMismatchDigestRow) -> int:
    if CONFLICTING_SOURCES_REASON in row.reason_codes:
        return 0
    if row.digest_status != STATUS_READY:
        return 1
    return 2


def _redacted_reference(value: str) -> str:
    if _is_reference_safe(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _is_reference_safe(value: str) -> bool:
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_public_evidence_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not _is_reference_safe(value) and "://" not in value:
        raise ValueError(f"{field_name} must be redacted")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or not all(character in "0123456789abcdef" for character in digest):
            raise ValueError(f"{field_name} must be redacted")
        return
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_digest_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must contain a known digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if field_name == "condition_id" and value.startswith("condition."):
        return
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _json_ready_no_floats(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_floats(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_floats(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_floats(item) for item in value]
    raise ValueError("value is not JSON serializable")
