"""Paper report reducer for market resolution source checklists."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_MARKET_RESOLUTION_SOURCE_CHECKLIST_V10_CONFIG_VERSION = (
    "strategy-market-resolution-source-checklist-v10"
)

DECIMAL_PRECISION = 64
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
LOW_SCORE_THRESHOLD = Decimal("0.500000")
HIGH_SCORE_THRESHOLD = Decimal("0.750000")
IMMINENT_RESOLUTION_MINUTES = Decimal("60.000000")
NEAR_RESOLUTION_MINUTES = Decimal("240.000000")

CHECKLIST_STATUSES = ("ready", "review_required", "blocked")
RULE_CHANGE_STATUSES = ("stable", "recent", "pending", "unknown")
BASE_REQUIRED_CHECKS = (
    "official_resolution_source_identified",
    "official_source_score_review",
    "precedent_alignment_review",
    "rule_change_review",
    "resolution_window_review",
)
CONDITIONAL_REQUIRED_CHECKS = (
    "independent_source_family_crosscheck",
    "rule_change_confirmation",
    "imminent_resolution_timestamp_check",
)
REQUIRED_CHECKS = BASE_REQUIRED_CHECKS + CONDITIONAL_REQUIRED_CHECKS
REASON_CODES = (
    "resolution_source_family_official",
    "resolution_source_family_unofficial",
    "official_source_score_high",
    "official_source_score_medium",
    "official_source_score_low",
    "precedent_score_high",
    "precedent_score_medium",
    "precedent_score_low",
    "rule_change_status_stable",
    "rule_change_status_recent",
    "rule_change_status_pending",
    "rule_change_status_unknown",
    "resolution_window_normal",
    "resolution_window_near",
    "resolution_window_imminent",
    "checklist_ready",
    "checklist_review_required",
    "checklist_blocked",
)
PAYLOAD_FIELDS = (
    "config_version",
    "market_id",
    "category",
    "resolution_source_family",
    "official_source_score",
    "precedent_score",
    "rule_change_status",
    "time_to_resolution_minutes",
    "checklist_status",
    "required_checks",
    "missing_checks",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class MarketResolutionSourceChecklistV10Input:
    market_id: str
    category: str
    resolution_source_family: str
    official_source_score: Decimal
    precedent_score: Decimal
    rule_change_status: str
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_text("market_id", self.market_id))
        object.__setattr__(self, "category", _normalize_text("category", self.category))
        object.__setattr__(
            self,
            "resolution_source_family",
            _normalize_text("resolution_source_family", self.resolution_source_family),
        )
        object.__setattr__(
            self,
            "official_source_score",
            _normalize_unit_decimal("official_source_score", self.official_source_score),
        )
        object.__setattr__(
            self,
            "precedent_score",
            _normalize_unit_decimal("precedent_score", self.precedent_score),
        )
        object.__setattr__(
            self,
            "rule_change_status",
            _normalize_member(
                "rule_change_status",
                self.rule_change_status,
                RULE_CHANGE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResolutionSourceChecklistV10Result:
    market_id: str
    category: str
    resolution_source_family: str
    official_source_score: Decimal
    precedent_score: Decimal
    rule_change_status: str
    time_to_resolution_minutes: Decimal
    checklist_status: str
    required_checks: tuple[str, ...]
    missing_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    config_version: str = (
        DEFAULT_STRATEGY_MARKET_RESOLUTION_SOURCE_CHECKLIST_V10_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_config_version(self.config_version)
        object.__setattr__(self, "market_id", _normalize_text("market_id", self.market_id))
        object.__setattr__(self, "category", _normalize_text("category", self.category))
        object.__setattr__(
            self,
            "resolution_source_family",
            _normalize_text("resolution_source_family", self.resolution_source_family),
        )
        object.__setattr__(
            self,
            "official_source_score",
            _normalize_unit_decimal("official_source_score", self.official_source_score),
        )
        object.__setattr__(
            self,
            "precedent_score",
            _normalize_unit_decimal("precedent_score", self.precedent_score),
        )
        object.__setattr__(
            self,
            "rule_change_status",
            _normalize_member(
                "rule_change_status",
                self.rule_change_status,
                RULE_CHANGE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "checklist_status",
            _normalize_member(
                "checklist_status",
                self.checklist_status,
                CHECKLIST_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "required_checks",
            _normalize_codes("required_checks", self.required_checks, REQUIRED_CHECKS),
        )
        object.__setattr__(
            self,
            "missing_checks",
            _normalize_codes("missing_checks", self.missing_checks, REQUIRED_CHECKS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        _require_hard_flags("result", self)
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_resolution_source_checklist_v10_payload(self)


def strategy_market_resolution_source_checklist_v10(
    market: MarketResolutionSourceChecklistV10Input,
) -> MarketResolutionSourceChecklistV10Result:
    if type(market) is not MarketResolutionSourceChecklistV10Input:
        raise ValueError("market must be a MarketResolutionSourceChecklistV10Input")
    _require_hard_flags("input", market)
    required_checks = _required_checks(market)
    missing_checks = _missing_checks(market)
    checklist_status = _checklist_status(market, missing_checks)
    return MarketResolutionSourceChecklistV10Result(
        market_id=market.market_id,
        category=market.category,
        resolution_source_family=market.resolution_source_family,
        official_source_score=market.official_source_score,
        precedent_score=market.precedent_score,
        rule_change_status=market.rule_change_status,
        time_to_resolution_minutes=market.time_to_resolution_minutes,
        checklist_status=checklist_status,
        required_checks=required_checks,
        missing_checks=missing_checks,
        reason_codes=_reason_codes(market, checklist_status),
    )


def strategy_market_resolution_source_checklist_v10_payload(
    report: MarketResolutionSourceChecklistV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResolutionSourceChecklistV10Result:
        _require_hard_flags("result", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsupported_payload_fields(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a MarketResolutionSourceChecklistV10Result")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsupported_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


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


def _required_checks(market: MarketResolutionSourceChecklistV10Input) -> tuple[str, ...]:
    checks = list(BASE_REQUIRED_CHECKS)
    if not _source_family_is_official(market):
        checks.append("independent_source_family_crosscheck")
    if market.rule_change_status != "stable":
        checks.append("rule_change_confirmation")
    if _resolution_is_imminent(market):
        checks.append("imminent_resolution_timestamp_check")
    return tuple(checks)


def _missing_checks(market: MarketResolutionSourceChecklistV10Input) -> tuple[str, ...]:
    missing: list[str] = []
    if not _source_family_is_official(market):
        missing.append("official_resolution_source_identified")
    if market.official_source_score < HIGH_SCORE_THRESHOLD:
        missing.append("official_source_score_review")
    if market.precedent_score < HIGH_SCORE_THRESHOLD:
        missing.append("precedent_alignment_review")
    if not _source_family_is_official(market):
        missing.append("independent_source_family_crosscheck")
    if market.rule_change_status != "stable":
        missing.append("rule_change_confirmation")
    if _resolution_is_imminent(market):
        missing.append("imminent_resolution_timestamp_check")
    return tuple(missing)


def _checklist_status(
    market: MarketResolutionSourceChecklistV10Input,
    missing_checks: tuple[str, ...],
) -> str:
    if not missing_checks:
        return "ready"
    if _has_blocking_resolution_source_gap(market):
        return "blocked"
    return "review_required"


def _has_blocking_resolution_source_gap(
    market: MarketResolutionSourceChecklistV10Input,
) -> bool:
    return (
        not _source_family_is_official(market)
        or market.official_source_score < LOW_SCORE_THRESHOLD
        or market.precedent_score < LOW_SCORE_THRESHOLD
        or market.rule_change_status != "stable"
        or _resolution_is_imminent(market)
    )


def _reason_codes(
    market: MarketResolutionSourceChecklistV10Input,
    checklist_status: str,
) -> tuple[str, ...]:
    return (
        _source_family_reason_code(market),
        _score_reason_code("official_source_score", market.official_source_score),
        _score_reason_code("precedent_score", market.precedent_score),
        f"rule_change_status_{market.rule_change_status}",
        _resolution_window_reason_code(market),
        f"checklist_{checklist_status}",
    )


def _source_family_is_official(market: MarketResolutionSourceChecklistV10Input) -> bool:
    return market.resolution_source_family == "official"


def _resolution_is_imminent(market: MarketResolutionSourceChecklistV10Input) -> bool:
    return market.time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES


def _source_family_reason_code(market: MarketResolutionSourceChecklistV10Input) -> str:
    if _source_family_is_official(market):
        return "resolution_source_family_official"
    return "resolution_source_family_unofficial"


def _score_reason_code(prefix: str, value: Decimal) -> str:
    if value >= HIGH_SCORE_THRESHOLD:
        return f"{prefix}_high"
    if value >= LOW_SCORE_THRESHOLD:
        return f"{prefix}_medium"
    return f"{prefix}_low"


def _resolution_window_reason_code(
    market: MarketResolutionSourceChecklistV10Input,
) -> str:
    if market.time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES:
        return "resolution_window_imminent"
    if market.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return "resolution_window_near"
    return "resolution_window_normal"


def _validate_result(result: MarketResolutionSourceChecklistV10Result) -> None:
    market = MarketResolutionSourceChecklistV10Input(
        market_id=result.market_id,
        category=result.category,
        resolution_source_family=result.resolution_source_family,
        official_source_score=result.official_source_score,
        precedent_score=result.precedent_score,
        rule_change_status=result.rule_change_status,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
    )
    expected_required_checks = _required_checks(market)
    expected_missing_checks = _missing_checks(market)
    expected_checklist_status = _checklist_status(market, expected_missing_checks)
    expected_reason_codes = _reason_codes(market, expected_checklist_status)
    if result.required_checks != expected_required_checks:
        raise ValueError("required_checks must match checklist inputs")
    if result.missing_checks != expected_missing_checks:
        raise ValueError("missing_checks must match checklist inputs")
    if result.checklist_status != expected_checklist_status:
        raise ValueError("checklist_status must match missing checks")
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match checklist inputs")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsupported_payload_fields(value: dict[str, object]) -> None:
    for key in value:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _normalize_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _normalize_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _normalize_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    normalized = _normalize_text(field_name, value)
    if normalized not in allowed:
        raise ValueError(f"{field_name} is not supported")
    return normalized


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_STRATEGY_MARKET_RESOLUTION_SOURCE_CHECKLIST_V10_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(RATIO_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_MARKET_RESOLUTION_SOURCE_CHECKLIST_V10_CONFIG_VERSION",
    "MarketResolutionSourceChecklistV10Input",
    "MarketResolutionSourceChecklistV10Result",
    "strategy_market_resolution_source_checklist_v10",
    "strategy_market_resolution_source_checklist_v10_payload",
)
