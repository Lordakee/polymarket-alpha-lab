"""Pure report-only research data source quality matrix.

The module accepts caller-supplied, already-redacted source quality observations
and returns a deterministic local matrix. It has no side effects, performs no
retrieval, and never stores output.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_DATA_SOURCE_QUALITY_MATRIX_CONFIG_VERSION = (
    "research-data-source-quality-matrix-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

DATA_SOURCE_FAMILIES = (
    "official",
    "primary",
    "independent",
    "data_vendor",
    "research",
    "community",
)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

LOW_RELIABILITY_BLOCK_REASON = "low_reliability_block"
LOW_AUDIT_TRAIL_BLOCK_REASON = "low_audit_trail_block"
STALE_REFRESH_BLOCK_REASON = "stale_refresh_block"
COVERAGE_GAP_BLOCK_REASON = "coverage_gap_block"
LOW_COMPOSITE_BLOCK_REASON = "low_composite_block"
LOW_RELIABILITY_WATCH_REASON = "low_reliability_watch"
LOW_AUDIT_TRAIL_WATCH_REASON = "low_audit_trail_watch"
STALE_REFRESH_WATCH_REASON = "stale_refresh_watch"
COVERAGE_GAP_WATCH_REASON = "coverage_gap_watch"
LOW_COMPOSITE_WATCH_REASON = "low_composite_watch"
PASS_REASON = "data_source_quality_matrix_pass"
NO_INPUTS_REASON = "data_source_quality_matrix_no_inputs"

ROW_REASON_CODES = (
    LOW_RELIABILITY_BLOCK_REASON,
    LOW_AUDIT_TRAIL_BLOCK_REASON,
    STALE_REFRESH_BLOCK_REASON,
    COVERAGE_GAP_BLOCK_REASON,
    LOW_COMPOSITE_BLOCK_REASON,
    LOW_RELIABILITY_WATCH_REASON,
    LOW_AUDIT_TRAIL_WATCH_REASON,
    STALE_REFRESH_WATCH_REASON,
    COVERAGE_GAP_WATCH_REASON,
    LOW_COMPOSITE_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    LOW_RELIABILITY_BLOCK_REASON,
    LOW_AUDIT_TRAIL_BLOCK_REASON,
    STALE_REFRESH_BLOCK_REASON,
    COVERAGE_GAP_BLOCK_REASON,
    LOW_RELIABILITY_WATCH_REASON,
    LOW_AUDIT_TRAIL_WATCH_REASON,
    STALE_REFRESH_WATCH_REASON,
    COVERAGE_GAP_WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
_DIGEST_FIELD = "derived_validation_digest"
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "candidate id",
        "raw candidate",
        "raw-candidate",
        "market_id",
        "market id",
        "market_slug",
        "market slug",
        "market_url",
        "question",
        "source_ref",
        "source ref",
        "source_url",
        "source url",
        "source_text",
        "source text",
        "://",
        "www.",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ),
)


@dataclass(frozen=True)
class ResearchDataSourceQualityMatrixConfig:
    config_version: str = DEFAULT_RESEARCH_DATA_SOURCE_QUALITY_MATRIX_CONFIG_VERSION
    min_pass_quality_score: Decimal = Decimal("0.750000")
    min_watch_quality_score: Decimal = Decimal("0.500000")
    min_pass_reliability_score: Decimal = Decimal("0.750000")
    min_watch_reliability_score: Decimal = Decimal("0.500000")
    min_pass_audit_trail_score: Decimal = Decimal("0.750000")
    min_watch_audit_trail_score: Decimal = Decimal("0.500000")
    max_pass_refresh_frequency_minutes: Decimal = Decimal("1440.000000")
    max_watch_refresh_frequency_minutes: Decimal = Decimal("10080.000000")
    max_pass_coverage_gap_ratio: Decimal = Decimal("0.100000")
    max_watch_coverage_gap_ratio: Decimal = Decimal("0.350000")
    reliability_weight: Decimal = Decimal("0.351372")
    audit_trail_weight: Decimal = Decimal("0.244522")
    refresh_frequency_weight: Decimal = Decimal("0.268915")
    coverage_gap_weight: Decimal = Decimal("0.135191")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDataSourceQualityMatrixConfig:
            raise TypeError(
                "ResearchDataSourceQualityMatrixConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDataSourceQualityMatrixConfig:
            raise ValueError(
                "config must be exactly ResearchDataSourceQualityMatrixConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DATA_SOURCE_QUALITY_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_quality_score",
            "min_watch_quality_score",
            "min_pass_reliability_score",
            "min_watch_reliability_score",
            "min_pass_audit_trail_score",
            "min_watch_audit_trail_score",
            "max_pass_coverage_gap_ratio",
            "max_watch_coverage_gap_ratio",
            "reliability_weight",
            "audit_trail_weight",
            "refresh_frequency_weight",
            "coverage_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_refresh_frequency_minutes",
            "max_watch_refresh_frequency_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDataSourceQualityObservation:
    data_source_family: str
    reliability_score: Decimal
    audit_trail_score: Decimal
    refresh_frequency_minutes: Decimal
    coverage_gap_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDataSourceQualityObservation:
            raise TypeError(
                "ResearchDataSourceQualityObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDataSourceQualityObservation:
            raise ValueError(
                "observation must be exactly ResearchDataSourceQualityObservation",
            )
        object.__setattr__(
            self,
            "data_source_family",
            _require_member("data_source_family", self.data_source_family, DATA_SOURCE_FAMILIES),
        )
        for field_name in (
            "reliability_score",
            "audit_trail_score",
            "coverage_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "refresh_frequency_minutes",
            _require_positive_decimal(
                "refresh_frequency_minutes",
                self.refresh_frequency_minutes,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchDataSourceQualityMatrixRow:
    matrix_key: str
    data_source_family: str
    reliability_score: Decimal
    audit_trail_score: Decimal
    refresh_frequency_minutes: Decimal
    coverage_gap_ratio: Decimal
    refresh_frequency_score: Decimal
    coverage_score: Decimal
    composite_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDataSourceQualityMatrixRow:
            raise TypeError(
                "ResearchDataSourceQualityMatrixRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDataSourceQualityMatrixRow:
            raise ValueError("row must be exactly ResearchDataSourceQualityMatrixRow")
        _require_public_identifier("matrix_key", self.matrix_key)
        object.__setattr__(
            self,
            "data_source_family",
            _require_member("data_source_family", self.data_source_family, DATA_SOURCE_FAMILIES),
        )
        for field_name in (
            "reliability_score",
            "audit_trail_score",
            "coverage_gap_ratio",
            "refresh_frequency_score",
            "coverage_score",
            "composite_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "refresh_frequency_minutes",
            _require_positive_decimal(
                "refresh_frequency_minutes",
                self.refresh_frequency_minutes,
            ),
        )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDataSourceQualityMatrixReport:
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_composite_quality_score: Decimal
    min_composite_quality_score: Decimal
    max_refresh_frequency_minutes: Decimal
    max_coverage_gap_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchDataSourceQualityMatrixRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDataSourceQualityMatrixReport:
            raise TypeError(
                "ResearchDataSourceQualityMatrixReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDataSourceQualityMatrixReport:
            raise ValueError("report must be exactly ResearchDataSourceQualityMatrixReport")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DATA_SOURCE_QUALITY_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_composite_quality_score",
            "min_composite_quality_score",
            "max_coverage_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_refresh_frequency_minutes",
            _require_nonnegative_decimal(
                "max_refresh_frequency_minutes",
                self.max_refresh_frequency_minutes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest mismatch")
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_data_source_quality_matrix_payload(self)


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


def build_research_data_source_quality_matrix(
    observations: Sequence[ResearchDataSourceQualityObservation],
    *,
    config: ResearchDataSourceQualityMatrixConfig,
) -> ResearchDataSourceQualityMatrixReport:
    """Build a deterministic, local, report-only source quality matrix."""

    if type(config) is not ResearchDataSourceQualityMatrixConfig:
        raise ValueError("config must be a ResearchDataSourceQualityMatrixConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    items = _normalize_observations(observations)
    preliminary_rows = tuple(_row_without_key(item, config) for item in items)
    sorted_rows = tuple(sorted(preliminary_rows, key=_preliminary_row_sort_key))
    rows = tuple(
        ResearchDataSourceQualityMatrixRow(
            matrix_key=f"redacted-data-source-{index:03d}",
            data_source_family=row["data_source_family"],
            reliability_score=row["reliability_score"],
            audit_trail_score=row["audit_trail_score"],
            refresh_frequency_minutes=row["refresh_frequency_minutes"],
            coverage_gap_ratio=row["coverage_gap_ratio"],
            refresh_frequency_score=row["refresh_frequency_score"],
            coverage_score=row["coverage_score"],
            composite_quality_score=row["composite_quality_score"],
            status=row["status"],
            reason_codes=row["reason_codes"],
        )
        for index, row in enumerate(sorted_rows, start=1)
    )
    return ResearchDataSourceQualityMatrixReport(
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_composite_quality_score=_average_score(
            tuple(row.composite_quality_score for row in rows),
        ),
        min_composite_quality_score=min(
            (row.composite_quality_score for row in rows),
            default=_ZERO,
        ),
        max_refresh_frequency_minutes=max(
            (row.refresh_frequency_minutes for row in rows),
            default=_ZERO,
        ),
        max_coverage_gap_ratio=max(
            (row.coverage_gap_ratio for row in rows),
            default=_ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_data_source_quality_matrix_payload(
    value: ResearchDataSourceQualityMatrixReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchDataSourceQualityMatrixReport:
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchDataSourceQualityMatrixReport or dict")
    _validate_public_payload(payload)
    return payload


def _row_without_key(
    item: ResearchDataSourceQualityObservation,
    config: ResearchDataSourceQualityMatrixConfig,
) -> dict[str, Any]:
    refresh_frequency_score = _clamp_ratio(
        _ONE - (item.refresh_frequency_minutes / config.max_watch_refresh_frequency_minutes),
    )
    coverage_score = _clamp_ratio(_ONE - item.coverage_gap_ratio)
    composite_quality_score = _clamp_ratio(
        item.reliability_score * config.reliability_weight
        + item.audit_trail_score * config.audit_trail_weight
        + refresh_frequency_score * config.refresh_frequency_weight
        + coverage_score * config.coverage_gap_weight,
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        composite_quality_score=composite_quality_score,
    )
    return {
        "data_source_family": item.data_source_family,
        "reliability_score": item.reliability_score,
        "audit_trail_score": item.audit_trail_score,
        "refresh_frequency_minutes": item.refresh_frequency_minutes,
        "coverage_gap_ratio": item.coverage_gap_ratio,
        "refresh_frequency_score": refresh_frequency_score,
        "coverage_score": coverage_score,
        "composite_quality_score": composite_quality_score,
        "status": _row_status(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_reason_codes(
    item: ResearchDataSourceQualityObservation,
    *,
    config: ResearchDataSourceQualityMatrixConfig,
    composite_quality_score: Decimal,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if item.reliability_score < config.min_watch_reliability_score:
        block_reasons.append(LOW_RELIABILITY_BLOCK_REASON)
    elif item.reliability_score < config.min_pass_reliability_score:
        watch_reasons.append(LOW_RELIABILITY_WATCH_REASON)
    if item.audit_trail_score < config.min_watch_audit_trail_score:
        block_reasons.append(LOW_AUDIT_TRAIL_BLOCK_REASON)
    elif item.audit_trail_score < config.min_pass_audit_trail_score:
        watch_reasons.append(LOW_AUDIT_TRAIL_WATCH_REASON)
    if item.refresh_frequency_minutes > config.max_watch_refresh_frequency_minutes:
        block_reasons.append(STALE_REFRESH_BLOCK_REASON)
    elif item.refresh_frequency_minutes > config.max_pass_refresh_frequency_minutes:
        watch_reasons.append(STALE_REFRESH_WATCH_REASON)
    if item.coverage_gap_ratio > config.max_watch_coverage_gap_ratio:
        block_reasons.append(COVERAGE_GAP_BLOCK_REASON)
    elif item.coverage_gap_ratio > config.max_pass_coverage_gap_ratio:
        watch_reasons.append(COVERAGE_GAP_WATCH_REASON)
    reason_codes = list(block_reasons)
    if composite_quality_score < config.min_watch_quality_score:
        reason_codes.append(LOW_COMPOSITE_BLOCK_REASON)
    elif composite_quality_score < config.min_pass_quality_score:
        reason_codes.append(LOW_COMPOSITE_WATCH_REASON)
    if not block_reasons:
        reason_codes.extend(watch_reasons)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes),
        ROW_REASON_CODES,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDataSourceQualityMatrixRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "block"


def _report_reason_codes(
    rows: tuple[ResearchDataSourceQualityMatrixRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in REPORT_REASON_CODES
    )
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in present)


def _status_count(
    rows: tuple[ResearchDataSourceQualityMatrixRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _count_decimal(len(values)))


def _normalize_observations(
    value: Sequence[ResearchDataSourceQualityObservation],
) -> tuple[ResearchDataSourceQualityObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    for item in observations:
        if type(item) is not ResearchDataSourceQualityObservation:
            raise ValueError(
                "observations must contain ResearchDataSourceQualityObservation items",
            )
        _require_hard_flags("observation", item)
        _reject_unsafe_public_payload("observation", item)
    return observations


def _normalize_rows(
    value: Sequence[ResearchDataSourceQualityMatrixRow],
) -> tuple[ResearchDataSourceQualityMatrixRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDataSourceQualityMatrixRow:
            raise ValueError("rows must contain ResearchDataSourceQualityMatrixRow items")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.matrix_key in seen:
            raise ValueError("rows must use unique matrix_key values")
        seen.add(row.matrix_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    return rows


def _preliminary_row_sort_key(row: dict[str, Any]) -> tuple[object, ...]:
    return (
        STATUS_RANK[row["status"]],
        row["data_source_family"],
        row["reliability_score"],
        row["audit_trail_score"],
        row["refresh_frequency_minutes"],
        row["coverage_gap_ratio"],
        row["composite_quality_score"],
    )


def _row_sort_key(row: ResearchDataSourceQualityMatrixRow) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        row.data_source_family,
        row.reliability_score,
        row.audit_trail_score,
        row.refresh_frequency_minutes,
        row.coverage_gap_ratio,
        row.composite_quality_score,
        row.matrix_key,
    )


def _validate_config(config: ResearchDataSourceQualityMatrixConfig) -> None:
    if config.min_pass_quality_score <= config.min_watch_quality_score:
        raise ValueError("min_pass_quality_score must exceed min_watch_quality_score")
    if config.min_pass_reliability_score <= config.min_watch_reliability_score:
        raise ValueError("min_pass_reliability_score must exceed min_watch_reliability_score")
    if config.min_pass_audit_trail_score <= config.min_watch_audit_trail_score:
        raise ValueError("min_pass_audit_trail_score must exceed min_watch_audit_trail_score")
    if config.max_watch_refresh_frequency_minutes <= config.max_pass_refresh_frequency_minutes:
        raise ValueError(
            "max_watch_refresh_frequency_minutes must exceed "
            "max_pass_refresh_frequency_minutes",
        )
    if config.max_pass_coverage_gap_ratio >= config.max_watch_coverage_gap_ratio:
        raise ValueError("max_pass_coverage_gap_ratio must be below watch gap ratio")
    if (
        config.reliability_weight
        + config.audit_trail_weight
        + config.refresh_frequency_weight
        + config.coverage_gap_weight
        != _ONE
    ):
        raise ValueError("matrix weights must sum to one")


def _validate_row(row: ResearchDataSourceQualityMatrixRow) -> None:
    if row.coverage_score != _clamp_ratio(_ONE - row.coverage_gap_ratio):
        raise ValueError("coverage_score must equal one minus coverage_gap_ratio")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")


def _validate_report(report: ResearchDataSourceQualityMatrixReport) -> None:
    rows = report.rows
    if report.observation_count != _count_decimal(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_composite_quality_score != _average_score(
        tuple(row.composite_quality_score for row in rows),
    ):
        raise ValueError("average_composite_quality_score must match rows")
    if report.min_composite_quality_score != min(
        (row.composite_quality_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_composite_quality_score must match rows")
    if report.max_refresh_frequency_minutes != max(
        (row.refresh_frequency_minutes for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_refresh_frequency_minutes must match rows")
    if report.max_coverage_gap_ratio != max(
        (row.coverage_gap_ratio for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_coverage_gap_ratio must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a list or tuple")
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for item in values:
        if type(item) is not str or item not in allowed_values:
            raise ValueError(f"{field_name} must contain known reason codes")
    ordered = tuple(item for item in allowed_values if item in values)
    if values != ordered:
        raise ValueError(f"{field_name} must use canonical ordering")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_EVEN
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    report: ResearchDataSourceQualityMatrixReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "status": report.status,
        "observation_count": _json_ready(report.observation_count),
        "pass_count": _json_ready(report.pass_count),
        "watch_count": _json_ready(report.watch_count),
        "block_count": _json_ready(report.block_count),
        "average_composite_quality_score": _json_ready(
            report.average_composite_quality_score,
        ),
        "min_composite_quality_score": _json_ready(report.min_composite_quality_score),
        "max_refresh_frequency_minutes": _json_ready(
            report.max_refresh_frequency_minutes,
        ),
        "max_coverage_gap_ratio": _json_ready(report.max_coverage_gap_ratio),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchDataSourceQualityMatrixRow) -> dict[str, object]:
    return {
        "matrix_key": row.matrix_key,
        "data_source_family": row.data_source_family,
        "reliability_score": _json_ready(row.reliability_score),
        "audit_trail_score": _json_ready(row.audit_trail_score),
        "refresh_frequency_minutes": _json_ready(row.refresh_frequency_minutes),
        "coverage_gap_ratio": _json_ready(row.coverage_gap_ratio),
        "refresh_frequency_score": _json_ready(row.refresh_frequency_score),
        "coverage_score": _json_ready(row.coverage_score),
        "composite_quality_score": _json_ready(row.composite_quality_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_payload(report: ResearchDataSourceQualityMatrixReport) -> dict[str, object]:
    payload = _report_payload_without_digest(report)
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: ResearchDataSourceQualityMatrixReport) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _validate_public_payload(payload: dict[str, object]) -> None:
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_public_numeric_values(payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    digest_value = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest_value)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    if digest_value != _digest_payload(payload_without_digest):
        raise ValueError("derived_validation_digest mismatch")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchDataSourceQualityMatrixReport:
        return _report_payload(value)
    if type(value) is ResearchDataSourceQualityMatrixRow:
        return _row_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, Decimal) or isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchDataSourceQualityMatrixConfig,
            ResearchDataSourceQualityObservation,
            ResearchDataSourceQualityMatrixRow,
            ResearchDataSourceQualityMatrixReport,
            _PayloadFlags,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{key} has unsafe public field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_DATA_SOURCE_QUALITY_MATRIX_CONFIG_VERSION",
    "ResearchDataSourceQualityMatrixConfig",
    "ResearchDataSourceQualityObservation",
    "ResearchDataSourceQualityMatrixRow",
    "ResearchDataSourceQualityMatrixReport",
    "build_research_data_source_quality_matrix",
    "research_data_source_quality_matrix_payload",
)
