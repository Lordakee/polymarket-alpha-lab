"""Deterministic report-only research decision audit summary.

This module aggregates already-redacted research audit signals for human
review. It does not fetch, persist, mutate state, or provide execution advice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any, Sequence


__all__ = (
    "DEFAULT_RESEARCH_DECISION_AUDIT_SUMMARY_CONFIG_VERSION",
    "ResearchDecisionAuditSummaryConfig",
    "ResearchDecisionAuditComponentSignal",
    "ResearchDecisionAuditSummaryRow",
    "ResearchDecisionAuditReasonCodeCount",
    "ResearchDecisionAuditSummaryReport",
    "build_research_decision_audit_summary",
    "research_decision_audit_summary_payload",
)


DEFAULT_RESEARCH_DECISION_AUDIT_SUMMARY_CONFIG_VERSION = (
    "research-decision-audit-summary-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

COMPONENTS = (
    "decision_change_log",
    "quality_assurance",
    "execution_boundary",
    "evidence_quality",
)
STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_COMPONENT_RANK = {
    "decision_change_log": Decimal("1.000000"),
    "quality_assurance": Decimal("2.000000"),
    "execution_boundary": Decimal("3.000000"),
    "evidence_quality": Decimal("4.000000"),
}

PASS_REASON = "research_decision_audit_pass"
WATCH_REASON = "research_decision_audit_watch"
BLOCK_REASON = "research_decision_audit_block"
MISSING_COMPONENT_REASON = "missing_required_audit_component"
COMPONENT_ISSUE_WATCH_REASON = "audit_component_issue_watch"
COMPONENT_ISSUE_BLOCK_REASON = "audit_component_issue_block"
INPUT_STATUS_WATCH_REASON = "input_status_watch"
INPUT_STATUS_BLOCK_REASON = "input_status_block"
SEVERITY_WATCH_REASON = "audit_severity_score_watch"
SEVERITY_BLOCK_REASON = "audit_severity_score_block"

ROW_REASON_CODES = (
    COMPONENT_ISSUE_BLOCK_REASON,
    INPUT_STATUS_BLOCK_REASON,
    SEVERITY_BLOCK_REASON,
    COMPONENT_ISSUE_WATCH_REASON,
    INPUT_STATUS_WATCH_REASON,
    SEVERITY_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    MISSING_COMPONENT_REASON,
    COMPONENT_ISSUE_BLOCK_REASON,
    INPUT_STATUS_BLOCK_REASON,
    SEVERITY_BLOCK_REASON,
    COMPONENT_ISSUE_WATCH_REASON,
    INPUT_STATUS_WATCH_REASON,
    SEVERITY_WATCH_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
)
_REASON_ORDER = {
    MISSING_COMPONENT_REASON: Decimal("0.000000"),
    COMPONENT_ISSUE_BLOCK_REASON: Decimal("10.000000"),
    INPUT_STATUS_BLOCK_REASON: Decimal("20.000000"),
    SEVERITY_BLOCK_REASON: Decimal("30.000000"),
    COMPONENT_ISSUE_WATCH_REASON: Decimal("40.000000"),
    INPUT_STATUS_WATCH_REASON: Decimal("50.000000"),
    SEVERITY_WATCH_REASON: Decimal("60.000000"),
    PASS_REASON: Decimal("80.000000"),
    WATCH_REASON: Decimal("90.000000"),
    BLOCK_REASON: Decimal("100.000000"),
}
_INPUT_REASON_ORDER = Decimal("70.000000")

_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw candidate",
        "raw-candidate",
        "raw_candidate",
        "candidate_id",
        "candidate id",
        "market_id",
        "market id",
        "market_slug",
        "market slug",
        "question",
        "source_ref",
        "source ref",
        "source_url",
        "source url",
        "source_text",
        "source text",
        "://",
        "www.",
        "url",
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
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchDecisionAuditSummaryConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_DECISION_AUDIT_SUMMARY_CONFIG_VERSION
    watch_audit_severity_score: Decimal = Decimal("0.250000")
    block_audit_severity_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDecisionAuditSummaryConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DECISION_AUDIT_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_audit_severity_score",
            _require_ratio_decimal(
                "watch_audit_severity_score",
                self.watch_audit_severity_score,
            ),
        )
        object.__setattr__(
            self,
            "block_audit_severity_score",
            _require_ratio_decimal(
                "block_audit_severity_score",
                self.block_audit_severity_score,
            ),
        )
        if self.block_audit_severity_score < self.watch_audit_severity_score:
            raise ValueError(
                "block_audit_severity_score must be at least watch_audit_severity_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDecisionAuditComponentSignal(_FinalPublicDataclass):
    component: str
    status: str
    audited_item_count: Decimal
    issue_count: Decimal
    audit_severity_score: Decimal
    reason_codes: tuple[str, ...] = ()
    public_summary: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDecisionAuditComponentSignal, "component signal")
        object.__setattr__(
            self,
            "component",
            _require_member("component", self.component, COMPONENTS),
        )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "audited_item_count",
            _require_nonnegative_count_decimal(
                "audited_item_count",
                self.audited_item_count,
            ),
        )
        object.__setattr__(
            self,
            "issue_count",
            _require_nonnegative_count_decimal("issue_count", self.issue_count),
        )
        object.__setattr__(
            self,
            "audit_severity_score",
            _require_ratio_decimal("audit_severity_score", self.audit_severity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_summary",
            _normalize_optional_public_text("public_summary", self.public_summary),
        )
        if self.issue_count > self.audited_item_count:
            raise ValueError("issue_count must not exceed audited_item_count")
        _require_hard_flags("component signal", self)
        _reject_unsafe_public_payload("component signal", self)


@dataclass(frozen=True)
class ResearchDecisionAuditSummaryRow(_FinalPublicDataclass):
    component_key: str
    component: str
    component_rank: Decimal
    status: str
    status_rank: Decimal
    audited_item_count: Decimal
    issue_count: Decimal
    audit_severity_score: Decimal
    reason_codes: tuple[str, ...]
    public_summary: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDecisionAuditSummaryRow, "row")
        _require_public_identifier("component_key", self.component_key)
        object.__setattr__(
            self,
            "component",
            _require_member("component", self.component, COMPONENTS),
        )
        object.__setattr__(
            self,
            "component_rank",
            _require_positive_count_decimal("component_rank", self.component_rank),
        )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "status_rank",
            _require_nonnegative_count_decimal("status_rank", self.status_rank),
        )
        object.__setattr__(
            self,
            "audited_item_count",
            _require_nonnegative_count_decimal(
                "audited_item_count",
                self.audited_item_count,
            ),
        )
        object.__setattr__(
            self,
            "issue_count",
            _require_nonnegative_count_decimal("issue_count", self.issue_count),
        )
        object.__setattr__(
            self,
            "audit_severity_score",
            _require_ratio_decimal("audit_severity_score", self.audit_severity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_summary",
            _normalize_optional_public_text("public_summary", self.public_summary),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDecisionAuditReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    component_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDecisionAuditReasonCodeCount, "reason code count")
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "component_ratio",
            _require_ratio_decimal("component_ratio", self.component_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchDecisionAuditSummaryReport(_FinalPublicDataclass):
    config_version: str
    status: str
    required_component_count: Decimal
    observed_component_count: Decimal
    missing_component_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_audited_item_count: Decimal
    total_issue_count: Decimal
    max_audit_severity_score: Decimal
    average_audit_severity_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDecisionAuditReasonCodeCount, ...]
    rows: tuple[ResearchDecisionAuditSummaryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDecisionAuditSummaryReport, "report")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DECISION_AUDIT_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        for field_name in (
            "required_component_count",
            "observed_component_count",
            "missing_component_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_audited_item_count",
            "total_issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_audit_severity_score", "average_audit_severity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest mismatch")
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_decision_audit_summary_payload(self)


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


def build_research_decision_audit_summary(
    signals: Sequence[ResearchDecisionAuditComponentSignal],
    *,
    config: ResearchDecisionAuditSummaryConfig,
) -> ResearchDecisionAuditSummaryReport:
    """Build a deterministic human-review summary from redacted audit signals."""

    if type(config) is not ResearchDecisionAuditSummaryConfig:
        raise ValueError("config must be a ResearchDecisionAuditSummaryConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    items = _normalize_component_signals(signals)
    signal_by_component = _component_signal_map(items)
    rows = tuple(
        _row_from_component(
            component,
            signal_by_component[component],
            config=config,
            index=index,
        )
        for index, component in enumerate(COMPONENTS, start=1)
        if component in signal_by_component
    )
    missing_component_count = _count_decimal(
        sum(1 for component in COMPONENTS if component not in signal_by_component),
    )
    reason_codes = _report_reason_codes(rows, missing_component_count)
    return ResearchDecisionAuditSummaryReport(
        config_version=config.config_version,
        status=_report_status(rows, missing_component_count),
        required_component_count=_count_decimal(len(COMPONENTS)),
        observed_component_count=_count_decimal(len(rows)),
        missing_component_count=missing_component_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_audited_item_count=sum((row.audited_item_count for row in rows), _ZERO),
        total_issue_count=sum((row.issue_count for row in rows), _ZERO),
        max_audit_severity_score=max(
            (row.audit_severity_score for row in rows),
            default=_ZERO,
        ),
        average_audit_severity_score=_average_score(
            tuple(row.audit_severity_score for row in rows),
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
    )


def research_decision_audit_summary_payload(
    value: ResearchDecisionAuditSummaryReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchDecisionAuditSummaryReport:
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchDecisionAuditSummaryReport or dict")
    _validate_public_payload(payload)
    return payload


def _row_from_component(
    component: str,
    signal: ResearchDecisionAuditComponentSignal,
    *,
    config: ResearchDecisionAuditSummaryConfig,
    index: int,
) -> ResearchDecisionAuditSummaryRow:
    reason_codes = _row_reason_codes(signal, config=config)
    status = _row_status(reason_codes)
    return ResearchDecisionAuditSummaryRow(
        component_key=f"redacted-decision-audit-{index:03d}",
        component=component,
        component_rank=_COMPONENT_RANK[component],
        status=status,
        status_rank=_STATUS_RANK[status],
        audited_item_count=signal.audited_item_count,
        issue_count=signal.issue_count,
        audit_severity_score=signal.audit_severity_score,
        reason_codes=reason_codes,
        public_summary=signal.public_summary,
    )


def _row_reason_codes(
    signal: ResearchDecisionAuditComponentSignal,
    *,
    config: ResearchDecisionAuditSummaryConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.issue_count > _ZERO:
        reasons.append(
            COMPONENT_ISSUE_BLOCK_REASON
            if signal.status == "block"
            else COMPONENT_ISSUE_WATCH_REASON,
        )
    if signal.status == "block":
        reasons.append(INPUT_STATUS_BLOCK_REASON)
    elif signal.status == "watch":
        reasons.append(INPUT_STATUS_WATCH_REASON)
    if signal.audit_severity_score >= config.block_audit_severity_score:
        reasons.append(SEVERITY_BLOCK_REASON)
    elif signal.audit_severity_score >= config.watch_audit_severity_score:
        reasons.append(SEVERITY_WATCH_REASON)
    reasons.extend(f"input_{reason_code}" for reason_code in signal.reason_codes)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_row_reason_codes("reason_codes", tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchDecisionAuditSummaryRow, ...],
    missing_component_count: Decimal,
) -> str:
    if missing_component_count > _ZERO or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDecisionAuditSummaryRow, ...],
    missing_component_count: Decimal,
) -> tuple[str, ...]:
    if missing_component_count > _ZERO:
        return (MISSING_COMPONENT_REASON, BLOCK_REASON)
    if any(row.status == "block" for row in rows):
        row_reasons = tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != PASS_REASON
        )
        return _normalize_report_reason_codes(
            "reason_codes",
            (*row_reasons, BLOCK_REASON),
        )
    if any(row.status == "watch" for row in rows):
        row_reasons = tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != PASS_REASON
        )
        return _normalize_report_reason_codes(
            "reason_codes",
            (*row_reasons, WATCH_REASON),
        )
    return (PASS_REASON,)


def _status_count(rows: tuple[ResearchDecisionAuditSummaryRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _count_decimal(len(values)))


def _normalize_component_signals(
    value: Sequence[ResearchDecisionAuditComponentSignal],
) -> tuple[ResearchDecisionAuditComponentSignal, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    items = tuple(value)
    for item in items:
        if type(item) is not ResearchDecisionAuditComponentSignal:
            raise ValueError("signals must contain ResearchDecisionAuditComponentSignal items")
        _require_hard_flags("component signal", item)
        _reject_unsafe_public_payload("component signal", item)
    return items


def _component_signal_map(
    items: tuple[ResearchDecisionAuditComponentSignal, ...],
) -> dict[str, ResearchDecisionAuditComponentSignal]:
    signal_by_component: dict[str, ResearchDecisionAuditComponentSignal] = {}
    for item in sorted(items, key=lambda signal: _COMPONENT_RANK[signal.component]):
        if item.component in signal_by_component:
            raise ValueError("duplicate component signals are not allowed")
        signal_by_component[item.component] = item
    return signal_by_component


def _normalize_rows(
    value: Sequence[ResearchDecisionAuditSummaryRow],
) -> tuple[ResearchDecisionAuditSummaryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDecisionAuditSummaryRow:
            raise ValueError("rows must contain ResearchDecisionAuditSummaryRow items")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.component in seen:
            raise ValueError("rows must not contain duplicate components")
        seen.add(row.component)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.component_rank))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by component_rank")
    return rows


def _normalize_reason_code_counts(
    value: Sequence[ResearchDecisionAuditReasonCodeCount],
) -> tuple[ResearchDecisionAuditReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchDecisionAuditReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchDecisionAuditReasonCodeCount items",
            )
        _require_hard_flags("reason code count", row)
        _reject_unsafe_public_payload("reason code count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: _reason_code_sort_key(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchDecisionAuditReasonCodeCount, ...]:
    denominator = _count_decimal(len(reason_codes))
    return tuple(
        ResearchDecisionAuditReasonCodeCount(
            reason_code=reason_code,
            count=_ONE,
            component_ratio=_quantize(_ONE / denominator),
        )
        for reason_code in reason_codes
    )


def _validate_row(row: ResearchDecisionAuditSummaryRow) -> None:
    if row.component_rank != _COMPONENT_RANK[row.component]:
        raise ValueError("component_rank must match component")
    if row.status_rank != _STATUS_RANK[row.status]:
        raise ValueError("status_rank must match status")
    if row.issue_count > row.audited_item_count:
        raise ValueError("issue_count must not exceed audited_item_count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchDecisionAuditSummaryReport) -> None:
    if report.required_component_count != _count_decimal(len(COMPONENTS)):
        raise ValueError("required_component_count must match required components")
    if report.observed_component_count != _count_decimal(len(report.rows)):
        raise ValueError("observed_component_count must match rows")
    expected_missing = _count_decimal(len(COMPONENTS) - len(report.rows))
    if report.missing_component_count != expected_missing:
        raise ValueError("missing_component_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_audited_item_count != sum(
        (row.audited_item_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("total_audited_item_count must match rows")
    if report.total_issue_count != sum((row.issue_count for row in report.rows), _ZERO):
        raise ValueError("total_issue_count must match rows")
    expected_max = max((row.audit_severity_score for row in report.rows), default=_ZERO)
    if report.max_audit_severity_score != expected_max:
        raise ValueError("max_audit_severity_score must match rows")
    if report.average_audit_severity_score != _average_score(
        tuple(row.audit_severity_score for row in report.rows),
    ):
        raise ValueError("average_audit_severity_score must match rows")
    if report.status != _report_status(report.rows, report.missing_component_count):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        report.missing_component_count,
    ):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _report_payload(report: ResearchDecisionAuditSummaryReport) -> dict[str, object]:
    return _json_ready(asdict(report))


def _report_digest(report: ResearchDecisionAuditSummaryReport) -> str:
    payload = dict(_report_payload(report))
    payload["derived_validation_digest"] = ""
    return sha256(
        json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()


def _validate_public_payload(payload: dict[str, object]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    payload_digest = payload.get("derived_validation_digest")
    if type(payload_digest) is not str or not _DIGEST_RE.fullmatch(payload_digest):
        raise ValueError("derived_validation_digest must be a hex digest")
    canonical_payload = dict(payload)
    canonical_payload["derived_validation_digest"] = ""
    expected_digest = sha256(
        json.dumps(
            canonical_payload,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    if payload_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(value, allow_nan=False, sort_keys=True))
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal values must be exact Decimal")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _require_exact_type(value: object, expected: type[object], label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    _reject_public_string(field_name, value)
    return value


def _normalize_input_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_public_identifier(field_name, item)
        normalized.append(item)
    return tuple(sorted(set(normalized)))


def _normalize_row_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    return _normalize_ordered_reason_codes(value, ROW_REASON_CODES, field_name=field_name)


def _normalize_report_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    return _normalize_ordered_reason_codes(value, REPORT_REASON_CODES, field_name=field_name)


def _normalize_ordered_reason_codes(
    value: object,
    allowed: tuple[str, ...],
    *,
    field_name: str = "reason_codes",
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    allowed_set = set(allowed)
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if reason_code.startswith("input_"):
            _require_public_identifier(field_name, reason_code)
        elif reason_code not in allowed_set:
            raise ValueError(f"{field_name} contains unsupported reason code")
        normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    unique = tuple(dict.fromkeys(normalized))
    return tuple(sorted(unique, key=_reason_code_sort_key))


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.startswith("input_"):
        _require_public_identifier(field_name, value)
        return value
    if value not in REPORT_REASON_CODES:
        raise ValueError(f"{field_name} must be supported")
    return value


def _reason_code_sort_key(reason_code: str) -> tuple[Decimal, str]:
    if reason_code in _REASON_ORDER:
        return (_REASON_ORDER[reason_code], reason_code)
    if reason_code.startswith("input_"):
        return (_INPUT_REASON_ORDER, reason_code)
    return (Decimal("999.000000"), reason_code)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a hex digest")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _required_attr(value: object, field_name: str) -> object:
    if isinstance(value, _PayloadFlags):
        return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        _reject_public_string(path or label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_string(label, key, is_key=True)
            item_path = key if not path else f"{path}.{key}"
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _reject_public_string(label: str, value: str, *, is_key: bool = False) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        detail = "field" if is_key else "value"
        raise ValueError(f"{label} has unsafe public {detail}")
