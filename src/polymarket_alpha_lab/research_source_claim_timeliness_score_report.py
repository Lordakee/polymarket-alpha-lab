"""Pure report-only aggregation for source claim timeliness scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CLAIM_TIMELINESS_SCORE_CONFIG_VERSION = (
    "research-source-claim-timeliness-score-v0"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "raw",
    "http",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "auth",
    "private",
    "secret",
    "credential",
)
_REASON_CODE_SEQUENCE = (
    "claim_age_watch",
    "claim_age_block",
    "update_latency_watch",
    "update_latency_block",
    "corroboration_delay_watch",
    "corroboration_delay_block",
    "stale_contradiction_pressure_watch",
    "stale_contradiction_pressure_block",
    "manual_escalation_urgency_watch",
    "manual_escalation_urgency_block",
    "source_class_timeliness_pass",
)


@dataclass(frozen=True)
class ResearchSourceClaimTimelinessScoreConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_CLAIM_TIMELINESS_SCORE_CONFIG_VERSION
    watch_claim_age_seconds: Decimal = Decimal("21600.000000")
    block_claim_age_seconds: Decimal = Decimal("86400.000000")
    watch_update_latency_seconds: Decimal = Decimal("7200.000000")
    block_update_latency_seconds: Decimal = Decimal("21600.000000")
    watch_corroboration_delay_seconds: Decimal = Decimal("14400.000000")
    block_corroboration_delay_seconds: Decimal = Decimal("43200.000000")
    watch_stale_contradiction_pressure: Decimal = Decimal("0.250000")
    block_stale_contradiction_pressure: Decimal = Decimal("0.750000")
    watch_manual_escalation_urgency: Decimal = Decimal("0.500000")
    block_manual_escalation_urgency: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimTimelinessScoreConfig:
            raise TypeError("ResearchSourceClaimTimelinessScoreConfig cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimTimelinessScoreConfig:
            raise ValueError("config must be exactly ResearchSourceClaimTimelinessScoreConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_CLAIM_TIMELINESS_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_claim_age_seconds",
            "block_claim_age_seconds",
            "watch_update_latency_seconds",
            "block_update_latency_seconds",
            "watch_corroboration_delay_seconds",
            "block_corroboration_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_contradiction_pressure",
            "block_stale_contradiction_pressure",
            "watch_manual_escalation_urgency",
            "block_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_before_block(
            "claim_age_seconds",
            self.watch_claim_age_seconds,
            self.block_claim_age_seconds,
        )
        _require_watch_before_block(
            "update_latency_seconds",
            self.watch_update_latency_seconds,
            self.block_update_latency_seconds,
        )
        _require_watch_before_block(
            "corroboration_delay_seconds",
            self.watch_corroboration_delay_seconds,
            self.block_corroboration_delay_seconds,
        )
        _require_watch_before_block(
            "stale_contradiction_pressure",
            self.watch_stale_contradiction_pressure,
            self.block_stale_contradiction_pressure,
        )
        _require_watch_before_block(
            "manual_escalation_urgency",
            self.watch_manual_escalation_urgency,
            self.block_manual_escalation_urgency,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimTimelinessObservation:
    source_class: str
    claim_observed_at: datetime
    source_updated_at: datetime
    corroborated_at: datetime | None
    stale_contradiction_count: Decimal
    manual_escalation_signal: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimTimelinessObservation:
            raise TypeError("ResearchSourceClaimTimelinessObservation cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimTimelinessObservation:
            raise ValueError(
                "observation must be exactly ResearchSourceClaimTimelinessObservation",
            )
        _require_public_identifier("source_class", self.source_class)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "source_updated_at",
            _as_utc("source_updated_at", self.source_updated_at),
        )
        if self.source_updated_at < self.claim_observed_at:
            raise ValueError("source_updated_at must not be before claim_observed_at")
        if self.corroborated_at is not None:
            object.__setattr__(
                self,
                "corroborated_at",
                _as_utc("corroborated_at", self.corroborated_at),
            )
            if self.corroborated_at < self.claim_observed_at:
                raise ValueError("corroborated_at must not be before claim_observed_at")
        object.__setattr__(
            self,
            "stale_contradiction_count",
            _require_nonnegative_whole_decimal(
                "stale_contradiction_count",
                self.stale_contradiction_count,
            ),
        )
        if type(self.manual_escalation_signal) is not bool:
            raise ValueError("manual_escalation_signal must be a bool")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimTimelinessScoreRow:
    source_class: str
    claim_count: Decimal
    average_claim_age_seconds: Decimal
    max_claim_age_seconds: Decimal
    average_update_latency_seconds: Decimal
    max_update_latency_seconds: Decimal
    average_corroboration_delay_seconds: Decimal
    max_corroboration_delay_seconds: Decimal
    stale_contradiction_pressure: Decimal
    manual_escalation_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimTimelinessScoreRow:
            raise TypeError("ResearchSourceClaimTimelinessScoreRow cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimTimelinessScoreRow:
            raise ValueError("row must be exactly ResearchSourceClaimTimelinessScoreRow")
        _require_public_identifier("source_class", self.source_class)
        object.__setattr__(
            self,
            "claim_count",
            _require_positive_whole_decimal("claim_count", self.claim_count),
        )
        for field_name in (
            "average_claim_age_seconds",
            "max_claim_age_seconds",
            "average_update_latency_seconds",
            "max_update_latency_seconds",
            "average_corroboration_delay_seconds",
            "max_corroboration_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_contradiction_pressure",
            "manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceClaimTimelinessScoreReport:
    generated_at: datetime
    config_version: str
    source_class_count: Decimal
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_claim_age_seconds: Decimal
    max_update_latency_seconds: Decimal
    max_corroboration_delay_seconds: Decimal
    max_stale_contradiction_pressure: Decimal
    max_manual_escalation_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimTimelinessScoreRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimTimelinessScoreReport:
            raise TypeError("ResearchSourceClaimTimelinessScoreReport cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimTimelinessScoreReport:
            raise ValueError("report must be exactly ResearchSourceClaimTimelinessScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_CLAIM_TIMELINESS_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_class_count",
            "claim_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_claim_age_seconds",
            "max_update_latency_seconds",
            "max_corroboration_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_stale_contradiction_pressure",
            "max_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_claim_timeliness_score_report(
    observations: Sequence[ResearchSourceClaimTimelinessObservation],
    *,
    config: ResearchSourceClaimTimelinessScoreConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceClaimTimelinessScoreReport:
    if config is None:
        config = ResearchSourceClaimTimelinessScoreConfig()
    if type(config) is not ResearchSourceClaimTimelinessScoreConfig:
        raise ValueError("config must be a ResearchSourceClaimTimelinessScoreConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_empty_observations(normalized)
    for item in normalized:
        _reject_future_time("claim_observed_at", item.claim_observed_at, generated_at)
        _reject_future_time("source_updated_at", item.source_updated_at, generated_at)
        if item.corroborated_at is not None:
            _reject_future_time("corroborated_at", item.corroborated_at, generated_at)

    rows = _build_rows(normalized, generated_at, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "source_class_count": _decimal_count(len(rows)),
        "claim_count": _decimal_count(len(normalized)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_claim_age_seconds": _average(
            tuple(_claim_age_seconds(item, generated_at) for item in normalized),
        ),
        "max_update_latency_seconds": max(
            (row.max_update_latency_seconds for row in rows),
            default=_ZERO,
        ),
        "max_corroboration_delay_seconds": max(
            (row.max_corroboration_delay_seconds for row in rows),
            default=_ZERO,
        ),
        "max_stale_contradiction_pressure": max(
            (row.stale_contradiction_pressure for row in rows),
            default=_ZERO,
        ),
        "max_manual_escalation_urgency": max(
            (row.manual_escalation_urgency for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimTimelinessScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_timeliness_score_report_payload(
    report: ResearchSourceClaimTimelinessScoreReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceClaimTimelinessScoreReport:
        raise ValueError("report must be a ResearchSourceClaimTimelinessScoreReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_rows(
    observations: tuple[ResearchSourceClaimTimelinessObservation, ...],
    generated_at: datetime,
    config: ResearchSourceClaimTimelinessScoreConfig,
) -> tuple[ResearchSourceClaimTimelinessScoreRow, ...]:
    grouped: dict[str, list[ResearchSourceClaimTimelinessObservation]] = {}
    for item in observations:
        grouped.setdefault(item.source_class, []).append(item)
    return tuple(
        _row_for_source_class(
            source_class=source_class,
            observations=tuple(grouped[source_class]),
            generated_at=generated_at,
            config=config,
        )
        for source_class in sorted(grouped)
    )


def _row_for_source_class(
    *,
    source_class: str,
    observations: tuple[ResearchSourceClaimTimelinessObservation, ...],
    generated_at: datetime,
    config: ResearchSourceClaimTimelinessScoreConfig,
) -> ResearchSourceClaimTimelinessScoreRow:
    claim_ages = tuple(_claim_age_seconds(item, generated_at) for item in observations)
    update_latencies = tuple(
        _elapsed_seconds(item.source_updated_at, generated_at) for item in observations
    )
    corroboration_delays = tuple(
        _corroboration_delay_seconds(item, generated_at) for item in observations
    )
    stale_pressure = _clamp_ratio(
        sum((item.stale_contradiction_count for item in observations), _ZERO)
        / _decimal_count(len(observations)),
    )
    manual_urgency = _clamp_ratio(
        _decimal_count(sum(1 for item in observations if item.manual_escalation_signal))
        / _decimal_count(len(observations)),
    )
    reason_codes = _row_reason_codes(
        max_claim_age_seconds=max(claim_ages, default=_ZERO),
        max_update_latency_seconds=max(update_latencies, default=_ZERO),
        max_corroboration_delay_seconds=max(corroboration_delays, default=_ZERO),
        stale_contradiction_pressure=stale_pressure,
        manual_escalation_urgency=manual_urgency,
        config=config,
    )
    return ResearchSourceClaimTimelinessScoreRow(
        source_class=source_class,
        claim_count=_decimal_count(len(observations)),
        average_claim_age_seconds=_average(claim_ages),
        max_claim_age_seconds=max(claim_ages, default=_ZERO),
        average_update_latency_seconds=_average(update_latencies),
        max_update_latency_seconds=max(update_latencies, default=_ZERO),
        average_corroboration_delay_seconds=_average(corroboration_delays),
        max_corroboration_delay_seconds=max(corroboration_delays, default=_ZERO),
        stale_contradiction_pressure=stale_pressure,
        manual_escalation_urgency=manual_urgency,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    max_claim_age_seconds: Decimal,
    max_update_latency_seconds: Decimal,
    max_corroboration_delay_seconds: Decimal,
    stale_contradiction_pressure: Decimal,
    manual_escalation_urgency: Decimal,
    config: ResearchSourceClaimTimelinessScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        prefix="claim_age",
        value=max_claim_age_seconds,
        watch_threshold=config.watch_claim_age_seconds,
        block_threshold=config.block_claim_age_seconds,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="update_latency",
        value=max_update_latency_seconds,
        watch_threshold=config.watch_update_latency_seconds,
        block_threshold=config.block_update_latency_seconds,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="corroboration_delay",
        value=max_corroboration_delay_seconds,
        watch_threshold=config.watch_corroboration_delay_seconds,
        block_threshold=config.block_corroboration_delay_seconds,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="stale_contradiction_pressure",
        value=stale_contradiction_pressure,
        watch_threshold=config.watch_stale_contradiction_pressure,
        block_threshold=config.block_stale_contradiction_pressure,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="manual_escalation_urgency",
        value=manual_escalation_urgency,
        watch_threshold=config.watch_manual_escalation_urgency,
        block_threshold=config.block_manual_escalation_urgency,
    )
    if not reason_codes:
        reason_codes.append("source_class_timeliness_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value >= watch_threshold:
        reason_codes.append(f"{prefix}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceClaimTimelinessScoreRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimTimelinessScoreRow, ...],
) -> tuple[str, ...]:
    if all(row.status == "pass" for row in rows):
        return ("source_class_timeliness_pass",)
    return _normalize_reason_codes(
        tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != "source_class_timeliness_pass"
        ),
    )


def _status_count(rows: tuple[ResearchSourceClaimTimelinessScoreRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _claim_age_seconds(
    observation: ResearchSourceClaimTimelinessObservation,
    generated_at: datetime,
) -> Decimal:
    return _elapsed_seconds(observation.claim_observed_at, generated_at)


def _corroboration_delay_seconds(
    observation: ResearchSourceClaimTimelinessObservation,
    generated_at: datetime,
) -> Decimal:
    if observation.corroborated_at is None:
        return _elapsed_seconds(observation.claim_observed_at, generated_at)
    return _elapsed_seconds(observation.claim_observed_at, observation.corroborated_at)


def _elapsed_seconds(started_at: datetime, ended_at: datetime) -> Decimal:
    elapsed = ended_at - started_at
    if elapsed.days < 0:
        raise ValueError("elapsed seconds must be nonnegative")
    elapsed_microseconds = (
        ((elapsed.days * 86400) + elapsed.seconds) * 1000000
    ) + elapsed.microseconds
    return _quantize(Decimal(elapsed_microseconds) / Decimal("1000000"))


def _validate_row_consistency(row: ResearchSourceClaimTimelinessScoreRow) -> None:
    if row.average_claim_age_seconds > row.max_claim_age_seconds:
        raise ValueError("average_claim_age_seconds must not exceed max_claim_age_seconds")
    if row.average_update_latency_seconds > row.max_update_latency_seconds:
        raise ValueError(
            "average_update_latency_seconds must not exceed max_update_latency_seconds",
        )
    if row.average_corroboration_delay_seconds > row.max_corroboration_delay_seconds:
        raise ValueError(
            "average_corroboration_delay_seconds must not exceed "
            "max_corroboration_delay_seconds",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchSourceClaimTimelinessScoreReport) -> None:
    _reject_empty_rows(report.rows)
    if report.source_class_count != _decimal_count(len(report.rows)):
        raise ValueError("source_class_count must match rows")
    if report.claim_count != sum((row.claim_count for row in report.rows), _ZERO):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_claim_age_seconds != _weighted_average_claim_age(report.rows):
        raise ValueError("average_claim_age_seconds must match rows")
    if report.max_update_latency_seconds != max(
        (row.max_update_latency_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_update_latency_seconds must match rows")
    if report.max_corroboration_delay_seconds != max(
        (row.max_corroboration_delay_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_corroboration_delay_seconds must match rows")
    if report.max_stale_contradiction_pressure != max(
        (row.stale_contradiction_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_stale_contradiction_pressure must match rows")
    if report.max_manual_escalation_urgency != max(
        (row.manual_escalation_urgency for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_manual_escalation_urgency must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    source_classes = tuple(row.source_class for row in report.rows)
    if len(source_classes) != len(set(source_classes)):
        raise ValueError("rows must contain unique source_class values")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.source_class)):
        raise ValueError("rows must be deterministic")


def _weighted_average_claim_age(
    rows: tuple[ResearchSourceClaimTimelinessScoreRow, ...],
) -> Decimal:
    total_count = sum((row.claim_count for row in rows), _ZERO)
    if total_count == _ZERO:
        return _ZERO
    weighted_total = sum(
        (row.average_claim_age_seconds * row.claim_count for row in rows),
        _ZERO,
    )
    return _quantize(weighted_total / total_count)


def _normalize_observations(
    observations: Sequence[ResearchSourceClaimTimelinessObservation],
) -> tuple[ResearchSourceClaimTimelinessObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceClaimTimelinessObservation] = []
    for item in observations:
        if type(item) is not ResearchSourceClaimTimelinessObservation:
            raise ValueError(
                "observations must contain ResearchSourceClaimTimelinessObservation values",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.source_class,
                item.claim_observed_at,
                item.source_updated_at,
                item.corroborated_at or item.claim_observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimTimelinessScoreRow],
) -> tuple[ResearchSourceClaimTimelinessScoreRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimTimelinessScoreRow] = []
    for row in rows:
        if type(row) is not ResearchSourceClaimTimelinessScoreRow:
            raise ValueError("rows must contain ResearchSourceClaimTimelinessScoreRow values")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.source_class))


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
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _reject_empty_observations(
    observations: tuple[ResearchSourceClaimTimelinessObservation, ...],
) -> None:
    if not observations:
        raise ValueError("observations must not be empty")


def _reject_empty_rows(rows: tuple[ResearchSourceClaimTimelinessScoreRow, ...]) -> None:
    if not rows:
        raise ValueError("rows must not be empty")


def _reject_future_time(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_watch_before_block(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value < watch_value:
        raise ValueError(f"block_{field_name} must be greater than or equal to watch")


def _require_decimal(field_name: str, value: object) -> Decimal:
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return value.quantize(_COUNT_QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchSourceClaimTimelinessScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = True,
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_TIMELINESS_SCORE_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceClaimTimelinessObservation",
    "ResearchSourceClaimTimelinessScoreConfig",
    "ResearchSourceClaimTimelinessScoreReport",
    "ResearchSourceClaimTimelinessScoreRow",
    "build_research_source_claim_timeliness_score_report",
    "research_source_claim_timeliness_score_report_payload",
)
