# Level 2 Proposal Evidence Comparison Artifact Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static, report-only registry describing the existing proposal evidence comparison artifact chain so later automation can discover available in-memory report builders without importing loaders, clients, scraping, accounts, or execution surfaces.

**Architecture:** Create one small `proposal_evidence_comparison_artifact_registry.py` module with frozen dataclasses and string metadata only. The registry is static, deterministic, and does not import any artifact implementation modules. It exposes tuple/list functions for introspection, and tests assert ordering, immutability, known artifact metadata, and report-only boundaries.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, pytest, CodeGraph, Codex subagents using `gpt-5.5` with reasoning `xhigh`, and local Claude Code review with model `claude-opus-4-8` using effort `max`.

---

## Project Rules To Preserve

- Codex implementation subagents must be launched with model `gpt-5.5` and reasoning effort `xhigh`.
- Implementation review and audit must be local Claude Code with model `claude-opus-4-8` and effort `max`; Claude review is read-only and must not edit or create files.
- Do not run multiple agents that edit the same files at the same time. Assign file ownership per task.
- Use CodeGraph before grep, find, or manual file reads when locating or understanding code because this repository has `.codegraph/`.
- The registry must not add web scraping, browser automation, account automation, live execution, trading, order placement, order cancellation, API clients, HTTP clients, request/session/WebSocket clients, credential workflows, wallet/private-key handling, approval workflows, recommendation/ranking logic, or financial advice.
- The registry must not fetch, discover, load, replay, glob, or read reports from disk or external systems. It is static metadata only.

## Files

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_artifact_registry.py`
- Create: `tests/test_proposal_evidence_comparison_artifact_registry.py`
- Create: `tests/test_proposal_evidence_comparison_artifact_registry_scope.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

No sibling allowlist tests need modification because this plan adds one production module and one matching scope test; existing scope tests should continue to parse package modules by their local allowlists.

## Public API

The module must expose exactly these public names:

```python
__all__ = (
    "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
    "REPORT_ONLY_FORBIDDEN_SURFACES",
    "ProposalEvidenceComparisonArtifactDefinition",
    "get_proposal_evidence_comparison_artifact",
    "list_proposal_evidence_comparison_artifacts",
)
```

Use this exact production code body:

```python
from __future__ import annotations

from dataclasses import dataclass

__all__ = (
    "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
    "REPORT_ONLY_FORBIDDEN_SURFACES",
    "ProposalEvidenceComparisonArtifactDefinition",
    "get_proposal_evidence_comparison_artifact",
    "list_proposal_evidence_comparison_artifacts",
)

REPORT_ONLY_FORBIDDEN_SURFACES = (
    "account_action",
    "account_automation",
    "api_client",
    "approval_workflow",
    "browser_automation",
    "credential_workflow",
    "external_loader",
    "financial_advice",
    "jsonl_reader",
    "live_execution",
    "order_placement",
    "ranking",
    "recommendation",
    "scraping",
    "settlement_review",
    "trading",
    "websocket_client",
)


@dataclass(frozen=True)
class ProposalEvidenceComparisonArtifactDefinition:
    artifact_id: str
    level: str
    module_name: str
    report_class_name: str
    builder_name: str
    upstream_report_class_name: str
    report_only: bool
    supplied_input_only: bool
    append_only_log: bool
    forbidden_surfaces: tuple[str, ...] = REPORT_ONLY_FORBIDDEN_SURFACES

    def __post_init__(self) -> None:
        _require_identifier("artifact_id", self.artifact_id)
        _require_identifier("level", self.level)
        _require_module_name(self.module_name)
        _require_identifier("report_class_name", self.report_class_name)
        _require_identifier("builder_name", self.builder_name)
        _require_identifier("upstream_report_class_name", self.upstream_report_class_name)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.supplied_input_only is not True:
            raise ValueError("supplied_input_only must be True")
        if type(self.append_only_log) is not bool:
            raise ValueError("append_only_log must be a bool")
        if type(self.forbidden_surfaces) is not tuple:
            raise ValueError("forbidden_surfaces must be a tuple")
        if self.forbidden_surfaces != REPORT_ONLY_FORBIDDEN_SURFACES:
            raise ValueError("forbidden_surfaces must match report-only boundary set")


PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS = (
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison",
        report_class_name="TradeProposalEvidenceComparisonReport",
        builder_name="build_trade_proposal_evidence_comparison_report",
        upstream_report_class_name="PaperForecastEvidenceReport+TradeProposalReviewDossierBatchReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=False,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history",
        report_class_name="TradeProposalEvidenceComparisonHistoryReport",
        builder_name="build_trade_proposal_evidence_comparison_history_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend_batch",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend_batch_health",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
)


def list_proposal_evidence_comparison_artifacts() -> tuple[
    ProposalEvidenceComparisonArtifactDefinition,
    ...,
]:
    return PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS


def get_proposal_evidence_comparison_artifact(
    artifact_id: str,
) -> ProposalEvidenceComparisonArtifactDefinition:
    _require_identifier("artifact_id", artifact_id)
    for artifact in PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS:
        if artifact.artifact_id == artifact_id:
            return artifact
    raise ValueError("artifact_id must identify a known proposal evidence comparison artifact")


def _require_identifier(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_module_name(value: str) -> None:
    _require_identifier("module_name", value)
    if not value.startswith("polymarket_alpha_lab."):
        raise ValueError("module_name must be a polymarket_alpha_lab module")
```

