"""Public event-decision review packet summary reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_RESEARCH_EVENT_DECISION_REVIEW_PACKET_SUMMARY_CONFIG_VERSION = (
    "research-event-decision-review-packet-summary-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_event_decision_review_packet_summary_"
PASS_REASON = f"{REASON_PREFIX}pass"
WATCH_REASON = f"{REASON_PREFIX}watch"
BLOCK_REASON = f"{REASON_PREFIX}block"
UNRESOLVED_BLOCKERS_REASON = f"{REASON_PREFIX}unresolved_blockers"
CAUTION_ITEMS_PRESENT_REASON = f"{REASON_PREFIX}caution_items_present"

COMPONENTS = (
    ("research_quality_score", "research_quality"),
    ("evidence_balance_score", "evidence_balance"),
    ("counterpoint_coverage_score", "counterpoint_coverage"),
    ("resolution_rule_clarity_score", "resolution_rule_clarity"),
    ("human_review_readiness_score", "human_review_readiness"),
)

COMPONENT_REASON_CODES = tuple(
    f"{REASON_PREFIX}{component_name}_{status_name}"
    for _, component_name in COMPONENTS
    for status_name in (STATUS_BLOCK, STATUS_WATCH)
)
REASON_CODE_SEQUENCE = (
    UNRESOLVED_BLOCKERS_REASON,
    *tuple(
        f"{REASON_PREFIX}{component_name}_{STATUS_BLOCK}"
        for _, component_name in COMPONENTS
    ),
    *tuple(
        f"{REASON_PREFIX}{component_name}_{STATUS_WATCH}"
        for _, component_name in COMPONENTS
    ),
    CAUTION_ITEMS_PRESENT_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "pass_human_review_packet_summary",
    STATUS_WATCH: "watch_human_review_packet_summary",
    STATUS_BLOCK: "block_human_review_packet_summary",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("5.000000")
BLOCKER_SCORE_PENALTY = Decimal("0.048000")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _word(*codepoints: int) -> str:
    return "".join(chr(codepoint) for codepoint in codepoints)


_RESTRICTED_PUBLIC_TEXT_FRAGMENTS = (
    _word(99, 97, 110, 100, 105, 100, 97, 116, 101),
    _word(109, 97, 114, 107, 101, 116),
    _word(115, 108, 117, 103),
    _word(113, 117, 101, 115, 116, 105, 111, 110),
    _word(115, 111, 117, 114, 99, 101),
    _word(114, 97, 119),
    _word(117, 114, 108),
    _word(104, 116, 116, 112),
    _word(58, 47, 47),
    _word(100, 115, 110),
    _word(116, 97, 98, 108, 101),
    _word(116, 111, 107, 101, 110),
    _word(97, 117, 116, 104),
    _word(112, 114, 105, 118, 97, 116, 101),
    _word(119, 97, 108, 108, 101, 116),
    _word(111, 114, 100, 101, 114),
    _word(116, 114, 97, 100, 101),
    _word(112, 111, 115, 105, 116, 105, 111, 110),
    _word(98, 117, 121),
    _word(115, 101, 108, 108),
    _word(114, 101, 99, 111, 109, 109, 101, 110, 100),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchEventDecisionReviewPacketSummaryConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_DECISION_REVIEW_PACKET_SUMMARY_CONFIG_VERSION
    )
    pass_score_threshold: Decimal = Decimal("0.750000")
    watch_score_threshold: Decimal = Decimal("0.500000")
    component_floor: Decimal = Decimal("0.700000")
    block_component_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventDecisionReviewPacketSummaryConfig,
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_score_threshold",
            "watch_score_threshold",
            "component_floor",
            "block_component_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold > self.pass_score_threshold:
            raise ValueError("watch_score_threshold must not exceed pass_score_threshold")
        if self.block_component_floor > self.component_floor:
            raise ValueError("block_component_floor must not exceed component_floor")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventDecisionReviewPacketSummaryInput(_FinalPublicDataclass):
    review_topic_key: str
    decision_material_label: str
    prepared_at: datetime
    research_quality_score: Decimal
    evidence_balance_score: Decimal
    counterpoint_coverage_score: Decimal
    resolution_rule_clarity_score: Decimal
    human_review_readiness_score: Decimal
    unresolved_blocker_count: Decimal = Decimal("0.000000")
    caution_item_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchEventDecisionReviewPacketSummaryInput,
        )
        for field_name in ("review_topic_key", "decision_material_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "prepared_at",
            _as_utc("prepared_at", self.prepared_at),
        )
        for field_name, _ in COMPONENTS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("unresolved_blocker_count", "caution_item_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventDecisionReviewPacketSummaryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    pass_score_threshold: Decimal
    watch_score_threshold: Decimal
    component_floor: Decimal
    block_component_floor: Decimal
    review_topic_key: str
    decision_material_label: str
    prepared_at: datetime
    research_quality_score: Decimal
    evidence_balance_score: Decimal
    counterpoint_coverage_score: Decimal
    resolution_rule_clarity_score: Decimal
    human_review_readiness_score: Decimal
    public_status: str
    review_score: Decimal
    unresolved_blocker_count: Decimal
    caution_item_count: Decimal
    next_review_step: str
    reason_codes: tuple[str, ...]
    summary_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchEventDecisionReviewPacketSummaryReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "prepared_at",
            _as_utc("prepared_at", self.prepared_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_score_threshold",
            "watch_score_threshold",
            "component_floor",
            "block_component_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold > self.pass_score_threshold:
            raise ValueError("watch_score_threshold must not exceed pass_score_threshold")
        if self.block_component_floor > self.component_floor:
            raise ValueError("block_component_floor must not exceed component_floor")
        for field_name in ("review_topic_key", "decision_material_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name, _ in COMPONENTS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "review_score",
            _require_ratio_decimal("review_score", self.review_score),
        )
        for field_name in ("unresolved_blocker_count", "caution_item_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_string("next_review_step", self.next_review_step)
        object.__setattr__(
            self,
            "summary_digest",
            _require_digest(self.summary_digest),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_restricted_public_payload(self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_decision_review_packet_summary_payload(self)


def build_research_event_decision_review_packet_summary(
    value: ResearchEventDecisionReviewPacketSummaryInput,
    *,
    config: ResearchEventDecisionReviewPacketSummaryConfig,
    generated_at: datetime,
) -> ResearchEventDecisionReviewPacketSummaryReport:
    if type(value) is not ResearchEventDecisionReviewPacketSummaryInput:
        raise ValueError(
            "value must be a ResearchEventDecisionReviewPacketSummaryInput",
        )
    if type(config) is not ResearchEventDecisionReviewPacketSummaryConfig:
        raise ValueError(
            "config must be a ResearchEventDecisionReviewPacketSummaryConfig",
        )
    _require_hard_flags("input", value)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    review_score = _review_score(value)
    public_status = _public_status(
        value,
        config=config,
        review_score=review_score,
    )
    reason_codes = _reason_codes(
        value,
        config=config,
        public_status=public_status,
    )
    next_review_step = NEXT_REVIEW_STEPS[public_status]
    digest = _digest_payload(
        _report_payload_fields(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            pass_score_threshold=config.pass_score_threshold,
            watch_score_threshold=config.watch_score_threshold,
            component_floor=config.component_floor,
            block_component_floor=config.block_component_floor,
            review_topic_key=value.review_topic_key,
            decision_material_label=value.decision_material_label,
            prepared_at=value.prepared_at,
            research_quality_score=value.research_quality_score,
            evidence_balance_score=value.evidence_balance_score,
            counterpoint_coverage_score=value.counterpoint_coverage_score,
            resolution_rule_clarity_score=value.resolution_rule_clarity_score,
            human_review_readiness_score=value.human_review_readiness_score,
            public_status=public_status,
            review_score=review_score,
            unresolved_blocker_count=value.unresolved_blocker_count,
            caution_item_count=value.caution_item_count,
            next_review_step=next_review_step,
            reason_codes=reason_codes,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )
    return ResearchEventDecisionReviewPacketSummaryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        pass_score_threshold=config.pass_score_threshold,
        watch_score_threshold=config.watch_score_threshold,
        component_floor=config.component_floor,
        block_component_floor=config.block_component_floor,
        review_topic_key=value.review_topic_key,
        decision_material_label=value.decision_material_label,
        prepared_at=value.prepared_at,
        research_quality_score=value.research_quality_score,
        evidence_balance_score=value.evidence_balance_score,
        counterpoint_coverage_score=value.counterpoint_coverage_score,
        resolution_rule_clarity_score=value.resolution_rule_clarity_score,
        human_review_readiness_score=value.human_review_readiness_score,
        public_status=public_status,
        review_score=review_score,
        unresolved_blocker_count=value.unresolved_blocker_count,
        caution_item_count=value.caution_item_count,
        next_review_step=next_review_step,
        reason_codes=reason_codes,
        summary_digest=digest,
    )


def research_event_decision_review_packet_summary_payload(
    report: ResearchEventDecisionReviewPacketSummaryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventDecisionReviewPacketSummaryReport:
        raise ValueError(
            "report must be a ResearchEventDecisionReviewPacketSummaryReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(_report_payload(report, include_digest=True))
    if type(payload) is not dict:
        raise ValueError("summary payload must be a JSON object")
    _reject_restricted_public_payload(payload)
    return payload


def research_event_decision_review_packet_summary_digest(
    report: ResearchEventDecisionReviewPacketSummaryReport,
) -> str:
    if type(report) is not ResearchEventDecisionReviewPacketSummaryReport:
        raise ValueError(
            "report must be a ResearchEventDecisionReviewPacketSummaryReport",
        )
    _require_hard_flags("report", report)
    return _digest_report(report)


def _validate_report(report: ResearchEventDecisionReviewPacketSummaryReport) -> None:
    if report.next_review_step != NEXT_REVIEW_STEPS[report.public_status]:
        raise ValueError("next_review_step must match public_status")
    if report.review_score != _review_score(_input_from_report(report)):
        raise ValueError("review_score must match public summary fields")
    expected_status = _public_status(
        _input_from_report(report),
        config=_config_from_report(report),
        review_score=report.review_score,
    )
    if report.public_status != expected_status:
        raise ValueError("public_status must match public summary fields")
    expected_reason_codes = _reason_codes(
        _input_from_report(report),
        config=_config_from_report(report),
        public_status=report.public_status,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match public summary fields")
    if report.summary_digest != _digest_report(report):
        raise ValueError("summary_digest must match report payload")


def _review_score(value: ResearchEventDecisionReviewPacketSummaryInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        component_total = sum(getattr(value, field_name) for field_name, _ in COMPONENTS)
        raw_score = (component_total / COMPONENT_COUNT) - (
            value.unresolved_blocker_count * BLOCKER_SCORE_PENALTY
        )
    return _clamp_ratio(raw_score)


def _input_from_report(
    report: ResearchEventDecisionReviewPacketSummaryReport,
) -> ResearchEventDecisionReviewPacketSummaryInput:
    return ResearchEventDecisionReviewPacketSummaryInput(
        review_topic_key=report.review_topic_key,
        decision_material_label=report.decision_material_label,
        prepared_at=report.prepared_at,
        research_quality_score=report.research_quality_score,
        evidence_balance_score=report.evidence_balance_score,
        counterpoint_coverage_score=report.counterpoint_coverage_score,
        resolution_rule_clarity_score=report.resolution_rule_clarity_score,
        human_review_readiness_score=report.human_review_readiness_score,
        unresolved_blocker_count=report.unresolved_blocker_count,
        caution_item_count=report.caution_item_count,
    )


def _config_from_report(
    report: ResearchEventDecisionReviewPacketSummaryReport,
) -> ResearchEventDecisionReviewPacketSummaryConfig:
    return ResearchEventDecisionReviewPacketSummaryConfig(
        config_version=report.config_version,
        pass_score_threshold=report.pass_score_threshold,
        watch_score_threshold=report.watch_score_threshold,
        component_floor=report.component_floor,
        block_component_floor=report.block_component_floor,
    )


def _public_status(
    value: ResearchEventDecisionReviewPacketSummaryInput,
    *,
    config: ResearchEventDecisionReviewPacketSummaryConfig,
    review_score: Decimal,
) -> str:
    if value.unresolved_blocker_count > ZERO:
        return STATUS_BLOCK
    if any(getattr(value, field_name) < config.block_component_floor for field_name, _ in COMPONENTS):
        return STATUS_BLOCK
    if review_score < config.watch_score_threshold:
        return STATUS_BLOCK
    if value.caution_item_count > ZERO:
        return STATUS_WATCH
    if review_score < config.pass_score_threshold:
        return STATUS_WATCH
    if any(getattr(value, field_name) < config.component_floor for field_name, _ in COMPONENTS):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_codes(
    value: ResearchEventDecisionReviewPacketSummaryInput,
    *,
    config: ResearchEventDecisionReviewPacketSummaryConfig,
    public_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.unresolved_blocker_count > ZERO:
        codes.append(UNRESOLVED_BLOCKERS_REASON)
    for field_name, component_name in COMPONENTS:
        if getattr(value, field_name) < config.block_component_floor:
            codes.append(f"{REASON_PREFIX}{component_name}_{STATUS_BLOCK}")
    if value.caution_item_count > ZERO:
        codes.append(CAUTION_ITEMS_PRESENT_REASON)
    for field_name, component_name in COMPONENTS:
        score = getattr(value, field_name)
        if config.block_component_floor <= score < config.component_floor:
            codes.append(f"{REASON_PREFIX}{component_name}_{STATUS_WATCH}")
    if public_status == STATUS_BLOCK:
        codes.append(BLOCK_REASON)
    elif public_status == STATUS_WATCH:
        codes.append(WATCH_REASON)
    else:
        codes.append(PASS_REASON)
    return _normalize_reason_codes(tuple(codes))


def _report_reason_codes(
    report: ResearchEventDecisionReviewPacketSummaryReport,
) -> tuple[str, ...]:
    codes = tuple(
        code
        for code in report.reason_codes
        if code != PASS_REASON
        and code != WATCH_REASON
        and code != BLOCK_REASON
    )
    return _normalize_reason_codes((*codes, _status_reason(report.public_status)))


def _status_reason(public_status: str) -> str:
    if public_status == STATUS_PASS:
        return PASS_REASON
    if public_status == STATUS_WATCH:
        return WATCH_REASON
    return BLOCK_REASON


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _digest_report(report: ResearchEventDecisionReviewPacketSummaryReport) -> str:
    return _digest_payload(_report_payload(report, include_digest=False))


def _digest_payload(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    canonical_payload = dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _report_payload(
    report: ResearchEventDecisionReviewPacketSummaryReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _report_payload_fields(
        generated_at=report.generated_at,
        config_version=report.config_version,
        pass_score_threshold=report.pass_score_threshold,
        watch_score_threshold=report.watch_score_threshold,
        component_floor=report.component_floor,
        block_component_floor=report.block_component_floor,
        review_topic_key=report.review_topic_key,
        decision_material_label=report.decision_material_label,
        prepared_at=report.prepared_at,
        research_quality_score=report.research_quality_score,
        evidence_balance_score=report.evidence_balance_score,
        counterpoint_coverage_score=report.counterpoint_coverage_score,
        resolution_rule_clarity_score=report.resolution_rule_clarity_score,
        human_review_readiness_score=report.human_review_readiness_score,
        public_status=report.public_status,
        review_score=report.review_score,
        unresolved_blocker_count=report.unresolved_blocker_count,
        caution_item_count=report.caution_item_count,
        next_review_step=report.next_review_step,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    if include_digest:
        payload["summary_digest"] = report.summary_digest
    return payload


def _report_payload_fields(
    *,
    generated_at: datetime,
    config_version: str,
    pass_score_threshold: Decimal,
    watch_score_threshold: Decimal,
    component_floor: Decimal,
    block_component_floor: Decimal,
    review_topic_key: str,
    decision_material_label: str,
    prepared_at: datetime,
    research_quality_score: Decimal,
    evidence_balance_score: Decimal,
    counterpoint_coverage_score: Decimal,
    resolution_rule_clarity_score: Decimal,
    human_review_readiness_score: Decimal,
    public_status: str,
    review_score: Decimal,
    unresolved_blocker_count: Decimal,
    caution_item_count: Decimal,
    next_review_step: str,
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "pass_score_threshold": pass_score_threshold,
        "watch_score_threshold": watch_score_threshold,
        "component_floor": component_floor,
        "block_component_floor": block_component_floor,
        "review_topic_key": review_topic_key,
        "decision_material_label": decision_material_label,
        "prepared_at": prepared_at,
        "research_quality_score": research_quality_score,
        "evidence_balance_score": evidence_balance_score,
        "counterpoint_coverage_score": counterpoint_coverage_score,
        "resolution_rule_clarity_score": resolution_rule_clarity_score,
        "human_review_readiness_score": human_review_readiness_score,
        "public_status": public_status,
        "review_score": review_score,
        "unresolved_blocker_count": unresolved_blocker_count,
        "caution_item_count": caution_item_count,
        "next_review_step": next_review_step,
        "reason_codes": reason_codes,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen_values: set[str] = set()
    for value in values:
        _require_public_string("reason_codes", value)
        if value not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen_values:
            raise ValueError("reason_codes contains duplicate value")
        seen_values.add(value)
    return tuple(code for code in REASON_CODE_SEQUENCE if code in seen_values)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return value.quantize(QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(QUANT)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value % COUNT_QUANT != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of {PUBLIC_STATUSES!r}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _RESTRICTED_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains restricted public text")


def _require_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("summary_digest must be exactly str")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("summary_digest must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready({field.name: getattr(value, field.name) for field in fields(value)})
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_restricted_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_public_string("payload key", key)
            _reject_restricted_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_restricted_public_payload(item)
        return
    if type(value) is str:
        _require_public_string("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains unsupported public value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_DECISION_REVIEW_PACKET_SUMMARY_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchEventDecisionReviewPacketSummaryConfig",
    "ResearchEventDecisionReviewPacketSummaryInput",
    "ResearchEventDecisionReviewPacketSummaryReport",
    "build_research_event_decision_review_packet_summary",
    "research_event_decision_review_packet_summary_digest",
    "research_event_decision_review_packet_summary_payload",
)
