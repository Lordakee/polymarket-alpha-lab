"""Pure Phase 1 paper-only category exposure guard v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, date, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any


__all__ = (
    "StrategyCategoryExposureGuardV2Candidate",
    "StrategyCategoryExposureGuardV2Config",
    "StrategyCategoryExposureGuardV2Position",
    "StrategyCategoryExposureGuardV2Report",
    "StrategyCategoryExposureGuardV2Row",
    "build_strategy_category_exposure_guard_v2_report",
    "strategy_category_exposure_guard_v2_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-category-exposure-guard-v2"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUSES = ("pass", "watch", "blocked")
PASS_REASON = "category_exposure_guard_v2_pass"
EMPTY_REASON = "category_exposure_guard_v2_empty"
REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    PASS_REASON,
    "category_concentration_watch",
    "category_concentration_blocked",
    "team_concentration_watch",
    "team_concentration_blocked",
    "correlated_event_exposure_watch",
    "correlated_event_exposure_blocked",
    "liquidity_overlap_watch",
    "liquidity_overlap_blocked",
    "settlement_date_cluster_watch",
    "settlement_date_cluster_blocked",
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
UNSAFE_PUBLIC_PAYLOAD_TOKENS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
ROW_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "candidate_id",
    "market_slug",
    "outcome_name",
    "category_id",
    "team_id",
    "event_id",
    "liquidity_pool_id",
    "settlement_date",
    "proposed_notional",
    "probability",
    "liquidity_depth_notional",
    "total_portfolio_notional_after_candidate",
    "category_exposure_ratio",
    "team_exposure_ratio",
    "event_exposure_ratio",
    "liquidity_pool_exposure_ratio",
    "settlement_date_exposure_ratio",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_FIELDS = (*ROW_PUBLIC_FIELDS_WITHOUT_DIGEST, DERIVED_VALIDATION_DIGEST_FIELD)
REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "existing_position_count",
    "candidate_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "total_existing_exposure_notional",
    "max_category_exposure_ratio",
    "max_team_exposure_ratio",
    "max_correlated_event_exposure_ratio",
    "max_liquidity_pool_exposure_ratio",
    "max_settlement_date_exposure_ratio",
    "status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    *REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


@dataclass(frozen=True)
class StrategyCategoryExposureGuardV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    category_watch_ratio: Decimal = Decimal("0.350000")
    category_block_ratio: Decimal = Decimal("0.450000")
    team_watch_ratio: Decimal = Decimal("0.350000")
    team_block_ratio: Decimal = Decimal("0.450000")
    event_watch_ratio: Decimal = Decimal("0.350000")
    event_block_ratio: Decimal = Decimal("0.450000")
    liquidity_pool_watch_ratio: Decimal = Decimal("0.350000")
    liquidity_pool_block_ratio: Decimal = Decimal("0.450000")
    settlement_date_watch_ratio: Decimal = Decimal("0.350000")
    settlement_date_block_ratio: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCategoryExposureGuardV2Config:
            raise TypeError(
                "StrategyCategoryExposureGuardV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyCategoryExposureGuardV2Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_watch_ratio",
            "category_block_ratio",
            "team_watch_ratio",
            "team_block_ratio",
            "event_watch_ratio",
            "event_block_ratio",
            "liquidity_pool_watch_ratio",
            "liquidity_pool_block_ratio",
            "settlement_date_watch_ratio",
            "settlement_date_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "category",
            self.category_watch_ratio,
            self.category_block_ratio,
        )
        _require_threshold_sequence("team", self.team_watch_ratio, self.team_block_ratio)
        _require_threshold_sequence("event", self.event_watch_ratio, self.event_block_ratio)
        _require_threshold_sequence(
            "liquidity_pool",
            self.liquidity_pool_watch_ratio,
            self.liquidity_pool_block_ratio,
        )
        _require_threshold_sequence(
            "settlement_date",
            self.settlement_date_watch_ratio,
            self.settlement_date_block_ratio,
        )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryExposureGuardV2Position:
    position_id: str
    category_id: str
    team_id: str
    event_id: str
    liquidity_pool_id: str
    settlement_date: date
    exposure_notional: Decimal
    probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCategoryExposureGuardV2Position:
            raise TypeError(
                "StrategyCategoryExposureGuardV2Position does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("position", self, StrategyCategoryExposureGuardV2Position)
        for field_name in (
            "position_id",
            "category_id",
            "team_id",
            "event_id",
            "liquidity_pool_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "settlement_date", _normalize_date("settlement_date", self.settlement_date))
        object.__setattr__(
            self,
            "exposure_notional",
            _normalize_nonnegative_decimal("exposure_notional", self.exposure_notional),
        )
        object.__setattr__(
            self,
            "probability",
            _normalize_probability_decimal("probability", self.probability),
        )
        _reject_unsafe_public_payload("position", self)
        _require_hard_flags("position", self)


@dataclass(frozen=True)
class StrategyCategoryExposureGuardV2Candidate:
    candidate_id: str
    market_slug: str
    outcome_name: str
    category_id: str
    team_id: str
    event_id: str
    liquidity_pool_id: str
    settlement_date: date
    proposed_notional: Decimal
    probability: Decimal
    liquidity_depth_notional: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCategoryExposureGuardV2Candidate:
            raise TypeError(
                "StrategyCategoryExposureGuardV2Candidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("candidate", self, StrategyCategoryExposureGuardV2Candidate)
        for field_name in (
            "candidate_id",
            "market_slug",
            "outcome_name",
            "category_id",
            "team_id",
            "event_id",
            "liquidity_pool_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "settlement_date", _normalize_date("settlement_date", self.settlement_date))
        object.__setattr__(
            self,
            "proposed_notional",
            _normalize_positive_decimal("proposed_notional", self.proposed_notional),
        )
        object.__setattr__(
            self,
            "probability",
            _normalize_probability_decimal("probability", self.probability),
        )
        object.__setattr__(
            self,
            "liquidity_depth_notional",
            _normalize_positive_decimal(
                "liquidity_depth_notional",
                self.liquidity_depth_notional,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("candidate", self)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyCategoryExposureGuardV2Row:
    candidate_id: str
    market_slug: str
    outcome_name: str
    category_id: str
    team_id: str
    event_id: str
    liquidity_pool_id: str
    settlement_date: date
    proposed_notional: Decimal
    probability: Decimal
    liquidity_depth_notional: Decimal
    total_portfolio_notional_after_candidate: Decimal
    category_exposure_ratio: Decimal
    team_exposure_ratio: Decimal
    event_exposure_ratio: Decimal
    liquidity_pool_exposure_ratio: Decimal
    settlement_date_exposure_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCategoryExposureGuardV2Row:
            raise TypeError("StrategyCategoryExposureGuardV2Row does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyCategoryExposureGuardV2Row)
        for field_name in (
            "candidate_id",
            "market_slug",
            "outcome_name",
            "category_id",
            "team_id",
            "event_id",
            "liquidity_pool_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "settlement_date", _normalize_date("settlement_date", self.settlement_date))
        for field_name in (
            "proposed_notional",
            "liquidity_depth_notional",
            "total_portfolio_notional_after_candidate",
            "category_exposure_ratio",
            "team_exposure_ratio",
            "event_exposure_ratio",
            "liquidity_pool_exposure_ratio",
            "settlement_date_exposure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability",
            _normalize_probability_decimal("probability", self.probability),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_status_reason_pair(self.status, self.reason_codes)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_derived_validation_digest(self)


@dataclass(frozen=True)
class StrategyCategoryExposureGuardV2Report:
    generated_at: datetime
    config_version: str
    existing_position_count: Decimal
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_existing_exposure_notional: Decimal
    max_category_exposure_ratio: Decimal
    max_team_exposure_ratio: Decimal
    max_correlated_event_exposure_ratio: Decimal
    max_liquidity_pool_exposure_ratio: Decimal
    max_settlement_date_exposure_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCategoryExposureGuardV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCategoryExposureGuardV2Report:
            raise TypeError(
                "StrategyCategoryExposureGuardV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyCategoryExposureGuardV2Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "existing_position_count",
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in (
            "total_existing_exposure_notional",
            "max_category_exposure_ratio",
            "max_team_exposure_ratio",
            "max_correlated_event_exposure_ratio",
            "max_liquidity_pool_exposure_ratio",
            "max_settlement_date_exposure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_strategy_category_exposure_guard_v2_report(
    existing_positions: Iterable[StrategyCategoryExposureGuardV2Position],
    candidates: Iterable[StrategyCategoryExposureGuardV2Candidate],
    *,
    config: StrategyCategoryExposureGuardV2Config,
    generated_at: datetime,
) -> StrategyCategoryExposureGuardV2Report:
    _require_exact_type("config", config, StrategyCategoryExposureGuardV2Config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_positions = _normalize_positions(existing_positions)
    normalized_candidates = _normalize_candidates(candidates)
    total_existing = _sum_decimals(item.exposure_notional for item in normalized_positions)
    rows = tuple(
        sorted(
            (
                _row_for_candidate(candidate, normalized_positions, total_existing, config)
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return StrategyCategoryExposureGuardV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        existing_position_count=_count(len(normalized_positions)),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_existing_exposure_notional=total_existing,
        max_category_exposure_ratio=_max_row_decimal(rows, "category_exposure_ratio"),
        max_team_exposure_ratio=_max_row_decimal(rows, "team_exposure_ratio"),
        max_correlated_event_exposure_ratio=_max_row_decimal(rows, "event_exposure_ratio"),
        max_liquidity_pool_exposure_ratio=_max_row_decimal(rows, "liquidity_pool_exposure_ratio"),
        max_settlement_date_exposure_ratio=_max_row_decimal(
            rows,
            "settlement_date_exposure_ratio",
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        rows=rows,
    )


def strategy_category_exposure_guard_v2_payload(
    report: StrategyCategoryExposureGuardV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyCategoryExposureGuardV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        for row in report.rows:
            _validate_row_derived_validation_digest(row)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_report_payload_fields(report)
        _validate_report_payload(report)
        return dict(report)
    raise ValueError("report must be a StrategyCategoryExposureGuardV2Report")


def _row_for_candidate(
    candidate: StrategyCategoryExposureGuardV2Candidate,
    positions: tuple[StrategyCategoryExposureGuardV2Position, ...],
    total_existing: Decimal,
    config: StrategyCategoryExposureGuardV2Config,
) -> StrategyCategoryExposureGuardV2Row:
    total_after = _sum_decimals((total_existing, candidate.proposed_notional))
    category_ratio = _candidate_group_ratio(
        positions,
        candidate.proposed_notional,
        total_after,
        "category_id",
        candidate.category_id,
    )
    team_ratio = _candidate_group_ratio(
        positions,
        candidate.proposed_notional,
        total_after,
        "team_id",
        candidate.team_id,
    )
    event_ratio = _candidate_group_ratio(
        positions,
        candidate.proposed_notional,
        total_after,
        "event_id",
        candidate.event_id,
    )
    liquidity_ratio = _candidate_group_ratio(
        positions,
        candidate.proposed_notional,
        total_after,
        "liquidity_pool_id",
        candidate.liquidity_pool_id,
    )
    settlement_ratio = _candidate_group_ratio(
        positions,
        candidate.proposed_notional,
        total_after,
        "settlement_date",
        candidate.settlement_date,
    )
    reason_codes = _row_reason_codes(
        candidate.reason_codes,
        category_ratio=category_ratio,
        team_ratio=team_ratio,
        event_ratio=event_ratio,
        liquidity_ratio=liquidity_ratio,
        settlement_ratio=settlement_ratio,
        config=config,
    )
    return StrategyCategoryExposureGuardV2Row(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        outcome_name=candidate.outcome_name,
        category_id=candidate.category_id,
        team_id=candidate.team_id,
        event_id=candidate.event_id,
        liquidity_pool_id=candidate.liquidity_pool_id,
        settlement_date=candidate.settlement_date,
        proposed_notional=candidate.proposed_notional,
        probability=candidate.probability,
        liquidity_depth_notional=candidate.liquidity_depth_notional,
        total_portfolio_notional_after_candidate=total_after,
        category_exposure_ratio=category_ratio,
        team_exposure_ratio=team_ratio,
        event_exposure_ratio=event_ratio,
        liquidity_pool_exposure_ratio=liquidity_ratio,
        settlement_date_exposure_ratio=settlement_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _candidate_group_ratio(
    positions: tuple[StrategyCategoryExposureGuardV2Position, ...],
    candidate_notional: Decimal,
    total_after: Decimal,
    field_name: str,
    value: object,
) -> Decimal:
    group_total = candidate_notional
    with localcontext(DECIMAL_CONTEXT):
        for position in positions:
            if getattr(position, field_name) == value:
                group_total += position.exposure_notional
    return _divide_decimal(_quantize(group_total), total_after)


def _row_reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    category_ratio: Decimal,
    team_ratio: Decimal,
    event_ratio: Decimal,
    liquidity_ratio: Decimal,
    settlement_ratio: Decimal,
    config: StrategyCategoryExposureGuardV2Config,
) -> tuple[str, ...]:
    reason_codes = list(source_reason_codes)
    reason_codes.extend(
        _threshold_reason_codes(
            category_ratio,
            watch_threshold=config.category_watch_ratio,
            block_threshold=config.category_block_ratio,
            watch_reason="category_concentration_watch",
            block_reason="category_concentration_blocked",
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            team_ratio,
            watch_threshold=config.team_watch_ratio,
            block_threshold=config.team_block_ratio,
            watch_reason="team_concentration_watch",
            block_reason="team_concentration_blocked",
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            event_ratio,
            watch_threshold=config.event_watch_ratio,
            block_threshold=config.event_block_ratio,
            watch_reason="correlated_event_exposure_watch",
            block_reason="correlated_event_exposure_blocked",
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            liquidity_ratio,
            watch_threshold=config.liquidity_pool_watch_ratio,
            block_threshold=config.liquidity_pool_block_ratio,
            watch_reason="liquidity_overlap_watch",
            block_reason="liquidity_overlap_blocked",
        ),
    )
    reason_codes.extend(
        _threshold_reason_codes(
            settlement_ratio,
            watch_threshold=config.settlement_date_watch_ratio,
            block_threshold=config.settlement_date_block_ratio,
            watch_reason="settlement_date_cluster_watch",
            block_reason="settlement_date_cluster_blocked",
        ),
    )
    if not any(reason_code in REASON_CODES and reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes.append(PASS_REASON)
    return _normalize_row_reason_codes("reason_codes", tuple(reason_codes))


def _threshold_reason_codes(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value >= block_threshold:
        return (block_reason,)
    if value >= watch_threshold:
        return (watch_reason,)
    return ()


def _report_reason_codes(rows: tuple[StrategyCategoryExposureGuardV2Row, ...]) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in REASON_CODES and reason_code != PASS_REASON
        )
    if reason_codes:
        return _normalize_report_reason_codes("reason_codes", tuple(reason_codes))
    if rows:
        return (PASS_REASON,)
    return (EMPTY_REASON,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_count(rows: tuple[StrategyCategoryExposureGuardV2Row, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_positions(
    positions: Iterable[StrategyCategoryExposureGuardV2Position],
) -> tuple[StrategyCategoryExposureGuardV2Position, ...]:
    if isinstance(positions, (str, bytes, dict)):
        raise ValueError("existing_positions must be an iterable")
    try:
        items = tuple(positions)
    except TypeError as exc:
        raise ValueError("existing_positions must be an iterable") from exc
    for item in items:
        _require_exact_type("position", item, StrategyCategoryExposureGuardV2Position)
        _require_hard_flags("position", item)
    return tuple(sorted(items, key=_position_sort_key))


def _normalize_candidates(
    candidates: Iterable[StrategyCategoryExposureGuardV2Candidate],
) -> tuple[StrategyCategoryExposureGuardV2Candidate, ...]:
    if isinstance(candidates, (str, bytes, dict)):
        raise ValueError("candidates must be an iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for item in items:
        _require_exact_type("candidate", item, StrategyCategoryExposureGuardV2Candidate)
        _require_hard_flags("candidate", item)
    return tuple(sorted(items, key=_candidate_sort_key))


def _normalize_rows(rows: Iterable[StrategyCategoryExposureGuardV2Row]) -> tuple[StrategyCategoryExposureGuardV2Row, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        _require_exact_type("row", item, StrategyCategoryExposureGuardV2Row)
        _require_hard_flags("row", item)
        _validate_row_derived_validation_digest(item)
    return items


def _validate_report_consistency(report: StrategyCategoryExposureGuardV2Report) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must equal rows length")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal watch rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must equal blocked rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.candidate_count:
        raise ValueError("status counts must equal candidate_count")
    if report.max_category_exposure_ratio != _max_row_decimal(report.rows, "category_exposure_ratio"):
        raise ValueError("max_category_exposure_ratio mismatch")
    if report.max_team_exposure_ratio != _max_row_decimal(report.rows, "team_exposure_ratio"):
        raise ValueError("max_team_exposure_ratio mismatch")
    if report.max_correlated_event_exposure_ratio != _max_row_decimal(report.rows, "event_exposure_ratio"):
        raise ValueError("max_correlated_event_exposure_ratio mismatch")
    if report.max_liquidity_pool_exposure_ratio != _max_row_decimal(
        report.rows,
        "liquidity_pool_exposure_ratio",
    ):
        raise ValueError("max_liquidity_pool_exposure_ratio mismatch")
    if report.max_settlement_date_exposure_ratio != _max_row_decimal(
        report.rows,
        "settlement_date_exposure_ratio",
    ):
        raise ValueError("max_settlement_date_exposure_ratio mismatch")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row reason_codes")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_status_reason_pair(status: str, reason_codes: tuple[str, ...]) -> None:
    if status != _status_from_reason_codes(reason_codes):
        raise ValueError("status must match reason_codes")
    if status == "pass" and PASS_REASON not in reason_codes:
        raise ValueError("pass rows must include pass reason")


def _row_public_payload_values(row: StrategyCategoryExposureGuardV2Row) -> dict[str, object]:
    return {
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "outcome_name": row.outcome_name,
        "category_id": row.category_id,
        "team_id": row.team_id,
        "event_id": row.event_id,
        "liquidity_pool_id": row.liquidity_pool_id,
        "settlement_date": row.settlement_date.isoformat(),
        "proposed_notional": _decimal_payload(row.proposed_notional),
        "probability": _decimal_payload(row.probability),
        "liquidity_depth_notional": _decimal_payload(row.liquidity_depth_notional),
        "total_portfolio_notional_after_candidate": _decimal_payload(
            row.total_portfolio_notional_after_candidate,
        ),
        "category_exposure_ratio": _decimal_payload(row.category_exposure_ratio),
        "team_exposure_ratio": _decimal_payload(row.team_exposure_ratio),
        "event_exposure_ratio": _decimal_payload(row.event_exposure_ratio),
        "liquidity_pool_exposure_ratio": _decimal_payload(row.liquidity_pool_exposure_ratio),
        "settlement_date_exposure_ratio": _decimal_payload(row.settlement_date_exposure_ratio),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: StrategyCategoryExposureGuardV2Row) -> dict[str, object]:
    payload = _row_public_payload_values(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _report_public_payload_values(report: StrategyCategoryExposureGuardV2Report) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.astimezone(UTC).isoformat(),
        "config_version": report.config_version,
        "existing_position_count": _decimal_payload(report.existing_position_count),
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "total_existing_exposure_notional": _decimal_payload(
            report.total_existing_exposure_notional,
        ),
        "max_category_exposure_ratio": _decimal_payload(report.max_category_exposure_ratio),
        "max_team_exposure_ratio": _decimal_payload(report.max_team_exposure_ratio),
        "max_correlated_event_exposure_ratio": _decimal_payload(
            report.max_correlated_event_exposure_ratio,
        ),
        "max_liquidity_pool_exposure_ratio": _decimal_payload(
            report.max_liquidity_pool_exposure_ratio,
        ),
        "max_settlement_date_exposure_ratio": _decimal_payload(
            report.max_settlement_date_exposure_ratio,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: StrategyCategoryExposureGuardV2Row) -> str:
    return _derived_validation_digest(
        "strategy_category_exposure_guard_v2_row",
        ROW_PUBLIC_FIELDS_WITHOUT_DIGEST,
        _row_public_payload_values(row),
    )


def _report_derived_validation_digest(report: StrategyCategoryExposureGuardV2Report) -> str:
    return _derived_validation_digest(
        "strategy_category_exposure_guard_v2_report",
        REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST,
        _report_public_payload_values(report),
    )


def _validate_row_derived_validation_digest(row: StrategyCategoryExposureGuardV2Row) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(report: StrategyCategoryExposureGuardV2Report) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(
    label: str,
    field_names: tuple[str, ...],
    payload: dict[str, object],
) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in field_names
    )
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_payload_value(value: object) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(value[key])}" for key in sorted(value)
        ) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    if isinstance(value, tuple):
        return "(" + ",".join(_digest_payload_value(item) for item in value) + ")"
    return str(value)


def _require_report_payload_fields(payload: dict[str, object]) -> None:
    for field_name in REPORT_PUBLIC_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(REPORT_PUBLIC_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _require_row_payload_fields(payload: dict[str, object]) -> None:
    for field_name in ROW_PUBLIC_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(ROW_PUBLIC_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public row field: {extra_fields[0]}")


def _validate_report_payload(payload: dict[str, object]) -> None:
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "existing_position_count",
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "total_existing_exposure_notional",
        "max_category_exposure_ratio",
        "max_team_exposure_ratio",
        "max_correlated_event_exposure_ratio",
        "max_liquidity_pool_exposure_ratio",
        "max_settlement_date_exposure_ratio",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _normalize_report_public_reason_codes("reason_codes", payload["reason_codes"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row_payload in payload["rows"]:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain objects")
        _require_row_payload_fields(row_payload)
        _validate_row_payload(row_payload)
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(
        "strategy_category_exposure_guard_v2_report",
        REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST,
        payload,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_row_payload(payload: dict[str, object]) -> None:
    for field_name in (
        "candidate_id",
        "market_slug",
        "outcome_name",
        "category_id",
        "team_id",
        "event_id",
        "liquidity_pool_id",
    ):
        _require_canonical_string(field_name, payload[field_name])
    _require_date_payload_string("settlement_date", payload["settlement_date"])
    for field_name in (
        "proposed_notional",
        "liquidity_depth_notional",
        "total_portfolio_notional_after_candidate",
        "category_exposure_ratio",
        "team_exposure_ratio",
        "event_exposure_ratio",
        "liquidity_pool_exposure_ratio",
        "settlement_date_exposure_ratio",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_decimal_payload_string("probability", payload["probability"], probability=True)
    _require_status("status", payload["status"])
    _normalize_row_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(
        "strategy_category_exposure_guard_v2_row",
        ROW_PUBLIC_FIELDS_WITHOUT_DIGEST,
        payload,
    ):
        raise ValueError("derived_validation_digest must match row payload fields")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric values must be Decimal-derived strings")
    normalized = _quantize(value)
    return format(normalized, "f")


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(decimal_value)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    return normalized


def _require_date_payload_string(field_name: str, value: object) -> date:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a date string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a date string") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical date string")
    return parsed


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    return parsed


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _max_row_decimal(rows: tuple[StrategyCategoryExposureGuardV2Row, ...], field_name: str) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use 6 decimal places or fewer")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _normalize_date(field_name: str, value: object) -> date:
    if type(value) is not date:
        raise ValueError(f"{field_name} must be a date")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_source_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    normalized: list[str] = []
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _normalize_row_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    normalized = _normalize_source_reason_codes(field_name, values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if any(reason_code in REASON_CODES and reason_code != PASS_REASON for reason_code in normalized):
        normalized = tuple(reason_code for reason_code in normalized if reason_code != PASS_REASON)
    unknown_guard_reasons = [
        reason_code
        for reason_code in normalized
        if reason_code.startswith("category_")
        or reason_code.startswith("team_")
        or reason_code.startswith("correlated_")
        or reason_code.startswith("liquidity_")
        or reason_code.startswith("settlement_")
    ]
    if any(reason_code not in REASON_CODES for reason_code in unknown_guard_reasons):
        raise ValueError(f"{field_name} contains unknown guard reason code")
    return _sort_guard_reason_codes(normalized)


def _normalize_report_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    normalized = _normalize_source_reason_codes(field_name, values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if any(reason_code not in REASON_CODES for reason_code in normalized):
        raise ValueError(f"{field_name} contains unknown report reason code")
    return _sort_guard_reason_codes(normalized)


def _normalize_row_public_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_row_reason_codes(field_name, tuple(values))


def _normalize_report_public_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_report_reason_codes(field_name, tuple(values))


def _sort_guard_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    source_reasons = [reason_code for reason_code in reason_codes if reason_code not in REASON_CODES]
    guard_reasons = [
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in reason_codes and reason_code not in source_reasons
    ]
    return tuple([*source_reasons, *guard_reasons])


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_threshold_sequence(label: str, watch: Decimal, block: Decimal) -> None:
    if watch > block:
        raise ValueError(f"{label} watch threshold must be at most block threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_token(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if type(value) is date:
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_token(key):
                raise ValueError(f"unsafe public surface field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in UNSAFE_PUBLIC_PAYLOAD_TOKENS)


def _position_sort_key(
    item: StrategyCategoryExposureGuardV2Position,
) -> tuple[str, str, str]:
    return (item.position_id, item.event_id, item.category_id)


def _candidate_sort_key(
    item: StrategyCategoryExposureGuardV2Candidate,
) -> tuple[str, str, str]:
    return (item.candidate_id, item.event_id, item.market_slug)


def _row_sort_key(row: StrategyCategoryExposureGuardV2Row) -> tuple[int, Decimal, str]:
    return (_status_sort_rank(row.status), -row.category_exposure_ratio, row.candidate_id)


def _status_sort_rank(status: str) -> int:
    if status == "blocked":
        return 0
    if status == "watch":
        return 1
    return 2


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
