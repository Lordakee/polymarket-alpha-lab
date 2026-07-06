"""Paper-only readonly market source confidence ladder."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any


VALUE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

OFFICIAL_SOURCE_THRESHOLD = Decimal("0.700000")
PRIMARY_SOURCE_THRESHOLD = Decimal("0.650000")
SECONDARY_SOURCE_THRESHOLD = Decimal("0.550000")
MARKET_DATA_THRESHOLD = Decimal("0.500000")
TRUSTED_ADJUSTED_CONFIDENCE = Decimal("0.650000")
BLOCKED_ADJUSTED_CONFIDENCE = Decimal("0.450000")
HIGH_SOURCE_DEPENDENCY_PENALTY = Decimal("0.250000")
HIGH_FRESHNESS_PENALTY = Decimal("0.200000")

CONFIDENCE_LADDER_STATUSES = ("trusted", "upgrade_required", "blocked")
CONFIDENCE_LEVELS = (
    "official",
    "primary",
    "secondary",
    "market_data",
    "insufficient",
)
REQUIRED_SOURCE_UPGRADES = (
    "none",
    "official_source",
    "official_or_primary_source",
    "primary_or_official_source",
    "independent_fresh_source",
)
REASON_CODES = (
    "confidence_ladder_trusted",
    "freshness_penalty_clear",
    "freshness_penalty_high",
    "market_data_only_supported",
    "official_source_verified",
    "primary_source_verified",
    "secondary_source_supported",
    "source_confidence_blocked",
    "source_confidence_insufficient",
    "source_dependency_penalty_clear",
    "source_dependency_penalty_high",
    "source_upgrade_required",
)
SENSITIVE_TEXT_FRAGMENTS = (
    "://",
    "sec" + "ret",
    "tok" + "en=",
    "api" + "_key=",
    "priv" + "ate",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
)
UNSAFE_FIELD_FRAGMENTS = (
    "aut" + "h",
    "wal" + "let",
    "account",
    "balance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
    "bro" + "ker",
)


@dataclass(frozen=True)
class StrategyMarketSourceConfidenceLadderV10Input:
    market_id: str
    official_source_score: Decimal
    primary_source_score: Decimal
    secondary_source_score: Decimal
    market_data_score: Decimal
    source_dependency_penalty: Decimal
    freshness_penalty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "official_source_score",
            "primary_source_score",
            "secondary_source_score",
            "market_data_score",
            "source_dependency_penalty",
            "freshness_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketSourceConfidenceLadderV10Report:
    market_id: str
    official_source_score: Decimal
    primary_source_score: Decimal
    secondary_source_score: Decimal
    market_data_score: Decimal
    source_dependency_penalty: Decimal
    freshness_penalty: Decimal
    adjusted_confidence_score: Decimal
    confidence_ladder_status: str
    confidence_level: str
    required_source_upgrade: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "official_source_score",
            "primary_source_score",
            "secondary_source_score",
            "market_data_score",
            "source_dependency_penalty",
            "freshness_penalty",
            "adjusted_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_ladder_status",
            _normalize_choice(
                "confidence_ladder_status",
                self.confidence_ladder_status,
                CONFIDENCE_LADDER_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "confidence_level",
            _normalize_choice("confidence_level", self.confidence_level, CONFIDENCE_LEVELS),
        )
        object.__setattr__(
            self,
            "required_source_upgrade",
            _normalize_choice(
                "required_source_upgrade",
                self.required_source_upgrade,
                REQUIRED_SOURCE_UPGRADES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )

        expected = _confidence_ladder_outputs(
            official_source_score=self.official_source_score,
            primary_source_score=self.primary_source_score,
            secondary_source_score=self.secondary_source_score,
            market_data_score=self.market_data_score,
            source_dependency_penalty=self.source_dependency_penalty,
            freshness_penalty=self.freshness_penalty,
        )
        if self.adjusted_confidence_score != expected.adjusted_confidence_score:
            raise ValueError("adjusted_confidence_score must match")
        if self.confidence_ladder_status != expected.confidence_ladder_status:
            raise ValueError("confidence_ladder_status must match")
        if self.confidence_level != expected.confidence_level:
            raise ValueError("confidence_level must match")
        if self.required_source_upgrade != expected.required_source_upgrade:
            raise ValueError("required_source_upgrade must match")
        if self.reason_codes != expected.reason_codes:
            raise ValueError("reason_codes must match")
        _require_paper_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_source_confidence_ladder_v10_payload(self)


@dataclass(frozen=True)
class _ConfidenceLadderOutputs:
    adjusted_confidence_score: Decimal
    confidence_ladder_status: str
    confidence_level: str
    required_source_upgrade: str
    reason_codes: tuple[str, ...]


def evaluate_strategy_market_source_confidence_ladder_v10(
    input_row: StrategyMarketSourceConfidenceLadderV10Input,
) -> StrategyMarketSourceConfidenceLadderV10Report:
    if type(input_row) is not StrategyMarketSourceConfidenceLadderV10Input:
        raise ValueError(
            "input_row must be a StrategyMarketSourceConfidenceLadderV10Input",
        )
    _require_paper_flags("input", input_row)
    _reject_unsafe_public_payload("input", input_row)

    outputs = _confidence_ladder_outputs(
        official_source_score=input_row.official_source_score,
        primary_source_score=input_row.primary_source_score,
        secondary_source_score=input_row.secondary_source_score,
        market_data_score=input_row.market_data_score,
        source_dependency_penalty=input_row.source_dependency_penalty,
        freshness_penalty=input_row.freshness_penalty,
    )
    return StrategyMarketSourceConfidenceLadderV10Report(
        market_id=input_row.market_id,
        official_source_score=input_row.official_source_score,
        primary_source_score=input_row.primary_source_score,
        secondary_source_score=input_row.secondary_source_score,
        market_data_score=input_row.market_data_score,
        source_dependency_penalty=input_row.source_dependency_penalty,
        freshness_penalty=input_row.freshness_penalty,
        adjusted_confidence_score=outputs.adjusted_confidence_score,
        confidence_ladder_status=outputs.confidence_ladder_status,
        confidence_level=outputs.confidence_level,
        required_source_upgrade=outputs.required_source_upgrade,
        reason_codes=outputs.reason_codes,
    )


def strategy_market_source_confidence_ladder_v10_payload(
    report: StrategyMarketSourceConfidenceLadderV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyMarketSourceConfidenceLadderV10Report:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyMarketSourceConfidenceLadderV10Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _confidence_ladder_outputs(
    *,
    official_source_score: Decimal,
    primary_source_score: Decimal,
    secondary_source_score: Decimal,
    market_data_score: Decimal,
    source_dependency_penalty: Decimal,
    freshness_penalty: Decimal,
) -> _ConfidenceLadderOutputs:
    confidence_level = _confidence_level(
        official_source_score=official_source_score,
        primary_source_score=primary_source_score,
        secondary_source_score=secondary_source_score,
        market_data_score=market_data_score,
    )
    selected_score = _selected_source_score(
        confidence_level=confidence_level,
        official_source_score=official_source_score,
        primary_source_score=primary_source_score,
        secondary_source_score=secondary_source_score,
        market_data_score=market_data_score,
    )
    adjusted_confidence_score = _q(
        selected_score - source_dependency_penalty - freshness_penalty,
    )
    if adjusted_confidence_score < ZERO:
        adjusted_confidence_score = ZERO

    dependency_penalty_is_high = (
        source_dependency_penalty >= HIGH_SOURCE_DEPENDENCY_PENALTY
    )
    freshness_penalty_is_high = freshness_penalty >= HIGH_FRESHNESS_PENALTY
    confidence_ladder_status = _confidence_ladder_status(
        adjusted_confidence_score=adjusted_confidence_score,
        confidence_level=confidence_level,
        dependency_penalty_is_high=dependency_penalty_is_high,
        freshness_penalty_is_high=freshness_penalty_is_high,
    )
    required_source_upgrade = _required_source_upgrade(
        confidence_ladder_status=confidence_ladder_status,
        confidence_level=confidence_level,
        dependency_penalty_is_high=dependency_penalty_is_high,
        freshness_penalty_is_high=freshness_penalty_is_high,
    )
    return _ConfidenceLadderOutputs(
        adjusted_confidence_score=adjusted_confidence_score,
        confidence_ladder_status=confidence_ladder_status,
        confidence_level=confidence_level,
        required_source_upgrade=required_source_upgrade,
        reason_codes=_reason_codes(
            confidence_ladder_status=confidence_ladder_status,
            confidence_level=confidence_level,
            dependency_penalty_is_high=dependency_penalty_is_high,
            freshness_penalty_is_high=freshness_penalty_is_high,
        ),
    )


def _confidence_level(
    *,
    official_source_score: Decimal,
    primary_source_score: Decimal,
    secondary_source_score: Decimal,
    market_data_score: Decimal,
) -> str:
    if official_source_score >= OFFICIAL_SOURCE_THRESHOLD:
        return "official"
    if primary_source_score >= PRIMARY_SOURCE_THRESHOLD:
        return "primary"
    if secondary_source_score >= SECONDARY_SOURCE_THRESHOLD:
        return "secondary"
    if market_data_score >= MARKET_DATA_THRESHOLD:
        return "market_data"
    return "insufficient"


def _selected_source_score(
    *,
    confidence_level: str,
    official_source_score: Decimal,
    primary_source_score: Decimal,
    secondary_source_score: Decimal,
    market_data_score: Decimal,
) -> Decimal:
    if confidence_level == "official":
        return official_source_score
    if confidence_level == "primary":
        return primary_source_score
    if confidence_level == "secondary":
        return secondary_source_score
    if confidence_level == "market_data":
        return market_data_score
    return max(
        official_source_score,
        primary_source_score,
        secondary_source_score,
        market_data_score,
    )


def _confidence_ladder_status(
    *,
    adjusted_confidence_score: Decimal,
    confidence_level: str,
    dependency_penalty_is_high: bool,
    freshness_penalty_is_high: bool,
) -> str:
    if (
        confidence_level == "insufficient"
        or adjusted_confidence_score < BLOCKED_ADJUSTED_CONFIDENCE
        or dependency_penalty_is_high
        or freshness_penalty_is_high
    ):
        return "blocked"
    if (
        confidence_level in {"official", "primary"}
        and adjusted_confidence_score >= TRUSTED_ADJUSTED_CONFIDENCE
    ):
        return "trusted"
    return "upgrade_required"


def _required_source_upgrade(
    *,
    confidence_ladder_status: str,
    confidence_level: str,
    dependency_penalty_is_high: bool,
    freshness_penalty_is_high: bool,
) -> str:
    if confidence_ladder_status == "trusted":
        return "none"
    if dependency_penalty_is_high or freshness_penalty_is_high:
        return "independent_fresh_source"
    if confidence_level == "primary":
        return "official_source"
    if confidence_level == "secondary":
        return "official_or_primary_source"
    return "primary_or_official_source"


def _reason_codes(
    *,
    confidence_ladder_status: str,
    confidence_level: str,
    dependency_penalty_is_high: bool,
    freshness_penalty_is_high: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if confidence_ladder_status == "trusted":
        codes.append("confidence_ladder_trusted")
    elif confidence_ladder_status == "upgrade_required":
        codes.append("source_upgrade_required")
    else:
        codes.append("source_confidence_blocked")

    if confidence_level == "official":
        codes.append("official_source_verified")
    elif confidence_level == "primary":
        codes.append("primary_source_verified")
    elif confidence_level == "secondary":
        codes.append("secondary_source_supported")
    elif confidence_level == "market_data":
        codes.append("market_data_only_supported")
    else:
        codes.append("source_confidence_insufficient")

    codes.append(
        "source_dependency_penalty_high"
        if dependency_penalty_is_high
        else "source_dependency_penalty_clear",
    )
    codes.append(
        "freshness_penalty_high"
        if freshness_penalty_is_high
        else "freshness_penalty_clear",
    )
    return tuple(sorted(set(codes)))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _q(value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        normalized.append(reason_code)
    if tuple(sorted(normalized)) != tuple(normalized):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if _contains_sensitive_text(value) or _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
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
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_sensitive_text(value) or _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has sensitive or unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in SENSITIVE_TEXT_FRAGMENTS)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_FIELD_FRAGMENTS)


def _q(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM)


__all__ = (
    "StrategyMarketSourceConfidenceLadderV10Input",
    "StrategyMarketSourceConfidenceLadderV10Report",
    "evaluate_strategy_market_source_confidence_ladder_v10",
    "strategy_market_source_confidence_ladder_v10_payload",
)
