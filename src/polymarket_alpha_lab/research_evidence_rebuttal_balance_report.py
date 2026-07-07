"""Pure research evidence/rebuttal balance report.

The module is deterministic and side-effect free. Callers provide typed evidence
stances; the report returns research-only balance metrics, statuses, and reason
codes without carrying raw source material into the public payload.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchEvidenceRebuttalBalanceConfig",
    "ResearchEvidenceRebuttalBalanceEvidenceRow",
    "ResearchEvidenceRebuttalBalanceReasonCodeCount",
    "ResearchEvidenceRebuttalBalanceReport",
    "ResearchEvidenceRebuttalBalanceRow",
    "build_research_evidence_rebuttal_balance_report",
    "research_evidence_rebuttal_balance_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-evidence-rebuttal-balance-report-v0"
STATUSES = ("pass", "watch", "blocked")
STANCES = ("support", "rebuttal", "neutral")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_MAX_PASS_ABSOLUTE_BALANCE_GAP = Decimal("0.200000")
DEFAULT_MAX_WATCH_ABSOLUTE_BALANCE_GAP = Decimal("0.500000")
UNSAFE_PUBLIC_PARTS = (
    "raw",
    "source_url",
    "url",
    "dsn",
    "table",
    "token",
)
UNSAFE_PUBLIC_EXACT = ("id", "source", "text")
UNSAFE_PUBLIC_VALUE_PARTS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "dsn=",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchEvidenceRebuttalBalanceConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_directional_evidence_count: Decimal = Decimal("2")
    max_pass_absolute_balance_gap: Decimal = DEFAULT_MAX_PASS_ABSOLUTE_BALANCE_GAP
    max_watch_absolute_balance_gap: Decimal = DEFAULT_MAX_WATCH_ABSOLUTE_BALANCE_GAP
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceRebuttalBalanceConfig:
            raise ValueError("config must be exact")
        _require_public_code("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_directional_evidence_count",
            _require_positive_whole_decimal(
                "min_directional_evidence_count",
                self.min_directional_evidence_count,
            ),
        )
        for field_name in (
            "max_pass_absolute_balance_gap",
            "max_watch_absolute_balance_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_absolute_balance_gap > self.max_watch_absolute_balance_gap:
            raise ValueError(
                "max_pass_absolute_balance_gap must not exceed "
                "max_watch_absolute_balance_gap",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEvidenceRebuttalBalanceEvidenceRow:
    research_key: str
    stance: str
    strength: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceRebuttalBalanceEvidenceRow:
            raise ValueError("evidence row must be exact")
        _require_public_code("research_key", self.research_key)
        _require_enum("stance", self.stance, STANCES)
        object.__setattr__(
            self,
            "strength",
            _require_probability_decimal("strength", self.strength),
        )
        if self.strength == ZERO:
            raise ValueError("strength must be positive")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence row", self)


@dataclass(frozen=True)
class ResearchEvidenceRebuttalBalanceRow:
    research_key: str
    status: str
    evidence_count: Decimal
    support_count: Decimal
    rebuttal_count: Decimal
    neutral_count: Decimal
    support_weight: Decimal
    rebuttal_weight: Decimal
    neutral_weight: Decimal
    directional_weight: Decimal
    support_share: Decimal
    rebuttal_share: Decimal
    absolute_balance_gap: Decimal
    balance_score: Decimal
    latest_observed_at: datetime
    latest_evidence_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceRebuttalBalanceRow:
            raise ValueError("row must be exact")
        _require_public_code("research_key", self.research_key)
        _require_status("status", self.status)
        for field_name in (
            "evidence_count",
            "support_count",
            "rebuttal_count",
            "neutral_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "support_weight",
            "rebuttal_weight",
            "neutral_weight",
            "directional_weight",
            "latest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "support_share",
            "rebuttal_share",
            "absolute_balance_gap",
            "balance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEvidenceRebuttalBalanceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceRebuttalBalanceReasonCodeCount:
            raise ValueError("reason code count must be exact")
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEvidenceRebuttalBalanceReport:
    generated_at: datetime
    config_version: str
    status: str
    research_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_balance_score: Decimal
    max_absolute_balance_gap: Decimal
    rows: tuple[ResearchEvidenceRebuttalBalanceRow, ...]
    reason_code_counts: tuple[ResearchEvidenceRebuttalBalanceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceRebuttalBalanceReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_code("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "research_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_balance_score", "max_absolute_balance_gap"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_evidence_rebuttal_balance_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchEvidenceRebuttalBalanceConfig,
    generated_at: datetime,
) -> ResearchEvidenceRebuttalBalanceReport:
    if type(config) is not ResearchEvidenceRebuttalBalanceConfig:
        raise ValueError("config must be a ResearchEvidenceRebuttalBalanceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        _reject_future_observed_at(item, generated_at_utc)

    grouped: dict[str, list[ResearchEvidenceRebuttalBalanceEvidenceRow]] = {}
    for item in evidence_items:
        grouped.setdefault(item.research_key, []).append(item)

    rows = tuple(
        _balance_row_from_research_key(
            research_key=research_key,
            evidence_rows=tuple(grouped[research_key]),
            config=config,
            generated_at=generated_at_utc,
        )
        for research_key in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchEvidenceRebuttalBalanceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_summary_status(reason_codes),
        research_count=_decimal_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_balance_score=_average_balance_score(rows),
        max_absolute_balance_gap=_max_absolute_balance_gap(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_evidence_rebuttal_balance_report_payload(
    report: ResearchEvidenceRebuttalBalanceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEvidenceRebuttalBalanceReport:
        raise ValueError("report must be a ResearchEvidenceRebuttalBalanceReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _balance_row_from_research_key(
    *,
    research_key: str,
    evidence_rows: tuple[ResearchEvidenceRebuttalBalanceEvidenceRow, ...],
    config: ResearchEvidenceRebuttalBalanceConfig,
    generated_at: datetime,
) -> ResearchEvidenceRebuttalBalanceRow:
    sorted_rows = tuple(
        sorted(
            evidence_rows,
            key=lambda item: (
                item.observed_at.isoformat(),
                item.stance,
                str(item.strength),
                tuple(item.reason_codes),
            ),
        ),
    )
    latest = max(sorted_rows, key=lambda item: item.observed_at)
    support_items = tuple(item for item in sorted_rows if item.stance == "support")
    rebuttal_items = tuple(item for item in sorted_rows if item.stance == "rebuttal")
    neutral_items = tuple(item for item in sorted_rows if item.stance == "neutral")
    support_weight = _weight_total(support_items)
    rebuttal_weight = _weight_total(rebuttal_items)
    neutral_weight = _weight_total(neutral_items)
    directional_weight = _quantize(support_weight + rebuttal_weight)
    support_share = _share(support_weight, directional_weight)
    rebuttal_share = _share(rebuttal_weight, directional_weight)
    absolute_balance_gap = _quantize(abs(support_share - rebuttal_share))
    balance_score = _quantize(ONE - absolute_balance_gap)
    directional_evidence_count = len(support_items) + len(rebuttal_items)
    status = _row_status(
        support_count=len(support_items),
        rebuttal_count=len(rebuttal_items),
        directional_evidence_count=directional_evidence_count,
        absolute_balance_gap=absolute_balance_gap,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        support_count=len(support_items),
        rebuttal_count=len(rebuttal_items),
        neutral_count=len(neutral_items),
        directional_evidence_count=directional_evidence_count,
        absolute_balance_gap=absolute_balance_gap,
        config=config,
        input_reason_codes=tuple(
            reason_code for item in sorted_rows for reason_code in item.reason_codes
        ),
    )

    return ResearchEvidenceRebuttalBalanceRow(
        research_key=research_key,
        status=status,
        evidence_count=_decimal_count(len(sorted_rows)),
        support_count=_decimal_count(len(support_items)),
        rebuttal_count=_decimal_count(len(rebuttal_items)),
        neutral_count=_decimal_count(len(neutral_items)),
        support_weight=support_weight,
        rebuttal_weight=rebuttal_weight,
        neutral_weight=neutral_weight,
        directional_weight=directional_weight,
        support_share=support_share,
        rebuttal_share=rebuttal_share,
        absolute_balance_gap=absolute_balance_gap,
        balance_score=balance_score,
        latest_observed_at=latest.observed_at,
        latest_evidence_age_seconds=_age_seconds(generated_at, latest.observed_at),
        reason_codes=reason_codes,
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchEvidenceRebuttalBalanceEvidenceRow, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_evidence_row(value) for value in values)


def _coerce_evidence_row(value: object) -> ResearchEvidenceRebuttalBalanceEvidenceRow:
    if type(value) is ResearchEvidenceRebuttalBalanceEvidenceRow:
        _require_hard_flags("evidence row", value)
        return value
    _require_hard_flags("evidence row", value)
    return ResearchEvidenceRebuttalBalanceEvidenceRow(
        research_key=_field_value(value, "research_key"),
        stance=_field_value(value, "stance"),
        strength=_field_value(value, "strength"),
        observed_at=_field_value(value, "observed_at"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_status(
    *,
    support_count: int,
    rebuttal_count: int,
    directional_evidence_count: int,
    absolute_balance_gap: Decimal,
    config: ResearchEvidenceRebuttalBalanceConfig,
) -> str:
    if support_count == 0 or rebuttal_count == 0:
        return "blocked"
    if Decimal(directional_evidence_count) < config.min_directional_evidence_count:
        return "blocked"
    if absolute_balance_gap <= config.max_pass_absolute_balance_gap:
        return "pass"
    if absolute_balance_gap <= config.max_watch_absolute_balance_gap:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    status: str,
    support_count: int,
    rebuttal_count: int,
    neutral_count: int,
    directional_evidence_count: int,
    absolute_balance_gap: Decimal,
    config: ResearchEvidenceRebuttalBalanceConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"evidence_rebuttal_balance_{status}"}
    if support_count == 0 or rebuttal_count == 0:
        reason_codes.add("one_sided_evidence")
    if Decimal(directional_evidence_count) < config.min_directional_evidence_count:
        reason_codes.add("insufficient_directional_evidence")
    if neutral_count:
        reason_codes.add("neutral_evidence_present")
    if absolute_balance_gap <= config.max_pass_absolute_balance_gap:
        reason_codes.add("balanced_evidence")
    elif absolute_balance_gap <= config.max_watch_absolute_balance_gap:
        reason_codes.add("moderate_evidence_imbalance")
    else:
        reason_codes.add("material_evidence_imbalance")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchEvidenceRebuttalBalanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_evidence",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.status == "watch" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("evidence_rebuttal_balance_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_research_evidence",):
        return "blocked"
    if "evidence_rebuttal_balance_blocked" in reason_codes:
        return "blocked"
    if "evidence_rebuttal_balance_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchEvidenceRebuttalBalanceRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEvidenceRebuttalBalanceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEvidenceRebuttalBalanceReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEvidenceRebuttalBalanceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_balance_score(rows: tuple[ResearchEvidenceRebuttalBalanceRow, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(sum((row.balance_score for row in rows), ZERO) / Decimal(len(rows)))


def _max_absolute_balance_gap(
    rows: tuple[ResearchEvidenceRebuttalBalanceRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(row.absolute_balance_gap for row in rows)


def _weight_total(items: tuple[ResearchEvidenceRebuttalBalanceEvidenceRow, ...]) -> Decimal:
    return _quantize(sum((item.strength for item in items), ZERO))


def _share(weight: Decimal, directional_weight: Decimal) -> Decimal:
    if directional_weight == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(weight / directional_weight)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _reject_future_observed_at(
    item: ResearchEvidenceRebuttalBalanceEvidenceRow,
    generated_at: datetime,
) -> None:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _status_count(
    rows: tuple[ResearchEvidenceRebuttalBalanceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEvidenceRebuttalBalanceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEvidenceRebuttalBalanceRow:
            raise ValueError("rows must contain ResearchEvidenceRebuttalBalanceRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchEvidenceRebuttalBalanceReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEvidenceRebuttalBalanceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEvidenceRebuttalBalanceReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchEvidenceRebuttalBalanceRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.evidence_count != row.support_count + row.rebuttal_count + row.neutral_count:
        raise ValueError("evidence_count must equal stance counts")
    if row.directional_weight != _quantize(row.support_weight + row.rebuttal_weight):
        raise ValueError("directional_weight must equal support and rebuttal weights")
    if row.directional_weight == ZERO:
        expected_support_share = ZERO.quantize(RATIO_QUANTUM)
        expected_rebuttal_share = ZERO.quantize(RATIO_QUANTUM)
    else:
        expected_support_share = _share(row.support_weight, row.directional_weight)
        expected_rebuttal_share = _share(row.rebuttal_weight, row.directional_weight)
    if row.support_share != expected_support_share:
        raise ValueError("support_share must match weights")
    if row.rebuttal_share != expected_rebuttal_share:
        raise ValueError("rebuttal_share must match weights")
    if row.absolute_balance_gap != _quantize(abs(row.support_share - row.rebuttal_share)):
        raise ValueError("absolute_balance_gap must match shares")
    if row.balance_score != _quantize(ONE - row.absolute_balance_gap):
        raise ValueError("balance_score must match absolute_balance_gap")
    if f"evidence_rebuttal_balance_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")


def _validate_report_consistency(report: ResearchEvidenceRebuttalBalanceReport) -> None:
    if report.research_count != _decimal_count(len(report.rows)):
        raise ValueError("research_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_balance_score != _average_balance_score(report.rows):
        raise ValueError("average_balance_score must match rows")
    if report.max_absolute_balance_gap != _max_absolute_balance_gap(report.rows):
        raise ValueError("max_absolute_balance_gap must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if normalized in UNSAFE_PUBLIC_EXACT:
        raise ValueError(f"{label} must not expose raw source material")
    if any(part in normalized for part in UNSAFE_PUBLIC_PARTS):
        raise ValueError(f"{label} must not expose raw source material")
    if any(part in normalized for part in UNSAFE_PUBLIC_VALUE_PARTS):
        raise ValueError(f"{label} must not expose raw source material")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic public code text")
    _reject_unsafe_public_text(field_name, value)


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain deterministic code text")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    _reject_unsafe_public_text(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
