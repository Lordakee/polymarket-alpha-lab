"""Pure signal convergence readiness report for analyst research review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_REPORT_CONFIG_VERSION = (
    "research-strategy-signal-convergence-readiness-report-v0"
)
RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_STATUSES = (
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
    "reco" + "mmendation",
    "siz" + "ing",
    "notional",
    "position",
    "stake",
    "quantity",
    "candi" + "date",
    "market",
    "ques" + "tion",
    "url",
    "d" + "sn",
    "tab" + "le",
)

ROW_REASON_CODES = (
    "convergence_score_block",
    "convergence_score_watch",
    "independent_consensus_block",
    "independent_consensus_watch",
    "mechanics_block",
    "mechanics_watch",
    "probability_model_agreement_block",
    "probability_model_agreement_watch",
    "resolution_clarity_block",
    "resolution_clarity_watch",
    "signal_convergence_readiness_pass",
    "specialist_memory_confidence_block",
    "specialist_memory_confidence_watch",
)
REPORT_REASON_CODES = (
    "independent_consensus_review",
    "mechanics_review",
    "probability_model_agreement_review",
    "resolution_clarity_review",
    "signal_convergence_readiness_report_block",
    "signal_convergence_readiness_report_empty",
    "signal_convergence_readiness_report_pass",
    "signal_convergence_readiness_report_watch",
    "specialist_memory_confidence_review",
)


@dataclass(frozen=True)
class ResearchStrategySignalConvergenceReadinessConfig:
    config_version: str
    convergence_pass_floor: Decimal
    convergence_watch_floor: Decimal
    probability_model_agreement_pass_floor: Decimal
    probability_model_agreement_watch_floor: Decimal
    independent_consensus_pass_floor: Decimal
    independent_consensus_watch_floor: Decimal
    mechanics_pass_floor: Decimal
    mechanics_watch_floor: Decimal
    resolution_clarity_pass_floor: Decimal
    resolution_clarity_watch_floor: Decimal
    specialist_memory_confidence_pass_floor: Decimal
    specialist_memory_confidence_watch_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "convergence_pass_floor",
            "convergence_watch_floor",
            "probability_model_agreement_pass_floor",
            "probability_model_agreement_watch_floor",
            "independent_consensus_pass_floor",
            "independent_consensus_watch_floor",
            "mechanics_pass_floor",
            "mechanics_watch_floor",
            "resolution_clarity_pass_floor",
            "resolution_clarity_watch_floor",
            "specialist_memory_confidence_pass_floor",
            "specialist_memory_confidence_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "convergence",
            self.convergence_pass_floor,
            self.convergence_watch_floor,
        )
        _require_floor_pair(
            "probability_model_agreement",
            self.probability_model_agreement_pass_floor,
            self.probability_model_agreement_watch_floor,
        )
        _require_floor_pair(
            "independent_consensus",
            self.independent_consensus_pass_floor,
            self.independent_consensus_watch_floor,
        )
        _require_floor_pair(
            "mechanics",
            self.mechanics_pass_floor,
            self.mechanics_watch_floor,
        )
        _require_floor_pair(
            "resolution_clarity",
            self.resolution_clarity_pass_floor,
            self.resolution_clarity_watch_floor,
        )
        _require_floor_pair(
            "specialist_memory_confidence",
            self.specialist_memory_confidence_pass_floor,
            self.specialist_memory_confidence_watch_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalConvergenceReadinessInput:
    signal_ref: str
    strategy_ref: str
    observed_at: datetime
    probability_model_agreement_score: Decimal
    independent_consensus_score: Decimal
    mechanics_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("signal_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_model_agreement_score",
            "independent_consensus_score",
            "mechanics_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySignalConvergenceReadinessReasonCodeCount:
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
class ResearchStrategySignalConvergenceReadinessRow:
    signal_ref: str
    strategy_ref: str
    observed_at: datetime
    probability_model_agreement_score: Decimal
    independent_consensus_score: Decimal
    mechanics_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    convergence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("signal_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_model_agreement_score",
            "independent_consensus_score",
            "mechanics_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
            "convergence_score",
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
class ResearchStrategySignalConvergenceReadinessReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_convergence_score: Decimal
    mean_probability_model_agreement_score: Decimal
    mean_independent_consensus_score: Decimal
    mean_mechanics_score: Decimal
    mean_resolution_clarity_score: Decimal
    mean_specialist_memory_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategySignalConvergenceReadinessReasonCodeCount, ...]
    rows: tuple[ResearchStrategySignalConvergenceReadinessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("input_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_convergence_score",
            "mean_probability_model_agreement_score",
            "mean_independent_consensus_score",
            "mean_mechanics_score",
            "mean_resolution_clarity_score",
            "mean_specialist_memory_confidence_score",
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


def build_research_strategy_signal_convergence_readiness_report(
    inputs: Iterable[ResearchStrategySignalConvergenceReadinessInput],
    *,
    config: ResearchStrategySignalConvergenceReadinessConfig,
    generated_at: datetime,
) -> ResearchStrategySignalConvergenceReadinessReport:
    if type(config) is not ResearchStrategySignalConvergenceReadinessConfig:
        raise ValueError(
            "config must be a ResearchStrategySignalConvergenceReadinessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategySignalConvergenceReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_convergence_score=_mean(tuple(row.convergence_score for row in rows)),
        mean_probability_model_agreement_score=_mean(
            tuple(row.probability_model_agreement_score for row in rows),
        ),
        mean_independent_consensus_score=_mean(
            tuple(row.independent_consensus_score for row in rows),
        ),
        mean_mechanics_score=_mean(tuple(row.mechanics_score for row in rows)),
        mean_resolution_clarity_score=_mean(
            tuple(row.resolution_clarity_score for row in rows),
        ),
        mean_specialist_memory_confidence_score=_mean(
            tuple(row.specialist_memory_confidence_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_signal_convergence_readiness_report_payload(
    report: ResearchStrategySignalConvergenceReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySignalConvergenceReadinessReport:
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
            "report must be a ResearchStrategySignalConvergenceReadinessReport",
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


def _row_from_input(
    value: ResearchStrategySignalConvergenceReadinessInput,
    *,
    config: ResearchStrategySignalConvergenceReadinessConfig,
    generated_at: datetime,
) -> ResearchStrategySignalConvergenceReadinessRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    convergence_score = _mean(
        (
            value.probability_model_agreement_score,
            value.independent_consensus_score,
            value.mechanics_score,
            value.resolution_clarity_score,
            value.specialist_memory_confidence_score,
        ),
    )
    return ResearchStrategySignalConvergenceReadinessRow(
        signal_ref=value.signal_ref,
        strategy_ref=value.strategy_ref,
        observed_at=observed_at,
        probability_model_agreement_score=value.probability_model_agreement_score,
        independent_consensus_score=value.independent_consensus_score,
        mechanics_score=value.mechanics_score,
        resolution_clarity_score=value.resolution_clarity_score,
        specialist_memory_confidence_score=value.specialist_memory_confidence_score,
        convergence_score=convergence_score,
        status=_row_status(
            convergence_score=convergence_score,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            convergence_score=convergence_score,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    convergence_score: Decimal,
    value: ResearchStrategySignalConvergenceReadinessInput,
    config: ResearchStrategySignalConvergenceReadinessConfig,
) -> str:
    if (
        convergence_score < config.convergence_watch_floor
        or value.probability_model_agreement_score
        < config.probability_model_agreement_watch_floor
        or value.independent_consensus_score < config.independent_consensus_watch_floor
        or value.mechanics_score < config.mechanics_watch_floor
        or value.resolution_clarity_score < config.resolution_clarity_watch_floor
        or value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_watch_floor
    ):
        return "block"
    if (
        convergence_score < config.convergence_pass_floor
        or value.probability_model_agreement_score
        < config.probability_model_agreement_pass_floor
        or value.independent_consensus_score < config.independent_consensus_pass_floor
        or value.mechanics_score < config.mechanics_pass_floor
        or value.resolution_clarity_score < config.resolution_clarity_pass_floor
        or value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    convergence_score: Decimal,
    value: ResearchStrategySignalConvergenceReadinessInput,
    config: ResearchStrategySignalConvergenceReadinessConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if convergence_score < config.convergence_watch_floor:
        codes.append("convergence_score_block")
    if value.independent_consensus_score < config.independent_consensus_watch_floor:
        codes.append("independent_consensus_block")
    elif value.independent_consensus_score < config.independent_consensus_pass_floor:
        codes.append("independent_consensus_watch")
    if value.mechanics_score < config.mechanics_watch_floor:
        codes.append("mechanics_block")
    elif value.mechanics_score < config.mechanics_pass_floor:
        codes.append("mechanics_watch")
    if (
        value.probability_model_agreement_score
        < config.probability_model_agreement_watch_floor
    ):
        codes.append("probability_model_agreement_block")
    elif (
        value.probability_model_agreement_score
        < config.probability_model_agreement_pass_floor
    ):
        codes.append("probability_model_agreement_watch")
    if value.resolution_clarity_score < config.resolution_clarity_watch_floor:
        codes.append("resolution_clarity_block")
    elif value.resolution_clarity_score < config.resolution_clarity_pass_floor:
        codes.append("resolution_clarity_watch")
    if (
        value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_watch_floor
    ):
        codes.append("specialist_memory_confidence_block")
    elif (
        value.specialist_memory_confidence_score
        < config.specialist_memory_confidence_pass_floor
    ):
        codes.append("specialist_memory_confidence_watch")
    if not codes and convergence_score < config.convergence_pass_floor:
        codes.append("convergence_score_watch")
    if not codes:
        codes.append("signal_convergence_readiness_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategySignalConvergenceReadinessRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySignalConvergenceReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("signal_convergence_readiness_report_empty",)
    report_status = _report_status(rows)
    codes = [f"signal_convergence_readiness_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("independent_consensus_") for code in row_codes):
        codes.append("independent_consensus_review")
    if any(code.startswith("mechanics_") for code in row_codes):
        codes.append("mechanics_review")
    if any(code.startswith("probability_model_agreement_") for code in row_codes):
        codes.append("probability_model_agreement_review")
    if any(code.startswith("resolution_clarity_") for code in row_codes):
        codes.append("resolution_clarity_review")
    if any(code.startswith("specialist_memory_confidence_") for code in row_codes):
        codes.append("specialist_memory_confidence_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategySignalConvergenceReadinessRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.convergence_score,
        row.probability_model_agreement_score,
        row.independent_consensus_score,
        row.mechanics_score,
        row.resolution_clarity_score,
        row.specialist_memory_confidence_score,
        row.signal_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategySignalConvergenceReadinessInput],
) -> tuple[ResearchStrategySignalConvergenceReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategySignalConvergenceReadinessInput:
            raise ValueError(
                "inputs must contain ResearchStrategySignalConvergenceReadinessInput values",
            )
        _require_hard_flags("input", value)
        if value.signal_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate signal_ref values")
        seen_refs.add(value.signal_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategySignalConvergenceReadinessRow],
) -> tuple[ResearchStrategySignalConvergenceReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySignalConvergenceReadinessRow:
            raise ValueError(
                "rows must contain ResearchStrategySignalConvergenceReadinessRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.signal_ref in seen_refs:
            raise ValueError("rows must not contain duplicate signal_ref values")
        seen_refs.add(row.signal_ref)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategySignalConvergenceReadinessRow,
) -> None:
    expected_score = _mean(
        (
            row.probability_model_agreement_score,
            row.independent_consensus_score,
            row.mechanics_score,
            row.resolution_clarity_score,
            row.specialist_memory_confidence_score,
        ),
    )
    if row.convergence_score != expected_score:
        raise ValueError("convergence_score does not match row inputs")
    if row.status == "pass" and row.reason_codes != ("signal_convergence_readiness_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategySignalConvergenceReadinessReport,
) -> None:
    if report.input_row_count != _count(len(report.rows)):
        raise ValueError("input_row_count must match rows")
    if report.input_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_convergence_score != _mean(tuple(row.convergence_score for row in report.rows)):
        raise ValueError("mean_convergence_score must match rows")
    if report.mean_probability_model_agreement_score != _mean(
        tuple(row.probability_model_agreement_score for row in report.rows),
    ):
        raise ValueError("mean_probability_model_agreement_score must match rows")
    if report.mean_independent_consensus_score != _mean(
        tuple(row.independent_consensus_score for row in report.rows),
    ):
        raise ValueError("mean_independent_consensus_score must match rows")
    if report.mean_mechanics_score != _mean(tuple(row.mechanics_score for row in report.rows)):
        raise ValueError("mean_mechanics_score must match rows")
    if report.mean_resolution_clarity_score != _mean(
        tuple(row.resolution_clarity_score for row in report.rows),
    ):
        raise ValueError("mean_resolution_clarity_score must match rows")
    if report.mean_specialist_memory_confidence_score != _mean(
        tuple(row.specialist_memory_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_specialist_memory_confidence_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(
    report: ResearchStrategySignalConvergenceReadinessReport,
) -> None:
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
    rows: tuple[ResearchStrategySignalConvergenceReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySignalConvergenceReadinessRow, ...],
) -> tuple[ResearchStrategySignalConvergenceReadinessReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategySignalConvergenceReadinessReasonCodeCount(
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
    value: Iterable[ResearchStrategySignalConvergenceReadinessReasonCodeCount],
) -> tuple[ResearchStrategySignalConvergenceReadinessReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategySignalConvergenceReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySignalConvergenceReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
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


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_STATUSES
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
    if "://" in lowered or "?" in lowered or "@" in lowered or "/" in lowered:
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
    "DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_STATUSES",
    "ResearchStrategySignalConvergenceReadinessConfig",
    "ResearchStrategySignalConvergenceReadinessInput",
    "ResearchStrategySignalConvergenceReadinessReasonCodeCount",
    "ResearchStrategySignalConvergenceReadinessRow",
    "ResearchStrategySignalConvergenceReadinessReport",
    "build_research_strategy_signal_convergence_readiness_report",
    "research_strategy_signal_convergence_readiness_report_payload",
)
