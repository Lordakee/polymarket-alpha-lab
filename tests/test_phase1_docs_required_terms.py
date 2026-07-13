from __future__ import annotations

import re
from pathlib import Path


PHASE1_NEW_DOC_PATHS = (
    Path("docs/acceptance/phase-1-development-node-acceptance-checklist.md"),
    Path("docs/config/phase-1-strategy-screening-schema.md"),
    Path("docs/contracts/phase1-data-field-contracts.md"),
    Path("docs/data_dictionary/phase1-research-decision-objects.md"),
    Path("docs/operators/phase1-probability-event-go-no-go-runbook.md"),
    Path("docs/phase1/probability-event-readonly-supabase-principles.md"),
    Path("docs/phases/2026-07-12-phase-1-capability-baseline.md"),
    Path("docs/playbooks/phase1-specialist-team-playbooks.md"),
    Path("docs/quality/phase-1-development-node-quality-gates.md"),
    Path("docs/research/source-acquisition-quality-policy.md"),
    Path("docs/review/2026-07-12-operating-review-rules.md"),
    Path("docs/risk/phase1-risk-capital-settlement-policy.md"),
    Path("docs/roadmap/2026-07-12-project-progress-roadmap.md"),
    Path("docs/strategy/phase1-probability-event-filtering-workflow.md"),
    Path("docs/supabase/local-supabase-operations.md"),
)

REQUIRED_CORE_RULE_PATTERNS = {
    "Polymarket probability events": r"\bPolymarket\s+probability[- ]event",
    "manual go/no-go": r"\bmanual\b.{0,120}\bgo/no-go\b|\bgo/no-go\b.{0,120}\bmanual\b",
    "local Supabase/Postgres": r"\blocal(?:-only)?\s+Supabase/Postgres\b",
    "paper_only flag": r"\bpaper_only\b",
    "report_only flag": r"\breport_only\b",
    "readonly flag": r"\breadonly\b",
    "no live trading": (
        r"\bno\s+live\s+trading\b"
        r"|\bdoes\s+not\s+authorize\s+live\s+trading\b"
        r"|\bnot\b.{0,120}\blive\s+trading\b"
        r"|\blive\s+trading\b.{0,120}\b(?:forbidden|out\s+of\s+scope|not)\b"
    ),
    "no wallet/private key/order submission": (
        r"\bno\s+wallet/private\s+key/order\s+submission\b"
        r"|\bno\s+wallet/private\s+keys?\b"
        r"|\bwallet/private-key\s+handling\b"
        r"|\bwallet\s+handling\b.{0,160}\border\s+(?:signing|submission)\b"
        r"|\bno\s+live\s+order,\s+wallet\b.{0,160}\b(?:signing|submission)\b"
    ),
}

BOUNDARY_ONLY_TERMS = (
    "live trading",
    "wallet",
    "wallet/private key",
    "private key",
    "private-key",
    "order submission",
    "order signing",
    "submit order",
)

BOUNDARY_MARKERS = (
    "account mutation",
    "boundary",
    "does not",
    "do not",
    "exclude",
    "excludes",
    "fail closed",
    "forbidden",
    "must not",
    "no ",
    "not ",
    "out of scope",
    "prohibited",
    "readonly",
    "reject",
    "without",
)

CRITICAL_BOUNDARY_DOC_PATHS = (
    Path("docs/operators/phase1-probability-event-go-no-go-runbook.md"),
    Path("docs/phase1/probability-event-readonly-supabase-principles.md"),
    Path("docs/risk/phase1-risk-capital-settlement-policy.md"),
    Path("docs/strategy/phase1-probability-event-filtering-workflow.md"),
)

DATA_FIELD_CONTRACT_PATH = Path("docs/contracts/phase1-data-field-contracts.md")
SCREENING_SCHEMA_PATH = Path("docs/config/phase-1-strategy-screening-schema.md")
RISK_POLICY_PATH = Path("docs/risk/phase1-risk-capital-settlement-policy.md")
AGENT_POLICY_PATH = Path("AGENTS.md")
AGENT_CONCURRENCY_PATH = Path(
    "docs/maintenance/phase1-agent-concurrency-and-review-rules.md",
)


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _combined_text(paths: tuple[Path, ...]) -> str:
    return _normalized("\n".join(_read(path) for path in paths))


def _prose_contexts(text: str) -> tuple[str, ...]:
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in text.lower().splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped and not (
            current and current[-1].rstrip().endswith((":", "include:"))
        ):
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        current.append(stripped)

    if current:
        blocks.append(" ".join(current))

    return tuple(
        " ".join(blocks[max(0, index - 1) : index + 2])
        for index in range(len(blocks))
    )


