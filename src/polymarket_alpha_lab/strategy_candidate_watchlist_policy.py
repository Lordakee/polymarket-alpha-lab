"""Pure paper-only watchlist policy for strategy candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
import hashlib
from typing import Any


__all__ = (
    "StrategyCandidateWatchlistCandidate",
    "StrategyCandidateWatchlistDecision",
    "StrategyCandidateWatchlistPolicyConfig",
    "classify_strategy_candidate_watchlist_policy",
    "strategy_candidate_watchlist_policy_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-watchlist-policy-v0"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "candidate_id",
    "market_slug",
    "outcome_name",
    "watchlist_status",
    "next_review_minutes",
    "best_ask_price",
    "target_entry_price",
    "estimated_edge",
    "source_count",
    "available_liquidity_notional",
    "resolution_is_clear",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
WATCHLIST_STATUSES = (
    "wait_for_price",
    "wait_for_source",
    "wait_for_liquidity",
    "wait_for_resolution_clarity",
    "drop",
)
STATUS_REASON_PREFIX = "strategy_candidate_watchlist_"
UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS = (
    "api_key",
    "author" + "ization",
    "credential",
    "private" + "_key",
    "signing",
)
UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS = (
    "account",
    "auth",
    "balance",
    "cancel",
    "credential",
    "database",
    "live",
    "network",
    "or" + "der",
    "persist",
    "secret",
    "sign",
    "token",
    "tra" + "de",
    "wal" + "let",
)


@dataclass(frozen=True)
class StrategyCandidateWatchlistPolicyConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_edge: Decimal = Decimal("0.030000")
    minimum_source_count: Decimal = Decimal("2.000000")
    minimum_liquidity_notional: Decimal = Decimal("1000.000000")
    price_review_minutes: Decimal = Decimal("30.000000")
    source_review_minutes: Decimal = Decimal("360.000000")
    liquidity_review_minutes: Decimal = Decimal("60.000000")
    resolution_review_minutes: Decimal = Decimal("720.000000")
    drop_review_minutes: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateWatchlistPolicyConfig:
            raise TypeError(
                "StrategyCandidateWatchlistPolicyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateWatchlistPolicyConfig:
            raise ValueError(
                "config must be exactly StrategyCandidateWatchlistPolicyConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_edge",
            _normalize_probability_decimal("minimum_edge", self.minimum_edge),
        )
        object.__setattr__(
            self,
            "minimum_source_count",
            _normalize_positive_whole_decimal(
                "minimum_source_count",
                self.minimum_source_count,
            ),
        )
        object.__setattr__(
            self,
            "minimum_liquidity_notional",
            _normalize_nonnegative_decimal(
                "minimum_liquidity_notional",
                self.minimum_liquidity_notional,
            ),
        )
        for field_name in (
            "price_review_minutes",
            "source_review_minutes",
            "liquidity_review_minutes",
            "resolution_review_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "drop_review_minutes",
            _normalize_nonnegative_whole_decimal(
                "drop_review_minutes",
                self.drop_review_minutes,
            ),
        )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateWatchlistCandidate:
    candidate_id: str
    market_slug: str
    outcome_name: str
    best_ask_price: Decimal
    target_entry_price: Decimal
    estimated_edge: Decimal
    source_count: Decimal
    available_liquidity_notional: Decimal
    resolution_is_clear: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateWatchlistCandidate:
            raise TypeError(
                "StrategyCandidateWatchlistCandidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateWatchlistCandidate:
            raise ValueError(
                "candidate_state must be exactly StrategyCandidateWatchlistCandidate",
            )
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("best_ask_price", "target_entry_price", "estimated_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "available_liquidity_notional",
            _normalize_nonnegative_decimal(
                "available_liquidity_notional",
                self.available_liquidity_notional,
            ),
        )
        if type(self.resolution_is_clear) is not bool:
            raise ValueError("resolution_is_clear must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("candidate_state", self)
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class StrategyCandidateWatchlistDecision:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    watchlist_status: str
    next_review_minutes: Decimal
    best_ask_price: Decimal
    target_entry_price: Decimal
    estimated_edge: Decimal
    source_count: Decimal
    available_liquidity_notional: Decimal
    resolution_is_clear: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateWatchlistDecision:
            raise TypeError(
                "StrategyCandidateWatchlistDecision does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateWatchlistDecision:
            raise ValueError(
                "decision must be exactly StrategyCandidateWatchlistDecision",
            )
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("watchlist_status", self.watchlist_status, WATCHLIST_STATUSES)
        object.__setattr__(
            self,
            "next_review_minutes",
            _normalize_nonnegative_whole_decimal(
                "next_review_minutes",
                self.next_review_minutes,
            ),
        )
        for field_name in ("best_ask_price", "target_entry_price", "estimated_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "available_liquidity_notional",
            _normalize_nonnegative_decimal(
                "available_liquidity_notional",
                self.available_liquidity_notional,
            ),
        )
        if type(self.resolution_is_clear) is not bool:
            raise ValueError("resolution_is_clear must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_decision_consistency(self)
        _reject_unsafe_public_payload("decision", self)
        _require_hard_flags("decision", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _decision_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_decision_derived_validation_digest(self)


def classify_strategy_candidate_watchlist_policy(
    candidate_state: StrategyCandidateWatchlistCandidate,
    config: StrategyCandidateWatchlistPolicyConfig,
) -> StrategyCandidateWatchlistDecision:
    """Classify one candidate into a pure paper-only watchlist bucket."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        StrategyCandidateWatchlistCandidate,
    )
    _require_exact_type("config", config, StrategyCandidateWatchlistPolicyConfig)

    watchlist_status, next_review_minutes, generated_reason_code = (
        _watchlist_status_review_and_reason(candidate_state, config)
    )
    return StrategyCandidateWatchlistDecision(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        watchlist_status=watchlist_status,
        next_review_minutes=next_review_minutes,
        best_ask_price=candidate_state.best_ask_price,
        target_entry_price=candidate_state.target_entry_price,
        estimated_edge=candidate_state.estimated_edge,
        source_count=candidate_state.source_count,
        available_liquidity_notional=candidate_state.available_liquidity_notional,
        resolution_is_clear=candidate_state.resolution_is_clear,
        reason_codes=_decision_reason_codes(
            watchlist_status,
            candidate_state.reason_codes,
            generated_reason_code,
        ),
    )


