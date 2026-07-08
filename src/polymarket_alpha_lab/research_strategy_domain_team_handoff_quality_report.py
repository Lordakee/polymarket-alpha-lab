"""Pure report for domain-team handoff quality review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any, Mapping


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION",
    "ResearchStrategyDomainTeamHandoffQualityConfig",
    "ResearchStrategyDomainTeamHandoffQualityInput",
    "ResearchStrategyDomainTeamHandoffQualityReasonCodeCount",
    "ResearchStrategyDomainTeamHandoffQualityReport",
    "ResearchStrategyDomainTeamHandoffQualityRow",
    "build_research_strategy_domain_team_handoff_quality_report",
    "research_strategy_domain_team_handoff_quality_report_digest",
    "research_strategy_domain_team_handoff_quality_report_payload",
)

DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-team-handoff-quality-report-v0"
)
STATUSES = ("pass", "watch", "block")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "au" "th",
    "b" "uy",
    "candidate",
    "data" "base",
    "dsn",
    "live",
    "market",
    "network",
    "or" "der",
    "position",
    "question",
    "raw",
    "recomme" "ndation",
    "se" "ll",
    "signing",
    "sizing",
    "slug",
    "source",
    "table",
    "token",
    "tr" "ade",
    "url",
    "wa" "llet",
)
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
STATUS_WEIGHT = {
    "block": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}


@dataclass(frozen=True)
class _PayloadFlags:
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


@dataclass(frozen=True)
class ResearchStrategyDomainTeamHandoffQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION
    )
    pass_dimension_score: Decimal = Decimal("0.700000")
    watch_dimension_score: Decimal = Decimal("0.500000")
    pass_handoff_quality_score: Decimal = Decimal("0.750000")
    watch_handoff_quality_score: Decimal = Decimal("0.500000")
    handoff_completeness_weight: Decimal = Decimal("0.250000")
    conflict_resolution_weight: Decimal = Decimal("0.250000")
    evidence_maturity_weight: Decimal = Decimal("0.250000")
    forecast_stability_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamHandoffQualityConfig:
            raise TypeError(
                "ResearchStrategyDomainTeamHandoffQualityConfig subclass is not allowed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainTeamHandoffQualityConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyDomainTeamHandoffQualityConfig",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_dimension_score",
            "watch_dimension_score",
            "pass_handoff_quality_score",
            "watch_handoff_quality_score",
            "handoff_completeness_weight",
            "conflict_resolution_weight",
            "evidence_maturity_weight",
            "forecast_stability_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_dimension_score <= self.watch_dimension_score:
            raise ValueError("pass_dimension_score must exceed watch_dimension_score")
        if self.pass_handoff_quality_score <= self.watch_handoff_quality_score:
            raise ValueError(
                "pass_handoff_quality_score must exceed watch_handoff_quality_score",
            )
        if _config_weight_sum(self) != ONE:
            raise ValueError("handoff quality weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamHandoffQualityInput:
    domain_team_label: str
    handoff_completeness: Decimal
    unresolved_conflict_pressure: Decimal
    evidence_maturity: Decimal
    forecast_readiness_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamHandoffQualityInput:
            raise TypeError(
                "ResearchStrategyDomainTeamHandoffQualityInput subclass is not allowed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainTeamHandoffQualityInput:
            raise ValueError(
                "input must be exactly ResearchStrategyDomainTeamHandoffQualityInput",
            )
        _require_public_label("domain_team_label", self.domain_team_label)
        for field_name in (
            "handoff_completeness",
            "unresolved_conflict_pressure",
            "evidence_maturity",
            "forecast_readiness_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamHandoffQualityRow:
    domain_team_label: str
    handoff_completeness: Decimal
    unresolved_conflict_pressure: Decimal
    evidence_maturity: Decimal
    forecast_readiness_pressure: Decimal
    conflict_resolution_score: Decimal
    forecast_stability_score: Decimal
    handoff_quality_score: Decimal
    lowest_dimension_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamHandoffQualityRow:
            raise TypeError(
                "ResearchStrategyDomainTeamHandoffQualityRow subclass is not allowed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainTeamHandoffQualityRow:
            raise ValueError("row must be exactly ResearchStrategyDomainTeamHandoffQualityRow")
        _require_public_label("domain_team_label", self.domain_team_label)
        for field_name in (
            "handoff_completeness",
            "unresolved_conflict_pressure",
            "evidence_maturity",
            "forecast_readiness_pressure",
            "conflict_resolution_score",
            "forecast_stability_score",
            "handoff_quality_score",
            "lowest_dimension_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamHandoffQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamHandoffQualityReasonCodeCount:
            raise TypeError(
                "ResearchStrategyDomainTeamHandoffQualityReasonCodeCount subclass "
                "is not allowed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainTeamHandoffQualityReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchStrategyDomainTeamHandoffQualityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamHandoffQualityReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_handoff_quality_score: Decimal | None
    min_handoff_completeness: Decimal | None
    min_evidence_maturity: Decimal | None
    max_unresolved_conflict_pressure: Decimal | None
    max_forecast_readiness_pressure: Decimal | None
    status: str
    rows: tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainTeamHandoffQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamHandoffQualityReport:
            raise TypeError(
                "ResearchStrategyDomainTeamHandoffQualityReport subclass is not allowed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainTeamHandoffQualityReport:
            raise ValueError(
                "report must be exactly ResearchStrategyDomainTeamHandoffQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_handoff_quality_score",
            "min_handoff_completeness",
            "min_evidence_maturity",
            "max_unresolved_conflict_pressure",
            "max_forecast_readiness_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = research_strategy_domain_team_handoff_quality_report_digest(self)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_domain_team_handoff_quality_report(
    items: Iterable[ResearchStrategyDomainTeamHandoffQualityInput],
    *,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamHandoffQualityReport:
    if type(config) is not ResearchStrategyDomainTeamHandoffQualityConfig:
        raise ValueError("config must be a ResearchStrategyDomainTeamHandoffQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(items)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_handoff_quality_score": _average_handoff_quality_score(rows),
        "min_handoff_completeness": _min_or_none(
            row.handoff_completeness for row in rows
        ),
        "min_evidence_maturity": _min_or_none(row.evidence_maturity for row in rows),
        "max_unresolved_conflict_pressure": _max_or_none(
            row.unresolved_conflict_pressure for row in rows
        ),
        "max_forecast_readiness_pressure": _max_or_none(
            row.forecast_readiness_pressure for row in rows
        ),
        "status": _summary_status(reason_codes),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDomainTeamHandoffQualityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_domain_team_handoff_quality_report_payload(
    report: ResearchStrategyDomainTeamHandoffQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainTeamHandoffQualityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _payload_value(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _payload_value(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256_digest("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchStrategyDomainTeamHandoffQualityReport")


def research_strategy_domain_team_handoff_quality_report_digest(
    report: ResearchStrategyDomainTeamHandoffQualityReport,
) -> str:
    if type(report) is not ResearchStrategyDomainTeamHandoffQualityReport:
        raise ValueError("report must be a ResearchStrategyDomainTeamHandoffQualityReport")
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _report_digest_from_values(values)


def _row_from_input(
    item: ResearchStrategyDomainTeamHandoffQualityInput,
    *,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
) -> ResearchStrategyDomainTeamHandoffQualityRow:
    conflict_resolution_score = _inverse_score(item.unresolved_conflict_pressure)
    forecast_stability_score = _inverse_score(item.forecast_readiness_pressure)
    handoff_quality_score = _handoff_quality_score(
        handoff_completeness=item.handoff_completeness,
        conflict_resolution_score=conflict_resolution_score,
        evidence_maturity=item.evidence_maturity,
        forecast_stability_score=forecast_stability_score,
        config=config,
    )
    lowest_dimension_score = min(
        item.handoff_completeness,
        conflict_resolution_score,
        item.evidence_maturity,
        forecast_stability_score,
    )
    status = _row_status(
        handoff_quality_score=handoff_quality_score,
        lowest_dimension_score=lowest_dimension_score,
        config=config,
    )
    return ResearchStrategyDomainTeamHandoffQualityRow(
        domain_team_label=item.domain_team_label,
        handoff_completeness=item.handoff_completeness,
        unresolved_conflict_pressure=item.unresolved_conflict_pressure,
        evidence_maturity=item.evidence_maturity,
        forecast_readiness_pressure=item.forecast_readiness_pressure,
        conflict_resolution_score=conflict_resolution_score,
        forecast_stability_score=forecast_stability_score,
        handoff_quality_score=handoff_quality_score,
        lowest_dimension_score=lowest_dimension_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _handoff_quality_score(
    *,
    handoff_completeness: Decimal,
    conflict_resolution_score: Decimal,
    evidence_maturity: Decimal,
    forecast_stability_score: Decimal,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            handoff_completeness * config.handoff_completeness_weight
            + conflict_resolution_score * config.conflict_resolution_weight
            + evidence_maturity * config.evidence_maturity_weight
            + forecast_stability_score * config.forecast_stability_weight
        )
    return _quantize(score)


def _row_status(
    *,
    handoff_quality_score: Decimal,
    lowest_dimension_score: Decimal,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
) -> str:
    if (
        handoff_quality_score < config.watch_handoff_quality_score
        or lowest_dimension_score < config.watch_dimension_score
    ):
        return "block"
    if (
        handoff_quality_score < config.pass_handoff_quality_score
        or lowest_dimension_score < config.pass_dimension_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyDomainTeamHandoffQualityInput,
    *,
    status: str,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
) -> tuple[str, ...]:
    normalized = [
        f"domain_team_handoff_quality_{status}",
        f"evidence_maturity_{_quality_status(item.evidence_maturity, config)}",
        (
            "forecast_readiness_pressure_"
            f"{_pressure_status(item.forecast_readiness_pressure, config)}"
        ),
        f"handoff_completeness_{_quality_status(item.handoff_completeness, config)}",
        f"report_only_domain_team_handoff_quality_{status}",
        (
            "unresolved_conflicts_"
            f"{_pressure_status(item.unresolved_conflict_pressure, config)}"
        ),
    ]
    for reason_code in item.reason_codes:
        input_code = f"input_{reason_code}"
        if input_code not in normalized:
            normalized.append(input_code)
    return tuple(
        code
        for code in (
            f"domain_team_handoff_quality_{status}",
            "evidence_maturity_block",
            "evidence_maturity_watch",
            "evidence_maturity_pass",
            "forecast_readiness_pressure_block",
            "forecast_readiness_pressure_watch",
            "forecast_readiness_pressure_pass",
            "handoff_completeness_block",
            "handoff_completeness_watch",
            "handoff_completeness_pass",
            *sorted(code for code in normalized if code.startswith("input_")),
            f"report_only_domain_team_handoff_quality_{status}",
            "unresolved_conflicts_block",
            "unresolved_conflicts_watch",
            "unresolved_conflicts_pass",
        )
        if code in normalized
    )


def _quality_status(
    value: Decimal,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
) -> str:
    if value < config.watch_dimension_score:
        return "block"
    if value < config.pass_dimension_score:
        return "watch"
    return "pass"


def _pressure_status(
    value: Decimal,
    config: ResearchStrategyDomainTeamHandoffQualityConfig,
) -> str:
    if value >= config.watch_dimension_score:
        return "block"
    if value > ONE - config.pass_dimension_score:
        return "watch"
    return "pass"


def _normalize_inputs(
    items: Iterable[ResearchStrategyDomainTeamHandoffQualityInput],
) -> tuple[ResearchStrategyDomainTeamHandoffQualityInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyDomainTeamHandoffQualityInput:
            raise ValueError(
                "items must contain ResearchStrategyDomainTeamHandoffQualityInput",
            )
        _require_hard_flags("input", item)
        if item.domain_team_label in seen:
            raise ValueError("domain_team_label values must be unique")
        seen.add(item.domain_team_label)
    return normalized


def _row_sort_key(
    row: ResearchStrategyDomainTeamHandoffQualityRow,
) -> tuple[Decimal, str]:
    return (-STATUS_WEIGHT[row.status], row.domain_team_label)


def _summary_reason_codes(
    rows: tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_domain_team_handoff_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("domain_team_handoff_quality_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_domain_team_handoff_inputs",):
        return "block"
    if "domain_team_handoff_quality_block" in reason_codes:
        return "block"
    if "domain_team_handoff_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyDomainTeamHandoffQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainTeamHandoffQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainTeamHandoffQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_handoff_quality_score(
    rows: tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.handoff_quality_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _min_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return min(items)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _normalize_rows(
    rows: tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...],
) -> tuple[ResearchStrategyDomainTeamHandoffQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyDomainTeamHandoffQualityRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainTeamHandoffQualityRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status and domain_team_label")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyDomainTeamHandoffQualityReasonCodeCount, ...],
) -> tuple[ResearchStrategyDomainTeamHandoffQualityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyDomainTeamHandoffQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainTeamHandoffQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchStrategyDomainTeamHandoffQualityRow,
) -> None:
    if row.conflict_resolution_score != _inverse_score(row.unresolved_conflict_pressure):
        raise ValueError("conflict_resolution_score must match unresolved_conflict_pressure")
    if row.forecast_stability_score != _inverse_score(row.forecast_readiness_pressure):
        raise ValueError("forecast_stability_score must match forecast_readiness_pressure")
    calculated_lowest = min(
        row.handoff_completeness,
        row.conflict_resolution_score,
        row.evidence_maturity,
        row.forecast_stability_score,
    )
    if row.lowest_dimension_score != calculated_lowest:
        raise ValueError("lowest_dimension_score must match dimensions")
    highest_dimension = max(
        row.handoff_completeness,
        row.conflict_resolution_score,
        row.evidence_maturity,
        row.forecast_stability_score,
    )
    if (
        row.handoff_quality_score < row.lowest_dimension_score
        or row.handoff_quality_score > highest_dimension
    ):
        raise ValueError("handoff_quality_score must stay within dimension bounds")
    expected_code = f"domain_team_handoff_quality_{row.status}"
    if expected_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyDomainTeamHandoffQualityReport,
) -> None:
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_handoff_quality_score != _average_handoff_quality_score(report.rows):
        raise ValueError("average_handoff_quality_score must match rows")
    if report.min_handoff_completeness != _min_or_none(
        row.handoff_completeness for row in report.rows
    ):
        raise ValueError("min_handoff_completeness must match rows")
    if report.min_evidence_maturity != _min_or_none(
        row.evidence_maturity for row in report.rows
    ):
        raise ValueError("min_evidence_maturity must match rows")
    if report.max_unresolved_conflict_pressure != _max_or_none(
        row.unresolved_conflict_pressure for row in report.rows
    ):
        raise ValueError("max_unresolved_conflict_pressure must match rows")
    if report.max_forecast_readiness_pressure != _max_or_none(
        row.forecast_readiness_pressure for row in report.rows
    ):
        raise ValueError("max_forecast_readiness_pressure must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is bool or type(value) is str or value is None:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    raise ValueError("payload value is not JSON serializable")


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest_payload",
        payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_validation_digest(payload: Mapping[str, object]) -> str:
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    return _report_digest_from_values(values)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _inverse_score(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _config_weight_sum(config: ResearchStrategyDomainTeamHandoffQualityConfig) -> Decimal:
    return _quantize(
        config.handoff_completeness_weight
        + config.conflict_resolution_weight
        + config.evidence_maturity_weight
        + config.forecast_stability_weight,
    )


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public reason code")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


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
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")