## Task 1: Behavior Tests RED

**Files:**

- Create: `tests/test_proposal_evidence_comparison_artifact_registry.py`

- [ ] **Step 1: Write the failing behavior tests**

Create this exact test file:

```python
import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry import (
    PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS,
    REPORT_ONLY_FORBIDDEN_SURFACES,
    ProposalEvidenceComparisonArtifactDefinition,
    get_proposal_evidence_comparison_artifact,
    list_proposal_evidence_comparison_artifacts,
)


EXPECTED_ARTIFACT_IDS = (
    "proposal_evidence_comparison",
    "proposal_evidence_comparison_history",
    "proposal_evidence_comparison_history_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend",
    "proposal_evidence_comparison_history_batch_health_trend_batch",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
)


def test_registry_lists_known_proposal_evidence_comparison_artifacts_in_order():
    artifacts = list_proposal_evidence_comparison_artifacts()

    assert artifacts is PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS
    assert tuple(artifact.artifact_id for artifact in artifacts) == EXPECTED_ARTIFACT_IDS
    assert tuple(sorted(EXPECTED_ARTIFACT_IDS)) == EXPECTED_ARTIFACT_IDS


def test_registry_definitions_are_report_only_and_supplied_input_only():
    for artifact in PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS:
        assert artifact.level == "level_2"
        assert artifact.module_name.startswith("polymarket_alpha_lab.")
        assert artifact.report_class_name.startswith("TradeProposal")
        assert artifact.builder_name.startswith("build_trade_")
        assert artifact.upstream_report_class_name
        assert artifact.report_only is True
        assert artifact.supplied_input_only is True
        assert artifact.forbidden_surfaces == REPORT_ONLY_FORBIDDEN_SURFACES
        assert "api_client" in artifact.forbidden_surfaces
        assert "browser_automation" in artifact.forbidden_surfaces
        assert "financial_advice" in artifact.forbidden_surfaces
        assert "order_placement" in artifact.forbidden_surfaces


def test_registry_lookup_returns_exact_artifact_and_rejects_unknown_ids():
    artifact = get_proposal_evidence_comparison_artifact(
        "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
    )

    assert artifact.report_class_name == (
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport"
    )
    assert artifact.upstream_report_class_name == (
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport"
    )
    assert artifact.append_only_log is True

    with pytest.raises(ValueError, match="artifact_id"):
        get_proposal_evidence_comparison_artifact("")
    with pytest.raises(ValueError, match="known proposal evidence comparison artifact"):
        get_proposal_evidence_comparison_artifact("unknown")


def test_registry_dataclass_rejects_mutated_or_loader_like_boundaries():
    base = PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS[0]

    with pytest.raises(ValueError, match="module_name"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name="requests",
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=True,
            supplied_input_only=True,
            append_only_log=base.append_only_log,
        )
    with pytest.raises(ValueError, match="report_only"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name=base.module_name,
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=False,
            supplied_input_only=True,
            append_only_log=base.append_only_log,
        )
    with pytest.raises(ValueError, match="supplied_input_only"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name=base.module_name,
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=True,
            supplied_input_only=False,
            append_only_log=base.append_only_log,
        )
    with pytest.raises(ValueError, match="forbidden_surfaces"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name=base.module_name,
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=True,
            supplied_input_only=True,
            append_only_log=base.append_only_log,
            forbidden_surfaces=("api_client",),
        )
```

