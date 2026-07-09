"""Pure public reducer for domain specialist vote reconciliation reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-specialist-vote-reconciliation-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_REASON = "domain_specialist_vote_reconciliation_pass"
EMPTY_REASON = "empty_input"
PRESSURE_FIELDS = (
    "disagreement_breadth",
    "memory_staleness_score",
    "evidence_gap_score",
    "cost_pressure",
)
ROW_REASON_CODES = (
    "disagreement_breadth_block",
    "calibration_memory_stale_block",
    "evidence_coverage_gap_block",
    "cost_pressure_block",
    "reconciliation_risk_score_block",
    "disagreement_breadth_watch",
    "calibration_memory_stale_watch",
    "evidence_coverage_gap_watch",
    "cost_pressure_watch",
    "reconciliation_risk_score_watch",
    PASS_REASON,
    EMPTY_REASON,
)
REASON_RANK = {reason: index for index, reason in enumerate(ROW_REASON_CODES)}
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    _join_parts("allo", "ca", "tion"),
    _join_parts("au", "th"),
    _join_parts("api", "_", "key"),
    _join_parts("bear", "er"),
    _join_parts("buy"),
    _join_parts("can", "did", "ate"),
    _join_parts("cre", "den", "tial"),
    _join_parts("data", "base"),
    _join_parts("d", "sn"),
    _join_parts("exe", "cu", "tion"),
    _join_parts("live", "_", "tra", "ding"),
    _join_parts("mar", "ket"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("or", "der"),
    _join_parts("po", "si", "tion"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("pri", "vate", "_key"),
    _join_parts("ques", "tion"),
    _join_parts("rec", "om", "men", "da", "tion"),
    _join_parts("rec", "om", "men", "ded"),
    _join_parts("sec", "ret"),
    _join_parts("sell"),
    _join_parts("siz", "ing"),
    _join_parts("sl", "ug"),
    _join_parts("sou", "rce"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("stake"),
    _join_parts("ta", "ble"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("to", "ken"),
    _join_parts("tra", "de"),
    _join_parts("u", "rl"),
    _join_parts("wa", "llet"),
)


@dataclass(frozen=True)
class ResearchStrategyDomainSpecialistVoteReconciliationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION
    )
    watch_disagreement_breadth: Decimal = Decimal("0.350000")
    block_disagreement_breadth: Decimal = Decimal("0.700000")
    watch_calibration_memory_staleness_score: Decimal = Decimal("0.200000")
    block_calibration_memory_staleness_score: Decimal = Decimal("0.400000")
    watch_evidence_coverage_gap_score: Decimal = Decimal("0.200000")
    block_evidence_coverage_gap_score: Decimal = Decimal("0.400000")
    watch_cost_pressure: Decimal = Decimal("0.350000")
    block_cost_pressure: Decimal = Decimal("0.700000")
    watch_reconciliation_risk_score: Decimal = Decimal("0.275000")
    block_reconciliation_risk_score: Decimal = Decimal("0.550000")
    disagreement_breadth_weight: Decimal = Decimal("0.250000")
    calibration_memory_staleness_weight: Decimal = Decimal("0.250000")
    evidence_coverage_gap_weight: Decimal = Decimal("0.250000")
    cost_pressure_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSpecialistVoteReconciliationConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "watch_disagreement_breadth",
            "block_disagreement_breadth",
            "watch_calibration_memory_staleness_score",
            "block_calibration_memory_staleness_score",
            "watch_evidence_coverage_gap_score",
            "block_evidence_coverage_gap_score",
            "watch_cost_pressure",
            "block_cost_pressure",
            "watch_reconciliation_risk_score",
            "block_reconciliation_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "watch_disagreement_breadth",
            self.watch_disagreement_breadth,
            "block_disagreement_breadth",
            self.block_disagreement_breadth,
        )
        _require_threshold_pair(
            "watch_calibration_memory_staleness_score",
            self.watch_calibration_memory_staleness_score,
            "block_calibration_memory_staleness_score",
            self.block_calibration_memory_staleness_score,
        )
        _require_threshold_pair(
            "watch_evidence_coverage_gap_score",
            self.watch_evidence_coverage_gap_score,
            "block_evidence_coverage_gap_score",
            self.block_evidence_coverage_gap_score,
        )
        _require_threshold_pair(
            "watch_cost_pressure",
            self.watch_cost_pressure,
            "block_cost_pressure",
            self.block_cost_pressure,
        )
        _require_threshold_pair(
            "watch_reconciliation_risk_score",
            self.watch_reconciliation_risk_score,
            "block_reconciliation_risk_score",
            self.block_reconciliation_risk_score,
        )
        for field_name in (
            "disagreement_breadth_weight",
            "calibration_memory_staleness_weight",
            "evidence_coverage_gap_weight",
            "cost_pressure_weight",
        ):
            value = _normalize_ratio(field_name, getattr(self, field_name))
            if value <= ZERO:
                raise ValueError(f"{field_name} must be positive")
            object.__setattr__(self, field_name, value)
        if _weight_total(self) <= ZERO:
            raise ValueError("weight total must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainSpecialistVoteReconciliationInput:
    vote_key: str
    disagreement_breadth: Decimal
    calibration_memory_freshness: Decimal
    evidence_coverage: Decimal
    cost_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSpecialistVoteReconciliationInput,
            "input",
        )
        _require_private_string("vote_key", self.vote_key)
        for field_name in (
            "disagreement_breadth",
            "calibration_memory_freshness",
            "evidence_coverage",
            "cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount:
    reason_code: str
    count: Decimal
    vote_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "vote_ratio",
            _normalize_ratio("vote_ratio", self.vote_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainSpecialistVoteReconciliationRow:
    vote_digest: str
    status: str
    disagreement_breadth: Decimal
    calibration_memory_freshness: Decimal
    memory_staleness_score: Decimal
    evidence_coverage: Decimal
    evidence_gap_score: Decimal
    cost_pressure: Decimal
    reconciliation_risk_score: Decimal
    dominant_pressure: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSpecialistVoteReconciliationRow,
            "row",
        )
        _require_digest_label("vote_digest", self.vote_digest)
        _require_status("status", self.status)
        for field_name in (
            "disagreement_breadth",
            "calibration_memory_freshness",
            "memory_staleness_score",
            "evidence_coverage",
            "evidence_gap_score",
            "cost_pressure",
            "reconciliation_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("dominant_pressure", self.dominant_pressure, PRESSURE_FIELDS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyDomainSpecialistVoteReconciliationReport:
    generated_at: datetime
    config_version: str
    status: str
    vote_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_reconciliation_risk_score: Decimal
    max_disagreement_breadth: Decimal
    min_calibration_memory_freshness: Decimal
    min_evidence_coverage: Decimal
    max_cost_pressure: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyDomainSpecialistVoteReconciliationRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSpecialistVoteReconciliationReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        _require_status("status", self.status)
        for field_name in ("vote_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_reconciliation_risk_score",
            "max_disagreement_breadth",
            "min_calibration_memory_freshness",
            "min_evidence_coverage",
            "max_cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_domain_specialist_vote_reconciliation_report_payload(self)


def build_research_strategy_domain_specialist_vote_reconciliation_report(
    votes: object,
    *,
    config: ResearchStrategyDomainSpecialistVoteReconciliationConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainSpecialistVoteReconciliationReport:
    _require_exact_type(
        config,
        ResearchStrategyDomainSpecialistVoteReconciliationConfig,
        "config",
    )
    _require_hard_flags("config", config)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in _normalize_inputs(votes)),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyDomainSpecialistVoteReconciliationReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        status=_report_status(rows),
        vote_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_reconciliation_risk_score=_average_or_zero(
            tuple(row.reconciliation_risk_score for row in rows),
        ),
        max_disagreement_breadth=_max_or_zero(
            tuple(row.disagreement_breadth for row in rows),
        ),
        min_calibration_memory_freshness=_min_or_zero(
            tuple(row.calibration_memory_freshness for row in rows),
        ),
        min_evidence_coverage=_min_or_zero(
            tuple(row.evidence_coverage for row in rows),
        ),
        max_cost_pressure=_max_or_zero(tuple(row.cost_pressure for row in rows)),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_strategy_domain_specialist_vote_reconciliation_report_payload(
    report: ResearchStrategyDomainSpecialistVoteReconciliationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainSpecialistVoteReconciliationReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_flag_downgrades("payload", report)
        _verify_payload_digest(report)
        _validate_payload_schema(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyDomainSpecialistVoteReconciliationReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _reject_flag_downgrades("payload", payload)
    _verify_payload_digest(payload)
    _validate_payload_schema(payload)
    return payload


def research_strategy_domain_specialist_vote_reconciliation_report_digest(
    report: ResearchStrategyDomainSpecialistVoteReconciliationReport,
) -> str:
    _require_exact_type(
        report,
        ResearchStrategyDomainSpecialistVoteReconciliationReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")
    _validate_report(report)
    return report.derived_validation_digest


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


def _row_from_input(
    item: ResearchStrategyDomainSpecialistVoteReconciliationInput,
    *,
    config: ResearchStrategyDomainSpecialistVoteReconciliationConfig,
) -> ResearchStrategyDomainSpecialistVoteReconciliationRow:
    memory_staleness_score = _subtract_from_one(item.calibration_memory_freshness)
    evidence_gap_score = _subtract_from_one(item.evidence_coverage)
    risk_score = _reconciliation_risk_score(
        disagreement_breadth=item.disagreement_breadth,
        memory_staleness_score=memory_staleness_score,
        evidence_gap_score=evidence_gap_score,
        cost_pressure=item.cost_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        disagreement_breadth=item.disagreement_breadth,
        memory_staleness_score=memory_staleness_score,
        evidence_gap_score=evidence_gap_score,
        cost_pressure=item.cost_pressure,
        risk_score=risk_score,
        config=config,
    )
    return ResearchStrategyDomainSpecialistVoteReconciliationRow(
        vote_digest=_digest_label(item.vote_key),
        status=_row_status(reason_codes),
        disagreement_breadth=item.disagreement_breadth,
        calibration_memory_freshness=item.calibration_memory_freshness,
        memory_staleness_score=memory_staleness_score,
        evidence_coverage=item.evidence_coverage,
        evidence_gap_score=evidence_gap_score,
        cost_pressure=item.cost_pressure,
        reconciliation_risk_score=risk_score,
        dominant_pressure=_dominant_pressure(
            item.disagreement_breadth,
            memory_staleness_score,
            evidence_gap_score,
            item.cost_pressure,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    disagreement_breadth: Decimal,
    memory_staleness_score: Decimal,
    evidence_gap_score: Decimal,
    cost_pressure: Decimal,
    risk_score: Decimal,
    config: ResearchStrategyDomainSpecialistVoteReconciliationConfig,
) -> tuple[str, ...]:
    reasons = []
    if disagreement_breadth >= config.block_disagreement_breadth:
        reasons.append("disagreement_breadth_block")
    elif disagreement_breadth >= config.watch_disagreement_breadth:
        reasons.append("disagreement_breadth_watch")
    if memory_staleness_score >= config.block_calibration_memory_staleness_score:
        reasons.append("calibration_memory_stale_block")
    elif memory_staleness_score >= config.watch_calibration_memory_staleness_score:
        reasons.append("calibration_memory_stale_watch")
    if evidence_gap_score >= config.block_evidence_coverage_gap_score:
        reasons.append("evidence_coverage_gap_block")
    elif evidence_gap_score >= config.watch_evidence_coverage_gap_score:
        reasons.append("evidence_coverage_gap_watch")
    if cost_pressure >= config.block_cost_pressure:
        reasons.append("cost_pressure_block")
    elif cost_pressure >= config.watch_cost_pressure:
        reasons.append("cost_pressure_watch")
    if risk_score >= config.block_reconciliation_risk_score:
        reasons.append("reconciliation_risk_score_block")
    elif risk_score >= config.watch_reconciliation_risk_score:
        reasons.append("reconciliation_risk_score_watch")
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(dict.fromkeys(reasons))


def _reconciliation_risk_score(
    *,
    disagreement_breadth: Decimal,
    memory_staleness_score: Decimal,
    evidence_gap_score: Decimal,
    cost_pressure: Decimal,
    config: ResearchStrategyDomainSpecialistVoteReconciliationConfig,
) -> Decimal:
    weighted_total = (
        disagreement_breadth * config.disagreement_breadth_weight
        + memory_staleness_score * config.calibration_memory_staleness_weight
        + evidence_gap_score * config.evidence_coverage_gap_weight
        + cost_pressure * config.cost_pressure_weight
    )
    return _ratio(weighted_total, _weight_total(config))


def _weight_total(
    config: ResearchStrategyDomainSpecialistVoteReconciliationConfig,
) -> Decimal:
    return _quantize(
        config.disagreement_breadth_weight
        + config.calibration_memory_staleness_weight
        + config.evidence_coverage_gap_weight
        + config.cost_pressure_weight,
    )


def _dominant_pressure(
    disagreement_breadth: Decimal,
    memory_staleness_score: Decimal,
    evidence_gap_score: Decimal,
    cost_pressure: Decimal,
) -> str:
    values = (
        ("disagreement_breadth", disagreement_breadth, 0),
        ("memory_staleness_score", memory_staleness_score, 1),
        ("evidence_gap_score", evidence_gap_score, 2),
        ("cost_pressure", cost_pressure, 3),
    )
    return max(values, key=lambda item: (item[1], -item[2]))[0]


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyDomainSpecialistVoteReconciliationRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainSpecialistVoteReconciliationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason for row in rows for reason in row.reason_codes if reason != PASS_REASON
    )
    if not reasons:
        return (PASS_REASON,)
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainSpecialistVoteReconciliationRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                vote_ratio=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.reason_codes:
            if reason == PASS_REASON and PASS_REASON not in report_reason_codes:
                continue
            counts[reason] = counts.get(reason, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
            vote_ratio=_ratio(_count(counts[reason]), denominator),
        )
        for reason in sorted(counts, key=_reason_key)
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainSpecialistVoteReconciliationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchStrategyDomainSpecialistVoteReconciliationRow) -> None:
    if EMPTY_REASON in row.reason_codes:
        raise ValueError("row reason_codes must not include empty_input")
    if PASS_REASON in row.reason_codes and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass reason must be the only row reason_code")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.memory_staleness_score != _subtract_from_one(
        row.calibration_memory_freshness,
    ):
        raise ValueError("memory_staleness_score must match calibration_memory_freshness")
    if row.evidence_gap_score != _subtract_from_one(row.evidence_coverage):
        raise ValueError("evidence_gap_score must match evidence_coverage")
    expected = _dominant_pressure(
        row.disagreement_breadth,
        row.memory_staleness_score,
        row.evidence_gap_score,
        row.cost_pressure,
    )
    if row.dominant_pressure != expected:
        raise ValueError("dominant_pressure must match pressure values")


def _validate_report(
    report: ResearchStrategyDomainSpecialistVoteReconciliationReport,
) -> None:
    rows = report.rows
    if report.vote_count != _count(len(rows)):
        raise ValueError("vote_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.mean_reconciliation_risk_score != _average_or_zero(
        tuple(row.reconciliation_risk_score for row in rows),
    ):
        raise ValueError("mean_reconciliation_risk_score must match rows")
    if report.max_disagreement_breadth != _max_or_zero(
        tuple(row.disagreement_breadth for row in rows),
    ):
        raise ValueError("max_disagreement_breadth must match rows")
    if report.min_calibration_memory_freshness != _min_or_zero(
        tuple(row.calibration_memory_freshness for row in rows),
    ):
        raise ValueError("min_calibration_memory_freshness must match rows")
    if report.min_evidence_coverage != _min_or_zero(
        tuple(row.evidence_coverage for row in rows),
    ):
        raise ValueError("min_evidence_coverage must match rows")
    if report.max_cost_pressure != _max_or_zero(tuple(row.cost_pressure for row in rows)):
        raise ValueError("max_cost_pressure must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    votes: object,
) -> tuple[ResearchStrategyDomainSpecialistVoteReconciliationInput, ...]:
    if isinstance(votes, (str, bytes)):
        raise ValueError("votes must be an iterable")
    try:
        items = tuple(votes)
    except TypeError as exc:
        raise ValueError("votes must be an iterable") from exc
    for item in items:
        _require_exact_type(
            item,
            ResearchStrategyDomainSpecialistVoteReconciliationInput,
            "vote input",
        )
        _require_hard_flags("vote input", item)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyDomainSpecialistVoteReconciliationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        _require_exact_type(
            item,
            ResearchStrategyDomainSpecialistVoteReconciliationRow,
            "row",
        )
        _require_hard_flags("row", item)
    return tuple(sorted(items, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        _require_exact_type(
            item,
            ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", item)
    return tuple(sorted(items, key=lambda item: _reason_key(item.reason_code)))


def _row_sort_key(
    row: ResearchStrategyDomainSpecialistVoteReconciliationRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.reconciliation_risk_score,
        row.vote_digest,
    )


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_key))


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for item in items:
        _require_reason_code(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
    return _sort_reason_codes(items)


def _require_reason_code(field_name: str, value: object) -> None:
    _require_member(field_name, value, ROW_REASON_CODES)


def _reason_key(reason: str) -> int:
    return REASON_RANK[reason]


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_STATUSES)


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members!r}")


def _require_threshold_pair(
    watch_field: str,
    watch_value: Decimal,
    block_field: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_field} must exceed {watch_field}")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty private string")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    _reject_unsafe_text(value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_flag_downgrades(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_digest_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest label")
    _require_digest(field_name, value.removeprefix("sha256:"))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize_exact(field_name, value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    normalized = _quantize_exact(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_exact(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _subtract_from_one(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _count(len(values)))


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _digest_label(value: str) -> str:
    return "sha256:" + sha256(value.encode()).hexdigest()


def _report_digest(
    report: ResearchStrategyDomainSpecialistVoteReconciliationReport,
) -> str:
    return _payload_digest(_payload_without_digest(_json_ready(report)))


def _payload_digest(payload: dict[str, Any]) -> str:
    canonical_payload = _json_ready(payload)
    if type(canonical_payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return sha256(
        dumps(
            canonical_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    sanitized.pop("derived_validation_digest", None)
    return sanitized


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    expected = _payload_digest(_payload_without_digest(payload))
    value = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", value)
    if value != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys(
        "report payload",
        payload,
        (
            "generated_at",
            "config_version",
            "status",
            "vote_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_reconciliation_risk_score",
            "max_disagreement_breadth",
            "min_calibration_memory_freshness",
            "min_evidence_coverage",
            "max_cost_pressure",
            "reason_codes",
            "rows",
            "reason_code_counts",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    rows = tuple(
        _payload_row(item)
        for item in _payload_object_list("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _payload_reason_code_count(item)
        for item in _payload_object_list(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    report = ResearchStrategyDomainSpecialistVoteReconciliationReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        status=_payload_string("status", payload["status"]),
        vote_count=_payload_decimal("vote_count", payload["vote_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        mean_reconciliation_risk_score=_payload_decimal(
            "mean_reconciliation_risk_score",
            payload["mean_reconciliation_risk_score"],
        ),
        max_disagreement_breadth=_payload_decimal(
            "max_disagreement_breadth",
            payload["max_disagreement_breadth"],
        ),
        min_calibration_memory_freshness=_payload_decimal(
            "min_calibration_memory_freshness",
            payload["min_calibration_memory_freshness"],
        ),
        min_evidence_coverage=_payload_decimal(
            "min_evidence_coverage",
            payload["min_evidence_coverage"],
        ),
        max_cost_pressure=_payload_decimal(
            "max_cost_pressure",
            payload["max_cost_pressure"],
        ),
        reason_codes=_payload_string_list("reason_codes", payload["reason_codes"]),
        rows=rows,
        reason_code_counts=reason_code_counts,
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("report payload must use canonical report payload schema")


def _payload_row(
    payload: dict[str, Any],
) -> ResearchStrategyDomainSpecialistVoteReconciliationRow:
    _require_payload_keys(
        "row payload",
        payload,
        (
            "vote_digest",
            "status",
            "disagreement_breadth",
            "calibration_memory_freshness",
            "memory_staleness_score",
            "evidence_coverage",
            "evidence_gap_score",
            "cost_pressure",
            "reconciliation_risk_score",
            "dominant_pressure",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchStrategyDomainSpecialistVoteReconciliationRow(
        vote_digest=_payload_string("vote_digest", payload["vote_digest"]),
        status=_payload_string("status", payload["status"]),
        disagreement_breadth=_payload_decimal(
            "disagreement_breadth",
            payload["disagreement_breadth"],
        ),
        calibration_memory_freshness=_payload_decimal(
            "calibration_memory_freshness",
            payload["calibration_memory_freshness"],
        ),
        memory_staleness_score=_payload_decimal(
            "memory_staleness_score",
            payload["memory_staleness_score"],
        ),
        evidence_coverage=_payload_decimal(
            "evidence_coverage",
            payload["evidence_coverage"],
        ),
        evidence_gap_score=_payload_decimal(
            "evidence_gap_score",
            payload["evidence_gap_score"],
        ),
        cost_pressure=_payload_decimal("cost_pressure", payload["cost_pressure"]),
        reconciliation_risk_score=_payload_decimal(
            "reconciliation_risk_score",
            payload["reconciliation_risk_score"],
        ),
        dominant_pressure=_payload_string(
            "dominant_pressure",
            payload["dominant_pressure"],
        ),
        reason_codes=_payload_string_list("reason_codes", payload["reason_codes"]),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _payload_reason_code_count(
    payload: dict[str, Any],
) -> ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount:
    _require_payload_keys(
        "reason_code_count payload",
        payload,
        (
            "reason_code",
            "count",
            "vote_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"]),
        vote_ratio=_payload_decimal("vote_ratio", payload["vote_ratio"]),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if any(type(key) is not str for key in payload) or set(payload) != set(expected_keys):
        raise ValueError(f"{label} must use canonical report payload schema")


def _payload_object_list(
    field_name: str,
    value: object,
) -> tuple[dict[str, Any], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    items: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must use canonical report payload schema")
        items.append(item)
    return tuple(items)


def _payload_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return value


def _payload_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        parsed = _as_utc(field_name, datetime.fromisoformat(value))
    except (ValueError, OverflowError) as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc
    if _json_ready(parsed) != value:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return parsed


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        return _require_decimal(field_name, Decimal(value))
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise ValueError("public payload keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_text(str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(value)
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    raise ValueError(f"unsafe public payload for {label}")


def _reject_unsafe_text(value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_STATUSES",
    "ResearchStrategyDomainSpecialistVoteReconciliationConfig",
    "ResearchStrategyDomainSpecialistVoteReconciliationInput",
    "ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount",
    "ResearchStrategyDomainSpecialistVoteReconciliationRow",
    "ResearchStrategyDomainSpecialistVoteReconciliationReport",
    "build_research_strategy_domain_specialist_vote_reconciliation_report",
    "research_strategy_domain_specialist_vote_reconciliation_report_payload",
    "research_strategy_domain_specialist_vote_reconciliation_report_digest",
)
