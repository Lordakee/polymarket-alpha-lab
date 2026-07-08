"""Pure equity index signal matrix for public research prioritization."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_RESEARCH_EQUITY_INDEX_SIGNAL_MATRIX_CONFIG_VERSION",
    "EquityIndexSignalMatrixCandidate",
    "EquityIndexSignalMatrixConfig",
    "EquityIndexSignalMatrixReasonCodeCount",
    "EquityIndexSignalMatrixReport",
    "EquityIndexSignalMatrixRow",
    "build_research_equity_index_signal_matrix_report",
    "research_equity_index_signal_matrix_digest",
    "research_equity_index_signal_matrix_payload",
)


DEFAULT_RESEARCH_EQUITY_INDEX_SIGNAL_MATRIX_CONFIG_VERSION = (
    "research-equity-index-signal-matrix-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "equity_index_signal_matrix_no_inputs"


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class EquityIndexSignalMatrixConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_EQUITY_INDEX_SIGNAL_MATRIX_CONFIG_VERSION
    index_momentum_watch: Decimal = Decimal("0.600000")
    index_momentum_block: Decimal = Decimal("0.850000")
    volatility_regime_watch: Decimal = Decimal("0.550000")
    volatility_regime_block: Decimal = Decimal("0.800000")
    earnings_season_watch: Decimal = Decimal("0.500000")
    earnings_season_block: Decimal = Decimal("0.750000")
    macro_catalyst_watch: Decimal = Decimal("0.500000")
    macro_catalyst_block: Decimal = Decimal("0.750000")
    evidence_confidence_watch: Decimal = Decimal("0.500000")
    evidence_confidence_block: Decimal = Decimal("0.250000")
    staleness_watch_seconds: Decimal = Decimal("86400.000000")
    staleness_block_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, EquityIndexSignalMatrixConfig, "config")
        _require_public_string("config_version", self.config_version)
        for name in (
            "index_momentum_watch",
            "index_momentum_block",
            "volatility_regime_watch",
            "volatility_regime_block",
            "earnings_season_watch",
            "earnings_season_block",
            "macro_catalyst_watch",
            "macro_catalyst_block",
            "evidence_confidence_watch",
            "evidence_confidence_block",
        ):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        for name in ("staleness_watch_seconds", "staleness_block_seconds"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_at_most(
            "index_momentum_watch",
            self.index_momentum_watch,
            self.index_momentum_block,
        )
        _require_at_most(
            "volatility_regime_watch",
            self.volatility_regime_watch,
            self.volatility_regime_block,
        )
        _require_at_most(
            "earnings_season_watch",
            self.earnings_season_watch,
            self.earnings_season_block,
        )
        _require_at_most(
            "macro_catalyst_watch",
            self.macro_catalyst_watch,
            self.macro_catalyst_block,
        )
        _require_at_least(
            "evidence_confidence_watch",
            self.evidence_confidence_watch,
            self.evidence_confidence_block,
        )
        _require_at_most(
            "staleness_watch_seconds",
            self.staleness_watch_seconds,
            self.staleness_block_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class EquityIndexSignalMatrixCandidate(_FinalPublicDataclass):
    public_event_label: str
    index_family: str
    signal_family: str
    index_momentum_score: Decimal
    volatility_regime_score: Decimal
    earnings_season_score: Decimal
    macro_catalyst_score: Decimal
    evidence_confidence_score: Decimal
    staleness_seconds: Decimal
    evidence_family_count: Decimal
    reason_codes: tuple[str, ...]
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, EquityIndexSignalMatrixCandidate, "candidate")
        for name in ("public_event_label", "index_family", "signal_family"):
            _require_public_string(name, getattr(self, name))
        for name in (
            "index_momentum_score",
            "volatility_regime_score",
            "earnings_season_score",
            "macro_catalyst_score",
            "evidence_confidence_score",
        ):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        for name in ("staleness_seconds", "evidence_family_count"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class EquityIndexSignalMatrixRow(_FinalPublicDataclass):
    public_event_label: str
    index_family: str
    signal_family: str
    public_status: str
    index_momentum_score: Decimal
    volatility_regime_score: Decimal
    earnings_season_score: Decimal
    macro_catalyst_score: Decimal
    evidence_confidence_score: Decimal
    staleness_seconds: Decimal
    evidence_family_count: Decimal
    priority_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, EquityIndexSignalMatrixRow, "row")
        for name in ("public_event_label", "index_family", "signal_family"):
            _require_public_string(name, getattr(self, name))
        _require_public_status("public_status", self.public_status)
        for name in (
            "index_momentum_score",
            "volatility_regime_score",
            "earnings_season_score",
            "macro_catalyst_score",
            "evidence_confidence_score",
            "priority_score",
        ):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        for name in ("staleness_seconds", "evidence_family_count"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.public_status != _row_status(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class EquityIndexSignalMatrixReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, EquityIndexSignalMatrixReasonCodeCount, "reason_count")
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_decimal("count", self.count))
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class EquityIndexSignalMatrixReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_priority_score: Decimal
    max_priority_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[EquityIndexSignalMatrixReasonCodeCount, ...]
    rows: tuple[EquityIndexSignalMatrixRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, EquityIndexSignalMatrixReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_status("status", self.status)
        for name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in ("mean_priority_score", "max_priority_score"):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    EquityIndexSignalMatrixCandidate,
    EquityIndexSignalMatrixConfig,
    EquityIndexSignalMatrixReasonCodeCount,
    EquityIndexSignalMatrixReport,
    EquityIndexSignalMatrixRow,
)


def build_research_equity_index_signal_matrix_report(
    candidates: Iterable[EquityIndexSignalMatrixCandidate],
    *,
    config: EquityIndexSignalMatrixConfig,
    generated_at: datetime,
) -> EquityIndexSignalMatrixReport:
    if type(config) is not EquityIndexSignalMatrixConfig:
        raise ValueError("config must be a EquityIndexSignalMatrixConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_matrix_row(row, config=config) for row in inputs),
            key=_row_sort_key,
        ),
    )
    return EquityIndexSignalMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_rollup_status(tuple(row.public_status for row in rows)),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_priority_score=_mean(tuple(row.priority_score for row in rows)),
        max_priority_score=_max_decimal(tuple(row.priority_score for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_equity_index_signal_matrix_payload(
    report: EquityIndexSignalMatrixReport,
) -> dict[str, Any]:
    if type(report) is not EquityIndexSignalMatrixReport:
        raise ValueError("report must be a EquityIndexSignalMatrixReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_equity_index_signal_matrix_digest(
    report: EquityIndexSignalMatrixReport,
) -> dict[str, Any]:
    payload = research_equity_index_signal_matrix_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "status": payload["status"],
        "candidate_count": payload["candidate_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "reason_codes": payload["reason_codes"],
        "top_rows": payload["rows"][:3],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("digest", digest)
    return digest


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


def _matrix_row(
    row: EquityIndexSignalMatrixCandidate,
    *,
    config: EquityIndexSignalMatrixConfig,
) -> EquityIndexSignalMatrixRow:
    reason_codes = _row_reason_codes(row, config=config)
    return EquityIndexSignalMatrixRow(
        public_event_label=row.public_event_label,
        index_family=row.index_family,
        signal_family=row.signal_family,
        public_status=_row_status(reason_codes),
        index_momentum_score=row.index_momentum_score,
        volatility_regime_score=row.volatility_regime_score,
        earnings_season_score=row.earnings_season_score,
        macro_catalyst_score=row.macro_catalyst_score,
        evidence_confidence_score=row.evidence_confidence_score,
        staleness_seconds=row.staleness_seconds,
        evidence_family_count=row.evidence_family_count,
        priority_score=_priority_score(row),
        observed_at=row.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: EquityIndexSignalMatrixCandidate,
    *,
    config: EquityIndexSignalMatrixConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    if row.index_momentum_score >= config.index_momentum_block:
        reason_codes.append("index_momentum_block")
    elif row.index_momentum_score >= config.index_momentum_watch:
        reason_codes.append("index_momentum_watch")
    if row.volatility_regime_score >= config.volatility_regime_block:
        reason_codes.append("volatility_regime_block")
    elif row.volatility_regime_score >= config.volatility_regime_watch:
        reason_codes.append("volatility_regime_watch")
    if row.earnings_season_score >= config.earnings_season_block:
        reason_codes.append("earnings_season_block")
    elif row.earnings_season_score >= config.earnings_season_watch:
        reason_codes.append("earnings_season_watch")
    if row.macro_catalyst_score >= config.macro_catalyst_block:
        reason_codes.append("macro_catalyst_block")
    elif row.macro_catalyst_score >= config.macro_catalyst_watch:
        reason_codes.append("macro_catalyst_watch")
    if row.evidence_confidence_score <= config.evidence_confidence_block:
        reason_codes.append("evidence_confidence_block")
    elif row.evidence_confidence_score <= config.evidence_confidence_watch:
        reason_codes.append("evidence_confidence_watch")
    if row.staleness_seconds > config.staleness_block_seconds:
        reason_codes.append("staleness_block")
    elif row.staleness_seconds > config.staleness_watch_seconds:
        reason_codes.append("staleness_watch")
    if not _has_matrix_signal(reason_codes):
        reason_codes.append("equity_index_signal_clear")
    return _normalize_reason_codes(tuple(sorted(reason_codes)))


def _priority_score(row: EquityIndexSignalMatrixCandidate) -> Decimal:
    confidence_gap = _quantize(ONE - row.evidence_confidence_score)
    staleness_pressure = min(
        ONE,
        _quantize(row.staleness_seconds / Decimal("259200.000000")),
    )
    return _clamp_probability(
        _quantize(
            (row.index_momentum_score * Decimal("0.250000"))
            + (row.volatility_regime_score * Decimal("0.250000"))
            + (row.earnings_season_score * Decimal("0.150000"))
            + (row.macro_catalyst_score * Decimal("0.250000"))
            + (confidence_gap * Decimal("0.050000"))
            + (staleness_pressure * Decimal("0.050000")),
        ),
    )


def _has_matrix_signal(reason_codes: list[str]) -> bool:
    return any(code.endswith("_watch") or code.endswith("_block") for code in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(rows: tuple[EquityIndexSignalMatrixRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.public_status for row in rows))
    reason_codes = [f"equity_index_signal_matrix_{'clear' if status == 'pass' else status}"]
    row_reason_codes = frozenset(code for row in rows for code in row.reason_codes)
    for code in (
        "earnings_season_block",
        "earnings_season_watch",
        "evidence_confidence_block",
        "evidence_confidence_watch",
        "index_momentum_block",
        "index_momentum_watch",
        "macro_catalyst_block",
        "macro_catalyst_watch",
        "staleness_block",
        "staleness_watch",
        "volatility_regime_block",
        "volatility_regime_watch",
    ):
        if code in row_reason_codes:
            reason_codes.append(code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[EquityIndexSignalMatrixRow, ...],
) -> tuple[EquityIndexSignalMatrixReasonCodeCount, ...]:
    if not rows:
        return (
            EquityIndexSignalMatrixReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        EquityIndexSignalMatrixReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_candidates(
    candidates: Iterable[EquityIndexSignalMatrixCandidate],
) -> tuple[EquityIndexSignalMatrixCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not EquityIndexSignalMatrixCandidate:
            raise ValueError("candidates must contain EquityIndexSignalMatrixCandidate values")
        _require_hard_flags("candidate", row)
        if row.public_event_label in seen_labels:
            raise ValueError("candidates must not contain duplicate public_event_label values")
        seen_labels.add(row.public_event_label)
    return rows


def _normalize_rows(
    rows: Iterable[EquityIndexSignalMatrixRow],
) -> tuple[EquityIndexSignalMatrixRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_labels: set[str] = set()
    for row in values:
        if type(row) is not EquityIndexSignalMatrixRow:
            raise ValueError("rows must contain EquityIndexSignalMatrixRow values")
        _require_hard_flags("row", row)
        if row.public_event_label in seen_labels:
            raise ValueError("rows must not contain duplicate public_event_label values")
        seen_labels.add(row.public_event_label)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[EquityIndexSignalMatrixReasonCodeCount],
) -> tuple[EquityIndexSignalMatrixReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not EquityIndexSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain EquityIndexSignalMatrixReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(row: EquityIndexSignalMatrixRow) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.public_status],
        -row.priority_score,
        row.public_event_label,
        row.index_family,
        row.signal_family,
    )


def _status_count(rows: tuple[EquityIndexSignalMatrixRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.public_status == status))


def _validate_report(report: EquityIndexSignalMatrixReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_priority_score != _mean(tuple(row.priority_score for row in rows)):
        raise ValueError("mean_priority_score must match rows")
    if report.max_priority_score != _max_decimal(tuple(row.priority_score for row in rows)):
        raise ValueError("max_priority_score must match rows")
    if report.status != _rollup_status(tuple(row.public_status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        _rebuild_public_dataclass(label, value)
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _require_public_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(str(exc)) from exc


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _unsafe_fragments() -> tuple[str, ...]:
    shared_fragments = tuple(
        fragment
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS
        if fragment != "sign"
    )
    return (
        *shared_fragments,
        "candidate" "_id",
        "candidate id",
        "raw_candidate",
        "market",
        "slug",
        "ques" "tion",
        "source" "_ref",
        "source ref",
        "source" "_url",
        "source url",
        "://",
        "ht" "tp",
        "raw",
        "te" "xt",
        "dsn",
        "tab" "le",
        "tok" "en",
        "api_",
        "au" "th",
        "wal" "let",
        "or" "der",
        "tra" "ding",
        "tra" "de",
        "b" "uy",
        "s" "ell",
        "rec" "ommend",
        "pos" "ition",
    )


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _unsafe_fragments())


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")


def _normalize_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_probability(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be at most one")
    return normalized


def _require_six_decimal_decimal(name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{name} must use six decimal places")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    if values == (NO_INPUTS_REASON,):
        return values
    if not values[0].startswith("equity_index_signal_matrix_"):
        raise ValueError("reason_codes must begin with matrix rollup code")
    if values[1:] != tuple(sorted(values[1:])):
        raise ValueError("reason_codes must use canonical sequence")
    return values


def _require_public_string(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} has unsafe value")


def _require_public_status(name: str, value: str) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for name in PHASE_FLAG_FIELDS:
        if getattr(value, name, None) is not True:
            raise ValueError(f"{name} must be True for {label}")


def _require_at_most(name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{name} must be less than or equal to paired threshold")


def _require_at_least(name: str, upper: Decimal, lower: Decimal) -> None:
    if upper < lower:
        raise ValueError(f"{name} must be greater than or equal to paired threshold")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
