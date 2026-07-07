from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any


DEFAULT_STRATEGY_PORTFOLIO_CORRELATED_RESOLUTION_EXPOSURE_V2_CONFIG_VERSION = (
    "strategy-portfolio-correlated-resolution-exposure-v2"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
COUNT_ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28

ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")
REASON_CODE_SEQUENCE = (
    "source_family_exposure_block",
    "cluster_exposure_block",
    "source_family_exposure_watch",
    "cluster_exposure_watch",
    "shared_resolution_source_family",
    "shared_event_cluster",
    "correlated_exposure_within_limits",
)

__all__ = (
    "DEFAULT_STRATEGY_PORTFOLIO_CORRELATED_RESOLUTION_EXPOSURE_V2_CONFIG_VERSION",
    "StrategyPortfolioCorrelatedResolutionExposureV2Config",
    "StrategyPortfolioCorrelatedResolutionExposureV2Position",
    "StrategyPortfolioCorrelatedResolutionExposureV2Row",
    "StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount",
    "StrategyPortfolioCorrelatedResolutionExposureV2Report",
    "build_strategy_portfolio_correlated_resolution_exposure_v2_report",
    "strategy_portfolio_correlated_resolution_exposure_v2_public_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class StrategyPortfolioCorrelatedResolutionExposureV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_STRATEGY_PORTFOLIO_CORRELATED_RESOLUTION_EXPOSURE_V2_CONFIG_VERSION
    )
    cluster_watch_exposure_usdc: Decimal = Decimal("100.000000")
    cluster_block_exposure_usdc: Decimal = Decimal("150.000000")
    source_family_watch_exposure_usdc: Decimal = Decimal("120.000000")
    source_family_block_exposure_usdc: Decimal = Decimal("180.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyPortfolioCorrelatedResolutionExposureV2Config,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PORTFOLIO_CORRELATED_RESOLUTION_EXPOSURE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "cluster_watch_exposure_usdc",
            "cluster_block_exposure_usdc",
            "source_family_watch_exposure_usdc",
            "source_family_block_exposure_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.cluster_watch_exposure_usdc > self.cluster_block_exposure_usdc:
            raise ValueError("cluster watch threshold must be <= block threshold")
        if (
            self.source_family_watch_exposure_usdc
            > self.source_family_block_exposure_usdc
        ):
            raise ValueError("source family watch threshold must be <= block threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _config_public_payload(self))


@dataclass(frozen=True)
class StrategyPortfolioCorrelatedResolutionExposureV2Position(_FinalPublicDataclass):
    position_id: str
    market_id: str
    event_slug: str
    category: str
    cluster_id: str
    resolution_source_family: str
    notional_usdc: Decimal
    max_loss_usdc: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyPortfolioCorrelatedResolutionExposureV2Position,
            "position",
        )
        for field_name in (
            "position_id",
            "market_id",
            "event_slug",
            "category",
            "cluster_id",
            "resolution_source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("notional_usdc", "max_loss_usdc"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("position", self)
        _reject_unsafe_public_payload("position", _position_public_payload(self))


@dataclass(frozen=True)
class StrategyPortfolioCorrelatedResolutionExposureV2Row(_FinalPublicDataclass):
    position_id: str
    market_id: str
    event_slug: str
    category: str
    cluster_id: str
    resolution_source_family: str
    notional_usdc: Decimal
    max_loss_usdc: Decimal
    cluster_exposure_usdc: Decimal
    source_family_exposure_usdc: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyPortfolioCorrelatedResolutionExposureV2Row,
            "row",
        )
        for field_name in (
            "position_id",
            "market_id",
            "event_slug",
            "category",
            "cluster_id",
            "resolution_source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "notional_usdc",
            "max_loss_usdc",
            "cluster_exposure_usdc",
            "source_family_exposure_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _row_public_payload_values(self))
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
class StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(
            "reason_code_count",
            _reason_code_count_public_payload(self),
        )


@dataclass(frozen=True)
class StrategyPortfolioCorrelatedResolutionExposureV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    cluster_watch_exposure_usdc: Decimal
    cluster_block_exposure_usdc: Decimal
    source_family_watch_exposure_usdc: Decimal
    source_family_block_exposure_usdc: Decimal
    position_count: Decimal
    cluster_count: Decimal
    source_family_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_cluster_exposure_usdc: Decimal
    max_source_family_exposure_usdc: Decimal
    total_max_loss_usdc: Decimal
    report_status: str
    rows: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Row, ...]
    reason_code_counts: tuple[
        StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyPortfolioCorrelatedResolutionExposureV2Report,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PORTFOLIO_CORRELATED_RESOLUTION_EXPOSURE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "cluster_watch_exposure_usdc",
            "cluster_block_exposure_usdc",
            "source_family_watch_exposure_usdc",
            "source_family_block_exposure_usdc",
            "max_cluster_exposure_usdc",
            "max_source_family_exposure_usdc",
            "total_max_loss_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "position_count",
            "cluster_count",
            "source_family_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report_derived_fields(self)
        _reject_unsafe_public_payload("report", _report_public_payload_values(self))
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


def build_strategy_portfolio_correlated_resolution_exposure_v2_report(
    positions: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Position, ...]
    | list[StrategyPortfolioCorrelatedResolutionExposureV2Position],
    *,
    config: StrategyPortfolioCorrelatedResolutionExposureV2Config | None = None,
    generated_at: datetime,
) -> StrategyPortfolioCorrelatedResolutionExposureV2Report:
    """Build a Phase 1 read-only correlated exposure report from paper positions."""

    if config is None:
        config = StrategyPortfolioCorrelatedResolutionExposureV2Config()
    _require_exact_type(
        config,
        StrategyPortfolioCorrelatedResolutionExposureV2Config,
        "config",
    )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_positions = _normalize_positions(positions)
    cluster_exposures = _group_exposures(normalized_positions, "cluster_id")
    source_family_exposures = _group_exposures(
        normalized_positions,
        "resolution_source_family",
    )
    cluster_position_counts = _group_counts(normalized_positions, "cluster_id")
    source_family_position_counts = _group_counts(
        normalized_positions,
        "resolution_source_family",
    )
    rows = tuple(
        _row_for_position(
            position,
            config=config,
            cluster_exposure=cluster_exposures[position.cluster_id],
            source_family_exposure=source_family_exposures[
                position.resolution_source_family
            ],
            cluster_position_count=cluster_position_counts[position.cluster_id],
            source_family_position_count=source_family_position_counts[
                position.resolution_source_family
            ],
        )
        for position in normalized_positions
    )
    sorted_rows = tuple(
        replace(row, derived_validation_digest="")
        for row in sorted(rows, key=_row_sort_key)
    )
    reason_code_counts = _reason_code_counts(sorted_rows)
    return StrategyPortfolioCorrelatedResolutionExposureV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        cluster_watch_exposure_usdc=config.cluster_watch_exposure_usdc,
        cluster_block_exposure_usdc=config.cluster_block_exposure_usdc,
        source_family_watch_exposure_usdc=config.source_family_watch_exposure_usdc,
        source_family_block_exposure_usdc=config.source_family_block_exposure_usdc,
        position_count=_count_decimal(len(sorted_rows)),
        cluster_count=_count_decimal(len(cluster_exposures)),
        source_family_count=_count_decimal(len(source_family_exposures)),
        pass_count=_count_decimal(sum(1 for row in sorted_rows if row.status == "pass")),
        watch_count=_count_decimal(
            sum(1 for row in sorted_rows if row.status == "watch"),
        ),
        block_count=_count_decimal(
            sum(1 for row in sorted_rows if row.status == "block"),
        ),
        max_cluster_exposure_usdc=_max_decimal(
            tuple(row.cluster_exposure_usdc for row in sorted_rows),
        ),
        max_source_family_exposure_usdc=_max_decimal(
            tuple(row.source_family_exposure_usdc for row in sorted_rows),
        ),
        total_max_loss_usdc=_sum_decimal(
            tuple(position.max_loss_usdc for position in normalized_positions),
        ),
        report_status=_report_status(sorted_rows),
        rows=sorted_rows,
        reason_code_counts=reason_code_counts,
    )


def strategy_portfolio_correlated_resolution_exposure_v2_public_payload(
    report: StrategyPortfolioCorrelatedResolutionExposureV2Report,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        StrategyPortfolioCorrelatedResolutionExposureV2Report,
        "report",
    )
    _require_hard_flags("report", report)
    _validate_report_derived_validation_digest(report)
    payload = _report_public_payload_values(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return _json_ready(payload)


def _row_for_position(
    position: StrategyPortfolioCorrelatedResolutionExposureV2Position,
    *,
    config: StrategyPortfolioCorrelatedResolutionExposureV2Config,
    cluster_exposure: Decimal,
    source_family_exposure: Decimal,
    cluster_position_count: Decimal,
    source_family_position_count: Decimal,
) -> StrategyPortfolioCorrelatedResolutionExposureV2Row:
    status = _status_for_exposures(
        cluster_exposure=cluster_exposure,
        source_family_exposure=source_family_exposure,
        config=config,
    )
    return StrategyPortfolioCorrelatedResolutionExposureV2Row(
        position_id=position.position_id,
        market_id=position.market_id,
        event_slug=position.event_slug,
        category=position.category,
        cluster_id=position.cluster_id,
        resolution_source_family=position.resolution_source_family,
        notional_usdc=position.notional_usdc,
        max_loss_usdc=position.max_loss_usdc,
        cluster_exposure_usdc=cluster_exposure,
        source_family_exposure_usdc=source_family_exposure,
        status=status,
        reason_codes=_row_reason_codes(
            cluster_exposure=cluster_exposure,
            source_family_exposure=source_family_exposure,
            cluster_position_count=cluster_position_count,
            source_family_position_count=source_family_position_count,
            config=config,
        ),
    )


def _status_for_exposures(
    *,
    cluster_exposure: Decimal,
    source_family_exposure: Decimal,
    config: StrategyPortfolioCorrelatedResolutionExposureV2Config,
) -> str:
    if (
        cluster_exposure >= config.cluster_block_exposure_usdc
        or source_family_exposure >= config.source_family_block_exposure_usdc
    ):
        return "block"
    if (
        cluster_exposure >= config.cluster_watch_exposure_usdc
        or source_family_exposure >= config.source_family_watch_exposure_usdc
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    cluster_exposure: Decimal,
    source_family_exposure: Decimal,
    cluster_position_count: Decimal,
    source_family_position_count: Decimal,
    config: StrategyPortfolioCorrelatedResolutionExposureV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_family_exposure >= config.source_family_block_exposure_usdc:
        reason_codes.append("source_family_exposure_block")
    elif source_family_exposure >= config.source_family_watch_exposure_usdc:
        reason_codes.append("source_family_exposure_watch")
    if cluster_exposure >= config.cluster_block_exposure_usdc:
        reason_codes.append("cluster_exposure_block")
    elif cluster_exposure >= config.cluster_watch_exposure_usdc:
        reason_codes.append("cluster_exposure_watch")
    if source_family_position_count > COUNT_ONE:
        reason_codes.append("shared_resolution_source_family")
    if cluster_position_count > COUNT_ONE:
        reason_codes.append("shared_event_cluster")
    if not reason_codes:
        reason_codes.append("correlated_exposure_within_limits")
    return tuple(reason_codes)


def _normalize_positions(
    positions: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Position, ...]
    | list[StrategyPortfolioCorrelatedResolutionExposureV2Position],
) -> tuple[StrategyPortfolioCorrelatedResolutionExposureV2Position, ...]:
    if type(positions) not in (tuple, list):
        raise ValueError("positions must be a tuple or list")
    normalized: list[StrategyPortfolioCorrelatedResolutionExposureV2Position] = []
    position_ids: set[str] = set()
    market_ids: set[str] = set()
    for position in positions:
        _require_exact_type(
            position,
            StrategyPortfolioCorrelatedResolutionExposureV2Position,
            "position",
        )
        if position.position_id in position_ids:
            raise ValueError("position_id values must be unique")
        if position.market_id in market_ids:
            raise ValueError("market_id values must be unique")
        position_ids.add(position.position_id)
        market_ids.add(position.market_id)
        normalized.append(position)
    return tuple(normalized)


def _group_exposures(
    positions: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Position, ...],
    field_name: str,
) -> dict[str, Decimal]:
    exposures: dict[str, Decimal] = {}
    for position in positions:
        key = getattr(position, field_name)
        exposures[key] = _sum_decimal(
            (
                exposures.get(key, ZERO),
                position.notional_usdc,
            ),
        )
    return exposures


def _group_counts(
    positions: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Position, ...],
    field_name: str,
) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for position in positions:
        key = getattr(position, field_name)
        counts[key] = _sum_decimal((counts.get(key, ZERO), COUNT_ONE))
    return counts


