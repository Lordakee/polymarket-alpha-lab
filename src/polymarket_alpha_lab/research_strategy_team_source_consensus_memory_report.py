"""Report-only consensus memory research for strategy teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence, final


DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONSENSUS_MEMORY_CONFIG_VERSION = (
    "research-strategy-team-consensus-memory-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_MEMORY_STATES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "db",
    "data" + "base",
    "net" + "work",
    "wall" + "et",
    "au" + "th",
    "ord" + "er",
    "li" + "ve",
    "trad" + "ing",
    "trade",
    "buy",
    "sell",
    "siz" + "ing",
    "reco" + "mmendation",
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "ta" + "ble",
    "tok" + "en",
)
_REASON_CODE_SEQUENCE = (
    "empty_consensus_memory",
    "missing_supporting_consensus",
    "insufficient_supporting_family_consensus",
    "conflicting_memory_observation",
    "independent_family_consensus_boost",
    "consensus_memory_pass",
)
_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "min_supporting_family_count",
    "min_consensus_score",
    "conflict_penalty_per_observation",
    "independent_family_boost_per_family",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "team_id",
    "memory_key",
    "observation_count",
    "supporting_observation_count",
    "family_count",
    "supporting_family_count",
    "conflicting_observation_count",
    "average_confidence_score",
    "consensus_score",
    "memory_state",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_PAYLOAD_ITEM_FIELDS = (
    "key",
    "value",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "memory_state",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_consensus_score",
    "rows",
    "reason_codes",
    "public_payload",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConsensusMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONSENSUS_MEMORY_CONFIG_VERSION
    )
    min_supporting_family_count: Decimal = Decimal("2.000000")
    min_consensus_score: Decimal = Decimal("0.750000")
    conflict_penalty_per_observation: Decimal = Decimal("0.150000")
    independent_family_boost_per_family: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConsensusMemoryConfig:
            raise TypeError(
                "ResearchStrategyTeamSourceConsensusMemoryConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConsensusMemoryConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyTeamSourceConsensusMemoryConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONSENSUS_MEMORY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_supporting_family_count",
            _require_positive_count_decimal(
                "min_supporting_family_count",
                self.min_supporting_family_count,
            ),
        )
        for field_name in (
            "min_consensus_score",
            "conflict_penalty_per_observation",
            "independent_family_boost_per_family",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConsensusMemoryObservation:
    team_id: str
    memory_key: str
    family_id: str
    confidence_score: Decimal
    supports_consensus: bool
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConsensusMemoryObservation:
            raise TypeError(
                "ResearchStrategyTeamSourceConsensusMemoryObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConsensusMemoryObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategyTeamSourceConsensusMemoryObservation",
            )
        for field_name in ("team_id", "memory_key", "family_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        _require_bool("supports_consensus", self.supports_consensus)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem:
            raise TypeError(
                "ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConsensusMemoryRow:
    team_id: str
    memory_key: str
    observation_count: Decimal
    supporting_observation_count: Decimal
    family_count: Decimal
    supporting_family_count: Decimal
    conflicting_observation_count: Decimal
    average_confidence_score: Decimal
    consensus_score: Decimal
    memory_state: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConsensusMemoryRow:
            raise TypeError(
                "ResearchStrategyTeamSourceConsensusMemoryRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConsensusMemoryRow:
            raise ValueError(
                "row must be exactly ResearchStrategyTeamSourceConsensusMemoryRow",
            )
        for field_name in ("team_id", "memory_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "observation_count",
            "supporting_observation_count",
            "family_count",
            "supporting_family_count",
            "conflicting_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "consensus_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_memory_state("memory_state", self.memory_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConsensusMemoryReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyTeamSourceConsensusMemoryConfig
    memory_state: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_consensus_score: Decimal
    rows: tuple[ResearchStrategyTeamSourceConsensusMemoryRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConsensusMemoryReport:
            raise TypeError(
                "ResearchStrategyTeamSourceConsensusMemoryReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConsensusMemoryReport:
            raise ValueError(
                "report must be exactly ResearchStrategyTeamSourceConsensusMemoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONSENSUS_MEMORY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "config", _revalidated_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_memory_state("memory_state", self.memory_state)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_consensus_score",
            _require_ratio_decimal(
                "average_consensus_score",
                self.average_consensus_score,
            ),
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
        return research_strategy_team_source_consensus_memory_report_payload(self)


def build_research_strategy_team_source_consensus_memory_report(
    observations: Sequence[ResearchStrategyTeamSourceConsensusMemoryObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamSourceConsensusMemoryConfig | None = None,
    public_payload: Sequence[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem] = (),
) -> ResearchStrategyTeamSourceConsensusMemoryReport:
    """Build a local read-only consensus memory report."""

    if config is None:
        config = ResearchStrategyTeamSourceConsensusMemoryConfig()
    config = _revalidated_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "config": config,
        "memory_state": _report_state(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_state_count(rows, "pass")),
        "watch_count": _decimal_count(_state_count(rows, "watch")),
        "block_count": _decimal_count(_state_count(rows, "block")),
        "average_consensus_score": _average(
            tuple(row.consensus_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamSourceConsensusMemoryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_team_source_consensus_memory_report_payload(
    report: ResearchStrategyTeamSourceConsensusMemoryReport,
) -> dict[str, object]:
    if type(report) is not ResearchStrategyTeamSourceConsensusMemoryReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamSourceConsensusMemoryReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(
        "ResearchStrategyTeamSourceConsensusMemoryReport.payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_strategy_team_source_consensus_memory_report_payload(payload)
    return payload


def validate_research_strategy_team_source_consensus_memory_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    _report_from_payload(payload)
    return True


def _report_from_payload(
    payload: dict[str, object],
) -> ResearchStrategyTeamSourceConsensusMemoryReport:
    values = _require_exact_payload_fields(
        "report payload",
        payload,
        _REPORT_PAYLOAD_FIELDS,
    )
    rows_value = _require_payload_list("rows", values["rows"])
    reason_codes_value = _require_payload_list("reason_codes", values["reason_codes"])
    public_payload_value = _require_payload_list(
        "public_payload",
        values["public_payload"],
    )
    rows = tuple(
        _row_from_payload(item, index=index)
        for index, item in enumerate(rows_value)
    )
    normalized_rows = _normalize_rows(rows)
    if rows != normalized_rows:
        raise ValueError("rows must use canonical order")
    public_payload = tuple(
        _public_payload_item_from_payload(item, index=index)
        for index, item in enumerate(public_payload_value)
    )
    normalized_public_payload = _normalize_public_payload(public_payload)
    if public_payload != normalized_public_payload:
        raise ValueError("public_payload must use canonical order")
    return ResearchStrategyTeamSourceConsensusMemoryReport(
        generated_at=_payload_datetime("generated_at", values["generated_at"]),
        config_version=_payload_identifier(
            "config_version",
            values["config_version"],
        ),
        config=_config_from_payload(values["config"]),
        memory_state=_payload_memory_state("memory_state", values["memory_state"]),
        row_count=_payload_count_decimal("row_count", values["row_count"]),
        pass_count=_payload_count_decimal("pass_count", values["pass_count"]),
        watch_count=_payload_count_decimal("watch_count", values["watch_count"]),
        block_count=_payload_count_decimal("block_count", values["block_count"]),
        average_consensus_score=_payload_ratio_decimal(
            "average_consensus_score",
            values["average_consensus_score"],
        ),
        rows=normalized_rows,
        reason_codes=_payload_reason_codes("reason_codes", reason_codes_value),
        public_payload=normalized_public_payload,
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            values["derived_validation_digest"],
        ),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _config_from_payload(
    value: object,
) -> ResearchStrategyTeamSourceConsensusMemoryConfig:
    values = _require_exact_payload_fields(
        "config payload",
        value,
        _CONFIG_PAYLOAD_FIELDS,
    )
    return ResearchStrategyTeamSourceConsensusMemoryConfig(
        config_version=_payload_identifier(
            "config_version",
            values["config_version"],
        ),
        min_supporting_family_count=_payload_count_decimal(
            "min_supporting_family_count",
            values["min_supporting_family_count"],
        ),
        min_consensus_score=_payload_ratio_decimal(
            "min_consensus_score",
            values["min_consensus_score"],
        ),
        conflict_penalty_per_observation=_payload_ratio_decimal(
            "conflict_penalty_per_observation",
            values["conflict_penalty_per_observation"],
        ),
        independent_family_boost_per_family=_payload_ratio_decimal(
            "independent_family_boost_per_family",
            values["independent_family_boost_per_family"],
        ),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyTeamSourceConsensusMemoryRow:
    values = _require_exact_payload_fields(
        f"row payload[{index}]",
        value,
        _ROW_PAYLOAD_FIELDS,
    )
    reason_codes_value = _require_payload_list(
        f"rows[{index}].reason_codes",
        values["reason_codes"],
    )
    return ResearchStrategyTeamSourceConsensusMemoryRow(
        team_id=_payload_identifier("team_id", values["team_id"]),
        memory_key=_payload_identifier("memory_key", values["memory_key"]),
        observation_count=_payload_count_decimal(
            "observation_count",
            values["observation_count"],
        ),
        supporting_observation_count=_payload_count_decimal(
            "supporting_observation_count",
            values["supporting_observation_count"],
        ),
        family_count=_payload_count_decimal("family_count", values["family_count"]),
        supporting_family_count=_payload_count_decimal(
            "supporting_family_count",
            values["supporting_family_count"],
        ),
        conflicting_observation_count=_payload_count_decimal(
            "conflicting_observation_count",
            values["conflicting_observation_count"],
        ),
        average_confidence_score=_payload_ratio_decimal(
            "average_confidence_score",
            values["average_confidence_score"],
        ),
        consensus_score=_payload_ratio_decimal(
            "consensus_score",
            values["consensus_score"],
        ),
        memory_state=_payload_memory_state("memory_state", values["memory_state"]),
        reason_codes=_payload_reason_codes(
            f"rows[{index}].reason_codes",
            reason_codes_value,
        ),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _public_payload_item_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem:
    values = _require_exact_payload_fields(
        f"public payload item[{index}]",
        value,
        _PUBLIC_PAYLOAD_ITEM_FIELDS,
    )
    return ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
        key=_payload_identifier("key", values["key"]),
        value=_payload_text("value", values["value"]),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != frozenset(expected_fields):
        raise ValueError(f"{label} must use exact schema")
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} must use canonical order")
    return value


def _require_payload_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _payload_identifier(field_name: str, value: object) -> str:
    return _require_public_identifier(field_name, value)


def _payload_text(field_name: str, value: object) -> str:
    return _require_public_text(field_name, value)


def _payload_memory_state(field_name: str, value: object) -> str:
    return _require_memory_state(field_name, value)


def _payload_digest(field_name: str, value: object) -> str:
    return _require_sha256_digest(field_name, value)


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    if _PUBLIC_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return parsed


def _payload_count_decimal(field_name: str, value: object) -> Decimal:
    parsed = _payload_decimal(field_name, value)
    normalized = _require_nonnegative_count_decimal(field_name, parsed)
    if value != format(normalized, ".6f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_ratio_decimal(field_name: str, value: object) -> Decimal:
    parsed = _payload_decimal(field_name, value)
    normalized = _require_ratio_decimal(field_name, parsed)
    if value != format(normalized, ".6f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(field_name, parsed)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_reason_codes(
    field_name: str,
    value: list[object],
) -> tuple[str, ...]:
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    normalized = _normalize_reason_codes(tuple(value))
    if tuple(value) != normalized:
        raise ValueError(f"{field_name} must be unique and deterministic")
    return normalized


def _payload_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _revalidated_config(
    config: object,
) -> ResearchStrategyTeamSourceConsensusMemoryConfig:
    if type(config) is not ResearchStrategyTeamSourceConsensusMemoryConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamSourceConsensusMemoryConfig",
        )
    canonical = ResearchStrategyTeamSourceConsensusMemoryConfig(
        config_version=config.config_version,
        min_supporting_family_count=config.min_supporting_family_count,
        min_consensus_score=config.min_consensus_score,
        conflict_penalty_per_observation=config.conflict_penalty_per_observation,
        independent_family_boost_per_family=config.independent_family_boost_per_family,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )
    _require_constructor_normalized("config", config, canonical)
    return canonical


def _revalidated_observation(
    observation: object,
) -> ResearchStrategyTeamSourceConsensusMemoryObservation:
    if type(observation) is not ResearchStrategyTeamSourceConsensusMemoryObservation:
        raise ValueError(
            "observations must contain ResearchStrategyTeamSourceConsensusMemoryObservation",
        )
    canonical = ResearchStrategyTeamSourceConsensusMemoryObservation(
        team_id=observation.team_id,
        memory_key=observation.memory_key,
        family_id=observation.family_id,
        confidence_score=observation.confidence_score,
        supports_consensus=observation.supports_consensus,
        observed_at=observation.observed_at,
        paper_only=observation.paper_only,
        report_only=observation.report_only,
        readonly=observation.readonly,
    )
    _require_constructor_normalized("observation", observation, canonical)
    return canonical


def _revalidated_public_payload_item(
    item: object,
) -> ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem:
    if type(item) is not ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem:
        raise ValueError(
            "public_payload items must be "
            "ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem",
        )
    canonical = ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
        key=item.key,
        value=item.value,
        paper_only=item.paper_only,
        report_only=item.report_only,
        readonly=item.readonly,
    )
    _require_constructor_normalized("public payload item", item, canonical)
    return canonical


def _revalidated_row(row: object) -> ResearchStrategyTeamSourceConsensusMemoryRow:
    if type(row) is not ResearchStrategyTeamSourceConsensusMemoryRow:
        raise ValueError("rows must contain ResearchStrategyTeamSourceConsensusMemoryRow")
    canonical = ResearchStrategyTeamSourceConsensusMemoryRow(
        team_id=row.team_id,
        memory_key=row.memory_key,
        observation_count=row.observation_count,
        supporting_observation_count=row.supporting_observation_count,
        family_count=row.family_count,
        supporting_family_count=row.supporting_family_count,
        conflicting_observation_count=row.conflicting_observation_count,
        average_confidence_score=row.average_confidence_score,
        consensus_score=row.consensus_score,
        memory_state=row.memory_state,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    _require_constructor_normalized("row", row, canonical)
    return canonical


def _require_constructor_normalized(
    label: str,
    value: object,
    canonical: object,
) -> None:
    if _constructor_snapshot(value) != _constructor_snapshot(canonical):
        raise ValueError(f"{label} must remain constructor-normalized")


def _constructor_snapshot(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _constructor_snapshot(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return tuple(_constructor_snapshot(item) for item in value)
    if type(value) is list:
        return [_constructor_snapshot(item) for item in value]
    return value


def _build_rows(
    observations: tuple[ResearchStrategyTeamSourceConsensusMemoryObservation, ...],
    config: ResearchStrategyTeamSourceConsensusMemoryConfig,
) -> tuple[ResearchStrategyTeamSourceConsensusMemoryRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchStrategyTeamSourceConsensusMemoryObservation]] = {}
    for observation in observations:
        grouped.setdefault((observation.team_id, observation.memory_key), []).append(
            observation,
        )
    return tuple(
        _row_for_group(team_id, memory_key, tuple(items), config)
        for (team_id, memory_key), items in sorted(grouped.items())
    )


def _row_for_group(
    team_id: str,
    memory_key: str,
    observations: tuple[ResearchStrategyTeamSourceConsensusMemoryObservation, ...],
    config: ResearchStrategyTeamSourceConsensusMemoryConfig,
) -> ResearchStrategyTeamSourceConsensusMemoryRow:
    supporting = tuple(item for item in observations if item.supports_consensus)
    conflicting_count = _decimal_count(len(observations) - len(supporting))
    family_count = _decimal_count(len({item.family_id for item in observations}))
    supporting_family_count = _decimal_count(len({item.family_id for item in supporting}))
    supporting_count = _decimal_count(len(supporting))
    average_confidence = _average(tuple(item.confidence_score for item in supporting))
    consensus_score = _consensus_score(
        average_confidence_score=average_confidence,
        supporting_family_count=supporting_family_count,
        conflicting_observation_count=conflicting_count,
        config=config,
    )
    memory_state = _row_state(
        supporting_observation_count=supporting_count,
        supporting_family_count=supporting_family_count,
        consensus_score=consensus_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        supporting_observation_count=supporting_count,
        supporting_family_count=supporting_family_count,
        conflicting_observation_count=conflicting_count,
        memory_state=memory_state,
        config=config,
    )
    return ResearchStrategyTeamSourceConsensusMemoryRow(
        team_id=team_id,
        memory_key=memory_key,
        observation_count=_decimal_count(len(observations)),
        supporting_observation_count=supporting_count,
        family_count=family_count,
        supporting_family_count=supporting_family_count,
        conflicting_observation_count=conflicting_count,
        average_confidence_score=average_confidence,
        consensus_score=consensus_score,
        memory_state=memory_state,
        reason_codes=reason_codes,
    )


def _consensus_score(
    *,
    average_confidence_score: Decimal,
    supporting_family_count: Decimal,
    conflicting_observation_count: Decimal,
    config: ResearchStrategyTeamSourceConsensusMemoryConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        family_boost = _clamp_ratio(
            max(supporting_family_count - _ONE, _ZERO)
            * config.independent_family_boost_per_family,
        )
        conflict_penalty = _clamp_ratio(
            conflicting_observation_count * config.conflict_penalty_per_observation,
        )
        return _clamp_ratio(
            average_confidence_score + family_boost - conflict_penalty,
        )


def _row_reason_codes(
    *,
    supporting_observation_count: Decimal,
    supporting_family_count: Decimal,
    conflicting_observation_count: Decimal,
    memory_state: str,
    config: ResearchStrategyTeamSourceConsensusMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if supporting_observation_count == _ZERO:
        reason_codes.append("missing_supporting_consensus")
    if supporting_family_count < config.min_supporting_family_count:
        reason_codes.append("insufficient_supporting_family_consensus")
    if conflicting_observation_count > _ZERO:
        reason_codes.append("conflicting_memory_observation")
    if supporting_family_count > _ONE:
        reason_codes.append("independent_family_consensus_boost")
    if memory_state == "pass":
        reason_codes.append("consensus_memory_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_state(
    *,
    supporting_observation_count: Decimal,
    supporting_family_count: Decimal,
    consensus_score: Decimal,
    config: ResearchStrategyTeamSourceConsensusMemoryConfig,
) -> str:
    if supporting_observation_count == _ZERO:
        return "block"
    if (
        supporting_family_count >= config.min_supporting_family_count
        and consensus_score >= config.min_consensus_score
    ):
        return "pass"
    return "watch"


def _report_state(rows: tuple[ResearchStrategyTeamSourceConsensusMemoryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.memory_state == "block" for row in rows):
        return "block"
    if any(row.memory_state == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamSourceConsensusMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_consensus_memory",)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in observed
    )


def _state_count(
    rows: tuple[ResearchStrategyTeamSourceConsensusMemoryRow, ...],
    memory_state: str,
) -> int:
    return sum(1 for row in rows if row.memory_state == memory_state)


def _validate_row_consistency(row: ResearchStrategyTeamSourceConsensusMemoryRow) -> None:
    if row.observation_count <= _ZERO:
        raise ValueError("observation_count must be positive for a row")
    if row.supporting_observation_count > row.observation_count:
        raise ValueError("supporting_observation_count must not exceed observation_count")
    if row.family_count > row.observation_count:
        raise ValueError("family_count must not exceed observation_count")
    if row.supporting_family_count > row.supporting_observation_count:
        raise ValueError(
            "supporting_family_count must not exceed supporting_observation_count",
        )
    if row.supporting_family_count > row.family_count:
        raise ValueError("supporting_family_count must not exceed family_count")
    if row.family_count <= _ZERO:
        raise ValueError("family_count must be positive for a row")
    with localcontext(_DECIMAL_CONTEXT):
        expected_conflicting_count = _quantize(
            row.observation_count - row.supporting_observation_count,
        )
    if row.conflicting_observation_count != expected_conflicting_count:
        raise ValueError(
            "conflicting_observation_count must match unsupported observations",
        )
    if row.supporting_observation_count == _ZERO:
        if row.supporting_family_count != _ZERO:
            raise ValueError(
                "supporting_family_count must be zero without supporting observations",
            )
        if row.average_confidence_score != _ZERO:
            raise ValueError(
                "average_confidence_score must be zero without supporting observations",
            )
    elif row.supporting_family_count == _ZERO:
        raise ValueError(
            "supporting_family_count must be positive with supporting observations",
        )
    if row.memory_state == "pass" and "consensus_memory_pass" not in row.reason_codes:
        raise ValueError("reason_codes must include consensus_memory_pass for pass rows")
    if row.memory_state == "block" and row.supporting_observation_count > _ZERO:
        raise ValueError("block rows must have no supporting observations")


def _validate_row_against_config(
    row: ResearchStrategyTeamSourceConsensusMemoryRow,
    *,
    config: ResearchStrategyTeamSourceConsensusMemoryConfig,
) -> None:
    expected_consensus_score = _consensus_score(
        average_confidence_score=row.average_confidence_score,
        supporting_family_count=row.supporting_family_count,
        conflicting_observation_count=row.conflicting_observation_count,
        config=config,
    )
    if row.consensus_score != expected_consensus_score:
        raise ValueError("consensus_score must match row inputs and config")
    expected_memory_state = _row_state(
        supporting_observation_count=row.supporting_observation_count,
        supporting_family_count=row.supporting_family_count,
        consensus_score=expected_consensus_score,
        config=config,
    )
    if row.memory_state != expected_memory_state:
        raise ValueError("memory_state must match row inputs and config")
    expected_reason_codes = _row_reason_codes(
        supporting_observation_count=row.supporting_observation_count,
        supporting_family_count=row.supporting_family_count,
        conflicting_observation_count=row.conflicting_observation_count,
        memory_state=expected_memory_state,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs and config")


def _validate_report_consistency(
    report: ResearchStrategyTeamSourceConsensusMemoryReport,
) -> None:
    for row in report.rows:
        _validate_row_against_config(row, config=report.config)
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_state_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_state_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_state_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_consensus_score != _average(
        tuple(row.consensus_score for row in report.rows),
    ):
        raise ValueError("average_consensus_score must match rows")
    if report.memory_state != _report_state(report.rows):
        raise ValueError("memory_state must match row states")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchStrategyTeamSourceConsensusMemoryObservation],
) -> tuple[ResearchStrategyTeamSourceConsensusMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchStrategyTeamSourceConsensusMemoryObservation] = []
    for observation in observations:
        normalized.append(_revalidated_observation(observation))
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_id,
                item.memory_key,
                item.observed_at,
                item.family_id,
                item.confidence_score,
                item.supports_consensus,
                item.paper_only,
                item.report_only,
                item.readonly,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyTeamSourceConsensusMemoryRow],
) -> tuple[ResearchStrategyTeamSourceConsensusMemoryRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyTeamSourceConsensusMemoryRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        row = _revalidated_row(row)
        key = (row.team_id, row.memory_key)
        if key in seen:
            raise ValueError("rows must not repeat team_id and memory_key")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.team_id, row.memory_key)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem],
) -> tuple[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        item = _revalidated_public_payload_item(item)
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


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
    if field_name == "derived_validation_digest" or field_name.endswith(
        ".derived_validation_digest",
    ):
        _require_sha256_digest("derived_validation_digest", value)
        return
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_memory_state(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _MEMORY_STATES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    return _canonical_zero(_quantize(raw_value))


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        if raw_value != raw_value.to_integral_value():
            raise ValueError(f"{field_name} must be a whole Decimal")
    return _canonical_zero(_quantize(raw_value))


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < _ZERO or raw_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _canonical_zero(_quantize(raw_value))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        if value < _ZERO:
            return _ZERO
        if value > _ONE:
            return _ONE
        return _canonical_zero(_quantize(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable to 0.000001") from exc


def _canonical_zero(value: Decimal) -> Decimal:
    if value.is_zero():
        return _ZERO
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    values = tuple(reason_codes)
    for reason_code in values:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    expected = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in values
    )
    if values != expected:
        raise ValueError("reason_codes must be deterministic")
    return expected


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchStrategyTeamSourceConsensusMemoryReport,
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
        if value.is_zero() and value.is_signed():
            raise ValueError("Decimal payload value must not use signed zero")
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONSENSUS_MEMORY_CONFIG_VERSION",
    "ResearchStrategyTeamSourceConsensusMemoryConfig",
    "ResearchStrategyTeamSourceConsensusMemoryObservation",
    "ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem",
    "ResearchStrategyTeamSourceConsensusMemoryReport",
    "ResearchStrategyTeamSourceConsensusMemoryRow",
    "build_research_strategy_team_source_consensus_memory_report",
    "research_strategy_team_source_consensus_memory_report_payload",
    "validate_research_strategy_team_source_consensus_memory_report_payload",
)
