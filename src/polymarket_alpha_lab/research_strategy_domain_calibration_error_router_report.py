"""Deterministic research strategy domain calibration error router reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_STRATEGY_DOMAIN_CALIBRATION_ERROR_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-calibration-error-router-report-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_WATCH_STATUS_PREMIUM = Decimal("0.080000")
_BLOCK_STATUS_PREMIUM = Decimal("0.250000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CANONICAL_DECIMAL_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = ("pass", "watch", "block")
_STATUS_PRIORITY = {"block": 0, "watch": 1, "pass": 2}
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "candidate_id",
    "market",
    "market_id",
    "market_" "slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "se" "cret",
    "au" "th",
    "wa" "llet",
    "or" "der",
    "tr" "ade",
    "tr" "ading",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "pos" "ition",
    "sizing",
    "acc" "ount",
    "cre" "dential",
    "pri" "vate_key",
)

ROW_REASON_CODES = (
    "research_strategy_domain_calibration_error_router_expected_error_block",
    "research_strategy_domain_calibration_error_router_brier_score_block",
    "research_strategy_domain_calibration_error_router_error_trend_block",
    "research_strategy_domain_calibration_error_router_review_quality_block",
    "research_strategy_domain_calibration_error_router_expected_error_watch",
    "research_strategy_domain_calibration_error_router_brier_score_watch",
    "research_strategy_domain_calibration_error_router_error_trend_watch",
    "research_strategy_domain_calibration_error_router_review_quality_watch",
    "research_strategy_domain_calibration_error_router_ready",
)
REPORT_REASON_CODES = (
    "research_strategy_domain_calibration_error_router_block_domains_present",
    "research_strategy_domain_calibration_error_router_watch_domains_present",
    "research_strategy_domain_calibration_error_router_pass",
    "research_strategy_domain_calibration_error_router_empty",
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "watch_expected_calibration_error",
        "block_expected_calibration_error",
        "watch_mean_brier_score",
        "block_mean_brier_score",
        "watch_error_trend_delta",
        "block_error_trend_delta",
        "watch_min_review_quality_score",
        "block_min_review_quality_score",
        "status",
        "domain_count",
        "pass_domain_count",
        "watch_domain_count",
        "block_domain_count",
        "average_expected_calibration_error",
        "max_expected_calibration_error",
        "average_error_pressure_score",
        "max_error_pressure_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "domain_label",
        "team_digest",
        "manual_review_priority_rank",
        "observation_count",
        "expected_calibration_error",
        "mean_brier_score",
        "calibration_error_trend_delta",
        "positive_error_trend_delta",
        "review_quality_score",
        "error_pressure_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CALIBRATION_ERROR_ROUTER_REPORT_CONFIG_VERSION",
    "ResearchStrategyDomainCalibrationErrorRouterConfig",
    "ResearchStrategyDomainCalibrationErrorRouterDomainInput",
    "ResearchStrategyDomainCalibrationErrorRouterDomainRow",
    "ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount",
    "ResearchStrategyDomainCalibrationErrorRouterReport",
    "build_research_strategy_domain_calibration_error_router_report",
    "research_strategy_domain_calibration_error_router_report_payload",
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCalibrationErrorRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_CALIBRATION_ERROR_ROUTER_REPORT_CONFIG_VERSION
    )
    watch_expected_calibration_error: Decimal = Decimal("0.050000")
    block_expected_calibration_error: Decimal = Decimal("0.100000")
    watch_mean_brier_score: Decimal = Decimal("0.220000")
    block_mean_brier_score: Decimal = Decimal("0.300000")
    watch_error_trend_delta: Decimal = Decimal("0.020000")
    block_error_trend_delta: Decimal = Decimal("0.050000")
    watch_min_review_quality_score: Decimal = Decimal("0.750000")
    block_min_review_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainCalibrationErrorRouterConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for name in (
            "watch_expected_calibration_error",
            "block_expected_calibration_error",
            "watch_mean_brier_score",
            "block_mean_brier_score",
            "watch_error_trend_delta",
            "block_error_trend_delta",
            "watch_min_review_quality_score",
            "block_min_review_quality_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        _validate_threshold_relationships(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCalibrationErrorRouterDomainInput(_FinalPublicDataclass):
    domain_label: str
    team_key: str
    observation_count: Decimal
    expected_calibration_error: Decimal
    mean_brier_score: Decimal
    calibration_error_trend_delta: Decimal
    review_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCalibrationErrorRouterDomainInput,
            "domain_input",
        )
        object.__setattr__(
            self,
            "domain_label",
            _require_public_identifier("domain_label", self.domain_label),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_private_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "observation_count",
            _require_nonnegative_count_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        for name in (
            "expected_calibration_error",
            "mean_brier_score",
            "review_quality_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "calibration_error_trend_delta",
            _require_bounded_delta_decimal(
                "calibration_error_trend_delta",
                self.calibration_error_trend_delta,
            ),
        )
        _require_hard_flags("domain_input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCalibrationErrorRouterDomainRow(_FinalPublicDataclass):
    domain_label: str
    team_digest: str
    manual_review_priority_rank: Decimal
    observation_count: Decimal
    expected_calibration_error: Decimal
    mean_brier_score: Decimal
    calibration_error_trend_delta: Decimal
    positive_error_trend_delta: Decimal
    review_quality_score: Decimal
    error_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCalibrationErrorRouterDomainRow,
            "row",
        )
        object.__setattr__(
            self,
            "domain_label",
            _require_public_identifier("domain_label", self.domain_label),
        )
        object.__setattr__(
            self,
            "team_digest",
            _require_public_digest("team_digest", self.team_digest),
        )
        object.__setattr__(
            self,
            "manual_review_priority_rank",
            _require_positive_count_decimal(
                "manual_review_priority_rank",
                self.manual_review_priority_rank,
            ),
        )
        object.__setattr__(
            self,
            "observation_count",
            _require_nonnegative_count_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        for name in (
            "expected_calibration_error",
            "mean_brier_score",
            "positive_error_trend_delta",
            "review_quality_score",
            "error_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "calibration_error_trend_delta",
            _require_bounded_delta_decimal(
                "calibration_error_trend_delta",
                self.calibration_error_trend_delta,
            ),
        )
        object.__setattr__(
            self,
            "status",
            _require_status(self.status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_public_identifier("reason_code", self.reason_code),
        )
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be known")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCalibrationErrorRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    watch_expected_calibration_error: Decimal
    block_expected_calibration_error: Decimal
    watch_mean_brier_score: Decimal
    block_mean_brier_score: Decimal
    watch_error_trend_delta: Decimal
    block_error_trend_delta: Decimal
    watch_min_review_quality_score: Decimal
    block_min_review_quality_score: Decimal
    status: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    average_expected_calibration_error: Decimal
    max_expected_calibration_error: Decimal
    average_error_pressure_score: Decimal
    max_error_pressure_score: Decimal
    rows: tuple[ResearchStrategyDomainCalibrationErrorRouterDomainRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainCalibrationErrorRouterReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for name in (
            "watch_expected_calibration_error",
            "block_expected_calibration_error",
            "watch_mean_brier_score",
            "block_mean_brier_score",
            "watch_error_trend_delta",
            "block_error_trend_delta",
            "watch_min_review_quality_score",
            "block_min_review_quality_score",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        _validate_threshold_relationships(self)
        object.__setattr__(self, "status", _require_status(self.status))
        for name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
        ):
            object.__setattr__(self, name, _require_nonnegative_count_decimal(name, getattr(self, name)))
        for name in (
            "average_expected_calibration_error",
            "max_expected_calibration_error",
            "average_error_pressure_score",
            "max_error_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_payload_digest("payload", payload)
        return payload


def build_research_strategy_domain_calibration_error_router_report(
    domain_inputs: Iterable[object],
    *,
    config: ResearchStrategyDomainCalibrationErrorRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainCalibrationErrorRouterReport:
    if type(config) is not ResearchStrategyDomainCalibrationErrorRouterConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainCalibrationErrorRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _prioritized_rows(_normalize_domain_items(domain_inputs), config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "watch_expected_calibration_error": config.watch_expected_calibration_error,
        "block_expected_calibration_error": config.block_expected_calibration_error,
        "watch_mean_brier_score": config.watch_mean_brier_score,
        "block_mean_brier_score": config.block_mean_brier_score,
        "watch_error_trend_delta": config.watch_error_trend_delta,
        "block_error_trend_delta": config.block_error_trend_delta,
        "watch_min_review_quality_score": config.watch_min_review_quality_score,
        "block_min_review_quality_score": config.block_min_review_quality_score,
        "status": _status_from_report_reason_codes(reason_codes),
        "domain_count": _decimal_count(len(rows)),
        "pass_domain_count": _status_count(rows, "pass"),
        "watch_domain_count": _status_count(rows, "watch"),
        "block_domain_count": _status_count(rows, "block"),
        "average_expected_calibration_error": _mean(
            tuple(row.expected_calibration_error for row in rows),
        ),
        "max_expected_calibration_error": _max_decimal(
            tuple(row.expected_calibration_error for row in rows),
        ),
        "average_error_pressure_score": _mean(
            tuple(row.error_pressure_score for row in rows),
        ),
        "max_error_pressure_score": _max_decimal(
            tuple(row.error_pressure_score for row in rows),
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDomainCalibrationErrorRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_domain_calibration_error_router_report_payload(
    report: ResearchStrategyDomainCalibrationErrorRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainCalibrationErrorRouterReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _report_from_payload(report).payload
    else:
        raise ValueError(
            "report must be a ResearchStrategyDomainCalibrationErrorRouterReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload_digest("payload", payload)
    return payload


def _row_from_domain_item(
    item: ResearchStrategyDomainCalibrationErrorRouterDomainInput,
    config: ResearchStrategyDomainCalibrationErrorRouterConfig,
) -> ResearchStrategyDomainCalibrationErrorRouterDomainRow:
    positive_trend = _positive_decimal(item.calibration_error_trend_delta)
    reason_codes = _row_reason_codes(
        item,
        positive_error_trend_delta=positive_trend,
        config=config,
    )
    status = _status_from_row_reason_codes(reason_codes)
    return ResearchStrategyDomainCalibrationErrorRouterDomainRow(
        domain_label=item.domain_label,
        team_digest=_public_digest("team", item.team_key),
        manual_review_priority_rank=_ONE,
        observation_count=item.observation_count,
        expected_calibration_error=item.expected_calibration_error,
        mean_brier_score=item.mean_brier_score,
        calibration_error_trend_delta=item.calibration_error_trend_delta,
        positive_error_trend_delta=positive_trend,
        review_quality_score=item.review_quality_score,
        error_pressure_score=_error_pressure_score(
            expected_calibration_error=item.expected_calibration_error,
            mean_brier_score=item.mean_brier_score,
            positive_error_trend_delta=positive_trend,
            review_quality_score=item.review_quality_score,
            status=status,
        ),
        status=status,
        reason_codes=reason_codes,
    )


def _prioritized_rows(
    items: tuple[ResearchStrategyDomainCalibrationErrorRouterDomainInput, ...],
    config: ResearchStrategyDomainCalibrationErrorRouterConfig,
) -> tuple[ResearchStrategyDomainCalibrationErrorRouterDomainRow, ...]:
    rows = tuple(sorted((_row_from_domain_item(item, config) for item in items), key=_row_sort_key))
    return tuple(
        replace(row, manual_review_priority_rank=_decimal_count(index))
        for index, row in enumerate(rows, start=1)
    )


def _row_sort_key(
    row: ResearchStrategyDomainCalibrationErrorRouterDomainRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_PRIORITY[row.status],
        -row.error_pressure_score,
        -row.expected_calibration_error,
        row.domain_label,
        row.team_digest,
    )


def _row_reason_codes(
    item: ResearchStrategyDomainCalibrationErrorRouterDomainInput,
    *,
    positive_error_trend_delta: Decimal,
    config: ResearchStrategyDomainCalibrationErrorRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.expected_calibration_error >= config.block_expected_calibration_error:
        reasons.append(
            "research_strategy_domain_calibration_error_router_expected_error_block",
        )
    if item.mean_brier_score >= config.block_mean_brier_score:
        reasons.append(
            "research_strategy_domain_calibration_error_router_brier_score_block",
        )
    if positive_error_trend_delta >= config.block_error_trend_delta:
        reasons.append(
            "research_strategy_domain_calibration_error_router_error_trend_block",
        )
    if item.review_quality_score <= config.block_min_review_quality_score:
        reasons.append(
            "research_strategy_domain_calibration_error_router_review_quality_block",
        )
    if reasons:
        return _normalize_reason_codes(tuple(reasons), ROW_REASON_CODES)

    if item.expected_calibration_error >= config.watch_expected_calibration_error:
        reasons.append(
            "research_strategy_domain_calibration_error_router_expected_error_watch",
        )
    if item.mean_brier_score >= config.watch_mean_brier_score:
        reasons.append(
            "research_strategy_domain_calibration_error_router_brier_score_watch",
        )
    if positive_error_trend_delta >= config.watch_error_trend_delta:
        reasons.append(
            "research_strategy_domain_calibration_error_router_error_trend_watch",
        )
    if item.review_quality_score <= config.watch_min_review_quality_score:
        reasons.append(
            "research_strategy_domain_calibration_error_router_review_quality_watch",
        )
    if reasons:
        return _normalize_reason_codes(tuple(reasons), ROW_REASON_CODES)
    return ("research_strategy_domain_calibration_error_router_ready",)


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainCalibrationErrorRouterDomainRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_strategy_domain_calibration_error_router_empty",)
    reasons: list[str] = []
    if any(row.status == "block" for row in rows):
        reasons.append(
            "research_strategy_domain_calibration_error_router_block_domains_present",
        )
    if any(row.status == "watch" for row in rows):
        reasons.append(
            "research_strategy_domain_calibration_error_router_watch_domains_present",
        )
    if not reasons:
        reasons.append("research_strategy_domain_calibration_error_router_pass")
    return tuple(reasons)


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_report_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "research_strategy_domain_calibration_error_router_block_domains_present"
        in reason_codes
        or "research_strategy_domain_calibration_error_router_empty" in reason_codes
    ):
        return "block"
    if (
        "research_strategy_domain_calibration_error_router_watch_domains_present"
        in reason_codes
    ):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainCalibrationErrorRouterDomainRow, ...],
) -> tuple[ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount, ...]:
    all_reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(all_reason_codes.count(reason_code)),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in all_reason_codes
    )


def _normalize_domain_items(
    value: Iterable[object],
) -> tuple[ResearchStrategyDomainCalibrationErrorRouterDomainInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("domain_inputs must be an iterable")
    items = tuple(value)
    seen_labels: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyDomainCalibrationErrorRouterDomainInput:
            raise ValueError("domain_inputs must contain domain input values")
        _require_hard_flags("domain_input", item)
        if item.domain_label in seen_labels:
            raise ValueError("domain_label values must be unique")
        seen_labels.add(item.domain_label)
    return tuple(sorted(items, key=lambda item: (item.domain_label, item.team_key)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyDomainCalibrationErrorRouterDomainRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDomainCalibrationErrorRouterDomainRow:
            raise ValueError("rows must contain domain row values")
        _require_hard_flags("row", row)
        if row.domain_label in seen_labels:
            raise ValueError("domain_label values must be unique")
        seen_labels.add(row.domain_label)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must be deterministic")
    for index, row in enumerate(rows, start=1):
        if row.manual_review_priority_rank != _decimal_count(index):
            raise ValueError(
                "manual_review_priority_rank must match deterministic row sequence",
            )
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen_reason_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
        _require_hard_flags("reason_code_count", row)
    expected = tuple(row for code in ROW_REASON_CODES for row in rows if row.reason_code == code)
    if rows != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    clean: list[str] = []
    allowed = frozenset(allowed_sequence)
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        reason_code = _require_public_identifier("reason_code", item)
        if reason_code not in allowed:
            raise ValueError("reason_codes must contain known values")
        if reason_code not in clean:
            clean.append(reason_code)
    if not clean:
        raise ValueError("reason_codes must contain at least one value")
    return tuple(reason_code for reason_code in allowed_sequence if reason_code in clean)


def _validate_row_consistency(
    row: ResearchStrategyDomainCalibrationErrorRouterDomainRow,
) -> None:
    if row.positive_error_trend_delta != _positive_decimal(
        row.calibration_error_trend_delta,
    ):
        raise ValueError("positive_error_trend_delta must match trend delta")
    if row.status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_score = _error_pressure_score(
        expected_calibration_error=row.expected_calibration_error,
        mean_brier_score=row.mean_brier_score,
        positive_error_trend_delta=row.positive_error_trend_delta,
        review_quality_score=row.review_quality_score,
        status=row.status,
    )
    if row.error_pressure_score != expected_score:
        raise ValueError("error_pressure_score must match row fields")


def _validate_report_consistency(
    report: ResearchStrategyDomainCalibrationErrorRouterReport,
) -> None:
    config = _config_from_report(report)
    for row in report.rows:
        expected_reason_codes = _row_reason_codes(
            row,
            positive_error_trend_delta=row.positive_error_trend_delta,
            config=config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError(
                "reason_codes must match calibration thresholds",
            )
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_domain_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_domain_count must match rows")
    if report.block_domain_count != _status_count(report.rows, "block"):
        raise ValueError("block_domain_count must match rows")
    if report.average_expected_calibration_error != _mean(
        tuple(row.expected_calibration_error for row in report.rows),
    ):
        raise ValueError("average_expected_calibration_error must match rows")
    if report.max_expected_calibration_error != _max_decimal(
        tuple(row.expected_calibration_error for row in report.rows),
    ):
        raise ValueError("max_expected_calibration_error must match rows")
    if report.average_error_pressure_score != _mean(
        tuple(row.error_pressure_score for row in report.rows),
    ):
        raise ValueError("average_error_pressure_score must match rows")
    if report.max_error_pressure_score != _max_decimal(
        tuple(row.error_pressure_score for row in report.rows),
    ):
        raise ValueError("max_error_pressure_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_report_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _config_from_report(
    report: ResearchStrategyDomainCalibrationErrorRouterReport,
) -> ResearchStrategyDomainCalibrationErrorRouterConfig:
    return ResearchStrategyDomainCalibrationErrorRouterConfig(
        config_version=report.config_version,
        watch_expected_calibration_error=report.watch_expected_calibration_error,
        block_expected_calibration_error=report.block_expected_calibration_error,
        watch_mean_brier_score=report.watch_mean_brier_score,
        block_mean_brier_score=report.block_mean_brier_score,
        watch_error_trend_delta=report.watch_error_trend_delta,
        block_error_trend_delta=report.block_error_trend_delta,
        watch_min_review_quality_score=report.watch_min_review_quality_score,
        block_min_review_quality_score=report.block_min_review_quality_score,
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainCalibrationErrorRouterDomainRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(max(values))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _positive_decimal(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    return _quantize(value)


def _error_pressure_score(
    *,
    expected_calibration_error: Decimal,
    mean_brier_score: Decimal,
    positive_error_trend_delta: Decimal,
    review_quality_score: Decimal,
    status: str,
) -> Decimal:
    if status == "pass":
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        pressure = (
            expected_calibration_error
            + mean_brier_score
            + positive_error_trend_delta
            + (_ONE - review_quality_score)
        ) / Decimal("4")
        if status == "watch":
            pressure += _WATCH_STATUS_PREMIUM
        elif status == "block":
            pressure += _BLOCK_STATUS_PREMIUM
        return min(_ONE, _quantize(pressure))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            clean = value.quantize(_QUANT)
    except InvalidOperation as error:
        raise ValueError("decimal value must fit configured precision") from error
    if clean.is_zero():
        return _ZERO
    return clean


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if raw > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _require_decimal(field_name, raw)


def _validate_threshold_relationships(value: object) -> None:
    if (
        getattr(value, "watch_expected_calibration_error")
        > getattr(value, "block_expected_calibration_error")
    ):
        raise ValueError(
            "watch_expected_calibration_error must not exceed "
            "block_expected_calibration_error",
        )
    if getattr(value, "watch_mean_brier_score") > getattr(
        value,
        "block_mean_brier_score",
    ):
        raise ValueError(
            "watch_mean_brier_score must not exceed block_mean_brier_score",
        )
    if getattr(value, "watch_error_trend_delta") > getattr(
        value,
        "block_error_trend_delta",
    ):
        raise ValueError(
            "watch_error_trend_delta must not exceed block_error_trend_delta",
        )
    if getattr(value, "block_min_review_quality_score") > getattr(
        value,
        "watch_min_review_quality_score",
    ):
        raise ValueError(
            "block_min_review_quality_score must not exceed "
            "watch_min_review_quality_score",
        )


def _require_bounded_delta_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < -_ONE:
        raise ValueError(f"{field_name} must be >= -1.000000")
    if raw > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _require_decimal(field_name, raw)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _require_decimal(field_name, raw)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_nonnegative_count_decimal(field_name, value)
    if clean <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return clean


def _require_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(raw)


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    lower_value = value.lower()
    if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} must be public")
    return value


def _require_private_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or len(value) > 256:
        raise ValueError(f"{field_name} must be a canonical identifier")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _PUBLIC_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a prefixed SHA-256 digest")
    return value


def _public_digest(label: str, value: str) -> str:
    return "sha256:" + sha256(f"{label}:{value}".encode("utf-8")).hexdigest()


def _require_status(value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{item.name}",
                getattr(value, item.name),
            )
        return
    if type(value) is str:
        _require_public_payload_string(label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("unsafe public payload")
        if not value.is_finite():
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("unsafe public payload")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            try:
                _require_public_identifier("payload_key", key)
            except ValueError as error:
                raise ValueError("unsafe public payload") from error
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _require_public_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError("unsafe public payload")
    lower_value = value.lower()
    if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError("unsafe public payload")
    if "://" in lower_value:
        raise ValueError("unsafe public payload")
    return value


def _report_values_without_digest(
    report: ResearchStrategyDomainCalibrationErrorRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainCalibrationErrorRouterReport:
    _validate_payload_digest("payload", payload)
    rows_value = _payload_list("rows", payload["rows"])
    reason_code_counts_value = _payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    return ResearchStrategyDomainCalibrationErrorRouterReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        watch_expected_calibration_error=_payload_decimal(
            "watch_expected_calibration_error",
            payload["watch_expected_calibration_error"],
        ),
        block_expected_calibration_error=_payload_decimal(
            "block_expected_calibration_error",
            payload["block_expected_calibration_error"],
        ),
        watch_mean_brier_score=_payload_decimal(
            "watch_mean_brier_score",
            payload["watch_mean_brier_score"],
        ),
        block_mean_brier_score=_payload_decimal(
            "block_mean_brier_score",
            payload["block_mean_brier_score"],
        ),
        watch_error_trend_delta=_payload_decimal(
            "watch_error_trend_delta",
            payload["watch_error_trend_delta"],
        ),
        block_error_trend_delta=_payload_decimal(
            "block_error_trend_delta",
            payload["block_error_trend_delta"],
        ),
        watch_min_review_quality_score=_payload_decimal(
            "watch_min_review_quality_score",
            payload["watch_min_review_quality_score"],
        ),
        block_min_review_quality_score=_payload_decimal(
            "block_min_review_quality_score",
            payload["block_min_review_quality_score"],
        ),
        status=_payload_string("status", payload["status"]),
        domain_count=_payload_decimal("domain_count", payload["domain_count"]),
        pass_domain_count=_payload_decimal(
            "pass_domain_count",
            payload["pass_domain_count"],
        ),
        watch_domain_count=_payload_decimal(
            "watch_domain_count",
            payload["watch_domain_count"],
        ),
        block_domain_count=_payload_decimal(
            "block_domain_count",
            payload["block_domain_count"],
        ),
        average_expected_calibration_error=_payload_decimal(
            "average_expected_calibration_error",
            payload["average_expected_calibration_error"],
        ),
        max_expected_calibration_error=_payload_decimal(
            "max_expected_calibration_error",
            payload["max_expected_calibration_error"],
        ),
        average_error_pressure_score=_payload_decimal(
            "average_error_pressure_score",
            payload["average_error_pressure_score"],
        ),
        max_error_pressure_score=_payload_decimal(
            "max_error_pressure_score",
            payload["max_error_pressure_score"],
        ),
        rows=tuple(_row_from_payload(row) for row in rows_value),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(item)
            for item in reason_code_counts_value
        ),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
) -> ResearchStrategyDomainCalibrationErrorRouterDomainRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys("row", value, _ROW_PAYLOAD_KEYS)
    return ResearchStrategyDomainCalibrationErrorRouterDomainRow(
        domain_label=_payload_string("domain_label", value["domain_label"]),
        team_digest=_payload_string("team_digest", value["team_digest"]),
        manual_review_priority_rank=_payload_decimal(
            "manual_review_priority_rank",
            value["manual_review_priority_rank"],
        ),
        observation_count=_payload_decimal(
            "observation_count",
            value["observation_count"],
        ),
        expected_calibration_error=_payload_decimal(
            "expected_calibration_error",
            value["expected_calibration_error"],
        ),
        mean_brier_score=_payload_decimal(
            "mean_brier_score",
            value["mean_brier_score"],
        ),
        calibration_error_trend_delta=_payload_decimal(
            "calibration_error_trend_delta",
            value["calibration_error_trend_delta"],
        ),
        positive_error_trend_delta=_payload_decimal(
            "positive_error_trend_delta",
            value["positive_error_trend_delta"],
        ),
        review_quality_score=_payload_decimal(
            "review_quality_score",
            value["review_quality_score"],
        ),
        error_pressure_score=_payload_decimal(
            "error_pressure_score",
            value["error_pressure_score"],
        ),
        status=_payload_string("status", value["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_payload_true("paper_only", value["paper_only"]),
        report_only=_payload_true("report_only", value["report_only"]),
        readonly=_payload_true("readonly", value["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
) -> ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_keys(
        "reason_code_count",
        value,
        _REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    return ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount(
        reason_code=_payload_string("reason_code", value["reason_code"]),
        count=_payload_decimal("count", value["count"]),
        paper_only=_payload_true("paper_only", value["paper_only"]),
        report_only=_payload_true("report_only", value["report_only"]),
        readonly=_payload_true("readonly", value["readonly"]),
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest_payload", payload)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(_canonical_payload_bytes(payload)).hexdigest()


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validate_payload_digest(label: str, payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(label, payload)
    _validate_payload_schema(payload)
    supplied = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", supplied)
    base_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys("report", payload, _REPORT_PAYLOAD_KEYS)
    rows = _payload_list("rows", payload["rows"])
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_keys("row", row, _ROW_PAYLOAD_KEYS)
    reason_code_counts = _payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    for item in reason_code_counts:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_keys(
            "reason_code_count",
            item,
            _REASON_CODE_COUNT_PAYLOAD_KEYS,
        )
    _payload_list("reason_codes", payload["reason_codes"])


def _require_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} keys must match report payload schema")


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a canonical JSON list")
    return value


def _payload_reason_codes(
    field_name: str,
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    items = _payload_list(field_name, value)
    if any(type(item) is not str for item in items):
        raise ValueError(f"{field_name} must contain strings")
    normalized = _normalize_reason_codes(tuple(items), allowed_sequence)
    if tuple(items) != normalized:
        raise ValueError(f"{field_name} must use canonical reason_codes")
    return normalized


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or _CANONICAL_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    raw = Decimal(value)
    if not raw.is_finite() or (raw.is_zero() and raw.as_tuple().sign == 1):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    clean = _require_decimal(field_name, raw)
    if format(clean, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return clean


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from error
    clean = _as_utc(field_name, parsed)
    if clean.isoformat() != text:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return clean


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a hex digest")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")
