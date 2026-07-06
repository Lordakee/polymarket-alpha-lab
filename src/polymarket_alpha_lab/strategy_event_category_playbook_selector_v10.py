"""Pure readonly event-category research playbook selector v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_EVENT_CATEGORY_PLAYBOOK_SELECTOR_V10_CONFIG_VERSION = (
    "strategy-event-category-playbook-selector-v10"
)
SCORE_QUANTUM = Decimal("0.000001")
MINUTE_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PLAYBOOK_STATUSES = ("ready", "review_required", "blocked")
RESOLUTION_RISK_TIERS = ("low", "medium", "high", "critical")
SOURCE_QUORUM_STATUSES = ("met", "partial", "conflict")
REQUIRED_CHECKS = (
    "official_resolution_source_check",
    "rule_text_alignment_check",
    "source_quorum_replay_check",
    "jurisdiction_timeline_check",
    "high_risk_adjudication_check",
    "primary_source_integrity_check",
    "cross_source_price_reference_check",
    "resolution_rule_specificity_check",
    "source_conflict_reconciliation_check",
    "critical_resolution_risk_check",
    "urgent_resolution_refresh_check",
    "team_specialist_handoff_check",
    "historical_edge_recheck",
    "secondary_source_consistency_check",
    "source_quorum_gap_check",
    "official_lineup_or_status_check",
    "market_context_consistency_check",
    "category_specific_source_check",
)
REASON_CODES = (
    "strategy_event_category_playbook_selector_v10_category_politics",
    "strategy_event_category_playbook_selector_v10_category_crypto",
    "strategy_event_category_playbook_selector_v10_category_sports",
    "strategy_event_category_playbook_selector_v10_category_finance",
    "strategy_event_category_playbook_selector_v10_category_general",
    "strategy_event_category_playbook_selector_v10_subcategory_election",
    "strategy_event_category_playbook_selector_v10_subcategory_stablecoin",
    "strategy_event_category_playbook_selector_v10_subcategory_soccer",
    "strategy_event_category_playbook_selector_v10_subcategory_basketball",
    "strategy_event_category_playbook_selector_v10_low_resolution_risk",
    "strategy_event_category_playbook_selector_v10_medium_resolution_risk",
    "strategy_event_category_playbook_selector_v10_high_resolution_risk",
    "strategy_event_category_playbook_selector_v10_critical_resolution_risk",
    "strategy_event_category_playbook_selector_v10_source_quorum_met",
    "strategy_event_category_playbook_selector_v10_source_quorum_partial",
    "strategy_event_category_playbook_selector_v10_source_quorum_conflict",
    "strategy_event_category_playbook_selector_v10_urgent_resolution_window",
    "strategy_event_category_playbook_selector_v10_team_specialization_ready",
    "strategy_event_category_playbook_selector_v10_team_specialization_watch",
    "strategy_event_category_playbook_selector_v10_team_specialization_weak",
    "strategy_event_category_playbook_selector_v10_historical_edge_supported",
    "strategy_event_category_playbook_selector_v10_historical_edge_watch",
    "strategy_event_category_playbook_selector_v10_historical_edge_weak",
    "strategy_event_category_playbook_selector_v10_ready",
    "strategy_event_category_playbook_selector_v10_review_required",
    "strategy_event_category_playbook_selector_v10_blocked",
)


@dataclass(frozen=True)
class StrategyEventCategoryPlaybookSelectorV10Config:
    config_version: str = DEFAULT_STRATEGY_EVENT_CATEGORY_PLAYBOOK_SELECTOR_V10_CONFIG_VERSION
    ready_team_specialization_threshold: Decimal = Decimal("0.600000")
    weak_team_specialization_threshold: Decimal = Decimal("0.450000")
    supported_historical_edge_threshold: Decimal = Decimal("0.550000")
    weak_historical_edge_threshold: Decimal = Decimal("0.300000")
    urgent_resolution_minutes: Decimal = Decimal("120")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyEventCategoryPlaybookSelectorV10Config)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "ready_team_specialization_threshold",
            "weak_team_specialization_threshold",
            "supported_historical_edge_threshold",
            "weak_historical_edge_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "urgent_resolution_minutes",
            _normalize_nonnegative_minutes(
                "urgent_resolution_minutes",
                self.urgent_resolution_minutes,
            ),
        )
        _validate_config(self)
        require_paper_only_flags("StrategyEventCategoryPlaybookSelectorV10Config", self)


@dataclass(frozen=True)
class StrategyEventCategoryPlaybookSelectorV10Input:
    category: str
    subcategory: str | None
    resolution_risk_tier: str
    source_quorum_status: str
    team_specialization_score: Decimal
    time_to_resolution_minutes: Decimal
    historical_edge_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("selection input", self, StrategyEventCategoryPlaybookSelectorV10Input)
        object.__setattr__(self, "category", _normalize_label("category", self.category))
        object.__setattr__(
            self,
            "subcategory",
            _normalize_optional_label("subcategory", self.subcategory),
        )
        object.__setattr__(
            self,
            "resolution_risk_tier",
            _require_member(
                "resolution_risk_tier",
                _normalize_label("resolution_risk_tier", self.resolution_risk_tier),
                RESOLUTION_RISK_TIERS,
            ),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _require_member(
                "source_quorum_status",
                _normalize_label("source_quorum_status", self.source_quorum_status),
                SOURCE_QUORUM_STATUSES,
            ),
        )
        for field_name in ("team_specialization_score", "historical_edge_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        require_paper_only_flags("StrategyEventCategoryPlaybookSelectorV10Input", self)


@dataclass(frozen=True)
class StrategyEventCategoryPlaybookSelectorV10Report:
    config_version: str
    category: str
    subcategory: str | None
    resolution_risk_tier: str
    source_quorum_status: str
    team_specialization_score: Decimal
    time_to_resolution_minutes: Decimal
    historical_edge_score: Decimal
    playbook_status: str
    selected_playbook_id: str
    required_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyEventCategoryPlaybookSelectorV10Report)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(self, "category", _normalize_label("category", self.category))
        object.__setattr__(
            self,
            "subcategory",
            _normalize_optional_label("subcategory", self.subcategory),
        )
        object.__setattr__(
            self,
            "resolution_risk_tier",
            _require_member("resolution_risk_tier", self.resolution_risk_tier, RESOLUTION_RISK_TIERS),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _require_member("source_quorum_status", self.source_quorum_status, SOURCE_QUORUM_STATUSES),
        )
        for field_name in ("team_specialization_score", "historical_edge_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "playbook_status",
            _require_member("playbook_status", self.playbook_status, PLAYBOOK_STATUSES),
        )
        object.__setattr__(
            self,
            "selected_playbook_id",
            _require_canonical_string("selected_playbook_id", self.selected_playbook_id),
        )
        object.__setattr__(
            self,
            "required_checks",
            _normalize_required_checks("required_checks", self.required_checks),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("StrategyEventCategoryPlaybookSelectorV10Report", self)


def select_strategy_event_category_playbook_v10(
    *,
    category: str,
    subcategory: str | None,
    resolution_risk_tier: str,
    source_quorum_status: str,
    team_specialization_score: Decimal,
    time_to_resolution_minutes: Decimal,
    historical_edge_score: Decimal,
    config: StrategyEventCategoryPlaybookSelectorV10Config | None = None,
) -> StrategyEventCategoryPlaybookSelectorV10Report:
    active_config = StrategyEventCategoryPlaybookSelectorV10Config() if config is None else config
    if type(active_config) is not StrategyEventCategoryPlaybookSelectorV10Config:
        raise ValueError("config must be a StrategyEventCategoryPlaybookSelectorV10Config")
    require_paper_only_flags("config", active_config)
    selection_input = StrategyEventCategoryPlaybookSelectorV10Input(
        category=category,
        subcategory=subcategory,
        resolution_risk_tier=resolution_risk_tier,
        source_quorum_status=source_quorum_status,
        team_specialization_score=team_specialization_score,
        time_to_resolution_minutes=time_to_resolution_minutes,
        historical_edge_score=historical_edge_score,
    )
    playbook_id, base_checks, category_code, subcategory_code = _playbook_spec(selection_input)
    required_checks = _required_checks(
        base_checks=base_checks,
        selection_input=selection_input,
        config=active_config,
    )
    status = _playbook_status(selection_input)
    reason_codes = _reason_codes(
        category_code=category_code,
        subcategory_code=subcategory_code,
        selection_input=selection_input,
        config=active_config,
        playbook_status=status,
    )
    return StrategyEventCategoryPlaybookSelectorV10Report(
        config_version=active_config.config_version,
        category=selection_input.category,
        subcategory=selection_input.subcategory,
        resolution_risk_tier=selection_input.resolution_risk_tier,
        source_quorum_status=selection_input.source_quorum_status,
        team_specialization_score=selection_input.team_specialization_score,
        time_to_resolution_minutes=selection_input.time_to_resolution_minutes,
        historical_edge_score=selection_input.historical_edge_score,
        playbook_status=status,
        selected_playbook_id=playbook_id,
        required_checks=required_checks,
        reason_codes=reason_codes,
    )


def strategy_event_category_playbook_selector_v10_payload(report: object) -> dict[str, Any]:
    if type(report) is not StrategyEventCategoryPlaybookSelectorV10Report:
        reject_unsafe_surface_fields("strategy event category playbook selector v10 report", report)
        raise ValueError("report must be a StrategyEventCategoryPlaybookSelectorV10Report")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _playbook_spec(
    selection_input: StrategyEventCategoryPlaybookSelectorV10Input,
) -> tuple[str, tuple[str, ...], str, str | None]:
    category = selection_input.category
    subcategory = "" if selection_input.subcategory is None else selection_input.subcategory
    if category.startswith("politics"):
        if subcategory in ("election", "ballot", "polling"):
            return (
                "politics_election_resolution_playbook_v10",
                (
                    "official_resolution_source_check",
                    "rule_text_alignment_check",
                    "source_quorum_replay_check",
                    "jurisdiction_timeline_check",
                ),
                "strategy_event_category_playbook_selector_v10_category_politics",
                "strategy_event_category_playbook_selector_v10_subcategory_election",
            )
        return (
            "politics_event_resolution_playbook_v10",
            (
                "official_resolution_source_check",
                "rule_text_alignment_check",
                "source_quorum_replay_check",
            ),
            "strategy_event_category_playbook_selector_v10_category_politics",
            None,
        )
    if "crypto" in category:
        if subcategory in ("stablecoin", "depeg"):
            return (
                "crypto_stablecoin_depeg_playbook_v10",
                (
                    "primary_source_integrity_check",
                    "cross_source_price_reference_check",
                    "resolution_rule_specificity_check",
                ),
                "strategy_event_category_playbook_selector_v10_category_crypto",
                "strategy_event_category_playbook_selector_v10_subcategory_stablecoin",
            )
        return (
            "crypto_market_resolution_playbook_v10",
            (
                "primary_source_integrity_check",
                "cross_source_price_reference_check",
                "resolution_rule_specificity_check",
            ),
            "strategy_event_category_playbook_selector_v10_category_crypto",
            None,
        )
    if "sports" in category:
        if subcategory == "soccer":
            return (
                "sports_soccer_event_playbook_v10",
                (
                    "official_resolution_source_check",
                    "official_lineup_or_status_check",
                    "market_context_consistency_check",
                ),
                "strategy_event_category_playbook_selector_v10_category_sports",
                "strategy_event_category_playbook_selector_v10_subcategory_soccer",
            )
        if subcategory == "basketball":
            return (
                "sports_basketball_event_playbook_v10",
                (
                    "official_resolution_source_check",
                    "official_lineup_or_status_check",
                    "market_context_consistency_check",
                ),
                "strategy_event_category_playbook_selector_v10_category_sports",
                "strategy_event_category_playbook_selector_v10_subcategory_basketball",
            )
        return (
            "sports_event_resolution_playbook_v10",
            (
                "official_resolution_source_check",
                "category_specific_source_check",
                "market_context_consistency_check",
            ),
            "strategy_event_category_playbook_selector_v10_category_sports",
            None,
        )
    if any(term in category for term in ("finance", "equity", "macro", "commodity")):
        return (
            "finance_macro_event_resolution_playbook_v10",
            (
                "official_resolution_source_check",
                "secondary_source_consistency_check",
                "market_context_consistency_check",
            ),
            "strategy_event_category_playbook_selector_v10_category_finance",
            None,
        )
    return (
        "general_event_resolution_playbook_v10",
        (
            "official_resolution_source_check",
            "secondary_source_consistency_check",
            "resolution_rule_specificity_check",
        ),
        "strategy_event_category_playbook_selector_v10_category_general",
        None,
    )


def _required_checks(
    *,
    base_checks: tuple[str, ...],
    selection_input: StrategyEventCategoryPlaybookSelectorV10Input,
    config: StrategyEventCategoryPlaybookSelectorV10Config,
) -> tuple[str, ...]:
    checks = list(base_checks)
    if selection_input.source_quorum_status == "partial":
        checks.append("source_quorum_gap_check")
    if selection_input.source_quorum_status == "conflict":
        checks.append("source_conflict_reconciliation_check")
    if selection_input.resolution_risk_tier == "high":
        checks.append("high_risk_adjudication_check")
    if selection_input.resolution_risk_tier == "critical":
        checks.append("critical_resolution_risk_check")
    if selection_input.time_to_resolution_minutes < config.urgent_resolution_minutes:
        checks.append("urgent_resolution_refresh_check")
    if selection_input.team_specialization_score < config.weak_team_specialization_threshold:
        checks.append("team_specialist_handoff_check")
    if selection_input.historical_edge_score < config.weak_historical_edge_threshold:
        checks.append("historical_edge_recheck")
    return _normalize_required_checks("required_checks", tuple(checks))


def _playbook_status(selection_input: StrategyEventCategoryPlaybookSelectorV10Input) -> str:
    if selection_input.source_quorum_status == "conflict":
        return "blocked"
    if selection_input.source_quorum_status == "partial":
        return "review_required"
    return "ready"


def _reason_codes(
    *,
    category_code: str,
    subcategory_code: str | None,
    selection_input: StrategyEventCategoryPlaybookSelectorV10Input,
    config: StrategyEventCategoryPlaybookSelectorV10Config,
    playbook_status: str,
) -> tuple[str, ...]:
    codes = [category_code]
    if subcategory_code is not None:
        codes.append(subcategory_code)
    codes.append(
        f"strategy_event_category_playbook_selector_v10_{selection_input.resolution_risk_tier}_resolution_risk",
    )
    codes.append(
        f"strategy_event_category_playbook_selector_v10_source_quorum_{selection_input.source_quorum_status}",
    )
    if selection_input.time_to_resolution_minutes < config.urgent_resolution_minutes:
        codes.append("strategy_event_category_playbook_selector_v10_urgent_resolution_window")
    codes.append(_team_specialization_reason(selection_input, config))
    codes.append(_historical_edge_reason(selection_input, config))
    codes.append(f"strategy_event_category_playbook_selector_v10_{playbook_status}")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _team_specialization_reason(
    selection_input: StrategyEventCategoryPlaybookSelectorV10Input,
    config: StrategyEventCategoryPlaybookSelectorV10Config,
) -> str:
    if selection_input.team_specialization_score < config.weak_team_specialization_threshold:
        return "strategy_event_category_playbook_selector_v10_team_specialization_weak"
    if selection_input.team_specialization_score >= config.ready_team_specialization_threshold:
        return "strategy_event_category_playbook_selector_v10_team_specialization_ready"
    return "strategy_event_category_playbook_selector_v10_team_specialization_watch"


def _historical_edge_reason(
    selection_input: StrategyEventCategoryPlaybookSelectorV10Input,
    config: StrategyEventCategoryPlaybookSelectorV10Config,
) -> str:
    if selection_input.historical_edge_score < config.weak_historical_edge_threshold:
        return "strategy_event_category_playbook_selector_v10_historical_edge_weak"
    if selection_input.historical_edge_score >= config.supported_historical_edge_threshold:
        return "strategy_event_category_playbook_selector_v10_historical_edge_supported"
    return "strategy_event_category_playbook_selector_v10_historical_edge_watch"


def _normalize_required_checks(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    return _dedupe_known_values(field_name, values, REQUIRED_CHECKS)


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    return _dedupe_known_values(field_name, values, REASON_CODES)


def _dedupe_known_values(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported value")
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def _normalize_label(field_name: str, value: object) -> str:
    return _require_canonical_string(field_name, value).casefold().replace("-", "_")


def _normalize_optional_label(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _normalize_label(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_minutes(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal minute count")
    return normalized.quantize(MINUTE_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SCORE_QUANTUM)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _validate_config(config: StrategyEventCategoryPlaybookSelectorV10Config) -> None:
    if config.weak_team_specialization_threshold > config.ready_team_specialization_threshold:
        raise ValueError("weak_team_specialization_threshold cannot exceed ready threshold")
    if config.weak_historical_edge_threshold > config.supported_historical_edge_threshold:
        raise ValueError("weak_historical_edge_threshold cannot exceed supported threshold")


def _validate_report(report: StrategyEventCategoryPlaybookSelectorV10Report) -> None:
    if report.playbook_status == "blocked":
        if "strategy_event_category_playbook_selector_v10_blocked" not in report.reason_codes:
            raise ValueError("blocked reports must include blocked reason")
    if report.playbook_status == "review_required":
        if "strategy_event_category_playbook_selector_v10_review_required" not in report.reason_codes:
            raise ValueError("review_required reports must include review reason")
    if report.playbook_status == "ready":
        if "strategy_event_category_playbook_selector_v10_ready" not in report.reason_codes:
            raise ValueError("ready reports must include ready reason")


__all__ = (
    "DEFAULT_STRATEGY_EVENT_CATEGORY_PLAYBOOK_SELECTOR_V10_CONFIG_VERSION",
    "PLAYBOOK_STATUSES",
    "REQUIRED_CHECKS",
    "RESOLUTION_RISK_TIERS",
    "SOURCE_QUORUM_STATUSES",
    "StrategyEventCategoryPlaybookSelectorV10Config",
    "StrategyEventCategoryPlaybookSelectorV10Input",
    "StrategyEventCategoryPlaybookSelectorV10Report",
    "select_strategy_event_category_playbook_v10",
    "strategy_event_category_playbook_selector_v10_payload",
)
