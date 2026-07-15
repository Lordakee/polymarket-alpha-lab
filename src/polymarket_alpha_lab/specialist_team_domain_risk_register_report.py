"""Pure readonly risk register report for specialist team domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
STALE_RISK_REVIEW_AGE_SECONDS = Decimal("2592000")
BASE_READY_CHECK_COUNT = Decimal("5")
UNMITIGATED_RISK_PENALTY_WEIGHT = Decimal("2")

UNMITIGATED_RISKS_PRESENT = "specialist_team_domain_unmitigated_risks_present"
PLAYBOOK_NOT_READY = "specialist_team_domain_playbook_not_ready"
SOURCE_RELIABILITY_NOT_READY = (
    "specialist_team_domain_source_reliability_not_ready"
)
MEMORY_QUALITY_NOT_READY = "specialist_team_domain_memory_quality_not_ready"
NO_KNOWN_RISKS_RECORDED = "specialist_team_domain_no_known_risks_recorded"
RISK_REVIEW_STALE = "specialist_team_domain_risk_review_stale"

BLOCKED_REASON_CODES = (
    UNMITIGATED_RISKS_PRESENT,
    PLAYBOOK_NOT_READY,
    SOURCE_RELIABILITY_NOT_READY,
    MEMORY_QUALITY_NOT_READY,
)
ATTENTION_REASON_CODES = (
    NO_KNOWN_RISKS_RECORDED,
    RISK_REVIEW_STALE,
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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

__all__ = (
    "SpecialistTeamDomainRiskRegisterReport",
    "build_specialist_team_domain_risk_register_report",
)


@dataclass(frozen=True)
class SpecialistTeamDomainRiskRegisterReport:
    domain: str
    team_code: str
    known_risk_count: Decimal
    unmitigated_risk_count: Decimal
    playbook_ready: bool
    source_reliability_ready: bool
    memory_quality_ready: bool
    last_risk_review_age_seconds: Decimal
    risk_register_ready: bool
    risk_score: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamDomainRiskRegisterReport:
            raise ValueError(
                "report must be exactly SpecialistTeamDomainRiskRegisterReport",
            )
        object.__setattr__(self, "domain", _require_public_label("domain", self.domain))
        object.__setattr__(
            self,
            "team_code",
            _require_public_label("team_code", self.team_code),
        )
        object.__setattr__(
            self,
            "known_risk_count",
            _require_integral_count_decimal("known_risk_count", self.known_risk_count),
        )
        object.__setattr__(
            self,
            "unmitigated_risk_count",
            _require_integral_count_decimal(
                "unmitigated_risk_count",
                self.unmitigated_risk_count,
            ),
        )
        if self.unmitigated_risk_count > self.known_risk_count:
            raise ValueError("unmitigated_risk_count must be <= known_risk_count")
        _require_exact_bool("playbook_ready", self.playbook_ready)
        _require_exact_bool("source_reliability_ready", self.source_reliability_ready)
        _require_exact_bool("memory_quality_ready", self.memory_quality_ready)
        object.__setattr__(
            self,
            "last_risk_review_age_seconds",
            _require_integral_count_decimal(
                "last_risk_review_age_seconds",
                self.last_risk_review_age_seconds,
            ),
        )
        _require_exact_bool("risk_register_ready", self.risk_register_ready)
        object.__setattr__(
            self,
            "risk_score",
            _require_ratio_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_hard_flags("SpecialistTeamDomainRiskRegisterReport", self)
        _require_sha256_digest("digest", self.digest)
        if self.digest != _digest_for_report(self):
            raise ValueError("digest must match report payload")
        if self.risk_register_ready != (
            self.blocked_reason_codes == () and self.attention_reason_codes == ()
        ):
            raise ValueError("risk_register_ready must match reason codes")
        if self.risk_score != _score_for_report(self):
            raise ValueError("risk_score must match report inputs")
        if self.ready_ratio != self.risk_score:
            raise ValueError("ready_ratio must match risk_score")
        _reject_unsafe_public_payload(
            "SpecialistTeamDomainRiskRegisterReport",
            _payload_value(asdict(self)),
        )

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public_payload must be a dict")
        _reject_unsafe_public_payload(
            "SpecialistTeamDomainRiskRegisterReport.public_payload",
            payload,
        )
        return payload


def build_specialist_team_domain_risk_register_report(
    *,
    domain: str,
    team_code: str,
    known_risk_count: Decimal,
    unmitigated_risk_count: Decimal,
    playbook_ready: bool,
    source_reliability_ready: bool,
    memory_quality_ready: bool,
    last_risk_review_age_seconds: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SpecialistTeamDomainRiskRegisterReport:
    domain = _require_public_label("domain", domain)
    team_code = _require_public_label("team_code", team_code)
    known_risk_count = _require_integral_count_decimal(
        "known_risk_count",
        known_risk_count,
    )
    unmitigated_risk_count = _require_integral_count_decimal(
        "unmitigated_risk_count",
        unmitigated_risk_count,
    )
    if unmitigated_risk_count > known_risk_count:
        raise ValueError("unmitigated_risk_count must be <= known_risk_count")
    _require_exact_bool("playbook_ready", playbook_ready)
    _require_exact_bool("source_reliability_ready", source_reliability_ready)
    _require_exact_bool("memory_quality_ready", memory_quality_ready)
    last_risk_review_age_seconds = _require_integral_count_decimal(
        "last_risk_review_age_seconds",
        last_risk_review_age_seconds,
    )
    _require_hard_flag("paper_only", paper_only)
    _require_hard_flag("report_only", report_only)
    _require_hard_flag("readonly", readonly)

    blocked_reason_codes = _blocked_reason_codes(
        unmitigated_risk_count=unmitigated_risk_count,
        playbook_ready=playbook_ready,
        source_reliability_ready=source_reliability_ready,
        memory_quality_ready=memory_quality_ready,
    )
    attention_reason_codes = _attention_reason_codes(
        known_risk_count=known_risk_count,
        last_risk_review_age_seconds=last_risk_review_age_seconds,
    )
    values: dict[str, object] = {
        "domain": domain,
        "team_code": team_code,
        "known_risk_count": known_risk_count,
        "unmitigated_risk_count": unmitigated_risk_count,
        "playbook_ready": playbook_ready,
        "source_reliability_ready": source_reliability_ready,
        "memory_quality_ready": memory_quality_ready,
        "last_risk_review_age_seconds": last_risk_review_age_seconds,
        "risk_register_ready": blocked_reason_codes == ()
        and attention_reason_codes == (),
        "risk_score": _risk_score(
            known_risk_count=known_risk_count,
            unmitigated_risk_count=unmitigated_risk_count,
            playbook_ready=playbook_ready,
            source_reliability_ready=source_reliability_ready,
            memory_quality_ready=memory_quality_ready,
            last_risk_review_age_seconds=last_risk_review_age_seconds,
        ),
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    values["ready_ratio"] = values["risk_score"]
    values["digest"] = _digest_for_values(values)
    return SpecialistTeamDomainRiskRegisterReport(**values)


def _blocked_reason_codes(
    *,
    unmitigated_risk_count: Decimal,
    playbook_ready: bool,
    source_reliability_ready: bool,
    memory_quality_ready: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if unmitigated_risk_count > ZERO_COUNT:
        reason_codes.append(UNMITIGATED_RISKS_PRESENT)
    if not playbook_ready:
        reason_codes.append(PLAYBOOK_NOT_READY)
    if not source_reliability_ready:
        reason_codes.append(SOURCE_RELIABILITY_NOT_READY)
    if not memory_quality_ready:
        reason_codes.append(MEMORY_QUALITY_NOT_READY)
    return tuple(reason_codes)


def _attention_reason_codes(
    *,
    known_risk_count: Decimal,
    last_risk_review_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if known_risk_count == ZERO_COUNT:
        reason_codes.append(NO_KNOWN_RISKS_RECORDED)
    if last_risk_review_age_seconds > STALE_RISK_REVIEW_AGE_SECONDS:
        reason_codes.append(RISK_REVIEW_STALE)
    return tuple(reason_codes)


def _score_for_report(report: SpecialistTeamDomainRiskRegisterReport) -> Decimal:
    return _risk_score(
        known_risk_count=report.known_risk_count,
        unmitigated_risk_count=report.unmitigated_risk_count,
        playbook_ready=report.playbook_ready,
        source_reliability_ready=report.source_reliability_ready,
        memory_quality_ready=report.memory_quality_ready,
        last_risk_review_age_seconds=report.last_risk_review_age_seconds,
    )


def _risk_score(
    *,
    known_risk_count: Decimal,
    unmitigated_risk_count: Decimal,
    playbook_ready: bool,
    source_reliability_ready: bool,
    memory_quality_ready: bool,
    last_risk_review_age_seconds: Decimal,
) -> Decimal:
    ready_checks = ZERO_COUNT
    if known_risk_count > ZERO_COUNT:
        ready_checks += COUNT_QUANT
    if playbook_ready:
        ready_checks += COUNT_QUANT
    if source_reliability_ready:
        ready_checks += COUNT_QUANT
    if memory_quality_ready:
        ready_checks += COUNT_QUANT
    if last_risk_review_age_seconds <= STALE_RISK_REVIEW_AGE_SECONDS:
        ready_checks += COUNT_QUANT
    denominator = BASE_READY_CHECK_COUNT + (
        unmitigated_risk_count * UNMITIGATED_RISK_PENALTY_WEIGHT
    )
    return _ratio(ready_checks, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
        if value < ZERO_RATIO:
            value = ZERO_RATIO
        if value > ONE_RATIO:
            value = ONE_RATIO
        return value.quantize(RATIO_QUANT)


def _digest_for_report(report: SpecialistTeamDomainRiskRegisterReport) -> str:
    return _digest_for_values(
        {
            "domain": report.domain,
            "team_code": report.team_code,
            "known_risk_count": report.known_risk_count,
            "unmitigated_risk_count": report.unmitigated_risk_count,
            "playbook_ready": report.playbook_ready,
            "source_reliability_ready": report.source_reliability_ready,
            "memory_quality_ready": report.memory_quality_ready,
            "last_risk_review_age_seconds": report.last_risk_review_age_seconds,
            "risk_register_ready": report.risk_register_ready,
            "risk_score": report.risk_score,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _digest_for_values(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in {str, bool} or value is None:
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "":
        raise ValueError(f"{name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    _reject_unsafe_public_payload(name, value)
    return value


def _require_integral_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if value < ZERO_COUNT:
        raise ValueError(f"{name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if value < ZERO_RATIO:
        raise ValueError(f"{name} must be >= 0.000000")
    if value > ONE_RATIO:
        raise ValueError(f"{name} must be <= 1.000000")
    if value != value.quantize(RATIO_QUANT):
        raise ValueError(f"{name} must use six decimal places or fewer")
    return value.quantize(RATIO_QUANT)


def _require_exact_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be exactly bool")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_hard_flag(name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{name} must be True")


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{name} must contain strings")
        if item not in allowed_reason_codes:
            raise ValueError(f"{name} must contain known reason codes")
        if item in normalized:
            raise ValueError(f"{name} must not contain duplicates")
        normalized.append(item)
    return tuple(normalized)


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")


def _reject_unsafe_public_payload(name: str, value: object) -> None:
    if isinstance(value, str):
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{name} unsafe public payload")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_payload(name, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(name, item)
