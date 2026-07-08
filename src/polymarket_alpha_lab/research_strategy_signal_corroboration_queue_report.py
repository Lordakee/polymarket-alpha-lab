"""Pure public signal corroboration queue reporting."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchStrategySignalCorroborationQueueConfig",
    "ResearchStrategySignalCorroborationQueueInput",
    "ResearchStrategySignalCorroborationQueueReasonCodeCount",
    "ResearchStrategySignalCorroborationQueueReport",
    "ResearchStrategySignalCorroborationQueueRow",
    "build_research_strategy_signal_corroboration_queue_report",
    "research_strategy_signal_corroboration_queue_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-signal-corroboration-queue-v0"
STATUSES = ("pass", "watch", "block")
QUEUE_ACTIONS = {
    "pass": "retain_public_summary",
    "watch": "queue_public_corroboration",
    "block": "hold_for_public_corroboration",
}
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DIGEST_LENGTH = 64


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategySignalCorroborationQueueConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_evidence_score: Decimal = Decimal("0.800000")
    stale_evidence_score: Decimal = Decimal("0.400000")
    reliable_source_score: Decimal = Decimal("0.800000")
    low_source_score: Decimal = Decimal("0.400000")
    aligned_team_dispersion: Decimal = Decimal("0.200000")
    dispersed_team_threshold: Decimal = Decimal("0.600000")
    evidence_freshness_weight: Decimal = Decimal("0.250000")
    source_reliability_weight: Decimal = Decimal("0.250000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    team_confidence_dispersion_weight: Decimal = Decimal("0.150000")
    cost_input_quality_weight: Decimal = Decimal("0.100000")
    watch_queue_pressure: Decimal = Decimal("0.350000")
    block_queue_pressure: Decimal = Decimal("0.650000")
    block_contradiction_pressure: Decimal = Decimal("0.850000")
    min_cost_input_quality: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalCorroborationQueueConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "fresh_evidence_score",
            "stale_evidence_score",
            "reliable_source_score",
            "low_source_score",
            "aligned_team_dispersion",
            "dispersed_team_threshold",
            "evidence_freshness_weight",
            "source_reliability_weight",
            "contradiction_pressure_weight",
            "team_confidence_dispersion_weight",
            "cost_input_quality_weight",
            "watch_queue_pressure",
            "block_queue_pressure",
            "block_contradiction_pressure",
            "min_cost_input_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_evidence_score <= self.stale_evidence_score:
            raise ValueError("fresh_evidence_score must exceed stale_evidence_score")
        if self.reliable_source_score <= self.low_source_score:
            raise ValueError("reliable_source_score must exceed low_source_score")
        if self.aligned_team_dispersion >= self.dispersed_team_threshold:
            raise ValueError(
                "aligned_team_dispersion must be below dispersed_team_threshold",
            )
        if self.watch_queue_pressure >= self.block_queue_pressure:
            raise ValueError("watch_queue_pressure must be below block_queue_pressure")
        weight_sum = _quantize(
            self.evidence_freshness_weight
            + self.source_reliability_weight
            + self.contradiction_pressure_weight
            + self.team_confidence_dispersion_weight
            + self.cost_input_quality_weight,
        )
        if weight_sum != ONE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalCorroborationQueueInput:
    public_signal_label: str
    aggregate_evidence_freshness: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    team_confidence_dispersion: Decimal
    cost_input_quality: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalCorroborationQueueInput, "input")
        _require_public_label("public_signal_label", self.public_signal_label)
        for field_name in (
            "aggregate_evidence_freshness",
            "source_reliability",
            "contradiction_pressure",
            "team_confidence_dispersion",
            "cost_input_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySignalCorroborationQueueRow:
    public_signal_label: str
    aggregate_evidence_freshness: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    team_confidence_dispersion: Decimal
    cost_input_quality: Decimal
    evidence_staleness_pressure: Decimal
    source_reliability_pressure: Decimal
    team_dispersion_pressure: Decimal
    cost_input_pressure: Decimal
    queue_pressure_score: Decimal
    queue_status: str
    queue_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalCorroborationQueueRow, "row")
        _require_public_label("public_signal_label", self.public_signal_label)
        for field_name in (
            "aggregate_evidence_freshness",
            "source_reliability",
            "contradiction_pressure",
            "team_confidence_dispersion",
            "cost_input_quality",
            "evidence_staleness_pressure",
            "source_reliability_pressure",
            "team_dispersion_pressure",
            "cost_input_pressure",
            "queue_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("queue_status", self.queue_status)
        _require_action(self.queue_status, self.queue_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategySignalCorroborationQueueReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySignalCorroborationQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategySignalCorroborationQueueReport:
    generated_at: datetime
    config_version: str
    status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_queue_pressure_score: Decimal | None
    max_contradiction_pressure: Decimal | None
    min_cost_input_quality: Decimal | None
    rows: tuple[ResearchStrategySignalCorroborationQueueRow, ...]
    reason_code_counts: tuple[ResearchStrategySignalCorroborationQueueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    queue_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalCorroborationQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_queue_pressure_score",
            "max_contradiction_pressure",
            "min_cost_input_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_report_payload(self, include_digest=False))
        if self.queue_digest == "":
            object.__setattr__(self, "queue_digest", expected_digest)
        elif self.queue_digest != expected_digest:
            raise ValueError("queue_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_signal_corroboration_queue_report_payload(self)


def build_research_strategy_signal_corroboration_queue_report(
    signals: Iterable[object],
    *,
    config: ResearchStrategySignalCorroborationQueueConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategySignalCorroborationQueueReport:
    cfg = config or ResearchStrategySignalCorroborationQueueConfig()
    if type(cfg) is not ResearchStrategySignalCorroborationQueueConfig:
        raise ValueError(
            "config must be a ResearchStrategySignalCorroborationQueueConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_signal_inputs(signals)
    rows = tuple(
        sorted(
            (_row_from_signal(signal, config=cfg) for signal in input_rows),
            key=lambda row: row.public_signal_label,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategySignalCorroborationQueueReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_summary_status(rows),
        signal_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_queue_pressure_score=_average_optional(
            tuple(row.queue_pressure_score for row in rows),
        ),
        max_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=None,
        ),
        min_cost_input_quality=min((row.cost_input_quality for row in rows), default=None),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_signal_corroboration_queue_report_payload(
    report: ResearchStrategySignalCorroborationQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySignalCorroborationQueueReport:
        raise ValueError("report must be a ResearchStrategySignalCorroborationQueueReport")
    _require_hard_flags("report", report)
    payload = _report_payload(report, include_digest=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_signal(
    signal: ResearchStrategySignalCorroborationQueueInput,
    *,
    config: ResearchStrategySignalCorroborationQueueConfig,
) -> ResearchStrategySignalCorroborationQueueRow:
    evidence_staleness_pressure = _inverse_unit(signal.aggregate_evidence_freshness)
    source_reliability_pressure = _inverse_unit(signal.source_reliability)
    team_dispersion_pressure = signal.team_confidence_dispersion
    cost_input_pressure = _inverse_unit(signal.cost_input_quality)
    queue_pressure_score = _queue_pressure_score(
        evidence_staleness_pressure=evidence_staleness_pressure,
        source_reliability_pressure=source_reliability_pressure,
        contradiction_pressure=signal.contradiction_pressure,
        team_dispersion_pressure=team_dispersion_pressure,
        cost_input_pressure=cost_input_pressure,
        config=config,
    )
    queue_status = _queue_status(
        signal,
        queue_pressure_score=queue_pressure_score,
        config=config,
    )
    return ResearchStrategySignalCorroborationQueueRow(
        public_signal_label=signal.public_signal_label,
        aggregate_evidence_freshness=signal.aggregate_evidence_freshness,
        source_reliability=signal.source_reliability,
        contradiction_pressure=signal.contradiction_pressure,
        team_confidence_dispersion=signal.team_confidence_dispersion,
        cost_input_quality=signal.cost_input_quality,
        evidence_staleness_pressure=evidence_staleness_pressure,
        source_reliability_pressure=source_reliability_pressure,
        team_dispersion_pressure=team_dispersion_pressure,
        cost_input_pressure=cost_input_pressure,
        queue_pressure_score=queue_pressure_score,
        queue_status=queue_status,
        queue_action=QUEUE_ACTIONS[queue_status],
        reason_codes=_row_reason_codes(
            signal,
            queue_status=queue_status,
            config=config,
        ),
    )


def _queue_pressure_score(
    *,
    evidence_staleness_pressure: Decimal,
    source_reliability_pressure: Decimal,
    contradiction_pressure: Decimal,
    team_dispersion_pressure: Decimal,
    cost_input_pressure: Decimal,
    config: ResearchStrategySignalCorroborationQueueConfig,
) -> Decimal:
    return _quantize(
        (evidence_staleness_pressure * config.evidence_freshness_weight)
        + (source_reliability_pressure * config.source_reliability_weight)
        + (contradiction_pressure * config.contradiction_pressure_weight)
        + (team_dispersion_pressure * config.team_confidence_dispersion_weight)
        + (cost_input_pressure * config.cost_input_quality_weight),
    )


def _queue_status(
    signal: ResearchStrategySignalCorroborationQueueInput,
    *,
    queue_pressure_score: Decimal,
    config: ResearchStrategySignalCorroborationQueueConfig,
) -> str:
    if signal.contradiction_pressure >= config.block_contradiction_pressure:
        return "block"
    if signal.cost_input_quality < config.min_cost_input_quality:
        return "block"
    if queue_pressure_score >= config.block_queue_pressure:
        return "block"
    if queue_pressure_score >= config.watch_queue_pressure:
        return "watch"
    if signal.aggregate_evidence_freshness <= config.stale_evidence_score:
        return "watch"
    if signal.source_reliability <= config.low_source_score:
        return "watch"
    if signal.team_confidence_dispersion >= config.dispersed_team_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    signal: ResearchStrategySignalCorroborationQueueInput,
    *,
    queue_status: str,
    config: ResearchStrategySignalCorroborationQueueConfig,
) -> tuple[str, ...]:
    reason_codes = {f"signal_corroboration_{queue_status}"}
    if signal.aggregate_evidence_freshness >= config.fresh_evidence_score:
        reason_codes.add("fresh_aggregate_evidence")
    elif signal.aggregate_evidence_freshness <= config.stale_evidence_score:
        reason_codes.add("stale_aggregate_evidence")
    else:
        reason_codes.add("aging_aggregate_evidence")
    if signal.source_reliability >= config.reliable_source_score:
        reason_codes.add("reliable_source_support")
    elif signal.source_reliability <= config.low_source_score:
        reason_codes.add("low_source_reliability")
    else:
        reason_codes.add("mixed_source_reliability")
    if signal.contradiction_pressure >= config.block_contradiction_pressure:
        reason_codes.add("contradiction_pressure_block")
    elif signal.contradiction_pressure >= config.watch_queue_pressure:
        reason_codes.add("contradiction_pressure_watch")
    else:
        reason_codes.add("contradiction_pressure_low")
    if signal.team_confidence_dispersion <= config.aligned_team_dispersion:
        reason_codes.add("team_confidence_aligned")
    elif signal.team_confidence_dispersion >= config.dispersed_team_threshold:
        reason_codes.add("team_confidence_dispersed")
    else:
        reason_codes.add("team_confidence_mixed")
    reason_codes.add(
        "cost_inputs_usable"
        if signal.cost_input_quality >= config.min_cost_input_quality
        else "cost_inputs_low_quality",
    )
    for reason_code in signal.upstream_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_signal_inputs(
    signals: Iterable[object],
) -> tuple[ResearchStrategySignalCorroborationQueueInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        values = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    return tuple(_coerce_signal_input(value) for value in values)


def _coerce_signal_input(value: object) -> ResearchStrategySignalCorroborationQueueInput:
    if type(value) is ResearchStrategySignalCorroborationQueueInput:
        _require_hard_flags("input", value)
        return value
    _reject_raw_id_fields(value)
    _require_hard_flags("input", value)
    return ResearchStrategySignalCorroborationQueueInput(
        public_signal_label=_field_value(value, "public_signal_label"),
        aggregate_evidence_freshness=_field_value(
            value,
            "aggregate_evidence_freshness",
        ),
        source_reliability=_field_value(value, "source_reliability"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        team_confidence_dispersion=_field_value(
            value,
            "team_confidence_dispersion",
        ),
        cost_input_quality=_field_value(value, "cost_input_quality"),
        upstream_reason_codes=_field_value(value, "upstream_reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategySignalCorroborationQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_signal_corroboration_inputs",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(
    rows: tuple[ResearchStrategySignalCorroborationQueueRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.queue_status == "block" for row in rows):
        return "block"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategySignalCorroborationQueueRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategySignalCorroborationQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySignalCorroborationQueueReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategySignalCorroborationQueueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchStrategySignalCorroborationQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.queue_status == status)


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _report_payload(
    report: ResearchStrategySignalCorroborationQueueReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if include_digest:
        payload["queue_digest"] = report.queue_digest
    else:
        payload.pop("queue_digest", None)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _reject_raw_id_fields(value: object) -> None:
    for field_name in _raw_id_field_names():
        if _field_value(value, field_name, default=None) is not None:
            raise ValueError("raw identifier fields are not allowed")


def _raw_id_field_names() -> tuple[str, ...]:
    return (
        "event" + "_id",
        "market" + "_id",
        "market" + "_slug",
        "source" + "_id",
        "source" + "_reference",
    )


def _blocked_public_terms() -> tuple[str, ...]:
    return (
        *_raw_id_field_names(),
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmend",
        "posi" + "tion",
        "tr" + "ade",
        "or" + "der",
    )


def _inverse_unit(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_unit_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_unit_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(term in lowered for term in _blocked_public_terms()):
        raise ValueError(f"{field_name} must avoid unsafe public terms")
    if ":" in value or "/" in value or "\\" in value:
        raise ValueError(f"{field_name} must avoid unsafe public terms")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value != value.lower() or not value.replace("_", "").isalnum():
        raise ValueError(f"{field_name} must contain lowercase reason codes")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_action(status: str, value: object) -> None:
    expected = QUEUE_ACTIONS[status]
    if value != expected:
        raise ValueError("queue_action must match queue_status")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise TypeError(f"{label} must be exactly {type_.__name__}")


def _normalize_rows(
    rows: tuple[ResearchStrategySignalCorroborationQueueRow, ...],
) -> tuple[ResearchStrategySignalCorroborationQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategySignalCorroborationQueueRow:
            raise ValueError(
                "rows must contain ResearchStrategySignalCorroborationQueueRow values",
            )
        _require_hard_flags("row", row)
    expected = tuple(sorted(rows, key=lambda row: row.public_signal_label))
    if rows != expected:
        raise ValueError("rows must be sorted by public_signal_label")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategySignalCorroborationQueueReasonCodeCount, ...],
) -> tuple[ResearchStrategySignalCorroborationQueueReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategySignalCorroborationQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySignalCorroborationQueueReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchStrategySignalCorroborationQueueRow,
) -> None:
    if row.evidence_staleness_pressure != _inverse_unit(row.aggregate_evidence_freshness):
        raise ValueError("evidence_staleness_pressure must match freshness")
    if row.source_reliability_pressure != _inverse_unit(row.source_reliability):
        raise ValueError("source_reliability_pressure must match reliability")
    if row.team_dispersion_pressure != row.team_confidence_dispersion:
        raise ValueError("team_dispersion_pressure must match dispersion")
    if row.cost_input_pressure != _inverse_unit(row.cost_input_quality):
        raise ValueError("cost_input_pressure must match cost_input_quality")
    expected_score = _quantize(
        (row.evidence_staleness_pressure * Decimal("0.250000"))
        + (row.source_reliability_pressure * Decimal("0.250000"))
        + (row.contradiction_pressure * Decimal("0.250000"))
        + (row.team_dispersion_pressure * Decimal("0.150000"))
        + (row.cost_input_pressure * Decimal("0.100000")),
    )
    if row.queue_pressure_score != expected_score:
        raise ValueError("queue_pressure_score must match pressure inputs")
    if f"signal_corroboration_{row.queue_status}" not in row.reason_codes:
        raise ValueError("reason_codes must match queue_status")


def _validate_report_consistency(
    report: ResearchStrategySignalCorroborationQueueReport,
) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.average_queue_pressure_score != _average_optional(
        tuple(row.queue_pressure_score for row in report.rows),
    ):
        raise ValueError("average_queue_pressure_score must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=None,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.min_cost_input_quality != min(
        (row.cost_input_quality for row in report.rows),
        default=None,
    ):
        raise ValueError("min_cost_input_quality must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
