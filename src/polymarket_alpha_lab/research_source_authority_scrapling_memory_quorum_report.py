from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_MEMORY_QUORUM_CONFIG_VERSION = (
    "research-source-authority-scrapling-memory-quorum-report-v0"
)

ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ROW_STATUSES

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_COUNT_ZERO = Decimal("0")
_COUNT_ONE = Decimal("1")
_SIX_PLACES = Decimal("0.000001")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_HEX = frozenset("0123456789abcdef")
_PUBLIC_DENY_FRAGMENTS = (
    "candidate",
    "market",
    "sourceurl",
    "url",
    "rawtext",
    "text",
    "dsn",
    "table",
    "token",
    "auth",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
    "execution",
    "execute",
    "buy",
    "sell",
    "cancel",
    "sign",
    "submit",
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "memory_count",
        "subject_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_score",
        "report_status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "subject_digest",
        "locator_digest",
        "finding_count",
        "family_count",
        "quorum_weight",
        "conflict_weight",
        "weighted_score",
        "row_status",
        "latest_observed_at",
        "latest_age_seconds",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingMemoryQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_MEMORY_QUORUM_CONFIG_VERSION
    )
    min_pass_score: Decimal = Decimal("0.750000")
    min_watch_score: Decimal = Decimal("0.500000")
    min_pass_family_count: Decimal = Decimal("2")
    min_pass_quorum_weight: Decimal = Decimal("2.000000")
    max_stale_age_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingMemoryQuorumConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceAuthorityScraplingMemoryQuorumConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_MEMORY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_pass_score", "min_watch_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_score > self.min_pass_score:
            raise ValueError("min_watch_score must not exceed min_pass_score")
        for field_name in (
            "min_pass_family_count",
            "min_pass_quorum_weight",
            "max_stale_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingMemoryQuorumFinding:
    private_subject_ref: str
    private_locator_ref: str
    family_ref: str
    observed_at: datetime
    authority_score: Decimal
    support_weight: Decimal
    conflict_weight: Decimal = _ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingMemoryQuorumFinding:
            raise ValueError(
                "finding must be exactly "
                "ResearchSourceAuthorityScraplingMemoryQuorumFinding",
            )
        for field_name in ("private_subject_ref", "private_locator_ref", "family_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        for field_name in ("support_weight", "conflict_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("finding", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingMemoryQuorumRow:
    subject_digest: str
    locator_digest: str
    finding_count: Decimal
    family_count: Decimal
    quorum_weight: Decimal
    conflict_weight: Decimal
    weighted_score: Decimal
    row_status: str
    latest_observed_at: datetime
    latest_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingMemoryQuorumRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityScraplingMemoryQuorumRow")
        _require_digest("subject_digest", self.subject_digest)
        _require_digest("locator_digest", self.locator_digest)
        for field_name in ("finding_count", "family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quorum_weight",
            "conflict_weight",
            "latest_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "weighted_score",
            _require_ratio_decimal("weighted_score", self.weighted_score),
        )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingMemoryQuorumReport:
    generated_at: datetime
    config_version: str
    memory_count: Decimal
    subject_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityScraplingMemoryQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingMemoryQuorumReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceAuthorityScraplingMemoryQuorumReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_MEMORY_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "memory_count",
            "subject_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_score",
            _require_ratio_decimal("average_score", self.average_score),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _validate_report_counts(self)
        digest = self.derived_validation_digest
        if digest == "":
            object.__setattr__(self, "derived_validation_digest", _digest_report(self))
            return
        _require_digest("derived_validation_digest", digest)
        expected_digest = _digest_report(self)
        if digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_authority_scrapling_memory_quorum_report(
    findings: Iterable[ResearchSourceAuthorityScraplingMemoryQuorumFinding],
    *,
    config: ResearchSourceAuthorityScraplingMemoryQuorumConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchSourceAuthorityScraplingMemoryQuorumReport:
    cfg = config or ResearchSourceAuthorityScraplingMemoryQuorumConfig()
    if type(cfg) is not ResearchSourceAuthorityScraplingMemoryQuorumConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityScraplingMemoryQuorumConfig",
        )
    _require_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))
    normalized_findings = _normalize_findings(findings)
    rows = tuple(
        sorted(
            (_row_from_group(group, cfg, generated) for group in _group_findings(normalized_findings)),
            key=_row_sort_key,
        ),
    )
    memory_count = _count_decimal(len(normalized_findings))
    subject_count = _count_decimal(len(rows))
    pass_count = _count_decimal(sum(_one_if(row.row_status == "pass") for row in rows))
    watch_count = _count_decimal(sum(_one_if(row.row_status == "watch") for row in rows))
    block_count = _count_decimal(sum(_one_if(row.row_status == "block") for row in rows))
    report_status = _report_status(rows)
    return ResearchSourceAuthorityScraplingMemoryQuorumReport(
        generated_at=generated,
        config_version=cfg.config_version,
        memory_count=memory_count,
        subject_count=subject_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_score=_average_score(tuple(row.weighted_score for row in rows)),
        report_status=report_status,
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_authority_scrapling_memory_quorum_report_payload(
    report: ResearchSourceAuthorityScraplingMemoryQuorumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceAuthorityScraplingMemoryQuorumReport:
        _require_flags("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchSourceAuthorityScraplingMemoryQuorumReport",
    )


def _normalize_findings(
    findings: Iterable[ResearchSourceAuthorityScraplingMemoryQuorumFinding],
) -> tuple[ResearchSourceAuthorityScraplingMemoryQuorumFinding, ...]:
    normalized = tuple(findings)
    for item in normalized:
        if type(item) is not ResearchSourceAuthorityScraplingMemoryQuorumFinding:
            raise ValueError(
                "finding must be a ResearchSourceAuthorityScraplingMemoryQuorumFinding",
            )
        _require_flags("finding", item)
    return normalized


def _group_findings(
    findings: tuple[ResearchSourceAuthorityScraplingMemoryQuorumFinding, ...],
) -> tuple[tuple[ResearchSourceAuthorityScraplingMemoryQuorumFinding, ...], ...]:
    groups: dict[str, list[ResearchSourceAuthorityScraplingMemoryQuorumFinding]] = {}
    for item in findings:
        if item.private_subject_ref not in groups:
            groups[item.private_subject_ref] = []
        groups[item.private_subject_ref].append(item)
    return tuple(
        tuple(sorted(group, key=_finding_sort_key))
        for _, group in sorted(groups.items(), key=lambda pair: _stable_digest(pair[0]))
    )


def _row_from_group(
    group: tuple[ResearchSourceAuthorityScraplingMemoryQuorumFinding, ...],
    cfg: ResearchSourceAuthorityScraplingMemoryQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityScraplingMemoryQuorumRow:
    subject_ref = group[0].private_subject_ref
    latest_observed_at = max(item.observed_at for item in group)
    latest_age_seconds = _seconds_between(latest_observed_at, generated_at)
    family_count = _count_decimal(len({item.family_ref for item in group}))
    finding_count = _count_decimal(len(group))
    quorum_weight = _sum_decimals(tuple(item.support_weight for item in group))
    conflict_weight = _sum_decimals(tuple(item.conflict_weight for item in group))
    weighted_score = _weighted_score(group)
    row_status, reason_codes = _row_status_and_reasons(
        weighted_score,
        family_count,
        quorum_weight,
        conflict_weight,
        latest_age_seconds,
        cfg,
    )
    return ResearchSourceAuthorityScraplingMemoryQuorumRow(
        subject_digest=_stable_digest(f"subject:{subject_ref}"),
        locator_digest=_canonical_digest(
            {
                "locator_refs": [
                    item.private_locator_ref
                    for item in group
                ],
            },
        ),
        finding_count=finding_count,
        family_count=family_count,
        quorum_weight=quorum_weight,
        conflict_weight=conflict_weight,
        weighted_score=weighted_score,
        row_status=row_status,
        latest_observed_at=latest_observed_at,
        latest_age_seconds=latest_age_seconds,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    weighted_score: Decimal,
    family_count: Decimal,
    quorum_weight: Decimal,
    conflict_weight: Decimal,
    latest_age_seconds: Decimal,
    cfg: ResearchSourceAuthorityScraplingMemoryQuorumConfig,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    stale = latest_age_seconds > cfg.max_stale_age_seconds
    below_watch = weighted_score < cfg.min_watch_score
    if stale:
        reasons.append("stale_memory")
    if below_watch:
        reasons.append("below_watch_score")
    if stale or below_watch:
        reasons.append("quorum_block")
        return "block", tuple(reasons)
    if family_count < cfg.min_pass_family_count:
        reasons.append("insufficient_family_quorum")
    if quorum_weight < cfg.min_pass_quorum_weight:
        reasons.append("insufficient_weight_quorum")
    if conflict_weight > _ZERO:
        reasons.append("conflict_weight_present")
    if weighted_score >= cfg.min_pass_score:
        reasons.append("pass_score")
    else:
        reasons.append("watch_score")
    if (
        weighted_score >= cfg.min_pass_score
        and family_count >= cfg.min_pass_family_count
        and quorum_weight >= cfg.min_pass_quorum_weight
        and conflict_weight == _ZERO
    ):
        reasons.append("quorum_pass")
        return "pass", tuple(reasons)
    reasons.append("quorum_watch")
    return "watch", tuple(reasons)


def _weighted_score(
    group: tuple[ResearchSourceAuthorityScraplingMemoryQuorumFinding, ...],
) -> Decimal:
    support_weight = _sum_decimals(tuple(item.support_weight for item in group))
    if support_weight == _ZERO:
        return _ZERO
    weighted_sum = _sum_decimals(
        tuple(item.authority_score * item.support_weight for item in group),
    )
    return _quantize(weighted_sum / support_weight)


def _report_status(
    rows: tuple[ResearchSourceAuthorityScraplingMemoryQuorumRow, ...],
) -> str:
    if not rows:
        return "block"
    statuses = tuple(row.row_status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityScraplingMemoryQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_memory_quorum",)
    reasons: list[str] = []
    statuses = tuple(row.row_status for row in rows)
    if "block" in statuses:
        reasons.append("block_present")
    if "pass" in statuses:
        reasons.append("pass_present")
    if "watch" in statuses:
        reasons.append("watch_present")
    return tuple(reasons)


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(_sum_decimals(values) / _count_decimal(len(values)))


def _validate_report_counts(
    report: ResearchSourceAuthorityScraplingMemoryQuorumReport,
) -> None:
    if report.memory_count != _sum_decimals(
        tuple(row.finding_count for row in report.rows),
    ):
        raise ValueError("memory_count must match rows")
    row_count = _count_decimal(len(report.rows))
    if report.subject_count != row_count:
        raise ValueError("subject_count must match rows")
    if report.pass_count != _count_decimal(
        sum(_one_if(row.row_status == "pass") for row in report.rows),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(_one_if(row.row_status == "watch") for row in report.rows),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(_one_if(row.row_status == "block") for row in report.rows),
    ):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.average_score != _average_score(
        tuple(row.weighted_score for row in report.rows),
    ):
        raise ValueError("average_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical ordering")
    subject_digests = tuple(row.subject_digest for row in report.rows)
    if len(subject_digests) != len(set(subject_digests)):
        raise ValueError("rows must contain unique subject_digest values")
    for row in report.rows:
        expected_age = _seconds_between(row.latest_observed_at, report.generated_at)
        if row.latest_age_seconds != expected_age:
            raise ValueError("latest_age_seconds must match generated_at")


def _validate_row(
    row: ResearchSourceAuthorityScraplingMemoryQuorumRow,
) -> None:
    if row.finding_count < _COUNT_ONE:
        raise ValueError("finding_count must be positive")
    if row.family_count < _COUNT_ONE:
        raise ValueError("family_count must be positive")
    if row.family_count > row.finding_count:
        raise ValueError("family_count must not exceed finding_count")


def _normalize_rows(
    rows: tuple[ResearchSourceAuthorityScraplingMemoryQuorumRow, ...],
) -> tuple[ResearchSourceAuthorityScraplingMemoryQuorumRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceAuthorityScraplingMemoryQuorumRow:
            raise ValueError("rows must contain ResearchSourceAuthorityScraplingMemoryQuorumRow")
        _require_flags("row", row)
    return normalized


def _finding_sort_key(
    item: ResearchSourceAuthorityScraplingMemoryQuorumFinding,
) -> tuple[str, str, str]:
    return (
        item.observed_at.isoformat(),
        _stable_digest(item.private_subject_ref),
        _stable_digest(item.private_locator_ref),
    )


def _row_sort_key(
    row: ResearchSourceAuthorityScraplingMemoryQuorumRow,
) -> tuple[Decimal, Decimal, str]:
    status_rank = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
    return (status_rank[row.row_status], row.weighted_score, row.subject_digest)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_payload_fields("public payload", payload, _REPORT_PAYLOAD_FIELDS)
    _require_flags("public payload", _DictFlags(payload))
    digest = payload["derived_validation_digest"] if "derived_validation_digest" in payload else None
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    reconstructed = _report_from_public_payload(payload)
    canonical = _json_ready(reconstructed)
    if canonical != payload:
        raise ValueError("public payload must use canonical schema values")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceAuthorityScraplingMemoryQuorumReport:
    return ResearchSourceAuthorityScraplingMemoryQuorumReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        memory_count=_public_decimal("memory_count", payload["memory_count"]),
        subject_count=_public_decimal("subject_count", payload["subject_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        average_score=_public_decimal("average_score", payload["average_score"]),
        report_status=_public_string("report_status", payload["report_status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        rows=_public_rows(payload["rows"]),
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_bool("paper_only", payload["paper_only"]),
        report_only=_public_bool("report_only", payload["report_only"]),
        readonly=_public_bool("readonly", payload["readonly"]),
    )


def _public_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityScraplingMemoryQuorumRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[ResearchSourceAuthorityScraplingMemoryQuorumRow] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_fields("row payload", item, _ROW_PAYLOAD_FIELDS)
        rows.append(_row_from_public_payload(item))
    return tuple(rows)


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceAuthorityScraplingMemoryQuorumRow:
    return ResearchSourceAuthorityScraplingMemoryQuorumRow(
        subject_digest=_public_string("subject_digest", payload["subject_digest"]),
        locator_digest=_public_string("locator_digest", payload["locator_digest"]),
        finding_count=_public_decimal("finding_count", payload["finding_count"]),
        family_count=_public_decimal("family_count", payload["family_count"]),
        quorum_weight=_public_decimal("quorum_weight", payload["quorum_weight"]),
        conflict_weight=_public_decimal("conflict_weight", payload["conflict_weight"]),
        weighted_score=_public_decimal("weighted_score", payload["weighted_score"]),
        row_status=_public_string("row_status", payload["row_status"]),
        latest_observed_at=_public_datetime(
            "latest_observed_at",
            payload["latest_observed_at"],
        ),
        latest_age_seconds=_public_decimal(
            "latest_age_seconds",
            payload["latest_age_seconds"],
        ),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_public_bool("paper_only", payload["paper_only"]),
        report_only=_public_bool("report_only", payload["report_only"]),
        readonly=_public_bool("readonly", payload["readonly"]),
    )


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{label} fields must match the public schema")


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc


def _public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_public_string(field_name, item) for item in value)


def _public_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _digest_report(report: ResearchSourceAuthorityScraplingMemoryQuorumReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload["derived_validation_digest"] = ""
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("report payload", payload)
    return _canonical_digest(payload)


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value["paper_only"] if "paper_only" in self.value else None

    @property
    def report_only(self) -> object:
        return self.value["report_only"] if "report_only" in self.value else None

    @property
    def readonly(self) -> object:
        return self.value["readonly"] if "readonly" in self.value else None


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _has_denied_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_denied_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_denied_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    if normalized in {
        "configversion",
        "researchsourceauthorityscraplingmemoryquorumreportv0",
    }:
        return False
    if normalized.startswith("researchsourceauthorityscraplingmemoryquorum"):
        return False
    return any(fragment in normalized for fragment in _PUBLIC_DENY_FRAGMENTS)


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in _DIGEST_HEX for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal_exact(field_name, value)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized.to_integral_value()


def _require_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal_exact(field_name, value)
    return _quantize(normalized)


def _require_decimal_exact(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if start > end:
        raise ValueError("observed_at must be at or before generated_at")
    delta = end - start
    seconds = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = _ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _one_if(condition: bool) -> int:
    return 1 if condition else 0


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_SIX_PLACES)


def _stable_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_MEMORY_QUORUM_CONFIG_VERSION",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "ResearchSourceAuthorityScraplingMemoryQuorumConfig",
    "ResearchSourceAuthorityScraplingMemoryQuorumFinding",
    "ResearchSourceAuthorityScraplingMemoryQuorumReport",
    "ResearchSourceAuthorityScraplingMemoryQuorumRow",
    "build_research_source_authority_scrapling_memory_quorum_report",
    "research_source_authority_scrapling_memory_quorum_report_payload",
)