def test_phase1_new_docs_exist_and_are_markdown() -> None:
    assert len(PHASE1_NEW_DOC_PATHS) == 15

    for path in PHASE1_NEW_DOC_PATHS:
        assert path.suffix == ".md", path
        assert path.exists(), path


def test_phase1_new_docs_keep_required_core_rules_in_corpus() -> None:
    combined_text = _combined_text(PHASE1_NEW_DOC_PATHS)

    for rule_name, pattern in REQUIRED_CORE_RULE_PATTERNS.items():
        assert re.search(pattern, combined_text, flags=re.IGNORECASE), rule_name


def test_phase1_critical_boundary_docs_repeat_required_rules() -> None:
    for path in CRITICAL_BOUNDARY_DOC_PATHS:
        text = _normalized(_read(path))

        for rule_name, pattern in REQUIRED_CORE_RULE_PATTERNS.items():
            if rule_name == "local Supabase/Postgres" and path.name.startswith(
                "phase1-risk",
            ):
                continue
            assert re.search(pattern, text, flags=re.IGNORECASE), (path, rule_name)


def test_phase1_docs_keep_execution_sensitive_terms_as_boundaries() -> None:
    for path in PHASE1_NEW_DOC_PATHS:
        for context in _prose_contexts(_read(path)):
            if any(term in context for term in BOUNDARY_ONLY_TERMS):
                assert any(marker in context for marker in BOUNDARY_MARKERS), (
                    path,
                    context,
                )


def test_phase1_data_contract_freezes_input_failure_timestamp_and_digest_shape() -> None:
    text = _normalized(_read(DATA_FIELD_CONTRACT_PATH))

    for required_text in (
        "InputFailureDegradationReadinessReport.generated_at",
        "exact timezone-aware `datetime`",
        "datetime.UTC",
        "2026-07-12T10:30:00+00:00",
        "must not be shortened to `Z`",
        "Input failure degradation readiness",
        "Probability-event market-signal risk readiness",
        "stored `payload_digest`",
        "InputFailureSignal",
    ):
        assert required_text in text


def test_phase1_docs_freeze_forecast_context_minimums_and_time_ordering() -> None:
    contracts_text = _normalized(_read(DATA_FIELD_CONTRACT_PATH))
    schema_text = _normalized(_read(SCREENING_SCHEMA_PATH))

    assert (
        "published_at <= captured_at <= context_captured_at <= generated_at"
        in contracts_text
    )
    assert "source timestamps must still be `<= generated_at`" in contracts_text
    for required_text in (
        "default_min_source_count",
        "default_min_source_family_count",
        "microstructure_min_source_count",
        "microstructure_min_source_family_count",
        "superforecaster_min_source_count",
        "superforecaster_min_source_family_count",
        "yes_ask_naive_v0",
        "book_imbalance_v0",
        "superforecaster_prompt_v0",
    ):
        assert required_text in schema_text


def test_phase1_risk_policy_freezes_portfolio_watch_reason_rollup() -> None:
    text = _normalized(_read(RISK_POLICY_PATH))

    for reason_code in (
        "same_outcome_dependency_watch",
        "correlation_cluster_concentration_watch",
        "event_category_concentration_watch",
        "capital_lockup_concentration_watch",
        "extended_lockup_watch",
        "negative_edge_after_lockup_watch",
        "low_exit_liquidity_watch",
    ):
        assert f"`{reason_code}`" in text
    assert "all canonical watch reasons" in text
    assert "block reasons plus `low_exit_liquidity_watch` only" in text


def test_project_policy_freezes_sustained_parallel_development_iron_rule() -> None:
    agents_text = _normalized(_read(AGENT_POLICY_PATH))
    concurrency_text = _normalized(_read(AGENT_CONCURRENCY_PATH))

    for required_text in (
        "Sustained parallel development is a project iron rule",
        "20 active subagent threads",
        "nested subagent depth cap of **3**",
        "ceilings, not quotas or minimums",
        "use fewer threads whenever",
        "multiple modules and multiple development nodes",
        "Reclaim agents immediately",
        "permanent lower artificial cap",
    ):
        assert required_text in agents_text

    for required_text in (
        "implements Project Iron Rule 6",
        "20 active subagent threads",
        "nested depth **3**",
        "ceilings, not quotas, minimums",
        "may run fewer active threads",
        "multiple modules and multiple development nodes",
        "permanent lower ceiling",
        "Failed or blocked agents must also be reclaimed promptly",
        "primary Codex coordinator follows the `AGENTS.md` Codex Node Push Policy",
        "Subagents must not create commits or push branches",
    ):
        assert required_text in concurrency_text

    for stale_text in (
        "64 active subagent threads",
        "nested subagent depth cap of **4**",
        "nested depth **4**",
    ):
        assert stale_text not in agents_text
        assert stale_text not in concurrency_text
