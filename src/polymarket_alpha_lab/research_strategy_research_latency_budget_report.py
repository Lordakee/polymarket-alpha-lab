"""Pure report-only research latency budget report."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESEARCH_LATENCY_BUDGET_REPORT_CONFIG_VERSION",
    "ResearchStrategyResearchLatencyBudgetCandidate",
    "ResearchStrategyResearchLatencyBudgetConfig",
    "ResearchStrategyResearchLatencyBudgetReport",
    "ResearchStrategyResearchLatencyBudgetRow",
    "build_research_strategy_research_latency_budget_report",
    "research_strategy_research_latency_budget_report_digest",
    "research_strategy_research_latency_budget_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_RESEARCH_LATENCY_BUDGET_REPORT_CONFIG_VERSION = (
    "research-strategy-research-latency-budget-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_PACKETS_REASON = "latency_budget_no_packets"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "packet_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_total_latency_seconds",
    "average_total_latency_seconds",
    "max_total_budget_utilization_ratio",
    "status",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_DIGEST_KEYS = (
    "row_number",
    "discovery_latency_seconds",
    "evidence_collection_latency_seconds",
    "specialist_review_latency_seconds",
    "manual_decision_queue_delay_seconds",
    "total_research_latency_seconds",
    "discovery_budget_utilization_ratio",
    "evidence_collection_budget_utilization_ratio",
    "specialist_review_budget_utilization_ratio",
    "manual_decision_queue_delay_budget_utilization_ratio",
    "total_budget_utilization_ratio",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (*ROW_DIGEST_KEYS, "validation_digest")
REPORT_DIGEST_KEYS = (
    "generated_at",
    "config_version",
    "packet_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_total_latency_seconds",
    "average_total_latency_seconds",
    "max_total_budget_utilization_ratio",
    "status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (*REPORT_DIGEST_KEYS, "validation_digest")
REASON_PRIORITY = (
    "discovery_latency_block",
    "evidence_collection_latency_block",
    "specialist_review_latency_block",
    "manual_decision_queue_delay_block",
    "total_research_latency_block",
    "latency_budget_block",
    "discovery_latency_watch",
    "evidence_collection_latency_watch",
    "specialist_review_latency_watch",
    "manual_decision_queue_delay_watch",
    "total_research_latency_watch",
    "latency_budget_watch",
    "latency_budget_pass",
    NO_PACKETS_REASON,
)
UNSAFE_TEXT_FRAGMENTS = (
    "candidate" "_" "id",
    "market" "_" "id",
    "market" "_" "slug",
    "question",
    "so" "urce",
    "url",
    "dsn",
    "table",
    "tok" "en",
    "private",
    "sec" "ret",
    "pass" "word",
    "api" "_" "key",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "li" "ve " "trading",
    "data" "base",
    "net" "work",
    "://",
    "reco" "mmend" "ation",
    "siz" "ing",
    "b" "uy",
    "s" "ell",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyResearchLatencyBudgetConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESEARCH_LATENCY_BUDGET_REPORT_CONFIG_VERSION
    )
    discovery_budget_seconds: Decimal = Decimal("900.000000")
    discovery_watch_ceiling_seconds: Decimal = Decimal("1800.000000")
    evidence_collection_budget_seconds: Decimal = Decimal("1800.000000")
    evidence_collection_watch_ceiling_seconds: Decimal = Decimal("3600.000000")
    specialist_review_budget_seconds: Decimal = Decimal("2700.000000")
    specialist_review_watch_ceiling_seconds: Decimal = Decimal("5400.000000")
    manual_decision_queue_delay_budget_seconds: Decimal = Decimal("600.000000")
    manual_decision_queue_delay_watch_ceiling_seconds: Decimal = Decimal("1200.000000")
    total_research_latency_budget_seconds: Decimal = Decimal("6000.000000")
    total_research_latency_watch_ceiling_seconds: Decimal = Decimal("12000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchLatencyBudgetConfig, "config")
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "discovery_budget_seconds",
            "discovery_watch_ceiling_seconds",
            "evidence_collection_budget_seconds",
            "evidence_collection_watch_ceiling_seconds",
            "specialist_review_budget_seconds",
            "specialist_review_watch_ceiling_seconds",
            "manual_decision_queue_delay_budget_seconds",
            "manual_decision_queue_delay_watch_ceiling_seconds",
            "total_research_latency_budget_seconds",
            "total_research_latency_watch_ceiling_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_above(
            "discovery_watch_ceiling_seconds",
            self.discovery_watch_ceiling_seconds,
            self.discovery_budget_seconds,
        )
        _require_above(
            "evidence_collection_watch_ceiling_seconds",
            self.evidence_collection_watch_ceiling_seconds,
            self.evidence_collection_budget_seconds,
        )
        _require_above(
            "specialist_review_watch_ceiling_seconds",
            self.specialist_review_watch_ceiling_seconds,
            self.specialist_review_budget_seconds,
        )
        _require_above(
            "manual_decision_queue_delay_watch_ceiling_seconds",
            self.manual_decision_queue_delay_watch_ceiling_seconds,
            self.manual_decision_queue_delay_budget_seconds,
        )
        _require_above(
            "total_research_latency_watch_ceiling_seconds",
            self.total_research_latency_watch_ceiling_seconds,
            self.total_research_latency_budget_seconds,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResearchLatencyBudgetCandidate(_FinalDataclass):
    packet_ref: str
    discovery_latency_seconds: Decimal
    evidence_collection_latency_seconds: Decimal
    specialist_review_latency_seconds: Decimal
    manual_decision_queue_delay_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchLatencyBudgetCandidate, "candidate")
        _require_private_reference("packet_ref", self.packet_ref)
        for field_name in (
            "discovery_latency_seconds",
            "evidence_collection_latency_seconds",
            "specialist_review_latency_seconds",
            "manual_decision_queue_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyResearchLatencyBudgetRow(_FinalDataclass):
    row_number: Decimal
    discovery_latency_seconds: Decimal
    evidence_collection_latency_seconds: Decimal
    specialist_review_latency_seconds: Decimal
    manual_decision_queue_delay_seconds: Decimal
    total_research_latency_seconds: Decimal
    discovery_budget_utilization_ratio: Decimal
    evidence_collection_budget_utilization_ratio: Decimal
    specialist_review_budget_utilization_ratio: Decimal
    manual_decision_queue_delay_budget_utilization_ratio: Decimal
    total_budget_utilization_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchLatencyBudgetRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        for field_name in (
            "discovery_latency_seconds",
            "evidence_collection_latency_seconds",
            "specialist_review_latency_seconds",
            "manual_decision_queue_delay_seconds",
            "total_research_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "discovery_budget_utilization_ratio",
            "evidence_collection_budget_utilization_ratio",
            "specialist_review_budget_utilization_ratio",
            "manual_decision_queue_delay_budget_utilization_ratio",
            "total_budget_utilization_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _require_hard_phase_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyResearchLatencyBudgetReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_total_latency_seconds: Decimal | None
    average_total_latency_seconds: Decimal | None
    max_total_budget_utilization_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyResearchLatencyBudgetRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchLatencyBudgetReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("packet_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_latency_seconds",
            "average_total_latency_seconds",
            "max_total_budget_utilization_ratio",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_nonnegative_decimal(field_name, value),
                )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)


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


def build_research_strategy_research_latency_budget_report(
    candidates: Iterable[ResearchStrategyResearchLatencyBudgetCandidate],
    *,
    config: ResearchStrategyResearchLatencyBudgetConfig,
    generated_at: datetime,
) -> ResearchStrategyResearchLatencyBudgetReport:
    if type(config) is not ResearchStrategyResearchLatencyBudgetConfig:
        raise ValueError("config must be a ResearchStrategyResearchLatencyBudgetConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    prepared_rows = tuple(
        sorted(
            (
                _prepared_row_from_candidate(candidate, config=config)
                for candidate in normalized_candidates
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(row_number=_count(index + 1), prepared=prepared)
        for index, prepared in enumerate(prepared_rows)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_total_latency_seconds": (
            None if not rows else max(row.total_research_latency_seconds for row in rows)
        ),
        "average_total_latency_seconds": _average_total_latency(rows),
        "max_total_budget_utilization_ratio": (
            None if not rows else max(row.total_budget_utilization_ratio for row in rows)
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyResearchLatencyBudgetReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_research_latency_budget_report_payload(
    report: ResearchStrategyResearchLatencyBudgetReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyResearchLatencyBudgetReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyResearchLatencyBudgetReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _validate_public_payload_digest(payload)
    return payload


def research_strategy_research_latency_budget_report_digest(
    report: ResearchStrategyResearchLatencyBudgetReport,
) -> dict[str, Any]:
    payload = research_strategy_research_latency_budget_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _prepared_row_from_candidate(
    candidate: ResearchStrategyResearchLatencyBudgetCandidate,
    *,
    config: ResearchStrategyResearchLatencyBudgetConfig,
) -> dict[str, Any]:
    total_latency = _sum_decimal(
        (
            candidate.discovery_latency_seconds,
            candidate.evidence_collection_latency_seconds,
            candidate.specialist_review_latency_seconds,
            candidate.manual_decision_queue_delay_seconds,
        ),
    )
    reason_codes = _row_reason_codes(candidate, config=config, total_latency=total_latency)
    return {
        "packet_ref": candidate.packet_ref,
        "discovery_latency_seconds": candidate.discovery_latency_seconds,
        "evidence_collection_latency_seconds": candidate.evidence_collection_latency_seconds,
        "specialist_review_latency_seconds": candidate.specialist_review_latency_seconds,
        "manual_decision_queue_delay_seconds": (
            candidate.manual_decision_queue_delay_seconds
        ),
        "total_research_latency_seconds": total_latency,
        "discovery_budget_utilization_ratio": _ratio(
            candidate.discovery_latency_seconds,
            config.discovery_budget_seconds,
        ),
        "evidence_collection_budget_utilization_ratio": _ratio(
            candidate.evidence_collection_latency_seconds,
            config.evidence_collection_budget_seconds,
        ),
        "specialist_review_budget_utilization_ratio": _ratio(
            candidate.specialist_review_latency_seconds,
            config.specialist_review_budget_seconds,
        ),
        "manual_decision_queue_delay_budget_utilization_ratio": _ratio(
            candidate.manual_decision_queue_delay_seconds,
            config.manual_decision_queue_delay_budget_seconds,
        ),
        "total_budget_utilization_ratio": _ratio(
            total_latency,
            config.total_research_latency_budget_seconds,
        ),
        "status": _row_status(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_prepared(
    *,
    row_number: Decimal,
    prepared: dict[str, Any],
) -> ResearchStrategyResearchLatencyBudgetRow:
    row_values = {
        key: value for key, value in prepared.items() if key != "packet_ref"
    }
    row_values["row_number"] = row_number
    return ResearchStrategyResearchLatencyBudgetRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    candidate: ResearchStrategyResearchLatencyBudgetCandidate,
    *,
    config: ResearchStrategyResearchLatencyBudgetConfig,
    total_latency: Decimal,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    _append_latency_reason(
        "discovery_latency",
        candidate.discovery_latency_seconds,
        config.discovery_budget_seconds,
        config.discovery_watch_ceiling_seconds,
        block_reasons,
        watch_reasons,
    )
    _append_latency_reason(
        "evidence_collection_latency",
        candidate.evidence_collection_latency_seconds,
        config.evidence_collection_budget_seconds,
        config.evidence_collection_watch_ceiling_seconds,
        block_reasons,
        watch_reasons,
    )
    _append_latency_reason(
        "specialist_review_latency",
        candidate.specialist_review_latency_seconds,
        config.specialist_review_budget_seconds,
        config.specialist_review_watch_ceiling_seconds,
        block_reasons,
        watch_reasons,
    )
    _append_latency_reason(
        "manual_decision_queue_delay",
        candidate.manual_decision_queue_delay_seconds,
        config.manual_decision_queue_delay_budget_seconds,
        config.manual_decision_queue_delay_watch_ceiling_seconds,
        block_reasons,
        watch_reasons,
    )
    _append_latency_reason(
        "total_research_latency",
        total_latency,
        config.total_research_latency_budget_seconds,
        config.total_research_latency_watch_ceiling_seconds,
        block_reasons,
        watch_reasons,
    )
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("latency_budget_pass",)
    return _normalize_reason_codes(reasons)


def _append_latency_reason(
    label: str,
    value: Decimal,
    budget: Decimal,
    watch_ceiling: Decimal,
    block_reasons: list[str],
    watch_reasons: list[str],
) -> None:
    if value > watch_ceiling:
        block_reasons.append(f"{label}_block")
    elif value > budget:
        watch_reasons.append(f"{label}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyResearchLatencyBudgetRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyResearchLatencyBudgetRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "latency_budget_pass"
    )
    return _normalize_reason_codes((*values, f"latency_budget_{status}"))


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyResearchLatencyBudgetCandidate],
) -> tuple[ResearchStrategyResearchLatencyBudgetCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not ResearchStrategyResearchLatencyBudgetCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyResearchLatencyBudgetCandidate",
            )
        _require_hard_phase_flags("candidate", candidate)
        if candidate.packet_ref in seen:
            raise ValueError("packet_ref values must be unique")
        seen.add(candidate.packet_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyResearchLatencyBudgetRow],
) -> tuple[ResearchStrategyResearchLatencyBudgetRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    expected_row_number = ONE
    for row in values:
        if type(row) is not ResearchStrategyResearchLatencyBudgetRow:
            raise ValueError("rows must contain ResearchStrategyResearchLatencyBudgetRow")
        _require_hard_phase_flags("row", row)
        if row.row_number != expected_row_number:
            raise ValueError("rows must be sorted deterministically")
        expected_row_number = _quantize(expected_row_number + ONE)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyResearchLatencyBudgetRow) -> None:
    expected_total = _sum_decimal(
        (
            row.discovery_latency_seconds,
            row.evidence_collection_latency_seconds,
            row.specialist_review_latency_seconds,
            row.manual_decision_queue_delay_seconds,
        ),
    )
    if row.total_research_latency_seconds != expected_total:
        raise ValueError("total_research_latency_seconds must match phases")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyResearchLatencyBudgetReport) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_max_latency = (
        None
        if not report.rows
        else max(row.total_research_latency_seconds for row in report.rows)
    )
    if report.max_total_latency_seconds != expected_max_latency:
        raise ValueError("max_total_latency_seconds must match rows")
    if report.average_total_latency_seconds != _average_total_latency(report.rows):
        raise ValueError("average_total_latency_seconds must match rows")
    expected_max_utilization = (
        None
        if not report.rows
        else max(row.total_budget_utilization_ratio for row in report.rows)
    )
    if report.max_total_budget_utilization_ratio != expected_max_utilization:
        raise ValueError("max_total_budget_utilization_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    public_rows = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _validate_public_row_digest(row)
        public_rows.append(_public_row_from_payload(row))
    _require_digest("validation_digest", payload["validation_digest"])
    expected_digest = _validation_digest(
        {key: payload[key] for key in REPORT_DIGEST_KEYS},
    )
    if payload["validation_digest"] != expected_digest:
        raise ValueError("validation_digest must match report payload")
    ResearchStrategyResearchLatencyBudgetReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        packet_count=_public_count("packet_count", payload["packet_count"]),
        pass_count=_public_count("pass_count", payload["pass_count"]),
        watch_count=_public_count("watch_count", payload["watch_count"]),
        block_count=_public_count("block_count", payload["block_count"]),
        max_total_latency_seconds=_optional_public_decimal(
            "max_total_latency_seconds",
            payload["max_total_latency_seconds"],
        ),
        average_total_latency_seconds=_optional_public_decimal(
            "average_total_latency_seconds",
            payload["average_total_latency_seconds"],
        ),
        max_total_budget_utilization_ratio=_optional_public_decimal(
            "max_total_budget_utilization_ratio",
            payload["max_total_budget_utilization_ratio"],
        ),
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        rows=tuple(public_rows),
        validation_digest=payload["validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _validate_public_row_digest(row: dict[str, Any]) -> None:
    _require_payload_keys("row payload", row, ROW_PAYLOAD_KEYS)
    _require_hard_phase_flags("row payload", _DictFlags(row))
    _require_digest("validation_digest", row["validation_digest"])
    expected_digest = _validation_digest({key: row[key] for key in ROW_DIGEST_KEYS})
    if row["validation_digest"] != expected_digest:
        raise ValueError("validation_digest must match row payload")


def _public_row_from_payload(row: dict[str, Any]) -> ResearchStrategyResearchLatencyBudgetRow:
    return ResearchStrategyResearchLatencyBudgetRow(
        row_number=_public_count("row_number", row["row_number"]),
        discovery_latency_seconds=_public_decimal(
            "discovery_latency_seconds",
            row["discovery_latency_seconds"],
        ),
        evidence_collection_latency_seconds=_public_decimal(
            "evidence_collection_latency_seconds",
            row["evidence_collection_latency_seconds"],
        ),
        specialist_review_latency_seconds=_public_decimal(
            "specialist_review_latency_seconds",
            row["specialist_review_latency_seconds"],
        ),
        manual_decision_queue_delay_seconds=_public_decimal(
            "manual_decision_queue_delay_seconds",
            row["manual_decision_queue_delay_seconds"],
        ),
        total_research_latency_seconds=_public_decimal(
            "total_research_latency_seconds",
            row["total_research_latency_seconds"],
        ),
        discovery_budget_utilization_ratio=_public_decimal(
            "discovery_budget_utilization_ratio",
            row["discovery_budget_utilization_ratio"],
        ),
        evidence_collection_budget_utilization_ratio=_public_decimal(
            "evidence_collection_budget_utilization_ratio",
            row["evidence_collection_budget_utilization_ratio"],
        ),
        specialist_review_budget_utilization_ratio=_public_decimal(
            "specialist_review_budget_utilization_ratio",
            row["specialist_review_budget_utilization_ratio"],
        ),
        manual_decision_queue_delay_budget_utilization_ratio=_public_decimal(
            "manual_decision_queue_delay_budget_utilization_ratio",
            row["manual_decision_queue_delay_budget_utilization_ratio"],
        ),
        total_budget_utilization_ratio=_public_decimal(
            "total_budget_utilization_ratio",
            row["total_budget_utilization_ratio"],
        ),
        status=row["status"],
        reason_codes=tuple(row["reason_codes"]),
        validation_digest=row["validation_digest"],
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _require_payload_keys(
    name: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if set(payload) != set(expected_keys):
        raise ValueError(f"{name} keys must match report payload")


def _row_digest_values(row: ResearchStrategyResearchLatencyBudgetRow) -> dict[str, Any]:
    return {
        "row_number": row.row_number,
        "discovery_latency_seconds": row.discovery_latency_seconds,
        "evidence_collection_latency_seconds": row.evidence_collection_latency_seconds,
        "specialist_review_latency_seconds": row.specialist_review_latency_seconds,
        "manual_decision_queue_delay_seconds": row.manual_decision_queue_delay_seconds,
        "total_research_latency_seconds": row.total_research_latency_seconds,
        "discovery_budget_utilization_ratio": row.discovery_budget_utilization_ratio,
        "evidence_collection_budget_utilization_ratio": (
            row.evidence_collection_budget_utilization_ratio
        ),
        "specialist_review_budget_utilization_ratio": (
            row.specialist_review_budget_utilization_ratio
        ),
        "manual_decision_queue_delay_budget_utilization_ratio": (
            row.manual_decision_queue_delay_budget_utilization_ratio
        ),
        "total_budget_utilization_ratio": row.total_budget_utilization_ratio,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyResearchLatencyBudgetReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "packet_count": report.packet_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "max_total_latency_seconds": report.max_total_latency_seconds,
        "average_total_latency_seconds": report.average_total_latency_seconds,
        "max_total_budget_utilization_ratio": (
            report.max_total_budget_utilization_ratio
        ),
        "status": report.status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _prepared_row_sort_key(prepared: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[prepared["status"]],
        prepared["total_budget_utilization_ratio"],
        prepared["total_research_latency_seconds"],
        prepared["packet_ref"],
    )


def _row_sort_key(
    row: ResearchStrategyResearchLatencyBudgetRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return (
        STATUS_WEIGHT[row.status],
        row.total_budget_utilization_ratio,
        row.total_research_latency_seconds,
        row.row_number,
    )


def _status_count(
    rows: tuple[ResearchStrategyResearchLatencyBudgetRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_total_latency(
    rows: tuple[ResearchStrategyResearchLatencyBudgetRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(_sum_decimal(row.total_research_latency_seconds for row in rows), _count(len(rows)))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        compact = "".join(part for part in reason_code if part != "_")
        if not compact.isalnum() or reason_code.lower() != reason_code:
            raise ValueError("reason_codes must be lowercase snake case")
    normalized = tuple(sorted(dict.fromkeys(reason_codes), key=_reason_sort_key))
    if "latency_budget_pass" in normalized and len(normalized) != 1:
        raise ValueError("latency_budget_pass must stand alone")
    if NO_PACKETS_REASON in normalized and len(normalized) != 1:
        raise ValueError("no packets reason must stand alone")
    return normalized


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _optional_public_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _public_decimal(name, value)


def _public_count(name: str, value: object) -> Decimal:
    return _normalize_nonnegative_count(name, _public_decimal(name, value))


def _public_decimal(name: str, value: object) -> Decimal:
    _require_text(name, value)
    try:
        normalized = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    normalized = _normalize_decimal(name, normalized)
    quantized = _quantize(normalized)
    if format(quantized, "f") != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return quantized


def _public_datetime(name: str, value: object) -> datetime:
    _require_text(name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_above(name: str, value: Decimal, floor: Decimal) -> None:
    if value <= floor:
        raise ValueError(f"{name} must exceed its paired budget")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_private_reference(name: str, value: object) -> None:
    _require_text(name, value)


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains unsupported value")