- [ ] **Step 2: Run behavior RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_artifact_registry.py -q
```

Expected: FAIL during collection because `polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry` does not exist.

## Task 2: Scope And Export Tests RED

**Files:**

- Create: `tests/test_proposal_evidence_comparison_artifact_registry_scope.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Create scope tests**

Create this exact scope test file:

```python
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "proposal_evidence_comparison_artifact_registry.py"
)
README_PATH = REPO_ROOT / "README.md"

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "ccxt",
    "httpx",
    "playwright",
    "polymarket",
    "py_clob_client",
    "requests",
    "selenium",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_PUBLIC_NAME_FRAGMENTS = (
    "account",
    "api_client",
    "approve",
    "authenticate",
    "browser",
    "cancel_order",
    "credential",
    "execute",
    "fetch",
    "financial_advice",
    "glob",
    "http",
    "load",
    "place_order",
    "rank",
    "read",
    "recommend",
    "replay",
    "scrape",
    "session",
    "sign",
    "submit",
    "trade",
    "wallet",
    "websocket",
)


def normalize_identifier(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def test_registry_module_uses_only_dataclasses_imports():
    tree = parse_module()
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

    for node in imports:
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".")[0] for alias in node.names}
            assert not (roots & FORBIDDEN_IMPORT_ROOTS)
        else:
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS
            assert node.module in {"__future__", "dataclasses"}


def test_registry_public_api_does_not_expose_loader_or_execution_names():
    tree = parse_module()
    assigned_exports: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
            and isinstance(node.value, ast.Tuple)
        ):
            for item in node.value.elts:
                assert isinstance(item, ast.Constant)
                assert isinstance(item.value, str)
                assigned_exports.add(item.value)

    assert assigned_exports == {
        "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
        "REPORT_ONLY_FORBIDDEN_SURFACES",
        "ProposalEvidenceComparisonArtifactDefinition",
        "get_proposal_evidence_comparison_artifact",
        "list_proposal_evidence_comparison_artifacts",
    }
    normalized_exports = {normalize_identifier(name) for name in assigned_exports}
    for forbidden in FORBIDDEN_PUBLIC_NAME_FRAGMENTS:
        normalized_forbidden = normalize_identifier(forbidden)
        assert all(normalized_forbidden not in name for name in normalized_exports)


def test_registry_readme_section_keeps_report_only_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    start = readme.index("## Proposal Evidence Comparison Artifact Registry")
    end = readme.index("## Automation Roadmap", start)
    normalized = normalize_identifier(readme[start:end])

    for fragment in (
        "staticreportonlyregistry",
        "stringmetadataonly",
        "doesnotimportartifactimplementationmodules",
        "doesnotfetch",
        "doesnotreadjsonl",
        "doesnotload",
        "doesnotreplay",
        "doesnotscrape",
        "doesnotusebrowserautomation",
        "doesnotuseaccountautomation",
        "doesnotuseapiclients",
        "doesnotplaceorders",
        "doesnotrank",
        "doesnotrecommend",
        "doesnotprovidefinancialadvice",
    ):
        assert fragment in normalized, fragment
```

- [ ] **Step 2: Add package-root export tests**

Modify `tests/test_init.py` by importing these names from `polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry`:

```python
PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS
REPORT_ONLY_FORBIDDEN_SURFACES
ProposalEvidenceComparisonArtifactDefinition
get_proposal_evidence_comparison_artifact
list_proposal_evidence_comparison_artifacts
```

Add this exact test:

