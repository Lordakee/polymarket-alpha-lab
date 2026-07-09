"""Public-safe domain specialist error taxonomy learning rollup report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_REPORT_CONFIG_VERSION = (
    "research-team-domain-error-taxonomy-rollup-report-v1"
)
RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

RESOLUTION_BLOCK_REASON = "domain_error_taxonomy_resolution_miss_block"
SOURCE_BLOCK_REASON = "domain_error_taxonomy_source_blindspot_block"
DRIFT_BLOCK_REASON = "domain_error_taxonomy_calibration_drift_block"
FEEDBACK_BLOCK_REASON = "domain_error_taxonomy_review_feedback_absorption_block"
RESOLUTION_WATCH_REASON = "domain_error_taxonomy_resolution_miss_watch"
SOURCE_WATCH_REASON = "domain_error_taxonomy_source_blindspot_watch"
DRIFT_WATCH_REASON = "domain_error_taxonomy_calibration_drift_watch"
FEEDBACK_WATCH_REASON = "domain_error_taxonomy_review_feedback_absorption_watch"
CLEAR_REASON = "domain_error_taxonomy_learning_signal_clear"
EMPTY_REASON = "domain_error_taxonomy_rollup_empty"

REASON_SEQUENCE = (
    RESOLUTION_BLOCK_REASON,
    SOURCE_BLOCK_REASON,
    DRIFT_BLOCK_REASON,
    FEEDBACK_BLOCK_REASON,
    RESOLUTION_WATCH_REASON,
    SOURCE_WATCH_REASON,
    DRIFT_WATCH_REASON,
    FEEDBACK_WATCH_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
UNSAFE_LABEL_FRAGMENTS = (
    "http",
    "://",
    "@",
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "secret",
    "private",
    "credential",
    "wallet",
    "order",
    "trade",
    "trading",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "position",
    "auth_",
    "_auth",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "secret",
    "private",
    "credential",
    "wallet",
    "order",
    "trade",
    "trading",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "position",
    "auth_",
    "_auth",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "market-",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "postgresql://",
    "table",
    "token",
    "secret",
    "private",
    "credential",
    "wallet",
    "order",
    "trade",
    "trading",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "position",
    "auth_",
    "_auth",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_STATUSES",
    "ResearchTeamDomainErrorTaxonomyRollupConfig",
    "ResearchTeamDomainErrorTaxonomyObservation",
    "ResearchTeamDomainErrorTaxonomyReasonCodeCount",
    "ResearchTeamDomainErrorTaxonomyRollupReport",
    "ResearchTeamDomainErrorTaxonomyRollupRow",
    "build_research_team_domain_error_taxonomy_rollup_report",
    "research_team_domain_error_taxonomy_rollup_report_digest",
    "research_team_domain_error_taxonomy_rollup_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainErrorTaxonomyRollupConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_REPORT_CONFIG_VERSION
    )
    max_pass_resolution_miss_count: Decimal = Decimal("0.000000")
    max_watch_resolution_miss_count: Decimal = Decimal("3.000000")
    max_pass_source_blindspot_count: Decimal = Decimal("0.000000")
    max_watch_source_blindspot_count: Decimal = Decimal("2.000000")
    max_pass_calibration_drift_score: Decimal = Decimal("0.050000")
    max_watch_calibration_drift_score: Decimal = Decimal("0.120000")
    min_pass_review_feedback_absorption_ratio: Decimal = Decimal("0.900000")
    min_watch_review_feedback_absorption_ratio: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainErrorTaxonomyRollupConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_resolution_miss_count",
            "max_watch_resolution_miss_count",
            "max_pass_source_blindspot_count",
            "max_watch_source_blindspot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_calibration_drift_score",
            "max_watch_calibration_drift_score",
            "min_pass_review_feedback_absorption_ratio",
            "min_watch_review_feedback_absorption_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainErrorTaxonomyObservation(_FinalPublicDataclass):
    domain_label: str
    specialist_label: str
    error_family_label: str
    resolution_miss_count: Decimal
    source_blindspot_count: Decimal
    calibration_drift_score: Decimal
    review_feedback_required_count: Decimal
    review_feedback_absorbed_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainErrorTaxonomyObservation,
            "observation",
        )
        for field_name in ("domain_label", "specialist_label", "error_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "resolution_miss_count",
            "source_blindspot_count",
            "review_feedback_required_count",
            "review_feedback_absorbed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_drift_score",
            _require_ratio_decimal(
                "calibration_drift_score",
                self.calibration_drift_score,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.review_feedback_absorbed_count > self.review_feedback_required_count:
            raise ValueError(
                "review_feedback_absorbed_count must not exceed required count",
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamDomainErrorTaxonomyRollupRow(_FinalPublicDataclass):
    rollup_rank: Decimal
    domain_label: str
    specialist_label: str
    error_family_label: str
    status: str
    source_observation_count: Decimal
    learning_signal_score: Decimal
    resolution_miss_count: Decimal
    source_blindspot_count: Decimal
    calibration_drift_score: Decimal
    review_feedback_required_count: Decimal
    review_feedback_absorbed_count: Decimal
    review_feedback_absorption_ratio: Decimal
    latest_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainErrorTaxonomyRollupRow, "row")
        object.__setattr__(self, "rollup_rank", _require_count_decimal("rollup_rank", self.rollup_rank))
        for field_name in ("domain_label", "specialist_label", "error_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        for field_name in (
            "source_observation_count",
            "resolution_miss_count",
            "source_blindspot_count",
            "review_feedback_required_count",
            "review_feedback_absorbed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "learning_signal_score",
            "calibration_drift_score",
            "review_feedback_absorption_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        if self.review_feedback_absorbed_count > self.review_feedback_required_count:
            raise ValueError(
                "review_feedback_absorbed_count must not exceed required count",
            )
        if self.review_feedback_absorption_ratio != _ratio(
            self.review_feedback_absorbed_count,
            self.review_feedback_required_count,
            zero_denominator=ONE,
        ):
            raise ValueError("review_feedback_absorption_ratio must match counts")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainErrorTaxonomyReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainErrorTaxonomyReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainErrorTaxonomyRollupReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    source_observation_count: Decimal
    taxonomy_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_resolution_miss_count: Decimal
    total_source_blindspot_count: Decimal
    total_review_feedback_required_count: Decimal
    total_review_feedback_absorbed_count: Decimal
    overall_review_feedback_absorption_ratio: Decimal
    max_calibration_drift_score: Decimal
    max_learning_signal_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainErrorTaxonomyReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainErrorTaxonomyRollupReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "source_observation_count",
            "taxonomy_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_resolution_miss_count",
            "total_source_blindspot_count",
            "total_review_feedback_required_count",
            "total_review_feedback_absorbed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overall_review_feedback_absorption_ratio",
            "max_calibration_drift_score",
            "max_learning_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return research_team_domain_error_taxonomy_rollup_report_payload(self)


def build_research_team_domain_error_taxonomy_rollup_report(
    observations: Iterable[ResearchTeamDomainErrorTaxonomyObservation],
    *,
    config: ResearchTeamDomainErrorTaxonomyRollupConfig,
    generated_at: datetime,
) -> ResearchTeamDomainErrorTaxonomyRollupReport:
    _require_exact_type(config, ResearchTeamDomainErrorTaxonomyRollupConfig, "config")
    _require_hard_flags("config", config)
    normalized_observations = _normalize_observations(observations)
    generated_at_utc = _as_utc("generated_at", generated_at)
    base_rows = tuple(
        _row_from_group(group, config=config)
        for group in _group_observations(normalized_observations)
    )
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "source_observation_count": _count(len(normalized_observations)),
        "taxonomy_row_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_resolution_miss_count": _sum_row_decimal(
            rows,
            "resolution_miss_count",
        ),
        "total_source_blindspot_count": _sum_row_decimal(
            rows,
            "source_blindspot_count",
        ),
        "total_review_feedback_required_count": _sum_row_decimal(
            rows,
            "review_feedback_required_count",
        ),
        "total_review_feedback_absorbed_count": _sum_row_decimal(
            rows,
            "review_feedback_absorbed_count",
        ),
        "overall_review_feedback_absorption_ratio": _ratio(
            _sum_row_decimal(rows, "review_feedback_absorbed_count"),
            _sum_row_decimal(rows, "review_feedback_required_count"),
        ),
        "max_calibration_drift_score": _max_decimal(
            tuple(row.calibration_drift_score for row in rows),
        ),
        "max_learning_signal_score": _max_decimal(
            tuple(row.learning_signal_score for row in rows),
        ),
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainErrorTaxonomyRollupReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_domain_error_taxonomy_rollup_report_payload(
    report: ResearchTeamDomainErrorTaxonomyRollupReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainErrorTaxonomyRollupReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainErrorTaxonomyRollupReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_domain_error_taxonomy_rollup_report_digest(
    report: ResearchTeamDomainErrorTaxonomyRollupReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_error_taxonomy_rollup_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _group_observations(
    observations: tuple[ResearchTeamDomainErrorTaxonomyObservation, ...],
) -> tuple[tuple[ResearchTeamDomainErrorTaxonomyObservation, ...], ...]:
    grouped: dict[
        tuple[str, str, str],
        list[ResearchTeamDomainErrorTaxonomyObservation],
    ] = {}
    for observation in observations:
        key = (
            observation.domain_label,
            observation.specialist_label,
            observation.error_family_label,
        )
        grouped.setdefault(key, []).append(observation)
    return tuple(tuple(grouped[key]) for key in sorted(grouped))


def _row_from_group(
    group: tuple[ResearchTeamDomainErrorTaxonomyObservation, ...],
    *,
    config: ResearchTeamDomainErrorTaxonomyRollupConfig,
) -> ResearchTeamDomainErrorTaxonomyRollupRow:
    first = group[0]
    resolution_miss_count = _sum_decimal(
        tuple(item.resolution_miss_count for item in group),
    )
    source_blindspot_count = _sum_decimal(
        tuple(item.source_blindspot_count for item in group),
    )
    calibration_drift_score = _max_decimal(
        tuple(item.calibration_drift_score for item in group),
    )
    required_count = _sum_decimal(
        tuple(item.review_feedback_required_count for item in group),
    )
    absorbed_count = _sum_decimal(
        tuple(item.review_feedback_absorbed_count for item in group),
    )
    absorption_ratio = _ratio(absorbed_count, required_count, zero_denominator=ONE)
    reason_codes = _row_reason_codes(
        resolution_miss_count=resolution_miss_count,
        source_blindspot_count=source_blindspot_count,
        calibration_drift_score=calibration_drift_score,
        review_feedback_absorption_ratio=absorption_ratio,
        config=config,
    )
    return ResearchTeamDomainErrorTaxonomyRollupRow(
        rollup_rank=ONE,
        domain_label=first.domain_label,
        specialist_label=first.specialist_label,
        error_family_label=first.error_family_label,
        status=_status_from_reason_codes(reason_codes),
        source_observation_count=_count(len(group)),
        learning_signal_score=_learning_signal_score(
            resolution_miss_count=resolution_miss_count,
            source_blindspot_count=source_blindspot_count,
            calibration_drift_score=calibration_drift_score,
            review_feedback_absorption_ratio=absorption_ratio,
            config=config,
        ),
        resolution_miss_count=resolution_miss_count,
        source_blindspot_count=source_blindspot_count,
        calibration_drift_score=calibration_drift_score,
        review_feedback_required_count=required_count,
        review_feedback_absorbed_count=absorbed_count,
        review_feedback_absorption_ratio=absorption_ratio,
        latest_observed_at=max(item.observed_at for item in group),
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchTeamDomainErrorTaxonomyRollupRow,
    rank: int,
) -> ResearchTeamDomainErrorTaxonomyRollupRow:
    return ResearchTeamDomainErrorTaxonomyRollupRow(
        rollup_rank=_count(rank),
        domain_label=row.domain_label,
        specialist_label=row.specialist_label,
        error_family_label=row.error_family_label,
        status=row.status,
        source_observation_count=row.source_observation_count,
        learning_signal_score=row.learning_signal_score,
        resolution_miss_count=row.resolution_miss_count,
        source_blindspot_count=row.source_blindspot_count,
        calibration_drift_score=row.calibration_drift_score,
        review_feedback_required_count=row.review_feedback_required_count,
        review_feedback_absorbed_count=row.review_feedback_absorbed_count,
        review_feedback_absorption_ratio=row.review_feedback_absorption_ratio,
        latest_observed_at=row.latest_observed_at,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    resolution_miss_count: Decimal,
    source_blindspot_count: Decimal,
    calibration_drift_score: Decimal,
    review_feedback_absorption_ratio: Decimal,
    config: ResearchTeamDomainErrorTaxonomyRollupConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=resolution_miss_count,
        watch=config.max_pass_resolution_miss_count,
        block=config.max_watch_resolution_miss_count,
        watch_code=RESOLUTION_WATCH_REASON,
        block_code=RESOLUTION_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=source_blindspot_count,
        watch=config.max_pass_source_blindspot_count,
        block=config.max_watch_source_blindspot_count,
        watch_code=SOURCE_WATCH_REASON,
        block_code=SOURCE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=calibration_drift_score,
        watch=config.max_pass_calibration_drift_score,
        block=config.max_watch_calibration_drift_score,
        watch_code=DRIFT_WATCH_REASON,
        block_code=DRIFT_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=review_feedback_absorption_ratio,
        watch=config.min_pass_review_feedback_absorption_ratio,
        block=config.min_watch_review_feedback_absorption_ratio,
        watch_code=FEEDBACK_WATCH_REASON,
        block_code=FEEDBACK_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in REASON_SEQUENCE if reason in set(reasons))


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > block:
        reasons.append(block_code)
    elif metric > watch:
        reasons.append(watch_code)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
    elif metric < watch:
        reasons.append(watch_code)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _learning_signal_score(
    *,
    resolution_miss_count: Decimal,
    source_blindspot_count: Decimal,
    calibration_drift_score: Decimal,
    review_feedback_absorption_ratio: Decimal,
    config: ResearchTeamDomainErrorTaxonomyRollupConfig,
) -> Decimal:
    return _max_decimal(
        (
            _high_threshold_pressure(
                resolution_miss_count,
                config.max_pass_resolution_miss_count,
                config.max_watch_resolution_miss_count,
            ),
            _high_threshold_pressure(
                source_blindspot_count,
                config.max_pass_source_blindspot_count,
                config.max_watch_source_blindspot_count,
            ),
            _high_threshold_pressure(
                calibration_drift_score,
                config.max_pass_calibration_drift_score,
                config.max_watch_calibration_drift_score,
            ),
            _low_threshold_pressure(
                review_feedback_absorption_ratio,
                config.min_pass_review_feedback_absorption_ratio,
                config.min_watch_review_feedback_absorption_ratio,
            ),
        ),
    )


def _high_threshold_pressure(value: Decimal, pass_limit: Decimal, block_limit: Decimal) -> Decimal:
    if value <= pass_limit:
        return ZERO
    if block_limit == pass_limit:
        return ONE
    return _clamp_ratio((value - pass_limit) / (block_limit - pass_limit))


def _low_threshold_pressure(value: Decimal, pass_limit: Decimal, block_limit: Decimal) -> Decimal:
    if value >= pass_limit:
        return ZERO
    if pass_limit == block_limit:
        return ONE
    return _clamp_ratio((pass_limit - value) / (pass_limit - block_limit))


def _normalize_observations(
    observations: Iterable[ResearchTeamDomainErrorTaxonomyObservation],
) -> tuple[ResearchTeamDomainErrorTaxonomyObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of taxonomy observations")
    normalized: list[ResearchTeamDomainErrorTaxonomyObservation] = []
    for observation in observations:
        _require_exact_type(
            observation,
            ResearchTeamDomainErrorTaxonomyObservation,
            "observation",
        )
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(normalized)


def _row_sort_key(row: ResearchTeamDomainErrorTaxonomyRollupRow) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        -row.learning_signal_score,
        row.domain_label,
        row.specialist_label,
        row.error_family_label,
    )


def _status_count(rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_status(rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    codes = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != CLEAR_REASON
    }
    if not codes:
        return (CLEAR_REASON,)
    return tuple(reason for reason in REASON_SEQUENCE if reason in codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...],
) -> tuple[ResearchTeamDomainErrorTaxonomyReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter(
        reason for row in rows for reason in row.reason_codes
    )
    total = _count(len(rows))
    return tuple(
        ResearchTeamDomainErrorTaxonomyReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
            row_ratio=_ratio(_count(counts[reason]), total),
        )
        for reason in REASON_SEQUENCE
        if counts[reason] > 0
    )


def _sum_row_decimal(
    rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...],
    field_name: str,
) -> Decimal:
    return _sum_decimal(tuple(getattr(row, field_name) for row in rows))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _ratio(
    numerator: Decimal,
    denominator: Decimal,
    *,
    zero_denominator: Decimal = ZERO,
) -> Decimal:
    if denominator == ZERO:
        return zero_denominator
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _validate_config(config: ResearchTeamDomainErrorTaxonomyRollupConfig) -> None:
    if config.max_pass_resolution_miss_count > config.max_watch_resolution_miss_count:
        raise ValueError("max_watch_resolution_miss_count must be at least pass")
    if config.max_pass_source_blindspot_count > config.max_watch_source_blindspot_count:
        raise ValueError("max_watch_source_blindspot_count must be at least pass")
    if config.max_pass_calibration_drift_score > config.max_watch_calibration_drift_score:
        raise ValueError("max_watch_calibration_drift_score must be at least pass")
    if (
        config.min_watch_review_feedback_absorption_ratio
        > config.min_pass_review_feedback_absorption_ratio
    ):
        raise ValueError(
            "min_watch_review_feedback_absorption_ratio must not exceed pass",
        )


def _validate_report(report: ResearchTeamDomainErrorTaxonomyRollupReport) -> None:
    rows = report.rows
    if report.taxonomy_row_count != _count(len(rows)):
        raise ValueError("taxonomy_row_count must match rows")
    if report.source_observation_count != _sum_row_decimal(
        rows,
        "source_observation_count",
    ):
        raise ValueError("source_observation_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_resolution_miss_count != _sum_row_decimal(
        rows,
        "resolution_miss_count",
    ):
        raise ValueError("total_resolution_miss_count must match rows")
    if report.total_source_blindspot_count != _sum_row_decimal(
        rows,
        "source_blindspot_count",
    ):
        raise ValueError("total_source_blindspot_count must match rows")
    if report.total_review_feedback_required_count != _sum_row_decimal(
        rows,
        "review_feedback_required_count",
    ):
        raise ValueError("total_review_feedback_required_count must match rows")
    if report.total_review_feedback_absorbed_count != _sum_row_decimal(
        rows,
        "review_feedback_absorbed_count",
    ):
        raise ValueError("total_review_feedback_absorbed_count must match rows")
    if report.overall_review_feedback_absorption_ratio != _ratio(
        report.total_review_feedback_absorbed_count,
        report.total_review_feedback_required_count,
    ):
        raise ValueError("overall_review_feedback_absorption_ratio must match rows")
    if report.max_calibration_drift_score != _max_decimal(
        tuple(row.calibration_drift_score for row in rows),
    ):
        raise ValueError("max_calibration_drift_score must match rows")
    if report.max_learning_signal_score != _max_decimal(
        tuple(row.learning_signal_score for row in rows),
    ):
        raise ValueError("max_learning_signal_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...],
) -> tuple[ResearchTeamDomainErrorTaxonomyRollupRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchTeamDomainErrorTaxonomyRollupRow, "row")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if tuple(row.rollup_rank for row in rows) != tuple(
        _count(rank) for rank in range(1, len(rows) + 1)
    ):
        raise ValueError("rollup_rank values must be sequential")
    return rows


def _require_reason_code_counts(
    counts: tuple[ResearchTeamDomainErrorTaxonomyReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainErrorTaxonomyReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        _require_exact_type(
            count,
            ResearchTeamDomainErrorTaxonomyReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(
        sorted(counts, key=lambda item: REASON_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a nonempty tuple")
    if EMPTY_REASON in reason_codes and reason_codes != (EMPTY_REASON,):
        raise ValueError("empty reason code cannot be combined")
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason code cannot be combined")
    for reason_code in reason_codes:
        if reason_code == EMPTY_REASON:
            continue
        _require_reason_code("reason_code", reason_code)
    return reason_codes


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if reason_codes != tuple(reason for reason in REASON_SEQUENCE if reason in set(reason_codes)):
        raise ValueError("reason_codes must be sorted deterministically")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason code cannot be combined")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_DOMAIN_ERROR_TAXONOMY_ROLLUP_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative finite Decimal")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be a Decimal ratio")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public aggregate label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be an unsafe-free public aggregate label")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a public string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in HEX_CHARS for character in value)
    ):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(
    label: str,
    payload: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload(
            label,
            asdict(payload),
            allow_json_containers=True,
        )
        return
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                value,
                allow_json_containers=True,
            )
        return
    if isinstance(payload, (tuple, list)):
        if not allow_json_containers:
            raise ValueError(f"unsafe public payload container in {label}")
        for item in payload:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(payload) is str:
        _reject_unsafe_text(label, payload)


def _reject_unsafe_public_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public payload key in {label}: {key}")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {label}")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, bool) or value is None or type(value) is str:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ValueError("JSON payload must not contain floats")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_values_without_digest(
    report: ResearchTeamDomainErrorTaxonomyRollupReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
