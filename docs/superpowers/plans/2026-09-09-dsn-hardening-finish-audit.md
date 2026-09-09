# Priority 1 Plan: DSN-Hardening Finish Audit

**Status:** Plan only; implementation and verification pending.
**Base:** `8325785dc4fbfcf52dcd7ce62b6d3ecd832e4d36` (`8325785d`, Node 8), clean `main`.
**Lineage:** Program Nodes 1–8 landed and PASS-reviewed; 19 local commits ahead of `origin/main`, with push blocked/recorded.

## Goal And Governing Contract

Close DSN enforcement debt under AGENTS.md Iron Rule 1, roadmap
`docs/roadmap/2026-07-12-project-progress-roadmap.md:62–64`, and
`docs/quality/phase-1-development-node-quality-gates.md` §6.

Every raw DSN from environment, configuration, CLI plumbing, fixtures, or
helper construction must cross `validate_local_postgres_dsn` before connection,
psycopg-wrapper, or persistence-adapter construction. No alternate validator,
ad hoc parsing, trusted-fixture exemption, or hosted-database allowlist is permitted.

The audited production paths currently satisfy the rule. Already-hardened
surfaces comprise 54 `*_psycopg.py`, four `*_psycopg_read.py`, 56
`supabase_*config.py`, `autonomous_market_scorer_load.py`, and
`scripts/verify_local.py`.

This node is freeze-compliant: validation hardening is not decision behavior.
Preserve Phase 1 paper-only/report-only/readonly semantics and local
Supabase/Postgres-only persistence.

## Pinned Decision: Option B

Add static pins plus explicit validation at the remaining CLI and intermediary
boundaries. Option A avoids production edits but requires a continuing
interprocedural proof of CLI operand origins and intermediary contracts.
B makes the added boundaries locally reviewable through bounded mechanical edits.

The CLI has 35 direct connection sites across 32 functions. Two connection
operands already have relevant validation inside their containing functions;
the nine validator calls elsewhere in the file do not establish nine guarded
connection sites. Expect 33 additional CLI validation calls.

## Exact Production Scope

In `cli.py`, change only the 32 functions containing those connections and
required imports. Insert the shared validator for each unguarded operand on
its existing enabled/non-None usage path before connection setup. Preserve
existing effective guards. Use the originating configuration module’s exact
DSN environment constant, including distinct constants for multiple DSNs.
Keep connection operands unchanged.

Add five validations across the three intermediary modules:

- `candidate_decision_score_store.py`: in
  `candidate_decision_score_report_sink_from_config` before sink construction,
  and `_CandidateDecisionScoreReportSink.__call__` before `connection_factory`.
- `strategy_candidate_research_queue_store.py`: in
  `paper_strategy_candidate_research_queue_report_sink_from_config` before sink
  construction, and `_StrategyCandidateResearchQueueReportSink.__call__`
  before `_report_sink`.
- `check_outcomes_paper_trade_source.py`: in
  `load_check_outcomes_paper_trade_records`, inside the enabled branch before
  `db_loader`.

Use each module’s existing configuration DSN constant. Preserve disabled
returns, optional-input guards, callback arguments, SQL, transactions, cleanup,
redaction, and legacy read-only journal fallback.

## Static Enforcement Contract

Extend the existing per-function gate’s file set with the four production
files above. Retain existing adapter setup contracts; add scoped recognition
of CLI connections, both sink constructors, and injected intermediary calls.
Do not require redundant guards inside every already-protected adapter’s
internal `_connect`.

For new boundaries, match the shared-validator binding and the exact DSN
operand, including named variants and attributes such as `self.dsn`.
Validation must precede the protected operation on its execution path.
A different operand, unrelated branch, nested parameter, or subsequent
reassignment cannot supply the proof.

Add repository-wide production pins scanning all `src/**/*.py`:

- DSN environment reads occur only in `supabase_*config.py`. Recognize
  environment aliases, `.get`, subscripts, and DSN-key constants.
- Discover every matching configuration module, including future additions.
  Require its actual `__post_init__` to validate non-None `self.dsn` through
  the shared validator. An unused import or unrelated call is insufficient.
- Freeze a literal sorted 60-path connector allowlist: the base’s 58 adapter
  paths plus `autonomous_market_scorer_load.py` and `cli.py`. Check connector
  references and calls, including import aliases. Runtime globs must not
  automatically approve new connector files. Preserve the CLI’s 35 sites.
- Preserve CLI absence of environment reads and `--dsn` options.

