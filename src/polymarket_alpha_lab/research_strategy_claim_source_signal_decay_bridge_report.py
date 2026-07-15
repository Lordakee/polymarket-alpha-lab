"""Read-only report for claim-source signal decay bridges."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, final


DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_SIGNAL_DECAY_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-strategy-claim-source-signal-decay-bridge-report-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "claim_source_signal_survives",
    "claim_source_signal_decayed",
    "claim_age_decay_watch",
    "source_age_decay_watch",
    "source_trust_watch",
    "corroboration_watch",
    "contradiction_watch",
    "contradiction_block",
)
REPORT_REASON_CODES = (
    "claim_source_signal_bridge_clear",
    "claim_source_signal_bridge_watch",
    "claim_source_signal_bridge_block",
    "claim_age_decay_watch",
    "source_age_decay_watch",
    "source_trust_watch",
    "corroboration_watch",
    "contradiction_watch",
    "contradiction_block",
)
REPORT_ROW_REASON_CODES = (
    "claim_age_decay_watch",
    "source_age_decay_watch",
    "source_trust_watch",
    "corroboration_watch",
    "contradiction_watch",
    "contradiction_block",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
REDACTED_DIGEST_LENGTH = 16

UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate",
    "condition",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "text",
    "d" + "sn",
    "table" + "_name",
    "table",
    "token",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "au" + "th",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "candidate",
    "condition",
    "market_id",
    "market-slug",
    "market_slug",
    "question",
    "source-url",
    "source_url",
    "source-text",
    "source_text",
    "raw-",
    "token",
    "secret",
    "private",
    "d" + "sn",
    "table" + "_name",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "au" + "th",
)
PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "pass_bridge_signal_floor",
        "watch_bridge_signal_floor",
        "max_claim_age_hours",
        "max_source_age_hours",
        "claim_age_decay_cap",
        "source_age_decay_cap",
        "source_trust_decay_cap",
        "corroboration_decay_cap",
        "contradiction_decay_cap",
        "source_trust_watch_floor",
        "corroboration_watch_floor",
        "contradiction_watch_score",
        "contradiction_block_score",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "surviving_bridge_count",
        "mean_decayed_bridge_signal_probability",
        "min_decayed_bridge_signal_probability",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "payload_sha256",
        "paper_only",
        "report_only",
        "readonly",
    },
)
PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    {
        "redacted_claim_ref",
        "redacted_source_ref",
        "claim_observed_at",
        "source_observed_at",
        "claim_age_hours",
        "source_age_hours",
        "claim_signal_probability",
        "source_alignment_score",
        "raw_bridge_signal_probability",
        "claim_age_decay_probability",
        "source_age_decay_probability",
        "source_trust_score",
        "source_trust_decay_probability",
        "corroboration_score",
        "corroboration_decay_probability",
        "contradiction_score",
        "contradiction_decay_probability",
        "decayed_bridge_signal_probability",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    },
)
CONFIG_DECIMAL_FIELDS = (
    "pass_bridge_signal_floor",
    "watch_bridge_signal_floor",
    "max_claim_age_hours",
    "max_source_age_hours",
    "claim_age_decay_cap",
    "source_age_decay_cap",
    "source_trust_decay_cap",
    "corroboration_decay_cap",
    "contradiction_decay_cap",
    "source_trust_watch_floor",
    "corroboration_watch_floor",
    "contradiction_watch_score",
    "contradiction_block_score",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_SIGNAL_DECAY_BRIDGE_REPORT_CONFIG_VERSION",
    "ResearchStrategyClaimSourceSignalDecayBridgeConfig",
    "ResearchStrategyClaimSourceSignalDecayBridgeObservation",
    "ResearchStrategyClaimSourceSignalDecayBridgeReport",
    "ResearchStrategyClaimSourceSignalDecayBridgeRow",
    "build_research_strategy_claim_source_signal_decay_bridge_report",
    "research_strategy_claim_source_signal_decay_bridge_report_json",
    "research_strategy_claim_source_signal_decay_bridge_report_payload",
    "validate_research_strategy_claim_source_signal_decay_bridge_report_payload",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceSignalDecayBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_SIGNAL_DECAY_BRIDGE_REPORT_CONFIG_VERSION
    )
    pass_bridge_signal_floor: Decimal = Decimal("0.070000")
    watch_bridge_signal_floor: Decimal = Decimal("0.030000")
    max_claim_age_hours: Decimal = Decimal("48.000000")
    max_source_age_hours: Decimal = Decimal("12.000000")
    claim_age_decay_cap: Decimal = Decimal("0.025000")
    source_age_decay_cap: Decimal = Decimal("0.025000")
    source_trust_decay_cap: Decimal = Decimal("0.020000")
    corroboration_decay_cap: Decimal = Decimal("0.020000")
    contradiction_decay_cap: Decimal = Decimal("0.050000")
    source_trust_watch_floor: Decimal = Decimal("0.600000")
    corroboration_watch_floor: Decimal = Decimal("0.500000")
    contradiction_watch_score: Decimal = Decimal("0.300000")
    contradiction_block_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategyClaimSourceSignalDecayBridgeConfig:
            raise TypeError(
                "ResearchStrategyClaimSourceSignalDecayBridgeConfig does not support subclassing",
            )
        super().__init_subclass__(**kwargs)

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyClaimSourceSignalDecayBridgeConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_SIGNAL_DECAY_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_bridge_signal_floor",
            "watch_bridge_signal_floor",
            "claim_age_decay_cap",
            "source_age_decay_cap",
            "source_trust_decay_cap",
            "corroboration_decay_cap",
            "contradiction_decay_cap",
            "source_trust_watch_floor",
            "corroboration_watch_floor",
            "contradiction_watch_score",
            "contradiction_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_claim_age_hours", "max_source_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) == ZERO_RATIO:
                raise ValueError(f"{field_name} must be positive")
        if self.watch_bridge_signal_floor > self.pass_bridge_signal_floor:
            raise ValueError("watch_bridge_signal_floor must not exceed pass_bridge_signal_floor")
        if self.contradiction_watch_score > self.contradiction_block_score:
            raise ValueError(
                "contradiction_watch_score must not exceed contradiction_block_score",
            )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceSignalDecayBridgeObservation:
    claim_ref: str
    source_ref: str
    claim_observed_at: datetime
    source_observed_at: datetime
    claim_signal_probability: Decimal
    source_alignment_score: Decimal
    source_trust_score: Decimal
    corroboration_score: Decimal
    contradiction_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategyClaimSourceSignalDecayBridgeObservation:
            raise TypeError(
                "ResearchStrategyClaimSourceSignalDecayBridgeObservation does not support subclassing",
            )
        super().__init_subclass__(**kwargs)

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyClaimSourceSignalDecayBridgeObservation,
            "observation",
        )
        _require_private_reference("claim_ref", self.claim_ref)
        _require_private_reference("source_ref", self.source_ref)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "claim_signal_probability",
            "source_alignment_score",
            "source_trust_score",
            "corroboration_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceSignalDecayBridgeRow:
    redacted_claim_ref: str
    redacted_source_ref: str
    claim_observed_at: datetime
    source_observed_at: datetime
    claim_age_hours: Decimal
    source_age_hours: Decimal
    claim_signal_probability: Decimal
    source_alignment_score: Decimal
    raw_bridge_signal_probability: Decimal
    claim_age_decay_probability: Decimal
    source_age_decay_probability: Decimal
    source_trust_score: Decimal
    source_trust_decay_probability: Decimal
    corroboration_score: Decimal
    corroboration_decay_probability: Decimal
    contradiction_score: Decimal
    contradiction_decay_probability: Decimal
    decayed_bridge_signal_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategyClaimSourceSignalDecayBridgeRow:
            raise TypeError(
                "ResearchStrategyClaimSourceSignalDecayBridgeRow does not support subclassing",
            )
        super().__init_subclass__(**kwargs)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimSourceSignalDecayBridgeRow, "row")
        _require_redacted_reference("redacted_claim_ref", self.redacted_claim_ref, "claim_ref")
        _require_redacted_reference("redacted_source_ref", self.redacted_source_ref, "source_ref")
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "claim_age_hours",
            "source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_signal_probability",
            "source_alignment_score",
            "claim_age_decay_probability",
            "source_age_decay_probability",
            "source_trust_score",
            "source_trust_decay_probability",
            "corroboration_score",
            "corroboration_decay_probability",
            "contradiction_score",
            "contradiction_decay_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "raw_bridge_signal_probability",
            "decayed_bridge_signal_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceSignalDecayBridgeReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    surviving_bridge_count: Decimal
    mean_decayed_bridge_signal_probability: Decimal
    min_decayed_bridge_signal_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyClaimSourceSignalDecayBridgeRow, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    pass_bridge_signal_floor: Decimal = Decimal("0.070000")
    watch_bridge_signal_floor: Decimal = Decimal("0.030000")
    max_claim_age_hours: Decimal = Decimal("48.000000")
    max_source_age_hours: Decimal = Decimal("12.000000")
    claim_age_decay_cap: Decimal = Decimal("0.025000")
    source_age_decay_cap: Decimal = Decimal("0.025000")
    source_trust_decay_cap: Decimal = Decimal("0.020000")
    corroboration_decay_cap: Decimal = Decimal("0.020000")
    contradiction_decay_cap: Decimal = Decimal("0.050000")
    source_trust_watch_floor: Decimal = Decimal("0.600000")
    corroboration_watch_floor: Decimal = Decimal("0.500000")
    contradiction_watch_score: Decimal = Decimal("0.300000")
    contradiction_block_score: Decimal = Decimal("0.700000")

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategyClaimSourceSignalDecayBridgeReport:
            raise TypeError(
                "ResearchStrategyClaimSourceSignalDecayBridgeReport does not support subclassing",
            )
        super().__init_subclass__(**kwargs)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimSourceSignalDecayBridgeReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_SIGNAL_DECAY_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        normalized_config = ResearchStrategyClaimSourceSignalDecayBridgeConfig(
            config_version=self.config_version,
            pass_bridge_signal_floor=self.pass_bridge_signal_floor,
            watch_bridge_signal_floor=self.watch_bridge_signal_floor,
            max_claim_age_hours=self.max_claim_age_hours,
            max_source_age_hours=self.max_source_age_hours,
            claim_age_decay_cap=self.claim_age_decay_cap,
            source_age_decay_cap=self.source_age_decay_cap,
            source_trust_decay_cap=self.source_trust_decay_cap,
            corroboration_decay_cap=self.corroboration_decay_cap,
            contradiction_decay_cap=self.contradiction_decay_cap,
            source_trust_watch_floor=self.source_trust_watch_floor,
            corroboration_watch_floor=self.corroboration_watch_floor,
            contradiction_watch_score=self.contradiction_watch_score,
            contradiction_block_score=self.contradiction_block_score,
            paper_only=self.paper_only,
            report_only=self.report_only,
            readonly=self.readonly,
        )
        for field_name in CONFIG_DECIMAL_FIELDS:
            object.__setattr__(self, field_name, getattr(normalized_config, field_name))
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "surviving_bridge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_decayed_bridge_signal_probability",
            "min_decayed_bridge_signal_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _payload_digest_without_digest(_json_ready(self))
        if self.payload_sha256:
            _require_sha256("payload_sha256", self.payload_sha256)
            if self.payload_sha256 != expected_digest:
                raise ValueError("payload_sha256 does not match report payload")
        else:
            object.__setattr__(self, "payload_sha256", expected_digest)


def build_research_strategy_claim_source_signal_decay_bridge_report(
    observations: list[ResearchStrategyClaimSourceSignalDecayBridgeObservation]
    | tuple[ResearchStrategyClaimSourceSignalDecayBridgeObservation, ...],
    *,
    config: ResearchStrategyClaimSourceSignalDecayBridgeConfig,
    generated_at: datetime,
) -> ResearchStrategyClaimSourceSignalDecayBridgeReport:
    if type(config) is not ResearchStrategyClaimSourceSignalDecayBridgeConfig:
        raise ValueError(
            "config must be a ResearchStrategyClaimSourceSignalDecayBridgeConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_observations(observations)
    for row in source_rows:
        _reject_future_observed_at("claim_observed_at", row.claim_observed_at, generated_at_utc)
        _reject_future_observed_at("source_observed_at", row.source_observed_at, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_observation(row, config, generated_at_utc) for row in source_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyClaimSourceSignalDecayBridgeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(source_rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        surviving_bridge_count=_count(
            sum(
                1
                for row in rows
                if row.decayed_bridge_signal_probability >= config.pass_bridge_signal_floor
            ),
        ),
        mean_decayed_bridge_signal_probability=_mean(
            tuple(row.decayed_bridge_signal_probability for row in rows),
        ),
        min_decayed_bridge_signal_probability=_min_or_zero(
            tuple(row.decayed_bridge_signal_probability for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
        pass_bridge_signal_floor=config.pass_bridge_signal_floor,
        watch_bridge_signal_floor=config.watch_bridge_signal_floor,
        max_claim_age_hours=config.max_claim_age_hours,
        max_source_age_hours=config.max_source_age_hours,
        claim_age_decay_cap=config.claim_age_decay_cap,
        source_age_decay_cap=config.source_age_decay_cap,
        source_trust_decay_cap=config.source_trust_decay_cap,
        corroboration_decay_cap=config.corroboration_decay_cap,
        contradiction_decay_cap=config.contradiction_decay_cap,
        source_trust_watch_floor=config.source_trust_watch_floor,
        corroboration_watch_floor=config.corroboration_watch_floor,
        contradiction_watch_score=config.contradiction_watch_score,
        contradiction_block_score=config.contradiction_block_score,
    )


def research_strategy_claim_source_signal_decay_bridge_report_payload(
    report: ResearchStrategyClaimSourceSignalDecayBridgeReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyClaimSourceSignalDecayBridgeReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_keys("payload", report)
        _reject_unsafe_public_values("payload", report)
        _require_public_payload_input_types(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyClaimSourceSignalDecayBridgeReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_keys("payload", payload)
    _reject_unsafe_public_values("payload", payload)
    validate_research_strategy_claim_source_signal_decay_bridge_report_payload(payload)
    return payload


def research_strategy_claim_source_signal_decay_bridge_report_json(
    report: ResearchStrategyClaimSourceSignalDecayBridgeReport | dict[str, Any],
) -> str:
    payload = research_strategy_claim_source_signal_decay_bridge_report_payload(report)
    return _canonical_json(payload)


def validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_keys("payload", payload)
    _reject_unsafe_public_values("payload", payload)
    _validate_public_payload_schema(payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    digest = ready["payload_sha256"]
    _require_sha256("payload_sha256", digest)
    expected_digest = _payload_digest_without_digest(ready)
    if digest != expected_digest:
        raise ValueError("payload_sha256 does not match report payload")
    _report_from_public_payload(payload)


@final
@dataclass(frozen=True, slots=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    if set(payload) != PUBLIC_PAYLOAD_KEYS:
        raise ValueError("payload keys must match exact schema")
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(payload[field_name]) is not bool or payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _parse_datetime_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_SIGNAL_DECAY_BRIDGE_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in CONFIG_DECIMAL_FIELDS:
        _parse_decimal_string(field_name, payload[field_name], ratio=field_name not in {
            "max_claim_age_hours",
            "max_source_age_hours",
        })
    for field_name in (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "surviving_bridge_count",
    ):
        _parse_decimal_string(field_name, payload[field_name], count=True)
    for field_name in (
        "mean_decayed_bridge_signal_probability",
        "min_decayed_bridge_signal_probability",
    ):
        _parse_decimal_string(field_name, payload[field_name], ratio=False)
    _require_member("status", payload["status"], STATUSES)
    _validate_reason_code_list("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    _validate_reason_code_counts_payload(payload["reason_code_counts"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a JSON array")
    for value in payload["rows"]:
        _validate_public_row_schema(value)
    _require_sha256("payload_sha256", payload["payload_sha256"])


def _validate_public_row_schema(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    row = value
    if set(row) != PUBLIC_ROW_PAYLOAD_KEYS:
        raise ValueError("row payload keys must match exact schema")
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(row[field_name]) is not bool or row[field_name] is not True:
            raise ValueError(f"row {field_name} must be True")
    _require_redacted_reference("redacted_claim_ref", row["redacted_claim_ref"], "claim_ref")
    _require_redacted_reference("redacted_source_ref", row["redacted_source_ref"], "source_ref")
    _parse_datetime_string("claim_observed_at", row["claim_observed_at"])
    _parse_datetime_string("source_observed_at", row["source_observed_at"])
    for field_name in ("claim_age_hours", "source_age_hours"):
        _parse_decimal_string(field_name, row[field_name], ratio=False)
    for field_name in (
        "claim_signal_probability",
        "source_alignment_score",
        "claim_age_decay_probability",
        "source_age_decay_probability",
        "source_trust_score",
        "source_trust_decay_probability",
        "corroboration_score",
        "corroboration_decay_probability",
        "contradiction_score",
        "contradiction_decay_probability",
    ):
        _parse_decimal_string(field_name, row[field_name], ratio=True)
    for field_name in ("raw_bridge_signal_probability", "decayed_bridge_signal_probability"):
        _parse_decimal_string(field_name, row[field_name], ratio=False)
    _require_member("status", row["status"], STATUSES)
    _validate_reason_code_list("reason_codes", row["reason_codes"], ROW_REASON_CODES)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyClaimSourceSignalDecayBridgeReport:
    rows = tuple(_row_from_public_payload(value) for value in payload["rows"])
    reason_code_counts = tuple(
        (
            item[0],
            _parse_decimal_string("reason_code_counts count", item[1], count=True),
        )
        for item in payload["reason_code_counts"]
    )
    values: dict[str, Any] = {
        "generated_at": _parse_datetime_string("generated_at", payload["generated_at"]),
        "config_version": payload["config_version"],
        **{
            field_name: _parse_decimal_string(
                field_name,
                payload[field_name],
                ratio=field_name not in {"max_claim_age_hours", "max_source_age_hours"},
            )
            for field_name in CONFIG_DECIMAL_FIELDS
        },
        "observation_count": _parse_decimal_string(
            "observation_count", payload["observation_count"], count=True,
        ),
        "pass_count": _parse_decimal_string("pass_count", payload["pass_count"], count=True),
        "watch_count": _parse_decimal_string("watch_count", payload["watch_count"], count=True),
        "block_count": _parse_decimal_string("block_count", payload["block_count"], count=True),
        "surviving_bridge_count": _parse_decimal_string(
            "surviving_bridge_count", payload["surviving_bridge_count"], count=True,
        ),
        "mean_decayed_bridge_signal_probability": _parse_decimal_string(
            "mean_decayed_bridge_signal_probability",
            payload["mean_decayed_bridge_signal_probability"],
            ratio=False,
        ),
        "min_decayed_bridge_signal_probability": _parse_decimal_string(
            "min_decayed_bridge_signal_probability",
            payload["min_decayed_bridge_signal_probability"],
            ratio=False,
        ),
        "status": payload["status"],
        "reason_codes": tuple(payload["reason_codes"]),
        "reason_code_counts": reason_code_counts,
        "rows": rows,
        "payload_sha256": payload["payload_sha256"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    return ResearchStrategyClaimSourceSignalDecayBridgeReport(**values)


def _row_from_public_payload(value: object) -> ResearchStrategyClaimSourceSignalDecayBridgeRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    return ResearchStrategyClaimSourceSignalDecayBridgeRow(
        redacted_claim_ref=value["redacted_claim_ref"],
        redacted_source_ref=value["redacted_source_ref"],
        claim_observed_at=_parse_datetime_string("claim_observed_at", value["claim_observed_at"]),
        source_observed_at=_parse_datetime_string("source_observed_at", value["source_observed_at"]),
        claim_age_hours=_parse_decimal_string("claim_age_hours", value["claim_age_hours"], ratio=False),
        source_age_hours=_parse_decimal_string("source_age_hours", value["source_age_hours"], ratio=False),
        claim_signal_probability=_parse_decimal_string("claim_signal_probability", value["claim_signal_probability"], ratio=True),
        source_alignment_score=_parse_decimal_string("source_alignment_score", value["source_alignment_score"], ratio=True),
        raw_bridge_signal_probability=_parse_decimal_string("raw_bridge_signal_probability", value["raw_bridge_signal_probability"], ratio=False),
        claim_age_decay_probability=_parse_decimal_string("claim_age_decay_probability", value["claim_age_decay_probability"], ratio=True),
        source_age_decay_probability=_parse_decimal_string("source_age_decay_probability", value["source_age_decay_probability"], ratio=True),
        source_trust_score=_parse_decimal_string("source_trust_score", value["source_trust_score"], ratio=True),
        source_trust_decay_probability=_parse_decimal_string("source_trust_decay_probability", value["source_trust_decay_probability"], ratio=True),
        corroboration_score=_parse_decimal_string("corroboration_score", value["corroboration_score"], ratio=True),
        corroboration_decay_probability=_parse_decimal_string("corroboration_decay_probability", value["corroboration_decay_probability"], ratio=True),
        contradiction_score=_parse_decimal_string("contradiction_score", value["contradiction_score"], ratio=True),
        contradiction_decay_probability=_parse_decimal_string("contradiction_decay_probability", value["contradiction_decay_probability"], ratio=True),
        decayed_bridge_signal_probability=_parse_decimal_string("decayed_bridge_signal_probability", value["decayed_bridge_signal_probability"], ratio=False),
        status=value["status"],
        reason_codes=tuple(value["reason_codes"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _validate_reason_code_list(
    field_name: str,
    value: object,
    supported: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    _normalize_reason_codes(field_name, value, supported)


def _validate_reason_code_counts_payload(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    for item in value:
        if type(item) is not list or len(item) != 2 or type(item[0]) is not str:
            raise ValueError("reason_code_counts must contain string/count pairs")
    _normalize_reason_code_counts(
        tuple(
            (
                item[0],
                _parse_decimal_string("reason_code_counts count", item[1], count=True),
            )
            for item in value
        ),
    )


def _parse_decimal_string(
    field_name: str,
    value: object,
    *,
    ratio: bool = False,
    count: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = (
        _normalize_nonnegative_count(field_name, parsed)
        if count
        else _normalize_probability(field_name, parsed)
        if ratio
        else _normalize_value(field_name, parsed)
    )
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _parse_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC")
    return normalized


def _normalize_observations(
    observations: list[ResearchStrategyClaimSourceSignalDecayBridgeObservation]
    | tuple[ResearchStrategyClaimSourceSignalDecayBridgeObservation, ...],
) -> tuple[ResearchStrategyClaimSourceSignalDecayBridgeObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyClaimSourceSignalDecayBridgeObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyClaimSourceSignalDecayBridgeObservation values",
            )
        _require_hard_flags("observation", row)
        key = (row.claim_ref, row.source_ref)
        if key in seen:
            raise ValueError("observations must not contain duplicate claim/source pairs")
        seen.add(key)
    return rows


def _row_from_observation(
    row: ResearchStrategyClaimSourceSignalDecayBridgeObservation,
    config: ResearchStrategyClaimSourceSignalDecayBridgeConfig,
    generated_at: datetime,
) -> ResearchStrategyClaimSourceSignalDecayBridgeRow:
    claim_age_hours = _age_hours(generated_at, row.claim_observed_at)
    source_age_hours = _age_hours(generated_at, row.source_observed_at)
    with localcontext(DECIMAL_CONTEXT):
        raw_bridge_signal = _quantize_ratio(
            row.claim_signal_probability * row.source_alignment_score,
        )
    claim_decay = _age_decay(
        claim_age_hours,
        max_age_hours=config.max_claim_age_hours,
        decay_cap=config.claim_age_decay_cap,
    )
    source_decay = _age_decay(
        source_age_hours,
        max_age_hours=config.max_source_age_hours,
        decay_cap=config.source_age_decay_cap,
    )
    trust_decay = _inverse_score_decay(
        row.source_trust_score,
        config.source_trust_decay_cap,
    )
    corroboration_decay = _inverse_score_decay(
        row.corroboration_score,
        config.corroboration_decay_cap,
    )
    with localcontext(DECIMAL_CONTEXT):
        contradiction_decay = _quantize_ratio(
            config.contradiction_decay_cap * row.contradiction_score,
        )
    with localcontext(DECIMAL_CONTEXT):
        decayed_bridge_signal = _quantize_ratio(
            raw_bridge_signal
            - claim_decay
            - source_decay
            - trust_decay
            - corroboration_decay
            - contradiction_decay,
        )
    return ResearchStrategyClaimSourceSignalDecayBridgeRow(
        redacted_claim_ref=_redacted_reference("claim_ref", row.claim_ref),
        redacted_source_ref=_redacted_reference("source_ref", row.source_ref),
        claim_observed_at=row.claim_observed_at,
        source_observed_at=row.source_observed_at,
        claim_age_hours=claim_age_hours,
        source_age_hours=source_age_hours,
        claim_signal_probability=row.claim_signal_probability,
        source_alignment_score=row.source_alignment_score,
        raw_bridge_signal_probability=raw_bridge_signal,
        claim_age_decay_probability=claim_decay,
        source_age_decay_probability=source_decay,
        source_trust_score=row.source_trust_score,
        source_trust_decay_probability=trust_decay,
        corroboration_score=row.corroboration_score,
        corroboration_decay_probability=corroboration_decay,
        contradiction_score=row.contradiction_score,
        contradiction_decay_probability=contradiction_decay,
        decayed_bridge_signal_probability=decayed_bridge_signal,
        status=_row_status(decayed_bridge_signal, row, claim_age_hours, source_age_hours, config),
        reason_codes=_row_reason_codes(
            decayed_bridge_signal,
            row,
            claim_age_hours,
            source_age_hours,
            config,
        ),
    )


def _row_status(
    decayed_bridge_signal: Decimal,
    row: ResearchStrategyClaimSourceSignalDecayBridgeObservation,
    claim_age_hours: Decimal,
    source_age_hours: Decimal,
    config: ResearchStrategyClaimSourceSignalDecayBridgeConfig,
) -> str:
    if decayed_bridge_signal < config.watch_bridge_signal_floor:
        return "block"
    if row.contradiction_score >= config.contradiction_block_score:
        return "block"
    if decayed_bridge_signal < config.pass_bridge_signal_floor:
        return "watch"
    if claim_age_hours > config.max_claim_age_hours:
        return "watch"
    if source_age_hours > config.max_source_age_hours:
        return "watch"
    if row.source_trust_score < config.source_trust_watch_floor:
        return "watch"
    if row.corroboration_score < config.corroboration_watch_floor:
        return "watch"
    if row.contradiction_score >= config.contradiction_watch_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    decayed_bridge_signal: Decimal,
    row: ResearchStrategyClaimSourceSignalDecayBridgeObservation,
    claim_age_hours: Decimal,
    source_age_hours: Decimal,
    config: ResearchStrategyClaimSourceSignalDecayBridgeConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if decayed_bridge_signal >= config.pass_bridge_signal_floor:
        codes.append("claim_source_signal_survives")
    else:
        codes.append("claim_source_signal_decayed")
    if claim_age_hours > config.max_claim_age_hours:
        codes.append("claim_age_decay_watch")
    if source_age_hours > config.max_source_age_hours:
        codes.append("source_age_decay_watch")
    if row.source_trust_score < config.source_trust_watch_floor:
        codes.append("source_trust_watch")
    if row.corroboration_score < config.corroboration_watch_floor:
        codes.append("corroboration_watch")
    if row.contradiction_score >= config.contradiction_block_score:
        codes.append("contradiction_block")
    elif row.contradiction_score >= config.contradiction_watch_score:
        codes.append("contradiction_watch")
    return tuple(codes)


def _report_status(
    rows: tuple[ResearchStrategyClaimSourceSignalDecayBridgeRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyClaimSourceSignalDecayBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("claim_source_signal_bridge_clear",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("claim_source_signal_bridge_block")
    if any(row.status == "watch" for row in rows):
        codes.append("claim_source_signal_bridge_watch")
    for code in REPORT_ROW_REASON_CODES:
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyClaimSourceSignalDecayBridgeRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _age_decay(
    age_hours: Decimal,
    *,
    max_age_hours: Decimal,
    decay_cap: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_ratio = age_hours / max_age_hours
        if age_ratio > ONE_RATIO:
            age_ratio = ONE_RATIO
        return _quantize_ratio(decay_cap * age_ratio)


def _inverse_score_decay(score: Decimal, decay_cap: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(decay_cap * (ONE_RATIO - score))


def _row_sort_key(
    row: ResearchStrategyClaimSourceSignalDecayBridgeRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        _status_rank(row.status),
        row.decayed_bridge_signal_probability,
        row.redacted_claim_ref,
        row.redacted_source_ref,
    )


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    return Decimal("2")


def _validate_row(row: ResearchStrategyClaimSourceSignalDecayBridgeRow) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_raw_bridge_signal = _quantize_ratio(
            row.claim_signal_probability * row.source_alignment_score,
        )
    if row.raw_bridge_signal_probability != expected_raw_bridge_signal:
        raise ValueError("raw_bridge_signal_probability must match claim source bridge")
    with localcontext(DECIMAL_CONTEXT):
        expected_decayed_bridge_signal = _quantize_ratio(
            row.raw_bridge_signal_probability
            - row.claim_age_decay_probability
            - row.source_age_decay_probability
            - row.source_trust_decay_probability
            - row.corroboration_decay_probability
            - row.contradiction_decay_probability,
        )
    if row.decayed_bridge_signal_probability != expected_decayed_bridge_signal:
        raise ValueError("decayed_bridge_signal_probability must match decay reducer")


def _validate_report(report: ResearchStrategyClaimSourceSignalDecayBridgeReport) -> None:
    rows = report.rows
    config = ResearchStrategyClaimSourceSignalDecayBridgeConfig(
        config_version=report.config_version,
        pass_bridge_signal_floor=report.pass_bridge_signal_floor,
        watch_bridge_signal_floor=report.watch_bridge_signal_floor,
        max_claim_age_hours=report.max_claim_age_hours,
        max_source_age_hours=report.max_source_age_hours,
        claim_age_decay_cap=report.claim_age_decay_cap,
        source_age_decay_cap=report.source_age_decay_cap,
        source_trust_decay_cap=report.source_trust_decay_cap,
        corroboration_decay_cap=report.corroboration_decay_cap,
        contradiction_decay_cap=report.contradiction_decay_cap,
        source_trust_watch_floor=report.source_trust_watch_floor,
        corroboration_watch_floor=report.corroboration_watch_floor,
        contradiction_watch_score=report.contradiction_watch_score,
        contradiction_block_score=report.contradiction_block_score,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    for row in rows:
        _validate_row_against_config(row, config, report.generated_at)
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.surviving_bridge_count != _count(
        sum(
            1
            for row in rows
            if row.decayed_bridge_signal_probability >= config.pass_bridge_signal_floor
        ),
    ):
        raise ValueError("surviving_bridge_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    decayed_signals = tuple(row.decayed_bridge_signal_probability for row in rows)
    if report.mean_decayed_bridge_signal_probability != _mean(decayed_signals):
        raise ValueError("mean_decayed_bridge_signal_probability must match rows")
    if report.min_decayed_bridge_signal_probability != _min_or_zero(decayed_signals):
        raise ValueError("min_decayed_bridge_signal_probability must match rows")


def _validate_row_against_config(
    row: ResearchStrategyClaimSourceSignalDecayBridgeRow,
    config: ResearchStrategyClaimSourceSignalDecayBridgeConfig,
    generated_at: datetime,
) -> None:
    _reject_future_observed_at("claim_observed_at", row.claim_observed_at, generated_at)
    _reject_future_observed_at("source_observed_at", row.source_observed_at, generated_at)
    claim_age_hours = _age_hours(generated_at, row.claim_observed_at)
    source_age_hours = _age_hours(generated_at, row.source_observed_at)
    if row.claim_age_hours != claim_age_hours:
        raise ValueError("claim_age_hours must match timestamps")
    if row.source_age_hours != source_age_hours:
        raise ValueError("source_age_hours must match timestamps")
    expected_components = {
        "claim_age_decay_probability": _age_decay(
            row.claim_age_hours,
            max_age_hours=config.max_claim_age_hours,
            decay_cap=config.claim_age_decay_cap,
        ),
        "source_age_decay_probability": _age_decay(
            row.source_age_hours,
            max_age_hours=config.max_source_age_hours,
            decay_cap=config.source_age_decay_cap,
        ),
        "source_trust_decay_probability": _inverse_score_decay(
            row.source_trust_score,
            config.source_trust_decay_cap,
        ),
        "corroboration_decay_probability": _inverse_score_decay(
            row.corroboration_score,
            config.corroboration_decay_cap,
        ),
        "contradiction_decay_probability": _quantized_product(
            config.contradiction_decay_cap,
            row.contradiction_score,
        ),
    }
    for field_name, expected in expected_components.items():
        if getattr(row, field_name) != expected:
            raise ValueError(f"{field_name} must match config and inputs")
    expected_observation = ResearchStrategyClaimSourceSignalDecayBridgeObservation(
        claim_ref=row.redacted_claim_ref,
        source_ref=row.redacted_source_ref,
        claim_observed_at=row.claim_observed_at,
        source_observed_at=row.source_observed_at,
        claim_signal_probability=row.claim_signal_probability,
        source_alignment_score=row.source_alignment_score,
        source_trust_score=row.source_trust_score,
        corroboration_score=row.corroboration_score,
        contradiction_score=row.contradiction_score,
    )
    expected_status = _row_status(
        row.decayed_bridge_signal_probability,
        expected_observation,
        row.claim_age_hours,
        row.source_age_hours,
        config,
    )
    if row.status != expected_status:
        raise ValueError("status must match config and rows")
    expected_reason_codes = _row_reason_codes(
        row.decayed_bridge_signal_probability,
        expected_observation,
        row.claim_age_hours,
        row.source_age_hours,
        config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match config and row")


def _normalize_rows(
    rows: list[ResearchStrategyClaimSourceSignalDecayBridgeRow]
    | tuple[ResearchStrategyClaimSourceSignalDecayBridgeRow, ...],
) -> tuple[ResearchStrategyClaimSourceSignalDecayBridgeRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyClaimSourceSignalDecayBridgeRow:
            raise ValueError(
                "rows must contain ResearchStrategyClaimSourceSignalDecayBridgeRow values",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in reason_code_counts:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        reason_code, count = item
        if type(reason_code) is not str:
            raise ValueError("reason_code_counts reason code must be a string")
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code_counts reason code is not supported")
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    expected = tuple(sorted(normalized, key=lambda item: (-item[1], item[0])))
    if tuple(normalized) != expected:
        raise ValueError("reason_code_counts must be sorted")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} values must be strings")
        if reason_code not in supported:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return normalized


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.copy_abs() if value.is_zero() else value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_public_payload_input_types(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_payload_input_types(item)
        return
    if type(value) is list:
        for item in value:
            _require_public_payload_input_types(item)
        return
    if type(value) is str or type(value) is bool:
        return
    if value is None:
        raise ValueError("JSON null is not allowed in public payload")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("public payload must contain only exact JSON containers and scalars")


def _payload_digest_without_digest(payload: dict[str, Any]) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    return sha256(_canonical_json(payload_without_digest).encode("utf-8")).hexdigest()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _reject_unsafe_public_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_keys(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key, UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_keys(label, item)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value, UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)


def _has_unsafe_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_private_reference(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty stable reference")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_redacted_reference(field_name: str, value: str, prefix: str) -> None:
    expected_prefix = f"{prefix}_"
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith(expected_prefix):
        raise ValueError(f"{field_name} must be redacted")
    digest = value[len(expected_prefix) :]
    if len(digest) != REDACTED_DIGEST_LENGTH:
        raise ValueError(f"{field_name} must use a short digest")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must use a lowercase hex digest")


def _redacted_reference(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256(value.encode('utf-8')).hexdigest()[:REDACTED_DIGEST_LENGTH]}"


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _reject_future_observed_at(
    field_name: str,
    observed_at: datetime,
    generated_at: datetime,
) -> None:
    if observed_at > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    total_microseconds = (
        ((delta.days * 86400) + delta.seconds) * 1000000
    ) + delta.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            Decimal(total_microseconds)
            / (SECONDS_PER_HOUR * MICROSECONDS_PER_SECOND),
        )


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_value(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_ratio(value)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(COUNT_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a whole number") from exc
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole number")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return ZERO_COUNT if normalized.is_zero() else normalized


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(RATIO_QUANTUM)
            return ZERO_RATIO if normalized.is_zero() else normalized
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _quantized_product(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(left * right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / _count(len(values)))


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return min(values)
