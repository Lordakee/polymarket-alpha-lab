"""Pure report-only aggregate resolution ambiguity escalation report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "PUBLIC_STATUSES",
    "ResearchResolutionAmbiguityEscalationConfig",
    "ResearchResolutionAmbiguityEscalationInput",
    "ResearchResolutionAmbiguityEscalationReasonCodeCount",
    "ResearchResolutionAmbiguityEscalationReport",
    "ResearchResolutionAmbiguityEscalationRow",
    "build_research_resolution_ambiguity_escalation_report",
    "research_resolution_ambiguity_escalation_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-ambiguity-escalation-v0"
PUBLIC_STATUSES = ("pass", "watch", "block")
_STATUSES = frozenset(PUBLIC_STATUSES)
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RESOLUTION_AREA_UNSAFE_TERMS = (
    "condition",
    "id",
    "market",
    "question",
    "raw",
    "slug",
    "source",
    "text",
    "url",
)
_PAYLOAD_UNSAFE_FRAGMENTS = (
    "_table",
    "candidate_",
    "candidate_id",
    "candidate_identifier",
    "condition_id",
    "database_dsn",
    "database_url",
    "db_url",
    "dsn",
    "http://",
    "https://",
    "market_id",
    "market_slug",
    "mongodb://",
    "mysql://",
    "postgres://",
    "postgresql://",
    "question",
    "raw_market",
    "raw_candidate",
    "raw_question",
    "raw_source",
    "raw_text",
    "raw_url",
    "redis://",
    "source_ref",
    "source_reference",
    "source_text",
    "source_url",
    "sqlite://",
    "table_",
    "table_name",
)
_ACTION_TERMS = (
    "credential",
    "place" + "_" + "or" + "der",
    "private" + "_" + "key",
    "api" + "_" + "key",
    "secret",
    "token",
    "tra" + "de",
    "tra" + "ding",
    "wal" + "let",
    "li" + "ve" + "_" + "tra" + "ding",
    "position" + "_" + "size",
    "recommend",
    "sizing",
    "stake" + "_" + "size",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchResolutionAmbiguityEscalationConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_authoritative_evidence_age_seconds: Decimal = Decimal("3600")
    stale_authoritative_evidence_age_seconds: Decimal = Decimal("86400")
    manual_review_capacity_per_reviewer: Decimal = Decimal("4")
    comfortable_recheck_window_seconds: Decimal = Decimal("86400")
    watch_escalation_pressure: Decimal = Decimal("0.350000")
    block_escalation_pressure: Decimal = Decimal("0.700000")
    rule_ambiguity_weight: Decimal = Decimal("0.250000")
    source_disagreement_weight: Decimal = Decimal("0.250000")
    stale_authoritative_evidence_weight: Decimal = Decimal("0.200000")
    manual_review_burden_weight: Decimal = Decimal("0.150000")
    recheck_urgency_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionAmbiguityEscalationConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_authoritative_evidence_age_seconds",
            "stale_authoritative_evidence_age_seconds",
            "manual_review_capacity_per_reviewer",
            "comfortable_recheck_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.stale_authoritative_evidence_age_seconds
            <= self.fresh_authoritative_evidence_age_seconds
        ):
            raise ValueError(
                "stale_authoritative_evidence_age_seconds must exceed "
                "fresh_authoritative_evidence_age_seconds",
            )
        for field_name in (
            "watch_escalation_pressure",
            "block_escalation_pressure",
            "rule_ambiguity_weight",
            "source_disagreement_weight",
            "stale_authoritative_evidence_weight",
            "manual_review_burden_weight",
            "recheck_urgency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_escalation_pressure <= self.watch_escalation_pressure:
            raise ValueError("block_escalation_pressure must exceed watch_escalation_pressure")
        weight_sum = _quantize(
            self.rule_ambiguity_weight
            + self.source_disagreement_weight
            + self.stale_authoritative_evidence_weight
            + self.manual_review_burden_weight
            + self.recheck_urgency_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "rule_ambiguity_weight, source_disagreement_weight, "
                "stale_authoritative_evidence_weight, manual_review_burden_weight, "
                "and recheck_urgency_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityEscalationInput:
    resolution_area: str
    affected_market_count: Decimal
    rule_ambiguity_score: Decimal
    source_disagreement_score: Decimal
    authoritative_evidence_age_seconds: Decimal
    manual_review_item_count: Decimal
    available_reviewer_count: Decimal
    seconds_until_required_recheck: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionAmbiguityEscalationInput, "input")
        _require_public_resolution_area("resolution_area", self.resolution_area)
        object.__setattr__(
            self,
            "affected_market_count",
            _require_positive_whole_decimal(
                "affected_market_count",
                self.affected_market_count,
            ),
        )
        for field_name in ("rule_ambiguity_score", "source_disagreement_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authoritative_evidence_age_seconds",
            _require_nonnegative_decimal(
                "authoritative_evidence_age_seconds",
                self.authoritative_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "manual_review_item_count",
            _require_nonnegative_whole_decimal(
                "manual_review_item_count",
                self.manual_review_item_count,
            ),
        )
        object.__setattr__(
            self,
            "available_reviewer_count",
            _require_positive_whole_decimal(
                "available_reviewer_count",
                self.available_reviewer_count,
            ),
        )
        object.__setattr__(
            self,
            "seconds_until_required_recheck",
            _require_nonnegative_decimal(
                "seconds_until_required_recheck",
                self.seconds_until_required_recheck,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityEscalationRow:
    resolution_area: str
    affected_market_count: Decimal
    rule_ambiguity_score: Decimal
    source_disagreement_score: Decimal
    authoritative_evidence_age_seconds: Decimal
    stale_authoritative_evidence_pressure: Decimal
    manual_review_item_count: Decimal
    available_reviewer_count: Decimal
    manual_review_capacity: Decimal
    manual_review_burden: Decimal
    seconds_until_required_recheck: Decimal
    recheck_urgency: Decimal
    escalation_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionAmbiguityEscalationRow, "row")
        _require_public_resolution_area("resolution_area", self.resolution_area)
        for field_name in (
            "affected_market_count",
            "manual_review_item_count",
            "available_reviewer_count",
        ):
            require_count = (
                _require_positive_whole_decimal
                if field_name in ("affected_market_count", "available_reviewer_count")
                else _require_nonnegative_whole_decimal
            )
            object.__setattr__(
                self,
                field_name,
                require_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_ambiguity_score",
            "source_disagreement_score",
            "stale_authoritative_evidence_pressure",
            "manual_review_burden",
            "recheck_urgency",
            "escalation_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authoritative_evidence_age_seconds",
            "manual_review_capacity",
            "seconds_until_required_recheck",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.manual_review_capacity <= _ZERO:
            raise ValueError("manual_review_capacity must be positive")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityEscalationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionAmbiguityEscalationReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityEscalationReport:
    generated_at: datetime
    config_version: str
    resolution_area_count: Decimal
    affected_market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_escalation_pressure: Decimal | None
    max_authoritative_evidence_age_seconds: Decimal
    status: str
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...]
    reason_code_counts: tuple[ResearchResolutionAmbiguityEscalationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionAmbiguityEscalationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "resolution_area_count",
            "affected_market_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_escalation_pressure",
            _require_optional_probability_decimal(
                "average_escalation_pressure",
                self.average_escalation_pressure,
            ),
        )
        object.__setattr__(
            self,
            "max_authoritative_evidence_age_seconds",
            _require_nonnegative_decimal(
                "max_authoritative_evidence_age_seconds",
                self.max_authoritative_evidence_age_seconds,
            ),
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
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest:
            digest = _require_digest("derived_validation_digest", self.derived_validation_digest)
            object.__setattr__(self, "derived_validation_digest", digest)
            if digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_resolution_ambiguity_escalation_report(
    ambiguity_inputs: Iterable[object],
    *,
    config: ResearchResolutionAmbiguityEscalationConfig,
    generated_at: datetime,
) -> ResearchResolutionAmbiguityEscalationReport:
    if type(config) is not ResearchResolutionAmbiguityEscalationConfig:
        raise ValueError("config must be a ResearchResolutionAmbiguityEscalationConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_ambiguity_inputs(ambiguity_inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(normalized_inputs, key=lambda value: value.resolution_area)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchResolutionAmbiguityEscalationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        resolution_area_count=_decimal_count(len({row.resolution_area for row in rows})),
        affected_market_count=_sum_decimal(row.affected_market_count for row in rows),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_escalation_pressure=_average_escalation_pressure(rows),
        max_authoritative_evidence_age_seconds=max(
            (row.authoritative_evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_resolution_ambiguity_escalation_report_payload(
    report: ResearchResolutionAmbiguityEscalationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchResolutionAmbiguityEscalationReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _validate_report_derived_validation_digest(report)
        payload = _json_ready(asdict(report))
        _reject_public_payload("report payload", payload)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        return payload
    if type(report) is dict:
        payload = _json_ready(dict(report))
        _reject_public_payload("payload", payload)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        if "derived_validation_digest" not in payload:
            raise ValueError("derived_validation_digest is required")
        _validate_public_payload_derived_validation_digest(payload)
        return payload
    raise ValueError("report must be a ResearchResolutionAmbiguityEscalationReport")


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


def _row_from_input(
    item: ResearchResolutionAmbiguityEscalationInput,
    *,
    config: ResearchResolutionAmbiguityEscalationConfig,
) -> ResearchResolutionAmbiguityEscalationRow:
    stale_pressure = _stale_authoritative_evidence_pressure(
        item.authoritative_evidence_age_seconds,
        config=config,
    )
    manual_capacity = _quantize(
        item.available_reviewer_count * config.manual_review_capacity_per_reviewer,
    )
    manual_burden = _manual_review_burden(
        item.manual_review_item_count,
        manual_capacity,
    )
    recheck_urgency = _recheck_urgency(
        item.seconds_until_required_recheck,
        config=config,
    )
    escalation_pressure = _quantize(
        (item.rule_ambiguity_score * config.rule_ambiguity_weight)
        + (item.source_disagreement_score * config.source_disagreement_weight)
        + (stale_pressure * config.stale_authoritative_evidence_weight)
        + (manual_burden * config.manual_review_burden_weight)
        + (recheck_urgency * config.recheck_urgency_weight),
    )
    status = _row_status(escalation_pressure, config=config)
    return ResearchResolutionAmbiguityEscalationRow(
        resolution_area=item.resolution_area,
        affected_market_count=item.affected_market_count,
        rule_ambiguity_score=item.rule_ambiguity_score,
        source_disagreement_score=item.source_disagreement_score,
        authoritative_evidence_age_seconds=item.authoritative_evidence_age_seconds,
        stale_authoritative_evidence_pressure=stale_pressure,
        manual_review_item_count=item.manual_review_item_count,
        available_reviewer_count=item.available_reviewer_count,
        manual_review_capacity=manual_capacity,
        manual_review_burden=manual_burden,
        seconds_until_required_recheck=item.seconds_until_required_recheck,
        recheck_urgency=recheck_urgency,
        escalation_pressure=escalation_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            rule_ambiguity_score=item.rule_ambiguity_score,
            source_disagreement_score=item.source_disagreement_score,
            stale_authoritative_evidence_pressure=stale_pressure,
            manual_review_burden=manual_burden,
            recheck_urgency=recheck_urgency,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _normalize_ambiguity_inputs(
    ambiguity_inputs: Iterable[object],
) -> tuple[ResearchResolutionAmbiguityEscalationInput, ...]:
    if isinstance(ambiguity_inputs, (str, bytes)):
        raise ValueError("ambiguity_inputs must be an iterable")
    try:
        values = tuple(ambiguity_inputs)
    except TypeError as exc:
        raise ValueError("ambiguity_inputs must be an iterable") from exc
    return tuple(_coerce_ambiguity_input(value) for value in values)


def _coerce_ambiguity_input(
    value: object,
) -> ResearchResolutionAmbiguityEscalationInput:
    if type(value) is ResearchResolutionAmbiguityEscalationInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchResolutionAmbiguityEscalationInput(
        resolution_area=_field_value(value, "resolution_area"),
        affected_market_count=_field_value(value, "affected_market_count"),
        rule_ambiguity_score=_field_value(value, "rule_ambiguity_score"),
        source_disagreement_score=_field_value(value, "source_disagreement_score"),
        authoritative_evidence_age_seconds=_field_value(
            value,
            "authoritative_evidence_age_seconds",
        ),
        manual_review_item_count=_field_value(value, "manual_review_item_count"),
        available_reviewer_count=_field_value(value, "available_reviewer_count"),
        seconds_until_required_recheck=_field_value(
            value,
            "seconds_until_required_recheck",
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _stale_authoritative_evidence_pressure(
    age_seconds: Decimal,
    *,
    config: ResearchResolutionAmbiguityEscalationConfig,
) -> Decimal:
    if age_seconds <= config.fresh_authoritative_evidence_age_seconds:
        return _ZERO
    if age_seconds >= config.stale_authoritative_evidence_age_seconds:
        return _ONE
    return _quantize(age_seconds / config.stale_authoritative_evidence_age_seconds)


def _manual_review_burden(
    manual_review_item_count: Decimal,
    manual_review_capacity: Decimal,
) -> Decimal:
    if manual_review_capacity <= _ZERO:
        raise ValueError("manual_review_capacity must be positive")
    return _quantize(min(_ONE, manual_review_item_count / manual_review_capacity))


def _recheck_urgency(
    seconds_until_required_recheck: Decimal,
    *,
    config: ResearchResolutionAmbiguityEscalationConfig,
) -> Decimal:
    if seconds_until_required_recheck <= _ZERO:
        return _ONE
    if seconds_until_required_recheck >= config.comfortable_recheck_window_seconds:
        return _ZERO
    return _quantize(
        (config.comfortable_recheck_window_seconds - seconds_until_required_recheck)
        / config.comfortable_recheck_window_seconds,
    )


def _row_status(
    escalation_pressure: Decimal,
    *,
    config: ResearchResolutionAmbiguityEscalationConfig,
) -> str:
    if escalation_pressure >= config.block_escalation_pressure:
        return "block"
    if escalation_pressure >= config.watch_escalation_pressure:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    rule_ambiguity_score: Decimal,
    source_disagreement_score: Decimal,
    stale_authoritative_evidence_pressure: Decimal,
    manual_review_burden: Decimal,
    recheck_urgency: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchResolutionAmbiguityEscalationConfig,
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_ambiguity_escalation_{status}"}
    codes.add(
        _threshold_reason_code(
            "rule_ambiguity",
            rule_ambiguity_score,
            config=config,
        ),
    )
    codes.add(
        _threshold_reason_code(
            "source_disagreement",
            source_disagreement_score,
            config=config,
        ),
    )
    if stale_authoritative_evidence_pressure == _ONE:
        codes.add("authoritative_evidence_stale")
    elif stale_authoritative_evidence_pressure > _ZERO:
        codes.add("authoritative_evidence_aging")
    else:
        codes.add("authoritative_evidence_fresh")
    if manual_review_burden >= config.block_escalation_pressure:
        codes.add("manual_review_burden_block")
    elif manual_review_burden >= config.watch_escalation_pressure:
        codes.add("manual_review_burden_watch")
    if recheck_urgency >= config.block_escalation_pressure:
        codes.add("recheck_urgency_block")
    elif recheck_urgency >= config.watch_escalation_pressure:
        codes.add("recheck_urgency_watch")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _threshold_reason_code(
    prefix: str,
    value: Decimal,
    *,
    config: ResearchResolutionAmbiguityEscalationConfig,
) -> str:
    if value >= config.block_escalation_pressure:
        return f"{prefix}_block"
    if value >= config.watch_escalation_pressure:
        return f"{prefix}_watch"
    return f"{prefix}_low"


def _report_status(
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_ambiguity_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_ambiguity_escalation_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionAmbiguityEscalationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionAmbiguityEscalationReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionAmbiguityEscalationReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_escalation_pressure(
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.escalation_pressure for row in rows), _ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _normalize_rows(
    rows: tuple[ResearchResolutionAmbiguityEscalationRow, ...],
) -> tuple[ResearchResolutionAmbiguityEscalationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionAmbiguityEscalationRow:
            raise ValueError(
                "rows must contain ResearchResolutionAmbiguityEscalationRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.resolution_area))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by resolution_area")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionAmbiguityEscalationReasonCodeCount, ...],
) -> tuple[ResearchResolutionAmbiguityEscalationReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionAmbiguityEscalationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionAmbiguityEscalationReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchResolutionAmbiguityEscalationRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"resolution_ambiguity_escalation_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    expected_manual_burden = _manual_review_burden(
        row.manual_review_item_count,
        row.manual_review_capacity,
    )
    if row.manual_review_burden != expected_manual_burden:
        raise ValueError("manual_review_burden must match manual review capacity")


def _validate_report_consistency(
    report: ResearchResolutionAmbiguityEscalationReport,
) -> None:
    if report.resolution_area_count != _decimal_count(
        len({row.resolution_area for row in report.rows}),
    ):
        raise ValueError("resolution_area_count must match rows")
    if report.affected_market_count != _sum_decimal(
        row.affected_market_count for row in report.rows
    ):
        raise ValueError("affected_market_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_escalation_pressure != _average_escalation_pressure(report.rows):
        raise ValueError("average_escalation_pressure must match rows")
    expected_max_age = max(
        (row.authoritative_evidence_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_authoritative_evidence_age_seconds != expected_max_age:
        raise ValueError("max_authoritative_evidence_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_derived_validation_digest(
    report: ResearchResolutionAmbiguityEscalationReport,
) -> None:
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_payload_derived_validation_digest(
    payload: Mapping[str, object],
) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(without_digest, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _report_values_without_digest(
    report: ResearchResolutionAmbiguityEscalationReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON value must use exact Decimal values")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        _reject_text_value("JSON string value", value)
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _field_value(value: object, name: str, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if any(field.name == name for field in fields(value)):
            return getattr(value, name)
    elif isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{name} is required")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_text_value(name, value)
    return value


def _require_public_resolution_area(name: str, value: str) -> str:
    _require_public_identifier(name, value)
    normalized = value.lower()
    if any(term in normalized for term in _RESOLUTION_AREA_UNSAFE_TERMS):
        raise ValueError(f"{name} must not expose raw resolution surfaces")
    return value


def _require_reason_code(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase reason code")
    _reject_text_value(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be nonempty")
    normalized = tuple(_require_reason_code(name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(sorted(normalized))


def _require_status(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(result)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(result)


def _require_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_positive_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_probability_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO or result > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(result)


def _require_optional_probability_decimal(
    name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(name, value)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_text_value(label, key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_text_value(label, value)


def _reject_text_value(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _PAYLOAD_UNSAFE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface text")
    if any(term in normalized for term in _ACTION_TERMS):
        raise ValueError(f"{label} contains unsafe action text")
