"""Pure reducer for paper autonomous readiness digest reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_CONFIG_VERSION = (
    "paper-autonomous-readiness-digest-v0"
)
DIGEST_STATUSES = ("pass", "watch", "blocked")
NEXT_REVIEW_ACTION_BY_STATUS = {
    "pass": "continue_operator_review_of_paper_autonomous_readiness_digest",
    "watch": "review_watch_paper_autonomous_readiness_evidence",
    "blocked": "review_blocked_paper_autonomous_readiness_evidence",
}
PASS_REASON_CODE = "paper_autonomous_readiness_digest_passed"
READINESS_SOURCE_NAME = "readiness_gate"
SCREENING_SOURCE_NAME = "screening"
TRANSITION_SOURCE_NAME = "transition"
ALLOCATION_SOURCE_NAME = "allocation"
AGREEMENT_TREND_GATE_SOURCE_NAME = "agreement_trend_gate"
LEDGER_SOURCE_NAME = "ledger"
SOURCE_NAMES = (
    READINESS_SOURCE_NAME,
    SCREENING_SOURCE_NAME,
    TRANSITION_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    AGREEMENT_TREND_GATE_SOURCE_NAME,
    LEDGER_SOURCE_NAME,
)
OPTIONAL_SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    TRANSITION_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    AGREEMENT_TREND_GATE_SOURCE_NAME,
    LEDGER_SOURCE_NAME,
)

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_CONFIG_VERSION",
    "PaperAutonomousReadinessDigestConfig",
    "PaperAutonomousReadinessDigestEvidence",
    "PaperAutonomousReadinessDigestReasonCodeCount",
    "PaperAutonomousReadinessDigestReport",
    "build_paper_autonomous_readiness_digest_report",
)


@dataclass(frozen=True)
class PaperAutonomousReadinessDigestConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessDigestConfig:
            raise TypeError(
                "PaperAutonomousReadinessDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessDigestConfig:
            raise ValueError(
                "config must be exactly PaperAutonomousReadinessDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousReadinessDigestEvidence:
    source_name: str
    status: str
    recommended_next_step: str
    generated_at: datetime
    config_version: str
    reason_codes: tuple[str, ...]
    required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessDigestEvidence:
            raise TypeError(
                "PaperAutonomousReadinessDigestEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessDigestEvidence:
            raise ValueError(
                "evidence must be exactly PaperAutonomousReadinessDigestEvidence",
            )
        _require_source_name("source_name", self.source_name)
        _require_digest_status("status", self.status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if type(self.required) is not bool:
            raise ValueError("required must be a bool")
        _validate_hard_flags("evidence", self)


@dataclass(frozen=True)
class PaperAutonomousReadinessDigestReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessDigestReasonCodeCount:
            raise TypeError(
                "PaperAutonomousReadinessDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousReadinessDigestReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousReadinessDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_review_action: str
    evidence: tuple[PaperAutonomousReadinessDigestEvidence, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[PaperAutonomousReadinessDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessDigestReport:
            raise TypeError(
                "PaperAutonomousReadinessDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessDigestReport:
            raise ValueError(
                "digest report must be exactly PaperAutonomousReadinessDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string(
            "recommended_next_review_action",
            self.recommended_next_review_action,
        )
        object.__setattr__(self, "evidence", _normalize_evidence(self.evidence))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
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
        _validate_digest_report(self)
        _validate_hard_flags("digest report", self)


def build_paper_autonomous_readiness_digest_report(
    readiness_report: object,
    *,
    screening_report: object | None = None,
    transition_report: object | None = None,
    allocation_report: object | None = None,
    agreement_trend_gate_report: object | None = None,
    ledger_report: object | None = None,
    config: PaperAutonomousReadinessDigestConfig,
    generated_at: datetime,
) -> PaperAutonomousReadinessDigestReport:
    if readiness_report is None:
        raise ValueError("readiness_report is required")
    if type(config) is not PaperAutonomousReadinessDigestConfig:
        raise ValueError("config must be a PaperAutonomousReadinessDigestConfig")

    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)
    evidence = [
        _evidence_from_report(
            READINESS_SOURCE_NAME,
            readiness_report,
            required=True,
            label="readiness_report",
        ),
    ]
    optional_reports = (
        (SCREENING_SOURCE_NAME, screening_report, "screening_report"),
        (TRANSITION_SOURCE_NAME, transition_report, "transition_report"),
        (ALLOCATION_SOURCE_NAME, allocation_report, "allocation_report"),
        (
            AGREEMENT_TREND_GATE_SOURCE_NAME,
            agreement_trend_gate_report,
            "agreement_trend_gate_report",
        ),
        (LEDGER_SOURCE_NAME, ledger_report, "ledger_report"),
    )
    for source_name, source_report, label in optional_reports:
        if source_report is not None:
            evidence.append(
                _evidence_from_report(
                    source_name,
                    source_report,
                    required=False,
                    label=label,
                ),
            )
    evidence_rows = tuple(evidence)
    digest_status = _digest_status(evidence_rows)
    reason_codes = _digest_reason_codes(evidence_rows)

    return PaperAutonomousReadinessDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_review_action=NEXT_REVIEW_ACTION_BY_STATUS[digest_status],
        evidence=evidence_rows,
        source_config_versions=tuple(
            (row.source_name, row.config_version) for row in evidence_rows
        ),
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def _evidence_from_report(
    source_name: str,
    source_report: object,
    *,
    required: bool,
    label: str,
) -> PaperAutonomousReadinessDigestEvidence:
    _validate_hard_flags(label, source_report)
    return PaperAutonomousReadinessDigestEvidence(
        source_name=source_name,
        status=_status_from_report(label, source_report),
        recommended_next_step=_required_attr(label, source_report, "recommended_next_step"),
        generated_at=_required_attr(label, source_report, "generated_at"),
        config_version=_required_attr(label, source_report, "config_version"),
        reason_codes=_reason_codes_from_report(label, source_report),
        required=required,
    )


def _status_from_report(label: str, source_report: object) -> str:
    for attr_name in ("readiness_status", "status", "gate_status", "health_status"):
        value = _optional_attr(source_report, attr_name)
        if value is not None:
            _require_digest_status(attr_name, value)
            return value
    raise ValueError(f"{label} must expose status")


def _reason_codes_from_report(label: str, source_report: object) -> tuple[str, ...]:
    value = _required_attr(label, source_report, "reason_codes")
    return _normalize_reason_codes("reason_codes", value)


def _required_attr(label: str, source_report: object, attr_name: str) -> object:
    try:
        value = object.__getattribute__(source_report, attr_name)
    except AttributeError as exc:
        raise ValueError(f"{label} must expose {attr_name}") from exc
    if value is None:
        raise ValueError(f"{label} must expose {attr_name}")
    return value


def _optional_attr(source_report: object, attr_name: str) -> object | None:
    try:
        return object.__getattribute__(source_report, attr_name)
    except AttributeError:
        return None


def _digest_status(
    evidence: tuple[PaperAutonomousReadinessDigestEvidence, ...],
) -> str:
    if any(row.status == "blocked" for row in evidence):
        return "blocked"
    if any(row.status == "watch" for row in evidence):
        return "watch"
    return "pass"


def _digest_reason_codes(
    evidence: tuple[PaperAutonomousReadinessDigestEvidence, ...],
) -> tuple[str, ...]:
    reason_codes = [f"{row.source_name}_{row.status}" for row in evidence]
    if _digest_status(evidence) == "pass":
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousReadinessDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        if reason_code in counts:
            counts[reason_code] += 1
        else:
            counts[reason_code] = 1
    return tuple(
        PaperAutonomousReadinessDigestReasonCodeCount(reason_code, report_count)
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_digest_report(report: PaperAutonomousReadinessDigestReport) -> None:
    if (
        report.recommended_next_review_action
        != NEXT_REVIEW_ACTION_BY_STATUS[report.digest_status]
    ):
        raise ValueError("recommended_next_review_action must match digest_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.digest_status != _digest_status(report.evidence):
        raise ValueError("digest_status must match evidence")
    if report.reason_codes != _digest_reason_codes(report.evidence):
        raise ValueError("reason_codes must match evidence")
    if report.source_config_versions != tuple(
        (row.source_name, row.config_version) for row in report.evidence
    ):
        raise ValueError("source_config_versions must match evidence")


def _normalize_evidence(
    value: object,
) -> tuple[PaperAutonomousReadinessDigestEvidence, ...]:
    if type(value) is not tuple:
        raise ValueError("evidence must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("evidence is required")
    for row in rows:
        if type(row) is not PaperAutonomousReadinessDigestEvidence:
            raise ValueError("evidence must contain exact evidence rows")
    if rows[0].source_name != READINESS_SOURCE_NAME:
        raise ValueError("evidence must contain readiness_gate first")
    if rows[0].required is not True:
        raise ValueError("readiness_gate evidence must be required")
    source_names = tuple(row.source_name for row in rows)
    if len(set(source_names)) != len(source_names):
        raise ValueError("evidence source names must be unique")
    if any(source_name not in SOURCE_NAMES for source_name in source_names):
        raise ValueError("evidence must contain known source names")
    observed_optional = tuple(
        source_name for source_name in source_names if source_name != READINESS_SOURCE_NAME
    )
    expected_optional = tuple(
        source_name
        for source_name in OPTIONAL_SOURCE_NAMES
        if source_name in observed_optional
    )
    if observed_optional != expected_optional:
        raise ValueError("evidence must use canonical source sequence")
    for row in rows[1:]:
        if row.required is not False:
            raise ValueError("optional evidence rows must not be required")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    rows: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain source/version pairs")
        source_name, config_version = item
        _require_source_name("source_config_versions", source_name)
        _require_canonical_string("source_config_versions", config_version)
        rows.append((source_name, config_version))
    return tuple(rows)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousReadinessDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    seen: set[str] = set()
    previous_key: tuple[int, str] | None = None
    for row in rows:
        if type(row) is not PaperAutonomousReadinessDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_source_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_NAMES:
        raise ValueError(f"{field_name} must be a known source name")


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _validate_hard_flags(label: str, value: object) -> None:
    if _optional_attr(value, "paper_only") is not True:
        raise ValueError(f"{label} must be paper_only")
    if _optional_attr(value, "report_only") is not True:
        raise ValueError(f"{label} must be report_only")
    if _optional_attr(value, "readonly") is not True:
        raise ValueError(f"{label} must be readonly")
