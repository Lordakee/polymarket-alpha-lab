from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_CONFIG_VERSION = "strategy-candidate-market-regime-fit-v10"
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

FIT_STATUSES = frozenset(("fit", "watch", "blocked"))
VOLATILITY_REGIME_SCORES = {
    "calm": Decimal("1.000000"),
    "normal": Decimal("0.800000"),
    "elevated": Decimal("0.650000"),
    "stressed": Decimal("0.250000"),
}
LIQUIDITY_REGIME_SCORES = {
    "deep": Decimal("1.000000"),
    "adequate": Decimal("0.650000"),
    "thin": Decimal("0.300000"),
    "impaired": Decimal("0.000000"),
}
UNSAFE_SURFACE_FRAGMENTS = frozenset(
    (
        "api_key",
        "auth",
        "credential",
        "execution",
        "fill",
        "live",
        "order",
        "place_order",
        "position",
        "private_key",
        "secret",
        "token",
        "trade",
        "wallet",
    ),
)


@dataclass(frozen=True)
class StrategyCandidateMarketRegimeFitConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fit_threshold: Decimal = Decimal("0.750000")
    watch_threshold: Decimal = Decimal("0.500000")
    fresh_source_update_cadence_minutes: Decimal = Decimal("60.000000")
    stale_source_update_cadence_minutes: Decimal = Decimal("360.000000")
    volatility_weight: Decimal = Decimal("0.200000")
    liquidity_weight: Decimal = Decimal("0.200000")
    source_cadence_weight: Decimal = Decimal("0.200000")
    anti_crowding_weight: Decimal = Decimal("0.200000")
    specialist_confidence_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateMarketRegimeFitConfig:
            raise TypeError("StrategyCandidateMarketRegimeFitConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateMarketRegimeFitConfig:
            raise ValueError("config must be exactly StrategyCandidateMarketRegimeFitConfig")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fit_threshold", "watch_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.fit_threshold <= self.watch_threshold:
            raise ValueError("fit_threshold must be greater than watch_threshold")
        for field_name in (
            "fresh_source_update_cadence_minutes",
            "stale_source_update_cadence_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_update_cadence_minutes <= self.fresh_source_update_cadence_minutes:
            raise ValueError("stale_source_update_cadence_minutes must exceed fresh threshold")
        for field_name in (
            "volatility_weight",
            "liquidity_weight",
            "source_cadence_weight",
            "anti_crowding_weight",
            "specialist_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        weight_sum = _quantize(
            self.volatility_weight
            + self.liquidity_weight
            + self.source_cadence_weight
            + self.anti_crowding_weight
            + self.specialist_confidence_weight,
        )
        if weight_sum != ONE:
            raise ValueError("regime fit weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateMarketRegimeFitCandidate:
    candidate_id: str
    market_slug: str
    market_question: str
    category: str
    volatility_regime: str
    liquidity_regime: str
    source_update_cadence_minutes: Decimal
    crowding_score: Decimal
    specialist_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateMarketRegimeFitCandidate:
            raise TypeError("StrategyCandidateMarketRegimeFitCandidate does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateMarketRegimeFitCandidate:
            raise ValueError("candidate must be exactly StrategyCandidateMarketRegimeFitCandidate")
        for field_name in ("candidate_id", "market_slug", "market_question", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member(
            "volatility_regime",
            self.volatility_regime,
            tuple(VOLATILITY_REGIME_SCORES),
        )
        _require_member(
            "liquidity_regime",
            self.liquidity_regime,
            tuple(LIQUIDITY_REGIME_SCORES),
        )
        object.__setattr__(
            self,
            "source_update_cadence_minutes",
            _normalize_nonnegative_decimal(
                "source_update_cadence_minutes",
                self.source_update_cadence_minutes,
            ),
        )
        for field_name in ("crowding_score", "specialist_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateMarketRegimeFitRow:
    candidate_id: str
    market_slug: str
    market_question: str
    category: str
    volatility_regime: str
    liquidity_regime: str
    source_update_cadence_minutes: Decimal
    crowding_score: Decimal
    volatility_regime_score: Decimal
    liquidity_regime_score: Decimal
    source_update_cadence_score: Decimal
    anti_crowding_score: Decimal
    specialist_confidence: Decimal
    regime_fit_score: Decimal
    fit_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateMarketRegimeFitRow:
            raise TypeError("StrategyCandidateMarketRegimeFitRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateMarketRegimeFitRow:
            raise ValueError("row must be exactly StrategyCandidateMarketRegimeFitRow")
        for field_name in ("candidate_id", "market_slug", "market_question", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("volatility_regime", self.volatility_regime, tuple(VOLATILITY_REGIME_SCORES))
        _require_member("liquidity_regime", self.liquidity_regime, tuple(LIQUIDITY_REGIME_SCORES))
        object.__setattr__(
            self,
            "source_update_cadence_minutes",
            _normalize_nonnegative_decimal(
                "source_update_cadence_minutes",
                self.source_update_cadence_minutes,
            ),
        )
        for field_name in (
            "crowding_score",
            "volatility_regime_score",
            "liquidity_regime_score",
            "source_update_cadence_score",
            "anti_crowding_score",
            "specialist_confidence",
            "regime_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("fit_status", self.fit_status, tuple(FIT_STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateMarketRegimeFitReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    fit_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_regime_fit_score: Decimal
    top_regime_fit_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateMarketRegimeFitRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateMarketRegimeFitReport:
            raise TypeError("StrategyCandidateMarketRegimeFitReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateMarketRegimeFitReport:
            raise ValueError("report must be exactly StrategyCandidateMarketRegimeFitReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("candidate_count", "fit_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_regime_fit_score", "top_regime_fit_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, tuple(FIT_STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_market_regime_fit_v10_payload(self)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def build_strategy_candidate_market_regime_fit_v10(
    candidates: tuple[StrategyCandidateMarketRegimeFitCandidate, ...],
    *,
    config: StrategyCandidateMarketRegimeFitConfig | None = None,
    generated_at: datetime | None = None,
) -> StrategyCandidateMarketRegimeFitReport:
    cfg = config or StrategyCandidateMarketRegimeFitConfig()
    if type(cfg) is not StrategyCandidateMarketRegimeFitConfig:
        raise ValueError("config must be StrategyCandidateMarketRegimeFitConfig")
    _require_hard_flags("config", cfg)
    rows = tuple(_row_for_candidate(candidate, cfg) for candidate in _normalize_candidates(candidates))
    rows = tuple(sorted(rows, key=lambda row: (-row.regime_fit_score, row.candidate_id)))
    candidate_count = _decimal_count(len(rows))
    fit_count = _decimal_count(sum(1 for row in rows if row.fit_status == "fit"))
    watch_count = _decimal_count(sum(1 for row in rows if row.fit_status == "watch"))
    blocked_count = _decimal_count(sum(1 for row in rows if row.fit_status == "blocked"))
    top_score = max((row.regime_fit_score for row in rows), default=ZERO)
    average_score = ZERO
    if rows:
        average_score = _quantize(sum((row.regime_fit_score for row in rows), ZERO) / candidate_count)
    status = _report_status(candidate_count, watch_count, blocked_count)
    return StrategyCandidateMarketRegimeFitReport(
        generated_at=_as_utc("generated_at", generated_at or datetime.now(UTC)),
        config_version=cfg.config_version,
        candidate_count=candidate_count,
        fit_count=fit_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_regime_fit_score=average_score,
        top_regime_fit_score=top_score,
        status=status,
        reason_codes=_report_reason_codes(status, rows),
        rows=rows,
    )


def strategy_candidate_market_regime_fit_v10_payload(
    report: StrategyCandidateMarketRegimeFitReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateMarketRegimeFitReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyCandidateMarketRegimeFitReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_for_candidate(
    candidate: StrategyCandidateMarketRegimeFitCandidate,
    config: StrategyCandidateMarketRegimeFitConfig,
) -> StrategyCandidateMarketRegimeFitRow:
    if type(candidate) is not StrategyCandidateMarketRegimeFitCandidate:
        raise ValueError("candidates must contain StrategyCandidateMarketRegimeFitCandidate values")
    _require_hard_flags("candidate", candidate)
    volatility_score = VOLATILITY_REGIME_SCORES[candidate.volatility_regime]
    liquidity_score = LIQUIDITY_REGIME_SCORES[candidate.liquidity_regime]
    cadence_score = _source_update_cadence_score(
        candidate.source_update_cadence_minutes,
        config,
    )
    anti_crowding_score = _quantize(ONE - candidate.crowding_score)
    fit_score = _quantize(
        (volatility_score * config.volatility_weight)
        + (liquidity_score * config.liquidity_weight)
        + (cadence_score * config.source_cadence_weight)
        + (anti_crowding_score * config.anti_crowding_weight)
        + (candidate.specialist_confidence * config.specialist_confidence_weight),
    )
    fit_status = _fit_status(fit_score, config)
    return StrategyCandidateMarketRegimeFitRow(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        market_question=candidate.market_question,
        category=candidate.category,
        volatility_regime=candidate.volatility_regime,
        liquidity_regime=candidate.liquidity_regime,
        source_update_cadence_minutes=candidate.source_update_cadence_minutes,
        crowding_score=candidate.crowding_score,
        volatility_regime_score=volatility_score,
        liquidity_regime_score=liquidity_score,
        source_update_cadence_score=cadence_score,
        anti_crowding_score=anti_crowding_score,
        specialist_confidence=candidate.specialist_confidence,
        regime_fit_score=fit_score,
        fit_status=fit_status,
        reason_codes=_row_reason_codes(fit_status, cadence_score, candidate),
    )


def _source_update_cadence_score(
    cadence_minutes: Decimal,
    config: StrategyCandidateMarketRegimeFitConfig,
) -> Decimal:
    if cadence_minutes <= config.fresh_source_update_cadence_minutes:
        return ONE
    if cadence_minutes >= config.stale_source_update_cadence_minutes:
        return ZERO
    window = config.stale_source_update_cadence_minutes - config.fresh_source_update_cadence_minutes
    remaining = config.stale_source_update_cadence_minutes - cadence_minutes
    return _normalize_unit_decimal("source_update_cadence_score", remaining / window)


def _fit_status(score: Decimal, config: StrategyCandidateMarketRegimeFitConfig) -> str:
    if score >= config.fit_threshold:
        return "fit"
    if score >= config.watch_threshold:
        return "watch"
    return "blocked"


def _row_reason_codes(
    fit_status: str,
    cadence_score: Decimal,
    candidate: StrategyCandidateMarketRegimeFitCandidate,
) -> tuple[str, ...]:
    if fit_status == "fit":
        return ("market_regime_fit_passed",)
    if fit_status == "watch":
        return ("market_regime_fit_watch",)
    codes = ["market_regime_fit_blocked_row"]
    if cadence_score == ZERO:
        codes.append("source_cadence_stale")
    if candidate.crowding_score >= Decimal("0.750000"):
        codes.append("crowding_elevated")
    if candidate.specialist_confidence <= Decimal("0.400000"):
        codes.append("specialist_confidence_low")
    return tuple(codes)


def _report_status(candidate_count: Decimal, watch_count: Decimal, blocked_count: Decimal) -> str:
    if candidate_count == ZERO:
        return "watch"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "fit"


def _report_reason_codes(
    status: str,
    rows: tuple[StrategyCandidateMarketRegimeFitRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_regime_fit_empty",)
    codes = [f"market_regime_fit_{status}"]
    for row in rows:
        codes.extend(row.reason_codes)
    return _stable_unique(codes)


def _normalize_candidates(
    candidates: tuple[StrategyCandidateMarketRegimeFitCandidate, ...],
) -> tuple[StrategyCandidateMarketRegimeFitCandidate, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyCandidateMarketRegimeFitCandidate:
            raise ValueError("candidates must contain StrategyCandidateMarketRegimeFitCandidate values")
        if candidate.candidate_id in seen_ids:
            raise ValueError("candidate_id values must be unique")
        if candidate.market_slug in seen_slugs:
            raise ValueError("market_slug values must be unique")
        seen_ids.add(candidate.candidate_id)
        seen_slugs.add(candidate.market_slug)
        _require_hard_flags("candidate", candidate)
    return normalized


def _normalize_rows(rows: tuple[StrategyCandidateMarketRegimeFitRow, ...]) -> tuple[StrategyCandidateMarketRegimeFitRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_ids: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyCandidateMarketRegimeFitRow:
            raise ValueError("rows must contain StrategyCandidateMarketRegimeFitRow values")
        if row.candidate_id in seen_ids:
            raise ValueError("row candidate_id values must be unique")
        seen_ids.add(row.candidate_id)
        _require_hard_flags("row", row)
    return normalized


def _validate_report(report: StrategyCandidateMarketRegimeFitReport) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    fit_count = _decimal_count(sum(1 for row in report.rows if row.fit_status == "fit"))
    watch_count = _decimal_count(sum(1 for row in report.rows if row.fit_status == "watch"))
    blocked_count = _decimal_count(sum(1 for row in report.rows if row.fit_status == "blocked"))
    if report.fit_count != fit_count:
        raise ValueError("fit_count must match rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match rows")
    if report.blocked_count != blocked_count:
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(report.candidate_count, report.watch_count, report.blocked_count):
        raise ValueError("status must match row statuses")
    top_score = max((row.regime_fit_score for row in report.rows), default=ZERO)
    if report.top_regime_fit_score != top_score:
        raise ValueError("top_regime_fit_score must match rows")
    average_score = ZERO
    if report.rows:
        average_score = _quantize(
            sum((row.regime_fit_score for row in report.rows), ZERO) / report.candidate_count,
        )
    if report.average_regime_fit_score != average_score:
        raise ValueError("average_regime_fit_score must match rows")
    if report.reason_codes != _report_reason_codes(report.status, report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_canonical_string(field_name, code)
        if _has_unsafe_surface_fragment(code):
            raise ValueError(f"unsafe live surface value in {field_name}")
    return _stable_unique(codes)


def _stable_unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _normalize_integer_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(DECIMAL_QUANTUM)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {path or label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyCandidateMarketRegimeFitCandidate",
    "StrategyCandidateMarketRegimeFitConfig",
    "StrategyCandidateMarketRegimeFitReport",
    "StrategyCandidateMarketRegimeFitRow",
    "build_strategy_candidate_market_regime_fit_v10",
    "strategy_candidate_market_regime_fit_v10_payload",
)
