from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_politics_debate_performance_poll_reaction_digest import (
    DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION,
    MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
    MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
    MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
    MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
    MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
    build_market_research_politics_debate_performance_poll_reaction_digest_report,
    market_research_politics_debate_performance_poll_reaction_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_politics_debate_performance_poll_reaction_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchPoliticsDebatePerformancePollReactionDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION
        ),
        "performance_score_watch_floor": d("0.480000"),
        "performance_score_blocked_floor": d("0.400000"),
        "poll_reaction_drop_watch": d("0.010000"),
        "poll_reaction_drop_blocked": d("0.030000"),
        "favorability_drop_watch": d("0.010000"),
        "favorability_drop_blocked": d("0.030000"),
        "poll_sample_size_floor": d("600.000000"),
        "stale_source_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return MarketResearchPoliticsDebatePerformancePollReactionDigestConfig(**values)


def observation(
    candidate_id: str = "candidate-alpha",
    *,
    debate_id: str = "debate-general-1",
    poll_source: str = "pollster-alpha",
    debate_performance_score: Decimal = d("0.620000"),
    post_debate_poll_change: Decimal = d("0.010000"),
    favorability_change: Decimal = d("0.005000"),
    poll_sample_size: Decimal = d("1200.000000"),
    source_observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    reason_codes: tuple[str, ...] = ("debate_poll_reaction_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPoliticsDebatePerformancePollReactionDigestInput:
    return MarketResearchPoliticsDebatePerformancePollReactionDigestInput(
        candidate_id=candidate_id,
        debate_id=debate_id,
        poll_source=poll_source,
        debate_performance_score=debate_performance_score,
        post_debate_poll_change=post_debate_poll_change,
        favorability_change=favorability_change,
        poll_sample_size=poll_sample_size,
        source_observed_at=source_observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
    cfg: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPoliticsDebatePerformancePollReactionDigestReport:
    return build_market_research_politics_debate_performance_poll_reaction_digest_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_clear_poll_reaction_report_uses_decimal_payload_strings() -> None:
    digest = report(observation("candidate-clear"))

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == (
        DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION
    )
    assert digest.candidate_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.status == "pass"
    assert digest.reason_codes == (
        "politics_debate_performance_poll_reaction_digest_clear",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.candidate_rows[0]
    assert row.candidate_id == "candidate-clear"
    assert row.reaction_status == "pass"
    assert row.poll_reaction_pressure_score == d("0.000000")
    assert row.source_age_seconds == d("3600.000000")
    assert row.reason_codes == (
        "debate_poll_reaction_clear",
        "debate_poll_reaction_input_available",
    )

    payload = market_research_politics_debate_performance_poll_reaction_digest_payload(
        digest,
    )
    assert payload["candidate_count"] == "1.000000"
    assert payload["candidate_rows"][0]["poll_reaction_pressure_score"] == "0.000000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    digest = report()

    assert digest.status == "blocked"
    assert digest.candidate_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.mean_poll_reaction_pressure_score == ZERO
    assert digest.max_poll_reaction_pressure_score == ZERO
    assert digest.reason_codes == (
        "market_research_politics_debate_performance_poll_reaction_digest_no_inputs",
    )
    assert digest.reason_code_counts == (
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="market_research_politics_debate_performance_poll_reaction_digest_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest.candidate_rows == ()


def test_utc_normalization_for_generated_and_source_times() -> None:
    digest = report(
        observation(
            source_observed_at=datetime(
                2026,
                7,
                4,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.candidate_rows[0].source_observed_at == datetime(
        2026,
        7,
        4,
        11,
        0,
        tzinfo=UTC,
    )
    assert digest.candidate_rows[0].source_age_seconds == d("3600.000000")


def test_naive_datetimes_are_rejected_at_phase1_boundary() -> None:
    with pytest.raises(ValueError, match="source_observed_at"):
        observation(source_observed_at=datetime(2026, 7, 4, 11, 0))

    with pytest.raises(ValueError, match="generated_at"):
        report(observation("aware-source"), generated_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="source_observed_at"):
        observation(
            source_observed_at=datetime(
                2026,
                7,
                4,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )


def test_negative_poll_reaction_and_low_performance_roll_up() -> None:
    digest = report(
        observation(
            "candidate-watch",
            debate_performance_score=d("0.450000"),
            post_debate_poll_change=d("-0.020000"),
            favorability_change=d("0.005000"),
            poll_sample_size=d("400.000000"),
            source_observed_at=GENERATED_AT - timedelta(days=2),
        ),
        observation(
            "candidate-blocked",
            debate_performance_score=d("0.350000"),
            post_debate_poll_change=d("-0.040000"),
            favorability_change=d("-0.035000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.low_sample_size_count == d("1.000000")
    assert digest.stale_source_count == d("1.000000")
    assert digest.mean_poll_reaction_pressure_score == d("0.132500")
    assert digest.reason_codes == (
        "politics_debate_performance_poll_reaction_digest_blocked",
        "debate_performance_score_low_blocked",
        "debate_performance_score_low_watch",
        "favorability_drop_blocked",
        "poll_reaction_drop_blocked",
        "poll_reaction_drop_watch",
        "poll_sample_size_low_watch",
        "source_stale_watch",
    )
    assert digest.candidate_rows[0].candidate_id == "candidate-blocked"
    assert digest.candidate_rows[0].reason_codes == (
        "debate_performance_score_low_blocked",
        "debate_poll_reaction_input_available",
        "favorability_drop_blocked",
        "poll_reaction_drop_blocked",
    )
    assert digest.candidate_rows[1].reason_codes == (
        "debate_performance_score_low_watch",
        "debate_poll_reaction_input_available",
        "poll_reaction_drop_watch",
        "poll_sample_size_low_watch",
        "source_stale_watch",
    )


def test_deterministic_sorting_and_reason_code_counts() -> None:
    digest = report(
        observation(
            "zeta-watch",
            post_debate_poll_change=d("-0.020000"),
            poll_sample_size=d("500.000000"),
        ),
        observation(
            "beta-blocked",
            debate_performance_score=d("0.350000"),
            post_debate_poll_change=d("-0.040000"),
        ),
        observation(
            "alpha-pass",
            reason_codes=(
                "debate_poll_reaction_input_available",
                "post_debate_polling_stable",
            ),
        ),
        observation(
            "alpha-blocked",
            favorability_change=d("-0.040000"),
        ),
    )

    assert tuple(row.candidate_id for row in digest.candidate_rows) == (
        "beta-blocked",
        "alpha-blocked",
        "zeta-watch",
        "alpha-pass",
    )
    assert digest.reason_code_counts == (
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="debate_poll_reaction_input_available",
            count=d("4.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="debate_performance_score_low_blocked",
            count=d("1.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="debate_poll_reaction_clear",
            count=d("1.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="favorability_drop_blocked",
            count=d("1.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="poll_reaction_drop_blocked",
            count=d("1.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="poll_reaction_drop_watch",
            count=d("1.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="poll_sample_size_low_watch",
            count=d("1.000000"),
        ),
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="post_debate_polling_stable",
            count=d("1.000000"),
        ),
    )


def test_hard_flags_frozen_dataclasses_and_decimal_public_numbers() -> None:
    digest = report(observation("frozen"))

    assert is_dataclass(MarketResearchPoliticsDebatePerformancePollReactionDigestConfig)
    assert is_dataclass(MarketResearchPoliticsDebatePerformancePollReactionDigestInput)
    assert is_dataclass(MarketResearchPoliticsDebatePerformancePollReactionDigestRow)
    assert is_dataclass(
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
    )
    assert is_dataclass(MarketResearchPoliticsDebatePerformancePollReactionDigestReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.candidate_rows[0].poll_reaction_pressure_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    for item in (digest, *digest.candidate_rows, *digest.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "negative_poll_reaction_count",
        "low_performance_count",
        "low_sample_size_count",
        "stale_source_count",
        "mean_poll_reaction_pressure_score",
        "max_poll_reaction_pressure_score",
    ):
        assert type(getattr(digest, field_name)) is Decimal


def test_public_dataclasses_reject_subclassing_and_subclass_instances() -> None:
    digest = report(observation("exact-type"))
    public_values = (
        config(),
        observation("exact-input"),
        digest.candidate_rows[0],
        digest.reason_code_counts[0],
        digest,
    )

    for value in public_values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(value)}

        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)


def test_constructors_reject_noncanonical_sequences_and_reason_count_shapes() -> None:
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        observation(reason_codes=["debate_poll_reaction_input_available"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="canonical sequence"):
        observation(
            reason_codes=(
                "post_debate_polling_stable",
                "debate_poll_reaction_input_available",
            ),
        )

    with pytest.raises(ValueError, match="canonical sequence"):
        MarketResearchPoliticsDebatePerformancePollReactionDigestRow(
            candidate_id="row-sequence",
            debate_id="debate-general-1",
            poll_source="pollster-alpha",
            reaction_status="watch",
            debate_performance_score=d("0.450000"),
            post_debate_poll_change=d("-0.020000"),
            favorability_change=d("0.005000"),
            poll_sample_size=d("1200.000000"),
            poll_reaction_pressure_score=d("0.050000"),
            source_observed_at=GENERATED_AT - timedelta(hours=1),
            source_age_seconds=d("3600.000000"),
            reason_codes=(
                "debate_poll_reaction_input_available",
                "debate_performance_score_low_watch",
            ),
        )

    digest = report(
        observation("zeta-watch", post_debate_poll_change=d("-0.020000")),
        observation("alpha-pass"),
    )
    with pytest.raises(ValueError, match="candidate_rows"):
        replace(digest, candidate_rows=tuple(reversed(digest.candidate_rows)))

    with pytest.raises(ValueError, match="count"):
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="manual_zero",
            count=ZERO,
        )

    with pytest.raises(ValueError, match="whole"):
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code="manual_fraction",
            count=d("1.500000"),
        )

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            digest,
            reason_code_counts=(
                MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
                    reason_code="debate_poll_reaction_input_available",
                    count=d("2.000000"),
                ),
            ),
        )


def test_validation_errors_cover_inputs_config_payload_and_consistency() -> None:
    with pytest.raises(ValueError, match="performance_score_blocked_floor"):
        config(performance_score_blocked_floor=d("-0.000001"))
    with pytest.raises(ValueError, match="performance_score_blocked_floor"):
        config(
            performance_score_watch_floor=d("0.400000"),
            performance_score_blocked_floor=d("0.500000"),
        )
    with pytest.raises(ValueError, match="poll_reaction_drop_watch"):
        config(poll_reaction_drop_watch=d("0.040000"))
    with pytest.raises(ValueError, match="poll_sample_size_floor"):
        config(poll_sample_size_floor=_DecimalSubclass("600.000000"))
    with pytest.raises(ValueError, match="candidate_id"):
        observation(candidate_id=" candidate")
    with pytest.raises(ValueError, match="debate_id"):
        observation(debate_id="")
    with pytest.raises(ValueError, match="debate_performance_score"):
        observation(debate_performance_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="poll_sample_size"):
        observation(poll_sample_size=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        report(observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)))

    digest = report(observation("consistent"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="blocked")
    with pytest.raises(ValueError, match="negative_poll_reaction_count"):
        replace(digest, negative_poll_reaction_count=d("2.000000"))
    with pytest.raises(ValueError, match="mean_poll_reaction_pressure_score"):
        replace(digest, mean_poll_reaction_pressure_score=d("2.000000"))
    with pytest.raises(ValueError, match="unsafe"):
        observation(candidate_id="wallet_candidate")
    with pytest.raises(
        ValueError,
        match="MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
    ):
        market_research_politics_debate_performance_poll_reaction_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "candidate_count": 1.0,
            },
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
    ):
        market_research_politics_debate_performance_poll_reaction_digest_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
    ):
        market_research_politics_debate_performance_poll_reaction_digest_payload(
            [("candidate_count", d("1.000000"))],  # type: ignore[arg-type]
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
    ):
        market_research_politics_debate_performance_poll_reaction_digest_payload(
            object(),  # type: ignore[arg-type]
        )


def test_payload_revalidates_nested_report_dataclasses_after_tampering() -> None:
    digest = report(observation("tampered-row-shape"))
    row_payload = market_research_politics_debate_performance_poll_reaction_digest_payload(
        digest,
    )["candidate_rows"][0]
    object.__setattr__(digest, "candidate_rows", (row_payload,))
    with pytest.raises(ValueError, match="candidate_rows"):
        market_research_politics_debate_performance_poll_reaction_digest_payload(digest)

    digest = report(observation("tampered-row-decimal"))
    object.__setattr__(
        digest.candidate_rows[0],
        "poll_reaction_pressure_score",
        d("0.0000000"),
    )
    with pytest.raises(ValueError, match="six decimal"):
        market_research_politics_debate_performance_poll_reaction_digest_payload(digest)

    digest = report(observation("tampered-row-time"))
    object.__setattr__(
        digest.candidate_rows[0],
        "source_observed_at",
        datetime(
            2026,
            7,
            4,
            7,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )
    with pytest.raises(ValueError, match="UTC"):
        market_research_politics_debate_performance_poll_reaction_digest_payload(digest)

    digest = report(observation("tampered-row-flag"))
    object.__setattr__(digest.candidate_rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_politics_debate_performance_poll_reaction_digest_payload(digest)

    digest = report(observation("tampered-reason-count"))
    object.__setattr__(digest.reason_code_counts[0], "count", ZERO)
    with pytest.raises(ValueError, match="count"):
        market_research_politics_debate_performance_poll_reaction_digest_payload(digest)


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.market_research_politics_debate_performance_poll_reaction_digest as digest

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION",
        "MarketResearchPoliticsDebatePerformancePollReactionDigestConfig",
        "MarketResearchPoliticsDebatePerformancePollReactionDigestInput",
        "MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount",
        "MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
        "MarketResearchPoliticsDebatePerformancePollReactionDigestRow",
        "build_market_research_politics_debate_performance_poll_reaction_digest_report",
        "market_research_politics_debate_performance_poll_reaction_digest_payload",
    )


def test_static_forbidden_surface_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "market_slug",
        "question",
        "payload_json",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_dataclass_helpers = {"asdict"}
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    forbidden_public_fields = {"market_slug", "question", "payload_json"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            if isinstance(node.value, str):
                assert node.value not in forbidden_public_fields
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assert node.target.id not in forbidden_public_fields
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", *forbidden_dataclass_helpers}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(
                alias.name not in forbidden_dataclass_helpers
                for alias in node.names
            )


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]
