"""Pure report-only policy for team research memory compaction plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


TEAM_RESEARCH_MEMORY_COMPACTION_POLICY_CONFIG_VERSION = (
    "team-research-memory-compaction-policy-v1"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
ROW_SORT_STATUSES = ("block", "watch", "pass")
PLAN_ACTIONS = (
    "prepare_upstream_compaction_digest",
    "hold_for_manual_review",
    "suppress_compaction_digest",
)
ROW_REASON_CODES = (
    "domain_summary_count_pass",
    "domain_summary_count_watch",
    "domain_summary_count_block",
    "evidence_quality_pass",
    "evidence_quality_watch",
    "evidence_quality_block",
    "prediction_bias_low",
    "prediction_bias_watch",
    "prediction_bias_block",
    "postmortem_complete",
    "postmortem_review_needed",
    "postmortem_incomplete",
    "memory_compaction_prepared",
    "memory_compaction_review_required",
    "memory_compaction_blocked",
)
REPORT_REASON_CODES = (
    "no_summaries_supplied",
    "upstream_compaction_plans_prepared",
    "manual_compaction_reviews_required",
    "compaction_plans_suppressed",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANTUM = Decimal("0.000001")
BPS_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
ZERO_BPS = Decimal("0.000000")
ZERO_COUNT = Decimal("0")

UNSAFE_PUBLIC_TERMS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "market_question",
    "market question",
    "question:",
    "source_ref",
    "source ref",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "http://",
    "https://",
    "www.",
    "url",
    "dsn",
    "database_url",
    "connection_string",
    "postgres://",
    "postgrest",
    "supabase",
    "table",
    "token",
    "bearer ",
    "api_key",
    "secret",
    "password",
    "private_key",
    "service_role",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "exposure",
    "shares",
    "stake",
    "buy",
    "sell",
    "recommend",
    "recommendation",
    "raw候选",
    "市场id",
    "市场问题",
    "来源",
    "表名",
    "令牌",
    "钱包",
    "授权",
    "订单",
    "交易",
    "仓位",
    "买",
    "卖",
    "推荐",
)

__all__ = (
    "TEAM_RESEARCH_MEMORY_COMPACTION_POLICY_CONFIG_VERSION",
    "TeamResearchMemoryCompactionPolicyConfig",
    "TeamResearchMemoryCompactionCandidate",
    "TeamResearchMemoryCompactionPlanRow",
    "TeamResearchMemoryCompactionPolicyReport",
    "build_team_research_memory_compaction_policy",
    "team_research_memory_compaction_policy_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("TeamResearchMemoryCompaction"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class TeamResearchMemoryCompactionPolicyConfig(_FinalPublicDataclass):
    config_version: str = TEAM_RESEARCH_MEMORY_COMPACTION_POLICY_CONFIG_VERSION
    min_domain_summary_count: Decimal = Decimal("1")
    min_pass_evidence_quality: Decimal = Decimal("0.750000")
    min_watch_evidence_quality: Decimal = Decimal("0.500000")
    max_pass_prediction_bias_bps: Decimal = Decimal("300.000000")
    max_watch_prediction_bias_bps: Decimal = Decimal("600.000000")
    min_pass_postmortem_completeness: Decimal = Decimal("0.800000")
    min_watch_postmortem_completeness: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamResearchMemoryCompactionPolicyConfig, "config")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_domain_summary_count",
            _normalize_positive_count(
                "min_domain_summary_count",
                self.min_domain_summary_count,
            ),
        )
        for field_name in (
            "min_pass_evidence_quality",
            "min_watch_evidence_quality",
            "min_pass_postmortem_completeness",
            "min_watch_postmortem_completeness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_prediction_bias_bps",
            "max_watch_prediction_bias_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        if self.min_watch_evidence_quality > self.min_pass_evidence_quality:
            raise ValueError("min_watch_evidence_quality must not exceed pass threshold")
        if (
            self.min_watch_postmortem_completeness
            > self.min_pass_postmortem_completeness
        ):
            raise ValueError(
                "min_watch_postmortem_completeness must not exceed pass threshold",
            )
        if self.max_pass_prediction_bias_bps > self.max_watch_prediction_bias_bps:
            raise ValueError("max_pass_prediction_bias_bps must not exceed watch ceiling")
        _reject_unsafe_public_payload("team research memory compaction config", self)
        _require_hard_flags("TeamResearchMemoryCompactionPolicyConfig", self)


@dataclass(frozen=True)
class TeamResearchMemoryCompactionCandidate(_FinalPublicDataclass):
    summary_digest: str
    domain_label: str
    evidence_quality: Decimal
    prediction_bias_bps: Decimal
    postmortem_completeness: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamResearchMemoryCompactionCandidate, "candidate")
        _require_digest_string("summary_digest", self.summary_digest)
        _require_public_string("domain_label", self.domain_label)
        object.__setattr__(
            self,
            "evidence_quality",
            _normalize_score("evidence_quality", self.evidence_quality),
        )
        object.__setattr__(
            self,
            "prediction_bias_bps",
            _normalize_nonnegative_bps("prediction_bias_bps", self.prediction_bias_bps),
        )
        object.__setattr__(
            self,
            "postmortem_completeness",
            _normalize_score("postmortem_completeness", self.postmortem_completeness),
        )
        _reject_unsafe_public_payload("team research memory compaction candidate", self)
        _require_hard_flags("TeamResearchMemoryCompactionCandidate", self)


@dataclass(frozen=True)
class TeamResearchMemoryCompactionPlanRow(_FinalPublicDataclass):
    domain_digest: str
    compaction_digest: str
    public_status: str
    plan_action: str
    upstream_prepare: bool
    summary_count: Decimal
    average_evidence_quality: Decimal
    average_prediction_bias_bps: Decimal
    max_prediction_bias_bps: Decimal
    average_postmortem_completeness: Decimal
    minimum_evidence_quality: Decimal
    minimum_postmortem_completeness: Decimal
    compaction_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamResearchMemoryCompactionPlanRow, "row")
        _require_digest_string("domain_digest", self.domain_digest)
        _require_digest_string("compaction_digest", self.compaction_digest)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        _require_member("plan_action", self.plan_action, PLAN_ACTIONS)
        if type(self.upstream_prepare) is not bool:
            raise ValueError("upstream_prepare must be a bool")
        object.__setattr__(
            self,
            "summary_count",
            _normalize_nonnegative_count("summary_count", self.summary_count),
        )
        for field_name in (
            "average_evidence_quality",
            "average_postmortem_completeness",
            "minimum_evidence_quality",
            "minimum_postmortem_completeness",
            "compaction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_prediction_bias_bps", "max_prediction_bias_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("team research memory compaction row", self)
        _require_hard_flags("TeamResearchMemoryCompactionPlanRow", self)
        _validate_plan_row(self)


@dataclass(frozen=True)
class TeamResearchMemoryCompactionPolicyReport(_FinalPublicDataclass):
    config_version: str
    report_status: str
    input_summary_count: Decimal
    domain_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    upstream_prepare_count: Decimal
    review_count: Decimal
    suppress_count: Decimal
    average_compaction_score: Decimal
    rows: tuple[TeamResearchMemoryCompactionPlanRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamResearchMemoryCompactionPolicyReport, "report")
        _require_public_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, PUBLIC_STATUSES)
        for field_name in (
            "input_summary_count",
            "domain_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "upstream_prepare_count",
            "review_count",
            "suppress_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_compaction_score",
            _normalize_score("average_compaction_score", self.average_compaction_score),
        )
        object.__setattr__(self, "rows", _normalize_plan_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("team research memory compaction report", self)
        _require_hard_flags("TeamResearchMemoryCompactionPolicyReport", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_team_research_memory_compaction_policy(
    candidates: list[TeamResearchMemoryCompactionCandidate]
    | tuple[TeamResearchMemoryCompactionCandidate, ...],
    *,
    config: TeamResearchMemoryCompactionPolicyConfig | None = None,
) -> TeamResearchMemoryCompactionPolicyReport:
    cfg = config or TeamResearchMemoryCompactionPolicyConfig()
    if type(cfg) is not TeamResearchMemoryCompactionPolicyConfig:
        raise ValueError("config must be a TeamResearchMemoryCompactionPolicyConfig")
    _require_hard_flags("TeamResearchMemoryCompactionPolicyConfig", cfg)
    source_rows = _normalize_input_candidates(candidates)
    grouped_rows = _group_candidates_by_domain(source_rows)
    report_rows = tuple(
        sorted(
            (
                _plan_row_for_domain(domain_digest, rows, config=cfg)
                for domain_digest, rows in grouped_rows
            ),
            key=_row_sort_key,
        ),
    )
    pass_count = _status_count(report_rows, "pass")
    watch_count = _status_count(report_rows, "watch")
    block_count = _status_count(report_rows, "block")

    return TeamResearchMemoryCompactionPolicyReport(
        config_version=cfg.config_version,
        report_status=_report_status(report_rows),
        input_summary_count=_count(len(source_rows)),
        domain_count=_count(len(report_rows)),
        row_count=_count(len(report_rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        upstream_prepare_count=_action_count(
            report_rows,
            "prepare_upstream_compaction_digest",
        ),
        review_count=_action_count(report_rows, "hold_for_manual_review"),
        suppress_count=_action_count(report_rows, "suppress_compaction_digest"),
        average_compaction_score=_average_score(
            tuple(row.compaction_score for row in report_rows),
        ),
        rows=report_rows,
        reason_codes=_report_reason_codes(report_rows, len(source_rows)),
    )


def team_research_memory_compaction_policy_payload(
    report: TeamResearchMemoryCompactionPolicyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamResearchMemoryCompactionPolicyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("team research memory compaction report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("team research memory compaction payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamResearchMemoryCompactionPolicyReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("team research memory compaction payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _group_candidates_by_domain(
    candidates: tuple[TeamResearchMemoryCompactionCandidate, ...],
) -> tuple[tuple[str, tuple[TeamResearchMemoryCompactionCandidate, ...]], ...]:
    grouped: dict[str, list[TeamResearchMemoryCompactionCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(_domain_digest(candidate.domain_label), []).append(candidate)
    return tuple(
        (domain_digest, tuple(sorted(rows, key=lambda row: row.summary_digest)))
        for domain_digest, rows in sorted(grouped.items())
    )


def _plan_row_for_domain(
    domain_digest: str,
    candidates: tuple[TeamResearchMemoryCompactionCandidate, ...],
    *,
    config: TeamResearchMemoryCompactionPolicyConfig,
) -> TeamResearchMemoryCompactionPlanRow:
    summary_count = _count(len(candidates))
    average_evidence_quality = _average_score(
        tuple(row.evidence_quality for row in candidates),
    )
    average_prediction_bias_bps = _average_bps(
        tuple(row.prediction_bias_bps for row in candidates),
    )
    max_prediction_bias_bps = max(
        (row.prediction_bias_bps for row in candidates),
        default=ZERO_BPS,
    ).quantize(BPS_QUANTUM)
    average_postmortem_completeness = _average_score(
        tuple(row.postmortem_completeness for row in candidates),
    )
    minimum_evidence_quality = min(
        (row.evidence_quality for row in candidates),
        default=ZERO_SCORE,
    )
    minimum_postmortem_completeness = min(
        (row.postmortem_completeness for row in candidates),
        default=ZERO_SCORE,
    )
    compaction_score = _compaction_score(
        average_evidence_quality=average_evidence_quality,
        average_prediction_bias_bps=average_prediction_bias_bps,
        average_postmortem_completeness=average_postmortem_completeness,
        config=config,
    )
    public_status = _public_status(
        summary_count=summary_count,
        average_evidence_quality=average_evidence_quality,
        minimum_evidence_quality=minimum_evidence_quality,
        max_prediction_bias_bps=max_prediction_bias_bps,
        average_postmortem_completeness=average_postmortem_completeness,
        minimum_postmortem_completeness=minimum_postmortem_completeness,
        config=config,
    )
    return TeamResearchMemoryCompactionPlanRow(
        domain_digest=domain_digest,
        compaction_digest=_compaction_digest(
            domain_digest=domain_digest,
            candidates=candidates,
            summary_count=summary_count,
            average_evidence_quality=average_evidence_quality,
            average_prediction_bias_bps=average_prediction_bias_bps,
            max_prediction_bias_bps=max_prediction_bias_bps,
            average_postmortem_completeness=average_postmortem_completeness,
            minimum_evidence_quality=minimum_evidence_quality,
            minimum_postmortem_completeness=minimum_postmortem_completeness,
            compaction_score=compaction_score,
        ),
        public_status=public_status,
        plan_action=_plan_action(public_status),
        upstream_prepare=public_status == "pass",
        summary_count=summary_count,
        average_evidence_quality=average_evidence_quality,
        average_prediction_bias_bps=average_prediction_bias_bps,
        max_prediction_bias_bps=max_prediction_bias_bps,
        average_postmortem_completeness=average_postmortem_completeness,
        minimum_evidence_quality=minimum_evidence_quality,
        minimum_postmortem_completeness=minimum_postmortem_completeness,
        compaction_score=compaction_score,
        reason_codes=_row_reason_codes(
            summary_count=summary_count,
            average_evidence_quality=average_evidence_quality,
            minimum_evidence_quality=minimum_evidence_quality,
            max_prediction_bias_bps=max_prediction_bias_bps,
            average_postmortem_completeness=average_postmortem_completeness,
            minimum_postmortem_completeness=minimum_postmortem_completeness,
            public_status=public_status,
            config=config,
        ),
    )


def _public_status(
    *,
    summary_count: Decimal,
    average_evidence_quality: Decimal,
    minimum_evidence_quality: Decimal,
    max_prediction_bias_bps: Decimal,
    average_postmortem_completeness: Decimal,
    minimum_postmortem_completeness: Decimal,
    config: TeamResearchMemoryCompactionPolicyConfig,
) -> str:
    if summary_count < config.min_domain_summary_count:
        return "block"
    if minimum_evidence_quality < config.min_watch_evidence_quality:
        return "block"
    if average_evidence_quality < config.min_watch_evidence_quality:
        return "block"
    if max_prediction_bias_bps > config.max_watch_prediction_bias_bps:
        return "block"
    if minimum_postmortem_completeness < config.min_watch_postmortem_completeness:
        return "block"
    if average_postmortem_completeness < config.min_watch_postmortem_completeness:
        return "block"
    if minimum_evidence_quality < config.min_pass_evidence_quality:
        return "watch"
    if average_evidence_quality < config.min_pass_evidence_quality:
        return "watch"
    if max_prediction_bias_bps > config.max_pass_prediction_bias_bps:
        return "watch"
    if minimum_postmortem_completeness < config.min_pass_postmortem_completeness:
        return "watch"
    if average_postmortem_completeness < config.min_pass_postmortem_completeness:
        return "watch"
    return "pass"


def _plan_action(public_status: str) -> str:
    if public_status == "pass":
        return "prepare_upstream_compaction_digest"
    if public_status == "watch":
        return "hold_for_manual_review"
    return "suppress_compaction_digest"


def _compaction_score(
    *,
    average_evidence_quality: Decimal,
    average_prediction_bias_bps: Decimal,
    average_postmortem_completeness: Decimal,
    config: TeamResearchMemoryCompactionPolicyConfig,
) -> Decimal:
    bias_factor = _prediction_bias_quality_factor(average_prediction_bias_bps, config)
    with localcontext(DECIMAL_CONTEXT):
        score = (
            average_evidence_quality * Decimal("0.400000")
            + average_postmortem_completeness * Decimal("0.350000")
            + bias_factor * Decimal("0.250000")
        )
    return _clamped_score(score)


def _prediction_bias_quality_factor(
    prediction_bias_bps: Decimal,
    config: TeamResearchMemoryCompactionPolicyConfig,
) -> Decimal:
    if config.max_watch_prediction_bias_bps == ZERO_BPS:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_score(
            ONE_SCORE - (prediction_bias_bps / config.max_watch_prediction_bias_bps),
        )


def _row_reason_codes(
    *,
    summary_count: Decimal,
    average_evidence_quality: Decimal,
    minimum_evidence_quality: Decimal,
    max_prediction_bias_bps: Decimal,
    average_postmortem_completeness: Decimal,
    minimum_postmortem_completeness: Decimal,
    public_status: str,
    config: TeamResearchMemoryCompactionPolicyConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if summary_count >= config.min_domain_summary_count:
        codes.append("domain_summary_count_pass")
    elif summary_count > ZERO_COUNT:
        codes.append("domain_summary_count_watch")
    else:
        codes.append("domain_summary_count_block")

    if (
        minimum_evidence_quality >= config.min_pass_evidence_quality
        and average_evidence_quality >= config.min_pass_evidence_quality
    ):
        codes.append("evidence_quality_pass")
    elif (
        minimum_evidence_quality >= config.min_watch_evidence_quality
        and average_evidence_quality >= config.min_watch_evidence_quality
    ):
        codes.append("evidence_quality_watch")
    else:
        codes.append("evidence_quality_block")

    if max_prediction_bias_bps <= config.max_pass_prediction_bias_bps:
        codes.append("prediction_bias_low")
    elif max_prediction_bias_bps <= config.max_watch_prediction_bias_bps:
        codes.append("prediction_bias_watch")
    else:
        codes.append("prediction_bias_block")

    if (
        minimum_postmortem_completeness >= config.min_pass_postmortem_completeness
        and average_postmortem_completeness >= config.min_pass_postmortem_completeness
    ):
        codes.append("postmortem_complete")
    elif (
        minimum_postmortem_completeness >= config.min_watch_postmortem_completeness
        and average_postmortem_completeness >= config.min_watch_postmortem_completeness
    ):
        codes.append("postmortem_review_needed")
    else:
        codes.append("postmortem_incomplete")

    if public_status == "pass":
        codes.append("memory_compaction_prepared")
    elif public_status == "watch":
        codes.append("memory_compaction_review_required")
    else:
        codes.append("memory_compaction_blocked")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_status(rows: tuple[TeamResearchMemoryCompactionPlanRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamResearchMemoryCompactionPlanRow, ...],
    input_summary_count: int,
) -> tuple[str, ...]:
    if input_summary_count == 0:
        return ("no_summaries_supplied",)
    codes: list[str] = []
    if any(row.plan_action == "prepare_upstream_compaction_digest" for row in rows):
        codes.append("upstream_compaction_plans_prepared")
    if any(row.plan_action == "hold_for_manual_review" for row in rows):
        codes.append("manual_compaction_reviews_required")
    if any(row.plan_action == "suppress_compaction_digest" for row in rows):
        codes.append("compaction_plans_suppressed")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _validate_plan_row(row: TeamResearchMemoryCompactionPlanRow) -> None:
    if row.reason_codes == ():
        raise ValueError("reason_codes must not be empty")
    if row.plan_action != _plan_action(row.public_status):
        raise ValueError("plan_action must match public_status")
    if row.upstream_prepare != (row.public_status == "pass"):
        raise ValueError("upstream_prepare must match public_status")
    if row.max_prediction_bias_bps < row.average_prediction_bias_bps:
        raise ValueError("max_prediction_bias_bps must cover average")


def _validate_report(report: TeamResearchMemoryCompactionPolicyReport) -> None:
    if report.domain_count != report.row_count:
        raise ValueError("domain_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_summary_count != _count(
        sum(int(row.summary_count) for row in report.rows),
    ):
        raise ValueError("input_summary_count must match row summary counts")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
        "upstream_prepare_count": _action_count(
            report.rows,
            "prepare_upstream_compaction_digest",
        ),
        "review_count": _action_count(report.rows, "hold_for_manual_review"),
        "suppress_count": _action_count(report.rows, "suppress_compaction_digest"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_compaction_score != _average_score(
        tuple(row.compaction_score for row in report.rows),
    ):
        raise ValueError("average_compaction_score must match rows")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        int(report.input_summary_count),
    ):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")


def _normalize_input_candidates(
    value: object,
) -> tuple[TeamResearchMemoryCompactionCandidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    seen_digests: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not TeamResearchMemoryCompactionCandidate:
            raise ValueError(
                "candidates must contain TeamResearchMemoryCompactionCandidate values",
            )
        _require_hard_flags("TeamResearchMemoryCompactionCandidate", candidate)
        if candidate.summary_digest in seen_digests:
            raise ValueError("duplicate summary_digest values are not allowed")
        seen_digests.add(candidate.summary_digest)
    return candidates


def _normalize_plan_rows(
    value: object,
) -> tuple[TeamResearchMemoryCompactionPlanRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not TeamResearchMemoryCompactionPlanRow:
            raise ValueError(
                "rows must contain TeamResearchMemoryCompactionPlanRow values",
            )
        _require_hard_flags("TeamResearchMemoryCompactionPlanRow", row)
        if row.domain_digest in seen_digests:
            raise ValueError("duplicate domain_digest values are not allowed")
        seen_digests.add(row.domain_digest)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in ROW_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _row_sort_key(
    row: TeamResearchMemoryCompactionPlanRow,
) -> tuple[int, Decimal, str, str]:
    return (
        ROW_SORT_STATUSES.index(row.public_status),
        row.compaction_score,
        row.domain_digest,
        row.compaction_digest,
    )


def _status_count(
    rows: tuple[TeamResearchMemoryCompactionPlanRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.public_status == status))


def _action_count(
    rows: tuple[TeamResearchMemoryCompactionPlanRow, ...],
    action: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.plan_action == action))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_SCORE) / _count(len(values))).quantize(SCORE_QUANTUM)


def _average_bps(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_BPS
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_BPS) / _count(len(values))).quantize(BPS_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_nonnegative_bps(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(BPS_QUANTUM)
    if normalized < ZERO_BPS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamped_score(value: Decimal) -> Decimal:
    normalized = _require_decimal("score", value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        return ZERO_SCORE
    if normalized > ONE_SCORE:
        return ONE_SCORE
    return normalized


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path or label} has unsafe public key")
            if _has_unsafe_public_term(key):
                raise ValueError(f"{path or label} has unsafe public key")
            child_path = f"{path}.{key}" if path else key
            _reject_unsafe_public_payload(label, item, child_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} has non-finite Decimal")
        return
    if type(value) is bool or value is None:
        return
    raise ValueError(f"{path or label} has unsupported public value")


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _domain_digest(domain_label: str) -> str:
    _require_public_string("domain_label", domain_label)
    return sha256(
        f"team-research-memory-domain:{domain_label.lower()}".encode("utf-8"),
    ).hexdigest()


def _compaction_digest(
    *,
    domain_digest: str,
    candidates: tuple[TeamResearchMemoryCompactionCandidate, ...],
    summary_count: Decimal,
    average_evidence_quality: Decimal,
    average_prediction_bias_bps: Decimal,
    max_prediction_bias_bps: Decimal,
    average_postmortem_completeness: Decimal,
    minimum_evidence_quality: Decimal,
    minimum_postmortem_completeness: Decimal,
    compaction_score: Decimal,
) -> str:
    _require_digest_string("domain_digest", domain_digest)
    material = {
        "domain_digest": domain_digest,
        "summary_digests": tuple(row.summary_digest for row in candidates),
        "summary_count": summary_count,
        "average_evidence_quality": average_evidence_quality,
        "average_prediction_bias_bps": average_prediction_bias_bps,
        "max_prediction_bias_bps": max_prediction_bias_bps,
        "average_postmortem_completeness": average_postmortem_completeness,
        "minimum_evidence_quality": minimum_evidence_quality,
        "minimum_postmortem_completeness": minimum_postmortem_completeness,
        "compaction_score": compaction_score,
    }
    return _digest_for_json_payload(_json_ready(material))


def _report_digest(report: TeamResearchMemoryCompactionPolicyReport) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("digest payload", payload_without_digest)
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {_json_ready_key(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _json_ready_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("public payload keys must be strings")
    return value
