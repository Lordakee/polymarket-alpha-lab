"""Report-only evidence decay reducer for research strategy domain decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_DECISION_EVIDENCE_DECAY_CONFIG_VERSION = (
    "research-strategy-domain-decision-evidence-decay-report-v0"
)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_SECONDS = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "domain_evidence_fresh",
    "evidence_decay_watch",
    "evidence_decay_block",
    "contradiction_pressure_block",
    "source_reliability_block",
)
REPORT_REASON_CODES = (
    "no_domain_evidence_supplied",
    "domain_evidence_decay_clear",
    "evidence_decay_watch_present",
    "evidence_decay_block_present",
)
STATUS_WEIGHT = {
    "block": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "candidate",
    "market",
    "condition",
    "slug",
    "question",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "dsn",
    "postgres://",
    "mysql://",
    "sqlite://",
    "table",
    "token",
    "auth",
    "private_key",
    "wallet",
    "account",
    "order",
    "trade",
    "live",
    "execution",
    "network",
    "database",
    "persist",
    "sizing",
    "recommend",
)
REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "source_domain_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_decay_ratio",
    "min_effective_confidence",
    "max_evidence_age_seconds",
    "min_decision_horizon_seconds",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "evidence_age_seconds",
    "decision_horizon_seconds",
    "evidence_confidence",
    "source_reliability",
    "contradiction_pressure",
    "freshness_score",
    "decay_ratio",
    "effective_confidence",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "domain_key",
    "status",
    "evidence_family",
    *ROW_DECIMAL_PAYLOAD_FIELDS,
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchStrategyDomainDecisionEvidenceDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_DECISION_EVIDENCE_DECAY_CONFIG_VERSION
    )
    max_evidence_age_seconds: Decimal = Decimal("7200.000000")
    watch_decay_ratio_threshold: Decimal = Decimal("0.500000")
    block_decay_ratio_threshold: Decimal = Decimal("0.900000")
    contradiction_block_threshold: Decimal = Decimal("0.800000")
    min_source_reliability: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainDecisionEvidenceDecayConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_DECISION_EVIDENCE_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_positive_seconds(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        for field_name in (
            "watch_decay_ratio_threshold",
            "block_decay_ratio_threshold",
            "contradiction_block_threshold",
            "min_source_reliability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_decay_ratio_threshold < self.watch_decay_ratio_threshold:
            raise ValueError(
                "block_decay_ratio_threshold must be at least watch_decay_ratio_threshold",
            )
        require_paper_only_flags("research strategy domain evidence decay config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainDecisionEvidenceDecayInput:
    domain_key: str
    evidence_family: str
    evidence_observed_at: datetime
    decision_due_at: datetime
    evidence_confidence: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainDecisionEvidenceDecayInput:
            raise ValueError("input must be exact")
        _require_canonical_string("domain_key", self.domain_key)
        _require_canonical_string("evidence_family", self.evidence_family)
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "decision_due_at",
            _as_utc("decision_due_at", self.decision_due_at),
        )
        for field_name in (
            "evidence_confidence",
            "source_reliability",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("research strategy domain evidence decay input", self)
        _reject_unsafe_public_payload("research strategy domain evidence decay input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainDecisionEvidenceDecayRow:
    domain_key: str
    status: str
    evidence_family: str
    evidence_age_seconds: Decimal
    decision_horizon_seconds: Decimal
    evidence_confidence: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    freshness_score: Decimal
    decay_ratio: Decimal
    effective_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainDecisionEvidenceDecayRow:
            raise ValueError("row must be exact")
        _require_canonical_string("domain_key", self.domain_key)
        _require_member("status", self.status, DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES)
        _require_canonical_string("evidence_family", self.evidence_family)
        for field_name in (
            "evidence_age_seconds",
            "decision_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_confidence",
            "source_reliability",
            "contradiction_pressure",
            "freshness_score",
            "decay_ratio",
            "effective_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        require_paper_only_flags("research strategy domain evidence decay row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("research strategy domain evidence decay row", self)


@dataclass(frozen=True)
class ResearchStrategyDomainDecisionEvidenceDecayReport:
    generated_at: datetime
    config_version: str
    source_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_decay_ratio: Decimal
    min_effective_confidence: Decimal
    max_evidence_age_seconds: Decimal
    min_decision_horizon_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyDomainDecisionEvidenceDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyDomainDecisionEvidenceDecayReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_DECISION_EVIDENCE_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_decay_ratio",
            "min_effective_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_age_seconds",
            "min_decision_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("research strategy domain evidence decay report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("research strategy domain evidence decay report", self)
        if self.derived_validation_digest:
            _validate_derived_validation_digest(self)
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )


def build_research_strategy_domain_decision_evidence_decay_report(
    inputs: object,
    *,
    config: ResearchStrategyDomainDecisionEvidenceDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainDecisionEvidenceDecayReport:
    if type(config) is not ResearchStrategyDomainDecisionEvidenceDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainDecisionEvidenceDecayConfig",
        )
    require_paper_only_flags("research strategy domain evidence decay config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at)
                for item in _normalize_inputs(inputs, generated_at)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyDomainDecisionEvidenceDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_domain_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_decay_ratio=_max_ratio(row.decay_ratio for row in rows),
        min_effective_confidence=_min_ratio(row.effective_confidence for row in rows),
        max_evidence_age_seconds=_max_seconds(row.evidence_age_seconds for row in rows),
        min_decision_horizon_seconds=_min_seconds(
            row.decision_horizon_seconds for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_strategy_domain_decision_evidence_decay_report_payload(
    report: ResearchStrategyDomainDecisionEvidenceDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainDecisionEvidenceDecayReport:
        require_paper_only_flags("research strategy domain evidence decay report", report)
        reject_unsafe_surface_fields(
            "research strategy domain evidence decay report",
            report,
        )
        _reject_unsafe_public_payload("research strategy domain evidence decay report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        reject_unsafe_surface_fields(
            "research strategy domain evidence decay payload",
            report,
        )
        _reject_unsafe_public_payload("research strategy domain evidence decay payload", report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyDomainDecisionEvidenceDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    require_paper_only_flags(
        "research strategy domain evidence decay payload",
        _DictFlags(payload),
    )
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


def _normalize_inputs(
    values: object,
    generated_at: datetime,
) -> tuple[ResearchStrategyDomainDecisionEvidenceDecayInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDomainDecisionEvidenceDecayInput:
            raise ValueError(
                "inputs must contain ResearchStrategyDomainDecisionEvidenceDecayInput values",
            )
        require_paper_only_flags("research strategy domain evidence decay input", row)
        if row.domain_key in seen:
            raise ValueError("duplicate domain_key values are not allowed")
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")
        if row.decision_due_at < generated_at:
            raise ValueError("decision_due_at must not be before generated_at")
        seen.add(row.domain_key)
    return rows


def _row_from_input(
    item: ResearchStrategyDomainDecisionEvidenceDecayInput,
    *,
    config: ResearchStrategyDomainDecisionEvidenceDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainDecisionEvidenceDecayRow:
    evidence_age_seconds = _seconds_between(generated_at, item.evidence_observed_at)
    decision_horizon_seconds = _seconds_between(item.decision_due_at, generated_at)
    decay_ratio = _clamp_ratio(
        _ratio(evidence_age_seconds, config.max_evidence_age_seconds),
    )
    freshness_score = _clamp_ratio(ONE - decay_ratio)
    effective_confidence = _quantize_ratio(
        item.evidence_confidence
        * item.source_reliability
        * freshness_score
        * (ONE - item.contradiction_pressure),
    )
    status = _row_status(
        decay_ratio=decay_ratio,
        contradiction_pressure=item.contradiction_pressure,
        source_reliability=item.source_reliability,
        config=config,
    )
    return ResearchStrategyDomainDecisionEvidenceDecayRow(
        domain_key=item.domain_key,
        status=status,
        evidence_family=item.evidence_family,
        evidence_age_seconds=evidence_age_seconds,
        decision_horizon_seconds=decision_horizon_seconds,
        evidence_confidence=item.evidence_confidence,
        source_reliability=item.source_reliability,
        contradiction_pressure=item.contradiction_pressure,
        freshness_score=freshness_score,
        decay_ratio=decay_ratio,
        effective_confidence=effective_confidence,
        reason_codes=_row_reason_codes(
            decay_ratio=decay_ratio,
            contradiction_pressure=item.contradiction_pressure,
            source_reliability=item.source_reliability,
            config=config,
        ),
    )


def _row_status(
    *,
    decay_ratio: Decimal,
    contradiction_pressure: Decimal,
    source_reliability: Decimal,
    config: ResearchStrategyDomainDecisionEvidenceDecayConfig,
) -> str:
    if (
        decay_ratio >= config.block_decay_ratio_threshold
        or contradiction_pressure >= config.contradiction_block_threshold
        or source_reliability < config.min_source_reliability
    ):
        return "block"
    if decay_ratio >= config.watch_decay_ratio_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    decay_ratio: Decimal,
    contradiction_pressure: Decimal,
    source_reliability: Decimal,
    config: ResearchStrategyDomainDecisionEvidenceDecayConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if decay_ratio >= config.block_decay_ratio_threshold:
        codes.append("evidence_decay_block")
    elif decay_ratio >= config.watch_decay_ratio_threshold:
        codes.append("evidence_decay_watch")
    if contradiction_pressure >= config.contradiction_block_threshold:
        codes.append("contradiction_pressure_block")
    if source_reliability < config.min_source_reliability:
        codes.append("source_reliability_block")
    return tuple(code for code in ROW_REASON_CODES if code in codes) or (
        "domain_evidence_fresh",
    )


def _report_status(
    rows: tuple[ResearchStrategyDomainDecisionEvidenceDecayRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainDecisionEvidenceDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_domain_evidence_supplied",)
    if any(row.status == "block" for row in rows):
        return ("evidence_decay_block_present",)
    if any(row.status == "watch" for row in rows):
        return ("evidence_decay_watch_present",)
    return ("domain_evidence_decay_clear",)


def _row_sort_key(
    row: ResearchStrategyDomainDecisionEvidenceDecayRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.decay_ratio,
        row.effective_confidence,
        row.decision_horizon_seconds,
        row.domain_key,
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainDecisionEvidenceDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchStrategyDomainDecisionEvidenceDecayRow) -> None:
    if "domain_evidence_fresh" in row.reason_codes and row.reason_codes != (
        "domain_evidence_fresh",
    ):
        raise ValueError("reason_codes must match status")
    if row.status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_effective_confidence = _quantize_ratio(
        row.evidence_confidence
        * row.source_reliability
        * row.freshness_score
        * (ONE - row.contradiction_pressure),
    )
    if row.effective_confidence != expected_effective_confidence:
        raise ValueError("effective_confidence must match row values")
    if row.freshness_score != _clamp_ratio(ONE - row.decay_ratio):
        raise ValueError("freshness_score must match decay_ratio")


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            "evidence_decay_block",
            "contradiction_pressure_block",
            "source_reliability_block",
        )
        for reason_code in reason_codes
    ):
        return "block"
    if "evidence_decay_watch" in reason_codes:
        return "watch"
    return "pass"


def _validate_report(report: ResearchStrategyDomainDecisionEvidenceDecayReport) -> None:
    if report.source_domain_count != _count(len(report.rows)):
        raise ValueError("source_domain_count must match rows")
    domain_keys = tuple(row.domain_key for row in report.rows)
    if len(set(domain_keys)) != len(domain_keys):
        raise ValueError("duplicate domain_key values are not allowed")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_decay_ratio != _max_ratio(row.decay_ratio for row in report.rows):
        raise ValueError("max_decay_ratio must match rows")
    if report.min_effective_confidence != _min_ratio(
        row.effective_confidence for row in report.rows
    ):
        raise ValueError("min_effective_confidence must match rows")
    if report.max_evidence_age_seconds != _max_seconds(
        row.evidence_age_seconds for row in report.rows
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.min_decision_horizon_seconds != _min_seconds(
        row.decision_horizon_seconds for row in report.rows
    ):
        raise ValueError("min_decision_horizon_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyDomainDecisionEvidenceDecayRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyDomainDecisionEvidenceDecayRow:
            raise ValueError("rows must contain evidence decay row values")
        require_paper_only_flags("research strategy domain evidence decay row", row)
    return rows


def _validate_derived_validation_digest(
    report: ResearchStrategyDomainDecisionEvidenceDecayReport,
) -> None:
    _require_digest_string(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match derived report values")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    generated_at = _require_utc_datetime_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_DECISION_EVIDENCE_DECAY_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    source_domain_count = _require_count_payload_decimal(
        "source_domain_count",
        payload["source_domain_count"],
    )
    pass_count = _require_count_payload_decimal("pass_count", payload["pass_count"])
    watch_count = _require_count_payload_decimal("watch_count", payload["watch_count"])
    block_count = _require_count_payload_decimal("block_count", payload["block_count"])
    max_decay_ratio = _require_ratio_payload_decimal(
        "max_decay_ratio",
        payload["max_decay_ratio"],
    )
    min_effective_confidence = _require_ratio_payload_decimal(
        "min_effective_confidence",
        payload["min_effective_confidence"],
    )
    max_evidence_age_seconds = _require_seconds_payload_decimal(
        "max_evidence_age_seconds",
        payload["max_evidence_age_seconds"],
    )
    min_decision_horizon_seconds = _require_seconds_payload_decimal(
        "min_decision_horizon_seconds",
        payload["min_decision_horizon_seconds"],
    )
    _require_member("status", payload["status"], DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    row_values = tuple(_validate_public_row_payload(row) for row in payload["rows"])
    _require_digest_string("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["derived_validation_digest"] != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload values")
    ResearchStrategyDomainDecisionEvidenceDecayReport(
        generated_at=generated_at,
        config_version=payload["config_version"],
        source_domain_count=source_domain_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_decay_ratio=max_decay_ratio,
        min_effective_confidence=min_effective_confidence,
        max_evidence_age_seconds=max_evidence_age_seconds,
        min_decision_horizon_seconds=min_decision_horizon_seconds,
        status=payload["status"],
        reason_codes=reason_codes,
        rows=tuple(
            ResearchStrategyDomainDecisionEvidenceDecayRow(**row_value)
            for row_value in row_values
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _validate_public_row_payload(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _reject_unknown_payload_keys("row payload", value, ROW_PAYLOAD_KEYS)
    _require_canonical_string("domain_key", value["domain_key"])
    _require_member("status", value["status"], DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES)
    _require_canonical_string("evidence_family", value["evidence_family"])
    evidence_age_seconds = _require_seconds_payload_decimal(
        "evidence_age_seconds",
        value["evidence_age_seconds"],
    )
    decision_horizon_seconds = _require_seconds_payload_decimal(
        "decision_horizon_seconds",
        value["decision_horizon_seconds"],
    )
    evidence_confidence = _require_ratio_payload_decimal(
        "evidence_confidence",
        value["evidence_confidence"],
    )
    source_reliability = _require_ratio_payload_decimal(
        "source_reliability",
        value["source_reliability"],
    )
    contradiction_pressure = _require_ratio_payload_decimal(
        "contradiction_pressure",
        value["contradiction_pressure"],
    )
    freshness_score = _require_ratio_payload_decimal(
        "freshness_score",
        value["freshness_score"],
    )
    decay_ratio = _require_ratio_payload_decimal("decay_ratio", value["decay_ratio"])
    effective_confidence = _require_ratio_payload_decimal(
        "effective_confidence",
        value["effective_confidence"],
    )
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        value["reason_codes"],
        ROW_REASON_CODES,
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    return {
        "domain_key": value["domain_key"],
        "status": value["status"],
        "evidence_family": value["evidence_family"],
        "evidence_age_seconds": evidence_age_seconds,
        "decision_horizon_seconds": decision_horizon_seconds,
        "evidence_confidence": evidence_confidence,
        "source_reliability": source_reliability,
        "contradiction_pressure": contradiction_pressure,
        "freshness_score": freshness_score,
        "decay_ratio": decay_ratio,
        "effective_confidence": effective_confidence,
        "reason_codes": reason_codes,
        "paper_only": value["paper_only"],
        "report_only": value["report_only"],
        "readonly": value["readonly"],
    }


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys:
        raise ValueError(f"{label} must use the public readonly schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _report_derived_validation_digest(
    report: ResearchStrategyDomainDecisionEvidenceDecayReport,
) -> str:
    return _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_domain_count=report.source_domain_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        max_decay_ratio=report.max_decay_ratio,
        min_effective_confidence=report.min_effective_confidence,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        min_decision_horizon_seconds=report.min_decision_horizon_seconds,
        status=report.status,
        reason_codes=report.reason_codes,
        rows=report.rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    return _derived_validation_digest(**unsigned_payload)


def _derived_validation_digest(**values: Any) -> str:
    ready = json_ready_no_floats(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must contain known values")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_ratio(_require_decimal(field_name, value))
    if decimal_value < ZERO_RATIO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_seconds(field_name, value)
    if decimal_value <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_seconds(_require_decimal(field_name, value))
    if decimal_value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_count(_require_decimal(field_name, value))
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_count_payload_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(
        field_name,
        _require_decimal_string(field_name, value),
    )
    _require_canonical_decimal_payload(field_name, value, decimal_value)
    return decimal_value


def _require_ratio_payload_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_ratio(field_name, _require_decimal_string(field_name, value))
    _require_canonical_decimal_payload(field_name, value, decimal_value)
    return decimal_value


def _require_seconds_payload_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_seconds(
        field_name,
        _require_decimal_string(field_name, value),
    )
    _require_canonical_decimal_payload(field_name, value, decimal_value)
    return decimal_value


def _require_canonical_decimal_payload(
    field_name: str,
    value: object,
    decimal_value: Decimal,
) -> None:
    if str(decimal_value) != value:
        raise ValueError(f"{field_name} must use canonical Decimal string values")


def _require_utc_datetime_string(field_name: str, value: object) -> datetime:
    text = _require_canonical_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    utc_value = _as_utc(field_name, parsed)
    if utc_value.isoformat() != text:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return utc_value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT or denominator == ZERO_SECONDS:
        return ZERO_RATIO
    return _quantize_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        return ZERO_RATIO
    if value > ONE:
        return ONE
    return _quantize_ratio(value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    return _normalize_nonnegative_seconds(
        "seconds",
        Decimal(str((later - earlier).total_seconds())),
    )


def _max_ratio(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_RATIO
    return max(items)


def _min_ratio(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_RATIO
    return min(items)


def _max_seconds(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_SECONDS
    return max(items)


def _min_seconds(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_SECONDS
    return min(items)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _quantize_seconds(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANTUM)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_DECISION_EVIDENCE_DECAY_CONFIG_VERSION",
    "DOMAIN_DECISION_EVIDENCE_DECAY_STATUSES",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "UNSAFE_PUBLIC_SURFACE_FRAGMENTS",
    "ResearchStrategyDomainDecisionEvidenceDecayConfig",
    "ResearchStrategyDomainDecisionEvidenceDecayInput",
    "ResearchStrategyDomainDecisionEvidenceDecayReport",
    "ResearchStrategyDomainDecisionEvidenceDecayRow",
    "build_research_strategy_domain_decision_evidence_decay_report",
    "research_strategy_domain_decision_evidence_decay_report_payload",
)
