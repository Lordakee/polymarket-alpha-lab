"""Report-only aggregate liquidity capacity readiness gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_LIQUIDITY_CAPACITY_GATE_CONFIG_VERSION = (
    "research-market-liquidity-capacity-gate-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUS_PRIORITY = {"block": 0, "watch": 1, "pass": 2}
_UNSAFE_PUBLIC_TERMS = (
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


@dataclass(frozen=True)
class ResearchMarketLiquidityCapacityGateConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_LIQUIDITY_CAPACITY_GATE_CONFIG_VERSION
    max_pass_spread_pressure: Decimal = Decimal("0.030000")
    max_watch_spread_pressure: Decimal = Decimal("0.070000")
    min_pass_book_depth_score: Decimal = Decimal("0.800000")
    min_watch_book_depth_score: Decimal = Decimal("0.500000")
    max_pass_fee_friction: Decimal = Decimal("0.015000")
    max_watch_fee_friction: Decimal = Decimal("0.040000")
    max_pass_settlement_friction: Decimal = Decimal("0.020000")
    max_watch_settlement_friction: Decimal = Decimal("0.060000")
    min_evidence_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCapacityGateConfig:
            raise TypeError(
                "ResearchMarketLiquidityCapacityGateConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityCapacityGateConfig:
            raise ValueError(
                "config must be exactly ResearchMarketLiquidityCapacityGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_CAPACITY_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_spread_pressure",
            "max_watch_spread_pressure",
            "min_pass_book_depth_score",
            "min_watch_book_depth_score",
            "max_pass_fee_friction",
            "max_watch_fee_friction",
            "max_pass_settlement_friction",
            "max_watch_settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_evidence_count",
            _require_positive_count_decimal(
                "min_evidence_count",
                self.min_evidence_count,
            ),
        )
        _validate_config_thresholds(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCapacityObservation:
    market_slug: str
    observed_at: datetime
    spread_pressure: Decimal
    book_depth_score: Decimal
    fee_friction: Decimal
    settlement_friction: Decimal
    evidence_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCapacityObservation:
            raise TypeError(
                "ResearchMarketLiquidityCapacityObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityCapacityObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketLiquidityCapacityObservation",
            )
        _require_public_identifier("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_pressure",
            "book_depth_score",
            "fee_friction",
            "settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_count_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCapacityRow:
    market_slug: str
    observed_at: datetime
    spread_pressure: Decimal
    book_depth_score: Decimal
    fee_friction: Decimal
    settlement_friction: Decimal
    evidence_count: Decimal
    readiness_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCapacityRow:
            raise TypeError(
                "ResearchMarketLiquidityCapacityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityCapacityRow:
            raise ValueError("row must be exactly ResearchMarketLiquidityCapacityRow")
        _require_public_identifier("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_pressure",
            "book_depth_score",
            "fee_friction",
            "settlement_friction",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_count_decimal("evidence_count", self.evidence_count),
        )
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCapacityGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    max_spread_pressure: Decimal
    min_book_depth_score: Decimal
    max_fee_friction: Decimal
    max_settlement_friction: Decimal
    rows: tuple[ResearchMarketLiquidityCapacityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCapacityGateReport:
            raise TypeError(
                "ResearchMarketLiquidityCapacityGateReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityCapacityGateReport:
            raise ValueError(
                "report must be exactly ResearchMarketLiquidityCapacityGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_CAPACITY_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "market_count",
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
            "average_readiness_score",
            "max_spread_pressure",
            "min_book_depth_score",
            "max_fee_friction",
            "max_settlement_friction",
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
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchMarketLiquidityCapacityGateReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_market_liquidity_capacity_gate_report(
    observations: Sequence[ResearchMarketLiquidityCapacityObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketLiquidityCapacityGateConfig | None = None,
) -> ResearchMarketLiquidityCapacityGateReport:
    """Build a local report-only aggregate liquidity capacity readiness report."""

    if config is None:
        config = ResearchMarketLiquidityCapacityGateConfig()
    if type(config) is not ResearchMarketLiquidityCapacityGateConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityCapacityGateConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_observation(item, config) for item in normalized_observations),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": _report_status(rows),
        "market_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_readiness_score": _average(
            tuple(row.readiness_score for row in rows),
        ),
        "max_spread_pressure": max(
            (row.spread_pressure for row in rows),
            default=_ZERO,
        ),
        "min_book_depth_score": min(
            (row.book_depth_score for row in rows),
            default=_ZERO,
        ),
        "max_fee_friction": max((row.fee_friction for row in rows), default=_ZERO),
        "max_settlement_friction": max(
            (row.settlement_friction for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketLiquidityCapacityGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_from_observation(
    observation: ResearchMarketLiquidityCapacityObservation,
    config: ResearchMarketLiquidityCapacityGateConfig,
) -> ResearchMarketLiquidityCapacityRow:
    readiness_score = _readiness_score(
        spread_pressure=observation.spread_pressure,
        book_depth_score=observation.book_depth_score,
        fee_friction=observation.fee_friction,
        settlement_friction=observation.settlement_friction,
    )
    reason_codes = _row_reason_codes(observation, config)
    return ResearchMarketLiquidityCapacityRow(
        market_slug=observation.market_slug,
        observed_at=observation.observed_at,
        spread_pressure=observation.spread_pressure,
        book_depth_score=observation.book_depth_score,
        fee_friction=observation.fee_friction,
        settlement_friction=observation.settlement_friction,
        evidence_count=observation.evidence_count,
        readiness_score=readiness_score,
        gate_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchMarketLiquidityCapacityObservation,
    config: ResearchMarketLiquidityCapacityGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(observation.reason_codes)
    if observation.evidence_count < config.min_evidence_count:
        reason_codes.append("insufficient_evidence")
        return _normalize_reason_codes(tuple(reason_codes))
    reason_codes.append(
        _spread_reason_code(
            observation.spread_pressure,
            pass_threshold=config.max_pass_spread_pressure,
            watch_threshold=config.max_watch_spread_pressure,
        ),
    )
    reason_codes.append(
        _book_depth_reason_code(
            observation.book_depth_score,
            pass_threshold=config.min_pass_book_depth_score,
            watch_threshold=config.min_watch_book_depth_score,
        ),
    )
    reason_codes.append(
        _fee_reason_code(
            observation.fee_friction,
            pass_threshold=config.max_pass_fee_friction,
            watch_threshold=config.max_watch_fee_friction,
        ),
    )
    reason_codes.append(
        _settlement_reason_code(
            observation.settlement_friction,
            pass_threshold=config.max_pass_settlement_friction,
            watch_threshold=config.max_watch_settlement_friction,
        ),
    )
    if not any(reason_code.endswith(("_watch", "_block")) for reason_code in reason_codes):
        reason_codes.append("capacity_gate_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _spread_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "spread_pressure_pass"
    if value <= watch_threshold:
        return "spread_pressure_watch"
    return "spread_pressure_block"


def _book_depth_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return "book_depth_sufficient"
    if value >= watch_threshold:
        return "book_depth_watch"
    return "book_depth_block"


def _fee_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "fee_friction_pass"
    if value <= watch_threshold:
        return "fee_friction_watch"
    return "fee_friction_block"


def _settlement_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "settlement_friction_pass"
    if value <= watch_threshold:
        return "settlement_friction_watch"
    return "settlement_friction_block"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "insufficient_evidence" in reason_codes:
        return "block"
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _readiness_score(
    *,
    spread_pressure: Decimal,
    book_depth_score: Decimal,
    fee_friction: Decimal,
    settlement_friction: Decimal,
) -> Decimal:
    return _average(
        (
            _clamp_ratio(_ONE - spread_pressure),
            book_depth_score,
            _clamp_ratio(_ONE - fee_friction),
            _clamp_ratio(_ONE - settlement_friction),
        ),
    )


def _report_status(rows: tuple[ResearchMarketLiquidityCapacityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityCapacityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchMarketLiquidityCapacityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _row_sort_key(
    row: ResearchMarketLiquidityCapacityRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        _STATUS_PRIORITY[row.gate_status],
        row.readiness_score,
        -row.spread_pressure,
        row.market_slug,
    )


def _validate_config_thresholds(
    config: ResearchMarketLiquidityCapacityGateConfig,
) -> None:
    if config.max_pass_spread_pressure > config.max_watch_spread_pressure:
        raise ValueError("max_pass_spread_pressure must not exceed watch threshold")
    if config.min_pass_book_depth_score < config.min_watch_book_depth_score:
        raise ValueError("min_pass_book_depth_score must cover watch threshold")
    if config.max_pass_fee_friction > config.max_watch_fee_friction:
        raise ValueError("max_pass_fee_friction must not exceed watch threshold")
    if config.max_pass_settlement_friction > config.max_watch_settlement_friction:
        raise ValueError("max_pass_settlement_friction must not exceed watch threshold")


def _validate_row_consistency(row: ResearchMarketLiquidityCapacityRow) -> None:
    expected_readiness_score = _readiness_score(
        spread_pressure=row.spread_pressure,
        book_depth_score=row.book_depth_score,
        fee_friction=row.fee_friction,
        settlement_friction=row.settlement_friction,
    )
    if row.readiness_score != expected_readiness_score:
        raise ValueError("readiness_score must match friction and depth inputs")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.gate_status == "pass" and "capacity_gate_pass" not in row.reason_codes:
        raise ValueError("pass rows must include capacity_gate_pass")


def _validate_report_consistency(
    report: ResearchMarketLiquidityCapacityGateReport,
) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.max_spread_pressure != max(
        (row.spread_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_spread_pressure must match rows")
    if report.min_book_depth_score != min(
        (row.book_depth_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_book_depth_score must match rows")
    if report.max_fee_friction != max(
        (row.fee_friction for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_fee_friction must match rows")
    if report.max_settlement_friction != max(
        (row.settlement_friction for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_settlement_friction must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchMarketLiquidityCapacityObservation],
) -> tuple[ResearchMarketLiquidityCapacityObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchMarketLiquidityCapacityObservation] = []
    for item in observations:
        if type(item) is not ResearchMarketLiquidityCapacityObservation:
            raise ValueError(
                "observations must contain ResearchMarketLiquidityCapacityObservation",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.market_slug,
                item.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchMarketLiquidityCapacityRow],
) -> tuple[ResearchMarketLiquidityCapacityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketLiquidityCapacityRow] = []
    for row in rows:
        if type(row) is not ResearchMarketLiquidityCapacityRow:
            raise ValueError("rows must contain ResearchMarketLiquidityCapacityRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_gate_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
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
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchMarketLiquidityCapacityGateReport,
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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_CAPACITY_GATE_CONFIG_VERSION",
    "ResearchMarketLiquidityCapacityGateConfig",
    "ResearchMarketLiquidityCapacityGateReport",
    "ResearchMarketLiquidityCapacityObservation",
    "ResearchMarketLiquidityCapacityRow",
    "build_research_market_liquidity_capacity_gate_report",
)
