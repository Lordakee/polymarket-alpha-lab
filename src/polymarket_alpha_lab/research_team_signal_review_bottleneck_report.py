"""Public-safe report-only signal review bottleneck summaries."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_BOTTLENECK_REPORT_CONFIG_VERSION = (
    "research-team-signal-review-bottleneck-report-v0"
)
STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT_PREC = 64
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")

_CAPACITY_WEIGHT = Decimal("0.157375000000")
_DISPERSION_WEIGHT = Decimal("0.208370370370")
_AGE_WEIGHT = Decimal("0.400000000000")
_CONFLICT_WEIGHT = Decimal("0.100000000000")
_EXPERTISE_WEIGHT = Decimal("0.132754629630")

_PASS_REASON_CODE = "signal_review_bottleneck_pass"
_EMPTY_REASON_CODE = "signal_review_bottleneck_no_inputs"
_REPORT_BLOCK_REASON_CODE = "signal_review_bottleneck_report_block_rows"
_REPORT_WATCH_REASON_CODE = "signal_review_bottleneck_report_watch_rows"
_REPORT_PASS_REASON_CODE = "signal_review_bottleneck_report_pass"
_ROW_REASON_CODE_SEQUENCE = (
    _PASS_REASON_CODE,
    "capacity_load_watch",
    "capacity_load_block",
    "confidence_dispersion_watch",
    "confidence_dispersion_block",
    "evidence_age_watch",
    "evidence_age_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "domain_expertise_watch",
    "domain_expertise_block",
)
_REPORT_REASON_CODE_SEQUENCE = (
    _REPORT_BLOCK_REASON_CODE,
    _REPORT_WATCH_REASON_CODE,
    _REPORT_PASS_REASON_CODE,
    _EMPTY_REASON_CODE,
)
_REASON_CODE_SEQUENCE = _ROW_REASON_CODE_SEQUENCE + _REPORT_REASON_CODE_SEQUENCE
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "event",
    "market",
    "source",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "bu" + "y",
    "se" + "ll",
    "recom" + "mendation",
    "siz" + "ing",
    "position",
    "private_key",
    "api_key",
    "token",
    "secret",
    "credential",
    "password",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database_url",
    "dsn",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_BOTTLENECK_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamSignalReviewBottleneckConfig",
    "ResearchTeamSignalReviewBottleneckInput",
    "ResearchTeamSignalReviewBottleneckReasonCodeCount",
    "ResearchTeamSignalReviewBottleneckReport",
    "ResearchTeamSignalReviewBottleneckRow",
    "build_research_team_signal_review_bottleneck_report",
    "research_team_signal_review_bottleneck_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSignalReviewBottleneckConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_BOTTLENECK_REPORT_CONFIG_VERSION
    )
    pass_bottleneck_score_threshold: Decimal = Decimal("0.350000")
    block_bottleneck_score_threshold: Decimal = Decimal("0.750000")
    watch_capacity_load_ratio: Decimal = Decimal("0.650000")
    block_capacity_load_ratio: Decimal = Decimal("1.000000")
    watch_confidence_dispersion: Decimal = Decimal("0.200000")
    block_confidence_dispersion: Decimal = Decimal("0.400000")
    watch_evidence_age_seconds: Decimal = Decimal("3600.000000")
    block_evidence_age_seconds: Decimal = Decimal("7200.000000")
    watch_contradiction_pressure: Decimal = Decimal("0.300000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    watch_min_domain_expertise: Decimal = Decimal("0.650000")
    block_min_domain_expertise: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewBottleneckConfig:
            raise TypeError(
                "ResearchTeamSignalReviewBottleneckConfig subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewBottleneckConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_key("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_BOTTLENECK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_bottleneck_score_threshold",
            "block_bottleneck_score_threshold",
            "watch_confidence_dispersion",
            "block_confidence_dispersion",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_min_domain_expertise",
            "block_min_domain_expertise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_capacity_load_ratio",
            "block_capacity_load_ratio",
            "watch_evidence_age_seconds",
            "block_evidence_age_seconds",
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
class ResearchTeamSignalReviewBottleneckInput:
    team_key: str
    domain_key: str
    aggregate_pending_signals: Decimal
    review_capacity_slots: Decimal
    confidence_min: Decimal
    confidence_max: Decimal
    mean_evidence_age_seconds: Decimal
    contradiction_pressure: Decimal
    domain_expertise: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewBottleneckInput:
            raise TypeError(
                "ResearchTeamSignalReviewBottleneckInput subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewBottleneckInput, "input")
        object.__setattr__(
            self,
            "team_key",
            _require_public_key("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_key("domain_key", self.domain_key),
        )
        for field_name in ("aggregate_pending_signals", "review_capacity_slots"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.review_capacity_slots <= _ZERO:
            raise ValueError("review_capacity_slots must be positive")
        for field_name in (
            "confidence_min",
            "confidence_max",
            "contradiction_pressure",
            "domain_expertise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.confidence_min > self.confidence_max:
            raise ValueError("confidence_min must be at most confidence_max")
        object.__setattr__(
            self,
            "mean_evidence_age_seconds",
            _require_nonnegative_decimal(
                "mean_evidence_age_seconds",
                self.mean_evidence_age_seconds,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamSignalReviewBottleneckRow:
    team_key: str
    domain_key: str
    status: str
    aggregate_pending_signals: Decimal
    review_capacity_slots: Decimal
    capacity_load_ratio: Decimal
    confidence_min: Decimal
    confidence_max: Decimal
    confidence_dispersion: Decimal
    mean_evidence_age_seconds: Decimal
    contradiction_pressure: Decimal
    domain_expertise: Decimal
    capacity_load_pressure: Decimal
    confidence_dispersion_pressure: Decimal
    evidence_age_pressure: Decimal
    contradiction_pressure_load: Decimal
    domain_expertise_gap_pressure: Decimal
    bottleneck_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewBottleneckRow:
            raise TypeError(
                "ResearchTeamSignalReviewBottleneckRow subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewBottleneckRow, "row")
        object.__setattr__(
            self,
            "team_key",
            _require_public_key("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_key("domain_key", self.domain_key),
        )
        _require_status("status", self.status)
        for field_name in ("aggregate_pending_signals", "review_capacity_slots"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.review_capacity_slots <= _ZERO:
            raise ValueError("review_capacity_slots must be positive")
        for field_name in (
            "confidence_min",
            "confidence_max",
            "contradiction_pressure",
            "domain_expertise",
            "capacity_load_pressure",
            "confidence_dispersion_pressure",
            "evidence_age_pressure",
            "contradiction_pressure_load",
            "domain_expertise_gap_pressure",
            "bottleneck_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_load_ratio",
            "confidence_dispersion",
            "mean_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.confidence_min > self.confidence_max:
            raise ValueError("confidence_min must be at most confidence_max")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSignalReviewBottleneckReasonCodeCount:
    reason_code: str
    count: Decimal
    team_domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewBottleneckReasonCodeCount:
            raise TypeError(
                "ResearchTeamSignalReviewBottleneckReasonCodeCount subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSignalReviewBottleneckReasonCodeCount,
            "reason_code_count",
        )
        if type(self.reason_code) is not str or self.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be a supported public reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "team_domain_ratio",
            _require_ratio_decimal("team_domain_ratio", self.team_domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSignalReviewBottleneckReport:
    generated_at: datetime
    config_version: str
    status: str
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_pending_signals: Decimal
    total_review_capacity_slots: Decimal
    average_capacity_load_ratio: Decimal
    average_confidence_dispersion: Decimal
    average_evidence_age_seconds: Decimal
    average_contradiction_pressure: Decimal
    average_domain_expertise: Decimal
    max_bottleneck_score: Decimal
    rows: tuple[ResearchTeamSignalReviewBottleneckRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSignalReviewBottleneckReasonCodeCount, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewBottleneckReport:
            raise TypeError(
                "ResearchTeamSignalReviewBottleneckReport subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewBottleneckReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_key("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in (
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pending_signals",
            "total_review_capacity_slots",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_capacity_load_ratio",
            "average_confidence_dispersion",
            "average_evidence_age_seconds",
            "average_contradiction_pressure",
            "average_domain_expertise",
            "max_bottleneck_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_contradiction_pressure",
            "average_domain_expertise",
            "max_bottleneck_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        else:
            _require_public_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")


def build_research_team_signal_review_bottleneck_report(
    inputs: Sequence[ResearchTeamSignalReviewBottleneckInput],
    *,
    config: ResearchTeamSignalReviewBottleneckConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSignalReviewBottleneckReport:
    cfg = config or ResearchTeamSignalReviewBottleneckConfig()
    if type(cfg) is not ResearchTeamSignalReviewBottleneckConfig:
        raise ValueError(
            "config must be a ResearchTeamSignalReviewBottleneckConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, cfg) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamSignalReviewBottleneckReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        team_domain_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        total_pending_signals=_sum_decimal(
            row.aggregate_pending_signals for row in rows
        ),
        total_review_capacity_slots=_sum_decimal(
            row.review_capacity_slots for row in rows
        ),
        average_capacity_load_ratio=_average_decimal(
            row.capacity_load_ratio for row in rows
        ),
        average_confidence_dispersion=_average_decimal(
            row.confidence_dispersion for row in rows
        ),
        average_evidence_age_seconds=_average_decimal(
            row.mean_evidence_age_seconds for row in rows
        ),
        average_contradiction_pressure=_average_decimal(
            row.contradiction_pressure for row in rows
        ),
        average_domain_expertise=_average_decimal(row.domain_expertise for row in rows),
        max_bottleneck_score=max(
            (row.bottleneck_score for row in rows),
            default=_ZERO,
        ),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_team_signal_review_bottleneck_report_payload(
    report: ResearchTeamSignalReviewBottleneckReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSignalReviewBottleneckReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamSignalReviewBottleneckReport or payload",
    )


def _row_from_input(
    item: ResearchTeamSignalReviewBottleneckInput,
    config: ResearchTeamSignalReviewBottleneckConfig,
) -> ResearchTeamSignalReviewBottleneckRow:
    capacity_load_ratio = _ratio_or_zero(
        item.aggregate_pending_signals,
        item.review_capacity_slots,
    )
    confidence_dispersion = _decimal(item.confidence_max - item.confidence_min)
    capacity_load_pressure = _clamp_ratio(
        capacity_load_ratio / config.block_capacity_load_ratio,
    )
    confidence_dispersion_pressure = _clamp_ratio(
        confidence_dispersion / config.block_confidence_dispersion,
    )
    evidence_age_pressure = _clamp_ratio(
        item.mean_evidence_age_seconds / config.block_evidence_age_seconds,
    )
    contradiction_pressure_load = _clamp_ratio(
        item.contradiction_pressure / config.block_contradiction_pressure,
    )
    domain_expertise_gap_pressure = _domain_expertise_gap_pressure(
        item.domain_expertise,
        config,
    )
    bottleneck_score = _bottleneck_score(
        capacity_load_pressure=capacity_load_pressure,
        confidence_dispersion_pressure=confidence_dispersion_pressure,
        evidence_age_pressure=evidence_age_pressure,
        contradiction_pressure_load=contradiction_pressure_load,
        domain_expertise_gap_pressure=domain_expertise_gap_pressure,
    )
    status = _score_status(bottleneck_score, config)
    return ResearchTeamSignalReviewBottleneckRow(
        team_key=item.team_key,
        domain_key=item.domain_key,
        status=status,
        aggregate_pending_signals=item.aggregate_pending_signals,
        review_capacity_slots=item.review_capacity_slots,
        capacity_load_ratio=capacity_load_ratio,
        confidence_min=item.confidence_min,
        confidence_max=item.confidence_max,
        confidence_dispersion=confidence_dispersion,
        mean_evidence_age_seconds=item.mean_evidence_age_seconds,
        contradiction_pressure=item.contradiction_pressure,
        domain_expertise=item.domain_expertise,
        capacity_load_pressure=capacity_load_pressure,
        confidence_dispersion_pressure=confidence_dispersion_pressure,
        evidence_age_pressure=evidence_age_pressure,
        contradiction_pressure_load=contradiction_pressure_load,
        domain_expertise_gap_pressure=domain_expertise_gap_pressure,
        bottleneck_score=bottleneck_score,
        reason_codes=_row_reason_codes(item, config),
    )


def _row_reason_codes(
    item: ResearchTeamSignalReviewBottleneckInput,
    config: ResearchTeamSignalReviewBottleneckConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_metric_reason(
        codes,
        "capacity_load",
        _metric_status_above(
            _ratio_or_zero(item.aggregate_pending_signals, item.review_capacity_slots),
            config.watch_capacity_load_ratio,
            config.block_capacity_load_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "confidence_dispersion",
        _metric_status_above(
            _decimal(item.confidence_max - item.confidence_min),
            config.watch_confidence_dispersion,
            config.block_confidence_dispersion,
        ),
    )
    _append_metric_reason(
        codes,
        "evidence_age",
        _metric_status_above(
            item.mean_evidence_age_seconds,
            config.watch_evidence_age_seconds,
            config.block_evidence_age_seconds,
        ),
    )
    _append_metric_reason(
        codes,
        "contradiction_pressure",
        _metric_status_above(
            item.contradiction_pressure,
            config.watch_contradiction_pressure,
            config.block_contradiction_pressure,
        ),
    )
    _append_metric_reason(
        codes,
        "domain_expertise",
        _metric_status_below(
            item.domain_expertise,
            config.watch_min_domain_expertise,
            config.block_min_domain_expertise,
        ),
    )
    if not codes:
        return (_PASS_REASON_CODE,)
    return _normalize_row_reason_codes(tuple(codes))


def _append_metric_reason(codes: list[str], prefix: str, status: str) -> None:
    if status != "pass":
        codes.append(f"{prefix}_{status}")


def _metric_status_above(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str:
    if value >= block_threshold:
        return "block"
    if value > watch_threshold:
        return "watch"
    return "pass"


def _metric_status_below(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str:
    if value <= block_threshold:
        return "block"
    if value < watch_threshold:
        return "watch"
    return "pass"


def _domain_expertise_gap_pressure(
    domain_expertise: Decimal,
    config: ResearchTeamSignalReviewBottleneckConfig,
) -> Decimal:
    if domain_expertise >= config.watch_min_domain_expertise:
        return _ZERO
    if domain_expertise <= config.block_min_domain_expertise:
        return _ONE
    return _clamp_ratio(
        (config.watch_min_domain_expertise - domain_expertise)
        / (config.watch_min_domain_expertise - config.block_min_domain_expertise),
    )


def _bottleneck_score(
    *,
    capacity_load_pressure: Decimal,
    confidence_dispersion_pressure: Decimal,
    evidence_age_pressure: Decimal,
    contradiction_pressure_load: Decimal,
    domain_expertise_gap_pressure: Decimal,
) -> Decimal:
    return _clamp_ratio(
        capacity_load_pressure * _CAPACITY_WEIGHT
        + confidence_dispersion_pressure * _DISPERSION_WEIGHT
        + evidence_age_pressure * _AGE_WEIGHT
        + contradiction_pressure_load * _CONFLICT_WEIGHT
        + domain_expertise_gap_pressure * _EXPERTISE_WEIGHT,
    )


def _score_status(
    score: Decimal,
    config: ResearchTeamSignalReviewBottleneckConfig,
) -> str:
    if score >= config.block_bottleneck_score_threshold:
        return "block"
    if score > config.pass_bottleneck_score_threshold:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Sequence[ResearchTeamSignalReviewBottleneckInput],
) -> tuple[ResearchTeamSignalReviewBottleneckInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized = tuple(inputs)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchTeamSignalReviewBottleneckInput:
            raise ValueError(
                "inputs must contain ResearchTeamSignalReviewBottleneckInput",
            )
        key = (item.team_key, item.domain_key)
        if key in seen:
            raise ValueError("duplicate team_key/domain_key")
        seen.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.team_key, item.domain_key)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamSignalReviewBottleneckRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamSignalReviewBottleneckRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamSignalReviewBottleneckRow",
        ) from exc
    for row in normalized:
        if type(row) is not ResearchTeamSignalReviewBottleneckRow:
            raise ValueError(
                "rows must contain ResearchTeamSignalReviewBottleneckRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchTeamSignalReviewBottleneckReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError(
            "reason_code_counts must contain ResearchTeamSignalReviewBottleneckReasonCodeCount",
        )
    try:
        normalized = tuple(counts)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reason_code_counts must contain ResearchTeamSignalReviewBottleneckReasonCodeCount",
        ) from exc
    for count in normalized:
        if type(count) is not ResearchTeamSignalReviewBottleneckReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTeamSignalReviewBottleneckReasonCodeCount",
            )
    return tuple(sorted(normalized, key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code)))


def _row_sort_key(
    row: ResearchTeamSignalReviewBottleneckRow,
) -> tuple[int, Decimal, str, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (status_rank[row.status], -row.bottleneck_score, row.team_key, row.domain_key)


def _report_status(rows: tuple[ResearchTeamSignalReviewBottleneckRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamSignalReviewBottleneckRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_reason_codes(
    rows: tuple[ResearchTeamSignalReviewBottleneckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON_CODE,)
    codes: list[str] = []
    if _status_count(rows, "block") > 0:
        codes.append(_REPORT_BLOCK_REASON_CODE)
    if _status_count(rows, "watch") > 0:
        codes.append(_REPORT_WATCH_REASON_CODE)
    if not codes:
        codes.append(_REPORT_PASS_REASON_CODE)
    return _normalize_report_reason_codes(tuple(codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamSignalReviewBottleneckRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSignalReviewBottleneckReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    counter.update(report_reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamSignalReviewBottleneckReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            team_domain_ratio=_ratio_or_zero(_count(count), row_count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: _REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _validate_config(config: ResearchTeamSignalReviewBottleneckConfig) -> None:
    if config.pass_bottleneck_score_threshold > config.block_bottleneck_score_threshold:
        raise ValueError(
            "pass_bottleneck_score_threshold must be at most block_bottleneck_score_threshold",
        )
    _require_threshold_pair(
        "watch_capacity_load_ratio",
        config.watch_capacity_load_ratio,
        "block_capacity_load_ratio",
        config.block_capacity_load_ratio,
    )
    _require_threshold_pair(
        "watch_confidence_dispersion",
        config.watch_confidence_dispersion,
        "block_confidence_dispersion",
        config.block_confidence_dispersion,
    )
    _require_threshold_pair(
        "watch_evidence_age_seconds",
        config.watch_evidence_age_seconds,
        "block_evidence_age_seconds",
        config.block_evidence_age_seconds,
    )
    _require_threshold_pair(
        "watch_contradiction_pressure",
        config.watch_contradiction_pressure,
        "block_contradiction_pressure",
        config.block_contradiction_pressure,
    )
    if config.block_min_domain_expertise > config.watch_min_domain_expertise:
        raise ValueError(
            "block_min_domain_expertise must be at most watch_min_domain_expertise",
        )


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must be at most {block_name}")


def _validate_row(row: ResearchTeamSignalReviewBottleneckRow) -> None:
    if row.capacity_load_ratio != _ratio_or_zero(
        row.aggregate_pending_signals,
        row.review_capacity_slots,
    ):
        raise ValueError("capacity_load_ratio must match aggregate capacity")
    if row.confidence_dispersion != _decimal(row.confidence_max - row.confidence_min):
        raise ValueError("confidence_dispersion must match confidence range")
    expected_score = _bottleneck_score(
        capacity_load_pressure=row.capacity_load_pressure,
        confidence_dispersion_pressure=row.confidence_dispersion_pressure,
        evidence_age_pressure=row.evidence_age_pressure,
        contradiction_pressure_load=row.contradiction_pressure_load,
        domain_expertise_gap_pressure=row.domain_expertise_gap_pressure,
    )
    if row.bottleneck_score != expected_score:
        raise ValueError("bottleneck_score must match pressure components")
    if row.status == "pass" and row.reason_codes != (_PASS_REASON_CODE,):
        raise ValueError("reason_codes must match status")
    if row.status != "pass" and row.reason_codes == (_PASS_REASON_CODE,):
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchTeamSignalReviewBottleneckReport) -> None:
    rows = report.rows
    if report.team_domain_count != _count(len(rows)):
        raise ValueError("team_domain_count must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.total_pending_signals != _sum_decimal(
        row.aggregate_pending_signals for row in rows
    ):
        raise ValueError("total_pending_signals must match rows")
    if report.total_review_capacity_slots != _sum_decimal(
        row.review_capacity_slots for row in rows
    ):
        raise ValueError("total_review_capacity_slots must match rows")
    if report.average_capacity_load_ratio != _average_decimal(
        row.capacity_load_ratio for row in rows
    ):
        raise ValueError("average_capacity_load_ratio must match rows")
    if report.average_confidence_dispersion != _average_decimal(
        row.confidence_dispersion for row in rows
    ):
        raise ValueError("average_confidence_dispersion must match rows")
    if report.average_evidence_age_seconds != _average_decimal(
        row.mean_evidence_age_seconds for row in rows
    ):
        raise ValueError("average_evidence_age_seconds must match rows")
    if report.average_contradiction_pressure != _average_decimal(
        row.contradiction_pressure for row in rows
    ):
        raise ValueError("average_contradiction_pressure must match rows")
    if report.average_domain_expertise != _average_decimal(row.domain_expertise for row in rows):
        raise ValueError("average_domain_expertise must match rows")
    if report.max_bottleneck_score != max(
        (row.bottleneck_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_bottleneck_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _ROW_REASON_CODE_SEQUENCE)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _REPORT_REASON_CODE_SEQUENCE)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError("reason_code must be a supported public reason code")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=allowed.index))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank str")
    if _PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public aggregate key")
    _reject_unsafe_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must set {field_name}=True")


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in _FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must set {field_name}=True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "public_digest":
                continue
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "public_digest":
                continue
            _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(_unsafe_term_matches(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(
            f"{field_name} must not expose raw identifiers or restricted actions",
        )


def _unsafe_term_matches(value: str, term: str) -> bool:
    if "://" in term or "_" in term:
        return term in value
    return re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", value) is not None


def _public_digest_for_report(report: ResearchTeamSignalReviewBottleneckReport) -> str:
    values = asdict(report)
    values.pop("public_digest", None)
    return _public_digest(values)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("public_digest")
    _require_public_digest("public_digest", digest)
    values = dict(payload)
    values.pop("public_digest", None)
    expected = _public_digest(values)
    if digest != expected:
        raise ValueError("public_digest must match payload")


def _public_digest(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return f"{value:.6f}"
    return value


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    total = _ZERO
    for value in values:
        total = _decimal(total + value)
    return total


def _average_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return _decimal(_sum_decimal(normalized) / Decimal(len(normalized)))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _decimal(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PREC
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)
