from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import hmac
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_EVENT_MEMORY_AUTHORITY_CLAIM_SCORECARD_CONFIG_VERSION = (
    "research_event_memory_authority_claim_scorecard_report.v1"
)
NO_INPUTS_REASON = "research_event_memory_authority_claim_scorecard_no_inputs"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX_PLACES = Decimal("0.000001")

_PASS = "pass"
_WATCH = "watch"
_BLOCK = "block"
_STATUSES = frozenset({_PASS, _WATCH, _BLOCK})
_STATUS_RANK = {_BLOCK: 0, _WATCH: 1, _PASS: 2}

_CLAIM_SCORE_WEIGHTS = (
    ("authority_claim_score", Decimal("0.714286")),
    ("parser_confidence_score", Decimal("0.100000")),
    ("memory_match_score", Decimal("0.100000")),
    ("source_recency_score", Decimal("0.085714")),
)

_UNSAFE_PUBLIC_STRING_FRAGMENTS = (
    "://",
    "www.",
    "postgres",
    "mysql",
    "sqlite",
    "dsn=",
    "token=",
    "bearer ",
    "raw text",
    "\n",
    "\r",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} must be used exactly")


@dataclass(frozen=True)
class ResearchEventMemoryAuthorityClaimScorecardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_MEMORY_AUTHORITY_CLAIM_SCORECARD_CONFIG_VERSION
    )
    minimum_authority_score_pass: Decimal = Decimal("0.700000")
    minimum_authority_score_watch: Decimal = Decimal("0.500000")
    minimum_parser_confidence_pass: Decimal = Decimal("0.700000")
    minimum_parser_confidence_watch: Decimal = Decimal("0.500000")
    minimum_memory_match_pass: Decimal = Decimal("0.600000")
    minimum_source_recency_pass: Decimal = Decimal("0.500000")
    maximum_conflict_ratio_watch: Decimal = Decimal("0.250000")
    maximum_conflict_ratio_block: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventMemoryAuthorityClaimScorecardConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "minimum_authority_score_pass",
            "minimum_authority_score_watch",
            "minimum_parser_confidence_pass",
            "minimum_parser_confidence_watch",
            "minimum_memory_match_pass",
            "minimum_source_recency_pass",
            "maximum_conflict_ratio_watch",
            "maximum_conflict_ratio_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "minimum_authority_score_pass",
            self.minimum_authority_score_pass,
            self.minimum_authority_score_watch,
        )
        _require_at_least(
            "minimum_parser_confidence_pass",
            self.minimum_parser_confidence_pass,
            self.minimum_parser_confidence_watch,
        )
        _require_at_least(
            "maximum_conflict_ratio_block",
            self.maximum_conflict_ratio_block,
            self.maximum_conflict_ratio_watch,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventMemoryAuthorityClaimScorecardObservation(_FinalPublicDataclass):
    event_key: str
    claim_key: str
    authority_key: str
    event_family: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    authority_source_count: Decimal
    conflicting_source_count: Decimal
    memory_match_score: Decimal
    authority_claim_score: Decimal
    parser_confidence_score: Decimal
    source_recency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventMemoryAuthorityClaimScorecardObservation,
            "observation",
        )
        for field_name in ("event_key", "claim_key", "authority_key", "event_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "authority_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_match_score",
            "authority_claim_score",
            "parser_confidence_score",
            "source_recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_source_count",
            "authority_source_count",
            "conflicting_source_count",
        ):
            if getattr(self, field_name) > self.source_count:
                raise ValueError(f"{field_name} must not exceed source_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventMemoryAuthorityClaimScorecardRow(_FinalPublicDataclass):
    event_key: str
    claim_key: str
    authority_key: str
    event_family: str
    status: str
    observed_at: datetime
    event_age_seconds: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    authority_source_count: Decimal
    conflicting_source_count: Decimal
    conflict_ratio: Decimal
    memory_match_score: Decimal
    authority_claim_score: Decimal
    parser_confidence_score: Decimal
    source_recency_score: Decimal
    claim_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventMemoryAuthorityClaimScorecardRow, "row")
        for field_name in ("event_key", "claim_key", "authority_key", "event_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "event_age_seconds",
            "source_count",
            "independent_source_count",
            "authority_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "conflict_ratio",
            "memory_match_score",
            "authority_claim_score",
            "parser_confidence_score",
            "source_recency_score",
            "claim_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventMemoryAuthorityClaimScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    independent_source_count: Decimal
    authority_source_count: Decimal
    conflicting_source_count: Decimal
    mean_claim_score: Decimal
    max_conflict_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount, ...]
    rows: tuple[ResearchEventMemoryAuthorityClaimScorecardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventMemoryAuthorityClaimScorecardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "independent_source_count",
            "authority_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_claim_score", "max_conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
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
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchEventMemoryAuthorityClaimScorecardConfig,
    ResearchEventMemoryAuthorityClaimScorecardObservation,
    ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount,
    ResearchEventMemoryAuthorityClaimScorecardReport,
    ResearchEventMemoryAuthorityClaimScorecardRow,
)


