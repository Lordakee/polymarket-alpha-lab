"""Public, report-only microstructure readiness gate for research escalation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_MARKET_MICROSTRUCTURE_RESEARCH_GATE_CONFIG_VERSION = (
    "research-market-microstructure-research-gate-report-v1"
)
STATUSES = ("pass", "watch", "block")

_STATUSES = frozenset(STATUSES)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "wallet",
    "private",
    "secret",
    "signature",
    "signed",
    "network",
    "database",
    "persist",
    "mutation",
    "execution",
    "live",
    "order",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "spread_watch",
    "spread_block",
    "depth_watch",
    "depth_block",
    "quote_staleness_watch",
    "quote_staleness_block",
    "liquidity_concentration_watch",
    "liquidity_concentration_block",
    "volume_burst_watch",
    "volume_burst_block",
    "fee_friction_watch",
    "fee_friction_block",
    "microstructure_research_gate_pass",
)


@dataclass(frozen=True)
class MarketMicrostructureGateConfig:
    config_version: str = DEFAULT_MARKET_MICROSTRUCTURE_RESEARCH_GATE_CONFIG_VERSION
    spread_watch_pct: Decimal = Decimal("0.050000")
    spread_block_pct: Decimal = Decimal("0.100000")
    depth_watch_threshold: Decimal = Decimal("1000.000000")
    depth_block_threshold: Decimal = Decimal("500.000000")
    quote_age_watch_seconds: Decimal = Decimal("60.000000")
    quote_age_block_seconds: Decimal = Decimal("300.000000")
    concentration_watch_share: Decimal = Decimal("0.600000")
    concentration_block_share: Decimal = Decimal("0.850000")
    volume_burst_watch_ratio: Decimal = Decimal("3.000000")
    volume_burst_block_ratio: Decimal = Decimal("7.000000")
    fee_friction_watch_pct: Decimal = Decimal("0.030000")
    fee_friction_block_pct: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMicrostructureGateConfig:
            raise TypeError("MarketMicrostructureGateConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketMicrostructureGateConfig:
            raise ValueError("config must be exactly MarketMicrostructureGateConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_MICROSTRUCTURE_RESEARCH_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "spread_watch_pct",
            "spread_block_pct",
            "depth_watch_threshold",
            "depth_block_threshold",
            "quote_age_watch_seconds",
            "quote_age_block_seconds",
            "concentration_watch_share",
            "concentration_block_share",
            "volume_burst_watch_ratio",
            "volume_burst_block_ratio",
            "fee_friction_watch_pct",
            "fee_friction_block_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_watch_pct",
            "spread_block_pct",
            "concentration_watch_share",
            "concentration_block_share",
            "fee_friction_watch_pct",
            "fee_friction_block_pct",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        if self.spread_block_pct <= self.spread_watch_pct:
            raise ValueError("spread_block_pct must exceed spread_watch_pct")
        if self.depth_watch_threshold <= self.depth_block_threshold:
            raise ValueError("depth_watch_threshold must exceed depth_block_threshold")
        if self.quote_age_block_seconds <= self.quote_age_watch_seconds:
            raise ValueError("quote_age_block_seconds must exceed quote_age_watch_seconds")
        if self.concentration_block_share <= self.concentration_watch_share:
            raise ValueError(
                "concentration_block_share must exceed concentration_watch_share",
            )
        if self.volume_burst_block_ratio <= self.volume_burst_watch_ratio:
            raise ValueError("volume_burst_block_ratio must exceed volume_burst_watch_ratio")
        if self.fee_friction_block_pct <= self.fee_friction_watch_pct:
            raise ValueError("fee_friction_block_pct must exceed fee_friction_watch_pct")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketMicrostructureInput:
    research_case_key: str
    observed_at: datetime
    spread_pct: Decimal
    top_of_book_depth: Decimal
    quote_age_seconds: Decimal
    top_liquidity_share: Decimal
    volume_burst_ratio: Decimal
    fee_friction_pct: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMicrostructureInput:
            raise TypeError("MarketMicrostructureInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketMicrostructureInput:
            raise ValueError("input must be exactly MarketMicrostructureInput")
        _require_public_identifier("research_case_key", self.research_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_pct",
            "top_of_book_depth",
            "quote_age_seconds",
            "top_liquidity_share",
            "volume_burst_ratio",
            "fee_friction_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("spread_pct", "top_liquidity_share", "fee_friction_pct"):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class MarketMicrostructureRow:
    research_case_key: str
    observed_at: datetime
    spread_pct: Decimal
    top_of_book_depth: Decimal
    quote_age_seconds: Decimal
    top_liquidity_share: Decimal
    volume_burst_ratio: Decimal
    fee_friction_pct: Decimal
    microstructure_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMicrostructureRow:
            raise TypeError("MarketMicrostructureRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketMicrostructureRow:
            raise ValueError("row must be exactly MarketMicrostructureRow")
        _require_public_identifier("research_case_key", self.research_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_pct",
            "top_of_book_depth",
            "quote_age_seconds",
            "top_liquidity_share",
            "volume_burst_ratio",
            "fee_friction_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("spread_pct", "top_liquidity_share", "fee_friction_pct"):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "microstructure_readiness_score",
            _require_ratio_decimal(
                "microstructure_readiness_score",
                self.microstructure_readiness_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketMicrostructureReport:
    generated_at: datetime
    config_version: str
    report_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    max_spread_pct: Decimal
    min_top_of_book_depth: Decimal
    max_quote_age_seconds: Decimal
    max_top_liquidity_share: Decimal
    max_volume_burst_ratio: Decimal
    max_fee_friction_pct: Decimal
    rows: tuple[MarketMicrostructureRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketMicrostructureReport:
            raise TypeError("MarketMicrostructureReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketMicrostructureReport:
            raise ValueError("report must be exactly MarketMicrostructureReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_MICROSTRUCTURE_RESEARCH_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "max_spread_pct",
            "min_top_of_book_depth",
            "max_quote_age_seconds",
            "max_top_liquidity_share",
            "max_volume_burst_ratio",
            "max_fee_friction_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal("average_readiness_score", self.average_readiness_score)
        _require_ratio_decimal("max_spread_pct", self.max_spread_pct)
        _require_ratio_decimal("max_top_liquidity_share", self.max_top_liquidity_share)
        _require_ratio_decimal("max_fee_friction_pct", self.max_fee_friction_pct)
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
        _reject_unsafe_public_payload("MarketMicrostructureReport.payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_market_microstructure_research_gate_report(
    rows: Sequence[MarketMicrostructureInput],
    *,
    generated_at: datetime,
    config: MarketMicrostructureGateConfig | None = None,
) -> MarketMicrostructureReport:
    """Build a deterministic, public-safe research escalation readiness report."""

    if config is None:
        config = MarketMicrostructureGateConfig()
    if type(config) is not MarketMicrostructureGateConfig:
        raise ValueError("config must be a MarketMicrostructureGateConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    report_rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(report_rows),
        "case_count": _decimal_count(len(report_rows)),
        "pass_count": _decimal_count(_status_count(report_rows, "pass")),
        "watch_count": _decimal_count(_status_count(report_rows, "watch")),
        "block_count": _decimal_count(_status_count(report_rows, "block")),
        "average_readiness_score": _average(
            tuple(row.microstructure_readiness_score for row in report_rows),
        ),
        "max_spread_pct": max((row.spread_pct for row in report_rows), default=_ZERO),
        "min_top_of_book_depth": min(
            (row.top_of_book_depth for row in report_rows),
            default=_ZERO,
        ),
        "max_quote_age_seconds": max(
            (row.quote_age_seconds for row in report_rows),
            default=_ZERO,
        ),
        "max_top_liquidity_share": max(
            (row.top_liquidity_share for row in report_rows),
            default=_ZERO,
        ),
        "max_volume_burst_ratio": max(
            (row.volume_burst_ratio for row in report_rows),
            default=_ZERO,
        ),
        "max_fee_friction_pct": max(
            (row.fee_friction_pct for row in report_rows),
            default=_ZERO,
        ),
        "rows": report_rows,
        "reason_codes": _report_reason_codes(report_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return MarketMicrostructureReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_input(
    item: MarketMicrostructureInput,
    config: MarketMicrostructureGateConfig,
) -> MarketMicrostructureRow:
    reason_codes = _row_reason_codes(item, config)
    status = _row_status(reason_codes)
    return MarketMicrostructureRow(
        research_case_key=item.research_case_key,
        observed_at=item.observed_at,
        spread_pct=item.spread_pct,
        top_of_book_depth=item.top_of_book_depth,
        quote_age_seconds=item.quote_age_seconds,
        top_liquidity_share=item.top_liquidity_share,
        volume_burst_ratio=item.volume_burst_ratio,
        fee_friction_pct=item.fee_friction_pct,
        microstructure_readiness_score=_readiness_score(reason_codes),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketMicrostructureInput,
    config: MarketMicrostructureGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        metric_name="spread",
        value=item.spread_pct,
        watch=config.spread_watch_pct,
        block=config.spread_block_pct,
        higher_is_worse=True,
    )
    _append_threshold_reason(
        reason_codes,
        metric_name="depth",
        value=item.top_of_book_depth,
        watch=config.depth_watch_threshold,
        block=config.depth_block_threshold,
        higher_is_worse=False,
    )
    _append_threshold_reason(
        reason_codes,
        metric_name="quote_staleness",
        value=item.quote_age_seconds,
        watch=config.quote_age_watch_seconds,
        block=config.quote_age_block_seconds,
        higher_is_worse=True,
    )
    _append_threshold_reason(
        reason_codes,
        metric_name="liquidity_concentration",
        value=item.top_liquidity_share,
        watch=config.concentration_watch_share,
        block=config.concentration_block_share,
        higher_is_worse=True,
    )
    _append_threshold_reason(
        reason_codes,
        metric_name="volume_burst",
        value=item.volume_burst_ratio,
        watch=config.volume_burst_watch_ratio,
        block=config.volume_burst_block_ratio,
        higher_is_worse=True,
    )
    _append_threshold_reason(
        reason_codes,
        metric_name="fee_friction",
        value=item.fee_friction_pct,
        watch=config.fee_friction_watch_pct,
        block=config.fee_friction_block_pct,
        higher_is_worse=True,
    )
    if not reason_codes:
        reason_codes.append("microstructure_research_gate_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    metric_name: str,
    value: Decimal,
    watch: Decimal,
    block: Decimal,
    higher_is_worse: bool,
) -> None:
    if higher_is_worse:
        if value >= block:
            reason_codes.append(f"{metric_name}_block")
            return
        if value >= watch:
            reason_codes.append(f"{metric_name}_watch")
            return
        return
    if value <= block:
        reason_codes.append(f"{metric_name}_block")
        return
    if value <= watch:
        reason_codes.append(f"{metric_name}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _readiness_score(reason_codes: tuple[str, ...]) -> Decimal:
    block_count = sum(1 for reason_code in reason_codes if reason_code.endswith("_block"))
    watch_count = sum(1 for reason_code in reason_codes if reason_code.endswith("_watch"))
    score = _ONE - Decimal("0.100000") - (Decimal(block_count) * Decimal("0.150000"))
    score -= Decimal(watch_count) * Decimal("0.050000")
    if score < _ZERO:
        return _ZERO
    return _quantize(score)


def _report_status(rows: tuple[MarketMicrostructureRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[MarketMicrostructureRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("spread_block",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[MarketMicrostructureRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    rows: Sequence[MarketMicrostructureInput],
) -> tuple[MarketMicrostructureInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[MarketMicrostructureInput] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketMicrostructureInput:
            raise ValueError("rows must contain MarketMicrostructureInput")
        if row.research_case_key in seen_keys:
            raise ValueError("research_case_key values must be unique")
        seen_keys.add(row.research_case_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.research_case_key))


def _normalize_rows(rows: Sequence[MarketMicrostructureRow]) -> tuple[MarketMicrostructureRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[MarketMicrostructureRow] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketMicrostructureRow:
            raise ValueError("rows must contain MarketMicrostructureRow")
        if row.research_case_key in seen_keys:
            raise ValueError("research_case_key values must be unique")
        seen_keys.add(row.research_case_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.research_case_key))


def _validate_row_consistency(row: MarketMicrostructureRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.reason_codes == ("microstructure_research_gate_pass",) and row.status != "pass":
        raise ValueError("pass reason must map to pass status")


def _validate_report_consistency(report: MarketMicrostructureReport) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average(
        tuple(row.microstructure_readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.max_spread_pct != max((row.spread_pct for row in report.rows), default=_ZERO):
        raise ValueError("max_spread_pct must match rows")
    if report.min_top_of_book_depth != min(
        (row.top_of_book_depth for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_top_of_book_depth must match rows")
    if report.max_quote_age_seconds != max(
        (row.quote_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.max_top_liquidity_share != max(
        (row.top_liquidity_share for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_top_liquidity_share must match rows")
    if report.max_volume_burst_ratio != max(
        (row.volume_burst_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_volume_burst_ratio must match rows")
    if report.max_fee_friction_pct != max(
        (row.fee_friction_pct for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_fee_friction_pct must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


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


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")
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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(report: MarketMicrostructureReport) -> dict[str, object]:
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


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
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
    "DEFAULT_MARKET_MICROSTRUCTURE_RESEARCH_GATE_CONFIG_VERSION",
    "STATUSES",
    "MarketMicrostructureGateConfig",
    "MarketMicrostructureInput",
    "MarketMicrostructureReport",
    "MarketMicrostructureRow",
    "build_market_microstructure_research_gate_report",
)