def _row_sort_key(
    row: StrategyPortfolioCorrelatedResolutionExposureV2Row,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -max(row.cluster_exposure_usdc, row.source_family_exposure_usdc),
        -row.source_family_exposure_usdc,
        -row.notional_usdc,
        row.position_id,
        row.market_id,
    )


def _reason_code_counts(
    rows: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Row, ...],
) -> tuple[StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _sum_decimal((counts.get(reason_code, ZERO), COUNT_ONE))
    return tuple(
        StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _report_status(
    rows: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_rows(
    rows: tuple[StrategyPortfolioCorrelatedResolutionExposureV2Row, ...],
) -> tuple[StrategyPortfolioCorrelatedResolutionExposureV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, StrategyPortfolioCorrelatedResolutionExposureV2Row, "row")
        _validate_row_derived_validation_digest(row)
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount,
        ...,
    ],
) -> tuple[StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in reason_code_counts:
        _require_exact_type(
            item,
            StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount,
            "reason_code_count",
        )
        if item.reason_code in seen:
            raise ValueError("reason_code_count reason_code values must be unique")
        seen.add(item.reason_code)
    return reason_code_counts


def _validate_report_derived_fields(
    report: StrategyPortfolioCorrelatedResolutionExposureV2Report,
) -> None:
    if report.position_count != _count_decimal(len(report.rows)):
        raise ValueError("position_count must equal row count")
    if report.cluster_count != _count_decimal(len({row.cluster_id for row in report.rows})):
        raise ValueError("cluster_count must equal unique cluster count")
    if report.source_family_count != _count_decimal(
        len({row.resolution_source_family for row in report.rows}),
    ):
        raise ValueError("source_family_count must equal unique source family count")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "pass"),
    ):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must equal block rows")
    if report.max_cluster_exposure_usdc != _max_decimal(
        tuple(row.cluster_exposure_usdc for row in report.rows),
    ):
        raise ValueError("max_cluster_exposure_usdc must equal max row cluster exposure")
    if report.max_source_family_exposure_usdc != _max_decimal(
        tuple(row.source_family_exposure_usdc for row in report.rows),
    ):
        raise ValueError(
            "max_source_family_exposure_usdc must equal max row source family exposure",
        )
    if report.total_max_loss_usdc != _sum_decimal(
        tuple(row.max_loss_usdc for row in report.rows),
    ):
        raise ValueError("total_max_loss_usdc must equal row max loss sum")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match row statuses")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match row reason codes")


