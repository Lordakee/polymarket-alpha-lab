"""Pure in-memory team-memory source reliability scorecard digest."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DEFAULT_TEAM_MEMORY_SOURCE_RELIABILITY_SCORECARD_DIGEST_CONFIG_VERSION = (
    "team-memory-source-reliability-scorecard-digest-v0"
)

RELIABILITY_STATUSES = ("pass", "watch", "blocked")

ROW_REASON_CODES = (
    "team_memory_source_reliability_scorecard_digest_row_high_contradiction_rate",
    "team_memory_source_reliability_scorecard_digest_row_low_hit_rate",
    "team_memory_source_reliability_scorecard_digest_row_stale_source_freshness",
    "team_memory_source_reliability_scorecard_digest_row_slow_resolution_acknowledgement",
    "team_memory_source_reliability_scorecard_digest_row_low_source_family_diversity",
    "team_memory_source_reliability_scorecard_digest_row_passed",
)

REPORT_REASON_CODES = (
    "team_memory_source_reliability_scorecard_digest_empty",
    "team_memory_source_reliability_scorecard_digest_high_contradiction_rate",
    "team_memory_source_reliability_scorecard_digest_low_hit_rate",
    "team_memory_source_reliability_scorecard_digest_stale_source_freshness",
    "team_memory_source_reliability_scorecard_digest_slow_resolution_acknowledgement",
    "team_memory_source_reliability_scorecard_digest_low_source_family_diversity",
    "team_memory_source_reliability_scorecard_digest_passed",
)

_BLOCKED_IDENTIFIER_FRAGMENTS = (
    "0x",
    "@",
    "acc" "ount",
    "api" "_" "key",
    "au" "th",
    "bro" "ker",
    "can" "cel",
    "email",
    "live" "_" "trading",
    "ord" "er",
    "place" "_" "ord" "er",
    "private",
    "private" "_" "key",
    "se" "cret",
    "sig" "n",
    "sub" "mit",
    "token",
    "tra" "ding" "_" "advice",
    "wal" "let",
    "web" "3",
)

_PAYLOAD_OMIT_FIELDS = {
    "team_id",
    "category",
    "row_key",
}


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RELIABILITY_SCORECARD_DIGEST_CONFIG_VERSION",
    "TeamMemorySourceReliabilityScorecardDigestConfig",
    "TeamMemorySourceReliabilityScorecardObservation",
    "TeamMemorySourceReliabilityScorecardReasonCodeCount",
    "TeamMemorySourceReliabilityScorecardReport",
    "TeamMemorySourceReliabilityScorecardRow",
    "build_team_memory_source_reliability_scorecard_digest",
    "team_memory_source_reliability_scorecard_digest_payload",
)


@dataclass(frozen=True)
class TeamMemorySourceReliabilityScorecardDigestConfig:
    config_version: str = (
        DEFAULT_TEAM_MEMORY_SOURCE_RELIABILITY_SCORECARD_DIGEST_CONFIG_VERSION
    )
    min_hit_rate: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    max_contradiction_rate: Decimal = Decimal("0.250000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("3600.000000")
    min_source_family_diversity_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_hit_rate",
            _normalize_ratio("min_hit_rate", self.min_hit_rate),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_contradiction_rate",
            _normalize_ratio("max_contradiction_rate", self.max_contradiction_rate),
        )
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _normalize_nonnegative_decimal(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_family_diversity_ratio",
            _normalize_ratio(
                "min_source_family_diversity_ratio",
                self.min_source_family_diversity_ratio,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceReliabilityScorecardObservation:
    team_id: str
    category: str
    source_ref: str
    source_family: str
    observed_at: datetime
    resolved_at: datetime
    acknowledged_at: datetime
    was_hit: bool
    contradiction_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "category", "source_ref", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_redacted_identifier("source_ref", self.source_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        if type(self.was_hit) is not bool:
            raise ValueError("was_hit must be a bool")
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_integral_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class TeamMemorySourceReliabilityScorecardRow:
    row_key: str
    team_id: str
    category: str
    event_count: Decimal
    source_count: Decimal
    source_family_count: Decimal
    hit_count: Decimal
    miss_count: Decimal
    hit_rate: Decimal
    freshness_age_seconds: Decimal
    contradiction_count: Decimal
    contradiction_rate: Decimal
    acknowledgement_lag_seconds: Decimal
    source_family_diversity_ratio: Decimal
    reliability_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("row_key", "team_id", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "event_count",
            "source_count",
            "source_family_count",
            "hit_count",
            "miss_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "hit_rate",
            "contradiction_rate",
            "source_family_diversity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_age_seconds",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_reliability_status("reliability_status", self.reliability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class TeamMemorySourceReliabilityScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known report reason code")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_integral_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamMemorySourceReliabilityScorecardReport:
    generated_at: datetime
    config_version: str
    reliability_status: str
    team_category_count: Decimal
    event_count: Decimal
    source_count: Decimal
    hit_count: Decimal
    miss_count: Decimal
    hit_rate: Decimal
    freshness_age_seconds: Decimal
    contradiction_count: Decimal
    contradiction_rate: Decimal
    acknowledgement_lag_seconds: Decimal
    source_family_diversity_ratio: Decimal
    rows: tuple[TeamMemorySourceReliabilityScorecardRow, ...]
    reason_code_counts: tuple[TeamMemorySourceReliabilityScorecardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_reliability_status("reliability_status", self.reliability_status)
        for field_name in (
            "team_category_count",
            "event_count",
            "source_count",
            "hit_count",
            "miss_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "hit_rate",
            "contradiction_rate",
            "source_family_diversity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_age_seconds",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_team_memory_source_reliability_scorecard_digest(
    observations: tuple[TeamMemorySourceReliabilityScorecardObservation, ...],
    *,
    config: TeamMemorySourceReliabilityScorecardDigestConfig,
    generated_at: datetime,
) -> TeamMemorySourceReliabilityScorecardReport:
    if type(config) is not TeamMemorySourceReliabilityScorecardDigestConfig:
        raise ValueError(
            "config must be a TeamMemorySourceReliabilityScorecardDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_input = _normalize_observations(observations)
    scorecard_rows = _build_rows(
        rows_input,
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(scorecard_rows)
    return TeamMemorySourceReliabilityScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        reliability_status=_status_from_reason_codes(reason_codes),
        team_category_count=_count(len(scorecard_rows)),
        event_count=_count(len(rows_input)),
        source_count=_count(len({row.source_ref for row in rows_input})),
        hit_count=_count(sum(1 for row in rows_input if row.was_hit)),
        miss_count=_count(sum(1 for row in rows_input if not row.was_hit)),
        hit_rate=_ratio(
            _count(sum(1 for row in rows_input if row.was_hit)),
            _count(len(rows_input)),
        ),
        freshness_age_seconds=_max_age_seconds(rows_input, generated_at_utc),
        contradiction_count=sum(
            (row.contradiction_count for row in rows_input),
            ZERO,
        ).quantize(COUNT_QUANT),
        contradiction_rate=_ratio(
            sum((row.contradiction_count for row in rows_input), ZERO),
            _count(len(rows_input)),
        ),
        acknowledgement_lag_seconds=_max_ack_lag_seconds(rows_input),
        source_family_diversity_ratio=_source_family_diversity_ratio(rows_input),
        rows=scorecard_rows,
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def team_memory_source_reliability_scorecard_digest_payload(
    report: TeamMemorySourceReliabilityScorecardReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceReliabilityScorecardReport:
        raise ValueError(
            "report must be a TeamMemorySourceReliabilityScorecardReport",
        )
    _require_hard_flags("report", report)
    return _payload_value(report, _RedactionMap())


def _build_rows(
    observations: tuple[TeamMemorySourceReliabilityScorecardObservation, ...],
    *,
    config: TeamMemorySourceReliabilityScorecardDigestConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceReliabilityScorecardRow, ...]:
    groups: dict[tuple[str, str], list[TeamMemorySourceReliabilityScorecardObservation]]
    groups = defaultdict(list)
    for observation in observations:
        groups[(observation.team_id, observation.category)].append(observation)

    rows: list[TeamMemorySourceReliabilityScorecardRow] = []
    for (team_id, category), group_rows in sorted(groups.items()):
        row_observations = tuple(group_rows)
        source_refs = {row.source_ref for row in row_observations}
        source_families = {row.source_family for row in row_observations}
        event_count = _count(len(row_observations))
        hit_count = _count(sum(1 for row in row_observations if row.was_hit))
        contradiction_count = sum(
            (row.contradiction_count for row in row_observations),
            ZERO,
        ).quantize(COUNT_QUANT)
        row_values = {
            "hit_rate": _ratio(hit_count, event_count),
            "freshness_age_seconds": _max_age_seconds(row_observations, generated_at),
            "contradiction_rate": _ratio(contradiction_count, event_count),
            "acknowledgement_lag_seconds": _max_ack_lag_seconds(row_observations),
            "source_family_diversity_ratio": _ratio(
                _count(len(source_families)),
                _count(len(source_refs)),
            ),
        }
        reason_codes = _row_reason_codes(
            hit_rate=row_values["hit_rate"],
            freshness_age_seconds=row_values["freshness_age_seconds"],
            contradiction_rate=row_values["contradiction_rate"],
            acknowledgement_lag_seconds=row_values["acknowledgement_lag_seconds"],
            source_family_diversity_ratio=row_values["source_family_diversity_ratio"],
            config=config,
        )
        rows.append(
            TeamMemorySourceReliabilityScorecardRow(
                row_key=f"{team_id}|{category}",
                team_id=team_id,
                category=category,
                event_count=event_count,
                source_count=_count(len(source_refs)),
                source_family_count=_count(len(source_families)),
                hit_count=hit_count,
                miss_count=_count(sum(1 for row in row_observations if not row.was_hit)),
                hit_rate=row_values["hit_rate"],
                freshness_age_seconds=row_values["freshness_age_seconds"],
                contradiction_count=contradiction_count,
                contradiction_rate=row_values["contradiction_rate"],
                acknowledgement_lag_seconds=row_values["acknowledgement_lag_seconds"],
                source_family_diversity_ratio=row_values["source_family_diversity_ratio"],
                reliability_status=_status_from_reason_codes(reason_codes),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _row_reason_codes(
    *,
    hit_rate: Decimal,
    freshness_age_seconds: Decimal,
    contradiction_rate: Decimal,
    acknowledgement_lag_seconds: Decimal,
    source_family_diversity_ratio: Decimal,
    config: TeamMemorySourceReliabilityScorecardDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if contradiction_rate > config.max_contradiction_rate:
        reasons.append(
            "team_memory_source_reliability_scorecard_digest_row_high_contradiction_rate",
        )
    if hit_rate < config.min_hit_rate:
        reasons.append("team_memory_source_reliability_scorecard_digest_row_low_hit_rate")
    if freshness_age_seconds > config.max_source_age_seconds:
        reasons.append(
            "team_memory_source_reliability_scorecard_digest_row_stale_source_freshness",
        )
    if acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(
            "team_memory_source_reliability_scorecard_digest_row_slow_resolution_acknowledgement",
        )
    if source_family_diversity_ratio < config.min_source_family_diversity_ratio:
        reasons.append(
            "team_memory_source_reliability_scorecard_digest_row_low_source_family_diversity",
        )
    return tuple(
        reasons
        or ("team_memory_source_reliability_scorecard_digest_row_passed",)
    )


def _report_reason_codes(
    rows: tuple[TeamMemorySourceReliabilityScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_memory_source_reliability_scorecard_digest_empty",)
    observed: set[str] = set()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code.endswith("_row_passed"):
                continue
            observed.add(reason_code.replace("_row", ""))
    if not observed:
        return ("team_memory_source_reliability_scorecard_digest_passed",)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in observed)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[TeamMemorySourceReliabilityScorecardReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        TeamMemorySourceReliabilityScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "team_memory_source_reliability_scorecard_digest_empty" in reason_codes
        or any("high_contradiction_rate" in reason_code for reason_code in reason_codes)
    ):
        return "blocked"
    if reason_codes in (
        ("team_memory_source_reliability_scorecard_digest_passed",),
        ("team_memory_source_reliability_scorecard_digest_row_passed",),
    ):
        return "pass"
    return "watch"


def _max_age_seconds(
    observations: tuple[TeamMemorySourceReliabilityScorecardObservation, ...],
    generated_at: datetime,
) -> Decimal:
    if not observations:
        return ZERO.quantize(RATIO_QUANT)
    max_age = max(_timedelta_seconds(generated_at - row.observed_at) for row in observations)
    return max(max_age, ZERO).quantize(RATIO_QUANT)


def _max_ack_lag_seconds(
    observations: tuple[TeamMemorySourceReliabilityScorecardObservation, ...],
) -> Decimal:
    if not observations:
        return ZERO.quantize(RATIO_QUANT)
    max_lag = max(
        _timedelta_seconds(row.acknowledged_at - row.resolved_at) for row in observations
    )
    return max(max_lag, ZERO).quantize(RATIO_QUANT)


def _source_family_diversity_ratio(
    observations: tuple[TeamMemorySourceReliabilityScorecardObservation, ...],
) -> Decimal:
    if not observations:
        return ZERO.quantize(RATIO_QUANT)
    groups: dict[tuple[str, str], list[TeamMemorySourceReliabilityScorecardObservation]]
    groups = defaultdict(list)
    for observation in observations:
        groups[(observation.team_id, observation.category)].append(observation)
    ratios = tuple(
        _ratio(
            _count(len({row.source_family for row in group_rows})),
            _count(len({row.source_ref for row in group_rows})),
        )
        for group_rows in groups.values()
    )
    return min(ratios).quantize(RATIO_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANT)
    with localcontext() as context:
        context.prec = 28
        return (numerator / denominator).quantize(RATIO_QUANT)


def _timedelta_seconds(value: timedelta) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        total_microseconds = (
            (Decimal(value.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND)
            + (Decimal(value.seconds) * MICROSECONDS_PER_SECOND)
            + Decimal(value.microseconds)
        )
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(RATIO_QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _normalize_observations(
    observations: object,
) -> tuple[TeamMemorySourceReliabilityScorecardObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not TeamMemorySourceReliabilityScorecardObservation:
            raise ValueError(
                "observations must contain "
                "TeamMemorySourceReliabilityScorecardObservation values",
            )
        _require_hard_flags("observation", observation)
    return normalized


def _normalize_rows(value: object) -> tuple[TeamMemorySourceReliabilityScorecardRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    keys: set[str] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceReliabilityScorecardRow:
            raise ValueError(
                "rows must contain TeamMemorySourceReliabilityScorecardRow values",
            )
        _require_hard_flags("row", row)
        if row.row_key in keys:
            raise ValueError("rows row_key values must be unique")
        keys.add(row.row_key)
    if rows != tuple(sorted(rows, key=lambda row: row.row_key)):
        raise ValueError("rows must use deterministic ordering")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamMemorySourceReliabilityScorecardReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in counts:
        if type(row) is not TeamMemorySourceReliabilityScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamMemorySourceReliabilityScorecardReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic ordering")
        previous_key = key
        seen.add(row.reason_code)
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic ordering")
    return reason_codes


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANT)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANT)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANT)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_identifier(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _BLOCKED_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} must be a redacted identifier")


def _require_reliability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RELIABILITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _validate_row(row: TeamMemorySourceReliabilityScorecardRow) -> None:
    if row.event_count != row.hit_count + row.miss_count:
        raise ValueError("event_count must equal hit_count plus miss_count")
    if row.source_count <= ZERO:
        raise ValueError("source_count must be positive")
    if row.source_family_count <= ZERO:
        raise ValueError("source_family_count must be positive")
    if row.reason_codes == (
        "team_memory_source_reliability_scorecard_digest_row_passed",
    ):
        if row.reliability_status != "pass":
            raise ValueError("passed row reason requires pass status")
    elif (
        "team_memory_source_reliability_scorecard_digest_row_high_contradiction_rate"
        in row.reason_codes
    ):
        if row.reliability_status != "blocked":
            raise ValueError("high contradiction row reason requires blocked status")
    elif row.reliability_status != "watch":
        raise ValueError("non-passed row reason requires watch status")


def _validate_report(report: TeamMemorySourceReliabilityScorecardReport) -> None:
    if report.team_category_count != _count(len(report.rows)):
        raise ValueError("team_category_count must match rows")
    if report.event_count != report.hit_count + report.miss_count:
        raise ValueError("event_count must equal hit_count plus miss_count")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.reliability_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("reliability_status must match reason_codes")


class _RedactionMap:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], str] = {}
        self._counters: Counter[str] = Counter()

    def ref(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._values:
            self._counters[kind] += 1
            self._values[key] = f"<redacted-{kind}-{self._counters[kind]:03d}>"
        return self._values[key]


def _payload_value(value: object, redactions: _RedactionMap) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        field_names = {field.name for field in fields(value)}
        if "team_id" in field_names:
            payload["redacted_team_ref"] = redactions.ref(
                "team",
                str(getattr(value, "team_id")),
            )
        if "category" in field_names:
            payload["redacted_category_ref"] = redactions.ref(
                "category",
                str(getattr(value, "category")),
            )
        for field in fields(value):
            field_name = field.name
            if field_name in _PAYLOAD_OMIT_FIELDS:
                continue
            payload[field_name] = _payload_value(getattr(value, field_name), redactions)
        return payload
    if isinstance(value, tuple):
        return [_payload_value(item, redactions) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, redactions) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, redactions)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    return value
