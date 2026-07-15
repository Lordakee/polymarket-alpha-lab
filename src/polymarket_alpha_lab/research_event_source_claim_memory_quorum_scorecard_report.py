"""Pure event-source claim memory quorum scorecard report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_SOURCE_CLAIM_MEMORY_QUORUM_SCORECARD_CONFIG_VERSION = (
    "research-event-claim-memory-quorum-scorecard-report-v1"
)
REPORT_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUS_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
_STATUS_REASON_BY_RANK = (
    "claim_memory_quorum_block",
    "claim_memory_quorum_watch",
    "claim_memory_quorum_pass",
)
_ROW_REASON_CODE_SEQUENCE = (
    "missing_agreeing_evidence_quorum",
    "missing_memory_quorum",
    *_STATUS_REASON_BY_RANK,
)
_PUBLIC_ITEM_PAYLOAD_KEYS = (
    "key",
    "value",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "event_key",
    "claim_key",
    "rank",
    "observation_count",
    "agreeing_evidence_count",
    "memory_quorum_count",
    "support_ratio",
    "average_parse_confidence",
    "average_memory_confidence",
    "quorum_score",
    "status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "min_agreeing_evidence_count",
    "min_memory_quorum_count",
    "min_memory_confidence",
    "watch_quorum_score",
    "pass_quorum_score",
    "status",
    "event_claim_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_quorum_score",
    "rows",
    "reason_codes",
    "public_payload",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_BAD_PUBLIC_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("can", "didate"),
        ("mar", "ket"),
        ("sou", "rce"),
        ("u", "rl"),
        ("te", "xt"),
        ("d", "sn"),
        ("ta", "ble"),
        ("to", "ken"),
        ("d", "b"),
        ("net", "work"),
        ("wal", "let"),
        ("au", "th"),
        ("or", "der"),
        ("li", "ve"),
        ("tra", "ding"),
        ("si", "zing"),
        ("recomm", "endation"),
    )
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchEventSourceClaimMemoryQuorumConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_CLAIM_MEMORY_QUORUM_SCORECARD_CONFIG_VERSION
    )
    min_agreeing_evidence_count: Decimal = Decimal("2")
    min_memory_quorum_count: Decimal = Decimal("2")
    min_memory_confidence: Decimal = Decimal("0.500000")
    watch_quorum_score: Decimal = Decimal("0.650000")
    pass_quorum_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceClaimMemoryQuorumConfig:
            raise ValueError(
                "config must be a ResearchEventSourceClaimMemoryQuorumConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_CLAIM_MEMORY_QUORUM_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_agreeing_evidence_count",
            "min_memory_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_memory_confidence",
            "watch_quorum_score",
            "pass_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_quorum_score > self.pass_quorum_score:
            raise ValueError("watch_quorum_score must not exceed pass_quorum_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceClaimMemoryQuorumObservation(_FinalPublicDataclass):
    event_key: str
    claim_key: str
    evidence_key: str
    captured_at: datetime
    claim_present: bool
    parse_confidence: Decimal
    memory_confidence: Decimal
    private_material: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceClaimMemoryQuorumObservation:
            raise ValueError(
                "observation must be a "
                "ResearchEventSourceClaimMemoryQuorumObservation",
            )
        for field_name in ("event_key", "claim_key", "evidence_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        if type(self.claim_present) is not bool:
            raise ValueError("claim_present must be a bool")
        for field_name in ("parse_confidence", "memory_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "private_material",
            _normalize_private_material(self.private_material),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(_FinalPublicDataclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceClaimMemoryQuorumPublicPayloadItem:
            raise ValueError(
                "public payload item must be a "
                "ResearchEventSourceClaimMemoryQuorumPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_string("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventSourceClaimMemoryQuorumRow(_FinalPublicDataclass):
    event_key: str
    claim_key: str
    rank: Decimal
    observation_count: Decimal
    agreeing_evidence_count: Decimal
    memory_quorum_count: Decimal
    support_ratio: Decimal
    average_parse_confidence: Decimal
    average_memory_confidence: Decimal
    quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceClaimMemoryQuorumRow:
            raise ValueError("row must be a ResearchEventSourceClaimMemoryQuorumRow")
        for field_name in ("event_key", "claim_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_count("rank", self.rank),
        )
        for field_name in (
            "observation_count",
            "agreeing_evidence_count",
            "memory_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "support_ratio",
            "average_parse_confidence",
            "average_memory_confidence",
            "quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)
        digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match row payload")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)


@dataclass(frozen=True)
class ResearchEventSourceClaimMemoryQuorumReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    min_agreeing_evidence_count: Decimal
    min_memory_quorum_count: Decimal
    min_memory_confidence: Decimal
    watch_quorum_score: Decimal
    pass_quorum_score: Decimal
    status: str
    event_claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quorum_score: Decimal
    rows: tuple[ResearchEventSourceClaimMemoryQuorumRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchEventSourceClaimMemoryQuorumPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceClaimMemoryQuorumReport:
            raise ValueError("report must be a ResearchEventSourceClaimMemoryQuorumReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_CLAIM_MEMORY_QUORUM_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_agreeing_evidence_count",
            "min_memory_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_memory_confidence",
            "watch_quorum_score",
            "pass_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_quorum_score > self.pass_quorum_score:
            raise ValueError("watch_quorum_score must not exceed pass_quorum_score")
        _require_status("status", self.status)
        for field_name in (
            "event_claim_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quorum_score",
            _normalize_ratio("average_quorum_score", self.average_quorum_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload_items(self.public_payload),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self, _report_config(self))
        digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_source_claim_memory_quorum_scorecard_report_payload(self)


def build_research_event_source_claim_memory_quorum_scorecard_report(
    observations: Sequence[ResearchEventSourceClaimMemoryQuorumObservation],
    *,
    generated_at: datetime,
    config: ResearchEventSourceClaimMemoryQuorumConfig | None = None,
    public_payload: Sequence[
        ResearchEventSourceClaimMemoryQuorumPublicPayloadItem
    ] = (),
) -> ResearchEventSourceClaimMemoryQuorumReport:
    if config is None:
        config = ResearchEventSourceClaimMemoryQuorumConfig()
    if type(config) is not ResearchEventSourceClaimMemoryQuorumConfig:
        raise ValueError("config must be a ResearchEventSourceClaimMemoryQuorumConfig")
    config = replace(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_values = _normalize_observations(observations)
    unranked_rows = _build_rows(observation_values, config)
    for observation in observation_values:
        if observation.captured_at > generated_at_utc:
            raise ValueError("captured_at must not be after generated_at")
    rows = _rank_rows(tuple(sorted(unranked_rows, key=_row_sort_key)))
    event_claim_count = _count_decimal(len(rows))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    average_quorum_score = _average(
        tuple(row.quorum_score for row in rows),
        default=_ZERO_RATIO,
    )
    report_status = _rollup_status(rows)
    return ResearchEventSourceClaimMemoryQuorumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        min_agreeing_evidence_count=config.min_agreeing_evidence_count,
        min_memory_quorum_count=config.min_memory_quorum_count,
        min_memory_confidence=config.min_memory_confidence,
        watch_quorum_score=config.watch_quorum_score,
        pass_quorum_score=config.pass_quorum_score,
        status=report_status,
        event_claim_count=event_claim_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_quorum_score=average_quorum_score,
        rows=rows,
        reason_codes=_report_reason_codes(report_status, rows),
        public_payload=_normalize_public_payload_items(public_payload),
    )


def research_event_source_claim_memory_quorum_scorecard_report_payload(
    report: ResearchEventSourceClaimMemoryQuorumReport | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(report, ResearchEventSourceClaimMemoryQuorumReport):
        _require_hard_flags("report", report)
        for row in report.rows:
            _require_hard_flags("row", row)
        for item in report.public_payload:
            _require_hard_flags("public payload item", item)
        _reject_unsafe_public_payload("report", report)
        payload = _report_public_payload(report, include_digest=True)
        if payload["derived_validation_digest"] != _report_digest(report):
            raise ValueError("derived_validation_digest tamper detected")
        _validate_report_consistency(report, _report_config(report))
        return _validate_public_payload(payload)
    if type(report) is dict:
        return _validate_public_payload(report)
    raise ValueError("report must be a ResearchEventSourceClaimMemoryQuorumReport")


def _normalize_observations(
    observations: object,
) -> tuple[ResearchEventSourceClaimMemoryQuorumObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(
        observations,
        Sequence,
    ):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchEventSourceClaimMemoryQuorumObservation] = []
    for observation in observations:
        if type(observation) is not ResearchEventSourceClaimMemoryQuorumObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventSourceClaimMemoryQuorumObservation items",
            )
        _require_hard_flags("observation", observation)
        normalized.append(replace(observation))
    return tuple(normalized)


def _build_rows(
    observations: tuple[ResearchEventSourceClaimMemoryQuorumObservation, ...],
    config: ResearchEventSourceClaimMemoryQuorumConfig,
) -> tuple[ResearchEventSourceClaimMemoryQuorumRow, ...]:
    grouped: dict[
        tuple[str, str],
        dict[str, ResearchEventSourceClaimMemoryQuorumObservation],
    ] = {}
    for observation in observations:
        if type(observation) is not ResearchEventSourceClaimMemoryQuorumObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventSourceClaimMemoryQuorumObservation items",
            )
        _require_hard_flags("observation", observation)
        group = grouped.setdefault((observation.event_key, observation.claim_key), {})
        existing = group.get(observation.evidence_key)
        if existing is None or _observation_sort_key(observation) > _observation_sort_key(
            existing,
        ):
            group[observation.evidence_key] = observation
    return tuple(
        _build_row(
            event_key,
            claim_key,
            tuple(items[evidence_key] for evidence_key in sorted(items)),
            config,
        )
        for (event_key, claim_key), items in sorted(grouped.items())
    )


def _build_row(
    event_key: str,
    claim_key: str,
    observations: tuple[ResearchEventSourceClaimMemoryQuorumObservation, ...],
    config: ResearchEventSourceClaimMemoryQuorumConfig,
) -> ResearchEventSourceClaimMemoryQuorumRow:
    observation_count = _count_decimal(len(observations))
    agreeing = tuple(item for item in observations if item.claim_present)
    agreeing_count = _count_decimal(len({item.evidence_key for item in agreeing}))
    memory_count = _count_decimal(
        len(
            {
                item.evidence_key
                for item in agreeing
                if item.memory_confidence >= config.min_memory_confidence
            },
        ),
    )
    support_ratio = _ratio(agreeing_count, observation_count)
    average_parse = _average(tuple(item.parse_confidence for item in observations))
    average_memory = _average(tuple(item.memory_confidence for item in observations))
    quorum_score = _average((support_ratio, average_parse, average_memory))
    status = _row_status(agreeing_count, memory_count, quorum_score, config)
    return ResearchEventSourceClaimMemoryQuorumRow(
        event_key=event_key,
        claim_key=claim_key,
        rank=_COUNT_QUANTUM,
        observation_count=observation_count,
        agreeing_evidence_count=agreeing_count,
        memory_quorum_count=memory_count,
        support_ratio=support_ratio,
        average_parse_confidence=average_parse,
        average_memory_confidence=average_memory,
        quorum_score=quorum_score,
        status=status,
        reason_codes=_row_reason_codes(agreeing_count, memory_count, status, config),
    )


def _observation_sort_key(
    observation: ResearchEventSourceClaimMemoryQuorumObservation,
) -> tuple[datetime, bool, Decimal, Decimal]:
    return (
        observation.captured_at,
        observation.claim_present,
        observation.parse_confidence,
        observation.memory_confidence,
    )


def _row_sort_key(
    row: ResearchEventSourceClaimMemoryQuorumRow,
) -> tuple[Decimal, str, str]:
    return (_STATUS_RANK[row.status], row.event_key, row.claim_key)


def _rank_rows(
    rows: tuple[ResearchEventSourceClaimMemoryQuorumRow, ...],
) -> tuple[ResearchEventSourceClaimMemoryQuorumRow, ...]:
    return tuple(
        replace(
            row,
            rank=_count_decimal(index),
            derived_validation_digest="",
        )
        for index, row in enumerate(rows, start=1)
    )


def _row_status(
    agreeing_count: Decimal,
    memory_count: Decimal,
    quorum_score: Decimal,
    config: ResearchEventSourceClaimMemoryQuorumConfig,
) -> str:
    if (
        agreeing_count < config.min_agreeing_evidence_count
        or memory_count < config.min_memory_quorum_count
    ):
        return "block"
    if quorum_score >= config.pass_quorum_score:
        return "pass"
    if quorum_score >= config.watch_quorum_score:
        return "watch"
    return "block"


def _row_reason_codes(
    agreeing_count: Decimal,
    memory_count: Decimal,
    status: str,
    config: ResearchEventSourceClaimMemoryQuorumConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if agreeing_count < config.min_agreeing_evidence_count:
        codes.append("missing_agreeing_evidence_quorum")
    if memory_count < config.min_memory_quorum_count:
        codes.append("missing_memory_quorum")
    codes.append(f"claim_memory_quorum_{status}")
    return tuple(dict.fromkeys(codes))


def _rollup_status(rows: tuple[ResearchEventSourceClaimMemoryQuorumRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    report_status: str,
    rows: tuple[ResearchEventSourceClaimMemoryQuorumRow, ...],
) -> tuple[str, ...]:
    codes = [f"claim_memory_quorum_scorecard_{report_status}"]
    status_set = {row.status for row in rows}
    for reason_code in _STATUS_REASON_BY_RANK:
        status = reason_code.rsplit("_", 1)[-1]
        if status in status_set:
            codes.append(reason_code)
    if not rows:
        codes.append("claim_memory_quorum_empty")
    return tuple(dict.fromkeys(codes))


def _report_public_payload(
    report: ResearchEventSourceClaimMemoryQuorumReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "min_agreeing_evidence_count": report.min_agreeing_evidence_count,
        "min_memory_quorum_count": report.min_memory_quorum_count,
        "min_memory_confidence": report.min_memory_confidence,
        "watch_quorum_score": report.watch_quorum_score,
        "pass_quorum_score": report.pass_quorum_score,
        "status": report.status,
        "event_claim_count": report.event_claim_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_quorum_score": report.average_quorum_score,
        "rows": [_row_public_payload(row, include_digest=True) for row in report.rows],
        "reason_codes": report.reason_codes,
        "public_payload": [
            _public_item_payload(item) for item in report.public_payload
        ],
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    payload["paper_only"] = report.paper_only
    payload["report_only"] = report.report_only
    payload["readonly"] = report.readonly
    return _json_ready(payload)


def _row_public_payload(
    row: ResearchEventSourceClaimMemoryQuorumRow,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_key": row.event_key,
        "claim_key": row.claim_key,
        "rank": row.rank,
        "observation_count": row.observation_count,
        "agreeing_evidence_count": row.agreeing_evidence_count,
        "memory_quorum_count": row.memory_quorum_count,
        "support_ratio": row.support_ratio,
        "average_parse_confidence": row.average_parse_confidence,
        "average_memory_confidence": row.average_memory_confidence,
        "quorum_score": row.quorum_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
    }
    if include_digest:
        payload["derived_validation_digest"] = row.derived_validation_digest
    payload["paper_only"] = row.paper_only
    payload["report_only"] = row.report_only
    payload["readonly"] = row.readonly
    ready = _json_ready(payload)
    if include_digest and ready["derived_validation_digest"] != _row_digest(row):
        raise ValueError("derived_validation_digest tamper detected")
    return ready


def _public_item_payload(
    item: ResearchEventSourceClaimMemoryQuorumPublicPayloadItem,
) -> dict[str, Any]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _validate_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    ready = _copy_public_json("payload", payload)
    _require_exact_payload_keys("payload schema", ready, _REPORT_PAYLOAD_KEYS)

    rows_value = ready["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(
        _row_from_public_payload(item, index)
        for index, item in enumerate(rows_value)
    )

    public_payload_value = ready["public_payload"]
    if type(public_payload_value) is not list:
        raise ValueError("public_payload must be a list")
    public_payload = tuple(
        _public_item_from_payload(item, index)
        for index, item in enumerate(public_payload_value)
    )

    report = ResearchEventSourceClaimMemoryQuorumReport(
        generated_at=_payload_datetime("generated_at", ready["generated_at"]),
        config_version=_payload_string("config_version", ready["config_version"]),
        min_agreeing_evidence_count=_payload_positive_count(
            "min_agreeing_evidence_count",
            ready["min_agreeing_evidence_count"],
        ),
        min_memory_quorum_count=_payload_positive_count(
            "min_memory_quorum_count",
            ready["min_memory_quorum_count"],
        ),
        min_memory_confidence=_payload_ratio(
            "min_memory_confidence",
            ready["min_memory_confidence"],
        ),
        watch_quorum_score=_payload_ratio(
            "watch_quorum_score",
            ready["watch_quorum_score"],
        ),
        pass_quorum_score=_payload_ratio(
            "pass_quorum_score",
            ready["pass_quorum_score"],
        ),
        status=_payload_status("status", ready["status"]),
        event_claim_count=_payload_nonnegative_count(
            "event_claim_count",
            ready["event_claim_count"],
        ),
        pass_count=_payload_nonnegative_count("pass_count", ready["pass_count"]),
        watch_count=_payload_nonnegative_count("watch_count", ready["watch_count"]),
        block_count=_payload_nonnegative_count("block_count", ready["block_count"]),
        average_quorum_score=_payload_ratio(
            "average_quorum_score",
            ready["average_quorum_score"],
        ),
        rows=rows,
        reason_codes=_payload_reason_codes("reason_codes", ready["reason_codes"]),
        public_payload=public_payload,
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            ready["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", ready["paper_only"]),
        report_only=_payload_true("report_only", ready["report_only"]),
        readonly=_payload_true("readonly", ready["readonly"]),
    )
    canonical = _report_public_payload(report, include_digest=True)
    if ready != canonical:
        raise ValueError("payload must use canonical schema values")
    return canonical


def _row_from_public_payload(
    value: object,
    index: int,
) -> ResearchEventSourceClaimMemoryQuorumRow:
    label = f"row {index}"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a dict")
    _require_exact_payload_keys(f"{label} schema", value, _ROW_PAYLOAD_KEYS)
    return ResearchEventSourceClaimMemoryQuorumRow(
        event_key=_payload_string("event_key", value["event_key"]),
        claim_key=_payload_string("claim_key", value["claim_key"]),
        rank=_payload_positive_count("rank", value["rank"]),
        observation_count=_payload_nonnegative_count(
            "observation_count",
            value["observation_count"],
        ),
        agreeing_evidence_count=_payload_nonnegative_count(
            "agreeing_evidence_count",
            value["agreeing_evidence_count"],
        ),
        memory_quorum_count=_payload_nonnegative_count(
            "memory_quorum_count",
            value["memory_quorum_count"],
        ),
        support_ratio=_payload_ratio("support_ratio", value["support_ratio"]),
        average_parse_confidence=_payload_ratio(
            "average_parse_confidence",
            value["average_parse_confidence"],
        ),
        average_memory_confidence=_payload_ratio(
            "average_memory_confidence",
            value["average_memory_confidence"],
        ),
        quorum_score=_payload_ratio("quorum_score", value["quorum_score"]),
        status=_payload_status("status", value["status"]),
        reason_codes=_payload_reason_codes("reason_codes", value["reason_codes"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", value["paper_only"]),
        report_only=_payload_true("report_only", value["report_only"]),
        readonly=_payload_true("readonly", value["readonly"]),
    )


def _public_item_from_payload(
    value: object,
    index: int,
) -> ResearchEventSourceClaimMemoryQuorumPublicPayloadItem:
    label = f"public payload item {index}"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a dict")
    _require_exact_payload_keys(f"{label} schema", value, _PUBLIC_ITEM_PAYLOAD_KEYS)
    return ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
        key=_payload_string("key", value["key"]),
        value=_payload_string("value", value["value"]),
        paper_only=_payload_true("paper_only", value["paper_only"]),
        report_only=_payload_true("report_only", value["report_only"]),
        readonly=_payload_true("readonly", value["readonly"]),
    )


def _copy_public_json(label: str, value: object) -> Any:
    if type(value) is str or type(value) is bool:
        return value
    if type(value) is list:
        return [
            _copy_public_json(f"{label} item", item)
            for item in value
        ]
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            copied[key] = _copy_public_json(f"{label}.{key}", item)
        return copied
    raise ValueError(f"{label} must contain only JSON strings, booleans, lists, and objects")


def _require_exact_payload_keys(
    label: str,
    value: dict[str, Any],
    expected: tuple[str, ...],
) -> None:
    if len(value) != len(expected) or set(value) != set(expected):
        raise ValueError(f"{label} keys must match exactly")


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_status(field_name: str, value: object) -> str:
    normalized = _payload_string(field_name, value)
    _require_status(field_name, normalized)
    return normalized


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_digest(field_name: str, value: object) -> str:
    normalized = _payload_string(field_name, value)
    _require_digest(field_name, normalized)
    return normalized


def _payload_datetime(field_name: str, value: object) -> datetime:
    normalized = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    parsed = _as_utc(field_name, parsed)
    if parsed.isoformat() != normalized:
        raise ValueError(f"{field_name} must use canonical UTC representation")
    return parsed


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string("reason_code", item) for item in value)


def _payload_positive_count(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_positive_count)


def _payload_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_count)


def _payload_ratio(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_ratio)


def _payload_decimal(
    field_name: str,
    value: object,
    normalize: Any,
) -> Decimal:
    normalized_string = _payload_string(field_name, value)
    try:
        raw = Decimal(normalized_string)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalize(field_name, raw)
    if str(normalized) != normalized_string:
        raise ValueError(f"{field_name} must use canonical Decimal representation")
    return normalized


def _row_digest(row: ResearchEventSourceClaimMemoryQuorumRow) -> str:
    return _sha256_payload(_row_public_payload(row, include_digest=False))


def _report_digest(report: ResearchEventSourceClaimMemoryQuorumReport) -> str:
    return _sha256_payload(_report_public_payload(report, include_digest=False))


def _sha256_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_row_consistency(
    row: ResearchEventSourceClaimMemoryQuorumRow,
) -> None:
    if row.observation_count <= _ZERO_COUNT:
        raise ValueError("observation_count must be positive")
    if row.agreeing_evidence_count > row.observation_count:
        raise ValueError("agreeing_evidence_count must not exceed observation_count")
    if row.memory_quorum_count > row.agreeing_evidence_count:
        raise ValueError("memory_quorum_count must not exceed agreeing_evidence_count")
    if row.support_ratio != _ratio(
        row.agreeing_evidence_count,
        row.observation_count,
    ):
        raise ValueError("support_ratio must match evidence counts")
    if row.quorum_score != _average(
        (
            row.support_ratio,
            row.average_parse_confidence,
            row.average_memory_confidence,
        ),
    ):
        raise ValueError("quorum_score must match score components")
    canonical_reasons = tuple(
        reason
        for reason in _ROW_REASON_CODE_SEQUENCE
        if reason in row.reason_codes
    )
    if row.reason_codes != canonical_reasons:
        raise ValueError("reason_codes must use the supported canonical sequence")
    expected_status_reason = f"claim_memory_quorum_{row.status}"
    status_reasons = tuple(
        reason for reason in row.reason_codes if reason in _STATUS_REASON_BY_RANK
    )
    if status_reasons != (expected_status_reason,):
        raise ValueError("reason_codes must match status")


def _report_config(
    report: ResearchEventSourceClaimMemoryQuorumReport,
) -> ResearchEventSourceClaimMemoryQuorumConfig:
    return ResearchEventSourceClaimMemoryQuorumConfig(
        config_version=report.config_version,
        min_agreeing_evidence_count=report.min_agreeing_evidence_count,
        min_memory_quorum_count=report.min_memory_quorum_count,
        min_memory_confidence=report.min_memory_confidence,
        watch_quorum_score=report.watch_quorum_score,
        pass_quorum_score=report.pass_quorum_score,
    )


def _validate_report_consistency(
    report: ResearchEventSourceClaimMemoryQuorumReport,
    config: ResearchEventSourceClaimMemoryQuorumConfig,
) -> None:
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
    for item in report.public_payload:
        _require_hard_flags("public payload item", item)
    _reject_unsafe_public_payload("report", report)
    rows = report.rows
    for row in rows:
        _validate_row_consistency(row)
        expected_status = _row_status(
            row.agreeing_evidence_count,
            row.memory_quorum_count,
            row.quorum_score,
            config,
        )
        if row.status != expected_status:
            raise ValueError("row status must match score and quorum thresholds")
        expected_reasons = _row_reason_codes(
            row.agreeing_evidence_count,
            row.memory_quorum_count,
            expected_status,
            config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("row reason_codes must match derived row state")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical status and identifier sequence")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rank values must match canonical row sequence")
    if report.event_claim_count != _count_decimal(len(rows)):
        raise ValueError("event_claim_count must match rows")
    expected_counts = {
        "pass_count": _count_decimal(sum(1 for row in rows if row.status == "pass")),
        "watch_count": _count_decimal(sum(1 for row in rows if row.status == "watch")),
        "block_count": _count_decimal(sum(1 for row in rows if row.status == "block")),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_quorum_score != _average(
        tuple(row.quorum_score for row in rows),
        default=_ZERO_RATIO,
    ):
        raise ValueError("average_quorum_score must match rows")
    if report.status != _rollup_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.status, rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    rows: Sequence[ResearchEventSourceClaimMemoryQuorumRow],
) -> tuple[ResearchEventSourceClaimMemoryQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventSourceClaimMemoryQuorumRow:
            raise ValueError("rows must contain ResearchEventSourceClaimMemoryQuorumRow")
        _require_hard_flags("row", row)
        replace(row)
    keys = tuple((row.event_key, row.claim_key) for row in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate event and claim keys")
    return normalized


def _normalize_public_payload_items(
    items: Sequence[ResearchEventSourceClaimMemoryQuorumPublicPayloadItem],
) -> tuple[ResearchEventSourceClaimMemoryQuorumPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized = tuple(items)
    for item in normalized:
        if type(item) is not ResearchEventSourceClaimMemoryQuorumPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventSourceClaimMemoryQuorumPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        _reject_unsafe_public_payload("public payload item", item)
        replace(item)
    keys = tuple(item.key for item in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return tuple(sorted(normalized, key=lambda item: (item.key, item.value)))


def _normalize_private_material(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("private_material must be a sequence")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not str:
            raise ValueError("private_material items must be strings")
    return normalized


def _normalize_reason_codes(
    value: Sequence[str],
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized = tuple(value)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    for item in normalized:
        _require_public_identifier("reason_code", item)
    return tuple(dict.fromkeys(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a 64-character sha256 hex digest")


def _require_public_identifier(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize_decimal(field_name, raw, _COUNT_QUANTUM)
    if normalized != raw:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _quantize_decimal(field_name, raw, _COUNT_QUANTUM)
    if normalized != raw:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized.is_zero():
        return _ZERO_COUNT
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO_RATIO or raw > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    normalized = _quantize_decimal(field_name, raw, _RATIO_QUANTUM)
    if normalized.is_zero():
        return _ZERO_RATIO
    return normalized


def _quantize_decimal(
    field_name: str,
    value: Decimal,
    quantum: Decimal,
) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(quantum, rounding=ROUND_HALF_UP)
    except DecimalException as exc:
        raise ValueError(f"{field_name} exceeds fixed Decimal bounds") from exc


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value), _COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    try:
        with localcontext(_DECIMAL_CONTEXT):
            value = numerator / denominator
    except DecimalException as exc:
        raise ValueError("ratio exceeds fixed Decimal bounds") from exc
    return _normalize_ratio("ratio", value)


def _average(
    values: tuple[Decimal, ...],
    *,
    default: Decimal = _ZERO_RATIO,
) -> Decimal:
    if not values:
        return default
    try:
        with localcontext(_DECIMAL_CONTEXT):
            total = sum(values, _ZERO_RATIO)
            value = total / _count_decimal(len(values))
    except DecimalException as exc:
        raise ValueError("average exceeds fixed Decimal bounds") from exc
    return _normalize_ratio("average", value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON payload must not contain numeric scalars")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON ready")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for value in _iter_public_strings(payload):
        normalized = value.lower()
        if "://" in normalized or any(
            fragment in normalized for fragment in _BAD_PUBLIC_FRAGMENTS
        ):
            raise ValueError(f"public payload contains restricted raw material: {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            if key == "derived_validation_digest":
                continue
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if isinstance(value, (tuple, list)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_CLAIM_MEMORY_QUORUM_SCORECARD_CONFIG_VERSION",
    "REPORT_STATUSES",
    "ResearchEventSourceClaimMemoryQuorumConfig",
    "ResearchEventSourceClaimMemoryQuorumObservation",
    "ResearchEventSourceClaimMemoryQuorumPublicPayloadItem",
    "ResearchEventSourceClaimMemoryQuorumReport",
    "ResearchEventSourceClaimMemoryQuorumRow",
    "build_research_event_source_claim_memory_quorum_scorecard_report",
    "research_event_source_claim_memory_quorum_scorecard_report_payload",
)
