"""Pure expected-value sanity gate for manual research prioritization.

The gate is deterministic and side-effect free. It only converts caller-supplied
sanitized research candidates into pass/watch/block states for human review.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any


CONFIG_VERSION = "research-expected-value-sanity-gate-v0"
DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")

_PASS_REASON = "expected_value_sanity_pass"
_EMPTY_REASON = "expected_value_sanity_empty"
_BLOCK_PRESENT_REASON = "expected_value_sanity_block_present"
_WATCH_PRESENT_REASON = "expected_value_sanity_watch_present"
_REPORT_REASON_PRIORITY = (
    _BLOCK_PRESENT_REASON,
    _WATCH_PRESENT_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_ROW_REASONS = frozenset(
    (
        "probability_delta_below_watch",
        "cost_ratio_at_or_above_block",
        "evidence_quality_below_watch",
        "liquidity_summary_below_watch",
    ),
)
_WATCH_ROW_REASONS = frozenset(
    (
        "probability_delta_below_pass",
        "cost_ratio_at_or_above_watch",
        "evidence_quality_below_pass",
        "liquidity_summary_below_pass",
    ),
)

_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_cost_to_delta_ratio",
        "min_evidence_quality_score",
        "min_liquidity_summary_score",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "research_reference",
        "observed_at",
        "sanitized_probability_delta",
        "total_cost_probability",
        "cost_to_delta_ratio",
        "evidence_quality_score",
        "liquidity_summary_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_DECIMAL_REPORT_FIELDS = frozenset(
    (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_cost_to_delta_ratio",
        "min_evidence_quality_score",
        "min_liquidity_summary_score",
    ),
)
_DECIMAL_ROW_FIELDS = frozenset(
    (
        "sanitized_probability_delta",
        "total_cost_probability",
        "cost_to_delta_ratio",
        "evidence_quality_score",
        "liquidity_summary_score",
    ),
)


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
class ResearchExpectedValueSanityGateConfig(_FinalPublicDataclass):
    config_version: str = CONFIG_VERSION
    min_pass_probability_delta: Decimal = Decimal("0.050000")
    min_watch_probability_delta: Decimal = Decimal("0.020000")
    watch_cost_to_delta_ratio: Decimal = Decimal("0.300000")
    block_cost_to_delta_ratio: Decimal = Decimal("0.500000")
    min_pass_evidence_quality: Decimal = Decimal("0.750000")
    min_watch_evidence_quality: Decimal = Decimal("0.500000")
    min_pass_liquidity_summary: Decimal = Decimal("0.650000")
    min_watch_liquidity_summary: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchExpectedValueSanityGateConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_probability_delta",
            "min_watch_probability_delta",
            "watch_cost_to_delta_ratio",
            "block_cost_to_delta_ratio",
            "min_pass_evidence_quality",
            "min_watch_evidence_quality",
            "min_pass_liquidity_summary",
            "min_watch_liquidity_summary",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        if self.min_watch_probability_delta > self.min_pass_probability_delta:
            raise ValueError("min_watch_probability_delta must be <= pass threshold")
        if self.watch_cost_to_delta_ratio > self.block_cost_to_delta_ratio:
            raise ValueError("watch_cost_to_delta_ratio must be <= block threshold")
        if self.min_watch_evidence_quality > self.min_pass_evidence_quality:
            raise ValueError("min_watch_evidence_quality must be <= pass threshold")
        if self.min_watch_liquidity_summary > self.min_pass_liquidity_summary:
            raise ValueError("min_watch_liquidity_summary must be <= pass threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchExpectedValueSanityGateCandidate(_FinalPublicDataclass):
    candidate_reference: str
    market_reference: str
    observed_at: datetime
    sanitized_probability_delta: Decimal
    total_cost_probability: Decimal
    evidence_quality_score: Decimal
    liquidity_summary_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchExpectedValueSanityGateCandidate, "candidate")
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "candidate_reference",
            _redacted_reference(
                "research_ref_",
                f"{self.candidate_reference}\0{self.market_reference}",
            ),
        )
        object.__setattr__(
            self,
            "market_reference",
            _redacted_reference("market_ref_", self.market_reference),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "sanitized_probability_delta",
            _require_positive_probability_decimal(
                "sanitized_probability_delta",
                self.sanitized_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "total_cost_probability",
            _require_probability_decimal(
                "total_cost_probability",
                self.total_cost_probability,
            ),
        )
        for field_name in ("evidence_quality_score", "liquidity_summary_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchExpectedValueSanityGateRow(_FinalPublicDataclass):
    research_reference: str
    observed_at: datetime
    sanitized_probability_delta: Decimal
    total_cost_probability: Decimal
    cost_to_delta_ratio: Decimal
    evidence_quality_score: Decimal
    liquidity_summary_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchExpectedValueSanityGateRow, "row")
        _require_redacted_reference("research_reference", self.research_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "sanitized_probability_delta",
            _require_positive_probability_decimal(
                "sanitized_probability_delta",
                self.sanitized_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "total_cost_probability",
            _require_probability_decimal(
                "total_cost_probability",
                self.total_cost_probability,
            ),
        )
        object.__setattr__(
            self,
            "cost_to_delta_ratio",
            _require_non_negative_decimal(
                "cost_to_delta_ratio",
                self.cost_to_delta_ratio,
            ),
        )
        for field_name in ("evidence_quality_score", "liquidity_summary_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchExpectedValueSanityGateReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_cost_to_delta_ratio: Decimal
    min_evidence_quality_score: Decimal
    min_liquidity_summary_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchExpectedValueSanityGateRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchExpectedValueSanityGateReport, "report")
        _require_hard_flags("report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_cost_to_delta_ratio",
            "min_evidence_quality_score",
            "min_liquidity_summary_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_negative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report values")


def build_research_expected_value_sanity_gate_report(
    candidates: Iterable[object],
    *,
    config: ResearchExpectedValueSanityGateConfig,
    generated_at: datetime,
) -> ResearchExpectedValueSanityGateReport:
    if type(config) is not ResearchExpectedValueSanityGateConfig:
        raise ValueError("config must be a ResearchExpectedValueSanityGateConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in _normalize_candidates(candidates)
            ),
            key=_row_sort_key,
        ),
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(sum(1 for row in rows if row.status == "pass")),
        "watch_count": _count_decimal(sum(1 for row in rows if row.status == "watch")),
        "block_count": _count_decimal(sum(1 for row in rows if row.status == "block")),
        "max_cost_to_delta_ratio": _max_decimal(
            row.cost_to_delta_ratio for row in rows
        ),
        "min_evidence_quality_score": _min_decimal(
            row.evidence_quality_score for row in rows
        ),
        "min_liquidity_summary_score": _min_decimal(
            row.liquidity_summary_score for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchExpectedValueSanityGateReport(
        **values,
        derived_validation_digest=_digest_payload(_json_ready(values)),
    )


def research_expected_value_sanity_gate_payload(
    report: ResearchExpectedValueSanityGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchExpectedValueSanityGateReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchExpectedValueSanityGateReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
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


def _row_from_candidate(
    candidate: ResearchExpectedValueSanityGateCandidate,
    *,
    config: ResearchExpectedValueSanityGateConfig,
    generated_at: datetime,
) -> ResearchExpectedValueSanityGateRow:
    if candidate.observed_at > generated_at:
        raise ValueError("observed_at must not follow generated_at")
    cost_to_delta_ratio = _quantize_decimal(
        candidate.total_cost_probability / candidate.sanitized_probability_delta,
    )
    reason_codes = _row_reason_codes(
        candidate,
        config=config,
        cost_to_delta_ratio=cost_to_delta_ratio,
    )
    return ResearchExpectedValueSanityGateRow(
        research_reference=candidate.candidate_reference,
        observed_at=candidate.observed_at,
        sanitized_probability_delta=candidate.sanitized_probability_delta,
        total_cost_probability=candidate.total_cost_probability,
        cost_to_delta_ratio=cost_to_delta_ratio,
        evidence_quality_score=candidate.evidence_quality_score,
        liquidity_summary_score=candidate.liquidity_summary_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    candidate: ResearchExpectedValueSanityGateCandidate,
    *,
    config: ResearchExpectedValueSanityGateConfig,
    cost_to_delta_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(candidate.reason_codes)
    if candidate.sanitized_probability_delta < config.min_watch_probability_delta:
        reason_codes.append("probability_delta_below_watch")
    elif candidate.sanitized_probability_delta < config.min_pass_probability_delta:
        reason_codes.append("probability_delta_below_pass")

    if cost_to_delta_ratio >= config.block_cost_to_delta_ratio:
        reason_codes.append("cost_ratio_at_or_above_block")
    elif cost_to_delta_ratio >= config.watch_cost_to_delta_ratio:
        reason_codes.append("cost_ratio_at_or_above_watch")

    if candidate.evidence_quality_score < config.min_watch_evidence_quality:
        reason_codes.append("evidence_quality_below_watch")
    elif candidate.evidence_quality_score < config.min_pass_evidence_quality:
        reason_codes.append("evidence_quality_below_pass")

    if candidate.liquidity_summary_score < config.min_watch_liquidity_summary:
        reason_codes.append("liquidity_summary_below_watch")
    elif candidate.liquidity_summary_score < config.min_pass_liquidity_summary:
        reason_codes.append("liquidity_summary_below_pass")

    if not any(
        reason in _BLOCK_ROW_REASONS or reason in _WATCH_ROW_REASONS
        for reason in reason_codes
    ):
        reason_codes.append(_PASS_REASON)
    return tuple(sorted(dict.fromkeys(reason_codes)))


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[ResearchExpectedValueSanityGateCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchExpectedValueSanityGateCandidate:
            raise ValueError(
                "candidates must contain ResearchExpectedValueSanityGateCandidate values",
            )
        _require_hard_flags("candidate", item)
        if item.candidate_reference in seen:
            raise ValueError("duplicate research reference")
        seen.add(item.candidate_reference)
    return tuple(sorted(items, key=lambda item: item.candidate_reference))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchExpectedValueSanityGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchExpectedValueSanityGateRow:
            raise ValueError("rows must contain ResearchExpectedValueSanityGateRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len({row.research_reference for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: ResearchExpectedValueSanityGateRow) -> None:
    if row.cost_to_delta_ratio != _quantize_decimal(
        row.total_cost_probability / row.sanitized_probability_delta,
    ):
        raise ValueError("cost_to_delta_ratio must match cost and delta")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and _PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")


def _validate_report(report: ResearchExpectedValueSanityGateReport) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count_decimal(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_cost_to_delta_ratio != _max_decimal(
        row.cost_to_delta_ratio for row in rows
    ):
        raise ValueError("max_cost_to_delta_ratio must match rows")
    if report.min_evidence_quality_score != _min_decimal(
        row.evidence_quality_score for row in rows
    ):
        raise ValueError("min_evidence_quality_score must match rows")
    if report.min_liquidity_summary_score != _min_decimal(
        row.liquidity_summary_score for row in rows
    ):
        raise ValueError("min_liquidity_summary_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_ROW_REASONS for reason in reason_codes):
        return "block"
    if any(reason in _WATCH_ROW_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchExpectedValueSanityGateRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchExpectedValueSanityGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append(_BLOCK_PRESENT_REASON)
    if any(row.status == "watch" for row in rows):
        reason_codes.append(_WATCH_PRESENT_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return tuple(reason_codes)


def _row_sort_key(
    row: ResearchExpectedValueSanityGateRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.cost_to_delta_ratio,
        -row.sanitized_probability_delta,
        row.research_reference,
    )


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return min(items)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANT)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_positive_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_probability_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_non_negative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    _require_text(field_name, value)
    assert type(value) is str
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for item in value:
        _require_public_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
    return value


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in _REPORT_REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        reason_index = _REPORT_REASON_PRIORITY.index(reason_code)
        if reason_index <= previous_index:
            raise ValueError("reason_codes must use priority sequence")
        seen.add(reason_code)
        previous_index = reason_index
    return reason_codes


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _redacted_reference(prefix: str, value: str) -> str:
    digest = sha256(f"{prefix}\0{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _require_redacted_reference(field_name: str, value: object) -> None:
    prefix = "research_ref_"
    if type(value) is not str or not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    suffix = value[len(prefix) :]
    if len(suffix) != 16 or any(character not in _HEX_CHARS for character in suffix):
        raise ValueError(f"{field_name} must be redacted")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be an exact Decimal")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, str) or type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    for key in _REPORT_PAYLOAD_KEYS:
        if key not in payload:
            raise ValueError(f"missing public field in payload: {key}")
    _require_public_string("config_version", payload["config_version"])
    if payload["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_datetime_string("generated_at", payload["generated_at"])
    for field_name in _DECIMAL_REPORT_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _validate_public_string_list("reason_codes", payload["reason_codes"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(payload["rows"]):
        _validate_public_row_payload(f"rows[{index}]", row)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if payload["derived_validation_digest"] != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_row_payload(label: str, row: object) -> None:
    if type(row) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _reject_unknown_keys(label, row, _ROW_PAYLOAD_KEYS)
    for key in _ROW_PAYLOAD_KEYS:
        if key not in row:
            raise ValueError(f"missing public field in {label}: {key}")
    _require_public_string(f"{label}.research_reference", row["research_reference"])
    _require_redacted_reference(f"{label}.research_reference", row["research_reference"])
    _require_datetime_string(f"{label}.observed_at", row["observed_at"])
    for field_name in _DECIMAL_ROW_FIELDS:
        _require_decimal_string(f"{label}.{field_name}", row[field_name])
    _require_status(f"{label}.status", row["status"])
    _validate_public_string_list(f"{label}.reason_codes", row["reason_codes"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if row[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _validate_public_string_list(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_public_string(field_name, item)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite() or decimal_value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-place Decimal-derived string")
    return decimal_value


def _require_datetime_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _reject_unknown_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    for key in payload:
        if key not in allowed_keys:
            raise ValueError(f"unsafe public field in {label}: {key}")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in _field_deny_fragments()):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in _value_deny_fragments()):
        raise ValueError(f"unsafe public value in {label}")


def _field_deny_fragments() -> tuple[str, ...]:
    return tuple(
        _word(value)
        for value in (
            "63616e6469646174655f6964",
            "7261775f63616e646964617465",
            "6d61726b65745f6964",
            "6d61726b65745f736c7567",
            "7175657374696f6e",
            "736f757263655f726566",
            "736f757263655f75726c",
            "736f757263655f74657874",
            "64736e",
            "7461626c65",
            "746f6b656e",
            "77616c6c6574",
            "61757468",
            "6f72646572",
            "7472616465",
            "706f736974696f6e",
            "627579",
            "73656c6c",
            "7265636f6d6d656e64",
        )
    )


def _value_deny_fragments() -> tuple[str, ...]:
    return tuple(
        _word(value)
        for value in (
            "63616e6469646174655f6964",
            "7261775f63616e646964617465",
            "6d61726b65745f6964",
            "6d61726b65745f736c7567",
            "7175657374696f6e",
            "736f757263655f726566",
            "736f757263655f75726c",
            "736f757263655f74657874",
            "687474703a2f2f",
            "68747470733a2f2f",
            "64736e",
            "7461626c653a",
            "746f6b656e",
            "77616c6c6574",
            "61757468",
            "6f72646572",
            "7472616465",
            "706f736974696f6e",
            "627579",
            "73656c6c",
            "7265636f6d6d656e64",
        )
    )


def _word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("utf-8")


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _report_derived_validation_digest(
    report: ResearchExpectedValueSanityGateReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


__all__ = (
    "CONFIG_VERSION",
    "ResearchExpectedValueSanityGateCandidate",
    "ResearchExpectedValueSanityGateConfig",
    "ResearchExpectedValueSanityGateReport",
    "ResearchExpectedValueSanityGateRow",
    "build_research_expected_value_sanity_gate_report",
    "research_expected_value_sanity_gate_payload",
)
