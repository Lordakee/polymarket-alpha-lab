"""Pure report-only scrapling claim consensus tail diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Iterable, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_CONSENSUS_TAIL_CONFIG_VERSION = (
    "research-source-scrapling-claim-consensus-tail-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_VALUES = frozenset((PASS_STATUS, WATCH_STATUS, BLOCK_STATUS))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_KEY_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "private",
    "auth",
    "wallet",
    "network",
    "database",
    "order",
    "buy",
    "sell",
    "trade",
    "position",
    "recommend",
    "sizing",
    "live",
)
_UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "raw-candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market-slug",
    "question?",
    "dsn",
    "postgres://",
    "wallet",
    "database",
    "order",
    "token",
    "private",
)
_REASON_CODE_SEQUENCE = (
    "low_consensus_watch",
    "low_consensus_block",
    "low_scrapling_confidence_watch",
    "low_scrapling_confidence_block",
    "tail_disagreement_watch",
    "tail_disagreement_block",
    "contradiction_watch",
    "contradiction_block",
    "sparse_family_watch",
    "sparse_evidence_watch",
    "scrapling_claim_consensus_tail_watch",
    "scrapling_claim_consensus_tail_block",
    "scrapling_claim_consensus_tail_pass",
)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimConsensusTailConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_CONSENSUS_TAIL_CONFIG_VERSION
    )
    watch_consensus_score_floor: Decimal = Decimal("0.700000")
    block_consensus_score_floor: Decimal = Decimal("0.450000")
    watch_scrapling_confidence_score_floor: Decimal = Decimal("0.650000")
    block_scrapling_confidence_score_floor: Decimal = Decimal("0.400000")
    watch_tail_disagreement_score: Decimal = Decimal("0.350000")
    block_tail_disagreement_score: Decimal = Decimal("0.700000")
    watch_contradiction_score: Decimal = Decimal("0.250000")
    block_contradiction_score: Decimal = Decimal("0.600000")
    min_family_count: Decimal = Decimal("2.000000")
    min_evidence_count: Decimal = Decimal("3.000000")
    block_watch_signal_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimConsensusTailConfig:
            raise TypeError(
                "ResearchSourceScraplingClaimConsensusTailConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimConsensusTailConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceScraplingClaimConsensusTailConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_CONSENSUS_TAIL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_consensus_score_floor",
            "block_consensus_score_floor",
            "watch_scrapling_confidence_score_floor",
            "block_scrapling_confidence_score_floor",
            "watch_tail_disagreement_score",
            "block_tail_disagreement_score",
            "watch_contradiction_score",
            "block_contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_family_count",
            "min_evidence_count",
            "block_watch_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "block_consensus_score_floor",
            self.watch_consensus_score_floor,
            self.block_consensus_score_floor,
        )
        _require_floor_pair(
            "block_scrapling_confidence_score_floor",
            self.watch_scrapling_confidence_score_floor,
            self.block_scrapling_confidence_score_floor,
        )
        _require_ceiling_pair(
            "block_tail_disagreement_score",
            self.watch_tail_disagreement_score,
            self.block_tail_disagreement_score,
        )
        _require_ceiling_pair(
            "block_contradiction_score",
            self.watch_contradiction_score,
            self.block_contradiction_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimConsensusTailObservation:
    observed_at: datetime
    consensus_score: Decimal
    scrapling_confidence_score: Decimal
    tail_disagreement_score: Decimal
    contradiction_score: Decimal
    family_count: Decimal
    evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimConsensusTailObservation:
            raise TypeError(
                "ResearchSourceScraplingClaimConsensusTailObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimConsensusTailObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceScraplingClaimConsensusTailObservation",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "consensus_score",
            "scrapling_confidence_score",
            "tail_disagreement_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("family_count", "evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimConsensusTailRow:
    row_label: str
    observed_at: datetime
    consensus_score: Decimal
    scrapling_confidence_score: Decimal
    tail_disagreement_score: Decimal
    contradiction_score: Decimal
    family_count: Decimal
    evidence_count: Decimal
    tail_pressure_score: Decimal
    watch_signal_count: Decimal
    weak_consensus: bool
    weak_scrapling_confidence: bool
    tail_disagreement: bool
    contradiction_present: bool
    sparse_family: bool
    sparse_evidence: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimConsensusTailRow:
            raise TypeError(
                "ResearchSourceScraplingClaimConsensusTailRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimConsensusTailRow:
            raise ValueError(
                "row must be exactly ResearchSourceScraplingClaimConsensusTailRow",
            )
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "consensus_score",
            "scrapling_confidence_score",
            "tail_disagreement_score",
            "contradiction_score",
            "tail_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("family_count", "evidence_count", "watch_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "weak_consensus",
            "weak_scrapling_confidence",
            "tail_disagreement",
            "contradiction_present",
            "sparse_family",
            "sparse_evidence",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimConsensusTailReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    weak_consensus_count: Decimal
    weak_scrapling_confidence_count: Decimal
    tail_disagreement_count: Decimal
    contradiction_count: Decimal
    sparse_family_count: Decimal
    sparse_evidence_count: Decimal
    max_tail_pressure_score: Decimal
    min_consensus_score: Decimal | None
    min_scrapling_confidence_score: Decimal | None
    rows: tuple[ResearchSourceScraplingClaimConsensusTailRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimConsensusTailReport:
            raise TypeError(
                "ResearchSourceScraplingClaimConsensusTailReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimConsensusTailReport:
            raise ValueError(
                "report must be exactly ResearchSourceScraplingClaimConsensusTailReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_CONSENSUS_TAIL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "weak_consensus_count",
            "weak_scrapling_confidence_count",
            "tail_disagreement_count",
            "contradiction_count",
            "sparse_family_count",
            "sparse_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_tail_pressure_score",
            _require_ratio_decimal("max_tail_pressure_score", self.max_tail_pressure_score),
        )
        for field_name in ("min_consensus_score", "min_scrapling_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_claim_consensus_tail_report_payload(self)


def build_research_source_scrapling_claim_consensus_tail_report(
    observations: Iterable[ResearchSourceScraplingClaimConsensusTailObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceScraplingClaimConsensusTailConfig | None = None,
) -> ResearchSourceScraplingClaimConsensusTailReport:
    """Build a deterministic local report-only claim consensus tail diagnostic."""

    if config is None:
        config = ResearchSourceScraplingClaimConsensusTailConfig()
    if type(config) is not ResearchSourceScraplingClaimConsensusTailConfig:
        raise ValueError(
            "config must be a ResearchSourceScraplingClaimConsensusTailConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "observation_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(_status_count(rows, PASS_STATUS)),
        "watch_count": _count_decimal(_status_count(rows, WATCH_STATUS)),
        "block_count": _count_decimal(_status_count(rows, BLOCK_STATUS)),
        "weak_consensus_count": _flag_total(rows, "weak_consensus"),
        "weak_scrapling_confidence_count": _flag_total(
            rows,
            "weak_scrapling_confidence",
        ),
        "tail_disagreement_count": _flag_total(rows, "tail_disagreement"),
        "contradiction_count": _flag_total(rows, "contradiction_present"),
        "sparse_family_count": _flag_total(rows, "sparse_family"),
        "sparse_evidence_count": _flag_total(rows, "sparse_evidence"),
        "max_tail_pressure_score": _max_decimal(row.tail_pressure_score for row in rows),
        "min_consensus_score": _min_optional_decimal(
            row.consensus_score for row in rows
        ),
        "min_scrapling_confidence_score": _min_optional_decimal(
            row.scrapling_confidence_score for row in rows
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceScraplingClaimConsensusTailReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_scrapling_claim_consensus_tail_report_payload(
    report: ResearchSourceScraplingClaimConsensusTailReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceScraplingClaimConsensusTailReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchSourceScraplingClaimConsensusTailReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_scrapling_claim_consensus_tail_public_payload(payload)
    return payload


def research_source_scrapling_claim_consensus_tail_report_digest(
    report: ResearchSourceScraplingClaimConsensusTailReport,
) -> str:
    if type(report) is not ResearchSourceScraplingClaimConsensusTailReport:
        raise ValueError(
            "report must be a ResearchSourceScraplingClaimConsensusTailReport",
        )
    _require_hard_flags("report", report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_source_scrapling_claim_consensus_tail_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _build_rows(
    observations: tuple[ResearchSourceScraplingClaimConsensusTailObservation, ...],
    config: ResearchSourceScraplingClaimConsensusTailConfig,
) -> tuple[ResearchSourceScraplingClaimConsensusTailRow, ...]:
    draft_rows = tuple(_row_from_observation(observation, config) for observation in observations)
    sorted_draft_rows = tuple(sorted(draft_rows, key=_row_sort_key_without_label))
    return tuple(
        ResearchSourceScraplingClaimConsensusTailRow(
            row_label=f"redacted-claim-consensus-tail-{index:06d}",
            observed_at=row.observed_at,
            consensus_score=row.consensus_score,
            scrapling_confidence_score=row.scrapling_confidence_score,
            tail_disagreement_score=row.tail_disagreement_score,
            contradiction_score=row.contradiction_score,
            family_count=row.family_count,
            evidence_count=row.evidence_count,
            tail_pressure_score=row.tail_pressure_score,
            watch_signal_count=row.watch_signal_count,
            weak_consensus=row.weak_consensus,
            weak_scrapling_confidence=row.weak_scrapling_confidence,
            tail_disagreement=row.tail_disagreement,
            contradiction_present=row.contradiction_present,
            sparse_family=row.sparse_family,
            sparse_evidence=row.sparse_evidence,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_draft_rows, start=1)
    )


def _row_from_observation(
    observation: ResearchSourceScraplingClaimConsensusTailObservation,
    config: ResearchSourceScraplingClaimConsensusTailConfig,
) -> ResearchSourceScraplingClaimConsensusTailRow:
    consensus_level = _floor_level(
        observation.consensus_score,
        config.watch_consensus_score_floor,
        config.block_consensus_score_floor,
    )
    confidence_level = _floor_level(
        observation.scrapling_confidence_score,
        config.watch_scrapling_confidence_score_floor,
        config.block_scrapling_confidence_score_floor,
    )
    tail_level = _ceiling_level(
        observation.tail_disagreement_score,
        config.watch_tail_disagreement_score,
        config.block_tail_disagreement_score,
    )
    contradiction_level = _ceiling_level(
        observation.contradiction_score,
        config.watch_contradiction_score,
        config.block_contradiction_score,
    )
    sparse_family = observation.family_count < config.min_family_count
    sparse_evidence = observation.evidence_count < config.min_evidence_count
    signal_count = _count_decimal(
        sum(
            1
            for value in (
                consensus_level,
                confidence_level,
                tail_level,
                contradiction_level,
                WATCH_STATUS if sparse_family else None,
                WATCH_STATUS if sparse_evidence else None,
            )
            if value is not None
        ),
    )
    status = _row_status(
        (
            consensus_level,
            confidence_level,
            tail_level,
            contradiction_level,
        ),
        signal_count,
        config,
    )
    return ResearchSourceScraplingClaimConsensusTailRow(
        row_label="redacted-claim-consensus-tail-000000",
        observed_at=observation.observed_at,
        consensus_score=observation.consensus_score,
        scrapling_confidence_score=observation.scrapling_confidence_score,
        tail_disagreement_score=observation.tail_disagreement_score,
        contradiction_score=observation.contradiction_score,
        family_count=observation.family_count,
        evidence_count=observation.evidence_count,
        tail_pressure_score=max(
            observation.tail_disagreement_score,
            observation.contradiction_score,
        ),
        watch_signal_count=signal_count,
        weak_consensus=consensus_level is not None,
        weak_scrapling_confidence=confidence_level is not None,
        tail_disagreement=tail_level is not None,
        contradiction_present=contradiction_level is not None,
        sparse_family=sparse_family,
        sparse_evidence=sparse_evidence,
        status=status,
        reason_codes=_row_reason_codes(
            consensus_level=consensus_level,
            confidence_level=confidence_level,
            tail_level=tail_level,
            contradiction_level=contradiction_level,
            sparse_family=sparse_family,
            sparse_evidence=sparse_evidence,
            status=status,
        ),
    )


def _floor_level(value: Decimal, watch_floor: Decimal, block_floor: Decimal) -> str | None:
    if value <= block_floor:
        return BLOCK_STATUS
    if value < watch_floor:
        return WATCH_STATUS
    return None


def _ceiling_level(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str | None:
    if value >= block_threshold:
        return BLOCK_STATUS
    if value >= watch_threshold:
        return WATCH_STATUS
    return None


def _row_status(
    levels: tuple[str | None, ...],
    signal_count: Decimal,
    config: ResearchSourceScraplingClaimConsensusTailConfig,
) -> str:
    if any(level == BLOCK_STATUS for level in levels):
        return BLOCK_STATUS
    if signal_count >= config.block_watch_signal_count:
        return BLOCK_STATUS
    if signal_count > _ZERO:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    consensus_level: str | None,
    confidence_level: str | None,
    tail_level: str | None,
    contradiction_level: str | None,
    sparse_family: bool,
    sparse_evidence: bool,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_level_code(reason_codes, "low_consensus", consensus_level)
    _append_level_code(reason_codes, "low_scrapling_confidence", confidence_level)
    _append_level_code(reason_codes, "tail_disagreement", tail_level)
    _append_level_code(reason_codes, "contradiction", contradiction_level)
    if sparse_family:
        reason_codes.append("sparse_family_watch")
    if sparse_evidence:
        reason_codes.append("sparse_evidence_watch")
    if status == BLOCK_STATUS:
        reason_codes.append("scrapling_claim_consensus_tail_block")
    elif status == WATCH_STATUS:
        reason_codes.append("scrapling_claim_consensus_tail_watch")
    else:
        reason_codes.append("scrapling_claim_consensus_tail_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_level_code(
    reason_codes: list[str],
    prefix: str,
    level: str | None,
) -> None:
    if level is not None:
        reason_codes.append(f"{prefix}_{level}")


def _row_sort_key_without_label(
    row: ResearchSourceScraplingClaimConsensusTailRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        -row.watch_signal_count,
        -row.tail_pressure_score,
        row.consensus_score,
        row.scrapling_confidence_score,
        -row.tail_disagreement_score,
        -row.contradiction_score,
        row.family_count,
        row.evidence_count,
        row.observed_at,
    )


def _row_sort_key(
    row: ResearchSourceScraplingClaimConsensusTailRow,
) -> tuple[object, ...]:
    return (*_row_sort_key_without_label(row), row.row_label)


def _report_status(
    rows: tuple[ResearchSourceScraplingClaimConsensusTailRow, ...],
) -> str:
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingClaimConsensusTailRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("scrapling_claim_consensus_tail_pass",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(
    row: ResearchSourceScraplingClaimConsensusTailRow,
) -> None:
    expected_signal_count = _count_decimal(
        sum(
            1
            for value in (
                row.weak_consensus,
                row.weak_scrapling_confidence,
                row.tail_disagreement,
                row.contradiction_present,
                row.sparse_family,
                row.sparse_evidence,
            )
            if value is True
        ),
    )
    if row.watch_signal_count != expected_signal_count:
        raise ValueError("watch_signal_count must match row flags")
    if row.tail_pressure_score != max(row.tail_disagreement_score, row.contradiction_score):
        raise ValueError("tail_pressure_score must match row scores")
    if row.status == PASS_STATUS and row.watch_signal_count != _ZERO:
        raise ValueError("pass rows must have no watch signals")
    if row.status in {WATCH_STATUS, BLOCK_STATUS} and row.watch_signal_count == _ZERO:
        raise ValueError("watch and block rows must have watch signals")
    if row.status == PASS_STATUS:
        expected_codes = ("scrapling_claim_consensus_tail_pass",)
    else:
        if not any(code.endswith(row.status) for code in row.reason_codes):
            raise ValueError("status must match reason_codes")
        expected_codes = row.reason_codes
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes must match row status")


def _validate_report_consistency(
    report: ResearchSourceScraplingClaimConsensusTailReport,
) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    for field_name, status in (
        ("pass_count", PASS_STATUS),
        ("watch_count", WATCH_STATUS),
        ("block_count", BLOCK_STATUS),
    ):
        if getattr(report, field_name) != _count_decimal(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    for field_name, row_field in (
        ("weak_consensus_count", "weak_consensus"),
        ("weak_scrapling_confidence_count", "weak_scrapling_confidence"),
        ("tail_disagreement_count", "tail_disagreement"),
        ("contradiction_count", "contradiction_present"),
        ("sparse_family_count", "sparse_family"),
        ("sparse_evidence_count", "sparse_evidence"),
    ):
        if getattr(report, field_name) != _flag_total(report.rows, row_field):
            raise ValueError(f"{field_name} must match rows")
    if report.max_tail_pressure_score != _max_decimal(
        row.tail_pressure_score for row in report.rows
    ):
        raise ValueError("max_tail_pressure_score must match rows")
    if report.min_consensus_score != _min_optional_decimal(
        row.consensus_score for row in report.rows
    ):
        raise ValueError("min_consensus_score must match rows")
    if report.min_scrapling_confidence_score != _min_optional_decimal(
        row.scrapling_confidence_score for row in report.rows
    ):
        raise ValueError("min_scrapling_confidence_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Iterable[ResearchSourceScraplingClaimConsensusTailObservation],
) -> tuple[ResearchSourceScraplingClaimConsensusTailObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchSourceScraplingClaimConsensusTailObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceScraplingClaimConsensusTailObservation",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchSourceScraplingClaimConsensusTailRow],
) -> tuple[ResearchSourceScraplingClaimConsensusTailRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceScraplingClaimConsensusTailRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingClaimConsensusTailRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
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


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_floor_pair(
    block_field_name: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if block_floor >= watch_floor:
        raise ValueError(f"{block_field_name} must be below the watch floor")


def _require_ceiling_pair(
    block_field_name: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed the watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if isinstance(value, datetime) and type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _status_count(
    rows: tuple[ResearchSourceScraplingClaimConsensusTailRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _flag_total(
    rows: tuple[ResearchSourceScraplingClaimConsensusTailRow, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name) is True))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _min_optional_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return min(normalized)


def _status_rank(status: str) -> int:
    return {BLOCK_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}[status]


def _report_values_without_digest(
    report: ResearchSourceScraplingClaimConsensusTailReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: object) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(values),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload must serialize numerics as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
    path: str = "",
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
            path=path,
        )
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose dict surfaces")
        for key, item in value.items():
            key_text = str(key)
            lowered_key = key_text.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_KEY_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public key: {key_text}")
            if key_text in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{key_text} must be True for {label}")
            item_path = f"{path}.{key_text}" if path else key_text
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=item_path,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose sequence surfaces")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=f"{path}[{index}]",
            )
        return
    if isinstance(value, str):
        _reject_unsafe_public_string(path or label, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")


class _PayloadFlags:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


__all__ = (
    "ResearchSourceScraplingClaimConsensusTailConfig",
    "ResearchSourceScraplingClaimConsensusTailObservation",
    "ResearchSourceScraplingClaimConsensusTailRow",
    "ResearchSourceScraplingClaimConsensusTailReport",
    "build_research_source_scrapling_claim_consensus_tail_report",
    "research_source_scrapling_claim_consensus_tail_report_digest",
    "research_source_scrapling_claim_consensus_tail_report_payload",
    "validate_research_source_scrapling_claim_consensus_tail_public_payload",
)
