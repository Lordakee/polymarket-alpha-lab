"""Paper-only specialist resolution latency score report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_TEAM_MEMORY_SPECIALIST_RESOLUTION_LATENCY_SCORE_V2_CONFIG_VERSION = (
    "team-memory-specialist-resolution-latency-score-v2"
)

_ZERO = Decimal("0.000000")
_FIFTY = Decimal("50.000000")
_HUNDRED = Decimal("100.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_REPORT_STATUSES = frozenset(("empty", "pass", "watch", "block"))
_ROW_STATUSES = frozenset(("pass", "watch", "block"))
_READY_REASON = "team_memory_specialist_learning_loop_ready"
_HIGH_LATENCY_REASON = "team_memory_specialist_resolution_latency_high"
_WEAK_POSTMORTEM_REASON = (
    "team_memory_specialist_postmortem_completion_weak"
)
_STALE_RESOLUTION_REASON = "team_memory_specialist_latest_resolution_stale"
_LOW_LEARNING_REASON = "team_memory_specialist_learning_loop_score_below_watch"
_ROW_REASON_ORDER = (
    _HIGH_LATENCY_REASON,
    _WEAK_POSTMORTEM_REASON,
    _STALE_RESOLUTION_REASON,
    _LOW_LEARNING_REASON,
    _READY_REASON,
)
_ROW_REASON_CODES = frozenset(_ROW_REASON_ORDER)


@dataclass(frozen=True)
class TeamMemorySpecialistResolutionLatencyScoreV2Config:
    config_version: str = (
        DEFAULT_TEAM_MEMORY_SPECIALIST_RESOLUTION_LATENCY_SCORE_V2_CONFIG_VERSION
    )
    max_pass_median_resolution_latency_seconds: Decimal = Decimal("3600.000000")
    max_watch_median_resolution_latency_seconds: Decimal = Decimal("14400.000000")
    max_pass_p95_resolution_latency_seconds: Decimal = Decimal("7200.000000")
    max_watch_p95_resolution_latency_seconds: Decimal = Decimal("28800.000000")
    min_pass_postmortem_completion_ratio: Decimal = Decimal("0.900000")
    min_watch_postmortem_completion_ratio: Decimal = Decimal("0.700000")
    stale_resolution_age_seconds: Decimal = Decimal("604800.000000")
    min_pass_learning_loop_score: Decimal = Decimal("90.000000")
    min_watch_learning_loop_score: Decimal = Decimal("50.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamMemorySpecialistResolutionLatencyScoreV2Config:
            raise TypeError(
                "TeamMemorySpecialistResolutionLatencyScoreV2Config "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamMemorySpecialistResolutionLatencyScoreV2Config:
            raise ValueError(
                "config must be exactly "
                "TeamMemorySpecialistResolutionLatencyScoreV2Config",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "max_pass_median_resolution_latency_seconds",
            "max_watch_median_resolution_latency_seconds",
            "max_pass_p95_resolution_latency_seconds",
            "max_watch_p95_resolution_latency_seconds",
            "stale_resolution_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_postmortem_completion_ratio",
            "min_watch_postmortem_completion_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_learning_loop_score",
            "min_watch_learning_loop_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("specialist resolution latency score config", self)


@dataclass(frozen=True)
class TeamMemorySpecialistResolutionLatencyScoreV2Source:
    team_id: str
    domain: str
    resolved_market_count: Decimal
    median_resolution_latency_seconds: Decimal
    p95_resolution_latency_seconds: Decimal
    postmortem_completion_ratio: Decimal
    latest_resolution_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamMemorySpecialistResolutionLatencyScoreV2Source:
            raise TypeError(
                "TeamMemorySpecialistResolutionLatencyScoreV2Source "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamMemorySpecialistResolutionLatencyScoreV2Source:
            raise ValueError(
                "source must be exactly "
                "TeamMemorySpecialistResolutionLatencyScoreV2Source",
            )
        _require_text("team_id", self.team_id)
        _require_text("domain", self.domain)
        object.__setattr__(
            self,
            "resolved_market_count",
            _normalize_nonnegative_decimal(
                "resolved_market_count",
                self.resolved_market_count,
            ),
        )
        for field_name in (
            "median_resolution_latency_seconds",
            "p95_resolution_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "postmortem_completion_ratio",
            _normalize_ratio(
                "postmortem_completion_ratio",
                self.postmortem_completion_ratio,
            ),
        )
        object.__setattr__(
            self,
            "latest_resolution_at",
            _as_utc("latest_resolution_at", self.latest_resolution_at),
        )
        if (
            self.p95_resolution_latency_seconds
            < self.median_resolution_latency_seconds
        ):
            raise ValueError(
                "p95_resolution_latency_seconds must be >= "
                "median_resolution_latency_seconds",
            )
        require_paper_only_flags("specialist resolution latency score source", self)


@dataclass(frozen=True)
class TeamMemorySpecialistResolutionLatencyScoreV2Row:
    team_id: str
    domain: str
    resolved_market_count: Decimal
    median_resolution_latency_seconds: Decimal
    p95_resolution_latency_seconds: Decimal
    postmortem_completion_ratio: Decimal
    latest_resolution_at: datetime
    resolution_age_seconds: Decimal
    latency_score: Decimal
    learning_loop_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamMemorySpecialistResolutionLatencyScoreV2Row:
            raise TypeError(
                "TeamMemorySpecialistResolutionLatencyScoreV2Row "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamMemorySpecialistResolutionLatencyScoreV2Row:
            raise ValueError(
                "row must be exactly "
                "TeamMemorySpecialistResolutionLatencyScoreV2Row",
            )
        _require_text("team_id", self.team_id)
        _require_text("domain", self.domain)
        for field_name in (
            "resolved_market_count",
            "median_resolution_latency_seconds",
            "p95_resolution_latency_seconds",
            "resolution_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "postmortem_completion_ratio",
            _normalize_ratio(
                "postmortem_completion_ratio",
                self.postmortem_completion_ratio,
            ),
        )
        object.__setattr__(
            self,
            "latest_resolution_at",
            _as_utc("latest_resolution_at", self.latest_resolution_at),
        )
        for field_name in ("latency_score", "learning_loop_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=False,
                order="row",
            ),
        )
        _validate_row(self)
        require_paper_only_flags("specialist resolution latency score row", self)


@dataclass(frozen=True)
class TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount:
            raise TypeError(
                "TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount",
            )
        _require_reason_code(self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        require_paper_only_flags(
            "specialist resolution latency score reason count",
            self,
        )


@dataclass(frozen=True)
class TeamMemorySpecialistResolutionLatencyScoreV2Report:
    generated_at: datetime
    config_version: str
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_latency_count: Decimal
    weak_postmortem_count: Decimal
    stale_resolution_count: Decimal
    min_learning_loop_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount,
        ...,
    ]
    rows: tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamMemorySpecialistResolutionLatencyScoreV2Report:
            raise TypeError(
                "TeamMemorySpecialistResolutionLatencyScoreV2Report "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamMemorySpecialistResolutionLatencyScoreV2Report:
            raise ValueError(
                "report must be exactly "
                "TeamMemorySpecialistResolutionLatencyScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_latency_count",
            "weak_postmortem_count",
            "stale_resolution_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_learning_loop_score",
            _normalize_score("min_learning_loop_score", self.min_learning_loop_score),
        )
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=True,
                order="sorted",
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("specialist resolution latency score report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_digest(self.derived_validation_digest),
            )
        _validate_report_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = json_ready_no_floats(asdict(self))
        reject_unsafe_surface_fields(
            "TeamMemorySpecialistResolutionLatencyScoreV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_memory_specialist_resolution_latency_score_v2_report(
    sources: tuple[
        TeamMemorySpecialistResolutionLatencyScoreV2Source | dict[str, object],
        ...,
    ]
    | list[TeamMemorySpecialistResolutionLatencyScoreV2Source | dict[str, object]],
    *,
    config: TeamMemorySpecialistResolutionLatencyScoreV2Config,
    generated_at: datetime,
) -> TeamMemorySpecialistResolutionLatencyScoreV2Report:
    if type(config) is not TeamMemorySpecialistResolutionLatencyScoreV2Config:
        raise ValueError(
            "config must be a TeamMemorySpecialistResolutionLatencyScoreV2Config",
        )
    require_paper_only_flags("specialist resolution latency score config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    rows = tuple(
        sorted(
            (
                _row_from_source(
                    source,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for source in normalized_sources
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    team_domain_count = _decimal_count(len(rows))
    learning_scores = tuple(row.learning_loop_score for row in rows)

    return TeamMemorySpecialistResolutionLatencyScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_domain_count=team_domain_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        high_latency_count=_reason_count(rows, _HIGH_LATENCY_REASON),
        weak_postmortem_count=_reason_count(rows, _WEAK_POSTMORTEM_REASON),
        stale_resolution_count=_reason_count(rows, _STALE_RESOLUTION_REASON),
        min_learning_loop_score=min(learning_scores) if learning_scores else _ZERO,
        report_status=_report_status(rows),
        reason_codes=tuple(count.reason_code for count in reason_code_counts),
        reason_code_counts=reason_code_counts,
        rows=rows,
    )


def _row_from_source(
    source: TeamMemorySpecialistResolutionLatencyScoreV2Source,
    *,
    config: TeamMemorySpecialistResolutionLatencyScoreV2Config,
    generated_at: datetime,
) -> TeamMemorySpecialistResolutionLatencyScoreV2Row:
    if source.latest_resolution_at > generated_at:
        raise ValueError("latest_resolution_at must not be after generated_at")
    resolution_age_seconds = _seconds_between(
        source.latest_resolution_at,
        generated_at,
    )
    latency_score = _latency_score(source, config)
    freshness_score = (
        _ZERO
        if resolution_age_seconds > config.stale_resolution_age_seconds
        else _HUNDRED
    )
    learning_loop_score = min(
        latency_score,
        _score_from_ratio(source.postmortem_completion_ratio),
        freshness_score,
    )
    reason_codes = _row_reason_codes(
        source,
        config=config,
        latency_score=latency_score,
        learning_loop_score=learning_loop_score,
        resolution_age_seconds=resolution_age_seconds,
    )
    return TeamMemorySpecialistResolutionLatencyScoreV2Row(
        team_id=source.team_id,
        domain=source.domain,
        resolved_market_count=source.resolved_market_count,
        median_resolution_latency_seconds=source.median_resolution_latency_seconds,
        p95_resolution_latency_seconds=source.p95_resolution_latency_seconds,
        postmortem_completion_ratio=source.postmortem_completion_ratio,
        latest_resolution_at=source.latest_resolution_at,
        resolution_age_seconds=resolution_age_seconds,
        latency_score=latency_score,
        learning_loop_score=learning_loop_score,
        status=_row_status(reason_codes, learning_loop_score, config),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    source: TeamMemorySpecialistResolutionLatencyScoreV2Source,
    *,
    config: TeamMemorySpecialistResolutionLatencyScoreV2Config,
    latency_score: Decimal,
    learning_loop_score: Decimal,
    resolution_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if latency_score < _HUNDRED:
        reason_codes.append(_HIGH_LATENCY_REASON)
    if (
        source.postmortem_completion_ratio
        < config.min_pass_postmortem_completion_ratio
    ):
        reason_codes.append(_WEAK_POSTMORTEM_REASON)
    if resolution_age_seconds > config.stale_resolution_age_seconds:
        reason_codes.append(_STALE_RESOLUTION_REASON)
    if learning_loop_score < config.min_watch_learning_loop_score:
        reason_codes.append(_LOW_LEARNING_REASON)
    if not reason_codes:
        reason_codes.append(_READY_REASON)
    return tuple(reason_codes)


def _row_status(
    reason_codes: tuple[str, ...],
    learning_loop_score: Decimal,
    config: TeamMemorySpecialistResolutionLatencyScoreV2Config,
) -> str:
    if (
        _LOW_LEARNING_REASON in reason_codes
        or _STALE_RESOLUTION_REASON in reason_codes
        or learning_loop_score < config.min_watch_learning_loop_score
    ):
        return "block"
    if learning_loop_score < config.min_pass_learning_loop_score:
        return "watch"
    if reason_codes != (_READY_REASON,):
        return "watch"
    return "pass"


def _latency_score(
    source: TeamMemorySpecialistResolutionLatencyScoreV2Source,
    config: TeamMemorySpecialistResolutionLatencyScoreV2Config,
) -> Decimal:
    if (
        source.median_resolution_latency_seconds
        <= config.max_pass_median_resolution_latency_seconds
        and source.p95_resolution_latency_seconds
        <= config.max_pass_p95_resolution_latency_seconds
    ):
        return _HUNDRED
    if (
        source.median_resolution_latency_seconds
        <= config.max_watch_median_resolution_latency_seconds
        and source.p95_resolution_latency_seconds
        <= config.max_watch_p95_resolution_latency_seconds
    ):
        return _FIFTY
    return _ZERO


def _score_from_ratio(value: Decimal) -> Decimal:
    return _normalize_score("score", value * _HUNDRED)


def _normalize_sources(
    sources: tuple[
        TeamMemorySpecialistResolutionLatencyScoreV2Source | dict[str, object],
        ...,
    ]
    | list[TeamMemorySpecialistResolutionLatencyScoreV2Source | dict[str, object]],
) -> tuple[TeamMemorySpecialistResolutionLatencyScoreV2Source, ...]:
    if type(sources) not in (tuple, list):
        raise ValueError("sources must be a tuple or list")
    normalized = tuple(_coerce_source(source) for source in sources)
    seen: set[tuple[str, str]] = set()
    for source in normalized:
        key = (source.team_id, source.domain)
        if key in seen:
            raise ValueError("duplicate team_id/domain")
        seen.add(key)
        require_paper_only_flags("specialist resolution latency score source", source)
    return normalized


def _coerce_source(
    source: TeamMemorySpecialistResolutionLatencyScoreV2Source | dict[str, object],
) -> TeamMemorySpecialistResolutionLatencyScoreV2Source:
    if type(source) is TeamMemorySpecialistResolutionLatencyScoreV2Source:
        return source
    if type(source) is dict:
        return TeamMemorySpecialistResolutionLatencyScoreV2Source(**source)
    raise ValueError(
        "sources must contain TeamMemorySpecialistResolutionLatencyScoreV2Source "
        "items",
    )


def _validate_config(
    config: TeamMemorySpecialistResolutionLatencyScoreV2Config,
) -> None:
    if (
        config.max_watch_median_resolution_latency_seconds
        < config.max_pass_median_resolution_latency_seconds
    ):
        raise ValueError(
            "max_watch_median_resolution_latency_seconds must be >= "
            "max_pass_median_resolution_latency_seconds",
        )
    if (
        config.max_watch_p95_resolution_latency_seconds
        < config.max_pass_p95_resolution_latency_seconds
    ):
        raise ValueError(
            "max_watch_p95_resolution_latency_seconds must be >= "
            "max_pass_p95_resolution_latency_seconds",
        )
    if (
        config.min_watch_postmortem_completion_ratio
        > config.min_pass_postmortem_completion_ratio
    ):
        raise ValueError(
            "min_watch_postmortem_completion_ratio must be <= "
            "min_pass_postmortem_completion_ratio",
        )
    if config.min_watch_learning_loop_score > config.min_pass_learning_loop_score:
        raise ValueError(
            "min_watch_learning_loop_score must be <= "
            "min_pass_learning_loop_score",
        )


def _validate_row(row: TeamMemorySpecialistResolutionLatencyScoreV2Row) -> None:
    if row.p95_resolution_latency_seconds < row.median_resolution_latency_seconds:
        raise ValueError(
            "p95_resolution_latency_seconds must be >= "
            "median_resolution_latency_seconds",
        )
    if row.status == "pass" and row.reason_codes != (_READY_REASON,):
        raise ValueError("pass rows must only carry the ready reason code")
    if row.status != "pass" and _READY_REASON in row.reason_codes:
        raise ValueError("ready reason code is only valid for pass rows")


def _validate_report(
    report: TeamMemorySpecialistResolutionLatencyScoreV2Report,
) -> None:
    expected_team_domain_count = _decimal_count(len(report.rows))
    if report.team_domain_count != expected_team_domain_count:
        raise ValueError("team_domain_count does not match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by domain and team_id")
    if len({(row.team_id, row.domain) for row in report.rows}) != len(report.rows):
        raise ValueError("rows contain duplicate team_id/domain")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
        "high_latency_count": _reason_count(report.rows, _HIGH_LATENCY_REASON),
        "weak_postmortem_count": _reason_count(report.rows, _WEAK_POSTMORTEM_REASON),
        "stale_resolution_count": _reason_count(report.rows, _STALE_RESOLUTION_REASON),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} does not match rows")
    learning_scores = tuple(row.learning_loop_score for row in report.rows)
    expected_min_score = min(learning_scores) if learning_scores else _ZERO
    if report.min_learning_loop_score != expected_min_score:
        raise ValueError("min_learning_loop_score does not match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    expected_reason_codes = tuple(
        count.reason_code for count in report.reason_code_counts
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match reason_code_counts")


def _validate_report_digest(
    report: TeamMemorySpecialistResolutionLatencyScoreV2Report,
) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")


def _report_digest(
    report: TeamMemorySpecialistResolutionLatencyScoreV2Report,
) -> str:
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload = dict(payload)
    payload["derived_validation_digest"] = ""
    reject_unsafe_surface_fields(
        "TeamMemorySpecialistResolutionLatencyScoreV2Report.digest",
        payload,
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reason_code_counts(
    rows: tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...],
) -> tuple[TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(counts)
    )


def _normalize_reason_code_counts(
    value: tuple[
        TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount,
        ...,
    ]
    | list[TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount],
) -> tuple[TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    counts = tuple(value)
    for count in counts:
        if type(count) is not TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount items",
            )
        require_paper_only_flags(
            "specialist resolution latency score reason count",
            count,
        )
    if tuple(sorted(counts, key=lambda count: count.reason_code)) != counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    if len({count.reason_code for count in counts}) != len(counts):
        raise ValueError("reason_code_counts contain duplicates")
    return counts


def _normalize_rows(
    value: tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...]
    | list[TeamMemorySpecialistResolutionLatencyScoreV2Row],
) -> tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemorySpecialistResolutionLatencyScoreV2Row:
            raise ValueError(
                "rows must contain "
                "TeamMemorySpecialistResolutionLatencyScoreV2Row items",
            )
        require_paper_only_flags("specialist resolution latency score row", row)
    return rows


def _normalize_reason_codes(
    value: tuple[str, ...] | list[str],
    *,
    allow_empty: bool,
    order: str,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    if reason_codes == (_READY_REASON,):
        return reason_codes
    if order == "row":
        expected = tuple(
            reason_code
            for reason_code in _ROW_REASON_ORDER
            if reason_code in reason_codes
        )
    elif order == "sorted":
        expected = tuple(sorted(reason_codes))
    else:
        raise ValueError("reason_codes order must be row or sorted")
    if reason_codes != expected:
        raise ValueError("reason_codes must be in canonical order")
    return reason_codes


def _require_reason_code(value: str) -> None:
    _require_text("reason_code", value)
    if value not in _ROW_REASON_CODES:
        raise ValueError(f"unknown reason_code: {value}")


def _require_member(name: str, value: str, allowed: frozenset[str]) -> None:
    _require_text(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")


def _require_text(name: str, value: str) -> None:
    if type(value) is not str or value.strip() != value or value == "":
        raise ValueError(f"{name} must be a non-empty canonical string")


def _normalize_digest(value: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(
            "derived_validation_digest must be a sha256 hex digest",
        ) from exc
    return value.lower()


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_ratio(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_score(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _HUNDRED:
        raise ValueError(f"{name} must be between 0 and 100")
    return normalized


def _normalize_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "resolution_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _status_count(
    rows: tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _report_status(
    rows: tuple[TeamMemorySpecialistResolutionLatencyScoreV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: TeamMemorySpecialistResolutionLatencyScoreV2Row,
) -> tuple[str, str]:
    return (row.domain, row.team_id)


__all__ = (
    "DEFAULT_TEAM_MEMORY_SPECIALIST_RESOLUTION_LATENCY_SCORE_V2_CONFIG_VERSION",
    "TeamMemorySpecialistResolutionLatencyScoreV2Config",
    "TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount",
    "TeamMemorySpecialistResolutionLatencyScoreV2Report",
    "TeamMemorySpecialistResolutionLatencyScoreV2Row",
    "TeamMemorySpecialistResolutionLatencyScoreV2Source",
    "build_team_memory_specialist_resolution_latency_score_v2_report",
)
