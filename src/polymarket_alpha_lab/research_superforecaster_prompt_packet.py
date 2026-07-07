"""Pure read-only superforecaster prompt packet builder."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DECIMAL_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MASK = "<redacted>"

PUBLIC_STATUSES = ("pass", "watch", "block")
PROMPT_AUDIENCES = ("human", "llm")
REASON_CODES = (
    "evidence_ready",
    "evidence_missing",
    "base_rate_ready",
    "base_rate_missing",
    "rule_risk_within_threshold",
    "rule_risk_above_threshold",
    "cost_within_threshold",
    "cost_above_threshold",
    "unsafe_public_content_redacted",
    "public_status_pass",
    "public_status_watch",
    "public_status_block",
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(chr(code) for code in codes)
    for codes in (
        (114, 97, 119, 45, 99, 97, 110, 100, 105, 100, 97, 116, 101),
        (114, 97, 119, 95, 99, 97, 110, 100, 105, 100, 97, 116, 101),
        (99, 97, 110, 100, 105, 100, 97, 116, 101, 95, 105, 100),
        (109, 97, 114, 107, 101, 116, 95, 105, 100),
        (109, 97, 114, 107, 101, 116, 95, 115, 108, 117, 103),
        (113, 117, 101, 115, 116, 105, 111, 110),
        (115, 111, 117, 114, 99, 101, 95, 114, 101, 102),
        (115, 111, 117, 114, 99, 101, 95, 117, 114, 108),
        (115, 111, 117, 114, 99, 101, 95, 116, 101, 120, 116),
        (104, 116, 116, 112, 58, 47, 47),
        (104, 116, 116, 112, 115, 58, 47, 47),
        (58, 47, 47),
        (100, 115, 110),
        (116, 97, 98, 108, 101),
        (116, 111, 107, 101, 110),
        (119, 97, 108, 108, 101, 116),
        (97, 117, 116, 104),
        (111, 114, 100, 101, 114),
        (116, 114, 97, 100, 101),
        (112, 111, 115, 105, 116, 105, 111, 110),
        (98, 117, 121),
        (115, 101, 108, 108),
        (114, 101, 99, 111, 109, 109, 101, 110, 100, 97, 116, 105, 111, 110),
    )
)


@dataclass(frozen=True)
class SuperforecasterEvidenceSummary:
    assessment_label: str
    evidence_strength: Decimal
    independent_evidence_count: Decimal
    missing_evidence_count: Decimal
    evidence_points: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assessment_label",
            _normalize_public_string("assessment_label", self.assessment_label),
        )
        object.__setattr__(
            self,
            "evidence_strength",
            _normalize_probability("evidence_strength", self.evidence_strength),
        )
        object.__setattr__(
            self,
            "independent_evidence_count",
            _normalize_nonnegative_count(
                "independent_evidence_count",
                self.independent_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "missing_evidence_count",
            _normalize_nonnegative_count(
                "missing_evidence_count",
                self.missing_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "evidence_points",
            _normalize_public_string_tuple("evidence_points", self.evidence_points),
        )
        require_paper_only_flags("superforecaster evidence summary", self)


@dataclass(frozen=True)
class SuperforecasterBaseRateSummary:
    reference_class: str
    base_rate_probability: Decimal
    base_rate_sample_count: Decimal
    base_rate_quality: Decimal
    base_rate_points: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_class",
            _normalize_public_string("reference_class", self.reference_class),
        )
        object.__setattr__(
            self,
            "base_rate_probability",
            _normalize_probability(
                "base_rate_probability",
                self.base_rate_probability,
            ),
        )
        object.__setattr__(
            self,
            "base_rate_sample_count",
            _normalize_nonnegative_count(
                "base_rate_sample_count",
                self.base_rate_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "base_rate_quality",
            _normalize_probability("base_rate_quality", self.base_rate_quality),
        )
        object.__setattr__(
            self,
            "base_rate_points",
            _normalize_public_string_tuple("base_rate_points", self.base_rate_points),
        )
        require_paper_only_flags("superforecaster base rate summary", self)


@dataclass(frozen=True)
class SuperforecasterRuleRiskSummary:
    rule_clarity: Decimal
    resolution_rule_risk: Decimal
    ambiguity_risk: Decimal
    rule_risk_codes: tuple[str, ...]
    rule_points: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "rule_clarity",
            "resolution_rule_risk",
            "ambiguity_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rule_risk_codes",
            _normalize_public_string_tuple(
                "rule_risk_codes",
                self.rule_risk_codes,
            ),
        )
        object.__setattr__(
            self,
            "rule_points",
            _normalize_public_string_tuple("rule_points", self.rule_points),
        )
        require_paper_only_flags("superforecaster rule risk summary", self)


@dataclass(frozen=True)
class SuperforecasterCostThreshold:
    maximum_research_cost_bps: Decimal
    estimated_research_cost_bps: Decimal
    minimum_evidence_strength: Decimal
    minimum_base_rate_count: Decimal
    maximum_rule_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "maximum_research_cost_bps",
            "estimated_research_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_evidence_strength",
            _normalize_probability(
                "minimum_evidence_strength",
                self.minimum_evidence_strength,
            ),
        )
        object.__setattr__(
            self,
            "minimum_base_rate_count",
            _normalize_nonnegative_count(
                "minimum_base_rate_count",
                self.minimum_base_rate_count,
            ),
        )
        object.__setattr__(
            self,
            "maximum_rule_risk",
            _normalize_probability("maximum_rule_risk", self.maximum_rule_risk),
        )
        require_paper_only_flags("superforecaster cost threshold", self)


@dataclass(frozen=True)
class SuperforecasterPromptSection:
    audience: str
    task_label: str
    instructions: tuple[str, ...]
    context_points: tuple[str, ...]
    checklist: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("audience", self.audience, PROMPT_AUDIENCES)
        object.__setattr__(
            self,
            "task_label",
            _normalize_public_string("task_label", self.task_label),
        )
        for field_name in ("instructions", "context_points", "checklist"):
            object.__setattr__(
                self,
                field_name,
                _normalize_public_string_tuple(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("superforecaster prompt section", self)
        _reject_unsafe_public_payload(
            "superforecaster prompt section",
            _json_object(self),
        )


@dataclass(frozen=True)
class ResearchSuperforecasterPromptPacket:
    status: str
    evidence_summary: SuperforecasterEvidenceSummary
    base_rate_summary: SuperforecasterBaseRateSummary
    rule_risk_summary: SuperforecasterRuleRiskSummary
    cost_threshold: SuperforecasterCostThreshold
    prompt_sections: tuple[SuperforecasterPromptSection, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("status", self.status, PUBLIC_STATUSES)
        _require_exact_type(
            "evidence_summary",
            self.evidence_summary,
            SuperforecasterEvidenceSummary,
        )
        _require_exact_type(
            "base_rate_summary",
            self.base_rate_summary,
            SuperforecasterBaseRateSummary,
        )
        _require_exact_type(
            "rule_risk_summary",
            self.rule_risk_summary,
            SuperforecasterRuleRiskSummary,
        )
        _require_exact_type(
            "cost_threshold",
            self.cost_threshold,
            SuperforecasterCostThreshold,
        )
        object.__setattr__(
            self,
            "prompt_sections",
            _normalize_prompt_sections(self.prompt_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("research superforecaster prompt packet", self)
        _validate_packet(self)
        payload = _packet_payload(
            status=self.status,
            evidence_summary=self.evidence_summary,
            base_rate_summary=self.base_rate_summary,
            rule_risk_summary=self.rule_risk_summary,
            cost_threshold=self.cost_threshold,
            prompt_sections=self.prompt_sections,
            reason_codes=self.reason_codes,
            derived_validation_digest=self.derived_validation_digest,
        )
        reject_unsafe_surface_fields("research superforecaster prompt packet", payload)
        _reject_unsafe_public_payload(
            "research superforecaster prompt packet",
            payload,
        )

    @property
    def payload(self) -> dict[str, Any]:
        return research_superforecaster_prompt_packet_payload(self)


def build_research_superforecaster_prompt_packet(
    evidence_summary: SuperforecasterEvidenceSummary,
    base_rate_summary: SuperforecasterBaseRateSummary,
    rule_risk_summary: SuperforecasterRuleRiskSummary,
    cost_threshold: SuperforecasterCostThreshold,
) -> ResearchSuperforecasterPromptPacket:
    _require_exact_type(
        "evidence_summary",
        evidence_summary,
        SuperforecasterEvidenceSummary,
    )
    _require_exact_type(
        "base_rate_summary",
        base_rate_summary,
        SuperforecasterBaseRateSummary,
    )
    _require_exact_type(
        "rule_risk_summary",
        rule_risk_summary,
        SuperforecasterRuleRiskSummary,
    )
    _require_exact_type(
        "cost_threshold",
        cost_threshold,
        SuperforecasterCostThreshold,
    )
    for label, value in (
        ("evidence_summary", evidence_summary),
        ("base_rate_summary", base_rate_summary),
        ("rule_risk_summary", rule_risk_summary),
        ("cost_threshold", cost_threshold),
    ):
        require_paper_only_flags(label, value)
    status = _derive_status(
        evidence_summary,
        base_rate_summary,
        rule_risk_summary,
        cost_threshold,
    )
    prompt_sections = _build_prompt_sections(
        status,
        evidence_summary,
        base_rate_summary,
        rule_risk_summary,
        cost_threshold,
    )
    reason_codes = _derive_reason_codes(
        status,
        evidence_summary,
        base_rate_summary,
        rule_risk_summary,
        cost_threshold,
    )
    digest = _digest_payload(
        _packet_payload(
            status=status,
            evidence_summary=evidence_summary,
            base_rate_summary=base_rate_summary,
            rule_risk_summary=rule_risk_summary,
            cost_threshold=cost_threshold,
            prompt_sections=prompt_sections,
            reason_codes=reason_codes,
            derived_validation_digest=None,
        ),
    )
    return ResearchSuperforecasterPromptPacket(
        status=status,
        evidence_summary=evidence_summary,
        base_rate_summary=base_rate_summary,
        rule_risk_summary=rule_risk_summary,
        cost_threshold=cost_threshold,
        prompt_sections=prompt_sections,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
    )


def research_superforecaster_prompt_packet_payload(
    result: ResearchSuperforecasterPromptPacket | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is dict:
        require_paper_only_flags("research superforecaster prompt packet payload", _DictFlags(result))
        payload = json_ready_no_floats(result)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        reject_unsafe_surface_fields(
            "research superforecaster prompt packet payload",
            payload,
        )
        _reject_unsafe_public_payload(
            "research superforecaster prompt packet payload",
            payload,
        )
        return payload
    _require_exact_type("result", result, ResearchSuperforecasterPromptPacket)
    require_paper_only_flags("research superforecaster prompt packet", result)
    payload = _packet_payload(
        status=result.status,
        evidence_summary=result.evidence_summary,
        base_rate_summary=result.base_rate_summary,
        rule_risk_summary=result.rule_risk_summary,
        cost_threshold=result.cost_threshold,
        prompt_sections=result.prompt_sections,
        reason_codes=result.reason_codes,
        derived_validation_digest=result.derived_validation_digest,
    )
    reject_unsafe_surface_fields("research superforecaster prompt packet payload", payload)
    _reject_unsafe_public_payload(
        "research superforecaster prompt packet payload",
        payload,
    )
    return payload


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


def _build_prompt_sections(
    status: str,
    evidence_summary: SuperforecasterEvidenceSummary,
    base_rate_summary: SuperforecasterBaseRateSummary,
    rule_risk_summary: SuperforecasterRuleRiskSummary,
    cost_threshold: SuperforecasterCostThreshold,
) -> tuple[SuperforecasterPromptSection, ...]:
    context_points = _context_points(
        status,
        evidence_summary,
        base_rate_summary,
        rule_risk_summary,
        cost_threshold,
    )
    checklist = (
        "compare_prior_to_new_facts",
        "state_uncertainty_drivers",
        "separate_rule_risk_from_event_risk",
        "return_probability_only",
    )
    return (
        SuperforecasterPromptSection(
            audience="human",
            task_label="manual_research_review",
            instructions=(
                "review_redacted_evidence_summary",
                "challenge_base_rate_fit",
                "record_missing_checks_before_use",
                "keep_output_readonly",
            ),
            context_points=context_points,
            checklist=checklist,
        ),
        SuperforecasterPromptSection(
            audience="llm",
            task_label="structured_probability_research",
            instructions=(
                "use_only_redacted_public_packet",
                "estimate_probability_with_calibration_notes",
                "flag_missing_evidence_without_external_action",
                "return_json_ready_reasoning",
            ),
            context_points=context_points,
            checklist=checklist,
        ),
    )


def _context_points(
    status: str,
    evidence_summary: SuperforecasterEvidenceSummary,
    base_rate_summary: SuperforecasterBaseRateSummary,
    rule_risk_summary: SuperforecasterRuleRiskSummary,
    cost_threshold: SuperforecasterCostThreshold,
) -> tuple[str, ...]:
    return (
        f"packet_status={status}",
        f"evidence_strength={evidence_summary.evidence_strength}",
        f"missing_evidence_count={evidence_summary.missing_evidence_count}",
        f"base_rate_probability={base_rate_summary.base_rate_probability}",
        f"base_rate_sample_count={base_rate_summary.base_rate_sample_count}",
        f"rule_risk={rule_risk_summary.resolution_rule_risk}",
        f"ambiguity_risk={rule_risk_summary.ambiguity_risk}",
        f"estimated_research_cost_bps={cost_threshold.estimated_research_cost_bps}",
    )


def _derive_status(
    evidence_summary: SuperforecasterEvidenceSummary,
    base_rate_summary: SuperforecasterBaseRateSummary,
    rule_risk_summary: SuperforecasterRuleRiskSummary,
    cost_threshold: SuperforecasterCostThreshold,
) -> str:
    if (
        _has_redacted_public_value(evidence_summary)
        or _has_redacted_public_value(base_rate_summary)
        or _has_redacted_public_value(rule_risk_summary)
        or cost_threshold.estimated_research_cost_bps
        > cost_threshold.maximum_research_cost_bps
        or _max_rule_risk(rule_risk_summary) > cost_threshold.maximum_rule_risk
    ):
        return "block"
    if (
        evidence_summary.evidence_strength < cost_threshold.minimum_evidence_strength
        or evidence_summary.missing_evidence_count > ZERO
        or not evidence_summary.evidence_points
        or base_rate_summary.base_rate_sample_count
        < cost_threshold.minimum_base_rate_count
        or not base_rate_summary.base_rate_points
        or not rule_risk_summary.rule_risk_codes
        or not rule_risk_summary.rule_points
    ):
        return "watch"
    return "pass"


def _derive_reason_codes(
    status: str,
    evidence_summary: SuperforecasterEvidenceSummary,
    base_rate_summary: SuperforecasterBaseRateSummary,
    rule_risk_summary: SuperforecasterRuleRiskSummary,
    cost_threshold: SuperforecasterCostThreshold,
) -> tuple[str, ...]:
    codes = [
        (
            "evidence_ready"
            if (
                evidence_summary.evidence_strength
                >= cost_threshold.minimum_evidence_strength
                and evidence_summary.missing_evidence_count == ZERO
                and bool(evidence_summary.evidence_points)
            )
            else "evidence_missing"
        ),
        (
            "base_rate_ready"
            if (
                base_rate_summary.base_rate_sample_count
                >= cost_threshold.minimum_base_rate_count
                and bool(base_rate_summary.base_rate_points)
            )
            else "base_rate_missing"
        ),
        (
            "rule_risk_within_threshold"
            if _max_rule_risk(rule_risk_summary) <= cost_threshold.maximum_rule_risk
            else "rule_risk_above_threshold"
        ),
        (
            "cost_within_threshold"
            if cost_threshold.estimated_research_cost_bps
            <= cost_threshold.maximum_research_cost_bps
            else "cost_above_threshold"
        ),
    ]
    if (
        _has_redacted_public_value(evidence_summary)
        or _has_redacted_public_value(base_rate_summary)
        or _has_redacted_public_value(rule_risk_summary)
    ):
        codes.append("unsafe_public_content_redacted")
    codes.append(f"public_status_{status}")
    return _normalize_reason_codes(tuple(codes))


def _validate_packet(result: ResearchSuperforecasterPromptPacket) -> None:
    expected_status = _derive_status(
        result.evidence_summary,
        result.base_rate_summary,
        result.rule_risk_summary,
        result.cost_threshold,
    )
    if result.status != expected_status:
        raise ValueError("status must match prompt packet inputs")
    expected_sections = _build_prompt_sections(
        result.status,
        result.evidence_summary,
        result.base_rate_summary,
        result.rule_risk_summary,
        result.cost_threshold,
    )
    if result.prompt_sections != expected_sections:
        raise ValueError("prompt_sections must match prompt packet inputs")
    expected_reason_codes = _derive_reason_codes(
        result.status,
        result.evidence_summary,
        result.base_rate_summary,
        result.rule_risk_summary,
        result.cost_threshold,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match prompt packet inputs")
    expected_digest = _digest_payload(
        _packet_payload(
            status=result.status,
            evidence_summary=result.evidence_summary,
            base_rate_summary=result.base_rate_summary,
            rule_risk_summary=result.rule_risk_summary,
            cost_threshold=result.cost_threshold,
            prompt_sections=result.prompt_sections,
            reason_codes=result.reason_codes,
            derived_validation_digest=None,
        ),
    )
    if result.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match prompt packet payload")


def _packet_payload(
    *,
    status: str,
    evidence_summary: SuperforecasterEvidenceSummary,
    base_rate_summary: SuperforecasterBaseRateSummary,
    rule_risk_summary: SuperforecasterRuleRiskSummary,
    cost_threshold: SuperforecasterCostThreshold,
    prompt_sections: tuple[SuperforecasterPromptSection, ...],
    reason_codes: tuple[str, ...],
    derived_validation_digest: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "evidence_summary": _json_object(evidence_summary),
        "base_rate_summary": _json_object(base_rate_summary),
        "rule_risk_summary": _json_object(rule_risk_summary),
        "cost_threshold": _json_object(cost_threshold),
        "prompt_sections": [_json_object(section) for section in prompt_sections],
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if derived_validation_digest is not None:
        payload["derived_validation_digest"] = derived_validation_digest
    return payload


def _json_object(value: object) -> dict[str, Any]:
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError("payload component must be a JSON object")
    _reject_unsafe_public_payload(
        "research superforecaster prompt packet component",
        payload,
    )
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _normalize_prompt_sections(
    value: object,
) -> tuple[SuperforecasterPromptSection, ...]:
    if type(value) is not tuple:
        raise ValueError("prompt_sections must be a tuple")
    if tuple(section.audience for section in value) != PROMPT_AUDIENCES:
        raise ValueError("prompt_sections must contain human and llm sections")
    for section in value:
        _require_exact_type("prompt_sections", section, SuperforecasterPromptSection)
        require_paper_only_flags("prompt section", section)
    return value


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_public_string_tuple("reason_codes", values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return normalized


def _normalize_public_string_tuple(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(_normalize_public_string(field_name, item) for item in value)


def _normalize_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_text(value):
        return MASK
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value).quantize(DECIMAL_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or "\n" in value
        or "\r" in value
        or "\t" in value
    ):
        raise ValueError(f"{field_name} must contain canonical strings")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_digest(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _max_rule_risk(rule_risk_summary: SuperforecasterRuleRiskSummary) -> Decimal:
    return max(rule_risk_summary.resolution_rule_risk, rule_risk_summary.ambiguity_risk)


def _has_redacted_public_value(value: object) -> bool:
    if isinstance(value, str):
        return value == MASK
    if isinstance(value, Decimal):
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, tuple):
        return any(_has_redacted_public_value(item) for item in value)
    if hasattr(value, "__dataclass_fields__"):
        return any(
            _has_redacted_public_value(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        )
    return False


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        if _contains_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload text in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


__all__ = (
    "MASK",
    "PROMPT_AUDIENCES",
    "PUBLIC_STATUSES",
    "REASON_CODES",
    "ResearchSuperforecasterPromptPacket",
    "SuperforecasterBaseRateSummary",
    "SuperforecasterCostThreshold",
    "SuperforecasterEvidenceSummary",
    "SuperforecasterPromptSection",
    "SuperforecasterRuleRiskSummary",
    "build_research_superforecaster_prompt_packet",
    "research_superforecaster_prompt_packet_payload",
)
