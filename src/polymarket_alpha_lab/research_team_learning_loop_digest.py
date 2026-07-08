"""Pure report-only research team learning loop digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_LEARNING_LOOP_DIGEST_CONFIG_VERSION",
    "ResearchTeamLearningLoopDigestConfig",
    "ResearchTeamLearningLoopDigestInput",
    "ResearchTeamLearningLoopDigestReasonCodeCount",
    "ResearchTeamLearningLoopDigestReport",
    "ResearchTeamLearningLoopDigestRow",
    "build_research_team_learning_loop_digest",
    "research_team_learning_loop_digest_payload",
)


DEFAULT_RESEARCH_TEAM_LEARNING_LOOP_DIGEST_CONFIG_VERSION = (
    "research-team-learning-loop-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

NO_INPUTS_REASON = "research_team_learning_loop_no_inputs"
PASS_REASON = "research_team_learning_loop_pass"
WATCH_REASON = "research_team_learning_loop_watch"
BLOCK_REASON = "research_team_learning_loop_block"
POSTMORTEM_LEARNING_REASON = "research_team_learning_loop_postmortem_learning"
THIN_POSTMORTEM_REASON = "research_team_learning_loop_thin_postmortem_history"
CALIBRATION_OK_REASON = "research_team_learning_loop_calibration_ok"
CALIBRATION_DRIFT_WATCH_REASON = "research_team_learning_loop_calibration_drift_watch"
CALIBRATION_DRIFT_BLOCK_REASON = "research_team_learning_loop_calibration_drift_block"
INFORMATION_GAP_NONE_REASON = "research_team_learning_loop_information_gap_none"
INFORMATION_GAP_CLOSED_REASON = "research_team_learning_loop_information_gap_closed"
INFORMATION_GAP_WATCH_REASON = "research_team_learning_loop_information_gap_watch"
INFORMATION_GAP_BLOCK_REASON = "research_team_learning_loop_information_gap_block"
CONFIDENCE_PASS_REASON = "research_team_learning_loop_confidence_pass"
CONFIDENCE_WATCH_REASON = "research_team_learning_loop_confidence_watch"
CONFIDENCE_BLOCK_REASON = "research_team_learning_loop_confidence_block"

REASON_CODE_SEQUENCE = (
    BLOCK_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    CALIBRATION_OK_REASON,
    CONFIDENCE_BLOCK_REASON,
    CONFIDENCE_PASS_REASON,
    CONFIDENCE_WATCH_REASON,
    INFORMATION_GAP_BLOCK_REASON,
    INFORMATION_GAP_CLOSED_REASON,
    INFORMATION_GAP_NONE_REASON,
    INFORMATION_GAP_WATCH_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    POSTMORTEM_LEARNING_REASON,
    THIN_POSTMORTEM_REASON,
    WATCH_REASON,
)

BLOCKING_REASON_CODES = frozenset(
    (
        BLOCK_REASON,
        CALIBRATION_DRIFT_BLOCK_REASON,
        CONFIDENCE_BLOCK_REASON,
        INFORMATION_GAP_BLOCK_REASON,
        NO_INPUTS_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        CALIBRATION_DRIFT_WATCH_REASON,
        CONFIDENCE_WATCH_REASON,
        INFORMATION_GAP_WATCH_REASON,
        THIN_POSTMORTEM_REASON,
        WATCH_REASON,
    ),
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_STATUS_NEXT_STEPS = {
    STATUS_PASS: "allow_public_learning_loop_digest",
    STATUS_WATCH: "watch_public_learning_loop_digest",
    STATUS_BLOCK: "block_public_learning_loop_digest",
}

LINK_PATTERN = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s)>\]]+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
HEX_ID_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


def _join(*parts: str) -> str:
    return "".join(parts)


PRIVATE_MARKERS = (
    _join("acc", "ount"),
    _join("ad", "vice"),
    _join("api", "_key"),
    "apikey",
    _join("au", "th"),
    "bearer",
    _join("bro", "ker"),
    _join("bu", "y"),
    _join("can", "cel"),
    _join("can", "didate"),
    _join("data", "base"),
    _join("ds", "n"),
    _join("exe", "cute"),
    _join("mar", "ket"),
    _join("or", "der"),
    "password",
    _join("posi", "tion"),
    _join("ques", "tion"),
    _join("re", "commend"),
    _join("re", "f"),
    _join("sec", "ret"),
    _join("sel", "l"),
    _join("sig", "ning"),
    _join("slu", "g"),
    _join("sour", "ce"),
    _join("sub", "mit"),
    _join("ta", "ble"),
    _join("to", "ken"),
    _join("tra", "de"),
    _join("wal", "let"),
)


@dataclass(frozen=True)
class ResearchTeamLearningLoopDigestConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_LEARNING_LOOP_DIGEST_CONFIG_VERSION
    max_pass_calibration_drift_count: Decimal = Decimal("0.000000")
    max_watch_calibration_drift_count: Decimal = Decimal("2.000000")
    max_pass_open_information_gap_count: Decimal = Decimal("0.000000")
    max_watch_open_information_gap_count: Decimal = Decimal("1.000000")
    max_pass_calibration_error_delta: Decimal = Decimal("0.050000")
    max_watch_calibration_error_delta: Decimal = Decimal("0.150000")
    min_pass_confidence_score: Decimal = Decimal("0.750000")
    min_watch_confidence_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamLearningLoopDigestConfig:
            raise TypeError(
                "ResearchTeamLearningLoopDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamLearningLoopDigestConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_pass_calibration_drift_count",
            "max_watch_calibration_drift_count",
            "max_pass_open_information_gap_count",
            "max_watch_open_information_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_pass_calibration_error_delta",
            "max_watch_calibration_error_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_confidence_score", "min_watch_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_calibration_drift_count < self.max_pass_calibration_drift_count:
            raise ValueError("watch drift threshold must not be below pass threshold")
        if (
            self.max_watch_open_information_gap_count
            < self.max_pass_open_information_gap_count
        ):
            raise ValueError("watch gap threshold must not be below pass threshold")
        if self.max_watch_calibration_error_delta < self.max_pass_calibration_error_delta:
            raise ValueError("watch delta threshold must not be below pass threshold")
        if self.min_watch_confidence_score > self.min_pass_confidence_score:
            raise ValueError("watch confidence threshold must not exceed pass threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamLearningLoopDigestInput:
    team_key: str
    specialty_key: str
    learning_label: str
    observed_at: datetime
    postmortem_count: Decimal
    calibration_drift_count: Decimal
    information_gap_count: Decimal
    closed_information_gap_count: Decimal
    calibration_error_delta: Decimal
    confidence_score: Decimal
    lesson_summary: str
    trace_marker: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamLearningLoopDigestInput:
            raise TypeError(
                "ResearchTeamLearningLoopDigestInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamLearningLoopDigestInput, "input")
        for field_name in ("team_key", "specialty_key", "learning_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "postmortem_count",
            "calibration_drift_count",
            "information_gap_count",
            "closed_information_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.closed_information_gap_count > self.information_gap_count:
            raise ValueError("closed information gaps must not exceed total gaps")
        object.__setattr__(
            self,
            "calibration_error_delta",
            _require_delta_decimal(
                "calibration_error_delta",
                self.calibration_error_delta,
            ),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        _require_note("lesson_summary", self.lesson_summary, allow_empty=False)
        _require_note("trace_marker", self.trace_marker, allow_empty=True)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamLearningLoopDigestRow:
    team_key: str
    specialty_key: str
    learning_key: str
    public_learning_label: str
    team_status: str
    observed_at: datetime
    postmortem_count: Decimal
    calibration_drift_count: Decimal
    information_gap_count: Decimal
    closed_information_gap_count: Decimal
    open_information_gap_count: Decimal
    calibration_error_delta: Decimal
    confidence_score: Decimal
    information_gap_closure_ratio: Decimal
    public_lesson_digest: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamLearningLoopDigestRow:
            raise TypeError(
                "ResearchTeamLearningLoopDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamLearningLoopDigestRow, "row")
        for field_name in ("team_key", "specialty_key", "public_learning_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_digest_string("learning_key", self.learning_key)
        _require_public_status("team_status", self.team_status)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "postmortem_count",
            "calibration_drift_count",
            "information_gap_count",
            "closed_information_gap_count",
            "open_information_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_delta",
            _require_delta_decimal(
                "calibration_error_delta",
                self.calibration_error_delta,
            ),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "information_gap_closure_ratio",
            _require_ratio_decimal(
                "information_gap_closure_ratio",
                self.information_gap_closure_ratio,
            ),
        )
        _require_digest_string("public_lesson_digest", self.public_lesson_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.team_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("team_status must match reason_codes")
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamLearningLoopDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    team_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamLearningLoopDigestReasonCodeCount:
            raise TypeError(
                "ResearchTeamLearningLoopDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamLearningLoopDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )


@dataclass(frozen=True)
class ResearchTeamLearningLoopDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    postmortem_count: Decimal
    calibration_drift_count: Decimal
    information_gap_count: Decimal
    closed_information_gap_count: Decimal
    open_information_gap_count: Decimal
    information_gap_closure_ratio: Decimal
    average_confidence_score: Decimal
    max_calibration_error_delta: Decimal
    digest_rows: tuple[ResearchTeamLearningLoopDigestRow, ...]
    reason_code_counts: tuple[ResearchTeamLearningLoopDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamLearningLoopDigestReport:
            raise TypeError(
                "ResearchTeamLearningLoopDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamLearningLoopDigestReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_public_status("digest_status", self.digest_status)
        if self.next_step != _STATUS_NEXT_STEPS[self.digest_status]:
            raise ValueError("next_step must match digest_status")
        for field_name in (
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "postmortem_count",
            "calibration_drift_count",
            "information_gap_count",
            "closed_information_gap_count",
            "open_information_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_gap_closure_ratio",
            _require_ratio_decimal(
                "information_gap_closure_ratio",
                self.information_gap_closure_ratio,
            ),
        )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_ratio_decimal(
                "average_confidence_score",
                self.average_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "max_calibration_error_delta",
            _require_delta_decimal(
                "max_calibration_error_delta",
                self.max_calibration_error_delta,
            ),
        )
        object.__setattr__(
            self,
            "digest_rows",
            _normalize_rows("digest_rows", self.digest_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(
                "reason_code_counts",
                self.reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_team_learning_loop_digest(
    rows: Iterable[ResearchTeamLearningLoopDigestInput],
    *,
    config: ResearchTeamLearningLoopDigestConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamLearningLoopDigestReport:
    cfg = config or ResearchTeamLearningLoopDigestConfig()
    if type(cfg) is not ResearchTeamLearningLoopDigestConfig:
        raise TypeError(
            "config must be exactly ResearchTeamLearningLoopDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs("rows", rows)
    for item in input_rows:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    digest_rows = tuple(
        sorted(
            (
                _digest_row_from_input(item, config=cfg)
                for item in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    _require_unique_learning_keys(digest_rows)
    reason_counts = _reason_code_counts(digest_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    digest_status = _report_status(digest_rows)
    return ResearchTeamLearningLoopDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=_STATUS_NEXT_STEPS[digest_status],
        team_count=_count_decimal(len(digest_rows)),
        pass_count=_count_decimal(_status_count(digest_rows, STATUS_PASS)),
        watch_count=_count_decimal(_status_count(digest_rows, STATUS_WATCH)),
        block_count=_count_decimal(_status_count(digest_rows, STATUS_BLOCK)),
        postmortem_count=_sum_decimal(
            tuple(row.postmortem_count for row in digest_rows),
        ),
        calibration_drift_count=_sum_decimal(
            tuple(row.calibration_drift_count for row in digest_rows),
        ),
        information_gap_count=_sum_decimal(
            tuple(row.information_gap_count for row in digest_rows),
        ),
        closed_information_gap_count=_sum_decimal(
            tuple(row.closed_information_gap_count for row in digest_rows),
        ),
        open_information_gap_count=_sum_decimal(
            tuple(row.open_information_gap_count for row in digest_rows),
        ),
        information_gap_closure_ratio=_ratio(
            _sum_decimal(tuple(row.closed_information_gap_count for row in digest_rows)),
            _sum_decimal(tuple(row.information_gap_count for row in digest_rows)),
        ),
        average_confidence_score=_average(
            tuple(row.confidence_score for row in digest_rows),
        ),
        max_calibration_error_delta=_max_or_zero(
            tuple(row.calibration_error_delta for row in digest_rows),
        ),
        digest_rows=digest_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_team_learning_loop_digest_payload(
    report: ResearchTeamLearningLoopDigestReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamLearningLoopDigestReport:
        raise TypeError("report must be exactly ResearchTeamLearningLoopDigestReport")
    _require_hard_flags("report", report)
    value = _payload_value(report)
    if not isinstance(value, dict):
        raise ValueError("digest payload must be a JSON object")
    return value


def _digest_row_from_input(
    item: ResearchTeamLearningLoopDigestInput,
    *,
    config: ResearchTeamLearningLoopDigestConfig,
) -> ResearchTeamLearningLoopDigestRow:
    open_gap_count = item.information_gap_count - item.closed_information_gap_count
    reason_codes = _row_reason_codes(
        item,
        open_gap_count=open_gap_count,
        config=config,
    )
    team_status = _status_from_reason_codes(reason_codes)
    return ResearchTeamLearningLoopDigestRow(
        team_key=item.team_key,
        specialty_key=item.specialty_key,
        learning_key=_learning_key(item),
        public_learning_label=item.learning_label,
        team_status=team_status,
        observed_at=item.observed_at,
        postmortem_count=item.postmortem_count,
        calibration_drift_count=item.calibration_drift_count,
        information_gap_count=item.information_gap_count,
        closed_information_gap_count=item.closed_information_gap_count,
        open_information_gap_count=open_gap_count,
        calibration_error_delta=item.calibration_error_delta,
        confidence_score=item.confidence_score,
        information_gap_closure_ratio=_ratio(
            item.closed_information_gap_count,
            item.information_gap_count,
        ),
        public_lesson_digest=_public_digest(item.lesson_summary, item.trace_marker),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamLearningLoopDigestInput,
    *,
    open_gap_count: Decimal,
    config: ResearchTeamLearningLoopDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.postmortem_count == ZERO:
        reason_codes.append(THIN_POSTMORTEM_REASON)
    else:
        reason_codes.append(POSTMORTEM_LEARNING_REASON)

    if (
        item.calibration_drift_count > config.max_watch_calibration_drift_count
        or item.calibration_error_delta > config.max_watch_calibration_error_delta
    ):
        reason_codes.append(CALIBRATION_DRIFT_BLOCK_REASON)
    elif (
        item.calibration_drift_count > config.max_pass_calibration_drift_count
        or item.calibration_error_delta > config.max_pass_calibration_error_delta
    ):
        reason_codes.append(CALIBRATION_DRIFT_WATCH_REASON)
    else:
        reason_codes.append(CALIBRATION_OK_REASON)

    if open_gap_count > config.max_watch_open_information_gap_count:
        reason_codes.append(INFORMATION_GAP_BLOCK_REASON)
    elif open_gap_count > config.max_pass_open_information_gap_count:
        reason_codes.append(INFORMATION_GAP_WATCH_REASON)
    elif item.information_gap_count == ZERO:
        reason_codes.append(INFORMATION_GAP_NONE_REASON)
    else:
        reason_codes.append(INFORMATION_GAP_CLOSED_REASON)

    if item.confidence_score < config.min_watch_confidence_score:
        reason_codes.append(CONFIDENCE_BLOCK_REASON)
    elif item.confidence_score < config.min_pass_confidence_score:
        reason_codes.append(CONFIDENCE_WATCH_REASON)
    else:
        reason_codes.append(CONFIDENCE_PASS_REASON)

    status = _status_from_reason_codes(tuple(reason_codes))
    if status == STATUS_BLOCK:
        reason_codes.append(BLOCK_REASON)
    elif status == STATUS_WATCH:
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchTeamLearningLoopDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.team_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.team_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchTeamLearningLoopDigestRow, ...],
) -> tuple[ResearchTeamLearningLoopDigestReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamLearningLoopDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_ratio=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchTeamLearningLoopDigestReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            team_ratio=_ratio(counts[reason_code], _count_decimal(len(rows))),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row_consistency(row: ResearchTeamLearningLoopDigestRow) -> None:
    if row.closed_information_gap_count > row.information_gap_count:
        raise ValueError("closed information gaps must not exceed total gaps")
    if (
        row.open_information_gap_count
        != row.information_gap_count - row.closed_information_gap_count
    ):
        raise ValueError("open_information_gap_count must match gap counts")
    if row.information_gap_closure_ratio != _ratio(
        row.closed_information_gap_count,
        row.information_gap_count,
    ):
        raise ValueError("information_gap_closure_ratio must match gap counts")


def _validate_report_consistency(report: ResearchTeamLearningLoopDigestReport) -> None:
    rows = report.digest_rows
    if report.team_count != _count_decimal(len(rows)):
        raise ValueError("team_count must match digest_rows")
    if report.pass_count != _count_decimal(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match digest_rows")
    if report.watch_count != _count_decimal(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match digest_rows")
    if report.block_count != _count_decimal(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match digest_rows")
    if report.postmortem_count != _sum_decimal(tuple(row.postmortem_count for row in rows)):
        raise ValueError("postmortem_count must match digest_rows")
    if report.calibration_drift_count != _sum_decimal(
        tuple(row.calibration_drift_count for row in rows),
    ):
        raise ValueError("calibration_drift_count must match digest_rows")
    if report.information_gap_count != _sum_decimal(
        tuple(row.information_gap_count for row in rows),
    ):
        raise ValueError("information_gap_count must match digest_rows")
    if report.closed_information_gap_count != _sum_decimal(
        tuple(row.closed_information_gap_count for row in rows),
    ):
        raise ValueError("closed_information_gap_count must match digest_rows")
    if report.open_information_gap_count != _sum_decimal(
        tuple(row.open_information_gap_count for row in rows),
    ):
        raise ValueError("open_information_gap_count must match digest_rows")
    if report.information_gap_closure_ratio != _ratio(
        report.closed_information_gap_count,
        report.information_gap_count,
    ):
        raise ValueError("information_gap_closure_ratio must match gap counts")
    if report.average_confidence_score != _average(
        tuple(row.confidence_score for row in rows),
    ):
        raise ValueError("average_confidence_score must match digest_rows")
    if report.max_calibration_error_delta != _max_or_zero(
        tuple(row.calibration_error_delta for row in rows),
    ):
        raise ValueError("max_calibration_error_delta must match digest_rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match digest_rows")
    expected_reason_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match digest_rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_inputs(
    field_name: str,
    rows: Iterable[ResearchTeamLearningLoopDigestInput],
) -> tuple[ResearchTeamLearningLoopDigestInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise TypeError(f"{field_name} must be an iterable")
    values = tuple(rows)
    for value in values:
        if type(value) is not ResearchTeamLearningLoopDigestInput:
            raise TypeError(
                f"{field_name} must contain ResearchTeamLearningLoopDigestInput values",
            )
        _require_hard_flags("input", value)
    return values


def _normalize_rows(
    field_name: str,
    rows: tuple[ResearchTeamLearningLoopDigestRow, ...],
) -> tuple[ResearchTeamLearningLoopDigestRow, ...]:
    if type(rows) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for row in rows:
        if type(row) is not ResearchTeamLearningLoopDigestRow:
            raise TypeError(
                f"{field_name} must contain ResearchTeamLearningLoopDigestRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    _require_unique_learning_keys(sorted_rows)
    return sorted_rows


def _normalize_reason_code_counts(
    field_name: str,
    counts: tuple[ResearchTeamLearningLoopDigestReasonCodeCount, ...],
) -> tuple[ResearchTeamLearningLoopDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for count in counts:
        if type(count) is not ResearchTeamLearningLoopDigestReasonCodeCount:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchTeamLearningLoopDigestReasonCodeCount values",
            )
    sorted_counts = tuple(sorted(counts, key=lambda item: _reason_rank(item.reason_code)))
    seen: set[str] = set()
    for count in sorted_counts:
        if count.reason_code in seen:
            raise ValueError("duplicate reason_code")
        seen.add(count.reason_code)
    return sorted_counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in normalized:
            raise ValueError("duplicate reason_code")
        normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_rank))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    _require_safe_payload_string(value)


def _row_sort_key(row: ResearchTeamLearningLoopDigestRow) -> tuple[str, str, str, str]:
    return (row.team_key, row.specialty_key, row.public_learning_label, row.learning_key)


def _require_unique_learning_keys(
    rows: tuple[ResearchTeamLearningLoopDigestRow, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.learning_key in seen:
            raise ValueError("duplicate learning_key")
        seen.add(row.learning_key)


def _status_count(rows: tuple[ResearchTeamLearningLoopDigestRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.team_status == status)


def _learning_key(item: ResearchTeamLearningLoopDigestInput) -> str:
    return _public_digest(
        item.team_key,
        item.specialty_key,
        item.learning_label,
        item.observed_at.isoformat(),
        _decimal_string(item.postmortem_count),
        _decimal_string(item.calibration_drift_count),
        _decimal_string(item.information_gap_count),
        _decimal_string(item.closed_information_gap_count),
        _decimal_string(item.calibration_error_delta),
        _decimal_string(item.confidence_score),
        item.lesson_summary,
        item.trace_marker,
    )


def _public_digest(*parts: str) -> str:
    joined = "\x1f".join(parts)
    return "sha256:" + sha256(joined.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str:
        _require_safe_payload_string(value)
        return value
    if type(value) is bool:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    raise TypeError("payload contains unsupported value")


def _require_payload_dataclass(value: object) -> None:
    if type(value) not in (
        ResearchTeamLearningLoopDigestReasonCodeCount,
        ResearchTeamLearningLoopDigestReport,
        ResearchTeamLearningLoopDigestRow,
    ):
        raise ValueError("payload contains unsupported dataclass")
    if hasattr(value, "paper_only"):
        _require_hard_flags("payload", value)


def _require_safe_payload_string(value: str) -> None:
    if _contains_private_marker(value):
        raise ValueError("payload string has unsafe public surface")


def _contains_private_marker(value: str) -> bool:
    lower = value.lower()
    if LINK_PATTERN.search(value) or EMAIL_PATTERN.search(value) or HEX_ID_PATTERN.search(value):
        return True
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", lower)
        for marker in PRIVATE_MARKERS
    )


def _reason_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("unknown reason_code") from exc


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise TypeError("count value must be exactly int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize(Decimal(value))


def _decimal_string(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must be finite") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _require_delta_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    _require_safe_payload_string(value)
    return value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    prefix = "sha256:"
    if not value.startswith(prefix) or len(value) != len(prefix) + 64:
        raise ValueError(f"{field_name} must be a public digest")
    suffix = value[len(prefix) :]
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be a public digest")


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_note(field_name: str, value: object, *, allow_empty: bool) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be nonempty")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} must keep {flag_name}=True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise TypeError(f"{label} must be exactly {type_.__name__}")
