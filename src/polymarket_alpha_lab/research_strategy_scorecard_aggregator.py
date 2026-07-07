"""Pure report-only strategy scorecard aggregation for manual research screening."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_SCORECARD_AGGREGATOR_CONFIG_VERSION = (
    "research-strategy-scorecard-aggregator-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SCORECARD_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_BLOCK_REASON_CODES = frozenset(
    (
        "research_readiness_block",
        "evidence_package_quality_block",
        "cost_threshold_block",
        "rule_risk_block",
        "team_capacity_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_input",
    "research_readiness_block",
    "evidence_package_quality_block",
    "cost_threshold_block",
    "rule_risk_block",
    "team_capacity_block",
    "research_readiness_watch",
    "evidence_package_quality_watch",
    "cost_threshold_watch",
    "rule_risk_watch",
    "team_capacity_watch",
    "scorecard_pass",
)
_NEXT_STEP_BY_STATUS = {
    "pass": "manual_screening_standard_review",
    "watch": "manual_screening_elevated_review",
    "block": "manual_screening_hold_rework",
}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchStrategyScorecardAggregatorConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_SCORECARD_AGGREGATOR_CONFIG_VERSION
    min_research_readiness_score: Decimal = Decimal("0.550000")
    pass_research_readiness_score: Decimal = Decimal("0.750000")
    min_evidence_package_quality_score: Decimal = Decimal("0.500000")
    pass_evidence_package_quality_score: Decimal = Decimal("0.750000")
    min_cost_threshold_score: Decimal = Decimal("0.450000")
    pass_cost_threshold_score: Decimal = Decimal("0.700000")
    watch_rule_risk_score: Decimal = Decimal("0.400000")
    block_rule_risk_score: Decimal = Decimal("0.800000")
    min_team_capacity_score: Decimal = Decimal("0.350000")
    pass_team_capacity_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyScorecardAggregatorConfig:
            raise TypeError(
                "ResearchStrategyScorecardAggregatorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyScorecardAggregatorConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyScorecardAggregatorConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SCORECARD_AGGREGATOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_research_readiness_score",
            "pass_research_readiness_score",
            "min_evidence_package_quality_score",
            "pass_evidence_package_quality_score",
            "min_cost_threshold_score",
            "pass_cost_threshold_score",
            "watch_rule_risk_score",
            "block_rule_risk_score",
            "min_team_capacity_score",
            "pass_team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_research_readiness_score > self.pass_research_readiness_score:
            raise ValueError("min_research_readiness_score must not exceed pass threshold")
        if (
            self.min_evidence_package_quality_score
            > self.pass_evidence_package_quality_score
        ):
            raise ValueError(
                "min_evidence_package_quality_score must not exceed pass threshold",
            )
        if self.min_cost_threshold_score > self.pass_cost_threshold_score:
            raise ValueError("min_cost_threshold_score must not exceed pass threshold")
        if self.watch_rule_risk_score > self.block_rule_risk_score:
            raise ValueError("watch_rule_risk_score must not exceed block threshold")
        if self.min_team_capacity_score > self.pass_team_capacity_score:
            raise ValueError("min_team_capacity_score must not exceed pass threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyScorecardInput:
    scorecard_item_key: str
    research_readiness_score: Decimal
    evidence_package_quality_score: Decimal
    cost_threshold_score: Decimal
    rule_risk_score: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyScorecardInput:
            raise TypeError("ResearchStrategyScorecardInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyScorecardInput:
            raise ValueError("input must be exactly ResearchStrategyScorecardInput")
        _require_public_identifier("scorecard_item_key", self.scorecard_item_key)
        for field_name in (
            "research_readiness_score",
            "evidence_package_quality_score",
            "cost_threshold_score",
            "rule_risk_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyScorecardPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyScorecardPublicPayloadItem:
            raise TypeError(
                "ResearchStrategyScorecardPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyScorecardPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategyScorecardPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchStrategyScorecardRow:
    scorecard_item_key: str
    research_readiness_score: Decimal
    evidence_package_quality_score: Decimal
    cost_threshold_score: Decimal
    rule_risk_score: Decimal
    rule_clearance_score: Decimal
    team_capacity_score: Decimal
    aggregate_score: Decimal
    manual_screening_priority_score: Decimal
    scorecard_status: str
    human_screening_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyScorecardRow:
            raise TypeError("ResearchStrategyScorecardRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyScorecardRow:
            raise ValueError("row must be exactly ResearchStrategyScorecardRow")
        _require_public_identifier("scorecard_item_key", self.scorecard_item_key)
        for field_name in (
            "research_readiness_score",
            "evidence_package_quality_score",
            "cost_threshold_score",
            "rule_risk_score",
            "rule_clearance_score",
            "team_capacity_score",
            "aggregate_score",
            "manual_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_scorecard_status("scorecard_status", self.scorecard_status)
        if self.human_screening_next_step != _NEXT_STEP_BY_STATUS[self.scorecard_status]:
            raise ValueError("human_screening_next_step must match scorecard_status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyScorecardReport:
    generated_at: datetime
    config_version: str
    scorecard_status: str
    human_screening_next_step: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal | None
    watch_ratio: Decimal | None
    block_ratio: Decimal | None
    average_aggregate_score: Decimal
    max_rule_risk_score: Decimal
    max_manual_screening_priority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyScorecardRow, ...]
    public_payload: tuple[ResearchStrategyScorecardPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyScorecardReport:
            raise TypeError("ResearchStrategyScorecardReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyScorecardReport:
            raise ValueError("report must be exactly ResearchStrategyScorecardReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SCORECARD_AGGREGATOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_scorecard_status("scorecard_status", self.scorecard_status)
        if self.human_screening_next_step != _NEXT_STEP_BY_STATUS[self.scorecard_status]:
            raise ValueError("human_screening_next_step must match scorecard_status")
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_ratio", "watch_ratio", "block_ratio"):
            _require_optional_ratio_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "average_aggregate_score",
            "max_rule_risk_score",
            "max_manual_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_scorecard_aggregator_payload(self)


def build_research_strategy_scorecard_aggregator(
    inputs: Sequence[ResearchStrategyScorecardInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyScorecardAggregatorConfig | None = None,
    public_payload: Sequence[ResearchStrategyScorecardPublicPayloadItem] = (),
) -> ResearchStrategyScorecardReport:
    """Build a deterministic paper-only scorecard for human research screening."""

    if config is None:
        config = ResearchStrategyScorecardAggregatorConfig()
    if type(config) is not ResearchStrategyScorecardAggregatorConfig:
        raise ValueError("config must be a ResearchStrategyScorecardAggregatorConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "scorecard_status": status,
        "human_screening_next_step": _NEXT_STEP_BY_STATUS[status],
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "pass_ratio": _optional_ratio(_status_count(rows, "pass"), len(rows)),
        "watch_ratio": _optional_ratio(_status_count(rows, "watch"), len(rows)),
        "block_ratio": _optional_ratio(_status_count(rows, "block"), len(rows)),
        "average_aggregate_score": _average_ratio(
            tuple(row.aggregate_score for row in rows),
        ),
        "max_rule_risk_score": max((row.rule_risk_score for row in rows), default=_ZERO),
        "max_manual_screening_priority_score": max(
            (row.manual_screening_priority_score for row in rows),
            default=_ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_scorecard_aggregator_payload(
    value: ResearchStrategyScorecardReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyScorecardReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchStrategyScorecardReport or dict")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_flag_downgrades("payload", payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

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
    inputs: tuple[ResearchStrategyScorecardInput, ...],
    config: ResearchStrategyScorecardAggregatorConfig,
) -> tuple[ResearchStrategyScorecardRow, ...]:
    return tuple(sorted((_row_for_input(item, config) for item in inputs), key=_row_sort_key))


def _row_for_input(
    item: ResearchStrategyScorecardInput,
    config: ResearchStrategyScorecardAggregatorConfig,
) -> ResearchStrategyScorecardRow:
    rule_clearance_score = _quantize(_ONE - item.rule_risk_score)
    aggregate_score = _average_ratio(
        (
            item.research_readiness_score,
            item.evidence_package_quality_score,
            item.cost_threshold_score,
            rule_clearance_score,
            item.team_capacity_score,
        ),
    )
    reason_codes = _row_reason_codes(
        research_readiness_score=item.research_readiness_score,
        evidence_package_quality_score=item.evidence_package_quality_score,
        cost_threshold_score=item.cost_threshold_score,
        rule_risk_score=item.rule_risk_score,
        team_capacity_score=item.team_capacity_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchStrategyScorecardRow(
        scorecard_item_key=item.scorecard_item_key,
        research_readiness_score=item.research_readiness_score,
        evidence_package_quality_score=item.evidence_package_quality_score,
        cost_threshold_score=item.cost_threshold_score,
        rule_risk_score=item.rule_risk_score,
        rule_clearance_score=rule_clearance_score,
        team_capacity_score=item.team_capacity_score,
        aggregate_score=aggregate_score,
        manual_screening_priority_score=_manual_screening_priority_score(
            scorecard_status=status,
            research_readiness_score=item.research_readiness_score,
            evidence_package_quality_score=item.evidence_package_quality_score,
            cost_threshold_score=item.cost_threshold_score,
            rule_risk_score=item.rule_risk_score,
            team_capacity_score=item.team_capacity_score,
        ),
        scorecard_status=status,
        human_screening_next_step=_NEXT_STEP_BY_STATUS[status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    research_readiness_score: Decimal,
    evidence_package_quality_score: Decimal,
    cost_threshold_score: Decimal,
    rule_risk_score: Decimal,
    team_capacity_score: Decimal,
    config: ResearchStrategyScorecardAggregatorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if research_readiness_score < config.min_research_readiness_score:
        reason_codes.append("research_readiness_block")
    if evidence_package_quality_score < config.min_evidence_package_quality_score:
        reason_codes.append("evidence_package_quality_block")
    if cost_threshold_score < config.min_cost_threshold_score:
        reason_codes.append("cost_threshold_block")
    if rule_risk_score >= config.block_rule_risk_score:
        reason_codes.append("rule_risk_block")
    if team_capacity_score < config.min_team_capacity_score:
        reason_codes.append("team_capacity_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if research_readiness_score < config.pass_research_readiness_score:
            reason_codes.append("research_readiness_watch")
        if evidence_package_quality_score < config.pass_evidence_package_quality_score:
            reason_codes.append("evidence_package_quality_watch")
        if cost_threshold_score < config.pass_cost_threshold_score:
            reason_codes.append("cost_threshold_watch")
        if rule_risk_score > config.watch_rule_risk_score:
            reason_codes.append("rule_risk_watch")
        if team_capacity_score < config.pass_team_capacity_score:
            reason_codes.append("team_capacity_watch")
    return tuple(reason_codes or ("scorecard_pass",))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("scorecard_pass",):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _manual_screening_priority_score(
    scorecard_status: str,
    *,
    research_readiness_score: Decimal,
    evidence_package_quality_score: Decimal,
    cost_threshold_score: Decimal,
    rule_risk_score: Decimal,
    team_capacity_score: Decimal,
) -> Decimal:
    base_priority = (
        (_ONE - research_readiness_score) * Decimal("0.150000")
        + (_ONE - evidence_package_quality_score) * Decimal("0.200000")
        + (_ONE - cost_threshold_score) * Decimal("0.150000")
        + rule_risk_score * Decimal("0.250000")
        + (_ONE - team_capacity_score) * Decimal("0.250000")
    )
    if scorecard_status == "block":
        return _clamp_ratio(base_priority + Decimal("0.500000"))
    if scorecard_status == "watch":
        return _clamp_ratio(base_priority + Decimal("0.250000"))
    return _clamp_ratio(base_priority)


def _report_status(rows: tuple[ResearchStrategyScorecardRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.scorecard_status == "block" for row in rows):
        return "block"
    if any(row.scorecard_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchStrategyScorecardRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _status_count(rows: tuple[ResearchStrategyScorecardRow, ...], status: str) -> int:
    return len(tuple(row for row in rows if row.scorecard_status == status))


def _validate_row_consistency(row: ResearchStrategyScorecardRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.scorecard_status != expected_status:
        raise ValueError("scorecard_status must match reason_codes")


def _validate_report_consistency(report: ResearchStrategyScorecardReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _optional_ratio(_status_count(report.rows, "pass"), len(report.rows)):
        raise ValueError("pass_ratio must match rows")
    if report.watch_ratio != _optional_ratio(
        _status_count(report.rows, "watch"),
        len(report.rows),
    ):
        raise ValueError("watch_ratio must match rows")
    if report.block_ratio != _optional_ratio(
        _status_count(report.rows, "block"),
        len(report.rows),
    ):
        raise ValueError("block_ratio must match rows")
    expected_average = _average_ratio(tuple(row.aggregate_score for row in report.rows))
    if report.average_aggregate_score != expected_average:
        raise ValueError("average_aggregate_score must match rows")
    expected_max_rule_risk = max((row.rule_risk_score for row in report.rows), default=_ZERO)
    if report.max_rule_risk_score != expected_max_rule_risk:
        raise ValueError("max_rule_risk_score must match rows")
    expected_max_priority = max(
        (row.manual_screening_priority_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_manual_screening_priority_score != expected_max_priority:
        raise ValueError("max_manual_screening_priority_score must match rows")
    if report.scorecard_status != _report_status(report.rows):
        raise ValueError("scorecard_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.human_screening_next_step != _NEXT_STEP_BY_STATUS[report.scorecard_status]:
        raise ValueError("human_screening_next_step must match scorecard_status")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyScorecardInput],
) -> tuple[ResearchStrategyScorecardInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchStrategyScorecardInput:
            raise ValueError("inputs items must be ResearchStrategyScorecardInput")
        _require_hard_flags("input", item)
    item_keys = tuple(item.scorecard_item_key for item in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("scorecard_item_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyScorecardRow, ...],
) -> tuple[ResearchStrategyScorecardRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyScorecardRow:
            raise ValueError("rows items must be ResearchStrategyScorecardRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic scorecard sorting")
    item_keys = tuple(row.scorecard_item_key for row in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("row scorecard_item_key values must be unique")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[ResearchStrategyScorecardPublicPayloadItem],
) -> tuple[ResearchStrategyScorecardPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not ResearchStrategyScorecardPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchStrategyScorecardPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
    keys = tuple(item.key for item in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_payload must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _row_sort_key(row: ResearchStrategyScorecardRow) -> tuple[int, Decimal, str]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_weight[row.scorecard_status],
        -row.manual_screening_priority_score,
        row.scorecard_item_key,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_scorecard_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SCORECARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_optional_ratio_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _optional_ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize(Decimal(numerator) / Decimal(denominator))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    scorecard_status: str,
    human_screening_next_step: str,
    item_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    pass_ratio: Decimal | None,
    watch_ratio: Decimal | None,
    block_ratio: Decimal | None,
    average_aggregate_score: Decimal,
    max_rule_risk_score: Decimal,
    max_manual_screening_priority_score: Decimal,
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchStrategyScorecardRow, ...],
    public_payload: tuple[ResearchStrategyScorecardPublicPayloadItem, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "scorecard_status": scorecard_status,
        "human_screening_next_step": human_screening_next_step,
        "item_count": _json_ready(item_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "pass_ratio": _json_ready(pass_ratio),
        "watch_ratio": _json_ready(watch_ratio),
        "block_ratio": _json_ready(block_ratio),
        "average_aggregate_score": _json_ready(average_aggregate_score),
        "max_rule_risk_score": _json_ready(max_rule_risk_score),
        "max_manual_screening_priority_score": _json_ready(
            max_manual_screening_priority_score,
        ),
        "reason_codes": list(reason_codes),
        "rows": [_row_payload(row) for row in rows],
        "public_payload": [_public_payload_item_payload(item) for item in public_payload],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: ResearchStrategyScorecardRow) -> dict[str, object]:
    return {
        "scorecard_item_key": row.scorecard_item_key,
        "research_readiness_score": _json_ready(row.research_readiness_score),
        "evidence_package_quality_score": _json_ready(
            row.evidence_package_quality_score,
        ),
        "cost_threshold_score": _json_ready(row.cost_threshold_score),
        "rule_risk_score": _json_ready(row.rule_risk_score),
        "rule_clearance_score": _json_ready(row.rule_clearance_score),
        "team_capacity_score": _json_ready(row.team_capacity_score),
        "aggregate_score": _json_ready(row.aggregate_score),
        "manual_screening_priority_score": _json_ready(
            row.manual_screening_priority_score,
        ),
        "scorecard_status": row.scorecard_status,
        "human_screening_next_step": row.human_screening_next_step,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_payload_item_payload(
    item: ResearchStrategyScorecardPublicPayloadItem,
) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(report: ResearchStrategyScorecardReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        scorecard_status=report.scorecard_status,
        human_screening_next_step=report.human_screening_next_step,
        item_count=report.item_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        pass_ratio=report.pass_ratio,
        watch_ratio=report.watch_ratio,
        block_ratio=report.block_ratio,
        average_aggregate_score=report.average_aggregate_score,
        max_rule_risk_score=report.max_rule_risk_score,
        max_manual_screening_priority_score=(
            report.max_manual_screening_priority_score
        ),
        reason_codes=report.reason_codes,
        rows=report.rows,
        public_payload=report.public_payload,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: ResearchStrategyScorecardReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "scorecard_status": report.scorecard_status,
            "human_screening_next_step": report.human_screening_next_step,
            "item_count": report.item_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "pass_ratio": report.pass_ratio,
            "watch_ratio": report.watch_ratio,
            "block_ratio": report.block_ratio,
            "average_aggregate_score": report.average_aggregate_score,
            "max_rule_risk_score": report.max_rule_risk_score,
            "max_manual_screening_priority_score": (
                report.max_manual_screening_priority_score
            ),
            "reason_codes": report.reason_codes,
            "rows": report.rows,
            "public_payload": report.public_payload,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        scorecard_status=_require_mapping_value(values, "scorecard_status", str),
        human_screening_next_step=_require_mapping_value(
            values,
            "human_screening_next_step",
            str,
        ),
        item_count=_require_mapping_value(values, "item_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        pass_ratio=_require_optional_mapping_value(values, "pass_ratio", Decimal),
        watch_ratio=_require_optional_mapping_value(values, "watch_ratio", Decimal),
        block_ratio=_require_optional_mapping_value(values, "block_ratio", Decimal),
        average_aggregate_score=_require_mapping_value(
            values,
            "average_aggregate_score",
            Decimal,
        ),
        max_rule_risk_score=_require_mapping_value(
            values,
            "max_rule_risk_score",
            Decimal,
        ),
        max_manual_screening_priority_score=_require_mapping_value(
            values,
            "max_manual_screening_priority_score",
            Decimal,
        ),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        rows=_require_mapping_value(values, "rows", tuple),
        public_payload=_require_mapping_value(values, "public_payload", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _require_optional_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if value is None:
        return None
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__} or None")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchStrategyScorecardReport:
        return _report_payload(value)
    if type(value) is ResearchStrategyScorecardRow:
        return _row_payload(value)
    if type(value) is ResearchStrategyScorecardPublicPayloadItem:
        return _public_payload_item_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload value is not supported")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SCORECARD_AGGREGATOR_CONFIG_VERSION",
    "ResearchStrategyScorecardAggregatorConfig",
    "ResearchStrategyScorecardInput",
    "ResearchStrategyScorecardPublicPayloadItem",
    "ResearchStrategyScorecardReport",
    "ResearchStrategyScorecardRow",
    "build_research_strategy_scorecard_aggregator",
    "research_strategy_scorecard_aggregator_payload",
)
