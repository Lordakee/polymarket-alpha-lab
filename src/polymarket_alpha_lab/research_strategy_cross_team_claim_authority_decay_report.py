"""Report-only cross-team claim authority decay research policy.

The module is deterministic and side-effect free. Callers provide observations;
the policy returns read-only report records and a redacted public digest payload.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


__all__ = (
    "CrossTeamClaimAuthorityDecayConfig",
    "CrossTeamClaimAuthorityDecayObservation",
    "CrossTeamClaimAuthorityDecayReasonCodeCount",
    "CrossTeamClaimAuthorityDecayReport",
    "CrossTeamClaimAuthorityDecayRow",
    "build_research_strategy_cross_team_claim_authority_decay_report",
    "research_strategy_cross_team_claim_authority_decay_report_payload",
    "validate_research_strategy_cross_team_claim_authority_decay_report_payload",
)


DEFAULT_CONFIG_VERSION = "cross-team-claim-authority-decay-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_PAYLOAD_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

PUBLIC_PAYLOAD_KEYS = (
    "report_type",
    "generated_at",
    "config_version",
    "claim_count",
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_authority_score",
    "status",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)
PUBLIC_ROW_KEYS = (
    "claim_key",
    "observation_count",
    "team_count",
    "authority_count",
    "source_count",
    "latest_observed_at",
    "latest_source_age_seconds",
    "cross_team_confirmation_score",
    "authority_confidence_score",
    "recency_score",
    "authority_score",
    "cross_team_weight",
    "authority_weight",
    "recency_weight",
    "pass_authority_score",
    "watch_authority_score",
    "fresh_age_seconds",
    "stale_age_seconds",
    "observation_keys",
    "team_keys",
    "authority_keys",
    "source_keys",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REASON_CODE_COUNT_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


@final
@dataclass(frozen=True, slots=True)
class CrossTeamClaimAuthorityDecayConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    cross_team_weight: Decimal = Decimal("0.450000")
    authority_weight: Decimal = Decimal("0.350000")
    recency_weight: Decimal = Decimal("0.200000")
    pass_authority_score: Decimal = Decimal("0.700000")
    watch_authority_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CrossTeamClaimAuthorityDecayConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "cross_team_weight",
            "authority_weight",
            "recency_weight",
            "pass_authority_score",
            "watch_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if (
            _sum_decimal(
                (
                    self.cross_team_weight,
                    self.authority_weight,
                    self.recency_weight,
                ),
            )
            != ONE
        ):
            raise ValueError(
                "cross_team_weight, authority_weight, and recency_weight must sum to 1",
            )
        if self.pass_authority_score <= self.watch_authority_score:
            raise ValueError(
                "pass_authority_score must be greater than watch_authority_score",
            )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class CrossTeamClaimAuthorityDecayObservation:
    claim_id: str
    observation_id: str
    team_id: str
    authority_id: str
    source_label: str
    cross_team_confirmations: Decimal
    total_confirmations: Decimal
    authority_confidence: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CrossTeamClaimAuthorityDecayObservation, "observation")
        for field_name in (
            "claim_id",
            "observation_id",
            "team_id",
            "authority_id",
            "source_label",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "cross_team_confirmations",
            _require_nonnegative_whole_decimal(
                "cross_team_confirmations",
                self.cross_team_confirmations,
            ),
        )
        object.__setattr__(
            self,
            "total_confirmations",
            _require_positive_whole_decimal(
                "total_confirmations",
                self.total_confirmations,
            ),
        )
        if self.cross_team_confirmations > self.total_confirmations:
            raise ValueError(
                "cross_team_confirmations must be less than or equal to "
                "total_confirmations",
            )
        object.__setattr__(
            self,
            "authority_confidence",
            _require_probability_decimal(
                "authority_confidence",
                self.authority_confidence,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True, slots=True)
class CrossTeamClaimAuthorityDecayRow:
    claim_id: str
    observation_count: Decimal
    team_count: Decimal
    authority_count: Decimal
    source_count: Decimal
    latest_observed_at: datetime
    latest_source_age_seconds: Decimal
    cross_team_confirmation_score: Decimal
    authority_confidence_score: Decimal
    recency_score: Decimal
    authority_score: Decimal
    observation_ids: tuple[str, ...]
    team_ids: tuple[str, ...]
    authority_ids: tuple[str, ...]
    source_labels: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    cross_team_weight: Decimal = Decimal("0.450000")
    authority_weight: Decimal = Decimal("0.350000")
    recency_weight: Decimal = Decimal("0.200000")
    pass_authority_score: Decimal = Decimal("0.700000")
    watch_authority_score: Decimal = Decimal("0.400000")
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CrossTeamClaimAuthorityDecayRow, "row")
        for field_name in ("claim_id",):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "observation_count",
            "team_count",
            "authority_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "cross_team_confirmation_score",
            "authority_confidence_score",
            "recency_score",
            "authority_score",
            "cross_team_weight",
            "authority_weight",
            "recency_weight",
            "pass_authority_score",
            "watch_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_ids",
            "team_ids",
            "authority_ids",
            "source_labels",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=False,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if _sum_decimal(
            (
                self.cross_team_weight,
                self.authority_weight,
                self.recency_weight,
            ),
        ) != ONE:
            raise ValueError("row scoring weights must sum to 1")
        if self.pass_authority_score <= self.watch_authority_score:
            raise ValueError(
                "row pass_authority_score must be greater than watch_authority_score",
            )
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("row stale_age_seconds must be greater than fresh_age_seconds")
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@final
@dataclass(frozen=True, slots=True)
class CrossTeamClaimAuthorityDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CrossTeamClaimAuthorityDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class CrossTeamClaimAuthorityDecayReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_score: Decimal | None
    status: str
    rows: tuple[CrossTeamClaimAuthorityDecayRow, ...]
    reason_code_counts: tuple[CrossTeamClaimAuthorityDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CrossTeamClaimAuthorityDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_score",
            _require_optional_probability_decimal(
                "average_authority_score",
                self.average_authority_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.digest:
            _require_digest(self.digest)
            if self.digest != expected_digest:
                raise ValueError("digest does not match public payload")
        else:
            object.__setattr__(self, "digest", expected_digest)


def build_research_strategy_cross_team_claim_authority_decay_report(
    observations: Iterable[object],
    *,
    config: CrossTeamClaimAuthorityDecayConfig,
    generated_at: datetime,
) -> CrossTeamClaimAuthorityDecayReport:
    if type(config) is not CrossTeamClaimAuthorityDecayConfig:
        raise ValueError("config must be a CrossTeamClaimAuthorityDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_items = _normalize_observations(observations)
    for item in observation_items:
        _reject_future_observed_at(item, generated_at_utc)

    grouped: dict[str, list[CrossTeamClaimAuthorityDecayObservation]] = {}
    for item in observation_items:
        grouped.setdefault(item.claim_id, []).append(item)

    rows = tuple(
        _row_from_claim(
            claim_id=claim_id,
            observations=tuple(grouped[claim_id]),
            config=config,
            generated_at=generated_at_utc,
        )
        for claim_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return CrossTeamClaimAuthorityDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_authority_score=_average_authority_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_cross_team_claim_authority_decay_report_payload(
    report: CrossTeamClaimAuthorityDecayReport,
) -> dict[str, Any]:
    if type(report) is not CrossTeamClaimAuthorityDecayReport:
        raise ValueError("report must be a CrossTeamClaimAuthorityDecayReport")
    _require_hard_flags("report", report)
    payload = _public_payload_base(report)
    _validate_public_payload_schema(payload, include_digest=False)
    digest = _digest_payload(payload)
    if report.digest != digest:
        raise ValueError("digest does not match public payload")
    payload["digest"] = digest
    return validate_research_strategy_cross_team_claim_authority_decay_report_payload(
        payload,
    )


def validate_research_strategy_cross_team_claim_authority_decay_report_payload(
    payload: object,
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_public_payload_schema(payload, include_digest=True)
    expected_digest = _digest_payload(
        {key: value for key, value in payload.items() if key != "digest"},
    )
    if payload["digest"] != expected_digest:
        raise ValueError("digest does not match public payload")
    _reject_unsafe_public_payload(payload)
    _validate_public_payload_consistency(payload)
    return payload


def _row_from_claim(
    *,
    claim_id: str,
    observations: tuple[CrossTeamClaimAuthorityDecayObservation, ...],
    config: CrossTeamClaimAuthorityDecayConfig,
    generated_at: datetime,
) -> CrossTeamClaimAuthorityDecayRow:
    sorted_observations = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.observation_id,
                item.team_id,
                item.authority_id,
                item.source_label,
            ),
        ),
    )
    latest = max(sorted_observations, key=lambda item: item.observed_at)
    latest_age = _age_seconds(generated_at, latest.observed_at)
    cross_team_score = _average_decimal(
        tuple(
            _ratio(item.cross_team_confirmations, item.total_confirmations)
            for item in sorted_observations
        ),
    )
    confidence_score = _average_decimal(
        tuple(item.authority_confidence for item in sorted_observations),
    )
    recency_score = max(
        _recency_score(
            _age_seconds(generated_at, item.observed_at),
            fresh_age_seconds=config.fresh_age_seconds,
            stale_age_seconds=config.stale_age_seconds,
        )
        for item in sorted_observations
    )
    with localcontext(DECIMAL_CONTEXT):
        authority_score = _quantize(
            cross_team_score * config.cross_team_weight
            + confidence_score * config.authority_weight
            + recency_score * config.recency_weight,
        )
    status = _row_status(authority_score, config)
    reason_codes = _row_reason_codes(
        status=status,
        cross_team_confirmation_score=cross_team_score,
        authority_confidence_score=confidence_score,
        recency_score=recency_score,
        input_reason_codes=tuple(
            reason_code
            for item in sorted_observations
            for reason_code in item.reason_codes
        ),
    )

    return CrossTeamClaimAuthorityDecayRow(
        claim_id=claim_id,
        observation_count=_decimal_count(len(sorted_observations)),
        team_count=_decimal_count(
            len({item.team_id for item in sorted_observations}),
        ),
        authority_count=_decimal_count(
            len({item.authority_id for item in sorted_observations}),
        ),
        source_count=_decimal_count(
            len({item.source_label for item in sorted_observations}),
        ),
        latest_observed_at=latest.observed_at,
        latest_source_age_seconds=latest_age,
        cross_team_confirmation_score=cross_team_score,
        authority_confidence_score=confidence_score,
        recency_score=recency_score,
        authority_score=authority_score,
        cross_team_weight=config.cross_team_weight,
        authority_weight=config.authority_weight,
        recency_weight=config.recency_weight,
        pass_authority_score=config.pass_authority_score,
        watch_authority_score=config.watch_authority_score,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
        observation_ids=tuple(item.observation_id for item in sorted_observations),
        team_ids=tuple(sorted({item.team_id for item in sorted_observations})),
        authority_ids=tuple(sorted({item.authority_id for item in sorted_observations})),
        source_labels=tuple(sorted({item.source_label for item in sorted_observations})),
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[CrossTeamClaimAuthorityDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized = tuple(_coerce_observation(value) for value in values)
    if len({item.observation_id for item in normalized}) != len(normalized):
        raise ValueError("observation_id must be unique")
    return normalized


def _coerce_observation(value: object) -> CrossTeamClaimAuthorityDecayObservation:
    if type(value) is CrossTeamClaimAuthorityDecayObservation:
        return value
    if not _has_observation_shape(value):
        raise ValueError(
            "observations must contain CrossTeamClaimAuthorityDecayObservation-like "
            "objects",
        )
    return CrossTeamClaimAuthorityDecayObservation(
        claim_id=getattr(value, "claim_id"),
        observation_id=getattr(value, "observation_id"),
        team_id=getattr(value, "team_id"),
        authority_id=getattr(value, "authority_id"),
        source_label=getattr(value, "source_label"),
        cross_team_confirmations=getattr(value, "cross_team_confirmations"),
        total_confirmations=getattr(value, "total_confirmations"),
        authority_confidence=getattr(value, "authority_confidence"),
        observed_at=getattr(value, "observed_at"),
        reason_codes=getattr(value, "reason_codes"),
        paper_only=getattr(value, "paper_only"),
        report_only=getattr(value, "report_only"),
        readonly=getattr(value, "readonly"),
    )


def _has_observation_shape(value: object) -> bool:
    return all(
        hasattr(value, field_name)
        for field_name in (
            "claim_id",
            "observation_id",
            "team_id",
            "authority_id",
            "source_label",
            "cross_team_confirmations",
            "total_confirmations",
            "authority_confidence",
            "observed_at",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        )
    )


def _row_status(
    authority_score: Decimal,
    config: CrossTeamClaimAuthorityDecayConfig,
) -> str:
    if authority_score >= config.pass_authority_score:
        return "pass"
    if authority_score >= config.watch_authority_score:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    status: str,
    cross_team_confirmation_score: Decimal,
    authority_confidence_score: Decimal,
    recency_score: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [f"claim_authority_decay_{status}"]
    if cross_team_confirmation_score < Decimal("0.500000"):
        reason_codes.append("weak_cross_team_confirmation")
    if authority_confidence_score >= Decimal("0.700000"):
        reason_codes.append("authority_confidence_strong")
    else:
        reason_codes.append("weak_authority_confidence")
    if recency_score == ONE:
        reason_codes.append("fresh_authority_observations")
    elif recency_score == ZERO:
        reason_codes.append("stale_authority_observations")
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        allow_empty=False,
    )


def _summary_reason_codes(
    rows: tuple[CrossTeamClaimAuthorityDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_claim_authority_observations",)
    return tuple(
        reason_code
        for reason_code in (
            "claim_authority_decay_block",
            "claim_authority_decay_watch",
            "claim_authority_decay_pass",
        )
        if any(row.status == reason_code.rsplit("_", 1)[-1] for row in rows)
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if "claim_authority_decay_block" in reason_codes:
        return "block"
    if "claim_authority_decay_watch" in reason_codes:
        return "watch"
    if "claim_authority_decay_pass" in reason_codes:
        return "pass"
    return "block"


def _reason_code_counts(
    rows: tuple[CrossTeamClaimAuthorityDecayRow, ...],
    summary_reason_codes: tuple[str, ...],
) -> tuple[CrossTeamClaimAuthorityDecayReasonCodeCount, ...]:
    if not rows:
        return (
            CrossTeamClaimAuthorityDecayReasonCodeCount(
                reason_code=summary_reason_codes[0],
                count=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        CrossTeamClaimAuthorityDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(counts)
    )


def _status_count(rows: tuple[CrossTeamClaimAuthorityDecayRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_authority_score(
    rows: tuple[CrossTeamClaimAuthorityDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.authority_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("cannot average empty values")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _recency_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE
    if age_seconds >= stale_age_seconds:
        return ZERO
    window = stale_age_seconds - fresh_age_seconds
    elapsed = age_seconds - fresh_age_seconds
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - (elapsed / window))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal("1000000")
        )
    return _require_nonnegative_decimal("latest_source_age_seconds", seconds)


def _normalize_rows(
    rows: object,
) -> tuple[CrossTeamClaimAuthorityDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[CrossTeamClaimAuthorityDecayRow] = []
    for row in rows:
        if type(row) is not CrossTeamClaimAuthorityDecayRow:
            raise ValueError("rows must contain CrossTeamClaimAuthorityDecayRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda item: item.claim_id))


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[CrossTeamClaimAuthorityDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[CrossTeamClaimAuthorityDecayReasonCodeCount] = []
    for count in counts:
        if type(count) is not CrossTeamClaimAuthorityDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CrossTeamClaimAuthorityDecayReasonCodeCount",
            )
        normalized.append(count)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _validate_row_consistency(row: CrossTeamClaimAuthorityDecayRow) -> None:
    if row.observation_count != _decimal_count(len(row.observation_ids)):
        raise ValueError("observation_count must match observation_ids")
    if row.team_count != _decimal_count(len(row.team_ids)):
        raise ValueError("team_count must match team_ids")
    if row.authority_count != _decimal_count(len(row.authority_ids)):
        raise ValueError("authority_count must match authority_ids")
    if row.source_count != _decimal_count(len(row.source_labels)):
        raise ValueError("source_count must match source_labels")
    if row.observation_ids != tuple(sorted(row.observation_ids)):
        raise ValueError("observation_ids must use canonical sequence")
    for field_name in ("observation_ids", "team_ids", "authority_ids", "source_labels"):
        values = getattr(row, field_name)
        if len(set(values)) != len(values):
            raise ValueError(f"{field_name} must be unique")
    expected_recency_score = _recency_score(
        row.latest_source_age_seconds,
        fresh_age_seconds=row.fresh_age_seconds,
        stale_age_seconds=row.stale_age_seconds,
    )
    if row.recency_score != expected_recency_score:
        raise ValueError("recency_score must match derived age thresholds")
    with localcontext(DECIMAL_CONTEXT):
        expected_authority_score = _quantize(
            row.cross_team_confirmation_score * row.cross_team_weight
            + row.authority_confidence_score * row.authority_weight
            + row.recency_score * row.recency_weight,
        )
    if row.authority_score != expected_authority_score:
        raise ValueError("authority_score must match derived components")
    expected_status = (
        "pass"
        if row.authority_score >= row.pass_authority_score
        else "watch"
        if row.authority_score >= row.watch_authority_score
        else "block"
    )
    if row.status != expected_status:
        raise ValueError("status must match derived authority_score")
    expected_status_reason = f"claim_authority_decay_{row.status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("status reason code must match status")


def _validate_report_consistency(report: CrossTeamClaimAuthorityDecayReport) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.observation_count != sum(
        (row.observation_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_authority_score != _average_authority_score(report.rows):
        raise ValueError("average_authority_score must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_reason_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _reject_future_observed_at(
    observation: CrossTeamClaimAuthorityDecayObservation,
    generated_at: datetime,
) -> None:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must be at or before generated_at")


def _public_payload_base(report: CrossTeamClaimAuthorityDecayReport) -> dict[str, Any]:
    return {
        "report_type": "research_strategy_cross_team_claim_authority_decay_report",
        "generated_at": _utc_isoformat(report.generated_at),
        "config_version": report.config_version,
        "claim_count": _decimal_string(report.claim_count),
        "observation_count": _decimal_string(report.observation_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_authority_score": _optional_decimal_payload(
            report.average_authority_score,
        ),
        "status": report.status,
        "rows": [_public_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            {
                "reason_code": count.reason_code,
                "count": _decimal_string(count.count),
                "paper_only": count.paper_only,
                "report_only": count.report_only,
                "readonly": count.readonly,
            }
            for count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_row_payload(row: CrossTeamClaimAuthorityDecayRow) -> dict[str, Any]:
    return {
        "claim_key": _public_key("claim", row.claim_id),
        "observation_count": _decimal_string(row.observation_count),
        "team_count": _decimal_string(row.team_count),
        "authority_count": _decimal_string(row.authority_count),
        "source_count": _decimal_string(row.source_count),
        "latest_observed_at": _utc_isoformat(row.latest_observed_at),
        "latest_source_age_seconds": _decimal_string(row.latest_source_age_seconds),
        "cross_team_confirmation_score": _decimal_string(
            row.cross_team_confirmation_score,
        ),
        "authority_confidence_score": _decimal_string(row.authority_confidence_score),
        "recency_score": _decimal_string(row.recency_score),
        "authority_score": _decimal_string(row.authority_score),
        "cross_team_weight": _decimal_string(row.cross_team_weight),
        "authority_weight": _decimal_string(row.authority_weight),
        "recency_weight": _decimal_string(row.recency_weight),
        "pass_authority_score": _decimal_string(row.pass_authority_score),
        "watch_authority_score": _decimal_string(row.watch_authority_score),
        "fresh_age_seconds": _decimal_string(row.fresh_age_seconds),
        "stale_age_seconds": _decimal_string(row.stale_age_seconds),
        "observation_keys": [
            _public_key("observation", value) for value in row.observation_ids
        ],
        "team_keys": [_public_key("team", value) for value in row.team_ids],
        "authority_keys": [
            _public_key("authority", value) for value in row.authority_ids
        ],
        "source_keys": [_public_key("source", value) for value in row.source_labels],
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)


def _decimal_string(value: Decimal) -> str:
    return str(_quantize(value))


def _public_key(prefix: str, value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _report_digest(report: CrossTeamClaimAuthorityDecayReport) -> str:
    payload = _public_payload_base(report)
    _validate_public_payload_schema(payload, include_digest=False)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload_schema(
    payload: dict[str, Any],
    *,
    include_digest: bool,
) -> None:
    expected_keys = PUBLIC_PAYLOAD_KEYS if include_digest else PUBLIC_PAYLOAD_KEYS[:-1]
    _require_payload_keys("public payload", payload, expected_keys)
    if payload["report_type"] != "research_strategy_cross_team_claim_authority_decay_report":
        raise ValueError("report_type must match report")
    _require_payload_datetime_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "claim_count",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    _require_optional_decimal_payload_string(
        "average_authority_score",
        payload["average_authority_score"],
    )
    _require_status("status", payload["status"])
    _validate_public_rows(payload["rows"])
    _validate_public_reason_code_counts(payload["reason_code_counts"])
    _validate_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_payload_flags("public payload", payload)
    if include_digest:
        _require_digest(payload["digest"])
    _reject_public_numerics(payload)


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_payload_keys(
            "row payload",
            row,
            PUBLIC_ROW_KEYS,
        )
        _require_public_key("claim_key", row["claim_key"], "claim")
        for field_name in (
            "observation_count",
            "team_count",
            "authority_count",
            "source_count",
        ):
            _require_decimal_payload_string(field_name, row[field_name], whole=True)
        _require_payload_datetime_string(
            "latest_observed_at",
            row["latest_observed_at"],
        )
        for field_name in (
            "latest_source_age_seconds",
            "cross_team_confirmation_score",
            "authority_confidence_score",
            "recency_score",
            "authority_score",
            "cross_team_weight",
            "authority_weight",
            "recency_weight",
            "pass_authority_score",
            "watch_authority_score",
            "fresh_age_seconds",
            "stale_age_seconds",
        ):
            _require_decimal_payload_string(field_name, row[field_name], whole=False)
        _require_public_key_list(
            "observation_keys",
            row["observation_keys"],
            "observation",
        )
        _require_public_key_list("team_keys", row["team_keys"], "team")
        _require_public_key_list("authority_keys", row["authority_keys"], "authority")
        _require_public_key_list("source_keys", row["source_keys"], "source")
        _require_status("status", row["status"])
        _validate_public_reason_codes("row.reason_codes", row["reason_codes"])
        _require_payload_flags("row payload", row)


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in value:
        if type(count) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        _require_payload_keys(
            "reason_code_count payload",
            count,
            PUBLIC_REASON_CODE_COUNT_KEYS,
        )
        _require_reason_code("reason_code", count["reason_code"])
        _require_decimal_payload_string("count", count["count"], whole=True)
        _require_payload_flags("reason_code_count payload", count)


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    row_values = tuple(rows)
    claim_count = _payload_decimal("claim_count", payload["claim_count"], whole=True)
    observation_count = _payload_decimal(
        "observation_count",
        payload["observation_count"],
        whole=True,
    )
    status_counts = Counter(row["status"] for row in row_values)
    if claim_count != Decimal(len(row_values)):
        raise ValueError("claim_count must match rows")
    expected_observation_count = _sum_decimal(
        _payload_decimal("observation_count", row["observation_count"], whole=True)
        for row in row_values
    )
    if observation_count != expected_observation_count:
        raise ValueError("observation_count must match rows")
    for status in STATUSES:
        field_name = f"{status}_count"
        expected = Decimal(status_counts[status])
        if _payload_decimal(field_name, payload[field_name], whole=True) != expected:
            raise ValueError(f"{field_name} must match rows")

    average = payload["average_authority_score"]
    if not row_values:
        if average is not None:
            raise ValueError("average_authority_score must match rows")
    else:
        expected_average = _average_decimal(
            tuple(_payload_decimal("authority_score", row["authority_score"]) for row in row_values),
        )
        if _payload_decimal("average_authority_score", average) != expected_average:
            raise ValueError("average_authority_score must match rows")

    expected_reason_codes = _summary_reason_codes_from_statuses(
        tuple(row["status"] for row in row_values),
    )
    if tuple(payload["reason_codes"]) != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = _summary_status(expected_reason_codes)
    if payload["status"] != expected_status:
        raise ValueError("status must match reason_codes")

    expected_reason_counts = Counter(
        reason_code
        for row in row_values
        for reason_code in row["reason_codes"]
    )
    actual_reason_counts = {
        item["reason_code"]: _payload_decimal(item["reason_code"], item["count"], whole=True)
        for item in payload["reason_code_counts"]
    }
    if len(actual_reason_counts) != len(payload["reason_code_counts"]):
        raise ValueError("reason_code_counts must be unique")
    if set(actual_reason_counts) != set(expected_reason_counts):
        raise ValueError("reason_code_counts must match rows")
    for reason_code, count in expected_reason_counts.items():
        if actual_reason_counts[reason_code] != Decimal(count):
            raise ValueError("reason_code_counts must match rows")

    generated_at = _parse_payload_datetime("generated_at", payload["generated_at"])
    for row in row_values:
        if _payload_decimal("observation_count", row["observation_count"], whole=True) != Decimal(
            len(row["observation_keys"]),
        ):
            raise ValueError("observation_count must match observation_keys")
        if _payload_decimal("team_count", row["team_count"], whole=True) != Decimal(
            len(row["team_keys"]),
        ):
            raise ValueError("team_count must match team_keys")
        if _payload_decimal("authority_count", row["authority_count"], whole=True) != Decimal(
            len(row["authority_keys"]),
        ):
            raise ValueError("authority_count must match authority_keys")
        if _payload_decimal("source_count", row["source_count"], whole=True) != Decimal(
            len(row["source_keys"]),
        ):
            raise ValueError("source_count must match source_keys")
        if _parse_payload_datetime("latest_observed_at", row["latest_observed_at"]) > generated_at:
            raise ValueError("latest_observed_at must be at or before generated_at")
        cross_team_weight = _payload_decimal("cross_team_weight", row["cross_team_weight"])
        authority_weight = _payload_decimal("authority_weight", row["authority_weight"])
        recency_weight = _payload_decimal("recency_weight", row["recency_weight"])
        if _sum_decimal((cross_team_weight, authority_weight, recency_weight)) != ONE:
            raise ValueError("row scoring weights must sum to 1")
        pass_score = _payload_decimal("pass_authority_score", row["pass_authority_score"])
        watch_score = _payload_decimal("watch_authority_score", row["watch_authority_score"])
        if pass_score <= watch_score:
            raise ValueError("row scoring thresholds must be increasing")
        fresh_age = _payload_decimal("fresh_age_seconds", row["fresh_age_seconds"])
        stale_age = _payload_decimal("stale_age_seconds", row["stale_age_seconds"])
        if fresh_age <= ZERO or stale_age <= fresh_age:
            raise ValueError("row age thresholds must be increasing")
        expected_row_reason = f"claim_authority_decay_{row['status']}"
        if expected_row_reason not in row["reason_codes"]:
            raise ValueError("row reason_codes must match status")
        age = _payload_decimal(
            "latest_source_age_seconds",
            row["latest_source_age_seconds"],
        )
        if age < ZERO:
            raise ValueError("latest_source_age_seconds must be nonnegative")
        expected_recency_score = _recency_score(
            age,
            fresh_age_seconds=fresh_age,
            stale_age_seconds=stale_age,
        )
        for field_name in (
            "cross_team_confirmation_score",
            "authority_confidence_score",
            "recency_score",
            "authority_score",
        ):
            parsed = _payload_decimal(field_name, row[field_name])
            if parsed < ZERO or parsed > ONE:
                raise ValueError(f"{field_name} must be between 0 and 1")
        if _payload_decimal("recency_score", row["recency_score"]) != expected_recency_score:
            raise ValueError("recency_score must match derived age thresholds")
        with localcontext(DECIMAL_CONTEXT):
            expected_authority_score = _quantize(
                _payload_decimal(
                    "cross_team_confirmation_score",
                    row["cross_team_confirmation_score"],
                )
                * cross_team_weight
                + _payload_decimal(
                    "authority_confidence_score",
                    row["authority_confidence_score"],
                )
                * authority_weight
                + _payload_decimal("recency_score", row["recency_score"])
                * recency_weight,
            )
        if _payload_decimal("authority_score", row["authority_score"]) != expected_authority_score:
            raise ValueError("authority_score must match derived components")
        expected_row_status = (
            "pass"
            if expected_authority_score >= pass_score
            else "watch"
            if expected_authority_score >= watch_score
            else "block"
        )
        if row["status"] != expected_row_status:
            raise ValueError("row status must match derived authority_score")


def _summary_reason_codes_from_statuses(statuses: tuple[str, ...]) -> tuple[str, ...]:
    if not statuses:
        return ("no_claim_authority_observations",)
    return tuple(
        reason_code
        for reason_code in (
            "claim_authority_decay_block",
            "claim_authority_decay_watch",
            "claim_authority_decay_pass",
        )
        if any(status == reason_code.rsplit("_", 1)[-1] for status in statuses)
    )


def _payload_decimal(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
) -> Decimal:
    _require_decimal_payload_string(field_name, value, whole=whole)
    return Decimal(value)


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    keys = set(payload)
    expected_set = set(expected_keys)
    if keys == expected_set and tuple(payload) == expected_keys:
        return
    extra = keys - expected_set
    if extra:
        raise ValueError(f"{label} has unsupported field: {sorted(extra)[0]}")
    missing = expected_set - keys
    if missing:
        raise ValueError(f"{label} is missing field: {sorted(missing)[0]}")
    raise ValueError(f"{label} fields must use canonical sequence")


def _require_payload_datetime_string(field_name: str, value: object) -> None:
    _parse_payload_datetime(field_name, value)


def _parse_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != _utc_isoformat(normalized):
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool,
) -> Decimal:
    if type(value) is not str or DECIMAL_PAYLOAD_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if whole and parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    if _quantize(parsed) != parsed:
        raise ValueError(f"{field_name} must be quantized to six decimals")
    return parsed


def _require_optional_decimal_payload_string(
    field_name: str,
    value: object,
) -> None:
    if value is None:
        return
    _require_decimal_payload_string(field_name, value, whole=False)


def _require_public_key(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public key")
    marker = f"{prefix}:"
    if not value.startswith(marker) or len(value) != len(marker) + 16:
        raise ValueError(f"{field_name} must be a public key")
    digest = value[len(marker) :]
    if not all(character in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a public key")


def _require_public_key_list(
    field_name: str,
    value: object,
    prefix: str,
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_public_key(field_name, item, prefix)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")


def _validate_public_reason_codes(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_reason_code(field_name, item)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)
        return
    if type(value) is int or type(value) is float:
        raise ValueError("public payload numerics must be Decimal-derived strings")


def _reject_unsafe_public_payload(payload: dict[str, Any]) -> None:
    unsafe_keys = {
        "claim_id",
        "observation_id",
        "source_label",
        "source_labels",
        "raw_candidate",
        "raw_market",
        "raw_source",
        "source_url",
        "ta" + "ble",
        "d" + "sn",
        "t" + "oken",
        "w" + "allet",
        "or" + "der",
        "tr" + "ade",
        "api" + "_key",
    }
    for key, value in _walk_payload_items(payload):
        if key in unsafe_keys:
            raise ValueError("unsafe public payload contains raw field")
        if isinstance(value, str) and any(
            fragment in value.lower() for fragment in _unsafe_fragments()
        ):
            raise ValueError("unsafe public payload contains raw text")


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "://",
        "candidate",
        "market",
        "source_label",
        "source_labels",
        "claim_id",
        "observation_id",
        "private",
        "secret",
        "postgres",
        "warehouse",
        "ta" + "ble",
        "d" + "sn",
        "t" + "oken",
        "w" + "allet",
        "or" + "der",
        "tr" + "ade",
        "api" + "_key",
    )


def _walk_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("payload keys must be strings")
            items.append((key, item))
            items.extend(_walk_payload_items(item))
    elif isinstance(value, list):
        for item in value:
            items.append(("", item))
            items.extend(_walk_payload_items(item))
    elif type(value) not in (str, bool, type(None)):
        raise ValueError("payload must contain only JSON scalar values")
    return tuple(items)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _utc_isoformat(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _require_exact_type(value: object, expected: type[object], label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    quantized = _quantize(normalized)
    if quantized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    if normalized.is_zero():
        return ZERO
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not all(
        character.islower() or character.isdigit() or character == "_"
        for character in value
    ):
        raise ValueError(
            f"{field_name} must contain only lowercase letters, digits, or underscores",
        )


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_digest(value: object) -> None:
    if type(value) is not str or SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError("digest must be a sha256 hex string")
