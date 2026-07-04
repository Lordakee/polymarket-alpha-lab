"""Pure Phase 1 macro jobs-data revision cluster risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MACRO_JOBS_REVISION_CLUSTER_DIGEST_CONFIG_VERSION = (
    "market-research-macro-jobs-revision-cluster-digest-v0"
)

REVISION_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "macro_jobs_revision_cluster_high_abs_revision",
    "macro_jobs_revision_cluster_inline",
    "macro_jobs_revision_cluster_watch_abs_revision",
    "macro_jobs_revision_cluster_window",
    "macro_jobs_revision_direction_flip",
    "macro_jobs_revision_material_surprise",
)
REPORT_REASON_CODES = (
    "macro_jobs_revision_cluster_high_abs_revision_present",
    "macro_jobs_revision_clustered_revisions_present",
    "macro_jobs_revision_material_surprise_overlap",
    "macro_jobs_revision_direction_flip_present",
    "macro_jobs_revision_cluster_digest_clear",
    "macro_jobs_revision_cluster_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
CLUSTER_RISK_SCORE = Decimal("0.750000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MACRO_JOBS_REVISION_CLUSTER_DIGEST_CONFIG_VERSION",
    "MacroJobsRevisionClusterDigestConfig",
    "MacroJobsRevisionClusterObservation",
    "MacroJobsRevisionClusterDigestRow",
    "MacroJobsRevisionClusterReasonCodeCount",
    "MacroJobsRevisionClusterDigestReport",
    "build_market_research_macro_jobs_revision_cluster_digest",
    "market_research_macro_jobs_revision_cluster_digest_payload",
)


@dataclass(frozen=True)
class MacroJobsRevisionClusterDigestConfig:
    config_version: str = DEFAULT_MACRO_JOBS_REVISION_CLUSTER_DIGEST_CONFIG_VERSION
    watch_abs_revision_jobs_k: Decimal = Decimal("75.000000")
    blocked_abs_revision_jobs_k: Decimal = Decimal("150.000000")
    cluster_window_days: Decimal = Decimal("45.000000")
    min_cluster_observations: Decimal = Decimal("2.000000")
    material_surprise_jobs_k: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJobsRevisionClusterDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MACRO_JOBS_REVISION_CLUSTER_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_abs_revision_jobs_k",
            "blocked_abs_revision_jobs_k",
            "cluster_window_days",
            "min_cluster_observations",
            "material_surprise_jobs_k",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_abs_revision_jobs_k > self.blocked_abs_revision_jobs_k:
            raise ValueError(
                "watch_abs_revision_jobs_k must not exceed blocked_abs_revision_jobs_k",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MacroJobsRevisionClusterObservation:
    source_id: str
    release_id: str
    market_slug: str
    revision_delta_jobs_k: Decimal
    prior_revision_delta_jobs_k: Decimal
    consensus_surprise_jobs_k: Decimal
    revision_window_days: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJobsRevisionClusterObservation, "observation")
        for field_name in ("source_id", "release_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "revision_delta_jobs_k",
            "prior_revision_delta_jobs_k",
            "consensus_surprise_jobs_k",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "revision_window_days",
            _require_nonnegative_decimal(
                "revision_window_days",
                self.revision_window_days,
            ),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MacroJobsRevisionClusterDigestRow:
    source_id: str
    release_id: str
    market_slug: str
    revision_delta_jobs_k: Decimal
    prior_revision_delta_jobs_k: Decimal
    absolute_revision_jobs_k: Decimal
    consensus_surprise_jobs_k: Decimal
    absolute_surprise_jobs_k: Decimal
    revision_window_days: Decimal
    data_timestamp: datetime
    revision_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJobsRevisionClusterDigestRow, "row")
        for field_name in ("source_id", "release_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "revision_delta_jobs_k",
            "prior_revision_delta_jobs_k",
            "consensus_surprise_jobs_k",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_revision_jobs_k",
            "absolute_surprise_jobs_k",
            "revision_window_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("revision_status", self.revision_status, REVISION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MacroJobsRevisionClusterReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJobsRevisionClusterReasonCodeCount, "reason code count")
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MacroJobsRevisionClusterDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    clustered_revision_count: Decimal
    material_surprise_count: Decimal
    max_absolute_revision_jobs_k: Decimal
    average_absolute_revision_jobs_k: Decimal
    cluster_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...]
    reason_code_counts: tuple[MacroJobsRevisionClusterReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJobsRevisionClusterDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MACRO_JOBS_REVISION_CLUSTER_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "clustered_revision_count",
            "material_surprise_count",
            "max_absolute_revision_jobs_k",
            "average_absolute_revision_jobs_k",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cluster_risk_score",
            _require_ratio("cluster_risk_score", self.cluster_risk_score),
        )
        _require_member("digest_status", self.digest_status, REVISION_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
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
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_macro_jobs_revision_cluster_digest(
    observations: Iterable[MacroJobsRevisionClusterObservation],
    *,
    config: MacroJobsRevisionClusterDigestConfig,
    generated_at: datetime,
) -> MacroJobsRevisionClusterDigestReport:
    if type(config) is not MacroJobsRevisionClusterDigestConfig:
        raise ValueError("config must be exactly MacroJobsRevisionClusterDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows, config=config)
    digest_status = _digest_status(rows, config=config)

    return MacroJobsRevisionClusterDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        clustered_revision_count=_reason_count(rows, "macro_jobs_revision_cluster_window"),
        material_surprise_count=_reason_count(
            rows,
            "macro_jobs_revision_material_surprise",
        ),
        max_absolute_revision_jobs_k=_max_row_decimal(rows, "absolute_revision_jobs_k"),
        average_absolute_revision_jobs_k=_ratio(
            _sum_decimal(row.absolute_revision_jobs_k for row in rows),
            row_count,
        ),
        cluster_risk_score=_cluster_risk_score(rows, config=config),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_macro_jobs_revision_cluster_digest_payload(
    report: MacroJobsRevisionClusterDigestReport,
) -> dict[str, Any]:
    if type(report) is not MacroJobsRevisionClusterDigestReport:
        raise ValueError("report must be exactly MacroJobsRevisionClusterDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: MacroJobsRevisionClusterObservation,
    *,
    config: MacroJobsRevisionClusterDigestConfig,
) -> MacroJobsRevisionClusterDigestRow:
    absolute_revision_jobs_k = _quantize_decimal(abs(observation.revision_delta_jobs_k))
    absolute_surprise_jobs_k = _quantize_decimal(abs(observation.consensus_surprise_jobs_k))
    revision_status = _revision_status(absolute_revision_jobs_k, config=config)
    return MacroJobsRevisionClusterDigestRow(
        source_id=observation.source_id,
        release_id=observation.release_id,
        market_slug=observation.market_slug,
        revision_delta_jobs_k=observation.revision_delta_jobs_k,
        prior_revision_delta_jobs_k=observation.prior_revision_delta_jobs_k,
        absolute_revision_jobs_k=absolute_revision_jobs_k,
        consensus_surprise_jobs_k=observation.consensus_surprise_jobs_k,
        absolute_surprise_jobs_k=absolute_surprise_jobs_k,
        revision_window_days=observation.revision_window_days,
        data_timestamp=observation.data_timestamp,
        revision_status=revision_status,
        reason_codes=_row_reason_codes(
            observation,
            revision_status=revision_status,
            absolute_surprise_jobs_k=absolute_surprise_jobs_k,
            config=config,
        ),
    )


def _revision_status(
    absolute_revision_jobs_k: Decimal,
    *,
    config: MacroJobsRevisionClusterDigestConfig,
) -> str:
    if absolute_revision_jobs_k >= config.blocked_abs_revision_jobs_k:
        return "blocked"
    if absolute_revision_jobs_k >= config.watch_abs_revision_jobs_k:
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: MacroJobsRevisionClusterObservation,
    *,
    revision_status: str,
    absolute_surprise_jobs_k: Decimal,
    config: MacroJobsRevisionClusterDigestConfig,
) -> tuple[str, ...]:
    if revision_status == "blocked":
        reason_codes = ["macro_jobs_revision_cluster_high_abs_revision"]
    elif revision_status == "watch":
        reason_codes = ["macro_jobs_revision_cluster_watch_abs_revision"]
    else:
        reason_codes = ["macro_jobs_revision_cluster_inline"]

    if (
        revision_status != "pass"
        and observation.revision_window_days <= config.cluster_window_days
    ):
        reason_codes.append("macro_jobs_revision_cluster_window")
    if _has_direction_flip(observation) and revision_status != "pass":
        reason_codes.append("macro_jobs_revision_direction_flip")
    if (
        absolute_surprise_jobs_k >= config.material_surprise_jobs_k
        and revision_status != "pass"
    ):
        reason_codes.append("macro_jobs_revision_material_surprise")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
    *,
    config: MacroJobsRevisionClusterDigestConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("macro_jobs_revision_cluster_digest_empty",)
    reason_codes: list[str] = []
    if any(row.revision_status == "blocked" for row in rows):
        reason_codes.append("macro_jobs_revision_cluster_high_abs_revision_present")
    if _reason_count(rows, "macro_jobs_revision_cluster_window") >= config.min_cluster_observations:
        reason_codes.append("macro_jobs_revision_clustered_revisions_present")
    if _reason_count(rows, "macro_jobs_revision_material_surprise") > ZERO:
        reason_codes.append("macro_jobs_revision_material_surprise_overlap")
    if _reason_count(rows, "macro_jobs_revision_direction_flip") > ZERO:
        reason_codes.append("macro_jobs_revision_direction_flip_present")
    if not reason_codes:
        reason_codes.append("macro_jobs_revision_cluster_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
) -> tuple[MacroJobsRevisionClusterReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("macro_jobs_revision_cluster_digest_empty",):
        return (
            MacroJobsRevisionClusterReasonCodeCount(
                reason_code="macro_jobs_revision_cluster_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MacroJobsRevisionClusterReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "macro_jobs_revision_cluster_high_abs_revision_present": (
            "macro_jobs_revision_cluster_high_abs_revision"
        ),
        "macro_jobs_revision_clustered_revisions_present": (
            "macro_jobs_revision_cluster_window"
        ),
        "macro_jobs_revision_material_surprise_overlap": (
            "macro_jobs_revision_material_surprise"
        ),
        "macro_jobs_revision_direction_flip_present": (
            "macro_jobs_revision_direction_flip"
        ),
        "macro_jobs_revision_cluster_digest_clear": "macro_jobs_revision_cluster_inline",
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
    *,
    config: MacroJobsRevisionClusterDigestConfig,
) -> str:
    if not rows:
        return "blocked"
    if any(row.revision_status == "blocked" for row in rows):
        return "blocked"
    clustered_count = _reason_count(rows, "macro_jobs_revision_cluster_window")
    material_count = _reason_count(rows, "macro_jobs_revision_material_surprise")
    if clustered_count >= config.min_cluster_observations and material_count > ZERO:
        return "blocked"
    if any(row.revision_status == "watch" for row in rows):
        return "watch"
    if clustered_count >= config.min_cluster_observations:
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_macro_jobs_revision_cluster_screening"
    if status == "watch":
        return "monitor_report_only_macro_jobs_revision_cluster_screening"
    return "block_report_only_macro_jobs_revision_cluster_screening"


def _cluster_risk_score(
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
    *,
    config: MacroJobsRevisionClusterDigestConfig,
) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows, config=config) == "blocked":
        return ONE
    if _reason_count(rows, "macro_jobs_revision_cluster_window") >= config.min_cluster_observations:
        return CLUSTER_RISK_SCORE
    if any(row.revision_status == "watch" for row in rows):
        return WATCH_RISK_SCORE
    return ZERO


def _has_direction_flip(observation: MacroJobsRevisionClusterObservation) -> bool:
    return (
        observation.revision_delta_jobs_k > ZERO
        and observation.prior_revision_delta_jobs_k < ZERO
    ) or (
        observation.revision_delta_jobs_k < ZERO
        and observation.prior_revision_delta_jobs_k > ZERO
    )


def _validate_row(row: MacroJobsRevisionClusterDigestRow) -> None:
    if row.absolute_revision_jobs_k != abs(row.revision_delta_jobs_k):
        raise ValueError("absolute_revision_jobs_k must match revision_delta_jobs_k")
    if row.absolute_surprise_jobs_k != abs(row.consensus_surprise_jobs_k):
        raise ValueError("absolute_surprise_jobs_k must match consensus_surprise_jobs_k")
    if row.revision_status == "pass":
        if row.reason_codes != ("macro_jobs_revision_cluster_inline",):
            raise ValueError("reason_codes must match revision_status")
        return
    if row.revision_status == "watch":
        if "macro_jobs_revision_cluster_watch_abs_revision" not in row.reason_codes:
            raise ValueError("reason_codes must match revision_status")
        if "macro_jobs_revision_cluster_high_abs_revision" in row.reason_codes:
            raise ValueError("reason_codes must match revision_status")
    if row.revision_status == "blocked":
        if "macro_jobs_revision_cluster_high_abs_revision" not in row.reason_codes:
            raise ValueError("reason_codes must match revision_status")
        if "macro_jobs_revision_cluster_watch_abs_revision" in row.reason_codes:
            raise ValueError("reason_codes must match revision_status")
    has_direction_flip = (
        row.revision_delta_jobs_k > ZERO
        and row.prior_revision_delta_jobs_k < ZERO
    ) or (
        row.revision_delta_jobs_k < ZERO
        and row.prior_revision_delta_jobs_k > ZERO
    )
    if has_direction_flip != ("macro_jobs_revision_direction_flip" in row.reason_codes):
        raise ValueError("reason_codes must match direction flip state")


def _validate_report(report: MacroJobsRevisionClusterDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.clustered_revision_count != _reason_count(
        report.rows,
        "macro_jobs_revision_cluster_window",
    ):
        raise ValueError("clustered_revision_count must match rows")
    if report.material_surprise_count != _reason_count(
        report.rows,
        "macro_jobs_revision_material_surprise",
    ):
        raise ValueError("material_surprise_count must match rows")
    if report.max_absolute_revision_jobs_k != _max_row_decimal(
        report.rows,
        "absolute_revision_jobs_k",
    ):
        raise ValueError("max_absolute_revision_jobs_k must match rows")
    if report.average_absolute_revision_jobs_k != _ratio(
        _sum_decimal(row.absolute_revision_jobs_k for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_absolute_revision_jobs_k must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[MacroJobsRevisionClusterObservation],
) -> tuple[MacroJobsRevisionClusterObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain MacroJobsRevisionClusterObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MacroJobsRevisionClusterObservation:
            raise ValueError(
                "observations must contain MacroJobsRevisionClusterObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MacroJobsRevisionClusterDigestRow],
) -> tuple[MacroJobsRevisionClusterDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain MacroJobsRevisionClusterDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MacroJobsRevisionClusterDigestRow:
            raise ValueError("rows must contain MacroJobsRevisionClusterDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[MacroJobsRevisionClusterReasonCodeCount],
) -> tuple[MacroJobsRevisionClusterReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MacroJobsRevisionClusterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MacroJobsRevisionClusterReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(row: MacroJobsRevisionClusterDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.revision_status],
        -row.absolute_revision_jobs_k,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.revision_status == status))


def _reason_count(
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MacroJobsRevisionClusterDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
