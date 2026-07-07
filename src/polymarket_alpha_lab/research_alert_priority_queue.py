"""Pure readonly research alert priority queue."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_ALERT_PRIORITY_QUEUE_CONFIG_VERSION",
    "ResearchAlertPriorityQueueConfig",
    "ResearchAlertPriorityQueueReport",
    "ResearchAlertPriorityQueueRow",
    "ResearchAlertSignal",
    "build_research_alert_priority_queue",
    "research_alert_priority_queue_payload",
)


DEFAULT_RESEARCH_ALERT_PRIORITY_QUEUE_CONFIG_VERSION = (
    "research-alert-priority-queue-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PUBLIC_STATUSES = frozenset(("pass", "watch", "block"))
NEXT_RESEARCH_ACTIONS = frozenset(
    (
        "escalate_rule_and_conflict_review",
        "escalate_team_sla_review",
        "no_alert",
        "refresh_sources",
        "resolve_evidence_conflict",
        "review_rule_risk",
        "route_to_research_owner",
    ),
)
ROW_REASON_CODE_PRIORITY = (
    "source_refresh_due",
    "evidence_conflict_blocking",
    "evidence_conflict_high",
    "rule_risk_blocking",
    "rule_risk_high",
    "team_sla_breached",
    "team_sla_pressure",
    "alert_pass",
)
REPORT_REASON_CODE_PRIORITY = (
    "alert_block_present",
    "alert_watch_present",
    "alert_pass_present",
    "source_refresh_due",
    "evidence_conflict_high",
    "evidence_conflict_blocking",
    "rule_risk_high",
    "rule_risk_blocking",
    "team_sla_pressure",
    "team_sla_breached",
)
REASON_CODE_SET = frozenset(ROW_REASON_CODE_PRIORITY + REPORT_REASON_CODE_PRIORITY)

PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "config_version",
        "queue_status",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "highest_priority_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_KEYS = frozenset(
    (
        "redacted_alert_id",
        "public_status",
        "priority_score",
        "alert_rank",
        "next_research_action",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "://",
        "api_key",
        "auth",
        "buy",
        "candidate_id",
        "candidate_reference",
        "database",
        "dsn",
        "execute",
        "http",
        "market_id",
        "market_question",
        "market_reference",
        "market_slug",
        "order",
        "position",
        "private_key",
        "question",
        "raw-candidate",
        "raw-market",
        "recommend",
        "sell",
        "slug",
        "source_reference",
        "source_text",
        "source_url",
        "sql",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)


@dataclass(frozen=True)
class ResearchAlertPriorityQueueConfig:
    config_version: str = DEFAULT_RESEARCH_ALERT_PRIORITY_QUEUE_CONFIG_VERSION
    source_refresh_weight: Decimal = Decimal("0.100000")
    evidence_conflict_weight: Decimal = Decimal("0.350000")
    rule_risk_weight: Decimal = Decimal("0.400000")
    team_sla_weight: Decimal = Decimal("0.150000")
    source_refresh_due_score: Decimal = Decimal("0.750000")
    high_evidence_conflict_score: Decimal = Decimal("0.700000")
    blocking_evidence_conflict_score: Decimal = Decimal("0.900000")
    high_rule_risk_score: Decimal = Decimal("0.700000")
    blocking_rule_risk_score: Decimal = Decimal("0.850000")
    team_sla_pressure_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchAlertPriorityQueueConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchAlertPriorityQueueConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_refresh_weight",
            "evidence_conflict_weight",
            "rule_risk_weight",
            "team_sla_weight",
            "source_refresh_due_score",
            "high_evidence_conflict_score",
            "blocking_evidence_conflict_score",
            "high_rule_risk_score",
            "blocking_rule_risk_score",
            "team_sla_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchAlertSignal:
    candidate_reference: str
    market_reference: str
    market_slug: str
    market_question: str
    source_reference: str
    source_text: str
    source_refresh_score: Decimal
    evidence_conflict_score: Decimal
    rule_risk_score: Decimal
    team_sla_age_seconds: Decimal
    team_sla_limit_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchAlertSignal does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("signal", self, ResearchAlertSignal)
        for field_name in (
            "candidate_reference",
            "market_reference",
            "market_slug",
            "market_question",
            "source_reference",
            "source_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_refresh_score",
            "evidence_conflict_score",
            "rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_sla_age_seconds",
            _require_nonnegative_decimal(
                "team_sla_age_seconds",
                self.team_sla_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "team_sla_limit_seconds",
            _require_positive_decimal(
                "team_sla_limit_seconds",
                self.team_sla_limit_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchAlertPriorityQueueRow:
    redacted_alert_id: str
    public_status: str
    priority_score: Decimal
    alert_rank: Decimal
    next_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchAlertPriorityQueueRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchAlertPriorityQueueRow)
        _require_canonical_string("redacted_alert_id", self.redacted_alert_id)
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "priority_score",
            _require_ratio("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "alert_rank",
            _require_positive_count("alert_rank", self.alert_rank),
        )
        _require_next_research_action(
            "next_research_action",
            self.next_research_action,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                priority=ROW_REASON_CODE_PRIORITY,
                require_nonempty=True,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchAlertPriorityQueueReport:
    config_version: str
    queue_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchAlertPriorityQueueRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchAlertPriorityQueueReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchAlertPriorityQueueReport)
        _require_canonical_string("config_version", self.config_version)
        _require_public_status("queue_status", self.queue_status)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _require_ratio("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                priority=REPORT_REASON_CODE_PRIORITY,
                require_nonempty=True,
            ),
        )
        _validate_report(self)
        _require_hard_flags(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_alert_priority_queue_payload(self)


def build_research_alert_priority_queue(
    signals: Iterable[ResearchAlertSignal],
    *,
    config: ResearchAlertPriorityQueueConfig,
) -> ResearchAlertPriorityQueueReport:
    """Build a deterministic public alert queue for human research review only."""

    if type(config) is not ResearchAlertPriorityQueueConfig:
        raise ValueError("config must be ResearchAlertPriorityQueueConfig")
    _require_hard_flags(config)
    source_signals = _normalize_signals(signals)
    ranked_rows = _ranked_rows(
        tuple(_unranked_row(item, config=config) for item in source_signals),
    )
    reason_codes = _combined_report_reason_codes(ranked_rows)
    return ResearchAlertPriorityQueueReport(
        config_version=config.config_version,
        queue_status=_report_status(ranked_rows),
        input_count=_count_decimal(len(source_signals)),
        pass_count=_count_decimal(
            sum(1 for row in ranked_rows if row.public_status == "pass"),
        ),
        watch_count=_count_decimal(
            sum(1 for row in ranked_rows if row.public_status == "watch"),
        ),
        block_count=_count_decimal(
            sum(1 for row in ranked_rows if row.public_status == "block"),
        ),
        highest_priority_score=ranked_rows[0].priority_score if ranked_rows else ZERO,
        rows=ranked_rows,
        reason_codes=reason_codes,
    )


def research_alert_priority_queue_payload(
    report: ResearchAlertPriorityQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchAlertPriorityQueueReport:
        return _report_payload(report, include_digest=True)
    if type(report) is dict:
        return _validated_public_payload(report)
    raise ValueError("report must be ResearchAlertPriorityQueueReport")


def _unranked_row(
    signal: ResearchAlertSignal,
    *,
    config: ResearchAlertPriorityQueueConfig,
) -> ResearchAlertPriorityQueueRow:
    reason_codes = _signal_reason_codes(signal, config)
    return ResearchAlertPriorityQueueRow(
        redacted_alert_id=_redacted_alert_id(signal),
        public_status=_public_status(reason_codes),
        priority_score=_priority_score(signal, config),
        alert_rank=ONE,
        next_research_action=_next_research_action(reason_codes),
        reason_codes=reason_codes,
    )


def _priority_score(
    signal: ResearchAlertSignal,
    config: ResearchAlertPriorityQueueConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            config.source_refresh_weight * signal.source_refresh_score
            + config.evidence_conflict_weight * signal.evidence_conflict_score
            + config.rule_risk_weight * signal.rule_risk_score
            + config.team_sla_weight * _team_sla_pressure(signal)
        )
    return _quantize_ratio("priority_score", _clamp_ratio(score))


def _team_sla_pressure(signal: ResearchAlertSignal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(signal.team_sla_age_seconds / signal.team_sla_limit_seconds)


def _signal_reason_codes(
    signal: ResearchAlertSignal,
    config: ResearchAlertPriorityQueueConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    sla_pressure = _team_sla_pressure(signal)
    if signal.source_refresh_score >= config.source_refresh_due_score:
        reason_codes.append("source_refresh_due")
    if signal.evidence_conflict_score >= config.blocking_evidence_conflict_score:
        reason_codes.append("evidence_conflict_blocking")
    if signal.evidence_conflict_score >= config.high_evidence_conflict_score:
        reason_codes.append("evidence_conflict_high")
    if signal.rule_risk_score >= config.blocking_rule_risk_score:
        reason_codes.append("rule_risk_blocking")
    if signal.rule_risk_score >= config.high_rule_risk_score:
        reason_codes.append("rule_risk_high")
    if sla_pressure >= ONE:
        reason_codes.append("team_sla_breached")
    elif sla_pressure >= config.team_sla_pressure_ratio:
        reason_codes.append("team_sla_pressure")
    if not reason_codes:
        reason_codes.append("alert_pass")
    return _normalize_reason_codes(
        tuple(reason_codes),
        priority=ROW_REASON_CODE_PRIORITY,
        require_nonempty=True,
    )


def _public_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in {
            "evidence_conflict_blocking",
            "rule_risk_blocking",
            "team_sla_breached",
        }
        for reason_code in reason_codes
    ):
        return "block"
    if reason_codes == ("alert_pass",):
        return "pass"
    return "watch"


def _next_research_action(reason_codes: tuple[str, ...]) -> str:
    if (
        "evidence_conflict_blocking" in reason_codes
        or "rule_risk_blocking" in reason_codes
    ):
        return "escalate_rule_and_conflict_review"
    if "team_sla_breached" in reason_codes:
        return "escalate_team_sla_review"
    if "evidence_conflict_high" in reason_codes:
        return "resolve_evidence_conflict"
    if "rule_risk_high" in reason_codes:
        return "review_rule_risk"
    if "source_refresh_due" in reason_codes:
        return "refresh_sources"
    if "team_sla_pressure" in reason_codes:
        return "route_to_research_owner"
    return "no_alert"


def _ranked_rows(
    rows: tuple[ResearchAlertPriorityQueueRow, ...],
) -> tuple[ResearchAlertPriorityQueueRow, ...]:
    return tuple(
        ResearchAlertPriorityQueueRow(
            redacted_alert_id=row.redacted_alert_id,
            public_status=row.public_status,
            priority_score=row.priority_score,
            alert_rank=_count_decimal(index),
            next_research_action=row.next_research_action,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(row: ResearchAlertPriorityQueueRow) -> tuple[Decimal, str]:
    return (-row.priority_score, row.redacted_alert_id)


def _combined_report_reason_codes(
    rows: tuple[ResearchAlertPriorityQueueRow, ...],
) -> tuple[str, ...]:
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    status_found = {row.public_status for row in rows}
    report_codes: list[str] = []
    if "block" in status_found:
        report_codes.append("alert_block_present")
    if "watch" in status_found:
        report_codes.append("alert_watch_present")
    if "pass" in status_found or not rows:
        report_codes.append("alert_pass_present")
    for reason_code in REPORT_REASON_CODE_PRIORITY:
        if (
            reason_code not in report_codes
            and reason_code in found
            and reason_code != "alert_pass"
        ):
            report_codes.append(reason_code)
    return _normalize_reason_codes(
        tuple(report_codes),
        priority=REPORT_REASON_CODE_PRIORITY,
        require_nonempty=True,
    )


def _report_status(rows: tuple[ResearchAlertPriorityQueueRow, ...]) -> str:
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_signals(
    signals: Iterable[ResearchAlertSignal],
) -> tuple[ResearchAlertSignal, ...]:
    normalized = tuple(signals)
    seen: set[str] = set()
    for signal in normalized:
        if type(signal) is not ResearchAlertSignal:
            raise ValueError("signals must contain ResearchAlertSignal")
        _require_hard_flags(signal)
        redacted_alert_id = _redacted_alert_id(signal)
        if redacted_alert_id in seen:
            raise ValueError("signals must not contain duplicate redacted alert ids")
        seen.add(redacted_alert_id)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchAlertPriorityQueueRow, ...],
) -> tuple[ResearchAlertPriorityQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchAlertPriorityQueueRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchAlertPriorityQueueRow:
            raise ValueError("rows must contain ResearchAlertPriorityQueueRow")
        _require_hard_flags(row)
        if row.redacted_alert_id in seen:
            raise ValueError("rows must not contain duplicate redacted_alert_id")
        seen.add(row.redacted_alert_id)
        normalized.append(row)
    return tuple(normalized)


def _validate_config(config: ResearchAlertPriorityQueueConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total_weight = (
            config.source_refresh_weight
            + config.evidence_conflict_weight
            + config.rule_risk_weight
            + config.team_sla_weight
        )
    if total_weight != ONE:
        raise ValueError("priority weights must sum to 1.000000")
    if config.high_evidence_conflict_score > config.blocking_evidence_conflict_score:
        raise ValueError(
            "high_evidence_conflict_score must be <= blocking_evidence_conflict_score",
        )
    if config.high_rule_risk_score > config.blocking_rule_risk_score:
        raise ValueError("high_rule_risk_score must be <= blocking_rule_risk_score")


def _validate_report(report: ResearchAlertPriorityQueueReport) -> None:
    expected_pass_count = _count_decimal(
        sum(1 for row in report.rows if row.public_status == "pass"),
    )
    expected_watch_count = _count_decimal(
        sum(1 for row in report.rows if row.public_status == "watch"),
    )
    expected_block_count = _count_decimal(
        sum(1 for row in report.rows if row.public_status == "block"),
    )
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match rows")
    if report.input_count < _count_decimal(len(report.rows)):
        raise ValueError("input_count must be >= rows")
    if report.queue_status != _report_status(report.rows):
        raise ValueError("queue_status must match rows")
    sorted_rows = tuple(sorted(report.rows, key=_row_sort_key))
    for index, row in enumerate(report.rows, start=1):
        if row != sorted_rows[index - 1] or row.alert_rank != _count_decimal(index):
            raise ValueError("rows must follow deterministic sequence")
    if report.highest_priority_score != (
        report.rows[0].priority_score if report.rows else ZERO
    ):
        raise ValueError("highest_priority_score must match first row")
    if report.reason_codes != _combined_report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_payload(
    report: ResearchAlertPriorityQueueReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    _require_hard_flags(report)
    payload: dict[str, Any] = {
        "config_version": report.config_version,
        "queue_status": report.queue_status,
        "input_count": _decimal_string(report.input_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "highest_priority_score": _decimal_string(report.highest_priority_score),
        "rows": [
            {
                "redacted_alert_id": row.redacted_alert_id,
                "public_status": row.public_status,
                "priority_score": _decimal_string(row.priority_score),
                "alert_rank": _decimal_string(row.alert_rank),
                "next_research_action": row.next_research_action,
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _validated_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _reject_unsafe_public_payload(payload)
    _require_public_payload_keys(payload)
    paper_only = _public_true("paper_only", payload["paper_only"])
    report_only = _public_true("report_only", payload["report_only"])
    readonly = _public_true("readonly", payload["readonly"])
    digest = _public_string(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_digest("derived_validation_digest", digest)
    if digest != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_public_payload_row(row) for row in payload["rows"])
    report = ResearchAlertPriorityQueueReport(
        config_version=_public_string("config_version", payload["config_version"]),
        queue_status=_public_string("queue_status", payload["queue_status"]),
        input_count=_public_decimal("input_count", payload["input_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        highest_priority_score=_public_decimal(
            "highest_priority_score",
            payload["highest_priority_score"],
        ),
        rows=rows,
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        derived_validation_digest=digest,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    return _report_payload(report, include_digest=True)


def _public_payload_row(payload: object) -> ResearchAlertPriorityQueueRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain dict payloads")
    _require_public_row_keys(payload)
    return ResearchAlertPriorityQueueRow(
        redacted_alert_id=_public_string(
            "redacted_alert_id",
            payload["redacted_alert_id"],
        ),
        public_status=_public_string("public_status", payload["public_status"]),
        priority_score=_public_decimal("priority_score", payload["priority_score"]),
        alert_rank=_public_decimal("alert_rank", payload["alert_rank"]),
        next_research_action=_public_string(
            "next_research_action",
            payload["next_research_action"],
        ),
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _require_public_payload_keys(payload: dict[str, Any]) -> None:
    missing = PUBLIC_PAYLOAD_KEYS - payload.keys()
    if missing:
        raise ValueError("public payload is missing required fields")
    extra = payload.keys() - PUBLIC_PAYLOAD_KEYS
    if extra:
        raise ValueError("public payload contains unsupported fields")


def _require_public_row_keys(payload: dict[str, Any]) -> None:
    missing = PUBLIC_ROW_KEYS - payload.keys()
    if missing:
        raise ValueError("row payload is missing required fields")
    extra = payload.keys() - PUBLIC_ROW_KEYS
    if extra:
        raise ValueError("row payload contains unsupported fields")


def _derived_validation_digest(report: ResearchAlertPriorityQueueReport) -> str:
    return _public_payload_digest(_report_payload(report, include_digest=False))


def _public_payload_digest(payload: dict[str, Any]) -> str:
    return sha256(repr(_canonical_payload_value(payload)).encode("utf-8")).hexdigest()


def _canonical_payload_value(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _canonical_payload_value(value[key]))
            for key in sorted(value)
            if key != "derived_validation_digest"
        )
    if type(value) is list:
        return tuple(_canonical_payload_value(item) for item in value)
    if type(value) in {str, bool}:
        return value
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, nested in value.items():
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is list:
        for nested in value:
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return
    if type(value) is bool:
        return
    raise ValueError("public payload numeric values must be Decimal-derived strings")


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    normalized = _require_decimal(field_name, decimal_value)
    if _decimal_string(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _public_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return tuple(_public_string("reason_code", item) for item in value)


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _quantize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return quantized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    count = _require_nonnegative_count(field_name, value)
    if count <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return count


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    priority: tuple[str, ...],
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SET:
            raise ValueError("reason_codes contains unsupported reason_code")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(reason_code for reason_code in priority if reason_code in seen)
    if tuple(normalized) != expected:
        raise ValueError("reason_codes must follow deterministic order")
    return tuple(normalized)


def _require_public_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} is unsupported")


def _require_next_research_action(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_RESEARCH_ACTIONS:
        raise ValueError(f"{field_name} is unsupported")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _redacted_alert_id(signal: ResearchAlertSignal) -> str:
    raw_value = "\x1f".join(
        (
            signal.candidate_reference,
            signal.market_reference,
            signal.market_slug,
            signal.market_question,
            signal.source_reference,
            signal.source_text,
        ),
    )
    return f"alert_{sha256(raw_value.encode('utf-8')).hexdigest()[:16]}"


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")
