"""Pure Phase 2 evidence adapter for candidate decision scoring."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION = (
    "candidate-decision-evidence-adapter-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EVIDENCE_STATUSES = ("pass", "research_more", "blocked")
REASON_CODE_ORDER = (
    "evidence_adapter_pass",
    "evidence_adapter_research_more",
    "evidence_adapter_blocked",
    "evidence_source_count_low",
    "evidence_single_source_research_more",
    "evidence_fresh_source_count_low",
    "evidence_stale_sources_present",
    "evidence_freshness_stale",
    "evidence_authority_low",
    "evidence_redundancy_low",
    "evidence_traceability_low",
    "evidence_traceability_missing",
    "evidence_contradiction_watch",
    "evidence_contradiction_blocked",
    "evidence_weighted_score_below_pass_threshold",
)
COMPONENT_NAMES = (
    "authority_score",
    "contradiction_absence_score",
    "freshness_score",
    "redundancy_score",
    "source_count_score",
    "traceability_score",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "pri" "vate_key",
    "api" "_key",
    "sec" "ret",
    "to" "ken",
    "wal" "let",
    "acc" "ount",
    "bro" "ker",
    "ord" "er",
    "can" "cel",
    "rep" "lace",
    "sub" "mit",
    "sig" "n",
    "tra" "de",
    "net" "work",
    "data" "base",
    "mut" "ation",
    "per" "sist",
)


@dataclass(frozen=True)
class CandidateDecisionEvidenceAdapterConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION
    min_pass_source_count: Decimal = Decimal("3")
    min_research_source_count: Decimal = Decimal("2")
    min_pass_fresh_source_count: Decimal = Decimal("2")
    stale_freshness_minutes: Decimal = Decimal("60.000000")
    min_pass_evidence_score: Decimal = Decimal("0.850000")
    min_authority_score: Decimal = Decimal("0.700000")
    min_redundancy_score: Decimal = Decimal("0.500000")
    min_traceability_score: Decimal = Decimal("0.500000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.750000")
    hard_block_evidence_score: Decimal = Decimal("0.300000")
    source_count_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.150000")
    authority_weight: Decimal = Decimal("0.250000")
    redundancy_weight: Decimal = Decimal("0.100000")
    contradiction_weight: Decimal = Decimal("0.150000")
    traceability_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceAdapterConfig:
            raise TypeError(
                "CandidateDecisionEvidenceAdapterConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionEvidenceAdapterConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_source_count",
            "min_research_source_count",
            "min_pass_fresh_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_freshness_minutes",
            _require_nonnegative_decimal(
                "stale_freshness_minutes",
                self.stale_freshness_minutes,
            ),
        )
        for field_name in (
            "min_pass_evidence_score",
            "min_authority_score",
            "min_redundancy_score",
            "min_traceability_score",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "hard_block_evidence_score",
            "source_count_weight",
            "freshness_weight",
            "authority_weight",
            "redundancy_weight",
            "contradiction_weight",
            "traceability_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_freshness_minutes <= ZERO:
            raise ValueError("stale_freshness_minutes must be positive")
        if self.min_research_source_count > self.min_pass_source_count:
            raise ValueError(
                "min_research_source_count must be no greater than min_pass_source_count",
            )
        if self.contradiction_watch_threshold > self.contradiction_block_threshold:
            raise ValueError(
                "contradiction_watch_threshold must be no greater than "
                "contradiction_block_threshold",
            )
        if self.hard_block_evidence_score >= self.min_pass_evidence_score:
            raise ValueError("hard_block_evidence_score must be below min_pass_evidence_score")
        if self.hard_block_evidence_score >= Decimal("0.350000"):
            raise ValueError(
                "hard_block_evidence_score must stay below the candidate blocker threshold",
            )
        weight_sum = (
            self.source_count_weight
            + self.freshness_weight
            + self.authority_weight
            + self.redundancy_weight
            + self.contradiction_weight
            + self.traceability_weight
        )
        if _quantize(weight_sum) != ONE:
            raise ValueError("evidence component weights must sum to one")
        _reject_unsafe_public_surface("candidate decision evidence adapter config", self)
        require_paper_only_flags("CandidateDecisionEvidenceAdapterConfig", self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceAdapterInput:
    source_count: Decimal
    fresh_source_count: Decimal
    authority_score: Decimal
    redundancy_score: Decimal
    contradiction_score: Decimal
    traceability_score: Decimal
    freshness_minutes: Decimal | None = None
    stale_source_count: Decimal | None = None
    source_report_refs: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceAdapterInput:
            raise TypeError(
                "CandidateDecisionEvidenceAdapterInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, CandidateDecisionEvidenceAdapterInput)
        for field_name in ("source_count", "fresh_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_source_count > self.source_count:
            raise ValueError("fresh_source_count must be no greater than source_count")
        for field_name in (
            "authority_score",
            "redundancy_score",
            "contradiction_score",
            "traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_minutes is None and self.stale_source_count is None:
            raise ValueError("freshness_minutes or stale_source_count is required")
        if self.freshness_minutes is not None and self.stale_source_count is not None:
            raise ValueError(
                "freshness_minutes and stale_source_count must not both be supplied",
            )
        if self.freshness_minutes is not None:
            object.__setattr__(
                self,
                "freshness_minutes",
                _require_nonnegative_decimal("freshness_minutes", self.freshness_minutes),
            )
        if self.stale_source_count is not None:
            stale_count = _require_nonnegative_count_decimal(
                "stale_source_count",
                self.stale_source_count,
            )
            if stale_count > self.source_count:
                raise ValueError("stale_source_count must be no greater than source_count")
            if self.fresh_source_count + stale_count > self.source_count:
                raise ValueError(
                    "fresh_source_count plus stale_source_count must not exceed source_count",
                )
            object.__setattr__(self, "stale_source_count", stale_count)
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_public_string_tuple("source_report_refs", self.source_report_refs),
        )
        _reject_unsafe_public_surface("candidate decision evidence adapter input", self)
        require_paper_only_flags("CandidateDecisionEvidenceAdapterInput", self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceAdapterComponent:
    component_name: str
    component_score: Decimal
    component_weight: Decimal
    weighted_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceAdapterComponent:
            raise TypeError(
                "CandidateDecisionEvidenceAdapterComponent does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("component", self, CandidateDecisionEvidenceAdapterComponent)
        if self.component_name not in COMPONENT_NAMES:
            raise ValueError("component_name must be a known component")
        for field_name in ("component_score", "component_weight", "weighted_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        expected = _weighted_score(self.component_score, self.component_weight)
        if self.weighted_score != expected:
            raise ValueError("weighted_score must match component_score times weight")
        _reject_unsafe_public_surface("candidate decision evidence adapter component", self)
        require_paper_only_flags("CandidateDecisionEvidenceAdapterComponent", self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceAdapterResult:
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    authority_score: Decimal
    redundancy_score: Decimal
    contradiction_score: Decimal
    traceability_score: Decimal
    freshness_minutes: Decimal | None
    components: tuple[CandidateDecisionEvidenceAdapterComponent, ...]
    weighted_evidence_score: Decimal
    evidence_score: Decimal
    evidence_status: str
    reason_codes: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    config_version: str = DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceAdapterResult:
            raise TypeError(
                "CandidateDecisionEvidenceAdapterResult does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("result", self, CandidateDecisionEvidenceAdapterResult)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("source_count", "fresh_source_count", "stale_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_source_count > self.source_count:
            raise ValueError("fresh_source_count must be no greater than source_count")
        if self.stale_source_count > self.source_count:
            raise ValueError("stale_source_count must be no greater than source_count")
        for field_name in (
            "authority_score",
            "redundancy_score",
            "contradiction_score",
            "traceability_score",
            "weighted_evidence_score",
            "evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_minutes is not None:
            object.__setattr__(
                self,
                "freshness_minutes",
                _require_nonnegative_decimal("freshness_minutes", self.freshness_minutes),
            )
        object.__setattr__(self, "components", _normalize_components(self.components))
        _require_member("evidence_status", self.evidence_status, EVIDENCE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_public_string_tuple("source_report_refs", self.source_report_refs),
        )
        _validate_result(self)
        _reject_unsafe_public_surface("candidate decision evidence adapter result", self)
        require_paper_only_flags("CandidateDecisionEvidenceAdapterResult", self)


def build_candidate_decision_evidence_adapter_result(
    evidence: CandidateDecisionEvidenceAdapterInput,
    *,
    config: CandidateDecisionEvidenceAdapterConfig | None = None,
) -> CandidateDecisionEvidenceAdapterResult:
    if config is None:
        config = CandidateDecisionEvidenceAdapterConfig()
    _require_exact_type("evidence", evidence, CandidateDecisionEvidenceAdapterInput)
    _require_exact_type("config", config, CandidateDecisionEvidenceAdapterConfig)
    require_paper_only_flags("CandidateDecisionEvidenceAdapterInput", evidence)
    require_paper_only_flags("CandidateDecisionEvidenceAdapterConfig", config)
    components = _components(evidence, config)
    weighted_score = _sum_weighted_scores(components)
    blocked = _has_hard_blocker(evidence, config)
    evidence_score = config.hard_block_evidence_score if blocked else weighted_score
    status = _evidence_status(evidence_score, blocked, config)
    return CandidateDecisionEvidenceAdapterResult(
        source_count=evidence.source_count,
        fresh_source_count=evidence.fresh_source_count,
        stale_source_count=_stale_source_count(evidence),
        authority_score=evidence.authority_score,
        redundancy_score=evidence.redundancy_score,
        contradiction_score=evidence.contradiction_score,
        traceability_score=evidence.traceability_score,
        freshness_minutes=evidence.freshness_minutes,
        components=components,
        weighted_evidence_score=weighted_score,
        evidence_score=evidence_score,
        evidence_status=status,
        reason_codes=_reason_codes(evidence, evidence_score, blocked, config),
        source_report_refs=evidence.source_report_refs,
        config_version=config.config_version,
    )


def candidate_decision_evidence_adapter_decision_fields(
    result: CandidateDecisionEvidenceAdapterResult,
) -> dict[str, object]:
    _require_exact_type("result", result, CandidateDecisionEvidenceAdapterResult)
    require_paper_only_flags("CandidateDecisionEvidenceAdapterResult", result)
    _reject_unsafe_public_surface("candidate decision evidence adapter result", result)
    return {
        "evidence_score": result.evidence_score,
        "adapter_reason_codes": result.reason_codes,
        "source_report_refs": result.source_report_refs,
    }


def candidate_decision_evidence_adapter_payload(
    result: CandidateDecisionEvidenceAdapterResult | Mapping[str, object],
) -> dict[str, Any]:
    if type(result) is CandidateDecisionEvidenceAdapterResult:
        require_paper_only_flags("CandidateDecisionEvidenceAdapterResult", result)
        _reject_unsafe_public_surface("candidate decision evidence adapter result", result)
        payload = json_ready_no_floats(result)
    elif isinstance(result, Mapping):
        _reject_unsafe_public_surface("candidate decision evidence adapter payload", result)
        payload = json_ready_no_floats(dict(result))
    else:
        raise ValueError(
            "result must be a CandidateDecisionEvidenceAdapterResult or mapping",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_surface("candidate decision evidence adapter payload", payload)
    return payload


def _components(
    evidence: CandidateDecisionEvidenceAdapterInput,
    config: CandidateDecisionEvidenceAdapterConfig,
) -> tuple[CandidateDecisionEvidenceAdapterComponent, ...]:
    values = {
        "authority_score": (
            evidence.authority_score,
            config.authority_weight,
        ),
        "contradiction_absence_score": (
            ONE - evidence.contradiction_score,
            config.contradiction_weight,
        ),
        "freshness_score": (
            _freshness_score(evidence, config),
            config.freshness_weight,
        ),
        "redundancy_score": (
            evidence.redundancy_score,
            config.redundancy_weight,
        ),
        "source_count_score": (
            _ratio_capped(evidence.source_count, config.min_pass_source_count),
            config.source_count_weight,
        ),
        "traceability_score": (
            evidence.traceability_score,
            config.traceability_weight,
        ),
    }
    return tuple(
        CandidateDecisionEvidenceAdapterComponent(
            component_name=name,
            component_score=score,
            component_weight=weight,
            weighted_score=_weighted_score(score, weight),
        )
        for name, (score, weight) in sorted(values.items())
    )


def _freshness_score(
    evidence: CandidateDecisionEvidenceAdapterInput,
    config: CandidateDecisionEvidenceAdapterConfig,
) -> Decimal:
    if evidence.freshness_minutes is not None:
        if evidence.freshness_minutes >= config.stale_freshness_minutes:
            return ZERO
        with localcontext(DECIMAL_CONTEXT):
            return _quantize(ONE - (evidence.freshness_minutes / config.stale_freshness_minutes))
    return _ratio_capped(evidence.fresh_source_count, evidence.source_count)


def _ratio_capped(part: Decimal, whole: Decimal) -> Decimal:
    if part <= ZERO or whole <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = _quantize(part / whole)
    if value > ONE:
        return ONE
    return value


def _weighted_score(score: Decimal, weight: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(score * weight)


def _sum_weighted_scores(
    components: tuple[CandidateDecisionEvidenceAdapterComponent, ...],
) -> Decimal:
    return _clamp_probability(
        sum((component.weighted_score for component in components), ZERO),
    )


def _stale_source_count(evidence: CandidateDecisionEvidenceAdapterInput) -> Decimal:
    if evidence.stale_source_count is not None:
        return evidence.stale_source_count
    return _quantize(evidence.source_count - evidence.fresh_source_count)


def _has_hard_blocker(
    evidence: CandidateDecisionEvidenceAdapterInput,
    config: CandidateDecisionEvidenceAdapterConfig,
) -> bool:
    return (
        evidence.contradiction_score >= config.contradiction_block_threshold
        or evidence.traceability_score == ZERO
    )


def _evidence_status(
    evidence_score: Decimal,
    blocked: bool,
    config: CandidateDecisionEvidenceAdapterConfig,
) -> str:
    if blocked:
        return "blocked"
    if evidence_score < config.min_pass_evidence_score:
        return "research_more"
    return "pass"


def _reason_codes(
    evidence: CandidateDecisionEvidenceAdapterInput,
    evidence_score: Decimal,
    blocked: bool,
    config: CandidateDecisionEvidenceAdapterConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    status = _evidence_status(evidence_score, blocked, config)
    codes.append(f"evidence_adapter_{status}")
    if evidence.source_count < config.min_research_source_count and evidence.source_count != ONE:
        codes.append("evidence_source_count_low")
    if evidence.source_count == ONE:
        codes.append("evidence_single_source_research_more")
    if evidence.source_count != ONE and evidence.fresh_source_count < config.min_pass_fresh_source_count:
        codes.append("evidence_fresh_source_count_low")
    if evidence.stale_source_count is not None and evidence.stale_source_count > ZERO:
        codes.append("evidence_stale_sources_present")
    if (
        evidence.freshness_minutes is not None
        and evidence.freshness_minutes >= config.stale_freshness_minutes
    ):
        codes.append("evidence_freshness_stale")
    if evidence.authority_score < config.min_authority_score:
        codes.append("evidence_authority_low")
    if evidence.redundancy_score < config.min_redundancy_score:
        codes.append("evidence_redundancy_low")
    if evidence.traceability_score == ZERO:
        codes.append("evidence_traceability_missing")
    elif evidence.traceability_score < config.min_traceability_score:
        codes.append("evidence_traceability_low")
    if evidence.contradiction_score >= config.contradiction_block_threshold:
        codes.append("evidence_contradiction_blocked")
    elif evidence.contradiction_score >= config.contradiction_watch_threshold:
        codes.append("evidence_contradiction_watch")
    if status == "research_more":
        codes.append("evidence_weighted_score_below_pass_threshold")
    return _normalize_reason_codes(tuple(codes))


def _normalize_components(value: object) -> tuple[CandidateDecisionEvidenceAdapterComponent, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("components must be a list or tuple")
    components = tuple(value)
    for component in components:
        if type(component) is not CandidateDecisionEvidenceAdapterComponent:
            raise ValueError(
                "components must contain CandidateDecisionEvidenceAdapterComponent values",
            )
        require_paper_only_flags("CandidateDecisionEvidenceAdapterComponent", component)
    names = tuple(component.component_name for component in components)
    if names != COMPONENT_NAMES:
        raise ValueError("components must use canonical component ordering")
    if len(set(names)) != len(names):
        raise ValueError("components must not contain duplicates")
    return components


def _validate_result(result: CandidateDecisionEvidenceAdapterResult) -> None:
    expected_weighted_score = _sum_weighted_scores(result.components)
    if result.weighted_evidence_score != expected_weighted_score:
        raise ValueError("weighted_evidence_score must match component weighted scores")
    if result.evidence_status == "blocked" and result.evidence_score >= Decimal("0.350000"):
        raise ValueError("blocked evidence_score must stay below the candidate blocker threshold")
    expected_action_reason = f"evidence_adapter_{result.evidence_status}"
    if result.reason_codes[0] != expected_action_reason:
        raise ValueError("reason_codes must start with evidence status reason")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in REASON_CODE_ORDER:
            raise ValueError("reason_code must be a known reason code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    status_codes = tuple(code for code in reason_codes if code.startswith("evidence_adapter_"))
    if len(status_codes) != 1:
        raise ValueError("reason_codes must contain one evidence status reason")
    expected_order = tuple(code for code in REASON_CODE_ORDER if code in reason_codes)
    if reason_codes != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    return reason_codes


def _normalize_public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(items))


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for key in _iter_public_keys(value):
        normalized = key.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"unsafe public surface field in {label}: {key}")


def _iter_public_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for field in fields(value):
            keys.append(field.name)
            keys.extend(_iter_public_keys(getattr(value, field.name)))
        return tuple(keys)
    if isinstance(value, Mapping):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    if type(value) in (list, tuple):
        keys = []
        for item in value:
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    return ()


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _clamp_probability(value: Decimal) -> Decimal:
    return min(max(_quantize(value), ZERO), ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION",
    "CandidateDecisionEvidenceAdapterConfig",
    "CandidateDecisionEvidenceAdapterInput",
    "CandidateDecisionEvidenceAdapterComponent",
    "CandidateDecisionEvidenceAdapterResult",
    "build_candidate_decision_evidence_adapter_result",
    "candidate_decision_evidence_adapter_decision_fields",
    "candidate_decision_evidence_adapter_payload",
)
