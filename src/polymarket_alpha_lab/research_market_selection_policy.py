"""Pure report-only market research selection policy.

The module turns caller-supplied, sanitized research selection inputs into
pass/watch/block research priorities. It is deterministic, side-effect free,
and does not produce trading advice or execution instructions.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import re
from typing import Any


CONFIG_VERSION = "research-selection-policy-v0"
DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_PRIORITIES = frozenset(("pass", "watch", "block"))
_PRIORITY_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")
_EVENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_REDACTED_REFERENCE_RE = re.compile(r"^selection_ref_[0-9a-f]{64}$")

_PASS_REASON = "selection_policy_pass"
_EMPTY_REASON = "selection_policy_empty"
_BLOCK_PRESENT_REASON = "selection_policy_block_present"
_WATCH_PRESENT_REASON = "selection_policy_watch_present"
_REPORT_REASON_CODES = (
    _BLOCK_PRESENT_REASON,
    _WATCH_PRESENT_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_ROW_REASONS = frozenset(
    (
        "unsupported_event_type_block",
        "evidence_quality_below_watch",
        "cost_ratio_at_or_above_block",
        "rule_clarity_below_watch",
        "team_coverage_below_watch",
    ),
)
_WATCH_ROW_REASONS = frozenset(
    (
        "evidence_quality_below_pass",
        "cost_ratio_above_pass",
        "rule_clarity_below_pass",
        "team_coverage_below_pass",
    ),
)
_ROW_REASON_CODES = tuple(
    sorted((*_BLOCK_ROW_REASONS, *_WATCH_ROW_REASONS, _PASS_REASON)),
)

_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_selection_score",
        "max_research_cost_ratio",
        "min_evidence_quality_score",
        "min_rule_clarity_score",
        "min_team_coverage_score",
        "overall_research_priority",
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
        "selection_reference",
        "event_type",
        "event_type_support_score",
        "evidence_quality_score",
        "research_cost_ratio",
        "rule_clarity_score",
        "team_coverage_score",
        "selection_score",
        "research_priority",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_DECIMAL_REPORT_FIELDS = frozenset(
    (
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_selection_score",
        "max_research_cost_ratio",
        "min_evidence_quality_score",
        "min_rule_clarity_score",
        "min_team_coverage_score",
    ),
)
_DECIMAL_ROW_FIELDS = frozenset(
    (
        "event_type_support_score",
        "evidence_quality_score",
        "research_cost_ratio",
        "rule_clarity_score",
        "team_coverage_score",
        "selection_score",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "http://",
    "https://",
    "://",
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
class ResearchMarketSelectionPolicyConfig(_FinalPublicDataclass):
    config_version: str = CONFIG_VERSION
    min_pass_evidence_quality_score: Decimal = Decimal("0.750000")
    min_watch_evidence_quality_score: Decimal = Decimal("0.500000")
    pass_research_cost_ratio: Decimal = Decimal("0.250000")
    block_research_cost_ratio: Decimal = Decimal("0.500000")
    min_pass_rule_clarity_score: Decimal = Decimal("0.700000")
    min_watch_rule_clarity_score: Decimal = Decimal("0.450000")
    min_pass_team_coverage_score: Decimal = Decimal("0.650000")
    min_watch_team_coverage_score: Decimal = Decimal("0.350000")
    supported_event_types: tuple[str, ...] = (
        "crypto_protocol",
        "macro_release",
        "policy_process",
        "sports_status",
        "weather_event",
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSelectionPolicyConfig, "config")
        _require_public_text("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_evidence_quality_score",
            "min_watch_evidence_quality_score",
            "pass_research_cost_ratio",
            "block_research_cost_ratio",
            "min_pass_rule_clarity_score",
            "min_watch_rule_clarity_score",
            "min_pass_team_coverage_score",
            "min_watch_team_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_evidence_quality_score > self.min_pass_evidence_quality_score:
            raise ValueError(
                "min_watch_evidence_quality_score must be <= pass threshold",
            )
        if self.pass_research_cost_ratio > self.block_research_cost_ratio:
            raise ValueError("pass_research_cost_ratio must be <= block threshold")
        if self.min_watch_rule_clarity_score > self.min_pass_rule_clarity_score:
            raise ValueError("min_watch_rule_clarity_score must be <= pass threshold")
        if self.min_watch_team_coverage_score > self.min_pass_team_coverage_score:
            raise ValueError("min_watch_team_coverage_score must be <= pass threshold")
        object.__setattr__(
            self,
            "supported_event_types",
            _normalize_supported_event_types(self.supported_event_types),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchMarketSelectionPolicyInput(_FinalPublicDataclass):
    private_selection_key: str
    event_type: str
    evidence_quality_score: Decimal
    research_cost_ratio: Decimal
    rule_clarity_score: Decimal
    team_coverage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSelectionPolicyInput, "selection input")
        private_key = _require_private_text("private_selection_key", self.private_selection_key)
        object.__setattr__(
            self,
            "private_selection_key",
            _redacted_reference(private_key),
        )
        object.__setattr__(
            self,
            "event_type",
            _require_event_type("event_type", self.event_type),
        )
        for field_name in (
            "evidence_quality_score",
            "research_cost_ratio",
            "rule_clarity_score",
            "team_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("selection input", self)


@dataclass(frozen=True)
class ResearchMarketSelectionPolicyRow(_FinalPublicDataclass):
    selection_reference: str
    event_type: str
    event_type_support_score: Decimal
    evidence_quality_score: Decimal
    research_cost_ratio: Decimal
    rule_clarity_score: Decimal
    team_coverage_score: Decimal
    selection_score: Decimal
    research_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSelectionPolicyRow, "row")
        _require_redacted_reference("selection_reference", self.selection_reference)
        object.__setattr__(
            self,
            "event_type",
            _require_event_type("event_type", self.event_type),
        )
        for field_name in (
            "event_type_support_score",
            "evidence_quality_score",
            "research_cost_ratio",
            "rule_clarity_score",
            "team_coverage_score",
            "selection_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_priority("research_priority", self.research_priority)
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchMarketSelectionPolicyReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_selection_score: Decimal
    max_research_cost_ratio: Decimal
    min_evidence_quality_score: Decimal
    min_rule_clarity_score: Decimal
    min_team_coverage_score: Decimal
    overall_research_priority: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSelectionPolicyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSelectionPolicyReport, "report")
        _require_hard_flags("report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "item_count",
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
            "average_selection_score",
            "max_research_cost_ratio",
            "min_evidence_quality_score",
            "min_rule_clarity_score",
            "min_team_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_priority("overall_research_priority", self.overall_research_priority)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_public_surface("report", self)
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report values")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_market_selection_policy_report(
    selections: Iterable[object],
    *,
    config: ResearchMarketSelectionPolicyConfig,
    generated_at: datetime,
) -> ResearchMarketSelectionPolicyReport:
    if type(config) is not ResearchMarketSelectionPolicyConfig:
        raise ValueError("config must be a ResearchMarketSelectionPolicyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_selection(selection, config=config)
                for selection in _normalize_selections(selections)
            ),
            key=_row_sort_key,
        ),
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "item_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(
            sum(1 for row in rows if row.research_priority == "pass"),
        ),
        "watch_count": _count_decimal(
            sum(1 for row in rows if row.research_priority == "watch"),
        ),
        "block_count": _count_decimal(
            sum(1 for row in rows if row.research_priority == "block"),
        ),
        "average_selection_score": _average_decimal(
            row.selection_score for row in rows
        ),
        "max_research_cost_ratio": _max_decimal(
            row.research_cost_ratio for row in rows
        ),
        "min_evidence_quality_score": _min_decimal(
            row.evidence_quality_score for row in rows
        ),
        "min_rule_clarity_score": _min_decimal(row.rule_clarity_score for row in rows),
        "min_team_coverage_score": _min_decimal(row.team_coverage_score for row in rows),
        "overall_research_priority": _report_priority(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketSelectionPolicyReport(
        **values,
        derived_validation_digest=_digest_payload(_json_ready(values)),
    )


def research_market_selection_policy_payload(
    report: ResearchMarketSelectionPolicyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketSelectionPolicyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketSelectionPolicyReport")
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


def _row_from_selection(
    selection: ResearchMarketSelectionPolicyInput,
    *,
    config: ResearchMarketSelectionPolicyConfig,
) -> ResearchMarketSelectionPolicyRow:
    event_type_support_score = (
        ONE if selection.event_type in config.supported_event_types else ZERO
    )
    selection_score = _quantize_decimal(
        (
            event_type_support_score
            + selection.evidence_quality_score
            + (ONE - selection.research_cost_ratio)
            + selection.rule_clarity_score
            + selection.team_coverage_score
        )
        / Decimal("5.000000"),
    )
    reason_codes = _row_reason_codes(
        selection,
        config=config,
        event_type_support_score=event_type_support_score,
    )
    return ResearchMarketSelectionPolicyRow(
        selection_reference=selection.private_selection_key,
        event_type=selection.event_type,
        event_type_support_score=event_type_support_score,
        evidence_quality_score=selection.evidence_quality_score,
        research_cost_ratio=selection.research_cost_ratio,
        rule_clarity_score=selection.rule_clarity_score,
        team_coverage_score=selection.team_coverage_score,
        selection_score=selection_score,
        research_priority=_priority_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    selection: ResearchMarketSelectionPolicyInput,
    *,
    config: ResearchMarketSelectionPolicyConfig,
    event_type_support_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if event_type_support_score == ZERO:
        reason_codes.append("unsupported_event_type_block")

    if selection.evidence_quality_score < config.min_watch_evidence_quality_score:
        reason_codes.append("evidence_quality_below_watch")
    elif selection.evidence_quality_score < config.min_pass_evidence_quality_score:
        reason_codes.append("evidence_quality_below_pass")

    if selection.research_cost_ratio >= config.block_research_cost_ratio:
        reason_codes.append("cost_ratio_at_or_above_block")
    elif selection.research_cost_ratio > config.pass_research_cost_ratio:
        reason_codes.append("cost_ratio_above_pass")

    if selection.rule_clarity_score < config.min_watch_rule_clarity_score:
        reason_codes.append("rule_clarity_below_watch")
    elif selection.rule_clarity_score < config.min_pass_rule_clarity_score:
        reason_codes.append("rule_clarity_below_pass")

    if selection.team_coverage_score < config.min_watch_team_coverage_score:
        reason_codes.append("team_coverage_below_watch")
    elif selection.team_coverage_score < config.min_pass_team_coverage_score:
        reason_codes.append("team_coverage_below_pass")

    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return tuple(sorted(dict.fromkeys(reason_codes)))


def _normalize_selections(
    selections: Iterable[object],
) -> tuple[ResearchMarketSelectionPolicyInput, ...]:
    if isinstance(selections, (str, bytes)):
        raise ValueError("selections must be iterable")
    try:
        items = tuple(selections)
    except TypeError as exc:
        raise ValueError("selections must be iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchMarketSelectionPolicyInput:
            raise ValueError(
                "selections must contain ResearchMarketSelectionPolicyInput values",
            )
        _require_hard_flags("selection input", item)
        if item.private_selection_key in seen:
            raise ValueError("duplicate selection reference")
        seen.add(item.private_selection_key)
    return tuple(sorted(items, key=lambda item: item.private_selection_key))


def _normalize_rows(rows: object) -> tuple[ResearchMarketSelectionPolicyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketSelectionPolicyRow:
            raise ValueError("rows must contain ResearchMarketSelectionPolicyRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len({row.selection_reference for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: ResearchMarketSelectionPolicyRow) -> None:
    if row.event_type_support_score not in (ZERO, ONE):
        raise ValueError("event_type_support_score must be binary")
    expected_score = _quantize_decimal(
        (
            row.event_type_support_score
            + row.evidence_quality_score
            + (ONE - row.research_cost_ratio)
            + row.rule_clarity_score
            + row.team_coverage_score
        )
        / Decimal("5.000000"),
    )
    if row.selection_score != expected_score:
        raise ValueError("selection_score must match row metrics")
    if row.research_priority != _priority_from_reason_codes(row.reason_codes):
        raise ValueError("research_priority must match reason_codes")
    if row.research_priority == "pass" and row.reason_codes != (_PASS_REASON,):
        raise ValueError("pass rows must include only the pass reason")


def _validate_report(report: ResearchMarketSelectionPolicyReport) -> None:
    rows = report.rows
    if report.item_count != _count_decimal(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in rows if row.research_priority == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in rows if row.research_priority == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in rows if row.research_priority == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_selection_score != _average_decimal(
        row.selection_score for row in rows
    ):
        raise ValueError("average_selection_score must match rows")
    if report.max_research_cost_ratio != _max_decimal(
        row.research_cost_ratio for row in rows
    ):
        raise ValueError("max_research_cost_ratio must match rows")
    if report.min_evidence_quality_score != _min_decimal(
        row.evidence_quality_score for row in rows
    ):
        raise ValueError("min_evidence_quality_score must match rows")
    if report.min_rule_clarity_score != _min_decimal(
        row.rule_clarity_score for row in rows
    ):
        raise ValueError("min_rule_clarity_score must match rows")
    if report.min_team_coverage_score != _min_decimal(
        row.team_coverage_score for row in rows
    ):
        raise ValueError("min_team_coverage_score must match rows")
    if report.overall_research_priority != _report_priority(rows):
        raise ValueError("overall_research_priority must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _priority_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_ROW_REASONS for reason in reason_codes):
        return "block"
    if any(reason in _WATCH_ROW_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _report_priority(rows: tuple[ResearchMarketSelectionPolicyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.research_priority == "block" for row in rows):
        return "block"
    if any(row.research_priority == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchMarketSelectionPolicyRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.research_priority == "block" for row in rows):
        reason_codes.append(_BLOCK_PRESENT_REASON)
    if any(row.research_priority == "watch" for row in rows):
        reason_codes.append(_WATCH_PRESENT_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return tuple(reason_codes)


def _row_sort_key(
    row: ResearchMarketSelectionPolicyRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        _PRIORITY_WEIGHT[row.research_priority],
        row.selection_score,
        -row.research_cost_ratio,
        row.selection_reference,
    )


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    return min(tuple(values), default=ZERO)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize_decimal(sum(items, ZERO) / _count_decimal(len(items)))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a non-negative integer")
    return Decimal(value).quantize(DECIMAL_QUANT)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_public_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    _reject_unsafe_public_text(name, normalized)
    return normalized


def _require_event_type(name: str, value: object) -> str:
    normalized = _require_public_text(name, value)
    if _EVENT_TYPE_RE.fullmatch(normalized) is None:
        raise ValueError(f"{name} must be a sanitized snake_case event type")
    return normalized


def _normalize_supported_event_types(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("supported_event_types must be a tuple")
    normalized = tuple(_require_event_type("supported_event_types", item) for item in value)
    if not normalized:
        raise ValueError("supported_event_types must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("supported_event_types must be unique")
    return tuple(sorted(normalized))


def _require_redacted_reference(name: str, value: object) -> str:
    if type(value) is not str or _REDACTED_REFERENCE_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a redacted selection reference")
    return value


def _require_priority(name: str, value: object) -> str:
    if type(value) is not str or value not in _PRIORITIES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_row_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of strings") from exc
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _ROW_REASON_CODES:
            raise ValueError(f"{name} must contain known reason codes")
        _reject_unsafe_public_text(name, reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{name} must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return normalized


def _require_report_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of strings") from exc
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REPORT_REASON_CODES:
            raise ValueError(f"{name} must contain known reason codes")
        _reject_unsafe_public_text(name, reason_code)
    expected = tuple(reason for reason in _REPORT_REASON_CODES if reason in normalized)
    if normalized != expected:
        raise ValueError(f"{name} must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return normalized


def _require_probability_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_canonical_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_canonical_decimal(name, value)
    if decimal_value < ZERO or decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a non-negative whole Decimal")
    return decimal_value


def _require_canonical_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent != DECIMAL_QUANT.as_tuple().exponent:
        raise ValueError(f"{name} must use 6 decimal places")
    if value != value.quantize(DECIMAL_QUANT):
        raise ValueError(f"{name} must be canonical")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _redacted_reference(value: str) -> str:
    return f"selection_ref_{sha256(value.encode('utf-8')).hexdigest()}"


def _require_digest(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in _HEX_CHARS for char in value)
    ):
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _reject_unsafe_public_surface(name: str, value: object) -> None:
    _walk_public_surface(name, value)


def _walk_public_surface(name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_field(field.name)
            _walk_public_surface(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{name} public field names must be strings")
            _reject_unsafe_public_field(key)
            _walk_public_surface(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _walk_public_surface(name, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(name, value)


def _reject_unsafe_public_field(name: str) -> None:
    lowered = name.casefold()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public field: {name}")


def _reject_unsafe_public_text(name: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value for {name}")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric payload values must be decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if frozenset(payload) != _REPORT_PAYLOAD_KEYS:
        raise ValueError("report payload has unexpected fields")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in _DECIMAL_REPORT_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_priority("overall_research_priority", payload["overall_research_priority"])
    _require_report_reason_codes("reason_codes", payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        if frozenset(row) != _ROW_PAYLOAD_KEYS:
            raise ValueError("row payload has unexpected fields")
        _require_redacted_reference("selection_reference", row["selection_reference"])
        _require_event_type("event_type", row["event_type"])
        for field_name in _DECIMAL_ROW_FIELDS:
            _require_decimal_string(field_name, row[field_name])
        _require_priority("research_priority", row["research_priority"])
        _require_row_reason_codes("row reason_codes", row["reason_codes"])
        _require_hard_flags("row payload", _DictFlags(row))
    expected_digest = _digest_payload(
        {
            key: value
            for key, value in payload.items()
            if key != "derived_validation_digest"
        },
    )
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match payload")


def _require_decimal_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    _require_canonical_decimal(name, Decimal(value))
    if Decimal(value) < ZERO:
        raise ValueError(f"{name} must be non-negative")
    return value


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _report_derived_validation_digest(
    report: ResearchMarketSelectionPolicyReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload = {key: value for key, value in payload.items() if key != "derived_validation_digest"}
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


__all__ = (
    "CONFIG_VERSION",
    "ResearchMarketSelectionPolicyConfig",
    "ResearchMarketSelectionPolicyInput",
    "ResearchMarketSelectionPolicyReport",
    "ResearchMarketSelectionPolicyRow",
    "build_research_market_selection_policy_report",
    "research_market_selection_policy_payload",
)
