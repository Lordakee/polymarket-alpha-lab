"""Pure report-only source resolution calendar dependency scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_RESOLUTION_CALENDAR_DEPENDENCY_REPORT_CONFIG_VERSION = (
    "research-source-resolution-calendar-dependency-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIVE = Decimal("5.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "candidate",
    "candidate_" + "id",
    "candidate" + "-",
    "market_" + "id",
    "market_" + "sl" + "ug",
    "market_" + "ques" + "tion",
    "market" + "-",
    "sl" + "ug",
    "ques" + "tion",
    "://",
    "www.",
    "u" + "rl",
    "d" + "sn",
    "tab" + "le",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "source_" + "text",
)


@dataclass(frozen=True)
class ResearchSourceResolutionCalendarDependencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_CALENDAR_DEPENDENCY_REPORT_CONFIG_VERSION
    )
    fresh_calendar_age_seconds: Decimal = Decimal("3600.000000")
    stale_calendar_age_seconds: Decimal = Decimal("86400.000000")
    watch_active_calendar_dependency_count: Decimal = Decimal("1.000000")
    block_active_calendar_dependency_count: Decimal = Decimal("3.000000")
    watch_stale_calendar_score: Decimal = Decimal("0.250000")
    block_stale_calendar_score: Decimal = Decimal("1.000000")
    watch_timing_ambiguity_score: Decimal = Decimal("0.250000")
    block_timing_ambiguity_score: Decimal = Decimal("1.000000")
    watch_dependency_score: Decimal = Decimal("0.250000")
    block_dependency_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionCalendarDependencyConfig:
            raise TypeError(
                "ResearchSourceResolutionCalendarDependencyConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionCalendarDependencyConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceResolutionCalendarDependencyConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_CALENDAR_DEPENDENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_calendar_age_seconds",
            "stale_calendar_age_seconds",
            "watch_active_calendar_dependency_count",
            "block_active_calendar_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_calendar_score",
            "block_stale_calendar_score",
            "watch_timing_ambiguity_score",
            "block_timing_ambiguity_score",
            "watch_dependency_score",
            "block_dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_calendar_age_seconds <= self.fresh_calendar_age_seconds:
            raise ValueError(
                "stale_calendar_age_seconds must exceed fresh_calendar_age_seconds",
            )
        if (
            self.block_active_calendar_dependency_count
            <= self.watch_active_calendar_dependency_count
        ):
            raise ValueError(
                "block_active_calendar_dependency_count must exceed "
                "watch_active_calendar_dependency_count",
            )
        if self.block_stale_calendar_score < self.watch_stale_calendar_score:
            raise ValueError(
                "block_stale_calendar_score must be at least watch_stale_calendar_score",
            )
        if (
            self.block_timing_ambiguity_score
            < self.watch_timing_ambiguity_score
        ):
            raise ValueError(
                "block_timing_ambiguity_score must be at least "
                "watch_timing_ambiguity_score",
            )
        if self.block_dependency_score <= self.watch_dependency_score:
            raise ValueError("block_dependency_score must exceed watch_dependency_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionCalendarDependencyInput:
    review_bucket: str
    evidence_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_material: str
    depends_on_dated_release: bool
    depends_on_scheduled_decision: bool
    depends_on_event_window: bool
    timing_ambiguity_unresolved: bool
    calendar_observed_at: datetime
    dependency_scheduled_at: datetime | None = None
    event_window_starts_at: datetime | None = None
    event_window_ends_at: datetime | None = None
    timing_clarity_score: Decimal = Decimal("1.000000")
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionCalendarDependencyInput:
            raise TypeError(
                "ResearchSourceResolutionCalendarDependencyInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionCalendarDependencyInput:
            raise ValueError(
                "input must be exactly ResearchSourceResolutionCalendarDependencyInput",
            )
        for field_name in ("review_bucket", "evidence_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _reject_unsafe_public_string("review_bucket", self.review_bucket)
        _reject_unsafe_public_string("evidence_bucket", self.evidence_bucket)
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_material",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        for field_name in (
            "depends_on_dated_release",
            "depends_on_scheduled_decision",
            "depends_on_event_window",
            "timing_ambiguity_unresolved",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "calendar_observed_at",
            _as_utc("calendar_observed_at", self.calendar_observed_at),
        )
        for field_name in (
            "dependency_scheduled_at",
            "event_window_starts_at",
            "event_window_ends_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name)),
            )
        if (
            self.event_window_starts_at is not None
            and self.event_window_ends_at is not None
            and self.event_window_ends_at < self.event_window_starts_at
        ):
            raise ValueError("event_window_ends_at must not precede event_window_starts_at")
        object.__setattr__(
            self,
            "timing_clarity_score",
            _require_ratio_decimal("timing_clarity_score", self.timing_clarity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionCalendarDependencyRow:
    review_bucket: str
    evidence_bucket: str
    active_calendar_dependency_count: Decimal
    dated_release_dependency_score: Decimal
    scheduled_decision_dependency_score: Decimal
    event_window_dependency_score: Decimal
    calendar_age_seconds: Decimal
    stale_calendar_score: Decimal
    unresolved_timing_ambiguity_score: Decimal
    dependency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionCalendarDependencyRow:
            raise TypeError(
                "ResearchSourceResolutionCalendarDependencyRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionCalendarDependencyRow:
            raise ValueError(
                "row must be exactly ResearchSourceResolutionCalendarDependencyRow",
            )
        for field_name in ("review_bucket", "evidence_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "active_calendar_dependency_count",
            "calendar_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dated_release_dependency_score",
            "scheduled_decision_dependency_score",
            "event_window_dependency_score",
            "stale_calendar_score",
            "unresolved_timing_ambiguity_score",
            "dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionCalendarDependencyReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    dated_release_dependency_count: Decimal
    scheduled_decision_dependency_count: Decimal
    event_window_dependency_count: Decimal
    stale_calendar_count: Decimal
    unresolved_timing_ambiguity_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_dependency_score: Decimal
    max_dependency_score: Decimal
    status: str
    rows: tuple[ResearchSourceResolutionCalendarDependencyRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionCalendarDependencyReport:
            raise TypeError(
                "ResearchSourceResolutionCalendarDependencyReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionCalendarDependencyReport:
            raise ValueError(
                "report must be exactly ResearchSourceResolutionCalendarDependencyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_CALENDAR_DEPENDENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "dated_release_dependency_count",
            "scheduled_decision_dependency_count",
            "event_window_dependency_count",
            "stale_calendar_count",
            "unresolved_timing_ambiguity_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_dependency_score", "max_dependency_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_source_resolution_calendar_dependency_report(
    dependencies: Sequence[ResearchSourceResolutionCalendarDependencyInput],
    *,
    generated_at: datetime,
    config: ResearchSourceResolutionCalendarDependencyConfig | None = None,
) -> ResearchSourceResolutionCalendarDependencyReport:
    if config is None:
        config = ResearchSourceResolutionCalendarDependencyConfig()
    if type(config) is not ResearchSourceResolutionCalendarDependencyConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionCalendarDependencyConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_dependencies = _normalize_dependencies(dependencies)
    for item in normalized_dependencies:
        if item.calendar_observed_at > generated_at:
            raise ValueError("calendar_observed_at must not be after generated_at")
    rows = tuple(_row_for_input(item, config, generated_at) for item in normalized_dependencies)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "row_count": _decimal_count(len(rows)),
        "dated_release_dependency_count": sum(
            (row.dated_release_dependency_score for row in rows),
            _ZERO,
        ),
        "scheduled_decision_dependency_count": sum(
            (row.scheduled_decision_dependency_score for row in rows),
            _ZERO,
        ),
        "event_window_dependency_count": sum(
            (row.event_window_dependency_score for row in rows),
            _ZERO,
        ),
        "stale_calendar_count": _decimal_count(
            sum(1 for row in rows if row.stale_calendar_score >= _ONE),
        ),
        "unresolved_timing_ambiguity_count": _decimal_count(
            sum(1 for row in rows if row.unresolved_timing_ambiguity_score >= _ONE),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_dependency_score": _average(
            tuple(row.dependency_score for row in rows),
        ),
        "max_dependency_score": max((row.dependency_score for row in rows), default=_ZERO),
        "status": _report_status(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceResolutionCalendarDependencyReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_resolution_calendar_dependency_report_payload(
    report: ResearchSourceResolutionCalendarDependencyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceResolutionCalendarDependencyReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError(
            "report must be a ResearchSourceResolutionCalendarDependencyReport",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
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


def _row_for_input(
    item: ResearchSourceResolutionCalendarDependencyInput,
    config: ResearchSourceResolutionCalendarDependencyConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionCalendarDependencyRow:
    dated_release_score = _bool_score(item.depends_on_dated_release)
    scheduled_decision_score = _bool_score(item.depends_on_scheduled_decision)
    event_window_score = _bool_score(item.depends_on_event_window)
    active_dependency_count = dated_release_score + scheduled_decision_score + event_window_score
    calendar_age = _age_seconds(generated_at, item.calendar_observed_at)
    stale_calendar_score = _stale_calendar_score(calendar_age, config)
    ambiguity_score = _timing_ambiguity_score(item)
    dependency_score = _dependency_score(
        dated_release_dependency_score=dated_release_score,
        scheduled_decision_dependency_score=scheduled_decision_score,
        event_window_dependency_score=event_window_score,
        stale_calendar_score=stale_calendar_score,
        unresolved_timing_ambiguity_score=ambiguity_score,
    )
    status = _row_status(
        active_calendar_dependency_count=active_dependency_count,
        stale_calendar_score=stale_calendar_score,
        unresolved_timing_ambiguity_score=ambiguity_score,
        dependency_score=dependency_score,
        config=config,
    )
    return ResearchSourceResolutionCalendarDependencyRow(
        review_bucket=item.review_bucket,
        evidence_bucket=item.evidence_bucket,
        active_calendar_dependency_count=active_dependency_count,
        dated_release_dependency_score=dated_release_score,
        scheduled_decision_dependency_score=scheduled_decision_score,
        event_window_dependency_score=event_window_score,
        calendar_age_seconds=calendar_age,
        stale_calendar_score=stale_calendar_score,
        unresolved_timing_ambiguity_score=ambiguity_score,
        dependency_score=dependency_score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            stale_calendar_score=stale_calendar_score,
            unresolved_timing_ambiguity_score=ambiguity_score,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _stale_calendar_score(
    calendar_age_seconds: Decimal,
    config: ResearchSourceResolutionCalendarDependencyConfig,
) -> Decimal:
    if calendar_age_seconds <= config.fresh_calendar_age_seconds:
        return _ZERO
    if calendar_age_seconds >= config.stale_calendar_age_seconds:
        return _ONE
    return _clamp_ratio(calendar_age_seconds / config.stale_calendar_age_seconds)


def _timing_ambiguity_score(
    item: ResearchSourceResolutionCalendarDependencyInput,
) -> Decimal:
    scores = [_ONE - item.timing_clarity_score]
    if item.timing_ambiguity_unresolved:
        scores.append(_ONE)
    if (
        item.depends_on_dated_release or item.depends_on_scheduled_decision
    ) and item.dependency_scheduled_at is None:
        scores.append(_ONE)
    if item.depends_on_event_window and (
        item.event_window_starts_at is None or item.event_window_ends_at is None
    ):
        scores.append(_ONE)
    return _clamp_ratio(max(scores, default=_ZERO))


def _dependency_score(
    *,
    dated_release_dependency_score: Decimal,
    scheduled_decision_dependency_score: Decimal,
    event_window_dependency_score: Decimal,
    stale_calendar_score: Decimal,
    unresolved_timing_ambiguity_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        (
            dated_release_dependency_score
            + scheduled_decision_dependency_score
            + event_window_dependency_score
            + stale_calendar_score
            + unresolved_timing_ambiguity_score
        )
        / _FIVE,
    )


def _row_status(
    *,
    active_calendar_dependency_count: Decimal,
    stale_calendar_score: Decimal,
    unresolved_timing_ambiguity_score: Decimal,
    dependency_score: Decimal,
    config: ResearchSourceResolutionCalendarDependencyConfig,
) -> str:
    if (
        active_calendar_dependency_count >= config.block_active_calendar_dependency_count
        or stale_calendar_score >= config.block_stale_calendar_score
        or unresolved_timing_ambiguity_score >= config.block_timing_ambiguity_score
        or dependency_score >= config.block_dependency_score
    ):
        return "block"
    if (
        active_calendar_dependency_count >= config.watch_active_calendar_dependency_count
        or stale_calendar_score >= config.watch_stale_calendar_score
        or unresolved_timing_ambiguity_score >= config.watch_timing_ambiguity_score
        or dependency_score >= config.watch_dependency_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchSourceResolutionCalendarDependencyInput,
    status: str,
    stale_calendar_score: Decimal,
    unresolved_timing_ambiguity_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchSourceResolutionCalendarDependencyConfig,
) -> tuple[str, ...]:
    reason_codes = {f"calendar_dependency_{status}"}
    if item.depends_on_dated_release:
        reason_codes.add("dated_release_dependency")
    if item.depends_on_scheduled_decision:
        reason_codes.add("scheduled_decision_dependency")
    if item.depends_on_event_window:
        reason_codes.add("event_window_dependency")
    if not (
        item.depends_on_dated_release
        or item.depends_on_scheduled_decision
        or item.depends_on_event_window
    ):
        reason_codes.add("no_calendar_dependency")
    if stale_calendar_score >= config.block_stale_calendar_score:
        reason_codes.add("calendar_stale")
    elif stale_calendar_score >= config.watch_stale_calendar_score:
        reason_codes.add("calendar_age_watch")
    else:
        reason_codes.add("calendar_fresh")
    if unresolved_timing_ambiguity_score >= config.block_timing_ambiguity_score:
        reason_codes.add("timing_ambiguity_unresolved")
    elif unresolved_timing_ambiguity_score >= config.watch_timing_ambiguity_score:
        reason_codes.add("timing_clarity_watch")
    else:
        reason_codes.add("timing_clarity_clear")
    if (
        item.depends_on_dated_release or item.depends_on_scheduled_decision
    ) and item.dependency_scheduled_at is None:
        reason_codes.add("scheduled_anchor_missing")
    if item.depends_on_event_window and (
        item.event_window_starts_at is None or item.event_window_ends_at is None
    ):
        reason_codes.add("event_window_missing")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _report_status(
    rows: tuple[ResearchSourceResolutionCalendarDependencyRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionCalendarDependencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_calendar_dependency_inputs",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        allow_empty=False,
    )


def _status_count(
    rows: tuple[ResearchSourceResolutionCalendarDependencyRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_dependencies(
    dependencies: Sequence[ResearchSourceResolutionCalendarDependencyInput],
) -> tuple[ResearchSourceResolutionCalendarDependencyInput, ...]:
    if isinstance(dependencies, (str, bytes)) or not isinstance(dependencies, Sequence):
        raise ValueError("dependencies must be a sequence")
    normalized: list[ResearchSourceResolutionCalendarDependencyInput] = []
    for item in dependencies:
        if type(item) is not ResearchSourceResolutionCalendarDependencyInput:
            raise ValueError(
                "dependencies must contain "
                "ResearchSourceResolutionCalendarDependencyInput",
            )
        _require_hard_flags("input", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.review_bucket,
                item.evidence_bucket,
                item.calendar_observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceResolutionCalendarDependencyRow],
) -> tuple[ResearchSourceResolutionCalendarDependencyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceResolutionCalendarDependencyRow] = []
    for row in rows:
        if type(row) is not ResearchSourceResolutionCalendarDependencyRow:
            raise ValueError(
                "rows must contain ResearchSourceResolutionCalendarDependencyRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.review_bucket, row.evidence_bucket)))


def _validate_row_consistency(
    row: ResearchSourceResolutionCalendarDependencyRow,
) -> None:
    expected_active_count = (
        row.dated_release_dependency_score
        + row.scheduled_decision_dependency_score
        + row.event_window_dependency_score
    )
    if row.active_calendar_dependency_count != expected_active_count:
        raise ValueError("active_calendar_dependency_count must match dependency scores")
    expected_score = _dependency_score(
        dated_release_dependency_score=row.dated_release_dependency_score,
        scheduled_decision_dependency_score=row.scheduled_decision_dependency_score,
        event_window_dependency_score=row.event_window_dependency_score,
        stale_calendar_score=row.stale_calendar_score,
        unresolved_timing_ambiguity_score=row.unresolved_timing_ambiguity_score,
    )
    if row.dependency_score != expected_score:
        raise ValueError("dependency_score must match calendar dependency components")
    status_reason_code = f"calendar_dependency_{row.status}"
    if status_reason_code not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")


def _validate_report_consistency(
    report: ResearchSourceResolutionCalendarDependencyReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.dated_release_dependency_count != sum(
        (row.dated_release_dependency_score for row in report.rows),
        _ZERO,
    ):
        raise ValueError("dated_release_dependency_count must match rows")
    if report.scheduled_decision_dependency_count != sum(
        (row.scheduled_decision_dependency_score for row in report.rows),
        _ZERO,
    ):
        raise ValueError("scheduled_decision_dependency_count must match rows")
    if report.event_window_dependency_count != sum(
        (row.event_window_dependency_score for row in report.rows),
        _ZERO,
    ):
        raise ValueError("event_window_dependency_count must match rows")
    if report.stale_calendar_count != _decimal_count(
        sum(1 for row in report.rows if row.stale_calendar_score >= _ONE),
    ):
        raise ValueError("stale_calendar_count must match rows")
    if report.unresolved_timing_ambiguity_count != _decimal_count(
        sum(1 for row in report.rows if row.unresolved_timing_ambiguity_score >= _ONE),
    ):
        raise ValueError("unresolved_timing_ambiguity_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_dependency_score != _average(
        tuple(row.dependency_score for row in report.rows),
    ):
        raise ValueError("average_dependency_score must match rows")
    if report.max_dependency_score != max(
        (row.dependency_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_dependency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_nonempty_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _bool_score(value: bool) -> Decimal:
    if type(value) is not bool:
        raise ValueError("calendar dependency flag must be a bool")
    if value:
        return _ONE
    return _ZERO


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(
    field_name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
            raise ValueError(f"{field_name} must be lowercase snake_case strings")
        _reject_unsafe_public_string(field_name, value)
        if value not in normalized:
            normalized.append(value)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(normalized))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _report_values_without_digest(
    report: ResearchSourceResolutionCalendarDependencyReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if _has_unsafe_public_fragment(key):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = _report_digest_from_values(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_CALENDAR_DEPENDENCY_REPORT_CONFIG_VERSION",
    "ResearchSourceResolutionCalendarDependencyConfig",
    "ResearchSourceResolutionCalendarDependencyInput",
    "ResearchSourceResolutionCalendarDependencyReport",
    "ResearchSourceResolutionCalendarDependencyRow",
    "build_research_source_resolution_calendar_dependency_report",
    "research_source_resolution_calendar_dependency_report_payload",
)
