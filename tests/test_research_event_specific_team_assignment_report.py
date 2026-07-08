from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_specific_team_assignment_report import (
    DEFAULT_RESEARCH_EVENT_SPECIFIC_TEAM_ASSIGNMENT_CONFIG_VERSION,
    ResearchEventSpecificTeamAssignmentCandidate,
    ResearchEventSpecificTeamAssignmentConfig,
    ResearchEventSpecificTeamAssignmentReasonCodeCount,
    ResearchEventSpecificTeamAssignmentReport,
    ResearchEventSpecificTeamAssignmentRow,
    ResearchEventSpecificTeamLoad,
    build_research_event_specific_team_assignment_report,
    research_event_specific_team_assignment_digest,
    research_event_specific_team_assignment_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    candidate_reference: str = "raw-alpha-candidate-id-market_slug-source_url-secret_token",
    *,
    event_category: str = "finance.crypto.btc",
    observed_at: datetime | None = None,
    evidence_gap_score: Decimal = d("0.100000"),
    information_freshness_score: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventSpecificTeamAssignmentCandidate:
    return ResearchEventSpecificTeamAssignmentCandidate(
        candidate_reference=candidate_reference,
        event_category=event_category,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        evidence_gap_score=evidence_gap_score,
        information_freshness_score=information_freshness_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def load(
    team_id: str,
    *,
    active_event_count: Decimal = d("1.000000"),
    load_score: Decimal = d("0.100000"),
) -> ResearchEventSpecificTeamLoad:
    return ResearchEventSpecificTeamLoad(
        team_id=team_id,
        active_event_count=active_event_count,
        load_score=load_score,
    )


def build_report(
    candidates: tuple[ResearchEventSpecificTeamAssignmentCandidate, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventSpecificTeamAssignmentReport:
    return build_research_event_specific_team_assignment_report(
        candidates,
        team_loads=(
            load("crypto_btc", load_score=d("0.100000")),
            load("crypto_eth", load_score=d("0.800000")),
            load("macro_rates", load_score=d("0.200000")),
            load("sports_soccer", load_score=d("0.200000")),
            load("sports_other", load_score=d("0.650000")),
            load("politics", load_score=d("0.300000")),
        ),
        config=ResearchEventSpecificTeamAssignmentConfig(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(walk_values(key))
            values.extend(walk_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(walk_values(item))
    return tuple(values)


def test_assignment_scores_event_category_evidence_freshness_and_team_load() -> None:
    report = build_report(
        (
            candidate(
                "pass-raw-candidate-id-market-question-source_text",
                event_category="finance.crypto.btc",
                evidence_gap_score=d("0.100000"),
                information_freshness_score=d("0.950000"),
            ),
            candidate(
                "watch-raw-candidate-id-market_slug",
                event_category="sports.soccer",
                evidence_gap_score=d("0.600000"),
                information_freshness_score=d("0.650000"),
            ),
            candidate(
                "block-raw-candidate-id-market_slug",
                event_category="politics",
                evidence_gap_score=d("0.900000"),
                information_freshness_score=d("0.150000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, ResearchEventSpecificTeamAssignmentReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_EVENT_SPECIFIC_TEAM_ASSIGNMENT_CONFIG_VERSION
    )
    assert report.public_status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.public_status for row in report.rows) == ("block", "watch", "pass")

    blocked, watched, passed = report.rows
    assert blocked.lead_team == "politics"
    assert blocked.assignment_score == d("0.575000")
    assert blocked.reason_codes == (
        "research_event_specific_team_assignment_category_politics",
        "research_event_specific_team_assignment_evidence_gap_block",
        "research_event_specific_team_assignment_stale_information_block",
        "research_event_specific_team_assignment_block",
    )

    assert watched.lead_team == "sports_soccer"
    assert watched.public_status == "watch"
    assert watched.assignment_score == d("0.760000")
    assert watched.reason_codes == (
        "research_event_specific_team_assignment_category_sports_soccer",
        "research_event_specific_team_assignment_evidence_gap_watch",
        "research_event_specific_team_assignment_watch",
    )

    assert passed.lead_team == "crypto_btc"
    assert passed.support_teams == ("macro_rates", "crypto_eth")
    assert passed.category_fit_score == d("1.000000")
    assert passed.evidence_readiness_score == d("0.900000")
    assert passed.information_freshness_score == d("0.950000")
    assert passed.load_availability_score == d("0.900000")
    assert passed.assignment_score == d("0.955000")
    assert passed.reason_codes == (
        "research_event_specific_team_assignment_category_crypto_btc",
        "research_event_specific_team_assignment_pass",
    )

    assert report.reason_code_counts == (
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_category_politics",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_category_crypto_btc",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_category_sports_soccer",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_evidence_gap_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_evidence_gap_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_stale_information_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == tuple(item.reason_code for item in report.reason_code_counts)


def test_empty_report_is_public_block_without_rows() -> None:
    report = build_report(())

    assert report.public_status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_specific_team_assignment_no_inputs",
    )
    assert report.reason_code_counts == (
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code="research_event_specific_team_assignment_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )


def test_rejects_non_decimal_subclasses_bad_status_and_mutation() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        candidate(evidence_gap_score=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="exactly"):
        candidate(evidence_gap_score=_DecimalSubclass("0.100000"))

    with pytest.raises(TypeError, match="exactly"):
        candidate(event_category=_StringSubclass("finance.crypto.btc"))  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        candidate(observed_at="2026-07-08T11:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        candidate(observed_at=datetime(2026, 7, 8, 11, 0))

    with pytest.raises(ValueError, match="whole second"):
        candidate(observed_at=datetime(2026, 7, 8, 11, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly"):
        candidate(observed_at=_DateTimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)

    with pytest.raises(ValueError, match="unit interval"):
        candidate(evidence_gap_score=d("1.000001"))

    with pytest.raises(TypeError, match="Decimal"):
        load("crypto_btc", active_event_count=1)  # type: ignore[arg-type]

    report = build_report((candidate(),))
    with pytest.raises(FrozenInstanceError):
        report.public_status = "pass"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.rows[0].lead_team = "macro_rates"  # type: ignore[misc]

    with pytest.raises(ValueError, match="public_status"):
        replace(report.rows[0], public_status="ready")

    for cls in (
        ResearchEventSpecificTeamAssignmentCandidate,
        ResearchEventSpecificTeamLoad,
        ResearchEventSpecificTeamAssignmentConfig,
        ResearchEventSpecificTeamAssignmentRow,
        ResearchEventSpecificTeamAssignmentReasonCodeCount,
        ResearchEventSpecificTeamAssignmentReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True


def test_public_payload_rejects_and_redacts_sensitive_surfaces() -> None:
    report = build_report(
        (
            candidate(
                "candidate-raw-id-market_id-market_slug-market-question-source_ref-source_url-source_text-dsn-table-token-wallet-order-buy-sell-position",
                event_category="finance.crypto.btc",
            ),
        ),
    )
    payload = research_event_specific_team_assignment_payload(report)
    digest = research_event_specific_team_assignment_digest(report)
    rendered = repr((payload, digest, asdict(report))).lower()

    for token in (
        "candidate-raw-id",
        "market_id",
        "market_slug",
        "market-question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "secret",
        "token",
        "wallet",
        "order",
        "buy",
        "sell",
        "position",
        "recommendation",
    ):
        assert token not in rendered

    assert report.rows[0].event_reference_digest.startswith("sha256:")
    assert len(report.rows[0].event_reference_digest) == 19

    with pytest.raises(ValueError, match="unsafe"):
        replace(report.rows[0], safe_summary="uses source_url secret-token")

    with pytest.raises(ValueError, match="unsafe"):
        research_event_specific_team_assignment_payload(
            {"wallet_order": "submit trade"},  # type: ignore[arg-type]
        )


def test_payload_and_digest_are_deterministic_safe_and_consistent() -> None:
    candidates = (
        candidate("z-candidate-id", event_category="sports.soccer"),
        candidate("a-candidate-id", event_category="finance.crypto.btc"),
        candidate("m-candidate-id", event_category="politics", evidence_gap_score=d("0.900000")),
    )

    report_a = build_report(candidates)
    report_b = build_report(tuple(reversed(candidates)))

    payload_a = research_event_specific_team_assignment_payload(report_a)
    payload_b = research_event_specific_team_assignment_payload(report_b)
    digest_a = research_event_specific_team_assignment_digest(report_a)
    digest_b = research_event_specific_team_assignment_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a == research_event_specific_team_assignment_payload(report_a)
    assert digest_a == research_event_specific_team_assignment_digest(report_a)

    assert digest_a["generated_at"] == payload_a["generated_at"]
    assert digest_a["config_version"] == payload_a["config_version"]
    assert digest_a["public_status"] == payload_a["public_status"]
    assert digest_a["input_count"] == payload_a["input_count"]
    assert digest_a["pass_count"] == payload_a["pass_count"]
    assert digest_a["watch_count"] == payload_a["watch_count"]
    assert digest_a["block_count"] == payload_a["block_count"]
    assert digest_a["reason_codes"] == payload_a["reason_codes"]
    assert digest_a["row_count"] == str(len(payload_a["rows"]))

    assert not any(isinstance(value, float) for value in walk_values(payload_a))
    assert not any(isinstance(value, float) for value in walk_values(digest_a))


def test_report_module_is_read_only_and_has_no_live_or_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_specific_team_assignment_report.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "json",
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
        "broker",
        "signing",
        "order",
        "cancel",
        "account",
        "advice",
        "buy",
        "sell",
        "position",
        "recommendation",
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
    assert not any(term in source.lower() for term in forbidden_terms)


def test_public_status_contract_only_exposes_pass_watch_block() -> None:
    report = build_report((candidate(),))

    assert {row.public_status for row in report.rows}.issubset({"pass", "watch", "block"})
    assert report.public_status in {"pass", "watch", "block"}
    assert research_event_specific_team_assignment_digest(report)["allowed_public_statuses"] == [
        "pass",
        "watch",
        "block",
    ]


def test_payload_rejects_unknown_report_objects_before_public_export() -> None:
    class UnknownPublicPayload:
        def __init__(self) -> None:
            self.safe_status = "pass"

    with pytest.raises(ValueError, match="ResearchEventSpecificTeamAssignmentReport"):
        research_event_specific_team_assignment_payload(UnknownPublicPayload())  # type: ignore[arg-type]
