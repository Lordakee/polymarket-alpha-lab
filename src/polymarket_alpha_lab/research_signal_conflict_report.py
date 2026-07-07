"""Pure research signal conflict reporting with redacted public output."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SIGNAL_CONFLICT_REPORT_CONFIG_VERSION = (
    "research-signal-conflict-report-v1"
)

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")

_PASS_REASON = "research_signal_conflict_pass"
_EMPTY_REASON = "research_signal_conflict_empty"
_SOURCE_DISAGREEMENT_WATCH_REASON = "source_disagreement_watch"
_SOURCE_DISAGREEMENT_BLOCK_REASON = "source_disagreement_block"
_EVIDENCE_CONFLICT_WATCH_REASON = "evidence_conflict_watch"
_EVIDENCE_CONFLICT_BLOCK_REASON = "evidence_conflict_block"
_PROBABILITY_GAP_WATCH_REASON = "probability_gap_watch"
_PROBABILITY_GAP_BLOCK_REASON = "probability_gap_block"
_RULE_RISK_WATCH_REASON = "rule_risk_watch"
_RULE_RISK_BLOCK_REASON = "rule_risk_block"

_ALIGNED_PROBABILITY_GAP = "aligned_probability_gap"
_WATCH_PROBABILITY_GAP = "watch_probability_gap"
_BLOCK_PROBABILITY_GAP = "block_probability_gap"

_NO_REVIEW_PROMPT = "no_conflict_review_required"
_SOURCE_REVIEW_PROMPT = "review_origin_family_disagreement"
_EVIDENCE_REVIEW_PROMPT = "review_conflicting_evidence"
_PROBABILITY_REVIEW_PROMPT = "review_probability_gap_explanation"
_RULE_RISK_REVIEW_PROMPT = "review_rule_risk_controls"

_REASON_PRIORITY = (
    _SOURCE_DISAGREEMENT_BLOCK_REASON,
    _EVIDENCE_CONFLICT_BLOCK_REASON,
    _PROBABILITY_GAP_BLOCK_REASON,
    _RULE_RISK_BLOCK_REASON,
    _SOURCE_DISAGREEMENT_WATCH_REASON,
    _EVIDENCE_CONFLICT_WATCH_REASON,
    _PROBABILITY_GAP_WATCH_REASON,
    _RULE_RISK_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_REASONS = frozenset(
    (
        _SOURCE_DISAGREEMENT_BLOCK_REASON,
        _EVIDENCE_CONFLICT_BLOCK_REASON,
        _PROBABILITY_GAP_BLOCK_REASON,
        _RULE_RISK_BLOCK_REASON,
    ),
)
_WATCH_REASONS = frozenset(
    (
        _SOURCE_DISAGREEMENT_WATCH_REASON,
        _EVIDENCE_CONFLICT_WATCH_REASON,
        _PROBABILITY_GAP_WATCH_REASON,
        _RULE_RISK_WATCH_REASON,
    ),
)
_REVIEW_PROMPT_PRIORITY = (
    _SOURCE_REVIEW_PROMPT,
    _EVIDENCE_REVIEW_PROMPT,
    _PROBABILITY_REVIEW_PROMPT,
    _RULE_RISK_REVIEW_PROMPT,
    _NO_REVIEW_PROMPT,
)

_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "slug",
        "source_ref",
        "source_reference",
        "source_url",
        "source_text",
        "http://",
        "https://",
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


@dataclass(frozen=True)
class ResearchSignalConflictConfig:
    config_version: str = DEFAULT_RESEARCH_SIGNAL_CONFLICT_REPORT_CONFIG_VERSION
    watch_source_disagreement_count: Decimal = Decimal("1")
    block_source_disagreement_count: Decimal = Decimal("3")
    watch_evidence_conflict_count: Decimal = Decimal("1")
    block_evidence_conflict_count: Decimal = Decimal("2")
    watch_probability_gap: Decimal = Decimal("0.050000")
    block_probability_gap: Decimal = Decimal("0.150000")
    watch_rule_risk_score: Decimal = Decimal("0.300000")
    block_rule_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "watch_source_disagreement_count",
            "block_source_disagreement_count",
            "watch_evidence_conflict_count",
            "block_evidence_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_probability_gap",
            "block_probability_gap",
            "watch_rule_risk_score",
            "block_rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "block_source_disagreement_count",
            self.watch_source_disagreement_count,
            self.block_source_disagreement_count,
        )
        _require_at_least(
            "block_evidence_conflict_count",
            self.watch_evidence_conflict_count,
            self.block_evidence_conflict_count,
        )
        _require_at_least(
            "block_probability_gap",
            self.watch_probability_gap,
            self.block_probability_gap,
        )
        _require_at_least(
            "block_rule_risk_score",
            self.watch_rule_risk_score,
            self.block_rule_risk_score,
        )
        require_paper_only_flags("research signal conflict config", self)


@dataclass(frozen=True)
class ResearchSignalConflictRecord:
    candidate_reference: str
    market_reference: str
    origin_reference: str
    origin_family: str
    observed_at: datetime
    model_probability: Decimal
    source_probability: Decimal
    source_disagreement_count: Decimal
    evidence_conflict_count: Decimal
    rule_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_reference", self.market_reference)
        _require_text("origin_reference", self.origin_reference)
        object.__setattr__(
            self,
            "candidate_reference",
            _redacted_marker("candidate_marker_", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "market_reference",
            _redacted_marker("market_marker_", self.market_reference),
        )
        object.__setattr__(
            self,
            "origin_reference",
            _redacted_marker("origin_marker_", self.origin_reference),
        )
        _require_public_text("origin_family", self.origin_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "source_probability",
            "rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_disagreement_count",
            "evidence_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("research signal conflict record", self)


@dataclass(frozen=True)
class ResearchSignalConflictRow:
    redacted_candidate_marker: str
    redacted_market_marker: str
    redacted_origin_marker: str
    origin_family: str
    observed_at: datetime
    model_probability: Decimal
    source_probability: Decimal
    probability_gap: Decimal
    source_disagreement_count: Decimal
    evidence_conflict_count: Decimal
    rule_risk_score: Decimal
    probability_gap_explanation: str
    status: str
    reason_codes: tuple[str, ...]
    review_prompts: tuple[str, ...]
    result_integrity_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_marker(
            "redacted_candidate_marker",
            self.redacted_candidate_marker,
            "candidate_marker_",
        )
        _require_redacted_marker(
            "redacted_market_marker",
            self.redacted_market_marker,
            "market_marker_",
        )
        _require_redacted_marker(
            "redacted_origin_marker",
            self.redacted_origin_marker,
            "origin_marker_",
        )
        _require_public_text("origin_family", self.origin_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "source_probability",
            "probability_gap",
            "rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_disagreement_count",
            "evidence_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_probability_gap_explanation(
            "probability_gap_explanation",
            self.probability_gap_explanation,
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "review_prompts",
            _normalize_review_prompts(self.review_prompts),
        )
        _require_integrity_digest(
            "result_integrity_digest",
            self.result_integrity_digest,
        )
        _validate_row(self)
        require_paper_only_flags("research signal conflict row", self)


@dataclass(frozen=True)
class ResearchSignalConflictReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_probability_gap: Decimal
    max_source_disagreement_count: Decimal
    max_evidence_conflict_count: Decimal
    max_rule_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    review_prompts: tuple[str, ...]
    rows: tuple[ResearchSignalConflictRow, ...]
    report_integrity_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_source_disagreement_count",
            "max_evidence_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_probability_gap",
            "max_rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "review_prompts",
            _normalize_review_prompts(self.review_prompts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_integrity_digest(
            "report_integrity_digest",
            self.report_integrity_digest,
        )
        _validate_report(self)
        require_paper_only_flags("research signal conflict report", self)


def build_research_signal_conflict_report(
    records: Iterable[object],
    *,
    config: ResearchSignalConflictConfig,
    generated_at: datetime,
) -> ResearchSignalConflictReport:
    if type(config) is not ResearchSignalConflictConfig:
        raise ValueError("config must be a ResearchSignalConflictConfig")
    require_paper_only_flags("research signal conflict config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_record(
                    record,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for record in _normalize_records(records)
            ),
            key=_row_key,
        ),
    )
    signal_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    max_probability_gap = _max_decimal(row.probability_gap for row in rows)
    max_source_disagreement_count = _max_count(
        row.source_disagreement_count for row in rows
    )
    max_evidence_conflict_count = _max_count(row.evidence_conflict_count for row in rows)
    max_rule_risk_score = _max_decimal(row.rule_risk_score for row in rows)
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    review_prompts = _report_review_prompts(rows)
    return ResearchSignalConflictReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=signal_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_probability_gap=max_probability_gap,
        max_source_disagreement_count=max_source_disagreement_count,
        max_evidence_conflict_count=max_evidence_conflict_count,
        max_rule_risk_score=max_rule_risk_score,
        status=status,
        reason_codes=reason_codes,
        review_prompts=review_prompts,
        rows=rows,
        report_integrity_digest=_report_integrity_digest_from_parts(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            signal_count=signal_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            max_probability_gap=max_probability_gap,
            max_source_disagreement_count=max_source_disagreement_count,
            max_evidence_conflict_count=max_evidence_conflict_count,
            max_rule_risk_score=max_rule_risk_score,
            status=status,
            reason_codes=reason_codes,
            review_prompts=review_prompts,
            rows=rows,
        ),
    )


def research_signal_conflict_report_payload(
    report: ResearchSignalConflictReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSignalConflictReport:
        raise ValueError("report must be a ResearchSignalConflictReport")
    require_paper_only_flags("research signal conflict report", report)
    _reject_unsafe_public_payload("research signal conflict report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    require_paper_only_flags(
        "research signal conflict payload",
        _PayloadFlags(payload),
    )
    _reject_unsafe_public_payload("research signal conflict payload", payload)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _row_from_record(
    record: ResearchSignalConflictRecord,
    *,
    config: ResearchSignalConflictConfig,
    generated_at: datetime,
) -> ResearchSignalConflictRow:
    if record.observed_at > generated_at:
        raise ValueError("observed_at must not follow generated_at")
    probability_gap = _probability_gap(record)
    reason_codes = list(record.reason_codes)
    reason_codes.extend(
        _scored_reason_codes(
            record,
            probability_gap=probability_gap,
            config=config,
        ),
    )
    if not any(reason_code in _WATCH_REASONS for reason_code in reason_codes) and not any(
        reason_code in _BLOCK_REASONS for reason_code in reason_codes
    ):
        reason_codes.append(_PASS_REASON)
    stable_reason_codes = _stable_reason_codes("reason_codes", tuple(reason_codes))
    status = _status_from_reason_codes(stable_reason_codes)
    review_prompts = _review_prompts_from_reason_codes(stable_reason_codes)
    probability_gap_explanation = _probability_gap_explanation(
        probability_gap,
        config=config,
    )
    return ResearchSignalConflictRow(
        redacted_candidate_marker=record.candidate_reference,
        redacted_market_marker=record.market_reference,
        redacted_origin_marker=record.origin_reference,
        origin_family=record.origin_family,
        observed_at=record.observed_at,
        model_probability=record.model_probability,
        source_probability=record.source_probability,
        probability_gap=probability_gap,
        source_disagreement_count=record.source_disagreement_count,
        evidence_conflict_count=record.evidence_conflict_count,
        rule_risk_score=record.rule_risk_score,
        probability_gap_explanation=probability_gap_explanation,
        status=status,
        reason_codes=stable_reason_codes,
        review_prompts=review_prompts,
        result_integrity_digest=_row_integrity_digest_from_parts(
            redacted_candidate_marker=record.candidate_reference,
            redacted_market_marker=record.market_reference,
            redacted_origin_marker=record.origin_reference,
            origin_family=record.origin_family,
            observed_at=record.observed_at,
            model_probability=record.model_probability,
            source_probability=record.source_probability,
            probability_gap=probability_gap,
            source_disagreement_count=record.source_disagreement_count,
            evidence_conflict_count=record.evidence_conflict_count,
            rule_risk_score=record.rule_risk_score,
            probability_gap_explanation=probability_gap_explanation,
            status=status,
            reason_codes=stable_reason_codes,
            review_prompts=review_prompts,
        ),
    )


def _scored_reason_codes(
    record: ResearchSignalConflictRecord,
    *,
    probability_gap: Decimal,
    config: ResearchSignalConflictConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_high_reason(
        reason_codes,
        record.source_disagreement_count,
        config.watch_source_disagreement_count,
        config.block_source_disagreement_count,
        _SOURCE_DISAGREEMENT_WATCH_REASON,
        _SOURCE_DISAGREEMENT_BLOCK_REASON,
    )
    _append_high_reason(
        reason_codes,
        record.evidence_conflict_count,
        config.watch_evidence_conflict_count,
        config.block_evidence_conflict_count,
        _EVIDENCE_CONFLICT_WATCH_REASON,
        _EVIDENCE_CONFLICT_BLOCK_REASON,
    )
    _append_high_reason(
        reason_codes,
        probability_gap,
        config.watch_probability_gap,
        config.block_probability_gap,
        _PROBABILITY_GAP_WATCH_REASON,
        _PROBABILITY_GAP_BLOCK_REASON,
    )
    _append_high_reason(
        reason_codes,
        record.rule_risk_score,
        config.watch_rule_risk_score,
        config.block_rule_risk_score,
        _RULE_RISK_WATCH_REASON,
        _RULE_RISK_BLOCK_REASON,
    )
    return tuple(reason_codes)


def _append_high_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_value:
        reason_codes.append(block_reason)
    elif value >= watch_value:
        reason_codes.append(watch_reason)


def _normalize_records(
    records: Iterable[object],
) -> tuple[ResearchSignalConflictRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be iterable")
    try:
        items = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be iterable") from exc
    seen_markers: set[str] = set()
    for item in items:
        if type(item) is not ResearchSignalConflictRecord:
            raise ValueError("records must contain ResearchSignalConflictRecord values")
        require_paper_only_flags("research signal conflict record", item)
        if item.candidate_reference in seen_markers:
            raise ValueError("duplicate candidate_reference in records")
        seen_markers.add(item.candidate_reference)
    return items


def _normalize_rows(rows: object) -> tuple[ResearchSignalConflictRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSignalConflictRow:
            raise ValueError("rows must contain ResearchSignalConflictRow values")
        _validate_row(row)
        require_paper_only_flags("research signal conflict row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must be sorted")
    if len({row.redacted_candidate_marker for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: ResearchSignalConflictRow) -> None:
    if row.probability_gap != _probability_gap(row):
        raise ValueError("probability_gap must match probabilities")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and _PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")
    if row.status == "watch" and not any(
        reason_code in _WATCH_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must include watch reason")
    if row.status == "block" and not any(
        reason_code in _BLOCK_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must include block reason")
    if row.review_prompts != _review_prompts_from_reason_codes(row.reason_codes):
        raise ValueError("review_prompts must match reason_codes")
    if row.result_integrity_digest != _row_integrity_digest(row):
        raise ValueError("result_integrity_digest must match row")


def _validate_report(report: ResearchSignalConflictReport) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_probability_gap != _max_decimal(row.probability_gap for row in rows):
        raise ValueError("max_probability_gap must match rows")
    if report.max_source_disagreement_count != _max_count(
        row.source_disagreement_count for row in rows
    ):
        raise ValueError("max_source_disagreement_count must match rows")
    if report.max_evidence_conflict_count != _max_count(
        row.evidence_conflict_count for row in rows
    ):
        raise ValueError("max_evidence_conflict_count must match rows")
    if report.max_rule_risk_score != _max_decimal(row.rule_risk_score for row in rows):
        raise ValueError("max_rule_risk_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.review_prompts != _report_review_prompts(rows):
        raise ValueError("review_prompts must match rows")
    if report.report_integrity_digest != _report_integrity_digest(report):
        raise ValueError("report_integrity_digest must match report")


def _row_integrity_digest(row: ResearchSignalConflictRow) -> str:
    return _row_integrity_digest_from_parts(
        redacted_candidate_marker=row.redacted_candidate_marker,
        redacted_market_marker=row.redacted_market_marker,
        redacted_origin_marker=row.redacted_origin_marker,
        origin_family=row.origin_family,
        observed_at=row.observed_at,
        model_probability=row.model_probability,
        source_probability=row.source_probability,
        probability_gap=row.probability_gap,
        source_disagreement_count=row.source_disagreement_count,
        evidence_conflict_count=row.evidence_conflict_count,
        rule_risk_score=row.rule_risk_score,
        probability_gap_explanation=row.probability_gap_explanation,
        status=row.status,
        reason_codes=row.reason_codes,
        review_prompts=row.review_prompts,
    )


def _row_integrity_digest_from_parts(
    *,
    redacted_candidate_marker: str,
    redacted_market_marker: str,
    redacted_origin_marker: str,
    origin_family: str,
    observed_at: datetime,
    model_probability: Decimal,
    source_probability: Decimal,
    probability_gap: Decimal,
    source_disagreement_count: Decimal,
    evidence_conflict_count: Decimal,
    rule_risk_score: Decimal,
    probability_gap_explanation: str,
    status: str,
    reason_codes: tuple[str, ...],
    review_prompts: tuple[str, ...],
) -> str:
    return _integrity_digest(
        (
            ("redacted_candidate_marker", redacted_candidate_marker),
            ("redacted_market_marker", redacted_market_marker),
            ("redacted_origin_marker", redacted_origin_marker),
            ("origin_family", origin_family),
            ("observed_at", observed_at),
            ("model_probability", model_probability),
            ("source_probability", source_probability),
            ("probability_gap", probability_gap),
            ("source_disagreement_count", source_disagreement_count),
            ("evidence_conflict_count", evidence_conflict_count),
            ("rule_risk_score", rule_risk_score),
            ("probability_gap_explanation", probability_gap_explanation),
            ("status", status),
            ("reason_codes", reason_codes),
            ("review_prompts", review_prompts),
        ),
    )


def _report_integrity_digest(report: ResearchSignalConflictReport) -> str:
    return _report_integrity_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        signal_count=report.signal_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        max_probability_gap=report.max_probability_gap,
        max_source_disagreement_count=report.max_source_disagreement_count,
        max_evidence_conflict_count=report.max_evidence_conflict_count,
        max_rule_risk_score=report.max_rule_risk_score,
        status=report.status,
        reason_codes=report.reason_codes,
        review_prompts=report.review_prompts,
        rows=report.rows,
    )


def _report_integrity_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    signal_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    max_probability_gap: Decimal,
    max_source_disagreement_count: Decimal,
    max_evidence_conflict_count: Decimal,
    max_rule_risk_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    review_prompts: tuple[str, ...],
    rows: tuple[ResearchSignalConflictRow, ...],
) -> str:
    return _integrity_digest(
        (
            ("generated_at", generated_at),
            ("config_version", config_version),
            ("signal_count", signal_count),
            ("pass_count", pass_count),
            ("watch_count", watch_count),
            ("block_count", block_count),
            ("max_probability_gap", max_probability_gap),
            ("max_source_disagreement_count", max_source_disagreement_count),
            ("max_evidence_conflict_count", max_evidence_conflict_count),
            ("max_rule_risk_score", max_rule_risk_score),
            ("status", status),
            ("reason_codes", reason_codes),
            ("review_prompts", review_prompts),
            ("row_integrity_digests", tuple(_row_integrity_digest(row) for row in rows)),
        ),
    )


def _integrity_digest(fields: Iterable[tuple[str, object]]) -> str:
    digest = sha256()
    for field_name, value in fields:
        encoded_value = _digest_value(value)
        digest.update(field_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(encoded_value)).encode("ascii"))
        digest.update(b":")
        digest.update(encoded_value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _digest_value(value: object) -> str:
    if type(value) is str:
        return value
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        encoded_items = tuple(_digest_value(item) for item in value)
        return "".join(f"{len(item)}:{item}" for item in encoded_items)
    raise ValueError("integrity value must be canonical")


def _probability_gap(value: object) -> Decimal:
    return _quantize(
        abs(getattr(value, "model_probability") - getattr(value, "source_probability")),
    )


def _probability_gap_explanation(
    probability_gap: Decimal,
    *,
    config: ResearchSignalConflictConfig,
) -> str:
    if probability_gap >= config.block_probability_gap:
        return _BLOCK_PROBABILITY_GAP
    if probability_gap >= config.watch_probability_gap:
        return _WATCH_PROBABILITY_GAP
    return _ALIGNED_PROBABILITY_GAP


def _report_status(rows: tuple[ResearchSignalConflictRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSignalConflictRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in _WATCH_REASONS or reason_code in _BLOCK_REASONS
    }
    if not observed:
        return (_PASS_REASON,)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed)


def _report_review_prompts(
    rows: tuple[ResearchSignalConflictRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_NO_REVIEW_PROMPT,)
    observed = {
        review_prompt
        for row in rows
        for review_prompt in row.review_prompts
        if review_prompt != _NO_REVIEW_PROMPT
    }
    if not observed:
        return (_NO_REVIEW_PROMPT,)
    return tuple(
        review_prompt
        for review_prompt in _REVIEW_PROMPT_PRIORITY
        if review_prompt in observed
    )


def _review_prompts_from_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    prompts: list[str] = []
    if any(
        reason_code
        in (_SOURCE_DISAGREEMENT_WATCH_REASON, _SOURCE_DISAGREEMENT_BLOCK_REASON)
        for reason_code in reason_codes
    ):
        prompts.append(_SOURCE_REVIEW_PROMPT)
    if any(
        reason_code in (_EVIDENCE_CONFLICT_WATCH_REASON, _EVIDENCE_CONFLICT_BLOCK_REASON)
        for reason_code in reason_codes
    ):
        prompts.append(_EVIDENCE_REVIEW_PROMPT)
    if any(
        reason_code in (_PROBABILITY_GAP_WATCH_REASON, _PROBABILITY_GAP_BLOCK_REASON)
        for reason_code in reason_codes
    ):
        prompts.append(_PROBABILITY_REVIEW_PROMPT)
    if any(
        reason_code in (_RULE_RISK_WATCH_REASON, _RULE_RISK_BLOCK_REASON)
        for reason_code in reason_codes
    ):
        prompts.append(_RULE_RISK_REVIEW_PROMPT)
    if not prompts:
        return (_NO_REVIEW_PROMPT,)
    return tuple(prompts)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_key(
    row: ResearchSignalConflictRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, datetime, str, str, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.probability_gap,
        -row.rule_risk_score,
        -row.evidence_conflict_count,
        -row.source_disagreement_count,
        row.observed_at,
        row.redacted_candidate_marker,
        row.redacted_market_marker,
        row.redacted_origin_marker,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        if reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        reason_index = _REASON_PRIORITY.index(reason_code)
        if reason_index <= previous_index:
            raise ValueError("reason_codes must use priority sequence")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        previous_index = reason_index
    return reason_codes


def _stable_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_public_text(field_name, item)
    return tuple(sorted(set(value)))


def _normalize_review_prompts(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("review_prompts must be a tuple")
    prompts = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for prompt in prompts:
        _require_public_text("review_prompts", prompt)
        if prompt not in _REVIEW_PROMPT_PRIORITY:
            raise ValueError("review_prompts must be known")
        prompt_index = _REVIEW_PROMPT_PRIORITY.index(prompt)
        if prompt_index <= previous_index:
            raise ValueError("review_prompts must use priority sequence")
        if prompt in seen:
            raise ValueError("review_prompts must be unique")
        seen.add(prompt)
        previous_index = prompt_index
    return prompts


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _max_count(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return Decimal("0")
    return max(items)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_at_least(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{field_name} must be at least watch threshold")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_public_text(field_name: str, value: object) -> None:
    _require_text(field_name, value)
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be block, watch, or pass")


def _require_probability_gap_explanation(field_name: str, value: object) -> None:
    if value not in (
        _ALIGNED_PROBABILITY_GAP,
        _WATCH_PROBABILITY_GAP,
        _BLOCK_PROBABILITY_GAP,
    ):
        raise ValueError(f"{field_name} must be a known probability gap explanation")


def _require_integrity_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _redacted_marker(prefix: str, value: str) -> str:
    digest = sha256(f"{prefix}\0{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _require_redacted_marker(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be redacted")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    suffix = value[len(prefix) :]
    if len(suffix) != 16 or any(character not in _HEX_CHARS for character in suffix):
        raise ValueError(f"{field_name} must be redacted")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}: non-string key")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _reject_unsafe_public_text(label, field_name)
            _reject_unsafe_public_payload(label, getattr(value, field_name))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


__all__ = (
    "DEFAULT_RESEARCH_SIGNAL_CONFLICT_REPORT_CONFIG_VERSION",
    "ResearchSignalConflictConfig",
    "ResearchSignalConflictRecord",
    "ResearchSignalConflictReport",
    "ResearchSignalConflictRow",
    "build_research_signal_conflict_report",
    "research_signal_conflict_report_payload",
)
