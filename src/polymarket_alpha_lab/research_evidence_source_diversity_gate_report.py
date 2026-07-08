"""Pure report-only source diversity gate for candidate research evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_CONFIG_VERSION = (
    "research-evidence-source-diversity-gate-report-v0"
)
RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_CHECK_COUNT = Decimal("3.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "url",
    "uri",
    "source_id",
    "source_ref",
    "source_reference",
    "source_locator",
    "source_text",
    "market_id",
    "market_slug",
    "question",
    "candidate_id",
    "candidate_slug",
    "wallet",
    "auth",
    "order",
)
_REASON_CODE_SEQUENCE = (
    "independent_source_classes_pass",
    "independent_source_classes_watch",
    "independent_source_classes_block",
    "stale_source_concentration_pass",
    "stale_source_concentration_watch",
    "stale_source_concentration_block",
    "contradiction_coverage_pass",
    "contradiction_coverage_watch",
    "contradiction_coverage_block",
)


@dataclass(frozen=True)
class ResearchEvidenceSourceDiversityGateConfig:
    config_version: str = DEFAULT_RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_CONFIG_VERSION
    min_pass_aggregate_source_count: Decimal = Decimal("6.000000")
    min_watch_aggregate_source_count: Decimal = Decimal("4.000000")
    min_pass_independent_source_class_count: Decimal = Decimal("3.000000")
    min_watch_independent_source_class_count: Decimal = Decimal("2.000000")
    max_pass_stale_source_concentration_ratio: Decimal = Decimal("0.250000")
    max_watch_stale_source_concentration_ratio: Decimal = Decimal("0.500000")
    min_pass_contradiction_coverage_ratio: Decimal = Decimal("1.000000")
    min_watch_contradiction_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceSourceDiversityGateConfig:
            raise TypeError(
                "ResearchEvidenceSourceDiversityGateConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceSourceDiversityGateConfig:
            raise ValueError(
                "config must be exactly ResearchEvidenceSourceDiversityGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_aggregate_source_count",
            "min_watch_aggregate_source_count",
            "min_pass_independent_source_class_count",
            "min_watch_independent_source_class_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_source_concentration_ratio",
            "max_watch_stale_source_concentration_ratio",
            "min_pass_contradiction_coverage_ratio",
            "min_watch_contradiction_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_aggregate_source_count > self.min_pass_aggregate_source_count:
            raise ValueError("watch aggregate threshold cannot exceed pass threshold")
        if (
            self.min_watch_independent_source_class_count
            > self.min_pass_independent_source_class_count
        ):
            raise ValueError("watch independent threshold cannot exceed pass threshold")
        if (
            self.max_pass_stale_source_concentration_ratio
            > self.max_watch_stale_source_concentration_ratio
        ):
            raise ValueError("pass stale threshold cannot exceed watch threshold")
        if (
            self.min_watch_contradiction_coverage_ratio
            > self.min_pass_contradiction_coverage_ratio
        ):
            raise ValueError("watch contradiction threshold cannot exceed pass threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEvidenceSourceDiversityGateInput:
    aggregate_source_count: Decimal
    independent_source_class_count: Decimal
    stale_source_count: Decimal
    contradiction_count: Decimal
    covered_contradiction_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceSourceDiversityGateInput:
            raise TypeError(
                "ResearchEvidenceSourceDiversityGateInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceSourceDiversityGateInput:
            raise ValueError(
                "inputs must be exactly ResearchEvidenceSourceDiversityGateInput",
            )
        for field_name in (
            "aggregate_source_count",
            "independent_source_class_count",
            "stale_source_count",
            "contradiction_count",
            "covered_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.contradiction_count == _ZERO:
            object.__setattr__(self, "covered_contradiction_count", _ZERO)
        if self.independent_source_class_count > self.aggregate_source_count:
            raise ValueError(
                "independent_source_class_count cannot exceed aggregate_source_count",
            )
        if self.stale_source_count > self.aggregate_source_count:
            raise ValueError("stale_source_count cannot exceed aggregate_source_count")
        if self.covered_contradiction_count > self.contradiction_count:
            raise ValueError(
                "covered_contradiction_count cannot exceed contradiction_count",
            )
        _require_hard_flags("inputs", self)
        _reject_unsafe_public_payload("inputs", self)


@dataclass(frozen=True)
class ResearchEvidenceSourceDiversityGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    aggregate_source_count: Decimal
    independent_source_class_count: Decimal
    stale_source_count: Decimal
    stale_source_concentration_ratio: Decimal
    contradiction_count: Decimal
    covered_contradiction_count: Decimal
    contradiction_coverage_ratio: Decimal
    check_count: Decimal
    passed_check_count: Decimal
    watch_check_count: Decimal
    blocked_check_count: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceSourceDiversityGateReport:
            raise TypeError(
                "ResearchEvidenceSourceDiversityGateReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceSourceDiversityGateReport:
            raise ValueError(
                "report must be exactly ResearchEvidenceSourceDiversityGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "aggregate_source_count",
            "independent_source_class_count",
            "stale_source_count",
            "contradiction_count",
            "covered_contradiction_count",
            "check_count",
            "passed_check_count",
            "watch_check_count",
            "blocked_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_concentration_ratio",
            "contradiction_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
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
        _reject_unsafe_public_payload(
            "ResearchEvidenceSourceDiversityGateReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_evidence_source_diversity_gate_report(
    inputs: ResearchEvidenceSourceDiversityGateInput,
    *,
    generated_at: datetime,
    config: ResearchEvidenceSourceDiversityGateConfig | None = None,
) -> ResearchEvidenceSourceDiversityGateReport:
    """Build a deterministic paper-only source diversity sufficiency report."""

    if type(inputs) is not ResearchEvidenceSourceDiversityGateInput:
        raise ValueError("inputs must be a ResearchEvidenceSourceDiversityGateInput")
    if config is None:
        config = ResearchEvidenceSourceDiversityGateConfig()
    if type(config) is not ResearchEvidenceSourceDiversityGateConfig:
        raise ValueError("config must be a ResearchEvidenceSourceDiversityGateConfig")
    generated_at = _as_utc("generated_at", generated_at)
    stale_source_concentration_ratio = _ratio(
        inputs.stale_source_count,
        inputs.aggregate_source_count,
        zero_denominator_value=_ZERO,
    )
    contradiction_coverage_ratio = _ratio(
        inputs.covered_contradiction_count,
        inputs.contradiction_count,
        zero_denominator_value=_ONE,
    )
    statuses = (
        _aggregate_independence_status(inputs, config),
        _maximum_status(
            stale_source_concentration_ratio,
            pass_threshold=config.max_pass_stale_source_concentration_ratio,
            watch_threshold=config.max_watch_stale_source_concentration_ratio,
        ),
        _minimum_status(
            contradiction_coverage_ratio,
            pass_threshold=config.min_pass_contradiction_coverage_ratio,
            watch_threshold=config.min_watch_contradiction_coverage_ratio,
        ),
    )
    reason_codes = _normalize_reason_codes(
        (
            f"independent_source_classes_{statuses[0]}",
            f"stale_source_concentration_{statuses[1]}",
            f"contradiction_coverage_{statuses[2]}",
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": _overall_status(statuses),
        "aggregate_source_count": inputs.aggregate_source_count,
        "independent_source_class_count": inputs.independent_source_class_count,
        "stale_source_count": inputs.stale_source_count,
        "stale_source_concentration_ratio": stale_source_concentration_ratio,
        "contradiction_count": inputs.contradiction_count,
        "covered_contradiction_count": inputs.covered_contradiction_count,
        "contradiction_coverage_ratio": contradiction_coverage_ratio,
        "check_count": _CHECK_COUNT,
        "passed_check_count": _status_count(statuses, "pass"),
        "watch_check_count": _status_count(statuses, "watch"),
        "blocked_check_count": _status_count(statuses, "block"),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEvidenceSourceDiversityGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _aggregate_independence_status(
    inputs: ResearchEvidenceSourceDiversityGateInput,
    config: ResearchEvidenceSourceDiversityGateConfig,
) -> str:
    aggregate_status = _minimum_status(
        inputs.aggregate_source_count,
        pass_threshold=config.min_pass_aggregate_source_count,
        watch_threshold=config.min_watch_aggregate_source_count,
    )
    class_status = _minimum_status(
        inputs.independent_source_class_count,
        pass_threshold=config.min_pass_independent_source_class_count,
        watch_threshold=config.min_watch_independent_source_class_count,
    )
    return _overall_status((aggregate_status, class_status))


def _minimum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return "pass"
    if value >= watch_threshold:
        return "watch"
    return "block"


def _maximum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "pass"
    if value <= watch_threshold:
        return "watch"
    return "block"


def _overall_status(statuses: Sequence[str]) -> str:
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_count(statuses: Sequence[str], target: str) -> Decimal:
    return _decimal_count(sum(1 for status in statuses if status == target))


def _validate_report_consistency(
    report: ResearchEvidenceSourceDiversityGateReport,
) -> None:
    if report.independent_source_class_count > report.aggregate_source_count:
        raise ValueError(
            "independent_source_class_count cannot exceed aggregate_source_count",
        )
    if report.stale_source_count > report.aggregate_source_count:
        raise ValueError("stale_source_count cannot exceed aggregate_source_count")
    if report.covered_contradiction_count > report.contradiction_count:
        raise ValueError(
            "covered_contradiction_count cannot exceed contradiction_count",
        )
    if report.stale_source_concentration_ratio != _ratio(
        report.stale_source_count,
        report.aggregate_source_count,
        zero_denominator_value=_ZERO,
    ):
        raise ValueError("stale_source_concentration_ratio must tie to source counts")
    if report.contradiction_coverage_ratio != _ratio(
        report.covered_contradiction_count,
        report.contradiction_count,
        zero_denominator_value=_ONE,
    ):
        raise ValueError("contradiction_coverage_ratio must tie to contradiction counts")
    if (
        report.passed_check_count
        + report.watch_check_count
        + report.blocked_check_count
        != report.check_count
    ):
        raise ValueError("check counts must sum to check_count")
    if report.check_count != _CHECK_COUNT:
        raise ValueError("check_count must equal the three source diversity checks")
    reason_statuses = tuple(reason_code.rsplit("_", 1)[1] for reason_code in report.reason_codes)
    if report.passed_check_count != _status_count(reason_statuses, "pass"):
        raise ValueError("passed_check_count must match reason_codes")
    if report.watch_check_count != _status_count(reason_statuses, "watch"):
        raise ValueError("watch_check_count must match reason_codes")
    if report.blocked_check_count != _status_count(reason_statuses, "block"):
        raise ValueError("blocked_check_count must match reason_codes")
    if report.gate_status == "pass" and (
        report.watch_check_count != _ZERO or report.blocked_check_count != _ZERO
    ):
        raise ValueError("pass status requires every check to pass")
    if report.gate_status == "watch" and (
        report.watch_check_count == _ZERO or report.blocked_check_count != _ZERO
    ):
        raise ValueError("watch status requires watch checks and no block checks")
    if report.gate_status == "block" and report.blocked_check_count == _ZERO:
        raise ValueError("block status requires at least one blocked check")


def _ratio(
    numerator: Decimal,
    denominator: Decimal,
    *,
    zero_denominator_value: Decimal,
) -> Decimal:
    if denominator == _ZERO:
        return zero_denominator_value
    return _require_ratio_decimal("ratio", numerator / denominator)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label}.{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label}.{field_name} must be true")


def _require_gate_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


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


def _require_whole_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


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


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchEvidenceSourceDiversityGateReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                f"{current_path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose arbitrary mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    _reject_unsafe_public_string(path, key)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


__all__ = (
    "DEFAULT_RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_CONFIG_VERSION",
    "RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_STATUSES",
    "ResearchEvidenceSourceDiversityGateConfig",
    "ResearchEvidenceSourceDiversityGateInput",
    "ResearchEvidenceSourceDiversityGateReport",
    "build_research_evidence_source_diversity_gate_report",
)
