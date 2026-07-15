"""Read-only Polymarket market discovery candidate pool readiness reports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION",
    "MarketDiscoveryCandidate",
    "MarketDiscoveryCandidatePoolConfig",
    "MarketDiscoveryCandidatePoolReadinessReport",
    "MarketDiscoveryCandidatePoolReasonCodeCount",
    "MarketDiscoveryCandidatePoolRow",
    "build_market_discovery_candidate_pool_readiness_report",
    "market_discovery_candidate_pool_readiness_report_payload",
)


DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION = "market-discovery-candidate-pool-v0"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
READY_STATUSES = ("ready", "watch", "blocked")
STATUS_RANK = {"blocked": 3, "watch": 2, "ready": 1}
CONFIG_THRESHOLD_FIELDS = (
    "min_liquidity",
    "max_spread",
    "max_data_age_seconds",
    "min_seconds_until_end",
)
REASON_SEQUENCE = (
    "candidate_pool_ready",
    "data_freshness_stale_blocker",
    "end_time_too_close_blocker",
    "liquidity_below_minimum_attention",
    "spread_above_maximum_attention",
    "candidate_pool_empty_blocker",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketDiscoveryCandidatePoolConfig(_FinalDataclass):
    config_version: str = DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION
    min_liquidity: Decimal = Decimal("1000.000000")
    max_spread: Decimal = Decimal("0.050000")
    max_data_age_seconds: Decimal = Decimal("300.000000")
    min_seconds_until_end: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.config_version) is not str
            or self.config_version != DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported candidate pool config")
        for field_name in CONFIG_THRESHOLD_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketDiscoveryCandidate(_FinalDataclass):
    market_id: str
    slug: str
    question: str
    category: str
    liquidity: Decimal
    spread: Decimal
    end_time: datetime
    data_freshness: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "slug", "question", "category"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "liquidity", _require_nonnegative_decimal("liquidity", self.liquidity))
        object.__setattr__(self, "spread", _require_nonnegative_decimal("spread", self.spread))
        object.__setattr__(self, "end_time", _as_utc("end_time", self.end_time))
        object.__setattr__(
            self,
            "data_freshness",
            _require_nonnegative_decimal("data_freshness", self.data_freshness),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class MarketDiscoveryCandidatePoolRow(_FinalDataclass):
    market_id: str
    slug: str
    question: str
    category: str
    liquidity: Decimal
    spread: Decimal
    end_time: datetime
    data_freshness: Decimal
    seconds_until_end: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "slug", "question", "category"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity",
            "spread",
            "data_freshness",
            "seconds_until_end",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "end_time", _as_utc("end_time", self.end_time))
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class MarketDiscoveryCandidatePoolReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "ratio", _require_ratio_decimal("ratio", self.ratio))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketDiscoveryCandidatePoolReadinessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketDiscoveryCandidatePoolReasonCodeCount, ...]
    rows: tuple[MarketDiscoveryCandidatePoolRow, ...]
    effective_config: MarketDiscoveryCandidatePoolConfig = field(
        default_factory=MarketDiscoveryCandidatePoolConfig,
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if (
            type(self.config_version) is not str
            or self.config_version != DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported candidate pool config")
        for field_name in ("candidate_count", "ready_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "effective_config",
            _require_effective_config(self.effective_config),
        )
        if self.config_version != self.effective_config.config_version:
            raise ValueError("config_version must match effective_config")
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        return market_discovery_candidate_pool_readiness_report_payload(self)


def build_market_discovery_candidate_pool_readiness_report(
    candidates: Iterable[object],
    *,
    config: MarketDiscoveryCandidatePoolConfig,
    generated_at: datetime,
) -> MarketDiscoveryCandidatePoolReadinessReport:
    if type(config) is not MarketDiscoveryCandidatePoolConfig:
        raise ValueError("config must be a MarketDiscoveryCandidatePoolConfig")
    _require_hard_flags("config", config)
    effective_config = _snapshot_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_values = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=effective_config,
                    generated_at=generated_at_utc,
                )
                for candidate in candidate_values
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return MarketDiscoveryCandidatePoolReadinessReport(
        generated_at=generated_at_utc,
        config_version=effective_config.config_version,
        candidate_count=_count(len(rows)),
        ready_count=_count(_status_count(rows, "ready")),
        watch_count=_count(_status_count(rows, "watch")),
        blocked_count=_count(_status_count(rows, "blocked")),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        effective_config=effective_config,
    )


def market_discovery_candidate_pool_readiness_report_payload(
    report: MarketDiscoveryCandidatePoolReadinessReport,
) -> dict[str, object]:
    if type(report) is not MarketDiscoveryCandidatePoolReadinessReport:
        raise ValueError("report must be a MarketDiscoveryCandidatePoolReadinessReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _snapshot_config(
    config: MarketDiscoveryCandidatePoolConfig,
) -> MarketDiscoveryCandidatePoolConfig:
    return MarketDiscoveryCandidatePoolConfig(
        config_version=config.config_version,
        min_liquidity=config.min_liquidity,
        max_spread=config.max_spread,
        max_data_age_seconds=config.max_data_age_seconds,
        min_seconds_until_end=config.min_seconds_until_end,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _row_from_candidate(
    candidate: MarketDiscoveryCandidate,
    *,
    config: MarketDiscoveryCandidatePoolConfig,
    generated_at: datetime,
) -> MarketDiscoveryCandidatePoolRow:
    if candidate.end_time <= generated_at:
        raise ValueError("end_time must be after generated_at")
    seconds_until_end = _seconds_between(generated_at, candidate.end_time)
    reason_codes = _row_reason_codes(
        candidate,
        config=config,
        seconds_until_end=seconds_until_end,
    )
    return MarketDiscoveryCandidatePoolRow(
        market_id=candidate.market_id,
        slug=candidate.slug,
        question=candidate.question,
        category=candidate.category,
        liquidity=candidate.liquidity,
        spread=candidate.spread,
        end_time=candidate.end_time,
        data_freshness=candidate.data_freshness,
        seconds_until_end=seconds_until_end,
        readiness_score=_readiness_score(reason_codes),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    candidate: MarketDiscoveryCandidate,
    *,
    config: MarketDiscoveryCandidatePoolConfig,
    seconds_until_end: Decimal,
) -> tuple[str, ...]:
    return _reason_codes_from_values(
        liquidity=candidate.liquidity,
        spread=candidate.spread,
        data_freshness=candidate.data_freshness,
        seconds_until_end=seconds_until_end,
        config=config,
    )


def _reason_codes_from_values(
    *,
    liquidity: Decimal,
    spread: Decimal,
    data_freshness: Decimal,
    seconds_until_end: Decimal,
    config: MarketDiscoveryCandidatePoolConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if liquidity < config.min_liquidity:
        reason_codes.append("liquidity_below_minimum_attention")
    if spread > config.max_spread:
        reason_codes.append("spread_above_maximum_attention")
    if data_freshness > config.max_data_age_seconds:
        reason_codes.append("data_freshness_stale_blocker")
    if seconds_until_end < config.min_seconds_until_end:
        reason_codes.append("end_time_too_close_blocker")
    if not reason_codes:
        reason_codes.append("candidate_pool_ready")
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in reason_codes)


def _readiness_score(reason_codes: tuple[str, ...]) -> Decimal:
    penalty = ZERO
    for reason_code in reason_codes:
        if reason_code.endswith("_blocker"):
            penalty += Decimal("0.750000")
        elif reason_code.endswith("_attention"):
            penalty += Decimal("0.250000")
    return _quantize(max(ZERO, ONE - penalty))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocker") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_attention") for reason_code in reason_codes):
        return "watch"
    return "ready"


def _report_status(rows: tuple[MarketDiscoveryCandidatePoolRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(rows: tuple[MarketDiscoveryCandidatePoolRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("candidate_pool_empty_blocker",)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in found)


def _reason_code_counts(
    rows: tuple[MarketDiscoveryCandidatePoolRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketDiscoveryCandidatePoolReasonCodeCount, ...]:
    if not rows:
        return (
            MarketDiscoveryCandidatePoolReasonCodeCount(
                reason_code="candidate_pool_empty_blocker",
                count=ONE,
                ratio=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        MarketDiscoveryCandidatePoolReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            ratio=_ratio(_count(counts[reason_code]), total),
        )
        for reason_code in reason_codes
    )


def _status_count(rows: tuple[MarketDiscoveryCandidatePoolRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: MarketDiscoveryCandidatePoolRow) -> tuple[int, Decimal, str]:
    return (-STATUS_RANK[row.status], -row.readiness_score, row.market_id)


def _normalize_candidates(candidates: Iterable[object]) -> tuple[MarketDiscoveryCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    normalized: list[MarketDiscoveryCandidate] = []
    market_ids: set[str] = set()
    slugs: set[str] = set()
    for value in values:
        if type(value) is not MarketDiscoveryCandidate:
            raise ValueError("candidates must contain MarketDiscoveryCandidate values")
        _require_hard_flags("candidate", value)
        if value.market_id in market_ids:
            raise ValueError("duplicate market_id values are not allowed")
        if value.slug in slugs:
            raise ValueError("duplicate slug values are not allowed")
        market_ids.add(value.market_id)
        slugs.add(value.slug)
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(
    rows: Iterable[MarketDiscoveryCandidatePoolRow],
) -> tuple[MarketDiscoveryCandidatePoolRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    previous_key: tuple[int, Decimal, str] | None = None
    market_ids: set[str] = set()
    slugs: set[str] = set()
    for row in values:
        if type(row) is not MarketDiscoveryCandidatePoolRow:
            raise ValueError("rows must contain MarketDiscoveryCandidatePoolRow values")
        _validate_row(row)
        if row.market_id in market_ids:
            raise ValueError("duplicate market_id values are not allowed")
        if row.slug in slugs:
            raise ValueError("duplicate slug values are not allowed")
        market_ids.add(row.market_id)
        slugs.add(row.slug)
        sort_key = _row_sort_key(row)
        if previous_key is not None and previous_key > sort_key:
            raise ValueError("rows must be sorted deterministically")
        previous_key = sort_key
    return values


def _normalize_reason_code_counts(
    values: Iterable[MarketDiscoveryCandidatePoolReasonCodeCount],
) -> tuple[MarketDiscoveryCandidatePoolReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    previous_index = -1
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketDiscoveryCandidatePoolReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count values")
        _require_hard_flags("reason_code_count", item)
        _require_reason_code("reason_code", item.reason_code)
        _require_canonical_nonnegative_decimal("count", item.count)
        _require_canonical_ratio_decimal("ratio", item.ratio)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        index = REASON_SEQUENCE.index(item.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must be sorted deterministically")
        seen.add(item.reason_code)
        previous_index = index
    return items


def _validate_row(row: MarketDiscoveryCandidatePoolRow) -> None:
    for field_name in ("market_id", "slug", "question", "category"):
        if _require_non_empty_string(field_name, getattr(row, field_name)) != getattr(
            row,
            field_name,
        ):
            raise ValueError(f"{field_name} must be canonical")
    for field_name in (
        "liquidity",
        "spread",
        "data_freshness",
        "seconds_until_end",
        "readiness_score",
    ):
        _require_canonical_nonnegative_decimal(field_name, getattr(row, field_name))
    if _as_utc("end_time", row.end_time) != row.end_time or row.end_time.tzinfo is not UTC:
        raise ValueError("end_time must be normalized to UTC")
    _require_status(row.status)
    if type(row.reason_codes) is not tuple or _require_reason_codes(
        row.reason_codes,
        require_nonempty=True,
    ) != row.reason_codes:
        raise ValueError("reason_codes must be a canonical tuple")
    _require_hard_flags("row", row)
    expected_score = _readiness_score(row.reason_codes)
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score must match reason codes")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason codes")


def _validate_report(report: MarketDiscoveryCandidatePoolReadinessReport) -> None:
    if (
        _as_utc("generated_at", report.generated_at) != report.generated_at
        or report.generated_at.tzinfo is not UTC
    ):
        raise ValueError("generated_at must be normalized to UTC")
    effective_config = _require_effective_config(report.effective_config)
    if (
        type(report.config_version) is not str
        or report.config_version != DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported candidate pool config")
    if report.config_version != effective_config.config_version:
        raise ValueError("config_version must match effective_config")
    for field_name in ("candidate_count", "ready_count", "watch_count", "blocked_count"):
        _require_canonical_nonnegative_decimal(field_name, getattr(report, field_name))
    _require_status(report.status)
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must be a canonical tuple")
    _require_reason_codes(report.reason_codes, require_nonempty=True)
    if type(report.reason_code_counts) is not tuple or _normalize_reason_code_counts(
        report.reason_code_counts,
    ) != report.reason_code_counts:
        raise ValueError("reason_code_counts must be a canonical tuple")
    if type(report.rows) is not tuple or _normalize_rows(report.rows) != report.rows:
        raise ValueError("rows must be a canonical tuple")
    rows = report.rows
    for row in rows:
        if type(row) is not MarketDiscoveryCandidatePoolRow:
            raise ValueError("rows must contain MarketDiscoveryCandidatePoolRow values")
        _require_hard_flags("row", row)
        _validate_row(row)
        if row.end_time <= report.generated_at:
            raise ValueError("end_time must be after generated_at")
        if row.seconds_until_end != _seconds_between(report.generated_at, row.end_time):
            raise ValueError("seconds_until_end must match generated_at and end_time")
        expected_reason_codes = _reason_codes_from_values(
            liquidity=row.liquidity,
            spread=row.spread,
            data_freshness=row.data_freshness,
            seconds_until_end=row.seconds_until_end,
            config=effective_config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match effective config and row values")
        if row.readiness_score != _readiness_score(expected_reason_codes):
            raise ValueError("readiness_score must match effective config and row values")
        if row.status != _row_status(expected_reason_codes):
            raise ValueError("status must match effective config and row values")
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _count(_status_count(rows, "ready")):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(_status_count(rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(rows, expected_reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_effective_config(value: object) -> MarketDiscoveryCandidatePoolConfig:
    if type(value) is not MarketDiscoveryCandidatePoolConfig:
        raise ValueError(
            "effective_config must be a MarketDiscoveryCandidatePoolConfig",
        )
    if (
        type(value.config_version) is not str
        or value.config_version != DEFAULT_MARKET_DISCOVERY_CANDIDATE_POOL_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported candidate pool config")
    for field_name in CONFIG_THRESHOLD_FIELDS:
        threshold = getattr(value, field_name)
        _require_canonical_nonnegative_decimal(field_name, threshold)
    _require_hard_flags("effective_config", value)
    return value


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a known candidate pool reason code")
    return value


def _require_reason_codes(
    values: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not items:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for item in items:
        reason_code = _require_reason_code("reason_codes", item)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        index = REASON_SEQUENCE.index(reason_code)
        if index <= previous_index:
            raise ValueError("reason_codes must be sorted deterministically")
        seen.add(reason_code)
        previous_index = index
    return items


def _require_status(value: object) -> None:
    if type(value) is not str or value not in READY_STATUSES:
        raise ValueError("status must be a known candidate pool readiness status")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_canonical_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if value.as_tuple() != normalized.as_tuple():
        raise ValueError(f"{field_name} must be normalized")
    return normalized


def _require_canonical_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_ratio_decimal(field_name, value)
    if value.as_tuple() != normalized.as_tuple():
        raise ValueError(f"{field_name} must be normalized")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000")
    )
    return _quantize(seconds)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value
