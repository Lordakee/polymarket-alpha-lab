"""Pure read-only expected utility rank readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import JSONEncoder
from typing import Any


__all__ = (
    "EXPECTED_UTILITY_RANK_PROBABILITY_FIELDS",
    "ProbabilityEventExpectedUtilityRankReadinessInput",
    "ProbabilityEventExpectedUtilityRankReadinessReport",
    "build_probability_event_expected_utility_rank_readiness_report",
    "probability_event_expected_utility_rank_payload_digest",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
EXPECTED_UTILITY_RANK_PROBABILITY_FIELDS = (
    "net_edge_probability",
    "confidence_probability",
    "liquidity_probability",
    "cost_probability",
    "capital_lockup_probability",
)

READY_REASON = "probability_event_expected_utility_rank_ready"
READY_STEP = (
    "Manually compare this report-only candidate against other readonly "
    "probability events before any operator-authorized action."
)
ATTENTION_STEP = (
    "Manually review attention probability inputs before comparing this "
    "paper-only candidate against other readonly events."
)
BLOCKED_STEP = (
    "Resolve blocked probability inputs before manually ranking this "
    "paper-only candidate."
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ProbabilityEventExpectedUtilityRankReadinessInput(_FinalDataclass):
    net_edge_probability: Decimal
    confidence_probability: Decimal
    liquidity_probability: Decimal
    cost_probability: Decimal
    capital_lockup_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventExpectedUtilityRankReadinessInput,
            "expected utility rank input",
        )
        for field_name in EXPECTED_UTILITY_RANK_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("expected utility rank input", self)


@dataclass(frozen=True)
class ProbabilityEventExpectedUtilityRankReadinessReport(_FinalDataclass):
    rank_status: str
    expected_utility_score: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, object]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventExpectedUtilityRankReadinessReport,
            "expected utility rank report",
        )
        object.__setattr__(self, "rank_status", _normalize_rank_status(self.rank_status))
        object.__setattr__(
            self,
            "expected_utility_score",
            _normalize_probability("expected_utility_score", self.expected_utility_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _normalize_manual_next_step(self.manual_next_step),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        if type(self.payload_digest) is not str or not self.payload_digest:
            raise ValueError("payload_digest must be a non-empty string")
        _require_hard_flags("expected utility rank report", self)
        _validate_report(self)


def build_probability_event_expected_utility_rank_readiness_report(
    readiness: ProbabilityEventExpectedUtilityRankReadinessInput,
) -> ProbabilityEventExpectedUtilityRankReadinessReport:
    if type(readiness) is not ProbabilityEventExpectedUtilityRankReadinessInput:
        raise ValueError(
            "readiness must be a ProbabilityEventExpectedUtilityRankReadinessInput",
        )
    _require_hard_flags("expected utility rank input", readiness)

    blocked_codes = tuple(
        f"probability_event_expected_utility_{_reason_name(field_name)}_blocked"
        for field_name in EXPECTED_UTILITY_RANK_PROBABILITY_FIELDS
        if getattr(readiness, field_name) == ZERO
    )
    attention_codes = tuple(
        f"probability_event_expected_utility_{_reason_name(field_name)}_attention"
        for field_name in EXPECTED_UTILITY_RANK_PROBABILITY_FIELDS
        if ZERO < getattr(readiness, field_name) < ONE
    )
    if blocked_codes:
        rank_status = "manual_rank_blocked"
        manual_next_step = BLOCKED_STEP
        reason_codes = blocked_codes + attention_codes
    elif attention_codes:
        rank_status = "manual_rank_attention"
        manual_next_step = ATTENTION_STEP
        reason_codes = attention_codes
    else:
        rank_status = "ready_for_manual_rank"
        manual_next_step = READY_STEP
        reason_codes = (READY_REASON,)

    score = _expected_utility_score(readiness)
    payload = _payload(
        rank_status=rank_status,
        expected_utility_score=score,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )

    return ProbabilityEventExpectedUtilityRankReadinessReport(
        rank_status=rank_status,
        expected_utility_score=score,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        public_payload=payload,
        payload_digest=probability_event_expected_utility_rank_payload_digest(payload),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_expected_utility_rank_payload_digest(
    payload: dict[str, object],
) -> str:
    normalized_payload = _normalize_public_payload(payload)
    encoded = JSONEncoder(
        sort_keys=True,
        separators=(",", ":"),
    ).encode(normalized_payload).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_rank_status(value: object) -> str:
    if type(value) is not str:
        raise ValueError("rank_status must be a string")
    if value not in {
        "ready_for_manual_rank",
        "manual_rank_attention",
        "manual_rank_blocked",
    }:
        raise ValueError("rank_status must be a supported manual rank status")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("reason_codes must contain non-empty strings")
        if reason_code != reason_code.strip():
            raise ValueError("reason_codes must be stripped")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _normalize_manual_next_step(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("manual_next_step must be a non-empty string")
    if value != value.strip():
        raise ValueError("manual_next_step must be stripped")
    _reject_unsafe_text("manual_next_step", value)
    return value


def _normalize_public_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        raise ValueError("public_payload must be a dict")
    expected_keys = {
        "rank_status",
        "expected_utility_score",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != expected_keys:
        raise ValueError("public_payload has unexpected keys")
    if type(payload["expected_utility_score"]) is not str:
        raise ValueError("public_payload expected_utility_score must be text")
    _decimal_text_to_probability(payload["expected_utility_score"])
    if type(payload["reason_codes"]) is not list:
        raise ValueError("public_payload reason_codes must be a list")
    reason_codes = tuple(payload["reason_codes"])
    normalized_reason_codes = _normalize_reason_codes(reason_codes)
    normalized = {
        "rank_status": _normalize_rank_status(payload["rank_status"]),
        "expected_utility_score": payload["expected_utility_score"],
        "reason_codes": list(normalized_reason_codes),
        "manual_next_step": _normalize_manual_next_step(payload["manual_next_step"]),
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    _require_hard_flags("public_payload", _PayloadFlags(normalized))
    _reject_unsafe_payload(normalized)
    return normalized


def _decimal_text_to_probability(value: str) -> Decimal:
    if value != value.strip():
        raise ValueError("decimal text must be stripped")
    if "." not in value or len(value.rsplit(".", maxsplit=1)[1]) != 6:
        raise ValueError("decimal text must use six decimal places")
    return _normalize_probability("decimal text", Decimal(value))


def _payload(
    *,
    rank_status: str,
    expected_utility_score: Decimal,
    reason_codes: tuple[str, ...],
    manual_next_step: str,
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "rank_status": rank_status,
        "expected_utility_score": _decimal_text(expected_utility_score),
        "reason_codes": list(reason_codes),
        "manual_next_step": manual_next_step,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _expected_utility_score(
    readiness: ProbabilityEventExpectedUtilityRankReadinessInput,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ONE
        for field_name in EXPECTED_UTILITY_RANK_PROBABILITY_FIELDS:
            score *= getattr(readiness, field_name)
        return score.quantize(QUANTUM)


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _validate_report(
    report: ProbabilityEventExpectedUtilityRankReadinessReport,
) -> None:
    expected_payload = _payload(
        rank_status=report.rank_status,
        expected_utility_score=report.expected_utility_score,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    if report.public_payload != expected_payload:
        raise ValueError("public_payload must match report fields")
    if report.payload_digest != probability_event_expected_utility_rank_payload_digest(
        report.public_payload,
    ):
        raise ValueError("payload_digest must match public_payload")
    if report.rank_status == "ready_for_manual_rank":
        if report.expected_utility_score != ONE:
            raise ValueError("ready_for_manual_rank requires expected_utility_score=1.000000")
        if report.reason_codes != (READY_REASON,):
            raise ValueError("ready_for_manual_rank requires ready reason code")
        if report.manual_next_step != READY_STEP:
            raise ValueError("ready_for_manual_rank requires ready manual next step")
    elif report.rank_status == "manual_rank_blocked":
        if not any(reason_code.endswith("_blocked") for reason_code in report.reason_codes):
            raise ValueError("manual_rank_blocked requires a blocked reason code")
        if report.manual_next_step != BLOCKED_STEP:
            raise ValueError("manual_rank_blocked requires blocked manual next step")
    else:
        if any(reason_code.endswith("_blocked") for reason_code in report.reason_codes):
            raise ValueError("manual_rank_attention cannot include blocked reason codes")
        if not all(reason_code.endswith("_attention") for reason_code in report.reason_codes):
            raise ValueError("manual_rank_attention requires attention reason codes")
        if report.manual_next_step != ATTENTION_STEP:
            raise ValueError("manual_rank_attention requires attention manual next step")


def _reject_unsafe_payload(payload: dict[str, object]) -> None:
    for key, value in payload.items():
        _reject_unsafe_text("public_payload key", key)
        if isinstance(value, str):
            _reject_unsafe_text(key, value)
        elif isinstance(value, list):
            for item in value:
                _reject_unsafe_text(key, item)


def _reject_unsafe_text(label: str, value: object) -> None:
    if type(value) is not str:
        return
    lowered = value.lower()
    forbidden_fragments = (
        "live",
        "authentication",
        "credential",
        "wallet",
        "private_key",
        "api_key",
        "signature",
        "submit",
        "cancel",
        "replace",
        "automated execution",
    )
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise ValueError(f"{label} contains unsafe execution text")


def _reason_name(field_name: str) -> str:
    return field_name.removesuffix("_probability")


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")


@dataclass(frozen=True)
class _PayloadFlags:
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
