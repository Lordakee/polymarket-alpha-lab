"""Pure report for domain signal review backlog pressure."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import (
    Context,
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_HALF_EVEN,
    localcontext,
)
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_SIGNAL_REVIEW_BACKLOG_REPORT_CONFIG_VERSION = (
    "research-team-domain-signal-review-backlog-report-v1"
)
DOMAIN_SIGNAL_REVIEW_BACKLOG_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIVE = Decimal("5.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_HEX_CHARS = frozenset("0123456789abcdef")
_MAX_TEXT_BYTES = 2048
_SAFE_PUBLIC_KEYS = frozenset(("source_fingerprint", "team_fingerprint"))
_BLOCK_REASONS = frozenset(
    (
        "pending_load_block",
        "stale_signal_block",
        "conflict_signal_block",
        "review_age_block",
        "memory_gap_block",
    ),
)
_PASS_REASONS = frozenset(("domain_signal_review_backlog_pass",))
_REASON_PRIORITY = (
    "pending_load_block",
    "pending_load_watch",
    "stale_signal_block",
    "stale_signal_watch",
    "conflict_signal_block",
    "conflict_signal_watch",
    "review_age_block",
    "review_age_watch",
    "memory_gap_block",
    "memory_gap_watch",
    "domain_signal_review_backlog_pass",
    "research_team_domain_signal_review_backlog_report_empty",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "can" "didate",
    "mar" "ket",
    "sl" "ug",
    "ques" "tion",
    "source",
    "u" "rl",
    "://" ,
    "d" "sn",
    "ta" "ble",
    "tok" "en",
    "wal" "let",
    "or" "der",
    "tr" "ade",
    "li" "ve",
    "au" "th",
    "reco" "mmend",
    "siz" "ing",
    "b" "uy",
    "se" "ll",
)


@dataclass(frozen=True)
class ResearchTeamDomainSignalReviewBacklogConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SIGNAL_REVIEW_BACKLOG_REPORT_CONFIG_VERSION
    )
    pending_load_watch_threshold: Decimal = Decimal("0.500000")
    pending_load_block_threshold: Decimal = Decimal("1.000000")
    stale_signal_watch_threshold: Decimal = Decimal("0.250000")
    stale_signal_block_threshold: Decimal = Decimal("0.500000")
    conflict_signal_watch_threshold: Decimal = Decimal("0.100000")
    conflict_signal_block_threshold: Decimal = Decimal("0.300000")
    review_age_watch_hours: Decimal = Decimal("24.000000")
    review_age_block_hours: Decimal = Decimal("72.000000")
    memory_gap_watch_threshold: Decimal = Decimal("0.250000")
    memory_gap_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSignalReviewBacklogConfig:
            raise TypeError(
                "ResearchTeamDomainSignalReviewBacklogConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSignalReviewBacklogConfig:
            raise ValueError(
                "config must be exactly ResearchTeamDomainSignalReviewBacklogConfig",
            )
        _require_public_text("config_version", self.config_version)
        for watch_field, block_field in (
            ("pending_load_watch_threshold", "pending_load_block_threshold"),
            ("stale_signal_watch_threshold", "stale_signal_block_threshold"),
            ("conflict_signal_watch_threshold", "conflict_signal_block_threshold"),
            ("review_age_watch_hours", "review_age_block_hours"),
            ("memory_gap_watch_threshold", "memory_gap_block_threshold"),
        ):
            _require_watch_not_above_block(
                _normalize_decimal(watch_field, getattr(self, watch_field)),
                _normalize_decimal(block_field, getattr(self, block_field)),
            )
        for field_name in (
            "pending_load_watch_threshold",
            "pending_load_block_threshold",
            "stale_signal_watch_threshold",
            "stale_signal_block_threshold",
            "conflict_signal_watch_threshold",
            "conflict_signal_block_threshold",
            "memory_gap_watch_threshold",
            "memory_gap_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("review_age_watch_hours", "review_age_block_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pending_load_block_threshold",
            "stale_signal_block_threshold",
            "conflict_signal_block_threshold",
            "memory_gap_block_threshold",
        ):
            if getattr(self, field_name) <= _ZERO:
                raise ValueError(f"{field_name} must remain positive after quantization")
        _require_watch_not_above_block(
            self.pending_load_watch_threshold,
            self.pending_load_block_threshold,
        )
        _require_watch_not_above_block(
            self.stale_signal_watch_threshold,
            self.stale_signal_block_threshold,
        )
        _require_watch_not_above_block(
            self.conflict_signal_watch_threshold,
            self.conflict_signal_block_threshold,
        )
        _require_watch_not_above_block(
            self.review_age_watch_hours,
            self.review_age_block_hours,
        )
        _require_watch_not_above_block(
            self.memory_gap_watch_threshold,
            self.memory_gap_block_threshold,
        )
        require_paper_only_flags("domain signal review backlog config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSignalReviewBacklogInput:
    backlog_key: str
    domain_key: str
    team_key: str
    source_key: str
    reviewer_capacity_points: Decimal
    pending_signal_count: Decimal
    stale_signal_count: Decimal
    conflict_signal_count: Decimal
    oldest_unreviewed_age_hours: Decimal
    memory_gap_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSignalReviewBacklogInput:
            raise TypeError(
                "ResearchTeamDomainSignalReviewBacklogInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSignalReviewBacklogInput:
            raise ValueError(
                "input must be exactly ResearchTeamDomainSignalReviewBacklogInput",
            )
        _require_private_key("backlog_key", self.backlog_key)
        _require_private_key("domain_key", self.domain_key)
        _require_private_key("team_key", self.team_key)
        _require_private_key("source_key", self.source_key)
        object.__setattr__(
            self,
            "reviewer_capacity_points",
            _normalize_positive_decimal(
                "reviewer_capacity_points",
                self.reviewer_capacity_points,
            ),
        )
        for field_name in (
            "pending_signal_count",
            "stale_signal_count",
            "conflict_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.stale_signal_count > self.pending_signal_count:
            raise ValueError(
                "stale_signal_count must be at most pending_signal_count",
            )
        if self.conflict_signal_count > self.pending_signal_count:
            raise ValueError(
                "conflict_signal_count must be at most pending_signal_count",
            )
        object.__setattr__(
            self,
            "oldest_unreviewed_age_hours",
            _normalize_nonnegative_decimal(
                "oldest_unreviewed_age_hours",
                self.oldest_unreviewed_age_hours,
            ),
        )
        if (
            self.pending_signal_count == _ZERO
            and self.oldest_unreviewed_age_hours != _ZERO
        ):
            raise ValueError(
                "oldest_unreviewed_age_hours must be zero when "
                "pending_signal_count is zero",
            )
        object.__setattr__(
            self,
            "memory_gap_ratio",
            _normalize_unit_decimal("memory_gap_ratio", self.memory_gap_ratio),
        )
        require_paper_only_flags("domain signal review backlog input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSignalReviewBacklogRow:
    priority_rank: Decimal
    backlog_fingerprint: str
    domain_fingerprint: str
    team_fingerprint: str
    source_fingerprint: str
    reviewer_capacity_points: Decimal
    pending_signal_count: Decimal
    stale_signal_count: Decimal
    conflict_signal_count: Decimal
    pending_load_ratio: Decimal
    stale_signal_ratio: Decimal
    conflict_signal_ratio: Decimal
    oldest_unreviewed_age_hours: Decimal
    memory_gap_ratio: Decimal
    pending_load_score: Decimal
    stale_signal_score: Decimal
    conflict_signal_score: Decimal
    review_age_score: Decimal
    memory_gap_score: Decimal
    backlog_score: Decimal
    manual_review_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSignalReviewBacklogRow:
            raise TypeError(
                "ResearchTeamDomainSignalReviewBacklogRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSignalReviewBacklogRow:
            raise ValueError("row must be exactly ResearchTeamDomainSignalReviewBacklogRow")
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        for field_name in (
            "backlog_fingerprint",
            "domain_fingerprint",
            "team_fingerprint",
            "source_fingerprint",
        ):
            _require_digest(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reviewer_capacity_points",
            _normalize_positive_decimal(
                "reviewer_capacity_points",
                self.reviewer_capacity_points,
            ),
        )
        for field_name in (
            "pending_signal_count",
            "stale_signal_count",
            "conflict_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.stale_signal_count > self.pending_signal_count:
            raise ValueError(
                "stale_signal_count must be at most pending_signal_count",
            )
        if self.conflict_signal_count > self.pending_signal_count:
            raise ValueError(
                "conflict_signal_count must be at most pending_signal_count",
            )
        for field_name in (
            "pending_load_ratio",
            "stale_signal_ratio",
            "conflict_signal_ratio",
            "oldest_unreviewed_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pending_signal_count == _ZERO
            and self.oldest_unreviewed_age_hours != _ZERO
        ):
            raise ValueError(
                "oldest_unreviewed_age_hours must be zero when "
                "pending_signal_count is zero",
            )
        for field_name in (
            "memory_gap_ratio",
            "pending_load_score",
            "stale_signal_score",
            "conflict_signal_score",
            "review_age_score",
            "memory_gap_score",
            "backlog_score",
            "manual_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        require_paper_only_flags("domain signal review backlog row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamDomainSignalReviewBacklogReport:
    generated_at: datetime
    config_version: str
    backlog_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_pending_signal_count: Decimal
    total_stale_signal_count: Decimal
    total_conflict_signal_count: Decimal
    max_backlog_score: Decimal | None
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamDomainSignalReviewBacklogRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSignalReviewBacklogReport:
            raise TypeError(
                "ResearchTeamDomainSignalReviewBacklogReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSignalReviewBacklogReport:
            raise ValueError(
                "report must be exactly ResearchTeamDomainSignalReviewBacklogReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "backlog_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pending_signal_count",
            "total_stale_signal_count",
            "total_conflict_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.max_backlog_score is not None:
            object.__setattr__(
                self,
                "max_backlog_score",
                _normalize_unit_decimal(
                    "max_backlog_score",
                    self.max_backlog_score,
                ),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        require_paper_only_flags("domain signal review backlog report", self)
        _validate_report(self)


def build_research_team_domain_signal_review_backlog_report(
    backlog_items: Iterable[ResearchTeamDomainSignalReviewBacklogInput],
    *,
    config: ResearchTeamDomainSignalReviewBacklogConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSignalReviewBacklogReport:
    config = _revalidate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_backlog_items(backlog_items)
    rows = _rank_rows(
        tuple(
            _row_from_input(item, config=config)
            for item in normalized_items
        ),
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "backlog_count": _count(len(rows)),
        "pass_count": _row_status_count(rows, "pass"),
        "watch_count": _row_status_count(rows, "watch"),
        "block_count": _row_status_count(rows, "block"),
        "total_pending_signal_count": _quantize_count(
            _sum_decimal(row.pending_signal_count for row in rows),
        ),
        "total_stale_signal_count": _quantize_count(
            _sum_decimal(row.stale_signal_count for row in rows),
        ),
        "total_conflict_signal_count": _quantize_count(
            _sum_decimal(row.conflict_signal_count for row in rows),
        ),
        "max_backlog_score": None if not rows else max(row.backlog_score for row in rows),
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    built_report = ResearchTeamDomainSignalReviewBacklogReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )
    object.__setattr__(built_report, "_validation_config", config)
    return built_report


def research_team_domain_signal_review_backlog_report_payload(
    report: ResearchTeamDomainSignalReviewBacklogReport | dict[str, Any],
    *,
    validation_config: ResearchTeamDomainSignalReviewBacklogConfig | None = None,
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainSignalReviewBacklogReport:
        require_paper_only_flags("domain signal review backlog report", report)
        _validate_report(report)
        if validation_config is None:
            validation_config = getattr(report, "_validation_config", None)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSignalReviewBacklogReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags(
        "domain signal review backlog payload",
        _PayloadFlags(payload),
    )
    resolved_config = _resolve_public_validation_config(
        payload,
        validation_config=validation_config,
    )
    _validate_public_payload(payload, validation_config=resolved_config)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _resolve_public_validation_config(
    payload: dict[str, Any],
    *,
    validation_config: ResearchTeamDomainSignalReviewBacklogConfig | None,
) -> ResearchTeamDomainSignalReviewBacklogConfig:
    if validation_config is None:
        if payload.get("config_version") != (
            DEFAULT_RESEARCH_TEAM_DOMAIN_SIGNAL_REVIEW_BACKLOG_REPORT_CONFIG_VERSION
        ):
            raise ValueError(
                "validation_config is required for a non-default config_version",
            )
        return ResearchTeamDomainSignalReviewBacklogConfig()
    validation_config = _revalidate_config(validation_config, label="validation_config")
    if payload.get("config_version") != validation_config.config_version:
        raise ValueError("validation_config must match config_version")
    return validation_config


def _revalidate_config(
    config: ResearchTeamDomainSignalReviewBacklogConfig,
    *,
    label: str = "config",
) -> ResearchTeamDomainSignalReviewBacklogConfig:
    if type(config) is not ResearchTeamDomainSignalReviewBacklogConfig:
        raise ValueError(
            f"{label} must be a ResearchTeamDomainSignalReviewBacklogConfig",
        )
    return ResearchTeamDomainSignalReviewBacklogConfig(
        **{
            field.name: getattr(config, field.name)
            for field in fields(ResearchTeamDomainSignalReviewBacklogConfig)
        },
    )


def _validate_public_payload(
    payload: dict[str, Any],
    *,
    validation_config: ResearchTeamDomainSignalReviewBacklogConfig,
) -> None:
    _validate_public_digests(payload)
    reconstructed = _report_from_public_payload(
        payload,
        validation_config=validation_config,
    )
    canonical_payload = _json_ready(reconstructed)
    if canonical_payload != payload:
        raise ValueError("public payload must use the exact canonical schema")


def _report_from_public_payload(
    payload: dict[str, Any],
    *,
    validation_config: ResearchTeamDomainSignalReviewBacklogConfig,
) -> ResearchTeamDomainSignalReviewBacklogReport:
    _require_exact_payload_schema(
        "public payload",
        payload,
        ResearchTeamDomainSignalReviewBacklogReport,
    )
    rows = tuple(
        _row_from_public_payload(
            row_payload,
            index=index,
            validation_config=validation_config,
        )
        for index, row_payload in enumerate(
            _require_public_list("rows", payload["rows"]),
        )
    )
    return ResearchTeamDomainSignalReviewBacklogReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        backlog_count=_public_decimal("backlog_count", payload["backlog_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        total_pending_signal_count=_public_decimal(
            "total_pending_signal_count",
            payload["total_pending_signal_count"],
        ),
        total_stale_signal_count=_public_decimal(
            "total_stale_signal_count",
            payload["total_stale_signal_count"],
        ),
        total_conflict_signal_count=_public_decimal(
            "total_conflict_signal_count",
            payload["total_conflict_signal_count"],
        ),
        max_backlog_score=_public_optional_decimal(
            "max_backlog_score",
            payload["max_backlog_score"],
        ),
        report_status=payload["report_status"],
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        rows=rows,
        validation_digest=payload["validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
    validation_config: ResearchTeamDomainSignalReviewBacklogConfig,
) -> ResearchTeamDomainSignalReviewBacklogRow:
    label = f"rows[{index}]"
    payload = _require_public_dict(label, value)
    _require_exact_payload_schema(
        label,
        payload,
        ResearchTeamDomainSignalReviewBacklogRow,
    )
    row = ResearchTeamDomainSignalReviewBacklogRow(
        priority_rank=_public_decimal(
            f"{label}.priority_rank",
            payload["priority_rank"],
        ),
        backlog_fingerprint=payload["backlog_fingerprint"],
        domain_fingerprint=payload["domain_fingerprint"],
        team_fingerprint=payload["team_fingerprint"],
        source_fingerprint=payload["source_fingerprint"],
        reviewer_capacity_points=_public_decimal(
            f"{label}.reviewer_capacity_points",
            payload["reviewer_capacity_points"],
        ),
        pending_signal_count=_public_decimal(
            f"{label}.pending_signal_count",
            payload["pending_signal_count"],
        ),
        stale_signal_count=_public_decimal(
            f"{label}.stale_signal_count",
            payload["stale_signal_count"],
        ),
        conflict_signal_count=_public_decimal(
            f"{label}.conflict_signal_count",
            payload["conflict_signal_count"],
        ),
        pending_load_ratio=_public_decimal(
            f"{label}.pending_load_ratio",
            payload["pending_load_ratio"],
        ),
        stale_signal_ratio=_public_decimal(
            f"{label}.stale_signal_ratio",
            payload["stale_signal_ratio"],
        ),
        conflict_signal_ratio=_public_decimal(
            f"{label}.conflict_signal_ratio",
            payload["conflict_signal_ratio"],
        ),
        oldest_unreviewed_age_hours=_public_decimal(
            f"{label}.oldest_unreviewed_age_hours",
            payload["oldest_unreviewed_age_hours"],
        ),
        memory_gap_ratio=_public_decimal(
            f"{label}.memory_gap_ratio",
            payload["memory_gap_ratio"],
        ),
        pending_load_score=_public_decimal(
            f"{label}.pending_load_score",
            payload["pending_load_score"],
        ),
        stale_signal_score=_public_decimal(
            f"{label}.stale_signal_score",
            payload["stale_signal_score"],
        ),
        conflict_signal_score=_public_decimal(
            f"{label}.conflict_signal_score",
            payload["conflict_signal_score"],
        ),
        review_age_score=_public_decimal(
            f"{label}.review_age_score",
            payload["review_age_score"],
        ),
        memory_gap_score=_public_decimal(
            f"{label}.memory_gap_score",
            payload["memory_gap_score"],
        ),
        backlog_score=_public_decimal(
            f"{label}.backlog_score",
            payload["backlog_score"],
        ),
        manual_review_priority_score=_public_decimal(
            f"{label}.manual_review_priority_score",
            payload["manual_review_priority_score"],
        ),
        status=payload["status"],
        reason_codes=_public_string_tuple(
            f"{label}.reason_codes",
            payload["reason_codes"],
        ),
        validation_digest=payload["validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    _validate_row_against_config(row, config=validation_config)
    return row


def _require_exact_payload_schema(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = tuple(field.name for field in fields(expected_type))
    if tuple(payload) != expected_fields:
        raise ValueError(f"{label} keys must match the exact schema")


def _require_public_dict(label: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object in the public schema")
    return value


def _require_public_list(label: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list in the public schema")
    return value


def _public_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a Decimal string in the public schema")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"{label} must be a Decimal string in the public schema",
        ) from exc


def _public_optional_decimal(label: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _public_decimal(label, value)


def _public_datetime(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be an ISO-8601 datetime in the public schema")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{label} must be an ISO-8601 datetime in the public schema",
        ) from exc
    return _as_utc(label, parsed)


def _public_string_tuple(label: str, value: object) -> tuple[str, ...]:
    return tuple(_require_public_list(label, value))


def _normalize_backlog_items(
    backlog_items: Iterable[ResearchTeamDomainSignalReviewBacklogInput],
) -> tuple[ResearchTeamDomainSignalReviewBacklogInput, ...]:
    if isinstance(backlog_items, (str, bytes)):
        raise ValueError("backlog_items must be an iterable")
    try:
        items = tuple(backlog_items)
    except TypeError as exc:
        raise ValueError("backlog_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamDomainSignalReviewBacklogInput:
            raise ValueError(
                "backlog_items must contain ResearchTeamDomainSignalReviewBacklogInput",
            )
        require_paper_only_flags("domain signal review backlog input", item)
        if item.backlog_key in seen:
            raise ValueError("backlog_key values must be unique")
        seen.add(item.backlog_key)
    return items


def _row_from_input(
    item: ResearchTeamDomainSignalReviewBacklogInput,
    *,
    config: ResearchTeamDomainSignalReviewBacklogConfig,
) -> ResearchTeamDomainSignalReviewBacklogRow:
    pending_load_ratio = _ratio(item.pending_signal_count, item.reviewer_capacity_points)
    stale_signal_ratio = _ratio_or_zero(item.stale_signal_count, item.pending_signal_count)
    conflict_signal_ratio = _ratio_or_zero(
        item.conflict_signal_count,
        item.pending_signal_count,
    )
    pending_load_score = _capped_ratio(
        pending_load_ratio,
        config.pending_load_block_threshold,
    )
    stale_signal_score = _capped_ratio(
        stale_signal_ratio,
        config.stale_signal_block_threshold,
    )
    conflict_signal_score = _capped_ratio(
        conflict_signal_ratio,
        config.conflict_signal_block_threshold,
    )
    review_age_score = _capped_ratio(
        item.oldest_unreviewed_age_hours,
        config.review_age_block_hours,
    )
    memory_gap_score = _capped_ratio(item.memory_gap_ratio, config.memory_gap_block_threshold)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        pending_load_ratio=pending_load_ratio,
        stale_signal_ratio=stale_signal_ratio,
        conflict_signal_ratio=conflict_signal_ratio,
    )
    backlog_score = _backlog_score(
        (
            pending_load_score,
            stale_signal_score,
            conflict_signal_score,
            review_age_score,
            memory_gap_score,
        ),
    )
    row_values = {
        "priority_rank": _count(1),
        "backlog_fingerprint": _fingerprint(item.backlog_key),
        "domain_fingerprint": _fingerprint(item.domain_key),
        "team_fingerprint": _fingerprint(item.team_key),
        "source_fingerprint": _fingerprint(item.source_key),
        "reviewer_capacity_points": item.reviewer_capacity_points,
        "pending_signal_count": item.pending_signal_count,
        "stale_signal_count": item.stale_signal_count,
        "conflict_signal_count": item.conflict_signal_count,
        "pending_load_ratio": pending_load_ratio,
        "stale_signal_ratio": stale_signal_ratio,
        "conflict_signal_ratio": conflict_signal_ratio,
        "oldest_unreviewed_age_hours": item.oldest_unreviewed_age_hours,
        "memory_gap_ratio": item.memory_gap_ratio,
        "pending_load_score": pending_load_score,
        "stale_signal_score": stale_signal_score,
        "conflict_signal_score": conflict_signal_score,
        "review_age_score": review_age_score,
        "memory_gap_score": memory_gap_score,
        "backlog_score": backlog_score,
        "manual_review_priority_score": _manual_review_priority_score(
            backlog_score,
        ),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    row = ResearchTeamDomainSignalReviewBacklogRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )
    _validate_row_against_config(row, config=config)
    return row


def _rank_rows(
    rows: tuple[ResearchTeamDomainSignalReviewBacklogRow, ...],
) -> tuple[ResearchTeamDomainSignalReviewBacklogRow, ...]:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    ranked_rows: list[ResearchTeamDomainSignalReviewBacklogRow] = []
    for index, row in enumerate(sorted_rows, start=1):
        row_values = _row_digest_values(row)
        row_values["priority_rank"] = _count(index)
        ranked_rows.append(
            ResearchTeamDomainSignalReviewBacklogRow(
                **row_values,
                validation_digest=_validation_digest(row_values),
            ),
        )
    return tuple(ranked_rows)


def _row_reason_codes(
    item: ResearchTeamDomainSignalReviewBacklogInput,
    *,
    config: ResearchTeamDomainSignalReviewBacklogConfig,
    pending_load_ratio: Decimal,
    stale_signal_ratio: Decimal,
    conflict_signal_ratio: Decimal,
) -> tuple[str, ...]:
    return _row_reason_codes_from_values(
        config=config,
        pending_load_ratio=pending_load_ratio,
        stale_signal_ratio=stale_signal_ratio,
        conflict_signal_ratio=conflict_signal_ratio,
        oldest_unreviewed_age_hours=item.oldest_unreviewed_age_hours,
        memory_gap_ratio=item.memory_gap_ratio,
    )


def _row_reason_codes_from_values(
    *,
    config: ResearchTeamDomainSignalReviewBacklogConfig,
    pending_load_ratio: Decimal,
    stale_signal_ratio: Decimal,
    conflict_signal_ratio: Decimal,
    oldest_unreviewed_age_hours: Decimal,
    memory_gap_ratio: Decimal,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if pending_load_ratio >= config.pending_load_block_threshold:
        block_reasons.append("pending_load_block")
    elif pending_load_ratio >= config.pending_load_watch_threshold:
        watch_reasons.append("pending_load_watch")
    if stale_signal_ratio >= config.stale_signal_block_threshold:
        block_reasons.append("stale_signal_block")
    elif stale_signal_ratio >= config.stale_signal_watch_threshold:
        watch_reasons.append("stale_signal_watch")
    if conflict_signal_ratio >= config.conflict_signal_block_threshold:
        block_reasons.append("conflict_signal_block")
    elif conflict_signal_ratio >= config.conflict_signal_watch_threshold:
        watch_reasons.append("conflict_signal_watch")
    if oldest_unreviewed_age_hours >= config.review_age_block_hours:
        block_reasons.append("review_age_block")
    elif oldest_unreviewed_age_hours >= config.review_age_watch_hours:
        watch_reasons.append("review_age_watch")
    if memory_gap_ratio >= config.memory_gap_block_threshold:
        block_reasons.append("memory_gap_block")
    elif memory_gap_ratio >= config.memory_gap_watch_threshold:
        watch_reasons.append("memory_gap_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("domain_signal_review_backlog_pass",)
    return _normalize_row_reason_codes("reason_codes", reasons)


def _backlog_score(component_values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(component_values), _FIVE)


def _manual_review_priority_score(backlog_score: Decimal) -> Decimal:
    return _normalize_unit_decimal(
        "manual_review_priority_score",
        backlog_score,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == ("domain_signal_review_backlog_pass",):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchTeamDomainSignalReviewBacklogRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSignalReviewBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_team_domain_signal_review_backlog_report_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _row_status_count(
    rows: tuple[ResearchTeamDomainSignalReviewBacklogRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamDomainSignalReviewBacklogRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_backlog_fingerprints: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamDomainSignalReviewBacklogRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainSignalReviewBacklogRow",
            )
        require_paper_only_flags("domain signal review backlog row", row)
        _validate_row(row)
        if row.backlog_fingerprint in seen_backlog_fingerprints:
            raise ValueError("backlog_fingerprint values must be unique")
        seen_backlog_fingerprints.add(row.backlog_fingerprint)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    expected_ranks = tuple(_count(index) for index in range(1, len(normalized) + 1))
    if tuple(row.priority_rank for row in normalized) != expected_ranks:
        raise ValueError("priority_rank values must match deterministic rank sequence")
    return normalized


def _validate_row(row: ResearchTeamDomainSignalReviewBacklogRow) -> None:
    if type(row) is not ResearchTeamDomainSignalReviewBacklogRow:
        raise ValueError("rows must contain ResearchTeamDomainSignalReviewBacklogRow")
    for field_name in (
        "backlog_fingerprint",
        "domain_fingerprint",
        "team_fingerprint",
        "source_fingerprint",
    ):
        _require_digest(field_name, getattr(row, field_name))
    _require_canonical_decimal(
        "priority_rank",
        row.priority_rank,
        _normalize_positive_count,
    )
    _require_canonical_decimal(
        "reviewer_capacity_points",
        row.reviewer_capacity_points,
        _normalize_positive_decimal,
    )
    for field_name in (
        "pending_signal_count",
        "stale_signal_count",
        "conflict_signal_count",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_nonnegative_count,
        )
    if row.stale_signal_count > row.pending_signal_count:
        raise ValueError("stale_signal_count must be at most pending_signal_count")
    if row.conflict_signal_count > row.pending_signal_count:
        raise ValueError("conflict_signal_count must be at most pending_signal_count")
    for field_name in (
        "pending_load_ratio",
        "stale_signal_ratio",
        "conflict_signal_ratio",
        "oldest_unreviewed_age_hours",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_nonnegative_decimal,
        )
    if (
        row.pending_signal_count == _ZERO
        and row.oldest_unreviewed_age_hours != _ZERO
    ):
        raise ValueError(
            "oldest_unreviewed_age_hours must be zero when "
            "pending_signal_count is zero",
        )
    for field_name in (
        "memory_gap_ratio",
        "pending_load_score",
        "stale_signal_score",
        "conflict_signal_score",
        "review_age_score",
        "memory_gap_score",
        "backlog_score",
        "manual_review_priority_score",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_unit_decimal,
        )
    _require_status("status", row.status)
    normalized_reason_codes = _normalize_row_reason_codes(
        "reason_codes",
        row.reason_codes,
    )
    if type(row.reason_codes) is not tuple or row.reason_codes != normalized_reason_codes:
        raise ValueError("reason_codes must be canonical")
    _require_digest("validation_digest", row.validation_digest)
    require_paper_only_flags("domain signal review backlog row", row)
    expected_pending_load_ratio = _ratio(
        row.pending_signal_count,
        row.reviewer_capacity_points,
    )
    if row.pending_load_ratio != expected_pending_load_ratio:
        raise ValueError("pending_load_ratio must match counts")
    expected_stale_signal_ratio = _ratio_or_zero(
        row.stale_signal_count,
        row.pending_signal_count,
    )
    if row.stale_signal_ratio != expected_stale_signal_ratio:
        raise ValueError("stale_signal_ratio must match counts")
    expected_conflict_signal_ratio = _ratio_or_zero(
        row.conflict_signal_count,
        row.pending_signal_count,
    )
    if row.conflict_signal_ratio != expected_conflict_signal_ratio:
        raise ValueError("conflict_signal_ratio must match counts")
    expected_score = _backlog_score(
        (
            row.pending_load_score,
            row.stale_signal_score,
            row.conflict_signal_score,
            row.review_age_score,
            row.memory_gap_score,
        ),
    )
    if row.backlog_score != expected_score:
        raise ValueError("backlog_score must match component scores")
    if row.manual_review_priority_score != _manual_review_priority_score(
        row.backlog_score,
    ):
        raise ValueError("manual_review_priority_score must match backlog_score")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_row_against_config(
    row: ResearchTeamDomainSignalReviewBacklogRow,
    *,
    config: ResearchTeamDomainSignalReviewBacklogConfig,
) -> None:
    expected_scores = {
        "pending_load_score": _capped_ratio(
            row.pending_load_ratio,
            config.pending_load_block_threshold,
        ),
        "stale_signal_score": _capped_ratio(
            row.stale_signal_ratio,
            config.stale_signal_block_threshold,
        ),
        "conflict_signal_score": _capped_ratio(
            row.conflict_signal_ratio,
            config.conflict_signal_block_threshold,
        ),
        "review_age_score": _capped_ratio(
            row.oldest_unreviewed_age_hours,
            config.review_age_block_hours,
        ),
        "memory_gap_score": _capped_ratio(
            row.memory_gap_ratio,
            config.memory_gap_block_threshold,
        ),
    }
    for field_name, expected_value in expected_scores.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match row metrics and config")
    expected_reasons = _row_reason_codes_from_values(
        config=config,
        pending_load_ratio=row.pending_load_ratio,
        stale_signal_ratio=row.stale_signal_ratio,
        conflict_signal_ratio=row.conflict_signal_ratio,
        oldest_unreviewed_age_hours=row.oldest_unreviewed_age_hours,
        memory_gap_ratio=row.memory_gap_ratio,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row metrics and config")
    if row.status != _status_from_reason_codes(expected_reasons):
        raise ValueError("status must match row metrics and config")


def _validate_report(report: ResearchTeamDomainSignalReviewBacklogReport) -> None:
    _require_canonical_utc_datetime("generated_at", report.generated_at)
    _require_public_text("config_version", report.config_version)
    for field_name in (
        "backlog_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_pending_signal_count",
        "total_stale_signal_count",
        "total_conflict_signal_count",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(report, field_name),
            _normalize_nonnegative_count,
        )
    if report.max_backlog_score is not None:
        _require_canonical_decimal(
            "max_backlog_score",
            report.max_backlog_score,
            _normalize_unit_decimal,
        )
    _require_status("report_status", report.report_status)
    normalized_reason_codes = _normalize_report_reason_codes(
        "reason_codes",
        report.reason_codes,
    )
    if type(report.reason_codes) is not tuple or report.reason_codes != normalized_reason_codes:
        raise ValueError("reason_codes must be canonical")
    _require_digest("validation_digest", report.validation_digest)
    require_paper_only_flags("domain signal review backlog report", report)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    if report.reason_codes != _normalize_report_reason_codes(
        "reason_codes",
        report.reason_codes,
    ):
        raise ValueError("reason_codes must be canonical")
    for row in report.rows:
        _validate_row(row)
    if report.backlog_count != _count(len(report.rows)):
        raise ValueError("backlog_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_pending_signal_count != _quantize_count(
        _sum_decimal(row.pending_signal_count for row in report.rows),
    ):
        raise ValueError("total_pending_signal_count must match rows")
    if report.total_stale_signal_count != _quantize_count(
        _sum_decimal(row.stale_signal_count for row in report.rows),
    ):
        raise ValueError("total_stale_signal_count must match rows")
    if report.total_conflict_signal_count != _quantize_count(
        _sum_decimal(row.conflict_signal_count for row in report.rows),
    ):
        raise ValueError("total_conflict_signal_count must match rows")
    expected_max = None if not report.rows else max(row.backlog_score for row in report.rows)
    if report.max_backlog_score != expected_max:
        raise ValueError("max_backlog_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchTeamDomainSignalReviewBacklogRow) -> dict[str, Any]:
    return {
        "priority_rank": row.priority_rank,
        "backlog_fingerprint": row.backlog_fingerprint,
        "domain_fingerprint": row.domain_fingerprint,
        "team_fingerprint": row.team_fingerprint,
        "source_fingerprint": row.source_fingerprint,
        "reviewer_capacity_points": row.reviewer_capacity_points,
        "pending_signal_count": row.pending_signal_count,
        "stale_signal_count": row.stale_signal_count,
        "conflict_signal_count": row.conflict_signal_count,
        "pending_load_ratio": row.pending_load_ratio,
        "stale_signal_ratio": row.stale_signal_ratio,
        "conflict_signal_ratio": row.conflict_signal_ratio,
        "oldest_unreviewed_age_hours": row.oldest_unreviewed_age_hours,
        "memory_gap_ratio": row.memory_gap_ratio,
        "pending_load_score": row.pending_load_score,
        "stale_signal_score": row.stale_signal_score,
        "conflict_signal_score": row.conflict_signal_score,
        "review_age_score": row.review_age_score,
        "memory_gap_score": row.memory_gap_score,
        "backlog_score": row.backlog_score,
        "manual_review_priority_score": row.manual_review_priority_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchTeamDomainSignalReviewBacklogReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "backlog_count": report.backlog_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "total_pending_signal_count": report.total_pending_signal_count,
        "total_stale_signal_count": report.total_stale_signal_count,
        "total_conflict_signal_count": report.total_conflict_signal_count,
        "max_backlog_score": report.max_backlog_score,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_sort_key(
    row: ResearchTeamDomainSignalReviewBacklogRow,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        _STATUS_WEIGHT[row.status],
        row.manual_review_priority_score.copy_negate(),
        row.team_fingerprint,
        row.domain_fingerprint,
        row.source_fingerprint,
        row.backlog_fingerprint,
    )


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if "domain_signal_review_backlog_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if codes == ("domain_signal_review_backlog_pass",):
        return codes
    if any(code in _PASS_REASONS for code in codes):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("research_team_domain_signal_review_backlog_report_empty",):
        return codes
    if "research_team_domain_signal_review_backlog_report_empty" in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize_count(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            total = _ZERO
            for value in values:
                total += _normalize_decimal("sum value", value)
            return _quantize(total, name="sum")
    except DecimalException as exc:
        raise ValueError("sum must fit the fixed context") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return _quantize(numerator / denominator, name="ratio")
    except DecimalException as exc:
        raise ValueError("ratio must fit the fixed context") from exc


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _normalize_decimal("numerator", numerator)
    denominator = _normalize_decimal("denominator", denominator)
    if denominator == _ZERO:
        if numerator != _ZERO:
            raise ValueError("numerator must be zero when denominator is zero")
        return _ZERO
    if denominator < _ZERO:
        raise ValueError("denominator must be nonnegative")
    return _ratio(numerator, denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    quantized = _quantize(normalized, name=name)
    if quantized <= _ZERO:
        raise ValueError(f"{name} must remain positive after quantization")
    return quantized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized, name=name)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    try:
        with localcontext(_DECIMAL_CONTEXT):
            if normalized != normalized.to_integral_value():
                raise ValueError(f"{name} must be an integer")
            return _quantize_count(normalized, name=name)
    except DecimalException as exc:
        raise ValueError(f"{name} must fit the fixed context") from exc


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized, name=name)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _require_canonical_decimal(
    name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    normalized = normalizer(name, value)
    if value.as_tuple() != normalized.as_tuple():
        raise ValueError(f"{name} must use a canonical Decimal")
    return normalized


def _quantize(value: Decimal, *, name: str = "decimal value") -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_QUANTUM)
    except DecimalException as exc:
        raise ValueError(f"{name} must fit the fixed context") from exc


def _quantize_count(value: Decimal, *, name: str = "count") -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_COUNT_QUANTUM)
    except DecimalException as exc:
        raise ValueError(f"{name} must fit the fixed context") from exc


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must fit the UTC datetime range") from exc
    if offset is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        return value.astimezone(UTC)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must fit the UTC datetime range") from exc


def _require_canonical_utc_datetime(name: str, value: object) -> datetime:
    normalized = _as_utc(name, value)
    if value.tzinfo is not UTC:
        raise ValueError(f"{name} must be a canonical UTC datetime")
    return normalized


def _require_watch_not_above_block(watch_threshold: Decimal, block_threshold: Decimal) -> None:
    if watch_threshold > block_threshold:
        raise ValueError("watch threshold must not exceed block threshold")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in DOMAIN_SIGNAL_REVIEW_BACKLOG_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_private_key(name: str, value: object) -> None:
    _require_text(name, value)


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be a non-empty canonical string") from exc
    if (
        not value
        or value.strip() != value
        or len(encoded) > _MAX_TEXT_BYTES
        or any(not character.isprintable() for character in value)
    ):
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public value")


def _require_public_key(name: str, value: object) -> None:
    _require_text(name, value)
    if value not in _SAFE_PUBLIC_KEYS:
        _require_public_text(name, value)


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _fingerprint(value: str) -> str:
    _require_private_key("fingerprint value", value)
    return sha256(value.encode("utf-8")).hexdigest()


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_key("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_key("payload key", key)
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


def _validate_public_digests(value: Any) -> None:
    if type(value) is dict:
        digest = value.get("validation_digest")
        if digest is not None:
            _require_digest("validation_digest", digest)
            unsigned_payload = dict(value)
            unsigned_payload.pop("validation_digest", None)
            if digest != _validation_digest(unsigned_payload):
                raise ValueError("validation_digest must match public payload")
        for item in value.values():
            _validate_public_digests(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_digests(item)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SIGNAL_REVIEW_BACKLOG_REPORT_CONFIG_VERSION",
    "DOMAIN_SIGNAL_REVIEW_BACKLOG_STATUSES",
    "ResearchTeamDomainSignalReviewBacklogConfig",
    "ResearchTeamDomainSignalReviewBacklogInput",
    "ResearchTeamDomainSignalReviewBacklogRow",
    "ResearchTeamDomainSignalReviewBacklogReport",
    "build_research_team_domain_signal_review_backlog_report",
    "research_team_domain_signal_review_backlog_report_payload",
)
