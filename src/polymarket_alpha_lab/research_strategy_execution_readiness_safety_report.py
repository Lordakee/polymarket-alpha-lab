"""Pure public readiness safety report for paper review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_EXECUTION_READINESS_SAFETY_REPORT_CONFIG_VERSION = (
    "research-strategy-execution-readiness-safety-report-v0"
)

READINESS_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PASS_REASON = "research_strategy_execution_readiness_safety_pass"
PUBLIC_REDACTION_GAP_REASON = (
    "research_strategy_execution_readiness_safety_public_redaction_gap"
)
PACKET_INCOMPLETE_REASON = (
    "research_strategy_execution_readiness_safety_packet_incomplete"
)
RESEARCH_STALE_REASON = "research_strategy_execution_readiness_safety_research_stale"
RESEARCH_QUALITY_WATCH_REASON = (
    "research_strategy_execution_readiness_safety_research_quality_watch"
)
RESEARCH_QUALITY_BLOCK_REASON = (
    "research_strategy_execution_readiness_safety_research_quality_block"
)
SOURCE_INDEPENDENCE_WATCH_REASON = (
    "research_strategy_execution_readiness_safety_source_independence_watch"
)
SOURCE_INDEPENDENCE_BLOCK_REASON = (
    "research_strategy_execution_readiness_safety_source_independence_block"
)
RESOLUTION_CLARITY_WATCH_REASON = (
    "research_strategy_execution_readiness_safety_resolution_clarity_watch"
)
RESOLUTION_CLARITY_BLOCK_REASON = (
    "research_strategy_execution_readiness_safety_resolution_clarity_block"
)
LIQUIDITY_REVIEW_WATCH_REASON = (
    "research_strategy_execution_readiness_safety_liquidity_review_watch"
)
LIQUIDITY_REVIEW_BLOCK_REASON = (
    "research_strategy_execution_readiness_safety_liquidity_review_block"
)
RISK_CONTROL_WATCH_REASON = (
    "research_strategy_execution_readiness_safety_risk_control_watch"
)
RISK_CONTROL_BLOCK_REASON = (
    "research_strategy_execution_readiness_safety_risk_control_block"
)
EDGE_QUALITY_WATCH_REASON = (
    "research_strategy_execution_readiness_safety_edge_quality_watch"
)
EDGE_QUALITY_BLOCK_REASON = (
    "research_strategy_execution_readiness_safety_edge_quality_block"
)

REASON_CODES = (
    PASS_REASON,
    PUBLIC_REDACTION_GAP_REASON,
    PACKET_INCOMPLETE_REASON,
    RESEARCH_STALE_REASON,
    RESEARCH_QUALITY_WATCH_REASON,
    RESEARCH_QUALITY_BLOCK_REASON,
    SOURCE_INDEPENDENCE_WATCH_REASON,
    SOURCE_INDEPENDENCE_BLOCK_REASON,
    RESOLUTION_CLARITY_WATCH_REASON,
    RESOLUTION_CLARITY_BLOCK_REASON,
    LIQUIDITY_REVIEW_WATCH_REASON,
    LIQUIDITY_REVIEW_BLOCK_REASON,
    RISK_CONTROL_WATCH_REASON,
    RISK_CONTROL_BLOCK_REASON,
    EDGE_QUALITY_WATCH_REASON,
    EDGE_QUALITY_BLOCK_REASON,
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EXECUTION_READINESS_SAFETY_REPORT_CONFIG_VERSION",
    "READINESS_STATUSES",
    "ResearchStrategyExecutionReadinessSafetyCandidate",
    "ResearchStrategyExecutionReadinessSafetyConfig",
    "ResearchStrategyExecutionReadinessSafetyReport",
    "ResearchStrategyExecutionReadinessSafetyRow",
    "build_research_strategy_execution_readiness_safety_report",
    "research_strategy_execution_readiness_safety_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyExecutionReadinessSafetyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EXECUTION_READINESS_SAFETY_REPORT_CONFIG_VERSION
    )
    min_research_quality_score: Decimal = Decimal("0.800000")
    min_source_independence_score: Decimal = Decimal("0.750000")
    min_resolution_clarity_score: Decimal = Decimal("0.800000")
    min_liquidity_review_score: Decimal = Decimal("0.700000")
    min_risk_control_score: Decimal = Decimal("0.800000")
    min_edge_quality_score: Decimal = Decimal("0.010000")
    watch_margin: Decimal = Decimal("0.050000")
    max_research_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_research_quality_score",
            "min_source_independence_score",
            "min_resolution_clarity_score",
            "min_liquidity_review_score",
            "min_risk_control_score",
            "watch_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_edge_quality_score",
            _finite_decimal("min_edge_quality_score", self.min_edge_quality_score),
        )
        object.__setattr__(
            self,
            "max_research_age_seconds",
            _positive_decimal("max_research_age_seconds", self.max_research_age_seconds),
        )
        require_paper_only_flags("research strategy execution readiness safety config", self)


@dataclass(frozen=True)
class ResearchStrategyExecutionReadinessSafetyCandidate:
    public_candidate_ref: str
    research_packet_ref: str
    evaluated_at: datetime = datetime(1970, 1, 1, tzinfo=UTC)
    research_quality_score: Decimal = Decimal("0.000000")
    source_independence_score: Decimal = Decimal("0.000000")
    resolution_clarity_score: Decimal = Decimal("0.000000")
    liquidity_review_score: Decimal = Decimal("0.000000")
    risk_control_score: Decimal = Decimal("0.000000")
    edge_quality_score: Decimal = Decimal("0.000000")
    public_evidence_redacted: bool = True
    research_packet_complete: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("public_candidate_ref", self.public_candidate_ref)
        _require_public_string("research_packet_ref", self.research_packet_ref)
        _reject_public_leakage("public_candidate_ref", self.public_candidate_ref)
        _reject_public_leakage("research_packet_ref", self.research_packet_ref)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in (
            "research_quality_score",
            "source_independence_score",
            "resolution_clarity_score",
            "liquidity_review_score",
            "risk_control_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_quality_score",
            _finite_decimal("edge_quality_score", self.edge_quality_score),
        )
        _require_bool("public_evidence_redacted", self.public_evidence_redacted)
        _require_bool("research_packet_complete", self.research_packet_complete)
        reject_unsafe_surface_fields(
            "research strategy execution readiness safety candidate",
            self,
        )
        require_paper_only_flags(
            "research strategy execution readiness safety candidate",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategyExecutionReadinessSafetyRow:
    public_candidate_ref: str
    research_packet_ref: str
    evaluated_at: datetime
    research_age_seconds: Decimal
    research_quality_score: Decimal
    source_independence_score: Decimal
    resolution_clarity_score: Decimal
    liquidity_review_score: Decimal
    risk_control_score: Decimal
    edge_quality_score: Decimal
    public_evidence_redacted: bool
    research_packet_complete: bool
    readiness_status: str
    finding_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("public_candidate_ref", self.public_candidate_ref)
        _require_public_string("research_packet_ref", self.research_packet_ref)
        _reject_public_leakage("public_candidate_ref", self.public_candidate_ref)
        _reject_public_leakage("research_packet_ref", self.research_packet_ref)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        object.__setattr__(
            self,
            "research_age_seconds",
            _nonnegative_decimal("research_age_seconds", self.research_age_seconds),
        )
        for field_name in (
            "research_quality_score",
            "source_independence_score",
            "resolution_clarity_score",
            "liquidity_review_score",
            "risk_control_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_quality_score",
            _finite_decimal("edge_quality_score", self.edge_quality_score),
        )
        _require_bool("public_evidence_redacted", self.public_evidence_redacted)
        _require_bool("research_packet_complete", self.research_packet_complete)
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "finding_count",
            _nonnegative_decimal("finding_count", self.finding_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("research strategy execution readiness safety row", self)
        require_paper_only_flags("research strategy execution readiness safety row", self)


@dataclass(frozen=True)
class ResearchStrategyExecutionReadinessSafetyReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal
    blocking_finding_count: Decimal
    watch_finding_count: Decimal
    max_research_age_seconds: Decimal
    rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "blocking_finding_count",
            "watch_finding_count",
            "max_research_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pass_ratio",
            _ratio_decimal("pass_ratio", self.pass_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.public_payload_digest:
            _require_sha256_digest("public_payload_digest", self.public_payload_digest)
        else:
            object.__setattr__(
                self,
                "public_payload_digest",
                _report_public_payload_digest(self),
            )
        _validate_report(self)
        reject_unsafe_surface_fields(
            "research strategy execution readiness safety report",
            self,
        )
        require_paper_only_flags("research strategy execution readiness safety report", self)


def build_research_strategy_execution_readiness_safety_report(
    candidates: tuple[ResearchStrategyExecutionReadinessSafetyCandidate, ...]
    | list[ResearchStrategyExecutionReadinessSafetyCandidate],
    *,
    config: ResearchStrategyExecutionReadinessSafetyConfig,
    generated_at: datetime,
) -> ResearchStrategyExecutionReadinessSafetyReport:
    if type(config) is not ResearchStrategyExecutionReadinessSafetyConfig:
        raise ValueError(
            "config must be a ResearchStrategyExecutionReadinessSafetyConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(candidate, config, generated_at_utc)
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyExecutionReadinessSafetyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        pass_ratio=_safe_ratio(_status_count(rows, "pass"), _count(len(rows))),
        blocking_finding_count=_blocking_finding_count(rows),
        watch_finding_count=_watch_finding_count(rows),
        max_research_age_seconds=_max_decimal(
            tuple(row.research_age_seconds for row in rows),
        ),
        rows=rows,
    )


def research_strategy_execution_readiness_safety_report_payload(
    report: ResearchStrategyExecutionReadinessSafetyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyExecutionReadinessSafetyReport:
        raise ValueError(
            "report must be a ResearchStrategyExecutionReadinessSafetyReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    _validate_report(report)
    payload = json_ready_no_floats(report)
    digest_value = _payload_required_string(payload, "public_payload_digest")
    _require_sha256_digest("public_payload_digest", digest_value)
    if digest_value != _public_payload_digest(payload):
        raise ValueError("public_payload_digest must match report fields")
    return payload


def _row_from_candidate(
    candidate: ResearchStrategyExecutionReadinessSafetyCandidate,
    config: ResearchStrategyExecutionReadinessSafetyConfig,
    generated_at: datetime,
) -> ResearchStrategyExecutionReadinessSafetyRow:
    age_seconds = _age_seconds(generated_at, candidate.evaluated_at)
    reason_codes = _candidate_reason_codes(candidate, config, age_seconds)
    return ResearchStrategyExecutionReadinessSafetyRow(
        public_candidate_ref=candidate.public_candidate_ref,
        research_packet_ref=candidate.research_packet_ref,
        evaluated_at=candidate.evaluated_at,
        research_age_seconds=age_seconds,
        research_quality_score=candidate.research_quality_score,
        source_independence_score=candidate.source_independence_score,
        resolution_clarity_score=candidate.resolution_clarity_score,
        liquidity_review_score=candidate.liquidity_review_score,
        risk_control_score=candidate.risk_control_score,
        edge_quality_score=candidate.edge_quality_score,
        public_evidence_redacted=candidate.public_evidence_redacted,
        research_packet_complete=candidate.research_packet_complete,
        readiness_status=_status_from_reason_codes(reason_codes),
        finding_count=ZERO if reason_codes == (PASS_REASON,) else _count(len(reason_codes)),
        reason_codes=reason_codes,
    )


def _candidate_reason_codes(
    candidate: ResearchStrategyExecutionReadinessSafetyCandidate,
    config: ResearchStrategyExecutionReadinessSafetyConfig,
    age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not candidate.public_evidence_redacted:
        reason_codes.append(PUBLIC_REDACTION_GAP_REASON)
    if not candidate.research_packet_complete:
        reason_codes.append(PACKET_INCOMPLETE_REASON)
    if age_seconds > config.max_research_age_seconds:
        reason_codes.append(RESEARCH_STALE_REASON)
    reason_codes.extend(
        _score_reason(
            candidate.research_quality_score,
            config.min_research_quality_score,
            config.watch_margin,
            RESEARCH_QUALITY_WATCH_REASON,
            RESEARCH_QUALITY_BLOCK_REASON,
        ),
    )
    reason_codes.extend(
        _score_reason(
            candidate.source_independence_score,
            config.min_source_independence_score,
            config.watch_margin,
            SOURCE_INDEPENDENCE_WATCH_REASON,
            SOURCE_INDEPENDENCE_BLOCK_REASON,
        ),
    )
    reason_codes.extend(
        _score_reason(
            candidate.resolution_clarity_score,
            config.min_resolution_clarity_score,
            config.watch_margin,
            RESOLUTION_CLARITY_WATCH_REASON,
            RESOLUTION_CLARITY_BLOCK_REASON,
        ),
    )
    reason_codes.extend(
        _score_reason(
            candidate.liquidity_review_score,
            config.min_liquidity_review_score,
            config.watch_margin,
            LIQUIDITY_REVIEW_WATCH_REASON,
            LIQUIDITY_REVIEW_BLOCK_REASON,
        ),
    )
    reason_codes.extend(
        _score_reason(
            candidate.risk_control_score,
            config.min_risk_control_score,
            config.watch_margin,
            RISK_CONTROL_WATCH_REASON,
            RISK_CONTROL_BLOCK_REASON,
        ),
    )
    reason_codes.extend(
        _score_reason(
            candidate.edge_quality_score,
            config.min_edge_quality_score,
            config.watch_margin,
            EDGE_QUALITY_WATCH_REASON,
            EDGE_QUALITY_BLOCK_REASON,
        ),
    )
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _score_reason(
    value: Decimal,
    threshold: Decimal,
    watch_margin: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value >= threshold:
        return ()
    if value >= threshold - watch_margin:
        return (watch_reason,)
    return (block_reason,)


def _normalize_candidates(
    candidates: tuple[ResearchStrategyExecutionReadinessSafetyCandidate, ...]
    | list[ResearchStrategyExecutionReadinessSafetyCandidate],
) -> tuple[ResearchStrategyExecutionReadinessSafetyCandidate, ...]:
    if type(candidates) not in (tuple, list):
        raise ValueError("candidates must be a tuple or list")
    normalized = tuple(candidates)
    seen_refs: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not ResearchStrategyExecutionReadinessSafetyCandidate:
            raise ValueError(
                "candidates must contain "
                "ResearchStrategyExecutionReadinessSafetyCandidate values",
            )
        require_paper_only_flags("candidate", candidate)
        if candidate.public_candidate_ref in seen_refs:
            raise ValueError("public_candidate_ref values must be unique")
        seen_refs.add(candidate.public_candidate_ref)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...]
    | list[ResearchStrategyExecutionReadinessSafetyRow],
) -> tuple[ResearchStrategyExecutionReadinessSafetyRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyExecutionReadinessSafetyRow:
            raise ValueError(
                "rows must contain ResearchStrategyExecutionReadinessSafetyRow values",
            )
        require_paper_only_flags("row", row)
        if row.public_candidate_ref in seen_refs:
            raise ValueError("public_candidate_ref values must be unique")
        seen_refs.add(row.public_candidate_ref)
    return normalized


def _report_status(rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...]) -> str:
    if any(row.readiness_status == "block" for row in rows):
        return "block"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if _has_block_reason(reason_codes):
        return "block"
    if reason_codes != (PASS_REASON,):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON,)
    seen: set[str] = set()
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code == PASS_REASON:
                continue
            if reason_code not in seen:
                seen.add(reason_code)
                reason_codes.append(reason_code)
    return tuple(reason_codes) or (PASS_REASON,)


def _status_count(
    rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _blocking_finding_count(
    rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            for reason_code in row.reason_codes
            if _is_block_reason(reason_code)
        ),
    )


def _watch_finding_count(
    rows: tuple[ResearchStrategyExecutionReadinessSafetyRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            for reason_code in row.reason_codes
            if _is_watch_reason(reason_code)
        ),
    )


def _has_block_reason(reason_codes: tuple[str, ...]) -> bool:
    return any(_is_block_reason(reason_code) for reason_code in reason_codes)


def _is_block_reason(reason_code: str) -> bool:
    return reason_code in {
        PUBLIC_REDACTION_GAP_REASON,
        PACKET_INCOMPLETE_REASON,
        RESEARCH_STALE_REASON,
        RESEARCH_QUALITY_BLOCK_REASON,
        SOURCE_INDEPENDENCE_BLOCK_REASON,
        RESOLUTION_CLARITY_BLOCK_REASON,
        LIQUIDITY_REVIEW_BLOCK_REASON,
        RISK_CONTROL_BLOCK_REASON,
        EDGE_QUALITY_BLOCK_REASON,
    }


def _is_watch_reason(reason_code: str) -> bool:
    return reason_code in {
        RESEARCH_QUALITY_WATCH_REASON,
        SOURCE_INDEPENDENCE_WATCH_REASON,
        RESOLUTION_CLARITY_WATCH_REASON,
        LIQUIDITY_REVIEW_WATCH_REASON,
        RISK_CONTROL_WATCH_REASON,
        EDGE_QUALITY_WATCH_REASON,
    }


def _row_sort_key(
    row: ResearchStrategyExecutionReadinessSafetyRow,
) -> tuple[Decimal, str]:
    return (STATUS_RANK[row.readiness_status], row.public_candidate_ref)


def _validate_row(row: ResearchStrategyExecutionReadinessSafetyRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.readiness_status != expected_status:
        raise ValueError("readiness_status must match reason_codes")
    expected_finding_count = (
        ZERO if row.reason_codes == (PASS_REASON,) else _count(len(row.reason_codes))
    )
    if row.finding_count != expected_finding_count:
        raise ValueError("finding_count must match reason_codes")


def _validate_report(report: ResearchStrategyExecutionReadinessSafetyReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by readiness_status and public_candidate_ref")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _safe_ratio(report.pass_count, report.candidate_count):
        raise ValueError("pass_ratio must match counts")
    if report.blocking_finding_count != _blocking_finding_count(report.rows):
        raise ValueError("blocking_finding_count must match rows")
    if report.watch_finding_count != _watch_finding_count(report.rows):
        raise ValueError("watch_finding_count must match rows")
    if report.max_research_age_seconds != _max_decimal(
        tuple(row.research_age_seconds for row in report.rows),
    ):
        raise ValueError("max_research_age_seconds must match rows")
    if report.public_payload_digest != _report_public_payload_digest(report):
        raise ValueError("public_payload_digest must match report fields")


def _normalize_reason_codes(value: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    normalized = tuple(value)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if PASS_REASON in seen and normalized != (PASS_REASON,):
        raise ValueError("pass reason must stand alone")
    return normalized


def _report_public_payload_digest(
    report: ResearchStrategyExecutionReadinessSafetyReport,
) -> str:
    return _public_payload_digest(_report_public_payload_for_digest(report))


def _report_public_payload_for_digest(
    report: ResearchStrategyExecutionReadinessSafetyReport,
) -> dict[str, Any]:
    payload = json_ready_no_floats(report)
    payload.pop("public_payload_digest", None)
    return payload


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("public_payload_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded_payload.encode("utf-8")).hexdigest()


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        raise ValueError("datetime values must not be after generated_at")
    return (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    ).quantize(QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined_values = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of: {joined_values}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _ratio_decimal(name: str, value: object) -> Decimal:
    decimal = _finite_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return decimal


def _positive_decimal(name: str, value: object) -> Decimal:
    decimal = _finite_decimal(name, value)
    if decimal <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _finite_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _finite_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_UP)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANT, rounding=ROUND_HALF_UP)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT, rounding=ROUND_HALF_UP)


def _join(*parts: str) -> str:
    return "".join(parts)


PUBLIC_LEAKAGE_FRAGMENTS = frozenset(
    (
        "raw",
        _join("candidate", "_id"),
        _join("market", "_id"),
        "slug",
        "question",
        "://",
        "www.",
        "http",
        _join("source", "_url"),
        _join("source", "_text"),
        "dsn",
        "postgres:",
        "mysql:",
        _join("table", "_name"),
        _join("tok", "en"),
        _join("wal", "let"),
        _join("au", "th"),
        _join("ord", "er"),
        _join("tra", "de"),
        _join("private", "_key"),
        "secret",
        "bearer",
    ),
)


def _reject_public_leakage(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_LEAKAGE_FRAGMENTS):
        raise ValueError(f"{name} contains public leakage")
