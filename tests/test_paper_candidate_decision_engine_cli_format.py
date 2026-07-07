from __future__ import annotations

import builtins
import importlib
import inspect
import sys
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


def _format_paper_candidate_decision_engine_report_cli_stdout(report: object) -> str:
    module = importlib.import_module(
        "polymarket_alpha_lab.paper_candidate_decision_engine_cli_format",
    )
    return module.format_paper_candidate_decision_engine_report_cli_stdout(report)


@dataclass(frozen=True)
class ReasonCodeCount:
    reason_code: str
    count: object


@dataclass(frozen=True)
class PaperCandidateDecisionEngineReportFixture:
    config_version: str
    candidate_count: object
    reject_count: object
    watch_count: object
    research_more_count: object
    paper_recommend_count: object
    reason_counts: tuple[ReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_format_paper_candidate_decision_engine_report_cli_stdout_formats_only_public_aggregate_fields() -> None:
    report = PaperCandidateDecisionEngineReportFixture(
        config_version="paper-candidate-decision-engine-v0",
        candidate_count="4",
        reject_count="1",
        watch_count="1",
        research_more_count="1",
        paper_recommend_count="1",
        reason_counts=(
            ReasonCodeCount("candidate_decision_reject_fee_drag", "1"),
            ReasonCodeCount("candidate_decision_watch_liquidity", "2"),
        ),
    )

    stdout = _format_paper_candidate_decision_engine_report_cli_stdout(report)

    assert stdout == (
        "paper-candidate-decision-engine-report: "
        "config_version=paper-candidate-decision-engine-v0 "
        "candidate_count=4 "
        "reject=1 "
        "watch=1 "
        "research_more=1 "
        "paper_recommend=1 "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
        "reason_code_counts: "
        "candidate_decision_reject_fee_drag:1 "
        "candidate_decision_watch_liquidity:2\n"
    )


def test_format_paper_candidate_decision_engine_report_cli_stdout_accepts_simple_namespace_and_mapping_reason_counts() -> None:
    report = SimpleNamespace(
        config_version="paper-candidate-decision-engine-v0",
        candidate_count=2,
        reject_count=0,
        watch_count=1,
        research_more_count=0,
        paper_recommend_count=1,
        reason_counts=(
            {"reason_code": "candidate_decision_watch_liquidity", "count": 1},
            ("candidate_decision_paper_recommend_expected_value", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = _format_paper_candidate_decision_engine_report_cli_stdout(report)

    assert stdout == (
        "paper-candidate-decision-engine-report: "
        "config_version=paper-candidate-decision-engine-v0 "
        "candidate_count=2 "
        "reject=0 "
        "watch=1 "
        "research_more=0 "
        "paper_recommend=1 "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
        "reason_code_counts: "
        "candidate_decision_watch_liquidity:1 "
        "candidate_decision_paper_recommend_expected_value:1\n"
    )


def test_format_paper_candidate_decision_engine_report_cli_stdout_prints_none_for_empty_reason_counts() -> None:
    report = PaperCandidateDecisionEngineReportFixture(
        config_version="paper-candidate-decision-engine-v0",
        candidate_count=0,
        reject_count=0,
        watch_count=0,
        research_more_count=0,
        paper_recommend_count=0,
        reason_counts=(),
    )

    stdout = _format_paper_candidate_decision_engine_report_cli_stdout(report)

    assert stdout.endswith("reason_code_counts: none\n")


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("paper_only", False),
        ("paper_only", 1),
        ("report_only", False),
        ("report_only", 1),
        ("readonly", False),
        ("readonly", 1),
    ),
)
def test_format_paper_candidate_decision_engine_report_cli_stdout_fails_closed_when_hard_flags_are_not_exactly_true(
    field_name: str,
    value: object,
) -> None:
    report = PaperCandidateDecisionEngineReportFixture(
        config_version="paper-candidate-decision-engine-v0",
        candidate_count=1,
        reject_count=1,
        watch_count=0,
        research_more_count=0,
        paper_recommend_count=0,
        reason_counts=(),
    )
    report = SimpleNamespace(**{**report.__dict__, field_name: value})

    with pytest.raises(ValueError, match=f"{field_name} must be True"):
        _format_paper_candidate_decision_engine_report_cli_stdout(report)


def test_format_paper_candidate_decision_engine_report_cli_stdout_does_not_echo_row_level_or_sensitive_fields() -> None:
    forbidden_values = {
        "candidate-secret-123",
        "market-secret-456",
        "Will private team win?",
        "private-market-slug",
        "https://source.example/private",
        "hash-secret-789",
        "payload-secret-abc",
        "postgresql://user:password@db.example/polymarket",
        "db.example",
        "candidate_decision_score_history",
    }
    report = SimpleNamespace(
        config_version="paper-candidate-decision-engine-v0",
        candidate_count=1,
        reject_count=0,
        watch_count=1,
        research_more_count=0,
        paper_recommend_count=0,
        reason_counts=(ReasonCodeCount("candidate_decision_watch_liquidity", 1),),
        rows=(
            SimpleNamespace(
                candidate_id="candidate-secret-123",
                market_id="market-secret-456",
                normalized_market_question="Will private team win?",
                market_slug="private-market-slug",
                source_refs=("https://source.example/private",),
                payload_hash="hash-secret-789",
                raw_payload="payload-secret-abc",
                dsn="postgresql://user:password@db.example/polymarket",
                host="db.example",
                table_name="candidate_decision_score_history",
            ),
        ),
        candidate_id="candidate-secret-123",
        market_id="market-secret-456",
        normalized_market_question="Will private team win?",
        market_slug="private-market-slug",
        market_question="Will private team win?",
        source_refs=("https://source.example/private",),
        payload_hash="hash-secret-789",
        raw_payload="payload-secret-abc",
        dsn="postgresql://user:password@db.example/polymarket",
        host="db.example",
        table_name="candidate_decision_score_history",
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = _format_paper_candidate_decision_engine_report_cli_stdout(report)

    for forbidden_value in forbidden_values:
        assert forbidden_value not in stdout


@pytest.mark.parametrize(
    "reason_code",
    (
        "candidate_id_leaked",
        "authorization_token_present",
        "cancel_live_order",
    ),
)
def test_format_paper_candidate_decision_engine_report_cli_stdout_rejects_unsafe_reason_count_labels(
    reason_code: str,
) -> None:
    report = PaperCandidateDecisionEngineReportFixture(
        config_version="paper-candidate-decision-engine-v0",
        candidate_count=1,
        reject_count=1,
        watch_count=0,
        research_more_count=0,
        paper_recommend_count=0,
        reason_counts=(ReasonCodeCount(reason_code, 1),),
    )

    with pytest.raises(ValueError, match="unsafe public summary value"):
        _format_paper_candidate_decision_engine_report_cli_stdout(report)


def test_formatter_imports_no_db_network_filesystem_or_subprocess_modules(
    monkeypatch: Any,
) -> None:
    disallowed_import_roots = {
        "asyncpg",
        "dotenv",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
    }
    imported_roots: list[str] = []
    original_import = builtins.__import__

    def tracking_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if level == 0:
            imported_roots.append(name.partition(".")[0])
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", tracking_import)
    sys.modules.pop(
        "polymarket_alpha_lab.paper_candidate_decision_engine_cli_format",
        None,
    )

    importlib.import_module(
        "polymarket_alpha_lab.paper_candidate_decision_engine_cli_format",
    )

    assert set(imported_roots).isdisjoint(disallowed_import_roots)


def test_formatter_source_exposes_no_live_trading_or_mutation_api_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.paper_candidate_decision_engine_cli_format",
    )
    public_names = tuple(name for name in dir(module) if not name.startswith("_"))
    forbidden_public_fragments = (
        "account",
        "auth",
        "cancel",
        "client",
        "exchange",
        "order",
        "private_key",
        "replace",
        "signing",
        "trading",
        "wallet",
    )

    assert public_names == ("format_paper_candidate_decision_engine_report_cli_stdout",)
    signature = inspect.signature(
        module.format_paper_candidate_decision_engine_report_cli_stdout,
    )
    for parameter_name in signature.parameters:
        for fragment in forbidden_public_fragments:
            assert fragment not in parameter_name
