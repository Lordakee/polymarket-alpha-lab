"""Read-only probability forecast model disagreement report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


PROBABILITY_EVENT_FORECAST_MODEL_DISAGREEMENT_STATUSES = (
    "pass",
    "attention",
    "blocker",
)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_PROBABILITY_FIELDS = (
    "naive_probability",
    "book_imbalance_probability",
    "llm_probability",
    "specialist_probability",
    "max_allowed_spread_probability",
)
_PUBLIC_FIELDS = frozenset(
    (
        "naive_probability",
        "book_imbalance_probability",
        "llm_probability",
        "specialist_probability",
        "max_allowed_spread_probability",
        "disagreement_status",
        "probability_range",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
        "payload_digest",
    ),
)
_REASON_CODES = (
    "forecast_model_disagreement_attention",
    "forecast_model_disagreement_blocker",
    "forecast_model_disagreement_pass",
    "spread_exceeds_allowed_probability",
    "spread_exceeds_double_allowed_probability",
)
_NEXT_STEPS = (
    "block_and_escalate_model_disagreement",
    "continue_readonly_monitoring",
    "manual_review_model_spread",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "candidate",
    "condition" + "_id",
    "credential",
    "data" + "base",
    "dsn",
    "exec" + "ute",
    "exec" + "ution",
    "key",
    "li" + "ve",
    "market" + "_id",
    "market" + "_slug",
    "net" + "work",
    "or" + "der",
    "persist",
    "private",
    "secret",
    "signature",
    "signing",
    "source" + "_url",
    "table",
    "token",
    "trad" + "e",
    "wal" + "let",
)


@dataclass(frozen=True)
class ProbabilityEventForecastModelDisagreementReport:
    naive_probability: Decimal
    book_imbalance_probability: Decimal
    llm_probability: Decimal
    specialist_probability: Decimal
    max_allowed_spread_probability: Decimal
    disagreement_status: str
    probability_range: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventForecastModelDisagreementReport:
            raise ValueError(
                "report must be exactly ProbabilityEventForecastModelDisagreementReport",
            )
        for field_name in _PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_range",
            _normalize_probability("probability_range", self.probability_range),
        )
        _require_status("disagreement_status", self.disagreement_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _public_payload_without_digest(self))
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_forecast_model_disagreement_report_payload(self)


def build_probability_event_forecast_model_disagreement_report(
    *,
    naive_probability: Decimal,
    book_imbalance_probability: Decimal,
    llm_probability: Decimal,
    specialist_probability: Decimal,
    max_allowed_spread_probability: Decimal,
) -> ProbabilityEventForecastModelDisagreementReport:
    """Build a deterministic report-only snapshot of model probability disagreement."""

    probabilities = tuple(
        _normalize_probability(field_name, value)
        for field_name, value in (
            ("naive_probability", naive_probability),
            ("book_imbalance_probability", book_imbalance_probability),
            ("llm_probability", llm_probability),
            ("specialist_probability", specialist_probability),
        )
    )
    allowed_spread = _normalize_probability(
        "max_allowed_spread_probability",
        max_allowed_spread_probability,
    )
    if allowed_spread <= _ZERO:
        raise ValueError("max_allowed_spread_probability must be positive")
    probability_range = _subtract_decimal(max(probabilities), min(probabilities))
    status = _disagreement_status(
        probability_range=probability_range,
        max_allowed_spread_probability=allowed_spread,
    )
    return ProbabilityEventForecastModelDisagreementReport(
        naive_probability=probabilities[0],
        book_imbalance_probability=probabilities[1],
        llm_probability=probabilities[2],
        specialist_probability=probabilities[3],
        max_allowed_spread_probability=allowed_spread,
        disagreement_status=status,
        probability_range=probability_range,
        reason_codes=_reason_codes(status),
        manual_next_step=_manual_next_step(status),
    )


def probability_event_forecast_model_disagreement_report_payload(
    report: ProbabilityEventForecastModelDisagreementReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ProbabilityEventForecastModelDisagreementReport:
        _require_hard_flags("report", report)
        _verify_digest(report)
        payload = _public_payload(report)
    elif type(report) is dict:
        _validate_public_payload_schema(report)
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ProbabilityEventForecastModelDisagreementReport",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def probability_event_forecast_model_disagreement_report_digest(
    report: ProbabilityEventForecastModelDisagreementReport,
) -> dict[str, Any]:
    payload = probability_event_forecast_model_disagreement_report_payload(report)
    return {
        "disagreement_status": payload["disagreement_status"],
        "probability_range": payload["probability_range"],
        "reason_codes": payload["reason_codes"],
        "manual_next_step": payload["manual_next_step"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
        "payload_digest": payload["payload_digest"],
    }


def _disagreement_status(
    *,
    probability_range: Decimal,
    max_allowed_spread_probability: Decimal,
) -> str:
    if probability_range > _multiply_decimal(
        max_allowed_spread_probability,
        Decimal("2"),
    ):
        return "blocker"
    if probability_range > max_allowed_spread_probability:
        return "attention"
    return "pass"


def _reason_codes(status: str) -> tuple[str, ...]:
    if status == "pass":
        return ("forecast_model_disagreement_pass",)
    if status == "attention":
        return (
            "forecast_model_disagreement_attention",
            "spread_exceeds_allowed_probability",
        )
    return (
        "forecast_model_disagreement_blocker",
        "spread_exceeds_double_allowed_probability",
    )


def _manual_next_step(status: str) -> str:
    if status == "pass":
        return "continue_readonly_monitoring"
    if status == "attention":
        return "manual_review_model_spread"
    return "block_and_escalate_model_disagreement"


def _public_payload(
    report: ProbabilityEventForecastModelDisagreementReport,
) -> dict[str, Any]:
    payload = _public_payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    return _json_ready(payload)


def _public_payload_without_digest(
    report: ProbabilityEventForecastModelDisagreementReport,
) -> dict[str, Any]:
    return {
        "naive_probability": report.naive_probability,
        "book_imbalance_probability": report.book_imbalance_probability,
        "llm_probability": report.llm_probability,
        "specialist_probability": report.specialist_probability,
        "max_allowed_spread_probability": report.max_allowed_spread_probability,
        "disagreement_status": report.disagreement_status,
        "probability_range": report.probability_range,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_report_consistency(
    report: ProbabilityEventForecastModelDisagreementReport,
) -> None:
    probabilities = (
        report.naive_probability,
        report.book_imbalance_probability,
        report.llm_probability,
        report.specialist_probability,
    )
    expected_range = _subtract_decimal(max(probabilities), min(probabilities))
    if report.probability_range != expected_range:
        raise ValueError("probability_range must match model probabilities")
    expected_status = _disagreement_status(
        probability_range=report.probability_range,
        max_allowed_spread_probability=report.max_allowed_spread_probability,
    )
    if report.disagreement_status != expected_status:
        raise ValueError("disagreement_status must match probability_range")
    if report.reason_codes != _reason_codes(report.disagreement_status):
        raise ValueError("reason_codes must match disagreement_status")
    if report.manual_next_step != _manual_next_step(report.disagreement_status):
        raise ValueError("manual_next_step must match disagreement_status")


def _apply_or_verify_digest(
    report: ProbabilityEventForecastModelDisagreementReport,
) -> None:
    expected = _payload_digest_from_report(report)
    if report.payload_digest == "":
        object.__setattr__(report, "payload_digest", expected)
        return
    _require_digest("payload_digest", report.payload_digest)
    if report.payload_digest != expected:
        raise ValueError("payload_digest does not match report fields")


def _verify_digest(report: ProbabilityEventForecastModelDisagreementReport) -> None:
    _require_digest("payload_digest", report.payload_digest)
    if report.payload_digest != _payload_digest_from_report(report):
        raise ValueError("payload_digest does not match report fields")


def _payload_digest_from_report(
    report: ProbabilityEventForecastModelDisagreementReport,
) -> str:
    return _payload_digest(_json_ready(_public_payload_without_digest(report)))


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    expected = _payload_digest({key: value for key, value in payload.items() if key != "payload_digest"})
    if payload["payload_digest"] != expected:
        raise ValueError("payload_digest does not match public payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (left - right).quantize(_QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (left * right).quantize(_QUANTUM)


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in PROBABILITY_EVENT_FORECAST_MODEL_DISAGREEMENT_STATUSES:
        raise ValueError(f"{name} must be a supported disagreement_status")


def _require_next_step(name: str, value: object) -> None:
    if type(value) is not str or value not in _NEXT_STEPS:
        raise ValueError(f"{name} must be a supported manual_next_step")


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    previous = ""
    normalized = []
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in _REASON_CODES:
            raise ValueError(f"{name} must contain supported reason codes")
        if previous and reason_code <= previous:
            raise ValueError(f"{name} must be sorted and unique")
        previous = reason_code
        normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return tuple(normalized)


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name}.{field_name} must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{name} must be a sha256 hex digest")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_public_keys("payload", payload, _PUBLIC_FIELDS)
    for field_name in _PROBABILITY_FIELDS:
        _normalize_probability_decimal_string(
            f"payload.{field_name}",
            payload.get(field_name),
        )
    _normalize_probability_decimal_string(
        "payload.probability_range",
        payload.get("probability_range"),
    )
    _require_status("payload.disagreement_status", payload.get("disagreement_status"))
    _validate_public_reason_codes(payload.get("reason_codes"))
    _require_next_step("payload.manual_next_step", payload.get("manual_next_step"))
    _require_hard_flags("payload", _DictFlags(payload))
    _require_digest("payload.payload_digest", payload.get("payload_digest"))


def _require_public_keys(name: str, payload: dict[str, Any], expected: frozenset[str]) -> None:
    actual = set(payload)
    if actual != expected:
        raise ValueError(f"{name} must contain only public report fields")


def _normalize_probability_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as error:
        raise ValueError(f"{name} must be a decimal string") from error
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    if value != _decimal_text(decimal_value):
        raise ValueError(f"{name} must be a normalized decimal string")
    return decimal_value


def _validate_public_reason_codes(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.reason_codes must be a public list")
    previous = ""
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in _REASON_CODES:
            raise ValueError("payload.reason_codes must contain supported reason codes")
        if previous and reason_code <= previous:
            raise ValueError("payload.reason_codes must be sorted and unique")
        previous = reason_code
    if not value:
        raise ValueError("payload.reason_codes must not be empty")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return _decimal_text(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    return value


def _decimal_text(value: Decimal) -> str:
    return f"{_normalize_decimal('decimal', value):.6f}"


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        if type(item) is dict:
            stack.extend(item.values())
            stack.extend(item.keys())
            continue
        if type(item) is list or type(item) is tuple:
            stack.extend(item)
            continue
        if type(item) is str:
            lowered = item.lower()
            if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{name} must contain only public report fields")


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


__all__ = (
    "PROBABILITY_EVENT_FORECAST_MODEL_DISAGREEMENT_STATUSES",
    "ProbabilityEventForecastModelDisagreementReport",
    "build_probability_event_forecast_model_disagreement_report",
    "probability_event_forecast_model_disagreement_report_digest",
    "probability_event_forecast_model_disagreement_report_payload",
)
