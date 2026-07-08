"""Pure report-only scraping quality gate for candidate research retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping


DEFAULT_RESEARCH_SOURCE_SCRAPING_QUALITY_GATE_CONFIG_VERSION = (
    "research-source-scraping-quality-gate-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_GATE_NEXT_STEPS = {
    "pass": "continue_candidate_research_scraping_review",
    "watch": "review_candidate_research_scraping_quality",
    "block": "block_candidate_research_scraping_until_remediated",
}
_GATE_STATUSES = frozenset(_GATE_NEXT_STEPS)
_REASON_CODE_SEQUENCE = (
    "scraping_quality_gate_pass",
    "empty_candidate_research_snapshot",
    "coverage_below_block_threshold",
    "freshness_below_block_threshold",
    "parse_confidence_below_block_threshold",
    "retry_pressure_above_block_threshold",
    "evidence_completeness_below_block_threshold",
    "coverage_below_pass_threshold",
    "freshness_below_pass_threshold",
    "parse_confidence_below_pass_threshold",
    "retry_pressure_above_pass_threshold",
    "evidence_completeness_below_pass_threshold",
)
_BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in _REASON_CODE_SEQUENCE
    if reason_code.endswith("_block_threshold")
)
_PASS_REASON_CODE = "scraping_quality_gate_pass"
_EMPTY_REASON_CODE = "empty_candidate_research_snapshot"
_UNSAFE_PUBLIC_TERMS = (
    "raw_url",
    "source_text",
    "market_id",
    "question",
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
class ResearchSourceScrapingQualityGateConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_SCRAPING_QUALITY_GATE_CONFIG_VERSION
    min_coverage_pass_ratio: Decimal = Decimal("0.900000")
    min_coverage_block_ratio: Decimal = Decimal("0.500000")
    min_freshness_pass_ratio: Decimal = Decimal("0.800000")
    min_freshness_block_ratio: Decimal = Decimal("0.200000")
    min_parse_confidence_pass_ratio: Decimal = Decimal("0.800000")
    min_parse_confidence_block_ratio: Decimal = Decimal("0.600000")
    max_retry_pressure_pass_ratio: Decimal = Decimal("0.100000")
    max_retry_pressure_block_ratio: Decimal = Decimal("0.500000")
    min_evidence_completeness_pass_ratio: Decimal = Decimal("0.800000")
    min_evidence_completeness_block_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceScrapingQualityGateConfig may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingQualityGateConfig:
            raise ValueError(
                "config must be a ResearchSourceScrapingQualityGateConfig",
            )
        _require_safe_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_coverage_pass_ratio",
            "min_coverage_block_ratio",
            "min_freshness_pass_ratio",
            "min_freshness_block_ratio",
            "min_parse_confidence_pass_ratio",
            "min_parse_confidence_block_ratio",
            "max_retry_pressure_pass_ratio",
            "max_retry_pressure_block_ratio",
            "min_evidence_completeness_pass_ratio",
            "min_evidence_completeness_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_coverage_block_ratio > self.min_coverage_pass_ratio:
            raise ValueError("coverage block threshold must not exceed pass threshold")
        if self.min_freshness_block_ratio > self.min_freshness_pass_ratio:
            raise ValueError("freshness block threshold must not exceed pass threshold")
        if self.min_parse_confidence_block_ratio > self.min_parse_confidence_pass_ratio:
            raise ValueError(
                "parse confidence block threshold must not exceed pass threshold",
            )
        if (
            self.min_evidence_completeness_block_ratio
            > self.min_evidence_completeness_pass_ratio
        ):
            raise ValueError(
                "evidence completeness block threshold must not exceed pass threshold",
            )
        if self.max_retry_pressure_pass_ratio > self.max_retry_pressure_block_ratio:
            raise ValueError(
                "retry pressure pass threshold must not exceed block threshold",
            )
        _require_hard_flags("ResearchSourceScrapingQualityGateConfig", self)


@dataclass(frozen=True)
class ResearchSourceScrapingQualityGateSnapshot:
    candidate_count: Decimal
    covered_candidate_count: Decimal
    fresh_candidate_count: Decimal
    parsed_candidate_count: Decimal
    parse_confidence_sum: Decimal
    retrieval_attempt_count: Decimal
    retrieval_retry_count: Decimal
    evidence_complete_candidate_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceScrapingQualityGateSnapshot may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingQualityGateSnapshot:
            raise ValueError(
                "snapshot must be a ResearchSourceScrapingQualityGateSnapshot",
            )
        for field_name in (
            "candidate_count",
            "covered_candidate_count",
            "fresh_candidate_count",
            "parsed_candidate_count",
            "retrieval_attempt_count",
            "retrieval_retry_count",
            "evidence_complete_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parse_confidence_sum",
            _require_nonnegative_decimal(
                "parse_confidence_sum",
                self.parse_confidence_sum,
            ),
        )
        _require_hard_flags("ResearchSourceScrapingQualityGateSnapshot", self)
        _validate_snapshot_consistency(self)


@dataclass(frozen=True)
class ResearchSourceScrapingQualityGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    gate_next_step: str
    candidate_count: Decimal
    covered_candidate_count: Decimal
    fresh_candidate_count: Decimal
    parsed_candidate_count: Decimal
    parse_confidence_sum: Decimal
    retrieval_attempt_count: Decimal
    retrieval_retry_count: Decimal
    evidence_complete_candidate_count: Decimal
    coverage_ratio: Decimal | None
    freshness_ratio: Decimal | None
    parse_confidence_ratio: Decimal | None
    retry_pressure_ratio: Decimal | None
    evidence_completeness_ratio: Decimal | None
    min_coverage_pass_ratio: Decimal
    min_coverage_block_ratio: Decimal
    min_freshness_pass_ratio: Decimal
    min_freshness_block_ratio: Decimal
    min_parse_confidence_pass_ratio: Decimal
    min_parse_confidence_block_ratio: Decimal
    max_retry_pressure_pass_ratio: Decimal
    max_retry_pressure_block_ratio: Decimal
    min_evidence_completeness_pass_ratio: Decimal
    min_evidence_completeness_block_ratio: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceScrapingQualityGateReport may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingQualityGateReport:
            raise ValueError("report must be a ResearchSourceScrapingQualityGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_canonical_string("config_version", self.config_version)
        _require_gate_status("gate_status", self.gate_status)
        _require_safe_canonical_string("gate_next_step", self.gate_next_step)
        for field_name in (
            "candidate_count",
            "covered_candidate_count",
            "fresh_candidate_count",
            "parsed_candidate_count",
            "retrieval_attempt_count",
            "retrieval_retry_count",
            "evidence_complete_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parse_confidence_sum",
            _require_nonnegative_decimal(
                "parse_confidence_sum",
                self.parse_confidence_sum,
            ),
        )
        for field_name in (
            "coverage_ratio",
            "freshness_ratio",
            "parse_confidence_ratio",
            "retry_pressure_ratio",
            "evidence_completeness_ratio",
        ):
            _require_optional_ratio_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "min_coverage_pass_ratio",
            "min_coverage_block_ratio",
            "min_freshness_pass_ratio",
            "min_freshness_block_ratio",
            "min_parse_confidence_pass_ratio",
            "min_parse_confidence_block_ratio",
            "max_retry_pressure_pass_ratio",
            "max_retry_pressure_block_ratio",
            "min_evidence_completeness_pass_ratio",
            "min_evidence_completeness_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("ResearchSourceScrapingQualityGateReport", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSourceScrapingQualityGateReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_scraping_quality_gate_report(
    snapshot: ResearchSourceScrapingQualityGateSnapshot,
    *,
    config: ResearchSourceScrapingQualityGateConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingQualityGateReport:
    if type(snapshot) is not ResearchSourceScrapingQualityGateSnapshot:
        raise ValueError("snapshot must be a ResearchSourceScrapingQualityGateSnapshot")
    if type(config) is not ResearchSourceScrapingQualityGateConfig:
        raise ValueError("config must be a ResearchSourceScrapingQualityGateConfig")
    _require_hard_flags("ResearchSourceScrapingQualityGateSnapshot", snapshot)
    _require_hard_flags("ResearchSourceScrapingQualityGateConfig", config)

    generated_at = _as_utc("generated_at", generated_at)
    coverage_ratio = _optional_ratio(
        snapshot.covered_candidate_count,
        snapshot.candidate_count,
    )
    freshness_ratio = _optional_ratio(
        snapshot.fresh_candidate_count,
        snapshot.candidate_count,
    )
    parse_confidence_ratio = _parse_confidence_ratio(snapshot)
    retry_pressure_ratio = _optional_ratio(
        snapshot.retrieval_retry_count,
        snapshot.retrieval_attempt_count,
    )
    evidence_completeness_ratio = _optional_ratio(
        snapshot.evidence_complete_candidate_count,
        snapshot.candidate_count,
    )
    reason_codes = _report_reason_codes(
        snapshot=snapshot,
        config=config,
        coverage_ratio=coverage_ratio,
        freshness_ratio=freshness_ratio,
        parse_confidence_ratio=parse_confidence_ratio,
        retry_pressure_ratio=retry_pressure_ratio,
        evidence_completeness_ratio=evidence_completeness_ratio,
    )
    gate_status = _gate_status(reason_codes)

    return ResearchSourceScrapingQualityGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        gate_status=gate_status,
        gate_next_step=_GATE_NEXT_STEPS[gate_status],
        candidate_count=snapshot.candidate_count,
        covered_candidate_count=snapshot.covered_candidate_count,
        fresh_candidate_count=snapshot.fresh_candidate_count,
        parsed_candidate_count=snapshot.parsed_candidate_count,
        parse_confidence_sum=snapshot.parse_confidence_sum,
        retrieval_attempt_count=snapshot.retrieval_attempt_count,
        retrieval_retry_count=snapshot.retrieval_retry_count,
        evidence_complete_candidate_count=snapshot.evidence_complete_candidate_count,
        coverage_ratio=coverage_ratio,
        freshness_ratio=freshness_ratio,
        parse_confidence_ratio=parse_confidence_ratio,
        retry_pressure_ratio=retry_pressure_ratio,
        evidence_completeness_ratio=evidence_completeness_ratio,
        min_coverage_pass_ratio=config.min_coverage_pass_ratio,
        min_coverage_block_ratio=config.min_coverage_block_ratio,
        min_freshness_pass_ratio=config.min_freshness_pass_ratio,
        min_freshness_block_ratio=config.min_freshness_block_ratio,
        min_parse_confidence_pass_ratio=config.min_parse_confidence_pass_ratio,
        min_parse_confidence_block_ratio=config.min_parse_confidence_block_ratio,
        max_retry_pressure_pass_ratio=config.max_retry_pressure_pass_ratio,
        max_retry_pressure_block_ratio=config.max_retry_pressure_block_ratio,
        min_evidence_completeness_pass_ratio=(
            config.min_evidence_completeness_pass_ratio
        ),
        min_evidence_completeness_block_ratio=(
            config.min_evidence_completeness_block_ratio
        ),
        reason_codes=reason_codes,
    )


def _report_reason_codes(
    *,
    snapshot: ResearchSourceScrapingQualityGateSnapshot,
    config: ResearchSourceScrapingQualityGateConfig,
    coverage_ratio: Decimal | None,
    freshness_ratio: Decimal | None,
    parse_confidence_ratio: Decimal | None,
    retry_pressure_ratio: Decimal | None,
    evidence_completeness_ratio: Decimal | None,
) -> tuple[str, ...]:
    if snapshot.candidate_count == _ZERO:
        return (_EMPTY_REASON_CODE,)

    block_reason_codes: list[str] = []
    if _below(coverage_ratio, config.min_coverage_block_ratio):
        block_reason_codes.append("coverage_below_block_threshold")
    if _below(freshness_ratio, config.min_freshness_block_ratio):
        block_reason_codes.append("freshness_below_block_threshold")
    if _below(parse_confidence_ratio, config.min_parse_confidence_block_ratio):
        block_reason_codes.append("parse_confidence_below_block_threshold")
    if _above(retry_pressure_ratio, config.max_retry_pressure_block_ratio):
        block_reason_codes.append("retry_pressure_above_block_threshold")
    if _below(
        evidence_completeness_ratio,
        config.min_evidence_completeness_block_ratio,
    ):
        block_reason_codes.append("evidence_completeness_below_block_threshold")
    if block_reason_codes:
        return _normalize_reason_codes(tuple(block_reason_codes))

    watch_reason_codes: list[str] = []
    if _below(coverage_ratio, config.min_coverage_pass_ratio):
        watch_reason_codes.append("coverage_below_pass_threshold")
    if _below(freshness_ratio, config.min_freshness_pass_ratio):
        watch_reason_codes.append("freshness_below_pass_threshold")
    if _below(parse_confidence_ratio, config.min_parse_confidence_pass_ratio):
        watch_reason_codes.append("parse_confidence_below_pass_threshold")
    if _above(retry_pressure_ratio, config.max_retry_pressure_pass_ratio):
        watch_reason_codes.append("retry_pressure_above_pass_threshold")
    if _below(
        evidence_completeness_ratio,
        config.min_evidence_completeness_pass_ratio,
    ):
        watch_reason_codes.append("evidence_completeness_below_pass_threshold")
    return _normalize_reason_codes(tuple(watch_reason_codes) or (_PASS_REASON_CODE,))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (_PASS_REASON_CODE,):
        return "pass"
    if reason_codes == (_EMPTY_REASON_CODE,) or any(
        reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes
    ):
        return "block"
    return "watch"


def _parse_confidence_ratio(
    snapshot: ResearchSourceScrapingQualityGateSnapshot,
) -> Decimal | None:
    if snapshot.candidate_count == _ZERO:
        return None
    if snapshot.parsed_candidate_count == _ZERO:
        return _ZERO
    return _optional_ratio(snapshot.parse_confidence_sum, snapshot.parsed_candidate_count)


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == _ZERO:
        return None
    return _quantize(numerator / denominator)


def _below(value: Decimal | None, threshold: Decimal) -> bool:
    return value is None or value < threshold


def _above(value: Decimal | None, threshold: Decimal) -> bool:
    return value is None or value > threshold


def _validate_snapshot_consistency(
    snapshot: ResearchSourceScrapingQualityGateSnapshot,
) -> None:
    for field_name in (
        "covered_candidate_count",
        "fresh_candidate_count",
        "parsed_candidate_count",
        "evidence_complete_candidate_count",
    ):
        if getattr(snapshot, field_name) > snapshot.candidate_count:
            raise ValueError(f"{field_name} must not exceed candidate_count")
    if snapshot.parse_confidence_sum > snapshot.parsed_candidate_count:
        raise ValueError("parse_confidence_sum must not exceed parsed_candidate_count")
    if snapshot.retrieval_retry_count > snapshot.retrieval_attempt_count:
        raise ValueError("retrieval_retry_count must not exceed retrieval_attempt_count")


def _validate_report_consistency(
    report: ResearchSourceScrapingQualityGateReport,
) -> None:
    if report.gate_next_step != _GATE_NEXT_STEPS[report.gate_status]:
        raise ValueError("gate_next_step must match gate_status")
    _validate_snapshot_consistency(
        ResearchSourceScrapingQualityGateSnapshot(
            candidate_count=report.candidate_count,
            covered_candidate_count=report.covered_candidate_count,
            fresh_candidate_count=report.fresh_candidate_count,
            parsed_candidate_count=report.parsed_candidate_count,
            parse_confidence_sum=report.parse_confidence_sum,
            retrieval_attempt_count=report.retrieval_attempt_count,
            retrieval_retry_count=report.retrieval_retry_count,
            evidence_complete_candidate_count=report.evidence_complete_candidate_count,
        ),
    )
    if report.coverage_ratio != _optional_ratio(
        report.covered_candidate_count,
        report.candidate_count,
    ):
        raise ValueError("coverage_ratio must match aggregate counts")
    if report.freshness_ratio != _optional_ratio(
        report.fresh_candidate_count,
        report.candidate_count,
    ):
        raise ValueError("freshness_ratio must match aggregate counts")
    expected_parse_confidence_ratio = _parse_confidence_ratio(
        ResearchSourceScrapingQualityGateSnapshot(
            candidate_count=report.candidate_count,
            covered_candidate_count=report.covered_candidate_count,
            fresh_candidate_count=report.fresh_candidate_count,
            parsed_candidate_count=report.parsed_candidate_count,
            parse_confidence_sum=report.parse_confidence_sum,
            retrieval_attempt_count=report.retrieval_attempt_count,
            retrieval_retry_count=report.retrieval_retry_count,
            evidence_complete_candidate_count=report.evidence_complete_candidate_count,
        ),
    )
    if report.parse_confidence_ratio != expected_parse_confidence_ratio:
        raise ValueError("parse_confidence_ratio must match aggregate counts")
    if report.retry_pressure_ratio != _optional_ratio(
        report.retrieval_retry_count,
        report.retrieval_attempt_count,
    ):
        raise ValueError("retry_pressure_ratio must match aggregate counts")
    if report.evidence_completeness_ratio != _optional_ratio(
        report.evidence_complete_candidate_count,
        report.candidate_count,
    ):
        raise ValueError("evidence_completeness_ratio must match aggregate counts")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in normalized:
        _require_safe_canonical_string("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
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


def _require_safe_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_string(field_name, value)


def _require_gate_status(field_name: str, value: object) -> None:
    _require_safe_canonical_string(field_name, value)
    if value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_ratio_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: ResearchSourceScrapingQualityGateReport,
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "http://" in lowered or "https://" in lowered or "www." in lowered:
        raise ValueError(f"{field_name} contains unsafe public location")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPING_QUALITY_GATE_CONFIG_VERSION",
    "ResearchSourceScrapingQualityGateConfig",
    "ResearchSourceScrapingQualityGateReport",
    "ResearchSourceScrapingQualityGateSnapshot",
    "build_research_source_scraping_quality_gate_report",
)
