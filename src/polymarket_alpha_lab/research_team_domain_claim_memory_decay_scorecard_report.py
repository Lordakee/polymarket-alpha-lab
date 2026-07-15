"""Read-only claim memory decay scorecard for research team domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_MEMORY_DECAY_SCORECARD_CONFIG_VERSION = (
    "research-team-domain-claim-memory-decay-scorecard-report-v0"
)
CLAIM_MEMORY_DECAY_STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "claim_memory_current",
    "claim_memory_watch",
    "claim_memory_decayed",
    "claim_memory_contradiction_excess",
    "claim_memory_review_gap_watch",
    "claim_memory_review_gap_block",
)
REPORT_REASON_CODES = (
    "claim_memory_decay_scorecard_ready",
    "claim_memory_decay_block_present",
    "claim_memory_decay_watch_present",
    "claim_memory_decay_scorecard_empty",
)
DECIMAL_ZERO = Decimal("0")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SCORE_QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DIGEST_HEX_LENGTH = 64
CONTRADICTION_EXCESS_PENALTY = Decimal("0.100000")
REVIEW_GAP_BLOCK_PENALTY = Decimal("0.100000")
THREE = Decimal("3")
UNSAFE_PUBLIC_FRAGMENTS = (
    "acc" "ount",
    "access" "_key",
    "api" "_key",
    "au" "th",
    "bear" "er",
    "b" "uy",
    "buck" "et",
    "can" "didate",
    "can" "cel",
    "conn" "ection",
    "cook" "ie",
    "cre" "dential",
    "data" "base",
    "dot" "env",
    "d" "sn",
    "end" "point",
    "env" "iron",
    "fi" "le",
    "ht" "tp",
    "inv" "est",
    "li" "ve",
    "mar" "ket",
    "net" "work",
    "or" "der",
    "pass" "word",
    "post" "gres",
    "pri" "vate_key",
    "req" "uest",
    "reco" "mmendation",
    "sec" "ret",
    "se" "ll",
    "sess" "ion",
    "sizi" "ng",
    "soc" "ket",
    "sou" "rce",
    "sql" "ite",
    "s" "tore",
    "stor" "age",
    "sub" "mit",
    "supa" "base",
    "ta" "ble",
    "to" "ken",
    "tr" "ade",
    "url" "lib",
    "wa" "llet",
)
PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "assessed_claim_count",
        "average_claim_memory_decay_score",
        "block_count",
        "config_version",
        "contradiction_excess_count",
        "derived_validation_digest",
        "generated_at",
        "half_life_seconds",
        "lowest_claim_memory_decay_score",
        "max_contradiction_count",
        "min_confirmation_count",
        "min_pass_score",
        "min_watch_score",
        "paper_only",
        "pass_count",
        "readonly",
        "reason_codes",
        "report_only",
        "report_status",
        "review_gap_block_count",
        "review_gap_block_seconds",
        "review_gap_watch_count",
        "review_gap_watch_seconds",
        "rows",
        "watch_count",
    },
)
PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    {
        "claim_age_seconds",
        "claim_digest",
        "claim_memory_decay_score",
        "confirmation_component",
        "confirmation_count",
        "contradiction_count",
        "contradiction_excess_count",
        "domain_id",
        "freshness_component",
        "memory_strength",
        "paper_only",
        "readonly",
        "reason_codes",
        "report_only",
        "review_gap_block",
        "review_gap_seconds",
        "review_gap_watch",
        "row_status",
        "team_id",
    },
)


@dataclass(frozen=True)
class ResearchTeamDomainClaimMemoryDecayScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_MEMORY_DECAY_SCORECARD_CONFIG_VERSION
    )
    half_life_seconds: Decimal = Decimal("2592000")
    review_gap_watch_seconds: Decimal = Decimal("604800")
    review_gap_block_seconds: Decimal = Decimal("1209600")
    min_confirmation_count: Decimal = Decimal("2")
    max_contradiction_count: Decimal = Decimal("1")
    min_pass_score: Decimal = Decimal("0.700000")
    min_watch_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainClaimMemoryDecayScorecardConfig:
            raise TypeError(
                "ResearchTeamDomainClaimMemoryDecayScorecardConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainClaimMemoryDecayScorecardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchTeamDomainClaimMemoryDecayScorecardConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "half_life_seconds",
            "review_gap_watch_seconds",
            "review_gap_block_seconds",
            "min_confirmation_count",
            "max_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.half_life_seconds <= DECIMAL_ZERO:
            raise ValueError("half_life_seconds must be positive")
        if self.min_confirmation_count <= DECIMAL_ZERO:
            raise ValueError("min_confirmation_count must be positive")
        if self.review_gap_watch_seconds > self.review_gap_block_seconds:
            raise ValueError("review gap thresholds must be deterministic")
        for field_name in ("min_pass_score", "min_watch_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_watch_score > self.min_pass_score:
            raise ValueError("score thresholds must be deterministic")
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchTeamDomainClaimMemoryDecayScorecardClaim:
    domain_id: str
    team_id: str
    claim_id: str
    memory_strength: Decimal
    claim_age_seconds: Decimal
    confirmation_count: Decimal
    contradiction_count: Decimal
    review_gap_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainClaimMemoryDecayScorecardClaim:
            raise TypeError(
                "ResearchTeamDomainClaimMemoryDecayScorecardClaim "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainClaimMemoryDecayScorecardClaim:
            raise ValueError(
                "claim must be exactly "
                "ResearchTeamDomainClaimMemoryDecayScorecardClaim",
            )
        _require_public_string("domain_id", self.domain_id)
        _require_public_string("team_id", self.team_id)
        _require_canonical_string("claim_id", self.claim_id)
        object.__setattr__(
            self,
            "memory_strength",
            _normalize_ratio("memory_strength", self.memory_strength),
        )
        for field_name in (
            "claim_age_seconds",
            "confirmation_count",
            "contradiction_count",
            "review_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardClaim",
            self,
        )


@dataclass(frozen=True)
class ResearchTeamDomainClaimMemoryDecayScorecardRow:
    domain_id: str
    team_id: str
    claim_digest: str
    memory_strength: Decimal
    claim_age_seconds: Decimal
    freshness_component: Decimal
    confirmation_component: Decimal
    confirmation_count: Decimal
    contradiction_count: Decimal
    contradiction_excess_count: Decimal
    review_gap_seconds: Decimal
    review_gap_watch: bool
    review_gap_block: bool
    claim_memory_decay_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainClaimMemoryDecayScorecardRow:
            raise TypeError(
                "ResearchTeamDomainClaimMemoryDecayScorecardRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainClaimMemoryDecayScorecardRow:
            raise ValueError(
                "row must be exactly "
                "ResearchTeamDomainClaimMemoryDecayScorecardRow",
            )
        _require_public_string("domain_id", self.domain_id)
        _require_public_string("team_id", self.team_id)
        _require_sha256_digest("claim_digest", self.claim_digest)
        for field_name in (
            "memory_strength",
            "freshness_component",
            "confirmation_component",
            "claim_memory_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_age_seconds",
            "confirmation_count",
            "contradiction_count",
            "contradiction_excess_count",
            "review_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if type(self.review_gap_watch) is not bool:
            raise ValueError("review_gap_watch must be a bool")
        if type(self.review_gap_block) is not bool:
            raise ValueError("review_gap_block must be a bool")
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardRow",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchTeamDomainClaimMemoryDecayScorecardRow",
            self,
        )


@dataclass(frozen=True)
class ResearchTeamDomainClaimMemoryDecayScorecardReport:
    generated_at: datetime
    config_version: str
    half_life_seconds: Decimal
    review_gap_watch_seconds: Decimal
    review_gap_block_seconds: Decimal
    min_confirmation_count: Decimal
    max_contradiction_count: Decimal
    min_pass_score: Decimal
    min_watch_score: Decimal
    report_status: str
    assessed_claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    review_gap_watch_count: Decimal
    review_gap_block_count: Decimal
    contradiction_excess_count: Decimal
    average_claim_memory_decay_score: Decimal
    lowest_claim_memory_decay_score: Decimal
    rows: tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainClaimMemoryDecayScorecardReport:
            raise TypeError(
                "ResearchTeamDomainClaimMemoryDecayScorecardReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainClaimMemoryDecayScorecardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchTeamDomainClaimMemoryDecayScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        normalized_config = ResearchTeamDomainClaimMemoryDecayScorecardConfig(
            config_version=self.config_version,
            half_life_seconds=self.half_life_seconds,
            review_gap_watch_seconds=self.review_gap_watch_seconds,
            review_gap_block_seconds=self.review_gap_block_seconds,
            min_confirmation_count=self.min_confirmation_count,
            max_contradiction_count=self.max_contradiction_count,
            min_pass_score=self.min_pass_score,
            min_watch_score=self.min_watch_score,
            paper_only=self.paper_only,
            report_only=self.report_only,
            readonly=self.readonly,
        )
        for field_name in (
            "half_life_seconds",
            "review_gap_watch_seconds",
            "review_gap_block_seconds",
            "min_confirmation_count",
            "max_contradiction_count",
            "min_pass_score",
            "min_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                getattr(normalized_config, field_name),
            )
        _require_status("report_status", self.report_status)
        for field_name in (
            "assessed_claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "review_gap_watch_count",
            "review_gap_block_count",
            "contradiction_excess_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_claim_memory_decay_score",
            "lowest_claim_memory_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardReport",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchTeamDomainClaimMemoryDecayScorecardReport",
            self,
        )
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardReport",
            self,
        )
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(
            _report_values_without_digest(self),
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload(
            "ResearchTeamDomainClaimMemoryDecayScorecardReport.payload",
            payload,
        )
        _validate_public_payload_schema(payload)
        _validate_payload_digest(payload)
        _report_from_public_payload(payload)
        return payload


def build_research_team_domain_claim_memory_decay_scorecard_report(
    claims: tuple[ResearchTeamDomainClaimMemoryDecayScorecardClaim, ...]
    | list[ResearchTeamDomainClaimMemoryDecayScorecardClaim],
    *,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
    generated_at: datetime,
) -> ResearchTeamDomainClaimMemoryDecayScorecardReport:
    if type(config) is not ResearchTeamDomainClaimMemoryDecayScorecardConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainClaimMemoryDecayScorecardConfig",
        )
    require_paper_only_flags(
        "ResearchTeamDomainClaimMemoryDecayScorecardConfig",
        config,
    )
    rows = _scorecard_rows(_normalize_claims(claims), config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "half_life_seconds": config.half_life_seconds,
        "review_gap_watch_seconds": config.review_gap_watch_seconds,
        "review_gap_block_seconds": config.review_gap_block_seconds,
        "min_confirmation_count": config.min_confirmation_count,
        "max_contradiction_count": config.max_contradiction_count,
        "min_pass_score": config.min_pass_score,
        "min_watch_score": config.min_watch_score,
        "report_status": _report_status(reason_codes),
        "assessed_claim_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(sum(1 for row in rows if row.row_status == "pass")),
        "watch_count": _decimal_count(sum(1 for row in rows if row.row_status == "watch")),
        "block_count": _decimal_count(sum(1 for row in rows if row.row_status == "block")),
        "review_gap_watch_count": _decimal_count(
            sum(1 for row in rows if row.review_gap_watch),
        ),
        "review_gap_block_count": _decimal_count(
            sum(1 for row in rows if row.review_gap_block),
        ),
        "contradiction_excess_count": _total_contradiction_excess_count(rows),
        "average_claim_memory_decay_score": _average_score(rows),
        "lowest_claim_memory_decay_score": _lowest_score(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainClaimMemoryDecayScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_claim_memory_decay_scorecard_payload(
    report: ResearchTeamDomainClaimMemoryDecayScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainClaimMemoryDecayScorecardReport:
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardReport",
            report,
        )
        payload = report.payload
    elif type(report) is dict:
        payload = dict(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainClaimMemoryDecayScorecardReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_schema(payload)
    _validate_payload_digest(payload)
    _report_from_public_payload(payload)
    return payload


def _scorecard_rows(
    claims: tuple[ResearchTeamDomainClaimMemoryDecayScorecardClaim, ...],
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...]:
    return tuple(
        sorted(
            (_scorecard_row(claim=claim, config=config) for claim in claims),
            key=lambda row: (
                row.row_status != "block",
                row.row_status != "watch",
                row.claim_memory_decay_score,
                row.domain_id,
                row.team_id,
                row.claim_digest,
            ),
        ),
    )


def _scorecard_row(
    *,
    claim: ResearchTeamDomainClaimMemoryDecayScorecardClaim,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> ResearchTeamDomainClaimMemoryDecayScorecardRow:
    freshness_component = _freshness_component(claim, config)
    confirmation_component = _confirmation_component(claim, config)
    contradiction_excess_count = _contradiction_excess_count(
        claim.contradiction_count,
        config.max_contradiction_count,
    )
    review_gap_watch = claim.review_gap_seconds >= config.review_gap_watch_seconds
    review_gap_block = claim.review_gap_seconds >= config.review_gap_block_seconds
    score = _claim_memory_decay_score(
        memory_strength=claim.memory_strength,
        freshness_component=freshness_component,
        confirmation_component=confirmation_component,
        contradiction_excess_count=contradiction_excess_count,
        review_gap_block=review_gap_block,
    )
    status = _score_status(score, config)
    return ResearchTeamDomainClaimMemoryDecayScorecardRow(
        domain_id=claim.domain_id,
        team_id=claim.team_id,
        claim_digest=_claim_digest(claim.claim_id),
        memory_strength=claim.memory_strength,
        claim_age_seconds=claim.claim_age_seconds,
        freshness_component=freshness_component,
        confirmation_component=confirmation_component,
        confirmation_count=claim.confirmation_count,
        contradiction_count=claim.contradiction_count,
        contradiction_excess_count=contradiction_excess_count,
        review_gap_seconds=claim.review_gap_seconds,
        review_gap_watch=review_gap_watch,
        review_gap_block=review_gap_block,
        claim_memory_decay_score=score,
        row_status=status,
        reason_codes=_row_reason_codes(
            status=status,
            contradiction_excess_count=contradiction_excess_count,
            review_gap_watch=review_gap_watch,
            review_gap_block=review_gap_block,
        ),
    )


def _freshness_component(
    claim: ResearchTeamDomainClaimMemoryDecayScorecardClaim,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> Decimal:
    return _freshness_component_from_age(claim.claim_age_seconds, config)


def _freshness_component_from_age(
    claim_age_seconds: Decimal,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> Decimal:
    if claim_age_seconds >= config.half_life_seconds:
        return Decimal("0.000000")
    with localcontext(DECIMAL_CONTEXT):
        value = (
            config.half_life_seconds - claim_age_seconds
        ) / config.half_life_seconds
    return _quantize_decimal("freshness_component", value, RATIO_QUANT)


def _confirmation_component(
    claim: ResearchTeamDomainClaimMemoryDecayScorecardClaim,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> Decimal:
    return _confirmation_component_from_count(claim.confirmation_count, config)


def _confirmation_component_from_count(
    confirmation_count: Decimal,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = confirmation_count / config.min_confirmation_count
    return min(
        Decimal("1.000000"),
        _quantize_decimal("confirmation_component", value, RATIO_QUANT),
    )


def _contradiction_excess_count(
    contradiction_count: Decimal,
    max_contradiction_count: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = max(
            DECIMAL_ZERO,
            contradiction_count - max_contradiction_count,
        )
    return _quantize_decimal("contradiction_excess_count", value, COUNT_QUANT)


def _score_status(
    score: Decimal,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> str:
    if score >= config.min_pass_score:
        return "pass"
    if score >= config.min_watch_score:
        return "watch"
    return "block"


def _claim_memory_decay_score(
    *,
    memory_strength: Decimal,
    freshness_component: Decimal,
    confirmation_component: Decimal,
    contradiction_excess_count: Decimal,
    review_gap_block: bool,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        penalty = contradiction_excess_count * CONTRADICTION_EXCESS_PENALTY
        if review_gap_block:
            penalty += REVIEW_GAP_BLOCK_PENALTY
        value = max(
            DECIMAL_ZERO,
            (
                memory_strength
                + freshness_component
                + confirmation_component
            )
            / THREE
            - penalty,
        )
    return _quantize_decimal("claim_memory_decay_score", value, SCORE_QUANT)


def _row_reason_codes(
    *,
    status: str,
    contradiction_excess_count: Decimal,
    review_gap_watch: bool,
    review_gap_block: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "block":
        reason_codes.append("claim_memory_decayed")
    elif status == "watch":
        reason_codes.append("claim_memory_watch")
    else:
        reason_codes.append("claim_memory_current")
    if contradiction_excess_count > DECIMAL_ZERO:
        reason_codes.append("claim_memory_contradiction_excess")
    if review_gap_block:
        reason_codes.append("claim_memory_review_gap_block")
    elif review_gap_watch:
        reason_codes.append("claim_memory_review_gap_watch")
    return tuple(
        code for code in ROW_REASON_CODES if code in reason_codes
    )


def _validate_row_consistency(
    row: ResearchTeamDomainClaimMemoryDecayScorecardRow,
) -> None:
    if row.contradiction_excess_count > row.contradiction_count:
        raise ValueError(
            "contradiction_excess_count must not exceed contradiction_count",
        )
    if row.review_gap_block and not row.review_gap_watch:
        raise ValueError("review_gap_block requires review_gap_watch")
    expected_score = _claim_memory_decay_score(
        memory_strength=row.memory_strength,
        freshness_component=row.freshness_component,
        confirmation_component=row.confirmation_component,
        contradiction_excess_count=row.contradiction_excess_count,
        review_gap_block=row.review_gap_block,
    )
    if row.claim_memory_decay_score != expected_score:
        raise ValueError("claim_memory_decay_score must match row components")
    expected_reason_codes = _row_reason_codes(
        status=row.row_status,
        contradiction_excess_count=row.contradiction_excess_count,
        review_gap_watch=row.review_gap_watch,
        review_gap_block=row.review_gap_block,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row status and diagnostics")


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("claim_memory_decay_scorecard_empty",)
    reason_codes: list[str] = []
    if any(row.row_status == "block" for row in rows):
        reason_codes.append("claim_memory_decay_block_present")
    if any(row.row_status == "watch" for row in rows):
        reason_codes.append("claim_memory_decay_watch_present")
    if not reason_codes:
        reason_codes.append("claim_memory_decay_scorecard_ready")
    return tuple(reason_codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "claim_memory_decay_block_present" in reason_codes
        or "claim_memory_decay_scorecard_empty" in reason_codes
    ):
        return "block"
    if "claim_memory_decay_watch_present" in reason_codes:
        return "watch"
    return "pass"


def _average_score(
    rows: tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...],
) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    with localcontext(DECIMAL_CONTEXT):
        value = (
            sum((row.claim_memory_decay_score for row in rows), DECIMAL_ZERO)
            / Decimal(len(rows))
        )
    return _quantize_decimal(
        "average_claim_memory_decay_score",
        value,
        SCORE_QUANT,
    )


def _lowest_score(
    rows: tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...],
) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    return _quantize_decimal(
        "lowest_claim_memory_decay_score",
        min(row.claim_memory_decay_score for row in rows),
        SCORE_QUANT,
    )


def _total_contradiction_excess_count(
    rows: tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...],
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = sum(
            (row.contradiction_excess_count for row in rows),
            DECIMAL_ZERO,
        )
    return _quantize_decimal("contradiction_excess_count", value, COUNT_QUANT)


def _validate_report_consistency(
    report: ResearchTeamDomainClaimMemoryDecayScorecardReport,
) -> None:
    normalized_generated_at = _as_utc("generated_at", report.generated_at)
    if (
        report.generated_at != normalized_generated_at
        or report.generated_at.tzinfo is not UTC
    ):
        raise ValueError("generated_at must use canonical UTC")
    config = _config_from_report(report)
    for row in report.rows:
        _validate_row_against_config(row, config)
    if report.assessed_claim_count != _decimal_count(len(report.rows)):
        raise ValueError("assessed_claim_count must match rows")
    if report.pass_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    with localcontext(DECIMAL_CONTEXT):
        status_count = report.pass_count + report.watch_count + report.block_count
    if status_count != report.assessed_claim_count:
        raise ValueError("status counts must match assessed_claim_count")
    if report.review_gap_watch_count != _decimal_count(
        sum(1 for row in report.rows if row.review_gap_watch),
    ):
        raise ValueError("review_gap_watch_count must match rows")
    if report.review_gap_block_count != _decimal_count(
        sum(1 for row in report.rows if row.review_gap_block),
    ):
        raise ValueError("review_gap_block_count must match rows")
    if report.contradiction_excess_count != _total_contradiction_excess_count(
        report.rows,
    ):
        raise ValueError("contradiction_excess_count must match rows")
    if report.average_claim_memory_decay_score != _average_score(report.rows):
        raise ValueError("average_claim_memory_decay_score must match rows")
    if report.lowest_claim_memory_decay_score != _lowest_score(report.rows):
        raise ValueError("lowest_claim_memory_decay_score must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(expected_reason_codes):
        raise ValueError("report_status must match rows")
    if report.rows != tuple(
        sorted(
            report.rows,
            key=lambda row: (
                row.row_status != "block",
                row.row_status != "watch",
                row.claim_memory_decay_score,
                row.domain_id,
                row.team_id,
                row.claim_digest,
            ),
        ),
    ):
        raise ValueError("rows must be deterministically sorted")


def _config_from_report(
    report: ResearchTeamDomainClaimMemoryDecayScorecardReport,
) -> ResearchTeamDomainClaimMemoryDecayScorecardConfig:
    return ResearchTeamDomainClaimMemoryDecayScorecardConfig(
        config_version=report.config_version,
        half_life_seconds=report.half_life_seconds,
        review_gap_watch_seconds=report.review_gap_watch_seconds,
        review_gap_block_seconds=report.review_gap_block_seconds,
        min_confirmation_count=report.min_confirmation_count,
        max_contradiction_count=report.max_contradiction_count,
        min_pass_score=report.min_pass_score,
        min_watch_score=report.min_watch_score,
    )


def _validate_row_against_config(
    row: ResearchTeamDomainClaimMemoryDecayScorecardRow,
    config: ResearchTeamDomainClaimMemoryDecayScorecardConfig,
) -> None:
    expected_freshness_component = _freshness_component_from_age(
        row.claim_age_seconds,
        config,
    )
    if row.freshness_component != expected_freshness_component:
        raise ValueError("freshness_component must match claim_age_seconds")
    expected_confirmation_component = _confirmation_component_from_count(
        row.confirmation_count,
        config,
    )
    if row.confirmation_component != expected_confirmation_component:
        raise ValueError(
            "confirmation_component must match confirmation_count",
        )
    expected_contradiction_excess_count = _contradiction_excess_count(
        row.contradiction_count,
        config.max_contradiction_count,
    )
    if row.contradiction_excess_count != expected_contradiction_excess_count:
        raise ValueError(
            "contradiction_excess_count must match contradiction_count",
        )
    expected_review_gap_watch = (
        row.review_gap_seconds >= config.review_gap_watch_seconds
    )
    if row.review_gap_watch != expected_review_gap_watch:
        raise ValueError("review_gap_watch must match review_gap_seconds")
    expected_review_gap_block = (
        row.review_gap_seconds >= config.review_gap_block_seconds
    )
    if row.review_gap_block != expected_review_gap_block:
        raise ValueError("review_gap_block must match review_gap_seconds")
    expected_score = _claim_memory_decay_score(
        memory_strength=row.memory_strength,
        freshness_component=expected_freshness_component,
        confirmation_component=expected_confirmation_component,
        contradiction_excess_count=expected_contradiction_excess_count,
        review_gap_block=expected_review_gap_block,
    )
    if row.claim_memory_decay_score != expected_score:
        raise ValueError(
            "claim_memory_decay_score must match claim diagnostics",
        )
    expected_status = _score_status(expected_score, config)
    if row.row_status != expected_status:
        raise ValueError("row_status must match claim_memory_decay_score")
    expected_reason_codes = _row_reason_codes(
        status=expected_status,
        contradiction_excess_count=expected_contradiction_excess_count,
        review_gap_watch=expected_review_gap_watch,
        review_gap_block=expected_review_gap_block,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match claim diagnostics")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(values):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    if any(type(key) is not str for key in payload):
        raise ValueError("payload keys must be strings")
    if set(payload) != PUBLIC_PAYLOAD_KEYS:
        raise ValueError("payload keys must match the public report schema")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        if any(type(key) is not str for key in row):
            raise ValueError("payload row keys must be strings")
        if set(row) != PUBLIC_ROW_PAYLOAD_KEYS:
            raise ValueError("payload row keys must match the public row schema")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamDomainClaimMemoryDecayScorecardReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a public list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    return ResearchTeamDomainClaimMemoryDecayScorecardReport(
        generated_at=_require_public_datetime(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_require_public_string_value(
            "config_version",
            payload["config_version"],
        ),
        half_life_seconds=_require_public_count(
            "half_life_seconds",
            payload["half_life_seconds"],
        ),
        review_gap_watch_seconds=_require_public_count(
            "review_gap_watch_seconds",
            payload["review_gap_watch_seconds"],
        ),
        review_gap_block_seconds=_require_public_count(
            "review_gap_block_seconds",
            payload["review_gap_block_seconds"],
        ),
        min_confirmation_count=_require_public_count(
            "min_confirmation_count",
            payload["min_confirmation_count"],
        ),
        max_contradiction_count=_require_public_count(
            "max_contradiction_count",
            payload["max_contradiction_count"],
        ),
        min_pass_score=_require_public_ratio(
            "min_pass_score",
            payload["min_pass_score"],
        ),
        min_watch_score=_require_public_ratio(
            "min_watch_score",
            payload["min_watch_score"],
        ),
        report_status=_require_public_status(
            "report_status",
            payload["report_status"],
        ),
        assessed_claim_count=_require_public_count(
            "assessed_claim_count",
            payload["assessed_claim_count"],
        ),
        pass_count=_require_public_count("pass_count", payload["pass_count"]),
        watch_count=_require_public_count("watch_count", payload["watch_count"]),
        block_count=_require_public_count("block_count", payload["block_count"]),
        review_gap_watch_count=_require_public_count(
            "review_gap_watch_count",
            payload["review_gap_watch_count"],
        ),
        review_gap_block_count=_require_public_count(
            "review_gap_block_count",
            payload["review_gap_block_count"],
        ),
        contradiction_excess_count=_require_public_count(
            "contradiction_excess_count",
            payload["contradiction_excess_count"],
        ),
        average_claim_memory_decay_score=_require_public_ratio(
            "average_claim_memory_decay_score",
            payload["average_claim_memory_decay_score"],
        ),
        lowest_claim_memory_decay_score=_require_public_ratio(
            "lowest_claim_memory_decay_score",
            payload["lowest_claim_memory_decay_score"],
        ),
        rows=rows,
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        derived_validation_digest=_require_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_true_flag("paper_only", payload["paper_only"]),
        report_only=_require_true_flag("report_only", payload["report_only"]),
        readonly=_require_true_flag("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchTeamDomainClaimMemoryDecayScorecardRow:
    if type(value) is not dict:
        raise ValueError("rows must contain public JSON objects")
    if set(value) != PUBLIC_ROW_PAYLOAD_KEYS:
        raise ValueError("payload row keys must match the public row schema")
    return ResearchTeamDomainClaimMemoryDecayScorecardRow(
        domain_id=_require_public_string_value("domain_id", value["domain_id"]),
        team_id=_require_public_string_value("team_id", value["team_id"]),
        claim_digest=_require_public_digest(
            "claim_digest",
            value["claim_digest"],
        ),
        memory_strength=_require_public_ratio(
            "memory_strength",
            value["memory_strength"],
        ),
        claim_age_seconds=_require_public_count(
            "claim_age_seconds",
            value["claim_age_seconds"],
        ),
        freshness_component=_require_public_ratio(
            "freshness_component",
            value["freshness_component"],
        ),
        confirmation_component=_require_public_ratio(
            "confirmation_component",
            value["confirmation_component"],
        ),
        confirmation_count=_require_public_count(
            "confirmation_count",
            value["confirmation_count"],
        ),
        contradiction_count=_require_public_count(
            "contradiction_count",
            value["contradiction_count"],
        ),
        contradiction_excess_count=_require_public_count(
            "contradiction_excess_count",
            value["contradiction_excess_count"],
        ),
        review_gap_seconds=_require_public_count(
            "review_gap_seconds",
            value["review_gap_seconds"],
        ),
        review_gap_watch=_require_public_bool(
            "review_gap_watch",
            value["review_gap_watch"],
        ),
        review_gap_block=_require_public_bool(
            "review_gap_block",
            value["review_gap_block"],
        ),
        claim_memory_decay_score=_require_public_ratio(
            "claim_memory_decay_score",
            value["claim_memory_decay_score"],
        ),
        row_status=_require_public_status("row_status", value["row_status"]),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_require_true_flag("paper_only", value["paper_only"]),
        report_only=_require_true_flag("report_only", value["report_only"]),
        readonly=_require_true_flag("readonly", value["readonly"]),
    )


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not _DictFlags:
            raise TypeError("_DictFlags does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not _DictFlags or type(self.value) is not dict:
            raise ValueError("payload flags must wrap exactly dict")

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_claims(
    value: object,
) -> tuple[ResearchTeamDomainClaimMemoryDecayScorecardClaim, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("claims must be a list or tuple")
    claims = tuple(value)
    digests: set[str] = set()
    for claim in claims:
        if type(claim) is not ResearchTeamDomainClaimMemoryDecayScorecardClaim:
            raise ValueError(
                "claims must contain ResearchTeamDomainClaimMemoryDecayScorecardClaim values",
            )
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardClaim",
            claim,
        )
        digest = _claim_digest(claim.claim_id)
        if digest in digests:
            raise ValueError("claims must be unique")
        digests.add(digest)
    return claims


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamDomainClaimMemoryDecayScorecardRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainClaimMemoryDecayScorecardRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainClaimMemoryDecayScorecardRow values",
            )
        require_paper_only_flags(
            "ResearchTeamDomainClaimMemoryDecayScorecardRow",
            row,
        )
        if row.claim_digest in digests:
            raise ValueError("rows must be unique")
        digests.add(row.claim_digest)
    return rows


def _normalize_reason_codes(
    value: object,
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in known_reason_codes:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in known_reason_codes if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CLAIM_MEMORY_DECAY_STATUSES:
        raise ValueError(f"{field_name} status must be pass, watch, or block")


def _require_public_status(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_public_digest(field_name: str, value: object) -> str:
    _require_sha256_digest(field_name, value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_string(field_name, value)


def _require_public_string_value(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    if value < DECIMAL_ZERO or value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    quantized = _quantize_decimal(field_name, value, RATIO_QUANT)
    if quantized < DECIMAL_ZERO or quantized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    quantized = _quantize_decimal(field_name, value, COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _quantize_decimal(
    field_name: str,
    value: Decimal,
    quant: Decimal,
) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = value.quantize(quant)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} cannot be represented canonically") from exc
    if quantized.is_zero() and quantized.is_signed():
        return quantized.copy_abs()
    return quantized


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is Decimal and value.is_finite() and value < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = _normalize_integral_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_public_decimal(
    field_name: str,
    value: object,
    *,
    quant: Decimal,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(
            f"{field_name} must be a canonical Decimal-derived string",
        )
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal-derived string",
        ) from exc
    normalized = (
        _normalize_integral_decimal(field_name, parsed)
        if quant == COUNT_QUANT
        else _normalize_ratio(field_name, parsed)
    )
    if str(normalized) != value:
        raise ValueError(
            f"{field_name} must be a canonical Decimal-derived string",
        )
    return normalized


def _require_public_count(field_name: str, value: object) -> Decimal:
    normalized = _require_public_decimal(
        field_name,
        value,
        quant=COUNT_QUANT,
    )
    if normalized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_public_ratio(field_name: str, value: object) -> Decimal:
    return _require_public_decimal(
        field_name,
        value,
        quant=RATIO_QUANT,
    )


def _require_public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_public_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_public_reason_codes(
    field_name: str,
    value: object,
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    return _normalize_reason_codes(tuple(value), known_reason_codes)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value), COUNT_QUANT)


def _claim_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchTeamDomainClaimMemoryDecayScorecardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_string(item_path, key)
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"unsafe public payload at {path}")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload at {path}")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_MEMORY_DECAY_SCORECARD_CONFIG_VERSION",
    "CLAIM_MEMORY_DECAY_STATUSES",
    "ResearchTeamDomainClaimMemoryDecayScorecardClaim",
    "ResearchTeamDomainClaimMemoryDecayScorecardConfig",
    "ResearchTeamDomainClaimMemoryDecayScorecardReport",
    "ResearchTeamDomainClaimMemoryDecayScorecardRow",
    "build_research_team_domain_claim_memory_decay_scorecard_report",
    "research_team_domain_claim_memory_decay_scorecard_payload",
)
