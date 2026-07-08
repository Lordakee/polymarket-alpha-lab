"""Report-only probability edge-case audit.

This module is deterministic and side-effect free. It turns typed boundary
signals into a public audit report and compact digest for human review only.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_RESEARCH_PROBABILITY_EDGE_CASE_AUDIT_CONFIG_VERSION = (
    "research-probability-edge-case-audit-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_EDGE_CASE_AUDIT_CONFIG_VERSION",
    "ResearchProbabilityEdgeCaseAuditConfig",
    "ResearchProbabilityEdgeCaseAuditInput",
    "ResearchProbabilityEdgeCaseAuditPublicDigest",
    "ResearchProbabilityEdgeCaseAuditReport",
    "ResearchProbabilityEdgeCaseAuditRow",
    "build_research_probability_edge_case_audit_report",
    "research_probability_edge_case_audit_digest",
    "research_probability_edge_case_audit_digest_payload",
    "research_probability_edge_case_audit_report_payload",
)


STATUSES = frozenset(("pass", "watch", "block"))
STATUS_SEVERITY = {"block": 2, "watch": 1, "pass": 0}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "condition_id",
        "dsn",
        "market",
        "order",
        "position",
        "question",
        "recommend",
        "ref",
        "slug",
        "source",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)
UNSAFE_ADVICE_FRAGMENTS = frozenset(
    (
        "buy ",
        "buying ",
        "sell ",
        "selling ",
        "place order",
        "take position",
    ),
)


@dataclass(frozen=True)
class ResearchProbabilityEdgeCaseAuditConfig:
    config_version: str = DEFAULT_RESEARCH_PROBABILITY_EDGE_CASE_AUDIT_CONFIG_VERSION
    watch_extreme_probability_tail_threshold: Decimal = Decimal("0.050000")
    block_extreme_probability_tail_threshold: Decimal = Decimal("0.010000")
    min_pass_liquidity_score: Decimal = Decimal("0.500000")
    min_watch_liquidity_score: Decimal = Decimal("0.200000")
    watch_short_settlement_hours: Decimal = Decimal("24.000000")
    block_short_settlement_hours: Decimal = Decimal("6.000000")
    watch_evidence_conflict_score: Decimal = Decimal("0.500000")
    block_evidence_conflict_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeCaseAuditConfig:
            raise ValueError("config must be exactly ResearchProbabilityEdgeCaseAuditConfig")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_extreme_probability_tail_threshold",
            "block_extreme_probability_tail_threshold",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "watch_evidence_conflict_score",
            "block_evidence_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_short_settlement_hours",
            "block_short_settlement_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.block_extreme_probability_tail_threshold
            >= self.watch_extreme_probability_tail_threshold
        ):
            raise ValueError(
                "block_extreme_probability_tail_threshold must be less than "
                "watch_extreme_probability_tail_threshold",
            )
        if self.min_watch_liquidity_score >= self.min_pass_liquidity_score:
            raise ValueError(
                "min_watch_liquidity_score must be less than min_pass_liquidity_score",
            )
        if self.block_short_settlement_hours >= self.watch_short_settlement_hours:
            raise ValueError(
                "block_short_settlement_hours must be less than watch_short_settlement_hours",
            )
        if self.watch_evidence_conflict_score >= self.block_evidence_conflict_score:
            raise ValueError(
                "block_evidence_conflict_score must be greater than "
                "watch_evidence_conflict_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeCaseAuditInput:
    audit_key: str
    model_probability: Decimal
    liquidity_score: Decimal
    settlement_hours: Decimal
    evidence_conflict_score: Decimal
    observed_at: datetime
    public_summary: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeCaseAuditInput:
            raise ValueError("input must be exactly ResearchProbabilityEdgeCaseAuditInput")
        _require_public_slug("audit_key", self.audit_key)
        for field_name in (
            "model_probability",
            "liquidity_score",
            "evidence_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_hours",
            _require_nonnegative_decimal("settlement_hours", self.settlement_hours),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_public_string("public_summary", self.public_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeCaseAuditRow:
    audit_key: str
    observed_at: datetime
    model_probability: Decimal
    probability_tail_distance: Decimal
    liquidity_score: Decimal
    settlement_hours: Decimal
    evidence_conflict_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    public_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeCaseAuditRow:
            raise ValueError("row must be exactly ResearchProbabilityEdgeCaseAuditRow")
        _require_public_slug("audit_key", self.audit_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "probability_tail_distance",
            "liquidity_score",
            "evidence_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_hours",
            _require_nonnegative_decimal("settlement_hours", self.settlement_hours),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_public_string("public_summary", self.public_summary)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeCaseAuditReport:
    generated_at: datetime
    config_version: str
    status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    extreme_probability_count: Decimal
    low_liquidity_count: Decimal
    short_settlement_count: Decimal
    conflict_evidence_count: Decimal
    rows: tuple[ResearchProbabilityEdgeCaseAuditRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeCaseAuditReport:
            raise ValueError("report must be exactly ResearchProbabilityEdgeCaseAuditReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "extreme_probability_count",
            "low_liquidity_count",
            "short_settlement_count",
            "conflict_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeCaseAuditPublicDigest:
    generated_at: datetime
    config_version: str
    status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    extreme_probability_count: Decimal
    low_liquidity_count: Decimal
    short_settlement_count: Decimal
    conflict_evidence_count: Decimal
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeCaseAuditPublicDigest:
            raise ValueError("digest must be exactly ResearchProbabilityEdgeCaseAuditPublicDigest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "extreme_probability_count",
            "low_liquidity_count",
            "short_settlement_count",
            "conflict_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
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
        _require_hard_flags("digest", self)


def build_research_probability_edge_case_audit_report(
    rows: Iterable[object],
    *,
    config: ResearchProbabilityEdgeCaseAuditConfig,
    generated_at: datetime,
) -> ResearchProbabilityEdgeCaseAuditReport:
    if type(config) is not ResearchProbabilityEdgeCaseAuditConfig:
        raise ValueError("config must be a ResearchProbabilityEdgeCaseAuditConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    for row in input_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("rows observed_at must not be after generated_at")
    report_rows = tuple(
        sorted((_build_row(row, config) for row in input_rows), key=_row_sort_key),
    )
    reason_codes = _report_reason_codes(report_rows)
    return ResearchProbabilityEdgeCaseAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_summary_status(reason_codes),
        case_count=_decimal_count(len(report_rows)),
        pass_count=_decimal_count(_status_count(report_rows, "pass")),
        watch_count=_decimal_count(_status_count(report_rows, "watch")),
        block_count=_decimal_count(_status_count(report_rows, "block")),
        extreme_probability_count=_decimal_count(_factor_count(report_rows, "extreme_probability")),
        low_liquidity_count=_decimal_count(_factor_count(report_rows, "low_liquidity")),
        short_settlement_count=_decimal_count(_factor_count(report_rows, "short_settlement")),
        conflict_evidence_count=_decimal_count(_factor_count(report_rows, "evidence_conflict")),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_probability_edge_case_audit_digest(
    report: ResearchProbabilityEdgeCaseAuditReport,
) -> ResearchProbabilityEdgeCaseAuditPublicDigest:
    if type(report) is not ResearchProbabilityEdgeCaseAuditReport:
        raise ValueError("report must be a ResearchProbabilityEdgeCaseAuditReport")
    _require_hard_flags("report", report)
    return ResearchProbabilityEdgeCaseAuditPublicDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        case_count=report.case_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        extreme_probability_count=report.extreme_probability_count,
        low_liquidity_count=report.low_liquidity_count,
        short_settlement_count=report.short_settlement_count,
        conflict_evidence_count=report.conflict_evidence_count,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
    )


def research_probability_edge_case_audit_report_payload(
    report: ResearchProbabilityEdgeCaseAuditReport,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilityEdgeCaseAuditReport:
        raise ValueError("report must be a ResearchProbabilityEdgeCaseAuditReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def research_probability_edge_case_audit_digest_payload(
    digest: ResearchProbabilityEdgeCaseAuditPublicDigest,
) -> dict[str, Any]:
    if type(digest) is not ResearchProbabilityEdgeCaseAuditPublicDigest:
        raise ValueError("digest must be a ResearchProbabilityEdgeCaseAuditPublicDigest")
    _require_hard_flags("digest", digest)
    payload = _json_ready(digest)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest payload", payload)
    return payload


def _build_row(
    row: ResearchProbabilityEdgeCaseAuditInput,
    config: ResearchProbabilityEdgeCaseAuditConfig,
) -> ResearchProbabilityEdgeCaseAuditRow:
    tail_distance = _probability_tail_distance(row.model_probability)
    status = _row_status(
        probability_tail_distance=tail_distance,
        liquidity_score=row.liquidity_score,
        settlement_hours=row.settlement_hours,
        evidence_conflict_score=row.evidence_conflict_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        input_reason_codes=row.reason_codes,
        status=status,
        probability_tail_distance=tail_distance,
        liquidity_score=row.liquidity_score,
        settlement_hours=row.settlement_hours,
        evidence_conflict_score=row.evidence_conflict_score,
        config=config,
    )
    return ResearchProbabilityEdgeCaseAuditRow(
        audit_key=row.audit_key,
        observed_at=row.observed_at,
        model_probability=row.model_probability,
        probability_tail_distance=tail_distance,
        liquidity_score=row.liquidity_score,
        settlement_hours=row.settlement_hours,
        evidence_conflict_score=row.evidence_conflict_score,
        status=status,
        reason_codes=reason_codes,
        public_summary=row.public_summary,
    )


def _row_status(
    *,
    probability_tail_distance: Decimal,
    liquidity_score: Decimal,
    settlement_hours: Decimal,
    evidence_conflict_score: Decimal,
    config: ResearchProbabilityEdgeCaseAuditConfig,
) -> str:
    if (
        probability_tail_distance <= config.block_extreme_probability_tail_threshold
        or liquidity_score < config.min_watch_liquidity_score
        or settlement_hours <= config.block_short_settlement_hours
        or evidence_conflict_score >= config.block_evidence_conflict_score
    ):
        return "block"
    if (
        probability_tail_distance <= config.watch_extreme_probability_tail_threshold
        or liquidity_score < config.min_pass_liquidity_score
        or settlement_hours <= config.watch_short_settlement_hours
        or evidence_conflict_score >= config.watch_evidence_conflict_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    input_reason_codes: tuple[str, ...],
    status: str,
    probability_tail_distance: Decimal,
    liquidity_score: Decimal,
    settlement_hours: Decimal,
    evidence_conflict_score: Decimal,
    config: ResearchProbabilityEdgeCaseAuditConfig,
) -> tuple[str, ...]:
    reasons = list(input_reason_codes)
    reasons.append(f"edge_case_audit_{status}")
    if probability_tail_distance <= (
        config.block_extreme_probability_tail_threshold
        if status == "block"
        else config.watch_extreme_probability_tail_threshold
    ):
        reasons.append(f"extreme_probability_{status}")
    if liquidity_score < (
        config.min_watch_liquidity_score
        if status == "block"
        else config.min_pass_liquidity_score
    ):
        reasons.append(f"low_liquidity_{status}")
    if settlement_hours <= (
        config.block_short_settlement_hours
        if status == "block"
        else config.watch_short_settlement_hours
    ):
        reasons.append(f"short_settlement_{status}")
    if evidence_conflict_score >= (
        config.block_evidence_conflict_score
        if status == "block"
        else config.watch_evidence_conflict_score
    ):
        reasons.append(f"evidence_conflict_{status}")
    return tuple(sorted(dict.fromkeys(reasons)))


def _report_reason_codes(rows: tuple[ResearchProbabilityEdgeCaseAuditRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("edge_case_audit_missing_inputs",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if "edge_case_audit_missing_inputs" in reason_codes:
        return "block"
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchProbabilityEdgeCaseAuditRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        counter = Counter(report_reason_codes)
    else:
        counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        (reason_code, _decimal_count(counter[reason_code]))
        for reason_code in sorted(counter)
    )


def _status_count(rows: tuple[ResearchProbabilityEdgeCaseAuditRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _factor_count(rows: tuple[ResearchProbabilityEdgeCaseAuditRow, ...], factor: str) -> int:
    return sum(
        1
        for row in rows
        if f"{factor}_watch" in row.reason_codes or f"{factor}_block" in row.reason_codes
    )


def _row_sort_key(row: ResearchProbabilityEdgeCaseAuditRow) -> tuple[int, str]:
    return (-STATUS_SEVERITY[row.status], row.audit_key)


def _normalize_input_rows(
    value: Iterable[object],
) -> tuple[ResearchProbabilityEdgeCaseAuditInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityEdgeCaseAuditInput:
            raise ValueError("rows must contain ResearchProbabilityEdgeCaseAuditInput values")
        _require_hard_flags("rows", row)
        if row.audit_key in seen:
            raise ValueError("rows must contain unique audit_key values")
        seen.add(row.audit_key)
    return rows


def _normalize_rows(
    value: Iterable[ResearchProbabilityEdgeCaseAuditRow],
) -> tuple[ResearchProbabilityEdgeCaseAuditRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityEdgeCaseAuditRow:
            raise ValueError("rows must contain ResearchProbabilityEdgeCaseAuditRow values")
        _require_hard_flags("rows", row)
        if row.audit_key in seen:
            raise ValueError("rows must contain unique audit_key values")
        seen.add(row.audit_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and audit_key")
    return rows


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
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = row
        _require_reason_code("reason_code_counts reason_code", reason_code)
        normalized.append(
            (
                reason_code,
                _require_positive_count_decimal("reason_code_counts count", count),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result, key=lambda item: item[0])):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return result


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return reason_codes


def _validate_row_consistency(row: ResearchProbabilityEdgeCaseAuditRow) -> None:
    if row.probability_tail_distance != _probability_tail_distance(row.model_probability):
        raise ValueError("probability_tail_distance must match model_probability")
    if f"edge_case_audit_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(report: ResearchProbabilityEdgeCaseAuditReport) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.extreme_probability_count != _decimal_count(_factor_count(report.rows, "extreme_probability")):
        raise ValueError("extreme_probability_count must match rows")
    if report.low_liquidity_count != _decimal_count(_factor_count(report.rows, "low_liquidity")):
        raise ValueError("low_liquidity_count must match rows")
    if report.short_settlement_count != _decimal_count(_factor_count(report.rows, "short_settlement")):
        raise ValueError("short_settlement_count must match rows")
    if report.conflict_evidence_count != _decimal_count(_factor_count(report.rows, "evidence_conflict")):
        raise ValueError("conflict_evidence_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _probability_tail_distance(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(min(value, ONE - value))


def _json_ready(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value, key if not path else f"{path}.{key}")
            for key, nested_value in asdict(value).items()
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) is str:
        _reject_unsafe_public_string(path or "value", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("payload key", key)
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(field_name: str, value: Any) -> None:
    _json_ready(value, field_name)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_slug(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    assert type(value) is str
    for character in value:
        if not (character.islower() or character.isdigit() or character in ("-", "_")):
            raise ValueError(f"{field_name} must contain only public slug characters")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be a single-line string")
    _reject_unsafe_public_string(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be a single-line string")
    if any(fragment in value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must contain only public reason-code characters")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")
    if any(fragment in lowered for fragment in UNSAFE_ADVICE_FRAGMENTS):
        raise ValueError(f"{field_name} contains trading or recommendation language")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
