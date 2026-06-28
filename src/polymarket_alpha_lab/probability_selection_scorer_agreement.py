from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context


__all__ = (
    "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_CONFIG_VERSION",
    "ProbabilitySelectionScorerAgreementConfig",
    "ProbabilitySelectionScorerAgreementReport",
    "build_probability_selection_scorer_agreement_report",
)


DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_CONFIG_VERSION = (
    "probability-selection-scorer-agreement-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SELECTED_VALUES = frozenset(("ready", "recommend", "recommended", "select", "selected"))
REJECTED_VALUES = frozenset(("block", "blocked", "reject", "rejected"))
SCORED_VALUES = frozenset(("pass", "ready", "recommend", "recommended", "scored"))


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementConfig:
    config_version: str = DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_CONFIG_VERSION
    min_selected_overlap_share: Decimal = ONE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilitySelectionScorerAgreementConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementConfig:
            raise ValueError(
                "config must be exactly ProbabilitySelectionScorerAgreementConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_selected_overlap_share",
            _require_probability(
                "min_selected_overlap_share",
                self.min_selected_overlap_share,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementReport:
    generated_at: datetime
    config_version: str
    selection_generated_at: datetime | None
    scorer_generated_at: datetime | None
    selected_count: int
    scorer_candidate_count: int
    selected_market_overlap_count: int
    selected_condition_overlap_count: int
    rejected_but_scored_count: int
    scored_but_unselected_count: int
    scorer_gate_status: str
    agreement_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_divergence_counts: tuple[tuple[str, int], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilitySelectionScorerAgreementReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementReport:
            raise ValueError(
                "report must be exactly ProbabilitySelectionScorerAgreementReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "selection_generated_at",
            _optional_utc("selection_generated_at", self.selection_generated_at),
        )
        object.__setattr__(
            self,
            "scorer_generated_at",
            _optional_utc("scorer_generated_at", self.scorer_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "selected_count",
            "scorer_candidate_count",
            "selected_market_overlap_count",
            "selected_condition_overlap_count",
            "rejected_but_scored_count",
            "scored_but_unselected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_canonical_string("scorer_gate_status", self.scorer_gate_status)
        _require_status("agreement_status", self.agreement_status)
        _require_next_step("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_divergence_counts",
            _normalize_divergence_counts(self.reason_code_divergence_counts),
        )
        _require_hard_flags("report", self)


@dataclass(frozen=True)
class _SelectionRow:
    market_slug: str | None
    condition_id: str | None
    reason_codes: tuple[str, ...]
    is_selected: bool
    is_rejected: bool


@dataclass(frozen=True)
class _ScorerRow:
    market_slug: str | None
    condition_id: str | None
    reason_codes: tuple[str, ...]
    is_scored: bool


def build_probability_selection_scorer_agreement_report(
    *,
    selection_input: object | None,
    scorer_input: object | None,
    generated_at: datetime,
    config: ProbabilitySelectionScorerAgreementConfig | None = None,
) -> ProbabilitySelectionScorerAgreementReport:
    if config is None:
        config = ProbabilitySelectionScorerAgreementConfig()
    if type(config) is not ProbabilitySelectionScorerAgreementConfig:
        raise ValueError("config must be ProbabilitySelectionScorerAgreementConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)

    missing_inputs = selection_input is None or scorer_input is None
    if selection_input is not None:
        _validate_source_tree("selection_input", selection_input)
    if scorer_input is not None:
        _validate_source_tree("scorer_input", scorer_input)

    selection_rows = _selection_rows(selection_input)
    scorer_rows = _scorer_rows(scorer_input)
    selected_rows = tuple(row for row in selection_rows if row.is_selected)
    rejected_rows = tuple(row for row in selection_rows if row.is_rejected)
    scored_rows = tuple(row for row in scorer_rows if row.is_scored)

    selected_count = _selection_count(selection_input, selected_rows)
    scorer_candidate_count = _scorer_candidate_count(scorer_input, scorer_rows)
    selected_market_overlap_count = _overlap_count(
        selected_rows,
        scored_rows,
        matcher=_same_market,
    )
    selected_condition_overlap_count = _overlap_count(
        selected_rows,
        scored_rows,
        matcher=_same_condition,
    )
    rejected_but_scored_count = sum(
        1 for row in rejected_rows if _row_matches_any(row, scored_rows)
    )
    scored_but_unselected_count = sum(
        1
        for row in scored_rows
        if _row_has_identifier(row) and not _row_matches_any(row, selected_rows)
    )
    divergence_counts = _reason_code_divergence_counts(selected_rows, scored_rows)
    scorer_gate_status = _scorer_gate_status(scorer_input)
    agreement_status = _agreement_status(
        missing_inputs=missing_inputs,
        scorer_gate_status=scorer_gate_status,
        selected_count=selected_count,
        scorer_candidate_count=scorer_candidate_count,
        selected_market_overlap_count=selected_market_overlap_count,
        selected_condition_overlap_count=selected_condition_overlap_count,
        selected_rows=selected_rows,
        scorer_rows=scorer_rows,
        scored_but_unselected_count=scored_but_unselected_count,
        selected_identity_overlap_count=_identity_overlap_count(
            selected_rows,
            scored_rows,
        ),
        config=config,
    )
    reason_codes = _reason_codes(
        agreement_status=agreement_status,
        rejected_but_scored_count=rejected_but_scored_count,
        scored_but_unselected_count=scored_but_unselected_count,
        divergence_counts=divergence_counts,
    )

    return ProbabilitySelectionScorerAgreementReport(
        generated_at=generated_at,
        config_version=config.config_version,
        selection_generated_at=_source_generated_at(selection_input),
        scorer_generated_at=_source_generated_at(scorer_input),
        selected_count=selected_count,
        scorer_candidate_count=scorer_candidate_count,
        selected_market_overlap_count=selected_market_overlap_count,
        selected_condition_overlap_count=selected_condition_overlap_count,
        rejected_but_scored_count=rejected_but_scored_count,
        scored_but_unselected_count=scored_but_unselected_count,
        scorer_gate_status=scorer_gate_status,
        agreement_status=agreement_status,
        recommended_next_step=_recommended_next_step(agreement_status),
        reason_codes=reason_codes,
        reason_code_divergence_counts=divergence_counts,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _validate_source_tree(label: str, value: object) -> None:
    _reject_float_tree(label, value)
    _reject_false_hard_flags(label, value)
    source_config = getattr(value, "config", None)
    if source_config is not None:
        _reject_float_tree(f"{label}.config", source_config)
        _reject_false_hard_flags(f"{label}.config", source_config)
    for rows_name in (
        "rows",
        "selected_rows",
        "score_rows",
        "candidates",
        "candidate_rows",
    ):
        rows = getattr(value, rows_name, None)
        if rows is not None:
            _validate_rows(f"{label}.{rows_name}", rows)


def _validate_rows(label: str, rows: object) -> None:
    if not isinstance(rows, tuple):
        raise ValueError(f"{label} must be a tuple")
    for index, row in enumerate(rows):
        _reject_float_tree(f"{label}.{index}", row)
        _reject_false_hard_flags(f"{label}.{index}", row)


def _selection_rows(source: object | None) -> tuple[_SelectionRow, ...]:
    if source is None:
        return ()
    selected_rows = getattr(source, "selected_rows", None)
    if selected_rows is not None:
        if not isinstance(selected_rows, tuple):
            raise ValueError("selected_rows must be a tuple")
        rows = selected_rows
        force_selected = True
    else:
        rows = _first_rows(source, ("rows",))
        force_selected = False
    return tuple(_selection_row(row, force_selected=force_selected) for row in rows)


def _scorer_rows(source: object | None) -> tuple[_ScorerRow, ...]:
    if source is None:
        return ()
    rows = _first_rows(source, ("score_rows", "candidates", "candidate_rows"))
    return tuple(_scorer_row(row) for row in rows)


def _first_rows(source: object, names: tuple[str, ...]) -> tuple[object, ...]:
    for name in names:
        rows = getattr(source, name, None)
        if rows is not None:
            if not isinstance(rows, tuple):
                raise ValueError(f"{name} must be a tuple")
            return rows
    return ()


def _selection_row(row: object, *, force_selected: bool) -> _SelectionRow:
    marker_values = _marker_values(
        row,
        ("selection_status", "status", "action", "recommendation"),
    )
    is_selected = force_selected or any(value in SELECTED_VALUES for value in marker_values)
    is_rejected = any(value in REJECTED_VALUES for value in marker_values)
    return _SelectionRow(
        market_slug=_optional_canonical_string("market_slug", getattr(row, "market_slug", None)),
        condition_id=_optional_canonical_string("condition_id", getattr(row, "condition_id", None)),
        reason_codes=_normalize_reason_codes(
            "reason_codes",
            getattr(row, "reason_codes", ()),
        ),
        is_selected=is_selected,
        is_rejected=is_rejected,
    )


def _scorer_row(row: object) -> _ScorerRow:
    marker_values = _marker_values(
        row,
        ("score_status", "status", "action", "recommendation"),
    )
    is_scored = not marker_values or any(value in SCORED_VALUES for value in marker_values)
    return _ScorerRow(
        market_slug=_optional_canonical_string("market_slug", getattr(row, "market_slug", None)),
        condition_id=_optional_canonical_string("condition_id", getattr(row, "condition_id", None)),
        reason_codes=_normalize_reason_codes(
            "reason_codes",
            getattr(row, "reason_codes", ()),
        ),
        is_scored=is_scored,
    )


def _selection_count(source: object | None, selected_rows: tuple[_SelectionRow, ...]) -> int:
    if source is None:
        return 0
    source_count = _first_nonnegative_count(
        source,
        ("selected_count", "latest_selected_count", "ready_count"),
        default=None,
    )
    if selected_rows:
        return len(selected_rows)
    if source_count is not None:
        return source_count
    return _first_nonnegative_count(
        source,
        ("selected_count", "latest_selected_count", "ready_count"),
        default=0,
    )


def _scorer_candidate_count(source: object | None, scorer_rows: tuple[_ScorerRow, ...]) -> int:
    if source is None:
        return 0
    source_count = _first_nonnegative_count(
        source,
        ("scorer_candidate_count", "candidate_count", "markets_scored"),
        default=None,
    )
    if scorer_rows:
        return len(scorer_rows)
    if source_count is not None:
        return source_count
    return _first_nonnegative_count(
        source,
        ("scorer_candidate_count", "candidate_count", "markets_scored"),
        default=0,
    )


def _first_nonnegative_count(
    source: object,
    names: tuple[str, ...],
    *,
    default: int | None,
) -> int | None:
    for name in names:
        value = getattr(source, name, None)
        if value is not None:
            _require_nonnegative_int(name, value)
            return value
    return default


def _agreement_status(
    *,
    missing_inputs: bool,
    scorer_gate_status: str,
    selected_count: int,
    scorer_candidate_count: int,
    selected_market_overlap_count: int,
    selected_condition_overlap_count: int,
    selected_rows: tuple[_SelectionRow, ...],
    scorer_rows: tuple[_ScorerRow, ...],
    scored_but_unselected_count: int,
    selected_identity_overlap_count: int,
    config: ProbabilitySelectionScorerAgreementConfig,
) -> str:
    if missing_inputs:
        return "missing_inputs"
    if scorer_gate_status == "blocked":
        return "gate_blocked"
    if _has_insufficient_identifiers(
        selected_count=selected_count,
        scorer_candidate_count=scorer_candidate_count,
        selected_rows=selected_rows,
        scorer_rows=scorer_rows,
    ):
        return "insufficient_identifiers"
    if _has_low_overlap(
        selected_count=selected_count,
        selected_market_overlap_count=selected_market_overlap_count,
        selected_condition_overlap_count=selected_condition_overlap_count,
        scored_but_unselected_count=scored_but_unselected_count,
        selected_identity_overlap_count=selected_identity_overlap_count,
        config=config,
    ):
        return "low_overlap"
    return "aligned"


def _has_insufficient_identifiers(
    *,
    selected_count: int,
    scorer_candidate_count: int,
    selected_rows: tuple[_SelectionRow, ...],
    scorer_rows: tuple[_ScorerRow, ...],
) -> bool:
    if selected_count > 0 and not _has_any_identifier(selected_rows):
        return True
    if scorer_candidate_count > 0 and not _has_any_identifier(scorer_rows):
        return True
    return False


def _has_low_overlap(
    *,
    selected_count: int,
    selected_market_overlap_count: int,
    selected_condition_overlap_count: int,
    scored_but_unselected_count: int,
    selected_identity_overlap_count: int,
    config: ProbabilitySelectionScorerAgreementConfig,
) -> bool:
    del selected_market_overlap_count
    del selected_condition_overlap_count
    if selected_count == 0:
        return scored_but_unselected_count > 0
    with localcontext(DECIMAL_CONTEXT):
        overlap_share = Decimal(selected_identity_overlap_count) / Decimal(selected_count)
    return overlap_share < config.min_selected_overlap_share


def _reason_codes(
    *,
    agreement_status: str,
    rejected_but_scored_count: int,
    scored_but_unselected_count: int,
    divergence_counts: tuple[tuple[str, int], ...],
) -> tuple[str, ...]:
    if agreement_status == "missing_inputs":
        codes = ["missing_inputs"]
    elif agreement_status == "insufficient_identifiers":
        codes = ["insufficient_identifiers"]
    elif agreement_status == "gate_blocked":
        codes = ["scorer_gate_blocked"]
    elif agreement_status == "low_overlap":
        codes = ["low_selection_scorer_overlap"]
    else:
        codes = ["selection_scorer_aligned"]
    if rejected_but_scored_count > 0:
        codes.append("rejected_but_scored")
    if scored_but_unselected_count > 0:
        codes.append("scored_but_unselected")
    if divergence_counts:
        codes.append("reason_code_divergence")
    return tuple(sorted(dict.fromkeys(codes)))


def _recommended_next_step(agreement_status: str) -> str:
    if agreement_status in ("missing_inputs", "insufficient_identifiers"):
        return "enrich_inputs"
    if agreement_status == "gate_blocked":
        return "review_scorer_gate"
    if agreement_status == "low_overlap":
        return "review_selection_scorer_disagreement"
    return "continue_monitoring"


def _reason_code_divergence_counts(
    selected_rows: tuple[_SelectionRow, ...],
    scored_rows: tuple[_ScorerRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    matched_scorer_indexes: set[int] = set()
    for selected_row in selected_rows:
        match_index = _matching_row_index(
            selected_row,
            scored_rows,
            matched_scorer_indexes,
        )
        if match_index is None:
            continue
        matched_scorer_indexes.add(match_index)
        scorer_row = scored_rows[match_index]
        selected_codes = set(selected_row.reason_codes)
        scorer_codes = set(scorer_row.reason_codes)
        for code in selected_codes.symmetric_difference(scorer_codes):
            counts[code] += 1
    return tuple(sorted(counts.items()))


def _matching_row_index(
    selected_row: _SelectionRow,
    scored_rows: tuple[_ScorerRow, ...],
    used_indexes: set[int],
) -> int | None:
    for index, scorer_row in enumerate(scored_rows):
        if index in used_indexes:
            continue
        if _same_identity(selected_row, scorer_row):
            return index
    return None


def _row_matches_any(row: _SelectionRow | _ScorerRow, candidates: Iterable[object]) -> bool:
    for candidate in candidates:
        if _same_identity(row, candidate):
            return True
    return False


def _same_identity(left: object, right: object) -> bool:
    left_condition = getattr(left, "condition_id", None)
    right_condition = getattr(right, "condition_id", None)
    if left_condition is not None and right_condition is not None:
        return left_condition == right_condition
    return _same_market(left, right)


def _same_condition(left: object, right: object) -> bool:
    left_value = getattr(left, "condition_id", None)
    right_value = getattr(right, "condition_id", None)
    return left_value is not None and left_value == right_value


def _same_market(left: object, right: object) -> bool:
    left_value = getattr(left, "market_slug", None)
    right_value = getattr(right, "market_slug", None)
    return left_value is not None and left_value == right_value


def _overlap_count(
    selected_rows: tuple[_SelectionRow, ...],
    scorer_rows: tuple[_ScorerRow, ...],
    *,
    matcher: Callable[[object, object], bool],
) -> int:
    return sum(
        1
        for selected_row in selected_rows
        if any(matcher(selected_row, scorer_row) for scorer_row in scorer_rows)
    )


def _identity_overlap_count(
    selected_rows: tuple[_SelectionRow, ...],
    scorer_rows: tuple[_ScorerRow, ...],
) -> int:
    return sum(
        1
        for selected_row in selected_rows
        if any(_same_identity(selected_row, scorer_row) for scorer_row in scorer_rows)
    )


def _has_any_identifier(rows: Iterable[object]) -> bool:
    for row in rows:
        if _row_has_identifier(row):
            return True
    return False


def _row_has_identifier(row: object) -> bool:
    if getattr(row, "market_slug", None) is not None:
        return True
    if getattr(row, "condition_id", None) is not None:
        return True
    return False


def _scorer_gate_status(source: object | None) -> str:
    if source is None:
        return "missing"
    value = getattr(source, "gate_status", getattr(source, "scorer_gate_status", "unknown"))
    _require_canonical_string("scorer_gate_status", value)
    return value


def _source_generated_at(source: object | None) -> datetime | None:
    if source is None:
        return None
    value = getattr(source, "generated_at", None)
    return _optional_utc("generated_at", value)


def _marker_values(row: object, names: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for name in names:
        value = getattr(row, name, None)
        if value is None:
            continue
        _require_canonical_string(name, value)
        values.append(value)
    return tuple(values)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for code in value:
        _require_canonical_string(field_name, code)
    return tuple(sorted(dict.fromkeys(value)))


def _normalize_divergence_counts(value: object) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_divergence_counts must be a tuple")
    previous_code: str | None = None
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not int
        ):
            raise ValueError("reason_code_divergence_counts entries must be pairs")
        code, count = item
        _require_canonical_string("reason_code_divergence_counts", code)
        _require_nonnegative_int("reason_code_divergence_count", count)
        if count == 0:
            raise ValueError("reason_code_divergence_count must be positive")
        if previous_code is not None and previous_code >= code:
            raise ValueError("reason_code_divergence_counts must be sorted and unique")
        previous_code = code
    return value


def _require_status(field_name: str, value: object) -> None:
    if value not in (
        "aligned",
        "gate_blocked",
        "insufficient_identifiers",
        "low_overlap",
        "missing_inputs",
    ):
        raise ValueError(f"{field_name} is not valid")


def _require_next_step(field_name: str, value: object) -> None:
    if value not in (
        "continue_monitoring",
        "enrich_inputs",
        "review_scorer_gate",
        "review_selection_scorer_disagreement",
    ):
        raise ValueError(f"{field_name} is not valid")


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_false_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if hasattr(value, field_name) and getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_float_tree(
    label: str,
    value: object,
    *,
    seen: set[int] | None = None,
) -> None:
    if type(value) is float:
        raise ValueError(f"{label} must not be a float")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if value is None or isinstance(value, (str, bool, int, datetime)):
        return
    if seen is None:
        seen = set()
    value_id = id(value)
    if value_id in seen:
        return
    seen.add(value_id)
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_float_tree(f"{label}.<key>", key, seen=seen)
            _reject_float_tree(f"{label}.{key}", item, seen=seen)
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_float_tree(f"{label}.{index}", item, seen=seen)
        return
    if isinstance(value, (list, set, frozenset)):
        for index, item in enumerate(value):
            _reject_float_tree(f"{label}.{index}", item, seen=seen)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_float_tree(
                f"{label}.{field.name}",
                getattr(value, field.name),
                seen=seen,
            )
        return
    if hasattr(value, "__dict__"):
        for field_name, item in vars(value).items():
            _reject_float_tree(f"{label}.{field_name}", item, seen=seen)
