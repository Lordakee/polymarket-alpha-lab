"""Pure probability-path consistency screening for strategy candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_PROBABILITY_PATH_CONSISTENCY_CONFIG_VERSION = (
    "strategy-candidate-probability-path-consistency-v10"
)

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")

_PASS_REASON = "strategy_candidate_probability_path_consistency_pass"
_EMPTY_REASON = "strategy_candidate_probability_path_consistency_empty"
_MOVE_WATCH_REASON = "move_magnitude_watch"
_MOVE_BLOCK_REASON = "move_magnitude_block"
_REVERSAL_WATCH_REASON = "reversal_count_watch"
_REVERSAL_BLOCK_REASON = "reversal_count_block"
_EVIDENCE_WATCH_REASON = "evidence_freshness_watch"
_EVIDENCE_BLOCK_REASON = "evidence_freshness_block"
_LIQUIDITY_WATCH_REASON = "liquidity_support_watch"
_LIQUIDITY_BLOCK_REASON = "liquidity_support_block"
_SOURCE_WATCH_REASON = "source_alignment_watch"
_SOURCE_BLOCK_REASON = "source_alignment_block"
_PATH_SCORE_WATCH_REASON = "path_consistency_score_watch"
_PATH_SCORE_BLOCK_REASON = "path_consistency_score_block"

_REASON_PRIORITY = (
    _MOVE_BLOCK_REASON,
    _REVERSAL_BLOCK_REASON,
    _EVIDENCE_BLOCK_REASON,
    _LIQUIDITY_BLOCK_REASON,
    _SOURCE_BLOCK_REASON,
    _PATH_SCORE_BLOCK_REASON,
    _MOVE_WATCH_REASON,
    _REVERSAL_WATCH_REASON,
    _EVIDENCE_WATCH_REASON,
    _LIQUIDITY_WATCH_REASON,
    _SOURCE_WATCH_REASON,
    _PATH_SCORE_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_REASONS = frozenset(
    (
        _MOVE_BLOCK_REASON,
        _REVERSAL_BLOCK_REASON,
        _EVIDENCE_BLOCK_REASON,
        _LIQUIDITY_BLOCK_REASON,
        _SOURCE_BLOCK_REASON,
        _PATH_SCORE_BLOCK_REASON,
    ),
)
_WATCH_REASONS = frozenset(
    (
        _MOVE_WATCH_REASON,
        _REVERSAL_WATCH_REASON,
        _EVIDENCE_WATCH_REASON,
        _LIQUIDITY_WATCH_REASON,
        _SOURCE_WATCH_REASON,
        _PATH_SCORE_WATCH_REASON,
    ),
)


@dataclass(frozen=True)
class StrategyCandidateProbabilityPathConsistencyConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_PROBABILITY_PATH_CONSISTENCY_CONFIG_VERSION
    )
    watch_move_magnitude: Decimal = Decimal("0.120000")
    block_move_magnitude: Decimal = Decimal("0.250000")
    watch_reversal_count: Decimal = Decimal("2")
    block_reversal_count: Decimal = Decimal("4")
    watch_evidence_age_hours: Decimal = Decimal("24")
    block_evidence_age_hours: Decimal = Decimal("72")
    watch_liquidity_support_score: Decimal = Decimal("0.550000")
    block_liquidity_support_score: Decimal = Decimal("0.300000")
    watch_source_alignment_score: Decimal = Decimal("0.600000")
    block_source_alignment_score: Decimal = Decimal("0.350000")
    watch_path_consistency_score: Decimal = Decimal("0.650000")
    block_path_consistency_score: Decimal = Decimal("0.450000")
    move_magnitude_weight: Decimal = Decimal("0.250000")
    reversal_weight: Decimal = Decimal("0.200000")
    evidence_freshness_weight: Decimal = Decimal("0.200000")
    liquidity_support_weight: Decimal = Decimal("0.150000")
    source_alignment_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "watch_move_magnitude",
            "block_move_magnitude",
            "watch_liquidity_support_score",
            "block_liquidity_support_score",
            "watch_source_alignment_score",
            "block_source_alignment_score",
            "watch_path_consistency_score",
            "block_path_consistency_score",
            "move_magnitude_weight",
            "reversal_weight",
            "evidence_freshness_weight",
            "liquidity_support_weight",
            "source_alignment_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_reversal_count",
            "block_reversal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_evidence_age_hours",
            "block_evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "block_move_magnitude",
            self.watch_move_magnitude,
            self.block_move_magnitude,
        )
        _require_at_least(
            "block_reversal_count",
            self.watch_reversal_count,
            self.block_reversal_count,
        )
        _require_at_least(
            "block_evidence_age_hours",
            self.watch_evidence_age_hours,
            self.block_evidence_age_hours,
        )
        _require_at_most(
            "block_liquidity_support_score",
            self.watch_liquidity_support_score,
            self.block_liquidity_support_score,
        )
        _require_at_most(
            "block_source_alignment_score",
            self.watch_source_alignment_score,
            self.block_source_alignment_score,
        )
        _require_at_most(
            "block_path_consistency_score",
            self.watch_path_consistency_score,
            self.block_path_consistency_score,
        )
        _require_weight_sum(self)
        require_paper_only_flags("probability path consistency config", self)


@dataclass(frozen=True)
class StrategyCandidateProbabilityPathConsistencyRecord:
    candidate_reference: str
    market_reference: str
    observed_at: datetime
    start_probability: Decimal
    current_probability: Decimal
    largest_single_move: Decimal
    reversal_count: Decimal
    evidence_age_hours: Decimal
    liquidity_support_score: Decimal
    source_alignment_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "candidate_reference",
            _redacted_reference("candidate_ref_", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "market_reference",
            _redacted_reference("market_ref_", self.market_reference),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "start_probability",
            "current_probability",
            "largest_single_move",
            "liquidity_support_score",
            "source_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reversal_count",
            _normalize_count("reversal_count", self.reversal_count),
        )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _normalize_nonnegative_decimal(
                "evidence_age_hours",
                self.evidence_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("probability path consistency record", self)


@dataclass(frozen=True)
class StrategyCandidateProbabilityPathConsistencyRow:
    redacted_candidate_reference: str
    redacted_market_reference: str
    observed_at: datetime
    start_probability: Decimal
    current_probability: Decimal
    largest_single_move: Decimal
    move_magnitude: Decimal
    reversal_count: Decimal
    evidence_age_hours: Decimal
    liquidity_support_score: Decimal
    source_alignment_score: Decimal
    path_consistency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    result_integrity_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
            "candidate_ref_",
        )
        _require_redacted_reference(
            "redacted_market_reference",
            self.redacted_market_reference,
            "market_ref_",
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "start_probability",
            "current_probability",
            "largest_single_move",
            "move_magnitude",
            "liquidity_support_score",
            "source_alignment_score",
            "path_consistency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reversal_count",
            _normalize_count("reversal_count", self.reversal_count),
        )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _normalize_nonnegative_decimal(
                "evidence_age_hours",
                self.evidence_age_hours,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        _require_integrity_digest(
            "result_integrity_digest",
            self.result_integrity_digest,
        )
        _validate_row(self)
        require_paper_only_flags("probability path consistency row", self)


@dataclass(frozen=True)
class StrategyCandidateProbabilityPathConsistencyReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_path_consistency_score: Decimal
    max_move_magnitude: Decimal
    max_reversal_count: Decimal
    max_evidence_age_hours: Decimal
    min_liquidity_support_score: Decimal
    min_source_alignment_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateProbabilityPathConsistencyRow, ...]
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
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_reversal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_path_consistency_score",
            "max_move_magnitude",
            "min_liquidity_support_score",
            "min_source_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_hours",
            _normalize_nonnegative_decimal(
                "max_evidence_age_hours",
                self.max_evidence_age_hours,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_integrity_digest(
            "report_integrity_digest",
            self.report_integrity_digest,
        )
        _validate_report(self)
        require_paper_only_flags("probability path consistency report", self)


def build_strategy_candidate_probability_path_consistency_report(
    records: Iterable[object],
    *,
    config: StrategyCandidateProbabilityPathConsistencyConfig,
    generated_at: datetime,
) -> StrategyCandidateProbabilityPathConsistencyReport:
    if type(config) is not StrategyCandidateProbabilityPathConsistencyConfig:
        raise ValueError(
            "config must be a StrategyCandidateProbabilityPathConsistencyConfig",
        )
    require_paper_only_flags("probability path consistency config", config)
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
    candidate_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    min_path_consistency_score = _min_decimal(
        row.path_consistency_score for row in rows
    )
    max_move_magnitude = _max_decimal(row.move_magnitude for row in rows)
    max_reversal_count = _max_count(row.reversal_count for row in rows)
    max_evidence_age_hours = _max_decimal(row.evidence_age_hours for row in rows)
    min_liquidity_support_score = _min_decimal(
        row.liquidity_support_score for row in rows
    )
    min_source_alignment_score = _min_decimal(
        row.source_alignment_score for row in rows
    )
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return StrategyCandidateProbabilityPathConsistencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        min_path_consistency_score=min_path_consistency_score,
        max_move_magnitude=max_move_magnitude,
        max_reversal_count=max_reversal_count,
        max_evidence_age_hours=max_evidence_age_hours,
        min_liquidity_support_score=min_liquidity_support_score,
        min_source_alignment_score=min_source_alignment_score,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
        report_integrity_digest=_report_integrity_digest_from_parts(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            candidate_count=candidate_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            min_path_consistency_score=min_path_consistency_score,
            max_move_magnitude=max_move_magnitude,
            max_reversal_count=max_reversal_count,
            max_evidence_age_hours=max_evidence_age_hours,
            min_liquidity_support_score=min_liquidity_support_score,
            min_source_alignment_score=min_source_alignment_score,
            status=status,
            reason_codes=reason_codes,
            rows=rows,
        ),
    )


def strategy_candidate_probability_path_consistency_payload(
    report: StrategyCandidateProbabilityPathConsistencyReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateProbabilityPathConsistencyReport:
        raise ValueError(
            "report must be a StrategyCandidateProbabilityPathConsistencyReport",
        )
    require_paper_only_flags("probability path consistency report", report)
    reject_unsafe_surface_fields("probability path consistency report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    require_paper_only_flags(
        "probability path consistency payload",
        _PayloadFlags(payload),
    )
    reject_unsafe_surface_fields("probability path consistency payload", payload)
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
    record: StrategyCandidateProbabilityPathConsistencyRecord,
    *,
    config: StrategyCandidateProbabilityPathConsistencyConfig,
    generated_at: datetime,
) -> StrategyCandidateProbabilityPathConsistencyRow:
    if record.observed_at > generated_at:
        raise ValueError("observed_at must not follow generated_at")
    move_magnitude = _move_magnitude(record)
    path_consistency_score = _path_consistency_score(
        record,
        move_magnitude=move_magnitude,
        config=config,
    )
    reason_codes = list(record.reason_codes)
    reason_codes.extend(
        _scored_reason_codes(
            record,
            move_magnitude=move_magnitude,
            path_consistency_score=path_consistency_score,
            config=config,
        ),
    )
    if not any(reason_code in _WATCH_REASONS for reason_code in reason_codes) and not any(
        reason_code in _BLOCK_REASONS for reason_code in reason_codes
    ):
        reason_codes.append(_PASS_REASON)
    stable_reason_codes = _stable_reason_codes("reason_codes", tuple(reason_codes))
    status = _status_from_reason_codes(stable_reason_codes)
    return StrategyCandidateProbabilityPathConsistencyRow(
        redacted_candidate_reference=record.candidate_reference,
        redacted_market_reference=record.market_reference,
        observed_at=record.observed_at,
        start_probability=record.start_probability,
        current_probability=record.current_probability,
        largest_single_move=record.largest_single_move,
        move_magnitude=move_magnitude,
        reversal_count=record.reversal_count,
        evidence_age_hours=record.evidence_age_hours,
        liquidity_support_score=record.liquidity_support_score,
        source_alignment_score=record.source_alignment_score,
        path_consistency_score=path_consistency_score,
        status=status,
        reason_codes=stable_reason_codes,
        result_integrity_digest=_row_integrity_digest_from_parts(
            redacted_candidate_reference=record.candidate_reference,
            redacted_market_reference=record.market_reference,
            observed_at=record.observed_at,
            start_probability=record.start_probability,
            current_probability=record.current_probability,
            largest_single_move=record.largest_single_move,
            move_magnitude=move_magnitude,
            reversal_count=record.reversal_count,
            evidence_age_hours=record.evidence_age_hours,
            liquidity_support_score=record.liquidity_support_score,
            source_alignment_score=record.source_alignment_score,
            path_consistency_score=path_consistency_score,
            status=status,
            reason_codes=stable_reason_codes,
        ),
    )


def _scored_reason_codes(
    record: StrategyCandidateProbabilityPathConsistencyRecord,
    *,
    move_magnitude: Decimal,
    path_consistency_score: Decimal,
    config: StrategyCandidateProbabilityPathConsistencyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_high_reason(
        reason_codes,
        move_magnitude,
        config.watch_move_magnitude,
        config.block_move_magnitude,
        _MOVE_WATCH_REASON,
        _MOVE_BLOCK_REASON,
    )
    _append_high_reason(
        reason_codes,
        record.reversal_count,
        config.watch_reversal_count,
        config.block_reversal_count,
        _REVERSAL_WATCH_REASON,
        _REVERSAL_BLOCK_REASON,
    )
    _append_high_reason(
        reason_codes,
        record.evidence_age_hours,
        config.watch_evidence_age_hours,
        config.block_evidence_age_hours,
        _EVIDENCE_WATCH_REASON,
        _EVIDENCE_BLOCK_REASON,
    )
    _append_low_reason(
        reason_codes,
        record.liquidity_support_score,
        config.watch_liquidity_support_score,
        config.block_liquidity_support_score,
        _LIQUIDITY_WATCH_REASON,
        _LIQUIDITY_BLOCK_REASON,
    )
    _append_low_reason(
        reason_codes,
        record.source_alignment_score,
        config.watch_source_alignment_score,
        config.block_source_alignment_score,
        _SOURCE_WATCH_REASON,
        _SOURCE_BLOCK_REASON,
    )
    _append_low_reason(
        reason_codes,
        path_consistency_score,
        config.watch_path_consistency_score,
        config.block_path_consistency_score,
        _PATH_SCORE_WATCH_REASON,
        _PATH_SCORE_BLOCK_REASON,
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


def _append_low_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value <= block_value:
        reason_codes.append(block_reason)
    elif value <= watch_value:
        reason_codes.append(watch_reason)


def _normalize_records(
    records: Iterable[object],
) -> tuple[StrategyCandidateProbabilityPathConsistencyRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be iterable")
    try:
        items = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be iterable") from exc
    seen_references: set[str] = set()
    for item in items:
        if type(item) is not StrategyCandidateProbabilityPathConsistencyRecord:
            raise ValueError(
                "records must contain StrategyCandidateProbabilityPathConsistencyRecord values",
            )
        require_paper_only_flags("probability path consistency record", item)
        if item.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference in records")
        seen_references.add(item.candidate_reference)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCandidateProbabilityPathConsistencyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateProbabilityPathConsistencyRow:
            raise ValueError(
                "rows must contain StrategyCandidateProbabilityPathConsistencyRow values",
            )
        _validate_row(row)
        require_paper_only_flags("probability path consistency row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must be sorted")
    if len({row.redacted_candidate_reference for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: StrategyCandidateProbabilityPathConsistencyRow) -> None:
    if row.move_magnitude != _move_magnitude(row):
        raise ValueError("move_magnitude must match probability path")
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
    if row.result_integrity_digest != _row_integrity_digest(row):
        raise ValueError("result_integrity_digest must match row")


def _validate_report(report: StrategyCandidateProbabilityPathConsistencyReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.min_path_consistency_score != _min_decimal(
        row.path_consistency_score for row in rows
    ):
        raise ValueError("min_path_consistency_score must match rows")
    if report.max_move_magnitude != _max_decimal(row.move_magnitude for row in rows):
        raise ValueError("max_move_magnitude must match rows")
    if report.max_reversal_count != _max_count(row.reversal_count for row in rows):
        raise ValueError("max_reversal_count must match rows")
    if report.max_evidence_age_hours != _max_decimal(
        row.evidence_age_hours for row in rows
    ):
        raise ValueError("max_evidence_age_hours must match rows")
    if report.min_liquidity_support_score != _min_decimal(
        row.liquidity_support_score for row in rows
    ):
        raise ValueError("min_liquidity_support_score must match rows")
    if report.min_source_alignment_score != _min_decimal(
        row.source_alignment_score for row in rows
    ):
        raise ValueError("min_source_alignment_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_integrity_digest != _report_integrity_digest(report):
        raise ValueError("report_integrity_digest must match report")


def _row_integrity_digest(
    row: StrategyCandidateProbabilityPathConsistencyRow,
) -> str:
    return _row_integrity_digest_from_parts(
        redacted_candidate_reference=row.redacted_candidate_reference,
        redacted_market_reference=row.redacted_market_reference,
        observed_at=row.observed_at,
        start_probability=row.start_probability,
        current_probability=row.current_probability,
        largest_single_move=row.largest_single_move,
        move_magnitude=row.move_magnitude,
        reversal_count=row.reversal_count,
        evidence_age_hours=row.evidence_age_hours,
        liquidity_support_score=row.liquidity_support_score,
        source_alignment_score=row.source_alignment_score,
        path_consistency_score=row.path_consistency_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_integrity_digest_from_parts(
    *,
    redacted_candidate_reference: str,
    redacted_market_reference: str,
    observed_at: datetime,
    start_probability: Decimal,
    current_probability: Decimal,
    largest_single_move: Decimal,
    move_magnitude: Decimal,
    reversal_count: Decimal,
    evidence_age_hours: Decimal,
    liquidity_support_score: Decimal,
    source_alignment_score: Decimal,
    path_consistency_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
) -> str:
    return _integrity_digest(
        (
            ("redacted_candidate_reference", redacted_candidate_reference),
            ("redacted_market_reference", redacted_market_reference),
            ("observed_at", observed_at),
            ("start_probability", start_probability),
            ("current_probability", current_probability),
            ("largest_single_move", largest_single_move),
            ("move_magnitude", move_magnitude),
            ("reversal_count", reversal_count),
            ("evidence_age_hours", evidence_age_hours),
            ("liquidity_support_score", liquidity_support_score),
            ("source_alignment_score", source_alignment_score),
            ("path_consistency_score", path_consistency_score),
            ("status", status),
            ("reason_codes", reason_codes),
        ),
    )


def _report_integrity_digest(
    report: StrategyCandidateProbabilityPathConsistencyReport,
) -> str:
    return _report_integrity_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        min_path_consistency_score=report.min_path_consistency_score,
        max_move_magnitude=report.max_move_magnitude,
        max_reversal_count=report.max_reversal_count,
        max_evidence_age_hours=report.max_evidence_age_hours,
        min_liquidity_support_score=report.min_liquidity_support_score,
        min_source_alignment_score=report.min_source_alignment_score,
        status=report.status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_integrity_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    min_path_consistency_score: Decimal,
    max_move_magnitude: Decimal,
    max_reversal_count: Decimal,
    max_evidence_age_hours: Decimal,
    min_liquidity_support_score: Decimal,
    min_source_alignment_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[StrategyCandidateProbabilityPathConsistencyRow, ...],
) -> str:
    return _integrity_digest(
        (
            ("generated_at", generated_at),
            ("config_version", config_version),
            ("candidate_count", candidate_count),
            ("pass_count", pass_count),
            ("watch_count", watch_count),
            ("block_count", block_count),
            ("min_path_consistency_score", min_path_consistency_score),
            ("max_move_magnitude", max_move_magnitude),
            ("max_reversal_count", max_reversal_count),
            ("max_evidence_age_hours", max_evidence_age_hours),
            ("min_liquidity_support_score", min_liquidity_support_score),
            ("min_source_alignment_score", min_source_alignment_score),
            ("status", status),
            ("reason_codes", reason_codes),
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


def _move_magnitude(value: object) -> Decimal:
    return max(
        abs(getattr(value, "current_probability") - getattr(value, "start_probability")),
        getattr(value, "largest_single_move"),
    )


def _path_consistency_score(
    record: StrategyCandidateProbabilityPathConsistencyRecord,
    *,
    move_magnitude: Decimal,
    config: StrategyCandidateProbabilityPathConsistencyConfig,
) -> Decimal:
    move_penalty = config.move_magnitude_weight * _capped_ratio(
        move_magnitude,
        config.block_move_magnitude,
    )
    reversal_penalty = config.reversal_weight * _capped_ratio(
        record.reversal_count,
        config.block_reversal_count,
    )
    evidence_penalty = config.evidence_freshness_weight * _capped_ratio(
        record.evidence_age_hours,
        config.block_evidence_age_hours,
    )
    liquidity_penalty = config.liquidity_support_weight * (
        _ONE - record.liquidity_support_score
    )
    source_penalty = config.source_alignment_weight * (
        _ONE - record.source_alignment_score
    )
    score = _ONE - (
        move_penalty
        + reversal_penalty
        + evidence_penalty
        + liquidity_penalty
        + source_penalty
    )
    if score < _ZERO:
        return _ZERO
    return _quantize(score)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        if numerator == _ZERO:
            return _ZERO
        return _ONE
    ratio = numerator / denominator
    if ratio > _ONE:
        return _ONE
    if ratio < _ZERO:
        return _ZERO
    return ratio


def _report_status(
    rows: tuple[StrategyCandidateProbabilityPathConsistencyRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateProbabilityPathConsistencyRow, ...],
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


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_key(
    row: StrategyCandidateProbabilityPathConsistencyRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, datetime, str, str]:
    return (
        _STATUS_WEIGHT[row.status],
        row.path_consistency_score,
        -row.move_magnitude,
        -row.reversal_count,
        -row.evidence_age_hours,
        row.observed_at,
        row.redacted_candidate_reference,
        row.redacted_market_reference,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
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
        _require_text(field_name, item)
    return tuple(sorted(set(value)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return min(items)


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


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _require_at_most(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"{field_name} must be at most watch threshold")


def _require_weight_sum(
    config: StrategyCandidateProbabilityPathConsistencyConfig,
) -> None:
    weight_sum = (
        config.move_magnitude_weight
        + config.reversal_weight
        + config.evidence_freshness_weight
        + config.liquidity_support_weight
        + config.source_alignment_weight
    )
    if _quantize(weight_sum) != _ONE:
        raise ValueError("weight values must sum to one")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be block, watch, or pass")


def _require_integrity_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _redacted_reference(prefix: str, value: str) -> str:
    digest = sha256(f"{prefix}\0{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _require_redacted_reference(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be redacted")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    suffix = value[len(prefix) :]
    if len(suffix) != 16 or any(char not in _HEX_CHARS for char in suffix):
        raise ValueError(f"{field_name} must be redacted")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_PROBABILITY_PATH_CONSISTENCY_CONFIG_VERSION",
    "StrategyCandidateProbabilityPathConsistencyConfig",
    "StrategyCandidateProbabilityPathConsistencyRecord",
    "StrategyCandidateProbabilityPathConsistencyReport",
    "StrategyCandidateProbabilityPathConsistencyRow",
    "build_strategy_candidate_probability_path_consistency_report",
    "strategy_candidate_probability_path_consistency_payload",
)
