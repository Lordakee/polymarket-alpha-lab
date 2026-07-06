"""Pure Phase 1 report reducer for cross-domain signal divergence gating."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any


DEFAULT_STRATEGY_CROSS_DOMAIN_SIGNAL_DIVERGENCE_GATE_V2_CONFIG_VERSION = (
    "strategy-cross-domain-signal-divergence-gate-v2-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_REDACTED_SOURCE_REFERENCE = "<redacted-source-reference>"
_DERIVED_VALIDATION_DIGEST_PREFIX = "scdsdgv2-v0:"
_PASS_REASON = "cross_domain_consensus_lift_pass"
_EMPTY_REASON = "strategy_cross_domain_signal_divergence_gate_v2_empty"
_ROW_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_REASON_RANK = {
    "cross_domain_domain_coverage_low": 0,
    "cross_domain_probability_divergence_high": 1,
    "cross_domain_expected_edge_divergence_high": 2,
    "cross_domain_consensus_lift_low": 3,
}
_ROW_REASON_CODES = tuple(_REASON_RANK) + (_PASS_REASON,)
_REPORT_REASON_CODES = _ROW_REASON_CODES + (_EMPTY_REASON,)
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "secret",
        "token",
        "private",
        "password",
        "credential",
        "api_key",
        "private_key",
    ),
)


@dataclass(frozen=True)
class StrategyCrossDomainSignalDivergenceGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CROSS_DOMAIN_SIGNAL_DIVERGENCE_GATE_V2_CONFIG_VERSION
    )
    max_probability_spread: Decimal = Decimal("0.200000")
    max_expected_edge_spread: Decimal = Decimal("0.050000")
    min_consensus_lift: Decimal = Decimal("0.050000")
    min_domain_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_probability_spread",
            _normalize_ratio("max_probability_spread", self.max_probability_spread),
        )
        object.__setattr__(
            self,
            "max_expected_edge_spread",
            _normalize_nonnegative_decimal(
                "max_expected_edge_spread",
                self.max_expected_edge_spread,
            ),
        )
        object.__setattr__(
            self,
            "min_consensus_lift",
            _normalize_decimal("min_consensus_lift", self.min_consensus_lift),
        )
        object.__setattr__(
            self,
            "min_domain_count",
            _normalize_count("min_domain_count", self.min_domain_count),
        )
        if self.min_domain_count <= _ZERO:
            raise ValueError("min_domain_count must be positive")
        if self.max_expected_edge_spread <= _ZERO:
            raise ValueError("max_expected_edge_spread must be positive")
        _require_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyCrossDomainSignalDivergenceGateV2Signal:
    condition_id: str
    domain_id: str
    forecast_probability: Decimal
    expected_edge: Decimal
    confidence: Decimal
    observed_at: datetime
    source_reference: str = _REDACTED_SOURCE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("condition_id", self.condition_id)
        _require_public_text("domain_id", self.domain_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_ratio("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "expected_edge",
            _normalize_decimal("expected_edge", self.expected_edge),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_ratio("confidence", self.confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_text("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", _REDACTED_SOURCE_REFERENCE)
        _require_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class StrategyCrossDomainSignalDivergenceGateV2Row:
    condition_id: str
    row_status: str
    domain_count: Decimal
    minimum_forecast_probability: Decimal
    maximum_forecast_probability: Decimal
    average_forecast_probability: Decimal
    cross_domain_probability_spread: Decimal
    minimum_expected_edge: Decimal
    maximum_expected_edge: Decimal
    cross_domain_expected_edge_spread: Decimal
    confidence_weighted_probability: Decimal
    consensus_lift: Decimal
    divergence_score: Decimal
    latest_observed_at: datetime
    source_references: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("condition_id", self.condition_id)
        _require_row_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "domain_count",
            _normalize_count("domain_count", self.domain_count),
        )
        for name in (
            "minimum_forecast_probability",
            "maximum_forecast_probability",
            "average_forecast_probability",
            "cross_domain_probability_spread",
            "confidence_weighted_probability",
            "divergence_score",
        ):
            object.__setattr__(self, name, _normalize_ratio(name, getattr(self, name)))
        for name in (
            "minimum_expected_edge",
            "maximum_expected_edge",
            "consensus_lift",
        ):
            object.__setattr__(self, name, _normalize_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "cross_domain_expected_edge_spread",
            _normalize_nonnegative_decimal(
                "cross_domain_expected_edge_spread",
                self.cross_domain_expected_edge_spread,
            ),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        object.__setattr__(self, "reason_codes", _normalize_row_reasons(self.reason_codes))
        _validate_row(self)
        object.__setattr__(self, "derived_validation_digest", _row_validation_digest(self))
        _require_row_validation_digest(self)
        _require_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyCrossDomainSignalDivergenceGateV2Report:
    generated_at: datetime
    config_version: str
    condition_count: Decimal
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    consensus_lift_condition_count: Decimal
    consensus_lift_condition_ratio: Decimal | None
    gate_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCrossDomainSignalDivergenceGateV2Row, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for name in (
            "condition_count",
            "signal_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "consensus_lift_condition_count",
        ):
            object.__setattr__(self, name, _normalize_count(name, getattr(self, name)))
        if self.consensus_lift_condition_ratio is not None:
            object.__setattr__(
                self,
                "consensus_lift_condition_ratio",
                _normalize_ratio(
                    "consensus_lift_condition_ratio",
                    self.consensus_lift_condition_ratio,
                ),
            )
        _require_row_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reasons(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        object.__setattr__(
            self,
            "derived_validation_digest",
            _report_validation_digest(self),
        )
        _require_report_validation_digest(self)
        _require_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_strategy_cross_domain_signal_divergence_gate_v2(
    signals: object,
    *,
    config: StrategyCrossDomainSignalDivergenceGateV2Config,
    generated_at: datetime,
) -> StrategyCrossDomainSignalDivergenceGateV2Report:
    if type(config) is not StrategyCrossDomainSignalDivergenceGateV2Config:
        raise ValueError(
            "config must be a StrategyCrossDomainSignalDivergenceGateV2Config",
        )
    _require_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _condition_row(
                    condition_id,
                    condition_signals,
                    config=config,
                    generated_at=generated_at,
                )
                for condition_id, condition_signals in _group_signals(normalized_signals)
            ),
            key=_row_key,
        ),
    )
    condition_count = _count(len(rows))
    consensus_lift_condition_count = _row_count(rows, "pass")

    return StrategyCrossDomainSignalDivergenceGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        condition_count=condition_count,
        signal_count=_count(len(normalized_signals)),
        pass_count=_row_count(rows, "pass"),
        watch_count=_row_count(rows, "watch"),
        blocked_count=_row_count(rows, "blocked"),
        consensus_lift_condition_count=consensus_lift_condition_count,
        consensus_lift_condition_ratio=(
            None
            if condition_count == _ZERO
            else _ratio(consensus_lift_condition_count, condition_count)
        ),
        gate_status=_report_status(rows),
        reason_codes=_report_reasons(rows),
        rows=rows,
    )


def strategy_cross_domain_signal_divergence_gate_v2_payload(
    report: StrategyCrossDomainSignalDivergenceGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        _require_payload_flags("payload", payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is not StrategyCrossDomainSignalDivergenceGateV2Report:
        raise ValueError(
            "report must be a StrategyCrossDomainSignalDivergenceGateV2Report",
        )
    _require_flags("report", report)
    _validate_report(report)
    _require_report_validation_digest(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags("report payload", payload)
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _condition_row(
    condition_id: str,
    signals: tuple[StrategyCrossDomainSignalDivergenceGateV2Signal, ...],
    *,
    config: StrategyCrossDomainSignalDivergenceGateV2Config,
    generated_at: datetime,
) -> StrategyCrossDomainSignalDivergenceGateV2Row:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    probabilities = tuple(signal.forecast_probability for signal in signals)
    expected_edges = tuple(signal.expected_edge for signal in signals)
    confidences = tuple(signal.confidence for signal in signals)
    domain_count = _count(len(signals))
    minimum_forecast_probability = min(probabilities)
    maximum_forecast_probability = max(probabilities)
    average_forecast_probability = _ratio(sum(probabilities, _ZERO), domain_count)
    probability_spread = _quantize(
        maximum_forecast_probability - minimum_forecast_probability,
    )
    minimum_expected_edge = min(expected_edges)
    maximum_expected_edge = max(expected_edges)
    expected_edge_spread = _quantize(maximum_expected_edge - minimum_expected_edge)
    confidence_sum = sum(confidences, _ZERO)
    confidence_weighted_probability = (
        average_forecast_probability
        if confidence_sum == _ZERO
        else _ratio(
            sum(
                (
                    signal.forecast_probability * signal.confidence
                    for signal in signals
                ),
                _ZERO,
            ),
            confidence_sum,
        )
    )
    consensus_lift = _quantize(
        confidence_weighted_probability - average_forecast_probability,
    )
    divergence_score = _capped_ratio(probability_spread + expected_edge_spread)
    reasons = _row_reasons(
        domain_count=domain_count,
        probability_spread=probability_spread,
        expected_edge_spread=expected_edge_spread,
        consensus_lift=consensus_lift,
        config=config,
    )

    return StrategyCrossDomainSignalDivergenceGateV2Row(
        condition_id=condition_id,
        row_status=_row_status(reasons),
        domain_count=domain_count,
        minimum_forecast_probability=minimum_forecast_probability,
        maximum_forecast_probability=maximum_forecast_probability,
        average_forecast_probability=average_forecast_probability,
        cross_domain_probability_spread=probability_spread,
        minimum_expected_edge=minimum_expected_edge,
        maximum_expected_edge=maximum_expected_edge,
        cross_domain_expected_edge_spread=expected_edge_spread,
        confidence_weighted_probability=confidence_weighted_probability,
        consensus_lift=consensus_lift,
        divergence_score=divergence_score,
        latest_observed_at=max(signal.observed_at for signal in signals),
        source_references=tuple(sorted({signal.source_reference for signal in signals})),
        reason_codes=reasons,
    )


def _normalize_signals(
    signals: object,
) -> tuple[StrategyCrossDomainSignalDivergenceGateV2Signal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategyCrossDomainSignalDivergenceGateV2Signal:
            raise ValueError(
                "signals must contain StrategyCrossDomainSignalDivergenceGateV2Signal",
            )
        _require_flags("signal", item)
        _reject_unsafe_public_payload("signal", item)
        key = (item.condition_id, item.domain_id)
        if key in seen:
            raise ValueError("signals must contain unique condition and domain values")
        seen.add(key)
    return items


def _group_signals(
    signals: tuple[StrategyCrossDomainSignalDivergenceGateV2Signal, ...],
) -> tuple[tuple[str, tuple[StrategyCrossDomainSignalDivergenceGateV2Signal, ...]], ...]:
    condition_ids = tuple(sorted({signal.condition_id for signal in signals}))
    return tuple(
        (
            condition_id,
            tuple(
                sorted(
                    (
                        signal
                        for signal in signals
                        if signal.condition_id == condition_id
                    ),
                    key=lambda signal: signal.domain_id,
                ),
            ),
        )
        for condition_id in condition_ids
    )


def _row_reasons(
    *,
    domain_count: Decimal,
    probability_spread: Decimal,
    expected_edge_spread: Decimal,
    consensus_lift: Decimal,
    config: StrategyCrossDomainSignalDivergenceGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if domain_count < config.min_domain_count:
        reasons.append("cross_domain_domain_coverage_low")
    if probability_spread > config.max_probability_spread:
        reasons.append("cross_domain_probability_divergence_high")
    if expected_edge_spread > config.max_expected_edge_spread:
        reasons.append("cross_domain_expected_edge_divergence_high")
    if not reasons and consensus_lift < config.min_consensus_lift:
        reasons.append("cross_domain_consensus_lift_low")
    if not reasons:
        return (_PASS_REASON,)
    return tuple(sorted(reasons, key=_reason_key))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    blocking_reasons = {
        "cross_domain_domain_coverage_low",
        "cross_domain_probability_divergence_high",
        "cross_domain_expected_edge_divergence_high",
    }
    if any(reason in blocking_reasons for reason in reason_codes):
        return "blocked"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[StrategyCrossDomainSignalDivergenceGateV2Row, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reasons(
    rows: tuple[StrategyCrossDomainSignalDivergenceGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reasons = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason != _PASS_REASON
            },
            key=_reason_key,
        ),
    )
    if reasons:
        return reasons
    return (_PASS_REASON,)


def _row_count(
    rows: tuple[StrategyCrossDomainSignalDivergenceGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == status))


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCrossDomainSignalDivergenceGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyCrossDomainSignalDivergenceGateV2Row:
            raise ValueError(
                "rows must contain StrategyCrossDomainSignalDivergenceGateV2Row",
            )
        _require_flags("row", row)
        _require_row_validation_digest(row)
        _reject_unsafe_public_payload("row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_source_references(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("source_references must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("source_references must be an iterable") from exc
    if not items:
        raise ValueError("source_references must not be empty")
    for item in items:
        _require_text("source_reference", item)
    return tuple(dict.fromkeys(_REDACTED_SOURCE_REFERENCE for _ in items))


def _normalize_row_reasons(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reasons = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reasons:
        raise ValueError("reason_codes must include at least one code")
    for reason in reasons:
        _require_reason_code("reason_code", reason, _ROW_REASON_CODES)
    if _PASS_REASON in reasons and reasons != (_PASS_REASON,):
        raise ValueError("pass reason_codes must stand alone")
    if tuple(sorted(dict.fromkeys(reasons), key=_reason_key)) != reasons:
        raise ValueError("reason_codes must use deterministic sequence")
    return reasons


def _normalize_report_reasons(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reasons = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reasons:
        raise ValueError("reason_codes must include at least one code")
    for reason in reasons:
        _require_reason_code("reason_code", reason, _REPORT_REASON_CODES)
    summary_codes = {_EMPTY_REASON, _PASS_REASON}
    if any(reason in summary_codes for reason in reasons) and len(reasons) != 1:
        raise ValueError("reason_codes summary code must stand alone")
    if tuple(sorted(dict.fromkeys(reasons), key=_reason_key)) != reasons:
        raise ValueError("reason_codes must use deterministic sequence")
    return reasons


def _validate_row(row: StrategyCrossDomainSignalDivergenceGateV2Row) -> None:
    if row.domain_count <= _ZERO:
        raise ValueError("domain_count must be positive")
    if row.minimum_forecast_probability > row.maximum_forecast_probability:
        raise ValueError("minimum_forecast_probability must not exceed maximum")
    if row.minimum_expected_edge > row.maximum_expected_edge:
        raise ValueError("minimum_expected_edge must not exceed maximum")
    if row.cross_domain_probability_spread != _quantize(
        row.maximum_forecast_probability - row.minimum_forecast_probability,
    ):
        raise ValueError("cross_domain_probability_spread must match min and max")
    if row.cross_domain_expected_edge_spread != _quantize(
        row.maximum_expected_edge - row.minimum_expected_edge,
    ):
        raise ValueError("cross_domain_expected_edge_spread must match min and max")
    if not (
        row.minimum_forecast_probability
        <= row.average_forecast_probability
        <= row.maximum_forecast_probability
    ):
        raise ValueError("average_forecast_probability must be between min and max")
    if not (
        row.minimum_forecast_probability
        <= row.confidence_weighted_probability
        <= row.maximum_forecast_probability
    ):
        raise ValueError("confidence_weighted_probability must be between min and max")
    if row.divergence_score != _capped_ratio(
        row.cross_domain_probability_spread + row.cross_domain_expected_edge_spread,
    ):
        raise ValueError("divergence_score must match derived validation")
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report(report: StrategyCrossDomainSignalDivergenceGateV2Report) -> None:
    for row in report.rows:
        _require_flags("row", row)
        _require_row_validation_digest(row)
    if report.condition_count != _count(len(report.rows)):
        raise ValueError("condition_count must match rows")
    if report.signal_count != sum((row.domain_count for row in report.rows), _ZERO):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _row_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _row_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.consensus_lift_condition_count != report.pass_count:
        raise ValueError("consensus_lift_condition_count must match pass rows")
    if report.condition_count == _ZERO:
        if report.consensus_lift_condition_ratio is not None:
            raise ValueError("empty reports must not set consensus_lift_condition_ratio")
    elif report.consensus_lift_condition_ratio != _ratio(
        report.consensus_lift_condition_count,
        report.condition_count,
    ):
        raise ValueError("consensus_lift_condition_ratio must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.condition_count:
        raise ValueError("condition status counts must match rows")
    if any(row.latest_observed_at > report.generated_at for row in report.rows):
        raise ValueError("latest_observed_at must not be after generated_at")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_validation_digest(row: StrategyCrossDomainSignalDivergenceGateV2Row) -> str:
    return _validation_digest(
        (
            "row",
            row.condition_id,
            row.row_status,
            row.domain_count,
            row.minimum_forecast_probability,
            row.maximum_forecast_probability,
            row.average_forecast_probability,
            row.cross_domain_probability_spread,
            row.minimum_expected_edge,
            row.maximum_expected_edge,
            row.cross_domain_expected_edge_spread,
            row.confidence_weighted_probability,
            row.consensus_lift,
            row.divergence_score,
            row.latest_observed_at,
            row.source_references,
            row.reason_codes,
            row.paper_only,
            row.report_only,
            row.readonly,
        ),
    )


def _report_validation_digest(
    report: StrategyCrossDomainSignalDivergenceGateV2Report,
) -> str:
    return _validation_digest(
        (
            "report",
            report.generated_at,
            report.config_version,
            report.condition_count,
            report.signal_count,
            report.pass_count,
            report.watch_count,
            report.blocked_count,
            report.consensus_lift_condition_count,
            report.consensus_lift_condition_ratio,
            report.gate_status,
            report.reason_codes,
            tuple(row.derived_validation_digest for row in report.rows),
            report.paper_only,
            report.report_only,
            report.readonly,
        ),
    )


def _validation_digest(parts: object) -> str:
    encoded = json.dumps(
        _digest_ready(parts),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return (
        f"{_DERIVED_VALIDATION_DIGEST_PREFIX}"
        f"{hashlib.sha256(encoded).hexdigest()}"
    )


def _require_row_validation_digest(
    row: StrategyCrossDomainSignalDivergenceGateV2Row,
) -> None:
    _require_derived_validation_digest(
        "row derived_validation_digest",
        row.derived_validation_digest,
    )
    if row.derived_validation_digest != _row_validation_digest(row):
        raise ValueError("derived_validation_digest must match")


def _require_report_validation_digest(
    report: StrategyCrossDomainSignalDivergenceGateV2Report,
) -> None:
    _require_derived_validation_digest(
        "report derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest must match")


def _require_derived_validation_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if not value.startswith(_DERIVED_VALIDATION_DIGEST_PREFIX):
        raise ValueError(f"{name} must use derived validation digest prefix")
    digest = value.removeprefix(_DERIVED_VALIDATION_DIGEST_PREFIX)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _row_key(row: StrategyCrossDomainSignalDivergenceGateV2Row) -> tuple[int, str]:
    return (_ROW_STATUS_RANK[row.row_status], row.condition_id)


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _normalize_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return value


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _capped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_text(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be a known code")


def _require_row_status(name: str, value: object) -> None:
    _require_text(name, value)
    if value not in _ROW_STATUS_RANK:
        raise ValueError(f"{name} must be pass, watch, or blocked")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_payload_flags(name: str, payload: dict[str, Any]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"{name} {flag} must be True")


def _json_ready(value: Any) -> Any:
    if _dataclass_isinstance(value):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("JSON datetime value", value).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if value is None or type(value) is bool:
        return value
    raise ValueError("value is not JSON serializable")


def _digest_ready(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("derived validation digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("derived validation digest datetime value", value).isoformat()
    if isinstance(value, tuple):
        return [_digest_ready(item) for item in value]
    if isinstance(value, list):
        return [_digest_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("derived validation digest object keys must be strings")
            ready[key] = _digest_ready(item)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("derived validation digest value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if _dataclass_isinstance(value):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload field in {label}: {nested_path}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public payload text in {label}: {path or label}")
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must use Decimal strings")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _dataclass_isinstance(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__") and not isinstance(value, type)


__all__ = (
    "DEFAULT_STRATEGY_CROSS_DOMAIN_SIGNAL_DIVERGENCE_GATE_V2_CONFIG_VERSION",
    "StrategyCrossDomainSignalDivergenceGateV2Config",
    "StrategyCrossDomainSignalDivergenceGateV2Report",
    "StrategyCrossDomainSignalDivergenceGateV2Row",
    "StrategyCrossDomainSignalDivergenceGateV2Signal",
    "build_strategy_cross_domain_signal_divergence_gate_v2",
    "strategy_cross_domain_signal_divergence_gate_v2_payload",
)
