"""Pure analyst scorecard for decision readiness memory checks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-strategy-decision-readiness-memory-scorecard-report-v0"
)
RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_STATUSES = (
    "pass",
    "watch",
    "block",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("5.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_SORT = {"block": 0, "watch": 1, "pass": 2}

PUBLIC_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,95}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")

ROW_REASON_CODES = (
    "decision_readiness_memory_block",
    "decision_readiness_memory_watch",
    "decision_readiness_memory_pass",
    "calibration_freshness_block",
    "calibration_freshness_watch",
    "calibration_freshness_fresh",
    "evidence_completeness_block",
    "evidence_completeness_watch",
    "evidence_completeness_complete",
    "prior_error_absorption_block",
    "prior_error_absorption_watch",
    "prior_error_absorption_absorbed",
    "liquidity_cost_pressure_block",
    "liquidity_cost_pressure_watch",
    "liquidity_cost_pressure_low",
    "review_backlog_block",
    "review_backlog_watch",
    "review_backlog_clear",
)
REPORT_REASON_CODES = (
    "decision_readiness_memory_report_block",
    "decision_readiness_memory_report_watch",
    "decision_readiness_memory_report_pass",
    "decision_readiness_memory_no_signals",
    "decision_readiness_memory_block_present",
    "decision_readiness_memory_watch_present",
    "calibration_freshness_gap_present",
    "evidence_completeness_gap_present",
    "prior_error_absorption_gap_present",
    "liquidity_cost_pressure_gap_present",
    "review_backlog_gap_present",
    "decision_readiness_memory_report_clear",
)
REASON_CODE_SEQUENCE = REPORT_REASON_CODES + ROW_REASON_CODES

CALIBRATION_WEIGHT = Decimal("0.250000")
EVIDENCE_WEIGHT = Decimal("0.300000")
PRIOR_ERROR_WEIGHT = Decimal("0.200000")
LIQUIDITY_SUPPORT_WEIGHT = Decimal("0.150000")
BACKLOG_SUPPORT_WEIGHT = Decimal("0.100000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket"),
    _join_parts("s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("so", "urce"),
    _join_parts("u", "r", "l"),
    _join_parts("d", "s", "n"),
    _join_parts("ta", "b", "le"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("a", "u", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("li", "ve"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    _join_parts("priv", "ate"),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_STATUSES",
    "ResearchStrategyDecisionReadinessMemoryScorecardConfig",
    "ResearchStrategyDecisionReadinessMemoryScorecardInput",
    "ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount",
    "ResearchStrategyDecisionReadinessMemoryScorecardReport",
    "ResearchStrategyDecisionReadinessMemoryScorecardRow",
    "build_research_strategy_decision_readiness_memory_scorecard_report",
    "research_strategy_decision_readiness_memory_scorecard_report_digest",
    "research_strategy_decision_readiness_memory_scorecard_report_payload",
    "validate_research_strategy_decision_readiness_memory_scorecard_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessMemoryScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
    )
    pass_readiness_score: Decimal = Decimal("0.800000")
    block_readiness_score: Decimal = Decimal("0.400000")
    watch_calibration_age_hours: Decimal = Decimal("72.000000")
    block_calibration_age_hours: Decimal = Decimal("168.000000")
    pass_evidence_completeness_ratio: Decimal = Decimal("0.750000")
    watch_evidence_completeness_ratio: Decimal = Decimal("0.500000")
    pass_prior_error_absorption_ratio: Decimal = Decimal("0.750000")
    watch_prior_error_absorption_ratio: Decimal = Decimal("0.500000")
    watch_liquidity_cost_pressure_ratio: Decimal = Decimal("0.300000")
    block_liquidity_cost_pressure_ratio: Decimal = Decimal("0.700000")
    watch_review_backlog_ratio: Decimal = Decimal("0.250000")
    block_review_backlog_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessMemoryScorecardConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        for name in (
            "pass_readiness_score",
            "block_readiness_score",
            "pass_evidence_completeness_ratio",
            "watch_evidence_completeness_ratio",
            "pass_prior_error_absorption_ratio",
            "watch_prior_error_absorption_ratio",
            "watch_liquidity_cost_pressure_ratio",
            "block_liquidity_cost_pressure_ratio",
            "watch_review_backlog_ratio",
            "block_review_backlog_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        for name in ("watch_calibration_age_hours", "block_calibration_age_hours"):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        if self.pass_readiness_score <= self.block_readiness_score:
            raise ValueError("pass_readiness_score must exceed block_readiness_score")
        if self.block_calibration_age_hours <= self.watch_calibration_age_hours:
            raise ValueError(
                "block_calibration_age_hours must exceed watch_calibration_age_hours",
            )
        if (
            self.watch_evidence_completeness_ratio
            > self.pass_evidence_completeness_ratio
        ):
            raise ValueError(
                "watch_evidence_completeness_ratio must not exceed pass",
            )
        if (
            self.watch_prior_error_absorption_ratio
            > self.pass_prior_error_absorption_ratio
        ):
            raise ValueError(
                "watch_prior_error_absorption_ratio must not exceed pass",
            )
        if (
            self.block_liquidity_cost_pressure_ratio
            <= self.watch_liquidity_cost_pressure_ratio
        ):
            raise ValueError(
                "block_liquidity_cost_pressure_ratio must exceed "
                "watch_liquidity_cost_pressure_ratio",
            )
        if self.block_review_backlog_ratio <= self.watch_review_backlog_ratio:
            raise ValueError(
                "block_review_backlog_ratio must exceed watch_review_backlog_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessMemoryScorecardInput:
    memory_signal_key: str
    domain_key: str
    observed_at: datetime
    calibration_age_hours: Decimal
    evidence_completeness_ratio: Decimal
    prior_error_absorption_ratio: Decimal
    liquidity_cost_pressure_ratio: Decimal
    review_backlog_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessMemoryScorecardInput)
        object.__setattr__(
            self,
            "memory_signal_key",
            _require_nonempty_string("memory_signal_key", self.memory_signal_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_code("domain_key", self.domain_key),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "calibration_age_hours",
            _require_nonnegative_decimal(
                "calibration_age_hours",
                self.calibration_age_hours,
            ),
        )
        for name in (
            "evidence_completeness_ratio",
            "prior_error_absorption_ratio",
            "liquidity_cost_pressure_ratio",
            "review_backlog_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessMemoryScorecardRow:
    rank: Decimal
    memory_signal_digest: str
    domain_key: str
    observed_at: datetime
    calibration_age_hours: Decimal
    calibration_freshness_score: Decimal
    evidence_completeness_ratio: Decimal
    prior_error_absorption_ratio: Decimal
    liquidity_cost_pressure_ratio: Decimal
    review_backlog_ratio: Decimal
    decision_readiness_score: Decimal
    readiness_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessMemoryScorecardRow)
        object.__setattr__(self, "rank", _require_count_decimal("rank", self.rank))
        _require_digest_ref("memory_signal_digest", self.memory_signal_digest)
        object.__setattr__(
            self,
            "domain_key",
            _require_public_code("domain_key", self.domain_key),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "calibration_age_hours",
            _require_nonnegative_decimal(
                "calibration_age_hours",
                self.calibration_age_hours,
            ),
        )
        for name in (
            "calibration_freshness_score",
            "evidence_completeness_ratio",
            "prior_error_absorption_ratio",
            "liquidity_cost_pressure_ratio",
            "review_backlog_ratio",
            "decision_readiness_score",
            "readiness_pressure",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", asdict(self))


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount,
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessMemoryScorecardReport:
    generated_at: datetime
    config_version: str
    report_status: str
    signal_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_freshness_score: Decimal
    average_evidence_completeness_ratio: Decimal
    average_prior_error_absorption_ratio: Decimal
    average_liquidity_cost_pressure_ratio: Decimal
    average_review_backlog_ratio: Decimal
    average_decision_readiness_score: Decimal
    max_calibration_age_hours: Decimal
    max_liquidity_cost_pressure_ratio: Decimal
    max_review_backlog_ratio: Decimal
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount,
        ...,
    ]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessMemoryScorecardReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for name in (
            "signal_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(self, name, _require_count_decimal(name, getattr(self, name)))
        for name in (
            "average_calibration_freshness_score",
            "average_evidence_completeness_ratio",
            "average_prior_error_absorption_ratio",
            "average_liquidity_cost_pressure_ratio",
            "average_review_backlog_ratio",
            "average_decision_readiness_score",
            "max_liquidity_cost_pressure_ratio",
            "max_review_backlog_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "max_calibration_age_hours",
            _require_nonnegative_decimal(
                "max_calibration_age_hours",
                self.max_calibration_age_hours,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_digest_or_empty("public_payload_digest", self.public_payload_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", asdict(self))
        expected = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_payload_digest:
            if self.public_payload_digest != expected:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_decision_readiness_memory_scorecard_report_payload(self)


def build_research_strategy_decision_readiness_memory_scorecard_report(
    signals: Iterable[ResearchStrategyDecisionReadinessMemoryScorecardInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyDecisionReadinessMemoryScorecardConfig | None = None,
) -> ResearchStrategyDecisionReadinessMemoryScorecardReport:
    cfg = config or ResearchStrategyDecisionReadinessMemoryScorecardConfig()
    if type(cfg) is not ResearchStrategyDecisionReadinessMemoryScorecardConfig:
        raise ValueError(
            "config must be ResearchStrategyDecisionReadinessMemoryScorecardConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(signals, generated_at=generated_at)
    rows = _rank_rows(tuple(_row_from_input(item, config=cfg) for item in normalized))
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": cfg.config_version,
        "report_status": _report_status(rows),
        "signal_count": _count(len(rows)),
        "domain_count": _count(len({row.domain_key for row in rows})),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_calibration_freshness_score": _average(
            tuple(row.calibration_freshness_score for row in rows),
        ),
        "average_evidence_completeness_ratio": _average(
            tuple(row.evidence_completeness_ratio for row in rows),
        ),
        "average_prior_error_absorption_ratio": _average(
            tuple(row.prior_error_absorption_ratio for row in rows),
        ),
        "average_liquidity_cost_pressure_ratio": _average(
            tuple(row.liquidity_cost_pressure_ratio for row in rows),
        ),
        "average_review_backlog_ratio": _average(
            tuple(row.review_backlog_ratio for row in rows),
        ),
        "average_decision_readiness_score": _average(
            tuple(row.decision_readiness_score for row in rows),
        ),
        "max_calibration_age_hours": _quantize(
            max((row.calibration_age_hours for row in rows), default=ZERO),
        ),
        "max_liquidity_cost_pressure_ratio": max(
            (row.liquidity_cost_pressure_ratio for row in rows),
            default=ZERO,
        ),
        "max_review_backlog_ratio": max(
            (row.review_backlog_ratio for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDecisionReadinessMemoryScorecardReport(
        **values,
        public_payload_digest=_public_digest_from_values(values),
    )


def research_strategy_decision_readiness_memory_scorecard_report_payload(
    report: ResearchStrategyDecisionReadinessMemoryScorecardReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDecisionReadinessMemoryScorecardReport:
        _require_hard_flags("report", report)
        if (
            report.public_payload_digest
            != research_strategy_decision_readiness_memory_scorecard_report_digest(report)
        ):
            raise ValueError("public_payload_digest must match report payload")
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(dict(report))
    else:
        raise ValueError(
            "report must be ResearchStrategyDecisionReadinessMemoryScorecardReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_strategy_decision_readiness_memory_scorecard_public_payload(payload)
    return payload


def research_strategy_decision_readiness_memory_scorecard_report_digest(
    report: ResearchStrategyDecisionReadinessMemoryScorecardReport,
) -> str:
    if type(report) is not ResearchStrategyDecisionReadinessMemoryScorecardReport:
        raise ValueError(
            "report must be ResearchStrategyDecisionReadinessMemoryScorecardReport",
        )
    return _public_digest_from_values(_report_values_without_digest(report))


def validate_research_strategy_decision_readiness_memory_scorecard_public_payload(
    payload: Mapping[str, Any],
) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    concrete = dict(payload)
    _reject_unsafe_public_payload("payload", concrete)
    _reject_raw_payload_numbers(concrete)
    digest = concrete.get("public_payload_digest")
    _require_sha256_hex("public_payload_digest", digest)
    digest_values = dict(concrete)
    digest_values.pop("public_payload_digest", None)
    expected = _public_digest_from_values(digest_values)
    if digest != expected:
        raise ValueError("public_payload_digest must match report payload")
    _validate_public_payload_contract(concrete)


def _validate_public_payload_contract(payload: Mapping[str, Any]) -> None:
    _require_payload_mapping_flags("payload", payload)
    _as_utc("generated_at", _require_payload_datetime("generated_at", payload.get("generated_at")))
    _require_config_version(payload.get("config_version"))
    report_status = _require_status("report_status", payload.get("report_status"))
    for name in (
        "signal_count",
        "domain_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_payload_count_decimal(name, payload.get(name))
    for name in (
        "average_calibration_freshness_score",
        "average_evidence_completeness_ratio",
        "average_prior_error_absorption_ratio",
        "average_liquidity_cost_pressure_ratio",
        "average_review_backlog_ratio",
        "average_decision_readiness_score",
        "max_liquidity_cost_pressure_ratio",
        "max_review_backlog_ratio",
    ):
        _require_payload_ratio_decimal(name, payload.get(name))
    _require_payload_nonnegative_decimal(
        "max_calibration_age_hours",
        payload.get("max_calibration_age_hours"),
    )
    _validate_public_payload_rows(payload.get("rows"))
    reason_codes = _require_payload_reason_codes(
        "reason_codes",
        payload.get("reason_codes"),
        REPORT_REASON_CODES,
    )
    if reason_codes[0] != f"decision_readiness_memory_report_{report_status}":
        raise ValueError("reason_codes must match report_status")
    _validate_public_payload_reason_code_counts(payload.get("reason_code_counts"))


def _validate_public_payload_rows(value: Any) -> None:
    rows = _require_payload_list("rows", value)
    for index, row_value in enumerate(rows, start=1):
        if not isinstance(row_value, Mapping):
            raise ValueError("rows must contain mappings")
        row = dict(row_value)
        _require_payload_mapping_flags("row", row)
        _require_payload_count_decimal("rank", row.get("rank"))
        if row.get("rank") != f"{_count(index):.6f}":
            raise ValueError("rows must use sequential ranks")
        _require_digest_ref("memory_signal_digest", row.get("memory_signal_digest"))
        _require_public_code("domain_key", row.get("domain_key"))
        _as_utc("observed_at", _require_payload_datetime("observed_at", row.get("observed_at")))
        _require_payload_nonnegative_decimal(
            "calibration_age_hours",
            row.get("calibration_age_hours"),
        )
        for name in (
            "calibration_freshness_score",
            "evidence_completeness_ratio",
            "prior_error_absorption_ratio",
            "liquidity_cost_pressure_ratio",
            "review_backlog_ratio",
            "decision_readiness_score",
            "readiness_pressure",
        ):
            _require_payload_ratio_decimal(name, row.get(name))
        status = _require_status("status", row.get("status"))
        reason_codes = _require_payload_reason_codes(
            "reason_codes",
            row.get("reason_codes"),
            ROW_REASON_CODES,
        )
        if reason_codes[0] != f"decision_readiness_memory_{status}":
            raise ValueError("reason_codes must match status")


def _validate_public_payload_reason_code_counts(value: Any) -> None:
    counts = _require_payload_list("reason_code_counts", value)
    seen: set[str] = set()
    last_index = -1
    for item_value in counts:
        if not isinstance(item_value, Mapping):
            raise ValueError("reason_code_counts must contain mappings")
        item = dict(item_value)
        _require_payload_mapping_flags("reason_code_count", item)
        reason_code = _require_member(
            "reason_code",
            item.get("reason_code"),
            REASON_CODE_SEQUENCE,
        )
        current_index = REASON_CODE_SEQUENCE.index(reason_code)
        if current_index <= last_index or reason_code in seen:
            raise ValueError("reason_code_counts must use deterministic sequence")
        seen.add(reason_code)
        last_index = current_index
        _require_payload_count_decimal("count", item.get("count"))
        _require_payload_ratio_decimal("row_ratio", item.get("row_ratio"))


def _require_payload_reason_codes(
    name: str,
    value: Any,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    values = _require_payload_list(name, value)
    return _normalize_reason_codes(tuple(values), allowed)


def _require_payload_mapping_flags(label: str, value: Mapping[str, Any]) -> None:
    _require_mapping_flags(label, value)
    for item in value.values():
        if isinstance(item, Mapping):
            _require_payload_mapping_flags(label, item)
        elif isinstance(item, list):
            for nested in item:
                if isinstance(nested, Mapping):
                    _require_payload_mapping_flags(label, nested)


def _require_payload_list(name: str, value: Any) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return value


def _require_payload_datetime(name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    return parsed


def _require_payload_count_decimal(name: str, value: Any) -> Decimal:
    return _require_payload_decimal_string(name, value, _require_count_decimal)


def _require_payload_ratio_decimal(name: str, value: Any) -> Decimal:
    return _require_payload_decimal_string(name, value, _require_ratio_decimal)


def _require_payload_nonnegative_decimal(name: str, value: Any) -> Decimal:
    return _require_payload_decimal_string(name, value, _require_nonnegative_decimal)


def _require_payload_decimal_string(
    name: str,
    value: Any,
    validator: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = validator(name, parsed)
    if value != f"{normalized:.6f}":
        raise ValueError(f"{name} must be a canonical decimal string")
    return normalized


def _row_from_input(
    item: ResearchStrategyDecisionReadinessMemoryScorecardInput,
    *,
    config: ResearchStrategyDecisionReadinessMemoryScorecardConfig,
) -> ResearchStrategyDecisionReadinessMemoryScorecardRow:
    freshness = _calibration_freshness_score(item.calibration_age_hours, config)
    readiness = _decision_readiness_score(
        calibration_freshness_score=freshness,
        evidence_completeness_ratio=item.evidence_completeness_ratio,
        prior_error_absorption_ratio=item.prior_error_absorption_ratio,
        liquidity_cost_pressure_ratio=item.liquidity_cost_pressure_ratio,
        review_backlog_ratio=item.review_backlog_ratio,
    )
    status = _row_status(
        calibration_age_hours=item.calibration_age_hours,
        evidence_completeness_ratio=item.evidence_completeness_ratio,
        prior_error_absorption_ratio=item.prior_error_absorption_ratio,
        liquidity_cost_pressure_ratio=item.liquidity_cost_pressure_ratio,
        review_backlog_ratio=item.review_backlog_ratio,
        decision_readiness_score=readiness,
        config=config,
    )
    return ResearchStrategyDecisionReadinessMemoryScorecardRow(
        rank=ONE,
        memory_signal_digest=_memory_signal_digest(item.memory_signal_key, item.domain_key),
        domain_key=item.domain_key,
        observed_at=item.observed_at,
        calibration_age_hours=item.calibration_age_hours,
        calibration_freshness_score=freshness,
        evidence_completeness_ratio=item.evidence_completeness_ratio,
        prior_error_absorption_ratio=item.prior_error_absorption_ratio,
        liquidity_cost_pressure_ratio=item.liquidity_cost_pressure_ratio,
        review_backlog_ratio=item.review_backlog_ratio,
        decision_readiness_score=readiness,
        readiness_pressure=_clamp_unit(ONE - readiness),
        status=status,
        reason_codes=_row_reason_codes(item=item, status=status, config=config),
    )


def _calibration_freshness_score(
    calibration_age_hours: Decimal,
    config: ResearchStrategyDecisionReadinessMemoryScorecardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(ONE - (calibration_age_hours / config.block_calibration_age_hours))


def _decision_readiness_score(
    *,
    calibration_freshness_score: Decimal,
    evidence_completeness_ratio: Decimal,
    prior_error_absorption_ratio: Decimal,
    liquidity_cost_pressure_ratio: Decimal,
    review_backlog_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(
            calibration_freshness_score * CALIBRATION_WEIGHT
            + evidence_completeness_ratio * EVIDENCE_WEIGHT
            + prior_error_absorption_ratio * PRIOR_ERROR_WEIGHT
            + (ONE - liquidity_cost_pressure_ratio) * LIQUIDITY_SUPPORT_WEIGHT
            + (ONE - review_backlog_ratio) * BACKLOG_SUPPORT_WEIGHT,
        )


def _row_status(
    *,
    calibration_age_hours: Decimal,
    evidence_completeness_ratio: Decimal,
    prior_error_absorption_ratio: Decimal,
    liquidity_cost_pressure_ratio: Decimal,
    review_backlog_ratio: Decimal,
    decision_readiness_score: Decimal,
    config: ResearchStrategyDecisionReadinessMemoryScorecardConfig,
) -> str:
    if (
        decision_readiness_score < config.block_readiness_score
        or calibration_age_hours >= config.block_calibration_age_hours
        or evidence_completeness_ratio < config.watch_evidence_completeness_ratio
        or prior_error_absorption_ratio < config.watch_prior_error_absorption_ratio
        or liquidity_cost_pressure_ratio >= config.block_liquidity_cost_pressure_ratio
        or review_backlog_ratio >= config.block_review_backlog_ratio
    ):
        return "block"
    if (
        decision_readiness_score >= config.pass_readiness_score
        and calibration_age_hours < config.watch_calibration_age_hours
        and evidence_completeness_ratio >= config.pass_evidence_completeness_ratio
        and prior_error_absorption_ratio >= config.pass_prior_error_absorption_ratio
        and liquidity_cost_pressure_ratio < config.watch_liquidity_cost_pressure_ratio
        and review_backlog_ratio < config.watch_review_backlog_ratio
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    item: ResearchStrategyDecisionReadinessMemoryScorecardInput,
    status: str,
    config: ResearchStrategyDecisionReadinessMemoryScorecardConfig,
) -> tuple[str, ...]:
    codes = [f"decision_readiness_memory_{status}"]
    if item.calibration_age_hours >= config.block_calibration_age_hours:
        codes.append("calibration_freshness_block")
    elif item.calibration_age_hours >= config.watch_calibration_age_hours:
        codes.append("calibration_freshness_watch")
    else:
        codes.append("calibration_freshness_fresh")
    if item.evidence_completeness_ratio < config.watch_evidence_completeness_ratio:
        codes.append("evidence_completeness_block")
    elif item.evidence_completeness_ratio < config.pass_evidence_completeness_ratio:
        codes.append("evidence_completeness_watch")
    else:
        codes.append("evidence_completeness_complete")
    if item.prior_error_absorption_ratio < config.watch_prior_error_absorption_ratio:
        codes.append("prior_error_absorption_block")
    elif item.prior_error_absorption_ratio < config.pass_prior_error_absorption_ratio:
        codes.append("prior_error_absorption_watch")
    else:
        codes.append("prior_error_absorption_absorbed")
    if item.liquidity_cost_pressure_ratio >= config.block_liquidity_cost_pressure_ratio:
        codes.append("liquidity_cost_pressure_block")
    elif item.liquidity_cost_pressure_ratio >= config.watch_liquidity_cost_pressure_ratio:
        codes.append("liquidity_cost_pressure_watch")
    else:
        codes.append("liquidity_cost_pressure_low")
    if item.review_backlog_ratio >= config.block_review_backlog_ratio:
        codes.append("review_backlog_block")
    elif item.review_backlog_ratio >= config.watch_review_backlog_ratio:
        codes.append("review_backlog_watch")
    else:
        codes.append("review_backlog_clear")
    return _normalize_reason_codes(tuple(codes), ROW_REASON_CODES)


def _rank_rows(
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...],
) -> tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...]:
    return tuple(
        ResearchStrategyDecisionReadinessMemoryScorecardRow(
            rank=_count(index),
            memory_signal_digest=row.memory_signal_digest,
            domain_key=row.domain_key,
            observed_at=row.observed_at,
            calibration_age_hours=row.calibration_age_hours,
            calibration_freshness_score=row.calibration_freshness_score,
            evidence_completeness_ratio=row.evidence_completeness_ratio,
            prior_error_absorption_ratio=row.prior_error_absorption_ratio,
            liquidity_cost_pressure_ratio=row.liquidity_cost_pressure_ratio,
            review_backlog_ratio=row.review_backlog_ratio,
            decision_readiness_score=row.decision_readiness_score,
            readiness_pressure=row.readiness_pressure,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(
    row: ResearchStrategyDecisionReadinessMemoryScorecardRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, datetime, str, str]:
    return (
        STATUS_SORT[row.status],
        -row.readiness_pressure,
        -row.review_backlog_ratio,
        -row.liquidity_cost_pressure_ratio,
        -row.calibration_age_hours,
        -row.decision_readiness_score,
        row.observed_at,
        row.domain_key,
        row.memory_signal_digest,
    )


def _normalize_inputs(
    signals: Iterable[ResearchStrategyDecisionReadinessMemoryScorecardInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyDecisionReadinessMemoryScorecardInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyDecisionReadinessMemoryScorecardInput:
            raise ValueError(
                "signals must contain "
                "ResearchStrategyDecisionReadinessMemoryScorecardInput values",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = _memory_signal_digest(item.memory_signal_key, item.domain_key)
        if key in seen:
            raise ValueError("memory signal digests must be unique")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyDecisionReadinessMemoryScorecardRow],
) -> tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in normalized) != tuple(
        _count(index) for index in range(1, len(normalized) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyDecisionReadinessMemoryScorecardRow:
            raise ValueError(
                "rows must contain ResearchStrategyDecisionReadinessMemoryScorecardRow",
            )
        _require_hard_flags("row", row)
        if row.memory_signal_digest in seen:
            raise ValueError("memory_signal_digest values must be unique")
        seen.add(row.memory_signal_digest)
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount],
) -> tuple[ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized = tuple(counts)
    expected = tuple(
        sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(item.reason_code)
    return normalized


def _normalize_reason_codes(
    values: Sequence[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    for value in values:
        seen.add(_require_member("reason_code", value, allowed))
    if not seen:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(code for code in allowed if code in seen)
    if tuple(values) != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return expected


def _report_status(
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            "decision_readiness_memory_report_block",
            "decision_readiness_memory_no_signals",
        )
    status = _report_status(rows)
    seen: set[str] = {f"decision_readiness_memory_report_{status}"}
    if any(row.status == "block" for row in rows):
        seen.add("decision_readiness_memory_block_present")
    if any(row.status == "watch" for row in rows):
        seen.add("decision_readiness_memory_watch_present")
    if _row_reason_count(
        rows,
        ("calibration_freshness_block", "calibration_freshness_watch"),
    ):
        seen.add("calibration_freshness_gap_present")
    if _row_reason_count(
        rows,
        ("evidence_completeness_block", "evidence_completeness_watch"),
    ):
        seen.add("evidence_completeness_gap_present")
    if _row_reason_count(
        rows,
        ("prior_error_absorption_block", "prior_error_absorption_watch"),
    ):
        seen.add("prior_error_absorption_gap_present")
    if _row_reason_count(
        rows,
        ("liquidity_cost_pressure_block", "liquidity_cost_pressure_watch"),
    ):
        seen.add("liquidity_cost_pressure_gap_present")
    if _row_reason_count(rows, ("review_backlog_block", "review_backlog_watch")):
        seen.add("review_backlog_gap_present")
    if seen == {"decision_readiness_memory_report_pass"}:
        seen.add("decision_readiness_memory_report_clear")
    return _normalize_reason_codes(
        tuple(code for code in REPORT_REASON_CODES if code in seen),
        REPORT_REASON_CODES,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    if not rows:
        counter.update(reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            row_ratio=_safe_divide(_count(counter[reason_code]), row_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _row_reason_count(
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...],
    reason_codes: tuple[str, ...],
) -> int:
    return sum(
        1
        for row in rows
        if any(reason_code in row.reason_codes for reason_code in reason_codes)
    )


def _status_count(
    rows: tuple[ResearchStrategyDecisionReadinessMemoryScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _validate_row(row: ResearchStrategyDecisionReadinessMemoryScorecardRow) -> None:
    if row.rank <= ZERO:
        raise ValueError("rank must be positive")
    if row.readiness_pressure != _clamp_unit(ONE - row.decision_readiness_score):
        raise ValueError("readiness_pressure must match decision_readiness_score")
    if row.status == "pass" and row.reason_codes[0] != "decision_readiness_memory_pass":
        raise ValueError("pass rows must include pass reason")
    if row.status == "watch" and row.reason_codes[0] != "decision_readiness_memory_watch":
        raise ValueError("watch rows must include watch reason")
    if row.status == "block" and row.reason_codes[0] != "decision_readiness_memory_block":
        raise ValueError("block rows must include block reason")


def _validate_report(
    report: ResearchStrategyDecisionReadinessMemoryScorecardReport,
) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.domain_count != _count(len({row.domain_key for row in rows})):
        raise ValueError("domain_count must match rows")
    if report.signal_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match signal_count")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.average_calibration_freshness_score != _average(
        tuple(row.calibration_freshness_score for row in rows),
    ):
        raise ValueError("average_calibration_freshness_score must match rows")
    if report.average_evidence_completeness_ratio != _average(
        tuple(row.evidence_completeness_ratio for row in rows),
    ):
        raise ValueError("average_evidence_completeness_ratio must match rows")
    if report.average_prior_error_absorption_ratio != _average(
        tuple(row.prior_error_absorption_ratio for row in rows),
    ):
        raise ValueError("average_prior_error_absorption_ratio must match rows")
    if report.average_liquidity_cost_pressure_ratio != _average(
        tuple(row.liquidity_cost_pressure_ratio for row in rows),
    ):
        raise ValueError("average_liquidity_cost_pressure_ratio must match rows")
    if report.average_review_backlog_ratio != _average(
        tuple(row.review_backlog_ratio for row in rows),
    ):
        raise ValueError("average_review_backlog_ratio must match rows")
    if report.average_decision_readiness_score != _average(
        tuple(row.decision_readiness_score for row in rows),
    ):
        raise ValueError("average_decision_readiness_score must match rows")
    if report.max_calibration_age_hours != _quantize(
        max((row.calibration_age_hours for row in rows), default=ZERO),
    ):
        raise ValueError("max_calibration_age_hours must match rows")
    if report.max_liquidity_cost_pressure_ratio != max(
        (row.liquidity_cost_pressure_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_liquidity_cost_pressure_ratio must match rows")
    if report.max_review_backlog_ratio != max(
        (row.review_backlog_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_review_backlog_ratio must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _memory_signal_digest(key: str, domain_key: str) -> str:
    digest = sha256(f"{domain_key}\0{key}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _report_values_without_digest(
    report: ResearchStrategyDecisionReadinessMemoryScorecardReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("public_payload_digest", None)
    return values


def _public_digest_from_values(values: Mapping[str, Any]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public payload")


def _reject_raw_payload_numbers(value: Any) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_raw_payload_numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_payload_numbers(item)
    elif type(value) in (Decimal, float, int):
        raise ValueError("payload must use decimal strings")


def _require_mapping_flags(label: str, value: Mapping[str, Any]) -> None:
    for field_name in FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: Any, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{expected.__name__} does not support subclassing")


def _require_config_version(value: Any) -> str:
    value = _require_nonempty_string("config_version", value)
    if value != DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return value


def _as_utc(name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_code(name: str, value: Any) -> str:
    value = _require_nonempty_string(name, value)
    if PUBLIC_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a public code")
    _reject_unsafe_public_text(name, value)
    return value


def _require_nonempty_string(name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _require_status(name: str, value: Any) -> str:
    return _require_member(
        name,
        value,
        RESEARCH_STRATEGY_DECISION_READINESS_MEMORY_SCORECARD_STATUSES,
    )


def _require_member(name: str, value: Any, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")
    return value


def _require_digest_ref(name: str, value: Any) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a sha256 digest reference")
    return value


def _require_digest_or_empty(name: str, value: Any) -> str:
    if value == "":
        return value
    _require_sha256_hex(name, value)
    return value


def _require_sha256_hex(name: str, value: Any) -> str:
    if type(value) is not str or SHA256_HEX_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_ratio_decimal(name: str, value: Any) -> Decimal:
    value = _require_decimal(name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


def _require_positive_decimal(name: str, value: Any) -> Decimal:
    value = _require_decimal(name, value)
    if value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return value


def _require_nonnegative_decimal(name: str, value: Any) -> Decimal:
    value = _require_decimal(name, value)
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _require_count_decimal(name: str, value: Any) -> Decimal:
    value = _require_nonnegative_decimal(name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return value


def _require_decimal(name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    return _quantize(value)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)
