"""Pure report-only source claim recheck latency quorum report."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_RECHECK_LATENCY_QUORUM_REPORT_CONFIG_VERSION = (
    "research-source-claim-recheck-latency-quorum-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_THREE = Decimal("3.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
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
    "sizing",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchSourceClaimRecheckLatencyQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_RECHECK_LATENCY_QUORUM_REPORT_CONFIG_VERSION
    )
    watch_recheck_latency_seconds: Decimal = Decimal("900.000000")
    block_recheck_latency_seconds: Decimal = Decimal("3600.000000")
    watch_quorum_ratio: Decimal = Decimal("0.750000")
    block_quorum_ratio: Decimal = Decimal("0.500000")
    watch_conflict_ratio: Decimal = Decimal("0.250000")
    block_conflict_ratio: Decimal = Decimal("0.500000")
    watch_recheck_latency_quorum_score: Decimal = Decimal("0.250000")
    block_recheck_latency_quorum_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimRecheckLatencyQuorumConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimRecheckLatencyQuorumConfig:
            raise ValueError(
                "config must be exactly ResearchSourceClaimRecheckLatencyQuorumConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_RECHECK_LATENCY_QUORUM_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_recheck_latency_seconds",
            "block_recheck_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_quorum_ratio",
            "block_quorum_ratio",
            "watch_conflict_ratio",
            "block_conflict_ratio",
            "watch_recheck_latency_quorum_score",
            "block_recheck_latency_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_recheck_latency_seconds <= self.watch_recheck_latency_seconds:
            raise ValueError(
                "block_recheck_latency_seconds must exceed "
                "watch_recheck_latency_seconds",
            )
        if self.block_quorum_ratio >= self.watch_quorum_ratio:
            raise ValueError("block_quorum_ratio must be below watch_quorum_ratio")
        if self.block_conflict_ratio < self.watch_conflict_ratio:
            raise ValueError("block_conflict_ratio must be at least watch_conflict_ratio")
        if (
            self.block_recheck_latency_quorum_score
            <= self.watch_recheck_latency_quorum_score
        ):
            raise ValueError(
                "block_recheck_latency_quorum_score must exceed "
                "watch_recheck_latency_quorum_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimRecheckLatencyQuorumInput:
    claim_bucket: str
    evidence_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    recheck_requested_at: datetime
    quorum_reached_at: datetime | None
    supporting_recheck_count: Decimal
    required_quorum_count: Decimal
    conflicting_recheck_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimRecheckLatencyQuorumInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimRecheckLatencyQuorumInput:
            raise ValueError(
                "input must be exactly ResearchSourceClaimRecheckLatencyQuorumInput",
            )
        for field_name in ("claim_bucket", "evidence_bucket"):
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
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
        object.__setattr__(
            self,
            "quorum_reached_at",
            _optional_as_utc("quorum_reached_at", self.quorum_reached_at),
        )
        object.__setattr__(
            self,
            "supporting_recheck_count",
            _require_nonnegative_whole_decimal(
                "supporting_recheck_count",
                self.supporting_recheck_count,
            ),
        )
        object.__setattr__(
            self,
            "required_quorum_count",
            _require_positive_whole_decimal(
                "required_quorum_count",
                self.required_quorum_count,
            ),
        )
        object.__setattr__(
            self,
            "conflicting_recheck_count",
            _require_nonnegative_whole_decimal(
                "conflicting_recheck_count",
                self.conflicting_recheck_count,
            ),
        )
        if (
            self.quorum_reached_at is not None
            and self.quorum_reached_at < self.recheck_requested_at
        ):
            raise ValueError(
                "quorum_reached_at must be at or after recheck_requested_at",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimRecheckLatencyQuorumRow:
    claim_bucket: str
    evidence_bucket: str
    recheck_latency_seconds: Decimal
    latency_pressure_score: Decimal
    supporting_recheck_count: Decimal
    required_quorum_count: Decimal
    conflicting_recheck_count: Decimal
    total_recheck_count: Decimal
    quorum_ratio: Decimal
    quorum_gap_score: Decimal
    conflict_ratio: Decimal
    recheck_latency_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimRecheckLatencyQuorumRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimRecheckLatencyQuorumRow:
            raise ValueError(
                "row must be exactly ResearchSourceClaimRecheckLatencyQuorumRow",
            )
        for field_name in ("claim_bucket", "evidence_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recheck_latency_seconds",
            _require_nonnegative_decimal(
                "recheck_latency_seconds",
                self.recheck_latency_seconds,
            ),
        )
        for field_name in (
            "supporting_recheck_count",
            "required_quorum_count",
            "conflicting_recheck_count",
            "total_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_quorum_count <= _ZERO:
            raise ValueError("required_quorum_count must be positive")
        for field_name in (
            "latency_pressure_score",
            "quorum_ratio",
            "quorum_gap_score",
            "conflict_ratio",
            "recheck_latency_quorum_score",
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
class ResearchSourceClaimRecheckLatencyQuorumReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    delayed_recheck_count: Decimal
    quorum_gap_count: Decimal
    conflict_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recheck_latency_seconds: Decimal
    average_quorum_ratio: Decimal
    max_recheck_latency_quorum_score: Decimal
    status: str
    rows: tuple[ResearchSourceClaimRecheckLatencyQuorumRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimRecheckLatencyQuorumReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimRecheckLatencyQuorumReport:
            raise ValueError(
                "report must be exactly ResearchSourceClaimRecheckLatencyQuorumReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_RECHECK_LATENCY_QUORUM_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "delayed_recheck_count",
            "quorum_gap_count",
            "conflict_count",
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
            "average_recheck_latency_seconds",
            _require_nonnegative_decimal(
                "average_recheck_latency_seconds",
                self.average_recheck_latency_seconds,
            ),
        )
        for field_name in (
            "average_quorum_ratio",
            "max_recheck_latency_quorum_score",
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


def build_research_source_claim_recheck_latency_quorum_report(
    candidates: Sequence[ResearchSourceClaimRecheckLatencyQuorumInput],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimRecheckLatencyQuorumConfig | None = None,
) -> ResearchSourceClaimRecheckLatencyQuorumReport:
    if config is None:
        config = ResearchSourceClaimRecheckLatencyQuorumConfig()
    if type(config) is not ResearchSourceClaimRecheckLatencyQuorumConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimRecheckLatencyQuorumConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for item in normalized_candidates:
        if item.recheck_requested_at > generated_at:
            raise ValueError("recheck_requested_at must not be after generated_at")
        if item.quorum_reached_at is not None and item.quorum_reached_at > generated_at:
            raise ValueError("quorum_reached_at must not be after generated_at")
    rows = _normalize_rows(
        tuple(_row_for_input(item, config, generated_at) for item in normalized_candidates),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "row_count": _decimal_count(len(rows)),
        "delayed_recheck_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.recheck_latency_seconds >= config.watch_recheck_latency_seconds
            ),
        ),
        "quorum_gap_count": _decimal_count(
            sum(1 for row in rows if row.quorum_ratio < config.watch_quorum_ratio),
        ),
        "conflict_count": _decimal_count(
            sum(1 for row in rows if row.conflict_ratio >= config.watch_conflict_ratio),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_recheck_latency_seconds": _average(
            tuple(row.recheck_latency_seconds for row in rows),
        ),
        "average_quorum_ratio": _average(tuple(row.quorum_ratio for row in rows)),
        "max_recheck_latency_quorum_score": max(
            (row.recheck_latency_quorum_score for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimRecheckLatencyQuorumReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_recheck_latency_quorum_report_payload(
    report: ResearchSourceClaimRecheckLatencyQuorumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceClaimRecheckLatencyQuorumReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError(
            "report must be a ResearchSourceClaimRecheckLatencyQuorumReport",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
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
    item: ResearchSourceClaimRecheckLatencyQuorumInput,
    config: ResearchSourceClaimRecheckLatencyQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceClaimRecheckLatencyQuorumRow:
    reached_at = item.quorum_reached_at if item.quorum_reached_at is not None else generated_at
    latency_seconds = _seconds_between(reached_at, item.recheck_requested_at)
    total_rechecks = _quantize(item.supporting_recheck_count + item.conflicting_recheck_count)
    latency_pressure = _pressure(latency_seconds, config.block_recheck_latency_seconds)
    quorum_ratio = _clamp_ratio(item.supporting_recheck_count / item.required_quorum_count)
    quorum_gap = _clamp_ratio(_ONE - quorum_ratio)
    conflict_ratio = _ZERO if total_rechecks == _ZERO else _clamp_ratio(
        item.conflicting_recheck_count / total_rechecks,
    )
    score = _average((latency_pressure, quorum_gap, conflict_ratio))
    status = _row_status(
        recheck_latency_seconds=latency_seconds,
        quorum_ratio=quorum_ratio,
        conflict_ratio=conflict_ratio,
        recheck_latency_quorum_score=score,
        config=config,
    )
    return ResearchSourceClaimRecheckLatencyQuorumRow(
        claim_bucket=item.claim_bucket,
        evidence_bucket=item.evidence_bucket,
        recheck_latency_seconds=latency_seconds,
        latency_pressure_score=latency_pressure,
        supporting_recheck_count=item.supporting_recheck_count,
        required_quorum_count=item.required_quorum_count,
        conflicting_recheck_count=item.conflicting_recheck_count,
        total_recheck_count=total_rechecks,
        quorum_ratio=quorum_ratio,
        quorum_gap_score=quorum_gap,
        conflict_ratio=conflict_ratio,
        recheck_latency_quorum_score=score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            recheck_latency_seconds=latency_seconds,
            quorum_ratio=quorum_ratio,
            conflict_ratio=conflict_ratio,
            config=config,
        ),
    )


def _row_status(
    *,
    recheck_latency_seconds: Decimal,
    quorum_ratio: Decimal,
    conflict_ratio: Decimal,
    recheck_latency_quorum_score: Decimal,
    config: ResearchSourceClaimRecheckLatencyQuorumConfig,
) -> str:
    if (
        recheck_latency_quorum_score >= config.block_recheck_latency_quorum_score
        or recheck_latency_seconds >= config.block_recheck_latency_seconds
        or quorum_ratio < config.block_quorum_ratio
        or conflict_ratio >= config.block_conflict_ratio
    ):
        return "block"
    if (
        recheck_latency_quorum_score >= config.watch_recheck_latency_quorum_score
        or recheck_latency_seconds >= config.watch_recheck_latency_seconds
        or quorum_ratio < config.watch_quorum_ratio
        or conflict_ratio >= config.watch_conflict_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchSourceClaimRecheckLatencyQuorumInput,
    status: str,
    recheck_latency_seconds: Decimal,
    quorum_ratio: Decimal,
    conflict_ratio: Decimal,
    config: ResearchSourceClaimRecheckLatencyQuorumConfig,
) -> tuple[str, ...]:
    reason_codes = {f"claim_recheck_latency_quorum_{status}"}
    if recheck_latency_seconds >= config.block_recheck_latency_seconds:
        reason_codes.add("recheck_latency_block")
    elif recheck_latency_seconds >= config.watch_recheck_latency_seconds:
        reason_codes.add("recheck_latency_watch")
    else:
        reason_codes.add("recheck_latency_clear")
    if quorum_ratio < config.block_quorum_ratio:
        reason_codes.add("recheck_quorum_block")
    elif quorum_ratio < config.watch_quorum_ratio:
        reason_codes.add("recheck_quorum_watch")
    else:
        reason_codes.add("recheck_quorum_clear")
    if conflict_ratio >= config.block_conflict_ratio:
        reason_codes.add("recheck_conflict_block")
    elif conflict_ratio >= config.watch_conflict_ratio:
        reason_codes.add("recheck_conflict_watch")
    else:
        reason_codes.add("recheck_conflict_clear")
    for reason_code in item.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_candidates(
    candidates: Sequence[ResearchSourceClaimRecheckLatencyQuorumInput],
) -> tuple[ResearchSourceClaimRecheckLatencyQuorumInput, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise ValueError("candidates must be a sequence")
    normalized: list[ResearchSourceClaimRecheckLatencyQuorumInput] = []
    seen: set[tuple[str, str]] = set()
    for item in candidates:
        if type(item) is not ResearchSourceClaimRecheckLatencyQuorumInput:
            raise ValueError(
                "candidate must be a ResearchSourceClaimRecheckLatencyQuorumInput",
            )
        _require_hard_flags("candidate", item)
        key = (item.claim_bucket, item.evidence_bucket)
        if key in seen:
            raise ValueError("duplicate claim_bucket and evidence_bucket pair")
        seen.add(key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.claim_bucket, item.evidence_bucket)))


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimRecheckLatencyQuorumRow],
) -> tuple[ResearchSourceClaimRecheckLatencyQuorumRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimRecheckLatencyQuorumRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimRecheckLatencyQuorumRow:
            raise ValueError("row must be a ResearchSourceClaimRecheckLatencyQuorumRow")
        _require_hard_flags("row", row)
        key = (row.claim_bucket, row.evidence_bucket)
        if key in seen:
            raise ValueError("duplicate row claim_bucket and evidence_bucket pair")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceClaimRecheckLatencyQuorumRow,
) -> tuple[Decimal, int, str, str]:
    return (
        -row.recheck_latency_quorum_score,
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.claim_bucket,
        row.evidence_bucket,
    )


def _report_reason_codes(
    rows: Sequence[ResearchSourceClaimRecheckLatencyQuorumRow],
) -> tuple[str, ...]:
    if not rows:
        return ("claim_recheck_latency_quorum_empty",)
    reason_codes = {f"claim_recheck_latency_quorum_{_report_status(rows)}"}
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _status_count(
    rows: Sequence[ResearchSourceClaimRecheckLatencyQuorumRow],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_status(rows: Sequence[ResearchSourceClaimRecheckLatencyQuorumRow]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _average(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _pressure(value: Decimal, block_value: Decimal) -> Decimal:
    if block_value <= _ZERO:
        raise ValueError("block_value must be positive")
    return _clamp_ratio(value / block_value)


def _validate_row_consistency(row: ResearchSourceClaimRecheckLatencyQuorumRow) -> None:
    total_rechecks = _quantize(
        row.supporting_recheck_count + row.conflicting_recheck_count,
    )
    if row.total_recheck_count != total_rechecks:
        raise ValueError("total_recheck_count must match support and conflict counts")
    expected_quorum_ratio = _clamp_ratio(
        row.supporting_recheck_count / row.required_quorum_count,
    )
    if row.quorum_ratio != expected_quorum_ratio:
        raise ValueError("quorum_ratio must match support and required counts")
    if row.quorum_gap_score != _quantize(_ONE - row.quorum_ratio):
        raise ValueError("quorum_gap_score must equal quorum gap")
    expected_conflict_ratio = _ZERO if row.total_recheck_count == _ZERO else _clamp_ratio(
        row.conflicting_recheck_count / row.total_recheck_count,
    )
    if row.conflict_ratio != expected_conflict_ratio:
        raise ValueError("conflict_ratio must match conflict and total counts")
    expected_score = _average(
        (
            row.latency_pressure_score,
            row.quorum_gap_score,
            row.conflict_ratio,
        ),
    )
    if row.recheck_latency_quorum_score != expected_score:
        raise ValueError("recheck_latency_quorum_score must match component scores")


def _validate_report_consistency(
    report: ResearchSourceClaimRecheckLatencyQuorumReport,
) -> None:
    rows = report.rows
    expected_counts = {
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_recheck_latency_seconds != _average(
        tuple(row.recheck_latency_seconds for row in rows),
    ):
        raise ValueError("average_recheck_latency_seconds must match rows")
    if report.average_quorum_ratio != _average(tuple(row.quorum_ratio for row in rows)):
        raise ValueError("average_quorum_ratio must match rows")
    if report.max_recheck_latency_quorum_score != max(
        (row.recheck_latency_quorum_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_recheck_latency_quorum_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_values_without_digest(
    row: ResearchSourceClaimRecheckLatencyQuorumRow,
) -> dict[str, object]:
    values = asdict(row)
    values.pop("derived_validation_digest")
    return values


def _report_values_without_digest(
    report: ResearchSourceClaimRecheckLatencyQuorumReport,
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


def _validate_row_digest(row: ResearchSourceClaimRecheckLatencyQuorumRow) -> None:
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


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
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
    "DEFAULT_RESEARCH_SOURCE_CLAIM_RECHECK_LATENCY_QUORUM_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimRecheckLatencyQuorumConfig",
    "ResearchSourceClaimRecheckLatencyQuorumInput",
    "ResearchSourceClaimRecheckLatencyQuorumReport",
    "ResearchSourceClaimRecheckLatencyQuorumRow",
    "build_research_source_claim_recheck_latency_quorum_report",
    "research_source_claim_recheck_latency_quorum_report_payload",
)
