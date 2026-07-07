"""Pure paper/report source-authority scoring for candidate support."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "candidate-decision-source-authority-score-v0"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("5")
DECIMAL_CONTEXT_PRECISION = 28
AUTHORITY_STATUSES = ("pass", "watch", "blocked")
SAFETY_FLAGS = (
    "paper_only",
    "report_only",
    "readonly",
    "local_facts_only",
    "redacted_candidate_refs_only",
    "no_execution_surface",
)
REDACTED_CANDIDATE_REF_PREFIX = "redacted-candidate-"
_STATUS_SORT_RANK = {"blocked": Decimal("0"), "pass": Decimal("1"), "watch": Decimal("2")}
_UNSAFE_TERM_PARTS = (
    ("reco", "mmendation"),
    ("reco", "mmend"),
    ("bu", "y"),
    ("se", "ll"),
    ("long", "_", "position"),
    ("short", "_", "position"),
    ("position", "_", "size"),
    ("position",),
    ("sizing",),
    ("sta", "ke"),
    ("sha", "res"),
    ("contr", "acts"),
    ("fi", "ll"),
    ("exec", "ute"),
    ("exec", "uted"),
    ("access", "_", "token"),
    ("api", "_", "key"),
    ("auth", "_", "token"),
    ("author", "ization"),
    ("bear", "er"),
    ("coo", "kie"),
    ("cs", "rf"),
    ("log", "in"),
    ("sign", "ature"),
    ("pri", "vate_", "key"),
    ("pri", "vate_", "token"),
    ("to", "ken"),
    ("se", "cret"),
    ("pass", "word"),
    ("cred", "ential"),
    ("sess", "ion"),
    ("j", "wt"),
    ("o", "auth"),
    ("wal", "let"),
    ("acco", "unt"),
    ("or", "der"),
    ("tra", "de"),
    ("trad", "ing"),
    ("position", "_", "sizing"),
    ("d", "sn"),
    ("connection", "_", "string"),
    ("ta", "ble"),
    ("sche", "ma"),
    ("ware", "house"),
    ("jd", "bc"),
    ("od", "bc"),
    ("postgres", "ql"),
    ("my", "sql"),
    ("sq", "lite"),
    ("snow", "flake"),
    ("big", "query"),
    ("red", "shift"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("ex", "change"),
    ("can", "cel"),
    ("re", "place"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_RAW_REFERENCE_TERM_PARTS = (
    ("candidate", "_id"),
    ("candidate", "-id"),
    ("mar", "ket", "_id"),
    ("mar", "ket", "_slug"),
    ("mar", "ket", "-"),
    ("event", "_slug"),
    ("slug",),
    ("norm", "alized_", "mar", "ket_", "ques", "tion"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "_refs"),
    ("source", "_url"),
    ("source", "_id"),
    ("source", "-ref"),
    ("source", "-url"),
    ("source", "-id"),
    ("url",),
    ("://",),
    ("www", "."),
)
_RAW_REFERENCE_TERMS = tuple("".join(parts) for parts in _RAW_REFERENCE_TERM_PARTS)
_ROW_DIGEST_FIELDS = (
    "candidate_ref",
    "official_source_count",
    "primary_source_count",
    "independent_source_count",
    "conflicting_source_count",
    "source_hierarchy_score",
    "recency_score",
    "authority_score",
    "authority_status",
    "safety_flags",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "max_authority_score",
    "min_authority_score",
    "average_authority_score",
    "report_status",
    "safety_flags",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionSourceAuthorityScoreConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_authority_score: Decimal = Decimal("0.700000")
    min_watch_authority_score: Decimal = Decimal("0.300000")
    official_source_count_cap: Decimal = Decimal("2")
    primary_source_count_cap: Decimal = Decimal("2")
    independent_source_count_cap: Decimal = Decimal("3")
    conflicting_source_block_count: Decimal = Decimal("1")
    strong_source_hierarchy_score: Decimal = Decimal("0.700000")
    current_recency_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceAuthorityScoreConfig:
            raise TypeError(
                "CandidateDecisionSourceAuthorityScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionSourceAuthorityScoreConfig:
            raise ValueError("config must be a CandidateDecisionSourceAuthorityScoreConfig")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_authority_score",
            "min_watch_authority_score",
            "strong_source_hierarchy_score",
            "current_recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_count_cap",
            "primary_source_count_cap",
            "independent_source_count_cap",
            "conflicting_source_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_authority_score > self.min_pass_authority_score:
            raise ValueError("min_watch_authority_score must be no greater than pass threshold")
        _require_paper_flags("source authority config", self)
        reject_candidate_decision_source_authority_score_unsafe_payload(
            "source authority config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceAuthorityScoreInput:
    candidate_ref: str
    official_source_count: Decimal
    primary_source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    source_hierarchy_score: Decimal
    recency_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceAuthorityScoreInput:
            raise TypeError(
                "CandidateDecisionSourceAuthorityScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionSourceAuthorityScoreInput:
            raise ValueError(
                "score input must be exactly CandidateDecisionSourceAuthorityScoreInput",
            )
        object.__setattr__(
            self,
            "candidate_ref",
            _require_redacted_candidate_ref("candidate_ref", self.candidate_ref),
        )
        for field_name in (
            "official_source_count",
            "primary_source_count",
            "independent_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_hierarchy_score", "recency_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_paper_flags("source authority input", self)
        reject_candidate_decision_source_authority_score_unsafe_payload(
            "source authority input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceAuthorityScoreRow:
    candidate_ref: str
    official_source_count: Decimal
    primary_source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    source_hierarchy_score: Decimal
    recency_score: Decimal
    authority_score: Decimal
    authority_status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceAuthorityScoreRow:
            raise TypeError(
                "CandidateDecisionSourceAuthorityScoreRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionSourceAuthorityScoreRow:
            raise ValueError("row must be exactly CandidateDecisionSourceAuthorityScoreRow")
        object.__setattr__(
            self,
            "candidate_ref",
            _require_redacted_candidate_ref("candidate_ref", self.candidate_ref),
        )
        for field_name in (
            "official_source_count",
            "primary_source_count",
            "independent_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_hierarchy_score",
            "recency_score",
            "authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("authority_status", self.authority_status, AUTHORITY_STATUSES)
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_paper_flags("source authority row", self)
        reject_candidate_decision_source_authority_score_unsafe_payload(
            "source authority row",
            self,
        )
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_source_authority_score_payload(self)


@dataclass(frozen=True)
class CandidateDecisionSourceAuthorityScoreReport:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_authority_score: Decimal
    min_authority_score: Decimal
    average_authority_score: Decimal
    report_status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionSourceAuthorityScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceAuthorityScoreReport:
            raise TypeError(
                "CandidateDecisionSourceAuthorityScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionSourceAuthorityScoreReport:
            raise ValueError("report must be exactly CandidateDecisionSourceAuthorityScoreReport")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_authority_score",
            "min_authority_score",
            "average_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("report_status", self.report_status, AUTHORITY_STATUSES)
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_paper_flags("source authority report", self)
        reject_candidate_decision_source_authority_score_unsafe_payload(
            "source authority report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_source_authority_score_payload(self)


def score_candidate_decision_source_authority(
    score_input: CandidateDecisionSourceAuthorityScoreInput,
    *,
    config: CandidateDecisionSourceAuthorityScoreConfig | None = None,
) -> CandidateDecisionSourceAuthorityScoreRow:
    if type(score_input) is not CandidateDecisionSourceAuthorityScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionSourceAuthorityScoreInput",
        )
    row_config = config or CandidateDecisionSourceAuthorityScoreConfig()
    if type(row_config) is not CandidateDecisionSourceAuthorityScoreConfig:
        raise ValueError("config must be a CandidateDecisionSourceAuthorityScoreConfig")
    _require_paper_flags("source authority input", score_input)
    _require_paper_flags("source authority config", row_config)
    reject_candidate_decision_source_authority_score_unsafe_payload(
        "source authority input",
        score_input,
    )
    reject_candidate_decision_source_authority_score_unsafe_payload(
        "source authority config",
        row_config,
    )

    authority_score = _authority_score(score_input, row_config)
    authority_status = _authority_status(score_input, row_config, authority_score)
    return CandidateDecisionSourceAuthorityScoreRow(
        candidate_ref=score_input.candidate_ref,
        official_source_count=score_input.official_source_count,
        primary_source_count=score_input.primary_source_count,
        independent_source_count=score_input.independent_source_count,
        conflicting_source_count=score_input.conflicting_source_count,
        source_hierarchy_score=score_input.source_hierarchy_score,
        recency_score=score_input.recency_score,
        authority_score=authority_score,
        authority_status=authority_status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_row_reason_codes(
            score_input.reason_codes,
            score_input,
            row_config,
            authority_score,
            authority_status,
        ),
    )


def build_candidate_decision_source_authority_score_report(
    candidates: Iterable[CandidateDecisionSourceAuthorityScoreInput],
    *,
    config: CandidateDecisionSourceAuthorityScoreConfig | None = None,
) -> CandidateDecisionSourceAuthorityScoreReport:
    report_config = config or CandidateDecisionSourceAuthorityScoreConfig()
    if type(report_config) is not CandidateDecisionSourceAuthorityScoreConfig:
        raise ValueError("config must be a CandidateDecisionSourceAuthorityScoreConfig")
    _require_paper_flags("source authority config", report_config)
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (
                score_candidate_decision_source_authority(
                    candidate_input,
                    config=report_config,
                )
                for candidate_input in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    statuses = tuple(row.authority_status for row in rows)
    report_status = _report_status(statuses)
    return CandidateDecisionSourceAuthorityScoreReport(
        config_version=report_config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.authority_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.authority_status == "watch")),
        blocked_count=_count(sum(1 for row in rows if row.authority_status == "blocked")),
        max_authority_score=_max_authority_score(rows),
        min_authority_score=_min_authority_score(rows),
        average_authority_score=_average_authority_score(rows),
        report_status=report_status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_report_reason_codes(rows, report_status),
        rows=rows,
    )


def candidate_decision_source_authority_score_payload(
    value: CandidateDecisionSourceAuthorityScoreRow
    | CandidateDecisionSourceAuthorityScoreReport,
) -> dict[str, Any]:
    if type(value) is CandidateDecisionSourceAuthorityScoreRow:
        _require_paper_flags("source authority row", value)
        if value.derived_validation_digest != _row_digest(value):
            raise ValueError("derived_validation_digest must match row fields")
    elif type(value) is CandidateDecisionSourceAuthorityScoreReport:
        _require_paper_flags("source authority report", value)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    else:
        raise ValueError("value must be a source authority row or report")
    reject_candidate_decision_source_authority_score_unsafe_payload(
        "source authority payload",
        value,
    )
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a dict")
    return ready


def reject_candidate_decision_source_authority_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_entries(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}: {path}")
        if any(term in lowered for term in _RAW_REFERENCE_TERMS):
            raise ValueError(f"raw reference public payload entry in {label}: {path}")


def _authority_score(
    score_input: CandidateDecisionSourceAuthorityScoreInput,
    config: CandidateDecisionSourceAuthorityScoreConfig,
) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context)
        total = (
            _source_count_component(
                score_input.official_source_count,
                config.official_source_count_cap,
            )
            + _source_count_component(
                score_input.primary_source_count,
                config.primary_source_count_cap,
            )
            + _source_count_component(
                score_input.independent_source_count,
                config.independent_source_count_cap,
            )
            + score_input.source_hierarchy_score
            + score_input.recency_score
        )
        return _normalize_unit_decimal("authority_score", total / COMPONENT_COUNT)


def _source_count_component(source_count: Decimal, source_count_cap: Decimal) -> Decimal:
    if source_count >= source_count_cap:
        return ONE
    with localcontext() as context:
        _set_decimal_context(context)
        return _normalize_unit_decimal("source_count_component", source_count / source_count_cap)


def _authority_status(
    score_input: CandidateDecisionSourceAuthorityScoreInput,
    config: CandidateDecisionSourceAuthorityScoreConfig,
    authority_score: Decimal,
) -> str:
    if score_input.conflicting_source_count >= config.conflicting_source_block_count:
        return "blocked"
    if authority_score < config.min_watch_authority_score:
        return "blocked"
    if authority_score < config.min_pass_authority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    existing: tuple[str, ...],
    score_input: CandidateDecisionSourceAuthorityScoreInput,
    config: CandidateDecisionSourceAuthorityScoreConfig,
    authority_score: Decimal,
    authority_status: str,
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_source_authority_score",
        f"source_authority_{authority_status}",
        _source_presence_reason("official_sources", score_input.official_source_count),
        _source_presence_reason("primary_sources", score_input.primary_source_count),
        _source_presence_reason("independent_sources", score_input.independent_source_count),
        _conflict_reason(score_input.conflicting_source_count),
    ]
    if score_input.conflicting_source_count >= config.conflicting_source_block_count:
        additions.append("source_conflict_hard_block")
    additions.append(
        _threshold_reason(
            "source_hierarchy",
            score_input.source_hierarchy_score,
            config.strong_source_hierarchy_score,
            "strong",
            "weak",
        ),
    )
    additions.append(
        _threshold_reason(
            "recency",
            score_input.recency_score,
            config.current_recency_score,
            "current",
            "stale",
        ),
    )
    if score_input.conflicting_source_count >= config.conflicting_source_block_count:
        additions.append("authority_score_blocked_by_conflict")
    elif authority_score < config.min_watch_authority_score:
        additions.append("authority_score_below_watch_threshold")
    elif authority_score < config.min_pass_authority_score:
        additions.append("authority_score_below_pass_threshold")
    else:
        additions.append("authority_score_meets_pass_threshold")
    return _append_reason_codes(existing, tuple(additions))


def _source_presence_reason(label: str, value: Decimal) -> str:
    if value > ZERO:
        return f"{label}_present"
    return f"{label}_absent"


def _conflict_reason(conflicting_source_count: Decimal) -> str:
    if conflicting_source_count > ZERO:
        return "conflicting_sources_present"
    return "no_conflicting_sources"


def _threshold_reason(
    label: str,
    value: Decimal,
    threshold: Decimal,
    met_label: str,
    missed_label: str,
) -> str:
    if value >= threshold:
        return f"{label}_{met_label}"
    return f"{label}_{missed_label}"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _report_status(statuses: tuple[str, ...]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if statuses and all(status == "pass" for status in statuses):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[CandidateDecisionSourceAuthorityScoreRow, ...],
    report_status: str,
) -> tuple[str, ...]:
    additions = [f"candidate_decision_source_authority_report_{report_status}"]
    if not rows:
        additions.append("source_authority_report_empty")
    if any(row.authority_status == "pass" for row in rows):
        additions.append("source_authority_report_has_pass")
    if any(row.authority_status == "watch" for row in rows):
        additions.append("source_authority_report_has_watch")
    if any(row.authority_status == "blocked" for row in rows):
        additions.append("source_authority_report_has_blocked")
    if any("source_conflict_hard_block" in row.reason_codes for row in rows):
        additions.append("source_authority_report_conflict_block")
    return _append_reason_codes((), tuple(additions))


def _normalize_inputs(
    candidates: Iterable[CandidateDecisionSourceAuthorityScoreInput],
) -> tuple[CandidateDecisionSourceAuthorityScoreInput, ...]:
    if type(candidates) is str or type(candidates) is bytes:
        raise ValueError("candidates must be an iterable of source authority inputs")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of source authority inputs") from exc
    for item in items:
        if type(item) is not CandidateDecisionSourceAuthorityScoreInput:
            raise ValueError("candidates must contain source authority inputs")
        _require_paper_flags("source authority input", item)
        reject_candidate_decision_source_authority_score_unsafe_payload(
            "source authority input",
            item,
        )
    return items


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionSourceAuthorityScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not CandidateDecisionSourceAuthorityScoreRow:
            raise ValueError("rows must contain source authority rows")
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted")
    return rows


def _row_sort_key(row: CandidateDecisionSourceAuthorityScoreRow) -> tuple[Decimal | str, ...]:
    return (
        _STATUS_SORT_RANK[row.authority_status],
        -row.authority_score,
        row.candidate_ref,
    )


def _validate_row(row: CandidateDecisionSourceAuthorityScoreRow) -> None:
    if row.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match paper boundary")
    status_reason = f"source_authority_{row.authority_status}"
    if status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include authority status")


def _validate_report(report: CandidateDecisionSourceAuthorityScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.authority_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.authority_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(sum(1 for row in rows if row.authority_status == "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.max_authority_score != _max_authority_score(rows):
        raise ValueError("max_authority_score must match rows")
    if report.min_authority_score != _min_authority_score(rows):
        raise ValueError("min_authority_score must match rows")
    if report.average_authority_score != _average_authority_score(rows):
        raise ValueError("average_authority_score must match rows")
    if report.report_status != _report_status(tuple(row.authority_status for row in rows)):
        raise ValueError("report_status must match rows")
    if report.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match paper boundary")


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(str(value)), COUNT_QUANTUM)


def _max_authority_score(rows: tuple[CandidateDecisionSourceAuthorityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_unit_decimal("max_authority_score", max(row.authority_score for row in rows))


def _min_authority_score(rows: tuple[CandidateDecisionSourceAuthorityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_unit_decimal("min_authority_score", min(row.authority_score for row in rows))


def _average_authority_score(rows: tuple[CandidateDecisionSourceAuthorityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext() as context:
        _set_decimal_context(context)
        total = sum((row.authority_score for row in rows), ZERO)
        return _normalize_unit_decimal("average_authority_score", total / _count(len(rows)))


def _row_digest(row: CandidateDecisionSourceAuthorityScoreRow) -> str:
    return _digest_from_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: CandidateDecisionSourceAuthorityScoreReport) -> str:
    return _digest_from_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(value, field_name))}"
        for field_name in field_names
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is str:
        return value
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is tuple:
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if is_dataclass(value) and not isinstance(value, type):
        return "{" + ",".join(
            f"{field.name}={_digest_value(getattr(value, field.name))}"
            for field in fields(value)
            if field.name != "derived_validation_digest"
        ) + "}"
    raise ValueError("digest value must be public scalar data")


def _normalize_safety_flags(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("safety_flags must be a tuple")
    if value != SAFETY_FLAGS:
        raise ValueError("safety_flags must match paper boundary")
    return value


def _normalize_reason_codes(
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
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(value, COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value, QUANTUM)


def _quantize_decimal(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context, value)
        return value.quantize(quantum)


def _set_decimal_context(context: Any, value: Decimal | None = None) -> None:
    context.prec = DECIMAL_CONTEXT_PRECISION
    if value is not None:
        context.prec = max(context.prec, len(value.as_tuple().digits))
    context.rounding = ROUND_HALF_EVEN


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_redacted_candidate_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    candidate_ref = str(value)
    if not candidate_ref.startswith(REDACTED_CANDIDATE_REF_PREFIX):
        raise ValueError(f"{field_name} must be redacted")
    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    if any(character not in allowed_characters for character in candidate_ref):
        raise ValueError(f"{field_name} must be redacted canonical text")
    if candidate_ref == REDACTED_CANDIDATE_REF_PREFIX:
        raise ValueError(f"{field_name} must be redacted")
    return candidate_ref


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_entries(value: object, path: str = "payload") -> tuple[tuple[str, str], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_entries(asdict(value), path)
    if isinstance(value, dict):
        entries: list[tuple[str, str]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            key_path = f"{path}.{key}"
            entries.append((key_path, key))
            entries.extend(_iter_public_entries(item, key_path))
        return tuple(entries)
    if type(value) is str:
        return ((path, value),)
    if isinstance(value, (list, tuple)):
        entries = []
        for index, item in enumerate(value):
            entries.extend(_iter_public_entries(item, f"{path}[{index}]"))
        return tuple(entries)
    return ()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if type(value) is str or type(value) is bool:
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


__all__ = (
    "AUTHORITY_STATUSES",
    "SAFETY_FLAGS",
    "CandidateDecisionSourceAuthorityScoreConfig",
    "CandidateDecisionSourceAuthorityScoreInput",
    "CandidateDecisionSourceAuthorityScoreRow",
    "CandidateDecisionSourceAuthorityScoreReport",
    "score_candidate_decision_source_authority",
    "build_candidate_decision_source_authority_score_report",
    "candidate_decision_source_authority_score_payload",
    "reject_candidate_decision_source_authority_score_unsafe_payload",
)
