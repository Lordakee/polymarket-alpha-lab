"""Report-only reducer for probability model and research-team disagreement.

The module is deliberately side-effect free: callers provide already-collected
probability estimates and receive deterministic public review metrics. It does
not perform network IO, persistence, credentialed execution, or directional
action language.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_MODEL_DISAGREEMENT_REPORT_CONFIG_VERSION",
    "ResearchProbabilityModelDisagreementConfig",
    "ResearchProbabilityModelDisagreementDigest",
    "ResearchProbabilityModelDisagreementInput",
    "ResearchProbabilityModelDisagreementReasonCodeCount",
    "ResearchProbabilityModelDisagreementReport",
    "ResearchProbabilityModelDisagreementRow",
    "build_research_probability_model_disagreement_report",
    "research_probability_model_disagreement_digest",
    "research_probability_model_disagreement_digest_payload",
    "research_probability_model_disagreement_report_payload",
)


DEFAULT_RESEARCH_PROBABILITY_MODEL_DISAGREEMENT_REPORT_CONFIG_VERSION = (
    "research-probability-model-disagreement-report-v0"
)

STATUSES = ("pass", "watch", "block")
PARTICIPANT_TYPES = ("model", "research_team")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
STATUS_SEVERITY = {"block": 2, "watch": 1, "pass": 0}
NO_INPUTS_REASON = "probability_model_disagreement_missing_inputs"
ALLOWED_PUBLIC_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-",
)
_UNSAFE_PUBLIC_TOKEN_PARTS = (
    ("adv", "ice"),
    ("au", "th"),
    ("b", "uy"),
    ("candi", "date"),
    ("d", "sn"),
    ("market", "_", "id"),
    ("market", "-", "id"),
    ("market", "_", "slug"),
    ("market", "-", "slug"),
    ("ord", "er"),
    ("pos", "ition"),
    ("priv", "ate"),
    ("ques", "tion"),
    ("raw", "_", "candi", "date"),
    ("raw", "-", "candi", "date"),
    ("rec", "ommend"),
    ("sec", "ret"),
    ("se", "ll"),
    ("sou", "rce"),
    ("tab", "le"),
    ("tok", "en"),
    ("tr", "ade"),
    ("u", "rl"),
    ("wal", "let"),
)
UNSAFE_PUBLIC_TOKENS = tuple("".join(parts) for parts in _UNSAFE_PUBLIC_TOKEN_PARTS)


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
class ResearchProbabilityModelDisagreementConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_PROBABILITY_MODEL_DISAGREEMENT_REPORT_CONFIG_VERSION
    )
    min_estimate_count: Decimal = Decimal("2")
    watch_probability_range: Decimal = Decimal("0.100000")
    block_probability_range: Decimal = Decimal("0.250000")
    watch_model_team_gap: Decimal = Decimal("0.080000")
    block_model_team_gap: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityModelDisagreementConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_estimate_count",
            _require_positive_whole_decimal(
                "min_estimate_count",
                self.min_estimate_count,
            ),
        )
        for field_name in (
            "watch_probability_range",
            "block_probability_range",
            "watch_model_team_gap",
            "block_model_team_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_probability_range",
            self.watch_probability_range,
            "block_probability_range",
            self.block_probability_range,
        )
        _require_less_than(
            "watch_model_team_gap",
            self.watch_model_team_gap,
            "block_model_team_gap",
            self.block_model_team_gap,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchProbabilityModelDisagreementInput(_FinalPublicDataclass):
    public_case_key: str
    participant_type: str
    participant_label: str
    probability: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityModelDisagreementInput,
            "input",
        )
        _require_public_string("public_case_key", self.public_case_key)
        _require_participant_type("participant_type", self.participant_type)
        _require_public_string("participant_label", self.participant_label)
        object.__setattr__(
            self,
            "probability",
            _require_probability_decimal("probability", self.probability),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchProbabilityModelDisagreementRow(_FinalPublicDataclass):
    public_case_key: str
    estimate_count: Decimal
    model_count: Decimal
    research_team_count: Decimal
    participant_labels: tuple[str, ...]
    latest_observed_at: datetime
    min_probability: Decimal
    max_probability: Decimal
    mean_probability: Decimal
    model_mean_probability: Decimal | None
    research_team_mean_probability: Decimal | None
    probability_range: Decimal
    model_team_gap: Decimal | None
    status: str
    human_review_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityModelDisagreementRow,
            "row",
        )
        _require_public_string("public_case_key", self.public_case_key)
        for field_name in ("estimate_count", "model_count", "research_team_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "participant_labels",
            _normalize_public_strings("participant_labels", self.participant_labels),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "min_probability",
            "max_probability",
            "mean_probability",
            "probability_range",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("model_mean_probability", "research_team_mean_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "model_team_gap",
            _require_optional_probability_decimal("model_team_gap", self.model_team_gap),
        )
        _require_status("status", self.status)
        _require_status("human_review_status", self.human_review_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchProbabilityModelDisagreementReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    case_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityModelDisagreementReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "case_ratio",
            _require_probability_decimal("case_ratio", self.case_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchProbabilityModelDisagreementDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    human_review_status: str
    case_count: Decimal
    estimate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_probability_range: Decimal
    max_model_team_gap: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchProbabilityModelDisagreementReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityModelDisagreementDigest,
            "digest",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_status("human_review_status", self.human_review_status)
        for field_name in (
            "case_count",
            "estimate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_probability_range", "max_model_team_gap"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("digest", self)
        _validate_digest(self)


@dataclass(frozen=True)
class ResearchProbabilityModelDisagreementReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    human_review_status: str
    case_count: Decimal
    estimate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_probability_range: Decimal
    max_model_team_gap: Decimal
    average_probability_range: Decimal
    rows: tuple[ResearchProbabilityModelDisagreementRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchProbabilityModelDisagreementReasonCodeCount, ...]
    digest: ResearchProbabilityModelDisagreementDigest
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityModelDisagreementReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_status("human_review_status", self.human_review_status)
        for field_name in (
            "case_count",
            "estimate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_probability_range",
            "max_model_team_gap",
            "average_probability_range",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if type(self.digest) is not ResearchProbabilityModelDisagreementDigest:
            raise ValueError("digest must be a ResearchProbabilityModelDisagreementDigest")
        _require_hard_flags("digest", self.digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)


def build_research_probability_model_disagreement_report(
    estimates: Iterable[ResearchProbabilityModelDisagreementInput],
    *,
    config: ResearchProbabilityModelDisagreementConfig,
    generated_at: datetime,
) -> ResearchProbabilityModelDisagreementReport:
    if type(config) is not ResearchProbabilityModelDisagreementConfig:
        raise ValueError("config must be a ResearchProbabilityModelDisagreementConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(estimates, generated_at_utc)
    grouped: dict[str, list[ResearchProbabilityModelDisagreementInput]] = {}
    for row in input_rows:
        grouped.setdefault(row.public_case_key, []).append(row)
    rows = tuple(
        sorted(
            (
                _build_row(
                    public_case_key=public_case_key,
                    estimates=tuple(grouped[public_case_key]),
                    config=config,
                )
                for public_case_key in sorted(grouped)
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    report_values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )
    digest = _digest_from_report_values(report_values)
    return ResearchProbabilityModelDisagreementReport(
        **report_values,
        digest=digest,
    )


def research_probability_model_disagreement_digest(
    report: ResearchProbabilityModelDisagreementReport,
) -> ResearchProbabilityModelDisagreementDigest:
    if type(report) is not ResearchProbabilityModelDisagreementReport:
        raise ValueError("report must be a ResearchProbabilityModelDisagreementReport")
    _require_hard_flags("report", report)
    return _digest_from_report(report)


def research_probability_model_disagreement_report_payload(
    report: ResearchProbabilityModelDisagreementReport,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilityModelDisagreementReport:
        raise ValueError("payload report must be a ResearchProbabilityModelDisagreementReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    _reject_unsafe_public_payload("payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def research_probability_model_disagreement_digest_payload(
    digest: ResearchProbabilityModelDisagreementDigest,
) -> dict[str, Any]:
    if type(digest) is not ResearchProbabilityModelDisagreementDigest:
        raise ValueError("digest must be a ResearchProbabilityModelDisagreementDigest")
    _require_hard_flags("digest", digest)
    payload = _json_ready(digest)
    _reject_unsafe_public_payload("digest payload", payload)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return payload


def _build_row(
    *,
    public_case_key: str,
    estimates: tuple[ResearchProbabilityModelDisagreementInput, ...],
    config: ResearchProbabilityModelDisagreementConfig,
) -> ResearchProbabilityModelDisagreementRow:
    sorted_estimates = tuple(
        sorted(estimates, key=lambda row: (row.participant_label, row.participant_type)),
    )
    probabilities = tuple(row.probability for row in sorted_estimates)
    model_probabilities = tuple(
        row.probability for row in sorted_estimates if row.participant_type == "model"
    )
    research_team_probabilities = tuple(
        row.probability
        for row in sorted_estimates
        if row.participant_type == "research_team"
    )
    min_probability = min(probabilities)
    max_probability = max(probabilities)
    model_mean = _mean(model_probabilities) if model_probabilities else None
    research_team_mean = (
        _mean(research_team_probabilities) if research_team_probabilities else None
    )
    model_team_gap = (
        _quantize(abs(model_mean - research_team_mean))
        if model_mean is not None and research_team_mean is not None
        else None
    )
    probability_range = _quantize(max_probability - min_probability)
    reason_codes = _row_reason_codes(
        estimates=sorted_estimates,
        estimate_count=_count(len(sorted_estimates)),
        model_count=_count(len(model_probabilities)),
        research_team_count=_count(len(research_team_probabilities)),
        probability_range=probability_range,
        model_team_gap=model_team_gap,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchProbabilityModelDisagreementRow(
        public_case_key=public_case_key,
        estimate_count=_count(len(sorted_estimates)),
        model_count=_count(len(model_probabilities)),
        research_team_count=_count(len(research_team_probabilities)),
        participant_labels=tuple(row.participant_label for row in sorted_estimates),
        latest_observed_at=max(row.observed_at for row in sorted_estimates),
        min_probability=min_probability,
        max_probability=max_probability,
        mean_probability=_mean(probabilities),
        model_mean_probability=model_mean,
        research_team_mean_probability=research_team_mean,
        probability_range=probability_range,
        model_team_gap=model_team_gap,
        status=status,
        human_review_status=status,
        reason_codes=tuple(sorted({*reason_codes, f"probability_model_disagreement_{status}"})),
    )


def _row_reason_codes(
    *,
    estimates: tuple[ResearchProbabilityModelDisagreementInput, ...],
    estimate_count: Decimal,
    model_count: Decimal,
    research_team_count: Decimal,
    probability_range: Decimal,
    model_team_gap: Decimal | None,
    config: ResearchProbabilityModelDisagreementConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if estimate_count < config.min_estimate_count:
        reason_codes.append("estimate_count_below_minimum_block")
    if model_count == ZERO:
        reason_codes.append("model_missing_block")
    if research_team_count == ZERO:
        reason_codes.append("research_team_missing_block")
    if probability_range >= config.block_probability_range:
        reason_codes.append("probability_range_block")
    elif probability_range >= config.watch_probability_range:
        reason_codes.append("probability_range_watch")
    if model_team_gap is not None:
        if model_team_gap >= config.block_model_team_gap:
            reason_codes.append("model_team_gap_block")
        elif model_team_gap >= config.watch_model_team_gap:
            reason_codes.append("model_team_gap_watch")
    for estimate in estimates:
        reason_codes.extend(f"input_{reason_code}" for reason_code in estimate.reason_codes)
    return tuple(sorted(set(reason_codes)))


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    status: str,
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[ResearchProbabilityModelDisagreementReasonCodeCount, ...],
    rows: tuple[ResearchProbabilityModelDisagreementRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "status": status,
        "human_review_status": status,
        "case_count": _count(len(rows)),
        "estimate_count": sum((row.estimate_count for row in rows), ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_probability_range": _max_decimal(
            tuple(row.probability_range for row in rows),
        ),
        "max_model_team_gap": _max_decimal(
            tuple(row.model_team_gap for row in rows if row.model_team_gap is not None),
        ),
        "average_probability_range": _mean(
            tuple(row.probability_range for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
    }


def _digest_from_report(
    report: ResearchProbabilityModelDisagreementReport,
) -> ResearchProbabilityModelDisagreementDigest:
    return _digest_from_report_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "human_review_status": report.human_review_status,
            "case_count": report.case_count,
            "estimate_count": report.estimate_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "max_probability_range": report.max_probability_range,
            "max_model_team_gap": report.max_model_team_gap,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
        },
    )


def _digest_from_report_values(
    values: dict[str, Any],
) -> ResearchProbabilityModelDisagreementDigest:
    return ResearchProbabilityModelDisagreementDigest(
        generated_at=values["generated_at"],
        config_version=values["config_version"],
        status=values["status"],
        human_review_status=values["human_review_status"],
        case_count=values["case_count"],
        estimate_count=values["estimate_count"],
        pass_count=values["pass_count"],
        watch_count=values["watch_count"],
        block_count=values["block_count"],
        max_probability_range=values["max_probability_range"],
        max_model_team_gap=values["max_model_team_gap"],
        reason_codes=values["reason_codes"],
        reason_code_counts=values["reason_code_counts"],
    )


def _normalize_inputs(
    estimates: Iterable[ResearchProbabilityModelDisagreementInput],
    generated_at: datetime,
) -> tuple[ResearchProbabilityModelDisagreementInput, ...]:
    if isinstance(estimates, (str, bytes)):
        raise ValueError("estimates must be an iterable")
    try:
        rows = tuple(estimates)
    except TypeError as exc:
        raise ValueError("estimates must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityModelDisagreementInput:
            raise ValueError(
                "estimates must contain ResearchProbabilityModelDisagreementInput values",
            )
        _require_hard_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.public_case_key, row.participant_type, row.participant_label)
        if key in seen:
            raise ValueError("estimates must not contain duplicate public participant rows")
        seen.add(key)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchProbabilityModelDisagreementRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityModelDisagreementRow:
            raise ValueError(
                "rows must contain ResearchProbabilityModelDisagreementRow values",
            )
        _require_hard_flags("row", row)
        if row.public_case_key in seen:
            raise ValueError("rows must not contain duplicate public_case_key values")
        seen.add(row.public_case_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchProbabilityModelDisagreementReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityModelDisagreementReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchProbabilityModelDisagreementReasonCodeCount values",
            )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    expected = tuple(sorted(rows, key=lambda row: (-row.count, row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return rows


def _normalize_public_strings(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        _require_public_string(field_name, value)
    if values != tuple(sorted(values)):
        raise ValueError(f"{field_name} must use canonical sequence")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_public_string(field_name, reason_code)
    if value != tuple(sorted(value)):
        raise ValueError(f"{field_name} must use canonical sequence")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _report_reason_codes(
    rows: tuple[ResearchProbabilityModelDisagreementRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchProbabilityModelDisagreementRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchProbabilityModelDisagreementReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchProbabilityModelDisagreementReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                case_ratio=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    case_count = _count(len(rows))
    return tuple(
        ResearchProbabilityModelDisagreementReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            case_ratio=_ratio(_count(counter[reason_code]), case_count),
        )
        for reason_code in sorted(reason_codes, key=lambda code: (-counter[code], code))
    )


def _row_sort_key(
    row: ResearchProbabilityModelDisagreementRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        -STATUS_SEVERITY[row.status],
        -max(row.probability_range, row.model_team_gap or ZERO),
        -row.probability_range,
        row.public_case_key,
    )


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchProbabilityModelDisagreementRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchProbabilityModelDisagreementRow) -> None:
    if row.estimate_count != _count(len(row.participant_labels)):
        raise ValueError("estimate_count must match participant_labels")
    if row.model_count + row.research_team_count != row.estimate_count:
        raise ValueError("participant type counts must match estimate_count")
    if row.min_probability > row.max_probability:
        raise ValueError("min_probability must be less than or equal to max_probability")
    if row.probability_range != _quantize(row.max_probability - row.min_probability):
        raise ValueError("probability_range must match min_probability and max_probability")
    expected_status = _status_from_reason_codes(
        tuple(
            reason_code
            for reason_code in row.reason_codes
            if not reason_code.startswith("probability_model_disagreement_")
        ),
    )
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.human_review_status != row.status:
        raise ValueError("human_review_status must match status")
    if f"probability_model_disagreement_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_digest(digest: ResearchProbabilityModelDisagreementDigest) -> None:
    if digest.human_review_status != digest.status:
        raise ValueError("human_review_status must match status")
    if digest.case_count != digest.pass_count + digest.watch_count + digest.block_count:
        raise ValueError("status counts must match case_count")
    if digest.status != _status_from_counts(
        pass_count=digest.pass_count,
        watch_count=digest.watch_count,
        block_count=digest.block_count,
        case_count=digest.case_count,
    ):
        raise ValueError("status must match status counts")


def _validate_report(report: ResearchProbabilityModelDisagreementReport) -> None:
    if report.human_review_status != report.status:
        raise ValueError("human_review_status must match status")
    if report.case_count != _count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.estimate_count != sum((row.estimate_count for row in report.rows), ZERO):
        raise ValueError("estimate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _rollup_status(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.max_probability_range != _max_decimal(
        tuple(row.probability_range for row in report.rows),
    ):
        raise ValueError("max_probability_range must match rows")
    if report.max_model_team_gap != _max_decimal(
        tuple(row.model_team_gap for row in report.rows if row.model_team_gap is not None),
    ):
        raise ValueError("max_model_team_gap must match rows")
    if report.average_probability_range != _mean(
        tuple(row.probability_range for row in report.rows),
    ):
        raise ValueError("average_probability_range must match rows")
    if report.digest != _digest_from_report(report):
        raise ValueError("digest must match report")


def _status_from_counts(
    *,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    case_count: Decimal,
) -> str:
    if case_count == ZERO:
        return "block"
    if block_count > ZERO:
        return "block"
    if watch_count > ZERO:
        return "watch"
    if pass_count == case_count:
        return "pass"
    raise ValueError("status counts are inconsistent")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_participant_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PARTICIPANT_TYPES:
        raise ValueError(f"{field_name} must be model or research_team")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in ALLOWED_PUBLIC_CHARS for character in value):
        raise ValueError(f"{field_name} must contain only public identifier characters")
    _reject_unsafe_public_text(field_name, value)
    return value


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in UNSAFE_PUBLIC_TOKENS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    payload = _json_ready(value)
    encoded = repr(payload).lower()
    if any(token in encoded for token in UNSAFE_PUBLIC_TOKENS):
        raise ValueError(f"{field_name} contains unsafe public payload")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_less_than(
    left_name: str,
    left_value: Decimal,
    right_name: str,
    right_value: Decimal,
) -> None:
    if left_value >= right_value:
        raise ValueError(f"{right_name} must be greater than {left_name}")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    number = _require_nonnegative_decimal(field_name, value)
    if number > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return number


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    number = _require_nonnegative_decimal(field_name, value)
    if number != number.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return number


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    number = _require_nonnegative_whole_decimal(field_name, value)
    if number <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return number


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return number


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(QUANTUM)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("payload numeric values must use Decimal strings")
    if type(value) is float:
        raise ValueError("payload must not contain floats")
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("payload contains unsupported value")
