"""Pure report-only research packet completeness gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_CONFIG_VERSION = (
    "research-research-packet-completeness-gate-report"
)
RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_CHECK_COUNT = Decimal("6.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate_slug",
    "market_id",
    "market_slug",
    "source_id",
    "source_url",
    "source_reference",
    "recommendation",
    "sizing",
    "order",
    "wallet",
    "auth",
)
_REASON_CODE_SEQUENCE = (
    "evidence_count_pass",
    "evidence_count_watch",
    "evidence_count_block",
    "source_diversity_pass",
    "source_diversity_watch",
    "source_diversity_block",
    "freshness_pass",
    "freshness_watch",
    "freshness_block",
    "rule_clarity_pass",
    "rule_clarity_watch",
    "rule_clarity_block",
    "team_signoff_pass",
    "team_signoff_watch",
    "team_signoff_block",
    "review_cost_pass",
    "review_cost_watch",
    "review_cost_block",
)


@dataclass(frozen=True)
class ResearchResearchPacketCompletenessGateConfig:
    config_version: str = DEFAULT_RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_CONFIG_VERSION
    min_pass_aggregate_evidence_count: Decimal = Decimal("6.000000")
    min_watch_aggregate_evidence_count: Decimal = Decimal("1.000000")
    min_pass_source_diversity_count: Decimal = Decimal("3.000000")
    min_watch_source_diversity_count: Decimal = Decimal("1.000000")
    min_pass_fresh_evidence_ratio: Decimal = Decimal("0.800000")
    min_watch_fresh_evidence_ratio: Decimal = Decimal("0.500000")
    min_pass_rule_clarity_score: Decimal = Decimal("0.800000")
    min_watch_rule_clarity_score: Decimal = Decimal("0.600000")
    min_pass_team_signoff_count: Decimal = Decimal("2.000000")
    min_watch_team_signoff_count: Decimal = Decimal("1.000000")
    max_pass_review_cost: Decimal = Decimal("750.000000")
    max_watch_review_cost: Decimal = Decimal("1200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResearchPacketCompletenessGateConfig:
            raise TypeError(
                "ResearchResearchPacketCompletenessGateConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResearchPacketCompletenessGateConfig:
            raise ValueError(
                "config must be exactly ResearchResearchPacketCompletenessGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_aggregate_evidence_count",
            "min_watch_aggregate_evidence_count",
            "min_pass_source_diversity_count",
            "min_watch_source_diversity_count",
            "min_pass_team_signoff_count",
            "min_watch_team_signoff_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_fresh_evidence_ratio",
            "min_watch_fresh_evidence_ratio",
            "min_pass_rule_clarity_score",
            "min_watch_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_pass_review_cost", "max_watch_review_cost"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_aggregate_evidence_count > self.min_pass_aggregate_evidence_count:
            raise ValueError("watch evidence threshold cannot exceed pass threshold")
        if self.min_watch_source_diversity_count > self.min_pass_source_diversity_count:
            raise ValueError("watch diversity threshold cannot exceed pass threshold")
        if self.min_watch_fresh_evidence_ratio > self.min_pass_fresh_evidence_ratio:
            raise ValueError("watch freshness threshold cannot exceed pass threshold")
        if self.min_watch_rule_clarity_score > self.min_pass_rule_clarity_score:
            raise ValueError("watch rule clarity threshold cannot exceed pass threshold")
        if self.min_watch_team_signoff_count > self.min_pass_team_signoff_count:
            raise ValueError("watch team signoff threshold cannot exceed pass threshold")
        if self.max_pass_review_cost > self.max_watch_review_cost:
            raise ValueError("pass cost threshold cannot exceed watch threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchResearchPacketCompletenessGateInput:
    aggregate_evidence_count: Decimal
    source_diversity_count: Decimal
    fresh_evidence_count: Decimal
    rule_clarity_score: Decimal
    team_signoff_count: Decimal
    estimated_review_cost: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResearchPacketCompletenessGateInput:
            raise TypeError(
                "ResearchResearchPacketCompletenessGateInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResearchPacketCompletenessGateInput:
            raise ValueError(
                "inputs must be exactly ResearchResearchPacketCompletenessGateInput",
            )
        for field_name in (
            "aggregate_evidence_count",
            "source_diversity_count",
            "fresh_evidence_count",
            "team_signoff_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rule_clarity_score",
            _require_ratio_decimal("rule_clarity_score", self.rule_clarity_score),
        )
        object.__setattr__(
            self,
            "estimated_review_cost",
            _require_nonnegative_decimal(
                "estimated_review_cost",
                self.estimated_review_cost,
            ),
        )
        if self.fresh_evidence_count > self.aggregate_evidence_count:
            raise ValueError("fresh_evidence_count cannot exceed aggregate_evidence_count")
        if self.source_diversity_count > self.aggregate_evidence_count:
            raise ValueError(
                "source_diversity_count cannot exceed aggregate_evidence_count",
            )
        _require_hard_flags("inputs", self)
        _reject_unsafe_public_payload("inputs", self)


@dataclass(frozen=True)
class ResearchResearchPacketCompletenessGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    aggregate_evidence_count: Decimal
    source_diversity_count: Decimal
    fresh_evidence_count: Decimal
    stale_evidence_count: Decimal
    fresh_evidence_ratio: Decimal
    rule_clarity_score: Decimal
    team_signoff_count: Decimal
    estimated_review_cost: Decimal
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
        if cls is not ResearchResearchPacketCompletenessGateReport:
            raise TypeError(
                "ResearchResearchPacketCompletenessGateReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchResearchPacketCompletenessGateReport:
            raise ValueError(
                "report must be exactly ResearchResearchPacketCompletenessGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "aggregate_evidence_count",
            "source_diversity_count",
            "fresh_evidence_count",
            "stale_evidence_count",
            "team_signoff_count",
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
        for field_name in ("fresh_evidence_ratio", "rule_clarity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_review_cost",
            _require_nonnegative_decimal(
                "estimated_review_cost",
                self.estimated_review_cost,
            ),
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
            "ResearchResearchPacketCompletenessGateReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_research_packet_completeness_gate_report(
    inputs: ResearchResearchPacketCompletenessGateInput,
    *,
    generated_at: datetime,
    config: ResearchResearchPacketCompletenessGateConfig | None = None,
) -> ResearchResearchPacketCompletenessGateReport:
    """Build a deterministic paper-only completeness gate report."""

    if type(inputs) is not ResearchResearchPacketCompletenessGateInput:
        raise ValueError(
            "inputs must be a ResearchResearchPacketCompletenessGateInput",
        )
    if config is None:
        config = ResearchResearchPacketCompletenessGateConfig()
    if type(config) is not ResearchResearchPacketCompletenessGateConfig:
        raise ValueError(
            "config must be a ResearchResearchPacketCompletenessGateConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    statuses = (
        _minimum_status(
            inputs.aggregate_evidence_count,
            pass_threshold=config.min_pass_aggregate_evidence_count,
            watch_threshold=config.min_watch_aggregate_evidence_count,
        ),
        _minimum_status(
            inputs.source_diversity_count,
            pass_threshold=config.min_pass_source_diversity_count,
            watch_threshold=config.min_watch_source_diversity_count,
        ),
        _minimum_status(
            _fresh_evidence_ratio(inputs),
            pass_threshold=config.min_pass_fresh_evidence_ratio,
            watch_threshold=config.min_watch_fresh_evidence_ratio,
        ),
        _minimum_status(
            inputs.rule_clarity_score,
            pass_threshold=config.min_pass_rule_clarity_score,
            watch_threshold=config.min_watch_rule_clarity_score,
        ),
        _minimum_status(
            inputs.team_signoff_count,
            pass_threshold=config.min_pass_team_signoff_count,
            watch_threshold=config.min_watch_team_signoff_count,
        ),
        _maximum_status(
            inputs.estimated_review_cost,
            pass_threshold=config.max_pass_review_cost,
            watch_threshold=config.max_watch_review_cost,
        ),
    )
    reason_codes = _normalize_reason_codes(
        (
            f"evidence_count_{statuses[0]}",
            f"source_diversity_{statuses[1]}",
            f"freshness_{statuses[2]}",
            f"rule_clarity_{statuses[3]}",
            f"team_signoff_{statuses[4]}",
            f"review_cost_{statuses[5]}",
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": _overall_status(statuses),
        "aggregate_evidence_count": inputs.aggregate_evidence_count,
        "source_diversity_count": inputs.source_diversity_count,
        "fresh_evidence_count": inputs.fresh_evidence_count,
        "stale_evidence_count": _quantize(
            inputs.aggregate_evidence_count - inputs.fresh_evidence_count,
        ),
        "fresh_evidence_ratio": _fresh_evidence_ratio(inputs),
        "rule_clarity_score": inputs.rule_clarity_score,
        "team_signoff_count": inputs.team_signoff_count,
        "estimated_review_cost": inputs.estimated_review_cost,
        "check_count": _CHECK_COUNT,
        "passed_check_count": _status_count(statuses, "pass"),
        "watch_check_count": _status_count(statuses, "watch"),
        "blocked_check_count": _status_count(statuses, "block"),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchResearchPacketCompletenessGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


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


def _fresh_evidence_ratio(
    inputs: ResearchResearchPacketCompletenessGateInput,
) -> Decimal:
    if inputs.aggregate_evidence_count == _ZERO:
        return _ZERO
    return _require_ratio_decimal(
        "fresh_evidence_ratio",
        inputs.fresh_evidence_count / inputs.aggregate_evidence_count,
    )


def _validate_report_consistency(
    report: ResearchResearchPacketCompletenessGateReport,
) -> None:
    if report.source_diversity_count > report.aggregate_evidence_count:
        raise ValueError("source_diversity_count cannot exceed aggregate_evidence_count")
    if report.fresh_evidence_count > report.aggregate_evidence_count:
        raise ValueError("fresh_evidence_count cannot exceed aggregate_evidence_count")
    if (
        report.stale_evidence_count
        != report.aggregate_evidence_count - report.fresh_evidence_count
    ):
        raise ValueError("stale_evidence_count must tie to evidence counts")
    if (
        report.passed_check_count
        + report.watch_check_count
        + report.blocked_check_count
        != report.check_count
    ):
        raise ValueError("check counts must sum to check_count")
    if report.check_count != _CHECK_COUNT:
        raise ValueError("check_count must equal the six completeness checks")
    if report.gate_status == "pass" and (
        report.watch_check_count != _ZERO or report.blocked_check_count != _ZERO
    ):
        raise ValueError("pass status requires every check to pass")
    if report.gate_status == "watch" and report.blocked_check_count != _ZERO:
        raise ValueError("watch status cannot include block checks")
    if report.gate_status == "block" and report.blocked_check_count == _ZERO:
        raise ValueError("block status requires at least one blocked check")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label}.{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label}.{field_name} must be true")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_STATUSES:
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
    report: ResearchResearchPacketCompletenessGateReport,
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
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
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
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_CONFIG_VERSION",
    "RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_STATUSES",
    "ResearchResearchPacketCompletenessGateConfig",
    "ResearchResearchPacketCompletenessGateInput",
    "ResearchResearchPacketCompletenessGateReport",
    "build_research_research_packet_completeness_gate_report",
)