def build_research_event_memory_authority_claim_scorecard_report(
    observations: Iterable[ResearchEventMemoryAuthorityClaimScorecardObservation],
    *,
    config: ResearchEventMemoryAuthorityClaimScorecardConfig,
    generated_at: datetime,
) -> ResearchEventMemoryAuthorityClaimScorecardReport:
    if type(config) is not ResearchEventMemoryAuthorityClaimScorecardConfig:
        raise TypeError(
            "config must be exactly ResearchEventMemoryAuthorityClaimScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _scorecard_row(row, config=config, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventMemoryAuthorityClaimScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_count=_status_count(rows, _PASS),
        watch_count=_status_count(rows, _WATCH),
        block_count=_status_count(rows, _BLOCK),
        independent_source_count=_sum_decimal(
            row.independent_source_count for row in rows
        ),
        authority_source_count=_sum_decimal(row.authority_source_count for row in rows),
        conflicting_source_count=_sum_decimal(
            row.conflicting_source_count for row in rows
        ),
        mean_claim_score=_mean(tuple(row.claim_score for row in rows)),
        max_conflict_ratio=_max_decimal(tuple(row.conflict_ratio for row in rows)),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_event_memory_authority_claim_scorecard_payload(
    report: ResearchEventMemoryAuthorityClaimScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventMemoryAuthorityClaimScorecardReport:
        raise TypeError(
            "report must be exactly ResearchEventMemoryAuthorityClaimScorecardReport",
        )
    _require_payload_safe_value("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_event_memory_authority_claim_scorecard_sha256_digest(
    report: ResearchEventMemoryAuthorityClaimScorecardReport,
) -> str:
    payload = research_event_memory_authority_claim_scorecard_payload(report)
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def validate_research_event_memory_authority_claim_scorecard_digest(
    report: ResearchEventMemoryAuthorityClaimScorecardReport,
    expected_digest: str,
) -> bool:
    if type(expected_digest) is not str:
        raise ValueError("expected sha256 digest must be a string")
    if len(expected_digest) != 64 or any(
        character not in "0123456789abcdef" for character in expected_digest
    ):
        raise ValueError("expected sha256 digest must be lowercase hex")
    actual_digest = research_event_memory_authority_claim_scorecard_sha256_digest(report)
    return hmac.compare_digest(actual_digest, expected_digest)


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


def _scorecard_row(
    row: ResearchEventMemoryAuthorityClaimScorecardObservation,
    *,
    config: ResearchEventMemoryAuthorityClaimScorecardConfig,
    generated_at: datetime,
) -> ResearchEventMemoryAuthorityClaimScorecardRow:
    event_age_seconds = _age_seconds(row.observed_at, generated_at)
    conflict_ratio = _ratio(row.conflicting_source_count, row.source_count)
    claim_score = _claim_score(row, conflict_ratio=conflict_ratio)
    reason_codes = _row_reason_codes(row, config=config, conflict_ratio=conflict_ratio)
    return ResearchEventMemoryAuthorityClaimScorecardRow(
        event_key=row.event_key,
        claim_key=row.claim_key,
        authority_key=row.authority_key,
        event_family=row.event_family,
        status=_row_status(reason_codes),
        observed_at=row.observed_at,
        event_age_seconds=event_age_seconds,
        source_count=row.source_count,
        independent_source_count=row.independent_source_count,
        authority_source_count=row.authority_source_count,
        conflicting_source_count=row.conflicting_source_count,
        conflict_ratio=conflict_ratio,
        memory_match_score=row.memory_match_score,
        authority_claim_score=row.authority_claim_score,
        parser_confidence_score=row.parser_confidence_score,
        source_recency_score=row.source_recency_score,
        claim_score=claim_score,
        reason_codes=reason_codes,
    )


def _claim_score(
    row: ResearchEventMemoryAuthorityClaimScorecardObservation,
    *,
    conflict_ratio: Decimal,
) -> Decimal:
    weighted_score = sum(
        getattr(row, field_name) * weight
        for field_name, weight in _CLAIM_SCORE_WEIGHTS
    )
    conflict_adjusted_score = weighted_score * (ONE - (conflict_ratio / Decimal("2.000000")))
    return _clamp_unit(conflict_adjusted_score)


def _row_reason_codes(
    row: ResearchEventMemoryAuthorityClaimScorecardObservation,
    *,
    config: ResearchEventMemoryAuthorityClaimScorecardConfig,
    conflict_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.source_count == ZERO:
        reason_codes.append("source_support_missing_block")
    if row.independent_source_count == ZERO:
        reason_codes.append("independent_support_missing_block")
    if row.authority_claim_score < config.minimum_authority_score_watch:
        reason_codes.append("authority_claim_score_block")
    elif row.authority_claim_score < config.minimum_authority_score_pass:
        reason_codes.append("authority_claim_score_watch")
    if row.parser_confidence_score < config.minimum_parser_confidence_watch:
        reason_codes.append("parser_confidence_block")
    elif row.parser_confidence_score < config.minimum_parser_confidence_pass:
        reason_codes.append("parser_confidence_watch")
    if row.memory_match_score < config.minimum_memory_match_pass:
        reason_codes.append("memory_match_watch")
    if row.source_recency_score < config.minimum_source_recency_pass:
        reason_codes.append("source_recency_watch")
    if conflict_ratio >= config.maximum_conflict_ratio_block:
        reason_codes.append("conflict_ratio_block")
    elif conflict_ratio >= config.maximum_conflict_ratio_watch:
        reason_codes.append("conflict_ratio_watch")
    if not reason_codes:
        reason_codes.append("authority_claim_supported")
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return _BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return _WATCH
    return _PASS


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return _BLOCK
    if any(status == _BLOCK for status in statuses):
        return _BLOCK
    if any(status == _WATCH for status in statuses):
        return _WATCH
    return _PASS


def _rollup_reason_codes(
    rows: tuple[ResearchEventMemoryAuthorityClaimScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"authority_claim_scorecard_{status}"]
    if status != _PASS:
        reason_codes.extend(
            sorted(
                {
                    reason_code
                    for row in rows
                    for reason_code in row.reason_codes
                    if reason_code != "authority_claim_supported"
                },
            ),
        )
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchEventMemoryAuthorityClaimScorecardRow, ...],
) -> tuple[ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    reason_codes = sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
        },
    )
    return tuple(
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _validate_report(report: ResearchEventMemoryAuthorityClaimScorecardReport) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(rows, _PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, _WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, _BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_observations(
    rows: Iterable[ResearchEventMemoryAuthorityClaimScorecardObservation],
) -> tuple[ResearchEventMemoryAuthorityClaimScorecardObservation, ...]:
    if isinstance(rows, (str, bytes)):
        raise TypeError("observations must be an iterable of observations")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventMemoryAuthorityClaimScorecardObservation:
            raise TypeError(
                "observations must contain "
                "ResearchEventMemoryAuthorityClaimScorecardObservation values",
            )
        _require_hard_flags("observation", row)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventMemoryAuthorityClaimScorecardRow, ...],
) -> tuple[ResearchEventMemoryAuthorityClaimScorecardRow, ...]:
    if type(rows) is not tuple:
        raise TypeError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventMemoryAuthorityClaimScorecardRow:
            raise TypeError("rows must contain scorecard rows")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount, ...],
) -> tuple[ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise TypeError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount:
            raise TypeError("reason_code_counts must contain reason code counts")
        _require_hard_flags("reason_code_count", row)
    if rows != tuple(sorted(rows, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use canonical sequence")
    return rows


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise TypeError("reason_codes must be a tuple")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    normalized = tuple(sorted(dict.fromkeys(reason_codes)))
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return normalized


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise TypeError("reason_codes must be a tuple")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    normalized = tuple(dict.fromkeys(reason_codes))
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    if normalized != reason_codes:
        raise ValueError("reason_codes must use canonical sequence")
    return normalized


def _row_sort_key(row: ResearchEventMemoryAuthorityClaimScorecardRow) -> tuple[int, str, str]:
    return (_STATUS_RANK[row.status], row.event_key, row.claim_key)


def _status_count(
    rows: tuple[ResearchEventMemoryAuthorityClaimScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(_sum_decimal(values) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(str(delta.total_seconds()))
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize(seconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_unit(numerator / denominator)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be a public string")
    if not value or value.strip() != value:
        raise ValueError(f"{label} must be a non-empty public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_STRING_FRAGMENTS):
        raise ValueError(f"{label} must not expose non-public material")
    return value


def _require_reason_code(label: str, value: object) -> str:
    _require_public_string(label, value)
    if type(value) is not str:
        raise TypeError(f"{label} must be a reason code")
    if not value.replace("_", "").isalnum() or value != value.lower():
        raise ValueError(f"{label} must be a canonical reason code")
    return value


def _require_status(label: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{label} must be pass, watch, or block")
    return value


def _require_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{label} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_decimal(label, value)
    if decimal_value < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return decimal_value


def _require_positive_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_decimal(label, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{label} must be positive")
    return decimal_value


def _require_unit_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(label, value)
    if decimal_value > ONE:
        raise ValueError(f"{label} must not exceed one")
    return decimal_value


def _require_at_least(label: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{label} must be at least its paired watch threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _as_utc(label: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES)


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("public payload contains unsupported value")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported public dataclass")
        _rebuild_public_dataclass(label, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is Decimal:
        _require_decimal(label, value)
        return
    if type(value) is datetime:
        _as_utc(label, value)
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
    raise ValueError(f"{label} contains unsupported public value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed public payload validation") from exc


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_string(f"{label}.key", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        _require_public_string(label, value)