```python
def test_proposal_evidence_comparison_artifact_registry_public_api_exports():
    expected_exports = {
        "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
        "REPORT_ONLY_FORBIDDEN_SURFACES",
        "ProposalEvidenceComparisonArtifactDefinition",
        "get_proposal_evidence_comparison_artifact",
        "list_proposal_evidence_comparison_artifacts",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS is PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS
    assert lab.REPORT_ONLY_FORBIDDEN_SURFACES is REPORT_ONLY_FORBIDDEN_SURFACES
    assert (
        lab.ProposalEvidenceComparisonArtifactDefinition
        is ProposalEvidenceComparisonArtifactDefinition
    )
    assert (
        lab.get_proposal_evidence_comparison_artifact
        is get_proposal_evidence_comparison_artifact
    )
    assert (
        lab.list_proposal_evidence_comparison_artifacts
        is list_proposal_evidence_comparison_artifacts
    )
```

- [ ] **Step 3: Run scope/export RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_artifact_registry.py \
  tests/test_proposal_evidence_comparison_artifact_registry_scope.py \
  tests/test_init.py \
  -q
```

Expected before production/docs/exports: FAIL for missing production module and README registry section.

## Task 3: Production GREEN

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_artifact_registry.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`

- [ ] **Step 1: Add production module**

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_artifact_registry.py` with the exact production code from `Public API`.

- [ ] **Step 2: Add package-root exports**

Add this exact import block to `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry import (
    PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS,
    REPORT_ONLY_FORBIDDEN_SURFACES,
    ProposalEvidenceComparisonArtifactDefinition,
    get_proposal_evidence_comparison_artifact,
    list_proposal_evidence_comparison_artifacts,
)
```

Add these exact names to package `__all__`:

```python
"PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
"REPORT_ONLY_FORBIDDEN_SURFACES",
"ProposalEvidenceComparisonArtifactDefinition",
"get_proposal_evidence_comparison_artifact",
"list_proposal_evidence_comparison_artifacts",
```

- [ ] **Step 3: Add README section**

Add this exact section immediately before `## Automation Roadmap`:

```markdown
## Proposal Evidence Comparison Artifact Registry

The proposal evidence comparison artifact registry is a static report-only registry with string metadata only. It describes the existing proposal evidence comparison artifact chain, builder names, report class names, upstream report class names, append-only-log availability, and report-only forbidden surfaces. It does not import artifact implementation modules and does not create reports.

The registry does not fetch, does not read JSONL, does not load, does not replay, does not scrape, does not use browser automation, does not use account automation, does not use API clients, does not place orders, does not rank investments, does not recommend trades, and does not provide financial advice.

Use `list_proposal_evidence_comparison_artifacts()` to inspect the static tuple and `get_proposal_evidence_comparison_artifact(artifact_id)` to look up one registry row by canonical artifact ID.
```

- [ ] **Step 4: Run behavior/scope GREEN**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_artifact_registry.py \
  tests/test_proposal_evidence_comparison_artifact_registry_scope.py \
  tests/test_init.py \
  -q
```

Expected: PASS.

## Task 4: Verification, Review, And Handoff

**Files:**

- Modify: `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-artifact-registry.md`

- [ ] **Step 1: Run final verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
```

Expected:

- pytest exits 0 and prints a final summary line such as `N passed in X.XXs`; record that exact line in the handoff
- `git diff --check` exits 0
- CodeGraph status says index is up to date
- secret scan exits 1 with no matches

- [ ] **Step 2: Run read-only Claude implementation review**

Run:

```bash
claude -p \
  --model claude-opus-4-8 \
  --effort max \
  --permission-mode dontAsk \
  --disallowed-tools "Edit,Write" \
  --append-system-prompt "You are performing a read-only code review. Do not edit files. Do not create files. Report findings only. Categorize findings as Critical, Important, or Minor. Critical or Important findings block commit." \
  "Review the proposal evidence comparison artifact registry implementation in /home/ubuntu/polymarket-alpha-lab against docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-artifact-registry.md. Check implementation, tests, exports, README, scope boundaries, and report-only/static-metadata constraints. Required output: Critical findings count, Important findings count, Minor findings count, Verdict: Proceed or Block."
```

Accepted state is Critical findings 0 and Important findings 0.

- [ ] **Step 3: Append handoff summary**

Append this heading and fill it with real evidence:

```markdown
## Implementation Handoff

- Changed files:
- Verification:
- Claude implementation review:
- Known residual risks:
- Next recommended node:
```

- [ ] **Step 4: Commit and push**

Run:

