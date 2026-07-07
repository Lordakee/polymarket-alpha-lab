"""Report-only microstructure warning snapshot for Polymarket research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_WARNING_CONFIG_VERSION = (
    "research-market-microstructure-warning-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_WARNING_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "wallet",
    "network",
    "database",
    "persist",
    "mutation",
    "order",
    "buy",
    "sell",
    "trade",
    "position",
    "recommend",
)
_REASON_CODE_SEQUENCE = (
    "depth_insufficient",
    "spread_abnormal",
    "book_skew",
    "fee_friction",
    "near_settlement_liquidity_risk",
    "microstructure_pass",
)


@dataclass(frozen=True)
class ResearchMarketMicrostructureWarningConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_WARNING_CONFIG_VERSION
    min_available_depth: Decimal = Decimal("1000.000000")
    max_spread_width: Decimal = Decimal("0.050000")
    min_book_balance_ratio: Decimal = Decimal("0.200000")
    max_book_balance_ratio: Decimal = Decimal("0.800000")
    max_fee_to_edge_ratio: Decimal = Decimal("0.350000")
    near_settlement_minutes_threshold: Decimal = Decimal("120.000000")
    block_warning_count_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureWarningConfig:
            raise TypeError(
                "ResearchMarketMicrostructureWarningConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureWarningConfig:
            raise ValueError(
                "config must be exactly ResearchMarketMicrostructureWarningConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_WARNING_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_available_depth",
            "near_settlement_minutes_threshold",
            "block_warning_count_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_width",
            "min_book_balance_ratio",
            "max_book_balance_ratio",
            "max_fee_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_book_balance_ratio >= self.max_book_balance_ratio:
            raise ValueError("min_book_balance_ratio must be below max_book_balance_ratio")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureObservation:
    observed_at: datetime
    available_depth: Decimal
    spread_width: Decimal
    book_balance_ratio: Decimal
    fee_to_edge_ratio: Decimal
    minutes_to_settlement: Decimal
    research_reviewed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureObservation:
            raise TypeError(
                "ResearchMarketMicrostructureObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureObservation:
            raise ValueError(
                "observation must be exactly ResearchMarketMicrostructureObservation",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "available_depth",
            "minutes_to_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_width",
            "book_balance_ratio",
            "fee_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("research_reviewed", self.research_reviewed)
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureWarningRow:
    sequence_number: Decimal
    observed_at: datetime
    available_depth: Decimal
    spread_width: Decimal
    book_balance_ratio: Decimal
    fee_to_edge_ratio: Decimal
    minutes_to_settlement: Decimal
    warning_status: str
    warning_count: Decimal
    depth_insufficient: bool
    spread_abnormal: bool
    book_skew: bool
    fee_friction: bool
    near_settlement_liquidity_risk: bool
    research_reviewed: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureWarningRow:
            raise TypeError(
                "ResearchMarketMicrostructureWarningRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureWarningRow:
            raise ValueError("row must be exactly ResearchMarketMicrostructureWarningRow")
        object.__setattr__(
            self,
            "sequence_number",
            _require_positive_decimal("sequence_number", self.sequence_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "available_depth",
            "minutes_to_settlement",
            "warning_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_width",
            "book_balance_ratio",
            "fee_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("warning_status", self.warning_status)
        for field_name in (
            "depth_insufficient",
            "spread_abnormal",
            "book_skew",
            "fee_friction",
            "near_settlement_liquidity_risk",
            "research_reviewed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketMicrostructureWarningReport:
    generated_at: datetime
    config_version: str
    warning_status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    insufficient_depth_count: Decimal
    abnormal_spread_count: Decimal
    book_skew_count: Decimal
    fee_friction_count: Decimal
    near_settlement_liquidity_risk_count: Decimal
    max_warning_count: Decimal
    min_available_depth: Decimal
    max_spread_width: Decimal
    max_fee_to_edge_ratio: Decimal
    min_minutes_to_settlement: Decimal
    rows: tuple[ResearchMarketMicrostructureWarningRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMicrostructureWarningReport:
            raise TypeError(
                "ResearchMarketMicrostructureWarningReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketMicrostructureWarningReport:
            raise ValueError(
                "report must be exactly ResearchMarketMicrostructureWarningReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_WARNING_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("warning_status", self.warning_status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "insufficient_depth_count",
            "abnormal_spread_count",
            "book_skew_count",
            "fee_friction_count",
            "near_settlement_liquidity_risk_count",
            "max_warning_count",
            "min_available_depth",
            "min_minutes_to_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_spread_width", "max_fee_to_edge_ratio"):
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
            "ResearchMarketMicrostructureWarningReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_market_microstructure_warning_report(
    observations: Sequence[ResearchMarketMicrostructureObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketMicrostructureWarningConfig | None = None,
) -> ResearchMarketMicrostructureWarningReport:
    """Build a local report-only market microstructure warning snapshot."""

    if config is None:
        config = ResearchMarketMicrostructureWarningConfig()
    if type(config) is not ResearchMarketMicrostructureWarningConfig:
        raise ValueError(
            "config must be a ResearchMarketMicrostructureWarningConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "warning_status": _report_status(rows),
        "observation_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "insufficient_depth_count": _flag_total(rows, "depth_insufficient"),
        "abnormal_spread_count": _flag_total(rows, "spread_abnormal"),
        "book_skew_count": _flag_total(rows, "book_skew"),
        "fee_friction_count": _flag_total(rows, "fee_friction"),
        "near_settlement_liquidity_risk_count": _flag_total(
            rows,
            "near_settlement_liquidity_risk",
        ),
        "max_warning_count": _max_decimal(row.warning_count for row in rows),
        "min_available_depth": _min_decimal(row.available_depth for row in rows),
        "max_spread_width": _max_decimal(row.spread_width for row in rows),
        "max_fee_to_edge_ratio": _max_decimal(row.fee_to_edge_ratio for row in rows),
        "min_minutes_to_settlement": _min_decimal(
            (row.minutes_to_settlement for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketMicrostructureWarningReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchMarketMicrostructureObservation, ...],
    config: ResearchMarketMicrostructureWarningConfig,
) -> tuple[ResearchMarketMicrostructureWarningRow, ...]:
    rows: list[ResearchMarketMicrostructureWarningRow] = []
    for index, observation in enumerate(observations, start=1):
        depth_insufficient = observation.available_depth < config.min_available_depth
        spread_abnormal = observation.spread_width > config.max_spread_width
        book_skew = (
            observation.book_balance_ratio < config.min_book_balance_ratio
            or observation.book_balance_ratio > config.max_book_balance_ratio
        )
        fee_friction = observation.fee_to_edge_ratio > config.max_fee_to_edge_ratio
        near_settlement_liquidity_risk = (
            observation.minutes_to_settlement <= config.near_settlement_minutes_threshold
            and depth_insufficient
        )
        reason_codes = _row_reason_codes(
            depth_insufficient=depth_insufficient,
            spread_abnormal=spread_abnormal,
            book_skew=book_skew,
            fee_friction=fee_friction,
            near_settlement_liquidity_risk=near_settlement_liquidity_risk,
        )
        warning_count = _decimal_count(len(reason_codes)) if reason_codes else _ZERO
        rows.append(
            ResearchMarketMicrostructureWarningRow(
                sequence_number=_decimal_count(index),
                observed_at=observation.observed_at,
                available_depth=observation.available_depth,
                spread_width=observation.spread_width,
                book_balance_ratio=observation.book_balance_ratio,
                fee_to_edge_ratio=observation.fee_to_edge_ratio,
                minutes_to_settlement=observation.minutes_to_settlement,
                warning_status=_row_status(warning_count, config),
                warning_count=warning_count,
                depth_insufficient=depth_insufficient,
                spread_abnormal=spread_abnormal,
                book_skew=book_skew,
                fee_friction=fee_friction,
                near_settlement_liquidity_risk=near_settlement_liquidity_risk,
                research_reviewed=observation.research_reviewed,
                reason_codes=reason_codes or ("microstructure_pass",),
            ),
        )
    return tuple(rows)


def _row_reason_codes(
    *,
    depth_insufficient: bool,
    spread_abnormal: bool,
    book_skew: bool,
    fee_friction: bool,
    near_settlement_liquidity_risk: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if depth_insufficient:
        reason_codes.append("depth_insufficient")
    if spread_abnormal:
        reason_codes.append("spread_abnormal")
    if book_skew:
        reason_codes.append("book_skew")
    if fee_friction:
        reason_codes.append("fee_friction")
    if near_settlement_liquidity_risk:
        reason_codes.append("near_settlement_liquidity_risk")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    warning_count: Decimal,
    config: ResearchMarketMicrostructureWarningConfig,
) -> str:
    if warning_count == _ZERO:
        return "pass"
    if warning_count >= config.block_warning_count_threshold:
        return "block"
    return "watch"


def _report_status(rows: tuple[ResearchMarketMicrostructureWarningRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.warning_status == "block" for row in rows):
        return "block"
    if any(row.warning_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketMicrostructureWarningRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("depth_insufficient",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code != "microstructure_pass"
        )
    if not reason_codes:
        return ("microstructure_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(row: ResearchMarketMicrostructureWarningRow) -> None:
    expected_codes = _row_reason_codes(
        depth_insufficient=row.depth_insufficient,
        spread_abnormal=row.spread_abnormal,
        book_skew=row.book_skew,
        fee_friction=row.fee_friction,
        near_settlement_liquidity_risk=row.near_settlement_liquidity_risk,
    )
    expected_warning_count = _decimal_count(len(expected_codes))
    if expected_codes:
        if row.reason_codes != expected_codes:
            raise ValueError("reason_codes must match warning flags")
    elif row.reason_codes != ("microstructure_pass",):
        raise ValueError("pass rows must include microstructure_pass")
    if row.warning_count != expected_warning_count:
        raise ValueError("warning_count must match warning flags")
    if row.warning_status == "pass" and row.warning_count != _ZERO:
        raise ValueError("pass rows must have zero warning_count")
    if row.warning_status == "block" and row.warning_count == _ZERO:
        raise ValueError("block rows must have warning_count")
    if row.near_settlement_liquidity_risk and not row.depth_insufficient:
        raise ValueError("near settlement liquidity risk requires insufficient depth")


def _validate_report_consistency(report: ResearchMarketMicrostructureWarningReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    for status_field, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, status_field) != _decimal_count(_status_count(report.rows, status)):
            raise ValueError(f"{status_field} must match rows")
    for count_field, row_field in (
        ("insufficient_depth_count", "depth_insufficient"),
        ("abnormal_spread_count", "spread_abnormal"),
        ("book_skew_count", "book_skew"),
        ("fee_friction_count", "fee_friction"),
        (
            "near_settlement_liquidity_risk_count",
            "near_settlement_liquidity_risk",
        ),
    ):
        if getattr(report, count_field) != _flag_total(report.rows, row_field):
            raise ValueError(f"{count_field} must match rows")
    if report.max_warning_count != _max_decimal(row.warning_count for row in report.rows):
        raise ValueError("max_warning_count must match rows")
    if report.min_available_depth != _min_decimal(row.available_depth for row in report.rows):
        raise ValueError("min_available_depth must match rows")
    if report.max_spread_width != _max_decimal(row.spread_width for row in report.rows):
        raise ValueError("max_spread_width must match rows")
    if report.max_fee_to_edge_ratio != _max_decimal(
        (row.fee_to_edge_ratio for row in report.rows),
    ):
        raise ValueError("max_fee_to_edge_ratio must match rows")
    if report.min_minutes_to_settlement != _min_decimal(
        (row.minutes_to_settlement for row in report.rows),
    ):
        raise ValueError("min_minutes_to_settlement must match rows")
    if report.warning_status != _report_status(report.rows):
        raise ValueError("warning_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchMarketMicrostructureObservation],
) -> tuple[ResearchMarketMicrostructureObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchMarketMicrostructureObservation] = []
    for item in observations:
        if type(item) is not ResearchMarketMicrostructureObservation:
            raise ValueError(
                "observations must contain ResearchMarketMicrostructureObservation",
            )
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketMicrostructureWarningRow],
) -> tuple[ResearchMarketMicrostructureWarningRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketMicrostructureWarningRow] = []
    for row in rows:
        if type(row) is not ResearchMarketMicrostructureWarningRow:
            raise ValueError(
                "rows must contain ResearchMarketMicrostructureWarningRow",
            )
        normalized.append(row)
    return tuple(normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _WARNING_STATUSES:
        raise ValueError(f"{field_name} must be a known warning status")
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
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


def _flag_total(
    rows: tuple[ResearchMarketMicrostructureWarningRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) is True))


def _status_count(
    rows: tuple[ResearchMarketMicrostructureWarningRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.warning_status == status)


def _max_decimal(values: Sequence[Decimal]) -> Decimal:
    return max(tuple(values), default=_ZERO)


def _min_decimal(values: Sequence[Decimal]) -> Decimal:
    return min(tuple(values), default=_ZERO)


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
    report: ResearchMarketMicrostructureWarningReport,
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
    if "market_id" in lowered or "market_slug" in lowered or "condition_id" in lowered:
        raise ValueError(f"{path}.{key} has unsafe public field")
    if "token_id" in lowered or "source" in lowered:
        raise ValueError(f"{path}.{key} has unsafe public field")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_MICROSTRUCTURE_WARNING_CONFIG_VERSION",
    "ResearchMarketMicrostructureObservation",
    "ResearchMarketMicrostructureWarningConfig",
    "ResearchMarketMicrostructureWarningReport",
    "ResearchMarketMicrostructureWarningRow",
    "build_research_market_microstructure_warning_report",
)
