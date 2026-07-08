"""Pure public aggregate report for evidence-explained repricing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_EVIDENCE_REPRICE_EXPLANATION_CONFIG_VERSION = (
    "research-market-evidence-reprice-explanation-v0"
)

STATUSES = ("pass", "watch", "block")

NO_ROWS_REASON = "evidence_reprice_explanation_no_rows"
STALE_EVIDENCE_REASON = "evidence_reprice_explanation_stale_evidence"
SOURCE_CLASS_QUORUM_GAP_REASON = (
    "evidence_reprice_explanation_source_class_quorum_gap"
)
UNEXPLAINED_BOOK_MOVEMENT_REASON = (
    "evidence_reprice_explanation_unexplained_book_movement"
)
CONTRADICTION_PRESSURE_REASON = (
    "evidence_reprice_explanation_contradiction_pressure"
)
MANUAL_REVIEW_URGENT_REASON = "evidence_reprice_explanation_manual_review_urgent"
CLEAR_REASON = "evidence_reprice_explanation_clear"

REASON_CODES = (
    NO_ROWS_REASON,
    STALE_EVIDENCE_REASON,
    SOURCE_CLASS_QUORUM_GAP_REASON,
    UNEXPLAINED_BOOK_MOVEMENT_REASON,
    CONTRADICTION_PRESSURE_REASON,
    MANUAL_REVIEW_URGENT_REASON,
    CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_TERM_PARTS = (
    ("raw", "_candidate", "_id"),
    ("candidate", "_id"),
    ("market", "_id"),
    ("market", "_slug"),
    ("ques", "tion"),
    ("source", "_url"),
    ("source", "_text"),
    ("d", "sn"),
    ("table", "_name"),
    ("private", "_token"),
    ("to", "ken"),
    ("private", "_key"),
    ("secret",),
    ("credential",),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("posi", "tion"),
    ("sizing",),
    ("recommend", "ation"),
    ("http", "://"),
    ("https", "://"),
    ("://",),
)
_UNSAFE_PUBLIC_TERMS = tuple(_join_parts(*parts) for parts in _UNSAFE_PUBLIC_TERM_PARTS)


@dataclass(frozen=True)
class ResearchMarketEvidenceRepriceExplanationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_EVIDENCE_REPRICE_EXPLANATION_CONFIG_VERSION
    )
    evidence_age_watch_seconds: Decimal = Decimal("3600.000000")
    evidence_age_block_seconds: Decimal = Decimal("7200.000000")
    source_class_quorum_watch_ratio: Decimal = Decimal("0.750000")
    source_class_quorum_block_ratio: Decimal = Decimal("0.500000")
    unexplained_book_movement_watch_bps: Decimal = Decimal("100.000000")
    unexplained_book_movement_block_bps: Decimal = Decimal("250.000000")
    contradiction_pressure_watch_ratio: Decimal = Decimal("0.250000")
    contradiction_pressure_block_ratio: Decimal = Decimal("0.500000")
    manual_review_urgency_watch_ratio: Decimal = Decimal("0.750000")
    manual_review_urgency_block_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEvidenceRepriceExplanationConfig:
            raise ValueError("config must be exact")
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "evidence_age_watch_seconds",
            "evidence_age_block_seconds",
            "unexplained_book_movement_watch_bps",
            "unexplained_book_movement_block_bps",
            "manual_review_urgency_watch_ratio",
            "manual_review_urgency_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_watch_ratio",
            "source_class_quorum_block_ratio",
            "contradiction_pressure_watch_ratio",
            "contradiction_pressure_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.evidence_age_block_seconds < self.evidence_age_watch_seconds:
            raise ValueError("evidence_age_block_seconds must not be below watch seconds")
        if (
            self.source_class_quorum_block_ratio
            > self.source_class_quorum_watch_ratio
        ):
            raise ValueError(
                "source_class_quorum_block_ratio must not exceed watch ratio",
            )
        if (
            self.unexplained_book_movement_block_bps
            < self.unexplained_book_movement_watch_bps
        ):
            raise ValueError(
                "unexplained_book_movement_block_bps must not be below watch bps",
            )
        if (
            self.contradiction_pressure_block_ratio
            < self.contradiction_pressure_watch_ratio
        ):
            raise ValueError(
                "contradiction_pressure_block_ratio must not be below watch ratio",
            )
        if (
            self.manual_review_urgency_block_ratio
            < self.manual_review_urgency_watch_ratio
        ):
            raise ValueError(
                "manual_review_urgency_block_ratio must not be below watch ratio",
            )
        require_paper_only_flags("evidence reprice explanation config", self)


@dataclass(frozen=True)
class ResearchMarketEvidenceRepriceExplanationInput:
    aggregate_row_number: Decimal
    evidence_age_seconds: Decimal
    source_class_quorum_count: Decimal
    required_source_class_quorum_count: Decimal
    total_book_movement_bps: Decimal
    explained_book_movement_bps: Decimal
    contradiction_count: Decimal
    evidence_claim_count: Decimal
    manual_review_age_seconds: Decimal
    manual_review_sla_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEvidenceRepriceExplanationInput:
            raise ValueError("input must be exact")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_integral_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        for field_name in (
            "evidence_age_seconds",
            "source_class_quorum_count",
            "total_book_movement_bps",
            "explained_book_movement_bps",
            "contradiction_count",
            "manual_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_source_class_quorum_count",
            "evidence_claim_count",
            "manual_review_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_count",
            "required_source_class_quorum_count",
            "contradiction_count",
            "evidence_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.source_class_quorum_count > self.required_source_class_quorum_count:
            raise ValueError(
                "source_class_quorum_count must not exceed required quorum count",
            )
        if self.explained_book_movement_bps > self.total_book_movement_bps:
            raise ValueError(
                "explained_book_movement_bps must not exceed total_book_movement_bps",
            )
        if self.contradiction_count > self.evidence_claim_count:
            raise ValueError("contradiction_count must not exceed evidence_claim_count")
        require_paper_only_flags("evidence reprice explanation input", self)


@dataclass(frozen=True)
class ResearchMarketEvidenceRepriceExplanationRow:
    aggregate_row_number: Decimal
    evidence_age_seconds: Decimal
    source_class_quorum_count: Decimal
    required_source_class_quorum_count: Decimal
    source_class_quorum_ratio: Decimal
    total_book_movement_bps: Decimal
    explained_book_movement_bps: Decimal
    unexplained_book_movement_bps: Decimal
    contradiction_count: Decimal
    evidence_claim_count: Decimal
    contradiction_pressure_ratio: Decimal
    manual_review_age_seconds: Decimal
    manual_review_sla_seconds: Decimal
    manual_review_urgency_ratio: Decimal
    evidence_explainability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEvidenceRepriceExplanationRow:
            raise ValueError("row must be exact")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_integral_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        for field_name in (
            "evidence_age_seconds",
            "source_class_quorum_count",
            "required_source_class_quorum_count",
            "total_book_movement_bps",
            "explained_book_movement_bps",
            "unexplained_book_movement_bps",
            "contradiction_count",
            "evidence_claim_count",
            "manual_review_age_seconds",
            "manual_review_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_count",
            "required_source_class_quorum_count",
            "contradiction_count",
            "evidence_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_ratio",
            "contradiction_pressure_ratio",
            "manual_review_urgency_ratio",
            "evidence_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("evidence reprice explanation row", self)


@dataclass(frozen=True)
class ResearchMarketEvidenceRepriceExplanationReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    block_row_count: Decimal
    max_evidence_age_seconds: Decimal
    min_source_class_quorum_ratio: Decimal
    max_unexplained_book_movement_bps: Decimal
    max_contradiction_pressure_ratio: Decimal
    max_manual_review_urgency_ratio: Decimal
    average_evidence_explainability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketEvidenceRepriceExplanationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEvidenceRepriceExplanationReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "row_count",
            "pass_row_count",
            "watch_row_count",
            "block_row_count",
            "max_evidence_age_seconds",
            "min_source_class_quorum_ratio",
            "max_unexplained_book_movement_bps",
            "max_contradiction_pressure_ratio",
            "max_manual_review_urgency_ratio",
            "average_evidence_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("evidence reprice explanation report", self)
        reject_research_market_evidence_reprice_explanation_unsafe_public_payload(
            "evidence reprice explanation report",
            _unsigned_report_payload(self),
        )
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_evidence_reprice_explanation_report_payload(self)


def build_research_market_evidence_reprice_explanation_report(
    inputs: list[ResearchMarketEvidenceRepriceExplanationInput]
    | tuple[ResearchMarketEvidenceRepriceExplanationInput, ...],
    *,
    config: ResearchMarketEvidenceRepriceExplanationConfig,
    generated_at: datetime,
) -> ResearchMarketEvidenceRepriceExplanationReport:
    if type(config) is not ResearchMarketEvidenceRepriceExplanationConfig:
        raise ValueError(
            "config must be a ResearchMarketEvidenceRepriceExplanationConfig",
        )
    require_paper_only_flags("evidence reprice explanation config", config)
    rows = tuple(
        sorted(
            (
                _row_from_input(row_input, config=config)
                for row_input in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketEvidenceRepriceExplanationReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        row_count=_count(len(rows)),
        pass_row_count=_count(sum(row.status == "pass" for row in rows)),
        watch_row_count=_count(sum(row.status == "watch" for row in rows)),
        block_row_count=_count(sum(row.status == "block" for row in rows)),
        max_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANTUM),
        min_source_class_quorum_ratio=min(
            (row.source_class_quorum_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANTUM),
        max_unexplained_book_movement_bps=max(
            (row.unexplained_book_movement_bps for row in rows),
            default=ZERO,
        ).quantize(QUANTUM),
        max_contradiction_pressure_ratio=max(
            (row.contradiction_pressure_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANTUM),
        max_manual_review_urgency_ratio=max(
            (row.manual_review_urgency_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANTUM),
        average_evidence_explainability_score=_average_row_decimal(
            rows,
            "evidence_explainability_score",
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_market_evidence_reprice_explanation_report_payload(
    report: ResearchMarketEvidenceRepriceExplanationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketEvidenceRepriceExplanationReport:
        raise ValueError(
            "report must be a ResearchMarketEvidenceRepriceExplanationReport",
        )
    require_paper_only_flags("evidence reprice explanation report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_research_market_evidence_reprice_explanation_unsafe_public_payload(
        "evidence reprice explanation report payload",
        payload,
    )
    _validate_payload_digest(payload)
    return payload


def reject_research_market_evidence_reprice_explanation_unsafe_public_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _row_from_input(
    row_input: ResearchMarketEvidenceRepriceExplanationInput,
    *,
    config: ResearchMarketEvidenceRepriceExplanationConfig,
) -> ResearchMarketEvidenceRepriceExplanationRow:
    source_class_quorum_ratio = _ratio(
        row_input.source_class_quorum_count,
        row_input.required_source_class_quorum_count,
    )
    unexplained_book_movement_bps = _require_nonnegative_decimal(
        "unexplained_book_movement_bps",
        row_input.total_book_movement_bps - row_input.explained_book_movement_bps,
    )
    contradiction_pressure_ratio = _ratio(
        row_input.contradiction_count,
        row_input.evidence_claim_count,
    )
    manual_review_urgency_ratio = _ratio(
        row_input.manual_review_age_seconds,
        row_input.manual_review_sla_seconds,
    )
    status = _row_status(
        evidence_age_seconds=row_input.evidence_age_seconds,
        source_class_quorum_ratio=source_class_quorum_ratio,
        unexplained_book_movement_bps=unexplained_book_movement_bps,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        manual_review_urgency_ratio=manual_review_urgency_ratio,
        config=config,
    )
    return ResearchMarketEvidenceRepriceExplanationRow(
        aggregate_row_number=row_input.aggregate_row_number,
        evidence_age_seconds=row_input.evidence_age_seconds,
        source_class_quorum_count=row_input.source_class_quorum_count,
        required_source_class_quorum_count=row_input.required_source_class_quorum_count,
        source_class_quorum_ratio=source_class_quorum_ratio,
        total_book_movement_bps=row_input.total_book_movement_bps,
        explained_book_movement_bps=row_input.explained_book_movement_bps,
        unexplained_book_movement_bps=unexplained_book_movement_bps,
        contradiction_count=row_input.contradiction_count,
        evidence_claim_count=row_input.evidence_claim_count,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        manual_review_age_seconds=row_input.manual_review_age_seconds,
        manual_review_sla_seconds=row_input.manual_review_sla_seconds,
        manual_review_urgency_ratio=manual_review_urgency_ratio,
        evidence_explainability_score=_evidence_explainability_score(
            evidence_age_seconds=row_input.evidence_age_seconds,
            source_class_quorum_ratio=source_class_quorum_ratio,
            unexplained_book_movement_bps=unexplained_book_movement_bps,
            contradiction_pressure_ratio=contradiction_pressure_ratio,
            manual_review_urgency_ratio=manual_review_urgency_ratio,
            config=config,
        ),
        status=status,
        reason_codes=_row_reason_codes(
            status,
            evidence_age_seconds=row_input.evidence_age_seconds,
            source_class_quorum_ratio=source_class_quorum_ratio,
            unexplained_book_movement_bps=unexplained_book_movement_bps,
            contradiction_pressure_ratio=contradiction_pressure_ratio,
            manual_review_urgency_ratio=manual_review_urgency_ratio,
            config=config,
        ),
    )


def _row_status(
    *,
    evidence_age_seconds: Decimal,
    source_class_quorum_ratio: Decimal,
    unexplained_book_movement_bps: Decimal,
    contradiction_pressure_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    config: ResearchMarketEvidenceRepriceExplanationConfig,
) -> str:
    if (
        evidence_age_seconds >= config.evidence_age_block_seconds
        or source_class_quorum_ratio <= config.source_class_quorum_block_ratio
        or unexplained_book_movement_bps
        >= config.unexplained_book_movement_block_bps
        or contradiction_pressure_ratio >= config.contradiction_pressure_block_ratio
        or manual_review_urgency_ratio >= config.manual_review_urgency_block_ratio
    ):
        return "block"
    if (
        evidence_age_seconds >= config.evidence_age_watch_seconds
        or source_class_quorum_ratio < config.source_class_quorum_watch_ratio
        or unexplained_book_movement_bps
        >= config.unexplained_book_movement_watch_bps
        or contradiction_pressure_ratio >= config.contradiction_pressure_watch_ratio
        or manual_review_urgency_ratio >= config.manual_review_urgency_watch_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    status: str,
    *,
    evidence_age_seconds: Decimal,
    source_class_quorum_ratio: Decimal,
    unexplained_book_movement_bps: Decimal,
    contradiction_pressure_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    config: ResearchMarketEvidenceRepriceExplanationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence_age_seconds >= config.evidence_age_watch_seconds:
        reasons.append(STALE_EVIDENCE_REASON)
    if source_class_quorum_ratio < config.source_class_quorum_watch_ratio:
        reasons.append(SOURCE_CLASS_QUORUM_GAP_REASON)
    if unexplained_book_movement_bps >= config.unexplained_book_movement_watch_bps:
        reasons.append(UNEXPLAINED_BOOK_MOVEMENT_REASON)
    if contradiction_pressure_ratio >= config.contradiction_pressure_watch_ratio:
        reasons.append(CONTRADICTION_PRESSURE_REASON)
    if manual_review_urgency_ratio >= config.manual_review_urgency_watch_ratio:
        reasons.append(MANUAL_REVIEW_URGENT_REASON)
    if status == "pass" and not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _evidence_explainability_score(
    *,
    evidence_age_seconds: Decimal,
    source_class_quorum_ratio: Decimal,
    unexplained_book_movement_bps: Decimal,
    contradiction_pressure_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    config: ResearchMarketEvidenceRepriceExplanationConfig,
) -> Decimal:
    freshness_pressure = _ratio(evidence_age_seconds, config.evidence_age_block_seconds)
    quorum_gap_pressure = _require_nonnegative_decimal(
        "quorum_gap_pressure",
        ONE - source_class_quorum_ratio,
    )
    book_movement_pressure = _ratio(
        unexplained_book_movement_bps,
        config.unexplained_book_movement_block_bps,
    )
    urgency_pressure = _ratio(
        manual_review_urgency_ratio,
        config.manual_review_urgency_block_ratio,
    )
    pressure = min(
        ONE,
        max(
            freshness_pressure,
            quorum_gap_pressure,
            book_movement_pressure,
            contradiction_pressure_ratio,
            urgency_pressure,
        ),
    )
    return _require_nonnegative_decimal("evidence_explainability_score", ONE - pressure)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchMarketEvidenceRepriceExplanationInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows: list[ResearchMarketEvidenceRepriceExplanationInput] = []
    seen_row_numbers: set[Decimal] = set()
    for item in value:
        if type(item) is not ResearchMarketEvidenceRepriceExplanationInput:
            raise ValueError(
                "inputs must contain ResearchMarketEvidenceRepriceExplanationInput",
            )
        require_paper_only_flags("evidence reprice explanation input", item)
        if item.aggregate_row_number in seen_row_numbers:
            raise ValueError("duplicate aggregate_row_number")
        seen_row_numbers.add(item.aggregate_row_number)
        rows.append(item)
    return tuple(rows)


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketEvidenceRepriceExplanationRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows: list[ResearchMarketEvidenceRepriceExplanationRow] = []
    seen_row_numbers: set[Decimal] = set()
    for item in value:
        if type(item) is not ResearchMarketEvidenceRepriceExplanationRow:
            raise ValueError(
                "rows must contain ResearchMarketEvidenceRepriceExplanationRow",
            )
        require_paper_only_flags("evidence reprice explanation row", item)
        if item.aggregate_row_number in seen_row_numbers:
            raise ValueError("duplicate aggregate_row_number")
        seen_row_numbers.add(item.aggregate_row_number)
        rows.append(item)
    return tuple(sorted(rows, key=_row_sort_key))


def _validate_row(row: ResearchMarketEvidenceRepriceExplanationRow) -> None:
    if row.required_source_class_quorum_count <= ZERO:
        raise ValueError("required_source_class_quorum_count must be positive")
    if row.evidence_claim_count <= ZERO:
        raise ValueError("evidence_claim_count must be positive")
    if row.manual_review_sla_seconds <= ZERO:
        raise ValueError("manual_review_sla_seconds must be positive")
    if row.source_class_quorum_count > row.required_source_class_quorum_count:
        raise ValueError(
            "source_class_quorum_count must not exceed required quorum count",
        )
    if row.contradiction_count > row.evidence_claim_count:
        raise ValueError("contradiction_count must not exceed evidence_claim_count")
    if row.explained_book_movement_bps > row.total_book_movement_bps:
        raise ValueError(
            "explained_book_movement_bps must not exceed total_book_movement_bps",
        )
    if row.source_class_quorum_ratio != _ratio(
        row.source_class_quorum_count,
        row.required_source_class_quorum_count,
    ):
        raise ValueError("source_class_quorum_ratio must match quorum counts")
    if row.unexplained_book_movement_bps != _require_nonnegative_decimal(
        "unexplained_book_movement_bps",
        row.total_book_movement_bps - row.explained_book_movement_bps,
    ):
        raise ValueError("unexplained_book_movement_bps must match book movement")
    if row.contradiction_pressure_ratio != _ratio(
        row.contradiction_count,
        row.evidence_claim_count,
    ):
        raise ValueError("contradiction_pressure_ratio must match contradiction count")
    if row.manual_review_urgency_ratio != _ratio(
        row.manual_review_age_seconds,
        row.manual_review_sla_seconds,
    ):
        raise ValueError("manual_review_urgency_ratio must match review age")


def _validate_report(report: ResearchMarketEvidenceRepriceExplanationReport) -> None:
    rows = report.rows
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_row_count != _count(sum(row.status == "pass" for row in rows)):
        raise ValueError("pass_row_count must match rows")
    if report.watch_row_count != _count(sum(row.status == "watch" for row in rows)):
        raise ValueError("watch_row_count must match rows")
    if report.block_row_count != _count(sum(row.status == "block" for row in rows)):
        raise ValueError("block_row_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.max_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.min_source_class_quorum_ratio != min(
        (row.source_class_quorum_ratio for row in rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("min_source_class_quorum_ratio must match rows")
    if report.max_unexplained_book_movement_bps != max(
        (row.unexplained_book_movement_bps for row in rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("max_unexplained_book_movement_bps must match rows")
    if report.max_contradiction_pressure_ratio != max(
        (row.contradiction_pressure_ratio for row in rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("max_contradiction_pressure_ratio must match rows")
    if report.max_manual_review_urgency_ratio != max(
        (row.manual_review_urgency_ratio for row in rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("max_manual_review_urgency_ratio must match rows")
    if report.average_evidence_explainability_score != _average_row_decimal(
        rows,
        "evidence_explainability_score",
    ):
        raise ValueError("average_evidence_explainability_score must match rows")


def _report_status(rows: tuple[ResearchMarketEvidenceRepriceExplanationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketEvidenceRepriceExplanationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_ROWS_REASON,)
    reason_set = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    }
    if not reason_set:
        return (CLEAR_REASON,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_set)


def _row_sort_key(row: ResearchMarketEvidenceRepriceExplanationRow) -> tuple[Decimal, Decimal]:
    return STATUS_RANK[row.status], row.aggregate_row_number


def _average_row_decimal(
    rows: tuple[ResearchMarketEvidenceRepriceExplanationRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(
        sum((getattr(row, field_name) for row in rows), ZERO),
        _count(len(rows)),
    )


def _json_ready(value: Any) -> Any:
    return json_ready_no_floats(value)


def _unsigned_report_payload(
    report: ResearchMarketEvidenceRepriceExplanationReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_digest(report: ResearchMarketEvidenceRepriceExplanationReport) -> str:
    payload = _unsigned_report_payload(report)
    rendered = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(rendered.encode("utf-8")).hexdigest()


def _require_or_set_digest(
    report: ResearchMarketEvidenceRepriceExplanationReport,
) -> None:
    expected_digest = _report_digest(report)
    if report.derived_validation_digest:
        _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
    else:
        object.__setattr__(report, "derived_validation_digest", expected_digest)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    rendered = json.dumps(
        unsigned,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if digest != sha256(rendered.encode("utf-8")).hexdigest():
        raise ValueError("derived_validation_digest must match payload")


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character in value for character in "\r\n\t"):
        raise ValueError(f"{field_name} must not contain control whitespace")
    reject_research_market_evidence_reprice_explanation_unsafe_public_payload(
        field_name,
        value,
    )
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return normalized


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_nonnegative_decimal("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_set: set[str] = set()
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        if item not in REASON_CODES:
            raise ValueError(f"unknown reason_code: {item}")
        reason_set.add(item)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_set)


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            strings.append(key)
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


__all__ = (
    "DEFAULT_RESEARCH_MARKET_EVIDENCE_REPRICE_EXPLANATION_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketEvidenceRepriceExplanationConfig",
    "ResearchMarketEvidenceRepriceExplanationInput",
    "ResearchMarketEvidenceRepriceExplanationReport",
    "ResearchMarketEvidenceRepriceExplanationRow",
    "build_research_market_evidence_reprice_explanation_report",
    "reject_research_market_evidence_reprice_explanation_unsafe_public_payload",
    "research_market_evidence_reprice_explanation_report_payload",
)
