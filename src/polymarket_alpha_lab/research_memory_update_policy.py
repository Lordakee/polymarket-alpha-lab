"""Pure report-only research memory update policy."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


RESEARCH_MEMORY_UPDATE_POLICY_CONFIG_VERSION = "research-memory-update-policy-v1"

EVENT_SETTLEMENT_STATUSES = ("settled", "pending", "disputed", "void")
PUBLIC_STATUSES = ("pass", "watch", "block")
WRITE_PLAN_ACTIONS = (
    "prepare_upstream_summary",
    "hold_for_review",
    "suppress_upstream_summary",
)
ROW_REASON_CODES = (
    "event_settled",
    "event_pending",
    "event_disputed",
    "event_void",
    "evidence_quality_pass",
    "evidence_quality_watch",
    "evidence_quality_block",
    "prediction_bias_high",
    "prediction_bias_meaningful",
    "prediction_bias_low",
    "postmortem_complete",
    "postmortem_review_needed",
    "postmortem_incomplete",
    "memory_update_prepared",
    "memory_update_review_required",
    "memory_update_blocked",
)
REPORT_REASON_CODES = (
    "no_summaries_supplied",
    "upstream_updates_prepared",
    "upstream_reviews_required",
    "upstream_updates_suppressed",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANTUM = Decimal("0.000001")
BPS_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
ZERO_BPS = Decimal("0.000000")
ZERO_COUNT = Decimal("0")

UNSAFE_PUBLIC_TERMS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_ref",
    "source_url",
    "source_text",
    "question:",
    "slug",
    "http://",
    "https://",
    "www.",
    "url",
    "dsn",
    "database_url",
    "connection_string",
    "postgres://",
    "postgrest",
    "table",
    "token",
    "bearer ",
    "api_key",
    "secret",
    "password",
    "private_key",
    "service_role",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "recommendation",
    "shares",
    "stake",
)


@dataclass(frozen=True)
class ResearchMemoryUpdatePolicyConfig:
    config_version: str = RESEARCH_MEMORY_UPDATE_POLICY_CONFIG_VERSION
    min_pass_evidence_quality: Decimal = Decimal("0.750000")
    min_watch_evidence_quality: Decimal = Decimal("0.500000")
    min_update_prediction_bias_bps: Decimal = Decimal("100.000000")
    high_prediction_bias_bps: Decimal = Decimal("600.000000")
    min_pass_postmortem_completeness: Decimal = Decimal("0.800000")
    min_watch_postmortem_completeness: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_evidence_quality",
            "min_watch_evidence_quality",
            "min_pass_postmortem_completeness",
            "min_watch_postmortem_completeness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_update_prediction_bias_bps",
            "high_prediction_bias_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        if self.min_watch_evidence_quality > self.min_pass_evidence_quality:
            raise ValueError("min_watch_evidence_quality must not exceed pass threshold")
        if (
            self.min_watch_postmortem_completeness
            > self.min_pass_postmortem_completeness
        ):
            raise ValueError(
                "min_watch_postmortem_completeness must not exceed pass threshold",
            )
        if self.high_prediction_bias_bps < self.min_update_prediction_bias_bps:
            raise ValueError("high_prediction_bias_bps must cover update threshold")
        _reject_unsafe_public_payload("research memory update config", self)
        _require_hard_flags("ResearchMemoryUpdatePolicyConfig", self)


@dataclass(frozen=True)
class ResearchMemoryUpdateCandidate:
    summary_digest: str
    event_settlement_status: str
    evidence_quality: Decimal
    prediction_bias_bps: Decimal
    postmortem_completeness: Decimal
    sanitized_summary: str
    sanitized_lesson: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_string("summary_digest", self.summary_digest)
        _require_member(
            "event_settlement_status",
            self.event_settlement_status,
            EVENT_SETTLEMENT_STATUSES,
        )
        object.__setattr__(
            self,
            "evidence_quality",
            _normalize_score("evidence_quality", self.evidence_quality),
        )
        object.__setattr__(
            self,
            "prediction_bias_bps",
            _normalize_nonnegative_bps("prediction_bias_bps", self.prediction_bias_bps),
        )
        object.__setattr__(
            self,
            "postmortem_completeness",
            _normalize_score("postmortem_completeness", self.postmortem_completeness),
        )
        _require_public_string("sanitized_summary", self.sanitized_summary)
        _require_public_string("sanitized_lesson", self.sanitized_lesson)
        _reject_unsafe_public_payload("research memory update candidate", self)
        _require_hard_flags("ResearchMemoryUpdateCandidate", self)


@dataclass(frozen=True)
class ResearchMemoryUpdatePlanRow:
    summary_digest: str
    public_status: str
    write_plan_action: str
    upstream_prepare: bool
    event_settlement_status: str
    evidence_quality: Decimal
    prediction_bias_bps: Decimal
    postmortem_completeness: Decimal
    readiness_score: Decimal
    sanitized_summary: str
    sanitized_lesson: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_string("summary_digest", self.summary_digest)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        _require_member("write_plan_action", self.write_plan_action, WRITE_PLAN_ACTIONS)
        if type(self.upstream_prepare) is not bool:
            raise ValueError("upstream_prepare must be a bool")
        _require_member(
            "event_settlement_status",
            self.event_settlement_status,
            EVENT_SETTLEMENT_STATUSES,
        )
        for field_name in (
            "evidence_quality",
            "postmortem_completeness",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "prediction_bias_bps",
            _normalize_nonnegative_bps("prediction_bias_bps", self.prediction_bias_bps),
        )
        _require_public_string("sanitized_summary", self.sanitized_summary)
        _require_public_string("sanitized_lesson", self.sanitized_lesson)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("research memory update row", self)
        _require_hard_flags("ResearchMemoryUpdatePlanRow", self)
        _validate_plan_row(self)


@dataclass(frozen=True)
class ResearchMemoryUpdatePolicyReport:
    config_version: str
    report_status: str
    input_summary_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    upstream_prepare_count: Decimal
    review_count: Decimal
    suppress_count: Decimal
    average_readiness_score: Decimal
    rows: tuple[ResearchMemoryUpdatePlanRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, PUBLIC_STATUSES)
        for field_name in (
            "input_summary_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "upstream_prepare_count",
            "review_count",
            "suppress_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_readiness_score",
            _normalize_score("average_readiness_score", self.average_readiness_score),
        )
        object.__setattr__(self, "rows", _normalize_plan_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("research memory update report", self)
        _require_hard_flags("ResearchMemoryUpdatePolicyReport", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_memory_update_policy_report(
    candidates: list[ResearchMemoryUpdateCandidate]
    | tuple[ResearchMemoryUpdateCandidate, ...],
    *,
    config: ResearchMemoryUpdatePolicyConfig,
) -> ResearchMemoryUpdatePolicyReport:
    if type(config) is not ResearchMemoryUpdatePolicyConfig:
        raise ValueError("config must be a ResearchMemoryUpdatePolicyConfig")
    _require_hard_flags("ResearchMemoryUpdatePolicyConfig", config)
    input_rows = _normalize_input_candidates(candidates)
    report_rows = tuple(
        sorted(
            (_plan_row_for_candidate(row, config=config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    pass_count = _status_count(report_rows, "pass")
    watch_count = _status_count(report_rows, "watch")
    block_count = _status_count(report_rows, "block")

    return ResearchMemoryUpdatePolicyReport(
        config_version=config.config_version,
        report_status=_report_status(report_rows),
        input_summary_count=_count(len(input_rows)),
        row_count=_count(len(report_rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        upstream_prepare_count=_action_count(report_rows, "prepare_upstream_summary"),
        review_count=_action_count(report_rows, "hold_for_review"),
        suppress_count=_action_count(report_rows, "suppress_upstream_summary"),
        average_readiness_score=_average_score(
            tuple(row.readiness_score for row in report_rows),
        ),
        rows=report_rows,
        reason_codes=_report_reason_codes(report_rows, len(input_rows)),
    )


def research_memory_update_policy_payload(
    report: ResearchMemoryUpdatePolicyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMemoryUpdatePolicyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("research memory update report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("research memory update payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError("report must be a ResearchMemoryUpdatePolicyReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("research memory update payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return payload


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


def _plan_row_for_candidate(
    candidate: ResearchMemoryUpdateCandidate,
    *,
    config: ResearchMemoryUpdatePolicyConfig,
) -> ResearchMemoryUpdatePlanRow:
    readiness_score = _readiness_score(candidate, config)
    public_status = _public_status(candidate, config)
    write_plan_action = _write_plan_action(public_status)
    return ResearchMemoryUpdatePlanRow(
        summary_digest=candidate.summary_digest,
        public_status=public_status,
        write_plan_action=write_plan_action,
        upstream_prepare=write_plan_action == "prepare_upstream_summary",
        event_settlement_status=candidate.event_settlement_status,
        evidence_quality=candidate.evidence_quality,
        prediction_bias_bps=candidate.prediction_bias_bps,
        postmortem_completeness=candidate.postmortem_completeness,
        readiness_score=readiness_score,
        sanitized_summary=candidate.sanitized_summary,
        sanitized_lesson=candidate.sanitized_lesson,
        reason_codes=_row_reason_codes(candidate, public_status, config),
    )


def _public_status(
    candidate: ResearchMemoryUpdateCandidate,
    config: ResearchMemoryUpdatePolicyConfig,
) -> str:
    if candidate.event_settlement_status in ("disputed", "void"):
        return "block"
    if candidate.evidence_quality < config.min_watch_evidence_quality:
        return "block"
    if candidate.postmortem_completeness < config.min_watch_postmortem_completeness:
        return "block"
    if candidate.prediction_bias_bps < config.min_update_prediction_bias_bps:
        return "block"
    if candidate.event_settlement_status != "settled":
        return "watch"
    if candidate.evidence_quality < config.min_pass_evidence_quality:
        return "watch"
    if candidate.postmortem_completeness < config.min_pass_postmortem_completeness:
        return "watch"
    return "pass"


def _write_plan_action(public_status: str) -> str:
    if public_status == "pass":
        return "prepare_upstream_summary"
    if public_status == "watch":
        return "hold_for_review"
    return "suppress_upstream_summary"


def _readiness_score(
    candidate: ResearchMemoryUpdateCandidate,
    config: ResearchMemoryUpdatePolicyConfig,
) -> Decimal:
    event_factor = _event_factor(candidate.event_settlement_status)
    bias_factor = _prediction_bias_factor(candidate.prediction_bias_bps, config)
    with localcontext(DECIMAL_CONTEXT):
        score = (
            event_factor * Decimal("0.300000")
            + candidate.evidence_quality * Decimal("0.300000")
            + candidate.postmortem_completeness * Decimal("0.250000")
            + bias_factor * Decimal("0.150000")
        )
    return _clamped_score(score)


def _event_factor(event_settlement_status: str) -> Decimal:
    if event_settlement_status == "settled":
        return ONE_SCORE
    if event_settlement_status == "pending":
        return Decimal("0.500000")
    return ZERO_SCORE


def _prediction_bias_factor(
    prediction_bias_bps: Decimal,
    config: ResearchMemoryUpdatePolicyConfig,
) -> Decimal:
    if config.high_prediction_bias_bps == ZERO_BPS:
        return ONE_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_score(prediction_bias_bps / config.high_prediction_bias_bps)


def _row_reason_codes(
    candidate: ResearchMemoryUpdateCandidate,
    public_status: str,
    config: ResearchMemoryUpdatePolicyConfig,
) -> tuple[str, ...]:
    codes: list[str] = [f"event_{candidate.event_settlement_status}"]
    if candidate.evidence_quality >= config.min_pass_evidence_quality:
        codes.append("evidence_quality_pass")
    elif candidate.evidence_quality >= config.min_watch_evidence_quality:
        codes.append("evidence_quality_watch")
    else:
        codes.append("evidence_quality_block")

    if candidate.prediction_bias_bps >= config.high_prediction_bias_bps:
        codes.append("prediction_bias_high")
    elif candidate.prediction_bias_bps >= config.min_update_prediction_bias_bps:
        codes.append("prediction_bias_meaningful")
    else:
        codes.append("prediction_bias_low")

    if candidate.postmortem_completeness >= config.min_pass_postmortem_completeness:
        codes.append("postmortem_complete")
    elif candidate.postmortem_completeness >= config.min_watch_postmortem_completeness:
        codes.append("postmortem_review_needed")
    else:
        codes.append("postmortem_incomplete")

    if public_status == "pass":
        codes.append("memory_update_prepared")
    elif public_status == "watch":
        codes.append("memory_update_review_required")
    else:
        codes.append("memory_update_blocked")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _row_sort_key(row: ResearchMemoryUpdatePlanRow) -> tuple[int, str]:
    return (("block", "watch", "pass").index(row.public_status), row.summary_digest)


def _report_status(rows: tuple[ResearchMemoryUpdatePlanRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMemoryUpdatePlanRow, ...],
    input_count: int,
) -> tuple[str, ...]:
    if input_count == 0:
        return ("no_summaries_supplied",)
    codes: list[str] = []
    if any(row.write_plan_action == "prepare_upstream_summary" for row in rows):
        codes.append("upstream_updates_prepared")
    if any(row.write_plan_action == "hold_for_review" for row in rows):
        codes.append("upstream_reviews_required")
    if any(row.write_plan_action == "suppress_upstream_summary" for row in rows):
        codes.append("upstream_updates_suppressed")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _validate_plan_row(row: ResearchMemoryUpdatePlanRow) -> None:
    if row.reason_codes == ():
        raise ValueError("reason_codes must not be empty")
    expected_action = _write_plan_action(row.public_status)
    if row.write_plan_action != expected_action:
        raise ValueError("write_plan_action must match public_status")
    if row.upstream_prepare != (row.public_status == "pass"):
        raise ValueError("upstream_prepare must match public_status")


def _validate_report(report: ResearchMemoryUpdatePolicyReport) -> None:
    if report.input_summary_count != report.row_count:
        raise ValueError("input_summary_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
        "upstream_prepare_count": _action_count(
            report.rows,
            "prepare_upstream_summary",
        ),
        "review_count": _action_count(report.rows, "hold_for_review"),
        "suppress_count": _action_count(report.rows, "suppress_upstream_summary"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_readiness_score != _average_score(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.row_count)):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _normalize_input_candidates(
    value: object,
) -> tuple[ResearchMemoryUpdateCandidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    seen_digests: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not ResearchMemoryUpdateCandidate:
            raise ValueError("candidates must contain ResearchMemoryUpdateCandidate values")
        _require_hard_flags("ResearchMemoryUpdateCandidate", candidate)
        if candidate.summary_digest in seen_digests:
            raise ValueError("duplicate summary_digest values are not allowed")
        seen_digests.add(candidate.summary_digest)
    return candidates


def _normalize_plan_rows(value: object) -> tuple[ResearchMemoryUpdatePlanRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMemoryUpdatePlanRow:
            raise ValueError("rows must contain ResearchMemoryUpdatePlanRow values")
        _require_hard_flags("ResearchMemoryUpdatePlanRow", row)
        if row.summary_digest in seen_digests:
            raise ValueError("duplicate summary_digest values are not allowed")
        seen_digests.add(row.summary_digest)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in ROW_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_nonnegative_bps(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(BPS_QUANTUM)
    if normalized < ZERO_BPS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamped_score(value: Decimal) -> Decimal:
    normalized = _require_decimal("score", value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        return ZERO_SCORE
    if normalized > ONE_SCORE:
        return ONE_SCORE
    return normalized


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_SCORE) / _count(len(values))).quantize(SCORE_QUANTUM)


def _status_count(rows: tuple[ResearchMemoryUpdatePlanRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.public_status == status))


def _action_count(
    rows: tuple[ResearchMemoryUpdatePlanRow, ...],
    action: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.write_plan_action == action))


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        _require_public_string("JSON string", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in JSON payload: {key}")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_digest(report: ResearchMemoryUpdatePolicyReport) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


__all__ = (
    "EVENT_SETTLEMENT_STATUSES",
    "PUBLIC_STATUSES",
    "RESEARCH_MEMORY_UPDATE_POLICY_CONFIG_VERSION",
    "ResearchMemoryUpdateCandidate",
    "ResearchMemoryUpdatePlanRow",
    "ResearchMemoryUpdatePolicyConfig",
    "ResearchMemoryUpdatePolicyReport",
    "research_memory_update_policy_payload",
    "build_research_memory_update_policy_report",
)
