"""Pure report for source, mechanics, and specialist memory alignment."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_STATUSES",
    "ResearchStrategySourceMarketMemoryAlignmentConfig",
    "ResearchStrategySourceMarketMemoryAlignmentInput",
    "ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount",
    "ResearchStrategySourceMarketMemoryAlignmentReport",
    "ResearchStrategySourceMarketMemoryAlignmentRow",
    "build_research_strategy_source_market_memory_alignment_report",
    "research_strategy_source_market_memory_alignment_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "research-strategy-source-market-memory-alignment-report-v0"
)

RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_STATUSES = (
    "pass",
    "watch",
    "block",
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

EMPTY_REPORT_REASON_CODE = "empty_source_market_memory_alignment_inputs"
REPORT_PASS_REASON_CODE = "source_market_memory_alignment_pass"
REPORT_WATCH_REASON_CODE = "source_market_memory_alignment_watch"
REPORT_BLOCK_REASON_CODE = "source_market_memory_alignment_block"
ROW_PASS_REASON_CODE = "source_market_memory_gap_pass"
ROW_REASON_CODES = (
    "source_market_memory_gap_block",
    "source_market_memory_gap_watch",
    ROW_PASS_REASON_CODE,
    "alignment_component_floor_block",
    "alignment_component_floor_watch",
    "evidence_freshness_block",
    "evidence_freshness_watch",
    "specialist_memory_freshness_block",
    "specialist_memory_freshness_watch",
    "mechanics_uncertainty_block",
    "mechanics_uncertainty_watch",
    "analyst_review_pressure_block",
    "analyst_review_pressure_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REPORT_REASON_CODE,
)
ROW_REASON_SEQUENCE = (
    (
        "source_market_memory_gap_block",
        "source_market_memory_gap_watch",
        ROW_PASS_REASON_CODE,
    ),
    ("alignment_component_floor_block", "alignment_component_floor_watch"),
    ("evidence_freshness_block", "evidence_freshness_watch"),
    (
        "specialist_memory_freshness_block",
        "specialist_memory_freshness_watch",
    ),
    ("mechanics_uncertainty_block", "mechanics_uncertainty_watch"),
    ("analyst_review_pressure_block", "analyst_review_pressure_watch"),
)
UNSAFE_KEY_FRAGMENTS = (
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "dsn",
    "tab" + "le_name",
    "tok" + "en",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
)
UNSAFE_VALUE_FRAGMENTS = (
    "au" + "th",
    "acc" + "ount",
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "ques" + "tion:",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "://",
    "dsn=",
    "tok" + "en=",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
    "buy",
    "sell",
    "recom" + "mend",
    "exec" + "ut",
    "siz" + "ing",
    "sub" + "mit",
    "can" + "cel",
    "li" + "ve",
)
HEX_CHARS = frozenset("0123456789abcdef")
PUBLIC_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")


@dataclass(frozen=True)
class ResearchStrategySourceMarketMemoryAlignmentConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    watch_alignment_gap: Decimal = Decimal("0.150000")
    block_alignment_gap: Decimal = Decimal("0.300000")
    watch_component_floor_score: Decimal = Decimal("0.700000")
    block_component_floor_score: Decimal = Decimal("0.450000")
    watch_evidence_age_seconds: Decimal = Decimal("7200.000000")
    block_evidence_age_seconds: Decimal = Decimal("21600.000000")
    watch_specialist_memory_age_seconds: Decimal = Decimal("86400.000000")
    block_specialist_memory_age_seconds: Decimal = Decimal("259200.000000")
    watch_mechanics_uncertainty_score: Decimal = Decimal("0.250000")
    block_mechanics_uncertainty_score: Decimal = Decimal("0.600000")
    watch_analyst_review_pressure: Decimal = Decimal("0.400000")
    block_analyst_review_pressure: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMarketMemoryAlignmentConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_alignment_gap",
            "block_alignment_gap",
            "watch_component_floor_score",
            "block_component_floor_score",
            "watch_mechanics_uncertainty_score",
            "block_mechanics_uncertainty_score",
            "watch_analyst_review_pressure",
            "block_analyst_review_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_evidence_age_seconds",
            "block_evidence_age_seconds",
            "watch_specialist_memory_age_seconds",
            "block_specialist_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        _require_rising_threshold(
            "alignment_gap",
            self.watch_alignment_gap,
            self.block_alignment_gap,
        )
        _require_falling_threshold(
            "component_floor_score",
            self.watch_component_floor_score,
            self.block_component_floor_score,
        )
        _require_rising_threshold(
            "evidence_age_seconds",
            self.watch_evidence_age_seconds,
            self.block_evidence_age_seconds,
        )
        _require_rising_threshold(
            "specialist_memory_age_seconds",
            self.watch_specialist_memory_age_seconds,
            self.block_specialist_memory_age_seconds,
        )
        _require_rising_threshold(
            "mechanics_uncertainty_score",
            self.watch_mechanics_uncertainty_score,
            self.block_mechanics_uncertainty_score,
        )
        _require_rising_threshold(
            "analyst_review_pressure",
            self.watch_analyst_review_pressure,
            self.block_analyst_review_pressure,
        )
        require_paper_only_flags(
            "ResearchStrategySourceMarketMemoryAlignmentConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceMarketMemoryAlignmentInput:
    review_packet_label: str
    evidence_alignment_score: Decimal
    mechanics_alignment_score: Decimal
    specialist_memory_alignment_score: Decimal
    mechanics_uncertainty_score: Decimal
    evidence_observed_at: datetime
    specialist_memory_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMarketMemoryAlignmentInput)
        object.__setattr__(
            self,
            "review_packet_label",
            _require_safe_label("review_packet_label", self.review_packet_label),
        )
        for field_name in (
            "evidence_alignment_score",
            "mechanics_alignment_score",
            "specialist_memory_alignment_score",
            "mechanics_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "specialist_memory_observed_at",
            _as_utc(
                "specialist_memory_observed_at",
                self.specialist_memory_observed_at,
            ),
        )
        require_paper_only_flags(
            "ResearchStrategySourceMarketMemoryAlignmentInput",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceMarketMemoryAlignmentRow:
    rank: Decimal
    review_packet_label: str
    status: str
    evidence_alignment_score: Decimal
    mechanics_alignment_score: Decimal
    specialist_memory_alignment_score: Decimal
    mechanics_uncertainty_score: Decimal
    pairwise_alignment_gap: Decimal
    component_floor_score: Decimal
    evidence_observed_at: datetime
    evidence_age_seconds: Decimal
    evidence_freshness_score: Decimal
    specialist_memory_observed_at: datetime
    specialist_memory_age_seconds: Decimal
    specialist_memory_freshness_score: Decimal
    analyst_review_pressure: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMarketMemoryAlignmentRow)
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "review_packet_label",
            _require_safe_label("review_packet_label", self.review_packet_label),
        )
        _require_member("status", self.status, RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_STATUSES)
        for field_name in (
            "evidence_alignment_score",
            "mechanics_alignment_score",
            "specialist_memory_alignment_score",
            "mechanics_uncertainty_score",
            "pairwise_alignment_gap",
            "component_floor_score",
            "evidence_freshness_score",
            "specialist_memory_freshness_score",
            "analyst_review_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "specialist_memory_observed_at",
            _as_utc(
                "specialist_memory_observed_at",
                self.specialist_memory_observed_at,
            ),
        )
        for field_name in ("evidence_age_seconds", "specialist_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        _validate_row(self)
        require_paper_only_flags(
            "ResearchStrategySourceMarketMemoryAlignmentRow",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount)
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        require_paper_only_flags(
            "ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceMarketMemoryAlignmentReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_pairwise_alignment_gap: Decimal
    average_component_floor_score: Decimal
    average_mechanics_uncertainty_score: Decimal
    average_analyst_review_pressure: Decimal
    max_analyst_review_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount, ...]
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMarketMemoryAlignmentReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_pairwise_alignment_gap",
            "average_component_floor_score",
            "average_mechanics_uncertainty_score",
            "average_analyst_review_pressure",
            "max_analyst_review_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_STRATEGY_SOURCE_MARKET_MEMORY_ALIGNMENT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_report_reason_code_sequence(self.reason_codes)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags(
            "ResearchStrategySourceMarketMemoryAlignmentReport",
            self,
        )
        expected_digest = _report_public_payload_digest(self)
        if self.public_payload_digest:
            object.__setattr__(
                self,
                "public_payload_digest",
                _normalize_sha256("public_payload_digest", self.public_payload_digest),
            )
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report fields")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)


def build_research_strategy_source_market_memory_alignment_report(
    observations: tuple[ResearchStrategySourceMarketMemoryAlignmentInput, ...]
    | list[ResearchStrategySourceMarketMemoryAlignmentInput],
    *,
    config: ResearchStrategySourceMarketMemoryAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySourceMarketMemoryAlignmentReport:
    if type(config) is not ResearchStrategySourceMarketMemoryAlignmentConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceMarketMemoryAlignmentConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(row, config=config, generated_at=generated_at_utc) for row in inputs),
    )
    return ResearchStrategySourceMarketMemoryAlignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_pairwise_alignment_gap=_average_field(rows, "pairwise_alignment_gap"),
        average_component_floor_score=_average_field(rows, "component_floor_score"),
        average_mechanics_uncertainty_score=_average_field(
            rows,
            "mechanics_uncertainty_score",
        ),
        average_analyst_review_pressure=_average_field(
            rows,
            "analyst_review_pressure",
        ),
        max_analyst_review_pressure=_max_field(rows, "analyst_review_pressure"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_source_market_memory_alignment_report_payload(
    report: ResearchStrategySourceMarketMemoryAlignmentReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySourceMarketMemoryAlignmentReport:
        raise ValueError(
            "report must be a ResearchStrategySourceMarketMemoryAlignmentReport",
        )
    require_paper_only_flags("report", report)
    _validate_report_public_payload_digest(report)
    payload = _report_public_payload(report, include_digest=True)
    require_paper_only_flags("payload", _DictFlags(payload))
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


def _build_row(
    row: ResearchStrategySourceMarketMemoryAlignmentInput,
    *,
    config: ResearchStrategySourceMarketMemoryAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySourceMarketMemoryAlignmentRow:
    evidence_age_seconds = _age_seconds(row.evidence_observed_at, generated_at)
    memory_age_seconds = _age_seconds(
        row.specialist_memory_observed_at,
        generated_at,
        older_name="specialist_memory_observed_at",
    )
    evidence_freshness_score = _remaining_ratio(
        evidence_age_seconds,
        config.block_evidence_age_seconds,
    )
    memory_freshness_score = _remaining_ratio(
        memory_age_seconds,
        config.block_specialist_memory_age_seconds,
    )
    pairwise_alignment_gap = _pairwise_alignment_gap(row)
    component_floor_score = min(
        row.evidence_alignment_score,
        row.mechanics_alignment_score,
        row.specialist_memory_alignment_score,
    )
    analyst_review_pressure = _analyst_review_pressure(
        pairwise_alignment_gap=pairwise_alignment_gap,
        component_floor_score=component_floor_score,
        mechanics_uncertainty_score=row.mechanics_uncertainty_score,
        evidence_freshness_score=evidence_freshness_score,
        specialist_memory_freshness_score=memory_freshness_score,
    )
    reason_codes = _row_reason_codes(
        pairwise_alignment_gap=pairwise_alignment_gap,
        component_floor_score=component_floor_score,
        evidence_age_seconds=evidence_age_seconds,
        specialist_memory_age_seconds=memory_age_seconds,
        mechanics_uncertainty_score=row.mechanics_uncertainty_score,
        analyst_review_pressure=analyst_review_pressure,
        config=config,
    )
    return ResearchStrategySourceMarketMemoryAlignmentRow(
        rank=COUNT_QUANTUM,
        review_packet_label=row.review_packet_label,
        status=_status_from_reason_codes(reason_codes),
        evidence_alignment_score=row.evidence_alignment_score,
        mechanics_alignment_score=row.mechanics_alignment_score,
        specialist_memory_alignment_score=row.specialist_memory_alignment_score,
        mechanics_uncertainty_score=row.mechanics_uncertainty_score,
        pairwise_alignment_gap=pairwise_alignment_gap,
        component_floor_score=component_floor_score,
        evidence_observed_at=row.evidence_observed_at,
        evidence_age_seconds=evidence_age_seconds,
        evidence_freshness_score=evidence_freshness_score,
        specialist_memory_observed_at=row.specialist_memory_observed_at,
        specialist_memory_age_seconds=memory_age_seconds,
        specialist_memory_freshness_score=memory_freshness_score,
        analyst_review_pressure=analyst_review_pressure,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
) -> tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...]:
    return tuple(
        ResearchStrategySourceMarketMemoryAlignmentRow(
            rank=_count(index),
            review_packet_label=row.review_packet_label,
            status=row.status,
            evidence_alignment_score=row.evidence_alignment_score,
            mechanics_alignment_score=row.mechanics_alignment_score,
            specialist_memory_alignment_score=row.specialist_memory_alignment_score,
            mechanics_uncertainty_score=row.mechanics_uncertainty_score,
            pairwise_alignment_gap=row.pairwise_alignment_gap,
            component_floor_score=row.component_floor_score,
            evidence_observed_at=row.evidence_observed_at,
            evidence_age_seconds=row.evidence_age_seconds,
            evidence_freshness_score=row.evidence_freshness_score,
            specialist_memory_observed_at=row.specialist_memory_observed_at,
            specialist_memory_age_seconds=row.specialist_memory_age_seconds,
            specialist_memory_freshness_score=row.specialist_memory_freshness_score,
            analyst_review_pressure=row.analyst_review_pressure,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    pairwise_alignment_gap: Decimal,
    component_floor_score: Decimal,
    evidence_age_seconds: Decimal,
    specialist_memory_age_seconds: Decimal,
    mechanics_uncertainty_score: Decimal,
    analyst_review_pressure: Decimal,
    config: ResearchStrategySourceMarketMemoryAlignmentConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if pairwise_alignment_gap >= config.block_alignment_gap:
        reason_codes.append("source_market_memory_gap_block")
    elif pairwise_alignment_gap >= config.watch_alignment_gap:
        reason_codes.append("source_market_memory_gap_watch")
    else:
        reason_codes.append(ROW_PASS_REASON_CODE)
    if component_floor_score <= config.block_component_floor_score:
        reason_codes.append("alignment_component_floor_block")
    elif component_floor_score <= config.watch_component_floor_score:
        reason_codes.append("alignment_component_floor_watch")
    if evidence_age_seconds >= config.block_evidence_age_seconds:
        reason_codes.append("evidence_freshness_block")
    elif evidence_age_seconds >= config.watch_evidence_age_seconds:
        reason_codes.append("evidence_freshness_watch")
    if specialist_memory_age_seconds >= config.block_specialist_memory_age_seconds:
        reason_codes.append("specialist_memory_freshness_block")
    elif specialist_memory_age_seconds >= config.watch_specialist_memory_age_seconds:
        reason_codes.append("specialist_memory_freshness_watch")
    if mechanics_uncertainty_score >= config.block_mechanics_uncertainty_score:
        reason_codes.append("mechanics_uncertainty_block")
    elif mechanics_uncertainty_score >= config.watch_mechanics_uncertainty_score:
        reason_codes.append("mechanics_uncertainty_watch")
    if analyst_review_pressure >= config.block_analyst_review_pressure:
        reason_codes.append("analyst_review_pressure_block")
    elif analyst_review_pressure >= config.watch_analyst_review_pressure:
        reason_codes.append("analyst_review_pressure_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _normalize_inputs(
    value: tuple[ResearchStrategySourceMarketMemoryAlignmentInput, ...]
    | list[ResearchStrategySourceMarketMemoryAlignmentInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategySourceMarketMemoryAlignmentInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategySourceMarketMemoryAlignmentInput:
            raise ValueError(
                "observations must contain ResearchStrategySourceMarketMemoryAlignmentInput values",
            )
        require_paper_only_flags("observation", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")
        if row.specialist_memory_observed_at > generated_at:
            raise ValueError(
                "specialist_memory_observed_at must not be after generated_at",
            )
    return rows


def _normalize_rows(
    value: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
) -> tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategySourceMarketMemoryAlignmentRow:
            raise ValueError("rows must contain alignment row values")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: tuple[ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount, ...],
) -> tuple[ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    expected = tuple(sorted(rows, key=lambda row: _row_reason_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        require_paper_only_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
) -> tuple[ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategySourceMarketMemoryAlignmentReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counter
    )


def _validate_row(row: ResearchStrategySourceMarketMemoryAlignmentRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.pairwise_alignment_gap != _pairwise_alignment_gap(row):
        raise ValueError("pairwise_alignment_gap must match alignment fields")
    expected_floor = min(
        row.evidence_alignment_score,
        row.mechanics_alignment_score,
        row.specialist_memory_alignment_score,
    )
    if row.component_floor_score != expected_floor:
        raise ValueError("component_floor_score must match alignment fields")
    expected_pressure = _analyst_review_pressure(
        pairwise_alignment_gap=row.pairwise_alignment_gap,
        component_floor_score=row.component_floor_score,
        mechanics_uncertainty_score=row.mechanics_uncertainty_score,
        evidence_freshness_score=row.evidence_freshness_score,
        specialist_memory_freshness_score=row.specialist_memory_freshness_score,
    )
    if row.analyst_review_pressure != expected_pressure:
        raise ValueError("analyst_review_pressure must match row fields")


def _validate_report(report: ResearchStrategySourceMarketMemoryAlignmentReport) -> None:
    rows = report.rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    for field_name in (
        "pairwise_alignment_gap",
        "component_floor_score",
        "mechanics_uncertainty_score",
        "analyst_review_pressure",
    ):
        if getattr(report, f"average_{field_name}") != _average_field(rows, field_name):
            raise ValueError(f"average_{field_name} must match rows")
    if report.max_analyst_review_pressure != _max_field(rows, "analyst_review_pressure"):
        raise ValueError("max_analyst_review_pressure must match rows")
    if report.status != _status_rollup(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_public_payload_digest(
    report: ResearchStrategySourceMarketMemoryAlignmentReport,
) -> None:
    _normalize_sha256("public_payload_digest", report.public_payload_digest)
    if report.public_payload_digest != _report_public_payload_digest(report):
        raise ValueError("public_payload_digest must match report fields")


def _report_public_payload_digest(
    report: ResearchStrategySourceMarketMemoryAlignmentReport,
) -> str:
    ready = _report_public_payload(report, include_digest=False)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_public_payload(
    report: ResearchStrategySourceMarketMemoryAlignmentReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = asdict(report)
    payload.pop("public_payload_digest", None)
    payload["rows"] = _redacted_public_rows(payload.get("rows"))
    if include_digest:
        payload["public_payload_digest"] = report.public_payload_digest
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("digest_payload", ready)
    return ready


def _redacted_public_rows(value: object) -> list[dict[str, Any]]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    public_rows: list[dict[str, Any]] = []
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON object values")
        public_row = dict(row)
        label = public_row.pop("review_packet_label", None)
        if type(label) is not str:
            raise ValueError("review_packet_label must be a string")
        public_row["review_packet_label_digest"] = _public_label_digest(label)
        public_rows.append(public_row)
    return public_rows


def _public_label_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pairwise_alignment_gap(value: object) -> Decimal:
    evidence = getattr(value, "evidence_alignment_score")
    mechanics = getattr(value, "mechanics_alignment_score")
    memory = getattr(value, "specialist_memory_alignment_score")
    return _normalize_probability(
        "pairwise_alignment_gap",
        max(
            _abs_decimal(evidence - mechanics),
            _abs_decimal(evidence - memory),
            _abs_decimal(mechanics - memory),
        ),
    )


def _analyst_review_pressure(
    *,
    pairwise_alignment_gap: Decimal,
    component_floor_score: Decimal,
    mechanics_uncertainty_score: Decimal,
    evidence_freshness_score: Decimal,
    specialist_memory_freshness_score: Decimal,
) -> Decimal:
    return _normalize_probability(
        "analyst_review_pressure",
        max(
            pairwise_alignment_gap,
            ONE_RATIO - component_floor_score,
            mechanics_uncertainty_score,
            ONE_RATIO - evidence_freshness_score,
            ONE_RATIO - specialist_memory_freshness_score,
        ),
    )


def _status_count(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            field_name,
            sum((getattr(row, field_name) for row in rows), ZERO_RATIO)
            / Decimal(len(rows)),
        )


def _max_field(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(getattr(row, field_name) for row in rows)


def _status_rollup(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceMarketMemoryAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _status_rollup(rows)
    codes = [_report_status_reason_code(status)]
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status_reason_code(status: str) -> str:
    if status == BLOCK_STATUS:
        return REPORT_BLOCK_REASON_CODE
    if status == WATCH_STATUS:
        return REPORT_WATCH_REASON_CODE
    return REPORT_PASS_REASON_CODE


def _row_sort_key(
    row: ResearchStrategySourceMarketMemoryAlignmentRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.analyst_review_pressure,
        -row.pairwise_alignment_gap,
        row.component_floor_score,
        -row.mechanics_uncertainty_score,
        row.review_packet_label,
    )


def _row_reason_rank(reason_code: str) -> int:
    return ROW_REASON_CODES.index(reason_code)


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    expected = tuple(
        reason_code
        for group in ROW_REASON_SEQUENCE
        for reason_code in group
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    gap_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code
        in (
            "source_market_memory_gap_block",
            "source_market_memory_gap_watch",
            ROW_PASS_REASON_CODE,
        )
    )
    if len(gap_reasons) != 1:
        raise ValueError("reason_codes must include exactly one alignment reason")


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(value)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    for code in codes:
        _require_member(name, code, allowed)
    return codes


def _age_seconds(
    older_at: datetime,
    newer_at: datetime,
    *,
    older_name: str = "evidence_observed_at",
) -> Decimal:
    older = _as_utc(older_name, older_at)
    newer = _as_utc("generated_at", newer_at)
    if older > newer:
        raise ValueError(f"{older_name} must not be after generated_at")
    delta = newer - older
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _normalize_nonnegative_measure(f"{older_name}_age_seconds", seconds)


def _remaining_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO_RATIO:
        raise ValueError("ratio limit must be positive")
    if value >= limit:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("remaining_ratio", ONE_RATIO - (value / limit))


def _require_rising_threshold(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"watch_{name} must not exceed block_{name}")


def _require_falling_threshold(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value < block_value:
        raise ValueError(f"watch_{name} must not be below block_{name}")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{expected_type.__name__} subclasses are not supported")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonblank trimmed string")


def _require_safe_label(name: str, value: object) -> str:
    _require_public_string(name, value)
    if len(value) > 64:
        raise ValueError(f"{name} must be at most 64 characters")
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{name} must be lower-case")
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{name} must not expose restricted references")
    if any(character not in PUBLIC_LABEL_CHARS for character in value):
        raise ValueError(f"{name} must use public label characters")
    return value


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO or decimal > ONE_RATIO:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_measure(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal.quantize(COUNT_QUANTUM)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(name, value)
    if count <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return count


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO_RATIO else value


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 string")
    return value


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_KEY_FRAGMENTS):
                raise ValueError(f"{context} contains restricted key")
            _reject_unsafe_public_payload(f"{context}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(context, item)
    elif type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"{context} contains restricted value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")
