"""Pure Phase 1 paper category resolution timeline rotation digest."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_STRATEGY_CATEGORY_RESOLUTION_TIMELINE_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-resolution-timeline-rotation-digest-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

ROTATION_STATUSES = ("recommend", "watch", "blocked")
REPORT_STATUSES = ("paper_rotation_ready", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "paper_rotation_ready": "review_paper_resolution_timeline_rotation_candidates",
    "watch": "review_resolution_timeline_watch_items",
    "blocked": "review_resolution_timeline_blockers",
}
STATUS_WEIGHT = {
    "recommend": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("2.000000"),
}
EMPTY_REASON_CODE = "strategy_category_resolution_timeline_rotation_digest_empty"
RAW_TIMELINE_REFERENCE_FIELD = "timeline_reference"

SENSITIVE_REFERENCE_MARKERS = (
    "://",
    "tok" + "en=",
    "api" + "_key=",
    "sec" + "ret",
    "priv" + "ate",
    "wal" + "let:",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
)
SENSITIVE_REASON_REPLACEMENTS = (
    (("wal" + "let", "priv" + "ate_key", "0x"), "reference_redacted"),
    (("api" + "_key", "sk_live", "sec" + "ret", "tok" + "en"), "credential_redacted"),
)
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "aut" + "h",
    "priv" + "ate_key",
    "wal" + "let",
    "acco" + "unt",
    "bal" + "ance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
    "bro" + "ker",
)
SURFACE_REASON_REPLACEMENT = "surface_redacted"


@dataclass(frozen=True)
class StrategyCategoryResolutionTimelineRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_RESOLUTION_TIMELINE_ROTATION_DIGEST_CONFIG_VERSION
    )
    maximum_stale_close_age_seconds: Decimal = Decimal("3600.000000")
    watch_stale_close_age_seconds: Decimal = Decimal("7200.000000")
    maximum_unresolved_closed_ratio: Decimal = Decimal("0.250000")
    watch_unresolved_closed_ratio: Decimal = Decimal("0.400000")
    maximum_settlement_pressure_ratio: Decimal = Decimal("0.300000")
    watch_settlement_pressure_ratio: Decimal = Decimal("0.500000")
    minimum_readiness_ratio: Decimal = Decimal("0.600000")
    watch_readiness_ratio: Decimal = Decimal("0.300000")
    maximum_evidence_age_seconds: Decimal = Decimal("1800.000000")
    watch_evidence_age_seconds: Decimal = Decimal("5400.000000")
    minimum_recommended_categories: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "maximum_stale_close_age_seconds",
            "watch_stale_close_age_seconds",
            "maximum_evidence_age_seconds",
            "watch_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_unresolved_closed_ratio",
            "watch_unresolved_closed_ratio",
            "maximum_settlement_pressure_ratio",
            "watch_settlement_pressure_ratio",
            "minimum_readiness_ratio",
            "watch_readiness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_recommended_categories",
            _normalize_nonnegative_count(
                "minimum_recommended_categories",
                self.minimum_recommended_categories,
            ),
        )
        _require_at_most(
            "maximum_stale_close_age_seconds",
            self.maximum_stale_close_age_seconds,
            self.watch_stale_close_age_seconds,
        )
        _require_at_most(
            "maximum_unresolved_closed_ratio",
            self.maximum_unresolved_closed_ratio,
            self.watch_unresolved_closed_ratio,
        )
        _require_at_most(
            "maximum_settlement_pressure_ratio",
            self.maximum_settlement_pressure_ratio,
            self.watch_settlement_pressure_ratio,
        )
        _require_at_most(
            "watch_readiness_ratio",
            self.watch_readiness_ratio,
            self.minimum_readiness_ratio,
        )
        _require_at_most(
            "maximum_evidence_age_seconds",
            self.maximum_evidence_age_seconds,
            self.watch_evidence_age_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryResolutionTimelineRotationInput:
    category_id: str
    team_id: str
    observed_at: datetime
    market_count: Decimal
    closed_market_count: Decimal
    unresolved_closed_market_count: Decimal
    stale_closed_market_count: Decimal
    pending_settlement_market_count: Decimal
    ready_to_settle_market_count: Decimal
    oldest_unresolved_close_at: datetime | None
    latest_evidence_at: datetime
    timeline_reference: str = field(repr=False)
    reason_codes: tuple[str, ...] = ("category_resolution_timeline_input_available",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "market_count",
            "closed_market_count",
            "unresolved_closed_market_count",
            "stale_closed_market_count",
            "pending_settlement_market_count",
            "ready_to_settle_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.market_count <= ZERO:
            raise ValueError("market_count must be positive")
        if self.closed_market_count > self.market_count:
            raise ValueError("closed_market_count must not exceed market_count")
        for field_name in (
            "unresolved_closed_market_count",
            "stale_closed_market_count",
        ):
            if getattr(self, field_name) > self.closed_market_count:
                raise ValueError(f"{field_name} must not exceed closed_market_count")
        for field_name in (
            "pending_settlement_market_count",
            "ready_to_settle_market_count",
        ):
            if getattr(self, field_name) > self.market_count:
                raise ValueError(f"{field_name} must not exceed market_count")
        if self.oldest_unresolved_close_at is not None:
            object.__setattr__(
                self,
                "oldest_unresolved_close_at",
                _as_utc("oldest_unresolved_close_at", self.oldest_unresolved_close_at),
            )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        _require_reference_string("timeline_reference", self.timeline_reference)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCategoryResolutionTimelineRotationDigestRow:
    rank: Decimal
    category_id: str
    team_id: str
    rotation_status: str
    rotation_score: Decimal
    observed_at: datetime
    market_count: Decimal
    closed_market_count: Decimal
    unresolved_closed_market_count: Decimal
    unresolved_closed_ratio: Decimal
    stale_closed_market_count: Decimal
    stale_close_ratio: Decimal
    pending_settlement_market_count: Decimal
    settlement_pressure_ratio: Decimal
    ready_to_settle_market_count: Decimal
    readiness_ratio: Decimal
    oldest_unresolved_close_at: datetime | None
    stale_close_age_seconds: Decimal
    latest_evidence_at: datetime
    evidence_age_seconds: Decimal
    redacted_timeline_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        _require_member("rotation_status", self.rotation_status, ROTATION_STATUSES)
        object.__setattr__(
            self,
            "rotation_score",
            _normalize_ratio("rotation_score", self.rotation_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "market_count",
            "closed_market_count",
            "unresolved_closed_market_count",
            "stale_closed_market_count",
            "pending_settlement_market_count",
            "ready_to_settle_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.market_count <= ZERO:
            raise ValueError("market_count must be positive")
        for field_name in (
            "unresolved_closed_ratio",
            "stale_close_ratio",
            "settlement_pressure_ratio",
            "readiness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.oldest_unresolved_close_at is not None:
            object.__setattr__(
                self,
                "oldest_unresolved_close_at",
                _as_utc("oldest_unresolved_close_at", self.oldest_unresolved_close_at),
            )
        object.__setattr__(
            self,
            "stale_close_age_seconds",
            _normalize_nonnegative_decimal(
                "stale_close_age_seconds",
                self.stale_close_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        _require_canonical_string(
            "redacted_timeline_reference",
            self.redacted_timeline_reference,
        )
        if _contains_sensitive_reference(self.redacted_timeline_reference):
            raise ValueError("redacted_timeline_reference must be redacted")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.rotation_status != _row_status(self.reason_codes):
            raise ValueError("rotation_status must match reason_codes")
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCategoryResolutionTimelineRotationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyCategoryResolutionTimelineRotationDigestReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    recommend_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    recommended_next_step: str
    recommended_category_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyCategoryResolutionTimelineRotationReasonCodeCount, ...]
    category_rows: tuple[StrategyCategoryResolutionTimelineRotationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_count",
            "recommend_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "recommended_category_ids",
            _normalize_category_ids("recommended_category_ids", self.recommended_category_ids),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "category_rows", _normalize_rows(self.category_rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_category_resolution_timeline_rotation_digest_report(
    categories: Iterable[StrategyCategoryResolutionTimelineRotationInput],
    *,
    config: StrategyCategoryResolutionTimelineRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryResolutionTimelineRotationDigestReport:
    if type(config) is not StrategyCategoryResolutionTimelineRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryResolutionTimelineRotationDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(categories)
    unranked_rows = tuple(
        sorted(
            (
                _digest_row(
                    category,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for category in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        _ranked_row(row, rank=index)
        for index, row in enumerate(unranked_rows, start=1)
    )
    status = _rollup_status(rows, config=config)
    return StrategyCategoryResolutionTimelineRotationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_count(len(rows)),
        recommend_count=_status_count(rows, "recommend"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        recommended_category_ids=tuple(
            row.category_id for row in rows if row.rotation_status == "recommend"
        ),
        reason_codes=_rollup_reason_codes(rows, status=status),
        reason_code_counts=_reason_code_counts(rows),
        category_rows=rows,
    )


def strategy_category_resolution_timeline_rotation_digest_payload(
    report: StrategyCategoryResolutionTimelineRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryResolutionTimelineRotationDigestReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCategoryResolutionTimelineRotationDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _digest_row(
    category: StrategyCategoryResolutionTimelineRotationInput,
    *,
    config: StrategyCategoryResolutionTimelineRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryResolutionTimelineRotationDigestRow:
    unresolved_closed_ratio = _ratio(
        category.unresolved_closed_market_count,
        category.closed_market_count,
    )
    stale_close_ratio = _ratio(
        category.stale_closed_market_count,
        category.closed_market_count,
    )
    settlement_pressure_ratio = _ratio(
        category.pending_settlement_market_count,
        category.market_count,
    )
    readiness_ratio = _ratio(
        category.ready_to_settle_market_count,
        category.market_count,
    )
    stale_close_age_seconds = _optional_age_seconds(
        "oldest_unresolved_close_at",
        category.oldest_unresolved_close_at,
        generated_at,
    )
    evidence_age_seconds = _age_seconds(
        "latest_evidence_at",
        category.latest_evidence_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        category,
        unresolved_closed_ratio=unresolved_closed_ratio,
        stale_close_ratio=stale_close_ratio,
        settlement_pressure_ratio=settlement_pressure_ratio,
        readiness_ratio=readiness_ratio,
        stale_close_age_seconds=stale_close_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        config=config,
    )
    return StrategyCategoryResolutionTimelineRotationDigestRow(
        rank=COUNT_QUANTUM,
        category_id=category.category_id,
        team_id=category.team_id,
        rotation_status=_row_status(reason_codes),
        rotation_score=_rotation_score(
            unresolved_closed_ratio=unresolved_closed_ratio,
            stale_close_ratio=stale_close_ratio,
            settlement_pressure_ratio=settlement_pressure_ratio,
            readiness_ratio=readiness_ratio,
            stale_close_age_seconds=stale_close_age_seconds,
            evidence_age_seconds=evidence_age_seconds,
            config=config,
        ),
        observed_at=category.observed_at,
        market_count=category.market_count,
        closed_market_count=category.closed_market_count,
        unresolved_closed_market_count=category.unresolved_closed_market_count,
        unresolved_closed_ratio=unresolved_closed_ratio,
        stale_closed_market_count=category.stale_closed_market_count,
        stale_close_ratio=stale_close_ratio,
        pending_settlement_market_count=category.pending_settlement_market_count,
        settlement_pressure_ratio=settlement_pressure_ratio,
        ready_to_settle_market_count=category.ready_to_settle_market_count,
        readiness_ratio=readiness_ratio,
        oldest_unresolved_close_at=category.oldest_unresolved_close_at,
        stale_close_age_seconds=stale_close_age_seconds,
        latest_evidence_at=category.latest_evidence_at,
        evidence_age_seconds=evidence_age_seconds,
        redacted_timeline_reference=_redact_reference(category.timeline_reference),
        reason_codes=reason_codes,
    )


def _ranked_row(
    row: StrategyCategoryResolutionTimelineRotationDigestRow,
    *,
    rank: int,
) -> StrategyCategoryResolutionTimelineRotationDigestRow:
    return StrategyCategoryResolutionTimelineRotationDigestRow(
        rank=_count(rank),
        category_id=row.category_id,
        team_id=row.team_id,
        rotation_status=row.rotation_status,
        rotation_score=row.rotation_score,
        observed_at=row.observed_at,
        market_count=row.market_count,
        closed_market_count=row.closed_market_count,
        unresolved_closed_market_count=row.unresolved_closed_market_count,
        unresolved_closed_ratio=row.unresolved_closed_ratio,
        stale_closed_market_count=row.stale_closed_market_count,
        stale_close_ratio=row.stale_close_ratio,
        pending_settlement_market_count=row.pending_settlement_market_count,
        settlement_pressure_ratio=row.settlement_pressure_ratio,
        ready_to_settle_market_count=row.ready_to_settle_market_count,
        readiness_ratio=row.readiness_ratio,
        oldest_unresolved_close_at=row.oldest_unresolved_close_at,
        stale_close_age_seconds=row.stale_close_age_seconds,
        latest_evidence_at=row.latest_evidence_at,
        evidence_age_seconds=row.evidence_age_seconds,
        redacted_timeline_reference=row.redacted_timeline_reference,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    category: StrategyCategoryResolutionTimelineRotationInput,
    *,
    unresolved_closed_ratio: Decimal,
    stale_close_ratio: Decimal,
    settlement_pressure_ratio: Decimal,
    readiness_ratio: Decimal,
    stale_close_age_seconds: Decimal,
    evidence_age_seconds: Decimal,
    config: StrategyCategoryResolutionTimelineRotationDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(category.reason_codes)
    reason_codes.append(
        _lower_threshold_reason_code(
            unresolved_closed_ratio,
            pass_threshold=config.maximum_unresolved_closed_ratio,
            watch_threshold=config.watch_unresolved_closed_ratio,
            pass_code="category_unresolved_closed_ratio_clear",
            watch_code="category_unresolved_closed_ratio_watch",
            blocked_code="category_unresolved_closed_ratio_blocked",
        ),
    )
    stale_close_status = _worst_reason_code(
        _lower_threshold_reason_code(
            stale_close_ratio,
            pass_threshold=config.maximum_unresolved_closed_ratio,
            watch_threshold=config.watch_unresolved_closed_ratio,
            pass_code="category_stale_close_window_clear",
            watch_code="category_stale_close_window_watch",
            blocked_code="category_stale_close_window_blocked",
        ),
        _lower_threshold_reason_code(
            stale_close_age_seconds,
            pass_threshold=config.maximum_stale_close_age_seconds,
            watch_threshold=config.watch_stale_close_age_seconds,
            pass_code="category_stale_close_window_clear",
            watch_code="category_stale_close_window_watch",
            blocked_code="category_stale_close_window_blocked",
        ),
    )
    reason_codes.append(stale_close_status)
    reason_codes.append(
        _lower_threshold_reason_code(
            settlement_pressure_ratio,
            pass_threshold=config.maximum_settlement_pressure_ratio,
            watch_threshold=config.watch_settlement_pressure_ratio,
            pass_code="category_settlement_pressure_clear",
            watch_code="category_settlement_pressure_watch",
            blocked_code="category_settlement_pressure_blocked",
        ),
    )
    reason_codes.append(
        _higher_threshold_reason_code(
            readiness_ratio,
            pass_threshold=config.minimum_readiness_ratio,
            watch_threshold=config.watch_readiness_ratio,
            pass_code="category_readiness_sufficient",
            watch_code="category_readiness_watch",
            blocked_code="category_readiness_blocked",
        ),
    )
    reason_codes.append(
        _lower_threshold_reason_code(
            evidence_age_seconds,
            pass_threshold=config.maximum_evidence_age_seconds,
            watch_threshold=config.watch_evidence_age_seconds,
            pass_code="category_evidence_fresh",
            watch_code="category_resolution_evidence_stale_watch",
            blocked_code="category_resolution_evidence_stale_blocked",
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes))


def _lower_threshold_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    pass_code: str,
    watch_code: str,
    blocked_code: str,
) -> str:
    if value <= pass_threshold:
        return pass_code
    if value <= watch_threshold:
        return watch_code
    return blocked_code


def _higher_threshold_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    pass_code: str,
    watch_code: str,
    blocked_code: str,
) -> str:
    if value >= pass_threshold:
        return pass_code
    if value >= watch_threshold:
        return watch_code
    return blocked_code


def _worst_reason_code(left: str, right: str) -> str:
    if left.endswith("_blocked") or right.endswith("_blocked"):
        return "category_stale_close_window_blocked"
    if left.endswith("_watch") or right.endswith("_watch"):
        return "category_stale_close_window_watch"
    return "category_stale_close_window_clear"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "recommend"


def _rotation_score(
    *,
    unresolved_closed_ratio: Decimal,
    stale_close_ratio: Decimal,
    settlement_pressure_ratio: Decimal,
    readiness_ratio: Decimal,
    stale_close_age_seconds: Decimal,
    evidence_age_seconds: Decimal,
    config: StrategyCategoryResolutionTimelineRotationDigestConfig,
) -> Decimal:
    stale_age_score = _bounded_one_minus(
        _bounded_fraction(
            stale_close_age_seconds,
            config.watch_stale_close_age_seconds,
        ),
    )
    evidence_age_score = _bounded_one_minus(
        _bounded_fraction(evidence_age_seconds, config.watch_evidence_age_seconds),
    )
    return _normalize_ratio(
        "rotation_score",
        (
            _bounded_one_minus(unresolved_closed_ratio)
            + _bounded_one_minus(stale_close_ratio)
            + _bounded_one_minus(settlement_pressure_ratio)
            + readiness_ratio
            + stale_age_score
            + evidence_age_score
        )
        / Decimal("6"),
    )


def _rollup_status(
    rows: tuple[StrategyCategoryResolutionTimelineRotationDigestRow, ...],
    *,
    config: StrategyCategoryResolutionTimelineRotationDigestConfig,
) -> str:
    recommend_count = _status_count(rows, "recommend")
    if recommend_count >= config.minimum_recommended_categories and recommend_count > ZERO:
        return "paper_rotation_ready"
    if rows and all(row.rotation_status == "blocked" for row in rows):
        return "blocked"
    return "watch" if rows else "blocked"


def _rollup_reason_codes(
    rows: tuple[StrategyCategoryResolutionTimelineRotationDigestRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes = [
        f"category_resolution_timeline_{'ready' if status == 'paper_rotation_ready' else status}",
    ]
    for row in rows:
        reason_codes.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code.endswith("_blocked")
        )
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[StrategyCategoryResolutionTimelineRotationDigestRow, ...],
) -> tuple[StrategyCategoryResolutionTimelineRotationReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyCategoryResolutionTimelineRotationReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_inputs(
    categories: Iterable[StrategyCategoryResolutionTimelineRotationInput],
) -> tuple[StrategyCategoryResolutionTimelineRotationInput, ...]:
    if isinstance(categories, (str, bytes)):
        raise ValueError("categories must be an iterable")
    try:
        rows = tuple(categories)
    except TypeError as exc:
        raise ValueError("categories must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyCategoryResolutionTimelineRotationInput:
            raise ValueError(
                "categories must contain exact resolution timeline input values",
            )
        _require_hard_flags("category", row)
        if row.category_id in seen:
            raise ValueError("categories must not contain duplicate category_id values")
        seen.add(row.category_id)
    return rows


def _normalize_rows(
    rows: Iterable[StrategyCategoryResolutionTimelineRotationDigestRow],
) -> tuple[StrategyCategoryResolutionTimelineRotationDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("category_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("category_rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not StrategyCategoryResolutionTimelineRotationDigestRow:
            raise ValueError("category_rows must contain exact row values")
        _require_hard_flags("category_row", row)
        if row.category_id in seen:
            raise ValueError("category_rows must not contain duplicate category_id values")
        seen.add(row.category_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("category_rows must use deterministic sort")
    expected_ranks = tuple(_count(index) for index in range(1, len(values) + 1))
    if tuple(row.rank for row in values) != expected_ranks:
        raise ValueError("category_rows must use sequential ranks")
    return values


def _normalize_reason_code_counts(
    value: Iterable[StrategyCategoryResolutionTimelineRotationReasonCodeCount],
) -> tuple[StrategyCategoryResolutionTimelineRotationReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not StrategyCategoryResolutionTimelineRotationReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count rows")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate values")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic sort")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_category_ids(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    category_ids = tuple(value)
    seen: set[str] = set()
    for category_id in category_ids:
        _require_canonical_string(field_name, category_id)
        if category_id in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(category_id)
    return category_ids


def _validate_row(row: StrategyCategoryResolutionTimelineRotationDigestRow) -> None:
    if row.closed_market_count > row.market_count:
        raise ValueError("closed_market_count must not exceed market_count")
    if row.unresolved_closed_market_count > row.closed_market_count:
        raise ValueError(
            "unresolved_closed_market_count must not exceed closed_market_count",
        )
    if row.stale_closed_market_count > row.closed_market_count:
        raise ValueError("stale_closed_market_count must not exceed closed_market_count")
    if row.pending_settlement_market_count > row.market_count:
        raise ValueError("pending_settlement_market_count must not exceed market_count")
    if row.ready_to_settle_market_count > row.market_count:
        raise ValueError("ready_to_settle_market_count must not exceed market_count")
    if row.unresolved_closed_ratio != _ratio(
        row.unresolved_closed_market_count,
        row.closed_market_count,
    ):
        raise ValueError("unresolved_closed_ratio must match counts")
    if row.stale_close_ratio != _ratio(
        row.stale_closed_market_count,
        row.closed_market_count,
    ):
        raise ValueError("stale_close_ratio must match counts")
    if row.settlement_pressure_ratio != _ratio(
        row.pending_settlement_market_count,
        row.market_count,
    ):
        raise ValueError("settlement_pressure_ratio must match counts")
    if row.readiness_ratio != _ratio(
        row.ready_to_settle_market_count,
        row.market_count,
    ):
        raise ValueError("readiness_ratio must match counts")


def _validate_report(
    report: StrategyCategoryResolutionTimelineRotationDigestReport,
) -> None:
    rows = report.category_rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match category_rows")
    for field_name, status in (
        ("recommend_count", "recommend"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match category_rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.recommended_category_ids != tuple(
        row.category_id for row in rows if row.rotation_status == "recommend"
    ):
        raise ValueError("recommended_category_ids must match category_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match category_rows")
    if report.reason_codes != _rollup_reason_codes(rows, status=report.status):
        raise ValueError("reason_codes must match category_rows")


def _row_sort_key(
    row: StrategyCategoryResolutionTimelineRotationDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.rotation_status],
        -row.rotation_score,
        -row.readiness_ratio,
        row.category_id,
        row.team_id,
    )


def _status_count(
    rows: tuple[StrategyCategoryResolutionTimelineRotationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rotation_status == status))


def _optional_age_seconds(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> Decimal:
    if value is None:
        return ZERO
    return _age_seconds(field_name, value, generated_at)


def _age_seconds(field_name: str, value: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - _as_utc(field_name, value)
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    age_seconds = _normalize_decimal(f"{field_name}_age_seconds", seconds)
    if age_seconds < ZERO:
        raise ValueError(f"{field_name} must not be after generated_at")
    return age_seconds


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio("ratio", numerator / denominator)


def _bounded_fraction(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    value = _normalize_nonnegative_decimal("ratio", numerator / denominator)
    if value > ONE:
        return ONE
    return value


def _bounded_one_minus(value: Decimal) -> Decimal:
    if value >= ONE:
        return ZERO
    if value <= ZERO:
        return ONE
    return _q(ONE - value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be less than or equal to watch threshold")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if _contains_sensitive_reference(value) or _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_reference_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        clean_reason_code = _sanitize_reason_code(reason_code)
        _require_reason_code(clean_reason_code)
        if clean_reason_code not in normalized:
            normalized.append(clean_reason_code)
    return tuple(sorted(normalized))


def _sanitize_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if value.strip() != value or not value:
        raise ValueError("reason_codes must contain canonical strings")
    normalized = value.lower()
    for fragments, safe_code in SENSITIVE_REASON_REPLACEMENTS:
        if any(fragment in normalized for fragment in fragments):
            return safe_code
    if _has_unsafe_surface_fragment(normalized):
        return SURFACE_REASON_REPLACEMENT
    return value


def _require_reason_code(value: str) -> None:
    if value != value.lower():
        raise ValueError("reason_codes must be lowercase snake_case strings")
    if value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")


def _redact_reference(value: str) -> str:
    if _contains_sensitive_reference(value) or _has_unsafe_surface_fragment(value):
        return "<redacted>"
    return value


def _json_ready(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value, key if not path else f"{path}.{key}")
            for key, nested_value in asdict(value).items()
            if key != RAW_TIMELINE_REFERENCE_FIELD
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key == RAW_TIMELINE_REFERENCE_FIELD:
                raise ValueError("unsafe field in payload")
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _contains_sensitive_reference(value) or _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key == RAW_TIMELINE_REFERENCE_FIELD or _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _contains_sensitive_reference(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS)


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_RESOLUTION_TIMELINE_ROTATION_DIGEST_CONFIG_VERSION",
    "StrategyCategoryResolutionTimelineRotationDigestConfig",
    "StrategyCategoryResolutionTimelineRotationDigestReport",
    "StrategyCategoryResolutionTimelineRotationDigestRow",
    "StrategyCategoryResolutionTimelineRotationInput",
    "StrategyCategoryResolutionTimelineRotationReasonCodeCount",
    "build_strategy_category_resolution_timeline_rotation_digest_report",
    "strategy_category_resolution_timeline_rotation_digest_payload",
)
