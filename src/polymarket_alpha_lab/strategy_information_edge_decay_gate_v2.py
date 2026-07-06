"""Pure paper/report/readonly information edge decay gate v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Any


SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

FRESH_INFORMATION_HOURS = Decimal("6.000000")
INFORMATION_DECAY_SPAN_HOURS = Decimal("66.000000")
OFFICIAL_SOURCE_FRESH_LAG_HOURS = Decimal("6.000000")
OFFICIAL_SOURCE_DECAY_SPAN_HOURS = Decimal("64.000000")

PASS_EDGE_DECAY_FACTOR = Decimal("0.750000")
REVIEW_EDGE_DECAY_FACTOR = Decimal("0.050000")
STRONG_QUALITY_THRESHOLD = Decimal("0.900000")
WATCH_QUALITY_THRESHOLD = Decimal("0.500000")
SEVERE_CONTRADICTION_THRESHOLD = Decimal("0.750000")
HIGH_UNSUPPORTED_MOVE_THRESHOLD = Decimal("0.500000")

GATE_STATUSES = ("pass", "review", "blocked")
RECOMMENDED_ACTIONS = (
    "include_in_paper_report",
    "review_before_paper_report",
    "exclude_from_paper_report",
)
REQUIRED_FOLLOWUPS = (
    "refresh_information_timestamp",
    "improve_source_quality",
    "resolve_evidence_contradictions",
    "wait_for_official_source_update",
    "explain_probability_move_with_evidence",
    "raise_specialist_confidence",
)
REASON_CODES = (
    "gate_status_pass",
    "gate_status_review",
    "gate_status_blocked",
    "freshness_clear",
    "freshness_watch",
    "freshness_blocked",
    "source_quality_strong",
    "source_quality_watch",
    "source_quality_weak",
    "contradiction_clear",
    "contradiction_watch",
    "contradiction_severe",
    "official_lag_clear",
    "official_lag_watch",
    "official_lag_blocked",
    "unsupported_move_clear",
    "unsupported_move_watch",
    "unsupported_move_high",
    "specialist_confidence_strong",
    "specialist_confidence_watch",
    "specialist_confidence_weak",
    "edge_decay_factor_pass",
    "edge_decay_factor_watch",
    "edge_decay_factor_blocked",
    "forecast_edge_retained",
    "forecast_edge_reduced",
    "forecast_edge_exhausted",
)
UNSAFE_PUBLIC_TERMS = (
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
class StrategyInformationEdgeDecayGateV2Input:
    signal_id: str
    market_slug: str
    forecast_edge: Decimal
    information_age_hours: Decimal
    source_quality_score: Decimal
    contradiction_severity_score: Decimal
    official_source_lag_hours: Decimal
    market_probability_move_without_evidence: Decimal
    specialist_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyInformationEdgeDecayGateV2Input:
            raise ValueError("subject must be a StrategyInformationEdgeDecayGateV2Input")
        _reject_unsafe_public_payload("information edge decay input", asdict(self))
        _require_identifier("signal_id", self.signal_id)
        _require_identifier("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "forecast_edge",
            _normalize_nonnegative_decimal("forecast_edge", self.forecast_edge),
        )
        for field_name in (
            "source_quality_score",
            "contradiction_severity_score",
            "market_probability_move_without_evidence",
            "specialist_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("information_age_hours", "official_source_lag_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyInformationEdgeDecayGateV2Result:
    signal_id: str
    market_slug: str
    forecast_edge: Decimal
    information_age_hours: Decimal
    source_quality_score: Decimal
    contradiction_severity_score: Decimal
    official_source_lag_hours: Decimal
    market_probability_move_without_evidence: Decimal
    specialist_confidence_score: Decimal
    freshness_factor: Decimal
    contradiction_factor: Decimal
    official_source_lag_factor: Decimal
    unsupported_move_factor: Decimal
    edge_decay_factor: Decimal
    decayed_forecast_edge: Decimal
    gate_status: str
    recommended_action: str
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyInformationEdgeDecayGateV2Result:
            raise ValueError("result must be a StrategyInformationEdgeDecayGateV2Result")
        _reject_unsafe_public_payload("information edge decay result", asdict(self))
        _require_identifier("signal_id", self.signal_id)
        _require_identifier("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "forecast_edge",
            _normalize_nonnegative_decimal("forecast_edge", self.forecast_edge),
        )
        for field_name in (
            "source_quality_score",
            "contradiction_severity_score",
            "market_probability_move_without_evidence",
            "specialist_confidence_score",
            "freshness_factor",
            "contradiction_factor",
            "official_source_lag_factor",
            "unsupported_move_factor",
            "edge_decay_factor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "information_age_hours",
            "official_source_lag_hours",
            "decayed_forecast_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("gate_status", self.gate_status, GATE_STATUSES)
        _require_choice("recommended_action", self.recommended_action, RECOMMENDED_ACTIONS)
        object.__setattr__(
            self,
            "required_followups",
            _normalize_string_tuple(
                "required_followups",
                self.required_followups,
                REQUIRED_FOLLOWUPS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_result(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("information edge decay payload", payload)
        if type(payload) is not dict:
            raise ValueError("information edge decay payload must be an object")
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> StrategyInformationEdgeDecayGateV2Result:
        _reject_unsafe_public_payload("information edge decay payload", payload)
        payload_dict = _payload_dict("information edge decay payload", payload)
        _require_payload_fields(
            payload_dict,
            (
                "signal_id",
                "market_slug",
                "forecast_edge",
                "information_age_hours",
                "source_quality_score",
                "contradiction_severity_score",
                "official_source_lag_hours",
                "market_probability_move_without_evidence",
                "specialist_confidence_score",
                "freshness_factor",
                "contradiction_factor",
                "official_source_lag_factor",
                "unsupported_move_factor",
                "edge_decay_factor",
                "decayed_forecast_edge",
                "gate_status",
                "recommended_action",
                "required_followups",
                "reason_codes",
                "derived_validation_digest",
                "paper_only",
                "report_only",
                "readonly",
            ),
        )
        values = _result_values_from_payload(payload_dict)
        expected_digest = _derived_validation_digest_values(**values)
        supplied_digest = _normalize_derived_validation_digest(
            "derived_validation_digest",
            payload_dict["derived_validation_digest"],
        )
        if supplied_digest != expected_digest:
            raise ValueError("derived_validation_digest must match result fields")
        return cls(**values, derived_validation_digest=supplied_digest)


def build_strategy_information_edge_decay_gate_v2(
    subject: StrategyInformationEdgeDecayGateV2Input,
) -> StrategyInformationEdgeDecayGateV2Result:
    if type(subject) is not StrategyInformationEdgeDecayGateV2Input:
        raise ValueError("subject must be a StrategyInformationEdgeDecayGateV2Input")
    _require_hard_flags(subject)
    _reject_unsafe_public_payload("information edge decay input", asdict(subject))

    freshness_factor = _staleness_factor(
        subject.information_age_hours,
        fresh_hours=FRESH_INFORMATION_HOURS,
        decay_span_hours=INFORMATION_DECAY_SPAN_HOURS,
    )
    contradiction_factor = _q(ONE - subject.contradiction_severity_score)
    official_source_lag_factor = _staleness_factor(
        subject.official_source_lag_hours,
        fresh_hours=OFFICIAL_SOURCE_FRESH_LAG_HOURS,
        decay_span_hours=OFFICIAL_SOURCE_DECAY_SPAN_HOURS,
    )
    unsupported_move_factor = _q(
        ONE - subject.market_probability_move_without_evidence,
    )
    edge_decay_factor = _edge_decay_factor(
        freshness_factor=freshness_factor,
        source_quality_score=subject.source_quality_score,
        contradiction_factor=contradiction_factor,
        official_source_lag_factor=official_source_lag_factor,
        unsupported_move_factor=unsupported_move_factor,
        specialist_confidence_score=subject.specialist_confidence_score,
    )
    decayed_forecast_edge = _q(subject.forecast_edge * edge_decay_factor)
    gate_status = _gate_status(edge_decay_factor)

    return StrategyInformationEdgeDecayGateV2Result(
        signal_id=subject.signal_id,
        market_slug=subject.market_slug,
        forecast_edge=subject.forecast_edge,
        information_age_hours=subject.information_age_hours,
        source_quality_score=subject.source_quality_score,
        contradiction_severity_score=subject.contradiction_severity_score,
        official_source_lag_hours=subject.official_source_lag_hours,
        market_probability_move_without_evidence=(
            subject.market_probability_move_without_evidence
        ),
        specialist_confidence_score=subject.specialist_confidence_score,
        freshness_factor=freshness_factor,
        contradiction_factor=contradiction_factor,
        official_source_lag_factor=official_source_lag_factor,
        unsupported_move_factor=unsupported_move_factor,
        edge_decay_factor=edge_decay_factor,
        decayed_forecast_edge=decayed_forecast_edge,
        gate_status=gate_status,
        recommended_action=_recommended_action(gate_status),
        required_followups=_required_followups(subject),
        reason_codes=_reason_codes(
            subject,
            freshness_factor=freshness_factor,
            official_source_lag_factor=official_source_lag_factor,
            edge_decay_factor=edge_decay_factor,
            decayed_forecast_edge=decayed_forecast_edge,
            gate_status=gate_status,
        ),
    )


def strategy_information_edge_decay_gate_v2_payload(
    result: StrategyInformationEdgeDecayGateV2Result,
) -> dict[str, object]:
    if type(result) is not StrategyInformationEdgeDecayGateV2Result:
        raise ValueError("result must be a StrategyInformationEdgeDecayGateV2Result")
    _require_hard_flags(result)
    _reject_unsafe_public_payload("information edge decay result", asdict(result))
    return result.payload


def _staleness_factor(
    hours: Decimal,
    *,
    fresh_hours: Decimal,
    decay_span_hours: Decimal,
) -> Decimal:
    if hours <= fresh_hours:
        return ONE
    elapsed = hours - fresh_hours
    if elapsed >= decay_span_hours:
        return ZERO
    return _q(ONE - (elapsed / decay_span_hours))


def _edge_decay_factor(
    *,
    freshness_factor: Decimal,
    source_quality_score: Decimal,
    contradiction_factor: Decimal,
    official_source_lag_factor: Decimal,
    unsupported_move_factor: Decimal,
    specialist_confidence_score: Decimal,
) -> Decimal:
    return _q(
        freshness_factor
        * source_quality_score
        * contradiction_factor
        * official_source_lag_factor
        * unsupported_move_factor
        * specialist_confidence_score,
    )


def _gate_status(edge_decay_factor: Decimal) -> str:
    if edge_decay_factor >= PASS_EDGE_DECAY_FACTOR:
        return "pass"
    if edge_decay_factor >= REVIEW_EDGE_DECAY_FACTOR:
        return "review"
    return "blocked"


def _recommended_action(gate_status: str) -> str:
    if gate_status == "pass":
        return "include_in_paper_report"
    if gate_status == "review":
        return "review_before_paper_report"
    if gate_status == "blocked":
        return "exclude_from_paper_report"
    raise ValueError("gate_status must be supported")


def _required_followups(
    subject: StrategyInformationEdgeDecayGateV2Input,
) -> tuple[str, ...]:
    values: list[str] = []
    if subject.information_age_hours > FRESH_INFORMATION_HOURS:
        values.append("refresh_information_timestamp")
    if subject.source_quality_score < STRONG_QUALITY_THRESHOLD:
        values.append("improve_source_quality")
    if subject.contradiction_severity_score > ZERO:
        values.append("resolve_evidence_contradictions")
    if subject.official_source_lag_hours > OFFICIAL_SOURCE_FRESH_LAG_HOURS:
        values.append("wait_for_official_source_update")
    if subject.market_probability_move_without_evidence > ZERO:
        values.append("explain_probability_move_with_evidence")
    if subject.specialist_confidence_score < STRONG_QUALITY_THRESHOLD:
        values.append("raise_specialist_confidence")
    return tuple(values)


def _reason_codes(
    subject: StrategyInformationEdgeDecayGateV2Input,
    *,
    freshness_factor: Decimal,
    official_source_lag_factor: Decimal,
    edge_decay_factor: Decimal,
    decayed_forecast_edge: Decimal,
    gate_status: str,
) -> tuple[str, ...]:
    return (
        f"gate_status_{gate_status}",
        _freshness_reason(freshness_factor),
        _source_quality_reason(subject.source_quality_score),
        _contradiction_reason(subject.contradiction_severity_score),
        _official_lag_reason(official_source_lag_factor),
        _unsupported_move_reason(subject.market_probability_move_without_evidence),
        _specialist_confidence_reason(subject.specialist_confidence_score),
        _edge_decay_reason(edge_decay_factor),
        _forecast_edge_reason(
            forecast_edge=subject.forecast_edge,
            decayed_forecast_edge=decayed_forecast_edge,
        ),
    )


def _freshness_reason(freshness_factor: Decimal) -> str:
    if freshness_factor == ONE:
        return "freshness_clear"
    if freshness_factor == ZERO:
        return "freshness_blocked"
    return "freshness_watch"


def _source_quality_reason(source_quality_score: Decimal) -> str:
    return _quality_reason(
        source_quality_score,
        strong_code="source_quality_strong",
        watch_code="source_quality_watch",
        weak_code="source_quality_weak",
    )


def _specialist_confidence_reason(specialist_confidence_score: Decimal) -> str:
    return _quality_reason(
        specialist_confidence_score,
        strong_code="specialist_confidence_strong",
        watch_code="specialist_confidence_watch",
        weak_code="specialist_confidence_weak",
    )


def _quality_reason(
    value: Decimal,
    *,
    strong_code: str,
    watch_code: str,
    weak_code: str,
) -> str:
    if value >= STRONG_QUALITY_THRESHOLD:
        return strong_code
    if value >= WATCH_QUALITY_THRESHOLD:
        return watch_code
    return weak_code


def _contradiction_reason(contradiction_severity_score: Decimal) -> str:
    if contradiction_severity_score == ZERO:
        return "contradiction_clear"
    if contradiction_severity_score >= SEVERE_CONTRADICTION_THRESHOLD:
        return "contradiction_severe"
    return "contradiction_watch"


def _official_lag_reason(official_source_lag_factor: Decimal) -> str:
    if official_source_lag_factor == ONE:
        return "official_lag_clear"
    if official_source_lag_factor == ZERO:
        return "official_lag_blocked"
    return "official_lag_watch"


def _unsupported_move_reason(market_probability_move_without_evidence: Decimal) -> str:
    if market_probability_move_without_evidence == ZERO:
        return "unsupported_move_clear"
    if market_probability_move_without_evidence >= HIGH_UNSUPPORTED_MOVE_THRESHOLD:
        return "unsupported_move_high"
    return "unsupported_move_watch"


def _edge_decay_reason(edge_decay_factor: Decimal) -> str:
    if edge_decay_factor >= PASS_EDGE_DECAY_FACTOR:
        return "edge_decay_factor_pass"
    if edge_decay_factor >= REVIEW_EDGE_DECAY_FACTOR:
        return "edge_decay_factor_watch"
    return "edge_decay_factor_blocked"


def _forecast_edge_reason(
    *,
    forecast_edge: Decimal,
    decayed_forecast_edge: Decimal,
) -> str:
    if decayed_forecast_edge == forecast_edge:
        return "forecast_edge_retained"
    if decayed_forecast_edge == ZERO:
        return "forecast_edge_exhausted"
    return "forecast_edge_reduced"


def _validate_result(result: StrategyInformationEdgeDecayGateV2Result) -> None:
    expected_subject = StrategyInformationEdgeDecayGateV2Input(
        signal_id=result.signal_id,
        market_slug=result.market_slug,
        forecast_edge=result.forecast_edge,
        information_age_hours=result.information_age_hours,
        source_quality_score=result.source_quality_score,
        contradiction_severity_score=result.contradiction_severity_score,
        official_source_lag_hours=result.official_source_lag_hours,
        market_probability_move_without_evidence=(
            result.market_probability_move_without_evidence
        ),
        specialist_confidence_score=result.specialist_confidence_score,
    )
    expected_freshness_factor = _staleness_factor(
        result.information_age_hours,
        fresh_hours=FRESH_INFORMATION_HOURS,
        decay_span_hours=INFORMATION_DECAY_SPAN_HOURS,
    )
    expected_contradiction_factor = _q(ONE - result.contradiction_severity_score)
    expected_official_source_lag_factor = _staleness_factor(
        result.official_source_lag_hours,
        fresh_hours=OFFICIAL_SOURCE_FRESH_LAG_HOURS,
        decay_span_hours=OFFICIAL_SOURCE_DECAY_SPAN_HOURS,
    )
    expected_unsupported_move_factor = _q(
        ONE - result.market_probability_move_without_evidence,
    )
    expected_edge_decay_factor = _edge_decay_factor(
        freshness_factor=expected_freshness_factor,
        source_quality_score=result.source_quality_score,
        contradiction_factor=expected_contradiction_factor,
        official_source_lag_factor=expected_official_source_lag_factor,
        unsupported_move_factor=expected_unsupported_move_factor,
        specialist_confidence_score=result.specialist_confidence_score,
    )
    expected_decayed_forecast_edge = _q(result.forecast_edge * expected_edge_decay_factor)
    expected_gate_status = _gate_status(expected_edge_decay_factor)
    if result.freshness_factor != expected_freshness_factor:
        raise ValueError("freshness_factor must match subject fields")
    if result.contradiction_factor != expected_contradiction_factor:
        raise ValueError("contradiction_factor must match subject fields")
    if result.official_source_lag_factor != expected_official_source_lag_factor:
        raise ValueError("official_source_lag_factor must match subject fields")
    if result.unsupported_move_factor != expected_unsupported_move_factor:
        raise ValueError("unsupported_move_factor must match subject fields")
    if result.edge_decay_factor != expected_edge_decay_factor:
        raise ValueError("edge_decay_factor must match subject fields")
    if result.decayed_forecast_edge != expected_decayed_forecast_edge:
        raise ValueError("decayed_forecast_edge must match subject fields")
    if result.gate_status != expected_gate_status:
        raise ValueError("gate_status must match edge_decay_factor")
    if result.recommended_action != _recommended_action(expected_gate_status):
        raise ValueError("recommended_action must match gate_status")
    if result.required_followups != _required_followups(expected_subject):
        raise ValueError("required_followups must match subject fields")
    if result.reason_codes != _reason_codes(
        expected_subject,
        freshness_factor=expected_freshness_factor,
        official_source_lag_factor=expected_official_source_lag_factor,
        edge_decay_factor=expected_edge_decay_factor,
        decayed_forecast_edge=expected_decayed_forecast_edge,
        gate_status=expected_gate_status,
    ):
        raise ValueError("reason_codes must match subject fields")
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < SCORE_QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _q(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_derived_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _normalize_string_tuple(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in items:
        _require_choice(field_name, item, allowed_values)
    return items


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if hasattr(payload, "__dataclass_fields__") and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _mentions_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str and _mentions_unsafe_public_term(payload):
        raise ValueError(f"unsafe public payload value in {label}: {payload}")


def _mentions_unsafe_public_term(value: str) -> bool:
    tokens = _public_tokens(value.lower())
    return any(term in tokens for term in UNSAFE_PUBLIC_TERMS)


def _public_tokens(value: str) -> tuple[str, ...]:
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


def _payload_value(value: Any) -> Any:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        return str(_q(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        _reject_unsafe_public_payload("information edge decay payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _payload_dict(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    return value


def _require_payload_fields(
    payload: dict[str, object],
    required_fields: tuple[str, ...],
) -> None:
    expected = set(required_fields)
    actual = set(payload)
    if actual != expected:
        raise ValueError("information edge decay payload fields must match public schema")


def _result_values_from_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "signal_id": _string_from_payload("signal_id", payload["signal_id"]),
        "market_slug": _string_from_payload("market_slug", payload["market_slug"]),
        "forecast_edge": _decimal_from_payload("forecast_edge", payload["forecast_edge"]),
        "information_age_hours": _decimal_from_payload(
            "information_age_hours",
            payload["information_age_hours"],
        ),
        "source_quality_score": _decimal_from_payload(
            "source_quality_score",
            payload["source_quality_score"],
        ),
        "contradiction_severity_score": _decimal_from_payload(
            "contradiction_severity_score",
            payload["contradiction_severity_score"],
        ),
        "official_source_lag_hours": _decimal_from_payload(
            "official_source_lag_hours",
            payload["official_source_lag_hours"],
        ),
        "market_probability_move_without_evidence": _decimal_from_payload(
            "market_probability_move_without_evidence",
            payload["market_probability_move_without_evidence"],
        ),
        "specialist_confidence_score": _decimal_from_payload(
            "specialist_confidence_score",
            payload["specialist_confidence_score"],
        ),
        "freshness_factor": _decimal_from_payload(
            "freshness_factor",
            payload["freshness_factor"],
        ),
        "contradiction_factor": _decimal_from_payload(
            "contradiction_factor",
            payload["contradiction_factor"],
        ),
        "official_source_lag_factor": _decimal_from_payload(
            "official_source_lag_factor",
            payload["official_source_lag_factor"],
        ),
        "unsupported_move_factor": _decimal_from_payload(
            "unsupported_move_factor",
            payload["unsupported_move_factor"],
        ),
        "edge_decay_factor": _decimal_from_payload(
            "edge_decay_factor",
            payload["edge_decay_factor"],
        ),
        "decayed_forecast_edge": _decimal_from_payload(
            "decayed_forecast_edge",
            payload["decayed_forecast_edge"],
        ),
        "gate_status": _string_from_payload("gate_status", payload["gate_status"]),
        "recommended_action": _string_from_payload(
            "recommended_action",
            payload["recommended_action"],
        ),
        "required_followups": tuple(
            _string_from_payload("required_followups", item)
            for item in _payload_list("required_followups", payload["required_followups"])
        ),
        "reason_codes": tuple(
            _string_from_payload("reason_codes", item)
            for item in _payload_list("reason_codes", payload["reason_codes"])
        ),
        "paper_only": _bool_from_payload("paper_only", payload["paper_only"]),
        "report_only": _bool_from_payload("report_only", payload["report_only"]),
        "readonly": _bool_from_payload("readonly", payload["readonly"]),
    }


def _string_from_payload(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_decimal(field_name, parsed)


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _payload_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _derived_validation_digest(
    result: StrategyInformationEdgeDecayGateV2Result,
) -> str:
    return _derived_validation_digest_values(
        signal_id=result.signal_id,
        market_slug=result.market_slug,
        forecast_edge=result.forecast_edge,
        information_age_hours=result.information_age_hours,
        source_quality_score=result.source_quality_score,
        contradiction_severity_score=result.contradiction_severity_score,
        official_source_lag_hours=result.official_source_lag_hours,
        market_probability_move_without_evidence=(
            result.market_probability_move_without_evidence
        ),
        specialist_confidence_score=result.specialist_confidence_score,
        freshness_factor=result.freshness_factor,
        contradiction_factor=result.contradiction_factor,
        official_source_lag_factor=result.official_source_lag_factor,
        unsupported_move_factor=result.unsupported_move_factor,
        edge_decay_factor=result.edge_decay_factor,
        decayed_forecast_edge=result.decayed_forecast_edge,
        gate_status=result.gate_status,
        recommended_action=result.recommended_action,
        required_followups=result.required_followups,
        reason_codes=result.reason_codes,
        paper_only=result.paper_only,
        report_only=result.report_only,
        readonly=result.readonly,
    )


def _derived_validation_digest_values(
    *,
    signal_id: str,
    market_slug: str,
    forecast_edge: Decimal,
    information_age_hours: Decimal,
    source_quality_score: Decimal,
    contradiction_severity_score: Decimal,
    official_source_lag_hours: Decimal,
    market_probability_move_without_evidence: Decimal,
    specialist_confidence_score: Decimal,
    freshness_factor: Decimal,
    contradiction_factor: Decimal,
    official_source_lag_factor: Decimal,
    unsupported_move_factor: Decimal,
    edge_decay_factor: Decimal,
    decayed_forecast_edge: Decimal,
    gate_status: str,
    recommended_action: str,
    required_followups: tuple[str, ...],
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    digest_material = "|".join(
        (
            f"signal_id={signal_id}",
            f"market_slug={market_slug}",
            f"forecast_edge={forecast_edge}",
            f"information_age_hours={information_age_hours}",
            f"source_quality_score={source_quality_score}",
            f"contradiction_severity_score={contradiction_severity_score}",
            f"official_source_lag_hours={official_source_lag_hours}",
            (
                "market_probability_move_without_evidence="
                f"{market_probability_move_without_evidence}"
            ),
            f"specialist_confidence_score={specialist_confidence_score}",
            f"freshness_factor={freshness_factor}",
            f"contradiction_factor={contradiction_factor}",
            f"official_source_lag_factor={official_source_lag_factor}",
            f"unsupported_move_factor={unsupported_move_factor}",
            f"edge_decay_factor={edge_decay_factor}",
            f"decayed_forecast_edge={decayed_forecast_edge}",
            f"gate_status={gate_status}",
            f"recommended_action={recommended_action}",
            f"required_followups={','.join(required_followups)}",
            f"reason_codes={','.join(reason_codes)}",
            f"paper_only={paper_only}",
            f"report_only={report_only}",
            f"readonly={readonly}",
        ),
    )
    return hashlib.sha256(digest_material.encode("utf-8")).hexdigest()


def _q(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT)


__all__ = (
    "GATE_STATUSES",
    "RECOMMENDED_ACTIONS",
    "REQUIRED_FOLLOWUPS",
    "REASON_CODES",
    "StrategyInformationEdgeDecayGateV2Input",
    "StrategyInformationEdgeDecayGateV2Result",
    "build_strategy_information_edge_decay_gate_v2",
    "strategy_information_edge_decay_gate_v2_payload",
)
