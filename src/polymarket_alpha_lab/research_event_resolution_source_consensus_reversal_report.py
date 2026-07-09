"""Report-only event resolution source consensus reversal reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION = (
    "research-event-resolution-source-consensus-reversal-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_BLOCK_REASON_CODES = frozenset(
    (
        "consensus_reversal_support_block",
        "consensus_reversal_family_block",
        "consensus_reversal_freshness_block",
        "consensus_reversal_contradiction_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "consensus_reversal_support_block",
    "consensus_reversal_support_watch",
    "consensus_reversal_family_block",
    "consensus_reversal_family_watch",
    "consensus_reversal_freshness_block",
    "consensus_reversal_freshness_watch",
    "consensus_reversal_contradiction_block",
    "consensus_reversal_contradiction_watch",
    "consensus_reversal_confirmation_watch",
    "source_consensus_reversal_pass",
    "source_consensus_stable_pass",
    "empty_source_consensus_reversal_set",
)
_STATUS_SORT_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "candidate",
        "market",
        _join_parts("que", "stion"),
        "url",
        "text",
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    ),
)
_UNSAFE_PUBLIC_VALUE_PATTERNS = (
    "://",
    "candidate",
    "credential",
    "dsn",
    "market id",
    "market_id",
    "market slug",
    "market_slug",
    _join_parts("ord", "er"),
    "password",
    "postgres",
    _join_parts("que", "stion"),
    _join_parts("recomm", "end"),
    _join_parts("siz", "ing"),
    "source text",
    "source_text",
    "source url",
    "source_url",
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("tra", "de"),
    _join_parts("wal", "let"),
)


@dataclass(frozen=True)
class ResearchEventResolutionSourceConsensusReversalConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION
    )
    pass_current_support_count: Decimal = Decimal("3.000000")
    watch_current_support_count: Decimal = Decimal("2.000000")
    pass_independent_source_family_count: Decimal = Decimal("2.000000")
    watch_independent_source_family_count: Decimal = Decimal("1.000000")
    stale_source_watch_seconds: Decimal = Decimal("7200.000000")
    stale_source_block_seconds: Decimal = Decimal("86400.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.250000")
    contradiction_block_pressure: Decimal = Decimal("0.500000")
    confirmation_watch_seconds: Decimal = Decimal("1800.000000")
    support_weight: Decimal = Decimal("0.360000")
    family_weight: Decimal = Decimal("0.240000")
    freshness_weight: Decimal = Decimal("0.100000")
    contradiction_weight: Decimal = Decimal("0.200000")
    confirmation_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceConsensusReversalConfig:
            raise TypeError(
                "ResearchEventResolutionSourceConsensusReversalConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionSourceConsensusReversalConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionSourceConsensusReversalConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_current_support_count",
            "watch_current_support_count",
            "pass_independent_source_family_count",
            "watch_independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_current_support_count > self.pass_current_support_count:
            raise ValueError(
                "watch_current_support_count must not exceed pass_current_support_count",
            )
        if (
            self.watch_independent_source_family_count
            > self.pass_independent_source_family_count
        ):
            raise ValueError(
                "watch_independent_source_family_count must not exceed "
                "pass_independent_source_family_count",
            )
        for field_name in (
            "stale_source_watch_seconds",
            "stale_source_block_seconds",
            "confirmation_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_block_seconds < self.stale_source_watch_seconds:
            raise ValueError(
                "stale_source_block_seconds must be greater than or equal to "
                "stale_source_watch_seconds",
            )
        for field_name in (
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "support_weight",
            "family_weight",
            "freshness_weight",
            "contradiction_weight",
            "confirmation_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.contradiction_watch_pressure > self.contradiction_block_pressure:
            raise ValueError(
                "contradiction_watch_pressure must not exceed "
                "contradiction_block_pressure",
            )
        if (
            self.support_weight
            + self.family_weight
            + self.freshness_weight
            + self.contradiction_weight
            + self.confirmation_weight
            != _ONE
        ):
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceConsensusReversalInput:
    event_digest: str
    previous_consensus_digest: str
    current_consensus_digest: str
    current_support_count: Decimal
    independent_source_family_count: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    contradiction_pressure: Decimal
    seconds_since_reversal: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceConsensusReversalInput:
            raise TypeError(
                "ResearchEventResolutionSourceConsensusReversalInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionSourceConsensusReversalInput:
            raise ValueError(
                "input must be exactly "
                "ResearchEventResolutionSourceConsensusReversalInput",
            )
        for field_name in (
            "event_digest",
            "previous_consensus_digest",
            "current_consensus_digest",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        for field_name in (
            "current_support_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_source_age_seconds",
            "oldest_source_age_seconds",
            "seconds_since_reversal",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_source_age_seconds < self.newest_source_age_seconds:
            raise ValueError(
                "oldest_source_age_seconds must be greater than or equal to "
                "newest_source_age_seconds",
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal("contradiction_pressure", self.contradiction_pressure),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceConsensusReversalPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceConsensusReversalPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionSourceConsensusReversalPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionSourceConsensusReversalPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventResolutionSourceConsensusReversalPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceConsensusReversalRow:
    event_digest: str
    previous_consensus_digest: str
    current_consensus_digest: str
    consensus_reversed: bool
    current_support_count: Decimal
    independent_source_family_count: Decimal
    support_score: Decimal
    family_score: Decimal
    freshness_score: Decimal
    contradiction_pressure: Decimal
    contradiction_score: Decimal
    confirmation_score: Decimal
    confidence_score: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    seconds_since_reversal: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceConsensusReversalRow:
            raise TypeError(
                "ResearchEventResolutionSourceConsensusReversalRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionSourceConsensusReversalRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionSourceConsensusReversalRow",
            )
        for field_name in (
            "event_digest",
            "previous_consensus_digest",
            "current_consensus_digest",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        if type(self.consensus_reversed) is not bool:
            raise ValueError("consensus_reversed must be a bool")
        for field_name in (
            "current_support_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "support_score",
            "family_score",
            "freshness_score",
            "contradiction_pressure",
            "contradiction_score",
            "confirmation_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_source_age_seconds",
            "oldest_source_age_seconds",
            "seconds_since_reversal",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_source_age_seconds < self.newest_source_age_seconds:
            raise ValueError(
                "oldest_source_age_seconds must be greater than or equal to "
                "newest_source_age_seconds",
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.consensus_reversed != (
            self.previous_consensus_digest != self.current_consensus_digest
        ):
            raise ValueError("consensus_reversed must match consensus digests")
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceConsensusReversalReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    stable_count: Decimal
    reversal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_score: Decimal
    average_support_score: Decimal
    average_family_score: Decimal
    average_freshness_score: Decimal
    average_contradiction_score: Decimal
    average_confirmation_score: Decimal
    freshness_pressure_count: Decimal
    contradiction_pressure_count: Decimal
    confirmation_pressure_count: Decimal
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchEventResolutionSourceConsensusReversalPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceConsensusReversalReport:
            raise TypeError(
                "ResearchEventResolutionSourceConsensusReversalReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionSourceConsensusReversalReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventResolutionSourceConsensusReversalReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "stable_count",
            "reversal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "freshness_pressure_count",
            "contradiction_pressure_count",
            "confirmation_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_score",
            "average_support_score",
            "average_family_score",
            "average_freshness_score",
            "average_contradiction_score",
            "average_confirmation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_payload(_public_payload(self, include_digest=False))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match public payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_event_resolution_source_consensus_reversal_public_payload(self)


def build_research_event_resolution_source_consensus_reversal_report(
    inputs: Sequence[ResearchEventResolutionSourceConsensusReversalInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionSourceConsensusReversalConfig | None = None,
    public_payload: Sequence[
        ResearchEventResolutionSourceConsensusReversalPublicPayloadItem
    ] = (),
) -> ResearchEventResolutionSourceConsensusReversalReport:
    """Build a deterministic report-only source consensus reversal snapshot."""

    if config is None:
        config = ResearchEventResolutionSourceConsensusReversalConfig()
    if type(config) is not ResearchEventResolutionSourceConsensusReversalConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionSourceConsensusReversalConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "stable_count": _stable_count(rows),
        "reversal_count": _reversal_count(rows),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_confidence_score": _average(tuple(row.confidence_score for row in rows)),
        "average_support_score": _average(tuple(row.support_score for row in rows)),
        "average_family_score": _average(tuple(row.family_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_contradiction_score": _average(
            tuple(row.contradiction_score for row in rows),
        ),
        "average_confirmation_score": _average(
            tuple(row.confirmation_score for row in rows),
        ),
        "freshness_pressure_count": _reason_prefix_count(
            rows,
            "consensus_reversal_freshness_",
        ),
        "contradiction_pressure_count": _reason_prefix_count(
            rows,
            "consensus_reversal_contradiction_",
        ),
        "confirmation_pressure_count": _reason_prefix_count(
            rows,
            "consensus_reversal_confirmation_",
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionSourceConsensusReversalReport(**values)


def research_event_resolution_source_consensus_reversal_public_payload(
    report: ResearchEventResolutionSourceConsensusReversalReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventResolutionSourceConsensusReversalReport:
        raise ValueError(
            "report must be a ResearchEventResolutionSourceConsensusReversalReport",
        )
    _rebuild_report_for_payload(report)
    return _public_payload(report, include_digest=True)


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchEventResolutionSourceConsensusReversalInput,
    *,
    config: ResearchEventResolutionSourceConsensusReversalConfig,
) -> ResearchEventResolutionSourceConsensusReversalRow:
    consensus_reversed = item.previous_consensus_digest != item.current_consensus_digest
    support_score = _clamp_ratio(
        item.current_support_count / config.pass_current_support_count,
    )
    family_score = _clamp_ratio(
        item.independent_source_family_count
        / config.pass_independent_source_family_count,
    )
    freshness_score = _freshness_score(item, config)
    contradiction_score = _contradiction_score(item.contradiction_pressure, config)
    confirmation_score = (
        _confirmation_score(item.seconds_since_reversal, config)
        if consensus_reversed
        else _ONE
    )
    confidence_score = _confidence_score(
        support_score=support_score,
        family_score=family_score,
        freshness_score=freshness_score,
        contradiction_score=contradiction_score,
        confirmation_score=confirmation_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        consensus_reversed=consensus_reversed,
        config=config,
    )
    return ResearchEventResolutionSourceConsensusReversalRow(
        event_digest=item.event_digest,
        previous_consensus_digest=item.previous_consensus_digest,
        current_consensus_digest=item.current_consensus_digest,
        consensus_reversed=consensus_reversed,
        current_support_count=item.current_support_count,
        independent_source_family_count=item.independent_source_family_count,
        support_score=support_score,
        family_score=family_score,
        freshness_score=freshness_score,
        contradiction_pressure=item.contradiction_pressure,
        contradiction_score=contradiction_score,
        confirmation_score=confirmation_score,
        confidence_score=confidence_score,
        newest_source_age_seconds=item.newest_source_age_seconds,
        oldest_source_age_seconds=item.oldest_source_age_seconds,
        seconds_since_reversal=item.seconds_since_reversal,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventResolutionSourceConsensusReversalInput,
    *,
    consensus_reversed: bool,
    config: ResearchEventResolutionSourceConsensusReversalConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.current_support_count < config.watch_current_support_count:
        reason_codes.append("consensus_reversal_support_block")
    elif item.current_support_count < config.pass_current_support_count:
        reason_codes.append("consensus_reversal_support_watch")
    if item.independent_source_family_count < config.watch_independent_source_family_count:
        reason_codes.append("consensus_reversal_family_block")
    elif item.independent_source_family_count < config.pass_independent_source_family_count:
        reason_codes.append("consensus_reversal_family_watch")
    if item.newest_source_age_seconds > config.stale_source_block_seconds:
        reason_codes.append("consensus_reversal_freshness_block")
    elif item.oldest_source_age_seconds > config.stale_source_watch_seconds:
        reason_codes.append("consensus_reversal_freshness_watch")
    if item.contradiction_pressure >= config.contradiction_block_pressure:
        reason_codes.append("consensus_reversal_contradiction_block")
    elif item.contradiction_pressure >= config.contradiction_watch_pressure:
        reason_codes.append("consensus_reversal_contradiction_watch")
    if (
        consensus_reversed
        and item.seconds_since_reversal < config.confirmation_watch_seconds
    ):
        reason_codes.append("consensus_reversal_confirmation_watch")
    if not reason_codes:
        if consensus_reversed:
            reason_codes.append("source_consensus_reversal_pass")
        else:
            reason_codes.append("source_consensus_stable_pass")
    return _normalize_reason_codes(reason_codes)


def _public_string_parts(value: str) -> tuple[str, ...]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", spaced).lower().strip()
    return tuple(part for part in normalized.split(" ") if part)


def _freshness_score(
    item: ResearchEventResolutionSourceConsensusReversalInput,
    config: ResearchEventResolutionSourceConsensusReversalConfig,
) -> Decimal:
    if item.newest_source_age_seconds > config.stale_source_block_seconds:
        return _ZERO
    if item.oldest_source_age_seconds > config.stale_source_watch_seconds:
        return Decimal("0.500000")
    return _ONE


def _contradiction_score(
    contradiction_pressure: Decimal,
    config: ResearchEventResolutionSourceConsensusReversalConfig,
) -> Decimal:
    if config.contradiction_block_pressure == _ZERO:
        return _ZERO if contradiction_pressure > _ZERO else _ONE
    return _clamp_ratio(_ONE - contradiction_pressure / config.contradiction_block_pressure)


def _confirmation_score(
    seconds_since_reversal: Decimal,
    config: ResearchEventResolutionSourceConsensusReversalConfig,
) -> Decimal:
    return _clamp_ratio(seconds_since_reversal / config.confirmation_watch_seconds)


def _confidence_score(
    *,
    support_score: Decimal,
    family_score: Decimal,
    freshness_score: Decimal,
    contradiction_score: Decimal,
    confirmation_score: Decimal,
    config: ResearchEventResolutionSourceConsensusReversalConfig,
) -> Decimal:
    return _clamp_ratio(
        support_score * config.support_weight
        + family_score * config.family_weight
        + freshness_score * config.freshness_weight
        + contradiction_score * config.contradiction_weight
        + confirmation_score * config.confirmation_weight,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchEventResolutionSourceConsensusReversalInput],
) -> tuple[ResearchEventResolutionSourceConsensusReversalInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchEventResolutionSourceConsensusReversalInput] = []
    seen: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchEventResolutionSourceConsensusReversalInput:
            raise ValueError(
                "inputs must contain "
                "ResearchEventResolutionSourceConsensusReversalInput",
            )
        _require_hard_flags("input", item)
        if item.event_digest in seen:
            raise ValueError("event_digest must be unique")
        seen.add(item.event_digest)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.event_digest))


def _normalize_rows(
    rows: Sequence[ResearchEventResolutionSourceConsensusReversalRow],
) -> tuple[ResearchEventResolutionSourceConsensusReversalRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionSourceConsensusReversalRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionSourceConsensusReversalRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionSourceConsensusReversalRow",
            )
        _require_hard_flags("row", row)
        if row.event_digest in seen:
            raise ValueError("row event_digest must be unique")
        seen.add(row.event_digest)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must use canonical sequence")
    return sorted_rows


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchEventResolutionSourceConsensusReversalPublicPayloadItem
    ],
) -> tuple[ResearchEventResolutionSourceConsensusReversalPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventResolutionSourceConsensusReversalPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchEventResolutionSourceConsensusReversalPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventResolutionSourceConsensusReversalPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_report_consistency(
    report: ResearchEventResolutionSourceConsensusReversalReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    if report.stable_count != _stable_count(rows):
        raise ValueError("stable_count does not match rows")
    if report.reversal_count != _reversal_count(rows):
        raise ValueError("reversal_count does not match rows")
    for status in _STATUSES:
        if getattr(report, f"{status}_count") != _status_count(rows, status):
            raise ValueError(f"{status}_count does not match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    expected_averages = {
        "average_confidence_score": _average(tuple(row.confidence_score for row in rows)),
        "average_support_score": _average(tuple(row.support_score for row in rows)),
        "average_family_score": _average(tuple(row.family_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_contradiction_score": _average(
            tuple(row.contradiction_score for row in rows),
        ),
        "average_confirmation_score": _average(
            tuple(row.confirmation_score for row in rows),
        ),
    }
    for field_name, expected in expected_averages.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} does not match rows")
    if report.freshness_pressure_count != _reason_prefix_count(
        rows,
        "consensus_reversal_freshness_",
    ):
        raise ValueError("freshness_pressure_count does not match rows")
    if report.contradiction_pressure_count != _reason_prefix_count(
        rows,
        "consensus_reversal_contradiction_",
    ):
        raise ValueError("contradiction_pressure_count does not match rows")
    if report.confirmation_pressure_count != _reason_prefix_count(
        rows,
        "consensus_reversal_confirmation_",
    ):
        raise ValueError("confirmation_pressure_count does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _row_status(reason_codes: Sequence[str]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if tuple(reason_codes) in (
        ("source_consensus_reversal_pass",),
        ("source_consensus_stable_pass",),
    ):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_source_consensus_reversal_set",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _status_count(
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _stable_count(
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if not row.consensus_reversed))


def _reversal_count(
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.consensus_reversed))


def _reason_prefix_count(
    rows: tuple[ResearchEventResolutionSourceConsensusReversalRow, ...],
    prefix: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code.startswith(prefix) for code in row.reason_codes)),
    )


def _row_sort_key(
    row: ResearchEventResolutionSourceConsensusReversalRow,
) -> tuple[Decimal, str]:
    return (_STATUS_SORT_WEIGHT[row.status], row.event_digest)


def _rebuild_report_for_payload(
    report: ResearchEventResolutionSourceConsensusReversalReport,
) -> None:
    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    try:
        ResearchEventResolutionSourceConsensusReversalReport(**kwargs)
    except Exception as exc:
        raise ValueError(
            "ResearchEventResolutionSourceConsensusReversalReport failed payload "
            "revalidation",
        ) from exc


def _public_payload(
    report: ResearchEventResolutionSourceConsensusReversalReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    if not include_digest:
        payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(
        "ResearchEventResolutionSourceConsensusReversalReport.payload",
        payload,
        allow_json_containers=True,
    )
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    ready = _json_ready(payload)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        ready,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        ready,
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
        _require_six_decimal_decimal("Decimal payload value", value)
        return format(value, "f")
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
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} numeric values must be Decimal")
    raise ValueError(f"{current_path} contains unsupported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    parts = _public_string_parts(key)
    compact = "_".join(parts)
    if any(part in _UNSAFE_PUBLIC_KEY_TOKENS for part in parts):
        raise ValueError(f"unsafe public key in {path}: {key}")
    if any(
        phrase in compact
        for phrase in (
            "candidate_id",
            "market_id",
            "market_slug",
            "source_url",
            "source_text",
            _join_parts("ta", "ble", "_name"),
        )
    ):
        raise ValueError(f"unsafe public key in {path}: {key}")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    parts = _public_string_parts(value)
    phrases = (" ".join(parts), "_".join(parts), lowered.replace("_", " "))
    token_patterns = frozenset(
        (
            _join_parts("au", "th"),
            "candidate",
            "credential",
            "dsn",
            "execution",
            _join_parts("li", "ve"),
            _join_parts("net", "work"),
            _join_parts("ord", "er"),
            "password",
            "postgres",
            _join_parts("que", "stion"),
            _join_parts("recomm", "end"),
            _join_parts("siz", "ing"),
            _join_parts("ta", "ble"),
            _join_parts("to", "ken"),
            _join_parts("tra", "de"),
            _join_parts("wal", "let"),
        ),
    )
    phrase_patterns = (
        "market id",
        "market slug",
        "source text",
        "source url",
    )
    if "://" in lowered:
        raise ValueError(f"unsafe public value in {path}")
    if any(part in token_patterns for part in parts):
        raise ValueError(f"unsafe public value in {path}")
    if any(pattern in phrase for phrase in phrases for pattern in phrase_patterns):
        raise ValueError(f"unsafe public value in {path}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_key(value, field_name)
    _reject_unsafe_public_string(field_name, value)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be stripped single-line text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
        seen.add(reason_code)
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in seen
    )


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = _quantize_decimal(value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_six_decimal_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must be quantized to six decimal places")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize_decimal(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if value >= _ONE:
        return _ONE
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_CONSENSUS_REVERSAL_CONFIG_VERSION",
    "ResearchEventResolutionSourceConsensusReversalConfig",
    "ResearchEventResolutionSourceConsensusReversalInput",
    "ResearchEventResolutionSourceConsensusReversalPublicPayloadItem",
    "ResearchEventResolutionSourceConsensusReversalReport",
    "ResearchEventResolutionSourceConsensusReversalRow",
    "build_research_event_resolution_source_consensus_reversal_report",
    "research_event_resolution_source_consensus_reversal_public_payload",
)
