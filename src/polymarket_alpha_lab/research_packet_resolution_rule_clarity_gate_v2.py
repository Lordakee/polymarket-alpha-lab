"""Pure paper/report/readonly resolution rule clarity gate v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Any


SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REQUIRED_RESOLUTION_CRITERIA_COUNT = Decimal("4.000000")
REQUIRED_EDGE_CASE_COVERAGE_COUNT = Decimal("4.000000")
AMBIGUOUS_PHRASE_CAP = Decimal("5.000000")
DISPUTE_PRONE_TRIGGER_CAP = Decimal("4.000000")
HEAVY_AMBIGUOUS_PHRASE_COUNT = Decimal("5.000000")
HEAVY_DISPUTE_PRONE_TRIGGER_COUNT = Decimal("4.000000")

WEIGHT_RESOLUTION_CRITERIA = Decimal("0.288000")
WEIGHT_OFFICIAL_SOURCE_MAPPING = Decimal("0.292000")
WEIGHT_AMBIGUITY_ABSENCE = Decimal("0.200000")
WEIGHT_EDGE_CASE_COVERAGE = Decimal("0.150000")
WEIGHT_DISPUTE_TRIGGER_ABSENCE = Decimal("0.070000")

PASS_CLARITY_THRESHOLD = Decimal("0.800000")
REVIEW_CLARITY_THRESHOLD = Decimal("0.400000")

CLARITY_GATE_STATUSES = ("pass", "review", "blocked")
RECOMMENDED_ACTIONS = (
    "include_in_research_packet",
    "clarify_before_packet_use",
    "exclude_until_rules_are_clarified",
)
REQUIRED_FOLLOWUPS = (
    "define_measurable_resolution_criteria",
    "map_each_resolution_criterion_to_official_source",
    "remove_or_define_ambiguous_rule_phrasing",
    "add_missing_edge_case_resolution_paths",
    "neutralize_dispute_prone_trigger_language",
)
REASON_CODES = (
    "clarity_status_pass",
    "clarity_status_review",
    "clarity_status_blocked",
    "resolution_criteria_complete",
    "resolution_criteria_partial",
    "resolution_criteria_missing",
    "official_sources_complete",
    "official_sources_partial",
    "official_sources_missing",
    "edge_cases_complete",
    "edge_cases_partial",
    "edge_cases_missing",
    "ambiguous_phrasing_clear",
    "ambiguous_phrasing_present",
    "ambiguous_phrasing_heavy",
    "dispute_triggers_clear",
    "dispute_triggers_present",
    "dispute_triggers_heavy",
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
class ResearchPacketResolutionRuleClarityGateV2Input:
    packet_id: str
    market_slug: str
    rule_text_excerpt: str
    resolution_criteria_count: Decimal
    official_source_mapping_count: Decimal
    ambiguous_phrase_count: Decimal
    edge_case_coverage_count: Decimal
    dispute_prone_trigger_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketResolutionRuleClarityGateV2Input:
            raise ValueError(
                "subject must be a ResearchPacketResolutionRuleClarityGateV2Input",
            )
        _require_identifier("packet_id", self.packet_id)
        _require_identifier("market_slug", self.market_slug)
        _require_canonical_string("rule_text_excerpt", self.rule_text_excerpt)
        for field_name in (
            "resolution_criteria_count",
            "official_source_mapping_count",
            "ambiguous_phrase_count",
            "edge_case_coverage_count",
            "dispute_prone_trigger_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_source_mapping_count(
            self.resolution_criteria_count,
            self.official_source_mapping_count,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("rule clarity gate input", asdict(self))


@dataclass(frozen=True)
class ResearchPacketResolutionRuleClarityGateV2Result:
    packet_id: str
    market_slug: str
    rule_text_excerpt: str
    resolution_criteria_count: Decimal
    official_source_mapping_count: Decimal
    ambiguous_phrase_count: Decimal
    edge_case_coverage_count: Decimal
    dispute_prone_trigger_count: Decimal
    resolution_criteria_score: Decimal
    official_source_mapping_score: Decimal
    ambiguity_penalty_score: Decimal
    edge_case_coverage_score: Decimal
    dispute_trigger_penalty_score: Decimal
    clarity_score: Decimal
    clarity_gate_status: str
    recommended_action: str
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketResolutionRuleClarityGateV2Result:
            raise ValueError(
                "result must be a ResearchPacketResolutionRuleClarityGateV2Result",
            )
        _require_identifier("packet_id", self.packet_id)
        _require_identifier("market_slug", self.market_slug)
        _require_canonical_string("rule_text_excerpt", self.rule_text_excerpt)
        for field_name in (
            "resolution_criteria_count",
            "official_source_mapping_count",
            "ambiguous_phrase_count",
            "edge_case_coverage_count",
            "dispute_prone_trigger_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_source_mapping_count(
            self.resolution_criteria_count,
            self.official_source_mapping_count,
        )
        for field_name in (
            "resolution_criteria_score",
            "official_source_mapping_score",
            "ambiguity_penalty_score",
            "edge_case_coverage_score",
            "dispute_trigger_penalty_score",
            "clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("clarity_gate_status", self.clarity_gate_status, CLARITY_GATE_STATUSES)
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
        _reject_unsafe_public_payload("rule clarity gate result", asdict(self))
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
        _reject_unsafe_public_payload("rule clarity gate payload", payload)
        if type(payload) is not dict:
            raise ValueError("rule clarity gate payload must be an object")
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> ResearchPacketResolutionRuleClarityGateV2Result:
        _reject_unsafe_public_payload("rule clarity gate payload", payload)
        payload_dict = _payload_dict("rule clarity gate payload", payload)
        _require_payload_fields(
            payload_dict,
            (
                "packet_id",
                "market_slug",
                "rule_text_excerpt",
                "resolution_criteria_count",
                "official_source_mapping_count",
                "ambiguous_phrase_count",
                "edge_case_coverage_count",
                "dispute_prone_trigger_count",
                "resolution_criteria_score",
                "official_source_mapping_score",
                "ambiguity_penalty_score",
                "edge_case_coverage_score",
                "dispute_trigger_penalty_score",
                "clarity_score",
                "clarity_gate_status",
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
        return cls(
            **values,
            derived_validation_digest=supplied_digest,
        )


def build_research_packet_resolution_rule_clarity_gate_v2(
    subject: ResearchPacketResolutionRuleClarityGateV2Input,
) -> ResearchPacketResolutionRuleClarityGateV2Result:
    if type(subject) is not ResearchPacketResolutionRuleClarityGateV2Input:
        raise ValueError("subject must be a ResearchPacketResolutionRuleClarityGateV2Input")
    _require_hard_flags(subject)
    _reject_unsafe_public_payload("rule clarity gate input", asdict(subject))

    resolution_criteria_score = _ratio_capped(
        subject.resolution_criteria_count,
        REQUIRED_RESOLUTION_CRITERIA_COUNT,
    )
    official_source_mapping_score = _official_source_mapping_score(
        subject.resolution_criteria_count,
        subject.official_source_mapping_count,
    )
    ambiguity_penalty_score = _ratio_capped(
        subject.ambiguous_phrase_count,
        AMBIGUOUS_PHRASE_CAP,
    )
    edge_case_coverage_score = _ratio_capped(
        subject.edge_case_coverage_count,
        REQUIRED_EDGE_CASE_COVERAGE_COUNT,
    )
    dispute_trigger_penalty_score = _ratio_capped(
        subject.dispute_prone_trigger_count,
        DISPUTE_PRONE_TRIGGER_CAP,
    )
    clarity_score = _clarity_score(
        resolution_criteria_score=resolution_criteria_score,
        official_source_mapping_score=official_source_mapping_score,
        ambiguity_penalty_score=ambiguity_penalty_score,
        edge_case_coverage_score=edge_case_coverage_score,
        dispute_trigger_penalty_score=dispute_trigger_penalty_score,
    )
    clarity_gate_status = _clarity_gate_status(clarity_score)

    return ResearchPacketResolutionRuleClarityGateV2Result(
        packet_id=subject.packet_id,
        market_slug=subject.market_slug,
        rule_text_excerpt=subject.rule_text_excerpt,
        resolution_criteria_count=subject.resolution_criteria_count,
        official_source_mapping_count=subject.official_source_mapping_count,
        ambiguous_phrase_count=subject.ambiguous_phrase_count,
        edge_case_coverage_count=subject.edge_case_coverage_count,
        dispute_prone_trigger_count=subject.dispute_prone_trigger_count,
        resolution_criteria_score=resolution_criteria_score,
        official_source_mapping_score=official_source_mapping_score,
        ambiguity_penalty_score=ambiguity_penalty_score,
        edge_case_coverage_score=edge_case_coverage_score,
        dispute_trigger_penalty_score=dispute_trigger_penalty_score,
        clarity_score=clarity_score,
        clarity_gate_status=clarity_gate_status,
        recommended_action=_recommended_action(clarity_gate_status),
        required_followups=_required_followups(subject),
        reason_codes=_reason_codes(subject, clarity_gate_status),
    )


def research_packet_resolution_rule_clarity_gate_v2_payload(
    result: ResearchPacketResolutionRuleClarityGateV2Result,
) -> dict[str, object]:
    if type(result) is not ResearchPacketResolutionRuleClarityGateV2Result:
        raise ValueError("result must be a ResearchPacketResolutionRuleClarityGateV2Result")
    _require_hard_flags(result)
    _reject_unsafe_public_payload("rule clarity gate result", asdict(result))
    return result.payload


def _official_source_mapping_score(
    resolution_criteria_count: Decimal,
    official_source_mapping_count: Decimal,
) -> Decimal:
    if resolution_criteria_count == ZERO:
        return ZERO
    return _ratio_capped(official_source_mapping_count, resolution_criteria_count)


def _clarity_score(
    *,
    resolution_criteria_score: Decimal,
    official_source_mapping_score: Decimal,
    ambiguity_penalty_score: Decimal,
    edge_case_coverage_score: Decimal,
    dispute_trigger_penalty_score: Decimal,
) -> Decimal:
    return _q(
        (resolution_criteria_score * WEIGHT_RESOLUTION_CRITERIA)
        + (official_source_mapping_score * WEIGHT_OFFICIAL_SOURCE_MAPPING)
        + ((ONE - ambiguity_penalty_score) * WEIGHT_AMBIGUITY_ABSENCE)
        + (edge_case_coverage_score * WEIGHT_EDGE_CASE_COVERAGE)
        + ((ONE - dispute_trigger_penalty_score) * WEIGHT_DISPUTE_TRIGGER_ABSENCE),
    )


def _clarity_gate_status(clarity_score: Decimal) -> str:
    if clarity_score >= PASS_CLARITY_THRESHOLD:
        return "pass"
    if clarity_score >= REVIEW_CLARITY_THRESHOLD:
        return "review"
    return "blocked"


def _recommended_action(clarity_gate_status: str) -> str:
    if clarity_gate_status == "pass":
        return "include_in_research_packet"
    if clarity_gate_status == "review":
        return "clarify_before_packet_use"
    if clarity_gate_status == "blocked":
        return "exclude_until_rules_are_clarified"
    raise ValueError("clarity_gate_status must be supported")


def _required_followups(
    subject: ResearchPacketResolutionRuleClarityGateV2Input,
) -> tuple[str, ...]:
    values: list[str] = []
    if subject.resolution_criteria_count == ZERO:
        values.append("define_measurable_resolution_criteria")
    if _official_source_mapping_score(
        subject.resolution_criteria_count,
        subject.official_source_mapping_count,
    ) < ONE:
        values.append("map_each_resolution_criterion_to_official_source")
    if subject.ambiguous_phrase_count > ZERO:
        values.append("remove_or_define_ambiguous_rule_phrasing")
    if _ratio_capped(
        subject.edge_case_coverage_count,
        REQUIRED_EDGE_CASE_COVERAGE_COUNT,
    ) < ONE:
        values.append("add_missing_edge_case_resolution_paths")
    if subject.dispute_prone_trigger_count > ZERO:
        values.append("neutralize_dispute_prone_trigger_language")
    return tuple(values)


def _reason_codes(
    subject: ResearchPacketResolutionRuleClarityGateV2Input,
    clarity_gate_status: str,
) -> tuple[str, ...]:
    values = [f"clarity_status_{clarity_gate_status}"]
    values.append(_resolution_criteria_reason(subject.resolution_criteria_count))
    values.append(
        _official_sources_reason(
            subject.resolution_criteria_count,
            subject.official_source_mapping_count,
        ),
    )
    values.append(_edge_cases_reason(subject.edge_case_coverage_count))
    values.append(_ambiguous_phrasing_reason(subject.ambiguous_phrase_count))
    values.append(_dispute_trigger_reason(subject.dispute_prone_trigger_count))
    return tuple(values)


def _resolution_criteria_reason(resolution_criteria_count: Decimal) -> str:
    score = _ratio_capped(resolution_criteria_count, REQUIRED_RESOLUTION_CRITERIA_COUNT)
    if score == ONE:
        return "resolution_criteria_complete"
    if score == ZERO:
        return "resolution_criteria_missing"
    return "resolution_criteria_partial"


def _official_sources_reason(
    resolution_criteria_count: Decimal,
    official_source_mapping_count: Decimal,
) -> str:
    score = _official_source_mapping_score(
        resolution_criteria_count,
        official_source_mapping_count,
    )
    if score == ONE:
        return "official_sources_complete"
    if score == ZERO:
        return "official_sources_missing"
    return "official_sources_partial"


def _edge_cases_reason(edge_case_coverage_count: Decimal) -> str:
    score = _ratio_capped(edge_case_coverage_count, REQUIRED_EDGE_CASE_COVERAGE_COUNT)
    if score == ONE:
        return "edge_cases_complete"
    if score == ZERO:
        return "edge_cases_missing"
    return "edge_cases_partial"


def _ambiguous_phrasing_reason(ambiguous_phrase_count: Decimal) -> str:
    if ambiguous_phrase_count >= HEAVY_AMBIGUOUS_PHRASE_COUNT:
        return "ambiguous_phrasing_heavy"
    if ambiguous_phrase_count > ZERO:
        return "ambiguous_phrasing_present"
    return "ambiguous_phrasing_clear"


def _dispute_trigger_reason(dispute_prone_trigger_count: Decimal) -> str:
    if dispute_prone_trigger_count >= HEAVY_DISPUTE_PRONE_TRIGGER_COUNT:
        return "dispute_triggers_heavy"
    if dispute_prone_trigger_count > ZERO:
        return "dispute_triggers_present"
    return "dispute_triggers_clear"


def _validate_result(result: ResearchPacketResolutionRuleClarityGateV2Result) -> None:
    expected_subject = ResearchPacketResolutionRuleClarityGateV2Input(
        packet_id=result.packet_id,
        market_slug=result.market_slug,
        rule_text_excerpt=result.rule_text_excerpt,
        resolution_criteria_count=result.resolution_criteria_count,
        official_source_mapping_count=result.official_source_mapping_count,
        ambiguous_phrase_count=result.ambiguous_phrase_count,
        edge_case_coverage_count=result.edge_case_coverage_count,
        dispute_prone_trigger_count=result.dispute_prone_trigger_count,
    )
    expected_resolution_criteria_score = _ratio_capped(
        result.resolution_criteria_count,
        REQUIRED_RESOLUTION_CRITERIA_COUNT,
    )
    expected_official_source_mapping_score = _official_source_mapping_score(
        result.resolution_criteria_count,
        result.official_source_mapping_count,
    )
    expected_ambiguity_penalty_score = _ratio_capped(
        result.ambiguous_phrase_count,
        AMBIGUOUS_PHRASE_CAP,
    )
    expected_edge_case_coverage_score = _ratio_capped(
        result.edge_case_coverage_count,
        REQUIRED_EDGE_CASE_COVERAGE_COUNT,
    )
    expected_dispute_trigger_penalty_score = _ratio_capped(
        result.dispute_prone_trigger_count,
        DISPUTE_PRONE_TRIGGER_CAP,
    )
    expected_clarity_score = _clarity_score(
        resolution_criteria_score=expected_resolution_criteria_score,
        official_source_mapping_score=expected_official_source_mapping_score,
        ambiguity_penalty_score=expected_ambiguity_penalty_score,
        edge_case_coverage_score=expected_edge_case_coverage_score,
        dispute_trigger_penalty_score=expected_dispute_trigger_penalty_score,
    )
    expected_clarity_gate_status = _clarity_gate_status(expected_clarity_score)
    if result.resolution_criteria_score != expected_resolution_criteria_score:
        raise ValueError("resolution_criteria_score must match subject fields")
    if result.official_source_mapping_score != expected_official_source_mapping_score:
        raise ValueError("official_source_mapping_score must match subject fields")
    if result.ambiguity_penalty_score != expected_ambiguity_penalty_score:
        raise ValueError("ambiguity_penalty_score must match subject fields")
    if result.edge_case_coverage_score != expected_edge_case_coverage_score:
        raise ValueError("edge_case_coverage_score must match subject fields")
    if result.dispute_trigger_penalty_score != expected_dispute_trigger_penalty_score:
        raise ValueError("dispute_trigger_penalty_score must match subject fields")
    if result.clarity_score != expected_clarity_score:
        raise ValueError("clarity_score must match subject fields")
    if result.clarity_gate_status != expected_clarity_gate_status:
        raise ValueError("clarity_gate_status must match clarity_score")
    if result.recommended_action != _recommended_action(expected_clarity_gate_status):
        raise ValueError("recommended_action must match clarity_gate_status")
    if result.required_followups != _required_followups(expected_subject):
        raise ValueError("required_followups must match subject fields")
    if result.reason_codes != _reason_codes(expected_subject, expected_clarity_gate_status):
        raise ValueError("reason_codes must match subject fields")
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _validate_source_mapping_count(
    resolution_criteria_count: Decimal,
    official_source_mapping_count: Decimal,
) -> None:
    if resolution_criteria_count > ZERO and official_source_mapping_count > resolution_criteria_count:
        raise ValueError("official_source_mapping_count cannot exceed resolution_criteria_count")


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = numerator / denominator
    if ratio >= ONE:
        return ONE
    if ratio <= ZERO:
        return ZERO
    return _q(ratio)


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


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
    if type(value) is Decimal:
        return str(_q(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        _reject_unsafe_public_payload("rule clarity gate payload", value)
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
        raise ValueError("rule clarity gate payload fields must match public schema")


def _result_values_from_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "packet_id": _string_from_payload("packet_id", payload["packet_id"]),
        "market_slug": _string_from_payload("market_slug", payload["market_slug"]),
        "rule_text_excerpt": _string_from_payload(
            "rule_text_excerpt",
            payload["rule_text_excerpt"],
        ),
        "resolution_criteria_count": _decimal_from_payload(
            "resolution_criteria_count",
            payload["resolution_criteria_count"],
        ),
        "official_source_mapping_count": _decimal_from_payload(
            "official_source_mapping_count",
            payload["official_source_mapping_count"],
        ),
        "ambiguous_phrase_count": _decimal_from_payload(
            "ambiguous_phrase_count",
            payload["ambiguous_phrase_count"],
        ),
        "edge_case_coverage_count": _decimal_from_payload(
            "edge_case_coverage_count",
            payload["edge_case_coverage_count"],
        ),
        "dispute_prone_trigger_count": _decimal_from_payload(
            "dispute_prone_trigger_count",
            payload["dispute_prone_trigger_count"],
        ),
        "resolution_criteria_score": _decimal_from_payload(
            "resolution_criteria_score",
            payload["resolution_criteria_score"],
        ),
        "official_source_mapping_score": _decimal_from_payload(
            "official_source_mapping_score",
            payload["official_source_mapping_score"],
        ),
        "ambiguity_penalty_score": _decimal_from_payload(
            "ambiguity_penalty_score",
            payload["ambiguity_penalty_score"],
        ),
        "edge_case_coverage_score": _decimal_from_payload(
            "edge_case_coverage_score",
            payload["edge_case_coverage_score"],
        ),
        "dispute_trigger_penalty_score": _decimal_from_payload(
            "dispute_trigger_penalty_score",
            payload["dispute_trigger_penalty_score"],
        ),
        "clarity_score": _decimal_from_payload("clarity_score", payload["clarity_score"]),
        "clarity_gate_status": _string_from_payload(
            "clarity_gate_status",
            payload["clarity_gate_status"],
        ),
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
    result: ResearchPacketResolutionRuleClarityGateV2Result,
) -> str:
    return _derived_validation_digest_values(
        packet_id=result.packet_id,
        market_slug=result.market_slug,
        rule_text_excerpt=result.rule_text_excerpt,
        resolution_criteria_count=result.resolution_criteria_count,
        official_source_mapping_count=result.official_source_mapping_count,
        ambiguous_phrase_count=result.ambiguous_phrase_count,
        edge_case_coverage_count=result.edge_case_coverage_count,
        dispute_prone_trigger_count=result.dispute_prone_trigger_count,
        resolution_criteria_score=result.resolution_criteria_score,
        official_source_mapping_score=result.official_source_mapping_score,
        ambiguity_penalty_score=result.ambiguity_penalty_score,
        edge_case_coverage_score=result.edge_case_coverage_score,
        dispute_trigger_penalty_score=result.dispute_trigger_penalty_score,
        clarity_score=result.clarity_score,
        clarity_gate_status=result.clarity_gate_status,
        recommended_action=result.recommended_action,
        required_followups=result.required_followups,
        reason_codes=result.reason_codes,
        paper_only=result.paper_only,
        report_only=result.report_only,
        readonly=result.readonly,
    )


def _derived_validation_digest_values(
    *,
    packet_id: str,
    market_slug: str,
    rule_text_excerpt: str,
    resolution_criteria_count: Decimal,
    official_source_mapping_count: Decimal,
    ambiguous_phrase_count: Decimal,
    edge_case_coverage_count: Decimal,
    dispute_prone_trigger_count: Decimal,
    resolution_criteria_score: Decimal,
    official_source_mapping_score: Decimal,
    ambiguity_penalty_score: Decimal,
    edge_case_coverage_score: Decimal,
    dispute_trigger_penalty_score: Decimal,
    clarity_score: Decimal,
    clarity_gate_status: str,
    recommended_action: str,
    required_followups: tuple[str, ...],
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    digest_material = "|".join(
        (
            f"packet_id={packet_id}",
            f"market_slug={market_slug}",
            f"rule_text_excerpt={rule_text_excerpt}",
            f"resolution_criteria_count={resolution_criteria_count}",
            f"official_source_mapping_count={official_source_mapping_count}",
            f"ambiguous_phrase_count={ambiguous_phrase_count}",
            f"edge_case_coverage_count={edge_case_coverage_count}",
            f"dispute_prone_trigger_count={dispute_prone_trigger_count}",
            f"resolution_criteria_score={resolution_criteria_score}",
            f"official_source_mapping_score={official_source_mapping_score}",
            f"ambiguity_penalty_score={ambiguity_penalty_score}",
            f"edge_case_coverage_score={edge_case_coverage_score}",
            f"dispute_trigger_penalty_score={dispute_trigger_penalty_score}",
            f"clarity_score={clarity_score}",
            f"clarity_gate_status={clarity_gate_status}",
            f"recommended_action={recommended_action}",
            f"required_followups={_digest_tuple(required_followups)}",
            f"reason_codes={_digest_tuple(reason_codes)}",
            f"paper_only={paper_only}",
            f"report_only={report_only}",
            f"readonly={readonly}",
        ),
    )
    return hashlib.sha256(digest_material.encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _q(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT)


__all__ = (
    "CLARITY_GATE_STATUSES",
    "RECOMMENDED_ACTIONS",
    "REQUIRED_FOLLOWUPS",
    "REASON_CODES",
    "ResearchPacketResolutionRuleClarityGateV2Input",
    "ResearchPacketResolutionRuleClarityGateV2Result",
    "build_research_packet_resolution_rule_clarity_gate_v2",
    "research_packet_resolution_rule_clarity_gate_v2_payload",
)
