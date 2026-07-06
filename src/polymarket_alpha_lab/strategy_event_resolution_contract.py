"""Typed contract checks for strategy event resolution ambiguity.

Polymarket markets are probability events, so resolution ambiguity is a core
strategy risk rather than a cosmetic metadata issue.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_STRATEGY_EVENT_RESOLUTION_CONTRACT_CONFIG_VERSION = (
    "strategy-event-resolution-contract-v0"
)
PASS_REASON_CODE = "polymarket_probability_event_resolution_contract_passed"
RESOLUTION_CONTRACT_STATUSES = ("pass", "watch", "blocked")
SOURCE_TIERS = (
    "polymarket_rules",
    "official_primary",
    "official_secondary",
    "proxy",
)
REASON_CODES = (
    "missing_question_text",
    "ambiguous_question_text",
    "missing_resolution_rules_summary",
    "ambiguous_resolution_rules_summary",
    "missing_close_time",
    "missing_source_hierarchy",
    "insufficient_source_hierarchy",
)
ALL_REASON_CODES = (PASS_REASON_CODE, *REASON_CODES)
ZERO = Decimal("0")
ONE = Decimal("1")
SIX_PLACES = Decimal("0.000001")


@dataclass(frozen=True)
class StrategyEventResolutionContractConfig:
    config_version: str = DEFAULT_STRATEGY_EVENT_RESOLUTION_CONTRACT_CONFIG_VERSION
    minimum_question_character_count: Decimal = Decimal("40")
    minimum_rules_summary_character_count: Decimal = Decimal("80")
    minimum_source_count: Decimal = Decimal("2")
    missing_question_text_weight: Decimal = Decimal("8.000000")
    ambiguous_question_text_weight: Decimal = Decimal("3.500000")
    missing_resolution_rules_summary_weight: Decimal = Decimal("5.000000")
    ambiguous_resolution_rules_summary_weight: Decimal = Decimal("4.500000")
    missing_close_time_weight: Decimal = Decimal("4.000000")
    missing_source_hierarchy_weight: Decimal = Decimal("5.000000")
    insufficient_source_hierarchy_weight: Decimal = Decimal("4.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionContractConfig:
            raise ValueError(
                "config must be exactly StrategyEventResolutionContractConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_question_character_count",
            "minimum_rules_summary_character_count",
            "minimum_source_count",
            "missing_question_text_weight",
            "ambiguous_question_text_weight",
            "missing_resolution_rules_summary_weight",
            "ambiguous_resolution_rules_summary_weight",
            "missing_close_time_weight",
            "missing_source_hierarchy_weight",
            "insufficient_source_hierarchy_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_integral_decimal(
            "minimum_question_character_count",
            self.minimum_question_character_count,
        )
        _require_integral_decimal(
            "minimum_rules_summary_character_count",
            self.minimum_rules_summary_character_count,
        )
        _require_integral_decimal("minimum_source_count", self.minimum_source_count)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyEventResolutionSource:
    source_key: str
    source_tier: str
    hierarchy_rank: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionSource:
            raise ValueError("source must be exactly StrategyEventResolutionSource")
        _require_canonical_string("source_key", self.source_key)
        _require_source_tier("source_tier", self.source_tier)
        object.__setattr__(
            self,
            "hierarchy_rank",
            _normalize_nonnegative_decimal("hierarchy_rank", self.hierarchy_rank),
        )
        if self.hierarchy_rank < ONE:
            raise ValueError("hierarchy_rank must be >= 1")
        _require_integral_decimal("hierarchy_rank", self.hierarchy_rank)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class StrategyEventResolutionContract:
    condition_id: str
    question_text: str
    rules_summary: str
    close_time: datetime | None
    source_hierarchy: tuple[StrategyEventResolutionSource, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionContract:
            raise ValueError("contract must be exactly StrategyEventResolutionContract")
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "question_text",
            _normalize_contract_text("question_text", self.question_text),
        )
        object.__setattr__(
            self,
            "rules_summary",
            _normalize_contract_text("rules_summary", self.rules_summary),
        )
        object.__setattr__(
            self,
            "close_time",
            _normalize_optional_utc("close_time", self.close_time),
        )
        object.__setattr__(
            self,
            "source_hierarchy",
            _normalize_source_hierarchy(self.source_hierarchy),
        )
        _require_hard_flags("contract", self)


@dataclass(frozen=True)
class StrategyEventResolutionContractCheck:
    condition_id: str
    resolution_contract_status: str
    risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionContractCheck:
            raise ValueError("check must be exactly StrategyEventResolutionContractCheck")
        _require_canonical_string("condition_id", self.condition_id)
        _require_resolution_contract_status(
            "resolution_contract_status",
            self.resolution_contract_status,
        )
        object.__setattr__(
            self,
            "risk_score",
            _quantize_six_places(
                _normalize_nonnegative_decimal("risk_score", self.risk_score),
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_check_consistency(self)
        _require_hard_flags("check", self)


def check_strategy_event_resolution_contract(
    contract: StrategyEventResolutionContract,
    *,
    config: StrategyEventResolutionContractConfig,
) -> StrategyEventResolutionContractCheck:
    if type(contract) is not StrategyEventResolutionContract:
        raise ValueError("contract must be a StrategyEventResolutionContract")
    if type(config) is not StrategyEventResolutionContractConfig:
        raise ValueError("config must be a StrategyEventResolutionContractConfig")
    _require_hard_flags("contract", contract)
    _require_hard_flags("config", config)

    reason_codes = _contract_reason_codes(contract, config)
    if not reason_codes:
        reason_codes = (PASS_REASON_CODE,)

    return StrategyEventResolutionContractCheck(
        condition_id=contract.condition_id,
        resolution_contract_status=_resolution_contract_status(reason_codes),
        risk_score=_risk_score(reason_codes, config),
        reason_codes=reason_codes,
    )


def strategy_event_resolution_contract_payload(
    check: StrategyEventResolutionContractCheck,
) -> dict[str, Any]:
    if type(check) is not StrategyEventResolutionContractCheck:
        raise ValueError("check must be a StrategyEventResolutionContractCheck")
    _require_hard_flags("check", check)
    return {
        "condition_id": check.condition_id,
        "resolution_contract_status": check.resolution_contract_status,
        "risk_score": _decimal_text(check.risk_score),
        "reason_codes": list(check.reason_codes),
        "paper_only": check.paper_only,
        "report_only": check.report_only,
        "readonly": check.readonly,
    }


def _contract_reason_codes(
    contract: StrategyEventResolutionContract,
    config: StrategyEventResolutionContractConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []

    if not contract.question_text:
        reason_codes.append("missing_question_text")
    elif _is_ambiguous_question_text(contract.question_text, config):
        reason_codes.append("ambiguous_question_text")

    if not contract.rules_summary:
        reason_codes.append("missing_resolution_rules_summary")
    elif _is_ambiguous_rules_summary(contract.rules_summary, config):
        reason_codes.append("ambiguous_resolution_rules_summary")

    if contract.close_time is None:
        reason_codes.append("missing_close_time")

    if not contract.source_hierarchy:
        reason_codes.append("missing_source_hierarchy")
    elif not _is_sufficient_source_hierarchy(contract.source_hierarchy, config):
        reason_codes.append("insufficient_source_hierarchy")

    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)


def _is_ambiguous_question_text(
    question_text: str,
    config: StrategyEventResolutionContractConfig,
) -> bool:
    normalized = question_text.casefold()
    if Decimal(len(question_text)) < config.minimum_question_character_count:
        return True
    return any(
        fragment in normalized
        for fragment in (
            "the thing",
            "something",
            "anything",
            "tbd",
            "to be determined",
            "unclear",
        )
    )


def _is_ambiguous_rules_summary(
    rules_summary: str,
    config: StrategyEventResolutionContractConfig,
) -> bool:
    normalized = rules_summary.casefold()
    has_resolution_verb = any(
        fragment in normalized
        for fragment in ("resolve", "resolves", "resolved", "resolution")
    )
    has_objective_source = any(
        fragment in normalized
        for fragment in ("official", "polymarket", "market rules", "certif")
    )
    has_deterministic_condition = any(
        fragment in normalized
        for fragment in ("only if", "yes", "no", "before close", "winner", "below")
    )
    has_ambiguous_terms = any(
        fragment in normalized
        for fragment in (
            "news reports",
            "community consensus",
            "social media",
            "generally accepted",
            "likely",
            "probably",
            "tbd",
            "unclear",
        )
    )
    if Decimal(len(rules_summary)) < config.minimum_rules_summary_character_count:
        return True
    return (
        has_ambiguous_terms
        or not has_resolution_verb
        or not has_objective_source
        or not has_deterministic_condition
    )


def _is_sufficient_source_hierarchy(
    source_hierarchy: tuple[StrategyEventResolutionSource, ...],
    config: StrategyEventResolutionContractConfig,
) -> bool:
    if Decimal(len(source_hierarchy)) < config.minimum_source_count:
        return False
    if source_hierarchy[0].hierarchy_rank != ONE:
        return False
    source_tiers = {source.source_tier for source in source_hierarchy}
    has_polymarket_rules = "polymarket_rules" in source_tiers
    has_official_source = bool(
        source_tiers.intersection({"official_primary", "official_secondary"}),
    )
    return has_polymarket_rules and has_official_source


def _resolution_contract_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    blocking_reasons = set(reason_codes).difference({"insufficient_source_hierarchy"})
    if blocking_reasons:
        return "blocked"
    return "watch"


def _risk_score(
    reason_codes: tuple[str, ...],
    config: StrategyEventResolutionContractConfig,
) -> Decimal:
    if reason_codes == (PASS_REASON_CODE,):
        return ZERO
    risk_weights = {
        "missing_question_text": config.missing_question_text_weight,
        "ambiguous_question_text": config.ambiguous_question_text_weight,
        "missing_resolution_rules_summary": (
            config.missing_resolution_rules_summary_weight
        ),
        "ambiguous_resolution_rules_summary": (
            config.ambiguous_resolution_rules_summary_weight
        ),
        "missing_close_time": config.missing_close_time_weight,
        "missing_source_hierarchy": config.missing_source_hierarchy_weight,
        "insufficient_source_hierarchy": config.insufficient_source_hierarchy_weight,
    }
    return _quantize_six_places(sum((risk_weights[code] for code in reason_codes), ZERO))


def _normalize_source_hierarchy(
    value: object,
) -> tuple[StrategyEventResolutionSource, ...]:
    if type(value) is not tuple:
        raise ValueError("source_hierarchy must be a tuple")
    sources = tuple(value)
    seen_keys: set[str] = set()
    seen_ranks: set[Decimal] = set()
    for source in sources:
        if type(source) is not StrategyEventResolutionSource:
            raise ValueError(
                "source_hierarchy must contain StrategyEventResolutionSource values",
            )
        _require_hard_flags("source", source)
        if source.source_key in seen_keys:
            raise ValueError("source_hierarchy source_key values must be unique")
        if source.hierarchy_rank in seen_ranks:
            raise ValueError("source_hierarchy hierarchy_rank values must be unique")
        seen_keys.add(source.source_key)
        seen_ranks.add(source.hierarchy_rank)
    return tuple(sorted(sources, key=lambda source: (source.hierarchy_rank, source.source_key)))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    expected_order = tuple(
        reason_code for reason_code in ALL_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected_order:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_check_consistency(check: StrategyEventResolutionContractCheck) -> None:
    if check.resolution_contract_status == "pass":
        if check.reason_codes != (PASS_REASON_CODE,):
            raise ValueError("pass check must use pass reason code")
        if check.risk_score != ZERO:
            raise ValueError("pass check must have zero risk_score")
        return
    if PASS_REASON_CODE in check.reason_codes:
        raise ValueError("non-pass check cannot use pass reason code")
    if check.resolution_contract_status == "watch" and any(
        reason_code != "insufficient_source_hierarchy"
        for reason_code in check.reason_codes
    ):
        raise ValueError("watch check can only use watch-level reason_codes")
    if check.resolution_contract_status == "blocked" and not set(
        check.reason_codes,
    ).difference({"insufficient_source_hierarchy"}):
        raise ValueError("blocked check requires a blocking reason_code")


def _normalize_contract_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value.strip()


def _normalize_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a finite nonnegative Decimal")
    return value


def _quantize_six_places(value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal("decimal", value).quantize(SIX_PLACES)


def _decimal_text(value: Decimal) -> str:
    if value == value.to_integral_value() and value.as_tuple().exponent == 0:
        return str(value.quantize(Decimal("1")))
    return format(value, "f")


def _require_source_tier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SOURCE_TIERS:
        raise ValueError(f"{field_name} must be a known source tier")


def _require_resolution_contract_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RESOLUTION_CONTRACT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ALL_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


__all__ = (
    "DEFAULT_STRATEGY_EVENT_RESOLUTION_CONTRACT_CONFIG_VERSION",
    "StrategyEventResolutionContract",
    "StrategyEventResolutionContractCheck",
    "StrategyEventResolutionContractConfig",
    "StrategyEventResolutionSource",
    "check_strategy_event_resolution_contract",
    "strategy_event_resolution_contract_payload",
)
