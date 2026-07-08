"""Pure report-only market microstructure outlier watch aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_OUTLIER_WATCH_CONFIG_VERSION = (
    "research-market-microstructure-outlier-watch-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_VALUES = frozenset((PASS_STATUS, WATCH_STATUS, BLOCK_STATUS))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_KEY_FRAGMENTS = (
    "raw",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source",
    "url",
    "text",
    "candidate",
    "dsn",
    "table",
    "token",
    "private",
    "auth",
    "wallet",
    "network",
    "database",
    "order",
    "buy",
    "sell",
    "trade",
    "position",
    "recommend",
    "sizing",
    "live",
)
_UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "candidate",
    "dsn",
    "wallet",
    "database",
    "order",
    "token",
    "private",
)
_REASON_CODE_SEQUENCE = (
    "spread_outlier_score_watch",
    "spread_outlier_score_block",
    "depth_imbalance_watch",
    "depth_imbalance_block",
    "stale_quote_age_watch",
    "stale_quote_age_block",
    "unexplained_book_movement_watch",
    "unexplained_book_movement_block",
    "fee_friction_watch",
    "fee_friction_block",
    "manual_review_urgency_watch",
    "manual_review_urgency_block",
    "microstructure_outlier_watch_watch",
    "microstructure_outlier_watch_block",
    "microstructure_outlier_watch_passed",
)


@dataclass(frozen=True)
class ResearchMarketMicrostructureOutlierWatchConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_OUTLIER_WATCH_CONFIG_VERSION
    )
    watch_spread_outlier_score: Decimal = Decimal("0.350000")
    block_spread_outlier_score: Decimal = Decimal("0.700000")
    watch_depth_imbalance_score: Decimal = Decimal("0.300000")
    block_depth_imbalance_score: Decimal = Decimal("0.650000")
    watch_quote_age_seconds: Decimal = Decimal("60.000000")
    block_quote_age_seconds: Decimal = Decimal("300.000000")
    watch_unexplained_book_movement_score: Decimal = Decimal("0.300000")
    block_unexplained_book_movement_score: Decimal = Decimal("0.650000")
    watch_fee_friction_score: Decimal = Decimal("0.250000")
    block_fee_friction_score: Decimal = Decimal("0.500000")
    watch_manual_review_urgency_score: Decimal = Decimal("0.350000")
    block_manual_review_urgency_score: Decimal = Decimal("0.700000")
    block_signal_count_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureOutlierWatchConfig:
            raise TypeError(
                "ResearchMarketMicrostructureOutlierWatchConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureOutlierWatchConfig:
            raise ValueError(
                "config must be exactly ResearchMarketMicrostructureOutlierWatchConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_OUTLIER_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_spread_outlier_score",
            "block_spread_outlier_score",
            "watch_depth_imbalance_score",
            "block_depth_imbalance_score",
            "watch_unexplained_book_movement_score",
            "block_unexplained_book_movement_score",
            "watch_fee_friction_score",
            "block_fee_friction_score",
            "watch_manual_review_urgency_score",
            "block_manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_quote_age_seconds", "block_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "block_signal_count_threshold",
            _require_positive_decimal(
                "block_signal_count_threshold",
                self.block_signal_count_threshold,
            ),
        )
        _require_threshold_pair(
            "block_spread_outlier_score",
            self.watch_spread_outlier_score,
            self.block_spread_outlier_score,
        )
        _require_threshold_pair(
            "block_depth_imbalance_score",
            self.watch_depth_imbalance_score,
            self.block_depth_imbalance_score,
        )
        _require_threshold_pair(
            "block_quote_age_seconds",
            self.watch_quote_age_seconds,
            self.block_quote_age_seconds,
        )
        _require_threshold_pair(
            "block_unexplained_book_movement_score",
            self.watch_unexplained_book_movement_score,
            self.block_unexplained_book_movement_score,
        )
        _require_threshold_pair(
            "block_fee_friction_score",
            self.watch_fee_friction_score,
            self.block_fee_friction_score,
        )
        _require_threshold_pair(
            "block_manual_review_urgency_score",
            self.watch_manual_review_urgency_score,
            self.block_manual_review_urgency_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureOutlierObservation:
    observed_at: datetime
    spread_outlier_score: Decimal
    depth_imbalance_score: Decimal
    quote_age_seconds: Decimal
    book_movement_score: Decimal
    book_movement_explained: bool
    fee_friction_score: Decimal
    manual_review_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureOutlierObservation:
            raise TypeError(
                "ResearchMarketMicrostructureOutlierObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureOutlierObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketMicrostructureOutlierObservation",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_outlier_score",
            "depth_imbalance_score",
            "book_movement_score",
            "fee_friction_score",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        _require_bool("book_movement_explained", self.book_movement_explained)
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureOutlierWatchRow:
    observed_at: datetime
    spread_outlier_score: Decimal
    depth_imbalance_score: Decimal
    quote_age_seconds: Decimal
    unexplained_book_movement_score: Decimal
    fee_friction_score: Decimal
    manual_review_urgency_score: Decimal
    outlier_signal_count: Decimal
    spread_outlier: bool
    depth_imbalance: bool
    stale_quote: bool
    unexplained_book_movement: bool
    fee_friction: bool
    manual_review_urgent: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureOutlierWatchRow:
            raise TypeError(
                "ResearchMarketMicrostructureOutlierWatchRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureOutlierWatchRow:
            raise ValueError(
                "row must be exactly ResearchMarketMicrostructureOutlierWatchRow",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_outlier_score",
            "depth_imbalance_score",
            "unexplained_book_movement_score",
            "fee_friction_score",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("quote_age_seconds", "outlier_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_outlier",
            "depth_imbalance",
            "stale_quote",
            "unexplained_book_movement",
            "fee_friction",
            "manual_review_urgent",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureOutlierWatchReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    spread_outlier_count: Decimal
    depth_imbalance_count: Decimal
    stale_quote_count: Decimal
    unexplained_book_movement_count: Decimal
    fee_friction_count: Decimal
    manual_review_urgent_count: Decimal
    max_spread_outlier_score: Decimal
    max_depth_imbalance_score: Decimal
    max_quote_age_seconds: Decimal
    max_unexplained_book_movement_score: Decimal
    max_fee_friction_score: Decimal
    max_manual_review_urgency_score: Decimal
    rows: tuple[ResearchMarketMicrostructureOutlierWatchRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureOutlierWatchReport:
            raise TypeError(
                "ResearchMarketMicrostructureOutlierWatchReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureOutlierWatchReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketMicrostructureOutlierWatchReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_OUTLIER_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "spread_outlier_count",
            "depth_imbalance_count",
            "stale_quote_count",
            "unexplained_book_movement_count",
            "fee_friction_count",
            "manual_review_urgent_count",
            "max_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_outlier_score",
            "max_depth_imbalance_score",
            "max_unexplained_book_movement_score",
            "max_fee_friction_score",
            "max_manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_market_microstructure_outlier_watch_report_payload(self)


def build_research_market_microstructure_outlier_watch_report(
    observations: Iterable[ResearchMarketMicrostructureOutlierObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketMicrostructureOutlierWatchConfig | None = None,
) -> ResearchMarketMicrostructureOutlierWatchReport:
    """Build a deterministic local report-only microstructure outlier watch."""

    if config is None:
        config = ResearchMarketMicrostructureOutlierWatchConfig()
    if type(config) is not ResearchMarketMicrostructureOutlierWatchConfig:
        raise ValueError(
            "config must be a ResearchMarketMicrostructureOutlierWatchConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "observation_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(_status_count(rows, PASS_STATUS)),
        "watch_count": _count_decimal(_status_count(rows, WATCH_STATUS)),
        "block_count": _count_decimal(_status_count(rows, BLOCK_STATUS)),
        "spread_outlier_count": _flag_total(rows, "spread_outlier"),
        "depth_imbalance_count": _flag_total(rows, "depth_imbalance"),
        "stale_quote_count": _flag_total(rows, "stale_quote"),
        "unexplained_book_movement_count": _flag_total(
            rows,
            "unexplained_book_movement",
        ),
        "fee_friction_count": _flag_total(rows, "fee_friction"),
        "manual_review_urgent_count": _flag_total(rows, "manual_review_urgent"),
        "max_spread_outlier_score": _max_decimal(
            row.spread_outlier_score for row in rows
        ),
        "max_depth_imbalance_score": _max_decimal(
            row.depth_imbalance_score for row in rows
        ),
        "max_quote_age_seconds": _max_decimal(row.quote_age_seconds for row in rows),
        "max_unexplained_book_movement_score": _max_decimal(
            row.unexplained_book_movement_score for row in rows
        ),
        "max_fee_friction_score": _max_decimal(row.fee_friction_score for row in rows),
        "max_manual_review_urgency_score": _max_decimal(
            row.manual_review_urgency_score for row in rows
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketMicrostructureOutlierWatchReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_microstructure_outlier_watch_report_payload(
    report: ResearchMarketMicrostructureOutlierWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketMicrostructureOutlierWatchReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketMicrostructureOutlierWatchReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_market_microstructure_outlier_watch_public_payload(payload)
    return payload


def validate_research_market_microstructure_outlier_watch_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def research_market_microstructure_outlier_watch_report_digest(
    report: ResearchMarketMicrostructureOutlierWatchReport,
) -> str:
    if type(report) is not ResearchMarketMicrostructureOutlierWatchReport:
        raise ValueError(
            "report must be a ResearchMarketMicrostructureOutlierWatchReport",
        )
    _require_hard_flags("report", report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def _build_rows(
    observations: tuple[ResearchMarketMicrostructureOutlierObservation, ...],
    config: ResearchMarketMicrostructureOutlierWatchConfig,
) -> tuple[ResearchMarketMicrostructureOutlierWatchRow, ...]:
    rows = tuple(_row_from_observation(observation, config) for observation in observations)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_observation(
    observation: ResearchMarketMicrostructureOutlierObservation,
    config: ResearchMarketMicrostructureOutlierWatchConfig,
) -> ResearchMarketMicrostructureOutlierWatchRow:
    spread_level = _threshold_level(
        observation.spread_outlier_score,
        config.watch_spread_outlier_score,
        config.block_spread_outlier_score,
    )
    depth_level = _threshold_level(
        observation.depth_imbalance_score,
        config.watch_depth_imbalance_score,
        config.block_depth_imbalance_score,
    )
    stale_level = _threshold_level(
        observation.quote_age_seconds,
        config.watch_quote_age_seconds,
        config.block_quote_age_seconds,
    )
    movement_score = (
        observation.book_movement_score
        if observation.book_movement_explained is False
        else _ZERO
    )
    movement_level = _threshold_level(
        movement_score,
        config.watch_unexplained_book_movement_score,
        config.block_unexplained_book_movement_score,
    )
    fee_level = _threshold_level(
        observation.fee_friction_score,
        config.watch_fee_friction_score,
        config.block_fee_friction_score,
    )
    urgency_level = _threshold_level(
        observation.manual_review_urgency_score,
        config.watch_manual_review_urgency_score,
        config.block_manual_review_urgency_score,
    )
    levels = (
        spread_level,
        depth_level,
        stale_level,
        movement_level,
        fee_level,
        urgency_level,
    )
    signal_count = _count_decimal(sum(1 for level in levels if level is not None))
    status = _row_status(levels, signal_count, config)
    reason_codes = _row_reason_codes(
        spread_level=spread_level,
        depth_level=depth_level,
        stale_level=stale_level,
        movement_level=movement_level,
        fee_level=fee_level,
        urgency_level=urgency_level,
        status=status,
    )
    return ResearchMarketMicrostructureOutlierWatchRow(
        observed_at=observation.observed_at,
        spread_outlier_score=observation.spread_outlier_score,
        depth_imbalance_score=observation.depth_imbalance_score,
        quote_age_seconds=observation.quote_age_seconds,
        unexplained_book_movement_score=movement_score,
        fee_friction_score=observation.fee_friction_score,
        manual_review_urgency_score=observation.manual_review_urgency_score,
        outlier_signal_count=signal_count,
        spread_outlier=spread_level is not None,
        depth_imbalance=depth_level is not None,
        stale_quote=stale_level is not None,
        unexplained_book_movement=movement_level is not None,
        fee_friction=fee_level is not None,
        manual_review_urgent=urgency_level is not None,
        status=status,
        reason_codes=reason_codes,
    )


def _threshold_level(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str | None:
    if value >= block_threshold:
        return BLOCK_STATUS
    if value >= watch_threshold:
        return WATCH_STATUS
    return None


def _row_status(
    levels: tuple[str | None, ...],
    signal_count: Decimal,
    config: ResearchMarketMicrostructureOutlierWatchConfig,
) -> str:
    if any(level == BLOCK_STATUS for level in levels):
        return BLOCK_STATUS
    if signal_count >= config.block_signal_count_threshold:
        return BLOCK_STATUS
    if signal_count > _ZERO:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    spread_level: str | None,
    depth_level: str | None,
    stale_level: str | None,
    movement_level: str | None,
    fee_level: str | None,
    urgency_level: str | None,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_level_code(reason_codes, "spread_outlier_score", spread_level)
    _append_level_code(reason_codes, "depth_imbalance", depth_level)
    _append_level_code(reason_codes, "stale_quote_age", stale_level)
    _append_level_code(reason_codes, "unexplained_book_movement", movement_level)
    _append_level_code(reason_codes, "fee_friction", fee_level)
    _append_level_code(reason_codes, "manual_review_urgency", urgency_level)
    if status == BLOCK_STATUS:
        reason_codes.append("microstructure_outlier_watch_block")
    elif status == WATCH_STATUS:
        reason_codes.append("microstructure_outlier_watch_watch")
    else:
        reason_codes.append("microstructure_outlier_watch_passed")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_level_code(
    reason_codes: list[str],
    prefix: str,
    level: str | None,
) -> None:
    if level is not None:
        reason_codes.append(f"{prefix}_{level}")


def _row_sort_key(
    row: ResearchMarketMicrostructureOutlierWatchRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        -row.outlier_signal_count,
        -row.manual_review_urgency_score,
        -row.spread_outlier_score,
        -row.depth_imbalance_score,
        -row.quote_age_seconds,
        -row.unexplained_book_movement_score,
        -row.fee_friction_score,
        row.observed_at,
    )


def _report_status(
    rows: tuple[ResearchMarketMicrostructureOutlierWatchRow, ...],
) -> str:
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketMicrostructureOutlierWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("microstructure_outlier_watch_passed",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(row: ResearchMarketMicrostructureOutlierWatchRow) -> None:
    expected_signal_count = _count_decimal(
        sum(
            1
            for value in (
                row.spread_outlier,
                row.depth_imbalance,
                row.stale_quote,
                row.unexplained_book_movement,
                row.fee_friction,
                row.manual_review_urgent,
            )
            if value is True
        ),
    )
    if row.outlier_signal_count != expected_signal_count:
        raise ValueError("outlier_signal_count must match row flags")
    if row.status == PASS_STATUS and row.outlier_signal_count != _ZERO:
        raise ValueError("pass rows must have no outlier signals")
    if row.status in {WATCH_STATUS, BLOCK_STATUS} and row.outlier_signal_count == _ZERO:
        raise ValueError("watch and block rows must have outlier signals")
    if row.status == PASS_STATUS:
        expected_codes = ("microstructure_outlier_watch_passed",)
    else:
        if not any(code.endswith(row.status) for code in row.reason_codes):
            raise ValueError("status must match reason_codes")
        expected_codes = row.reason_codes
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes must match row status")
    if row.unexplained_book_movement is False and row.unexplained_book_movement_score != _ZERO:
        raise ValueError(
            "unexplained_book_movement_score requires unexplained book movement",
        )


def _validate_report_consistency(
    report: ResearchMarketMicrostructureOutlierWatchReport,
) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    for field_name, status in (
        ("pass_count", PASS_STATUS),
        ("watch_count", WATCH_STATUS),
        ("block_count", BLOCK_STATUS),
    ):
        if getattr(report, field_name) != _count_decimal(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    for field_name, row_field in (
        ("spread_outlier_count", "spread_outlier"),
        ("depth_imbalance_count", "depth_imbalance"),
        ("stale_quote_count", "stale_quote"),
        ("unexplained_book_movement_count", "unexplained_book_movement"),
        ("fee_friction_count", "fee_friction"),
        ("manual_review_urgent_count", "manual_review_urgent"),
    ):
        if getattr(report, field_name) != _flag_total(report.rows, row_field):
            raise ValueError(f"{field_name} must match rows")
    for field_name, values in (
        (
            "max_spread_outlier_score",
            (row.spread_outlier_score for row in report.rows),
        ),
        (
            "max_depth_imbalance_score",
            (row.depth_imbalance_score for row in report.rows),
        ),
        ("max_quote_age_seconds", (row.quote_age_seconds for row in report.rows)),
        (
            "max_unexplained_book_movement_score",
            (row.unexplained_book_movement_score for row in report.rows),
        ),
        ("max_fee_friction_score", (row.fee_friction_score for row in report.rows)),
        (
            "max_manual_review_urgency_score",
            (row.manual_review_urgency_score for row in report.rows),
        ),
    ):
        if getattr(report, field_name) != _max_decimal(values):
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Iterable[ResearchMarketMicrostructureOutlierObservation],
) -> tuple[ResearchMarketMicrostructureOutlierObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchMarketMicrostructureOutlierObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketMicrostructureOutlierObservation",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchMarketMicrostructureOutlierWatchRow],
) -> tuple[ResearchMarketMicrostructureOutlierWatchRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketMicrostructureOutlierWatchRow:
            raise ValueError(
                "rows must contain ResearchMarketMicrostructureOutlierWatchRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_threshold_pair(
    block_field_name: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed the watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if isinstance(value, datetime) and type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _flag_total(
    rows: tuple[ResearchMarketMicrostructureOutlierWatchRow, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name) is True))


def _status_count(
    rows: tuple[ResearchMarketMicrostructureOutlierWatchRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=_ZERO)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _status_rank(status: str) -> Decimal:
    if status == BLOCK_STATUS:
        return Decimal("0")
    if status == WATCH_STATUS:
        return Decimal("1")
    return Decimal("2")


def _report_values_without_digest(
    report: ResearchMarketMicrostructureOutlierWatchReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


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


__all__ = (
    "BLOCK_STATUS",
    "DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_OUTLIER_WATCH_CONFIG_VERSION",
    "PASS_STATUS",
    "ResearchMarketMicrostructureOutlierObservation",
    "ResearchMarketMicrostructureOutlierWatchConfig",
    "ResearchMarketMicrostructureOutlierWatchReport",
    "ResearchMarketMicrostructureOutlierWatchRow",
    "WATCH_STATUS",
    "build_research_market_microstructure_outlier_watch_report",
    "research_market_microstructure_outlier_watch_report_digest",
    "research_market_microstructure_outlier_watch_report_payload",
    "validate_research_market_microstructure_outlier_watch_public_payload",
)
