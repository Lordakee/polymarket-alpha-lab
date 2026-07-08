"""Pure resolution confidence decay report reducer for manual review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-resolution-confidence-decay-report-v0"
)
RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
ROW_REASON_CODES = (
    "corroboration_freshness_block",
    "corroboration_freshness_watch",
    "manual_recheck_urgency_block",
    "manual_recheck_urgency_watch",
    "official_evidence_age_block",
    "official_evidence_age_watch",
    "resolution_confidence_decay_pass",
    "rule_ambiguity_block",
    "rule_ambiguity_watch",
    "unresolved_contradiction_block",
    "unresolved_contradiction_watch",
)
REPORT_REASON_CODES = (
    "corroboration_freshness_review",
    "manual_recheck_review",
    "no_resolution_confidence_assumptions",
    "official_evidence_age_review",
    "resolution_confidence_decay_block",
    "resolution_confidence_decay_pass",
    "resolution_confidence_decay_watch",
    "rule_ambiguity_review",
    "unresolved_contradiction_review",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate" + "_" + "id",
    "market" + "_" + "id",
    "market" + "_" + "slug",
    "q" + "uestion",
    "source" + "_" + "url",
    "source" + "_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "private",
    "to" + "ken",
    "sec" + "ret",
    "api" + "_" + "key",
    "cred" + "ential",
    "auth",
    "ra" + "w",
    "li" + "ve",
    "data" + "base",
    "net" + "work",
    "persist",
    "wal" + "let",
    "or" + "der",
    "b" + "uy",
    "se" + "ll",
    "trad" + "e",
    "trad" + "ing",
    "signing",
    "mutation",
    "http://",
    "https://",
)


@dataclass(frozen=True)
class ResearchStrategyResolutionConfidenceDecayConfig:
    config_version: str
    official_evidence_watch_age_seconds: Decimal
    official_evidence_block_age_seconds: Decimal
    corroboration_watch_age_seconds: Decimal
    corroboration_block_age_seconds: Decimal
    rule_ambiguity_watch_threshold: Decimal
    rule_ambiguity_block_threshold: Decimal
    contradiction_pressure_watch_threshold: Decimal
    contradiction_pressure_block_threshold: Decimal
    manual_recheck_watch_age_seconds: Decimal
    manual_recheck_block_age_seconds: Decimal
    manual_recheck_urgency_watch_threshold: Decimal
    manual_recheck_urgency_block_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionConfidenceDecayConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyResolutionConfidenceDecayConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "official_evidence_watch_age_seconds",
            "official_evidence_block_age_seconds",
            "corroboration_watch_age_seconds",
            "corroboration_block_age_seconds",
            "manual_recheck_watch_age_seconds",
            "manual_recheck_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_ambiguity_watch_threshold",
            "rule_ambiguity_block_threshold",
            "contradiction_pressure_watch_threshold",
            "contradiction_pressure_block_threshold",
            "manual_recheck_urgency_watch_threshold",
            "manual_recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_age_threshold_pair(
            "official_evidence_age",
            self.official_evidence_watch_age_seconds,
            self.official_evidence_block_age_seconds,
        )
        _require_age_threshold_pair(
            "corroboration_age",
            self.corroboration_watch_age_seconds,
            self.corroboration_block_age_seconds,
        )
        _require_threshold_pair(
            "rule_ambiguity threshold",
            self.rule_ambiguity_watch_threshold,
            self.rule_ambiguity_block_threshold,
        )
        _require_threshold_pair(
            "contradiction_pressure threshold",
            self.contradiction_pressure_watch_threshold,
            self.contradiction_pressure_block_threshold,
        )
        _require_age_threshold_pair(
            "manual_recheck_age",
            self.manual_recheck_watch_age_seconds,
            self.manual_recheck_block_age_seconds,
        )
        _require_threshold_pair(
            "manual_recheck_urgency threshold",
            self.manual_recheck_urgency_watch_threshold,
            self.manual_recheck_urgency_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionConfidenceDecayInput:
    resolution_assumption_ref: str
    official_evidence_observed_at: datetime
    corroboration_observed_at: datetime
    rule_clarity_score: Decimal
    unresolved_contradiction_count: Decimal
    contradiction_severity_score: Decimal
    last_manual_recheck_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionConfidenceDecayInput:
            raise ValueError(
                "input must be exactly ResearchStrategyResolutionConfidenceDecayInput",
            )
        _require_reference_string("resolution_assumption_ref", self.resolution_assumption_ref)
        for field_name in (
            "official_evidence_observed_at",
            "corroboration_observed_at",
            "last_manual_recheck_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rule_clarity_score",
            _normalize_probability("rule_clarity_score", self.rule_clarity_score),
        )
        object.__setattr__(
            self,
            "unresolved_contradiction_count",
            _normalize_whole_decimal(
                "unresolved_contradiction_count",
                self.unresolved_contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_severity_score",
            _normalize_probability(
                "contradiction_severity_score",
                self.contradiction_severity_score,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionConfidenceDecayRow:
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    official_evidence_age_seconds: Decimal
    official_evidence_age_pressure: Decimal
    corroboration_age_seconds: Decimal
    corroboration_freshness_score: Decimal
    rule_ambiguity_score: Decimal
    unresolved_contradiction_pressure: Decimal
    manual_recheck_age_seconds: Decimal
    manual_recheck_urgency_score: Decimal
    resolution_confidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionConfidenceDecayRow:
            raise ValueError(
                "row must be exactly ResearchStrategyResolutionConfidenceDecayRow",
            )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_sha256_digest("aggregate_row_hash", self.aggregate_row_hash)
        for field_name in (
            "official_evidence_age_seconds",
            "corroboration_age_seconds",
            "manual_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_evidence_age_pressure",
            "corroboration_freshness_score",
            "rule_ambiguity_score",
            "unresolved_contradiction_pressure",
            "manual_recheck_urgency_score",
            "resolution_confidence_decay_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyResolutionConfidenceDecayReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_official_evidence_age_pressure: Decimal
    mean_corroboration_freshness_score: Decimal
    mean_rule_ambiguity_score: Decimal
    mean_unresolved_contradiction_pressure: Decimal
    mean_manual_recheck_urgency_score: Decimal
    mean_resolution_confidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyResolutionConfidenceDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionConfidenceDecayReport:
            raise ValueError(
                "report must be exactly ResearchStrategyResolutionConfidenceDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_official_evidence_age_pressure",
            "mean_corroboration_freshness_score",
            "mean_rule_ambiguity_score",
            "mean_unresolved_contradiction_pressure",
            "mean_manual_recheck_urgency_score",
            "mean_resolution_confidence_decay_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_resolution_confidence_decay_report(
    inputs: Iterable[ResearchStrategyResolutionConfidenceDecayInput],
    *,
    config: ResearchStrategyResolutionConfidenceDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyResolutionConfidenceDecayReport:
    if type(config) is not ResearchStrategyResolutionConfidenceDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyResolutionConfidenceDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    prepared_rows = tuple(
        sorted(
            (
                _prepare_row(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(value, aggregate_row_number=_count(index))
        for index, value in enumerate(prepared_rows, start=1)
    )
    return ResearchStrategyResolutionConfidenceDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_official_evidence_age_pressure=_mean(
            tuple(row.official_evidence_age_pressure for row in rows),
        ),
        mean_corroboration_freshness_score=_mean(
            tuple(row.corroboration_freshness_score for row in rows),
        ),
        mean_rule_ambiguity_score=_mean(tuple(row.rule_ambiguity_score for row in rows)),
        mean_unresolved_contradiction_pressure=_mean(
            tuple(row.unresolved_contradiction_pressure for row in rows),
        ),
        mean_manual_recheck_urgency_score=_mean(
            tuple(row.manual_recheck_urgency_score for row in rows),
        ),
        mean_resolution_confidence_decay_score=_mean(
            tuple(row.resolution_confidence_decay_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_resolution_confidence_decay_report_payload(
    report: ResearchStrategyResolutionConfidenceDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyResolutionConfidenceDecayReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_values("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyResolutionConfidenceDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_STATUSES",
    "ResearchStrategyResolutionConfidenceDecayConfig",
    "ResearchStrategyResolutionConfidenceDecayInput",
    "ResearchStrategyResolutionConfidenceDecayRow",
    "ResearchStrategyResolutionConfidenceDecayReport",
    "build_research_strategy_resolution_confidence_decay_report",
    "research_strategy_resolution_confidence_decay_report_payload",
)


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


@dataclass(frozen=True)
class _PreparedRow:
    aggregate_row_hash: str
    official_evidence_age_seconds: Decimal
    official_evidence_age_pressure: Decimal
    corroboration_age_seconds: Decimal
    corroboration_freshness_score: Decimal
    rule_ambiguity_score: Decimal
    unresolved_contradiction_pressure: Decimal
    manual_recheck_age_seconds: Decimal
    manual_recheck_urgency_score: Decimal
    resolution_confidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategyResolutionConfidenceDecayInput,
    *,
    config: ResearchStrategyResolutionConfidenceDecayConfig,
    generated_at: datetime,
) -> _PreparedRow:
    _reject_future_input_times(value, generated_at)
    official_age = _age_seconds(generated_at, value.official_evidence_observed_at)
    corroboration_age = _age_seconds(generated_at, value.corroboration_observed_at)
    manual_age = _age_seconds(generated_at, value.last_manual_recheck_at)
    official_pressure = _age_pressure(
        official_age,
        watch_age=config.official_evidence_watch_age_seconds,
        block_age=config.official_evidence_block_age_seconds,
    )
    corroboration_pressure = _age_pressure(
        corroboration_age,
        watch_age=config.corroboration_watch_age_seconds,
        block_age=config.corroboration_block_age_seconds,
    )
    corroboration_freshness = _quantize(ONE - corroboration_pressure)
    rule_ambiguity = _quantize(ONE - value.rule_clarity_score)
    contradiction_pressure = _contradiction_pressure(value)
    manual_urgency = _manual_recheck_urgency(
        manual_age=manual_age,
        rule_ambiguity_score=rule_ambiguity,
        unresolved_contradiction_pressure=contradiction_pressure,
        config=config,
    )
    decay_score = _mean(
        (
            official_pressure,
            corroboration_pressure,
            rule_ambiguity,
            contradiction_pressure,
            manual_urgency,
        ),
    )
    reason_codes = _row_reason_codes(
        official_age=official_age,
        corroboration_age=corroboration_age,
        rule_ambiguity_score=rule_ambiguity,
        unresolved_contradiction_pressure=contradiction_pressure,
        manual_recheck_urgency_score=manual_urgency,
        config=config,
    )
    status = _row_status(reason_codes)
    return _PreparedRow(
        aggregate_row_hash=_aggregate_row_hash(value.resolution_assumption_ref),
        official_evidence_age_seconds=official_age,
        official_evidence_age_pressure=official_pressure,
        corroboration_age_seconds=corroboration_age,
        corroboration_freshness_score=corroboration_freshness,
        rule_ambiguity_score=rule_ambiguity,
        unresolved_contradiction_pressure=contradiction_pressure,
        manual_recheck_age_seconds=manual_age,
        manual_recheck_urgency_score=manual_urgency,
        resolution_confidence_decay_score=decay_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
) -> ResearchStrategyResolutionConfidenceDecayRow:
    return ResearchStrategyResolutionConfidenceDecayRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=value.aggregate_row_hash,
        official_evidence_age_seconds=value.official_evidence_age_seconds,
        official_evidence_age_pressure=value.official_evidence_age_pressure,
        corroboration_age_seconds=value.corroboration_age_seconds,
        corroboration_freshness_score=value.corroboration_freshness_score,
        rule_ambiguity_score=value.rule_ambiguity_score,
        unresolved_contradiction_pressure=value.unresolved_contradiction_pressure,
        manual_recheck_age_seconds=value.manual_recheck_age_seconds,
        manual_recheck_urgency_score=value.manual_recheck_urgency_score,
        resolution_confidence_decay_score=value.resolution_confidence_decay_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    official_age: Decimal,
    corroboration_age: Decimal,
    rule_ambiguity_score: Decimal,
    unresolved_contradiction_pressure: Decimal,
    manual_recheck_urgency_score: Decimal,
    config: ResearchStrategyResolutionConfidenceDecayConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if official_age >= config.official_evidence_block_age_seconds:
        codes.append("official_evidence_age_block")
    elif official_age >= config.official_evidence_watch_age_seconds:
        codes.append("official_evidence_age_watch")
    if corroboration_age >= config.corroboration_block_age_seconds:
        codes.append("corroboration_freshness_block")
    elif corroboration_age >= config.corroboration_watch_age_seconds:
        codes.append("corroboration_freshness_watch")
    if rule_ambiguity_score >= config.rule_ambiguity_block_threshold:
        codes.append("rule_ambiguity_block")
    elif rule_ambiguity_score >= config.rule_ambiguity_watch_threshold:
        codes.append("rule_ambiguity_watch")
    if unresolved_contradiction_pressure >= config.contradiction_pressure_block_threshold:
        codes.append("unresolved_contradiction_block")
    elif unresolved_contradiction_pressure >= config.contradiction_pressure_watch_threshold:
        codes.append("unresolved_contradiction_watch")
    if manual_recheck_urgency_score >= config.manual_recheck_urgency_block_threshold:
        codes.append("manual_recheck_urgency_block")
    elif manual_recheck_urgency_score >= config.manual_recheck_urgency_watch_threshold:
        codes.append("manual_recheck_urgency_watch")
    if not codes:
        codes.append("resolution_confidence_decay_pass")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes != ("resolution_confidence_decay_pass",):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyResolutionConfidenceDecayRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyResolutionConfidenceDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_confidence_assumptions",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_confidence_decay_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("resolution_confidence_decay_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("resolution_confidence_decay_watch")
    if any(
        reason_code.startswith("official_evidence_age_")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("official_evidence_age_review")
    if any(
        reason_code.startswith("corroboration_freshness_")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("corroboration_freshness_review")
    if any(
        reason_code.startswith("rule_ambiguity_")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("rule_ambiguity_review")
    if any(
        reason_code.startswith("unresolved_contradiction_")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("unresolved_contradiction_review")
    if any(
        reason_code.startswith("manual_recheck_urgency_")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("manual_recheck_review")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), REPORT_REASON_CODES)


def _prepared_row_sort_key(
    row: _PreparedRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.resolution_confidence_decay_score,
        -row.manual_recheck_urgency_score,
        -row.official_evidence_age_pressure,
        row.corroboration_freshness_score,
        row.aggregate_row_hash,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyResolutionConfidenceDecayInput],
) -> tuple[ResearchStrategyResolutionConfidenceDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyResolutionConfidenceDecayInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyResolutionConfidenceDecayInput values",
            )
        _require_hard_flags("input", value)
        if value.resolution_assumption_ref in seen_refs:
            raise ValueError(
                "inputs must not contain duplicate resolution_assumption_ref values",
            )
        seen_refs.add(value.resolution_assumption_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyResolutionConfidenceDecayRow],
) -> tuple[ResearchStrategyResolutionConfidenceDecayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    previous_number = ZERO
    for row in normalized:
        if type(row) is not ResearchStrategyResolutionConfidenceDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyResolutionConfidenceDecayRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.aggregate_row_number <= previous_number:
            raise ValueError("rows must use deterministic aggregate_row_number sequence")
        previous_number = row.aggregate_row_number
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != sorted_rows:
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _row_sort_key(
    row: ResearchStrategyResolutionConfidenceDecayRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.resolution_confidence_decay_score,
        -row.manual_recheck_urgency_score,
        -row.official_evidence_age_pressure,
        row.corroboration_freshness_score,
        row.aggregate_row_hash,
    )


def _validate_row_consistency(
    row: ResearchStrategyResolutionConfidenceDecayRow,
) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("resolution_confidence_decay_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(
        reason_code.endswith("_watch") for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(
        reason_code.endswith("_block") for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyResolutionConfidenceDecayReport,
) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.source_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match source_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_official_evidence_age_pressure != _mean(
        tuple(row.official_evidence_age_pressure for row in report.rows),
    ):
        raise ValueError("mean_official_evidence_age_pressure must match rows")
    if report.mean_corroboration_freshness_score != _mean(
        tuple(row.corroboration_freshness_score for row in report.rows),
    ):
        raise ValueError("mean_corroboration_freshness_score must match rows")
    if report.mean_rule_ambiguity_score != _mean(
        tuple(row.rule_ambiguity_score for row in report.rows),
    ):
        raise ValueError("mean_rule_ambiguity_score must match rows")
    if report.mean_unresolved_contradiction_pressure != _mean(
        tuple(row.unresolved_contradiction_pressure for row in report.rows),
    ):
        raise ValueError("mean_unresolved_contradiction_pressure must match rows")
    if report.mean_manual_recheck_urgency_score != _mean(
        tuple(row.manual_recheck_urgency_score for row in report.rows),
    ):
        raise ValueError("mean_manual_recheck_urgency_score must match rows")
    if report.mean_resolution_confidence_decay_score != _mean(
        tuple(row.resolution_confidence_decay_score for row in report.rows),
    ):
        raise ValueError("mean_resolution_confidence_decay_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _verify_report_integrity(
    report: ResearchStrategyResolutionConfidenceDecayReport,
) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get(DERIVED_VALIDATION_DIGEST_FIELD)
    _require_sha256_digest(f"{label}.{DERIVED_VALIDATION_DIGEST_FIELD}", provided)
    digest_input = dict(payload)
    digest_input.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyResolutionConfidenceDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyResolutionConfidenceDecayRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    if not rows:
        counts["no_resolution_confidence_assumptions"] = 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_reason_code_counts(
    value: Iterable[tuple[str, Decimal]],
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    normalized: list[tuple[str, Decimal]] = []
    supported_codes = set(ROW_REASON_CODES) | set(REPORT_REASON_CODES)
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason_code count tuples")
        reason_code, count = row
        _require_reason_code("reason_code_counts reason_code", reason_code)
        if reason_code not in supported_codes:
            raise ValueError("reason_code_counts reason_code is not supported")
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    sorted_rows = tuple(
        sorted(normalized, key=lambda item: (-item[1], item[0])),
    )
    if tuple(normalized) != sorted_rows:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return tuple(normalized)


def _contradiction_pressure(
    value: ResearchStrategyResolutionConfidenceDecayInput,
) -> Decimal:
    return _clamp_probability(
        _quantize(
            value.unresolved_contradiction_count * value.contradiction_severity_score,
        ),
    )


def _manual_recheck_urgency(
    *,
    manual_age: Decimal,
    rule_ambiguity_score: Decimal,
    unresolved_contradiction_pressure: Decimal,
    config: ResearchStrategyResolutionConfidenceDecayConfig,
) -> Decimal:
    manual_age_pressure = _age_pressure(
        manual_age,
        watch_age=config.manual_recheck_watch_age_seconds,
        block_age=config.manual_recheck_block_age_seconds,
    )
    return _clamp_probability(
        _quantize(
            (manual_age_pressure * Decimal("0.600000"))
            + (rule_ambiguity_score * Decimal("0.200000"))
            + (unresolved_contradiction_pressure * Decimal("0.200000")),
        ),
    )


def _age_pressure(
    age_seconds: Decimal,
    *,
    watch_age: Decimal,
    block_age: Decimal,
) -> Decimal:
    if age_seconds <= watch_age:
        return ZERO
    if age_seconds >= block_age:
        return ONE
    return _clamp_probability(_quantize((age_seconds - watch_age) / (block_age - watch_age)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    if value % ONE == ZERO:
        return +value
    return _quantize(value)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _aggregate_row_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _reject_future_input_times(
    value: ResearchStrategyResolutionConfidenceDecayInput,
    generated_at: datetime,
) -> None:
    for field_name in (
        "official_evidence_observed_at",
        "corroboration_observed_at",
        "last_manual_recheck_at",
    ):
        if getattr(value, field_name) > generated_at:
            raise ValueError(f"{field_name} must not be after generated_at")


def _require_age_threshold_pair(label: str, watch_age: Decimal, block_age: Decimal) -> None:
    if block_age <= watch_age:
        raise ValueError(f"{label} threshold block value must exceed watch value")


def _require_threshold_pair(label: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{label} block value must exceed watch value")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_reason_code(field_name, code)
        if code not in allowed_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
    if tuple(sorted(codes)) != codes:
        raise ValueError(f"{field_name} must be sorted")
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_reference_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be trimmed")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value % ONE == ZERO:
        return +decimal_value
    return _quantize(decimal_value)


def _normalize_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return +decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _apply_or_verify_digest(value: object) -> None:
    supplied = getattr(value, DERIVED_VALIDATION_DIGEST_FIELD)
    expected = _derived_validation_digest(value)
    if supplied == "":
        object.__setattr__(value, DERIVED_VALIDATION_DIGEST_FIELD, expected)
        return
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, supplied)
    if supplied != expected:
        raise ValueError("derived_validation_digest must match fields")


def _verify_digest(value: object) -> None:
    supplied = getattr(value, DERIVED_VALIDATION_DIGEST_FIELD)
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, supplied)
    if supplied != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest must match fields")


def _derived_validation_digest(value: object) -> str:
    encoded = dumps(
        _digest_ready(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_digest_ready(item) for item in value]
    if isinstance(value, list):
        return [_digest_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _digest_ready(item)
            for key, item in value.items()
            if key != DERIVED_VALIDATION_DIGEST_FIELD
        }
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _validate_public_payload_values(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{current_path} has unsafe value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _validate_public_payload_values(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _validate_public_payload_values(label, item, item_path)
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"{label} has unsafe value")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