```bash
git add \
  README.md \
  src/polymarket_alpha_lab/proposal_evidence_comparison_artifact_registry.py \
  src/polymarket_alpha_lab/__init__.py \
  tests/test_proposal_evidence_comparison_artifact_registry.py \
  tests/test_proposal_evidence_comparison_artifact_registry_scope.py \
  tests/test_init.py \
  docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-artifact-registry.md
git commit -m "feat: add proposal evidence comparison artifact registry"
git push
```

Expected: commit and push succeed.

## Implementation Handoff

- Changed files:
  - `README.md`
  - `src/polymarket_alpha_lab/proposal_evidence_comparison_artifact_registry.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_evidence_comparison_artifact_registry.py`
  - `tests/test_proposal_evidence_comparison_artifact_registry_scope.py`
  - `tests/test_init.py`
  - Existing package-root scope allowlist tests:
    - `tests/test_analytics_scope.py`
    - `tests/test_analytics_history_scope.py`
    - `tests/test_forecast_evidence_scope.py`
    - `tests/test_manual_review_queue_scope.py`
    - `tests/test_proposal_packet_scope.py`
    - `tests/test_proposal_review_scope.py`
    - `tests/test_proposal_review_summary_scope.py`
    - `tests/test_proposal_review_quality_scope.py`
    - `tests/test_proposal_review_diagnostics_scope.py`
    - `tests/test_proposal_review_coverage_scope.py`
    - `tests/test_proposal_review_dossier_scope.py`
    - `tests/test_proposal_review_dossier_batch_scope.py`
    - `tests/test_proposal_evidence_comparison_scope.py`
    - `tests/test_proposal_evidence_comparison_history_scope.py`
    - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
- Implementation notes:
  - Added the static report-only registry as string metadata only.
  - The registry module imports only `__future__` and `dataclasses`; it does not import artifact implementation modules.
  - The helper functions are intentionally defined before `PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS` so dataclass validation is available during tuple construction.
  - Added package-root exports for the five planned registry public names.
  - Added the README section before `## Automation Roadmap`.
  - Full-suite verification showed existing package-root scope tests each had local Level 2 export allowlists; those allowlists were updated with only the four `proposal`-prefixed registry names. `REPORT_ONLY_FORBIDDEN_SURFACES` was not added to those allowlists because it does not contain `proposal` or `tradeproposal` and remains covered by the existing forbidden-fragment fallthrough checks.
- Verification:
  - Initial RED behavior/export run failed during collection with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry'`.
  - Focused GREEN after implementation: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_artifact_registry.py tests/test_proposal_evidence_comparison_artifact_registry_scope.py tests/test_init.py -q` -> `31 passed in 0.40s`.
  - Strengthened registry-focused tests after review feedback: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_artifact_registry.py tests/test_proposal_evidence_comparison_artifact_registry_scope.py tests/test_init.py::test_proposal_evidence_comparison_artifact_registry_public_api_exports -q` -> `10 passed in 0.37s`.
  - Proposal evidence comparison suite after allowlist fixes: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison*.py tests/test_init.py -q` -> `211 passed in 3.58s`.
  - Full suite: `.venv/bin/python -m pytest -q` -> `801 passed in 8.05s`.
  - `git diff --check` exited 0.
  - Secret scan over `README.md docs src tests` exited 1 with no matches.
  - `codegraph sync && codegraph status .` reported the index is up to date.
- Claude implementation review:
  - Model: `claude-opus-4-8`
  - Effort: `max`
  - Mode: read-only review over supplied plan excerpts, tracked diff, and untracked file contents.
  - Critical 0, Important 0.
  - Minor notes were explanatory only: `REPORT_ONLY_FORBIDDEN_SURFACES` is deliberately exported but not part of proposal-prefixed allowlists; helper definitions are intentionally before tuple construction to avoid import-time `NameError`.
  - Verdict: Proceed.
- Known residual risks:
  - The registry is discovery metadata only; it intentionally has no loader, reader, replay, API client, browser/account automation, ranking, recommendation, order-placement, or financial-advice behavior.
  - Future package-root scope tests that introduce another independent Level 2 export allowlist must include the four proposal-prefixed registry names or centralize the allowlist to avoid repeated updates.
- Next recommended node:
  - Continue with the next report-only/static-metadata planning node only after preserving the same no-loader/no-reader/no-live-execution boundaries.
