"""Report-only evidence authority, conflict, and decay snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_AUTHORITY_CONFLICT_DECAY_CONFIG_VERSION = (
    "research-strategy-evidence-authority-conflict-decay-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_KEY_TERMS = (
    "candidate_id",
    "raw_candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "network",
    "live",
    "auth",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
)
_UNSAFE_PUBLIC_VALUE_TERMS = _UNSAFE_PUBLIC_KEY_TERMS + (
    "source_url",
    "postgres://",
    "mysql://",
    "sqlite://",
)
_UNSAFE_TOKEN_RE = re.compile(r"[a-z0-9]+")
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "insufficient_authority",
    "insufficient_family_authority",
    "evidence_conflict",
    "conflict_block",
    "evidence_decay",
    "decay_watch",
    "authority_conflict_decay_watch",
    "authority_conflict_decay_pass",
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_authority_conflict_decay_score",
        "max_conflict_score",
        "rows",
        "reason_codes",
        "public_payload",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "candidate_digest",
        "evidence_count",
        "evidence_family_count",
        "average_authority_score",
        "max_conflict_score",
        "average_decay_score",
        "authority_conflict_decay_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_PAYLOAD_ITEM_KEYS = frozenset(
    ("key", "value", "paper_only", "report_only", "readonly"),
)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAuthorityConflictDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_AUTHORITY_CONFLICT_DECAY_CONFIG_VERSION
    )
    max_decay_age_seconds: Decimal = Decimal("3600.000000")
    pass_score_threshold: Decimal = Decimal("0.650000")
    watch_score_threshold: Decimal = Decimal("0.350000")
    conflict_block_threshold: Decimal = Decimal("0.800000")
    min_evidence_family_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceAuthorityConflictDecayConfig:
            raise TypeError(
                "ResearchStrategyEvidenceAuthorityConflictDecayConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceAuthorityConflictDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyEvidenceAuthorityConflictDecayConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_AUTHORITY_CONFLICT_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_decay_age_seconds",
            _require_positive_decimal(
                "max_decay_age_seconds",
                self.max_decay_age_seconds,
            ),
        )
        for field_name in (
            "pass_score_threshold",
            "watch_score_threshold",
            "conflict_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_evidence_family_count",
            _require_positive_integral_decimal(
                "min_evidence_family_count",
                self.min_evidence_family_count,
            ),
        )
        if self.pass_score_threshold <= self.watch_score_threshold:
            raise ValueError("pass_score_threshold must exceed watch_score_threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAuthorityConflictDecaySignal:
    candidate_digest: str
    evidence_digest: str
    evidence_family: str
    observed_at: datetime
    authority_score: Decimal
    conflict_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceAuthorityConflictDecaySignal:
            raise TypeError(
                "ResearchStrategyEvidenceAuthorityConflictDecaySignal does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceAuthorityConflictDecaySignal:
            raise ValueError(
                "signal must be exactly "
                "ResearchStrategyEvidenceAuthorityConflictDecaySignal",
            )
        _require_sha256_digest("candidate_digest", self.candidate_digest)
        _require_sha256_digest("evidence_digest", self.evidence_digest)
        _require_public_identifier("evidence_family", self.evidence_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("authority_score", "conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem:
            raise TypeError(
                "ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAuthorityConflictDecayRow:
    candidate_digest: str
    evidence_count: Decimal
    evidence_family_count: Decimal
    average_authority_score: Decimal
    max_conflict_score: Decimal
    average_decay_score: Decimal
    authority_conflict_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceAuthorityConflictDecayRow:
            raise TypeError(
                "ResearchStrategyEvidenceAuthorityConflictDecayRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceAuthorityConflictDecayRow:
            raise ValueError(
                "row must be exactly ResearchStrategyEvidenceAuthorityConflictDecayRow",
            )
        _require_sha256_digest("candidate_digest", self.candidate_digest)
        for field_name in ("evidence_count", "evidence_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_authority_score",
            "max_conflict_score",
            "average_decay_score",
            "authority_conflict_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAuthorityConflictDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_conflict_decay_score: Decimal
    max_conflict_score: Decimal
    rows: tuple[ResearchStrategyEvidenceAuthorityConflictDecayRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceAuthorityConflictDecayReport:
            raise TypeError(
                "ResearchStrategyEvidenceAuthorityConflictDecayReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceAuthorityConflictDecayReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategyEvidenceAuthorityConflictDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_AUTHORITY_CONFLICT_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_authority_conflict_decay_score",
            "max_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
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
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchStrategyEvidenceAuthorityConflictDecayReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_evidence_authority_conflict_decay_report(
    signals: Sequence[ResearchStrategyEvidenceAuthorityConflictDecaySignal],
    *,
    generated_at: datetime,
    config: ResearchStrategyEvidenceAuthorityConflictDecayConfig | None = None,
    public_payload: Sequence[
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem
    ] = (),
) -> ResearchStrategyEvidenceAuthorityConflictDecayReport:
    """Build a deterministic local report-only authority/conflict/decay snapshot."""

    if config is None:
        config = ResearchStrategyEvidenceAuthorityConflictDecayConfig()
    if type(config) is not ResearchStrategyEvidenceAuthorityConflictDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyEvidenceAuthorityConflictDecayConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("signal observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_signals, generated_at, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "candidate_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_authority_conflict_decay_score": _average(
            tuple(row.authority_conflict_decay_score for row in rows),
        ),
        "max_conflict_score": max(
            (row.max_conflict_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEvidenceAuthorityConflictDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_evidence_authority_conflict_decay_report_payload(
    report: ResearchStrategyEvidenceAuthorityConflictDecayReport,
) -> dict[str, Any]:
    """Return the validated canonical public payload for a report."""

    if type(report) is not ResearchStrategyEvidenceAuthorityConflictDecayReport:
        raise ValueError(
            "report must be exactly "
            "ResearchStrategyEvidenceAuthorityConflictDecayReport",
        )
    _require_hard_flags("report", report)
    payload = report.payload
    _report_from_public_payload(payload)
    return payload


def validate_research_strategy_evidence_authority_conflict_decay_report_payload(
    payload: dict[str, Any],
) -> bool:
    """Validate an exact canonical public report payload."""

    _report_from_public_payload(payload)
    return True


def _build_rows(
    signals: tuple[ResearchStrategyEvidenceAuthorityConflictDecaySignal, ...],
    generated_at: datetime,
    config: ResearchStrategyEvidenceAuthorityConflictDecayConfig,
) -> tuple[ResearchStrategyEvidenceAuthorityConflictDecayRow, ...]:
    grouped: dict[str, list[ResearchStrategyEvidenceAuthorityConflictDecaySignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.candidate_digest, []).append(signal)
    return tuple(
        _row_for_candidate(candidate_digest, tuple(items), generated_at, config)
        for candidate_digest, items in sorted(grouped.items())
    )


def _row_for_candidate(
    candidate_digest: str,
    signals: tuple[ResearchStrategyEvidenceAuthorityConflictDecaySignal, ...],
    generated_at: datetime,
    config: ResearchStrategyEvidenceAuthorityConflictDecayConfig,
) -> ResearchStrategyEvidenceAuthorityConflictDecayRow:
    authority_scores = tuple(signal.authority_score for signal in signals)
    conflict_scores = tuple(signal.conflict_score for signal in signals)
    decay_scores = tuple(
        _decay_score(signal.observed_at, generated_at, config.max_decay_age_seconds)
        for signal in signals
    )
    average_authority = _average(authority_scores)
    max_conflict = max(conflict_scores, default=_ZERO)
    average_decay = _average(decay_scores)
    family_count = _decimal_count(len({signal.evidence_family for signal in signals}))
    score = _clamp_ratio(average_authority * (_ONE - max_conflict) * average_decay)
    status = _row_status(
        family_count=family_count,
        average_authority=average_authority,
        max_conflict=max_conflict,
        average_decay=average_decay,
        score=score,
        config=config,
    )
    return ResearchStrategyEvidenceAuthorityConflictDecayRow(
        candidate_digest=candidate_digest,
        evidence_count=_decimal_count(len(signals)),
        evidence_family_count=family_count,
        average_authority_score=average_authority,
        max_conflict_score=max_conflict,
        average_decay_score=average_decay,
        authority_conflict_decay_score=score,
        status=status,
        reason_codes=_row_reason_codes(
            family_count=family_count,
            average_authority=average_authority,
            max_conflict=max_conflict,
            average_decay=average_decay,
            score=score,
            status=status,
            config=config,
        ),
    )


def _decay_score(
    observed_at: datetime,
    generated_at: datetime,
    max_decay_age_seconds: Decimal,
) -> Decimal:
    age_seconds = _age_seconds(observed_at, generated_at)
    return _clamp_ratio(_ONE - (age_seconds / max_decay_age_seconds))


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds).quantize(_QUANT)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("age_seconds", seconds)


def _row_reason_codes(
    *,
    family_count: Decimal,
    average_authority: Decimal,
    max_conflict: Decimal,
    average_decay: Decimal,
    score: Decimal,
    status: str,
    config: ResearchStrategyEvidenceAuthorityConflictDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if average_authority < config.pass_score_threshold:
        reason_codes.append("insufficient_authority")
    if family_count < config.min_evidence_family_count:
        reason_codes.append("insufficient_family_authority")
    if max_conflict > _ZERO:
        reason_codes.append("evidence_conflict")
    if max_conflict >= config.conflict_block_threshold:
        reason_codes.append("conflict_block")
    if average_decay < _ONE:
        reason_codes.append("evidence_decay")
    if average_decay < config.pass_score_threshold:
        reason_codes.append("decay_watch")
    if status == "pass":
        reason_codes.append("authority_conflict_decay_pass")
    elif score < config.pass_score_threshold:
        reason_codes.append("authority_conflict_decay_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    family_count: Decimal,
    average_authority: Decimal,
    max_conflict: Decimal,
    average_decay: Decimal,
    score: Decimal,
    config: ResearchStrategyEvidenceAuthorityConflictDecayConfig,
) -> str:
    if (
        max_conflict >= config.conflict_block_threshold
        or score < config.watch_score_threshold
        or average_authority == _ZERO
        or average_decay == _ZERO
    ):
        return "block"
    if (
        family_count >= config.min_evidence_family_count
        and score >= config.pass_score_threshold
    ):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchStrategyEvidenceAuthorityConflictDecayRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEvidenceAuthorityConflictDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchStrategyEvidenceAuthorityConflictDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(
    row: ResearchStrategyEvidenceAuthorityConflictDecayRow,
) -> None:
    if row.evidence_family_count > row.evidence_count:
        raise ValueError("evidence_family_count must not exceed evidence_count")
    if row.status == "pass" and "authority_conflict_decay_pass" not in row.reason_codes:
        raise ValueError("pass rows must include authority_conflict_decay_pass")
    if row.status == "block" and (
        "conflict_block" not in row.reason_codes
        and "authority_conflict_decay_watch" not in row.reason_codes
    ):
        raise ValueError("block rows must include a blocking reason")


def _validate_report_consistency(
    report: ResearchStrategyEvidenceAuthorityConflictDecayReport,
) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_score = _average(
        tuple(row.authority_conflict_decay_score for row in report.rows),
    )
    if report.average_authority_conflict_decay_score != expected_score:
        raise ValueError("average_authority_conflict_decay_score must match rows")
    expected_max_conflict = max(
        (row.max_conflict_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_conflict_score != expected_max_conflict:
        raise ValueError("max_conflict_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_signals(
    signals: Sequence[ResearchStrategyEvidenceAuthorityConflictDecaySignal],
) -> tuple[ResearchStrategyEvidenceAuthorityConflictDecaySignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized: list[ResearchStrategyEvidenceAuthorityConflictDecaySignal] = []
    identities: set[tuple[str, str]] = set()
    for signal in signals:
        if type(signal) is not ResearchStrategyEvidenceAuthorityConflictDecaySignal:
            raise ValueError(
                "signals must contain "
                "ResearchStrategyEvidenceAuthorityConflictDecaySignal",
            )
        identity = (signal.candidate_digest, signal.evidence_digest)
        if identity in identities:
            raise ValueError("signals must be unique by candidate and evidence digest")
        identities.add(identity)
        normalized.append(signal)
    return tuple(
        sorted(
            normalized,
            key=lambda signal: (
                signal.candidate_digest,
                signal.observed_at,
                signal.evidence_digest,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyEvidenceAuthorityConflictDecayRow],
) -> tuple[ResearchStrategyEvidenceAuthorityConflictDecayRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized: list[ResearchStrategyEvidenceAuthorityConflictDecayRow] = []
    candidate_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyEvidenceAuthorityConflictDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyEvidenceAuthorityConflictDecayRow",
            )
        if row.candidate_digest in candidate_digests:
            raise ValueError("rows must have unique candidate digests")
        candidate_digests.add(row.candidate_digest)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.candidate_digest))


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem
    ],
) -> tuple[ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized: list[ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem] = []
    keys: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem",
            )
        if item.key in keys:
            raise ValueError("public_payload keys must be unique")
        keys.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _report_from_public_payload(
    payload: object,
) -> ResearchStrategyEvidenceAuthorityConflictDecayReport:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _require_public_payload_shape(payload)
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    _require_payload_hard_flags(payload)
    report = ResearchStrategyEvidenceAuthorityConflictDecayReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        status=_public_status("status", payload["status"]),
        candidate_count=_public_count("candidate_count", payload["candidate_count"]),
        pass_count=_public_count("pass_count", payload["pass_count"]),
        watch_count=_public_count("watch_count", payload["watch_count"]),
        block_count=_public_count("block_count", payload["block_count"]),
        average_authority_conflict_decay_score=_public_ratio(
            "average_authority_conflict_decay_score",
            payload["average_authority_conflict_decay_score"],
        ),
        max_conflict_score=_public_ratio(
            "max_conflict_score",
            payload["max_conflict_score"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in payload["rows"]),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        public_payload=tuple(
            _public_payload_item_from_payload(item)
            for item in payload["public_payload"]
        ),
        derived_validation_digest=_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if report.payload != payload:
        raise ValueError("public payload must use canonical ordering and values")
    return report


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyEvidenceAuthorityConflictDecayRow:
    return ResearchStrategyEvidenceAuthorityConflictDecayRow(
        candidate_digest=_public_digest(
            "candidate_digest",
            payload["candidate_digest"],
        ),
        evidence_count=_public_count("evidence_count", payload["evidence_count"]),
        evidence_family_count=_public_count(
            "evidence_family_count",
            payload["evidence_family_count"],
        ),
        average_authority_score=_public_ratio(
            "average_authority_score",
            payload["average_authority_score"],
        ),
        max_conflict_score=_public_ratio(
            "max_conflict_score",
            payload["max_conflict_score"],
        ),
        average_decay_score=_public_ratio(
            "average_decay_score",
            payload["average_decay_score"],
        ),
        authority_conflict_decay_score=_public_ratio(
            "authority_conflict_decay_score",
            payload["authority_conflict_decay_score"],
        ),
        status=_public_status("status", payload["status"]),
        reason_codes=_public_reason_codes("reason_codes", payload["reason_codes"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _public_payload_item_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem:
    return ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem(
        key=_public_string("key", payload["key"]),
        value=_public_string("value", payload["value"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_public_payload_shape(payload: dict[str, Any]) -> None:
    if set(payload) != _REPORT_PAYLOAD_KEYS:
        raise ValueError("payload keys must match the public report schema")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        if set(row) != _ROW_PAYLOAD_KEYS:
            raise ValueError("payload row keys must match the public row schema")
    public_payload = payload["public_payload"]
    if type(public_payload) is not list:
        raise ValueError("public_payload must be a list")
    for item in public_payload:
        if type(item) is not dict:
            raise ValueError("public_payload must contain JSON objects")
        if set(item) != _PUBLIC_PAYLOAD_ITEM_KEYS:
            raise ValueError(
                "public payload item keys must match the public item schema",
            )


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_status(field_name: str, value: object) -> str:
    return _require_status(field_name, value)


def _public_digest(field_name: str, value: object) -> str:
    _require_sha256_digest(field_name, value)
    return value


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not _PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(value)


def _public_count(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_integral_decimal(
        field_name,
        _public_decimal(field_name, value),
    )


def _public_ratio(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(field_name, _public_decimal(field_name, value))


def _public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if _contains_unsafe_term(lowered, _UNSAFE_PUBLIC_VALUE_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, or block")
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_integral_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


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


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    canonical = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if tuple(normalized) != canonical:
        raise ValueError("reason_codes must use canonical ordering")
    return canonical


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchStrategyEvidenceAuthorityConflictDecayReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
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
            raise ValueError(f"{current_path} must remain constructor-normalized")
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
            raise ValueError(f"{current_path} must remain constructor-normalized")
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
    lowered = key.lower()
    if _contains_unsafe_term(lowered, _UNSAFE_PUBLIC_KEY_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _contains_unsafe_term(value: str, terms: tuple[str, ...]) -> bool:
    tokens = set(_UNSAFE_TOKEN_RE.findall(value))
    value_tokens = tuple(_UNSAFE_TOKEN_RE.findall(value))
    for term in terms:
        if "://" in term and term in value:
            return True
        term_tokens = tuple(_UNSAFE_TOKEN_RE.findall(term))
        if len(term_tokens) == 1 and term_tokens[0] in tokens:
            return True
        if len(term_tokens) > 1:
            if any(
                value_tokens[index : index + len(term_tokens)] == term_tokens
                for index in range(len(value_tokens) - len(term_tokens) + 1)
            ):
                return True
    return False


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_AUTHORITY_CONFLICT_DECAY_CONFIG_VERSION",
    "ResearchStrategyEvidenceAuthorityConflictDecayConfig",
    "ResearchStrategyEvidenceAuthorityConflictDecayPublicPayloadItem",
    "ResearchStrategyEvidenceAuthorityConflictDecayReport",
    "ResearchStrategyEvidenceAuthorityConflictDecayRow",
    "ResearchStrategyEvidenceAuthorityConflictDecaySignal",
    "build_research_strategy_evidence_authority_conflict_decay_report",
    "research_strategy_evidence_authority_conflict_decay_report_payload",
    "validate_research_strategy_evidence_authority_conflict_decay_report_payload",
)