def _validate_row_derived_validation_digest(
    row: StrategyPortfolioCorrelatedResolutionExposureV2Row,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _validate_report_derived_validation_digest(
    report: StrategyPortfolioCorrelatedResolutionExposureV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _row_derived_validation_digest(
    row: StrategyPortfolioCorrelatedResolutionExposureV2Row,
) -> str:
    return _digest(_row_public_payload_values(row))


def _report_derived_validation_digest(
    report: StrategyPortfolioCorrelatedResolutionExposureV2Report,
) -> str:
    return _digest(_report_public_payload_values(report))


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _config_public_payload(
    config: StrategyPortfolioCorrelatedResolutionExposureV2Config,
) -> dict[str, Any]:
    return {
        "config_version": config.config_version,
        "cluster_watch_exposure_usdc": _decimal_payload(
            config.cluster_watch_exposure_usdc,
        ),
        "cluster_block_exposure_usdc": _decimal_payload(
            config.cluster_block_exposure_usdc,
        ),
        "source_family_watch_exposure_usdc": _decimal_payload(
            config.source_family_watch_exposure_usdc,
        ),
        "source_family_block_exposure_usdc": _decimal_payload(
            config.source_family_block_exposure_usdc,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _position_public_payload(
    position: StrategyPortfolioCorrelatedResolutionExposureV2Position,
) -> dict[str, Any]:
    return {
        "position_id": position.position_id,
        "market_id": position.market_id,
        "event_slug": position.event_slug,
        "category": position.category,
        "cluster_id": position.cluster_id,
        "resolution_source_family": position.resolution_source_family,
        "notional_usdc": _decimal_payload(position.notional_usdc),
        "max_loss_usdc": _decimal_payload(position.max_loss_usdc),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload_values(
    row: StrategyPortfolioCorrelatedResolutionExposureV2Row,
) -> dict[str, Any]:
    return {
        "position_id": row.position_id,
        "market_id": row.market_id,
        "event_slug": row.event_slug,
        "category": row.category,
        "cluster_id": row.cluster_id,
        "resolution_source_family": row.resolution_source_family,
        "notional_usdc": _decimal_payload(row.notional_usdc),
        "max_loss_usdc": _decimal_payload(row.max_loss_usdc),
        "cluster_exposure_usdc": _decimal_payload(row.cluster_exposure_usdc),
        "source_family_exposure_usdc": _decimal_payload(
            row.source_family_exposure_usdc,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(
    row: StrategyPortfolioCorrelatedResolutionExposureV2Row,
) -> dict[str, Any]:
    payload = _row_public_payload_values(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _reason_code_count_public_payload(
    item: StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_public_payload_values(
    report: StrategyPortfolioCorrelatedResolutionExposureV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "cluster_watch_exposure_usdc": _decimal_payload(
            report.cluster_watch_exposure_usdc,
        ),
        "cluster_block_exposure_usdc": _decimal_payload(
            report.cluster_block_exposure_usdc,
        ),
        "source_family_watch_exposure_usdc": _decimal_payload(
            report.source_family_watch_exposure_usdc,
        ),
        "source_family_block_exposure_usdc": _decimal_payload(
            report.source_family_block_exposure_usdc,
        ),
        "position_count": _decimal_payload(report.position_count),
        "cluster_count": _decimal_payload(report.cluster_count),
        "source_family_count": _decimal_payload(report.source_family_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "max_cluster_exposure_usdc": _decimal_payload(
            report.max_cluster_exposure_usdc,
        ),
        "max_source_family_exposure_usdc": _decimal_payload(
            report.max_source_family_exposure_usdc,
        ),
        "total_max_loss_usdc": _decimal_payload(report.total_max_loss_usdc),
        "report_status": report.report_status,
        "rows": [_row_public_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_public_payload(item)
            for item in report.reason_code_counts
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reject_unsafe_public_payload(field_name: str, value: dict[str, Any]) -> None:
    try:
        _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} payload {exc}") from exc


def _json_ready(value: Any) -> Any:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is int:
        raise ValueError("int values are not safe JSON payload values")
    if type(value) is float:
        raise ValueError("float values are not safe JSON payload values")
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError(f"{type(value).__name__} values are not safe JSON payload values")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} values must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(DECIMAL_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(str(value)).quantize(DECIMAL_QUANT)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        for value in values:
            total += value
        return total.quantize(DECIMAL_QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(DECIMAL_QUANT)


def _decimal_payload(value: Decimal) -> str:
    return f"{_normalize_decimal('decimal_payload', value):.6f}"


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    return value
