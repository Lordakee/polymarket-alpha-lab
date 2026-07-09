"""Public-safe report-only cross-domain specialist review load summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION = (
    "research-team-cross-domain-review-load-report-v0"
)
PUBLIC_STATUSES = ("pass", "watch", "block")
REVIEW_DOMAINS = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT_PREC = 28
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")

_ACTIVE_QUEUE_WEIGHT = Decimal("0.247814")
_STALE_MEMORY_WEIGHT = Decimal("0.362665")
_CALIBRATION_BACKLOG_WEIGHT = Decimal("0.443234")

_ROW_REASON_CODE_SEQUENCE = (
    "cross_domain_review_load_pass",
    "cross_domain_review_load_watch",
    "cross_domain_review_load_block",
    "active_queue_pressure_pass",
    "active_queue_pressure_watch",
    "active_queue_pressure_block",
    "stale_memory_pressure_pass",
    "stale_memory_pressure_watch",
    "stale_memory_pressure_block",
    "calibration_backlog_pressure_pass",
    "calibration_backlog_pressure_watch",
    "calibration_backlog_pressure_block",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "cross_domain_review_load_report_pass",
    "cross_domain_review_load_report_watch",
    "cross_domain_review_load_report_block",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate_id",
    "candidateid",
    "event_id",
    "eventid",
    "market_id",
    "marketid",
    "market_slug",
    "marketslug",
    "market_question",
    "source_id",
    "sourceid",
    "source_ref",
    "source_reference",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database_url",
    "dsn",
    "table_name",
    "table",
    "token",
    "secret",
    "credential",
    "password",
    "private_key",
    "api_key",
    "auth",
    "wallet",
    "order",
    "trade",
    "live",
    "execution",
    "position",
    "buy",
    "sell",
    "recommendation",
    "sizing",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "REVIEW_DOMAINS",
    "ResearchTeamCrossDomainReviewLoadConfig",
    "ResearchTeamCrossDomainReviewLoadObservation",
    "ResearchTeamCrossDomainReviewLoadRow",
    "ResearchTeamCrossDomainReviewLoadReport",
    "build_research_team_cross_domain_review_load_report",
    "research_team_cross_domain_review_load_payload",
    "format_research_team_cross_domain_review_load_digest",
)


@dataclass(frozen=True)
class ResearchTeamCrossDomainReviewLoadConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION
    )
    pass_review_load_score_threshold: Decimal = Decimal("0.350000")
    block_review_load_score_threshold: Decimal = Decimal("0.800000")
    stale_memory_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainReviewLoadConfig:
            raise TypeError(
                "ResearchTeamCrossDomainReviewLoadConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainReviewLoadConfig:
            raise ValueError(
                "config must be exactly ResearchTeamCrossDomainReviewLoadConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "pass_review_load_score_threshold",
            "block_review_load_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_review_load_score_threshold > self.block_review_load_score_threshold:
            raise ValueError(
                "block_review_load_score_threshold must be at least "
                "pass_review_load_score_threshold",
            )
        object.__setattr__(
            self,
            "stale_memory_age_seconds",
            _require_positive_decimal(
                "stale_memory_age_seconds",
                self.stale_memory_age_seconds,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainReviewLoadObservation:
    team_id: str
    domain: str
    capacity_points: Decimal
    active_queue_points: Decimal
    stale_memory_count: Decimal
    oldest_memory_age_seconds: Decimal
    calibration_backlog_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainReviewLoadObservation:
            raise TypeError(
                "ResearchTeamCrossDomainReviewLoadObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainReviewLoadObservation:
            raise ValueError(
                "observation must be exactly ResearchTeamCrossDomainReviewLoadObservation",
            )
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        object.__setattr__(
            self,
            "capacity_points",
            _require_positive_decimal("capacity_points", self.capacity_points),
        )
        object.__setattr__(
            self,
            "active_queue_points",
            _require_nonnegative_decimal(
                "active_queue_points",
                self.active_queue_points,
            ),
        )
        for field_name in ("stale_memory_count", "calibration_backlog_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _require_nonnegative_decimal(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainReviewLoadRow:
    team_id: str
    domain: str
    capacity_points: Decimal
    active_queue_points: Decimal
    active_queue_pressure: Decimal
    stale_memory_count: Decimal
    oldest_memory_age_seconds: Decimal
    stale_memory_pressure: Decimal
    calibration_backlog_count: Decimal
    calibration_backlog_pressure: Decimal
    review_load_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainReviewLoadRow:
            raise TypeError(
                "ResearchTeamCrossDomainReviewLoadRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainReviewLoadRow:
            raise ValueError("row must be exactly ResearchTeamCrossDomainReviewLoadRow")
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        object.__setattr__(
            self,
            "capacity_points",
            _require_positive_decimal("capacity_points", self.capacity_points),
        )
        for field_name in (
            "active_queue_points",
            "oldest_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_memory_count", "calibration_backlog_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "active_queue_pressure",
            "stale_memory_pressure",
            "calibration_backlog_pressure",
            "review_load_score",
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
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainReviewLoadReport:
    generated_at: datetime
    config_version: str
    report_status: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_capacity_points: Decimal
    total_active_queue_points: Decimal
    total_stale_memory_count: Decimal
    total_calibration_backlog_count: Decimal
    max_review_load_score: Decimal
    average_review_load_score: Decimal
    rows: tuple[ResearchTeamCrossDomainReviewLoadRow, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamCrossDomainReviewLoadReport:
            raise TypeError(
                "ResearchTeamCrossDomainReviewLoadReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCrossDomainReviewLoadReport:
            raise ValueError(
                "report must be exactly ResearchTeamCrossDomainReviewLoadReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_status("report_status", self.report_status)
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_capacity_points",
            "total_active_queue_points",
            "max_review_load_score",
            "average_review_load_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_stale_memory_count",
            "total_calibration_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_review_load_score", "average_review_load_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        else:
            _require_public_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")


def build_research_team_cross_domain_review_load_report(
    observations: Sequence[ResearchTeamCrossDomainReviewLoadObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamCrossDomainReviewLoadConfig | None = None,
) -> ResearchTeamCrossDomainReviewLoadReport:
    cfg = config or ResearchTeamCrossDomainReviewLoadConfig()
    if type(cfg) is not ResearchTeamCrossDomainReviewLoadConfig:
        raise ValueError(
            "config must be a ResearchTeamCrossDomainReviewLoadConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted((_row_from_observation(row, cfg) for row in normalized), key=_row_sort_key),
    )
    report_status = _report_status(rows)
    return ResearchTeamCrossDomainReviewLoadReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        team_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        total_capacity_points=_sum_decimal(row.capacity_points for row in rows),
        total_active_queue_points=_sum_decimal(row.active_queue_points for row in rows),
        total_stale_memory_count=_sum_decimal(row.stale_memory_count for row in rows),
        total_calibration_backlog_count=_sum_decimal(
            row.calibration_backlog_count for row in rows
        ),
        max_review_load_score=max(
            (row.review_load_score for row in rows),
            default=_ZERO,
        ),
        average_review_load_score=_average_decimal(
            row.review_load_score for row in rows
        ),
        rows=rows,
        reason_codes=(f"cross_domain_review_load_report_{report_status}",),
    )


def research_team_cross_domain_review_load_payload(
    report: ResearchTeamCrossDomainReviewLoadReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamCrossDomainReviewLoadReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamCrossDomainReviewLoadReport or payload",
    )


def format_research_team_cross_domain_review_load_digest(
    report: ResearchTeamCrossDomainReviewLoadReport,
) -> str:
    if type(report) is not ResearchTeamCrossDomainReviewLoadReport:
        raise ValueError("report must be a ResearchTeamCrossDomainReviewLoadReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    return (
        "research-team-cross-domain-review-load: "
        f"generated_at={report.generated_at.isoformat()} "
        f"status={report.report_status} "
        f"teams={report.team_count} "
        f"pass={report.pass_count} "
        f"watch={report.watch_count} "
        f"block={report.block_count} "
        f"capacity={report.total_capacity_points} "
        f"active_queue_points={report.total_active_queue_points} "
        f"stale_memory_count={report.total_stale_memory_count} "
        f"calibration_backlog_count={report.total_calibration_backlog_count} "
        f"max_score={report.max_review_load_score} "
        f"average_score={report.average_review_load_score} "
        f"reason_codes={','.join(report.reason_codes)} "
        f"public_digest={report.public_digest} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}\n"
    )


def _row_from_observation(
    observation: ResearchTeamCrossDomainReviewLoadObservation,
    config: ResearchTeamCrossDomainReviewLoadConfig,
) -> ResearchTeamCrossDomainReviewLoadRow:
    active_queue_pressure = _clamp_ratio(
        _ratio_or_zero(observation.active_queue_points, observation.capacity_points),
    )
    stale_memory_pressure = _stale_memory_pressure(observation, config)
    calibration_backlog_pressure = _clamp_ratio(
        _ratio_or_zero(observation.calibration_backlog_count, observation.capacity_points),
    )
    review_load_score = _review_load_score(
        active_queue_pressure=active_queue_pressure,
        stale_memory_pressure=stale_memory_pressure,
        calibration_backlog_pressure=calibration_backlog_pressure,
    )
    status = _score_status(review_load_score, config)
    return ResearchTeamCrossDomainReviewLoadRow(
        team_id=observation.team_id,
        domain=observation.domain,
        capacity_points=observation.capacity_points,
        active_queue_points=observation.active_queue_points,
        active_queue_pressure=active_queue_pressure,
        stale_memory_count=observation.stale_memory_count,
        oldest_memory_age_seconds=observation.oldest_memory_age_seconds,
        stale_memory_pressure=stale_memory_pressure,
        calibration_backlog_count=observation.calibration_backlog_count,
        calibration_backlog_pressure=calibration_backlog_pressure,
        review_load_score=review_load_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            active_queue_pressure=active_queue_pressure,
            stale_memory_pressure=stale_memory_pressure,
            calibration_backlog_pressure=calibration_backlog_pressure,
            config=config,
        ),
    )


def _stale_memory_pressure(
    observation: ResearchTeamCrossDomainReviewLoadObservation,
    config: ResearchTeamCrossDomainReviewLoadConfig,
) -> Decimal:
    if observation.stale_memory_count == _ZERO:
        return _ZERO
    return _clamp_ratio(
        observation.oldest_memory_age_seconds / config.stale_memory_age_seconds,
    )


def _review_load_score(
    *,
    active_queue_pressure: Decimal,
    stale_memory_pressure: Decimal,
    calibration_backlog_pressure: Decimal,
) -> Decimal:
    return _clamp_ratio(
        active_queue_pressure * _ACTIVE_QUEUE_WEIGHT
        + stale_memory_pressure * _STALE_MEMORY_WEIGHT
        + calibration_backlog_pressure * _CALIBRATION_BACKLOG_WEIGHT,
    )


def _score_status(
    score: Decimal,
    config: ResearchTeamCrossDomainReviewLoadConfig,
) -> str:
    if score >= config.block_review_load_score_threshold:
        return "block"
    if score > config.pass_review_load_score_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    active_queue_pressure: Decimal,
    stale_memory_pressure: Decimal,
    calibration_backlog_pressure: Decimal,
    config: ResearchTeamCrossDomainReviewLoadConfig,
) -> tuple[str, ...]:
    return _normalize_row_reason_codes(
        (
            f"cross_domain_review_load_{status}",
            _pressure_reason("active_queue_pressure", active_queue_pressure, config),
            _pressure_reason("stale_memory_pressure", stale_memory_pressure, config),
            _pressure_reason(
                "calibration_backlog_pressure",
                calibration_backlog_pressure,
                config,
            ),
        ),
    )


def _pressure_reason(
    prefix: str,
    value: Decimal,
    config: ResearchTeamCrossDomainReviewLoadConfig,
) -> str:
    if value >= config.block_review_load_score_threshold:
        return f"{prefix}_block"
    if value > config.pass_review_load_score_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_observations(
    observations: Sequence[ResearchTeamCrossDomainReviewLoadObservation],
) -> tuple[ResearchTeamCrossDomainReviewLoadObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchTeamCrossDomainReviewLoadObservation:
            raise ValueError(
                "observations must contain ResearchTeamCrossDomainReviewLoadObservation",
            )
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.domain)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamCrossDomainReviewLoadRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamCrossDomainReviewLoadRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamCrossDomainReviewLoadRow",
        ) from exc
    for row in normalized:
        if type(row) is not ResearchTeamCrossDomainReviewLoadRow:
            raise ValueError(
                "rows must contain ResearchTeamCrossDomainReviewLoadRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchTeamCrossDomainReviewLoadRow,
) -> tuple[int, Decimal, str, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (status_rank[row.status], -row.review_load_score, row.team_id, row.domain)


def _report_status(rows: tuple[ResearchTeamCrossDomainReviewLoadRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamCrossDomainReviewLoadRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_report(report: ResearchTeamCrossDomainReviewLoadReport) -> None:
    if report.team_count != _count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.total_capacity_points != _sum_decimal(
        row.capacity_points for row in report.rows
    ):
        raise ValueError("total_capacity_points must match rows")
    if report.total_active_queue_points != _sum_decimal(
        row.active_queue_points for row in report.rows
    ):
        raise ValueError("total_active_queue_points must match rows")
    if report.total_stale_memory_count != _sum_decimal(
        row.stale_memory_count for row in report.rows
    ):
        raise ValueError("total_stale_memory_count must match rows")
    if report.total_calibration_backlog_count != _sum_decimal(
        row.calibration_backlog_count for row in report.rows
    ):
        raise ValueError("total_calibration_backlog_count must match rows")
    if report.max_review_load_score != max(
        (row.review_load_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_review_load_score must match rows")
    if report.average_review_load_score != _average_decimal(
        row.review_load_score for row in report.rows
    ):
        raise ValueError("average_review_load_score must match rows")
    if report.reason_codes != (f"cross_domain_review_load_report_{report.report_status}",):
        raise ValueError("reason_codes must match report_status")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        value,
        _ROW_REASON_CODE_SEQUENCE,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        value,
        _REPORT_REASON_CODE_SEQUENCE,
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"reason_code must be one of {allowed}")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=allowed.index))


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_text(field_name, value)
    return value


def _require_domain(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REVIEW_DOMAINS:
        raise ValueError(f"{field_name} must be one of {REVIEW_DOMAINS}")
    _reject_unsafe_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of {PUBLIC_STATUSES}")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must set {field_name}=True")


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in _FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must set {field_name}=True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "public_digest":
                continue
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if key != "public_digest":
                _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(_unsafe_term_matches(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} must not expose raw identifiers or execution terms")


def _unsafe_term_matches(value: str, term: str) -> bool:
    if "://" in term or "_" in term:
        return term in value
    return re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", value) is not None


def _public_digest_for_report(report: ResearchTeamCrossDomainReviewLoadReport) -> str:
    values = asdict(report)
    values.pop("public_digest", None)
    return _public_digest(values)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("public_digest")
    _require_public_digest("public_digest", digest)
    values = dict(payload)
    values.pop("public_digest", None)
    expected = _public_digest(values)
    if digest != expected:
        raise ValueError("public_digest must match payload")


def _public_digest(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return f"{value:.6f}"
    return value


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    total = _ZERO
    for value in values:
        total = _decimal(total + value)
    return total


def _average_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return _decimal(_sum_decimal(normalized) / Decimal(len(normalized)))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _decimal(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PREC
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)
