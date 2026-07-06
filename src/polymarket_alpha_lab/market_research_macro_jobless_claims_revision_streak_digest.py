"""Pure Phase 1 macro jobless claims revision streak digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from types import MappingProxyType
from typing import Any


DEFAULT_MACRO_JOBLESS_CLAIMS_REVISION_STREAK_DIGEST_CONFIG_VERSION = (
    "market-research-macro-jobless-claims-revision-streak-digest-v0"
)

INPUT_REASON_CODES = (
    "official_dol_release",
    "vendor_revision",
)
ROW_REASON_CODES = (
    "jobless_claims_revision_streak_blocked",
    "jobless_claims_revision_streak_watch",
    "jobless_claims_revision_streak_inline",
    "jobless_claims_initial_revision_blocked",
    "jobless_claims_initial_revision_watch",
    "jobless_claims_continuing_revision_blocked",
    "jobless_claims_continuing_revision_watch",
    "jobless_claims_same_direction_streak",
    "jobless_claims_upstream_revision_present",
)
REPORT_REASON_CODES = (
    "jobless_claims_revision_streak_blocked_present",
    "jobless_claims_revision_streak_watch_present",
    "jobless_claims_initial_revision_present",
    "jobless_claims_continuing_revision_present",
    "jobless_claims_same_direction_streak_present",
    "jobless_claims_upstream_revision_present",
    "jobless_claims_revision_streak_clear",
    "jobless_claims_revision_streak_digest_empty",
)
REVISION_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MACRO_JOBLESS_CLAIMS_REVISION_STREAK_DIGEST_CONFIG_VERSION",
    "MacroJoblessClaimsRevisionStreakDigestConfig",
    "MacroJoblessClaimsRevisionStreakObservation",
    "MacroJoblessClaimsRevisionStreakDigestRow",
    "MacroJoblessClaimsRevisionStreakReasonCodeCount",
    "MacroJoblessClaimsRevisionStreakDigestReport",
    "build_market_research_macro_jobless_claims_revision_streak_digest",
    "market_research_macro_jobless_claims_revision_streak_digest_payload",
)


@dataclass(frozen=True)
class MacroJoblessClaimsRevisionStreakDigestConfig:
    config_version: str = (
        DEFAULT_MACRO_JOBLESS_CLAIMS_REVISION_STREAK_DIGEST_CONFIG_VERSION
    )
    watch_initial_claims_revision: Decimal = Decimal("5000.000000")
    blocked_initial_claims_revision: Decimal = Decimal("15000.000000")
    watch_continuing_claims_revision: Decimal = Decimal("10000.000000")
    blocked_continuing_claims_revision: Decimal = Decimal("30000.000000")
    watch_revision_streak_weeks: Decimal = Decimal("3.000000")
    blocked_revision_streak_weeks: Decimal = Decimal("5.000000")
    same_direction_streak_weeks: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MacroJoblessClaimsRevisionStreakDigestConfig:
            raise TypeError(
                "MacroJoblessClaimsRevisionStreakDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoblessClaimsRevisionStreakDigestConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MACRO_JOBLESS_CLAIMS_REVISION_STREAK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "watch_initial_claims_revision",
            "blocked_initial_claims_revision",
            "watch_continuing_claims_revision",
            "blocked_continuing_claims_revision",
            "watch_revision_streak_weeks",
            "blocked_revision_streak_weeks",
            "same_direction_streak_weeks",
        ):
            object.__setattr__(self, name, _require_positive_decimal(name, getattr(self, name)))
        if self.watch_initial_claims_revision > self.blocked_initial_claims_revision:
            raise ValueError("watch_initial_claims_revision must not exceed blocked threshold")
        if self.watch_continuing_claims_revision > self.blocked_continuing_claims_revision:
            raise ValueError("watch_continuing_claims_revision must not exceed blocked threshold")
        if self.watch_revision_streak_weeks > self.blocked_revision_streak_weeks:
            raise ValueError("watch_revision_streak_weeks must not exceed blocked threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MacroJoblessClaimsRevisionStreakObservation:
    source_id: str
    release_id: str
    research_topic_key: str
    release_week: str
    initial_claims_revision: Decimal
    continuing_claims_revision: Decimal
    revision_streak_weeks: Decimal
    same_direction_revision_weeks: Decimal
    revised_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MacroJoblessClaimsRevisionStreakObservation:
            raise TypeError(
                "MacroJoblessClaimsRevisionStreakObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoblessClaimsRevisionStreakObservation, "observation")
        for name in ("source_id", "release_id", "research_topic_key", "release_week"):
            object.__setattr__(self, name, _require_canonical_string(name, getattr(self, name)))
        for name in ("initial_claims_revision", "continuing_claims_revision"):
            object.__setattr__(self, name, _require_decimal(name, getattr(self, name)))
        for name in ("revision_streak_weeks", "same_direction_revision_weeks"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "revised_at", _as_utc("revised_at", self.revised_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MacroJoblessClaimsRevisionStreakDigestRow:
    source_id: str
    release_id: str
    research_topic_key: str
    release_week: str
    initial_claims_revision: Decimal
    continuing_claims_revision: Decimal
    absolute_initial_claims_revision: Decimal
    absolute_continuing_claims_revision: Decimal
    revision_streak_weeks: Decimal
    same_direction_revision_weeks: Decimal
    revised_at: datetime
    revision_status: str
    revision_streak_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MacroJoblessClaimsRevisionStreakDigestRow:
            raise TypeError(
                "MacroJoblessClaimsRevisionStreakDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoblessClaimsRevisionStreakDigestRow, "row")
        for name in ("source_id", "release_id", "research_topic_key", "release_week"):
            object.__setattr__(self, name, _require_canonical_string(name, getattr(self, name)))
        for name in ("initial_claims_revision", "continuing_claims_revision"):
            object.__setattr__(self, name, _require_decimal(name, getattr(self, name)))
        for name in (
            "absolute_initial_claims_revision",
            "absolute_continuing_claims_revision",
            "revision_streak_weeks",
            "same_direction_revision_weeks",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "revision_streak_pressure_score",
            _require_ratio("revision_streak_pressure_score", self.revision_streak_pressure_score),
        )
        object.__setattr__(self, "revised_at", _as_utc("revised_at", self.revised_at))
        _require_member("revision_status", self.revision_status, REVISION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MacroJoblessClaimsRevisionStreakReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MacroJoblessClaimsRevisionStreakReasonCodeCount:
            raise TypeError(
                "MacroJoblessClaimsRevisionStreakReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MacroJoblessClaimsRevisionStreakReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MacroJoblessClaimsRevisionStreakDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    revision_streak_count: Decimal
    initial_revision_count: Decimal
    continuing_revision_count: Decimal
    same_direction_streak_count: Decimal
    max_absolute_initial_claims_revision: Decimal
    average_absolute_initial_claims_revision: Decimal
    max_revision_streak_weeks: Decimal
    max_revision_streak_pressure_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...]
    reason_code_counts: tuple[MacroJoblessClaimsRevisionStreakReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MacroJoblessClaimsRevisionStreakDigestReport:
            raise TypeError(
                "MacroJoblessClaimsRevisionStreakDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoblessClaimsRevisionStreakDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MACRO_JOBLESS_CLAIMS_REVISION_STREAK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "revision_streak_count",
            "initial_revision_count",
            "continuing_revision_count",
            "same_direction_streak_count",
            "max_absolute_initial_claims_revision",
            "average_absolute_initial_claims_revision",
            "max_revision_streak_weeks",
            "max_revision_streak_pressure_score",
        ):
            object.__setattr__(self, name, _require_nonnegative_decimal(name, getattr(self, name)))
        _require_member("digest_status", self.digest_status, REVISION_STATUSES)
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_canonical_string("recommended_next_step", self.recommended_next_step),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_macro_jobless_claims_revision_streak_digest(
    observations: object,
    *,
    config: MacroJoblessClaimsRevisionStreakDigestConfig,
    generated_at: datetime,
) -> MacroJoblessClaimsRevisionStreakDigestReport:
    if type(config) is not MacroJoblessClaimsRevisionStreakDigestConfig:
        raise ValueError(
            "config must be exactly MacroJoblessClaimsRevisionStreakDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    for observation in normalized:
        if observation.revised_at > generated_at_utc:
            raise ValueError("revised_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_observation(observation, config=config) for observation in normalized),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return MacroJoblessClaimsRevisionStreakDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        revision_streak_count=_report_reason_row_count(
            "jobless_claims_revision_streak_watch_present",
            rows,
        )
        + _report_reason_row_count(
            "jobless_claims_revision_streak_blocked_present",
            rows,
        ),
        initial_revision_count=_report_reason_row_count(
            "jobless_claims_initial_revision_present",
            rows,
        ),
        continuing_revision_count=_report_reason_row_count(
            "jobless_claims_continuing_revision_present",
            rows,
        ),
        same_direction_streak_count=_report_reason_row_count(
            "jobless_claims_same_direction_streak_present",
            rows,
        ),
        max_absolute_initial_claims_revision=_max_decimal(
            tuple(row.absolute_initial_claims_revision for row in rows),
        ),
        average_absolute_initial_claims_revision=_ratio(
            _sum_decimal(tuple(row.absolute_initial_claims_revision for row in rows)),
            row_count,
        ),
        max_revision_streak_weeks=_max_decimal(
            tuple(row.revision_streak_weeks for row in rows),
        ),
        max_revision_streak_pressure_score=_max_decimal(
            tuple(row.revision_streak_pressure_score for row in rows),
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_macro_jobless_claims_revision_streak_digest_payload(
    report: MacroJoblessClaimsRevisionStreakDigestReport,
) -> MappingProxyType:
    if type(report) is not MacroJoblessClaimsRevisionStreakDigestReport:
        raise ValueError(
            "report must be exactly MacroJoblessClaimsRevisionStreakDigestReport",
        )
    revalidated = _revalidate_payload_value(report, "report")
    return _payload_value(revalidated)


def _row_from_observation(
    observation: MacroJoblessClaimsRevisionStreakObservation,
    *,
    config: MacroJoblessClaimsRevisionStreakDigestConfig,
) -> MacroJoblessClaimsRevisionStreakDigestRow:
    absolute_initial = _quantize_decimal(abs(observation.initial_claims_revision))
    absolute_continuing = _quantize_decimal(abs(observation.continuing_claims_revision))
    revision_status = _row_status(
        absolute_initial_claims_revision=absolute_initial,
        absolute_continuing_claims_revision=absolute_continuing,
        revision_streak_weeks=observation.revision_streak_weeks,
        same_direction_revision_weeks=observation.same_direction_revision_weeks,
        config=config,
    )
    return MacroJoblessClaimsRevisionStreakDigestRow(
        source_id=observation.source_id,
        release_id=observation.release_id,
        research_topic_key=observation.research_topic_key,
        release_week=observation.release_week,
        initial_claims_revision=observation.initial_claims_revision,
        continuing_claims_revision=observation.continuing_claims_revision,
        absolute_initial_claims_revision=absolute_initial,
        absolute_continuing_claims_revision=absolute_continuing,
        revision_streak_weeks=observation.revision_streak_weeks,
        same_direction_revision_weeks=observation.same_direction_revision_weeks,
        revised_at=observation.revised_at,
        revision_status=revision_status,
        revision_streak_pressure_score=_row_pressure_score(
            absolute_initial_claims_revision=absolute_initial,
            absolute_continuing_claims_revision=absolute_continuing,
            revision_streak_weeks=observation.revision_streak_weeks,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            observation,
            absolute_initial_claims_revision=absolute_initial,
            absolute_continuing_claims_revision=absolute_continuing,
            revision_status=revision_status,
            config=config,
        ),
    )


def _row_status(
    *,
    absolute_initial_claims_revision: Decimal,
    absolute_continuing_claims_revision: Decimal,
    revision_streak_weeks: Decimal,
    same_direction_revision_weeks: Decimal,
    config: MacroJoblessClaimsRevisionStreakDigestConfig,
) -> str:
    if (
        absolute_initial_claims_revision >= config.blocked_initial_claims_revision
        or absolute_continuing_claims_revision >= config.blocked_continuing_claims_revision
        or revision_streak_weeks >= config.blocked_revision_streak_weeks
    ):
        return "blocked"
    if (
        absolute_initial_claims_revision >= config.watch_initial_claims_revision
        or absolute_continuing_claims_revision >= config.watch_continuing_claims_revision
        or revision_streak_weeks >= config.watch_revision_streak_weeks
        or same_direction_revision_weeks >= config.same_direction_streak_weeks
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: MacroJoblessClaimsRevisionStreakObservation,
    *,
    absolute_initial_claims_revision: Decimal,
    absolute_continuing_claims_revision: Decimal,
    revision_status: str,
    config: MacroJoblessClaimsRevisionStreakDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if revision_status == "blocked":
        reason_codes.append("jobless_claims_revision_streak_blocked")
    elif revision_status == "watch":
        reason_codes.append("jobless_claims_revision_streak_watch")
    else:
        reason_codes.append("jobless_claims_revision_streak_inline")

    if absolute_initial_claims_revision >= config.blocked_initial_claims_revision:
        reason_codes.append("jobless_claims_initial_revision_blocked")
    elif absolute_initial_claims_revision >= config.watch_initial_claims_revision:
        reason_codes.append("jobless_claims_initial_revision_watch")

    if absolute_continuing_claims_revision >= config.blocked_continuing_claims_revision:
        reason_codes.append("jobless_claims_continuing_revision_blocked")
    elif absolute_continuing_claims_revision >= config.watch_continuing_claims_revision:
        reason_codes.append("jobless_claims_continuing_revision_watch")

    if observation.same_direction_revision_weeks >= config.same_direction_streak_weeks:
        reason_codes.append("jobless_claims_same_direction_streak")
    if observation.upstream_reason_codes:
        reason_codes.append("jobless_claims_upstream_revision_present")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("jobless_claims_revision_streak_digest_empty",)
    reason_codes: list[str] = []
    if any(row.revision_status == "blocked" for row in rows):
        reason_codes.append("jobless_claims_revision_streak_blocked_present")
    if any(row.revision_status == "watch" for row in rows):
        reason_codes.append("jobless_claims_revision_streak_watch_present")
    if _any_row_reason(
        rows,
        (
            "jobless_claims_initial_revision_blocked",
            "jobless_claims_initial_revision_watch",
        ),
    ):
        reason_codes.append("jobless_claims_initial_revision_present")
    if _any_row_reason(
        rows,
        (
            "jobless_claims_continuing_revision_blocked",
            "jobless_claims_continuing_revision_watch",
        ),
    ):
        reason_codes.append("jobless_claims_continuing_revision_present")
    if _any_row_reason(rows, ("jobless_claims_same_direction_streak",)):
        reason_codes.append("jobless_claims_same_direction_streak_present")
    if _any_row_reason(rows, ("jobless_claims_upstream_revision_present",)):
        reason_codes.append("jobless_claims_upstream_revision_present")
    if not reason_codes:
        reason_codes.append("jobless_claims_revision_streak_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...],
) -> tuple[MacroJoblessClaimsRevisionStreakReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("jobless_claims_revision_streak_digest_empty",):
        return (
            MacroJoblessClaimsRevisionStreakReasonCodeCount(
                reason_code="jobless_claims_revision_streak_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MacroJoblessClaimsRevisionStreakReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...],
) -> Decimal:
    if reason_code == "jobless_claims_revision_streak_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "jobless_claims_revision_streak_watch_present":
        return _status_count(rows, "watch")
    if reason_code == "jobless_claims_initial_revision_present":
        return _row_reason_count(
            rows,
            (
                "jobless_claims_initial_revision_blocked",
                "jobless_claims_initial_revision_watch",
            ),
        )
    if reason_code == "jobless_claims_continuing_revision_present":
        return _row_reason_count(
            rows,
            (
                "jobless_claims_continuing_revision_blocked",
                "jobless_claims_continuing_revision_watch",
            ),
        )
    if reason_code == "jobless_claims_same_direction_streak_present":
        return _row_reason_count(rows, ("jobless_claims_same_direction_streak",))
    if reason_code == "jobless_claims_upstream_revision_present":
        return _row_reason_count(rows, ("jobless_claims_upstream_revision_present",))
    if reason_code == "jobless_claims_revision_streak_clear":
        return _row_reason_count(rows, ("jobless_claims_revision_streak_inline",))
    if reason_code == "jobless_claims_revision_streak_digest_empty":
        return ONE
    raise ValueError("reason_code must be supported")


def _digest_status(rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.revision_status == "blocked" for row in rows):
        return "blocked"
    if any(row.revision_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_macro_jobless_claims_revision_streak_digest"
    if status == "watch":
        return "watch_report_only_macro_jobless_claims_revision_streak_digest"
    return "block_report_only_macro_jobless_claims_revision_streak_digest"


def _row_pressure_score(
    *,
    absolute_initial_claims_revision: Decimal,
    absolute_continuing_claims_revision: Decimal,
    revision_streak_weeks: Decimal,
    config: MacroJoblessClaimsRevisionStreakDigestConfig,
) -> Decimal:
    return _max_decimal(
        (
            _capped_ratio(
                absolute_initial_claims_revision,
                config.blocked_initial_claims_revision,
            ),
            _capped_ratio(
                absolute_continuing_claims_revision,
                config.blocked_continuing_claims_revision,
            ),
            _capped_ratio(revision_streak_weeks, config.blocked_revision_streak_weeks),
        ),
    )


def _validate_row(row: MacroJoblessClaimsRevisionStreakDigestRow) -> None:
    if row.absolute_initial_claims_revision != _quantize_decimal(
        abs(row.initial_claims_revision),
    ):
        raise ValueError(
            "absolute_initial_claims_revision must match initial_claims_revision",
        )
    if row.absolute_continuing_claims_revision != _quantize_decimal(
        abs(row.continuing_claims_revision),
    ):
        raise ValueError(
            "absolute_continuing_claims_revision must match continuing_claims_revision",
        )
    _validate_row_reason_shape(row)


def _validate_row_reason_shape(row: MacroJoblessClaimsRevisionStreakDigestRow) -> None:
    blocked_reasons = (
        "jobless_claims_revision_streak_blocked",
        "jobless_claims_initial_revision_blocked",
        "jobless_claims_continuing_revision_blocked",
    )
    watch_reasons = (
        "jobless_claims_revision_streak_watch",
        "jobless_claims_initial_revision_watch",
        "jobless_claims_continuing_revision_watch",
        "jobless_claims_same_direction_streak",
    )
    has_blocked_reason = _row_has_any(row, blocked_reasons)
    has_watch_reason = _row_has_any(row, watch_reasons)
    has_inline_reason = "jobless_claims_revision_streak_inline" in row.reason_codes
    has_upstream_reason = "jobless_claims_upstream_revision_present" in row.reason_codes
    if has_inline_reason and tuple(
        reason
        for reason in row.reason_codes
        if reason
        not in (
            "jobless_claims_revision_streak_inline",
            "jobless_claims_upstream_revision_present",
        )
    ):
        raise ValueError("reason_codes must match row fields")
    if row.revision_status == "pass":
        if has_blocked_reason or has_watch_reason or has_inline_reason is False:
            raise ValueError("reason_codes must match row fields")
        if has_upstream_reason and len(row.reason_codes) != 2:
            raise ValueError("reason_codes must match row fields")
        if not has_upstream_reason and len(row.reason_codes) != 1:
            raise ValueError("reason_codes must match row fields")
        return
    if row.revision_status == "watch":
        if has_blocked_reason or has_inline_reason or not has_watch_reason:
            raise ValueError("reason_codes must match row fields")
        return
    if not has_blocked_reason or has_inline_reason:
        raise ValueError("reason_codes must match row fields")


def _validate_report(report: MacroJoblessClaimsRevisionStreakDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.revision_streak_count != (
        _report_reason_row_count("jobless_claims_revision_streak_blocked_present", report.rows)
        + _report_reason_row_count("jobless_claims_revision_streak_watch_present", report.rows)
    ):
        raise ValueError("revision_streak_count must match rows")
    if report.initial_revision_count != _report_reason_row_count(
        "jobless_claims_initial_revision_present",
        report.rows,
    ):
        raise ValueError("initial_revision_count must match rows")
    if report.continuing_revision_count != _report_reason_row_count(
        "jobless_claims_continuing_revision_present",
        report.rows,
    ):
        raise ValueError("continuing_revision_count must match rows")
    if report.same_direction_streak_count != _report_reason_row_count(
        "jobless_claims_same_direction_streak_present",
        report.rows,
    ):
        raise ValueError("same_direction_streak_count must match rows")
    if report.max_absolute_initial_claims_revision != _max_decimal(
        tuple(row.absolute_initial_claims_revision for row in report.rows),
    ):
        raise ValueError("max_absolute_initial_claims_revision must match rows")
    if report.average_absolute_initial_claims_revision != _ratio(
        _sum_decimal(tuple(row.absolute_initial_claims_revision for row in report.rows)),
        report.row_count,
    ):
        raise ValueError("average_absolute_initial_claims_revision must match rows")
    if report.max_revision_streak_weeks != _max_decimal(
        tuple(row.revision_streak_weeks for row in report.rows),
    ):
        raise ValueError("max_revision_streak_weeks must match rows")
    if report.max_revision_streak_pressure_score != _max_decimal(
        tuple(row.revision_streak_pressure_score for row in report.rows),
    ):
        raise ValueError("max_revision_streak_pressure_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: object,
) -> tuple[MacroJoblessClaimsRevisionStreakObservation, ...]:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    seen_source_ids: set[str] = set()
    normalized: list[MacroJoblessClaimsRevisionStreakObservation] = []
    for observation in observations:
        if type(observation) is not MacroJoblessClaimsRevisionStreakObservation:
            raise ValueError(
                "observations must contain MacroJoblessClaimsRevisionStreakObservation",
            )
        revalidated = _revalidate_payload_value(observation, "observation")
        if type(revalidated) is not MacroJoblessClaimsRevisionStreakObservation:
            raise ValueError(
                "observations must contain MacroJoblessClaimsRevisionStreakObservation",
            )
        if revalidated.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(revalidated.source_id)
        normalized.append(revalidated)
    return tuple(normalized)


def _normalize_rows(value: object) -> tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not MacroJoblessClaimsRevisionStreakDigestRow:
            raise ValueError("rows must contain MacroJoblessClaimsRevisionStreakDigestRow")
        _require_hard_flags("row", row)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    seen_source_ids: set[str] = set()
    for row in value:
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MacroJoblessClaimsRevisionStreakReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not MacroJoblessClaimsRevisionStreakReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MacroJoblessClaimsRevisionStreakReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    if value != tuple(sorted(value, key=lambda item: REPORT_REASON_CODES.index(item.reason_code))):
        raise ValueError("reason_code_counts must use canonical sequence")
    if len({item.reason_code for item in value}) != len(value):
        raise ValueError("reason_code_counts must not contain duplicates")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_member("reason_code", item, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    if value != tuple(sorted(value, key=lambda item: allowed.index(item))):
        raise ValueError(f"{field_name} must use canonical sequence")
    return value


def _row_sort_key(row: MacroJoblessClaimsRevisionStreakDigestRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.revision_status],
        -row.revision_streak_pressure_score,
        row.research_topic_key,
    )


def _status_count(
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.revision_status == status))


def _row_reason_count(
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _any_row_reason(
    rows: tuple[MacroJoblessClaimsRevisionStreakDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> bool:
    return any(any(reason in row.reason_codes for reason in reason_codes) for row in rows)


def _row_has_any(
    row: MacroJoblessClaimsRevisionStreakDigestRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason in row.reason_codes for reason in reason_codes)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must contain exactly Decimal values")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE:
        return ONE
    return value


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use exactly six decimal places")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_already_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must already be UTC")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _revalidate_payload_value(value: object, field_name: str) -> object:
    public_types = (
        MacroJoblessClaimsRevisionStreakDigestConfig,
        MacroJoblessClaimsRevisionStreakObservation,
        MacroJoblessClaimsRevisionStreakDigestRow,
        MacroJoblessClaimsRevisionStreakReasonCodeCount,
        MacroJoblessClaimsRevisionStreakDigestReport,
    )
    if type(value) in public_types:
        kwargs: dict[str, object] = {}
        for field in fields(value):
            child = getattr(value, field.name)
            if type(child) is datetime:
                kwargs[field.name] = _require_already_utc(field.name, child)
            elif type(child) is tuple:
                kwargs[field.name] = tuple(
                    _revalidate_payload_value(item, field.name) for item in child
                )
            elif is_dataclass(child) and not isinstance(child, type):
                kwargs[field.name] = _revalidate_payload_value(child, field.name)
            else:
                _require_supported_payload_scalar(field.name, child)
                kwargs[field.name] = child
        return type(value)(**kwargs)
    if type(value) is Decimal:
        return _require_decimal(field_name, value)
    if type(value) in (str, bool):
        return value
    raise ValueError(f"{field_name} has unsupported payload value")


def _require_supported_payload_scalar(field_name: str, value: object) -> None:
    if type(value) in (str, bool):
        return
    if type(value) is Decimal:
        _require_decimal(field_name, value)
        return
    raise ValueError(f"{field_name} has unsupported payload value")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        _require_already_utc("datetime", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return MappingProxyType(
            {
                field.name: _payload_value(getattr(value, field.name))
                for field in fields(value)
            },
        )
    if type(value) is tuple:
        return tuple(_payload_value(item) for item in value)
    return value
