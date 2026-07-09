"""Pure report-only market microstructure signal quality aggregation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_SIGNAL_QUALITY_CONFIG_VERSION = (
    "research-market-microstructure-signal-quality-report-v0"
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
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source",
    "url",
    "text",
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
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "dsn",
    "wallet",
    "database",
    "order",
    "token",
    "private",
)
_REASON_CODE_SEQUENCE = (
    "spread_instability_watch",
    "spread_instability_block",
    "depth_imbalance_watch",
    "depth_imbalance_block",
    "update_age_watch",
    "update_age_block",
    "movement_attribution_watch",
    "movement_attribution_block",
    "microstructure_signal_quality_watch",
    "microstructure_signal_quality_block",
    "microstructure_signal_quality_pass",
    "no_microstructure_signal_quality_observations",
)
_REPORT_PUBLIC_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "spread_inconsistent_count",
        "depth_unbalanced_count",
        "update_stale_count",
        "movement_unattributed_count",
        "max_spread_instability_score",
        "max_depth_imbalance_score",
        "max_update_age_seconds",
        "max_unattributed_movement_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PUBLIC_FIELDS = frozenset(
    (
        "observed_at",
        "spread_instability_score",
        "depth_imbalance_score",
        "update_age_seconds",
        "unattributed_movement_score",
        "quality_signal_count",
        "spread_inconsistent",
        "depth_unbalanced",
        "update_stale",
        "movement_unattributed",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchMarketMicrostructureSignalQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_SIGNAL_QUALITY_CONFIG_VERSION
    )
    watch_spread_instability_score: Decimal = Decimal("0.300000")
    block_spread_instability_score: Decimal = Decimal("0.650000")
    watch_depth_imbalance_score: Decimal = Decimal("0.300000")
    block_depth_imbalance_score: Decimal = Decimal("0.650000")
    watch_update_age_seconds: Decimal = Decimal("60.000000")
    block_update_age_seconds: Decimal = Decimal("300.000000")
    watch_unattributed_movement_score: Decimal = Decimal("0.250000")
    block_unattributed_movement_score: Decimal = Decimal("0.600000")
    block_signal_count_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureSignalQualityConfig:
            raise TypeError(
                "ResearchMarketMicrostructureSignalQualityConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureSignalQualityConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketMicrostructureSignalQualityConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_SIGNAL_QUALITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_spread_instability_score",
            "block_spread_instability_score",
            "watch_depth_imbalance_score",
            "block_depth_imbalance_score",
            "watch_unattributed_movement_score",
            "block_unattributed_movement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_update_age_seconds", "block_update_age_seconds"):
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
            "block_spread_instability_score",
            self.watch_spread_instability_score,
            self.block_spread_instability_score,
        )
        _require_threshold_pair(
            "block_depth_imbalance_score",
            self.watch_depth_imbalance_score,
            self.block_depth_imbalance_score,
        )
        _require_threshold_pair(
            "block_update_age_seconds",
            self.watch_update_age_seconds,
            self.block_update_age_seconds,
        )
        _require_threshold_pair(
            "block_unattributed_movement_score",
            self.watch_unattributed_movement_score,
            self.block_unattributed_movement_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureSignalObservation:
    observed_at: datetime
    spread_stability_score: Decimal
    depth_balance_score: Decimal
    update_age_seconds: Decimal
    movement_magnitude_score: Decimal
    movement_attribution_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureSignalObservation:
            raise TypeError(
                "ResearchMarketMicrostructureSignalObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureSignalObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketMicrostructureSignalObservation",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_stability_score",
            "depth_balance_score",
            "movement_magnitude_score",
            "movement_attribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "update_age_seconds",
            _require_nonnegative_decimal("update_age_seconds", self.update_age_seconds),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureSignalQualityRow:
    observed_at: datetime
    spread_instability_score: Decimal
    depth_imbalance_score: Decimal
    update_age_seconds: Decimal
    unattributed_movement_score: Decimal
    quality_signal_count: Decimal
    spread_inconsistent: bool
    depth_unbalanced: bool
    update_stale: bool
    movement_unattributed: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureSignalQualityRow:
            raise TypeError(
                "ResearchMarketMicrostructureSignalQualityRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureSignalQualityRow:
            raise ValueError(
                "row must be exactly ResearchMarketMicrostructureSignalQualityRow",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_instability_score",
            "depth_imbalance_score",
            "unattributed_movement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("update_age_seconds", "quality_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_inconsistent",
            "depth_unbalanced",
            "update_stale",
            "movement_unattributed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureSignalQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    spread_inconsistent_count: Decimal
    depth_unbalanced_count: Decimal
    update_stale_count: Decimal
    movement_unattributed_count: Decimal
    max_spread_instability_score: Decimal
    max_depth_imbalance_score: Decimal
    max_update_age_seconds: Decimal
    max_unattributed_movement_score: Decimal
    rows: tuple[ResearchMarketMicrostructureSignalQualityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureSignalQualityReport:
            raise TypeError(
                "ResearchMarketMicrostructureSignalQualityReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureSignalQualityReport:
            raise ValueError(
                "report must be exactly ResearchMarketMicrostructureSignalQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_SIGNAL_QUALITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "spread_inconsistent_count",
            "depth_unbalanced_count",
            "update_stale_count",
            "movement_unattributed_count",
            "max_update_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_instability_score",
            "max_depth_imbalance_score",
            "max_unattributed_movement_score",
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
        return research_market_microstructure_signal_quality_report_payload(self)


def build_research_market_microstructure_signal_quality_report(
    observations: Iterable[ResearchMarketMicrostructureSignalObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketMicrostructureSignalQualityConfig | None = None,
) -> ResearchMarketMicrostructureSignalQualityReport:
    """Build a deterministic local report-only microstructure signal quality report."""

    if config is None:
        config = ResearchMarketMicrostructureSignalQualityConfig()
    if type(config) is not ResearchMarketMicrostructureSignalQualityConfig:
        raise ValueError(
            "config must be a ResearchMarketMicrostructureSignalQualityConfig",
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
        "spread_inconsistent_count": _flag_total(rows, "spread_inconsistent"),
        "depth_unbalanced_count": _flag_total(rows, "depth_unbalanced"),
        "update_stale_count": _flag_total(rows, "update_stale"),
        "movement_unattributed_count": _flag_total(rows, "movement_unattributed"),
        "max_spread_instability_score": _max_decimal(
            row.spread_instability_score for row in rows
        ),
        "max_depth_imbalance_score": _max_decimal(
            row.depth_imbalance_score for row in rows
        ),
        "max_update_age_seconds": _max_decimal(row.update_age_seconds for row in rows),
        "max_unattributed_movement_score": _max_decimal(
            row.unattributed_movement_score for row in rows
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketMicrostructureSignalQualityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_microstructure_signal_quality_report_payload(
    report: ResearchMarketMicrostructureSignalQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketMicrostructureSignalQualityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketMicrostructureSignalQualityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_market_microstructure_signal_quality_public_payload(payload)
    return payload


def validate_research_market_microstructure_signal_quality_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_json_ready_public_payload(payload)
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _validate_public_payload_semantics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def research_market_microstructure_signal_quality_report_digest(
    report: ResearchMarketMicrostructureSignalQualityReport,
) -> str:
    if type(report) is not ResearchMarketMicrostructureSignalQualityReport:
        raise ValueError(
            "report must be a ResearchMarketMicrostructureSignalQualityReport",
        )
    _require_hard_flags("report", report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def _build_rows(
    observations: tuple[ResearchMarketMicrostructureSignalObservation, ...],
    config: ResearchMarketMicrostructureSignalQualityConfig,
) -> tuple[ResearchMarketMicrostructureSignalQualityRow, ...]:
    rows = tuple(_row_from_observation(observation, config) for observation in observations)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_observation(
    observation: ResearchMarketMicrostructureSignalObservation,
    config: ResearchMarketMicrostructureSignalQualityConfig,
) -> ResearchMarketMicrostructureSignalQualityRow:
    spread_instability_score = _quantize(_ONE - observation.spread_stability_score)
    depth_imbalance_score = _quantize(_ONE - observation.depth_balance_score)
    unattributed_movement_score = _quantize(
        observation.movement_magnitude_score
        * (_ONE - observation.movement_attribution_score),
    )
    spread_level = _threshold_level(
        spread_instability_score,
        config.watch_spread_instability_score,
        config.block_spread_instability_score,
    )
    depth_level = _threshold_level(
        depth_imbalance_score,
        config.watch_depth_imbalance_score,
        config.block_depth_imbalance_score,
    )
    update_level = _threshold_level(
        observation.update_age_seconds,
        config.watch_update_age_seconds,
        config.block_update_age_seconds,
    )
    movement_level = _threshold_level(
        unattributed_movement_score,
        config.watch_unattributed_movement_score,
        config.block_unattributed_movement_score,
    )
    levels = (spread_level, depth_level, update_level, movement_level)
    signal_count = _count_decimal(sum(1 for level in levels if level is not None))
    status = _row_status(levels, signal_count, config)
    return ResearchMarketMicrostructureSignalQualityRow(
        observed_at=observation.observed_at,
        spread_instability_score=spread_instability_score,
        depth_imbalance_score=depth_imbalance_score,
        update_age_seconds=observation.update_age_seconds,
        unattributed_movement_score=unattributed_movement_score,
        quality_signal_count=signal_count,
        spread_inconsistent=spread_level is not None,
        depth_unbalanced=depth_level is not None,
        update_stale=update_level is not None,
        movement_unattributed=movement_level is not None,
        status=status,
        reason_codes=_row_reason_codes(
            spread_level=spread_level,
            depth_level=depth_level,
            update_level=update_level,
            movement_level=movement_level,
            status=status,
        ),
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
    config: ResearchMarketMicrostructureSignalQualityConfig,
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
    update_level: str | None,
    movement_level: str | None,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_level_code(reason_codes, "spread_instability", spread_level)
    _append_level_code(reason_codes, "depth_imbalance", depth_level)
    _append_level_code(reason_codes, "update_age", update_level)
    _append_level_code(reason_codes, "movement_attribution", movement_level)
    reason_codes.append(f"microstructure_signal_quality_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_level_code(
    reason_codes: list[str],
    prefix: str,
    level: str | None,
) -> None:
    if level is not None:
        reason_codes.append(f"{prefix}_{level}")


def _row_sort_key(
    row: ResearchMarketMicrostructureSignalQualityRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        -row.quality_signal_count,
        -row.unattributed_movement_score,
        -row.spread_instability_score,
        -row.depth_imbalance_score,
        -row.update_age_seconds,
        row.observed_at,
    )


def _report_status(
    rows: tuple[ResearchMarketMicrostructureSignalQualityRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketMicrostructureSignalQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_microstructure_signal_quality_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(row: ResearchMarketMicrostructureSignalQualityRow) -> None:
    expected_signal_count = _count_decimal(
        sum(
            1
            for value in (
                row.spread_inconsistent,
                row.depth_unbalanced,
                row.update_stale,
                row.movement_unattributed,
            )
            if value is True
        ),
    )
    if row.quality_signal_count != expected_signal_count:
        raise ValueError("quality_signal_count must match row flags")
    if row.status == PASS_STATUS and row.quality_signal_count != _ZERO:
        raise ValueError("pass rows must have no quality signals")
    if row.status in {WATCH_STATUS, BLOCK_STATUS} and row.quality_signal_count == _ZERO:
        raise ValueError("watch and block rows must have quality signals")
    if row.status == PASS_STATUS:
        expected_codes = ("microstructure_signal_quality_pass",)
    else:
        if f"microstructure_signal_quality_{row.status}" not in row.reason_codes:
            raise ValueError("status must match reason_codes")
        expected_codes = row.reason_codes
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes must match row status")


def _validate_report_consistency(
    report: ResearchMarketMicrostructureSignalQualityReport,
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
        ("spread_inconsistent_count", "spread_inconsistent"),
        ("depth_unbalanced_count", "depth_unbalanced"),
        ("update_stale_count", "update_stale"),
        ("movement_unattributed_count", "movement_unattributed"),
    ):
        if getattr(report, field_name) != _flag_total(report.rows, row_field):
            raise ValueError(f"{field_name} must match rows")
    for field_name, values in (
        (
            "max_spread_instability_score",
            (row.spread_instability_score for row in report.rows),
        ),
        (
            "max_depth_imbalance_score",
            (row.depth_imbalance_score for row in report.rows),
        ),
        ("max_update_age_seconds", (row.update_age_seconds for row in report.rows)),
        (
            "max_unattributed_movement_score",
            (row.unattributed_movement_score for row in report.rows),
        ),
    ):
        if getattr(report, field_name) != _max_decimal(values):
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Iterable[ResearchMarketMicrostructureSignalObservation],
) -> tuple[ResearchMarketMicrostructureSignalObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchMarketMicrostructureSignalObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketMicrostructureSignalObservation",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchMarketMicrostructureSignalQualityRow],
) -> tuple[ResearchMarketMicrostructureSignalQualityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketMicrostructureSignalQualityRow:
            raise ValueError(
                "rows must contain ResearchMarketMicrostructureSignalQualityRow",
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


def _validate_public_payload_semantics(payload: dict[str, Any]) -> None:
    _require_exact_public_schema("public payload", payload, _REPORT_PUBLIC_FIELDS)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("public payload.rows must be a list")
    rows = tuple(
        _row_from_public_payload(row_value, index)
        for index, row_value in enumerate(rows_value)
    )
    ResearchMarketMicrostructureSignalQualityReport(
        generated_at=_require_public_datetime_string(
            "public payload.generated_at",
            payload["generated_at"],
        ),
        config_version=payload["config_version"],
        status=payload["status"],
        observation_count=_require_public_nonnegative_decimal_string(
            "public payload.observation_count",
            payload["observation_count"],
        ),
        pass_count=_require_public_nonnegative_decimal_string(
            "public payload.pass_count",
            payload["pass_count"],
        ),
        watch_count=_require_public_nonnegative_decimal_string(
            "public payload.watch_count",
            payload["watch_count"],
        ),
        block_count=_require_public_nonnegative_decimal_string(
            "public payload.block_count",
            payload["block_count"],
        ),
        spread_inconsistent_count=_require_public_nonnegative_decimal_string(
            "public payload.spread_inconsistent_count",
            payload["spread_inconsistent_count"],
        ),
        depth_unbalanced_count=_require_public_nonnegative_decimal_string(
            "public payload.depth_unbalanced_count",
            payload["depth_unbalanced_count"],
        ),
        update_stale_count=_require_public_nonnegative_decimal_string(
            "public payload.update_stale_count",
            payload["update_stale_count"],
        ),
        movement_unattributed_count=_require_public_nonnegative_decimal_string(
            "public payload.movement_unattributed_count",
            payload["movement_unattributed_count"],
        ),
        max_spread_instability_score=_require_public_ratio_decimal_string(
            "public payload.max_spread_instability_score",
            payload["max_spread_instability_score"],
        ),
        max_depth_imbalance_score=_require_public_ratio_decimal_string(
            "public payload.max_depth_imbalance_score",
            payload["max_depth_imbalance_score"],
        ),
        max_update_age_seconds=_require_public_nonnegative_decimal_string(
            "public payload.max_update_age_seconds",
            payload["max_update_age_seconds"],
        ),
        max_unattributed_movement_score=_require_public_ratio_decimal_string(
            "public payload.max_unattributed_movement_score",
            payload["max_unattributed_movement_score"],
        ),
        rows=rows,
        reason_codes=_require_public_reason_codes(
            "public payload.reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    value: object,
    index: int,
) -> ResearchMarketMicrostructureSignalQualityRow:
    label = f"public payload.rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_exact_public_schema(label, value, _ROW_PUBLIC_FIELDS)
    return ResearchMarketMicrostructureSignalQualityRow(
        observed_at=_require_public_datetime_string(
            f"{label}.observed_at",
            value["observed_at"],
        ),
        spread_instability_score=_require_public_ratio_decimal_string(
            f"{label}.spread_instability_score",
            value["spread_instability_score"],
        ),
        depth_imbalance_score=_require_public_ratio_decimal_string(
            f"{label}.depth_imbalance_score",
            value["depth_imbalance_score"],
        ),
        update_age_seconds=_require_public_nonnegative_decimal_string(
            f"{label}.update_age_seconds",
            value["update_age_seconds"],
        ),
        unattributed_movement_score=_require_public_ratio_decimal_string(
            f"{label}.unattributed_movement_score",
            value["unattributed_movement_score"],
        ),
        quality_signal_count=_require_public_nonnegative_decimal_string(
            f"{label}.quality_signal_count",
            value["quality_signal_count"],
        ),
        spread_inconsistent=value["spread_inconsistent"],
        depth_unbalanced=value["depth_unbalanced"],
        update_stale=value["update_stale"],
        movement_unattributed=value["movement_unattributed"],
        status=value["status"],
        reason_codes=_require_public_reason_codes(
            f"{label}.reason_codes",
            value["reason_codes"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_exact_public_schema(
    label: str,
    value: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(value) != expected_fields:
        raise ValueError(f"{label} must match the exact schema")


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal string",
        ) from exc
    normalized = _require_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_nonnegative_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_public_decimal_string(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_public_ratio_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_public_decimal_string(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(value)
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use canonical reason codes")
    return normalized


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
    rows: tuple[ResearchMarketMicrostructureSignalQualityRow, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name) is True))


def _status_count(
    rows: tuple[ResearchMarketMicrostructureSignalQualityRow, ...],
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
    report: ResearchMarketMicrostructureSignalQualityReport,
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


def _require_json_ready_public_payload(
    value: object,
    path: str = "public payload",
) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if type(value) is int or isinstance(value, (float, Decimal, datetime)):
        raise ValueError(f"{path} must be JSON-ready")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} must use string JSON object keys")
            _require_json_ready_public_payload(item, f"{path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_json_ready_public_payload(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} must be JSON-ready")


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
            raise ValueError(f"unexpected mapping in {label}")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
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


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    for fragment in _UNSAFE_KEY_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public field in {path}: {key}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in _UNSAFE_VALUE_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public value for {field_name}")


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
    "ResearchMarketMicrostructureSignalObservation",
    "ResearchMarketMicrostructureSignalQualityConfig",
    "ResearchMarketMicrostructureSignalQualityReport",
    "ResearchMarketMicrostructureSignalQualityRow",
    "build_research_market_microstructure_signal_quality_report",
    "research_market_microstructure_signal_quality_report_digest",
    "research_market_microstructure_signal_quality_report_payload",
    "validate_research_market_microstructure_signal_quality_public_payload",
)
