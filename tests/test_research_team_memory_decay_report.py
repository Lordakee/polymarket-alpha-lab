from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_memory_decay_report import (
    DEFAULT_RESEARCH_TEAM_MEMORY_DECAY_REPORT_CONFIG_VERSION,
    ResearchTeamMemoryDecayConfig,
    ResearchTeamMemoryDecayDigest,
    ResearchTeamMemoryDecayObservation,
    ResearchTeamMemoryDecayReasonCodeCount,
    ResearchTeamMemoryDecayReport,
    ResearchTeamMemoryDecayRow,
    build_research_team_memory_decay_report,
    research_team_memory_decay_digest,
    research_team_memory_decay_digest_payload,
    research_team_memory_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
_DEFAULT_REVIEW_AT = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    team_id: str = "politics",
    *,
    category_id: str = "politics",
    specialist_role: str = "politics_memory_postmortem",
    internal_memory_key: str = "candidate://alpha?market_id=pm-1&slug=hidden&question=hidden",
    latest_memory_refresh_at: datetime | None = None,
    latest_review_completed_at: object = _DEFAULT_REVIEW_AT,
    memory_confidence_score: Decimal = d("0.900000"),
    unresolved_conflict_count: Decimal = d("0.000000"),
    review_gap_count: Decimal = d("0.000000"),
    postmortem_coverage_ratio: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamMemoryDecayObservation:
    return ResearchTeamMemoryDecayObservation(
        team_id=team_id,
        category_id=category_id,
        specialist_role=specialist_role,
        internal_memory_key=internal_memory_key,
        latest_memory_refresh_at=latest_memory_refresh_at
        or GENERATED_AT - timedelta(days=1),
        latest_review_completed_at=(
            GENERATED_AT - timedelta(days=1)
            if latest_review_completed_at is _DEFAULT_REVIEW_AT
            else latest_review_completed_at
        ),
        memory_confidence_score=memory_confidence_score,
        unresolved_conflict_count=unresolved_conflict_count,
        review_gap_count=review_gap_count,
        postmortem_coverage_ratio=postmortem_coverage_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchTeamMemoryDecayObservation, ...],
    *,
    cfg: ResearchTeamMemoryDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamMemoryDecayReport:
    return build_research_team_memory_decay_report(
        rows,
        config=cfg or ResearchTeamMemoryDecayConfig(),
        generated_at=generated_at,
    )


def test_team_memory_decay_report_scores_pass_watch_and_block_rows() -> None:
    summary = report(
        (
            observation(
                "crypto_btc",
                category_id="finance.crypto.btc",
                specialist_role="btc_memory_postmortem",
                internal_memory_key=(
                    "candidate://btc?market_id=pm-btc&slug=btc-hidden&question=hidden"
                ),
            ),
            observation(
                "macro_rates",
                category_id="finance.macro.rates",
                specialist_role="macro_memory_postmortem",
                internal_memory_key=(
                    "candidate://macro?source_url=https://hidden.example/private"
                ),
                latest_memory_refresh_at=GENERATED_AT - timedelta(days=40),
                latest_review_completed_at=GENERATED_AT - timedelta(days=20),
                memory_confidence_score=d("0.850000"),
                unresolved_conflict_count=d("2.000000"),
                review_gap_count=d("1.000000"),
                postmortem_coverage_ratio=d("0.550000"),
            ),
            observation(
                "sports_soccer",
                category_id="sports.soccer",
                specialist_role="soccer_memory_postmortem",
                internal_memory_key="candidate://soccer?raw_candidate_id=secret",
                latest_memory_refresh_at=GENERATED_AT - timedelta(days=70),
                latest_review_completed_at=None,
                memory_confidence_score=d("0.400000"),
                unresolved_conflict_count=d("5.000000"),
                review_gap_count=d("3.000000"),
                postmortem_coverage_ratio=d("0.200000"),
            ),
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == DEFAULT_RESEARCH_TEAM_MEMORY_DECAY_REPORT_CONFIG_VERSION
    assert summary.public_status == "block"
    assert summary.observation_count == d("3.000000")
    assert summary.team_count == d("3.000000")
    assert summary.specialist_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.stale_memory_count == d("2.000000")
    assert summary.conflict_accumulation_count == d("2.000000")
    assert summary.postmortem_coverage_gap_count == d("2.000000")
    assert summary.review_gap_count == d("2.000000")
    assert summary.score_gap_count == d("2.000000")
    assert summary.average_adjusted_memory_score == d("0.456667")
    assert summary.average_postmortem_coverage_ratio == d("0.550000")
    assert summary.max_memory_age_seconds == d("6048000.000000")
    assert summary.local_supabase_summary_ready is True
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.public_status for row in summary.rows) == (
        "block",
        "watch",
        "pass",
    )

    blocked = summary.rows[0]
    assert blocked.team_id == "sports_soccer"
    assert blocked.memory_age_seconds == d("6048000.000000")
    assert blocked.review_age_seconds is None
    assert blocked.adjusted_memory_score == d("0.000000")
    assert blocked.reason_codes == (
        "research_team_memory_decay_stale",
        "research_team_memory_conflict_accumulation_block",
        "research_team_postmortem_coverage_gap",
        "research_team_review_gap_block",
        "research_team_memory_score_block",
    )

    watched = summary.rows[1]
    assert watched.team_id == "macro_rates"
    assert watched.memory_age_seconds == d("3456000.000000")
    assert watched.review_age_seconds == d("1728000.000000")
    assert watched.adjusted_memory_score == d("0.470000")
    assert watched.reason_codes == (
        "research_team_memory_decay_stale",
        "research_team_memory_conflict_accumulation_watch",
        "research_team_postmortem_coverage_gap",
        "research_team_review_gap_watch",
        "research_team_memory_score_watch",
    )

    passed = summary.rows[2]
    assert passed.team_id == "crypto_btc"
    assert passed.public_memory_digest.startswith("sha256:")
    assert passed.adjusted_memory_score == d("0.900000")
    assert passed.reason_codes == ("research_team_memory_decay_current",)

    assert summary.reason_code_counts == (
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_memory_decay_stale",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_memory_conflict_accumulation_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_memory_conflict_accumulation_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_postmortem_coverage_gap",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_review_gap_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_review_gap_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_memory_score_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_memory_score_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code="research_team_memory_decay_current",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == (
        "research_team_memory_decay_report_stale_present",
        "research_team_memory_decay_report_conflict_present",
        "research_team_memory_decay_report_postmortem_coverage_gap_present",
        "research_team_memory_decay_report_review_gap_present",
        "research_team_memory_decay_report_score_gap_present",
    )


def test_team_memory_decay_report_public_status_rollups() -> None:
    pass_summary = report((observation(),))
    assert pass_summary.public_status == "pass"
    assert pass_summary.reason_codes == (
        "research_team_memory_decay_report_current",
    )

    watch_summary = report(
        (
            observation(
                latest_memory_refresh_at=GENERATED_AT - timedelta(days=40),
                memory_confidence_score=d("0.850000"),
            ),
        ),
    )
    assert watch_summary.public_status == "watch"
    assert watch_summary.rows[0].public_status == "watch"

    block_summary = report(
        (
            observation(
                memory_confidence_score=d("0.200000"),
                unresolved_conflict_count=d("5.000000"),
            ),
        ),
    )
    assert block_summary.public_status == "block"
    assert block_summary.rows[0].public_status == "block"

    empty_summary = report(())
    assert empty_summary.public_status == "pass"
    assert empty_summary.observation_count == d("0.000000")
    assert empty_summary.rows == ()
    assert empty_summary.reason_codes == (
        "research_team_memory_decay_no_observations",
    )


def test_team_memory_decay_report_rejects_types_decimals_flags_and_mutation() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        observation(memory_confidence_score=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="exactly Decimal"):
        observation(memory_confidence_score=_DecimalSubclass("0.900000"))

    with pytest.raises(TypeError, match="datetime"):
        observation(latest_memory_refresh_at="2026-07-08T11:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        observation(
            latest_memory_refresh_at=_DateTimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(latest_memory_refresh_at=datetime(2026, 7, 8, 11, 0))

    with pytest.raises(ValueError, match="whole second"):
        observation(latest_memory_refresh_at=datetime(2026, 7, 8, 11, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly str"):
        observation(specialist_role=_StringSubclass("politics_memory_postmortem"))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="whole number"):
        observation(unresolved_conflict_count=d("1.500000"))

    with pytest.raises(ValueError, match="unit interval"):
        observation(postmortem_coverage_ratio=d("1.000001"))

    with pytest.raises(TypeError, match="tuple"):
        build_research_team_memory_decay_report(
            [observation()],  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    frozen = observation()
    with pytest.raises(FrozenInstanceError):
        frozen.memory_confidence_score = d("0.100000")  # type: ignore[misc]

    summary = report((observation(),))
    with pytest.raises(FrozenInstanceError):
        summary.public_status = "block"  # type: ignore[misc]


def test_team_memory_decay_report_rejects_public_leaks_but_hashes_internal_keys() -> None:
    summary = report(
        (
            observation(
                internal_memory_key=(
                    "raw_candidate_id=abc|market_id=pm|slug=hidden|question=hidden|"
                    "source_ref=https://hidden.example/path?token=secret|wallet=0xabc|"
                    "order=hidden|position=hidden|buy=sell|recommend=hidden"
                ),
            ),
        ),
    )
    payload = research_team_memory_decay_report_payload(summary)
    public = json.dumps(payload, sort_keys=True).lower()
    for leak in (
        "raw_candidate_id",
        "candidate://",
        "market_id",
        "slug=hidden",
        "question=hidden",
        "source_ref",
        "hidden.example",
        "token=secret",
        "wallet",
        "order",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert leak not in public

    with pytest.raises(ValueError, match="unsafe"):
        observation(specialist_role="wallet_research")

    with pytest.raises(ValueError, match="unsafe"):
        research_team_memory_decay_report_payload(
            {
                "raw_candidate_id": "abc",
                "derived_validation_digest": "0" * 64,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_team_memory_decay_report_payload_and_digest_are_deterministic() -> None:
    row_a = observation(
        "crypto_eth",
        category_id="finance.crypto.eth",
        specialist_role="eth_memory_postmortem",
        internal_memory_key="candidate://eth?market_id=hidden",
    )
    row_b = observation(
        "politics",
        category_id="politics",
        specialist_role="politics_memory_postmortem",
        internal_memory_key="candidate://politics?market_id=hidden",
        latest_memory_refresh_at=GENERATED_AT - timedelta(days=40),
        memory_confidence_score=d("0.850000"),
    )

    first = report((row_b, row_a))
    second = report((row_a, row_b))

    first_payload = research_team_memory_decay_report_payload(first)
    second_payload = research_team_memory_decay_report_payload(second)
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )

    first_digest = research_team_memory_decay_digest(first)
    second_digest = research_team_memory_decay_digest(second)
    assert research_team_memory_decay_digest_payload(first_digest) == (
        research_team_memory_decay_digest_payload(second_digest)
    )


def test_team_memory_decay_report_and_digest_are_consistent_and_validated() -> None:
    summary = report(
        (
            observation(),
            observation(
                "sports_basketball",
                category_id="sports.basketball",
                specialist_role="basketball_memory_postmortem",
                internal_memory_key="candidate://basketball?question=hidden",
                unresolved_conflict_count=d("5.000000"),
            ),
        ),
    )
    digest = research_team_memory_decay_digest(summary)

    assert isinstance(digest, ResearchTeamMemoryDecayDigest)
    assert digest.public_status == summary.public_status
    assert digest.observation_count == summary.observation_count
    assert digest.pass_count == summary.pass_count
    assert digest.watch_count == summary.watch_count
    assert digest.block_count == summary.block_count
    assert digest.reason_codes == summary.reason_codes
    assert digest.report_validation_digest == summary.derived_validation_digest
    assert digest.local_supabase_summary_ready is True
    assert digest.derived_validation_digest != summary.derived_validation_digest

    payload = research_team_memory_decay_report_payload(summary)
    digest_payload = research_team_memory_decay_digest_payload(digest)
    assert payload["derived_validation_digest"] == digest_payload["report_validation_digest"]
    assert digest_payload["public_status"] in {"pass", "watch", "block"}

    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_memory_decay_report_payload(
            {
                **payload,
                "pass_count": "9.000000",
            },
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_memory_decay_digest_payload(
            {
                **digest_payload,
                "public_status": "watch",
            },
        )

    with pytest.raises(ValueError, match="public_status"):
        replace(summary.rows[0], public_status="blocked")

    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary.rows[0], reason_codes=("research_team_memory_decay_current", "bad"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)

    assert asdict(digest)["report_validation_digest"] == summary.derived_validation_digest


def test_team_memory_decay_report_module_is_report_only_and_has_no_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_memory_decay_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8")
    module_lower = module_text.lower()
    tree = ast.parse(module_text)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "position",
        "buy",
        "sell",
        "recommend",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in module_lower for term in forbidden_terms)

    for cls in (
        ResearchTeamMemoryDecayConfig,
        ResearchTeamMemoryDecayObservation,
        ResearchTeamMemoryDecayRow,
        ResearchTeamMemoryDecayReasonCodeCount,
        ResearchTeamMemoryDecayReport,
        ResearchTeamMemoryDecayDigest,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
