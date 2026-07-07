"""Pure report-only strategy risk register for manual research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_RISK_REGISTER_CONFIG_VERSION = (
    "research-strategy-risk-register-v0"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_SCORE_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_REGISTER_STATUSES = ("pass", "watch", "block")
_ROW_REASON_CODES = (
    "strategy_risk_register_entry_pass",
    "rule_risk_block",
    "evidence_source_risk_block",
    "cost_risk_block",
    "team_capacity_risk_block",
    "composite_risk_block",
    "rule_risk_watch",
    "evidence_source_risk_watch",
    "cost_risk_watch",
    "team_capacity_risk_watch",
    "composite_risk_watch",
)
_REPORT_REASON_CODES = (
    "strategy_risk_register_entries_pass",
    "strategy_risk_register_entries_watch",
    "strategy_risk_register_entries_block",
    "strategy_risk_register_no_entries_block",
    "rule_risk_block",
    "evidence_source_risk_block",
    "cost_risk_block",
    "team_capacity_risk_block",
    "rule_risk_watch",
    "evidence_source_risk_watch",
    "cost_risk_watch",
    "team_capacity_risk_watch",
)
_BLOCK_REASON_CODES = (
    "rule_risk_block",
    "evidence_source_risk_block",
    "cost_risk_block",
    "team_capacity_risk_block",
    "composite_risk_block",
)
_WATCH_REASON_CODES = (
    "rule_risk_watch",
    "evidence_source_risk_watch",
    "cost_risk_watch",
    "team_capacity_risk_watch",
    "composite_risk_watch",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "http://",
    "https://",
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
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RISK_REGISTER_CONFIG_VERSION",
    "ResearchStrategyRiskRegisterConfig",
    "ResearchStrategyRiskRegisterObservation",
    "ResearchStrategyRiskRegisterRow",
    "ResearchStrategyRiskRegisterReasonCodeCount",
    "ResearchStrategyRiskRegisterReport",
    "build_research_strategy_risk_register",
    "research_strategy_risk_register_payload",
)


@dataclass(frozen=True)
class ResearchStrategyRiskRegisterConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_RISK_REGISTER_CONFIG_VERSION
    watch_rule_risk_score: Decimal = Decimal("0.300000")
    block_rule_risk_score: Decimal = Decimal("0.700000")
    watch_evidence_source_risk_score: Decimal = Decimal("0.300000")
    block_evidence_source_risk_score: Decimal = Decimal("0.700000")
    watch_cost_risk_score: Decimal = Decimal("0.300000")
    block_cost_risk_score: Decimal = Decimal("0.700000")
    watch_team_capacity_risk_score: Decimal = Decimal("0.300000")
    block_team_capacity_risk_score: Decimal = Decimal("0.700000")
    watch_composite_risk_score: Decimal = Decimal("0.250000")
    block_composite_risk_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskRegisterConfig:
            raise ValueError("config must be exactly ResearchStrategyRiskRegisterConfig")
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_RISK_REGISTER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_rule_risk_score",
            "block_rule_risk_score",
            "watch_evidence_source_risk_score",
            "block_evidence_source_risk_score",
            "watch_cost_risk_score",
            "block_cost_risk_score",
            "watch_team_capacity_risk_score",
            "block_team_capacity_risk_score",
            "watch_composite_risk_score",
            "block_composite_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_threshold_pair(
            "rule_risk_score",
            self.watch_rule_risk_score,
            self.block_rule_risk_score,
        )
        _validate_threshold_pair(
            "evidence_source_risk_score",
            self.watch_evidence_source_risk_score,
            self.block_evidence_source_risk_score,
        )
        _validate_threshold_pair(
            "cost_risk_score",
            self.watch_cost_risk_score,
            self.block_cost_risk_score,
        )
        _validate_threshold_pair(
            "team_capacity_risk_score",
            self.watch_team_capacity_risk_score,
            self.block_team_capacity_risk_score,
        )
        _validate_threshold_pair(
            "composite_risk_score",
            self.watch_composite_risk_score,
            self.block_composite_risk_score,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskRegisterConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskRegisterObservation:
    rule_risk_score: Decimal
    evidence_source_risk_score: Decimal
    cost_risk_score: Decimal
    team_capacity_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskRegisterObservation:
            raise ValueError(
                "observation must be exactly ResearchStrategyRiskRegisterObservation",
            )
        _require_hard_flags(self)
        for field_name in (
            "rule_risk_score",
            "evidence_source_risk_score",
            "cost_risk_score",
            "team_capacity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskRegisterObservation",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskRegisterRow:
    risk_status: str
    rule_risk_score: Decimal
    evidence_source_risk_score: Decimal
    cost_risk_score: Decimal
    team_capacity_risk_score: Decimal
    composite_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskRegisterRow:
            raise ValueError("row must be exactly ResearchStrategyRiskRegisterRow")
        _require_hard_flags(self)
        _require_status("risk_status", self.risk_status)
        for field_name in (
            "rule_risk_score",
            "evidence_source_risk_score",
            "cost_risk_score",
            "team_capacity_risk_score",
            "composite_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row(self)
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskRegisterRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskRegisterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskRegisterReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchStrategyRiskRegisterReasonCodeCount",
            )
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _normalize_positive_integral_decimal("count", self.count),
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskRegisterReasonCodeCount",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskRegisterReport:
    generated_at: datetime
    config_version: str
    register_status: str
    entry_count: Decimal
    pass_entry_count: Decimal
    watch_entry_count: Decimal
    block_entry_count: Decimal
    average_rule_risk_score: Decimal
    average_evidence_source_risk_score: Decimal
    average_cost_risk_score: Decimal
    average_team_capacity_risk_score: Decimal
    average_composite_risk_score: Decimal
    max_rule_risk_score: Decimal
    max_evidence_source_risk_score: Decimal
    max_cost_risk_score: Decimal
    max_team_capacity_risk_score: Decimal
    max_composite_risk_score: Decimal
    rows: tuple[ResearchStrategyRiskRegisterRow, ...]
    reason_code_counts: tuple[ResearchStrategyRiskRegisterReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    risk_summary: tuple[str, ...]
    risk_summary_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskRegisterReport:
            raise ValueError("report must be exactly ResearchStrategyRiskRegisterReport")
        _require_hard_flags(self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_RISK_REGISTER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("register_status", self.register_status)
        for field_name in (
            "entry_count",
            "pass_entry_count",
            "watch_entry_count",
            "block_entry_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_rule_risk_score",
            "average_evidence_source_risk_score",
            "average_cost_risk_score",
            "average_team_capacity_risk_score",
            "average_composite_risk_score",
            "max_rule_risk_score",
            "max_evidence_source_risk_score",
            "max_cost_risk_score",
            "max_team_capacity_risk_score",
            "max_composite_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "risk_summary",
            _normalize_risk_summary(self.risk_summary),
        )
        _require_sha256_digest("risk_summary_digest", self.risk_summary_digest)
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskRegisterReport",
            _payload_value(asdict(self)),
        )
        if self.risk_summary_digest != _risk_summary_digest(asdict(self)):
            raise ValueError("risk_summary_digest mismatch")
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskRegisterReport.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_risk_register(
    observations: object,
    *,
    config: ResearchStrategyRiskRegisterConfig,
    generated_at: datetime,
) -> ResearchStrategyRiskRegisterReport:
    if type(config) is not ResearchStrategyRiskRegisterConfig:
        raise ValueError("config must be exactly ResearchStrategyRiskRegisterConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _sort_rows(
        tuple(_row_for_observation(observation, config) for observation in normalized_observations),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(reason_codes, rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "register_status": _register_status(rows),
        "entry_count": _count(len(rows)),
        "pass_entry_count": _status_count(rows, "pass"),
        "watch_entry_count": _status_count(rows, "watch"),
        "block_entry_count": _status_count(rows, "block"),
        "average_rule_risk_score": _average(rows, "rule_risk_score"),
        "average_evidence_source_risk_score": _average(
            rows,
            "evidence_source_risk_score",
        ),
        "average_cost_risk_score": _average(rows, "cost_risk_score"),
        "average_team_capacity_risk_score": _average(
            rows,
            "team_capacity_risk_score",
        ),
        "average_composite_risk_score": _average(rows, "composite_risk_score"),
        "max_rule_risk_score": _maximum(rows, "rule_risk_score"),
        "max_evidence_source_risk_score": _maximum(
            rows,
            "evidence_source_risk_score",
        ),
        "max_cost_risk_score": _maximum(rows, "cost_risk_score"),
        "max_team_capacity_risk_score": _maximum(rows, "team_capacity_risk_score"),
        "max_composite_risk_score": _maximum(rows, "composite_risk_score"),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["risk_summary"] = _risk_summary(values)
    values["risk_summary_digest"] = _risk_summary_digest(values)
    return ResearchStrategyRiskRegisterReport(**values)


def research_strategy_risk_register_payload(
    report: object,
) -> dict[str, object]:
    if type(report) is not ResearchStrategyRiskRegisterReport:
        raise ValueError("report must be exactly ResearchStrategyRiskRegisterReport")
    return report.payload


def _row_for_observation(
    observation: ResearchStrategyRiskRegisterObservation,
    config: ResearchStrategyRiskRegisterConfig,
) -> ResearchStrategyRiskRegisterRow:
    composite = _composite_risk_score(observation)
    reason_codes = _row_reason_codes(observation, composite, config)
    return ResearchStrategyRiskRegisterRow(
        risk_status=_row_status(reason_codes),
        rule_risk_score=observation.rule_risk_score,
        evidence_source_risk_score=observation.evidence_source_risk_score,
        cost_risk_score=observation.cost_risk_score,
        team_capacity_risk_score=observation.team_capacity_risk_score,
        composite_risk_score=composite,
        reason_codes=reason_codes,
    )


def _composite_risk_score(observation: ResearchStrategyRiskRegisterObservation) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (
            (
                observation.rule_risk_score
                + observation.evidence_source_risk_score
                + observation.cost_risk_score
                + observation.team_capacity_risk_score
            )
            / Decimal("4")
        ).quantize(_SCORE_QUANT)


def _row_reason_codes(
    observation: ResearchStrategyRiskRegisterObservation,
    composite_risk_score: Decimal,
    config: ResearchStrategyRiskRegisterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.rule_risk_score >= config.block_rule_risk_score:
        reasons.append("rule_risk_block")
    if observation.evidence_source_risk_score >= config.block_evidence_source_risk_score:
        reasons.append("evidence_source_risk_block")
    if observation.cost_risk_score >= config.block_cost_risk_score:
        reasons.append("cost_risk_block")
    if observation.team_capacity_risk_score >= config.block_team_capacity_risk_score:
        reasons.append("team_capacity_risk_block")
    if composite_risk_score >= config.block_composite_risk_score:
        reasons.append("composite_risk_block")
    if reasons:
        return tuple(reasons)
    if observation.rule_risk_score >= config.watch_rule_risk_score:
        reasons.append("rule_risk_watch")
    if observation.evidence_source_risk_score >= config.watch_evidence_source_risk_score:
        reasons.append("evidence_source_risk_watch")
    if observation.cost_risk_score >= config.watch_cost_risk_score:
        reasons.append("cost_risk_watch")
    if observation.team_capacity_risk_score >= config.watch_team_capacity_risk_score:
        reasons.append("team_capacity_risk_watch")
    if composite_risk_score >= config.watch_composite_risk_score:
        reasons.append("composite_risk_watch")
    if reasons:
        return tuple(reasons)
    return ("strategy_risk_register_entry_pass",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _register_status(rows: tuple[ResearchStrategyRiskRegisterRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.risk_status == "block" for row in rows):
        return "block"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyRiskRegisterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_risk_register_no_entries_block",)
    included: list[str] = []
    status = _register_status(rows)
    if status == "block":
        included.append("strategy_risk_register_entries_block")
    elif status == "watch":
        included.append("strategy_risk_register_entries_watch")
    else:
        included.append("strategy_risk_register_entries_pass")
    row_reasons = tuple(reason for row in rows for reason in row.reason_codes)
    for reason in _REPORT_REASON_CODES[4:]:
        if reason in row_reasons:
            included.append(reason)
    return tuple(included)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchStrategyRiskRegisterRow, ...],
) -> tuple[ResearchStrategyRiskRegisterReasonCodeCount, ...]:
    row_reasons = tuple(reason for row in rows for reason in row.reason_codes)
    counts: list[ResearchStrategyRiskRegisterReasonCodeCount] = []
    for reason in reason_codes:
        if reason.startswith("strategy_risk_register_entries"):
            count = _count(
                sum(1 for row in rows if row.risk_status == _status_from_report_reason(reason)),
            )
        elif reason == "strategy_risk_register_no_entries_block":
            count = _count(1)
        else:
            count = _count(sum(1 for row_reason in row_reasons if row_reason == reason))
        counts.append(ResearchStrategyRiskRegisterReasonCodeCount(reason, count))
    return tuple(counts)


def _status_from_report_reason(reason_code: str) -> str:
    if reason_code == "strategy_risk_register_entries_block":
        return "block"
    if reason_code == "strategy_risk_register_entries_watch":
        return "watch"
    return "pass"


def _sort_rows(
    rows: tuple[ResearchStrategyRiskRegisterRow, ...],
) -> tuple[ResearchStrategyRiskRegisterRow, ...]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_rank[row.risk_status],
                -row.composite_risk_score,
                -row.rule_risk_score,
                -row.evidence_source_risk_score,
                -row.cost_risk_score,
                -row.team_capacity_risk_score,
            ),
        ),
    )


def _risk_summary(values: dict[str, object]) -> tuple[str, ...]:
    reason_code_counts = values["reason_code_counts"]
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    summary = [
        f"register_status={values['register_status']}",
        f"entry_count={values['entry_count']}",
        f"block_entry_count={values['block_entry_count']}",
        f"watch_entry_count={values['watch_entry_count']}",
        f"pass_entry_count={values['pass_entry_count']}",
        f"average_composite_risk_score={values['average_composite_risk_score']}",
        f"max_composite_risk_score={values['max_composite_risk_score']}",
    ]
    for row in reason_code_counts:
        if type(row) is not ResearchStrategyRiskRegisterReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        summary.append(f"reason={row.reason_code} count={row.count}")
    return tuple(summary)


def _risk_summary_digest(value: object) -> str:
    payload = _payload_value(_without_digest(value))
    _reject_unsafe_public_payload("risk_summary_digest", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _without_digest(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_digest(item)
            for key, item in value.items()
            if key != "risk_summary_digest"
        }
    if isinstance(value, tuple):
        return tuple(_without_digest(item) for item in value)
    if isinstance(value, list):
        return [_without_digest(item) for item in value]
    return value


def _normalize_observations(
    observations: object,
) -> tuple[ResearchStrategyRiskRegisterObservation, ...]:
    if isinstance(observations, (str, bytes)) or not hasattr(observations, "__iter__"):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchStrategyRiskRegisterObservation:
            raise ValueError(
                "observations must contain ResearchStrategyRiskRegisterObservation values",
            )
        _require_hard_flags(item)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyRiskRegisterRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyRiskRegisterRow:
            raise ValueError("rows must contain ResearchStrategyRiskRegisterRow values")
        _require_hard_flags(row)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchStrategyRiskRegisterReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchStrategyRiskRegisterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyRiskRegisterReasonCodeCount values",
            )
        _require_hard_flags(value)
    if len({value.reason_code for value in values}) != len(values):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        reason = _require_canonical_string(field_name, value)
        if reason not in allowed:
            raise ValueError(f"{field_name} contains unknown reason code")
        if reason not in normalized:
            normalized.append(reason)
    return tuple(normalized)


def _normalize_risk_summary(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("risk_summary must be a tuple")
    if not values:
        raise ValueError("risk_summary must not be empty")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_canonical_string("risk_summary", value))
    return tuple(normalized)


def _validate_row(row: ResearchStrategyRiskRegisterRow) -> None:
    expected_composite = (
        (
            row.rule_risk_score
            + row.evidence_source_risk_score
            + row.cost_risk_score
            + row.team_capacity_risk_score
        )
        / Decimal("4")
    ).quantize(_SCORE_QUANT)
    if row.composite_risk_score != expected_composite:
        raise ValueError("composite_risk_score must match component risk scores")
    if row.risk_status != _row_status(row.reason_codes):
        raise ValueError("risk_status must match reason_codes")
    if row.risk_status == "pass" and row.reason_codes != (
        "strategy_risk_register_entry_pass",
    ):
        raise ValueError("pass rows must use the pass reason code")
    if row.risk_status != "pass" and "strategy_risk_register_entry_pass" in row.reason_codes:
        raise ValueError("non-pass rows must not use the pass reason code")


def _validate_report(report: ResearchStrategyRiskRegisterReport) -> None:
    rows = report.rows
    if report.register_status != _register_status(rows):
        raise ValueError("register_status must match rows")
    if report.entry_count != _count(len(rows)):
        raise ValueError("entry_count must match rows")
    if report.pass_entry_count != _status_count(rows, "pass"):
        raise ValueError("pass_entry_count must match rows")
    if report.watch_entry_count != _status_count(rows, "watch"):
        raise ValueError("watch_entry_count must match rows")
    if report.block_entry_count != _status_count(rows, "block"):
        raise ValueError("block_entry_count must match rows")
    if (
        report.pass_entry_count + report.watch_entry_count + report.block_entry_count
        != report.entry_count
    ):
        raise ValueError("entry status counts must sum to entry_count")
    for field_name in (
        "rule_risk_score",
        "evidence_source_risk_score",
        "cost_risk_score",
        "team_capacity_risk_score",
        "composite_risk_score",
    ):
        average_name = f"average_{field_name}"
        max_name = f"max_{field_name}"
        if getattr(report, average_name) != _average(rows, field_name):
            raise ValueError(f"{average_name} must match rows")
        if getattr(report, max_name) != _maximum(rows, field_name):
            raise ValueError(f"{max_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match reason_codes")
    expected_summary = _risk_summary(
        {
            "register_status": report.register_status,
            "entry_count": report.entry_count,
            "block_entry_count": report.block_entry_count,
            "watch_entry_count": report.watch_entry_count,
            "pass_entry_count": report.pass_entry_count,
            "average_composite_risk_score": report.average_composite_risk_score,
            "max_composite_risk_score": report.max_composite_risk_score,
            "reason_code_counts": report.reason_code_counts,
        },
    )
    if report.risk_summary != expected_summary:
        raise ValueError("risk_summary must match report values")


def _validate_threshold_pair(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if watch_value >= block_value:
        raise ValueError(f"watch_{field_name} must be below block_{field_name}")


def _status_count(
    rows: tuple[ResearchStrategyRiskRegisterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.risk_status == status))


def _average(
    rows: tuple[ResearchStrategyRiskRegisterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (
            sum((getattr(row, field_name) for row in rows), _ZERO)
            / Decimal(len(rows))
        ).quantize(_SCORE_QUANT)


def _maximum(
    rows: tuple[ResearchStrategyRiskRegisterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if value not in _REGISTER_STATUSES:
        raise ValueError(f"{field_name} must be one of {_REGISTER_STATUSES}")


def _require_reason_code(field_name: str, value: object) -> str:
    reason = _require_canonical_string(field_name, value)
    if reason not in _ROW_REASON_CODES and reason not in _REPORT_REASON_CODES:
        raise ValueError(f"{field_name} contains unknown reason code")
    return reason


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SCORE_QUANT)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized.quantize(_COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be > 0")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    for char in value:
        if char not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be lowercase hex")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _mentions_unsafe_public_text(str(key)):
                raise ValueError(f"{label} unsafe public key: {key}")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, str) and _mentions_unsafe_public_text(value):
        raise ValueError(f"{label} unsafe public value")


def _mentions_unsafe_public_text(value: str) -> bool:
    folded = value.lower()
    return any(fragment in folded for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS)
