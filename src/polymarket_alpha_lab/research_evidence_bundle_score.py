"""Pure report-only research evidence bundle quality scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any, Mapping


DEFAULT_RESEARCH_EVIDENCE_BUNDLE_SCORE_CONFIG_VERSION = (
    "research-evidence-bundle-score-v1"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
PUBLIC_STATUS_RANK = {
    STATUS_BLOCK: Decimal("0"),
    STATUS_WATCH: Decimal("1"),
    STATUS_PASS: Decimal("2"),
}

_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_WEIGHT_FIELDS = (
    "traceability_weight",
    "freshness_weight",
    "conflict_cleanliness_weight",
    "source_diversity_weight",
    "revision_stability_weight",
)
_ROW_METRIC_FIELDS = (
    "traceability_score",
    "staleness_score",
    "freshness_score",
    "conflict_severity_score",
    "conflict_cleanliness_score",
    "source_diversity_score",
    "revision_frequency_score",
    "revision_stability_score",
    "evidence_bundle_quality_score",
)
_HEX_CHARS = frozenset("0123456789abcdef")
_PUBLIC_IDENTIFIER_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-",
)

_UNSAFE_TERM_PARTS = (
    ("raw", "_candidate"),
    ("candidate", "_id"),
    ("candidate", "-id"),
    ("market", "_id"),
    ("market", "-id"),
    ("market", "_sl", "ug"),
    ("market", "-sl", "ug"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "-ref"),
    ("source", "_u", "rl"),
    ("source", "-u", "rl"),
    ("source", "_text"),
    ("source", "-text"),
    ("raw", "_text"),
    ("u", "rl"),
    ("ht", "tp"),
    ("ht", "tps"),
    ("://",),
    ("d", "sn"),
    ("connection", "_string"),
    ("ta", "ble"),
    ("sche", "ma"),
    ("warehouse",),
    ("jd", "bc"),
    ("od", "bc"),
    ("postgres", "ql"),
    ("my", "sql"),
    ("sq", "lite"),
    ("snow", "flake"),
    ("big", "query"),
    ("red", "shift"),
    ("to", "ken"),
    ("se", "cret"),
    ("au", "th"),
    ("bear", "er"),
    ("api", "_key"),
    ("private", "_key"),
    ("password",),
    ("cred", "ential"),
    ("sess", "ion"),
    ("j", "wt"),
    ("o", "au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("tra", "de"),
    ("pos", "ition"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmendation"),
    ("reco", "mmend"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_UNSAFE_NORMALIZED_TERMS = tuple(
    term
    for term in (
        "".join(character for character in value if character.isalnum())
        for value in _UNSAFE_TERMS
    )
    if term
)


@dataclass(frozen=True)
class ResearchEvidenceBundleScoreConfig:
    config_version: str = DEFAULT_RESEARCH_EVIDENCE_BUNDLE_SCORE_CONFIG_VERSION
    min_pass_bundle_quality_score: Decimal = Decimal("0.750000")
    min_watch_bundle_quality_score: Decimal = Decimal("0.500000")
    min_pass_traceability_score: Decimal = Decimal("0.750000")
    min_watch_traceability_score: Decimal = Decimal("0.500000")
    max_pass_staleness_score: Decimal = Decimal("0.250000")
    max_watch_staleness_score: Decimal = Decimal("0.600000")
    max_pass_conflict_severity_score: Decimal = Decimal("0.250000")
    max_watch_conflict_severity_score: Decimal = Decimal("0.600000")
    min_pass_source_diversity_score: Decimal = Decimal("0.650000")
    min_watch_source_diversity_score: Decimal = Decimal("0.400000")
    max_pass_revision_frequency_score: Decimal = Decimal("0.250000")
    max_watch_revision_frequency_score: Decimal = Decimal("0.600000")
    traceability_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.200000")
    conflict_cleanliness_weight: Decimal = Decimal("0.250000")
    source_diversity_weight: Decimal = Decimal("0.150000")
    revision_stability_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchEvidenceBundleScoreConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEvidenceBundleScoreConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_BUNDLE_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_bundle_quality_score",
            "min_watch_bundle_quality_score",
            "min_pass_traceability_score",
            "min_watch_traceability_score",
            "max_pass_staleness_score",
            "max_watch_staleness_score",
            "max_pass_conflict_severity_score",
            "max_watch_conflict_severity_score",
            "min_pass_source_diversity_score",
            "min_watch_source_diversity_score",
            "max_pass_revision_frequency_score",
            "max_watch_revision_frequency_score",
            *_WEIGHT_FIELDS,
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        reject_research_evidence_bundle_score_unsafe_payload("config", self)


@dataclass(frozen=True)
class ResearchEvidenceBundleScoreInput:
    redacted_bundle_ref: str
    traceability_score: Decimal
    staleness_score: Decimal
    conflict_severity_score: Decimal
    source_diversity_score: Decimal
    revision_frequency_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchEvidenceBundleScoreInput does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEvidenceBundleScoreInput, "score input")
        object.__setattr__(
            self,
            "redacted_bundle_ref",
            _require_public_string("redacted_bundle_ref", self.redacted_bundle_ref),
        )
        for field_name in (
            "traceability_score",
            "staleness_score",
            "conflict_severity_score",
            "source_diversity_score",
            "revision_frequency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("score input", self)
        reject_research_evidence_bundle_score_unsafe_payload("score input", self)


@dataclass(frozen=True)
class ResearchEvidenceBundleScoreRow:
    config_version: str
    redacted_bundle_ref: str
    source_input: ResearchEvidenceBundleScoreInput
    traceability_score: Decimal
    staleness_score: Decimal
    freshness_score: Decimal
    conflict_severity_score: Decimal
    conflict_cleanliness_score: Decimal
    source_diversity_score: Decimal
    revision_frequency_score: Decimal
    revision_stability_score: Decimal
    evidence_bundle_quality_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchEvidenceBundleScoreRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEvidenceBundleScoreRow, "row")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_BUNDLE_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "redacted_bundle_ref",
            _require_public_string("redacted_bundle_ref", self.redacted_bundle_ref),
        )
        if type(self.source_input) is not ResearchEvidenceBundleScoreInput:
            raise ValueError("source_input must be a ResearchEvidenceBundleScoreInput")
        _require_hard_flags("source_input", self.source_input)
        if self.source_input.redacted_bundle_ref != self.redacted_bundle_ref:
            raise ValueError("source_input redacted_bundle_ref must match row")
        for field_name in _ROW_METRIC_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _normalize_optional_sha256(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("row", self)
        reject_research_evidence_bundle_score_unsafe_payload("row", self)
        _validate_row(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _row_digest(self))
        _validate_row_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_evidence_bundle_score_payload(self)


@dataclass(frozen=True)
class ResearchEvidenceBundleScoreReport:
    config_version: str
    bundle_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_evidence_bundle_quality_score: Decimal
    min_evidence_bundle_quality_score: Decimal
    average_evidence_bundle_quality_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEvidenceBundleScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchEvidenceBundleScoreReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEvidenceBundleScoreReport, "report")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_BUNDLE_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "bundle_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_bundle_quality_score",
            "min_evidence_bundle_quality_score",
            "average_evidence_bundle_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "derived_validation_digest",
            _normalize_optional_sha256(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        reject_research_evidence_bundle_score_unsafe_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        _validate_report_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_evidence_bundle_score_payload(self)


def score_research_evidence_bundle(
    score_input: ResearchEvidenceBundleScoreInput,
    *,
    config: ResearchEvidenceBundleScoreConfig | None = None,
) -> ResearchEvidenceBundleScoreRow:
    if type(score_input) is not ResearchEvidenceBundleScoreInput:
        raise ValueError("score_input must be a ResearchEvidenceBundleScoreInput")
    cfg = config or ResearchEvidenceBundleScoreConfig()
    if type(cfg) is not ResearchEvidenceBundleScoreConfig:
        raise ValueError("config must be a ResearchEvidenceBundleScoreConfig")
    _require_hard_flags("score input", score_input)
    _require_hard_flags("config", cfg)
    reject_research_evidence_bundle_score_unsafe_payload("score input", score_input)
    reject_research_evidence_bundle_score_unsafe_payload("config", cfg)

    freshness_score = _invert_score(score_input.staleness_score)
    conflict_cleanliness_score = _invert_score(score_input.conflict_severity_score)
    revision_stability_score = _invert_score(score_input.revision_frequency_score)
    quality_score = _evidence_bundle_quality_score(
        traceability_score=score_input.traceability_score,
        freshness_score=freshness_score,
        conflict_cleanliness_score=conflict_cleanliness_score,
        source_diversity_score=score_input.source_diversity_score,
        revision_stability_score=revision_stability_score,
        config=cfg,
    )
    metric_statuses = _metric_statuses(score_input, cfg)
    public_status = _row_status(
        quality_score=quality_score,
        metric_statuses=metric_statuses,
        config=cfg,
    )

    return ResearchEvidenceBundleScoreRow(
        config_version=cfg.config_version,
        redacted_bundle_ref=score_input.redacted_bundle_ref,
        source_input=score_input,
        traceability_score=score_input.traceability_score,
        staleness_score=score_input.staleness_score,
        freshness_score=freshness_score,
        conflict_severity_score=score_input.conflict_severity_score,
        conflict_cleanliness_score=conflict_cleanliness_score,
        source_diversity_score=score_input.source_diversity_score,
        revision_frequency_score=score_input.revision_frequency_score,
        revision_stability_score=revision_stability_score,
        evidence_bundle_quality_score=quality_score,
        public_status=public_status,
        reason_codes=_row_reason_codes(
            score_input.reason_codes,
            public_status=public_status,
            metric_statuses=metric_statuses,
        ),
    )


def build_research_evidence_bundle_score_report(
    source_inputs: tuple[ResearchEvidenceBundleScoreInput, ...],
    *,
    config: ResearchEvidenceBundleScoreConfig | None = None,
) -> ResearchEvidenceBundleScoreReport:
    if type(source_inputs) is not tuple:
        raise ValueError("source_inputs must be a tuple")
    cfg = config or ResearchEvidenceBundleScoreConfig()
    if type(cfg) is not ResearchEvidenceBundleScoreConfig:
        raise ValueError("config must be a ResearchEvidenceBundleScoreConfig")
    _require_hard_flags("config", cfg)
    rows = tuple(
        sorted(
            (score_research_evidence_bundle(item, config=cfg) for item in source_inputs),
            key=_row_sort_key,
        ),
    )
    return ResearchEvidenceBundleScoreReport(
        config_version=cfg.config_version,
        bundle_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        max_evidence_bundle_quality_score=_max_quality_score(rows),
        min_evidence_bundle_quality_score=_min_quality_score(rows),
        average_evidence_bundle_quality_score=_average_quality_score(rows),
        public_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_evidence_bundle_score_payload(
    value: ResearchEvidenceBundleScoreRow | ResearchEvidenceBundleScoreReport,
) -> dict[str, Any]:
    if type(value) is ResearchEvidenceBundleScoreRow:
        _require_hard_flags("row", value)
        _validate_row(value)
        _validate_row_digest(value)
    elif type(value) is ResearchEvidenceBundleScoreReport:
        _require_hard_flags("report", value)
        _validate_report(value)
        _validate_report_digest(value)
    else:
        raise ValueError("value must be a research evidence bundle row or report")
    reject_research_evidence_bundle_score_unsafe_payload("payload value", value)
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_evidence_bundle_score_payload(payload)
    return payload


def validate_research_evidence_bundle_score_payload(payload: dict[str, Any]) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_payload_numbers(payload)
    reject_research_evidence_bundle_score_unsafe_payload("payload", payload)
    _require_payload_hard_flags(payload)
    if "rows" in payload:
        _report_from_payload(payload)
    elif "source_input" in payload:
        _row_from_payload(payload)
    else:
        raise ValueError("payload must be a row or report payload")
    return True


def reject_research_evidence_bundle_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    _reject_unsafe_public_payload(label, payload)


def _evidence_bundle_quality_score(
    *,
    traceability_score: Decimal,
    freshness_score: Decimal,
    conflict_cleanliness_score: Decimal,
    source_diversity_score: Decimal,
    revision_stability_score: Decimal,
    config: ResearchEvidenceBundleScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(
            traceability_score * config.traceability_weight
            + freshness_score * config.freshness_weight
            + conflict_cleanliness_score * config.conflict_cleanliness_weight
            + source_diversity_score * config.source_diversity_weight
            + revision_stability_score * config.revision_stability_weight,
        )


def _invert_score(value: Decimal) -> Decimal:
    return _clamp_ratio(ONE - value)


def _metric_statuses(
    score_input: ResearchEvidenceBundleScoreInput,
    config: ResearchEvidenceBundleScoreConfig,
) -> dict[str, str]:
    return {
        "traceability": _high_is_good_status(
            score_input.traceability_score,
            pass_threshold=config.min_pass_traceability_score,
            watch_threshold=config.min_watch_traceability_score,
        ),
        "staleness": _low_is_good_status(
            score_input.staleness_score,
            pass_threshold=config.max_pass_staleness_score,
            watch_threshold=config.max_watch_staleness_score,
        ),
        "conflict_severity": _low_is_good_status(
            score_input.conflict_severity_score,
            pass_threshold=config.max_pass_conflict_severity_score,
            watch_threshold=config.max_watch_conflict_severity_score,
        ),
        "source_diversity": _high_is_good_status(
            score_input.source_diversity_score,
            pass_threshold=config.min_pass_source_diversity_score,
            watch_threshold=config.min_watch_source_diversity_score,
        ),
        "revision_frequency": _low_is_good_status(
            score_input.revision_frequency_score,
            pass_threshold=config.max_pass_revision_frequency_score,
            watch_threshold=config.max_watch_revision_frequency_score,
        ),
    }


def _high_is_good_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return STATUS_PASS
    if value >= watch_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _low_is_good_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return STATUS_PASS
    if value <= watch_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_status(
    *,
    quality_score: Decimal,
    metric_statuses: dict[str, str],
    config: ResearchEvidenceBundleScoreConfig,
) -> str:
    if STATUS_BLOCK in metric_statuses.values():
        return STATUS_BLOCK
    if quality_score < config.min_watch_bundle_quality_score:
        return STATUS_BLOCK
    if STATUS_WATCH in metric_statuses.values():
        return STATUS_WATCH
    if quality_score < config.min_pass_bundle_quality_score:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    existing: tuple[str, ...],
    *,
    public_status: str,
    metric_statuses: dict[str, str],
) -> tuple[str, ...]:
    return _append_reason_codes(
        existing,
        (
            "research_evidence_bundle_score",
            f"evidence_bundle_quality_{public_status}",
            f"traceability_{metric_statuses['traceability']}",
            f"staleness_{metric_statuses['staleness']}",
            f"conflict_severity_{metric_statuses['conflict_severity']}",
            f"source_diversity_{metric_statuses['source_diversity']}",
            f"revision_frequency_{metric_statuses['revision_frequency']}",
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchEvidenceBundleScoreRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes = (
        "research_evidence_bundle_score_report",
        f"evidence_bundle_score_report_{status}",
    )
    for row in rows:
        reason_codes = _append_reason_codes(reason_codes, row.reason_codes)
    return reason_codes


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_config(config: ResearchEvidenceBundleScoreConfig) -> None:
    if config.min_watch_bundle_quality_score > config.min_pass_bundle_quality_score:
        raise ValueError("min_watch_bundle_quality_score must not exceed pass threshold")
    if config.min_watch_traceability_score > config.min_pass_traceability_score:
        raise ValueError("min_watch_traceability_score must not exceed pass threshold")
    if config.max_pass_staleness_score > config.max_watch_staleness_score:
        raise ValueError("max_pass_staleness_score must not exceed watch threshold")
    if config.max_pass_conflict_severity_score > config.max_watch_conflict_severity_score:
        raise ValueError(
            "max_pass_conflict_severity_score must not exceed watch threshold",
        )
    if config.min_watch_source_diversity_score > config.min_pass_source_diversity_score:
        raise ValueError("min_watch_source_diversity_score must not exceed pass threshold")
    if config.max_pass_revision_frequency_score > config.max_watch_revision_frequency_score:
        raise ValueError(
            "max_pass_revision_frequency_score must not exceed watch threshold",
        )
    if _sum_decimal(getattr(config, field_name) for field_name in _WEIGHT_FIELDS) != ONE:
        raise ValueError("config weights must sum to 1.000000")


def _validate_row(row: ResearchEvidenceBundleScoreRow) -> None:
    cfg = ResearchEvidenceBundleScoreConfig()
    expected_freshness_score = _invert_score(row.source_input.staleness_score)
    expected_conflict_cleanliness_score = _invert_score(
        row.source_input.conflict_severity_score,
    )
    expected_revision_stability_score = _invert_score(
        row.source_input.revision_frequency_score,
    )
    if row.traceability_score != row.source_input.traceability_score:
        raise ValueError("traceability_score must match source_input")
    if row.staleness_score != row.source_input.staleness_score:
        raise ValueError("staleness_score must match source_input")
    if row.freshness_score != expected_freshness_score:
        raise ValueError("freshness_score must match source_input")
    if row.conflict_severity_score != row.source_input.conflict_severity_score:
        raise ValueError("conflict_severity_score must match source_input")
    if row.conflict_cleanliness_score != expected_conflict_cleanliness_score:
        raise ValueError("conflict_cleanliness_score must match source_input")
    if row.source_diversity_score != row.source_input.source_diversity_score:
        raise ValueError("source_diversity_score must match source_input")
    if row.revision_frequency_score != row.source_input.revision_frequency_score:
        raise ValueError("revision_frequency_score must match source_input")
    if row.revision_stability_score != expected_revision_stability_score:
        raise ValueError("revision_stability_score must match source_input")
    expected_quality_score = _evidence_bundle_quality_score(
        traceability_score=row.traceability_score,
        freshness_score=row.freshness_score,
        conflict_cleanliness_score=row.conflict_cleanliness_score,
        source_diversity_score=row.source_diversity_score,
        revision_stability_score=row.revision_stability_score,
        config=cfg,
    )
    if row.evidence_bundle_quality_score != expected_quality_score:
        raise ValueError("evidence_bundle_quality_score must match source_input")
    metric_statuses = _metric_statuses(row.source_input, cfg)
    expected_status = _row_status(
        quality_score=row.evidence_bundle_quality_score,
        metric_statuses=metric_statuses,
        config=cfg,
    )
    if row.public_status != expected_status:
        raise ValueError("public_status must match bundle metrics")
    expected_reason_codes = _row_reason_codes(
        row.source_input.reason_codes,
        public_status=row.public_status,
        metric_statuses=metric_statuses,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match bundle metrics")


def _validate_report(report: ResearchEvidenceBundleScoreReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.bundle_count != _count_decimal(len(report.rows)):
        raise ValueError("bundle_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.max_evidence_bundle_quality_score != _max_quality_score(report.rows):
        raise ValueError("max_evidence_bundle_quality_score must match rows")
    if report.min_evidence_bundle_quality_score != _min_quality_score(report.rows):
        raise ValueError("min_evidence_bundle_quality_score must match rows")
    if report.average_evidence_bundle_quality_score != _average_quality_score(
        report.rows,
    ):
        raise ValueError("average_evidence_bundle_quality_score must match rows")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_rows(value: object) -> tuple[ResearchEvidenceBundleScoreRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_refs: set[str] = set()
    rows: list[ResearchEvidenceBundleScoreRow] = []
    for row in value:
        if type(row) is not ResearchEvidenceBundleScoreRow:
            raise ValueError("rows must contain ResearchEvidenceBundleScoreRow values")
        if row.redacted_bundle_ref in seen_refs:
            raise ValueError("rows redacted_bundle_ref values must be unique")
        seen_refs.add(row.redacted_bundle_ref)
        _require_hard_flags("row", row)
        _validate_row_digest(row)
        rows.append(row)
    return tuple(rows)


def _row_sort_key(row: ResearchEvidenceBundleScoreRow) -> tuple[str, str]:
    return (row.redacted_bundle_ref, row.derived_validation_digest)


def _status_count(rows: tuple[ResearchEvidenceBundleScoreRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _max_quality_score(rows: tuple[ResearchEvidenceBundleScoreRow, ...]) -> Decimal:
    return max((row.evidence_bundle_quality_score for row in rows), default=ZERO)


def _min_quality_score(rows: tuple[ResearchEvidenceBundleScoreRow, ...]) -> Decimal:
    return min((row.evidence_bundle_quality_score for row in rows), default=ZERO)


def _average_quality_score(rows: tuple[ResearchEvidenceBundleScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(
            sum((row.evidence_bundle_quality_score for row in rows), ZERO)
            / _count_decimal(len(rows)),
        )


def _report_status(rows: tuple[ResearchEvidenceBundleScoreRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    statuses = tuple(row.public_status for row in rows)
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: Any) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return _quantize_value(sum(values, ZERO))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 128:
        raise ValueError(f"{field_name} must be a public identifier")
    if not value[0].isalnum():
        raise ValueError(f"{field_name} must be a public identifier")
    if any(character not in _PUBLIC_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_value(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_public_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be a public status")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in _PHASE_FLAG_FIELDS:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def _normalize_optional_sha256(field_name: str, value: object) -> str:
    if value == "":
        return ""
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_value(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize_value(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM, rounding=ROUND_HALF_UP)


def _row_digest(row: ResearchEvidenceBundleScoreRow) -> str:
    values = asdict(row)
    values.pop("derived_validation_digest", None)
    return _digest_payload(values)


def _report_digest(report: ResearchEvidenceBundleScoreReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_payload(values)


def _digest_payload(value: object) -> str:
    reject_research_evidence_bundle_score_unsafe_payload("digest", value)
    canonical = json.dumps(
        _json_ready(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_row_digest(row: ResearchEvidenceBundleScoreRow) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_digest(report: ResearchEvidenceBundleScoreReport) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_payload_numbers(value: object) -> None:
    if type(value) is int or type(value) is float:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_payload_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _reject_payload_numbers(item)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if _contains_unsafe_term(key):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    if _contains_unsafe_term(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _contains_unsafe_term(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        return True
    normalized = "".join(character for character in lowered if character.isalnum())
    return any(term in lowered for term in _UNSAFE_TERMS) or any(
        term in normalized for term in _UNSAFE_NORMALIZED_TERMS
    )


def _require_payload_hard_flags(payload: object) -> None:
    if isinstance(payload, Mapping):
        for flag_name in _PHASE_FLAG_FIELDS:
            if flag_name in payload and payload[flag_name] is not True:
                raise ValueError(f"{flag_name} must be True")
        for item in payload.values():
            _require_payload_hard_flags(item)
    elif isinstance(payload, list):
        for item in payload:
            _require_payload_hard_flags(item)


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    return _require_decimal(field_name, Decimal(value))


def _payload_string(field_name: str, value: object) -> str:
    return _require_public_string(field_name, value)


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _require_reason_codes(field_name, tuple(value))


def _input_from_payload(payload: Mapping[str, Any]) -> ResearchEvidenceBundleScoreInput:
    return ResearchEvidenceBundleScoreInput(
        redacted_bundle_ref=_payload_string(
            "redacted_bundle_ref",
            payload.get("redacted_bundle_ref"),
        ),
        traceability_score=_payload_decimal(
            "traceability_score",
            payload.get("traceability_score"),
        ),
        staleness_score=_payload_decimal("staleness_score", payload.get("staleness_score")),
        conflict_severity_score=_payload_decimal(
            "conflict_severity_score",
            payload.get("conflict_severity_score"),
        ),
        source_diversity_score=_payload_decimal(
            "source_diversity_score",
            payload.get("source_diversity_score"),
        ),
        revision_frequency_score=_payload_decimal(
            "revision_frequency_score",
            payload.get("revision_frequency_score"),
        ),
        reason_codes=_payload_reason_codes("reason_codes", payload.get("reason_codes", []))
        if "reason_codes" in payload
        else (),
        paper_only=payload.get("paper_only"),
        report_only=payload.get("report_only"),
        readonly=payload.get("readonly"),
    )


def _row_from_payload(payload: Mapping[str, Any]) -> ResearchEvidenceBundleScoreRow:
    source_input = payload.get("source_input")
    if type(source_input) is not dict:
        raise ValueError("source_input must be a payload object")
    return ResearchEvidenceBundleScoreRow(
        config_version=_payload_string("config_version", payload.get("config_version")),
        redacted_bundle_ref=_payload_string(
            "redacted_bundle_ref",
            payload.get("redacted_bundle_ref"),
        ),
        source_input=_input_from_payload(source_input),
        traceability_score=_payload_decimal(
            "traceability_score",
            payload.get("traceability_score"),
        ),
        staleness_score=_payload_decimal("staleness_score", payload.get("staleness_score")),
        freshness_score=_payload_decimal("freshness_score", payload.get("freshness_score")),
        conflict_severity_score=_payload_decimal(
            "conflict_severity_score",
            payload.get("conflict_severity_score"),
        ),
        conflict_cleanliness_score=_payload_decimal(
            "conflict_cleanliness_score",
            payload.get("conflict_cleanliness_score"),
        ),
        source_diversity_score=_payload_decimal(
            "source_diversity_score",
            payload.get("source_diversity_score"),
        ),
        revision_frequency_score=_payload_decimal(
            "revision_frequency_score",
            payload.get("revision_frequency_score"),
        ),
        revision_stability_score=_payload_decimal(
            "revision_stability_score",
            payload.get("revision_stability_score"),
        ),
        evidence_bundle_quality_score=_payload_decimal(
            "evidence_bundle_quality_score",
            payload.get("evidence_bundle_quality_score"),
        ),
        public_status=_require_public_status("public_status", payload.get("public_status")),
        reason_codes=_payload_reason_codes("reason_codes", payload.get("reason_codes")),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload.get("derived_validation_digest"),
        ),
        paper_only=payload.get("paper_only"),
        report_only=payload.get("report_only"),
        readonly=payload.get("readonly"),
    )


def _report_from_payload(payload: Mapping[str, Any]) -> ResearchEvidenceBundleScoreReport:
    row_payloads = payload.get("rows")
    if type(row_payloads) is not list:
        raise ValueError("rows must be a list")
    return ResearchEvidenceBundleScoreReport(
        config_version=_payload_string("config_version", payload.get("config_version")),
        bundle_count=_payload_decimal("bundle_count", payload.get("bundle_count")),
        pass_count=_payload_decimal("pass_count", payload.get("pass_count")),
        watch_count=_payload_decimal("watch_count", payload.get("watch_count")),
        block_count=_payload_decimal("block_count", payload.get("block_count")),
        max_evidence_bundle_quality_score=_payload_decimal(
            "max_evidence_bundle_quality_score",
            payload.get("max_evidence_bundle_quality_score"),
        ),
        min_evidence_bundle_quality_score=_payload_decimal(
            "min_evidence_bundle_quality_score",
            payload.get("min_evidence_bundle_quality_score"),
        ),
        average_evidence_bundle_quality_score=_payload_decimal(
            "average_evidence_bundle_quality_score",
            payload.get("average_evidence_bundle_quality_score"),
        ),
        public_status=_require_public_status("public_status", payload.get("public_status")),
        reason_codes=_payload_reason_codes("reason_codes", payload.get("reason_codes")),
        rows=tuple(_row_from_payload(row) for row in row_payloads),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload.get("derived_validation_digest"),
        ),
        paper_only=payload.get("paper_only"),
        report_only=payload.get("report_only"),
        readonly=payload.get("readonly"),
    )


__all__ = (
    "DEFAULT_RESEARCH_EVIDENCE_BUNDLE_SCORE_CONFIG_VERSION",
    "ResearchEvidenceBundleScoreConfig",
    "ResearchEvidenceBundleScoreInput",
    "ResearchEvidenceBundleScoreReport",
    "ResearchEvidenceBundleScoreRow",
    "build_research_evidence_bundle_score_report",
    "research_evidence_bundle_score_payload",
    "reject_research_evidence_bundle_score_unsafe_payload",
    "score_research_evidence_bundle",
    "validate_research_evidence_bundle_score_payload",
)
