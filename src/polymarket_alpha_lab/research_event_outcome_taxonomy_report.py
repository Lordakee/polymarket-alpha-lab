from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
PROBABILITY_QUANTUM = Decimal("0.000001")

STATUSES = frozenset(("pass", "watch", "blocked"))
SEVERITIES = frozenset(("watch", "blocked"))
CHECK_NAMES = frozenset(
    (
        "ambiguity_risk",
        "exhaustiveness",
        "mutual_exclusivity",
        "settlement_mapping",
    ),
)
GENERATED_OUTCOME_REASON_CODES = frozenset(
    (
        "outcome_taxonomy_pass",
        "residual_outcome_declared",
    ),
)
SAFE_STRING_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_:-")
UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "raw",
        "question",
        "slug",
        "source_url",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "://",
        "raw question",
        "source_url",
        "token=",
        "dsn=",
    ),
)


@dataclass(frozen=True)
class ResearchEventOutcomeTaxonomyConfig:
    config_version: str
    ambiguity_watch_threshold: Decimal
    ambiguity_block_threshold: Decimal
    min_outcome_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "ambiguity_watch_threshold",
            _require_probability_decimal(
                "ambiguity_watch_threshold",
                self.ambiguity_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_block_threshold",
            _require_probability_decimal(
                "ambiguity_block_threshold",
                self.ambiguity_block_threshold,
            ),
        )
        if self.ambiguity_watch_threshold >= self.ambiguity_block_threshold:
            raise ValueError(
                "ambiguity_watch_threshold must be below ambiguity_block_threshold",
            )
        object.__setattr__(
            self,
            "min_outcome_count",
            _require_nonnegative_whole_decimal(
                "min_outcome_count",
                self.min_outcome_count,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventOutcomeTaxonomyOutcome:
    outcome_id: str
    coverage_keys: tuple[str, ...]
    settlement_keys: tuple[str, ...]
    covers_residual: bool = False
    ambiguity_risk: Decimal = ZERO
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("outcome_id", self.outcome_id)
        object.__setattr__(
            self,
            "coverage_keys",
            _normalize_string_tuple(
                "coverage_keys",
                self.coverage_keys,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "settlement_keys",
            _normalize_string_tuple(
                "settlement_keys",
                self.settlement_keys,
                allow_empty=True,
            ),
        )
        _require_bool("covers_residual", self.covers_residual)
        object.__setattr__(
            self,
            "ambiguity_risk",
            _require_probability_decimal("ambiguity_risk", self.ambiguity_risk),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, prefix_input=True),
        )
        _require_hard_flags("outcome", self)


@dataclass(frozen=True)
class ResearchEventOutcomeTaxonomyFinding:
    check_name: str
    severity: str
    reason_code: str
    outcome_ids: tuple[str, ...]
    detail_key: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("check_name", self.check_name, CHECK_NAMES)
        _require_member("severity", self.severity, SEVERITIES)
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "outcome_ids",
            _normalize_string_tuple(
                "outcome_ids",
                self.outcome_ids,
                allow_empty=True,
            ),
        )
        _require_canonical_string("detail_key", self.detail_key)
        _require_hard_flags("finding", self)


@dataclass(frozen=True)
class ResearchEventOutcomeTaxonomyReport:
    generated_at: datetime
    config_version: str
    redacted_event_ref: str
    outcome_count: Decimal
    coverage_key_count: Decimal
    settlement_key_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    rows: tuple[ResearchEventOutcomeTaxonomyOutcome, ...]
    findings: tuple[ResearchEventOutcomeTaxonomyFinding, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("redacted_event_ref", self.redacted_event_ref)
        for field_name in (
            "outcome_count",
            "coverage_key_count",
            "settlement_key_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "findings", _normalize_findings(self.findings))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, prefix_input=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_outcome_taxonomy_report_payload(self)


def build_research_event_outcome_taxonomy_report(
    *,
    event_ref: str,
    outcomes: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
    expected_coverage_keys: tuple[str, ...],
    config: ResearchEventOutcomeTaxonomyConfig,
    generated_at: datetime,
) -> ResearchEventOutcomeTaxonomyReport:
    if type(config) is not ResearchEventOutcomeTaxonomyConfig:
        raise ValueError("config must be a ResearchEventOutcomeTaxonomyConfig")
    _require_hard_flags("config", config)
    _require_private_ref("event_ref", event_ref)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _build_rows(_normalize_input_rows(outcomes))
    expected_keys = _normalize_string_tuple(
        "expected_coverage_keys",
        expected_coverage_keys,
        allow_empty=True,
    )
    findings = _build_findings(
        rows,
        expected_coverage_keys=expected_keys,
        config=config,
    )

    return ResearchEventOutcomeTaxonomyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        redacted_event_ref=_redacted_event_ref(event_ref),
        outcome_count=_decimal_count(len(rows)),
        coverage_key_count=_decimal_count(len(_coverage_key_set(rows))),
        settlement_key_count=_decimal_count(len(_settlement_key_set(rows))),
        watch_count=_decimal_count(_finding_count(findings, "watch")),
        blocked_count=_decimal_count(_finding_count(findings, "blocked")),
        status=_summary_status(findings),
        rows=rows,
        findings=findings,
        reason_codes=_summary_reason_codes(findings),
    )


def research_event_outcome_taxonomy_report_payload(
    report: ResearchEventOutcomeTaxonomyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventOutcomeTaxonomyReport:
        raise ValueError("report must be a ResearchEventOutcomeTaxonomyReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _build_rows(
    outcomes: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
) -> tuple[ResearchEventOutcomeTaxonomyOutcome, ...]:
    rows: list[ResearchEventOutcomeTaxonomyOutcome] = []
    for item in sorted(outcomes, key=lambda row: row.outcome_id):
        reason_codes = set(item.reason_codes)
        if item.covers_residual:
            reason_codes.add("residual_outcome_declared")
        reason_codes.add("outcome_taxonomy_pass")
        rows.append(
            ResearchEventOutcomeTaxonomyOutcome(
                outcome_id=item.outcome_id,
                coverage_keys=item.coverage_keys,
                settlement_keys=item.settlement_keys,
                covers_residual=item.covers_residual,
                ambiguity_risk=item.ambiguity_risk,
                reason_codes=tuple(sorted(reason_codes)),
            ),
        )
    return tuple(rows)


def _build_findings(
    rows: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
    *,
    expected_coverage_keys: tuple[str, ...],
    config: ResearchEventOutcomeTaxonomyConfig,
) -> tuple[ResearchEventOutcomeTaxonomyFinding, ...]:
    findings: list[ResearchEventOutcomeTaxonomyFinding] = []
    coverage_to_outcomes = _key_to_outcomes(rows, attr_name="coverage_keys")
    settlement_to_outcomes = _key_to_outcomes(rows, attr_name="settlement_keys")

    if _decimal_count(len(rows)) < config.min_outcome_count:
        findings.append(
            _finding(
                check_name="exhaustiveness",
                severity="blocked",
                reason_code="insufficient_outcomes",
                outcome_ids=(),
                detail_key="outcome_count",
            ),
        )

    for key in sorted(coverage_to_outcomes):
        outcome_ids = coverage_to_outcomes[key]
        if len(outcome_ids) > 1:
            findings.append(
                _finding(
                    check_name="mutual_exclusivity",
                    severity="blocked",
                    reason_code="coverage_key_overlap",
                    outcome_ids=outcome_ids,
                    detail_key=key,
                ),
            )

    covered_keys = frozenset(coverage_to_outcomes)
    for key in expected_coverage_keys:
        if key not in covered_keys:
            findings.append(
                _finding(
                    check_name="exhaustiveness",
                    severity="blocked",
                    reason_code="missing_expected_coverage",
                    outcome_ids=(),
                    detail_key=key,
                ),
            )

    if not any(row.covers_residual for row in rows):
        findings.append(
            _finding(
                check_name="exhaustiveness",
                severity="watch",
                reason_code="missing_residual_outcome",
                outcome_ids=(),
                detail_key="residual",
            ),
        )

    for row in rows:
        if not row.settlement_keys:
            findings.append(
                _finding(
                    check_name="settlement_mapping",
                    severity="blocked",
                    reason_code="missing_settlement_mapping",
                    outcome_ids=(row.outcome_id,),
                    detail_key=row.outcome_id,
                ),
            )

    for key in sorted(settlement_to_outcomes):
        outcome_ids = settlement_to_outcomes[key]
        if len(outcome_ids) > 1:
            findings.append(
                _finding(
                    check_name="settlement_mapping",
                    severity="blocked",
                    reason_code="settlement_key_overlap",
                    outcome_ids=outcome_ids,
                    detail_key=key,
                ),
            )

    for row in rows:
        if row.ambiguity_risk >= config.ambiguity_block_threshold:
            findings.append(
                _finding(
                    check_name="ambiguity_risk",
                    severity="blocked",
                    reason_code="ambiguity_risk_blocked",
                    outcome_ids=(row.outcome_id,),
                    detail_key=row.outcome_id,
                ),
            )
        elif row.ambiguity_risk >= config.ambiguity_watch_threshold:
            findings.append(
                _finding(
                    check_name="ambiguity_risk",
                    severity="watch",
                    reason_code="ambiguity_risk_watch",
                    outcome_ids=(row.outcome_id,),
                    detail_key=row.outcome_id,
                ),
            )

    return tuple(findings)


def _finding(
    *,
    check_name: str,
    severity: str,
    reason_code: str,
    outcome_ids: tuple[str, ...],
    detail_key: str,
) -> ResearchEventOutcomeTaxonomyFinding:
    return ResearchEventOutcomeTaxonomyFinding(
        check_name=check_name,
        severity=severity,
        reason_code=reason_code,
        outcome_ids=outcome_ids,
        detail_key=detail_key,
    )


def _key_to_outcomes(
    rows: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
    *,
    attr_name: str,
) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, list[str]] = {}
    for row in rows:
        keys = getattr(row, attr_name)
        if type(keys) is not tuple:
            raise ValueError(f"{attr_name} must be a tuple")
        for key in keys:
            mapping.setdefault(key, []).append(row.outcome_id)
    return {key: tuple(sorted(value)) for key, value in mapping.items()}


def _coverage_key_set(
    rows: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
) -> frozenset[str]:
    return frozenset(key for row in rows for key in row.coverage_keys)


def _settlement_key_set(
    rows: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
) -> frozenset[str]:
    return frozenset(key for row in rows for key in row.settlement_keys)


def _finding_count(
    findings: tuple[ResearchEventOutcomeTaxonomyFinding, ...],
    severity: str,
) -> int:
    return sum(1 for finding in findings if finding.severity == severity)


def _summary_status(
    findings: tuple[ResearchEventOutcomeTaxonomyFinding, ...],
) -> str:
    if any(finding.severity == "blocked" for finding in findings):
        return "blocked"
    if any(finding.severity == "watch" for finding in findings):
        return "watch"
    return "pass"


def _summary_reason_codes(
    findings: tuple[ResearchEventOutcomeTaxonomyFinding, ...],
) -> tuple[str, ...]:
    if not findings:
        return ("outcome_taxonomy_pass",)
    return tuple(sorted({finding.reason_code for finding in findings}))


def _validate_report_consistency(report: ResearchEventOutcomeTaxonomyReport) -> None:
    if report.outcome_count != _decimal_count(len(report.rows)):
        raise ValueError("outcome_count must match rows")
    if report.coverage_key_count != _decimal_count(len(_coverage_key_set(report.rows))):
        raise ValueError("coverage_key_count must match rows")
    if report.settlement_key_count != _decimal_count(len(_settlement_key_set(report.rows))):
        raise ValueError("settlement_key_count must match rows")
    if report.watch_count != _decimal_count(_finding_count(report.findings, "watch")):
        raise ValueError("watch_count must match findings")
    if report.blocked_count != _decimal_count(_finding_count(report.findings, "blocked")):
        raise ValueError("blocked_count must match findings")
    if report.status != _summary_status(report.findings):
        raise ValueError("status must match findings")
    if report.reason_codes != _summary_reason_codes(report.findings):
        raise ValueError("reason_codes must match findings")


def _normalize_input_rows(
    outcomes: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
) -> tuple[ResearchEventOutcomeTaxonomyOutcome, ...]:
    if type(outcomes) is not tuple:
        raise ValueError("outcomes must be a tuple")
    rows: list[ResearchEventOutcomeTaxonomyOutcome] = []
    seen: set[str] = set()
    for item in outcomes:
        if type(item) is not ResearchEventOutcomeTaxonomyOutcome:
            raise ValueError("outcomes must contain ResearchEventOutcomeTaxonomyOutcome values")
        _require_hard_flags("outcome", item)
        if item.outcome_id in seen:
            raise ValueError("outcome_id values must be unique")
        seen.add(item.outcome_id)
        rows.append(item)
    return tuple(rows)


def _normalize_rows(
    rows: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
) -> tuple[ResearchEventOutcomeTaxonomyOutcome, ...]:
    normalized = _normalize_input_rows(rows)
    return tuple(sorted(normalized, key=lambda row: row.outcome_id))


def _normalize_findings(
    findings: tuple[ResearchEventOutcomeTaxonomyFinding, ...],
) -> tuple[ResearchEventOutcomeTaxonomyFinding, ...]:
    if type(findings) is not tuple:
        raise ValueError("findings must be a tuple")
    for item in findings:
        if type(item) is not ResearchEventOutcomeTaxonomyFinding:
            raise ValueError("findings must contain ResearchEventOutcomeTaxonomyFinding values")
        _require_hard_flags("finding", item)
    return findings


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} values must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(sorted(normalized))


def _normalize_reason_codes(value: object, *, prefix_input: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_canonical_string("reason_codes", item)
        if (
            not prefix_input
            or item.startswith("input_")
            or item in GENERATED_OUTCOME_REASON_CODES
        ):
            reason_code = item
        else:
            reason_code = f"input_{item}"
        if reason_code not in seen:
            seen.add(reason_code)
            reason_codes.append(reason_code)
    return tuple(sorted(reason_codes))


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be trimmed")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(char not in SAFE_STRING_CHARS for char in value):
        raise ValueError(f"{field_name} must be canonical")
    if value[0] in "_:-" or value[-1] in "_:-":
        raise ValueError(f"{field_name} must not start or end with punctuation")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: frozenset[str],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {tuple(sorted(allowed_values))}")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(PROBABILITY_QUANTUM)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value.quantize(COUNT_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redacted_event_ref(event_ref: str) -> str:
    digest = sha256(event_ref.encode("utf-8")).hexdigest()[:16]
    return f"event_{digest}"


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public payload key: {key}")
            _reject_unsafe_public_payload(value)
    elif isinstance(payload, list):
        for item in payload:
            _reject_unsafe_public_payload(item)
    elif type(payload) is str:
        normalized_value = payload.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("unsafe public payload value")


__all__ = (
    "ResearchEventOutcomeTaxonomyConfig",
    "ResearchEventOutcomeTaxonomyFinding",
    "ResearchEventOutcomeTaxonomyOutcome",
    "ResearchEventOutcomeTaxonomyReport",
    "build_research_event_outcome_taxonomy_report",
    "research_event_outcome_taxonomy_report_payload",
)
