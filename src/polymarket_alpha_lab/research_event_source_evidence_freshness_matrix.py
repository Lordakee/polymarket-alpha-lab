"""Pure research event source-evidence freshness matrix."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "research-event-source-evidence-freshness-matrix-v0"

STATUSES = ("pass", "watch", "block")
EVIDENCE_ROLES = (
    "official_event_notice",
    "independent_confirmation",
    "market_rules",
    "resolution_update",
    "contradiction_review",
    "data_snapshot",
)

PASS_REASON = "freshness_matrix_pass"
WATCH_REASON = "freshness_matrix_watch"
BLOCK_REASON = "freshness_matrix_block"
EMPTY_REASON = "no_event_evidence"
REFRESH_REASON = "freshness_refresh_needed"
STALE_REASON = "stale_evidence_present"
NO_FRESH_REASON = "no_fresh_evidence"
COVERAGE_PASS_REASON = "coverage_below_pass_floor"
COVERAGE_WATCH_REASON = "coverage_below_watch_floor"
CONFLICT_REASON = "conflict_signal_present"
HARD_FLAG_REASON = "hard_collection_flag_present"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    EMPTY_REASON,
    COVERAGE_WATCH_REASON,
    REFRESH_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    HARD_FLAG_REASON,
    NO_FRESH_REASON,
    STALE_REASON,
    COVERAGE_PASS_REASON,
    CONFLICT_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw-candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source_url",
    "source_text",
    "source_reference",
    "http://",
    "https://",
    "url",
    "dsn",
    "table",
    "token",
    "auth",
    "live",
    "network",
    "persist",
    "signing",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "position",
    "buy",
    "sell",
    "recommend",
)


@dataclass(frozen=True)
class ResearchEventSourceEvidenceFreshnessMatrixConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    min_evidence_count: Decimal = Decimal("3")
    min_source_family_count: Decimal = Decimal("2")
    min_required_role_count: Decimal = Decimal("2")
    pass_coverage_score: Decimal = Decimal("0.800000")
    watch_coverage_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "min_evidence_count",
            "min_source_family_count",
            "min_required_role_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_coverage_score", "watch_coverage_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_coverage_score <= self.watch_coverage_score:
            raise ValueError("pass_coverage_score must be greater than watch_coverage_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceEvidenceFreshnessMatrixObservation:
    event_key: str
    evidence_key: str
    source_family: str
    evidence_role: str
    observed_at: datetime
    conflict_signal: bool = False
    hard_block_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_key", self.event_key)
        _require_canonical_string("evidence_key", self.evidence_key)
        _require_canonical_string("source_family", self.source_family)
        _require_member("evidence_role", self.evidence_role, EVIDENCE_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.conflict_signal) is not bool:
            raise ValueError("conflict_signal must be a bool")
        if type(self.hard_block_flag) is not bool:
            raise ValueError("hard_block_flag must be a bool")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceEvidenceFreshnessMatrixRow:
    event_public_id: str
    evidence_count: Decimal
    source_family_count: Decimal
    required_role_count: Decimal
    fresh_evidence_count: Decimal
    stale_evidence_count: Decimal
    conflict_signal_count: Decimal
    hard_flag_count: Decimal
    latest_observed_at: datetime
    latest_evidence_age_seconds: Decimal
    oldest_evidence_age_seconds: Decimal
    freshness_score: Decimal
    coverage_score: Decimal
    conflict_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_public_id", self.event_public_id)
        for field_name in (
            "evidence_count",
            "source_family_count",
            "required_role_count",
            "fresh_evidence_count",
            "stale_evidence_count",
            "conflict_signal_count",
            "hard_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "latest_evidence_age_seconds",
            "oldest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_score",
            "coverage_score",
            "conflict_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODE_PRIORITY)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventSourceEvidenceFreshnessMatrixReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_freshness_score: Decimal | None
    average_coverage_score: Decimal | None
    average_conflict_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchEventSourceEvidenceFreshnessMatrixRow, ...]
    reason_code_counts: tuple[
        ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_freshness_score",
            "average_coverage_score",
            "average_conflict_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_public_digest(self)
        _reject_unsafe_public_payload("report", _payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_source_evidence_freshness_matrix_public_payload(self)


def build_research_event_source_evidence_freshness_matrix_report(
    observations: Iterable[ResearchEventSourceEvidenceFreshnessMatrixObservation],
    *,
    config: ResearchEventSourceEvidenceFreshnessMatrixConfig,
    generated_at: datetime,
) -> ResearchEventSourceEvidenceFreshnessMatrixReport:
    if type(config) is not ResearchEventSourceEvidenceFreshnessMatrixConfig:
        raise ValueError(
            "config must be a ResearchEventSourceEvidenceFreshnessMatrixConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_observations(observations, generated_at=generated_at_utc)

    grouped: dict[str, list[ResearchEventSourceEvidenceFreshnessMatrixObservation]] = {}
    for row in rows:
        grouped.setdefault(row.event_key, []).append(row)

    event_public_ids = {
        event_key: f"event-{index:03d}"
        for index, event_key in enumerate(sorted(grouped), start=1)
    }
    matrix_rows = tuple(
        _row_for_event(
            event_public_id=event_public_ids[event_key],
            observations=tuple(grouped[event_key]),
            config=config,
            generated_at=generated_at_utc,
        )
        for event_key in sorted(grouped)
    )
    reason_codes = _report_reason_codes(matrix_rows)
    return ResearchEventSourceEvidenceFreshnessMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(matrix_rows)),
        evidence_count=sum((row.evidence_count for row in matrix_rows), ZERO),
        pass_count=_count(_status_count(matrix_rows, "pass")),
        watch_count=_count(_status_count(matrix_rows, "watch")),
        block_count=_count(_status_count(matrix_rows, "block")),
        average_freshness_score=_average_score(row.freshness_score for row in matrix_rows),
        average_coverage_score=_average_score(row.coverage_score for row in matrix_rows),
        average_conflict_risk_score=_average_score(
            (row.conflict_risk_score for row in matrix_rows),
        ),
        status=_status_from_reason_codes(reason_codes),
        rows=matrix_rows,
        reason_code_counts=_reason_code_counts(matrix_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_source_evidence_freshness_matrix_public_payload(
    value: ResearchEventSourceEvidenceFreshnessMatrixReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventSourceEvidenceFreshnessMatrixReport:
        _validate_report(value)
        _validate_public_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEventSourceEvidenceFreshnessMatrixReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _validate_public_payload(payload)
    return dict(payload)


def research_event_source_evidence_freshness_matrix_public_digest(
    value: ResearchEventSourceEvidenceFreshnessMatrixReport | dict[str, Any],
) -> str:
    payload = research_event_source_evidence_freshness_matrix_public_payload(value)
    digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", digest)
    return digest


def _row_for_event(
    *,
    event_public_id: str,
    observations: tuple[ResearchEventSourceEvidenceFreshnessMatrixObservation, ...],
    config: ResearchEventSourceEvidenceFreshnessMatrixConfig,
    generated_at: datetime,
) -> ResearchEventSourceEvidenceFreshnessMatrixRow:
    rows = tuple(sorted(observations, key=_observation_sort_key))
    ages = tuple(_seconds_between(row.observed_at, generated_at) for row in rows)
    evidence_count = len(rows)
    source_family_count = len({row.source_family for row in rows})
    required_role_count = len({row.evidence_role for row in rows})
    fresh_count = sum(1 for age in ages if age <= config.fresh_age_seconds)
    stale_count = sum(1 for age in ages if age >= config.stale_age_seconds)
    conflict_count = sum(1 for row in rows if row.conflict_signal)
    hard_flag_count = sum(1 for row in rows if row.hard_block_flag)
    freshness_score = _average_score(
        _freshness_score(
            age,
            fresh_age_seconds=config.fresh_age_seconds,
            stale_age_seconds=config.stale_age_seconds,
        )
        for age in ages
    )
    coverage_score = _coverage_score(
        evidence_count=evidence_count,
        source_family_count=source_family_count,
        required_role_count=required_role_count,
        config=config,
    )
    conflict_risk_score = _conflict_risk_score(
        evidence_count=evidence_count,
        conflict_count=conflict_count,
        hard_flag_count=hard_flag_count,
    )
    if freshness_score is None:
        raise ValueError("freshness_score must be available for event rows")
    reason_codes = _row_reason_codes(
        coverage_score=coverage_score,
        freshness_score=freshness_score,
        fresh_count=fresh_count,
        stale_count=stale_count,
        conflict_count=conflict_count,
        hard_flag_count=hard_flag_count,
        config=config,
    )
    return ResearchEventSourceEvidenceFreshnessMatrixRow(
        event_public_id=event_public_id,
        evidence_count=_count(evidence_count),
        source_family_count=_count(source_family_count),
        required_role_count=_count(required_role_count),
        fresh_evidence_count=_count(fresh_count),
        stale_evidence_count=_count(stale_count),
        conflict_signal_count=_count(conflict_count),
        hard_flag_count=_count(hard_flag_count),
        latest_observed_at=max(row.observed_at for row in rows),
        latest_evidence_age_seconds=min(ages),
        oldest_evidence_age_seconds=max(ages),
        freshness_score=freshness_score,
        coverage_score=coverage_score,
        conflict_risk_score=conflict_risk_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    coverage_score: Decimal,
    freshness_score: Decimal,
    fresh_count: int,
    stale_count: int,
    conflict_count: int,
    hard_flag_count: int,
    config: ResearchEventSourceEvidenceFreshnessMatrixConfig,
) -> tuple[str, ...]:
    fresh_coverage_requirements_met = (
        _count(fresh_count) >= config.min_evidence_count
        and coverage_score >= config.pass_coverage_score
    )
    if hard_flag_count > 0 or coverage_score < config.watch_coverage_score:
        status_reason = BLOCK_REASON
    elif (
        fresh_coverage_requirements_met
        and freshness_score == ONE
        and conflict_count == 0
    ):
        status_reason = PASS_REASON
    else:
        status_reason = WATCH_REASON

    reasons: list[str] = [status_reason]
    if freshness_score < ONE and not (stale_count > 0 and fresh_count == 0):
        reasons.append(REFRESH_REASON)
    if stale_count > 0:
        reasons.append(STALE_REASON)
    if stale_count > 0 and fresh_count == 0:
        reasons.append(NO_FRESH_REASON)
    if coverage_score < config.watch_coverage_score:
        reasons.append(COVERAGE_WATCH_REASON)
    elif coverage_score < config.pass_coverage_score:
        reasons.append(COVERAGE_PASS_REASON)
    if conflict_count > 0 and hard_flag_count == 0:
        reasons.append(CONFLICT_REASON)
    if hard_flag_count > 0:
        reasons.append(HARD_FLAG_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchEventSourceEvidenceFreshnessMatrixRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if all(row.status == "pass" for row in rows):
        return (PASS_REASON,)
    status_reason = BLOCK_REASON if any(row.status == "block" for row in rows) else WATCH_REASON
    detail_codes = tuple(
        code
        for row in rows
        for code in row.reason_codes
        if code not in (PASS_REASON, WATCH_REASON, BLOCK_REASON)
    )
    return _normalize_reason_codes(
        "reason_codes",
        (status_reason, *detail_codes),
    )


def _reason_code_counts(
    rows: tuple[ResearchEventSourceEvidenceFreshnessMatrixRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_observations(
    value: Iterable[ResearchEventSourceEvidenceFreshnessMatrixObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchEventSourceEvidenceFreshnessMatrixObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventSourceEvidenceFreshnessMatrixObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventSourceEvidenceFreshnessMatrixObservation values",
            )
        _require_hard_flags("observation", row)
        marker = (row.event_key, row.evidence_key)
        if marker in seen:
            raise ValueError("event_key and evidence_key pairs must be unique")
        seen.add(marker)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(sorted(rows, key=_observation_sort_key))


def _normalize_rows(
    value: Iterable[ResearchEventSourceEvidenceFreshnessMatrixRow],
) -> tuple[ResearchEventSourceEvidenceFreshnessMatrixRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventSourceEvidenceFreshnessMatrixRow:
            raise ValueError(
                "rows must contain ResearchEventSourceEvidenceFreshnessMatrixRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_public_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_public_id")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount],
) -> tuple[ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(
        sorted(counts, key=lambda count: REASON_CODE_PRIORITY.index(count.reason_code)),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _validate_row(row: ResearchEventSourceEvidenceFreshnessMatrixRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    for field_name in (
        "source_family_count",
        "required_role_count",
        "fresh_evidence_count",
        "stale_evidence_count",
        "conflict_signal_count",
        "hard_flag_count",
    ):
        if getattr(row, field_name) > row.evidence_count:
            raise ValueError(f"{field_name} must not exceed evidence_count")
    if row.latest_evidence_age_seconds > row.oldest_evidence_age_seconds:
        raise ValueError(
            "latest_evidence_age_seconds must not exceed oldest_evidence_age_seconds",
        )
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchEventSourceEvidenceFreshnessMatrixReport,
) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in rows), ZERO):
        raise ValueError("evidence_count must match rows")
    for status_name, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _count(_status_count(rows, status_name)):
            raise ValueError(f"{field_name} must match rows")
    if report.average_freshness_score != _average_score(
        (row.freshness_score for row in rows),
    ):
        raise ValueError("average_freshness_score must match rows")
    if report.average_coverage_score != _average_score(row.coverage_score for row in rows):
        raise ValueError("average_coverage_score must match rows")
    if report.average_conflict_risk_score != _average_score(
        (row.conflict_risk_score for row in rows),
    ):
        raise ValueError("average_conflict_risk_score must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("public payload", payload)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", digest)
    if digest != _public_digest(payload):
        raise ValueError("public_digest must match public payload")


def _set_or_validate_public_digest(
    report: ResearchEventSourceEvidenceFreshnessMatrixReport,
) -> None:
    current = report.public_digest
    expected = _public_digest(report)
    if current == "":
        object.__setattr__(report, "public_digest", expected)
        return
    _require_sha256_digest("public_digest", current)
    if current != expected:
        raise ValueError("public_digest must match report fields")


def _validate_public_digest(
    report: ResearchEventSourceEvidenceFreshnessMatrixReport,
) -> None:
    current = _require_sha256_digest("public_digest", report.public_digest)
    if current != _public_digest(report):
        raise ValueError("public_digest must match report fields")


def _public_digest(value: object) -> str:
    encoded = json.dumps(
        _without_public_digest(_payload_value(value)),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_public_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_public_digest(item)
            for key, item in value.items()
            if key != "public_digest"
        }
    if type(value) is list:
        return [_without_public_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _coverage_score(
    *,
    evidence_count: int,
    source_family_count: int,
    required_role_count: int,
    config: ResearchEventSourceEvidenceFreshnessMatrixConfig,
) -> Decimal:
    ratios = (
        min(ONE, _count(evidence_count) / config.min_evidence_count),
        min(ONE, _count(source_family_count) / config.min_source_family_count),
        min(ONE, _count(required_role_count) / config.min_required_role_count),
    )
    return _quantize(sum(ratios, ZERO) / Decimal(len(ratios)))


def _freshness_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE
    if age_seconds >= stale_age_seconds:
        return ZERO
    return _quantize(ONE - (age_seconds / stale_age_seconds))


def _conflict_risk_score(
    *,
    evidence_count: int,
    conflict_count: int,
    hard_flag_count: int,
) -> Decimal:
    if evidence_count <= 0:
        return ZERO
    return _quantize(
        min(ONE, _count(conflict_count + hard_flag_count) / _count(evidence_count)),
    )


def _average_score(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _status_count(
    rows: tuple[ResearchEventSourceEvidenceFreshnessMatrixRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes or reason_codes == (EMPTY_REASON,):
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    status_reasons = [code for code in codes if code in (PASS_REASON, WATCH_REASON, BLOCK_REASON)]
    if len(set(status_reasons)) > 1:
        raise ValueError(f"{field_name} must contain only one status reason")
    if PASS_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if EMPTY_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} empty reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _observation_sort_key(
    row: ResearchEventSourceEvidenceFreshnessMatrixObservation,
) -> tuple[str, str, str, str]:
    return (row.event_key, row.source_family, row.evidence_role, row.evidence_key)


__all__ = (
    "ResearchEventSourceEvidenceFreshnessMatrixConfig",
    "ResearchEventSourceEvidenceFreshnessMatrixObservation",
    "ResearchEventSourceEvidenceFreshnessMatrixReasonCodeCount",
    "ResearchEventSourceEvidenceFreshnessMatrixReport",
    "ResearchEventSourceEvidenceFreshnessMatrixRow",
    "build_research_event_source_evidence_freshness_matrix_report",
    "research_event_source_evidence_freshness_matrix_public_digest",
    "research_event_source_evidence_freshness_matrix_public_payload",
)
