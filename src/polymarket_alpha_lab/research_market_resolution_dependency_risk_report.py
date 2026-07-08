"""Pure report-only aggregation for market resolution dependency risk."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_RESOLUTION_DEPENDENCY_RISK_CONFIG_VERSION = (
    "research-market-resolution-dependency-risk-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_market",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
)


@dataclass(frozen=True)
class ResearchMarketResolutionDependencyRiskConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_RESOLUTION_DEPENDENCY_RISK_CONFIG_VERSION
    fresh_official_source_age_seconds: Decimal = Decimal("3600.000000")
    stale_official_source_age_seconds: Decimal = Decimal("86400.000000")
    watch_unresolved_dependency_count: Decimal = Decimal("1.000000")
    block_unresolved_dependency_count: Decimal = Decimal("3.000000")
    watch_rule_clarity_score: Decimal = Decimal("0.700000")
    block_rule_clarity_score: Decimal = Decimal("0.400000")
    watch_manual_escalation_urgency_score: Decimal = Decimal("0.500000")
    block_manual_escalation_urgency_score: Decimal = Decimal("0.800000")
    watch_risk_score: Decimal = Decimal("0.250000")
    block_risk_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionDependencyRiskConfig:
            raise TypeError(
                "ResearchMarketResolutionDependencyRiskConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionDependencyRiskConfig:
            raise ValueError(
                "config must be exactly ResearchMarketResolutionDependencyRiskConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_DEPENDENCY_RISK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_official_source_age_seconds",
            "stale_official_source_age_seconds",
            "watch_unresolved_dependency_count",
            "block_unresolved_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_rule_clarity_score",
            "block_rule_clarity_score",
            "watch_manual_escalation_urgency_score",
            "block_manual_escalation_urgency_score",
            "watch_risk_score",
            "block_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_official_source_age_seconds <= self.fresh_official_source_age_seconds:
            raise ValueError(
                "stale_official_source_age_seconds must exceed "
                "fresh_official_source_age_seconds",
            )
        if self.block_unresolved_dependency_count <= self.watch_unresolved_dependency_count:
            raise ValueError(
                "block_unresolved_dependency_count must exceed "
                "watch_unresolved_dependency_count",
            )
        if self.watch_rule_clarity_score <= self.block_rule_clarity_score:
            raise ValueError(
                "watch_rule_clarity_score must exceed block_rule_clarity_score",
            )
        if (
            self.block_manual_escalation_urgency_score
            <= self.watch_manual_escalation_urgency_score
        ):
            raise ValueError(
                "block_manual_escalation_urgency_score must exceed "
                "watch_manual_escalation_urgency_score",
            )
        if self.block_risk_score <= self.watch_risk_score:
            raise ValueError("block_risk_score must exceed watch_risk_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionDependencyInput:
    resolution_group_id: str
    raw_market_id: str
    market_slug: str
    market_question: str
    dependency_id: str
    dependency_kind: str
    is_unresolved: bool
    official_source_observed_at: datetime
    rule_clarity_score: Decimal
    manual_escalation_urgency_score: Decimal
    source_url: str
    source_text: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionDependencyInput:
            raise TypeError(
                "ResearchMarketResolutionDependencyInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionDependencyInput:
            raise ValueError(
                "dependency must be exactly ResearchMarketResolutionDependencyInput",
            )
        for field_name in ("resolution_group_id", "dependency_id", "dependency_kind"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in ("raw_market_id", "market_slug", "market_question"):
            _require_nonempty_text(field_name, getattr(self, field_name))
        for field_name in ("source_url", "source_text"):
            _require_nonempty_text(field_name, getattr(self, field_name))
        if type(self.is_unresolved) is not bool:
            raise ValueError("is_unresolved must be a bool")
        object.__setattr__(
            self,
            "official_source_observed_at",
            _as_utc("official_source_observed_at", self.official_source_observed_at),
        )
        for field_name in (
            "rule_clarity_score",
            "manual_escalation_urgency_score",
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
        _require_hard_flags("dependency", self)


@dataclass(frozen=True)
class ResearchMarketResolutionDependencyRiskRow:
    resolution_group_id: str
    dependency_count: Decimal
    unresolved_external_dependency_count: Decimal
    latest_official_source_age_seconds: Decimal
    official_source_freshness_score: Decimal
    average_rule_clarity_score: Decimal
    max_manual_escalation_urgency_score: Decimal
    risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionDependencyRiskRow:
            raise TypeError(
                "ResearchMarketResolutionDependencyRiskRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionDependencyRiskRow:
            raise ValueError(
                "row must be exactly ResearchMarketResolutionDependencyRiskRow",
            )
        _require_public_identifier("resolution_group_id", self.resolution_group_id)
        for field_name in (
            "dependency_count",
            "unresolved_external_dependency_count",
            "latest_official_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_freshness_score",
            "average_rule_clarity_score",
            "max_manual_escalation_urgency_score",
            "risk_score",
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
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketResolutionDependencyRiskReport:
    generated_at: datetime
    config_version: str
    group_count: Decimal
    dependency_count: Decimal
    unresolved_external_dependency_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_official_source_freshness_score: Decimal
    average_rule_clarity_score: Decimal
    max_manual_escalation_urgency_score: Decimal
    status: str
    rows: tuple[ResearchMarketResolutionDependencyRiskRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionDependencyRiskReport:
            raise TypeError(
                "ResearchMarketResolutionDependencyRiskReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionDependencyRiskReport:
            raise ValueError(
                "report must be exactly ResearchMarketResolutionDependencyRiskReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_DEPENDENCY_RISK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "group_count",
            "dependency_count",
            "unresolved_external_dependency_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_official_source_freshness_score",
            "average_rule_clarity_score",
            "max_manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_market_resolution_dependency_risk_report(
    dependencies: Sequence[ResearchMarketResolutionDependencyInput],
    *,
    generated_at: datetime,
    config: ResearchMarketResolutionDependencyRiskConfig | None = None,
) -> ResearchMarketResolutionDependencyRiskReport:
    if config is None:
        config = ResearchMarketResolutionDependencyRiskConfig()
    if type(config) is not ResearchMarketResolutionDependencyRiskConfig:
        raise ValueError(
            "config must be a ResearchMarketResolutionDependencyRiskConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_dependencies = _normalize_dependencies(dependencies)
    for item in normalized_dependencies:
        if item.official_source_observed_at > generated_at:
            raise ValueError(
                "official_source_observed_at must not be after generated_at",
            )
    rows = _build_rows(normalized_dependencies, config, generated_at)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "group_count": _decimal_count(len(rows)),
        "dependency_count": sum((row.dependency_count for row in rows), _ZERO),
        "unresolved_external_dependency_count": sum(
            (row.unresolved_external_dependency_count for row in rows),
            _ZERO,
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "block")),
        "average_official_source_freshness_score": _average(
            tuple(row.official_source_freshness_score for row in rows),
        ),
        "average_rule_clarity_score": _average(
            tuple(row.average_rule_clarity_score for row in rows),
        ),
        "max_manual_escalation_urgency_score": max(
            (row.max_manual_escalation_urgency_score for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketResolutionDependencyRiskReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_resolution_dependency_risk_report_payload(
    report: ResearchMarketResolutionDependencyRiskReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketResolutionDependencyRiskReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError(
            "report must be a ResearchMarketResolutionDependencyRiskReport",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
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


def _build_rows(
    dependencies: tuple[ResearchMarketResolutionDependencyInput, ...],
    config: ResearchMarketResolutionDependencyRiskConfig,
    generated_at: datetime,
) -> tuple[ResearchMarketResolutionDependencyRiskRow, ...]:
    grouped: dict[str, list[ResearchMarketResolutionDependencyInput]] = {}
    for item in dependencies:
        grouped.setdefault(item.resolution_group_id, []).append(item)
    return tuple(
        _row_for_group(
            resolution_group_id,
            tuple(grouped[resolution_group_id]),
            config,
            generated_at,
        )
        for resolution_group_id in sorted(grouped)
    )


def _row_for_group(
    resolution_group_id: str,
    dependencies: tuple[ResearchMarketResolutionDependencyInput, ...],
    config: ResearchMarketResolutionDependencyRiskConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionDependencyRiskRow:
    dependency_count = _decimal_count(len(dependencies))
    unresolved_count = _decimal_count(sum(1 for item in dependencies if item.is_unresolved))
    latest_observed_at = max(item.official_source_observed_at for item in dependencies)
    latest_age = _age_seconds(generated_at, latest_observed_at)
    freshness_score = _official_source_freshness_score(latest_age, config)
    clarity_score = _average(tuple(item.rule_clarity_score for item in dependencies))
    urgency_score = max(
        (item.manual_escalation_urgency_score for item in dependencies),
        default=_ZERO,
    )
    risk_score = _risk_score(
        dependency_count=dependency_count,
        unresolved_external_dependency_count=unresolved_count,
        official_source_freshness_score=freshness_score,
        average_rule_clarity_score=clarity_score,
        max_manual_escalation_urgency_score=urgency_score,
    )
    status = _row_status(
        unresolved_external_dependency_count=unresolved_count,
        official_source_freshness_score=freshness_score,
        average_rule_clarity_score=clarity_score,
        max_manual_escalation_urgency_score=urgency_score,
        risk_score=risk_score,
        config=config,
    )
    return ResearchMarketResolutionDependencyRiskRow(
        resolution_group_id=resolution_group_id,
        dependency_count=dependency_count,
        unresolved_external_dependency_count=unresolved_count,
        latest_official_source_age_seconds=latest_age,
        official_source_freshness_score=freshness_score,
        average_rule_clarity_score=clarity_score,
        max_manual_escalation_urgency_score=urgency_score,
        risk_score=risk_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            unresolved_external_dependency_count=unresolved_count,
            official_source_freshness_score=freshness_score,
            average_rule_clarity_score=clarity_score,
            max_manual_escalation_urgency_score=urgency_score,
            input_reason_codes=tuple(
                reason_code for item in dependencies for reason_code in item.reason_codes
            ),
            config=config,
        ),
    )


def _official_source_freshness_score(
    age_seconds: Decimal,
    config: ResearchMarketResolutionDependencyRiskConfig,
) -> Decimal:
    if age_seconds <= config.fresh_official_source_age_seconds:
        return _ONE
    if age_seconds >= config.stale_official_source_age_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (age_seconds / config.stale_official_source_age_seconds))


def _risk_score(
    *,
    dependency_count: Decimal,
    unresolved_external_dependency_count: Decimal,
    official_source_freshness_score: Decimal,
    average_rule_clarity_score: Decimal,
    max_manual_escalation_urgency_score: Decimal,
) -> Decimal:
    if dependency_count <= _ZERO:
        return _ZERO
    unresolved_ratio = _clamp_ratio(unresolved_external_dependency_count / dependency_count)
    freshness_gap = _ONE - official_source_freshness_score
    clarity_gap = _ONE - average_rule_clarity_score
    return _clamp_ratio(
        (
            unresolved_ratio
            + freshness_gap
            + clarity_gap
            + max_manual_escalation_urgency_score
        )
        / _FOUR,
    )


def _row_status(
    *,
    unresolved_external_dependency_count: Decimal,
    official_source_freshness_score: Decimal,
    average_rule_clarity_score: Decimal,
    max_manual_escalation_urgency_score: Decimal,
    risk_score: Decimal,
    config: ResearchMarketResolutionDependencyRiskConfig,
) -> str:
    if (
        unresolved_external_dependency_count >= config.block_unresolved_dependency_count
        or official_source_freshness_score == _ZERO
        or average_rule_clarity_score <= config.block_rule_clarity_score
        or max_manual_escalation_urgency_score
        >= config.block_manual_escalation_urgency_score
        or risk_score >= config.block_risk_score
    ):
        return "block"
    if (
        unresolved_external_dependency_count >= config.watch_unresolved_dependency_count
        or average_rule_clarity_score <= config.watch_rule_clarity_score
        or max_manual_escalation_urgency_score
        >= config.watch_manual_escalation_urgency_score
        or risk_score >= config.watch_risk_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    unresolved_external_dependency_count: Decimal,
    official_source_freshness_score: Decimal,
    average_rule_clarity_score: Decimal,
    max_manual_escalation_urgency_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketResolutionDependencyRiskConfig,
) -> tuple[str, ...]:
    reason_codes = {f"resolution_dependency_risk_{status}"}
    if unresolved_external_dependency_count > _ZERO:
        reason_codes.add("unresolved_external_dependencies")
    else:
        reason_codes.add("all_external_dependencies_resolved")
    if official_source_freshness_score == _ZERO:
        reason_codes.add("official_source_stale")
    else:
        reason_codes.add("official_source_fresh")
    if average_rule_clarity_score <= config.block_rule_clarity_score:
        reason_codes.add("rule_clarity_block")
    elif average_rule_clarity_score <= config.watch_rule_clarity_score:
        reason_codes.add("rule_clarity_watch")
    else:
        reason_codes.add("rule_clarity_clear")
    if (
        max_manual_escalation_urgency_score
        >= config.block_manual_escalation_urgency_score
    ):
        reason_codes.add("manual_escalation_block")
    elif (
        max_manual_escalation_urgency_score
        >= config.watch_manual_escalation_urgency_score
    ):
        reason_codes.add("manual_escalation_urgent")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _report_status(rows: tuple[ResearchMarketResolutionDependencyRiskRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketResolutionDependencyRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_dependencies",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        allow_empty=False,
    )


def _status_count(
    rows: tuple[ResearchMarketResolutionDependencyRiskRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_dependencies(
    dependencies: Sequence[ResearchMarketResolutionDependencyInput],
) -> tuple[ResearchMarketResolutionDependencyInput, ...]:
    if isinstance(dependencies, (str, bytes)) or not isinstance(dependencies, Sequence):
        raise ValueError("dependencies must be a sequence")
    normalized: list[ResearchMarketResolutionDependencyInput] = []
    for item in dependencies:
        if type(item) is not ResearchMarketResolutionDependencyInput:
            raise ValueError(
                "dependencies must contain ResearchMarketResolutionDependencyInput",
            )
        _require_hard_flags("dependency", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.resolution_group_id,
                item.dependency_id,
                item.official_source_observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchMarketResolutionDependencyRiskRow],
) -> tuple[ResearchMarketResolutionDependencyRiskRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketResolutionDependencyRiskRow] = []
    for row in rows:
        if type(row) is not ResearchMarketResolutionDependencyRiskRow:
            raise ValueError(
                "rows must contain ResearchMarketResolutionDependencyRiskRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.resolution_group_id))


def _validate_row_consistency(row: ResearchMarketResolutionDependencyRiskRow) -> None:
    if row.dependency_count <= _ZERO:
        raise ValueError("dependency_count must be positive")
    if row.unresolved_external_dependency_count > row.dependency_count:
        raise ValueError(
            "unresolved_external_dependency_count must not exceed dependency_count",
        )
    expected_risk_score = _risk_score(
        dependency_count=row.dependency_count,
        unresolved_external_dependency_count=row.unresolved_external_dependency_count,
        official_source_freshness_score=row.official_source_freshness_score,
        average_rule_clarity_score=row.average_rule_clarity_score,
        max_manual_escalation_urgency_score=row.max_manual_escalation_urgency_score,
    )
    if row.risk_score != expected_risk_score:
        raise ValueError("risk_score must match dependency risk components")
    status_reason_code = f"resolution_dependency_risk_{row.status}"
    if status_reason_code not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")


def _validate_report_consistency(
    report: ResearchMarketResolutionDependencyRiskReport,
) -> None:
    if report.group_count != _decimal_count(len(report.rows)):
        raise ValueError("group_count must match rows")
    if report.dependency_count != sum((row.dependency_count for row in report.rows), _ZERO):
        raise ValueError("dependency_count must match rows")
    if report.unresolved_external_dependency_count != sum(
        (row.unresolved_external_dependency_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("unresolved_external_dependency_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("blocked_count must match rows")
    if report.average_official_source_freshness_score != _average(
        tuple(row.official_source_freshness_score for row in report.rows),
    ):
        raise ValueError("average_official_source_freshness_score must match rows")
    if report.average_rule_clarity_score != _average(
        tuple(row.average_rule_clarity_score for row in report.rows),
    ):
        raise ValueError("average_rule_clarity_score must match rows")
    if report.max_manual_escalation_urgency_score != max(
        (row.max_manual_escalation_urgency_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_manual_escalation_urgency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if "://" in value or "?" in value or "@" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_nonempty_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
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


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(
    field_name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
            raise ValueError(f"{field_name} must be lowercase snake_case strings")
        if value not in normalized:
            normalized.append(value)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(normalized))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchMarketResolutionDependencyRiskReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
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
            raise ValueError(f"{current_path} must remain normalized")
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
            raise ValueError(f"{current_path} must remain normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        if "://" in value or "?" in value or "raw-market" in value.lower():
            raise ValueError(f"{current_path} has unsafe public value")
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
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = _report_digest_from_values(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_DEPENDENCY_RISK_CONFIG_VERSION",
    "ResearchMarketResolutionDependencyInput",
    "ResearchMarketResolutionDependencyRiskConfig",
    "ResearchMarketResolutionDependencyRiskReport",
    "ResearchMarketResolutionDependencyRiskRow",
    "build_research_market_resolution_dependency_risk_report",
    "research_market_resolution_dependency_risk_report_payload",
)
