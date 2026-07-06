"""Pure report-only hierarchy for pre-decision resolution sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SOURCE_TIERS = (
    "official_rules",
    "exchange_polymarket_page",
    "primary_data_source",
    "secondary_news",
    "social_rumor",
)
HIERARCHY_STATUSES = ("pass", "watch", "blocked")
TIER_RANK = {
    source_tier: rank
    for rank, source_tier in enumerate(SOURCE_TIERS)
}
BEST_SOURCE_TIER_REASON_CODES = {
    "exchange_polymarket_page": "best_available_source_is_exchange_polymarket_page",
    "primary_data_source": "best_available_source_is_primary_data_source",
    "secondary_news": "best_available_source_is_secondary_news",
    "social_rumor": "best_available_source_is_social_rumor",
}
REASON_CODES = (
    "official_resolution_rules_available",
    "missing_official_resolution_rules",
    "weak_resolution_source_hierarchy",
    "missing_resolution_source",
) + tuple(BEST_SOURCE_TIER_REASON_CODES.values())


@dataclass(frozen=True)
class StrategyResolutionSourceEvidence:
    source_id: str
    source_tier: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionSourceEvidence:
            raise ValueError("source must be a StrategyResolutionSourceEvidence")
        _require_canonical_string("source_id", self.source_id)
        _require_source_tier("source_tier", self.source_tier)
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyResolutionSourceHierarchyReport:
    hierarchy_status: str
    best_available_source_tier: str | None
    source_count: int
    best_available_source_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionSourceHierarchyReport:
            raise ValueError("report must be a StrategyResolutionSourceHierarchyReport")
        _require_hierarchy_status("hierarchy_status", self.hierarchy_status)
        _require_best_available_source_tier(
            "best_available_source_tier",
            self.best_available_source_tier,
        )
        _require_nonnegative_int("source_count", self.source_count)
        _require_nonnegative_int(
            "best_available_source_count",
            self.best_available_source_count,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.hierarchy_status != _status_for_best_tier(
            self.best_available_source_tier,
        ):
            raise ValueError("hierarchy_status must match best_available_source_tier")
        if self.reason_codes != _reason_codes_for_best_tier(
            self.best_available_source_tier,
        ):
            raise ValueError("reason_codes must match best_available_source_tier")
        if self.source_count == 0:
            if self.best_available_source_tier is not None:
                raise ValueError("best_available_source_tier must be None without sources")
            if self.best_available_source_count != 0:
                raise ValueError("best_available_source_count must be 0 without sources")
        else:
            if self.best_available_source_tier is None:
                raise ValueError("best_available_source_tier must be present with sources")
            if self.best_available_source_count <= 0:
                raise ValueError("best_available_source_count must be positive with sources")
            if self.best_available_source_count > self.source_count:
                raise ValueError("best_available_source_count must not exceed source_count")
        _require_hard_flags(self)


def build_strategy_resolution_source_hierarchy_report(
    sources: tuple[StrategyResolutionSourceEvidence, ...],
) -> StrategyResolutionSourceHierarchyReport:
    """Return the best available resolution source tier before a decision."""

    normalized_sources = _normalize_sources(sources)
    best_available_source_tier = _best_available_source_tier(normalized_sources)
    best_available_source_count = _best_available_source_count(
        normalized_sources,
        best_available_source_tier,
    )

    return StrategyResolutionSourceHierarchyReport(
        hierarchy_status=_status_for_best_tier(best_available_source_tier),
        best_available_source_tier=best_available_source_tier,
        source_count=len(normalized_sources),
        best_available_source_count=best_available_source_count,
        reason_codes=_reason_codes_for_best_tier(best_available_source_tier),
    )


def strategy_resolution_source_hierarchy_payload(
    report: StrategyResolutionSourceHierarchyReport,
) -> dict[str, Any]:
    if type(report) is not StrategyResolutionSourceHierarchyReport:
        raise ValueError("report must be a StrategyResolutionSourceHierarchyReport")
    _require_hard_flags(report)
    return _payload_value(asdict(report))


def _normalize_sources(
    sources: tuple[StrategyResolutionSourceEvidence, ...],
) -> tuple[StrategyResolutionSourceEvidence, ...]:
    if type(sources) is not tuple:
        raise ValueError("sources must be a tuple")
    source_ids: list[str] = []
    for source in sources:
        if type(source) is not StrategyResolutionSourceEvidence:
            raise ValueError("sources must contain source evidence")
        _require_hard_flags(source)
        source_ids.append(source.source_id)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("source_id values must be unique")
    return sources


def _best_available_source_tier(
    sources: tuple[StrategyResolutionSourceEvidence, ...],
) -> str | None:
    if not sources:
        return None
    return min((source.source_tier for source in sources), key=TIER_RANK.__getitem__)


def _best_available_source_count(
    sources: tuple[StrategyResolutionSourceEvidence, ...],
    best_available_source_tier: str | None,
) -> int:
    if best_available_source_tier is None:
        return 0
    return sum(
        1
        for source in sources
        if source.source_tier == best_available_source_tier
    )


def _reason_codes_for_best_tier(
    best_available_source_tier: str | None,
) -> tuple[str, ...]:
    if best_available_source_tier is None:
        return ("missing_resolution_source",)
    if best_available_source_tier == "official_rules":
        return ("official_resolution_rules_available",)
    if best_available_source_tier in (
        "exchange_polymarket_page",
        "primary_data_source",
    ):
        return (
            "missing_official_resolution_rules",
            BEST_SOURCE_TIER_REASON_CODES[best_available_source_tier],
        )
    return (
        "missing_official_resolution_rules",
        "weak_resolution_source_hierarchy",
        BEST_SOURCE_TIER_REASON_CODES[best_available_source_tier],
    )


def _status_for_best_tier(best_available_source_tier: str | None) -> str:
    if best_available_source_tier == "official_rules":
        return "pass"
    if best_available_source_tier in (
        "exchange_polymarket_page",
        "primary_data_source",
    ):
        return "watch"
    return "blocked"


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must contain at least one reason code")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_reason_code(field_name, value)
    return values


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hierarchy_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in HIERARCHY_STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_source_tier(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in SOURCE_TIERS:
        raise ValueError(f"{field_name} must be a known source tier")


def _require_best_available_source_tier(
    field_name: str,
    value: str | None,
) -> None:
    if value is None:
        return
    _require_source_tier(field_name, value)


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


__all__ = (
    "HIERARCHY_STATUSES",
    "SOURCE_TIERS",
    "StrategyResolutionSourceEvidence",
    "StrategyResolutionSourceHierarchyReport",
    "build_strategy_resolution_source_hierarchy_report",
    "strategy_resolution_source_hierarchy_payload",
)
