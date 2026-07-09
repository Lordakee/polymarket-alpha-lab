"""Pure report-only claim-authority memory ladder report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_MEMORY_LADDER_REPORT_CONFIG_VERSION = (
    "research-source-claim-authority-memory-ladder-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
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
_REASON_ORDER = {
    "authority_memory_clear": 10,
    "authority_memory_watch": 10,
    "authority_memory_block": 10,
    "authority_score_clear": 20,
    "authority_score_watch": 20,
    "authority_score_block": 20,
    "claim_confidence_clear": 30,
    "claim_confidence_watch": 30,
    "claim_confidence_block": 30,
    "claim_contradiction_clear": 40,
    "claim_contradiction_watch": 40,
    "claim_contradiction_block": 40,
    "memory_reuse_clear": 50,
    "memory_reuse_watch": 50,
    "memory_reuse_block": 50,
    "support_gap_clear": 60,
    "support_gap_watch": 60,
    "support_gap_block": 60,
}


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_MEMORY_LADDER_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimAuthorityMemoryLadderConfig",
    "ResearchSourceClaimAuthorityMemoryLadderInput",
    "ResearchSourceClaimAuthorityMemoryLadderReport",
    "ResearchSourceClaimAuthorityMemoryLadderRow",
    "build_research_source_claim_authority_memory_ladder_report",
    "research_source_claim_authority_memory_ladder_report_digest",
    "research_source_claim_authority_memory_ladder_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityMemoryLadderConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
    )
    fresh_memory_age_seconds: Decimal = Decimal("3600.000000")
    stale_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_ladder_score: Decimal = Decimal("0.250000")
    block_ladder_score: Decimal = Decimal("0.700000")
    watch_authority_score: Decimal = Decimal("0.700000")
    block_authority_score: Decimal = Decimal("0.300000")
    watch_memory_reuse_score: Decimal = Decimal("0.600000")
    block_memory_reuse_score: Decimal = Decimal("0.300000")
    watch_claim_confidence_score: Decimal = Decimal("0.700000")
    block_claim_confidence_score: Decimal = Decimal("0.500000")
    watch_contradiction_score: Decimal = Decimal("0.300000")
    block_contradiction_score: Decimal = Decimal("0.700000")
    watch_support_gap_score: Decimal = Decimal("0.500000")
    block_support_gap_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityMemoryLadderConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityMemoryLadderConfig:
            raise ValueError(
                "config must be exactly ResearchSourceClaimAuthorityMemoryLadderConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_memory_age_seconds", "stale_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_ladder_score",
            "block_ladder_score",
            "watch_authority_score",
            "block_authority_score",
            "watch_memory_reuse_score",
            "block_memory_reuse_score",
            "watch_claim_confidence_score",
            "block_claim_confidence_score",
            "watch_contradiction_score",
            "block_contradiction_score",
            "watch_support_gap_score",
            "block_support_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_memory_age_seconds <= self.fresh_memory_age_seconds:
            raise ValueError(
                "stale_memory_age_seconds must exceed fresh_memory_age_seconds",
            )
        if self.block_ladder_score <= self.watch_ladder_score:
            raise ValueError("block_ladder_score must exceed watch_ladder_score")
        if self.block_authority_score > self.watch_authority_score:
            raise ValueError(
                "block_authority_score must not exceed watch_authority_score",
            )
        if self.block_memory_reuse_score > self.watch_memory_reuse_score:
            raise ValueError(
                "block_memory_reuse_score must not exceed watch_memory_reuse_score",
            )
        if self.block_claim_confidence_score > self.watch_claim_confidence_score:
            raise ValueError(
                "block_claim_confidence_score must not exceed "
                "watch_claim_confidence_score",
            )
        if self.block_contradiction_score < self.watch_contradiction_score:
            raise ValueError(
                "block_contradiction_score must be at least watch_contradiction_score",
            )
        if self.block_support_gap_score < self.watch_support_gap_score:
            raise ValueError(
                "block_support_gap_score must be at least watch_support_gap_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityMemoryLadderInput:
    claim_bucket: str
    authority_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    claim_observed_at: datetime
    memory_last_checked_at: datetime
    authority_score: Decimal
    memory_reuse_score: Decimal
    claim_confidence_score: Decimal
    contradiction_score: Decimal
    supporting_evidence_count: Decimal
    required_evidence_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityMemoryLadderInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityMemoryLadderInput:
            raise ValueError(
                "input must be exactly ResearchSourceClaimAuthorityMemoryLadderInput",
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
            "memory_last_checked_at",
            _as_utc("memory_last_checked_at", self.memory_last_checked_at),
        )
        for field_name in (
            "authority_score",
            "memory_reuse_score",
            "claim_confidence_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "supporting_evidence_count",
            _require_nonnegative_decimal(
                "supporting_evidence_count",
                self.supporting_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "required_evidence_count",
            _require_positive_decimal(
                "required_evidence_count",
                self.required_evidence_count,
            ),
        )
        if self.supporting_evidence_count > self.required_evidence_count:
            raise ValueError(
                "supporting_evidence_count must not exceed required_evidence_count",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityMemoryLadderRow:
    claim_digest: str
    authority_digest: str
    claim_age_seconds: Decimal
    memory_age_seconds: Decimal
    memory_decay_score: Decimal
    authority_score: Decimal
    authority_gap_score: Decimal
    memory_reuse_score: Decimal
    memory_reuse_gap_score: Decimal
    claim_confidence_score: Decimal
    claim_confidence_gap_score: Decimal
    contradiction_score: Decimal
    supporting_evidence_count: Decimal
    required_evidence_count: Decimal
    support_gap_score: Decimal
    memory_ladder_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityMemoryLadderRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityMemoryLadderRow:
            raise ValueError(
                "row must be exactly ResearchSourceClaimAuthorityMemoryLadderRow",
            )
        _require_digest_reference("claim_digest", self.claim_digest)
        _require_digest_reference("authority_digest", self.authority_digest)
        for field_name in (
            "claim_age_seconds",
            "memory_age_seconds",
            "supporting_evidence_count",
            "required_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_evidence_count <= _ZERO:
            raise ValueError("required_evidence_count must be positive")
        if self.supporting_evidence_count > self.required_evidence_count:
            raise ValueError(
                "supporting_evidence_count must not exceed required_evidence_count",
            )
        for field_name in (
            "memory_decay_score",
            "authority_score",
            "authority_gap_score",
            "memory_reuse_score",
            "memory_reuse_gap_score",
            "claim_confidence_score",
            "claim_confidence_gap_score",
            "contradiction_score",
            "support_gap_score",
            "memory_ladder_score",
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
class ResearchSourceClaimAuthorityMemoryLadderReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    stale_memory_count: Decimal
    authority_gap_count: Decimal
    memory_reuse_gap_count: Decimal
    claim_confidence_gap_count: Decimal
    contradiction_count: Decimal
    support_gap_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_ladder_score: Decimal
    max_memory_ladder_score: Decimal
    status: str
    rows: tuple[ResearchSourceClaimAuthorityMemoryLadderRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimAuthorityMemoryLadderReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityMemoryLadderReport:
            raise ValueError(
                "report must be exactly ResearchSourceClaimAuthorityMemoryLadderReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "stale_memory_count",
            "authority_gap_count",
            "memory_reuse_gap_count",
            "claim_confidence_gap_count",
            "contradiction_count",
            "support_gap_count",
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
            "average_memory_ladder_score",
            "max_memory_ladder_score",
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_report(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_source_claim_authority_memory_ladder_report(
    rows: tuple[ResearchSourceClaimAuthorityMemoryLadderInput, ...]
    | list[ResearchSourceClaimAuthorityMemoryLadderInput],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimAuthorityMemoryLadderConfig | None = None,
) -> ResearchSourceClaimAuthorityMemoryLadderReport:
    if config is None:
        config = ResearchSourceClaimAuthorityMemoryLadderConfig()
    if type(config) is not ResearchSourceClaimAuthorityMemoryLadderConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimAuthorityMemoryLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_inputs(rows)
    for item in normalized_rows:
        if item.claim_observed_at > generated_at:
            raise ValueError("claim_observed_at must not be after generated_at")
        if item.memory_last_checked_at > generated_at:
            raise ValueError("memory_last_checked_at must not be after generated_at")
    report_rows = _normalize_rows(
        tuple(_row_for_input(item, config, generated_at) for item in normalized_rows),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "row_count": _decimal_count(len(report_rows)),
        "stale_memory_count": _decimal_count(
            sum(1 for row in report_rows if row.memory_decay_score > _ZERO),
        ),
        "authority_gap_count": _decimal_count(
            sum(1 for row in report_rows if row.authority_score < config.watch_authority_score),
        ),
        "memory_reuse_gap_count": _decimal_count(
            sum(1 for row in report_rows if row.memory_reuse_score < config.watch_memory_reuse_score),
        ),
        "claim_confidence_gap_count": _decimal_count(
            sum(
                1
                for row in report_rows
                if row.claim_confidence_score < config.watch_claim_confidence_score
            ),
        ),
        "contradiction_count": _decimal_count(
            sum(
                1
                for row in report_rows
                if row.contradiction_score >= config.watch_contradiction_score
            ),
        ),
        "support_gap_count": _decimal_count(
            sum(1 for row in report_rows if row.support_gap_score >= config.watch_support_gap_score),
        ),
        "pass_count": _decimal_count(_status_count(report_rows, "pass")),
        "watch_count": _decimal_count(_status_count(report_rows, "watch")),
        "block_count": _decimal_count(_status_count(report_rows, "block")),
        "average_memory_ladder_score": _average(
            tuple(row.memory_ladder_score for row in report_rows),
        ),
        "max_memory_ladder_score": max(
            (row.memory_ladder_score for row in report_rows),
            default=_ZERO,
        ),
        "status": _report_status(report_rows),
        "rows": report_rows,
        "reason_codes": _report_reason_codes(report_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimAuthorityMemoryLadderReport(**values)


def research_source_claim_authority_memory_ladder_report_payload(
    report: ResearchSourceClaimAuthorityMemoryLadderReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchSourceClaimAuthorityMemoryLadderReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
    else:
        raise ValueError("report must be a ResearchSourceClaimAuthorityMemoryLadderReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return _freeze_json_object(payload)


def research_source_claim_authority_memory_ladder_report_digest(
    report: ResearchSourceClaimAuthorityMemoryLadderReport,
) -> str:
    if type(report) is not ResearchSourceClaimAuthorityMemoryLadderReport:
        raise ValueError("report must be a ResearchSourceClaimAuthorityMemoryLadderReport")
    _require_hard_flags("report", report)
    return _report_digest_from_report(report)


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


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_for_input(
    item: ResearchSourceClaimAuthorityMemoryLadderInput,
    config: ResearchSourceClaimAuthorityMemoryLadderConfig,
    generated_at: datetime,
) -> ResearchSourceClaimAuthorityMemoryLadderRow:
    claim_age = _seconds_between(generated_at, item.claim_observed_at)
    memory_age = _seconds_between(generated_at, item.memory_last_checked_at)
    memory_decay = _memory_decay_score(memory_age, config)
    authority_gap = _clamp_ratio(_ONE - item.authority_score)
    memory_reuse_gap = _clamp_ratio(_ONE - item.memory_reuse_score)
    claim_confidence_gap = _clamp_ratio(_ONE - item.claim_confidence_score)
    support_gap = _clamp_ratio(
        _ONE
        - _clamp_ratio(item.supporting_evidence_count / item.required_evidence_count),
    )
    ladder_score = _memory_ladder_score(
        memory_decay_score=memory_decay,
        authority_gap_score=authority_gap,
        memory_reuse_gap_score=memory_reuse_gap,
        claim_confidence_gap_score=claim_confidence_gap,
        contradiction_score=item.contradiction_score,
        support_gap_score=support_gap,
    )
    status = _row_status(
        memory_decay_score=memory_decay,
        authority_score=item.authority_score,
        memory_reuse_score=item.memory_reuse_score,
        claim_confidence_score=item.claim_confidence_score,
        contradiction_score=item.contradiction_score,
        support_gap_score=support_gap,
        memory_ladder_score=ladder_score,
        config=config,
    )
    return ResearchSourceClaimAuthorityMemoryLadderRow(
        claim_digest=_digest_reference(
            f"{item.claim_bucket}\x1f{item.private_candidate_reference}",
        ),
        authority_digest=_digest_reference(
            f"{item.authority_bucket}\x1f{item.private_source_reference}",
        ),
        claim_age_seconds=claim_age,
        memory_age_seconds=memory_age,
        memory_decay_score=memory_decay,
        authority_score=item.authority_score,
        authority_gap_score=authority_gap,
        memory_reuse_score=item.memory_reuse_score,
        memory_reuse_gap_score=memory_reuse_gap,
        claim_confidence_score=item.claim_confidence_score,
        claim_confidence_gap_score=claim_confidence_gap,
        contradiction_score=item.contradiction_score,
        supporting_evidence_count=item.supporting_evidence_count,
        required_evidence_count=item.required_evidence_count,
        support_gap_score=support_gap,
        memory_ladder_score=ladder_score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            memory_decay_score=memory_decay,
            support_gap_score=support_gap,
            config=config,
        ),
    )


def _memory_decay_score(
    memory_age_seconds: Decimal,
    config: ResearchSourceClaimAuthorityMemoryLadderConfig,
) -> Decimal:
    if memory_age_seconds <= config.fresh_memory_age_seconds:
        return _ZERO
    if memory_age_seconds >= config.stale_memory_age_seconds:
        return _ONE
    denominator = config.stale_memory_age_seconds - config.fresh_memory_age_seconds
    return _clamp_ratio(
        (memory_age_seconds - config.fresh_memory_age_seconds) / denominator,
    )


def _memory_ladder_score(
    *,
    memory_decay_score: Decimal,
    authority_gap_score: Decimal,
    memory_reuse_gap_score: Decimal,
    claim_confidence_gap_score: Decimal,
    contradiction_score: Decimal,
    support_gap_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        (
            memory_decay_score
            + authority_gap_score
            + memory_reuse_gap_score
            + claim_confidence_gap_score
            + contradiction_score
            + support_gap_score
        )
        / _SIX,
    )


def _row_status(
    *,
    memory_decay_score: Decimal,
    authority_score: Decimal,
    memory_reuse_score: Decimal,
    claim_confidence_score: Decimal,
    contradiction_score: Decimal,
    support_gap_score: Decimal,
    memory_ladder_score: Decimal,
    config: ResearchSourceClaimAuthorityMemoryLadderConfig,
) -> str:
    if (
        memory_ladder_score >= config.block_ladder_score
        or memory_decay_score >= _ONE
        or authority_score <= config.block_authority_score
        or memory_reuse_score <= config.block_memory_reuse_score
        or claim_confidence_score <= config.block_claim_confidence_score
        or contradiction_score >= config.block_contradiction_score
        or support_gap_score >= config.block_support_gap_score
    ):
        return "block"
    if (
        memory_ladder_score >= config.watch_ladder_score
        or memory_decay_score > _ZERO
        or authority_score < config.watch_authority_score
        or memory_reuse_score < config.watch_memory_reuse_score
        or claim_confidence_score < config.watch_claim_confidence_score
        or contradiction_score >= config.watch_contradiction_score
        or support_gap_score >= config.watch_support_gap_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchSourceClaimAuthorityMemoryLadderInput,
    status: str,
    memory_decay_score: Decimal,
    support_gap_score: Decimal,
    config: ResearchSourceClaimAuthorityMemoryLadderConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if memory_decay_score >= _ONE:
        codes.append("authority_memory_block")
    elif memory_decay_score > _ZERO:
        codes.append("authority_memory_watch")
    else:
        codes.append("authority_memory_clear")

    if item.authority_score <= config.block_authority_score:
        codes.append("authority_score_block")
    elif item.authority_score < config.watch_authority_score:
        codes.append("authority_score_watch")
    else:
        codes.append("authority_score_clear")

    if item.claim_confidence_score <= config.block_claim_confidence_score:
        codes.append("claim_confidence_block")
    elif item.claim_confidence_score < config.watch_claim_confidence_score:
        codes.append("claim_confidence_watch")
    else:
        codes.append("claim_confidence_clear")

    if item.contradiction_score >= config.block_contradiction_score:
        codes.append("claim_contradiction_block")
    elif item.contradiction_score >= config.watch_contradiction_score:
        codes.append("claim_contradiction_watch")
    else:
        codes.append("claim_contradiction_clear")

    codes.extend(f"input_{code}" for code in item.reason_codes)

    if item.memory_reuse_score <= config.block_memory_reuse_score:
        codes.append("memory_reuse_block")
    elif item.memory_reuse_score < config.watch_memory_reuse_score:
        codes.append("memory_reuse_watch")
    else:
        codes.append("memory_reuse_clear")

    if support_gap_score >= config.block_support_gap_score:
        codes.append("support_gap_block")
    elif support_gap_score >= config.watch_support_gap_score:
        codes.append("support_gap_watch")
    else:
        codes.append("support_gap_clear")

    normalized = _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)
    if status == "pass" and any(code.endswith("_watch") or code.endswith("_block") for code in normalized):
        raise ValueError("reason_codes must match status")
    return normalized


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceClaimAuthorityMemoryLadderInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimAuthorityMemoryLadderInput:
            raise ValueError(
                "rows must contain ResearchSourceClaimAuthorityMemoryLadderInput values",
            )
        _require_hard_flags("input", row)
        key = (row.claim_bucket, row.authority_bucket)
        if key in seen:
            raise ValueError("duplicate claim and authority buckets are not allowed")
        seen.add(key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceClaimAuthorityMemoryLadderRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceClaimAuthorityMemoryLadderRow:
            raise ValueError(
                "rows must contain ResearchSourceClaimAuthorityMemoryLadderRow values",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceClaimAuthorityMemoryLadderRow) -> tuple[int, Decimal, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (status_rank[row.status], _ONE - row.memory_ladder_score, row.claim_digest)


def _status_count(
    rows: tuple[ResearchSourceClaimAuthorityMemoryLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_status(rows: tuple[ResearchSourceClaimAuthorityMemoryLadderRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimAuthorityMemoryLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("authority_memory_clear",)
    codes = {code for row in rows for code in row.reason_codes}
    return tuple(sorted(codes, key=_reason_sort_key))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _validate_row_consistency(row: ResearchSourceClaimAuthorityMemoryLadderRow) -> None:
    if row.authority_gap_score != _clamp_ratio(_ONE - row.authority_score):
        raise ValueError("authority_gap_score must match authority_score")
    if row.memory_reuse_gap_score != _clamp_ratio(_ONE - row.memory_reuse_score):
        raise ValueError("memory_reuse_gap_score must match memory_reuse_score")
    if row.claim_confidence_gap_score != _clamp_ratio(
        _ONE - row.claim_confidence_score,
    ):
        raise ValueError("claim_confidence_gap_score must match claim_confidence_score")
    expected_support_gap = _clamp_ratio(
        _ONE
        - _clamp_ratio(row.supporting_evidence_count / row.required_evidence_count),
    )
    if row.support_gap_score != expected_support_gap:
        raise ValueError("support_gap_score must match evidence counts")
    expected_ladder_score = _memory_ladder_score(
        memory_decay_score=row.memory_decay_score,
        authority_gap_score=row.authority_gap_score,
        memory_reuse_gap_score=row.memory_reuse_gap_score,
        claim_confidence_gap_score=row.claim_confidence_gap_score,
        contradiction_score=row.contradiction_score,
        support_gap_score=row.support_gap_score,
    )
    if row.memory_ladder_score != expected_ladder_score:
        raise ValueError("memory_ladder_score must match component scores")


def _validate_report_consistency(
    report: ResearchSourceClaimAuthorityMemoryLadderReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    expected_gap_counts = (
        (
            "stale_memory_count",
            _decimal_count(sum(1 for row in rows if row.memory_decay_score > _ZERO)),
        ),
        (
            "authority_gap_count",
            _reason_count(rows, ("authority_score_watch", "authority_score_block")),
        ),
        (
            "memory_reuse_gap_count",
            _reason_count(rows, ("memory_reuse_watch", "memory_reuse_block")),
        ),
        (
            "claim_confidence_gap_count",
            _reason_count(rows, ("claim_confidence_watch", "claim_confidence_block")),
        ),
        (
            "contradiction_count",
            _reason_count(
                rows,
                ("claim_contradiction_watch", "claim_contradiction_block"),
            ),
        ),
        (
            "support_gap_count",
            _reason_count(rows, ("support_gap_watch", "support_gap_block")),
        ),
    )
    for field_name, expected_count in expected_gap_counts:
        if getattr(report, field_name) != expected_count:
            raise ValueError(f"{field_name} must match rows")
    if report.average_memory_ladder_score != _average(
        tuple(row.memory_ladder_score for row in rows),
    ):
        raise ValueError("average_memory_ladder_score must match rows")
    if report.max_memory_ladder_score != max(
        (row.memory_ladder_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_memory_ladder_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _reason_count(
    rows: tuple[ResearchSourceClaimAuthorityMemoryLadderRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _require_nonempty_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty stripped text")


def _require_digest_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 reference")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


def _decimal_count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(str(delta.days * 86400 + delta.seconds))
    microseconds = Decimal(str(delta.microseconds)) / Decimal("1000000")
    return _require_nonnegative_decimal("age_seconds", seconds + microseconds)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
            raise ValueError(f"{field_name} contains invalid reason code")
        normalized.append(value)
    return tuple(sorted(dict.fromkeys(normalized), key=_reason_sort_key))


def _reason_sort_key(value: str) -> tuple[int, str]:
    if value.startswith("input_"):
        return (45, value)
    if value in _REASON_ORDER:
        return (_REASON_ORDER[value], value)
    return (90, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public field must be a string")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_unsafe_public_fragment(field.name):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError(f"{label} contains unsafe public value")
    if not allow_json_containers and type(value) in (int, float):
        raise ValueError(f"{label} public numerics must be Decimal-backed")


def _contains_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    squashed = "".join(character for character in normalized if character.isalnum())
    return any(
        fragment in normalized or fragment in squashed
        for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    )


def _digest_reference(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _report_digest_from_report(
    report: ResearchSourceClaimAuthorityMemoryLadderReport,
) -> str:
    payload = report.payload
    payload.pop("derived_validation_digest", None)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _validate_payload_digest(payload: dict[str, object]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _payload_digest(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value
