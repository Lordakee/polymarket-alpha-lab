"""Pure reducer for team memory market-regime learning digest reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import re

from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_MEMORY_MARKET_REGIME_LEARNING_DIGEST_CONFIG_VERSION = (
    "team-memory-market-regime-learning-digest-v0"
)

PASS_REASON = "team_memory_market_regime_learning_digest_passed"
WATCH_REASON = (
    "team_memory_market_regime_learning_digest_watch_learning_signals_present"
)
BLOCKED_REASON = (
    "team_memory_market_regime_learning_digest_blocked_learning_signals_present"
)
EMPTY_REASON = "team_memory_market_regime_learning_digest_empty_sources"

SOURCE_PASS_REASON = "team_memory_market_regime_learning_digest_pass_learning_signal"
SOURCE_WATCH_REASON = "team_memory_market_regime_learning_digest_watch_learning_signal"
SOURCE_BLOCKED_REASON = (
    "team_memory_market_regime_learning_digest_blocked_learning_signal"
)

REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCKED_REASON, EMPTY_REASON)
SOURCE_REASON_CODES = (SOURCE_PASS_REASON, SOURCE_WATCH_REASON, SOURCE_BLOCKED_REASON)

NEXT_STEPS = {
    "pass": "allow_market_regime_learning_use",
    "watch": "review_market_regime_learning_digest",
    "blocked": "block_market_regime_learning_use",
}

_ZERO = Decimal("0")
_ONE = Decimal("1")
_HIGH_CONFIDENCE_THRESHOLD = Decimal("0.70")
_WATCH_CONFIDENCE_THRESHOLD = Decimal("0.50")
_WATCH_SURPRISE_THRESHOLD = Decimal("0.50")
_BLOCKED_CONFIDENCE_THRESHOLD = Decimal("0.40")
_BLOCKED_SURPRISE_THRESHOLD = Decimal("0.80")
_REDACTED_QUERY_PATTERN = re.compile(r"([?&])[^#\s]*")
_SENSITIVE_TOKEN_PATTERN = re.compile(
    r"\b(auth|bearer|broker|key|private_key|secret|signature|token|wallet)\b",
    re.IGNORECASE,
)

__all__ = (
    "DEFAULT_TEAM_MEMORY_MARKET_REGIME_LEARNING_DIGEST_CONFIG_VERSION",
    "PASS_REASON",
    "WATCH_REASON",
    "BLOCKED_REASON",
    "EMPTY_REASON",
    "SOURCE_PASS_REASON",
    "SOURCE_WATCH_REASON",
    "SOURCE_BLOCKED_REASON",
    "TeamMemoryMarketRegimeLearningDigestConfig",
    "TeamMemoryMarketRegimeLearningDigestSource",
    "TeamMemoryMarketRegimeLearningDigestSourceStatus",
    "TeamMemoryMarketRegimeLearningDigestReasonCodeCount",
    "TeamMemoryMarketRegimeLearningDigestReport",
    "build_team_memory_market_regime_learning_digest_report",
)


@dataclass(frozen=True)
class TeamMemoryMarketRegimeLearningDigestConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_MARKET_REGIME_LEARNING_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamMemoryMarketRegimeLearningDigestSource:
    team_id: str
    market_slug: str
    regime_label: str
    learning_signal: str
    observation_count: Decimal
    confidence_ratio: Decimal
    surprise_ratio: Decimal
    reference: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamMemoryMarketRegimeLearningDigestSource:
            raise ValueError(
                "source must be exactly TeamMemoryMarketRegimeLearningDigestSource"
            )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("regime_label", self.regime_label)
        _require_canonical_string("learning_signal", self.learning_signal)
        _require_nonnegative_count_decimal("observation_count", self.observation_count)
        _require_probability_decimal("confidence_ratio", self.confidence_ratio)
        _require_probability_decimal("surprise_ratio", self.surprise_ratio)
        _require_canonical_string("reference", self.reference)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class TeamMemoryMarketRegimeLearningDigestSourceStatus:
    team_id: str
    market_slug: str
    regime_label: str
    learning_signal: str
    observation_count: Decimal
    confidence_ratio: Decimal
    surprise_ratio: Decimal
    redacted_reference: str
    observed_at: datetime
    source_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("regime_label", self.regime_label)
        _require_canonical_string("learning_signal", self.learning_signal)
        _require_nonnegative_count_decimal("observation_count", self.observation_count)
        _require_probability_decimal("confidence_ratio", self.confidence_ratio)
        _require_probability_decimal("surprise_ratio", self.surprise_ratio)
        _require_canonical_string("redacted_reference", self.redacted_reference)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_digest_status("source_status", self.source_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes(self.reason_codes),
        )
        if self.source_status != _expected_source_status(self.reason_codes):
            raise ValueError("source_status must match reason_codes")
        _require_hard_flags("source_status", self)


@dataclass(frozen=True)
class TeamMemoryMarketRegimeLearningDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_reason_code("reason_code", self.reason_code)
        _require_positive_count_decimal("count", self.count)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamMemoryMarketRegimeLearningDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_confidence_ratio: Decimal | None
    average_surprise_ratio: Decimal | None
    source_statuses: tuple[TeamMemoryMarketRegimeLearningDigestSourceStatus, ...]
    reason_code_counts: tuple[TeamMemoryMarketRegimeLearningDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_count_decimal("source_count", self.source_count)
        _require_nonnegative_count_decimal("pass_count", self.pass_count)
        _require_nonnegative_count_decimal("watch_count", self.watch_count)
        _require_nonnegative_count_decimal("blocked_count", self.blocked_count)
        if self.average_confidence_ratio is not None:
            _require_probability_decimal(
                "average_confidence_ratio",
                self.average_confidence_ratio,
            )
        if self.average_surprise_ratio is not None:
            _require_probability_decimal(
                "average_surprise_ratio",
                self.average_surprise_ratio,
            )
        object.__setattr__(
            self,
            "source_statuses",
            _normalize_source_statuses(self.source_statuses),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_memory_market_regime_learning_digest_report(
    sources: list[TeamMemoryMarketRegimeLearningDigestSource]
    | tuple[TeamMemoryMarketRegimeLearningDigestSource, ...],
    *,
    config: TeamMemoryMarketRegimeLearningDigestConfig,
    generated_at: datetime,
) -> TeamMemoryMarketRegimeLearningDigestReport:
    if type(config) is not TeamMemoryMarketRegimeLearningDigestConfig:
        raise ValueError(
            "config must be a TeamMemoryMarketRegimeLearningDigestConfig"
        )
    _require_hard_flags("config", config)

    normalized_sources = _normalize_sources(sources)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_statuses = _source_statuses(normalized_sources)
    pass_count = _decimal_count(
        sum(1 for status in source_statuses if status.source_status == "pass")
    )
    watch_count = _decimal_count(
        sum(1 for status in source_statuses if status.source_status == "watch")
    )
    blocked_count = _decimal_count(
        sum(1 for status in source_statuses if status.source_status == "blocked")
    )
    reason_codes = _digest_reason_codes(
        source_count=_decimal_count(len(source_statuses)),
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    digest_status = _expected_digest_status(reason_codes)

    return TeamMemoryMarketRegimeLearningDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        source_count=_decimal_count(len(source_statuses)),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_confidence_ratio=_average_ratio(
            tuple(status.confidence_ratio for status in source_statuses),
        ),
        average_surprise_ratio=_average_ratio(
            tuple(status.surprise_ratio for status in source_statuses),
        ),
        source_statuses=source_statuses,
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_sources(
    sources: list[TeamMemoryMarketRegimeLearningDigestSource]
    | tuple[TeamMemoryMarketRegimeLearningDigestSource, ...],
) -> tuple[TeamMemoryMarketRegimeLearningDigestSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized_sources = tuple(sources)
    seen_keys: set[tuple[str, str]] = set()
    for source in normalized_sources:
        if type(source) is not TeamMemoryMarketRegimeLearningDigestSource:
            raise ValueError(
                "sources must contain TeamMemoryMarketRegimeLearningDigestSource"
            )
        _require_hard_flags("source", source)
        key = (source.team_id, source.market_slug)
        if key in seen_keys:
            raise ValueError("sources team_id and market_slug values must be unique")
        seen_keys.add(key)
    return normalized_sources


def _source_statuses(
    sources: tuple[TeamMemoryMarketRegimeLearningDigestSource, ...],
) -> tuple[TeamMemoryMarketRegimeLearningDigestSourceStatus, ...]:
    return tuple(
        sorted(
            (
                TeamMemoryMarketRegimeLearningDigestSourceStatus(
                    team_id=source.team_id,
                    market_slug=source.market_slug,
                    regime_label=source.regime_label,
                    learning_signal=source.learning_signal,
                    observation_count=source.observation_count,
                    confidence_ratio=source.confidence_ratio,
                    surprise_ratio=source.surprise_ratio,
                    redacted_reference=_redacted_reference(source.reference),
                    observed_at=source.observed_at,
                    source_status=_source_status(source),
                    reason_codes=_source_reason_codes(source),
                )
                for source in sources
            ),
            key=lambda status: (status.team_id, status.market_slug),
        )
    )


def _source_status(source: TeamMemoryMarketRegimeLearningDigestSource) -> str:
    return _expected_source_status(_source_reason_codes(source))


def _source_reason_codes(
    source: TeamMemoryMarketRegimeLearningDigestSource,
) -> tuple[str, ...]:
    signal = source.learning_signal
    if (
        "contradictory" in signal
        or "blocked" in signal
        or source.confidence_ratio < _BLOCKED_CONFIDENCE_THRESHOLD
        or source.surprise_ratio >= _BLOCKED_SURPRISE_THRESHOLD
    ):
        return (SOURCE_BLOCKED_REASON,)
    if (
        "thin" in signal
        or "unstable" in signal
        or source.confidence_ratio < _HIGH_CONFIDENCE_THRESHOLD
        or source.surprise_ratio >= _WATCH_SURPRISE_THRESHOLD
    ):
        return (SOURCE_WATCH_REASON,)
    return (SOURCE_PASS_REASON,)


def _digest_reason_codes(
    *,
    source_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> tuple[str, ...]:
    if source_count == _ZERO:
        return (EMPTY_REASON,)
    if blocked_count > _ZERO:
        return (BLOCKED_REASON,)
    if watch_count > _ZERO:
        return (WATCH_REASON,)
    return (PASS_REASON,)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[TeamMemoryMarketRegimeLearningDigestReasonCodeCount, ...]:
    return tuple(
        TeamMemoryMarketRegimeLearningDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return (sum(values, _ZERO) / _decimal_count(len(values))).quantize(Decimal("0.01"))


def _validate_report_consistency(
    report: TeamMemoryMarketRegimeLearningDigestReport,
) -> None:
    if report.source_count != _decimal_count(len(report.source_statuses)):
        raise ValueError("source_count must match source_statuses")
    expected_pass_count = _decimal_count(
        sum(1 for status in report.source_statuses if status.source_status == "pass")
    )
    expected_watch_count = _decimal_count(
        sum(1 for status in report.source_statuses if status.source_status == "watch")
    )
    expected_blocked_count = _decimal_count(
        sum(1 for status in report.source_statuses if status.source_status == "blocked")
    )
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match source_statuses")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match source_statuses")
    if report.blocked_count != expected_blocked_count:
        raise ValueError("blocked_count must match source_statuses")
    if report.average_confidence_ratio != _average_ratio(
        tuple(status.confidence_ratio for status in report.source_statuses)
    ):
        raise ValueError("average_confidence_ratio must match source_statuses")
    if report.average_surprise_ratio != _average_ratio(
        tuple(status.surprise_ratio for status in report.source_statuses)
    ):
        raise ValueError("average_surprise_ratio must match source_statuses")
    expected_reason_codes = _digest_reason_codes(
        source_count=report.source_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match digest status inputs")
    expected_digest_status = _expected_digest_status(report.reason_codes)
    if report.digest_status != expected_digest_status:
        raise ValueError("digest_status must match reason_codes")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must summarize reason_codes")


def _normalize_source_statuses(
    source_statuses: tuple[TeamMemoryMarketRegimeLearningDigestSourceStatus, ...],
) -> tuple[TeamMemoryMarketRegimeLearningDigestSourceStatus, ...]:
    if type(source_statuses) not in (list, tuple):
        raise ValueError("source_statuses must be a list or tuple")
    statuses = tuple(source_statuses)
    seen_keys: set[tuple[str, str]] = set()
    for status in statuses:
        if type(status) is not TeamMemoryMarketRegimeLearningDigestSourceStatus:
            raise ValueError("source_statuses must contain source status rows")
        _require_hard_flags("source_status", status)
        key = (status.team_id, status.market_slug)
        if key in seen_keys:
            raise ValueError(
                "source_statuses team_id and market_slug values must be unique"
            )
        seen_keys.add(key)
    if tuple((status.team_id, status.market_slug) for status in statuses) != tuple(
        sorted((status.team_id, status.market_slug) for status in statuses)
    ):
        raise ValueError("source_statuses must be sorted by team_id and market_slug")
    return statuses


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        TeamMemoryMarketRegimeLearningDigestReasonCodeCount,
        ...,
    ],
) -> tuple[TeamMemoryMarketRegimeLearningDigestReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not TeamMemoryMarketRegimeLearningDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts)
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(reason_codes)
    if not codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in codes:
        _require_digest_reason_code("reason_codes", reason_code)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    return codes


def _normalize_source_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("source reason_codes must be a list or tuple")
    codes = tuple(reason_codes)
    if not codes:
        raise ValueError("source reason_codes must contain at least one value")
    for reason_code in codes:
        _require_source_reason_code("source reason_codes", reason_code)
    if len(set(codes)) != len(codes):
        raise ValueError("source reason_codes must be unique")
    return codes


def _expected_digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if reason_codes == (WATCH_REASON,):
        return "watch"
    if reason_codes in ((BLOCKED_REASON,), (EMPTY_REASON,)):
        return "blocked"
    raise ValueError("reason_codes must contain known digest reasons")


def _expected_source_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (SOURCE_PASS_REASON,):
        return "pass"
    if reason_codes == (SOURCE_WATCH_REASON,):
        return "watch"
    if reason_codes == (SOURCE_BLOCKED_REASON,):
        return "blocked"
    raise ValueError("source reason_codes must contain known source reasons")


def _redacted_reference(value: str) -> str:
    redacted = _REDACTED_QUERY_PATTERN.sub(r"\1[redacted]", value)
    return _SENSITIVE_TOKEN_PATTERN.sub("[redacted]", redacted)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEPS:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_digest_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known digest reason codes")


def _require_source_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SOURCE_REASON_CODES:
        raise ValueError(f"{field_name} must contain known source reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_probability_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_nonnegative_count_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_count_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
