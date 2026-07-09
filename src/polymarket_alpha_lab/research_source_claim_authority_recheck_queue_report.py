"""Pure report-only source claim-authority recheck queue report."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_RECHECK_QUEUE_REPORT_CONFIG_VERSION = (
    "research-source-claim-authority-recheck-queue-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_ROW_REASON_CODE_PREFIXES = (
    "authority_freshness",
    "authority_gap",
    "claim_conflict",
    "source_confidence",
    "authority_corroboration",
    "deadline_proximity",
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "claim_bucket",
        "authority_bucket",
        "claim_age_seconds",
        "authority_age_seconds",
        "authority_freshness_score",
        "source_authority_score",
        "authority_gap_score",
        "source_confidence_score",
        "source_confidence_gap_score",
        "conflict_score",
        "corroborating_authority_count",
        "required_authority_count",
        "authority_corroboration_gap_score",
        "deadline_proximity_score",
        "recheck_priority_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "row_count",
        "stale_authority_count",
        "authority_gap_count",
        "conflict_count",
        "source_confidence_gap_count",
        "corroboration_gap_count",
        "deadline_proximity_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_recheck_priority_score",
        "max_recheck_priority_score",
        "status",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "candidate",
    "candidate_" + "id",
    "condition_" + "id",
    "market_" + "id",
    "market_" + "sl" + "ug",
    "market_" + "ques" + "tion",
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
    "raw_" + "text",
    "private_",
    "secret",
    "credential",
)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityRecheckQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_RECHECK_QUEUE_REPORT_CONFIG_VERSION
    )
    fresh_authority_age_seconds: Decimal = Decimal("3600.000000")
    stale_authority_age_seconds: Decimal = Decimal("86400.000000")
    deadline_proximity_window_seconds: Decimal = Decimal("172800.000000")
    watch_priority_score: Decimal = Decimal("0.250000")
    block_priority_score: Decimal = Decimal("0.700000")
    watch_authority_freshness_score: Decimal = Decimal("0.250000")
    block_authority_freshness_score: Decimal = Decimal("1.000000")
    min_source_authority_score: Decimal = Decimal("0.700000")
    block_source_authority_score: Decimal = Decimal("0.300000")
    watch_conflict_score: Decimal = Decimal("0.300000")
    block_conflict_score: Decimal = Decimal("0.700000")
    min_source_confidence_score: Decimal = Decimal("0.700000")
    block_source_confidence_score: Decimal = Decimal("0.300000")
    watch_corroboration_gap_score: Decimal = Decimal("0.500000")
    block_corroboration_gap_score: Decimal = Decimal("0.800000")
    watch_deadline_proximity_score: Decimal = Decimal("0.500000")
    block_deadline_proximity_score: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityRecheckQueueConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityRecheckQueueConfig:
            raise ValueError(
                "config must be exactly ResearchSourceClaimAuthorityRecheckQueueConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_RECHECK_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_authority_age_seconds",
            "stale_authority_age_seconds",
            "deadline_proximity_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_priority_score",
            "block_priority_score",
            "watch_authority_freshness_score",
            "block_authority_freshness_score",
            "min_source_authority_score",
            "block_source_authority_score",
            "watch_conflict_score",
            "block_conflict_score",
            "min_source_confidence_score",
            "block_source_confidence_score",
            "watch_corroboration_gap_score",
            "block_corroboration_gap_score",
            "watch_deadline_proximity_score",
            "block_deadline_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_authority_age_seconds <= self.fresh_authority_age_seconds:
            raise ValueError(
                "stale_authority_age_seconds must exceed fresh_authority_age_seconds",
            )
        if self.block_priority_score <= self.watch_priority_score:
            raise ValueError("block_priority_score must exceed watch_priority_score")
        if (
            self.block_authority_freshness_score
            < self.watch_authority_freshness_score
        ):
            raise ValueError(
                "block_authority_freshness_score must be at least "
                "watch_authority_freshness_score",
            )
        if self.block_source_authority_score > self.min_source_authority_score:
            raise ValueError(
                "block_source_authority_score must not exceed "
                "min_source_authority_score",
            )
        if self.block_conflict_score < self.watch_conflict_score:
            raise ValueError("block_conflict_score must be at least watch_conflict_score")
        if self.block_source_confidence_score > self.min_source_confidence_score:
            raise ValueError(
                "block_source_confidence_score must not exceed "
                "min_source_confidence_score",
            )
        if self.block_corroboration_gap_score < self.watch_corroboration_gap_score:
            raise ValueError(
                "block_corroboration_gap_score must be at least "
                "watch_corroboration_gap_score",
            )
        if self.block_deadline_proximity_score < self.watch_deadline_proximity_score:
            raise ValueError(
                "block_deadline_proximity_score must be at least "
                "watch_deadline_proximity_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityRecheckQueueInput:
    claim_bucket: str
    authority_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    claim_observed_at: datetime
    authority_last_checked_at: datetime
    source_authority_score: Decimal
    source_confidence_score: Decimal
    conflict_score: Decimal
    corroborating_authority_count: Decimal
    required_authority_count: Decimal
    resolution_deadline_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityRecheckQueueInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityRecheckQueueInput:
            raise ValueError(
                "input must be exactly ResearchSourceClaimAuthorityRecheckQueueInput",
            )
        for field_name in ("claim_bucket", "authority_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_reference",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "authority_last_checked_at",
            _as_utc("authority_last_checked_at", self.authority_last_checked_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _optional_as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "source_authority_score",
            "source_confidence_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroborating_authority_count",
            _require_nonnegative_decimal(
                "corroborating_authority_count",
                self.corroborating_authority_count,
            ),
        )
        object.__setattr__(
            self,
            "required_authority_count",
            _require_positive_decimal(
                "required_authority_count",
                self.required_authority_count,
            ),
        )
        if self.corroborating_authority_count > self.required_authority_count:
            raise ValueError(
                "corroborating_authority_count must not exceed "
                "required_authority_count",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityRecheckQueueRow:
    claim_bucket: str
    authority_bucket: str
    claim_age_seconds: Decimal
    authority_age_seconds: Decimal
    authority_freshness_score: Decimal
    source_authority_score: Decimal
    authority_gap_score: Decimal
    source_confidence_score: Decimal
    source_confidence_gap_score: Decimal
    conflict_score: Decimal
    corroborating_authority_count: Decimal
    required_authority_count: Decimal
    authority_corroboration_gap_score: Decimal
    deadline_proximity_score: Decimal
    recheck_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityRecheckQueueRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityRecheckQueueRow:
            raise ValueError(
                "row must be exactly ResearchSourceClaimAuthorityRecheckQueueRow",
            )
        for field_name in ("claim_bucket", "authority_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "claim_age_seconds",
            "authority_age_seconds",
            "corroborating_authority_count",
            "required_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_authority_count <= _ZERO:
            raise ValueError("required_authority_count must be positive")
        if self.corroborating_authority_count > self.required_authority_count:
            raise ValueError(
                "corroborating_authority_count must not exceed "
                "required_authority_count",
            )
        for field_name in (
            "authority_freshness_score",
            "source_authority_score",
            "authority_gap_score",
            "source_confidence_score",
            "source_confidence_gap_score",
            "conflict_score",
            "authority_corroboration_gap_score",
            "deadline_proximity_score",
            "recheck_priority_score",
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
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_digest_from_values(_row_values_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row_consistency(self)
        _validate_row_digest(self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityRecheckQueueReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    stale_authority_count: Decimal
    authority_gap_count: Decimal
    conflict_count: Decimal
    source_confidence_gap_count: Decimal
    corroboration_gap_count: Decimal
    deadline_proximity_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recheck_priority_score: Decimal
    max_recheck_priority_score: Decimal
    status: str
    rows: tuple[ResearchSourceClaimAuthorityRecheckQueueRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityRecheckQueueReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityRecheckQueueReport:
            raise ValueError(
                "report must be exactly ResearchSourceClaimAuthorityRecheckQueueReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_RECHECK_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "stale_authority_count",
            "authority_gap_count",
            "conflict_count",
            "source_confidence_gap_count",
            "corroboration_gap_count",
            "deadline_proximity_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_recheck_priority_score",
            "max_recheck_priority_score",
        ):
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


def build_research_source_claim_authority_recheck_queue_report(
    candidates: Sequence[ResearchSourceClaimAuthorityRecheckQueueInput],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimAuthorityRecheckQueueConfig | None = None,
) -> ResearchSourceClaimAuthorityRecheckQueueReport:
    if config is None:
        config = ResearchSourceClaimAuthorityRecheckQueueConfig()
    if type(config) is not ResearchSourceClaimAuthorityRecheckQueueConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimAuthorityRecheckQueueConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for item in normalized_candidates:
        if item.claim_observed_at > generated_at:
            raise ValueError("claim_observed_at must not be after generated_at")
        if item.authority_last_checked_at > generated_at:
            raise ValueError("authority_last_checked_at must not be after generated_at")
    rows = _normalize_rows(
        tuple(_row_for_input(item, config, generated_at) for item in normalized_candidates),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "row_count": _decimal_count(len(rows)),
        "stale_authority_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.authority_freshness_score >= config.watch_authority_freshness_score
            ),
        ),
        "authority_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.source_authority_score <= config.min_source_authority_score
            ),
        ),
        "conflict_count": _decimal_count(
            sum(1 for row in rows if row.conflict_score >= config.watch_conflict_score),
        ),
        "source_confidence_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.source_confidence_score <= config.min_source_confidence_score
            ),
        ),
        "corroboration_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.authority_corroboration_gap_score
                >= config.watch_corroboration_gap_score
            ),
        ),
        "deadline_proximity_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.deadline_proximity_score >= config.watch_deadline_proximity_score
            ),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_recheck_priority_score": _average(
            tuple(row.recheck_priority_score for row in rows),
        ),
        "max_recheck_priority_score": max(
            (row.recheck_priority_score for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimAuthorityRecheckQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_authority_recheck_queue_report_payload(
    report: ResearchSourceClaimAuthorityRecheckQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceClaimAuthorityRecheckQueueReport:
        _require_hard_flags("report", report)
        raw_payload = report.payload
    elif type(report) is dict:
        raw_payload = report
    else:
        raise ValueError(
            "report must be a ResearchSourceClaimAuthorityRecheckQueueReport",
        )
    _reject_unsafe_public_payload(
        "payload",
        raw_payload,
        allow_json_containers=True,
    )
    validated_report = _report_from_payload(raw_payload)
    payload = validated_report.payload
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _row_for_input(
    item: ResearchSourceClaimAuthorityRecheckQueueInput,
    config: ResearchSourceClaimAuthorityRecheckQueueConfig,
    generated_at: datetime,
) -> ResearchSourceClaimAuthorityRecheckQueueRow:
    claim_age = _seconds_between(generated_at, item.claim_observed_at)
    authority_age = _seconds_between(generated_at, item.authority_last_checked_at)
    authority_freshness = _authority_freshness_score(authority_age, config)
    authority_gap = _clamp_ratio(_ONE - item.source_authority_score)
    confidence_gap = _clamp_ratio(_ONE - item.source_confidence_score)
    corroboration_gap = _clamp_ratio(
        _ONE
        - _clamp_ratio(
            item.corroborating_authority_count / item.required_authority_count,
        ),
    )
    deadline_proximity = _deadline_proximity_score(
        item.resolution_deadline_at,
        config,
        generated_at,
    )
    priority_score = _priority_score(
        authority_freshness_score=authority_freshness,
        authority_gap_score=authority_gap,
        conflict_score=item.conflict_score,
        source_confidence_gap_score=confidence_gap,
        authority_corroboration_gap_score=corroboration_gap,
        deadline_proximity_score=deadline_proximity,
    )
    status = _row_status(
        authority_freshness_score=authority_freshness,
        source_authority_score=item.source_authority_score,
        conflict_score=item.conflict_score,
        source_confidence_score=item.source_confidence_score,
        authority_corroboration_gap_score=corroboration_gap,
        deadline_proximity_score=deadline_proximity,
        recheck_priority_score=priority_score,
        config=config,
    )
    return ResearchSourceClaimAuthorityRecheckQueueRow(
        claim_bucket=item.claim_bucket,
        authority_bucket=item.authority_bucket,
        claim_age_seconds=claim_age,
        authority_age_seconds=authority_age,
        authority_freshness_score=authority_freshness,
        source_authority_score=item.source_authority_score,
        authority_gap_score=authority_gap,
        source_confidence_score=item.source_confidence_score,
        source_confidence_gap_score=confidence_gap,
        conflict_score=item.conflict_score,
        corroborating_authority_count=item.corroborating_authority_count,
        required_authority_count=item.required_authority_count,
        authority_corroboration_gap_score=corroboration_gap,
        deadline_proximity_score=deadline_proximity,
        recheck_priority_score=priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            authority_freshness_score=authority_freshness,
            deadline_proximity_score=deadline_proximity,
            authority_corroboration_gap_score=corroboration_gap,
            config=config,
        ),
    )


def _authority_freshness_score(
    authority_age_seconds: Decimal,
    config: ResearchSourceClaimAuthorityRecheckQueueConfig,
) -> Decimal:
    if authority_age_seconds <= config.fresh_authority_age_seconds:
        return _ZERO
    if authority_age_seconds >= config.stale_authority_age_seconds:
        return _ONE
    denominator = config.stale_authority_age_seconds - config.fresh_authority_age_seconds
    return _clamp_ratio(
        (authority_age_seconds - config.fresh_authority_age_seconds) / denominator,
    )


def _deadline_proximity_score(
    resolution_deadline_at: datetime | None,
    config: ResearchSourceClaimAuthorityRecheckQueueConfig,
    generated_at: datetime,
) -> Decimal:
    if resolution_deadline_at is None:
        return _ZERO
    seconds_until_deadline = _seconds_between(resolution_deadline_at, generated_at)
    if seconds_until_deadline <= _ZERO:
        return _ONE
    if seconds_until_deadline >= config.deadline_proximity_window_seconds:
        return _ZERO
    return _clamp_ratio(
        _ONE - (seconds_until_deadline / config.deadline_proximity_window_seconds),
    )


def _priority_score(
    *,
    authority_freshness_score: Decimal,
    authority_gap_score: Decimal,
    conflict_score: Decimal,
    source_confidence_gap_score: Decimal,
    authority_corroboration_gap_score: Decimal,
    deadline_proximity_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        (
            authority_freshness_score
            + authority_gap_score
            + conflict_score
            + source_confidence_gap_score
            + authority_corroboration_gap_score
            + deadline_proximity_score
        )
        / _SIX,
    )


def _row_status(
    *,
    authority_freshness_score: Decimal,
    source_authority_score: Decimal,
    conflict_score: Decimal,
    source_confidence_score: Decimal,
    authority_corroboration_gap_score: Decimal,
    deadline_proximity_score: Decimal,
    recheck_priority_score: Decimal,
    config: ResearchSourceClaimAuthorityRecheckQueueConfig,
) -> str:
    if (
        recheck_priority_score >= config.block_priority_score
        or authority_freshness_score >= config.block_authority_freshness_score
        or source_authority_score <= config.block_source_authority_score
        or conflict_score >= config.block_conflict_score
        or source_confidence_score <= config.block_source_confidence_score
        or authority_corroboration_gap_score >= config.block_corroboration_gap_score
        or deadline_proximity_score >= config.block_deadline_proximity_score
    ):
        return "block"
    if (
        recheck_priority_score >= config.watch_priority_score
        or authority_freshness_score >= config.watch_authority_freshness_score
        or source_authority_score <= config.min_source_authority_score
        or conflict_score >= config.watch_conflict_score
        or source_confidence_score <= config.min_source_confidence_score
        or authority_corroboration_gap_score >= config.watch_corroboration_gap_score
        or deadline_proximity_score >= config.watch_deadline_proximity_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchSourceClaimAuthorityRecheckQueueInput,
    status: str,
    authority_freshness_score: Decimal,
    deadline_proximity_score: Decimal,
    authority_corroboration_gap_score: Decimal,
    config: ResearchSourceClaimAuthorityRecheckQueueConfig,
) -> tuple[str, ...]:
    reason_codes = {f"claim_authority_recheck_queue_{status}"}
    if authority_freshness_score >= config.block_authority_freshness_score:
        reason_codes.add("authority_freshness_block")
    elif authority_freshness_score >= config.watch_authority_freshness_score:
        reason_codes.add("authority_freshness_watch")
    else:
        reason_codes.add("authority_freshness_clear")
    if item.source_authority_score <= config.block_source_authority_score:
        reason_codes.add("authority_gap_block")
    elif item.source_authority_score <= config.min_source_authority_score:
        reason_codes.add("authority_gap_watch")
    else:
        reason_codes.add("authority_gap_clear")
    if item.conflict_score >= config.block_conflict_score:
        reason_codes.add("claim_conflict_block")
    elif item.conflict_score >= config.watch_conflict_score:
        reason_codes.add("claim_conflict_watch")
    else:
        reason_codes.add("claim_conflict_clear")
    if item.source_confidence_score <= config.block_source_confidence_score:
        reason_codes.add("source_confidence_block")
    elif item.source_confidence_score <= config.min_source_confidence_score:
        reason_codes.add("source_confidence_watch")
    else:
        reason_codes.add("source_confidence_clear")
    if authority_corroboration_gap_score >= config.block_corroboration_gap_score:
        reason_codes.add("authority_corroboration_block")
    elif authority_corroboration_gap_score >= config.watch_corroboration_gap_score:
        reason_codes.add("authority_corroboration_watch")
    else:
        reason_codes.add("authority_corroboration_clear")
    if deadline_proximity_score >= config.block_deadline_proximity_score:
        reason_codes.add("deadline_proximity_block")
    elif deadline_proximity_score >= config.watch_deadline_proximity_score:
        reason_codes.add("deadline_proximity_watch")
    else:
        reason_codes.add("deadline_proximity_clear")
    for reason_code in item.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_candidates(
    candidates: Sequence[ResearchSourceClaimAuthorityRecheckQueueInput],
) -> tuple[ResearchSourceClaimAuthorityRecheckQueueInput, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise ValueError("candidates must be a sequence")
    normalized: list[ResearchSourceClaimAuthorityRecheckQueueInput] = []
    seen: set[tuple[str, str]] = set()
    for item in candidates:
        if type(item) is not ResearchSourceClaimAuthorityRecheckQueueInput:
            raise ValueError(
                "candidate must be a ResearchSourceClaimAuthorityRecheckQueueInput",
            )
        _require_hard_flags("candidate", item)
        key = (item.claim_bucket, item.authority_bucket)
        if key in seen:
            raise ValueError("duplicate claim_bucket and authority_bucket pair")
        seen.add(key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.claim_bucket, item.authority_bucket)))


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimAuthorityRecheckQueueRow],
) -> tuple[ResearchSourceClaimAuthorityRecheckQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimAuthorityRecheckQueueRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimAuthorityRecheckQueueRow:
            raise ValueError(
                "row must be a ResearchSourceClaimAuthorityRecheckQueueRow",
            )
        _require_hard_flags("row", row)
        key = (row.claim_bucket, row.authority_bucket)
        if key in seen:
            raise ValueError("duplicate row claim_bucket and authority_bucket pair")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceClaimAuthorityRecheckQueueRow,
) -> tuple[Decimal, int, str, str]:
    return (
        -row.recheck_priority_score,
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.claim_bucket,
        row.authority_bucket,
    )


def _report_reason_codes(
    rows: Sequence[ResearchSourceClaimAuthorityRecheckQueueRow],
) -> tuple[str, ...]:
    if not rows:
        return ("claim_authority_recheck_queue_empty",)
    reason_codes = {f"claim_authority_recheck_queue_{_report_status(rows)}"}
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _status_count(
    rows: Sequence[ResearchSourceClaimAuthorityRecheckQueueRow],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_status(rows: Sequence[ResearchSourceClaimAuthorityRecheckQueueRow]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _average(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _validate_row_consistency(row: ResearchSourceClaimAuthorityRecheckQueueRow) -> None:
    if row.authority_gap_score != _quantize(_ONE - row.source_authority_score):
        raise ValueError("authority_gap_score must equal source authority gap")
    if row.source_confidence_gap_score != _quantize(
        _ONE - row.source_confidence_score,
    ):
        raise ValueError(
            "source_confidence_gap_score must equal source confidence gap",
        )
    expected_corroboration_gap = _clamp_ratio(
        _ONE
        - _clamp_ratio(
            row.corroborating_authority_count / row.required_authority_count,
        ),
    )
    if row.authority_corroboration_gap_score != expected_corroboration_gap:
        raise ValueError(
            "authority_corroboration_gap_score must match authority counts",
        )
    expected_score = _priority_score(
        authority_freshness_score=row.authority_freshness_score,
        authority_gap_score=row.authority_gap_score,
        conflict_score=row.conflict_score,
        source_confidence_gap_score=row.source_confidence_gap_score,
        authority_corroboration_gap_score=row.authority_corroboration_gap_score,
        deadline_proximity_score=row.deadline_proximity_score,
    )
    if row.recheck_priority_score != expected_score:
        raise ValueError("recheck_priority_score must match component scores")
    _validate_row_reason_code_consistency(row)


def _validate_row_reason_code_consistency(
    row: ResearchSourceClaimAuthorityRecheckQueueRow,
) -> None:
    reason_codes = set(row.reason_codes)
    status_codes = {
        f"claim_authority_recheck_queue_{status}" for status in _STATUSES
    }
    expected_status_code = f"claim_authority_recheck_queue_{row.status}"
    if reason_codes.intersection(status_codes) != {expected_status_code}:
        raise ValueError("reason_codes must match row status")

    generated_codes = set(status_codes)
    for prefix in _ROW_REASON_CODE_PREFIXES:
        category_codes = {
            f"{prefix}_clear",
            f"{prefix}_watch",
            f"{prefix}_block",
        }
        if len(reason_codes.intersection(category_codes)) != 1:
            raise ValueError(
                f"reason_codes must contain one {prefix} category",
            )
        generated_codes.update(category_codes)

    for reason_code in reason_codes.difference(generated_codes):
        if not reason_code.startswith("input_"):
            raise ValueError("reason_codes contain unsupported public code")
        input_reason_code = reason_code.removeprefix("input_")
        if not _REASON_CODE_RE.fullmatch(input_reason_code):
            raise ValueError("reason_codes contain invalid input reason code")
        _reject_unsafe_public_string("reason_codes", input_reason_code)


def _validate_report_consistency(
    report: ResearchSourceClaimAuthorityRecheckQueueReport,
) -> None:
    rows = report.rows
    expected_counts = {
        "row_count": _decimal_count(len(rows)),
        "stale_authority_count": _reason_level_count(
            rows,
            "authority_freshness",
        ),
        "authority_gap_count": _reason_level_count(rows, "authority_gap"),
        "conflict_count": _reason_level_count(rows, "claim_conflict"),
        "source_confidence_gap_count": _reason_level_count(
            rows,
            "source_confidence",
        ),
        "corroboration_gap_count": _reason_level_count(
            rows,
            "authority_corroboration",
        ),
        "deadline_proximity_count": _reason_level_count(
            rows,
            "deadline_proximity",
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_recheck_priority_score != _average(
        tuple(row.recheck_priority_score for row in rows),
    ):
        raise ValueError("average_recheck_priority_score must match rows")
    if report.max_recheck_priority_score != max(
        (row.recheck_priority_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_recheck_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _reason_level_count(
    rows: Sequence[ResearchSourceClaimAuthorityRecheckQueueRow],
    prefix: str,
) -> Decimal:
    watch_code = f"{prefix}_watch"
    block_code = f"{prefix}_block"
    return _decimal_count(
        sum(
            1
            for row in rows
            if watch_code in row.reason_codes or block_code in row.reason_codes
        ),
    )


def _row_values_without_digest(
    row: ResearchSourceClaimAuthorityRecheckQueueRow,
) -> dict[str, object]:
    values = asdict(row)
    values.pop("derived_validation_digest")
    return values


def _report_values_without_digest(
    report: ResearchSourceClaimAuthorityRecheckQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _row_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_values(values)


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_row_digest(row: ResearchSourceClaimAuthorityRecheckQueueRow) -> None:
    expected = _row_digest_from_values(_row_values_without_digest(row))
    if row.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match row payload")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected = _report_digest_from_values(unsigned_payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _report_from_payload(
    payload: object,
) -> ResearchSourceClaimAuthorityRecheckQueueReport:
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_exact_payload_keys("report payload", payload, _REPORT_PAYLOAD_KEYS)

    raw_rows = payload["rows"]
    if type(raw_rows) is not list:
        raise ValueError("rows must match exact public schema")
    rows = tuple(_row_from_payload(row) for row in raw_rows)

    parsed_report = ResearchSourceClaimAuthorityRecheckQueueReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        row_count=_decimal_from_payload("row_count", payload["row_count"]),
        stale_authority_count=_decimal_from_payload(
            "stale_authority_count",
            payload["stale_authority_count"],
        ),
        authority_gap_count=_decimal_from_payload(
            "authority_gap_count",
            payload["authority_gap_count"],
        ),
        conflict_count=_decimal_from_payload(
            "conflict_count",
            payload["conflict_count"],
        ),
        source_confidence_gap_count=_decimal_from_payload(
            "source_confidence_gap_count",
            payload["source_confidence_gap_count"],
        ),
        corroboration_gap_count=_decimal_from_payload(
            "corroboration_gap_count",
            payload["corroboration_gap_count"],
        ),
        deadline_proximity_count=_decimal_from_payload(
            "deadline_proximity_count",
            payload["deadline_proximity_count"],
        ),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        average_recheck_priority_score=_decimal_from_payload(
            "average_recheck_priority_score",
            payload["average_recheck_priority_score"],
        ),
        max_recheck_priority_score=_decimal_from_payload(
            "max_recheck_priority_score",
            payload["max_recheck_priority_score"],
        ),
        status=payload["status"],
        rows=rows,
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if parsed_report.payload != payload:
        raise ValueError("report payload must match exact public schema")
    return parsed_report


def _row_from_payload(
    payload: object,
) -> ResearchSourceClaimAuthorityRecheckQueueRow:
    if type(payload) is not dict:
        raise ValueError("row must match exact public schema")
    _require_exact_payload_keys("row payload", payload, _ROW_PAYLOAD_KEYS)
    return ResearchSourceClaimAuthorityRecheckQueueRow(
        claim_bucket=payload["claim_bucket"],
        authority_bucket=payload["authority_bucket"],
        claim_age_seconds=_decimal_from_payload(
            "claim_age_seconds",
            payload["claim_age_seconds"],
        ),
        authority_age_seconds=_decimal_from_payload(
            "authority_age_seconds",
            payload["authority_age_seconds"],
        ),
        authority_freshness_score=_decimal_from_payload(
            "authority_freshness_score",
            payload["authority_freshness_score"],
        ),
        source_authority_score=_decimal_from_payload(
            "source_authority_score",
            payload["source_authority_score"],
        ),
        authority_gap_score=_decimal_from_payload(
            "authority_gap_score",
            payload["authority_gap_score"],
        ),
        source_confidence_score=_decimal_from_payload(
            "source_confidence_score",
            payload["source_confidence_score"],
        ),
        source_confidence_gap_score=_decimal_from_payload(
            "source_confidence_gap_score",
            payload["source_confidence_gap_score"],
        ),
        conflict_score=_decimal_from_payload(
            "conflict_score",
            payload["conflict_score"],
        ),
        corroborating_authority_count=_decimal_from_payload(
            "corroborating_authority_count",
            payload["corroborating_authority_count"],
        ),
        required_authority_count=_decimal_from_payload(
            "required_authority_count",
            payload["required_authority_count"],
        ),
        authority_corroboration_gap_score=_decimal_from_payload(
            "authority_corroboration_gap_score",
            payload["authority_corroboration_gap_score"],
        ),
        deadline_proximity_score=_decimal_from_payload(
            "deadline_proximity_score",
            payload["deadline_proximity_score"],
        ),
        recheck_priority_score=_decimal_from_payload(
            "recheck_priority_score",
            payload["recheck_priority_score"],
        ),
        status=payload["status"],
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_exact_payload_keys(
    label: str,
    payload: dict[object, object],
    expected_keys: frozenset[str],
) -> None:
    if set(payload) != expected_keys:
        raise ValueError(f"{label} must match exact public schema")


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal string",
        ) from exc
    normalized = _require_decimal(field_name, parsed)
    if normalized.to_eng_string() != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _string_tuple_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must match exact public schema")
    return tuple(value)


def _json_ready(value: Any) -> Any:
    if type(value) is bool or value is None:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal subclasses are not supported")
        return _quantize(value).to_eng_string()
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    raise ValueError(f"unsupported JSON payload value {type(value).__name__}")


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
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


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


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_nonempty_text(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be nonempty text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or not _REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError(f"{field_name} must contain canonical reason codes")
        _reject_unsafe_public_string(field_name, reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            _reject_unsafe_public_string(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", field_value)
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_string(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, str):
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    raise ValueError(f"{label} contains unsupported public value")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_RECHECK_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimAuthorityRecheckQueueConfig",
    "ResearchSourceClaimAuthorityRecheckQueueInput",
    "ResearchSourceClaimAuthorityRecheckQueueReport",
    "ResearchSourceClaimAuthorityRecheckQueueRow",
    "build_research_source_claim_authority_recheck_queue_report",
    "research_source_claim_authority_recheck_queue_report_payload",
)
