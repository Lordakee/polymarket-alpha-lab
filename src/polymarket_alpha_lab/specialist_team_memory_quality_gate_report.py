"""Readonly Decimal quality gate report for specialist team memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PASS_MEMORY_SAMPLE_FLOOR = Decimal("20")
WATCH_MEMORY_SAMPLE_FLOOR = Decimal("8")
PASS_SETTLED_SAMPLE_FLOOR = Decimal("10")
WATCH_SETTLED_SAMPLE_FLOOR = Decimal("3")
PASS_CALIBRATION_ERROR_CEILING = Decimal("0.100000")
WATCH_CALIBRATION_ERROR_CEILING = Decimal("0.200000")
PASS_SOURCE_FAMILY_COVERAGE_FLOOR = Decimal("0.800000")
WATCH_SOURCE_FAMILY_COVERAGE_FLOOR = Decimal("0.600000")
PASS_MEMORY_AGE_SECONDS_CEILING = Decimal("86400")
WATCH_MEMORY_AGE_SECONDS_CEILING = Decimal("259200")

BLOCKED_REASON_CODES = (
    "specialist_team_memory_sample_blocked",
    "specialist_team_settled_sample_blocked",
    "specialist_team_calibration_error_blocked",
    "specialist_team_source_family_coverage_blocked",
    "specialist_team_memory_freshness_blocked",
    "specialist_team_supabase_persistence_not_ready",
    "specialist_team_schema_contract_not_ready",
)
ATTENTION_REASON_CODES = (
    "specialist_team_memory_sample_watch",
    "specialist_team_settled_sample_watch",
    "specialist_team_calibration_error_watch",
    "specialist_team_source_family_coverage_watch",
    "specialist_team_memory_freshness_watch",
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
    "SpecialistTeamMemoryQualityGateReport",
    "build_specialist_team_memory_quality_gate_report",
)


@dataclass(frozen=True)
class SpecialistTeamMemoryQualityGateReport:
    team: str
    domain: str
    memory_sample_count: Decimal
    settled_sample_count: Decimal
    calibration_error_rate: Decimal
    source_family_coverage_ratio: Decimal
    last_memory_update_age_seconds: Decimal
    supabase_persistence_ready: bool
    schema_contract_ready: bool
    memory_quality_band: str
    can_use_for_screening: bool
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team", _require_public_label("team", self.team))
        object.__setattr__(self, "domain", _require_public_label("domain", self.domain))
        object.__setattr__(
            self,
            "memory_sample_count",
            _require_nonnegative_integral_decimal(
                "memory_sample_count",
                self.memory_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "settled_sample_count",
            _require_nonnegative_integral_decimal(
                "settled_sample_count",
                self.settled_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "calibration_error_rate",
            _require_ratio_decimal("calibration_error_rate", self.calibration_error_rate),
        )
        object.__setattr__(
            self,
            "source_family_coverage_ratio",
            _require_ratio_decimal(
                "source_family_coverage_ratio",
                self.source_family_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "last_memory_update_age_seconds",
            _require_nonnegative_integral_decimal(
                "last_memory_update_age_seconds",
                self.last_memory_update_age_seconds,
            ),
        )
        _require_exact_bool("supabase_persistence_ready", self.supabase_persistence_ready)
        _require_exact_bool("schema_contract_ready", self.schema_contract_ready)
        _require_band("memory_quality_band", self.memory_quality_band)
        _require_exact_bool("can_use_for_screening", self.can_use_for_screening)
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
        _require_hard_flags("SpecialistTeamMemoryQualityGateReport", self)
        _require_sha256_digest("digest", self.digest)
        if self.digest != _digest_for_report(self):
            raise ValueError("digest must match report payload")
        _reject_unsafe_public_payload(
            "SpecialistTeamMemoryQualityGateReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public_payload must be a dict")
        _reject_unsafe_public_payload(
            "SpecialistTeamMemoryQualityGateReport.public_payload",
            payload,
        )
        return payload


def build_specialist_team_memory_quality_gate_report(
    *,
    team: str,
    domain: str,
    memory_sample_count: Decimal,
    settled_sample_count: Decimal,
    calibration_error_rate: Decimal,
    source_family_coverage_ratio: Decimal,
    last_memory_update_age_seconds: Decimal,
    supabase_persistence_ready: bool,
    schema_contract_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SpecialistTeamMemoryQualityGateReport:
    team = _require_public_label("team", team)
    domain = _require_public_label("domain", domain)
    memory_sample_count = _require_nonnegative_integral_decimal(
        "memory_sample_count",
        memory_sample_count,
    )
    settled_sample_count = _require_nonnegative_integral_decimal(
        "settled_sample_count",
        settled_sample_count,
    )
    calibration_error_rate = _require_ratio_decimal(
        "calibration_error_rate",
        calibration_error_rate,
    )
    source_family_coverage_ratio = _require_ratio_decimal(
        "source_family_coverage_ratio",
        source_family_coverage_ratio,
    )
    last_memory_update_age_seconds = _require_nonnegative_integral_decimal(
        "last_memory_update_age_seconds",
        last_memory_update_age_seconds,
    )
    _require_exact_bool("supabase_persistence_ready", supabase_persistence_ready)
    _require_exact_bool("schema_contract_ready", schema_contract_ready)
    values: dict[str, object] = {
        "team": team,
        "domain": domain,
        "memory_sample_count": memory_sample_count,
        "settled_sample_count": settled_sample_count,
        "calibration_error_rate": calibration_error_rate,
        "source_family_coverage_ratio": source_family_coverage_ratio,
        "last_memory_update_age_seconds": last_memory_update_age_seconds,
        "supabase_persistence_ready": supabase_persistence_ready,
        "schema_contract_ready": schema_contract_ready,
        "memory_quality_band": _memory_quality_band(
            memory_sample_count=memory_sample_count,
            settled_sample_count=settled_sample_count,
            calibration_error_rate=calibration_error_rate,
            source_family_coverage_ratio=source_family_coverage_ratio,
            last_memory_update_age_seconds=last_memory_update_age_seconds,
            supabase_persistence_ready=supabase_persistence_ready,
            schema_contract_ready=schema_contract_ready,
        ),
        "blocked_reason_codes": _blocked_reason_codes(
            memory_sample_count=memory_sample_count,
            settled_sample_count=settled_sample_count,
            calibration_error_rate=calibration_error_rate,
            source_family_coverage_ratio=source_family_coverage_ratio,
            last_memory_update_age_seconds=last_memory_update_age_seconds,
            supabase_persistence_ready=supabase_persistence_ready,
            schema_contract_ready=schema_contract_ready,
        ),
        "attention_reason_codes": _attention_reason_codes(
            memory_sample_count=memory_sample_count,
            settled_sample_count=settled_sample_count,
            calibration_error_rate=calibration_error_rate,
            source_family_coverage_ratio=source_family_coverage_ratio,
            last_memory_update_age_seconds=last_memory_update_age_seconds,
        ),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    values["can_use_for_screening"] = (
        values["memory_quality_band"] == "pass"
        and values["blocked_reason_codes"] == ()
        and values["attention_reason_codes"] == ()
    )
    values["ready_ratio"] = _ready_ratio(
        blocked_reason_codes=values["blocked_reason_codes"],
        attention_reason_codes=values["attention_reason_codes"],
    )
    values["digest"] = _digest_for_values(values)
    return SpecialistTeamMemoryQualityGateReport(**values)


def _memory_quality_band(
    *,
    memory_sample_count: Decimal,
    settled_sample_count: Decimal,
    calibration_error_rate: Decimal,
    source_family_coverage_ratio: Decimal,
    last_memory_update_age_seconds: Decimal,
    supabase_persistence_ready: bool,
    schema_contract_ready: bool,
) -> str:
    if _blocked_reason_codes(
        memory_sample_count=memory_sample_count,
        settled_sample_count=settled_sample_count,
        calibration_error_rate=calibration_error_rate,
        source_family_coverage_ratio=source_family_coverage_ratio,
        last_memory_update_age_seconds=last_memory_update_age_seconds,
        supabase_persistence_ready=supabase_persistence_ready,
        schema_contract_ready=schema_contract_ready,
    ):
        return "blocked"
    if _attention_reason_codes(
        memory_sample_count=memory_sample_count,
        settled_sample_count=settled_sample_count,
        calibration_error_rate=calibration_error_rate,
        source_family_coverage_ratio=source_family_coverage_ratio,
        last_memory_update_age_seconds=last_memory_update_age_seconds,
    ):
        return "watch"
    return "pass"


def _blocked_reason_codes(
    *,
    memory_sample_count: Decimal,
    settled_sample_count: Decimal,
    calibration_error_rate: Decimal,
    source_family_coverage_ratio: Decimal,
    last_memory_update_age_seconds: Decimal,
    supabase_persistence_ready: bool,
    schema_contract_ready: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if memory_sample_count < WATCH_MEMORY_SAMPLE_FLOOR:
        codes.append("specialist_team_memory_sample_blocked")
    if settled_sample_count < WATCH_SETTLED_SAMPLE_FLOOR:
        codes.append("specialist_team_settled_sample_blocked")
    if calibration_error_rate > WATCH_CALIBRATION_ERROR_CEILING:
        codes.append("specialist_team_calibration_error_blocked")
    if source_family_coverage_ratio < WATCH_SOURCE_FAMILY_COVERAGE_FLOOR:
        codes.append("specialist_team_source_family_coverage_blocked")
    if last_memory_update_age_seconds > WATCH_MEMORY_AGE_SECONDS_CEILING:
        codes.append("specialist_team_memory_freshness_blocked")
    if supabase_persistence_ready is not True:
        codes.append("specialist_team_supabase_persistence_not_ready")
    if schema_contract_ready is not True:
        codes.append("specialist_team_schema_contract_not_ready")
    return tuple(codes)


def _attention_reason_codes(
    *,
    memory_sample_count: Decimal,
    settled_sample_count: Decimal,
    calibration_error_rate: Decimal,
    source_family_coverage_ratio: Decimal,
    last_memory_update_age_seconds: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if WATCH_MEMORY_SAMPLE_FLOOR <= memory_sample_count < PASS_MEMORY_SAMPLE_FLOOR:
        codes.append("specialist_team_memory_sample_watch")
    if WATCH_SETTLED_SAMPLE_FLOOR <= settled_sample_count < PASS_SETTLED_SAMPLE_FLOOR:
        codes.append("specialist_team_settled_sample_watch")
    if PASS_CALIBRATION_ERROR_CEILING < calibration_error_rate <= WATCH_CALIBRATION_ERROR_CEILING:
        codes.append("specialist_team_calibration_error_watch")
    if (
        WATCH_SOURCE_FAMILY_COVERAGE_FLOOR
        <= source_family_coverage_ratio
        < PASS_SOURCE_FAMILY_COVERAGE_FLOOR
    ):
        codes.append("specialist_team_source_family_coverage_watch")
    if PASS_MEMORY_AGE_SECONDS_CEILING < last_memory_update_age_seconds <= WATCH_MEMORY_AGE_SECONDS_CEILING:
        codes.append("specialist_team_memory_freshness_watch")
    return tuple(codes)


def _ready_ratio(
    *,
    blocked_reason_codes: object,
    attention_reason_codes: object,
) -> Decimal:
    if blocked_reason_codes:
        return ZERO
    attention_count = Decimal(len(attention_reason_codes)).quantize(COUNT_QUANT)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(ONE - (attention_count * Decimal("0.080000")))


def _validate_report_consistency(report: SpecialistTeamMemoryQualityGateReport) -> None:
    blocked_reason_codes = _blocked_reason_codes(
        memory_sample_count=report.memory_sample_count,
        settled_sample_count=report.settled_sample_count,
        calibration_error_rate=report.calibration_error_rate,
        source_family_coverage_ratio=report.source_family_coverage_ratio,
        last_memory_update_age_seconds=report.last_memory_update_age_seconds,
        supabase_persistence_ready=report.supabase_persistence_ready,
        schema_contract_ready=report.schema_contract_ready,
    )
    attention_reason_codes = _attention_reason_codes(
        memory_sample_count=report.memory_sample_count,
        settled_sample_count=report.settled_sample_count,
        calibration_error_rate=report.calibration_error_rate,
        source_family_coverage_ratio=report.source_family_coverage_ratio,
        last_memory_update_age_seconds=report.last_memory_update_age_seconds,
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match report inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match report inputs")
    if report.memory_quality_band != _memory_quality_band(
        memory_sample_count=report.memory_sample_count,
        settled_sample_count=report.settled_sample_count,
        calibration_error_rate=report.calibration_error_rate,
        source_family_coverage_ratio=report.source_family_coverage_ratio,
        last_memory_update_age_seconds=report.last_memory_update_age_seconds,
        supabase_persistence_ready=report.supabase_persistence_ready,
        schema_contract_ready=report.schema_contract_ready,
    ):
        raise ValueError("memory_quality_band must match report inputs")
    if report.can_use_for_screening is not (
        report.memory_quality_band == "pass"
        and report.blocked_reason_codes == ()
        and report.attention_reason_codes == ()
    ):
        raise ValueError("can_use_for_screening must match report inputs")
    if report.ready_ratio != _ready_ratio(
        blocked_reason_codes=report.blocked_reason_codes,
        attention_reason_codes=report.attention_reason_codes,
    ):
        raise ValueError("ready_ratio must match report inputs")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_public_text(field_name, normalized)
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize_ratio(decimal_value)


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANT)


def _require_exact_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_band(field_name: str, value: object) -> None:
    if value not in {"pass", "watch", "blocked"}:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        if value not in allowed_codes:
            _reject_unsafe_public_text(field_name, value)
            raise ValueError(f"{field_name} contains unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _digest_for_report(report: SpecialistTeamMemoryQualityGateReport) -> str:
    return _digest_for_values(asdict(report))


def _digest_for_values(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "digest"
    }
    _reject_unsafe_public_payload("digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
    elif type(value) is list or type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        if value in BLOCKED_REASON_CODES or value in ATTENTION_REASON_CODES:
            return
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public payload in {label}")
