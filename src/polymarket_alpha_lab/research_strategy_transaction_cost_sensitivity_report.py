"""Pure transaction-cost sensitivity readiness report for strategy review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_REPORT_CONFIG_VERSION = (
    "research-strategy-transaction-cost-sensitivity-report-v0"
)
RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_STATUSES = (
    "pass",
    "watch",
    "block",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "credential",
    "private",
    "secret",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "data" + "base",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmend",
    "siz" + "ing",
    "candi" + "date",
    "mar" + "ket",
    "slug",
    "ques" + "tion",
    "u" + "rl",
    "sou" + "rce",
    "d" + "sn",
    "tab" + "le",
)

ROW_REASON_CODES = (
    "cost_input_age_block",
    "cost_input_age_watch",
    "cost_input_completeness_block",
    "cost_input_completeness_watch",
    "cost_profile_coverage_block",
    "cost_profile_coverage_watch",
    "transaction_cost_sensitivity_ready",
)
REPORT_REASON_CODES = (
    "cost_input_age_review",
    "cost_input_completeness_review",
    "cost_profile_coverage_review",
    "transaction_cost_sensitivity_report_block",
    "transaction_cost_sensitivity_report_empty",
    "transaction_cost_sensitivity_report_pass",
    "transaction_cost_sensitivity_report_watch",
)


@dataclass(frozen=True)
class ResearchStrategyTransactionCostSensitivityConfig:
    config_version: str
    required_cost_profile_count: Decimal
    profile_coverage_pass_floor: Decimal
    profile_coverage_watch_floor: Decimal
    max_pass_input_age_seconds: Decimal
    max_watch_input_age_seconds: Decimal
    completeness_pass_floor: Decimal
    completeness_watch_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_cost_profile_count",
            _normalize_positive_decimal(
                "required_cost_profile_count",
                self.required_cost_profile_count,
            ),
        )
        for field_name in (
            "profile_coverage_pass_floor",
            "profile_coverage_watch_floor",
            "completeness_pass_floor",
            "completeness_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_input_age_seconds",
            "max_watch_input_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "profile_coverage",
            self.profile_coverage_pass_floor,
            self.profile_coverage_watch_floor,
        )
        _require_floor_pair(
            "completeness",
            self.completeness_pass_floor,
            self.completeness_watch_floor,
        )
        _require_ceiling_pair(
            "max_input_age_seconds",
            self.max_pass_input_age_seconds,
            self.max_watch_input_age_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyTransactionCostSensitivityInput:
    cost_case_ref: str
    cost_profile_ref: str
    observed_at: datetime
    fee_bps: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    settlement_bps: Decimal
    completeness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("cost_case_ref", "cost_profile_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("fee_bps", "spread_bps", "slippage_bps", "settlement_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completeness_score",
            _normalize_probability("completeness_score", self.completeness_score),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTransactionCostSensitivityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyTransactionCostSensitivityRow:
    cost_case_ref: str
    profile_count: Decimal
    missing_profile_count: Decimal
    profile_coverage_score: Decimal
    max_input_age_seconds: Decimal
    min_completeness_score: Decimal
    average_total_cost_bps: Decimal
    cost_sensitivity_span_bps: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("cost_case_ref", self.cost_case_ref)
        for field_name in (
            "profile_count",
            "missing_profile_count",
            "max_input_age_seconds",
            "average_total_cost_bps",
            "cost_sensitivity_span_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "profile_coverage_score",
            "min_completeness_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyTransactionCostSensitivityReport:
    generated_at: datetime
    config_version: str
    input_profile_count: Decimal
    cost_case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_profile_coverage_score: Decimal
    mean_min_completeness_score: Decimal
    mean_max_input_age_seconds: Decimal
    mean_readiness_score: Decimal
    mean_cost_sensitivity_span_bps: Decimal
    max_cost_sensitivity_span_bps: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyTransactionCostSensitivityReasonCodeCount, ...]
    rows: tuple[ResearchStrategyTransactionCostSensitivityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "input_profile_count",
            "cost_case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_max_input_age_seconds",
            "mean_cost_sensitivity_span_bps",
            "max_cost_sensitivity_span_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_profile_coverage_score",
            "mean_min_completeness_score",
            "mean_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_transaction_cost_sensitivity_report(
    inputs: Iterable[ResearchStrategyTransactionCostSensitivityInput],
    *,
    config: ResearchStrategyTransactionCostSensitivityConfig,
    generated_at: datetime,
) -> ResearchStrategyTransactionCostSensitivityReport:
    if type(config) is not ResearchStrategyTransactionCostSensitivityConfig:
        raise ValueError(
            "config must be a ResearchStrategyTransactionCostSensitivityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            _rows_from_inputs(
                normalized_inputs,
                config=config,
                generated_at=generated_at_utc,
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyTransactionCostSensitivityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_profile_count=_count(len(normalized_inputs)),
        cost_case_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_profile_coverage_score=_mean(
            tuple(row.profile_coverage_score for row in rows),
        ),
        mean_min_completeness_score=_mean(
            tuple(row.min_completeness_score for row in rows),
        ),
        mean_max_input_age_seconds=_mean(
            tuple(row.max_input_age_seconds for row in rows),
        ),
        mean_readiness_score=_mean(tuple(row.readiness_score for row in rows)),
        mean_cost_sensitivity_span_bps=_mean(
            tuple(row.cost_sensitivity_span_bps for row in rows),
        ),
        max_cost_sensitivity_span_bps=_max_decimal(
            tuple(row.cost_sensitivity_span_bps for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_transaction_cost_sensitivity_report_payload(
    report: ResearchStrategyTransactionCostSensitivityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTransactionCostSensitivityReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyTransactionCostSensitivityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _rows_from_inputs(
    inputs: tuple[ResearchStrategyTransactionCostSensitivityInput, ...],
    *,
    config: ResearchStrategyTransactionCostSensitivityConfig,
    generated_at: datetime,
) -> tuple[ResearchStrategyTransactionCostSensitivityRow, ...]:
    grouped: dict[str, list[ResearchStrategyTransactionCostSensitivityInput]] = {}
    for value in inputs:
        observed_at = _as_utc("observed_at", value.observed_at)
        if observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        grouped.setdefault(value.cost_case_ref, []).append(value)
    return tuple(
        _row_from_group(
            cost_case_ref=cost_case_ref,
            values=tuple(grouped[cost_case_ref]),
            config=config,
            generated_at=generated_at,
        )
        for cost_case_ref in sorted(grouped)
    )


def _row_from_group(
    *,
    cost_case_ref: str,
    values: tuple[ResearchStrategyTransactionCostSensitivityInput, ...],
    config: ResearchStrategyTransactionCostSensitivityConfig,
    generated_at: datetime,
) -> ResearchStrategyTransactionCostSensitivityRow:
    profile_count = _count(len(values))
    missing_profile_count = _max_decimal(
        (config.required_cost_profile_count - profile_count, ZERO),
    )
    profile_coverage_score = _clamp_probability(
        _divide_decimal(profile_count, config.required_cost_profile_count),
    )
    input_ages = tuple(
        _seconds_between(generated_at, _as_utc("observed_at", value.observed_at))
        for value in values
    )
    total_costs = tuple(_input_total_cost_bps(value) for value in values)
    min_completeness_score = min(
        (value.completeness_score for value in values),
        default=ZERO,
    )
    max_input_age_seconds = _max_decimal(input_ages)
    average_total_cost_bps = _mean(total_costs)
    cost_sensitivity_span_bps = _subtract_decimal(
        _max_decimal(total_costs),
        min(total_costs, default=ZERO),
    )
    readiness_score = _readiness_score(
        profile_coverage_score=profile_coverage_score,
        min_completeness_score=min_completeness_score,
        max_input_age_seconds=max_input_age_seconds,
        config=config,
    )
    status = _row_status(
        profile_coverage_score=profile_coverage_score,
        max_input_age_seconds=max_input_age_seconds,
        min_completeness_score=min_completeness_score,
        config=config,
    )
    return ResearchStrategyTransactionCostSensitivityRow(
        cost_case_ref=cost_case_ref,
        profile_count=profile_count,
        missing_profile_count=missing_profile_count,
        profile_coverage_score=profile_coverage_score,
        max_input_age_seconds=max_input_age_seconds,
        min_completeness_score=min_completeness_score,
        average_total_cost_bps=average_total_cost_bps,
        cost_sensitivity_span_bps=cost_sensitivity_span_bps,
        readiness_score=readiness_score,
        status=status,
        reason_codes=_row_reason_codes(
            profile_coverage_score=profile_coverage_score,
            max_input_age_seconds=max_input_age_seconds,
            min_completeness_score=min_completeness_score,
            config=config,
        ),
    )


def _input_total_cost_bps(
    value: ResearchStrategyTransactionCostSensitivityInput,
) -> Decimal:
    return _sum_decimals(
        (
            value.fee_bps,
            value.spread_bps,
            value.slippage_bps,
            value.settlement_bps,
        ),
    )


def _readiness_score(
    *,
    profile_coverage_score: Decimal,
    min_completeness_score: Decimal,
    max_input_age_seconds: Decimal,
    config: ResearchStrategyTransactionCostSensitivityConfig,
) -> Decimal:
    freshness_score = _clamp_probability(
        ONE - _divide_decimal(max_input_age_seconds, config.max_watch_input_age_seconds),
    )
    return _clamp_probability(
        min(profile_coverage_score, min_completeness_score, freshness_score),
    )


def _row_status(
    *,
    profile_coverage_score: Decimal,
    max_input_age_seconds: Decimal,
    min_completeness_score: Decimal,
    config: ResearchStrategyTransactionCostSensitivityConfig,
) -> str:
    if (
        profile_coverage_score < config.profile_coverage_watch_floor
        or max_input_age_seconds > config.max_watch_input_age_seconds
        or min_completeness_score < config.completeness_watch_floor
    ):
        return "block"
    if (
        profile_coverage_score < config.profile_coverage_pass_floor
        or max_input_age_seconds > config.max_pass_input_age_seconds
        or min_completeness_score < config.completeness_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    profile_coverage_score: Decimal,
    max_input_age_seconds: Decimal,
    min_completeness_score: Decimal,
    config: ResearchStrategyTransactionCostSensitivityConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if max_input_age_seconds > config.max_watch_input_age_seconds:
        codes.append("cost_input_age_block")
    elif max_input_age_seconds > config.max_pass_input_age_seconds:
        codes.append("cost_input_age_watch")
    if min_completeness_score < config.completeness_watch_floor:
        codes.append("cost_input_completeness_block")
    elif min_completeness_score < config.completeness_pass_floor:
        codes.append("cost_input_completeness_watch")
    if profile_coverage_score < config.profile_coverage_watch_floor:
        codes.append("cost_profile_coverage_block")
    elif profile_coverage_score < config.profile_coverage_pass_floor:
        codes.append("cost_profile_coverage_watch")
    if not codes:
        codes.append("transaction_cost_sensitivity_ready")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyTransactionCostSensitivityRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTransactionCostSensitivityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("transaction_cost_sensitivity_report_empty",)
    report_status = _report_status(rows)
    codes = [f"transaction_cost_sensitivity_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("cost_input_age_") for code in row_codes):
        codes.append("cost_input_age_review")
    if any(code.startswith("cost_input_completeness_") for code in row_codes):
        codes.append("cost_input_completeness_review")
    if any(code.startswith("cost_profile_coverage_") for code in row_codes):
        codes.append("cost_profile_coverage_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyTransactionCostSensitivityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.readiness_score,
        row.profile_coverage_score,
        -row.max_input_age_seconds,
        row.cost_case_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyTransactionCostSensitivityInput],
) -> tuple[ResearchStrategyTransactionCostSensitivityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[tuple[str, str]] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyTransactionCostSensitivityInput:
            raise ValueError(
                "inputs must contain ResearchStrategyTransactionCostSensitivityInput values",
            )
        _require_hard_flags("input", value)
        ref = (value.cost_case_ref, value.cost_profile_ref)
        if ref in seen_refs:
            raise ValueError(
                "inputs must not contain duplicate cost_case_ref and cost_profile_ref values",
            )
        seen_refs.add(ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyTransactionCostSensitivityRow],
) -> tuple[ResearchStrategyTransactionCostSensitivityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyTransactionCostSensitivityRow:
            raise ValueError(
                "rows must contain ResearchStrategyTransactionCostSensitivityRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.cost_case_ref in seen_refs:
            raise ValueError("rows must not contain duplicate cost_case_ref values")
        seen_refs.add(row.cost_case_ref)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategyTransactionCostSensitivityRow,
) -> None:
    if row.profile_count < ZERO:
        raise ValueError("profile_count must be nonnegative")
    if row.missing_profile_count < ZERO:
        raise ValueError("missing_profile_count must be nonnegative")
    if row.status == "pass" and row.reason_codes != ("transaction_cost_sensitivity_ready",):
        raise ValueError("pass rows must only contain ready reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyTransactionCostSensitivityReport,
) -> None:
    if report.cost_case_count != _count(len(report.rows)):
        raise ValueError("cost_case_count must match rows")
    if report.cost_case_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match cost_case_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_profile_coverage_score != _mean(
        tuple(row.profile_coverage_score for row in report.rows),
    ):
        raise ValueError("mean_profile_coverage_score must match rows")
    if report.mean_min_completeness_score != _mean(
        tuple(row.min_completeness_score for row in report.rows),
    ):
        raise ValueError("mean_min_completeness_score must match rows")
    if report.mean_max_input_age_seconds != _mean(
        tuple(row.max_input_age_seconds for row in report.rows),
    ):
        raise ValueError("mean_max_input_age_seconds must match rows")
    if report.mean_readiness_score != _mean(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("mean_readiness_score must match rows")
    if report.mean_cost_sensitivity_span_bps != _mean(
        tuple(row.cost_sensitivity_span_bps for row in report.rows),
    ):
        raise ValueError("mean_cost_sensitivity_span_bps must match rows")
    if report.max_cost_sensitivity_span_bps != _max_decimal(
        tuple(row.cost_sensitivity_span_bps for row in report.rows),
    ):
        raise ValueError("max_cost_sensitivity_span_bps must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyTransactionCostSensitivityReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyTransactionCostSensitivityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyTransactionCostSensitivityRow, ...],
) -> tuple[ResearchStrategyTransactionCostSensitivityReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyTransactionCostSensitivityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyTransactionCostSensitivityReasonCodeCount],
) -> tuple[ResearchStrategyTransactionCostSensitivityReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyTransactionCostSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTransactionCostSensitivityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(max(values, default=ZERO))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _normalize_nonnegative_decimal(
        "input_age_seconds",
        Decimal(delta.days * 86400 + delta.seconds).quantize(RATIO_QUANTUM),
    )


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _clamp_probability(value: Decimal) -> Decimal:
    return _quantize(max(ZERO, min(ONE, value)))


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be at least {name}_watch_floor")


def _require_ceiling_pair(
    name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if watch_ceiling < pass_ceiling:
        raise ValueError(f"{name}_watch_ceiling must be at least {name}_pass_ceiling")


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_canonical_public_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code)
        if reason_code not in supported:
            raise ValueError(f"{name} contains an unsupported reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_canonical_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _apply_or_verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    if provided:
        _verify_digest(value)
    else:
        object.__setattr__(value, "derived_validation_digest", _digest_for(value))


def _verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    _require_digest("derived_validation_digest", provided)
    if provided != _digest_for(value):
        raise ValueError("derived_validation_digest does not match payload")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _digest_for(value: object) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(RATIO_QUANTUM))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and any(
        fragment in value.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_STATUSES",
    "ResearchStrategyTransactionCostSensitivityConfig",
    "ResearchStrategyTransactionCostSensitivityInput",
    "ResearchStrategyTransactionCostSensitivityReasonCodeCount",
    "ResearchStrategyTransactionCostSensitivityRow",
    "ResearchStrategyTransactionCostSensitivityReport",
    "build_research_strategy_transaction_cost_sensitivity_report",
    "research_strategy_transaction_cost_sensitivity_report_payload",
)
