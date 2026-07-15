"""Pure report for research-team domain review disagreement queues."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import InitVar, asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION = (
    "research-team-domain-review-disagreement-queue-report-v1"
)
DOMAIN_REVIEW_DISAGREEMENT_QUEUE_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_MAX_PRIVATE_KEY_BYTES = 2048
_HEX_CHARS = frozenset("0123456789abcdef")
_BLOCK_REASONS = frozenset(
    (
        "reviewer_disagreement_block",
        "probability_spread_block",
        "evidence_conflict_block",
        "unresolved_blocker_block",
        "queue_age_block",
        "prior_resolution_miss_block",
    ),
)
_PASS_REASONS = frozenset(("domain_review_disagreement_queue_pass",))
_REASON_PRIORITY = (
    "reviewer_disagreement_block",
    "reviewer_disagreement_watch",
    "probability_spread_block",
    "probability_spread_watch",
    "evidence_conflict_block",
    "evidence_conflict_watch",
    "unresolved_blocker_block",
    "unresolved_blocker_watch",
    "queue_age_block",
    "queue_age_watch",
    "prior_resolution_miss_block",
    "prior_resolution_miss_watch",
    "domain_review_disagreement_queue_pass",
    "research_team_domain_review_disagreement_queue_report_empty",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "can" "didate",
    "mar" "ket",
    "sl" "ug",
    "ques" "tion",
    "source",
    "u" "rl",
    "://",
    "d" "sn",
    "ta" "ble",
    "tok" "en",
    "wal" "let",
    "or" "der",
    "tra" "de",
    "li" "ve",
    "au" "th",
)
_ROW_PAYLOAD_SCHEMA = (
    "queue_fingerprint",
    "domain_fingerprint",
    "reviewer_count",
    "disagreeing_reviewer_count",
    "reviewer_disagreement_ratio",
    "probability_spread",
    "evidence_conflict_ratio",
    "unresolved_blocker_count",
    "queued_at",
    "queue_age_hours",
    "prior_resolution_miss_count",
    "reviewer_disagreement_score",
    "probability_spread_score",
    "evidence_conflict_score",
    "unresolved_blocker_score",
    "queue_age_score",
    "prior_resolution_miss_score",
    "disagreement_queue_score",
    "status",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_SCHEMA = (
    "generated_at",
    "config_version",
    "queue_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_disagreement_queue_score",
    "report_status",
    "reason_codes",
    "rows",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchTeamDomainReviewDisagreementQueueConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION
    )
    reviewer_disagreement_watch_threshold: Decimal = Decimal("0.250000")
    reviewer_disagreement_block_threshold: Decimal = Decimal("0.500000")
    probability_spread_watch_threshold: Decimal = Decimal("0.100000")
    probability_spread_block_threshold: Decimal = Decimal("0.250000")
    evidence_conflict_watch_threshold: Decimal = Decimal("0.250000")
    evidence_conflict_block_threshold: Decimal = Decimal("0.500000")
    unresolved_blocker_watch_threshold: Decimal = Decimal("1")
    unresolved_blocker_block_threshold: Decimal = Decimal("2")
    queue_age_watch_hours: Decimal = Decimal("24.000000")
    queue_age_block_hours: Decimal = Decimal("72.000000")
    prior_resolution_miss_watch_threshold: Decimal = Decimal("1")
    prior_resolution_miss_block_threshold: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamDomainReviewDisagreementQueueConfig,
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        unit_threshold_fields = (
            "reviewer_disagreement_watch_threshold",
            "reviewer_disagreement_block_threshold",
            "probability_spread_watch_threshold",
            "probability_spread_block_threshold",
            "evidence_conflict_watch_threshold",
            "evidence_conflict_block_threshold",
        )
        count_threshold_fields = (
            "unresolved_blocker_watch_threshold",
            "unresolved_blocker_block_threshold",
            "prior_resolution_miss_watch_threshold",
            "prior_resolution_miss_block_threshold",
        )
        age_threshold_fields = (
            "queue_age_watch_hours",
            "queue_age_block_hours",
        )
        raw_thresholds = {
            field_name: _validate_unit_decimal_raw(
                field_name,
                getattr(self, field_name),
            )
            for field_name in unit_threshold_fields
        }
        raw_thresholds.update(
            {
                field_name: _validate_positive_count_raw(
                    field_name,
                    getattr(self, field_name),
                )
                for field_name in count_threshold_fields
            },
        )
        raw_thresholds.update(
            {
                field_name: _validate_positive_decimal_raw(
                    field_name,
                    getattr(self, field_name),
                )
                for field_name in age_threshold_fields
            },
        )
        for watch_field, block_field in (
            (
                "reviewer_disagreement_watch_threshold",
                "reviewer_disagreement_block_threshold",
            ),
            (
                "probability_spread_watch_threshold",
                "probability_spread_block_threshold",
            ),
            (
                "evidence_conflict_watch_threshold",
                "evidence_conflict_block_threshold",
            ),
            (
                "unresolved_blocker_watch_threshold",
                "unresolved_blocker_block_threshold",
            ),
            ("queue_age_watch_hours", "queue_age_block_hours"),
            (
                "prior_resolution_miss_watch_threshold",
                "prior_resolution_miss_block_threshold",
            ),
        ):
            _require_watch_not_above_block(
                raw_thresholds[watch_field],
                raw_thresholds[block_field],
            )
        for field_name in unit_threshold_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in count_threshold_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in age_threshold_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("domain review disagreement queue config", self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewDisagreementQueueInput(_FinalPublicDataclass):
    queue_key: str
    domain_key: str
    reviewer_count: Decimal
    disagreeing_reviewer_count: Decimal
    probability_spread: Decimal
    evidence_conflict_ratio: Decimal
    unresolved_blocker_count: Decimal
    queued_at: datetime
    prior_resolution_miss_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchTeamDomainReviewDisagreementQueueInput,
        )
        _require_private_key("queue_key", self.queue_key)
        _require_private_key("domain_key", self.domain_key)
        object.__setattr__(
            self,
            "reviewer_count",
            _normalize_positive_count("reviewer_count", self.reviewer_count),
        )
        for field_name in (
            "disagreeing_reviewer_count",
            "unresolved_blocker_count",
            "prior_resolution_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.disagreeing_reviewer_count > self.reviewer_count:
            raise ValueError(
                "disagreeing_reviewer_count must be at most reviewer_count",
            )
        for field_name in ("probability_spread", "evidence_conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        require_paper_only_flags("domain review disagreement queue input", self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewDisagreementQueueRow(_FinalPublicDataclass):
    queue_fingerprint: str
    domain_fingerprint: str
    reviewer_count: Decimal
    disagreeing_reviewer_count: Decimal
    reviewer_disagreement_ratio: Decimal
    probability_spread: Decimal
    evidence_conflict_ratio: Decimal
    unresolved_blocker_count: Decimal
    queued_at: datetime
    queue_age_hours: Decimal
    prior_resolution_miss_count: Decimal
    reviewer_disagreement_score: Decimal
    probability_spread_score: Decimal
    evidence_conflict_score: Decimal
    unresolved_blocker_score: Decimal
    queue_age_score: Decimal
    prior_resolution_miss_score: Decimal
    disagreement_queue_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    generated_at: InitVar[datetime]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamDomainReviewDisagreementQueueConfig | None
    ] = None

    def __post_init__(
        self,
        generated_at: datetime,
        validation_config: ResearchTeamDomainReviewDisagreementQueueConfig | None,
    ) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchTeamDomainReviewDisagreementQueueRow,
        )
        active_config = _normalize_validation_config(validation_config)
        _require_digest("queue_fingerprint", self.queue_fingerprint)
        _require_digest("domain_fingerprint", self.domain_fingerprint)
        for field_name in (
            "reviewer_count",
            "disagreeing_reviewer_count",
            "unresolved_blocker_count",
            "prior_resolution_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.reviewer_count <= _ZERO:
            raise ValueError("reviewer_count must be positive")
        if self.disagreeing_reviewer_count > self.reviewer_count:
            raise ValueError(
                "disagreeing_reviewer_count must be at most reviewer_count",
            )
        for field_name in (
            "reviewer_disagreement_ratio",
            "probability_spread",
            "evidence_conflict_ratio",
            "reviewer_disagreement_score",
            "probability_spread_score",
            "evidence_conflict_score",
            "unresolved_blocker_score",
            "queue_age_score",
            "prior_resolution_miss_score",
            "disagreement_queue_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "queue_age_hours",
            _normalize_nonnegative_decimal("queue_age_hours", self.queue_age_hours),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        require_paper_only_flags("domain review disagreement queue row", self)
        _validate_row(
            self,
            config=active_config,
            generated_at=generated_at,
        )


@dataclass(frozen=True)
class ResearchTeamDomainReviewDisagreementQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    queue_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_disagreement_queue_score: Decimal | None
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamDomainReviewDisagreementQueueRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamDomainReviewDisagreementQueueConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchTeamDomainReviewDisagreementQueueConfig | None,
    ) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchTeamDomainReviewDisagreementQueueReport,
        )
        active_config = _normalize_validation_config(validation_config)
        object.__setattr__(self, "_validation_config", active_config)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if self.config_version != active_config.config_version:
            raise ValueError("config_version must match validation config")
        for field_name in (
            "queue_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.max_disagreement_queue_score is not None:
            object.__setattr__(
                self,
                "max_disagreement_queue_score",
                _normalize_unit_decimal(
                    "max_disagreement_queue_score",
                    self.max_disagreement_queue_score,
                ),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "rows",
            _normalize_rows(
                self.rows,
                config=active_config,
                generated_at=self.generated_at,
            ),
        )
        _require_digest("validation_digest", self.validation_digest)
        require_paper_only_flags("domain review disagreement queue report", self)
        _validate_report(self, config=active_config)


def build_research_team_domain_review_disagreement_queue_report(
    queue_items: Iterable[ResearchTeamDomainReviewDisagreementQueueInput],
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
    generated_at: datetime,
) -> ResearchTeamDomainReviewDisagreementQueueReport:
    if type(config) is not ResearchTeamDomainReviewDisagreementQueueConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainReviewDisagreementQueueConfig",
        )
    config = _normalize_validation_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_queue_items(queue_items)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in normalized_items
            ),
            key=_row_sort_key,
        ),
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "queue_count": _count(len(rows)),
        "pass_count": _row_status_count(rows, "pass"),
        "watch_count": _row_status_count(rows, "watch"),
        "block_count": _row_status_count(rows, "block"),
        "max_disagreement_queue_score": (
            None if not rows else max(row.disagreement_queue_score for row in rows)
        ),
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainReviewDisagreementQueueReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
        validation_config=config,
    )


def research_team_domain_review_disagreement_queue_report_payload(
    report: ResearchTeamDomainReviewDisagreementQueueReport | dict[str, Any],
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig | None = None,
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainReviewDisagreementQueueReport:
        require_paper_only_flags("domain review disagreement queue report", report)
        active_config = _normalize_validation_config(
            getattr(report, "_validation_config", config),
        )
        _validate_report(report, config=active_config)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_payload(report)
        active_config = _normalize_validation_config(config)
        parsed_report = _report_from_public_payload(
            report,
            validation_config=active_config,
        )
        payload = _json_ready(parsed_report)
        if payload != report:
            raise ValueError("report payload must use canonical representation")
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainReviewDisagreementQueueReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags(
        "domain review disagreement queue payload",
        _PayloadFlags(payload),
    )
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


def _normalize_validation_config(
    config: ResearchTeamDomainReviewDisagreementQueueConfig | None,
) -> ResearchTeamDomainReviewDisagreementQueueConfig:
    if config is None:
        return ResearchTeamDomainReviewDisagreementQueueConfig()
    if type(config) is not ResearchTeamDomainReviewDisagreementQueueConfig:
        raise ValueError(
            "validation config must be a "
            "ResearchTeamDomainReviewDisagreementQueueConfig",
        )
    require_paper_only_flags("domain review disagreement queue config", config)
    return ResearchTeamDomainReviewDisagreementQueueConfig(
        config_version=config.config_version,
        reviewer_disagreement_watch_threshold=(
            config.reviewer_disagreement_watch_threshold
        ),
        reviewer_disagreement_block_threshold=(
            config.reviewer_disagreement_block_threshold
        ),
        probability_spread_watch_threshold=(
            config.probability_spread_watch_threshold
        ),
        probability_spread_block_threshold=(
            config.probability_spread_block_threshold
        ),
        evidence_conflict_watch_threshold=config.evidence_conflict_watch_threshold,
        evidence_conflict_block_threshold=config.evidence_conflict_block_threshold,
        unresolved_blocker_watch_threshold=(
            config.unresolved_blocker_watch_threshold
        ),
        unresolved_blocker_block_threshold=(
            config.unresolved_blocker_block_threshold
        ),
        queue_age_watch_hours=config.queue_age_watch_hours,
        queue_age_block_hours=config.queue_age_block_hours,
        prior_resolution_miss_watch_threshold=(
            config.prior_resolution_miss_watch_threshold
        ),
        prior_resolution_miss_block_threshold=(
            config.prior_resolution_miss_block_threshold
        ),
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _report_from_public_payload(
    value: object,
    *,
    validation_config: ResearchTeamDomainReviewDisagreementQueueConfig,
) -> ResearchTeamDomainReviewDisagreementQueueReport:
    payload = _require_public_object_schema(
        "report payload",
        value,
        _REPORT_PAYLOAD_SCHEMA,
    )
    generated_at = _public_datetime("generated_at", payload["generated_at"])
    rows = tuple(
        _row_from_public_payload(
            item,
            validation_config=validation_config,
            generated_at=generated_at,
        )
        for item in _require_public_array("rows", payload["rows"])
    )
    max_score_value = payload["max_disagreement_queue_score"]
    max_score = (
        None
        if max_score_value is None
        else _public_decimal(
            "max_disagreement_queue_score",
            max_score_value,
            _normalize_unit_decimal,
        )
    )
    return ResearchTeamDomainReviewDisagreementQueueReport(
        generated_at=generated_at,
        config_version=_public_string("config_version", payload["config_version"]),
        queue_count=_public_decimal(
            "queue_count",
            payload["queue_count"],
            _normalize_nonnegative_count,
        ),
        pass_count=_public_decimal(
            "pass_count",
            payload["pass_count"],
            _normalize_nonnegative_count,
        ),
        watch_count=_public_decimal(
            "watch_count",
            payload["watch_count"],
            _normalize_nonnegative_count,
        ),
        block_count=_public_decimal(
            "block_count",
            payload["block_count"],
            _normalize_nonnegative_count,
        ),
        max_disagreement_queue_score=max_score,
        report_status=_public_string("report_status", payload["report_status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        rows=rows,
        validation_digest=_public_digest(
            "validation_digest",
            payload["validation_digest"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=validation_config,
    )


def _row_from_public_payload(
    value: object,
    *,
    validation_config: ResearchTeamDomainReviewDisagreementQueueConfig,
    generated_at: datetime,
) -> ResearchTeamDomainReviewDisagreementQueueRow:
    payload = _require_public_object_schema("row payload", value, _ROW_PAYLOAD_SCHEMA)
    return ResearchTeamDomainReviewDisagreementQueueRow(
        queue_fingerprint=_public_digest(
            "queue_fingerprint",
            payload["queue_fingerprint"],
        ),
        domain_fingerprint=_public_digest(
            "domain_fingerprint",
            payload["domain_fingerprint"],
        ),
        reviewer_count=_public_decimal(
            "reviewer_count",
            payload["reviewer_count"],
            _normalize_positive_count,
        ),
        disagreeing_reviewer_count=_public_decimal(
            "disagreeing_reviewer_count",
            payload["disagreeing_reviewer_count"],
            _normalize_nonnegative_count,
        ),
        reviewer_disagreement_ratio=_public_decimal(
            "reviewer_disagreement_ratio",
            payload["reviewer_disagreement_ratio"],
            _normalize_unit_decimal,
        ),
        probability_spread=_public_decimal(
            "probability_spread",
            payload["probability_spread"],
            _normalize_unit_decimal,
        ),
        evidence_conflict_ratio=_public_decimal(
            "evidence_conflict_ratio",
            payload["evidence_conflict_ratio"],
            _normalize_unit_decimal,
        ),
        unresolved_blocker_count=_public_decimal(
            "unresolved_blocker_count",
            payload["unresolved_blocker_count"],
            _normalize_nonnegative_count,
        ),
        queued_at=_public_datetime("queued_at", payload["queued_at"]),
        queue_age_hours=_public_decimal(
            "queue_age_hours",
            payload["queue_age_hours"],
            _normalize_nonnegative_decimal,
        ),
        prior_resolution_miss_count=_public_decimal(
            "prior_resolution_miss_count",
            payload["prior_resolution_miss_count"],
            _normalize_nonnegative_count,
        ),
        reviewer_disagreement_score=_public_decimal(
            "reviewer_disagreement_score",
            payload["reviewer_disagreement_score"],
            _normalize_unit_decimal,
        ),
        probability_spread_score=_public_decimal(
            "probability_spread_score",
            payload["probability_spread_score"],
            _normalize_unit_decimal,
        ),
        evidence_conflict_score=_public_decimal(
            "evidence_conflict_score",
            payload["evidence_conflict_score"],
            _normalize_unit_decimal,
        ),
        unresolved_blocker_score=_public_decimal(
            "unresolved_blocker_score",
            payload["unresolved_blocker_score"],
            _normalize_unit_decimal,
        ),
        queue_age_score=_public_decimal(
            "queue_age_score",
            payload["queue_age_score"],
            _normalize_unit_decimal,
        ),
        prior_resolution_miss_score=_public_decimal(
            "prior_resolution_miss_score",
            payload["prior_resolution_miss_score"],
            _normalize_unit_decimal,
        ),
        disagreement_queue_score=_public_decimal(
            "disagreement_queue_score",
            payload["disagreement_queue_score"],
            _normalize_unit_decimal,
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        validation_digest=_public_digest(
            "validation_digest",
            payload["validation_digest"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=validation_config,
        generated_at=generated_at,
    )


def _require_public_object_schema(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} schema must use exact fields")
    return value


def _require_public_array(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _public_string(field_name: str, value: object) -> str:
    _require_text(field_name, value)
    return value


def _public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    items = _require_public_array(field_name, value)
    for item in items:
        _require_text(field_name, item)
    return items


def _public_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _public_datetime(field_name: str, value: object) -> datetime:
    string_value = _public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(string_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != string_value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _public_digest(field_name: str, value: object) -> str:
    _require_digest(field_name, value)
    return value


def _public_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _normalize_queue_items(
    queue_items: Iterable[ResearchTeamDomainReviewDisagreementQueueInput],
) -> tuple[ResearchTeamDomainReviewDisagreementQueueInput, ...]:
    if isinstance(queue_items, (str, bytes)):
        raise ValueError("queue_items must be an iterable")
    try:
        items = tuple(queue_items)
    except TypeError as exc:
        raise ValueError("queue_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamDomainReviewDisagreementQueueInput:
            raise ValueError(
                "queue_items must contain ResearchTeamDomainReviewDisagreementQueueInput",
            )
        require_paper_only_flags("domain review disagreement queue input", item)
        if item.queue_key in seen:
            raise ValueError("queue_key values must be unique")
        seen.add(item.queue_key)
    return items


def _row_from_input(
    item: ResearchTeamDomainReviewDisagreementQueueInput,
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
    generated_at: datetime,
) -> ResearchTeamDomainReviewDisagreementQueueRow:
    queue_age_hours = _queue_age_hours(item.queued_at, generated_at)
    reviewer_disagreement_ratio = _ratio(
        item.disagreeing_reviewer_count,
        item.reviewer_count,
    )
    reviewer_disagreement_score = _capped_ratio(
        reviewer_disagreement_ratio,
        config.reviewer_disagreement_block_threshold,
    )
    probability_spread_score = _capped_ratio(
        item.probability_spread,
        config.probability_spread_block_threshold,
    )
    evidence_conflict_score = _capped_ratio(
        item.evidence_conflict_ratio,
        config.evidence_conflict_block_threshold,
    )
    unresolved_blocker_score = _capped_ratio(
        item.unresolved_blocker_count,
        config.unresolved_blocker_block_threshold,
    )
    queue_age_score = _capped_ratio(queue_age_hours, config.queue_age_block_hours)
    prior_resolution_miss_score = _capped_ratio(
        item.prior_resolution_miss_count,
        config.prior_resolution_miss_block_threshold,
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        reviewer_disagreement_ratio=reviewer_disagreement_ratio,
        queue_age_hours=queue_age_hours,
    )
    row_values = {
        "queue_fingerprint": _fingerprint(item.queue_key),
        "domain_fingerprint": _fingerprint(item.domain_key),
        "reviewer_count": item.reviewer_count,
        "disagreeing_reviewer_count": item.disagreeing_reviewer_count,
        "reviewer_disagreement_ratio": reviewer_disagreement_ratio,
        "probability_spread": item.probability_spread,
        "evidence_conflict_ratio": item.evidence_conflict_ratio,
        "unresolved_blocker_count": item.unresolved_blocker_count,
        "queued_at": item.queued_at,
        "queue_age_hours": queue_age_hours,
        "prior_resolution_miss_count": item.prior_resolution_miss_count,
        "reviewer_disagreement_score": reviewer_disagreement_score,
        "probability_spread_score": probability_spread_score,
        "evidence_conflict_score": evidence_conflict_score,
        "unresolved_blocker_score": unresolved_blocker_score,
        "queue_age_score": queue_age_score,
        "prior_resolution_miss_score": prior_resolution_miss_score,
        "disagreement_queue_score": _disagreement_queue_score(
            (
                reviewer_disagreement_score,
                probability_spread_score,
                evidence_conflict_score,
                unresolved_blocker_score,
                queue_age_score,
                prior_resolution_miss_score,
            ),
        ),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainReviewDisagreementQueueRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
        validation_config=config,
        generated_at=generated_at,
    )


def _row_reason_codes(
    item: ResearchTeamDomainReviewDisagreementQueueInput,
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
    reviewer_disagreement_ratio: Decimal,
    queue_age_hours: Decimal,
) -> tuple[str, ...]:
    return _reason_codes_from_values(
        reviewer_disagreement_ratio=reviewer_disagreement_ratio,
        probability_spread=item.probability_spread,
        evidence_conflict_ratio=item.evidence_conflict_ratio,
        unresolved_blocker_count=item.unresolved_blocker_count,
        queue_age_hours=queue_age_hours,
        prior_resolution_miss_count=item.prior_resolution_miss_count,
        config=config,
    )


def _reason_codes_from_values(
    *,
    reviewer_disagreement_ratio: Decimal,
    probability_spread: Decimal,
    evidence_conflict_ratio: Decimal,
    unresolved_blocker_count: Decimal,
    queue_age_hours: Decimal,
    prior_resolution_miss_count: Decimal,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if reviewer_disagreement_ratio >= config.reviewer_disagreement_block_threshold:
        block_reasons.append("reviewer_disagreement_block")
    elif reviewer_disagreement_ratio >= config.reviewer_disagreement_watch_threshold:
        watch_reasons.append("reviewer_disagreement_watch")
    if probability_spread >= config.probability_spread_block_threshold:
        block_reasons.append("probability_spread_block")
    elif probability_spread >= config.probability_spread_watch_threshold:
        watch_reasons.append("probability_spread_watch")
    if evidence_conflict_ratio >= config.evidence_conflict_block_threshold:
        block_reasons.append("evidence_conflict_block")
    elif evidence_conflict_ratio >= config.evidence_conflict_watch_threshold:
        watch_reasons.append("evidence_conflict_watch")
    if unresolved_blocker_count >= config.unresolved_blocker_block_threshold:
        block_reasons.append("unresolved_blocker_block")
    elif unresolved_blocker_count >= config.unresolved_blocker_watch_threshold:
        watch_reasons.append("unresolved_blocker_watch")
    if queue_age_hours >= config.queue_age_block_hours:
        block_reasons.append("queue_age_block")
    elif queue_age_hours >= config.queue_age_watch_hours:
        watch_reasons.append("queue_age_watch")
    if prior_resolution_miss_count >= config.prior_resolution_miss_block_threshold:
        block_reasons.append("prior_resolution_miss_block")
    elif prior_resolution_miss_count >= config.prior_resolution_miss_watch_threshold:
        watch_reasons.append("prior_resolution_miss_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("domain_review_disagreement_queue_pass",)
    return _normalize_row_reason_codes("reason_codes", reasons)


def _queue_age_hours(queued_at: datetime, generated_at: datetime) -> Decimal:
    queued_at_utc = _as_utc("queued_at", queued_at)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if queued_at_utc > generated_at_utc:
        raise ValueError("generated_at must not be before queued_at")
    delta = generated_at_utc - queued_at_utc
    with localcontext(_DECIMAL_CONTEXT):
        total_seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal("1000000")
        )
    return _ratio(total_seconds, Decimal("3600.000000"))


def _disagreement_queue_score(component_values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(component_values), _SIX)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == ("domain_review_disagreement_queue_pass",):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchTeamDomainReviewDisagreementQueueRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainReviewDisagreementQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_team_domain_review_disagreement_queue_report_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _row_status_count(
    rows: tuple[ResearchTeamDomainReviewDisagreementQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    rows: object,
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainReviewDisagreementQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_queue_fingerprints: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamDomainReviewDisagreementQueueRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainReviewDisagreementQueueRow",
            )
        require_paper_only_flags("domain review disagreement queue row", row)
        _validate_row(row, config=config, generated_at=generated_at)
        if row.queue_fingerprint in seen_queue_fingerprints:
            raise ValueError("queue_fingerprint values must be unique")
        seen_queue_fingerprints.add(row.queue_fingerprint)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_row(
    row: ResearchTeamDomainReviewDisagreementQueueRow,
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
    generated_at: datetime,
) -> None:
    _require_exact_type(
        "row",
        row,
        ResearchTeamDomainReviewDisagreementQueueRow,
    )
    _require_digest("queue_fingerprint", row.queue_fingerprint)
    _require_digest("domain_fingerprint", row.domain_fingerprint)
    _require_canonical_decimal(
        "reviewer_count",
        row.reviewer_count,
        _normalize_positive_count,
    )
    for field_name in (
        "disagreeing_reviewer_count",
        "unresolved_blocker_count",
        "prior_resolution_miss_count",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_nonnegative_count,
        )
    if row.disagreeing_reviewer_count > row.reviewer_count:
        raise ValueError(
            "disagreeing_reviewer_count must be at most reviewer_count",
        )
    for field_name in (
        "reviewer_disagreement_ratio",
        "probability_spread",
        "evidence_conflict_ratio",
        "reviewer_disagreement_score",
        "probability_spread_score",
        "evidence_conflict_score",
        "unresolved_blocker_score",
        "queue_age_score",
        "prior_resolution_miss_score",
        "disagreement_queue_score",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_unit_decimal,
        )
    _require_canonical_utc_datetime("queued_at", row.queued_at)
    _require_canonical_decimal(
        "queue_age_hours",
        row.queue_age_hours,
        _normalize_nonnegative_decimal,
    )
    _require_status("status", row.status)
    _require_canonical_reason_codes(
        "reason_codes",
        row.reason_codes,
        _normalize_row_reason_codes,
    )
    _require_digest("validation_digest", row.validation_digest)
    require_paper_only_flags("domain review disagreement queue row", row)

    expected_ratio = _ratio(row.disagreeing_reviewer_count, row.reviewer_count)
    if row.reviewer_disagreement_ratio != expected_ratio:
        raise ValueError("reviewer_disagreement_ratio must match reviewer counts")
    expected_age = _queue_age_hours(row.queued_at, generated_at)
    if row.queue_age_hours != expected_age:
        raise ValueError("queue_age_hours must match queued_at and generated_at")
    expected_components = {
        "reviewer_disagreement_score": _capped_ratio(
            row.reviewer_disagreement_ratio,
            config.reviewer_disagreement_block_threshold,
        ),
        "probability_spread_score": _capped_ratio(
            row.probability_spread,
            config.probability_spread_block_threshold,
        ),
        "evidence_conflict_score": _capped_ratio(
            row.evidence_conflict_ratio,
            config.evidence_conflict_block_threshold,
        ),
        "unresolved_blocker_score": _capped_ratio(
            row.unresolved_blocker_count,
            config.unresolved_blocker_block_threshold,
        ),
        "queue_age_score": _capped_ratio(
            row.queue_age_hours,
            config.queue_age_block_hours,
        ),
        "prior_resolution_miss_score": _capped_ratio(
            row.prior_resolution_miss_count,
            config.prior_resolution_miss_block_threshold,
        ),
    }
    for field_name, expected_value in expected_components.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match raw row values")
    expected_score = _disagreement_queue_score(
        (
            expected_components["reviewer_disagreement_score"],
            expected_components["probability_spread_score"],
            expected_components["evidence_conflict_score"],
            expected_components["unresolved_blocker_score"],
            expected_components["queue_age_score"],
            expected_components["prior_resolution_miss_score"],
        ),
    )
    if row.disagreement_queue_score != expected_score:
        raise ValueError("disagreement_queue_score must match component scores")
    expected_reason_codes = _reason_codes_from_values(
        reviewer_disagreement_ratio=row.reviewer_disagreement_ratio,
        probability_spread=row.probability_spread,
        evidence_conflict_ratio=row.evidence_conflict_ratio,
        unresolved_blocker_count=row.unresolved_blocker_count,
        queue_age_hours=row.queue_age_hours,
        prior_resolution_miss_count=row.prior_resolution_miss_count,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match raw row values")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(
    report: ResearchTeamDomainReviewDisagreementQueueReport,
    *,
    config: ResearchTeamDomainReviewDisagreementQueueConfig,
) -> None:
    _require_exact_type(
        "report",
        report,
        ResearchTeamDomainReviewDisagreementQueueReport,
    )
    _require_canonical_utc_datetime("generated_at", report.generated_at)
    _require_public_text("config_version", report.config_version)
    if report.config_version != config.config_version:
        raise ValueError("config_version must match validation config")
    for field_name in (
        "queue_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(report, field_name),
            _normalize_nonnegative_count,
        )
    if report.max_disagreement_queue_score is not None:
        _require_canonical_decimal(
            "max_disagreement_queue_score",
            report.max_disagreement_queue_score,
            _normalize_unit_decimal,
        )
    _require_status("report_status", report.report_status)
    _require_canonical_reason_codes(
        "reason_codes",
        report.reason_codes,
        _normalize_report_reason_codes,
    )
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    _normalize_rows(
        report.rows,
        config=config,
        generated_at=report.generated_at,
    )
    _require_digest("validation_digest", report.validation_digest)
    require_paper_only_flags("domain review disagreement queue report", report)
    if report.queue_count != _count(len(report.rows)):
        raise ValueError("queue_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_max = (
        None
        if not report.rows
        else max(row.disagreement_queue_score for row in report.rows)
    )
    if report.max_disagreement_queue_score != expected_max:
        raise ValueError("max_disagreement_queue_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(
    row: ResearchTeamDomainReviewDisagreementQueueRow,
) -> dict[str, Any]:
    return {
        "queue_fingerprint": row.queue_fingerprint,
        "domain_fingerprint": row.domain_fingerprint,
        "reviewer_count": row.reviewer_count,
        "disagreeing_reviewer_count": row.disagreeing_reviewer_count,
        "reviewer_disagreement_ratio": row.reviewer_disagreement_ratio,
        "probability_spread": row.probability_spread,
        "evidence_conflict_ratio": row.evidence_conflict_ratio,
        "unresolved_blocker_count": row.unresolved_blocker_count,
        "queued_at": row.queued_at,
        "queue_age_hours": row.queue_age_hours,
        "prior_resolution_miss_count": row.prior_resolution_miss_count,
        "reviewer_disagreement_score": row.reviewer_disagreement_score,
        "probability_spread_score": row.probability_spread_score,
        "evidence_conflict_score": row.evidence_conflict_score,
        "unresolved_blocker_score": row.unresolved_blocker_score,
        "queue_age_score": row.queue_age_score,
        "prior_resolution_miss_score": row.prior_resolution_miss_score,
        "disagreement_queue_score": row.disagreement_queue_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchTeamDomainReviewDisagreementQueueReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "queue_count": report.queue_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "max_disagreement_queue_score": report.max_disagreement_queue_score,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_sort_key(
    row: ResearchTeamDomainReviewDisagreementQueueRow,
) -> tuple[
    int,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    str,
]:
    return (
        _STATUS_WEIGHT[row.status],
        row.disagreement_queue_score.copy_negate(),
        row.reviewer_disagreement_score.copy_negate(),
        row.probability_spread_score.copy_negate(),
        row.evidence_conflict_score.copy_negate(),
        row.unresolved_blocker_score.copy_negate(),
        row.queue_age_score.copy_negate(),
        row.prior_resolution_miss_score.copy_negate(),
        row.reviewer_disagreement_ratio.copy_negate(),
        row.probability_spread.copy_negate(),
        row.evidence_conflict_ratio.copy_negate(),
        row.unresolved_blocker_count.copy_negate(),
        row.queue_age_hours.copy_negate(),
        row.prior_resolution_miss_count.copy_negate(),
        row.domain_fingerprint,
        row.queue_fingerprint,
    )


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if "domain_review_disagreement_queue_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if codes == ("domain_review_disagreement_queue_pass",):
        return codes
    if any(code in _PASS_REASONS for code in codes):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("research_team_domain_review_disagreement_queue_report_empty",):
        return codes
    if "research_team_domain_review_disagreement_queue_report_empty" in codes:
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
    return _quantize(
        Decimal(value),
        quantum=_COUNT_QUANTUM,
        name="count",
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(
        _normalize_decimal("sum value", value) for value in values
    )
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in normalized_values:
            total += value
        return _quantize(total, name="sum")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator, name="ratio")


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _validate_positive_count_raw(name, value)
    return _quantize(
        normalized,
        quantum=_COUNT_QUANTUM,
        name=name,
    )


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _validate_nonnegative_count_raw(name, value)
    return _quantize(
        normalized,
        quantum=_COUNT_QUANTUM,
        name=name,
    )


def _validate_positive_count_raw(name: str, value: object) -> Decimal:
    normalized = _validate_nonnegative_count_raw(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _validate_nonnegative_count_raw(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        integral = normalized.to_integral_value()
    if normalized != integral:
        raise ValueError(f"{name} must be an integer")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _validate_positive_decimal_raw(name, value)
    quantized = _quantize(normalized, name=name)
    if quantized <= _ZERO:
        raise ValueError(f"{name} must be positive after quantization")
    return quantized


def _validate_positive_decimal_raw(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized, name=name)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _validate_unit_decimal_raw(name, value)
    return _quantize(normalized, name=name)


def _validate_unit_decimal_raw(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not be signed zero")
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


def _quantize(
    value: Decimal,
    *,
    quantum: Decimal = _QUANTUM,
    name: str = "value",
) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must fit the decimal context") from exc
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError(f"{name} must not quantize to signed zero")
    return normalized


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


def _require_canonical_reason_codes(
    name: str,
    value: object,
    normalizer: Any,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a canonical tuple")
    normalized = normalizer(name, value)
    if value != normalized:
        raise ValueError(f"{name} must use canonical sequence")
    return normalized


def _require_watch_not_above_block(watch_threshold: Decimal, block_threshold: Decimal) -> None:
    if watch_threshold > block_threshold:
        raise ValueError("watch threshold must not exceed block threshold")


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in DOMAIN_REVIEW_DISAGREEMENT_QUEUE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_private_key(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    try:
        encoded_value = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be a non-empty canonical string") from exc
    if (
        not value
        or value.strip() != value
        or len(encoded_value) > _MAX_PRIVATE_KEY_BYTES
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public value")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _fingerprint(value: str) -> str:
    _require_private_key("fingerprint value", value)
    return sha256(value.encode("utf-8")).hexdigest()


def _validation_digest(values: dict[str, Any]) -> str:
    """Return a checksum for canonical self-consistency only."""
    ready = _json_ready(values)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
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
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not be signed zero")
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
            _require_public_text("JSON object key", key)
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
            _require_public_text("payload key", key)
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, Decimal):
        raise ValueError("payload numeric values must use Decimal strings")
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION",
    "DOMAIN_REVIEW_DISAGREEMENT_QUEUE_STATUSES",
    "ResearchTeamDomainReviewDisagreementQueueConfig",
    "ResearchTeamDomainReviewDisagreementQueueInput",
    "ResearchTeamDomainReviewDisagreementQueueReport",
    "ResearchTeamDomainReviewDisagreementQueueRow",
    "build_research_team_domain_review_disagreement_queue_report",
    "research_team_domain_review_disagreement_queue_report_payload",
)
