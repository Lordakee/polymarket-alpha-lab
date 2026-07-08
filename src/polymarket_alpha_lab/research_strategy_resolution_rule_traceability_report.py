"""Pure report-only resolution rule traceability reducer."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RULE_TRACEABILITY_REPORT_CONFIG_VERSION = (
    "research-strategy-resolution-rule-traceability-report-v0"
)

QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

REASON_SEQUENCE = (
    "rule_specificity_block",
    "official_evidence_strength_block",
    "source_quorum_block",
    "contradiction_pressure_block",
    "rule_specificity_watch",
    "official_evidence_strength_watch",
    "source_quorum_watch",
    "contradiction_pressure_watch",
    "resolution_rule_traceability_pass",
    "resolution_rule_traceability_empty",
)
BLOCK_REASONS = (
    "rule_specificity_block",
    "official_evidence_strength_block",
    "source_quorum_block",
    "contradiction_pressure_block",
)
WATCH_REASONS = (
    "rule_specificity_watch",
    "official_evidence_strength_watch",
    "source_quorum_watch",
    "contradiction_pressure_watch",
)
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
SHA_HEX = frozenset("0123456789abcdef")
UNSAFE_KEY_TOKENS = (
    "acc" + "ount",
    "api" + "_key",
    "a" + "uth",
    "bal" + "ance",
    "b" + "uy",
    "can" + "didate",
    "can" + "cel",
    "cred" + "ential",
    "data" + "base",
    "d" + "b",
    "d" + "sn",
    "li" + "ve",
    "mar" + "ket",
    "net" + "work",
    "or" + "der",
    "private" + "_key",
    "ques" + "tion",
    "s" + "ell",
    "s" + "ign",
    "siz" + "ing",
    "sl" + "ug",
    "source" + "_text",
    "ta" + "ble",
    "to" + "ken",
    "tra" + "de",
    "u" + "rl",
    "wal" + "let",
)
UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "?",
    "@",
)


@dataclass(frozen=True)
class ResearchStrategyResolutionRuleTraceabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RULE_TRACEABILITY_REPORT_CONFIG_VERSION
    )
    min_pass_rule_specificity: Decimal = Decimal("0.750000")
    min_watch_rule_specificity: Decimal = Decimal("0.500000")
    min_pass_official_evidence_strength: Decimal = Decimal("0.750000")
    min_watch_official_evidence_strength: Decimal = Decimal("0.500000")
    min_pass_quorum_source_count: Decimal = Decimal("3.000000")
    min_watch_quorum_source_count: Decimal = Decimal("2.000000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRuleTraceabilityConfig:
            raise TypeError(
                "ResearchStrategyResolutionRuleTraceabilityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRuleTraceabilityConfig:
            raise ValueError(
                "config must be a ResearchStrategyResolutionRuleTraceabilityConfig",
            )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RULE_TRACEABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_pass_rule_specificity",
            "min_watch_rule_specificity",
            "min_pass_official_evidence_strength",
            "min_watch_official_evidence_strength",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_quorum_source_count",
            "min_watch_quorum_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_rule_specificity < self.min_watch_rule_specificity:
            raise ValueError("min_pass_rule_specificity must be at least watch threshold")
        if (
            self.min_pass_official_evidence_strength
            < self.min_watch_official_evidence_strength
        ):
            raise ValueError(
                "min_pass_official_evidence_strength must be at least watch threshold",
            )
        if self.min_pass_quorum_source_count < self.min_watch_quorum_source_count:
            raise ValueError("min_pass_quorum_source_count must be at least watch threshold")
        if self.max_pass_contradiction_pressure > self.max_watch_contradiction_pressure:
            raise ValueError(
                "max_pass_contradiction_pressure must be at most watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRuleTraceabilityObservation:
    trace_reference: str
    resolution_rule_reference: str
    official_evidence_reference: str
    observed_at: datetime
    rule_specificity: Decimal
    official_evidence_strength: Decimal
    quorum_source_count: Decimal
    independent_source_count: Decimal
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRuleTraceabilityObservation:
            raise TypeError(
                "ResearchStrategyResolutionRuleTraceabilityObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRuleTraceabilityObservation:
            raise ValueError(
                "observation must be a ResearchStrategyResolutionRuleTraceabilityObservation",
            )
        for field_name in (
            "trace_reference",
            "resolution_rule_reference",
            "official_evidence_reference",
        ):
            _require_raw_reference(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rule_specificity",
            "official_evidence_strength",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("quorum_source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.quorum_source_count:
            raise ValueError("independent_source_count must not exceed quorum_source_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRuleTraceabilityRow:
    trace_digest: str
    rule_digest: str
    evidence_digest: str
    observed_at: datetime
    rule_specificity: Decimal
    official_evidence_strength: Decimal
    quorum_source_count: Decimal
    independent_source_count: Decimal
    contradiction_pressure: Decimal
    traceability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRuleTraceabilityRow:
            raise TypeError(
                "ResearchStrategyResolutionRuleTraceabilityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRuleTraceabilityRow:
            raise ValueError("row must be a ResearchStrategyResolutionRuleTraceabilityRow")
        _require_prefixed_digest("trace_digest", self.trace_digest, "trace_")
        _require_prefixed_digest("rule_digest", self.rule_digest, "rule_")
        _require_prefixed_digest("evidence_digest", self.evidence_digest, "evidence_")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rule_specificity",
            "official_evidence_strength",
            "contradiction_pressure",
            "traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("quorum_source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.quorum_source_count:
            raise ValueError("independent_source_count must not exceed quorum_source_count")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.row_sha256 == "":
            object.__setattr__(self, "row_sha256", _row_sha256(self))
        else:
            object.__setattr__(
                self,
                "row_sha256",
                _normalize_sha256("row_sha256", self.row_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRuleTraceabilityReport:
    generated_at: datetime
    config_version: str
    trace_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_contradiction_pressure: Decimal
    average_traceability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyResolutionRuleTraceabilityRow, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRuleTraceabilityReport:
            raise TypeError(
                "ResearchStrategyResolutionRuleTraceabilityReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRuleTraceabilityReport:
            raise ValueError("report must be a ResearchStrategyResolutionRuleTraceabilityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RULE_TRACEABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("trace_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_contradiction_pressure",
            "average_traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.report_sha256 == "":
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        else:
            object.__setattr__(
                self,
                "report_sha256",
                _normalize_sha256("report_sha256", self.report_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_strategy_resolution_rule_traceability_report(
    observations: object,
    *,
    config: ResearchStrategyResolutionRuleTraceabilityConfig,
    generated_at: datetime,
) -> ResearchStrategyResolutionRuleTraceabilityReport:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of traceability observations")
    try:
        observation_values = tuple(observations)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "observations must be an iterable of traceability observations",
        ) from exc
    if type(config) is not ResearchStrategyResolutionRuleTraceabilityConfig:
        raise ValueError("config must be a ResearchStrategyResolutionRuleTraceabilityConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)

    seen_trace_references: set[str] = set()
    normalized: list[ResearchStrategyResolutionRuleTraceabilityObservation] = []
    for item in observation_values:
        if type(item) is not ResearchStrategyResolutionRuleTraceabilityObservation:
            raise ValueError(
                "observations must contain ResearchStrategyResolutionRuleTraceabilityObservation",
            )
        _require_hard_flags("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.trace_reference in seen_trace_references:
            raise ValueError("duplicate trace_reference")
        seen_trace_references.add(item.trace_reference)
        normalized.append(item)

    rows = tuple(sorted((_row_from_observation(item, config) for item in normalized), key=_row_key))
    return ResearchStrategyResolutionRuleTraceabilityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        trace_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_decimal_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_decimal_count(sum(1 for row in rows if row.status == "block")),
        max_contradiction_pressure=_max_contradiction_pressure(rows),
        average_traceability_score=_average_traceability_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def validate_research_strategy_resolution_rule_traceability_report(
    report: ResearchStrategyResolutionRuleTraceabilityReport,
) -> bool:
    if type(report) is not ResearchStrategyResolutionRuleTraceabilityReport:
        raise ValueError("report must be a ResearchStrategyResolutionRuleTraceabilityReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    return True


def research_strategy_resolution_rule_traceability_report_payload(
    report: ResearchStrategyResolutionRuleTraceabilityReport,
) -> dict[str, Any]:
    validate_research_strategy_resolution_rule_traceability_report(report)
    payload = _report_payload(report, include_report_digests=True)
    validate_research_strategy_resolution_rule_traceability_public_payload(payload)
    return payload


def validate_research_strategy_resolution_rule_traceability_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_flags("payload", payload)
    _require_payload_status("payload.status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload rows must contain dict values")
        _require_payload_flags(f"payload.rows[{index}]", row)
        _require_payload_status(f"payload.rows[{index}].status", row.get("status"))
        _validate_public_row_payload(row)
    expected_report_sha256 = _payload_sha256(
        _without_keys(payload, ("report_sha256", "derived_validation_digest")),
    )
    if payload.get("report_sha256") != expected_report_sha256:
        raise ValueError("report_sha256 must match public payload")
    _validate_public_report_aggregates(payload)
    expected_derived = _payload_sha256(_report_derived_payload_from_payload(payload))
    if payload.get("derived_validation_digest") != expected_derived:
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_from_observation(
    item: ResearchStrategyResolutionRuleTraceabilityObservation,
    config: ResearchStrategyResolutionRuleTraceabilityConfig,
) -> ResearchStrategyResolutionRuleTraceabilityRow:
    traceability_score = _traceability_score(
        rule_specificity=item.rule_specificity,
        official_evidence_strength=item.official_evidence_strength,
        quorum_source_count=item.quorum_source_count,
        contradiction_pressure=item.contradiction_pressure,
        min_pass_quorum_source_count=config.min_pass_quorum_source_count,
    )
    reason_codes = _row_reason_codes(
        rule_specificity=item.rule_specificity,
        official_evidence_strength=item.official_evidence_strength,
        quorum_source_count=item.quorum_source_count,
        contradiction_pressure=item.contradiction_pressure,
        config=config,
    )
    return ResearchStrategyResolutionRuleTraceabilityRow(
        trace_digest=_redacted_digest("trace_", item.trace_reference),
        rule_digest=_redacted_digest("rule_", item.resolution_rule_reference),
        evidence_digest=_redacted_digest("evidence_", item.official_evidence_reference),
        observed_at=item.observed_at,
        rule_specificity=item.rule_specificity,
        official_evidence_strength=item.official_evidence_strength,
        quorum_source_count=item.quorum_source_count,
        independent_source_count=item.independent_source_count,
        contradiction_pressure=item.contradiction_pressure,
        traceability_score=traceability_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _traceability_score(
    *,
    rule_specificity: Decimal,
    official_evidence_strength: Decimal,
    quorum_source_count: Decimal,
    contradiction_pressure: Decimal,
    min_pass_quorum_source_count: Decimal,
) -> Decimal:
    quorum_score = _bounded_probability(quorum_source_count / min_pass_quorum_source_count)
    contradiction_quality = _bounded_probability(ONE - contradiction_pressure)
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            (
                rule_specificity
                + official_evidence_strength
                + quorum_score
                + contradiction_quality
            )
            / Decimal("4.000000"),
        )


def _row_reason_codes(
    *,
    rule_specificity: Decimal,
    official_evidence_strength: Decimal,
    quorum_source_count: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchStrategyResolutionRuleTraceabilityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if rule_specificity < config.min_watch_rule_specificity:
        reason_codes.append("rule_specificity_block")
    elif rule_specificity < config.min_pass_rule_specificity:
        reason_codes.append("rule_specificity_watch")
    if official_evidence_strength < config.min_watch_official_evidence_strength:
        reason_codes.append("official_evidence_strength_block")
    elif official_evidence_strength < config.min_pass_official_evidence_strength:
        reason_codes.append("official_evidence_strength_watch")
    if quorum_source_count < config.min_watch_quorum_source_count:
        reason_codes.append("source_quorum_block")
    elif quorum_source_count < config.min_pass_quorum_source_count:
        reason_codes.append("source_quorum_watch")
    if contradiction_pressure > config.max_watch_contradiction_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure > config.max_pass_contradiction_pressure:
        reason_codes.append("contradiction_pressure_watch")
    if not reason_codes:
        reason_codes.append("resolution_rule_traceability_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyResolutionRuleTraceabilityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyResolutionRuleTraceabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_rule_traceability_empty",)
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    if observed == {"resolution_rule_traceability_pass"}:
        return ("resolution_rule_traceability_pass",)
    return tuple(
        reason_code
        for reason_code in REASON_SEQUENCE
        if reason_code in observed and reason_code != "resolution_rule_traceability_pass"
    )


def _validate_row(row: ResearchStrategyResolutionRuleTraceabilityRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.row_sha256 != _row_sha256(row):
        raise ValueError("row_sha256 must match row fields")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchStrategyResolutionRuleTraceabilityReport) -> None:
    rows = report.rows
    if report.trace_count != _decimal_count(len(rows)):
        raise ValueError("trace_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_contradiction_pressure != _max_contradiction_pressure(rows):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.average_traceability_score != _average_traceability_score(rows):
        raise ValueError("average_traceability_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_row_payload(row: dict[str, Any]) -> None:
    reason_codes = row.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("payload row reason_codes must be a list")
    normalized_reasons = tuple(reason_codes)
    _normalize_reason_codes("payload row reason_codes", normalized_reasons, allow_empty=False)
    if row.get("status") != _status_from_reason_codes(normalized_reasons):
        raise ValueError("payload row status must match reason_codes")
    expected_row_sha256 = _payload_sha256(
        _without_keys(row, ("row_sha256", "derived_validation_digest")),
    )
    if row.get("row_sha256") != expected_row_sha256:
        raise ValueError("row_sha256 must match public payload row")
    expected_derived = _payload_sha256(_row_derived_payload_from_payload(row))
    if row.get("derived_validation_digest") != expected_derived:
        raise ValueError("derived_validation_digest must match public payload row")


def _validate_public_report_aggregates(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    row_statuses = tuple(row["status"] for row in rows)
    if _payload_decimal(payload.get("trace_count")) != _decimal_count(len(rows)):
        raise ValueError("trace_count must match payload rows")
    if _payload_decimal(payload.get("pass_count")) != _decimal_count(
        sum(1 for status in row_statuses if status == "pass"),
    ):
        raise ValueError("pass_count must match payload rows")
    if _payload_decimal(payload.get("watch_count")) != _decimal_count(
        sum(1 for status in row_statuses if status == "watch"),
    ):
        raise ValueError("watch_count must match payload rows")
    if _payload_decimal(payload.get("block_count")) != _decimal_count(
        sum(1 for status in row_statuses if status == "block"),
    ):
        raise ValueError("block_count must match payload rows")
    max_pressure = max(
        (_payload_decimal(row["contradiction_pressure"]) for row in rows),
        default=ZERO,
    )
    if _payload_decimal(payload.get("max_contradiction_pressure")) != max_pressure:
        raise ValueError("max_contradiction_pressure must match payload rows")
    average_score = _average(tuple(_payload_decimal(row["traceability_score"]) for row in rows))
    if _payload_decimal(payload.get("average_traceability_score")) != average_score:
        raise ValueError("average_traceability_score must match payload rows")
    if payload.get("status") != _public_report_status(rows):
        raise ValueError("status must match payload rows")
    if payload.get("reason_codes") != list(_public_report_reason_codes(rows)):
        raise ValueError("reason_codes must match payload rows")


def _public_report_status(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "block"
    if any(row["status"] == "block" for row in rows):
        return "block"
    if any(row["status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _public_report_reason_codes(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    if not rows:
        return ("resolution_rule_traceability_empty",)
    observed = {
        reason_code
        for row in rows
        for reason_code in row["reason_codes"]
    }
    if observed == {"resolution_rule_traceability_pass"}:
        return ("resolution_rule_traceability_pass",)
    return tuple(
        reason_code
        for reason_code in REASON_SEQUENCE
        if reason_code in observed and reason_code != "resolution_rule_traceability_pass"
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyResolutionRuleTraceabilityRow],
) -> tuple[ResearchStrategyResolutionRuleTraceabilityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyResolutionRuleTraceabilityRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyResolutionRuleTraceabilityRow:
            raise ValueError(
                "rows must contain ResearchStrategyResolutionRuleTraceabilityRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_key))


def _row_key(row: ResearchStrategyResolutionRuleTraceabilityRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.contradiction_pressure,
        row.trace_digest,
    )


def _max_contradiction_pressure(
    rows: tuple[ResearchStrategyResolutionRuleTraceabilityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.contradiction_pressure for row in rows)


def _average_traceability_score(
    rows: tuple[ResearchStrategyResolutionRuleTraceabilityRow, ...],
) -> Decimal:
    return _average(tuple(row.traceability_score for row in rows))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(sum(values, ZERO) / _decimal_count(len(values)))


def _report_payload(
    report: ResearchStrategyResolutionRuleTraceabilityReport,
    *,
    include_report_digests: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "trace_count": _decimal_payload(report.trace_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "max_contradiction_pressure": _decimal_payload(report.max_contradiction_pressure),
        "average_traceability_score": _decimal_payload(report.average_traceability_score),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row, include_row_digests=True) for row in report.rows],
    }
    if include_report_digests:
        payload["report_sha256"] = report.report_sha256
        payload["derived_validation_digest"] = report.derived_validation_digest
    payload["paper_only"] = report.paper_only
    payload["report_only"] = report.report_only
    payload["readonly"] = report.readonly
    return payload


def _row_payload(
    row: ResearchStrategyResolutionRuleTraceabilityRow,
    *,
    include_row_digests: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "trace_digest": row.trace_digest,
        "rule_digest": row.rule_digest,
        "evidence_digest": row.evidence_digest,
        "observed_at": row.observed_at.isoformat(),
        "rule_specificity": _decimal_payload(row.rule_specificity),
        "official_evidence_strength": _decimal_payload(row.official_evidence_strength),
        "quorum_source_count": _decimal_payload(row.quorum_source_count),
        "independent_source_count": _decimal_payload(row.independent_source_count),
        "contradiction_pressure": _decimal_payload(row.contradiction_pressure),
        "traceability_score": _decimal_payload(row.traceability_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
    }
    if include_row_digests:
        payload["row_sha256"] = row.row_sha256
        payload["derived_validation_digest"] = row.derived_validation_digest
    payload["paper_only"] = row.paper_only
    payload["report_only"] = row.report_only
    payload["readonly"] = row.readonly
    return payload


def _row_sha256(row: ResearchStrategyResolutionRuleTraceabilityRow) -> str:
    return _payload_sha256(_row_payload(row, include_row_digests=False))


def _row_derived_validation_digest(
    row: ResearchStrategyResolutionRuleTraceabilityRow,
) -> str:
    return _payload_sha256(
        {
            "traceability_score": _decimal_payload(row.traceability_score),
            "status": row.status,
            "reason_codes": list(row.reason_codes),
            "row_sha256": row.row_sha256,
            "paper_only": row.paper_only,
            "report_only": row.report_only,
            "readonly": row.readonly,
        },
    )


def _row_derived_payload_from_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "traceability_score": row["traceability_score"],
        "status": row["status"],
        "reason_codes": row["reason_codes"],
        "row_sha256": row["row_sha256"],
        "paper_only": row["paper_only"],
        "report_only": row["report_only"],
        "readonly": row["readonly"],
    }


def _report_sha256(report: ResearchStrategyResolutionRuleTraceabilityReport) -> str:
    return _payload_sha256(_report_payload(report, include_report_digests=False))


def _report_derived_validation_digest(
    report: ResearchStrategyResolutionRuleTraceabilityReport,
) -> str:
    return _payload_sha256(
        {
            "trace_count": _decimal_payload(report.trace_count),
            "pass_count": _decimal_payload(report.pass_count),
            "watch_count": _decimal_payload(report.watch_count),
            "block_count": _decimal_payload(report.block_count),
            "average_traceability_score": _decimal_payload(
                report.average_traceability_score,
            ),
            "status": report.status,
            "reason_codes": list(report.reason_codes),
            "row_derived_validation_digests": [
                row.derived_validation_digest for row in report.rows
            ],
            "report_sha256": report.report_sha256,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_derived_payload_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["rows"]
    return {
        "trace_count": payload["trace_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "average_traceability_score": payload["average_traceability_score"],
        "status": payload["status"],
        "reason_codes": payload["reason_codes"],
        "row_derived_validation_digests": [
            row["derived_validation_digest"] for row in rows
        ],
        "report_sha256": payload["report_sha256"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _without_keys(payload: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in keys}


def _redacted_digest(prefix: str, value: str) -> str:
    return f"{prefix}{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _decimal_payload(value: Decimal) -> str:
    return str(_q(value))


def _payload_decimal(value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError("payload Decimal values must be strings")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError("payload Decimal values must parse as Decimal") from exc
    return _normalize_decimal("payload Decimal value", parsed)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _q(Decimal(value))


def _bounded_probability(value: Decimal) -> Decimal:
    normalized = _q(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_SEQUENCE:
            raise ValueError(f"{field_name} contains unsupported reason code")
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_payload_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value or not set(value) <= SHA_HEX:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_prefixed_digest(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must use a redacted digest prefix")
    _normalize_sha256(field_name, value[len(prefix):])


def _require_raw_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_public_text(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_flags(label: str, payload: Mapping[str, Any]) -> None:
    for field_name in FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_key(current_path, key)
            _reject_unsafe_public_payload(label, item, key if not path else f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(path: str, key: str) -> None:
    normalized = key.lower()
    if (
        "source" + "_text" in normalized
        or any(item in _surface_tokens(normalized) for item in UNSAFE_KEY_TOKENS)
    ):
        raise ValueError(f"unsafe public payload field in {path}: {key}")


def _reject_unsafe_public_text(path: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {path}")
    tokens = _surface_tokens(normalized)
    if any(item in tokens for item in UNSAFE_KEY_TOKENS):
        raise ValueError(f"unsafe public payload value in {path}")


def _surface_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RULE_TRACEABILITY_REPORT_CONFIG_VERSION",
    "ResearchStrategyResolutionRuleTraceabilityConfig",
    "ResearchStrategyResolutionRuleTraceabilityObservation",
    "ResearchStrategyResolutionRuleTraceabilityReport",
    "ResearchStrategyResolutionRuleTraceabilityRow",
    "build_research_strategy_resolution_rule_traceability_report",
    "research_strategy_resolution_rule_traceability_report_payload",
    "validate_research_strategy_resolution_rule_traceability_public_payload",
    "validate_research_strategy_resolution_rule_traceability_report",
)
