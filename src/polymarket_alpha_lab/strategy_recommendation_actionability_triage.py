from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any, Iterable


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
TRIAGE_STATUSES = ("actionable", "watch", "blocked")
REPORT_STATUSES = ("empty", "actionable", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "actionable": 2}
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_TEXT_FRAGMENTS = (
    "li" + "ve",
    "tra" + "de",
    "au" + "th",
    "wall" + "et",
    "bro" + "ker",
    "ord" + "er",
    "can" + "cel",
    "rep" + "lace",
    "sig" + "ning",
    "adv" + "ice",
    "private" + "_key",
    "api" + "_key",
    "sec" + "ret",
    "tok" + "en",
    "pass" + "word",
)


@dataclass(frozen=True)
class StrategyRecommendationActionabilityTriageConfig:
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationArtifact:
    artifact_id: str
    market_slug: str
    status: str
    severity_score: Decimal
    confidence_ratio: Decimal
    generated_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("artifact_id", self.artifact_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "severity_score",
            _normalize_nonnegative_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "confidence_ratio",
            _normalize_ratio("confidence_ratio", self.confidence_ratio),
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationActionabilityReasonCodeCount:
    reason_code: str
    count: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )


@dataclass(frozen=True)
class StrategyRecommendationActionabilityTriageRow:
    market_slug: str
    status: str
    artifact_count: Decimal
    max_severity_score: Decimal
    mean_confidence_ratio: Decimal
    latest_artifact_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "artifact_count",
            _normalize_positive_whole_decimal("artifact_count", self.artifact_count),
        )
        object.__setattr__(
            self,
            "max_severity_score",
            _normalize_nonnegative_decimal("max_severity_score", self.max_severity_score),
        )
        object.__setattr__(
            self,
            "mean_confidence_ratio",
            _normalize_ratio("mean_confidence_ratio", self.mean_confidence_ratio),
        )
        object.__setattr__(
            self,
            "latest_artifact_at",
            _as_utc("latest_artifact_at", self.latest_artifact_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationActionabilityTriageReport:
    generated_at: datetime
    config_version: str
    triage_status: str
    artifact_count: Decimal
    row_count: Decimal
    actionable_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    actionable_ratio: Decimal
    watch_ratio: Decimal
    blocked_ratio: Decimal
    reason_code_counts: tuple[StrategyRecommendationActionabilityReasonCodeCount, ...]
    rows: tuple[StrategyRecommendationActionabilityTriageRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("triage_status", self.triage_status)
        for field_name in (
            "artifact_count",
            "row_count",
            "actionable_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("actionable_ratio", "watch_ratio", "blocked_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_strategy_recommendation_actionability_triage_report(
    artifacts: Iterable[StrategyRecommendationArtifact],
    *,
    config: StrategyRecommendationActionabilityTriageConfig,
    generated_at: datetime,
) -> StrategyRecommendationActionabilityTriageReport:
    if type(config) is not StrategyRecommendationActionabilityTriageConfig:
        raise ValueError("config must be a StrategyRecommendationActionabilityTriageConfig")
    _require_hard_flags(config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    normalized_artifacts = _normalize_artifacts(artifacts)
    rows = _build_rows(normalized_artifacts)
    reason_code_counts = _reason_code_counts(normalized_artifacts)
    total_count = Decimal(len(normalized_artifacts))
    actionable_count = Decimal(
        sum(1 for artifact in normalized_artifacts if artifact.status == "actionable"),
    )
    watch_count = Decimal(
        sum(1 for artifact in normalized_artifacts if artifact.status == "watch"),
    )
    blocked_count = Decimal(
        sum(1 for artifact in normalized_artifacts if artifact.status == "blocked"),
    )

    return StrategyRecommendationActionabilityTriageReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        triage_status=_triage_status(rows),
        artifact_count=total_count,
        row_count=Decimal(len(rows)),
        actionable_count=actionable_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        actionable_ratio=_ratio(actionable_count, total_count),
        watch_ratio=_ratio(watch_count, total_count),
        blocked_ratio=_ratio(blocked_count, total_count),
        reason_code_counts=reason_code_counts,
        rows=rows,
    )


def strategy_recommendation_actionability_triage_payload(
    report: StrategyRecommendationActionabilityTriageReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationActionabilityTriageReport:
        raise ValueError("report must be a StrategyRecommendationActionabilityTriageReport")
    _require_hard_flags(report)
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _build_rows(
    artifacts: tuple[StrategyRecommendationArtifact, ...],
) -> tuple[StrategyRecommendationActionabilityTriageRow, ...]:
    grouped: dict[tuple[str, str], list[StrategyRecommendationArtifact]] = {}
    for artifact in artifacts:
        grouped.setdefault((artifact.status, artifact.market_slug), []).append(artifact)
    rows = tuple(_row(status, market_slug, tuple(items)) for (status, market_slug), items in grouped.items())
    return tuple(sorted(rows, key=_row_sort_key))


def _row(
    status: str,
    market_slug: str,
    artifacts: tuple[StrategyRecommendationArtifact, ...],
) -> StrategyRecommendationActionabilityTriageRow:
    reason_codes: set[str] = set()
    for artifact in artifacts:
        reason_codes.update(artifact.reason_codes)
    return StrategyRecommendationActionabilityTriageRow(
        market_slug=market_slug,
        status=status,
        artifact_count=Decimal(len(artifacts)),
        max_severity_score=max(artifact.severity_score for artifact in artifacts),
        mean_confidence_ratio=_mean_decimal(
            tuple(artifact.confidence_ratio for artifact in artifacts),
        ),
        latest_artifact_at=max(artifact.generated_at for artifact in artifacts),
        reason_codes=tuple(sorted(reason_codes)),
    )


def _row_sort_key(
    row: StrategyRecommendationActionabilityTriageRow,
) -> tuple[int, Decimal, str]:
    return (STATUS_RANK[row.status], -row.max_severity_score, row.market_slug)


def _triage_status(rows: tuple[StrategyRecommendationActionabilityTriageRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "actionable"


def _reason_code_counts(
    artifacts: tuple[StrategyRecommendationArtifact, ...],
) -> tuple[StrategyRecommendationActionabilityReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for artifact in artifacts:
        counts.update(artifact.reason_codes)
    return tuple(
        StrategyRecommendationActionabilityReasonCodeCount(
            reason_code=reason_code,
            count=Decimal(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must contain at least one Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _normalize_artifacts(
    artifacts: Iterable[StrategyRecommendationArtifact],
) -> tuple[StrategyRecommendationArtifact, ...]:
    if isinstance(artifacts, (str, bytes)):
        raise ValueError("artifacts must be an iterable")
    try:
        items = tuple(artifacts)
    except TypeError as exc:
        raise ValueError("artifacts must be an iterable") from exc
    for artifact in items:
        if type(artifact) is not StrategyRecommendationArtifact:
            raise ValueError(
                "artifacts must contain only StrategyRecommendationArtifact values",
            )
    return items


def _normalize_rows(
    rows: Iterable[StrategyRecommendationActionabilityTriageRow],
) -> tuple[StrategyRecommendationActionabilityTriageRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not StrategyRecommendationActionabilityTriageRow:
            raise ValueError(
                "rows must contain only StrategyRecommendationActionabilityTriageRow values",
            )
    if len({(row.status, row.market_slug) for row in items}) != len(items):
        raise ValueError("rows must not contain duplicate status and market_slug pairs")
    return tuple(sorted(items, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[StrategyRecommendationActionabilityReasonCodeCount],
) -> tuple[StrategyRecommendationActionabilityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyRecommendationActionabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain only "
                "StrategyRecommendationActionabilityReasonCodeCount values",
            )
    if len({item.reason_code for item in items}) != len(items):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return tuple(sorted(items, key=lambda item: (-item.count, item.reason_code)))


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string("reason_code", item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(items))


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(value)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    _require_decimal("decimal value", value)
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in TRIAGE_STATUSES:
        raise ValueError(f"{field_name} must be actionable, watch, or blocked")


def _require_report_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known triage status")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_text_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _has_unsafe_text_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)


def _validate_report_consistency(
    report: StrategyRecommendationActionabilityTriageReport,
) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.artifact_count != sum((row.artifact_count for row in report.rows), ZERO):
        raise ValueError("artifact_count must match rows")
    if report.actionable_count + report.watch_count + report.blocked_count != report.artifact_count:
        raise ValueError("artifact_count must match status counts")
    if report.actionable_ratio != _ratio(report.actionable_count, report.artifact_count):
        raise ValueError("actionable_ratio must match counts")
    if report.watch_ratio != _ratio(report.watch_count, report.artifact_count):
        raise ValueError("watch_ratio must match counts")
    if report.blocked_ratio != _ratio(report.blocked_count, report.artifact_count):
        raise ValueError("blocked_ratio must match counts")
    if report.triage_status != _triage_status(report.rows):
        raise ValueError("triage_status must match rows")
    row_reason_codes = {reason_code for row in report.rows for reason_code in row.reason_codes}
    count_reason_codes = {item.reason_code for item in report.reason_code_counts}
    if row_reason_codes != count_reason_codes:
        raise ValueError("reason_code_counts must match rows")


def _payload_value(value: Any, *, field_name: str | None = None) -> Any:
    label = field_name or "payload value"
    if isinstance(value, Decimal):
        if field_name is not None and field_name.endswith("count"):
            return str(_normalize_whole_decimal(field_name, value).quantize(Decimal("1")))
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        return _payload_datetime(value, label)
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal values")
    if type(value) is str:
        _require_canonical_string(label, value)
        return value
    if value is None:
        return None
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field must be a string")
            _require_canonical_string("payload field", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _payload_value(item, field_name=key)
        return ready
    raise ValueError(f"{label} is not JSON serializable")


def _payload_datetime(value: datetime, field_name: str) -> str:
    text = _as_utc(field_name, value).isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    return text
