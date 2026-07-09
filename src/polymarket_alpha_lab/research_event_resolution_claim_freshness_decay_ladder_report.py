"""Report-only event resolution claim freshness decay ladder reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_CONFIG_VERSION = (
    "research-event-resolution-claim-freshness-decay-ladder-report-v1"
)
RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_STATUSES = (
    "pass",
    "watch",
    "block",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_STATUSES)
_BLOCK_REASON_CODES = frozenset(
    (
        "claim_freshness_block",
        "confirmation_freshness_block",
        "corroborating_claim_quorum_block",
        "independent_signal_quorum_block",
        "contradiction_pressure_block",
        "update_latency_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "claim_freshness_block",
    "claim_freshness_watch",
    "confirmation_freshness_block",
    "confirmation_freshness_watch",
    "corroborating_claim_quorum_block",
    "corroborating_claim_quorum_watch",
    "independent_signal_quorum_block",
    "independent_signal_quorum_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "update_latency_block",
    "update_latency_watch",
    "freshness_decay_score_watch",
    "claim_freshness_decay_ladder_pass",
    "empty_claim_freshness_decay_ladder_set",
)
_STATUS_SORT_WEIGHT = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "block": Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_BAD_PUBLIC_KEY_PARTS = frozenset(
    (
        _join_parts("au", "th"),
        "buy",
        "candidate",
        _join_parts("data", "base"),
        "db",
        "dsn",
        _join_parts("li", "ve"),
        "market",
        _join_parts("net", "work"),
        _join_parts("ord", "er"),
        "question",
        _join_parts("recomm", "endation"),
        "sell",
        _join_parts("siz", "ing"),
        "slug",
        _join_parts("sou", "rce"),
        _join_parts("ta", "ble"),
        "text",
        _join_parts("to", "ken"),
        _join_parts("tra", "de"),
        "url",
        _join_parts("wal", "let"),
    ),
)
_BAD_PUBLIC_PHRASES = (
    "://",
    _join_parts("au", "th"),
    "buy ",
    "candidate",
    "credential",
    _join_parts("data", "base"),
    "dsn",
    _join_parts("li", "ve ", "trading"),
    "market",
    _join_parts("ord", "er"),
    "password",
    "postgres",
    "private",
    "question",
    _join_parts("recomm", "endation"),
    "secret",
    "sell ",
    _join_parts("siz", "ing"),
    "slug",
    _join_parts("sou", "rce ", "text"),
    _join_parts("sou", "rce_text"),
    _join_parts("sou", "rce ", "url"),
    _join_parts("sou", "rce_url"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("tra", "de"),
    _join_parts("wal", "let"),
)


@dataclass(frozen=True)
class ResearchEventResolutionClaimFreshnessDecayLadderConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_CONFIG_VERSION
    )
    watch_claim_age_seconds: Decimal = Decimal("21600.000000")
    block_claim_age_seconds: Decimal = Decimal("86400.000000")
    watch_confirmation_age_seconds: Decimal = Decimal("43200.000000")
    block_confirmation_age_seconds: Decimal = Decimal("172800.000000")
    pass_corrob_claim_count: Decimal = Decimal("3.000000")
    watch_corrob_claim_count: Decimal = Decimal("2.000000")
    pass_independent_signal_count: Decimal = Decimal("2.000000")
    watch_independent_signal_count: Decimal = Decimal("1.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.250000")
    contradiction_block_pressure: Decimal = Decimal("0.500000")
    update_latency_watch_seconds: Decimal = Decimal("7200.000000")
    update_latency_block_seconds: Decimal = Decimal("21600.000000")
    min_freshness_decay_score: Decimal = Decimal("0.750000")
    freshness_weight: Decimal = Decimal("0.350000")
    confirmation_weight: Decimal = Decimal("0.250000")
    quorum_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.150000")
    latency_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClaimFreshnessDecayLadderConfig:
            raise TypeError(
                "ResearchEventResolutionClaimFreshnessDecayLadderConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionClaimFreshnessDecayLadderConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_claim_age_seconds",
            "block_claim_age_seconds",
            "watch_confirmation_age_seconds",
            "block_confirmation_age_seconds",
            "update_latency_watch_seconds",
            "update_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_claim_age_seconds > self.block_claim_age_seconds:
            raise ValueError(
                "watch_claim_age_seconds must not exceed block_claim_age_seconds",
            )
        if self.watch_confirmation_age_seconds > self.block_confirmation_age_seconds:
            raise ValueError(
                "watch_confirmation_age_seconds must not exceed "
                "block_confirmation_age_seconds",
            )
        if self.update_latency_watch_seconds > self.update_latency_block_seconds:
            raise ValueError(
                "update_latency_watch_seconds must not exceed "
                "update_latency_block_seconds",
            )
        for field_name in (
            "pass_corrob_claim_count",
            "watch_corrob_claim_count",
            "pass_independent_signal_count",
            "watch_independent_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_corrob_claim_count > self.pass_corrob_claim_count:
            raise ValueError(
                "watch_corrob_claim_count must not exceed pass_corrob_claim_count",
            )
        if (
            self.watch_independent_signal_count
            > self.pass_independent_signal_count
        ):
            raise ValueError(
                "watch_independent_signal_count must not exceed "
                "pass_independent_signal_count",
            )
        for field_name in (
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "min_freshness_decay_score",
            "freshness_weight",
            "confirmation_weight",
            "quorum_weight",
            "contradiction_weight",
            "latency_weight",
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
            self.freshness_weight
            + self.confirmation_weight
            + self.quorum_weight
            + self.contradiction_weight
            + self.latency_weight
            != _ONE
        ):
            raise ValueError("freshness decay weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimFreshnessDecayLadderInput:
    claim_digest: str
    resolution_digest: str
    evidence_digest: str
    claim_age_seconds: Decimal
    confirmation_age_seconds: Decimal
    corroborating_claim_count: Decimal
    independent_signal_count: Decimal
    contradiction_pressure: Decimal
    resolution_update_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClaimFreshnessDecayLadderInput:
            raise TypeError(
                "ResearchEventResolutionClaimFreshnessDecayLadderInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionClaimFreshnessDecayLadderInput,
            "input",
        )
        for field_name in ("claim_digest", "resolution_digest", "evidence_digest"):
            _require_sha256_digest(field_name, getattr(self, field_name))
        for field_name in ("corroborating_claim_count", "independent_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_age_seconds",
            "confirmation_age_seconds",
            "resolution_update_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal("contradiction_pressure", self.contradiction_pressure),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem,
            "public payload item",
        )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimFreshnessDecayLadderRow:
    claim_digest: str
    resolution_digest: str
    evidence_digest: str
    claim_age_seconds: Decimal
    confirmation_age_seconds: Decimal
    corroborating_claim_count: Decimal
    independent_signal_count: Decimal
    claim_freshness_score: Decimal
    confirmation_score: Decimal
    quorum_score: Decimal
    contradiction_pressure: Decimal
    contradiction_score: Decimal
    latency_score: Decimal
    freshness_decay_score: Decimal
    resolution_update_latency_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClaimFreshnessDecayLadderRow:
            raise TypeError(
                "ResearchEventResolutionClaimFreshnessDecayLadderRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionClaimFreshnessDecayLadderRow, "row")
        for field_name in ("claim_digest", "resolution_digest", "evidence_digest"):
            _require_sha256_digest(field_name, getattr(self, field_name))
        for field_name in ("corroborating_claim_count", "independent_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_age_seconds",
            "confirmation_age_seconds",
            "resolution_update_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_freshness_score",
            "confirmation_score",
            "quorum_score",
            "contradiction_pressure",
            "contradiction_score",
            "latency_score",
            "freshness_decay_score",
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
            _normalize_reason_codes(self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimFreshnessDecayLadderReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_freshness_decay_score: Decimal
    average_claim_freshness_score: Decimal
    average_confirmation_score: Decimal
    average_quorum_score: Decimal
    average_contradiction_pressure: Decimal
    average_latency_score: Decimal
    stale_claim_count: Decimal
    stale_confirmation_count: Decimal
    insufficient_quorum_count: Decimal
    contradiction_pressure_count: Decimal
    update_latency_count: Decimal
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionClaimFreshnessDecayLadderReport:
            raise TypeError(
                "ResearchEventResolutionClaimFreshnessDecayLadderReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionClaimFreshnessDecayLadderReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_claim_count",
            "stale_confirmation_count",
            "insufficient_quorum_count",
            "contradiction_pressure_count",
            "update_latency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_freshness_decay_score",
            "average_claim_freshness_score",
            "average_confirmation_score",
            "average_quorum_score",
            "average_contradiction_pressure",
            "average_latency_score",
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
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_event_resolution_claim_freshness_decay_ladder_public_payload(self)


def build_research_event_resolution_claim_freshness_decay_ladder_report(
    inputs: Sequence[ResearchEventResolutionClaimFreshnessDecayLadderInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig | None = None,
    public_payload: Sequence[
        ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem
    ] = (),
) -> ResearchEventResolutionClaimFreshnessDecayLadderReport:
    """Build a deterministic report-only claim freshness decay ladder snapshot."""

    if config is None:
        config = ResearchEventResolutionClaimFreshnessDecayLadderConfig()
    if type(config) is not ResearchEventResolutionClaimFreshnessDecayLadderConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionClaimFreshnessDecayLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_freshness_decay_score": _average(
            tuple(row.freshness_decay_score for row in rows),
        ),
        "average_claim_freshness_score": _average(
            tuple(row.claim_freshness_score for row in rows),
        ),
        "average_confirmation_score": _average(
            tuple(row.confirmation_score for row in rows),
        ),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "average_contradiction_pressure": _average(
            tuple(row.contradiction_pressure for row in rows),
        ),
        "average_latency_score": _average(tuple(row.latency_score for row in rows)),
        "stale_claim_count": _reason_code_count(
            rows,
            ("claim_freshness_block", "claim_freshness_watch"),
        ),
        "stale_confirmation_count": _reason_prefix_count(rows, "confirmation_freshness_"),
        "insufficient_quorum_count": _quorum_penalty_count(rows),
        "contradiction_pressure_count": _reason_prefix_count(
            rows,
            "contradiction_pressure_",
        ),
        "update_latency_count": _reason_prefix_count(rows, "update_latency_"),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionClaimFreshnessDecayLadderReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_claim_freshness_decay_ladder_public_payload(
    report: ResearchEventResolutionClaimFreshnessDecayLadderReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventResolutionClaimFreshnessDecayLadderReport:
        raise ValueError(
            "report must be a ResearchEventResolutionClaimFreshnessDecayLadderReport",
        )
    _rebuild_report_for_payload(report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(
        "ResearchEventResolutionClaimFreshnessDecayLadderReport.payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_event_resolution_claim_freshness_decay_ladder_report_digest(
    report: ResearchEventResolutionClaimFreshnessDecayLadderReport,
) -> str:
    if type(report) is not ResearchEventResolutionClaimFreshnessDecayLadderReport:
        raise ValueError(
            "report must be a ResearchEventResolutionClaimFreshnessDecayLadderReport",
        )
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_event_resolution_claim_freshness_decay_ladder_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    payload_copy = dict(payload)
    _reject_unsafe_public_payload(
        "research_event_resolution_claim_freshness_decay_ladder_public_payload",
        payload_copy,
        allow_json_containers=True,
    )
    digest = payload_copy.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload_copy)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = _public_payload_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    _require_hard_flags("payload", _DictFlags(payload_copy))
    return payload_copy


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
    item: ResearchEventResolutionClaimFreshnessDecayLadderInput,
    *,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig,
) -> ResearchEventResolutionClaimFreshnessDecayLadderRow:
    claim_freshness_score = _decay_score(
        item.claim_age_seconds,
        watch_seconds=config.watch_claim_age_seconds,
        block_seconds=config.block_claim_age_seconds,
    )
    confirmation_score = _decay_score(
        item.confirmation_age_seconds,
        watch_seconds=config.watch_confirmation_age_seconds,
        block_seconds=config.block_confirmation_age_seconds,
    )
    quorum_score = _average(
        (
            _clamp_ratio(item.corroborating_claim_count / config.pass_corrob_claim_count),
            _clamp_ratio(
                item.independent_signal_count / config.pass_independent_signal_count,
            ),
        ),
    )
    contradiction_score = _contradiction_score(item.contradiction_pressure, config)
    latency_score = _latency_score(item.resolution_update_latency_seconds, config)
    freshness_decay_score = _freshness_decay_score(
        claim_freshness_score=claim_freshness_score,
        confirmation_score=confirmation_score,
        quorum_score=quorum_score,
        contradiction_score=contradiction_score,
        latency_score=latency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        freshness_decay_score=freshness_decay_score,
        config=config,
    )
    return ResearchEventResolutionClaimFreshnessDecayLadderRow(
        claim_digest=item.claim_digest,
        resolution_digest=item.resolution_digest,
        evidence_digest=item.evidence_digest,
        claim_age_seconds=item.claim_age_seconds,
        confirmation_age_seconds=item.confirmation_age_seconds,
        corroborating_claim_count=item.corroborating_claim_count,
        independent_signal_count=item.independent_signal_count,
        claim_freshness_score=claim_freshness_score,
        confirmation_score=confirmation_score,
        quorum_score=quorum_score,
        contradiction_pressure=item.contradiction_pressure,
        contradiction_score=contradiction_score,
        latency_score=latency_score,
        freshness_decay_score=freshness_decay_score,
        resolution_update_latency_seconds=item.resolution_update_latency_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventResolutionClaimFreshnessDecayLadderInput,
    *,
    freshness_decay_score: Decimal,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.claim_age_seconds > config.block_claim_age_seconds:
        reason_codes.append("claim_freshness_block")
    elif item.claim_age_seconds >= config.watch_claim_age_seconds:
        reason_codes.append("claim_freshness_watch")
    if item.confirmation_age_seconds > config.block_confirmation_age_seconds:
        reason_codes.append("confirmation_freshness_block")
    elif item.confirmation_age_seconds >= config.watch_confirmation_age_seconds:
        reason_codes.append("confirmation_freshness_watch")
    if item.corroborating_claim_count < config.watch_corrob_claim_count:
        reason_codes.append("corroborating_claim_quorum_block")
    elif item.corroborating_claim_count < config.pass_corrob_claim_count:
        reason_codes.append("corroborating_claim_quorum_watch")
    if item.independent_signal_count < config.watch_independent_signal_count:
        reason_codes.append("independent_signal_quorum_block")
    elif item.independent_signal_count < config.pass_independent_signal_count:
        reason_codes.append("independent_signal_quorum_watch")
    if item.contradiction_pressure >= config.contradiction_block_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif item.contradiction_pressure >= config.contradiction_watch_pressure:
        reason_codes.append("contradiction_pressure_watch")
    if item.resolution_update_latency_seconds >= config.update_latency_block_seconds:
        reason_codes.append("update_latency_block")
    elif item.resolution_update_latency_seconds >= config.update_latency_watch_seconds:
        reason_codes.append("update_latency_watch")
    if (
        not _has_block_reason(reason_codes)
        and freshness_decay_score < config.min_freshness_decay_score
    ):
        reason_codes.append("freshness_decay_score_watch")
    if not reason_codes:
        reason_codes.append("claim_freshness_decay_ladder_pass")
    return _normalize_reason_codes(reason_codes)


def _decay_score(
    age_seconds: Decimal,
    *,
    watch_seconds: Decimal,
    block_seconds: Decimal,
) -> Decimal:
    if age_seconds <= watch_seconds:
        return _ONE
    if age_seconds >= block_seconds:
        return _ZERO
    window = block_seconds - watch_seconds
    if window == _ZERO:
        return _ZERO
    return _clamp_ratio((block_seconds - age_seconds) / window)


def _contradiction_score(
    contradiction_pressure: Decimal,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig,
) -> Decimal:
    if config.contradiction_block_pressure == _ZERO:
        return _ZERO if contradiction_pressure > _ZERO else _ONE
    return _clamp_ratio(_ONE - contradiction_pressure / config.contradiction_block_pressure)


def _latency_score(
    resolution_update_latency_seconds: Decimal,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig,
) -> Decimal:
    if resolution_update_latency_seconds <= config.update_latency_watch_seconds:
        return _ONE
    if resolution_update_latency_seconds >= config.update_latency_block_seconds:
        return _ZERO
    window = config.update_latency_block_seconds - config.update_latency_watch_seconds
    if window == _ZERO:
        return _ZERO
    return _clamp_ratio(
        (config.update_latency_block_seconds - resolution_update_latency_seconds)
        / window,
    )


def _freshness_decay_score(
    *,
    claim_freshness_score: Decimal,
    confirmation_score: Decimal,
    quorum_score: Decimal,
    contradiction_score: Decimal,
    latency_score: Decimal,
    config: ResearchEventResolutionClaimFreshnessDecayLadderConfig,
) -> Decimal:
    return _clamp_ratio(
        claim_freshness_score * config.freshness_weight
        + confirmation_score * config.confirmation_weight
        + quorum_score * config.quorum_weight
        + contradiction_score * config.contradiction_weight
        + latency_score * config.latency_weight,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchEventResolutionClaimFreshnessDecayLadderInput],
) -> tuple[ResearchEventResolutionClaimFreshnessDecayLadderInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchEventResolutionClaimFreshnessDecayLadderInput] = []
    seen: set[tuple[str, str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchEventResolutionClaimFreshnessDecayLadderInput:
            raise ValueError(
                "inputs must contain "
                "ResearchEventResolutionClaimFreshnessDecayLadderInput",
            )
        _require_hard_flags("input", item)
        key = (item.claim_digest, item.resolution_digest, item.evidence_digest)
        if key in seen:
            raise ValueError("input digests must be unique")
        seen.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.claim_digest,
                item.resolution_digest,
                item.evidence_digest,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventResolutionClaimFreshnessDecayLadderRow],
) -> tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionClaimFreshnessDecayLadderRow] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionClaimFreshnessDecayLadderRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionClaimFreshnessDecayLadderRow",
            )
        _require_hard_flags("row", row)
        key = (row.claim_digest, row.resolution_digest, row.evidence_digest)
        if key in seen:
            raise ValueError("row digests must be unique")
        seen.add(key)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must use canonical sequence")
    return sorted_rows


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem
    ],
) -> tuple[ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_report_consistency(
    report: ResearchEventResolutionClaimFreshnessDecayLadderReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    for status in _STATUSES:
        if getattr(report, f"{status}_count") != _status_count(rows, status):
            raise ValueError(f"{status}_count does not match rows")
    if report.stale_claim_count != _reason_code_count(
        rows,
        ("claim_freshness_block", "claim_freshness_watch"),
    ):
        raise ValueError("stale_claim_count does not match rows")
    if report.stale_confirmation_count != _reason_prefix_count(
        rows,
        "confirmation_freshness_",
    ):
        raise ValueError("stale_confirmation_count does not match rows")
    if report.insufficient_quorum_count != _quorum_penalty_count(rows):
        raise ValueError("insufficient_quorum_count does not match rows")
    if report.contradiction_pressure_count != _reason_prefix_count(
        rows,
        "contradiction_pressure_",
    ):
        raise ValueError("contradiction_pressure_count does not match rows")
    if report.update_latency_count != _reason_prefix_count(rows, "update_latency_"):
        raise ValueError("update_latency_count does not match rows")
    expected_averages = {
        "average_freshness_decay_score": _average(
            tuple(row.freshness_decay_score for row in rows),
        ),
        "average_claim_freshness_score": _average(
            tuple(row.claim_freshness_score for row in rows),
        ),
        "average_confirmation_score": _average(
            tuple(row.confirmation_score for row in rows),
        ),
        "average_quorum_score": _average(tuple(row.quorum_score for row in rows)),
        "average_contradiction_pressure": _average(
            tuple(row.contradiction_pressure for row in rows),
        ),
        "average_latency_score": _average(tuple(row.latency_score for row in rows)),
    }
    for field_name, expected in expected_averages.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _row_status(reason_codes: Sequence[str]) -> str:
    if _has_block_reason(reason_codes):
        return "block"
    if tuple(reason_codes) == ("claim_freshness_decay_ladder_pass",):
        return "pass"
    return "watch"


def _has_block_reason(reason_codes: Sequence[str]) -> bool:
    return any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes)


def _report_status(
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_claim_freshness_decay_ladder_set",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _status_count(
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_prefix_count(
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...],
    prefix: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code.startswith(prefix) for code in row.reason_codes)),
    )


def _reason_code_count(
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code in reason_codes for code in row.reason_codes)),
    )


def _quorum_penalty_count(
    rows: tuple[ResearchEventResolutionClaimFreshnessDecayLadderRow, ...],
) -> Decimal:
    quorum_penalty_reasons = (
        "corroborating_claim_quorum_block",
        "corroborating_claim_quorum_watch",
        "independent_signal_quorum_block",
        "independent_signal_quorum_watch",
    )
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(code in quorum_penalty_reasons for code in row.reason_codes)
        ),
    )


def _row_sort_key(
    row: ResearchEventResolutionClaimFreshnessDecayLadderRow,
) -> tuple[Decimal, str, str, str]:
    return (
        _STATUS_SORT_WEIGHT[row.status],
        row.claim_digest,
        row.resolution_digest,
        row.evidence_digest,
    )


def _rebuild_report_for_payload(
    report: ResearchEventResolutionClaimFreshnessDecayLadderReport,
) -> None:
    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    try:
        ResearchEventResolutionClaimFreshnessDecayLadderReport(**kwargs)
    except Exception as exc:
        raise ValueError(
            "ResearchEventResolutionClaimFreshnessDecayLadderReport failed payload "
            "revalidation",
        ) from exc


def _report_values_without_digest(
    report: ResearchEventResolutionClaimFreshnessDecayLadderReport,
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


def _public_payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload(
        "public payload digest",
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
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    parts = tuple(part for part in re.split(r"[^a-z0-9]+", lowered) if part)
    if any(part in _BAD_PUBLIC_KEY_PARTS for part in parts):
        raise ValueError(f"{path}.{key} has unsafe public field")
    if any(
        term in lowered
        for term in (
            _join_parts("candidate", "_", "id"),
            _join_parts("market", "_", "id"),
            _join_parts("market", "_", "slug"),
            _join_parts("sou", "rce", "_url"),
            _join_parts("sou", "rce", "_text"),
            _join_parts("ta", "ble", "_name"),
        )
    ):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(phrase in lowered for phrase in _BAD_PUBLIC_PHRASES):
        raise ValueError(f"{path} has unsafe public value")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or len(value) > 512:
        raise ValueError(f"{field_name} must be public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a supported status")
    return value


def _normalize_reason_codes(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in value:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_six_decimal_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_six_decimal_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_six_decimal_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_six_decimal_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places")
    return quantized


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _quantize(max(_ZERO, min(_ONE, value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _signed_age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    return _quantize(
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND),
    )


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_CLAIM_FRESHNESS_DECAY_LADDER_STATUSES",
    "ResearchEventResolutionClaimFreshnessDecayLadderConfig",
    "ResearchEventResolutionClaimFreshnessDecayLadderInput",
    "ResearchEventResolutionClaimFreshnessDecayLadderPublicPayloadItem",
    "ResearchEventResolutionClaimFreshnessDecayLadderReport",
    "ResearchEventResolutionClaimFreshnessDecayLadderRow",
    "build_research_event_resolution_claim_freshness_decay_ladder_report",
    "research_event_resolution_claim_freshness_decay_ladder_public_payload",
    "research_event_resolution_claim_freshness_decay_ladder_report_digest",
    "validate_research_event_resolution_claim_freshness_decay_ladder_public_payload",
)