Keep existing backend, durable-file, and smoke-test guards. Production
confinement does not exempt test fixtures from validation before actual
persistence; the existing opt-in smoke boundary remains validated and disabled
during this node. Synthetic source strings and fake connectors remain controls.
Pin the existing `_validate_local_dsn` shim’s delegation to the shared validator;
do not generalize that name into permission for alternate implementations.

## Exact Sorted Allowlist

The plan file is a separate planning artifact. Implementation may change only:

```text
src/polymarket_alpha_lab/candidate_decision_score_store.py
src/polymarket_alpha_lab/check_outcomes_paper_trade_source.py
src/polymarket_alpha_lab/cli.py
src/polymarket_alpha_lab/strategy_candidate_research_queue_store.py
tests/test_database_persistence_iron_rule.py
```

No §6 amendment is needed. Keep `docs/supabase/local-supabase-operations.md`,
AGENTS.md, policies, configuration modules, adapters, and verification scripts
untouched.

## Physical Line Ceilings

```text
candidate_decision_score_store.py                 <= 450
check_outcomes_paper_trade_source.py               <= 92
cli.py                                           <= 15,260
strategy_candidate_research_queue_store.py        <= 480
test_database_persistence_iron_rule.py             <= 1,600
aggregate production net growth from base         <= 352
```

## Red/Green Work

- [ ] **RED — Boundary coverage:** Add assertions exposing the currently
  unguarded CLI operands and five intermediary boundaries.
- [ ] **RED — Negative controls:** Follow the existing test’s lines 723–804:
  `ast.parse` synthetic source, a synthetic repository path, and explicit
  violation assertions. Cover missing/late/wrong-operand validation, alternate
  branches, reassignment, nested DSN parameters, injected callbacks, misplaced
  environment reads, missing config validation, and unapproved/aliased
  connectors. Prove each new pin rejects its own counterexample.
- [ ] **GREEN — Static pins:** Implement scanners in the allowlisted test file.
  Environment/config/connector inventories must show zero baseline violations;
  newly required local boundary checks must still fail before production edits.
- [ ] **GREEN — Mechanical guards:** Insert the validations and required imports.
  Require zero boundary violations.
- [ ] **GREEN — Controls and behavior:** Preserve positive controls for valid
  guards, optional branches, unrelated network calls, and synthetic strings.
  Add offline callback spies in the same test file proving invalid intermediary
  DSNs reach no callback and valid inputs preserve delegation. Do not write
  mutation fixtures to disk or open a database.

## Verification And Review

Run from the repository root with the existing `.venv`:

```powershell
@'
import subprocess, sys
from scripts.verify_local import build_environment
paths = [
    "tests/test_database_persistence_iron_rule.py",
    "tests/test_supabase_durable_only_scope.py",
    "tests/test_supabase_local_dsn.py",
    "tests/test_candidate_decision_score_store.py",
    "tests/test_strategy_candidate_research_queue_store.py",
    "tests/test_check_outcomes_paper_trade_source.py",
]
raise SystemExit(subprocess.call(
    [sys.executable, "-m", "pytest", "-q", *paths],
    env=build_environment(),
))
'@ | .\.venv\Scripts\python.exe -
.\.venv\Scripts\python.exe scripts/verify_local.py --full
git diff --check
git diff --check 8325785d
```

The full verifier supplies sanitized full pytest and compile verification.
Record secret/Phase 1 scans, allowlist/ceiling checks, and CodeGraph synchronization.
Never print environment values or raw DSNs.

Obtain the explicitly authorized read-only Codex review using `gpt-6-astra`
and `model_reasoning_effort=max`, ending `VERDICT: PASS`. Do not change model
configuration. Monitor long reviews about every 30 seconds without imposing
a fixed timeout or replacing a live reviewer.

## Stop Conditions And Completion Evidence

Stop dependent work for base drift, out-of-scope edits, ceiling breaches, DSN-flow
changes beyond validation insertion, a new DSN validator, alternate persistence,
secret exposure, decision/provider/cost changes, unexpected test failures, or
review non-PASS. Fix findings within scope; otherwise reopen the plan.

Unavailable verification, indexing, review, or push remains BLOCKED. Continue
independent authorized work, record the exact blocker, and withhold completion
or publication requiring that gate. Do not waive gates or alter policies.

Completion evidence must contain the full base/implementation hashes, sorted
changed paths, line counts, 35-site CLI inventory with operand-to-environment
mapping, five intermediary proofs, configuration/connector inventories, RED
counterexamples and GREEN results, focused/full/compile/diff/scan outcomes,
CodeGraph status, review verdict, clean committed worktree, and exact push
status. Preserve the recorded 19-commit backlog until its blocker is resolved.
Offline success does not claim real-database integration verification.
