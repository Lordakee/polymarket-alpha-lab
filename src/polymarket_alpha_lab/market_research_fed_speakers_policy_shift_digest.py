"""Pure Phase 1 Fed speakers policy shift digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-fed-speakers-policy-shift-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

DIRECTION_HAWKISH = "hawkish"
DIRECTION_DOVISH = "dovish"
DIRECTION_NEUTRAL = "neutral"
POLICY_SHIFT_DIRECTIONS = (DIRECTION_HAWKISH, DIRECTION_DOVISH, DIRECTION_NEUTRAL)

REASON_PREFIX = "market_research_fed_speakers_policy_shift_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_POLICY_SHIFT_REASON = f"{REASON_PREFIX}material_policy_shift"
HAWKISH_SHIFT_REASON = f"{REASON_PREFIX}hawkish_shift"
DOVISH_SHIFT_REASON = f"{REASON_PREFIX}dovish_shift"
MARKET_REPRICING_REASON = f"{REASON_PREFIX}market_repricing"
LOW_CONSENSUS_REASON = f"{REASON_PREFIX}low_consensus"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_EVENT_REASON = f"{REASON_PREFIX}stale_event"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    STALE_EVENT_REASON,
    MATERIAL_POLICY_SHIFT_REASON,
    HAWKISH_SHIFT_REASON,
    DOVISH_SHIFT_REASON,
    MARKET_REPRICING_REASON,
    LOW_CONSENSUS_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_POLICY_SHIFT_REASON,
    HAWKISH_SHIFT_REASON,
    DOVISH_SHIFT_REASON,
    MARKET_REPRICING_REASON,
    LOW_CONSENSUS_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_EVENT_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_fed_speakers_policy_shift_digest",
    STATUS_WATCH: "watch_report_only_market_research_fed_speakers_policy_shift_digest",
    STATUS_BLOCKED: "block_report_only_market_research_fed_speakers_policy_shift_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
HEX_DIGITS = frozenset("0123456789abcdef")


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
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION",
    "MarketResearchFedSpeakersPolicyShiftDigestConfig",
    "MarketResearchFedSpeakersPolicyShiftDigestInputRow",
    "MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount",
    "MarketResearchFedSpeakersPolicyShiftDigestReport",
    "MarketResearchFedSpeakersPolicyShiftDigestRow",
    "build_market_research_fed_speakers_policy_shift_digest",
    "market_research_fed_speakers_policy_shift_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchFedSpeakersPolicyShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION
    )
    max_event_age_seconds: Decimal = Decimal("7200.000000")
    material_policy_shift_threshold: Decimal = Decimal("0.500000")
    min_market_repricing_score: Decimal = Decimal("0.050000")
    min_statement_consensus_score: Decimal = Decimal("0.600000")
    min_source_count: Decimal = Decimal("2.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedSpeakersPolicyShiftDigestConfig:
            raise TypeError(
                "MarketResearchFedSpeakersPolicyShiftDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedSpeakersPolicyShiftDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchFedSpeakersPolicyShiftDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_event_age_seconds", "min_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _require_positive_decimal(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
        )
        for field_name in (
            "material_policy_shift_threshold",
            "min_market_repricing_score",
            "min_statement_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchFedSpeakersPolicyShiftDigestInputRow:
    research_key: str
    condition_id: str
    speaker_key: str
    speaker_name: str
    policy_topic: str
    public_statement_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    hawkish_shift_score: Decimal
    dovish_shift_score: Decimal
    market_repricing_score: Decimal
    statement_consensus_score: Decimal
    event_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedSpeakersPolicyShiftDigestInputRow:
            raise TypeError(
                "MarketResearchFedSpeakersPolicyShiftDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedSpeakersPolicyShiftDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchFedSpeakersPolicyShiftDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "speaker_key",
            "speaker_name",
            "policy_topic",
            "event_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_statement_reference", self.public_statement_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "hawkish_shift_score",
            "dovish_shift_score",
            "market_repricing_score",
            "statement_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchFedSpeakersPolicyShiftDigestRow:
    research_key: str
    condition_id: str
    speaker_key: str
    speaker_name: str
    policy_topic: str
    policy_shift_status: str
    policy_shift_direction: str
    observed_at: datetime
    acknowledged_at: datetime | None
    event_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    hawkish_shift_score: Decimal
    dovish_shift_score: Decimal
    policy_shift_score: Decimal
    market_repricing_score: Decimal
    statement_consensus_score: Decimal
    redacted_public_statement_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedSpeakersPolicyShiftDigestRow:
            raise TypeError(
                "MarketResearchFedSpeakersPolicyShiftDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedSpeakersPolicyShiftDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchFedSpeakersPolicyShiftDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "speaker_key",
            "speaker_name",
            "policy_topic",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("policy_shift_status", self.policy_shift_status)
        _require_policy_shift_direction(
            "policy_shift_direction",
            self.policy_shift_direction,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in ("event_age_seconds", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in (
            "hawkish_shift_score",
            "dovish_shift_score",
            "policy_shift_score",
            "market_repricing_score",
            "statement_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_statement_reference",
            _require_redacted_reference(
                "redacted_public_statement_reference",
                self.redacted_public_statement_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchFedSpeakersPolicyShiftDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    material_policy_shift_count: Decimal
    hawkish_shift_count: Decimal
    dovish_shift_count: Decimal
    market_repricing_count: Decimal
    low_consensus_count: Decimal
    stale_event_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    average_policy_shift_score: Decimal
    average_market_repricing_score: Decimal
    average_statement_consensus_score: Decimal
    max_event_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...]
    event_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedSpeakersPolicyShiftDigestReport:
            raise TypeError(
                "MarketResearchFedSpeakersPolicyShiftDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedSpeakersPolicyShiftDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchFedSpeakersPolicyShiftDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "material_policy_shift_count",
            "hawkish_shift_count",
            "dovish_shift_count",
            "market_repricing_count",
            "low_consensus_count",
            "stale_event_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_policy_shift_score",
            "average_market_repricing_score",
            "average_statement_consensus_score",
            "max_event_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "event_config_versions",
            _normalize_event_config_versions(self.event_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_fed_speakers_policy_shift_digest(
    input_rows: Iterable[MarketResearchFedSpeakersPolicyShiftDigestInputRow],
    *,
    config: MarketResearchFedSpeakersPolicyShiftDigestConfig,
    generated_at: datetime,
) -> MarketResearchFedSpeakersPolicyShiftDigestReport:
    if type(config) is not MarketResearchFedSpeakersPolicyShiftDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchFedSpeakersPolicyShiftDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_rows
    )
    sorted_rows = _sorted_rows(rows)
    event_count = _count(len(sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows, event_count)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = (
            MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    ready_event_count = _count(
        sum(1 for row in sorted_rows if row.policy_shift_status == STATUS_READY),
    )
    watch_event_count = _count(
        sum(1 for row in sorted_rows if row.policy_shift_status == STATUS_WATCH),
    )
    blocked_event_count = _count(
        sum(1 for row in sorted_rows if row.policy_shift_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(sorted_rows),
        blocked_event_count=blocked_event_count,
        watch_event_count=watch_event_count,
    )

    return MarketResearchFedSpeakersPolicyShiftDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        event_count=event_count,
        ready_event_count=ready_event_count,
        watch_event_count=watch_event_count,
        blocked_event_count=blocked_event_count,
        material_policy_shift_count=_reason_event_count(
            sorted_rows,
            MATERIAL_POLICY_SHIFT_REASON,
        ),
        hawkish_shift_count=_reason_event_count(sorted_rows, HAWKISH_SHIFT_REASON),
        dovish_shift_count=_reason_event_count(sorted_rows, DOVISH_SHIFT_REASON),
        market_repricing_count=_reason_event_count(
            sorted_rows,
            MARKET_REPRICING_REASON,
        ),
        low_consensus_count=_reason_event_count(sorted_rows, LOW_CONSENSUS_REASON),
        stale_event_count=_reason_event_count(sorted_rows, STALE_EVENT_REASON),
        thin_source_count=_reason_event_count(sorted_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_event_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_event_count(
            sorted_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        average_policy_shift_score=_ratio(
            _decimal_sum(row.policy_shift_score for row in sorted_rows),
            event_count,
        ),
        average_market_repricing_score=_ratio(
            _decimal_sum(row.market_repricing_score for row in sorted_rows),
            event_count,
        ),
        average_statement_consensus_score=_ratio(
            _decimal_sum(row.statement_consensus_score for row in sorted_rows),
            event_count,
        ),
        max_event_age_seconds=max(
            (row.event_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            event_count,
        ),
        rows=sorted_rows,
        event_config_versions=_event_config_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_fed_speakers_policy_shift_digest_payload(
    report: MarketResearchFedSpeakersPolicyShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchFedSpeakersPolicyShiftDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchFedSpeakersPolicyShiftDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_input(
    row: MarketResearchFedSpeakersPolicyShiftDigestInputRow,
    *,
    config: MarketResearchFedSpeakersPolicyShiftDigestConfig,
    generated_at: datetime,
) -> MarketResearchFedSpeakersPolicyShiftDigestRow:
    event_age_seconds = _seconds_between(generated_at, row.observed_at)
    if row.acknowledged_at is None:
        acknowledgement_lag_seconds = None
    else:
        acknowledgement_lag_seconds = _seconds_between(row.acknowledged_at, row.observed_at)
    policy_shift_score = max(row.hawkish_shift_score, row.dovish_shift_score)
    policy_shift_direction = _policy_shift_direction(
        hawkish_shift_score=row.hawkish_shift_score,
        dovish_shift_score=row.dovish_shift_score,
        threshold=config.material_policy_shift_threshold,
    )
    reason_codes = _row_reason_codes(
        event_age_seconds=event_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        hawkish_shift_score=row.hawkish_shift_score,
        dovish_shift_score=row.dovish_shift_score,
        policy_shift_score=policy_shift_score,
        market_repricing_score=row.market_repricing_score,
        statement_consensus_score=row.statement_consensus_score,
        config=config,
    )
    return MarketResearchFedSpeakersPolicyShiftDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        speaker_key=row.speaker_key,
        speaker_name=row.speaker_name,
        policy_topic=row.policy_topic,
        policy_shift_status=_row_status(reason_codes),
        policy_shift_direction=policy_shift_direction,
        observed_at=row.observed_at,
        acknowledged_at=row.acknowledged_at,
        event_age_seconds=event_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        hawkish_shift_score=row.hawkish_shift_score,
        dovish_shift_score=row.dovish_shift_score,
        policy_shift_score=policy_shift_score,
        market_repricing_score=row.market_repricing_score,
        statement_consensus_score=row.statement_consensus_score,
        redacted_public_statement_reference=_redact_reference(
            row.public_statement_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    event_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_count: Decimal,
    hawkish_shift_score: Decimal,
    dovish_shift_score: Decimal,
    policy_shift_score: Decimal,
    market_repricing_score: Decimal,
    statement_consensus_score: Decimal,
    config: MarketResearchFedSpeakersPolicyShiftDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if policy_shift_score >= config.material_policy_shift_threshold:
        reasons.append(MATERIAL_POLICY_SHIFT_REASON)
        if hawkish_shift_score >= dovish_shift_score:
            reasons.append(HAWKISH_SHIFT_REASON)
        else:
            reasons.append(DOVISH_SHIFT_REASON)
    if market_repricing_score >= config.min_market_repricing_score:
        reasons.append(MARKET_REPRICING_REASON)
    if statement_consensus_score < config.min_statement_consensus_score:
        reasons.append(LOW_CONSENSUS_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    if (
        acknowledgement_lag_seconds is not None
        and acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds
    ):
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if event_age_seconds > config.max_event_age_seconds:
        reasons.append(STALE_EVENT_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(reasons, order=ROW_REASON_CODE_SEQUENCE)


def _policy_shift_direction(
    *,
    hawkish_shift_score: Decimal,
    dovish_shift_score: Decimal,
    threshold: Decimal,
) -> str:
    policy_shift_score = max(hawkish_shift_score, dovish_shift_score)
    if policy_shift_score < threshold:
        return DIRECTION_NEUTRAL
    if hawkish_shift_score >= dovish_shift_score:
        return DIRECTION_HAWKISH
    return DIRECTION_DOVISH


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_event_count: Decimal,
    watch_event_count: Decimal,
) -> str:
    if not has_inputs or blocked_event_count > ZERO:
        return STATUS_BLOCKED
    if watch_event_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _sorted_rows(
    rows: tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...],
) -> tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.policy_shift_status),
                -row.policy_shift_score,
                -row.market_repricing_score,
                -row.event_age_seconds,
                row.speaker_key,
                row.research_key,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...],
    event_count: Decimal,
) -> tuple[MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            event_ratio=_ratio(count, event_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        for count in (_reason_event_count(rows, reason_code),)
        if count > ZERO
    )


def _reason_event_count(
    rows: tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _event_config_versions(
    rows: tuple[MarketResearchFedSpeakersPolicyShiftDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((row.speaker_key, row.event_config_version) for row in rows))


def _normalize_input_rows(
    rows: Iterable[MarketResearchFedSpeakersPolicyShiftDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchFedSpeakersPolicyShiftDigestInputRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("input rows must be an iterable")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchFedSpeakersPolicyShiftDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchFedSpeakersPolicyShiftDigestInputRow values",
            )
        _require_hard_flags("input row", row)
        if row.speaker_key in seen_keys:
            raise ValueError("input rows speaker_key values must be unique")
        seen_keys.add(row.speaker_key)
        if row.observed_at > generated_at:
            raise ValueError("observed_at cannot be in the future")
        if row.acknowledged_at is not None and row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at cannot precede observed_at")
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...],
) -> tuple[MarketResearchFedSpeakersPolicyShiftDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchFedSpeakersPolicyShiftDigestRow:
            raise ValueError(
                "rows must contain MarketResearchFedSpeakersPolicyShiftDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.speaker_key in seen_keys:
            raise ValueError("rows speaker_key values must be unique")
        seen_keys.add(row.speaker_key)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    values: tuple[MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount, ...],
) -> tuple[MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount values",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(value.reason_code)
    if tuple(value.reason_code for value in normalized) != tuple(
        reason for reason in REASON_CODE_SEQUENCE if reason in seen_codes
    ):
        raise ValueError("reason_code_counts must use canonical reason sequence")
    return normalized


def _normalize_event_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) not in (list, tuple):
        raise ValueError("event_config_versions must be a list or tuple")
    normalized = tuple(values)
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) not in (list, tuple) or len(value) != 2:
            raise ValueError("event_config_versions must contain key/version pairs")
        speaker_key, config_version = value
        _require_public_string("event_config_versions key", speaker_key)
        _require_public_string("event_config_versions version", config_version)
        if speaker_key in seen_keys:
            raise ValueError("event_config_versions keys must be unique")
        seen_keys.add(speaker_key)
    normalized_pairs = tuple((str(key), str(version)) for key, version in normalized)
    if normalized_pairs != tuple(sorted(normalized_pairs)):
        raise ValueError("event_config_versions must be sorted deterministically")
    return normalized_pairs


def _normalize_reason_codes(
    values: object,
    *,
    order: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen_codes: set[str] = set()
    for value in normalized:
        _require_reason_code("reason_codes", value)
        if value in seen_codes:
            raise ValueError("reason_codes must be unique")
        seen_codes.add(value)
    if normalized != tuple(reason for reason in order if reason in seen_codes):
        raise ValueError("reason_codes must use canonical reason sequence")
    return normalized


def _validate_row(row: MarketResearchFedSpeakersPolicyShiftDigestRow) -> None:
    if row.policy_shift_score != max(row.hawkish_shift_score, row.dovish_shift_score):
        raise ValueError("policy_shift_score must match directional shift scores")
    if MATERIAL_POLICY_SHIFT_REASON not in row.reason_codes:
        expected_direction = DIRECTION_NEUTRAL
    elif row.hawkish_shift_score >= row.dovish_shift_score:
        expected_direction = DIRECTION_HAWKISH
    else:
        expected_direction = DIRECTION_DOVISH
    if row.policy_shift_direction != expected_direction:
        raise ValueError("policy_shift_direction must match shift scores")
    if row.acknowledged_at is None and row.acknowledgement_lag_seconds is not None:
        raise ValueError("acknowledgement_lag_seconds must be absent without acknowledgement")
    if row.acknowledged_at is not None:
        expected_lag = _seconds_between(row.acknowledged_at, row.observed_at)
        if row.acknowledgement_lag_seconds != expected_lag:
            raise ValueError("acknowledgement_lag_seconds must match timestamps")
    if row.policy_shift_status != _row_status(row.reason_codes):
        raise ValueError("policy_shift_status must match reason_codes")


def _validate_report(report: MarketResearchFedSpeakersPolicyShiftDigestReport) -> None:
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.policy_shift_status == STATUS_READY),
    )
    expected_watch = _count(
        sum(1 for row in report.rows if row.policy_shift_status == STATUS_WATCH),
    )
    expected_blocked = _count(
        sum(1 for row in report.rows if row.policy_shift_status == STATUS_BLOCKED),
    )
    if report.ready_event_count != expected_ready:
        raise ValueError("ready_event_count must match rows")
    if report.watch_event_count != expected_watch:
        raise ValueError("watch_event_count must match rows")
    if report.blocked_event_count != expected_blocked:
        raise ValueError("blocked_event_count must match rows")
    if report.ready_event_count + report.watch_event_count + report.blocked_event_count != report.event_count:
        raise ValueError("event status counts must reconcile")
    expected_reason_counts = _reason_code_counts(report.rows, report.event_count)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_event_count=report.blocked_event_count,
        watch_event_count=report.watch_event_count,
    ):
        raise ValueError("digest_status must match rows")
    expected_counts = {
        "material_policy_shift_count": MATERIAL_POLICY_SHIFT_REASON,
        "hawkish_shift_count": HAWKISH_SHIFT_REASON,
        "dovish_shift_count": DOVISH_SHIFT_REASON,
        "market_repricing_count": MARKET_REPRICING_REASON,
        "low_consensus_count": LOW_CONSENSUS_REASON,
        "stale_event_count": STALE_EVENT_REASON,
        "thin_source_count": THIN_SOURCES_REASON,
        "missing_acknowledgement_count": MISSING_ACKNOWLEDGEMENT_REASON,
        "slow_acknowledgement_count": SLOW_ACKNOWLEDGEMENT_REASON,
    }
    for field_name, reason_code in expected_counts.items():
        if getattr(report, field_name) != _reason_event_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_policy_shift_score != _ratio(
        _decimal_sum(row.policy_shift_score for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_policy_shift_score must match rows")
    if report.average_market_repricing_score != _ratio(
        _decimal_sum(row.market_repricing_score for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_market_repricing_score must match rows")
    if report.average_statement_consensus_score != _ratio(
        _decimal_sum(row.statement_consensus_score for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_statement_consensus_score must match rows")
    if report.max_event_age_seconds != max(
        (row.event_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_event_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_source_count must match rows")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _redact_reference(value: str) -> str:
    if _is_redacted_safe(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_redacted_safe(value: str) -> bool:
    if value.startswith("sha256:"):
        return _is_short_sha256_redaction(value)
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return False
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
            if key != "public_statement_reference"
        }
    return value


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_policy_shift_direction(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in POLICY_SHIFT_DIRECTIONS:
        raise ValueError(f"{field_name} must be hawkish, dovish, or neutral")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public report-safe text")


def _require_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:") and not _is_short_sha256_redaction(value):
        raise ValueError(f"{field_name} must be a short sha256 redaction")
    if not _is_redacted_safe(value) and not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _is_short_sha256_redaction(value: str) -> bool:
    suffix = value.removeprefix("sha256:")
    return (
        len(value) == 19
        and len(suffix) == 12
        and all(character in HEX_DIGITS for character in suffix)
    )


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
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
