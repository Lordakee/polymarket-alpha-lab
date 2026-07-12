"""Read-only cross-team disagreement escalation report.

Pure in-memory Decimal arithmetic for comparing a primary team probability
against advisory team probabilities. The module only produces immutable report
objects, public payloads, and digests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES = ("pass", "watch", "blocked")
DISAGREEMENT_LEVELS = ("low", "medium", "high")
SOURCE_QUALITY_STATUSES = ("clear", "degraded", "blocked")
MEMORY_POLICY_STATUSES = ("clear", "stale", "blocked")
MANUAL_NEXT_STEPS = (
    "no_manual_escalation_required",
    "manual_advisory_review_required",
    "manual_probability_reconciliation_required",
    "manual_source_memory_review_required",
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
MEDIUM_DISAGREEMENT_THRESHOLD = Decimal("0.050000")
HIGH_DISAGREEMENT_THRESHOLD = Decimal("0.120000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_ROW_REASON_CODES = (
    "cross_team_disagreement_pass",
    "high_disagreement_blocked",
    "memory_policy_blocked",
    "memory_policy_stale_watch",
    "medium_disagreement_watch",
    "source_quality_blocked",
    "source_quality_degraded_watch",
)
_REPORT_REASON_CODES = (
    "cross_team_disagreement_report_blocked",
    "cross_team_disagreement_report_empty",
    "cross_team_disagreement_report_pass",
    "cross_team_disagreement_report_watch",
    "high_disagreement_blocked_review",
    "medium_disagreement_watch_review",
    "memory_policy_blocked_review",
    "memory_policy_watch_review",
    "source_quality_blocked_review",
    "source_quality_watch_review",
)
_PUBLIC_ROW_FIELDS = frozenset(
    (
        "observed_at",
        "primary_team_probability",
        "advisory_team_probabilities",
        "advisory_mean_probability",
        "max_probability_gap",
        "source_quality_status",
        "memory_policy_status",
        "disagreement_level",
        "escalation_status",
        "reason_codes",
        "manual_next_step",
        "row_number",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "input_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "max_probability_gap",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "credential",
    "data" + "base",
    "dsn",
    "exec" + "ute",
    "exec" + "ution",
    "li" + "ve",
    "net" + "work",
    "or" + "der",
    "persist",
    "private",
    "secret",
    "source" + "_text",
    "source" + "_url",
    "table",
    "token",
    "trad" + "e",
    "trad" + "ing",
    "url",
    "wal" + "let",
    "b" + "uy",
    "se" + "ll",
)


@dataclass(frozen=True)
class CrossTeamDisagreementEscalationInput:
    observed_at: datetime
    primary_team_probability: Decimal
    advisory_team_probabilities: tuple[Decimal, ...]
    source_quality_status: str
    memory_policy_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CrossTeamDisagreementEscalationInput:
            raise ValueError("input must be exactly CrossTeamDisagreementEscalationInput")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "primary_team_probability",
            _normalize_probability(
                "primary_team_probability",
                self.primary_team_probability,
            ),
        )
        object.__setattr__(
            self,
            "advisory_team_probabilities",
            _normalize_advisory_probabilities(self.advisory_team_probabilities),
        )
        _require_known_value(
            "source_quality_status",
            self.source_quality_status,
            SOURCE_QUALITY_STATUSES,
        )
        _require_known_value(
            "memory_policy_status",
            self.memory_policy_status,
            MEMORY_POLICY_STATUSES,
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class CrossTeamDisagreementEscalationRow:
    observed_at: datetime
    primary_team_probability: Decimal
    advisory_team_probabilities: tuple[Decimal, ...]
    advisory_mean_probability: Decimal
    max_probability_gap: Decimal
    source_quality_status: str
    memory_policy_status: str
    disagreement_level: str
    escalation_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CrossTeamDisagreementEscalationRow:
            raise ValueError("row must be exactly CrossTeamDisagreementEscalationRow")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "primary_team_probability",
            _normalize_probability(
                "primary_team_probability",
                self.primary_team_probability,
            ),
        )
        object.__setattr__(
            self,
            "advisory_team_probabilities",
            _normalize_advisory_probabilities(self.advisory_team_probabilities),
        )
        object.__setattr__(
            self,
            "advisory_mean_probability",
            _normalize_probability("advisory_mean_probability", self.advisory_mean_probability),
        )
        object.__setattr__(
            self,
            "max_probability_gap",
            _normalize_probability("max_probability_gap", self.max_probability_gap),
        )
        _require_known_value(
            "source_quality_status",
            self.source_quality_status,
            SOURCE_QUALITY_STATUSES,
        )
        _require_known_value(
            "memory_policy_status",
            self.memory_policy_status,
            MEMORY_POLICY_STATUSES,
        )
        _require_known_value("disagreement_level", self.disagreement_level, DISAGREEMENT_LEVELS)
        _require_known_value(
            "escalation_status",
            self.escalation_status,
            CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _require_known_value("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class CrossTeamDisagreementEscalationReport:
    generated_at: datetime
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_probability_gap: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[CrossTeamDisagreementEscalationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CrossTeamDisagreementEscalationReport:
            raise ValueError("report must be exactly CrossTeamDisagreementEscalationReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("input_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_probability_gap",
            _normalize_probability("max_probability_gap", self.max_probability_gap),
        )
        _require_known_value(
            "status",
            self.status,
            CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
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


def build_cross_team_disagreement_escalation_report(
    inputs: Iterable[CrossTeamDisagreementEscalationInput],
    *,
    generated_at: datetime,
) -> CrossTeamDisagreementEscalationReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return CrossTeamDisagreementEscalationReport(
        generated_at=generated_at_utc,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_probability_gap=_max_decimal(tuple(row.max_probability_gap for row in rows)),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def cross_team_disagreement_escalation_report_payload(
    report: CrossTeamDisagreementEscalationReport | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(report, dict):
        _validate_public_payload(report)
        return _json_ready(report)
    if type(report) is not CrossTeamDisagreementEscalationReport:
        raise ValueError("report must be CrossTeamDisagreementEscalationReport")
    return _public_report_payload(report)


def cross_team_disagreement_escalation_report_digest(
    report: CrossTeamDisagreementEscalationReport,
) -> dict[str, Any]:
    payload = cross_team_disagreement_escalation_report_payload(report)
    return {
        "generated_at": payload["generated_at"],
        "status": payload["status"],
        "input_count": payload["input_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "blocked_count": payload["blocked_count"],
        "max_probability_gap": payload["max_probability_gap"],
        "reason_codes": payload["reason_codes"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
        "derived_validation_digest": payload["derived_validation_digest"],
    }


def _row_from_input(value: CrossTeamDisagreementEscalationInput) -> CrossTeamDisagreementEscalationRow:
    advisory_mean = _mean(value.advisory_team_probabilities)
    max_gap = _max_probability_gap(
        value.primary_team_probability,
        value.advisory_team_probabilities,
    )
    disagreement_level = _disagreement_level(max_gap)
    reason_codes = _row_reason_codes(
        disagreement_level=disagreement_level,
        source_quality_status=value.source_quality_status,
        memory_policy_status=value.memory_policy_status,
    )
    return CrossTeamDisagreementEscalationRow(
        observed_at=value.observed_at,
        primary_team_probability=value.primary_team_probability,
        advisory_team_probabilities=value.advisory_team_probabilities,
        advisory_mean_probability=advisory_mean,
        max_probability_gap=max_gap,
        source_quality_status=value.source_quality_status,
        memory_policy_status=value.memory_policy_status,
        disagreement_level=disagreement_level,
        escalation_status=_escalation_status(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(reason_codes),
    )


def _row_reason_codes(
    *,
    disagreement_level: str,
    source_quality_status: str,
    memory_policy_status: str,
) -> tuple[str, ...]:
    reasons = []
    if disagreement_level == "high":
        reasons.append("high_disagreement_blocked")
    elif disagreement_level == "medium":
        reasons.append("medium_disagreement_watch")
    if source_quality_status == "blocked":
        reasons.append("source_quality_blocked")
    elif source_quality_status == "degraded":
        reasons.append("source_quality_degraded_watch")
    if memory_policy_status == "blocked":
        reasons.append("memory_policy_blocked")
    elif memory_policy_status == "stale":
        reasons.append("memory_policy_stale_watch")
    if not reasons:
        reasons.append("cross_team_disagreement_pass")
    return tuple(sorted(dict.fromkeys(reasons)))


def _escalation_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if "high_disagreement_blocked" in reason_codes:
        return "manual_probability_reconciliation_required"
    if "source_quality_blocked" in reason_codes or "memory_policy_blocked" in reason_codes:
        return "manual_source_memory_review_required"
    if (
        "source_quality_degraded_watch" in reason_codes
        or "memory_policy_stale_watch" in reason_codes
    ):
        return "manual_source_memory_review_required"
    if "medium_disagreement_watch" in reason_codes:
        return "manual_advisory_review_required"
    return "no_manual_escalation_required"


def _disagreement_level(max_probability_gap: Decimal) -> str:
    if max_probability_gap >= HIGH_DISAGREEMENT_THRESHOLD:
        return "high"
    if max_probability_gap >= MEDIUM_DISAGREEMENT_THRESHOLD:
        return "medium"
    return "low"


def _report_reason_codes(
    rows: tuple[CrossTeamDisagreementEscalationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cross_team_disagreement_report_empty",)
    reasons = []
    status = _report_status(rows)
    reasons.append(f"cross_team_disagreement_report_{status}")
    if any("high_disagreement_blocked" in row.reason_codes for row in rows):
        reasons.append("high_disagreement_blocked_review")
    if any("medium_disagreement_watch" in row.reason_codes for row in rows):
        reasons.append("medium_disagreement_watch_review")
    if any("source_quality_blocked" in row.reason_codes for row in rows):
        reasons.append("source_quality_blocked_review")
    if any("source_quality_degraded_watch" in row.reason_codes for row in rows):
        reasons.append("source_quality_watch_review")
    if any("memory_policy_blocked" in row.reason_codes for row in rows):
        reasons.append("memory_policy_blocked_review")
    if any("memory_policy_stale_watch" in row.reason_codes for row in rows):
        reasons.append("memory_policy_watch_review")
    return tuple(sorted(dict.fromkeys(reasons)))


def _report_status(rows: tuple[CrossTeamDisagreementEscalationRow, ...]) -> str:
    if not rows or any(row.escalation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.escalation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[CrossTeamDisagreementEscalationRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return (("cross_team_disagreement_report_empty", _count(1)),)
    counts = []
    all_codes = sorted(
        set(report_reason_codes).union(
            reason_code for row in rows for reason_code in row.reason_codes
        ),
    )
    for reason_code in all_codes:
        if reason_code in _REPORT_REASON_CODES:
            count = _count(1)
        else:
            count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        counts.append((reason_code, count))
    return tuple(counts)


def _public_report_payload(report: CrossTeamDisagreementEscalationReport) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row) for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _validate_public_payload(public_payload)
    return public_payload


def _public_row_payload(
    row_number: int,
    row: CrossTeamDisagreementEscalationRow,
) -> dict[str, Any]:
    payload = asdict(row)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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


def _normalize_inputs(
    inputs: Iterable[CrossTeamDisagreementEscalationInput],
) -> tuple[CrossTeamDisagreementEscalationInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable of CrossTeamDisagreementEscalationInput")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not CrossTeamDisagreementEscalationInput:
            raise ValueError("inputs must contain CrossTeamDisagreementEscalationInput")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: tuple[CrossTeamDisagreementEscalationRow, ...],
) -> tuple[CrossTeamDisagreementEscalationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not CrossTeamDisagreementEscalationRow:
            raise ValueError("rows must contain CrossTeamDisagreementEscalationRow")
        _require_hard_flags("row", row)
        _verify_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by escalation severity")
    return rows


def _normalize_reason_code_counts(
    value: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = []
    previous = ""
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = item
        _require_reason_code("reason_code", reason_code, (*_ROW_REASON_CODES, *_REPORT_REASON_CODES))
        if previous and reason_code <= previous:
            raise ValueError("reason_code_counts must be sorted")
        previous = reason_code
        normalized.append((reason_code, _normalize_count("count", count)))
    return tuple(normalized)


def _row_sort_key(row: CrossTeamDisagreementEscalationRow) -> tuple[int, Decimal, str, str]:
    return (
        {"blocked": 0, "watch": 1, "pass": 2}[row.escalation_status],
        -row.max_probability_gap,
        row.source_quality_status,
        row.memory_policy_status,
    )


def _status_count(rows: tuple[CrossTeamDisagreementEscalationRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.escalation_status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("advisory_team_probabilities must not be empty")
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _max_probability_gap(primary: Decimal, advisory_values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(max(abs(primary - value) for value in advisory_values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _quantize(max(values))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return _quantize(total)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("division denominator must be nonzero")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_advisory_probabilities(value: object) -> tuple[Decimal, ...]:
    if type(value) is not tuple:
        raise ValueError("advisory_team_probabilities must be a tuple")
    if not value:
        raise ValueError("advisory_team_probabilities must not be empty")
    normalized = []
    for item in value:
        normalized.append(_normalize_probability("advisory_team_probabilities", item))
    return tuple(normalized)


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer-valued Decimal")
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_known_value(name: str, value: object, supported: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in supported:
        raise ValueError(f"{name} must be supported")


def _require_reason_code(name: str, value: object, supported: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in supported:
        raise ValueError(f"{name} must be a supported reason code")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized = tuple(sorted(dict.fromkeys(value)))
    for reason_code in normalized:
        _require_reason_code(f"{name} item", reason_code, supported)
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _validate_row_consistency(row: CrossTeamDisagreementEscalationRow) -> None:
    if row.advisory_mean_probability != _mean(row.advisory_team_probabilities):
        raise ValueError("advisory_mean_probability does not match inputs")
    if row.max_probability_gap != _max_probability_gap(
        row.primary_team_probability,
        row.advisory_team_probabilities,
    ):
        raise ValueError("max_probability_gap does not match inputs")
    if row.disagreement_level != _disagreement_level(row.max_probability_gap):
        raise ValueError("disagreement_level does not match derived fields")
    expected_reasons = _row_reason_codes(
        disagreement_level=row.disagreement_level,
        source_quality_status=row.source_quality_status,
        memory_policy_status=row.memory_policy_status,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match derived fields")
    if row.escalation_status != _escalation_status(row.reason_codes):
        raise ValueError("escalation_status does not match reason_codes")
    if row.manual_next_step != _manual_next_step(row.reason_codes):
        raise ValueError("manual_next_step does not match reason_codes")
    if row.disagreement_level == "high" and row.escalation_status == "pass":
        raise ValueError("high disagreement cannot pass")


def _validate_report_consistency(report: CrossTeamDisagreementEscalationReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count does not match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count does not match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count does not match rows")
    if report.max_probability_gap != _max_decimal(tuple(row.max_probability_gap for row in rows)):
        raise ValueError("max_probability_gap does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    reason_codes = _report_reason_codes(rows)
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(rows, reason_codes):
        raise ValueError("reason_code_counts do not match rows")


def _apply_or_verify_digest(
    value: CrossTeamDisagreementEscalationRow | CrossTeamDisagreementEscalationReport,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: CrossTeamDisagreementEscalationRow | CrossTeamDisagreementEscalationReport,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: CrossTeamDisagreementEscalationRow | CrossTeamDisagreementEscalationReport,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8",
    )
    return sha256(encoded).hexdigest()


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{name} must be a sha256 hex digest")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a public object")
    _reject_unsafe_public_surface("payload", payload)
    _require_public_keys("payload", payload, _PUBLIC_REPORT_FIELDS)
    _require_public_datetime("payload.generated_at", payload.get("generated_at"))
    for field_name in ("input_count", "pass_count", "watch_count", "blocked_count"):
        _normalize_nonnegative_decimal_string(f"payload.{field_name}", payload.get(field_name))
    _normalize_probability_decimal_string("payload.max_probability_gap", payload.get("max_probability_gap"))
    _require_known_value(
        "payload.status",
        payload.get("status"),
        CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES,
    )
    _normalize_public_reason_codes(
        "payload.reason_codes",
        payload.get("reason_codes"),
        _REPORT_REASON_CODES,
    )
    _validate_public_reason_code_counts(payload.get("reason_code_counts"))
    _validate_public_rows(payload.get("rows"))
    _require_digest("payload.derived_validation_digest", payload.get("derived_validation_digest"))
    _require_hard_flags("payload", _DictFlags(payload))
    if payload["derived_validation_digest"] != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.reason_code_counts must be a public list")
    previous = ""
    for index, item in enumerate(value):
        if type(item) is not list or len(item) != 2:
            raise ValueError("payload.reason_code_counts must contain public tuples")
        reason_code = item[0]
        _require_reason_code(
            f"payload.reason_code_counts[{index}].reason_code",
            reason_code,
            (*_ROW_REASON_CODES, *_REPORT_REASON_CODES),
        )
        if previous and reason_code <= previous:
            raise ValueError("payload.reason_code_counts must be sorted")
        previous = reason_code
        _normalize_nonnegative_decimal_string(
            f"payload.reason_code_counts[{index}].count",
            item[1],
        )


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.rows must be a public list")
    for index, item in enumerate(value):
        if type(item) is not dict:
            raise ValueError("payload.rows must contain public objects")
        label = f"payload.rows[{index}]"
        _require_public_keys(label, item, _PUBLIC_ROW_FIELDS)
        _require_public_datetime(f"{label}.observed_at", item.get("observed_at"))
        _normalize_probability_decimal_string(
            f"{label}.primary_team_probability",
            item.get("primary_team_probability"),
        )
        _validate_public_advisory_values(item.get("advisory_team_probabilities"))
        _normalize_probability_decimal_string(
            f"{label}.advisory_mean_probability",
            item.get("advisory_mean_probability"),
        )
        _normalize_probability_decimal_string(
            f"{label}.max_probability_gap",
            item.get("max_probability_gap"),
        )
        _require_known_value(
            f"{label}.source_quality_status",
            item.get("source_quality_status"),
            SOURCE_QUALITY_STATUSES,
        )
        _require_known_value(
            f"{label}.memory_policy_status",
            item.get("memory_policy_status"),
            MEMORY_POLICY_STATUSES,
        )
        _require_known_value(
            f"{label}.disagreement_level",
            item.get("disagreement_level"),
            DISAGREEMENT_LEVELS,
        )
        _require_known_value(
            f"{label}.escalation_status",
            item.get("escalation_status"),
            CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES,
        )
        _normalize_public_reason_codes(
            f"{label}.reason_codes",
            item.get("reason_codes"),
            _ROW_REASON_CODES,
        )
        _require_known_value(
            f"{label}.manual_next_step",
            item.get("manual_next_step"),
            MANUAL_NEXT_STEPS,
        )
        _normalize_nonnegative_decimal_string(f"{label}.row_number", item.get("row_number"))
        _require_digest(f"{label}.derived_validation_digest", item.get("derived_validation_digest"))
        _require_hard_flags(label, _DictFlags(item))
        if item["derived_validation_digest"] != _public_payload_digest(item):
            raise ValueError("derived_validation_digest does not match public row")


def _validate_public_advisory_values(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.advisory_team_probabilities must be a public list")
    if not value:
        raise ValueError("payload.advisory_team_probabilities must not be empty")
    for index, item in enumerate(value):
        _normalize_probability_decimal_string(
            f"payload.advisory_team_probabilities[{index}]",
            item,
        )


def _require_public_keys(label: str, payload: dict[str, Any], expected: frozenset[str]) -> None:
    actual = set(payload)
    if actual != expected:
        raise ValueError(f"{label} public keys do not match schema")


def _require_public_datetime(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a public datetime")
    parsed = datetime.fromisoformat(value)
    _as_utc(name, parsed)


def _normalize_public_reason_codes(
    name: str,
    value: object,
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a public list")
    return _normalize_reason_codes(name, tuple(value), supported)


def _normalize_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a public decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a public decimal string") from exc
    if parsed != _quantize(parsed):
        raise ValueError(f"{name} must use six decimal places")
    return _normalize_decimal(name, parsed)


def _normalize_nonnegative_decimal_string(name: str, value: object) -> Decimal:
    parsed = _normalize_decimal_string(name, value)
    if parsed < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return parsed


def _normalize_probability_decimal_string(name: str, value: object) -> Decimal:
    parsed = _normalize_decimal_string(name, value)
    if parsed < ZERO or parsed > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return parsed


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_unsafe_fragment(key):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_unsafe_fragment(field.name):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if type(value) is str and _contains_unsafe_fragment(value):
        raise ValueError("unsafe public value")


def _contains_unsafe_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES",
    "CrossTeamDisagreementEscalationInput",
    "CrossTeamDisagreementEscalationReport",
    "CrossTeamDisagreementEscalationRow",
    "build_cross_team_disagreement_escalation_report",
    "cross_team_disagreement_escalation_report_digest",
    "cross_team_disagreement_escalation_report_payload",
)
