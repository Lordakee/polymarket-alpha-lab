"""Pure post-review readiness report for manual queue handoff."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_STRATEGY_POST_REVIEW_READINESS_REPORT_CONFIG_VERSION = (
    "research-strategy-post-review-readiness-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_CANDIDATES_REASON = "post_review_readiness_no_candidates"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_readiness_score",
    "min_readiness_score",
    "max_manual_review_urgency_score",
    "handoff_status",
    "manual_decision_queue_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_PRIORITY = (
    "evidence_maturity_block",
    "source_corroboration_block",
    "cost_freshness_block",
    "specialist_consensus_block",
    "unresolved_blocker_pressure_block",
    "manual_review_urgency_block",
    "post_review_readiness_block",
    "evidence_maturity_watch",
    "source_corroboration_watch",
    "cost_freshness_watch",
    "specialist_consensus_watch",
    "unresolved_blocker_pressure_watch",
    "manual_review_urgency_watch",
    "post_review_readiness_watch",
    "post_review_readiness_pass",
    NO_CANDIDATES_REASON,
)
UNSAFE_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "private" "_" "key",
    "api" "_" "key",
    "sec" "ret",
    "mar" "ket" "_" "id",
    "s" "lug",
    "ques" "tion",
    "source" "_" "url",
    "source" "_" "text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "po" "sition",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "req" "uests",
    "ht" "tp",
    "sock" "et",
    "sub" "process",
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyPostReviewReadinessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_POST_REVIEW_READINESS_REPORT_CONFIG_VERSION
    )
    evidence_maturity_pass_floor: Decimal = Decimal("0.800000")
    evidence_maturity_watch_floor: Decimal = Decimal("0.600000")
    source_corroboration_pass_floor: Decimal = Decimal("0.800000")
    source_corroboration_watch_floor: Decimal = Decimal("0.600000")
    cost_freshness_pass_floor: Decimal = Decimal("0.800000")
    cost_freshness_watch_floor: Decimal = Decimal("0.600000")
    specialist_consensus_pass_floor: Decimal = Decimal("0.800000")
    specialist_consensus_watch_floor: Decimal = Decimal("0.600000")
    unresolved_blocker_pressure_watch_ceiling: Decimal = Decimal("0.250000")
    unresolved_blocker_pressure_block_ceiling: Decimal = Decimal("0.600000")
    manual_review_urgency_pass_floor: Decimal = Decimal("0.700000")
    manual_review_urgency_watch_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPostReviewReadinessConfig, "config")
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "evidence_maturity_pass_floor",
            "evidence_maturity_watch_floor",
            "source_corroboration_pass_floor",
            "source_corroboration_watch_floor",
            "cost_freshness_pass_floor",
            "cost_freshness_watch_floor",
            "specialist_consensus_pass_floor",
            "specialist_consensus_watch_floor",
            "unresolved_blocker_pressure_watch_ceiling",
            "unresolved_blocker_pressure_block_ceiling",
            "manual_review_urgency_pass_floor",
            "manual_review_urgency_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_maturity_pass_floor",
            self.evidence_maturity_pass_floor,
            self.evidence_maturity_watch_floor,
        )
        _require_at_least(
            "source_corroboration_pass_floor",
            self.source_corroboration_pass_floor,
            self.source_corroboration_watch_floor,
        )
        _require_at_least(
            "cost_freshness_pass_floor",
            self.cost_freshness_pass_floor,
            self.cost_freshness_watch_floor,
        )
        _require_at_least(
            "specialist_consensus_pass_floor",
            self.specialist_consensus_pass_floor,
            self.specialist_consensus_watch_floor,
        )
        _require_at_most(
            "unresolved_blocker_pressure_watch_ceiling",
            self.unresolved_blocker_pressure_watch_ceiling,
            self.unresolved_blocker_pressure_block_ceiling,
        )
        _require_at_least(
            "manual_review_urgency_pass_floor",
            self.manual_review_urgency_pass_floor,
            self.manual_review_urgency_watch_floor,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyPostReviewReadinessCandidate(_FinalDataclass):
    reviewed_candidate_key: str
    evidence_maturity_score: Decimal
    source_corroboration_score: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    unresolved_blocker_pressure: Decimal
    manual_review_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyPostReviewReadinessCandidate,
            "candidate",
        )
        _require_internal_reference_text(
            "reviewed_candidate_key",
            self.reviewed_candidate_key,
        )
        for field_name in (
            "evidence_maturity_score",
            "source_corroboration_score",
            "cost_freshness_score",
            "specialist_consensus_score",
            "unresolved_blocker_pressure",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyPostReviewReadinessRow(_FinalDataclass):
    row_number: Decimal
    public_candidate_hash: str
    evidence_maturity_score: Decimal
    source_corroboration_score: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    unresolved_blocker_pressure: Decimal
    blocker_clearance_score: Decimal
    manual_review_urgency_score: Decimal
    post_review_readiness_score: Decimal
    readiness_status: str
    manual_decision_queue_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPostReviewReadinessRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_hash("public_candidate_hash", self.public_candidate_hash)
        for field_name in (
            "evidence_maturity_score",
            "source_corroboration_score",
            "cost_freshness_score",
            "specialist_consensus_score",
            "unresolved_blocker_pressure",
            "blocker_clearance_score",
            "manual_review_urgency_score",
            "post_review_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("readiness_status", self.readiness_status)
        _require_manual_queue_state(
            "manual_decision_queue_state",
            self.manual_decision_queue_state,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("row", self)
        _validate_row(self)
        if self.validation_digest != _validation_digest(asdict(self)):
            raise ValueError("validation_digest must match row fields")


@dataclass(frozen=True)
class ResearchStrategyPostReviewReadinessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal | None
    min_readiness_score: Decimal | None
    max_manual_review_urgency_score: Decimal | None
    handoff_status: str
    manual_decision_queue_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyPostReviewReadinessRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPostReviewReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "min_readiness_score",
            "max_manual_review_urgency_score",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _normalize_ratio(field_name, value))
        _require_status("handoff_status", self.handoff_status)
        _require_manual_queue_state(
            "manual_decision_queue_state",
            self.manual_decision_queue_state,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)
        if self.validation_digest != _validation_digest(asdict(self)):
            raise ValueError("validation_digest must match report fields")


def build_research_strategy_post_review_readiness_report(
    candidates: Iterable[ResearchStrategyPostReviewReadinessCandidate],
    *,
    config: ResearchStrategyPostReviewReadinessConfig,
    generated_at: datetime,
) -> ResearchStrategyPostReviewReadinessReport:
    if type(config) is not ResearchStrategyPostReviewReadinessConfig:
        raise ValueError("config must be a ResearchStrategyPostReviewReadinessConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    draft_rows = tuple(
        sorted(
            (_draft_row_values(candidate, config=config) for candidate in normalized_candidates),
            key=_draft_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_draft(row_number=index, draft_values=draft_values)
        for index, draft_values in enumerate(draft_rows, start=1)
    )
    handoff_status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_readiness_score": _average_readiness_score(rows),
        "min_readiness_score": None if not rows else min(
            row.post_review_readiness_score for row in rows
        ),
        "max_manual_review_urgency_score": None if not rows else max(
            row.manual_review_urgency_score for row in rows
        ),
        "handoff_status": handoff_status,
        "manual_decision_queue_state": _manual_queue_state(handoff_status),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyPostReviewReadinessReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_post_review_readiness_report_payload(
    report: ResearchStrategyPostReviewReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyPostReviewReadinessReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyPostReviewReadinessReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _require_digest("validation_digest", payload.get("validation_digest"))
    if payload["validation_digest"] != _validation_digest(payload):
        raise ValueError("validation_digest must match payload fields")
    return payload


def research_strategy_post_review_readiness_report_digest(
    report: ResearchStrategyPostReviewReadinessReport,
) -> dict[str, Any]:
    payload = research_strategy_post_review_readiness_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


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


def _draft_row_values(
    candidate: ResearchStrategyPostReviewReadinessCandidate,
    *,
    config: ResearchStrategyPostReviewReadinessConfig,
) -> dict[str, object]:
    blocker_clearance_score = _quantize(ONE - candidate.unresolved_blocker_pressure)
    reason_codes = _row_reason_codes(candidate, config=config)
    readiness_status = _row_status(reason_codes)
    return {
        "public_candidate_hash": _public_hash(candidate.reviewed_candidate_key),
        "evidence_maturity_score": candidate.evidence_maturity_score,
        "source_corroboration_score": candidate.source_corroboration_score,
        "cost_freshness_score": candidate.cost_freshness_score,
        "specialist_consensus_score": candidate.specialist_consensus_score,
        "unresolved_blocker_pressure": candidate.unresolved_blocker_pressure,
        "blocker_clearance_score": blocker_clearance_score,
        "manual_review_urgency_score": candidate.manual_review_urgency_score,
        "post_review_readiness_score": _readiness_score(
            (
                candidate.evidence_maturity_score,
                candidate.source_corroboration_score,
                candidate.cost_freshness_score,
                candidate.specialist_consensus_score,
                blocker_clearance_score,
                candidate.manual_review_urgency_score,
            ),
        ),
        "readiness_status": readiness_status,
        "manual_decision_queue_state": _manual_queue_state(readiness_status),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_draft(
    *,
    row_number: int,
    draft_values: dict[str, object],
) -> ResearchStrategyPostReviewReadinessRow:
    row_values = {"row_number": _count(row_number), **draft_values}
    return ResearchStrategyPostReviewReadinessRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    candidate: ResearchStrategyPostReviewReadinessCandidate,
    *,
    config: ResearchStrategyPostReviewReadinessConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.evidence_maturity_score,
        pass_floor=config.evidence_maturity_pass_floor,
        watch_floor=config.evidence_maturity_watch_floor,
        reason_prefix="evidence_maturity",
    )
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.source_corroboration_score,
        pass_floor=config.source_corroboration_pass_floor,
        watch_floor=config.source_corroboration_watch_floor,
        reason_prefix="source_corroboration",
    )
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.cost_freshness_score,
        pass_floor=config.cost_freshness_pass_floor,
        watch_floor=config.cost_freshness_watch_floor,
        reason_prefix="cost_freshness",
    )
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.specialist_consensus_score,
        pass_floor=config.specialist_consensus_pass_floor,
        watch_floor=config.specialist_consensus_watch_floor,
        reason_prefix="specialist_consensus",
    )
    if candidate.unresolved_blocker_pressure >= (
        config.unresolved_blocker_pressure_block_ceiling
    ):
        block_reasons.append("unresolved_blocker_pressure_block")
    elif candidate.unresolved_blocker_pressure > (
        config.unresolved_blocker_pressure_watch_ceiling
    ):
        watch_reasons.append("unresolved_blocker_pressure_watch")
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.manual_review_urgency_score,
        pass_floor=config.manual_review_urgency_pass_floor,
        watch_floor=config.manual_review_urgency_watch_floor,
        reason_prefix="manual_review_urgency",
    )
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("post_review_readiness_pass",)
    return _normalize_reason_codes(reasons)


def _append_floor_reasons(
    block_reasons: list[str],
    watch_reasons: list[str],
    *,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
    reason_prefix: str,
) -> None:
    if value < watch_floor:
        block_reasons.append(f"{reason_prefix}_block")
    elif value < pass_floor:
        watch_reasons.append(f"{reason_prefix}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyPostReviewReadinessRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.readiness_status == "block" for row in rows):
        return "block"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_queue_state(status: str) -> str:
    if status == "block":
        return "manual_decision_queue_block"
    if status == "watch":
        return "manual_decision_queue_watch"
    return "manual_decision_queue_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyPostReviewReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "post_review_readiness_pass"
    )
    return _normalize_reason_codes((*values, f"post_review_readiness_{status}"))


def _readiness_score(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(values), SIX)


def _average_readiness_score(
    rows: tuple[ResearchStrategyPostReviewReadinessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(
        _sum_decimal(tuple(row.post_review_readiness_score for row in rows)),
        _count(len(rows)),
    )


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyPostReviewReadinessCandidate],
) -> tuple[ResearchStrategyPostReviewReadinessCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not ResearchStrategyPostReviewReadinessCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyPostReviewReadinessCandidate",
            )
        _require_hard_phase_flags("candidate", candidate)
        if candidate.reviewed_candidate_key in seen:
            raise ValueError("reviewed_candidate_key values must be unique")
        seen.add(candidate.reviewed_candidate_key)
    return values


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyPostReviewReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyPostReviewReadinessRow:
            raise ValueError("rows must contain ResearchStrategyPostReviewReadinessRow")
        _require_hard_phase_flags("row", row)
    return rows


def _validate_row(row: ResearchStrategyPostReviewReadinessRow) -> None:
    expected_clearance = _quantize(ONE - row.unresolved_blocker_pressure)
    if row.blocker_clearance_score != expected_clearance:
        raise ValueError("blocker_clearance_score must match blocker pressure")
    expected_score = _readiness_score(
        (
            row.evidence_maturity_score,
            row.source_corroboration_score,
            row.cost_freshness_score,
            row.specialist_consensus_score,
            row.blocker_clearance_score,
            row.manual_review_urgency_score,
        ),
    )
    if row.post_review_readiness_score != expected_score:
        raise ValueError("post_review_readiness_score must match row inputs")
    if row.readiness_status != _row_status(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")
    if row.manual_decision_queue_state != _manual_queue_state(row.readiness_status):
        raise ValueError("manual_decision_queue_state must match readiness_status")


def _validate_report(report: ResearchStrategyPostReviewReadinessReport) -> None:
    _validate_rows_sorted(report.rows)
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average_readiness_score(report.rows):
        raise ValueError("average_readiness_score must match rows")
    expected_min = None if not report.rows else min(
        row.post_review_readiness_score for row in report.rows
    )
    if report.min_readiness_score != expected_min:
        raise ValueError("min_readiness_score must match rows")
    expected_urgency = None if not report.rows else max(
        row.manual_review_urgency_score for row in report.rows
    )
    if report.max_manual_review_urgency_score != expected_urgency:
        raise ValueError("max_manual_review_urgency_score must match rows")
    if report.handoff_status != _report_status(report.rows):
        raise ValueError("handoff_status must match rows")
    if report.manual_decision_queue_state != _manual_queue_state(report.handoff_status):
        raise ValueError("manual_decision_queue_state must match handoff_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_rows_sorted(rows: tuple[ResearchStrategyPostReviewReadinessRow, ...]) -> None:
    expected_rows = tuple(sorted(rows, key=_row_sort_key))
    expected_numbers = tuple(_count(index) for index in range(1, len(rows) + 1))
    actual_numbers = tuple(row.row_number for row in rows)
    if rows != expected_rows or actual_numbers != expected_numbers:
        raise ValueError("rows must be sorted deterministically")


def _draft_row_sort_key(draft_values: dict[str, object]) -> tuple[Decimal, Decimal, str]:
    status = draft_values["readiness_status"]
    score = draft_values["post_review_readiness_score"]
    public_hash = draft_values["public_candidate_hash"]
    if type(status) is not str or type(score) is not Decimal or type(public_hash) is not str:
        raise ValueError("draft row fields are invalid")
    return (STATUS_WEIGHT[status], score, public_hash)


def _row_sort_key(
    row: ResearchStrategyPostReviewReadinessRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.readiness_status],
        row.post_review_readiness_score,
        row.public_candidate_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyPostReviewReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_internal_reference_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip() or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip() or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    _reject_unsafe_text(field_name, value)


def _require_public_hash(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a public sha256 hash")
    _require_digest(field_name, value[len(prefix):])


def _require_status(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_manual_queue_state(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if value not in (
        "manual_decision_queue_ready",
        "manual_decision_queue_watch",
        "manual_decision_queue_block",
    ):
        raise ValueError(f"{field_name} must be a known manual queue state")


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized = tuple(_reason_code(item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    if any(item not in REASON_PRIORITY for item in normalized):
        raise ValueError("reason_codes must contain known reason codes")
    present = frozenset(normalized)
    return tuple(reason for reason in REASON_PRIORITY if reason in present)


def _reason_code(value: object) -> str:
    if type(value) is not str or not value.strip() or value.strip() != value:
        raise ValueError("reason_codes must be canonical nonblank strings")
    _reject_unsafe_text("reason_codes", value)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize(value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_count(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_at_least(field_name: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{field_name} must be at least paired floor")


def _require_at_most(field_name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{field_name} must be at most paired ceiling")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_phase_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _public_hash(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _validation_digest(values: dict[str, object]) -> str:
    payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "validation_digest"
    }
    _reject_unsafe_payload(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        return _as_utc("JSON datetime", value).isoformat()
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON serializable")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric value must use Decimal strings")
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_text("public payload", key)
            _reject_unsafe_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_text("public payload", value)
        return
    if type(value) in (int, float):
        raise ValueError("unsafe numeric public payload")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public text in {field_name}")


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_POST_REVIEW_READINESS_REPORT_CONFIG_VERSION",
    "ResearchStrategyPostReviewReadinessCandidate",
    "ResearchStrategyPostReviewReadinessConfig",
    "ResearchStrategyPostReviewReadinessReport",
    "ResearchStrategyPostReviewReadinessRow",
    "build_research_strategy_post_review_readiness_report",
    "research_strategy_post_review_readiness_report_digest",
    "research_strategy_post_review_readiness_report_payload",
)