def strategy_candidate_watchlist_policy_payload(
    decision: StrategyCandidateWatchlistDecision | dict[str, object],
) -> dict[str, object]:
    if type(decision) is StrategyCandidateWatchlistDecision:
        _require_hard_flags("decision", decision)
        _reject_unsafe_public_payload("decision", decision)
        _validate_decision_derived_validation_digest(decision)
        payload = _decision_public_payload_values(decision)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = decision.derived_validation_digest
        return payload
    if type(decision) is dict:
        _reject_unsafe_public_payload("payload", decision)
        _require_public_payload_fields(decision)
        _validate_public_payload(decision)
        return dict(decision)
    raise ValueError("decision must be a StrategyCandidateWatchlistDecision")


def _watchlist_status_review_and_reason(
    candidate_state: StrategyCandidateWatchlistCandidate,
    config: StrategyCandidateWatchlistPolicyConfig,
) -> tuple[str, Decimal, str]:
    if candidate_state.estimated_edge < config.minimum_edge:
        return "drop", config.drop_review_minutes, "estimated_edge_below_minimum"
    if candidate_state.source_count < config.minimum_source_count:
        return (
            "wait_for_source",
            config.source_review_minutes,
            "source_count_below_minimum",
        )
    if candidate_state.available_liquidity_notional < config.minimum_liquidity_notional:
        return (
            "wait_for_liquidity",
            config.liquidity_review_minutes,
            "liquidity_below_minimum",
        )
    if not candidate_state.resolution_is_clear:
        return (
            "wait_for_resolution_clarity",
            config.resolution_review_minutes,
            "resolution_clarity_missing",
        )
    if candidate_state.best_ask_price > candidate_state.target_entry_price:
        return "wait_for_price", config.price_review_minutes, "entry_price_above_target"
    return "drop", config.drop_review_minutes, "candidate_already_watchlist_complete"


def _decision_reason_codes(
    watchlist_status: str,
    upstream_reason_codes: tuple[str, ...],
    generated_reason_code: str,
) -> tuple[str, ...]:
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{watchlist_status}",
        *upstream_reason_codes,
        generated_reason_code,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _validate_decision_consistency(
    decision: StrategyCandidateWatchlistDecision,
) -> None:
    expected_reason_code = f"{STATUS_REASON_PREFIX}{decision.watchlist_status}"
    if not decision.reason_codes or decision.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with watchlist_status reason code")


def _decision_public_payload_values(
    decision: StrategyCandidateWatchlistDecision,
) -> dict[str, object]:
    return {
        "config_version": decision.config_version,
        "candidate_id": decision.candidate_id,
        "market_slug": decision.market_slug,
        "outcome_name": decision.outcome_name,
        "watchlist_status": decision.watchlist_status,
        "next_review_minutes": _decimal_payload(decision.next_review_minutes),
        "best_ask_price": _decimal_payload(decision.best_ask_price),
        "target_entry_price": _decimal_payload(decision.target_entry_price),
        "estimated_edge": _decimal_payload(decision.estimated_edge),
        "source_count": _decimal_payload(decision.source_count),
        "available_liquidity_notional": _decimal_payload(
            decision.available_liquidity_notional,
        ),
        "resolution_is_clear": decision.resolution_is_clear,
        "reason_codes": list(decision.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _decision_derived_validation_digest(
    decision: StrategyCandidateWatchlistDecision,
) -> str:
    return _derived_validation_digest(_decision_public_payload_values(decision))


def _validate_decision_derived_validation_digest(
    decision: StrategyCandidateWatchlistDecision,
) -> None:
    if decision.derived_validation_digest != _decision_derived_validation_digest(decision):
        raise ValueError("derived_validation_digest must match decision fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("strategy_candidate_watchlist_policy_derived", values)


def _digest_payload_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ",".join(_digest_payload_value(item) for item in value)
    return str(value)


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    for field_name in ("config_version", "candidate_id", "market_slug", "outcome_name"):
        _require_canonical_string(field_name, payload[field_name])
    _require_member("watchlist_status", payload["watchlist_status"], WATCHLIST_STATUSES)
    _require_decimal_payload_string(
        "next_review_minutes",
        payload["next_review_minutes"],
        whole=True,
    )
    for field_name in ("best_ask_price", "target_entry_price", "estimated_edge"):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_decimal_payload_string("source_count", payload["source_count"], whole=True)
    _require_decimal_payload_string(
        "available_liquidity_notional",
        payload["available_liquidity_notional"],
    )
    if type(payload["resolution_is_clear"]) is not bool:
        raise ValueError("resolution_is_clear must be a bool")
    reason_codes = _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    expected_reason_code = f"{STATUS_REASON_PREFIX}{payload['watchlist_status']}"
    if not reason_codes or reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with watchlist_status reason code")


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    reason_codes: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        reason_codes.append(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(reason_codes)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = decimal_value.quantize(QUANTUM)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    return normalized


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _is_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_public_text(key):
                raise ValueError(f"unsafe field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)


def _is_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS):
        return True
    tokens = _surface_text_tokens(normalized)
    return any(token in tokens for token in UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS)


def _surface_text_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)
