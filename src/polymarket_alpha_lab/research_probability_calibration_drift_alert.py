"""Pure report-only probability calibration drift alert reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_PROBABILITY_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION = (
    "probability-calibration-drift-alert-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_THREE = Decimal("3.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ALERT_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "source",
    "market_id",
    "condition_id",
    "slug",
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
)
_REASON_CODE_SEQUENCE = (
    "probability_calibration_drift_pass",
    "probability_calibration_drift_watch",
    "probability_calibration_drift_block",
    "max_pairwise_drift_watch",
    "max_pairwise_drift_block",
    "model_team_drift_watch",
    "model_team_drift_block",
    "team_domain_drift_watch",
    "team_domain_drift_block",
    "market_model_drift_watch",
    "market_model_drift_block",
    "consensus_market_drift_watch",
    "consensus_market_drift_block",
)


@dataclass(frozen=True)
class ProbabilityCalibrationDriftAlertConfig:
    config_version: str = DEFAULT_PROBABILITY_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION
    max_pairwise_watch_threshold: Decimal = Decimal("0.100000")
    max_pairwise_block_threshold: Decimal = Decimal("0.200000")
    model_team_watch_threshold: Decimal = Decimal("0.075000")
    model_team_block_threshold: Decimal = Decimal("0.200000")
    team_domain_watch_threshold: Decimal = Decimal("0.075000")
    team_domain_block_threshold: Decimal = Decimal("0.200000")
    market_model_watch_threshold: Decimal = Decimal("0.100000")
    market_model_block_threshold: Decimal = Decimal("0.250000")
    consensus_market_watch_threshold: Decimal = Decimal("0.080000")
    consensus_market_block_threshold: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityCalibrationDriftAlertConfig:
            raise TypeError(
                "ProbabilityCalibrationDriftAlertConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityCalibrationDriftAlertConfig:
            raise ValueError(
                "config must be exactly ProbabilityCalibrationDriftAlertConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PROBABILITY_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pairwise_watch_threshold",
            "max_pairwise_block_threshold",
            "model_team_watch_threshold",
            "model_team_block_threshold",
            "team_domain_watch_threshold",
            "team_domain_block_threshold",
            "market_model_watch_threshold",
            "market_model_block_threshold",
            "consensus_market_watch_threshold",
            "consensus_market_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "max_pairwise",
            self.max_pairwise_watch_threshold,
            self.max_pairwise_block_threshold,
        )
        _require_threshold_order(
            "model_team",
            self.model_team_watch_threshold,
            self.model_team_block_threshold,
        )
        _require_threshold_order(
            "team_domain",
            self.team_domain_watch_threshold,
            self.team_domain_block_threshold,
        )
        _require_threshold_order(
            "market_model",
            self.market_model_watch_threshold,
            self.market_model_block_threshold,
        )
        _require_threshold_order(
            "consensus_market",
            self.consensus_market_watch_threshold,
            self.consensus_market_block_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ProbabilityCalibrationDriftAlertSample:
    sample_key: str
    observed_at: datetime
    model_probability: Decimal
    team_probability: Decimal
    domain_probability: Decimal
    market_implied_probability: Decimal
    model_confidence: Decimal
    team_confidence: Decimal
    domain_confidence: Decimal
    market_depth_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityCalibrationDriftAlertSample:
            raise TypeError(
                "ProbabilityCalibrationDriftAlertSample does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityCalibrationDriftAlertSample:
            raise ValueError(
                "sample must be exactly ProbabilityCalibrationDriftAlertSample",
            )
        _require_public_identifier("sample_key", self.sample_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "team_probability",
            "domain_probability",
            "market_implied_probability",
            "model_confidence",
            "team_confidence",
            "domain_confidence",
            "market_depth_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("sample", self)
        _reject_unsafe_public_payload("sample", self)


@dataclass(frozen=True)
class ProbabilityCalibrationDriftAlertRow:
    sample_key: str
    observed_at: datetime
    model_probability: Decimal
    team_probability: Decimal
    domain_probability: Decimal
    market_implied_probability: Decimal
    model_team_drift: Decimal
    model_domain_drift: Decimal
    team_domain_drift: Decimal
    market_model_drift: Decimal
    market_team_drift: Decimal
    market_domain_drift: Decimal
    consensus_market_drift: Decimal
    max_pairwise_drift: Decimal
    confidence_weighted_drift_score: Decimal
    alert_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityCalibrationDriftAlertRow:
            raise TypeError(
                "ProbabilityCalibrationDriftAlertRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityCalibrationDriftAlertRow:
            raise ValueError("row must be exactly ProbabilityCalibrationDriftAlertRow")
        _require_public_identifier("sample_key", self.sample_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "team_probability",
            "domain_probability",
            "market_implied_probability",
            "model_team_drift",
            "model_domain_drift",
            "team_domain_drift",
            "market_model_drift",
            "market_team_drift",
            "market_domain_drift",
            "consensus_market_drift",
            "max_pairwise_drift",
            "confidence_weighted_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_alert_status("alert_status", self.alert_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ProbabilityCalibrationDriftAlertReport:
    generated_at: datetime
    config_version: str
    alert_status: str
    sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_drift_score: Decimal
    max_drift_score: Decimal
    rows: tuple[ProbabilityCalibrationDriftAlertRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityCalibrationDriftAlertReport:
            raise TypeError(
                "ProbabilityCalibrationDriftAlertReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityCalibrationDriftAlertReport:
            raise ValueError(
                "report must be exactly ProbabilityCalibrationDriftAlertReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PROBABILITY_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_alert_status("alert_status", self.alert_status)
        for field_name in ("sample_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_drift_score", "max_drift_score"):
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
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ProbabilityCalibrationDriftAlertReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_probability_calibration_drift_alert_report(
    samples: Sequence[ProbabilityCalibrationDriftAlertSample],
    *,
    generated_at: datetime,
    config: ProbabilityCalibrationDriftAlertConfig | None = None,
) -> ProbabilityCalibrationDriftAlertReport:
    """Build a local report-only probability calibration drift alert snapshot."""

    if config is None:
        config = ProbabilityCalibrationDriftAlertConfig()
    if type(config) is not ProbabilityCalibrationDriftAlertConfig:
        raise ValueError("config must be a ProbabilityCalibrationDriftAlertConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_samples = _normalize_samples(samples)
    for sample in normalized_samples:
        if sample.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_samples, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "alert_status": _report_status(rows),
        "sample_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_drift_score": _average(
            tuple(row.confidence_weighted_drift_score for row in rows),
        ),
        "max_drift_score": max(
            (row.confidence_weighted_drift_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityCalibrationDriftAlertReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    samples: tuple[ProbabilityCalibrationDriftAlertSample, ...],
    config: ProbabilityCalibrationDriftAlertConfig,
) -> tuple[ProbabilityCalibrationDriftAlertRow, ...]:
    return tuple(_row_for_sample(sample, config) for sample in samples)


def _row_for_sample(
    sample: ProbabilityCalibrationDriftAlertSample,
    config: ProbabilityCalibrationDriftAlertConfig,
) -> ProbabilityCalibrationDriftAlertRow:
    model_team_drift = _gap(sample.model_probability, sample.team_probability)
    model_domain_drift = _gap(sample.model_probability, sample.domain_probability)
    team_domain_drift = _gap(sample.team_probability, sample.domain_probability)
    market_model_drift = _gap(
        sample.market_implied_probability,
        sample.model_probability,
    )
    market_team_drift = _gap(sample.market_implied_probability, sample.team_probability)
    market_domain_drift = _gap(
        sample.market_implied_probability,
        sample.domain_probability,
    )
    max_pairwise_drift = max(
        model_team_drift,
        model_domain_drift,
        team_domain_drift,
        market_model_drift,
        market_team_drift,
        market_domain_drift,
    )
    consensus_market_drift = _consensus_market_drift(sample)
    status = _row_status(
        config,
        max_pairwise_drift=max_pairwise_drift,
        model_team_drift=model_team_drift,
        team_domain_drift=team_domain_drift,
        market_model_drift=market_model_drift,
        consensus_market_drift=consensus_market_drift,
    )
    return ProbabilityCalibrationDriftAlertRow(
        sample_key=sample.sample_key,
        observed_at=sample.observed_at,
        model_probability=sample.model_probability,
        team_probability=sample.team_probability,
        domain_probability=sample.domain_probability,
        market_implied_probability=sample.market_implied_probability,
        model_team_drift=model_team_drift,
        model_domain_drift=model_domain_drift,
        team_domain_drift=team_domain_drift,
        market_model_drift=market_model_drift,
        market_team_drift=market_team_drift,
        market_domain_drift=market_domain_drift,
        consensus_market_drift=consensus_market_drift,
        max_pairwise_drift=max_pairwise_drift,
        confidence_weighted_drift_score=_confidence_weighted_drift_score(
            sample,
            model_team_drift=model_team_drift,
            model_domain_drift=model_domain_drift,
            team_domain_drift=team_domain_drift,
            market_model_drift=market_model_drift,
            market_team_drift=market_team_drift,
            market_domain_drift=market_domain_drift,
        ),
        alert_status=status,
        reason_codes=_row_reason_codes(
            config,
            alert_status=status,
            max_pairwise_drift=max_pairwise_drift,
            model_team_drift=model_team_drift,
            team_domain_drift=team_domain_drift,
            market_model_drift=market_model_drift,
            consensus_market_drift=consensus_market_drift,
        ),
    )


def _row_status(
    config: ProbabilityCalibrationDriftAlertConfig,
    *,
    max_pairwise_drift: Decimal,
    model_team_drift: Decimal,
    team_domain_drift: Decimal,
    market_model_drift: Decimal,
    consensus_market_drift: Decimal,
) -> str:
    if (
        max_pairwise_drift >= config.max_pairwise_block_threshold
        or model_team_drift >= config.model_team_block_threshold
        or team_domain_drift >= config.team_domain_block_threshold
        or market_model_drift >= config.market_model_block_threshold
        or consensus_market_drift >= config.consensus_market_block_threshold
    ):
        return "block"
    if (
        max_pairwise_drift >= config.max_pairwise_watch_threshold
        or model_team_drift >= config.model_team_watch_threshold
        or team_domain_drift >= config.team_domain_watch_threshold
        or market_model_drift >= config.market_model_watch_threshold
        or consensus_market_drift >= config.consensus_market_watch_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    config: ProbabilityCalibrationDriftAlertConfig,
    *,
    alert_status: str,
    max_pairwise_drift: Decimal,
    model_team_drift: Decimal,
    team_domain_drift: Decimal,
    market_model_drift: Decimal,
    consensus_market_drift: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"probability_calibration_drift_{alert_status}"]
    _append_threshold_reason(
        reason_codes,
        "max_pairwise_drift",
        max_pairwise_drift,
        config.max_pairwise_watch_threshold,
        config.max_pairwise_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "model_team_drift",
        model_team_drift,
        config.model_team_watch_threshold,
        config.model_team_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "team_domain_drift",
        team_domain_drift,
        config.team_domain_watch_threshold,
        config.team_domain_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "market_model_drift",
        market_model_drift,
        config.market_model_watch_threshold,
        config.market_model_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "consensus_market_drift",
        consensus_market_drift,
        config.consensus_market_watch_threshold,
        config.consensus_market_block_threshold,
    )
    return _normalize_reason_codes(tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reason_codes.append(f"{label}_block")
    elif value >= watch_threshold:
        reason_codes.append(f"{label}_watch")


def _consensus_market_drift(sample: ProbabilityCalibrationDriftAlertSample) -> Decimal:
    consensus = _quantize(
        (
            sample.model_probability
            + sample.team_probability
            + sample.domain_probability
        )
        / _THREE,
    )
    return _gap(consensus, sample.market_implied_probability)


def _confidence_weighted_drift_score(
    sample: ProbabilityCalibrationDriftAlertSample,
    *,
    model_team_drift: Decimal,
    model_domain_drift: Decimal,
    team_domain_drift: Decimal,
    market_model_drift: Decimal,
    market_team_drift: Decimal,
    market_domain_drift: Decimal,
) -> Decimal:
    weighted_pairs = (
        (model_team_drift, _average_pair(sample.model_confidence, sample.team_confidence)),
        (
            model_domain_drift,
            _average_pair(sample.model_confidence, sample.domain_confidence),
        ),
        (
            team_domain_drift,
            _average_pair(sample.team_confidence, sample.domain_confidence),
        ),
        (
            market_model_drift,
            _average_pair(sample.market_depth_score, sample.model_confidence),
        ),
        (
            market_team_drift,
            _average_pair(sample.market_depth_score, sample.team_confidence),
        ),
        (
            market_domain_drift,
            _average_pair(sample.market_depth_score, sample.domain_confidence),
        ),
    )
    weight_sum = sum((weight for _, weight in weighted_pairs), _ZERO)
    if weight_sum <= _ZERO:
        return _ZERO
    numerator = sum((drift * weight for drift, weight in weighted_pairs), _ZERO)
    return _clamp_ratio(numerator / weight_sum)


def _average_pair(left: Decimal, right: Decimal) -> Decimal:
    return _quantize((left + right) / _TWO)


def _gap(left_probability: Decimal, right_probability: Decimal) -> Decimal:
    return _quantize(abs(left_probability - right_probability))


def _report_status(rows: tuple[ProbabilityCalibrationDriftAlertRow, ...]) -> str:
    if not rows:
        return "pass"
    return max((row.alert_status for row in rows), key=lambda status: _STATUS_RANK[status])


def _report_reason_codes(
    rows: tuple[ProbabilityCalibrationDriftAlertRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("probability_calibration_drift_pass",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ProbabilityCalibrationDriftAlertRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.alert_status == status)


def _normalize_samples(
    samples: Sequence[ProbabilityCalibrationDriftAlertSample],
) -> tuple[ProbabilityCalibrationDriftAlertSample, ...]:
    if isinstance(samples, (str, bytes)) or not isinstance(samples, Sequence):
        raise ValueError("samples must be a sequence")
    normalized: list[ProbabilityCalibrationDriftAlertSample] = []
    seen: set[str] = set()
    for sample in samples:
        if type(sample) is not ProbabilityCalibrationDriftAlertSample:
            raise ValueError("sample must be exactly ProbabilityCalibrationDriftAlertSample")
        if sample.sample_key in seen:
            raise ValueError("sample_key must be unique")
        seen.add(sample.sample_key)
        normalized.append(sample)
    return tuple(sorted(normalized, key=lambda sample: sample.sample_key))


def _normalize_rows(
    rows: object,
) -> tuple[ProbabilityCalibrationDriftAlertRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ProbabilityCalibrationDriftAlertRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ProbabilityCalibrationDriftAlertRow:
            raise ValueError("rows must contain ProbabilityCalibrationDriftAlertRow")
        if row.sample_key in seen:
            raise ValueError("row sample_key must be unique")
        seen.add(row.sample_key)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=lambda row: row.sample_key))
    if sorted_rows != rows:
        raise ValueError("rows must be sorted by sample_key")
    return sorted_rows


def _validate_report_consistency(report: ProbabilityCalibrationDriftAlertReport) -> None:
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.alert_status != _report_status(report.rows):
        raise ValueError("alert_status must match rows")
    if report.average_drift_score != _average(
        tuple(row.confidence_weighted_drift_score for row in report.rows),
    ):
        raise ValueError("average_drift_score must match rows")
    if report.max_drift_score != max(
        (row.confidence_weighted_drift_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_drift_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_threshold_order(
    label: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _require_alert_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _ALERT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


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
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ProbabilityCalibrationDriftAlertReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
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


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path} has unsafe public value")


__all__ = (
    "DEFAULT_PROBABILITY_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION",
    "ProbabilityCalibrationDriftAlertConfig",
    "ProbabilityCalibrationDriftAlertReport",
    "ProbabilityCalibrationDriftAlertRow",
    "ProbabilityCalibrationDriftAlertSample",
    "build_probability_calibration_drift_alert_report",
)
