"""Public-safe specialist research team handoff queue report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchSpecialistTeamHandoffQueueConfig",
    "ResearchSpecialistTeamHandoffQueueInput",
    "ResearchSpecialistTeamHandoffQueueReasonCodeCount",
    "ResearchSpecialistTeamHandoffQueueReport",
    "ResearchSpecialistTeamHandoffQueueRow",
    "build_research_specialist_team_handoff_queue_report",
    "research_specialist_team_handoff_queue_report_payload",
)


DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION = (
    "research-specialist-team-handoff-queue-report-v1"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DOMAINS = ("politics", "crypto", "equities", "gold", "soccer", "basketball", "other")
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PAPER_ACTION_BY_STATUS = {
    "pass": "paper_monitor_only",
    "watch": "paper_handoff_watch",
    "block": "paper_handoff_block",
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "event",
    "market",
    "source",
    "recommendation",
    "sizing",
    "order",
    "wallet",
    "auth",
    "network",
    "database",
    "persist",
    "write",
    "trade",
    "buy",
    "sell",
    "position",
    "account",
    "balance",
    "private_key",
    "signing",
    "mutation",
)
ROW_REASON_PRIORITY = (
    "handoff_confidence_low_block",
    "handoff_evidence_low_block",
    "handoff_urgency_high_block",
    "handoff_confidence_thin_watch",
    "handoff_evidence_thin_watch",
    "handoff_urgency_elevated_watch",
    "handoff_queue_clear",
)
REPORT_REASON_PRIORITY = (
    "handoff_confidence_low_block",
    "handoff_evidence_low_block",
    "handoff_urgency_high_block",
    "handoff_confidence_thin_watch",
    "handoff_evidence_thin_watch",
    "handoff_urgency_elevated_watch",
)
HEX_CHARS = frozenset("0123456789abcdef")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchSpecialistTeamHandoffQueueConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION
    )
    min_pass_confidence_score: Decimal = Decimal("0.750000")
    min_watch_confidence_score: Decimal = Decimal("0.550000")
    min_pass_evidence_score: Decimal = Decimal("0.700000")
    min_watch_evidence_score: Decimal = Decimal("0.500000")
    max_pass_urgency_score: Decimal = Decimal("0.400000")
    max_watch_urgency_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSpecialistTeamHandoffQueueConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_confidence_score",
            "min_watch_confidence_score",
            "min_pass_evidence_score",
            "min_watch_evidence_score",
            "max_pass_urgency_score",
            "max_watch_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_confidence_score > self.min_pass_confidence_score:
            raise ValueError("min_watch_confidence_score must not exceed pass threshold")
        if self.min_watch_evidence_score > self.min_pass_evidence_score:
            raise ValueError("min_watch_evidence_score must not exceed pass threshold")
        if self.max_pass_urgency_score > self.max_watch_urgency_score:
            raise ValueError("max_pass_urgency_score must not exceed watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSpecialistTeamHandoffQueueInput(_FinalPublicDataclass):
    from_domain: str
    to_domain: str
    aggregate_confidence_score: Decimal
    aggregate_evidence_score: Decimal
    aggregate_urgency_score: Decimal
    domain_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSpecialistTeamHandoffQueueInput, "input")
        _require_domain("from_domain", self.from_domain)
        _require_domain("to_domain", self.to_domain)
        if self.from_domain == self.to_domain:
            raise ValueError("from_domain and to_domain must be different")
        for field_name in (
            "aggregate_confidence_score",
            "aggregate_evidence_score",
            "aggregate_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_count",
            _require_count_decimal("domain_count", self.domain_count),
        )
        if self.domain_count < Decimal("2.000000"):
            raise ValueError("domain_count must be at least 2 for a handoff")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSpecialistTeamHandoffQueueRow(_FinalPublicDataclass):
    from_domain: str
    to_domain: str
    handoff_status: str
    aggregate_confidence_score: Decimal
    aggregate_evidence_score: Decimal
    aggregate_urgency_score: Decimal
    domain_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSpecialistTeamHandoffQueueRow, "row")
        _require_domain("from_domain", self.from_domain)
        _require_domain("to_domain", self.to_domain)
        if self.from_domain == self.to_domain:
            raise ValueError("from_domain and to_domain must be different")
        _require_status("handoff_status", self.handoff_status)
        for field_name in (
            "aggregate_confidence_score",
            "aggregate_evidence_score",
            "aggregate_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_count",
            _require_count_decimal("domain_count", self.domain_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSpecialistTeamHandoffQueueReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    handoff_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSpecialistTeamHandoffQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code.lower() != self.reason_code:
            raise ValueError("reason_code must be lowercase")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "handoff_ratio",
            _require_ratio_decimal("handoff_ratio", self.handoff_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSpecialistTeamHandoffQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    handoff_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_confidence_score: Decimal
    min_evidence_score: Decimal
    max_urgency_score: Decimal
    max_domain_count: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSpecialistTeamHandoffQueueReasonCodeCount, ...]
    rows: tuple[ResearchSpecialistTeamHandoffQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSpecialistTeamHandoffQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "handoff_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_confidence_score",
            "min_evidence_score",
            "max_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report_status(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_specialist_team_handoff_queue_report(
    handoffs: Iterable[ResearchSpecialistTeamHandoffQueueInput],
    *,
    config: ResearchSpecialistTeamHandoffQueueConfig,
    generated_at: datetime,
) -> ResearchSpecialistTeamHandoffQueueReport:
    if type(config) is not ResearchSpecialistTeamHandoffQueueConfig:
        raise ValueError("config must be a ResearchSpecialistTeamHandoffQueueConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(handoffs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.handoff_status for row in rows))
    return ResearchSpecialistTeamHandoffQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        handoff_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        min_confidence_score=_min_decimal(
            tuple(row.aggregate_confidence_score for row in rows),
        ),
        min_evidence_score=_min_decimal(
            tuple(row.aggregate_evidence_score for row in rows),
        ),
        max_urgency_score=_max_decimal(
            tuple(row.aggregate_urgency_score for row in rows),
        ),
        max_domain_count=_max_decimal(tuple(row.domain_count for row in rows)),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_specialist_team_handoff_queue_report_payload(
    report: ResearchSpecialistTeamHandoffQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSpecialistTeamHandoffQueueReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchSpecialistTeamHandoffQueueReport")


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


def _normalize_inputs(
    handoffs: Iterable[ResearchSpecialistTeamHandoffQueueInput],
) -> tuple[ResearchSpecialistTeamHandoffQueueInput, ...]:
    if isinstance(handoffs, (str, bytes)):
        raise ValueError("handoffs must be an iterable")
    try:
        items = tuple(handoffs)
    except TypeError as exc:
        raise ValueError("handoffs must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchSpecialistTeamHandoffQueueInput:
            raise ValueError(
                "handoffs must contain ResearchSpecialistTeamHandoffQueueInput",
            )
        _require_hard_flags("input", item)
        key = (item.from_domain, item.to_domain)
        if key in seen:
            raise ValueError("from_domain and to_domain handoff pairs must be unique")
        seen.add(key)
    return items


def _row_from_input(
    item: ResearchSpecialistTeamHandoffQueueInput,
    *,
    config: ResearchSpecialistTeamHandoffQueueConfig,
    generated_at: datetime,
) -> ResearchSpecialistTeamHandoffQueueRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchSpecialistTeamHandoffQueueRow(
        from_domain=item.from_domain,
        to_domain=item.to_domain,
        handoff_status=_row_status(reason_codes),
        aggregate_confidence_score=item.aggregate_confidence_score,
        aggregate_evidence_score=item.aggregate_evidence_score,
        aggregate_urgency_score=item.aggregate_urgency_score,
        domain_count=item.domain_count,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchSpecialistTeamHandoffQueueInput,
    *,
    config: ResearchSpecialistTeamHandoffQueueConfig,
) -> tuple[str, ...]:
    reasons = list(item.reason_codes)
    if item.aggregate_confidence_score < config.min_watch_confidence_score:
        reasons.append("handoff_confidence_low_block")
    elif item.aggregate_confidence_score < config.min_pass_confidence_score:
        reasons.append("handoff_confidence_thin_watch")

    if item.aggregate_evidence_score < config.min_watch_evidence_score:
        reasons.append("handoff_evidence_low_block")
    elif item.aggregate_evidence_score < config.min_pass_evidence_score:
        reasons.append("handoff_evidence_thin_watch")

    if item.aggregate_urgency_score > config.max_watch_urgency_score:
        reasons.append("handoff_urgency_high_block")
    elif item.aggregate_urgency_score > config.max_pass_urgency_score:
        reasons.append("handoff_urgency_elevated_watch")

    if not any(reason.startswith("handoff_") for reason in reasons):
        reasons.append("handoff_queue_clear")
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSpecialistTeamHandoffQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("specialist_handoff_queue_empty",)
    status = _rollup_status(tuple(row.handoff_status for row in rows))
    reason_codes = [
        f"specialist_handoff_queue_{'clear' if status == 'pass' else status}",
    ]
    row_handoff_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code.startswith("handoff_") and reason_code != "handoff_queue_clear"
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_handoff_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchSpecialistTeamHandoffQueueRow, ...],
) -> tuple[ResearchSpecialistTeamHandoffQueueReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    return tuple(
        ResearchSpecialistTeamHandoffQueueReasonCodeCount(
            reason_code=reason_code,
            count=count,
            handoff_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], item[1]),
        )
    )


def _row_sort_key(
    row: ResearchSpecialistTeamHandoffQueueRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.handoff_status],
        -row.aggregate_urgency_score,
        row.from_domain,
        row.to_domain,
    )


def _status_count(
    rows: tuple[ResearchSpecialistTeamHandoffQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.handoff_status == status))


def _validate_row(row: ResearchSpecialistTeamHandoffQueueRow) -> None:
    if row.handoff_status != _row_status(row.reason_codes):
        raise ValueError("handoff_status must match reason_codes")


def _validate_report_status(report: ResearchSpecialistTeamHandoffQueueReport) -> None:
    expected_status = _rollup_status(tuple(row.handoff_status for row in report.rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")


def _validate_report_materialized_fields(
    report: ResearchSpecialistTeamHandoffQueueReport,
) -> None:
    rows = report.rows
    checks = {
        "handoff_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "min_confidence_score": _min_decimal(
            tuple(row.aggregate_confidence_score for row in rows),
        ),
        "min_evidence_score": _min_decimal(
            tuple(row.aggregate_evidence_score for row in rows),
        ),
        "max_urgency_score": _max_decimal(
            tuple(row.aggregate_urgency_score for row in rows),
        ),
        "max_domain_count": _max_decimal(tuple(row.domain_count for row in rows)),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchSpecialistTeamHandoffQueueRow, ...],
) -> tuple[ResearchSpecialistTeamHandoffQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSpecialistTeamHandoffQueueRow:
            raise ValueError("rows must contain ResearchSpecialistTeamHandoffQueueRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, urgency, and domain")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchSpecialistTeamHandoffQueueReasonCodeCount, ...],
) -> tuple[ResearchSpecialistTeamHandoffQueueReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSpecialistTeamHandoffQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSpecialistTeamHandoffQueueReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by count and reason_code")
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_domain(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in DOMAINS:
        raise ValueError(f"{field_name} must be a supported domain")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code.lower() != reason_code:
            raise ValueError("reason_code must be lowercase")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                1 if reason_code.startswith("handoff_") else 0,
                (
                    ROW_REASON_PRIORITY.index(reason_code)
                    if reason_code in ROW_REASON_PRIORITY
                    else len(ROW_REASON_PRIORITY)
                ),
                reason_code,
            ),
        ),
    )


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(reason_codes, require_nonempty=True)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                0 if reason_code.startswith("specialist_handoff_queue_") else 1,
                (
                    REPORT_REASON_PRIORITY.index(reason_code)
                    if reason_code in REPORT_REASON_PRIORITY
                    else len(REPORT_REASON_PRIORITY)
                ),
                reason_code,
            ),
        ),
    )


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _require_count_decimal("count", value)
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _derived_validation_digest(report: ResearchSpecialistTeamHandoffQueueReport) -> str:
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")
