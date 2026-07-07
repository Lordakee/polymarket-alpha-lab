"""Pure Phase 1 event catalyst-chain completeness scorer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "research-packet-event-catalyst-chain-score-v2"
RATIO_QUANTUM = Decimal("0.000001")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
MINIMUM_COMPONENT_SCORE = Decimal("0.700000")
PASS_SCORE_THRESHOLD = Decimal("0.850000")
WATCH_SCORE_THRESHOLD = Decimal("0.600000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

COMPONENTS = (
    "initial_catalyst",
    "confirmation_source",
    "market_probability_move",
    "follow_up_evidence",
    "contradiction_resolution",
    "resolution_source_link",
)
BLOCKING_COMPONENTS = (
    "initial_catalyst",
    "confirmation_source",
    "contradiction_resolution",
    "resolution_source_link",
)
COMPONENT_WEIGHTS = (
    ("initial_catalyst", Decimal("0.200000")),
    ("confirmation_source", Decimal("0.200000")),
    ("market_probability_move", Decimal("0.150000")),
    ("follow_up_evidence", Decimal("0.150000")),
    ("contradiction_resolution", Decimal("0.150000")),
    ("resolution_source_link", Decimal("0.150000")),
)
CATALYST_CHAIN_STATUSES = ("complete", "watch", "blocked")
COMPONENT_GAP_REASONS = {
    "initial_catalyst": "initial_catalyst_missing",
    "confirmation_source": "confirmation_source_missing",
    "market_probability_move": "market_probability_move_missing",
    "follow_up_evidence": "follow_up_evidence_missing",
    "contradiction_resolution": "contradiction_unresolved",
    "resolution_source_link": "resolution_source_link_missing",
}
REASON_CODES = (
    "event_catalyst_chain_complete",
    "initial_catalyst_missing",
    "confirmation_source_missing",
    "market_probability_move_missing",
    "follow_up_evidence_missing",
    "contradiction_unresolved",
    "resolution_source_link_missing",
    "event_catalyst_chain_watch_score",
    "event_catalyst_chain_blocked_score",
)


@dataclass(frozen=True)
class ResearchPacketEventCatalystChainScoreV2Input:
    packet_id: str
    market_slug: str
    initial_catalyst_score: Decimal
    confirmation_source_score: Decimal
    market_probability_move_score: Decimal
    follow_up_evidence_score: Decimal
    contradiction_resolution_score: Decimal
    resolution_source_link_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "value",
            self,
            ResearchPacketEventCatalystChainScoreV2Input,
        )
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in _component_score_fields():
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        reject_unsafe_surface_fields("event catalyst chain score input", self)
        require_paper_only_flags("event catalyst chain score input", self)


@dataclass(frozen=True)
class ResearchPacketEventCatalystChainScoreV2Result:
    config_version: str
    packet_id: str
    market_slug: str
    initial_catalyst_score: Decimal
    confirmation_source_score: Decimal
    market_probability_move_score: Decimal
    follow_up_evidence_score: Decimal
    contradiction_resolution_score: Decimal
    resolution_source_link_score: Decimal
    catalyst_chain_score: Decimal
    catalyst_chain_status: str
    component_gaps: tuple[str, ...]
    reason_codes: tuple[str, ...]
    chain_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "result",
            self,
            ResearchPacketEventCatalystChainScoreV2Result,
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in _component_score_fields():
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "catalyst_chain_score",
            _normalize_ratio("catalyst_chain_score", self.catalyst_chain_score),
        )
        _require_member(
            "catalyst_chain_status",
            self.catalyst_chain_status,
            CATALYST_CHAIN_STATUSES,
        )
        object.__setattr__(
            self,
            "component_gaps",
            _normalize_component_gaps(self.component_gaps),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "chain_digest", _require_digest(self.chain_digest))
        _validate_result(self)
        reject_unsafe_surface_fields("event catalyst chain score result", self)
        require_paper_only_flags("event catalyst chain score result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_event_catalyst_chain_score_v2_payload(self)


def score_research_packet_event_catalyst_chain_score_v2(
    value: ResearchPacketEventCatalystChainScoreV2Input,
) -> ResearchPacketEventCatalystChainScoreV2Result:
    if type(value) is not ResearchPacketEventCatalystChainScoreV2Input:
        raise ValueError("value must be a ResearchPacketEventCatalystChainScoreV2Input")
    reject_unsafe_surface_fields("event catalyst chain score input", value)
    require_paper_only_flags("event catalyst chain score input", value)

    catalyst_chain_score = _catalyst_chain_score(value)
    component_gaps = _component_gaps(value)
    catalyst_chain_status = _catalyst_chain_status(
        component_gaps=component_gaps,
        catalyst_chain_score=catalyst_chain_score,
    )
    reason_codes = _reason_codes(
        component_gaps=component_gaps,
        catalyst_chain_score=catalyst_chain_score,
    )
    chain_digest = _digest_payload(
        _result_payload_fields(
            config_version=DEFAULT_CONFIG_VERSION,
            packet_id=value.packet_id,
            market_slug=value.market_slug,
            initial_catalyst_score=value.initial_catalyst_score,
            confirmation_source_score=value.confirmation_source_score,
            market_probability_move_score=value.market_probability_move_score,
            follow_up_evidence_score=value.follow_up_evidence_score,
            contradiction_resolution_score=value.contradiction_resolution_score,
            resolution_source_link_score=value.resolution_source_link_score,
            catalyst_chain_score=catalyst_chain_score,
            catalyst_chain_status=catalyst_chain_status,
            component_gaps=component_gaps,
            reason_codes=reason_codes,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )

    return ResearchPacketEventCatalystChainScoreV2Result(
        config_version=DEFAULT_CONFIG_VERSION,
        packet_id=value.packet_id,
        market_slug=value.market_slug,
        initial_catalyst_score=value.initial_catalyst_score,
        confirmation_source_score=value.confirmation_source_score,
        market_probability_move_score=value.market_probability_move_score,
        follow_up_evidence_score=value.follow_up_evidence_score,
        contradiction_resolution_score=value.contradiction_resolution_score,
        resolution_source_link_score=value.resolution_source_link_score,
        catalyst_chain_score=catalyst_chain_score,
        catalyst_chain_status=catalyst_chain_status,
        component_gaps=component_gaps,
        reason_codes=reason_codes,
        chain_digest=chain_digest,
    )


def research_packet_event_catalyst_chain_score_v2_payload(
    result: ResearchPacketEventCatalystChainScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not ResearchPacketEventCatalystChainScoreV2Result:
        raise ValueError("result must be a ResearchPacketEventCatalystChainScoreV2Result")
    reject_unsafe_surface_fields("event catalyst chain score result", result)
    require_paper_only_flags("event catalyst chain score result", result)
    payload = _result_payload(result, include_digest=True)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _catalyst_chain_score(
    value: ResearchPacketEventCatalystChainScoreV2Input
    | ResearchPacketEventCatalystChainScoreV2Result,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ZERO_RATIO
        for component_name, weight in COMPONENT_WEIGHTS:
            score += getattr(value, f"{component_name}_score") * weight
        return _clamp_ratio(score)


def _component_gaps(
    value: ResearchPacketEventCatalystChainScoreV2Input
    | ResearchPacketEventCatalystChainScoreV2Result,
) -> tuple[str, ...]:
    gaps: list[str] = []
    for component_name in COMPONENTS:
        if getattr(value, f"{component_name}_score") < MINIMUM_COMPONENT_SCORE:
            gaps.append(component_name)
    return _normalize_component_gaps(tuple(gaps))


def _catalyst_chain_status(
    *,
    component_gaps: tuple[str, ...],
    catalyst_chain_score: Decimal,
) -> str:
    if (
        any(component_name in BLOCKING_COMPONENTS for component_name in component_gaps)
        or catalyst_chain_score < WATCH_SCORE_THRESHOLD
    ):
        return "blocked"
    if component_gaps or catalyst_chain_score < PASS_SCORE_THRESHOLD:
        return "watch"
    return "complete"


def _reason_codes(
    *,
    component_gaps: tuple[str, ...],
    catalyst_chain_score: Decimal,
) -> tuple[str, ...]:
    if not component_gaps and catalyst_chain_score >= PASS_SCORE_THRESHOLD:
        return ("event_catalyst_chain_complete",)

    reason_codes = [COMPONENT_GAP_REASONS[component_name] for component_name in component_gaps]
    if catalyst_chain_score < WATCH_SCORE_THRESHOLD:
        reason_codes.append("event_catalyst_chain_blocked_score")
    elif catalyst_chain_score < PASS_SCORE_THRESHOLD:
        reason_codes.append("event_catalyst_chain_watch_score")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_result(result: ResearchPacketEventCatalystChainScoreV2Result) -> None:
    expected_score = _catalyst_chain_score(result)
    expected_gaps = _component_gaps(result)
    expected_status = _catalyst_chain_status(
        component_gaps=expected_gaps,
        catalyst_chain_score=expected_score,
    )
    expected_reasons = _reason_codes(
        component_gaps=expected_gaps,
        catalyst_chain_score=expected_score,
    )
    if result.catalyst_chain_score != expected_score:
        raise ValueError("catalyst_chain_score must match component scores")
    if result.component_gaps != expected_gaps:
        raise ValueError("component_gaps must match component scores")
    if result.catalyst_chain_status != expected_status:
        raise ValueError("catalyst_chain_status must match component scores")
    if result.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match component scores")
    if result.chain_digest != _chain_digest(result):
        raise ValueError("chain_digest must match result fields")


def _chain_digest(result: ResearchPacketEventCatalystChainScoreV2Result) -> str:
    return _digest_payload(_result_payload(result, include_digest=False))


def _digest_payload(payload: dict[str, Any]) -> str:
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    canonical_payload = dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _result_payload(
    result: ResearchPacketEventCatalystChainScoreV2Result,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _result_payload_fields(
        config_version=result.config_version,
        packet_id=result.packet_id,
        market_slug=result.market_slug,
        initial_catalyst_score=result.initial_catalyst_score,
        confirmation_source_score=result.confirmation_source_score,
        market_probability_move_score=result.market_probability_move_score,
        follow_up_evidence_score=result.follow_up_evidence_score,
        contradiction_resolution_score=result.contradiction_resolution_score,
        resolution_source_link_score=result.resolution_source_link_score,
        catalyst_chain_score=result.catalyst_chain_score,
        catalyst_chain_status=result.catalyst_chain_status,
        component_gaps=result.component_gaps,
        reason_codes=result.reason_codes,
        paper_only=result.paper_only,
        report_only=result.report_only,
        readonly=result.readonly,
    )
    if include_digest:
        payload["chain_digest"] = result.chain_digest
    return payload


def _result_payload_fields(
    *,
    config_version: str,
    packet_id: str,
    market_slug: str,
    initial_catalyst_score: Decimal,
    confirmation_source_score: Decimal,
    market_probability_move_score: Decimal,
    follow_up_evidence_score: Decimal,
    contradiction_resolution_score: Decimal,
    resolution_source_link_score: Decimal,
    catalyst_chain_score: Decimal,
    catalyst_chain_status: str,
    component_gaps: tuple[str, ...],
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    return {
        "config_version": config_version,
        "packet_id": packet_id,
        "market_slug": market_slug,
        "initial_catalyst_score": initial_catalyst_score,
        "confirmation_source_score": confirmation_source_score,
        "market_probability_move_score": market_probability_move_score,
        "follow_up_evidence_score": follow_up_evidence_score,
        "contradiction_resolution_score": contradiction_resolution_score,
        "resolution_source_link_score": resolution_source_link_score,
        "catalyst_chain_score": catalyst_chain_score,
        "catalyst_chain_status": catalyst_chain_status,
        "component_gaps": component_gaps,
        "reason_codes": reason_codes,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _component_score_fields() -> tuple[str, ...]:
    return tuple(f"{component_name}_score" for component_name in COMPONENTS)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_component_gaps(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("component_gaps must be a tuple")
    seen_values: set[str] = set()
    for value in values:
        _require_canonical_string("component_gaps", value)
        if value not in COMPONENTS:
            raise ValueError("component_gaps contains unsupported value")
        if value in seen_values:
            raise ValueError("component_gaps contains duplicate value")
        seen_values.add(value)
    return tuple(component_name for component_name in COMPONENTS if component_name in seen_values)


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen_values: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen_values:
            raise ValueError("reason_codes contains duplicate value")
        seen_values.add(value)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen_values)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("chain_digest must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("chain_digest must be a lowercase sha256 hex digest")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


_weight_total = sum(weight for _, weight in COMPONENT_WEIGHTS).quantize(RATIO_QUANTUM)
if _weight_total != ONE_RATIO:
    raise ValueError("component weights must sum to 1.000000")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "CATALYST_CHAIN_STATUSES",
    "COMPONENTS",
    "REASON_CODES",
    "ResearchPacketEventCatalystChainScoreV2Input",
    "ResearchPacketEventCatalystChainScoreV2Result",
    "research_packet_event_catalyst_chain_score_v2_payload",
    "score_research_packet_event_catalyst_chain_score_v2",
)
