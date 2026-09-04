# Python 3.11 Scenario-Ladder f-string Syntax Remediation

**Status:** Draft implementation plan. No implementation, test, review, CodeGraph,
Git, or push gate described below has been run or passed merely by appearing in
this document.

## Goal

Restore parsing of the resolution-probability scenario-ladder report under the
project's minimum supported Python version (3.11) while preserving every
reason-code result and leaving the existing behavioral test unchanged.

## Approach

Make one grammar-only production edit inside `_row_reason_codes()`: replace the
five f-strings whose replacement fields span physical source lines with
parenthesized literal-string-plus-helper-call expressions. Keep the helper calls,
arguments, threshold semantics, set construction, deduplication, and sorted
return value exactly the same. Use an in-memory Python 3.11 compiler as the
minimum-version syntax proof; it performs no import and writes no `.pyc` file.

## Current Facts

- `pyproject.toml` declares `requires-python = ">=3.11"`.
- The only implementation surface for the eventual code patch is
  `src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py`,
  `_row_reason_codes()` at current lines 555–591.
- Current source lines 563, 568, 573, 578, and 583 begin f-string replacement
  fields whose `_floor_status(...)` or `_ceiling_status(...)` calls are split
  over physical lines. Python 3.11 rejects this pre-PEP-701 f-string grammar;
  Python 3.12 accepts it.
- The single-line f-strings at current lines 562 and 590 are not part of the
  defect and must remain unchanged.
- The paired test is
  `tests/test_research_strategy_resolution_probability_scenario_ladder_report.py`.
  Its `test_ladder_scores_pass_watch_and_block_probability_events()` assertions
  already cover the block, pass, and watch row reason-code outputs, including
  all five component-code families. It is a behavioral regression test, not an
  authorized edit target for this minimal repair.
- The currently resolved `pytest` wrapper uses Python 3.12. That wrapper is
  useful for the paired behavioral test and the full suite, but it **must never
  substitute for the Python 3.11 compiler gate**.
- A `.codegraph/` directory is present. Future implementation verification must
  sync/status CodeGraph after the code patch; this planning task does not run
  CodeGraph initialization or synchronization.
- The checkout already contains protected dirty/untracked work outside this
  remediation. Preserve it exactly: do not reset, clean, stash, reformat,
  stage, commit, or attribute any pre-existing path to this node.

## Explicit Scope

### In scope for the eventual implementation node

- Modify only
  `src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py`
  within `_row_reason_codes()` (current lines 555–591).
- Convert only the five invalid multiline f-string expressions at current lines
  563/568/573/578/583 into Python 3.11-valid string concatenations with the
  identical helper calls and arguments.
- Verify parsing with Python 3.11 and verify unchanged behavior with the
  existing paired pytest file.

### Out of scope

- Any change to `pyproject.toml`, the `>=3.11` minimum, dependencies, virtual
  environments, package installation, formatter configuration, or CI.
- Any modification to the paired test or any other test. The existing test is
  intentionally sufficient for the behavior-preservation portion of this
  grammar-only fix.
- Refactoring, extracting intermediate status variables, changing thresholds,
  reason-code names/order, set behavior, sorting, public API, imports, data
  models, flags, or report semantics.
- Node B, Node C, their plans, their source/tests/migrations, database work,
  network work, credentials, `.env` files, live/account/wallet/order surfaces,
  or unrelated dirty files.
- Commit or push during this plan-writing task.

## Ownership and Protected Boundaries

| Responsibility | Owner and exact boundary |
| --- | --- |
| Plan artifact | This task owns only `docs/superpowers/plans/2026-08-07-python311-scenario-ladder-syntax-remediation.md`. |
| Future implementation | One assigned implementation owner has exclusive write scope over only `src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py:555-591`. |
| Paired test | Read-only verification input: `tests/test_research_strategy_resolution_probability_scenario_ladder_report.py`; no ownership transfer and no edit. |
| Node B / Node C | Explicitly untouched; their current owners retain all files and responsibilities. |
| Plan/result review | Local Claude Code only, using `claude-opus-5` and `--effort max`, read-only, fast mode off. |
| Integration/Git | The coordinator stages only the approved source path after every required gate and only when protected pre-existing work remains untouched. |

## Mandatory Prerequisite: Direct Claude Code Plan-Review Gate

Before any source or test edit, submit **this exact plan** directly to local
Claude Code for a read-only plan review.

1. Use `claude-opus-5` with `--effort max`; fast mode is forbidden. Restrict the
   reviewer to read-only access (for example, `Read` only / plan permission),
   and never use a permission-bypass flag.
2. Run it in an inspectable local session. Do not impose a fixed elapsed-time
   timeout. Check its liveness and available stream/stderr/terminal progress at
   roughly 30-second intervals; a quiet interval alone is not a stall.
3. Give the reviewer this plan, the production function, and the paired test.
   Ask for an explicit `Proceed` or `Blocked` verdict plus Critical, Important,
   and Minor findings focused on: exact source-only ownership; Python 3.11
   parser compatibility; unchanged reason-code behavior; the Python 3.12 pytest
   wrapper caveat; Phase 1 boundaries; protected dirty work; and the proposed
   verification/commit gates.
4. Implementation may begin only after an explicit `Proceed` with all accepted
   findings incorporated into the plan. If Claude Code is unavailable, returns
   no explicit positive verdict, or finds an unresolved blocker, this node is
   blocked. There is no fallback reviewer.

## Execution Tasks (RED → GREEN)

### Task 1 — Preserve the baseline and establish the Python 3.11 RED parser proof

**Files:** Read only; do not edit code or tests.

1. Record the current Git status and the current patch scope before touching the
   owned source file. Do not use the output as permission to clean or alter
   another owner's work.

   ```bash
   git status --short
   git diff --no-ext-diff -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
   ```

2. Run this focused, in-memory Python 3.11 compiler command. It reads exactly
   the production source text and calls `compile()`; it does not import the
   module and writes no bytecode.

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3.11 -c 'from pathlib import Path; p = Path("src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py"); compile(p.read_text(encoding="utf-8"), str(p), "exec")'
   ```

   **Expected RED result:** non-zero exit with a `SyntaxError` at the first
   offending multiline f-string replacement field (currently beginning at line
   563). The parser normally stops at the first failure, so this command is not
   expected to report all five locations at once.

3. Treat this compiler failure as the RED proof. Do **not** add or modify a test
   merely to manufacture a RED pytest result: Python 3.11 cannot import the
   module until its parser accepts the source, and the existing paired test
   already specifies the observable reason-code behavior.

**Stop condition:** If the source unexpectedly compiles under Python 3.11 before
this edit, or fails for a different unrelated syntax problem, stop without
editing. Re-inspect the current source and revise/re-review the plan rather than
making a speculative change.

### Task 2 — Apply the one grammar-only source change

**Files:**

- Modify only:
  `src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py:555-591`
- Do not modify:
  `tests/test_research_strategy_resolution_probability_scenario_ladder_report.py`

Replace the five invalid expressions with the following equivalent shape. The
full `codes` set should retain the existing first f-string and the existing
`for code in item.reason_codes` / `tuple(sorted(codes))` logic unchanged:

```python
    codes = {
        f"resolution_probability_scenario_ladder_{status}",
        (
            "base_evidence_strength_"
            + _floor_status(
                item.base_evidence_strength,
                config.min_pass_base_evidence_strength,
                config.min_watch_base_evidence_strength,
            )
        ),
        (
            "cost_drag_"
            + _ceiling_status(
                item.cost_drag,
                config.max_pass_cost_drag,
                config.max_watch_cost_drag,
            )
        ),
        (
            "liquidity_reliability_"
            + _floor_status(
                item.liquidity_reliability,
                config.min_pass_liquidity_reliability,
                config.min_watch_liquidity_reliability,
            )
        ),
        (
            "resolution_ambiguity_"
            + _ceiling_status(
                item.resolution_ambiguity,
                config.max_pass_resolution_ambiguity,
                config.max_watch_resolution_ambiguity,
            )
        ),
        (
            "specialist_confidence_"
            + _floor_status(
                item.specialist_confidence,
                config.min_pass_specialist_confidence,
                config.min_watch_specialist_confidence,
            )
        ),
    }
```

This is deliberately not a refactor: each helper invocation still receives the
same values in the same order and returns the same suffix string; concatenating
the unchanged prefix produces the same reason code. Do not extract local
variables, change the set, alter sort order, or touch the two valid f-strings.

Immediately inspect the owned-path diff. It must show only the five grammar
shape substitutions in this function.

```bash
git diff --check -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
git diff --no-ext-diff -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
```

### Task 3 — Run the focused Python 3.11 GREEN compiler loop

Re-run the exact no-write compiler from Task 1:

```bash
PYTHONDONTWRITEBYTECODE=1 python3.11 -c 'from pathlib import Path; p = Path("src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py"); compile(p.read_text(encoding="utf-8"), str(p), "exec")'
```

**Expected GREEN result:** exit code 0 and no compiler output.

If it still fails, make no broad repair. Limit diagnosis and any retry to the
five expressions in `_row_reason_codes()`; rerun the same focused compiler after
each grammar-only correction. Any need to alter another file, behavior, or the
Python minimum is a stop-and-replan condition.

### Task 4 — Verify behavior without confusing the Python versions

1. Run the existing paired test unchanged through the currently available
   Python 3.12 `pytest` wrapper:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest -q tests/test_research_strategy_resolution_probability_scenario_ladder_report.py
   ```

   **Expected result:** every test in that file passes, including the exact
   block/pass/watch reason-code assertions. This verifies the grammar-only edit
   preserved current behavior.

2. Label this result accurately: it is a **Python 3.12 behavioral pytest
   verification**. It is not evidence that Python 3.11 accepted the source;
   only the Python 3.11 in-memory compiler from Tasks 1 and 3 establishes that
   minimum-version syntax gate.

3. Check whether a Python 3.11 pytest invocation is available without installing
   anything or changing an environment:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3.11 -m pytest --version
   ```

   - If available, run the focused paired test under Python 3.11 as an
     additional runtime gate:

     ```bash
     PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest -q tests/test_research_strategy_resolution_probability_scenario_ladder_report.py
     ```

     **Expected result:** all tests in the file pass.

   - If the availability command fails because `pytest` cannot be imported by
     Python 3.11, **stop the Python 3.11 pytest branch immediately**. Record the
     command, exit status, and redacted failure classification as
     `NOT RUN — Python 3.11 pytest unavailable`. Do not install packages, create
     a virtual environment, edit dependency/configuration files, inspect
     credentials, or retry through bare `pytest`. The bare wrapper is Python
     3.12 and is not a substitute.

   - If Python 3.11 can run pytest but the focused test fails, treat it as a real
     remediation failure: stop, fix only an approved source-scope defect through
     the RED→GREEN loop, and re-run all affected gates. Do not use a Python 3.12
     pass to mask it.

**Commit/push disposition for unavailable Python 3.11 pytest:** the compiler
and Python 3.12 behavior results may be reported, but the node must not be
represented as Python-3.11-pytest-verified. Before a commit or push, an owner
must either provision an approved Python 3.11 pytest environment and rerun this
branch, or explicitly accept the documented runtime-test limitation. Without
that explicit disposition, commit/push is blocked.

## Repository-Wide Verification and Quality Gates

Run these only after the focused GREEN compiler succeeds. Preserve the baseline
worktree; do not hide, delete, or stage unrelated changes. Capture failures that
pre-date the source patch separately from regressions caused by this node.

1. **Repository-wide Python 3.11 syntax gate (no writes).** Compile every Python
   file under `src/` and `tests/` in memory rather than using a bytecode-producing
   compiler command:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3.11 -c 'from pathlib import Path; paths = sorted([p for root in (Path("src"), Path("tests")) for p in root.rglob("*.py")], key=str); [compile(p.read_text(encoding="utf-8"), str(p), "exec") for p in paths]; print(f"compiled {len(paths)} source/test files in memory with Python 3.11")'
   ```

   **Expected result:** exit code 0. This is the repository-wide minimum-version
   parser gate. Do not replace it with the Python 3.12 wrapper or claim it passed
   until the command actually succeeds.

2. **Full pytest gate through the currently available wrapper.** This is a
   separately labelled Python 3.12 full-suite check:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest -q
   ```

   **Expected result:** the suite passes, subject to explicit baseline comparison
   for protected pre-existing work. If Python 3.11 pytest is available, also run
   the equivalent full suite under it before finalizing:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest -q
   ```

   Apply the unavailable-Python-3.11-pytest stop condition above if that runtime
   cannot import pytest; do not install or substitute a different interpreter.

3. **Diff and narrow staged-scope gates.** Before staging, the working diff for
   the owned source path must be clean for whitespace and limited to the five
   substitutions. Do not use `git add -A`.

   ```bash
   git diff --check -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
   git diff --no-ext-diff -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
   ```

4. **Secret-safety scans without printing candidate values.** Scan only the
   intended tracked source file and then only staged added lines; do not scan or
   read `.env` files, credentials, or unrelated protected diffs.

   ```bash
   git grep -l -I -E '(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)' -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
   ```

   **Expected result:** no output and exit code 1. Treat exit code 0 as a
   blocker; it prints only a path, not a matched value. Treat any other nonzero
   status as a scan error rather than silently accepting it.

   After staging only the approved source file, run this added-line scan, which
   emits no candidate text:

   ```bash
   git diff --cached --no-ext-diff --unified=0 -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py | PYTHONDONTWRITEBYTECODE=1 python3.11 -c 'import re, sys; pattern = re.compile(r"ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----|(?i:api[_-]?key|secret|token|password)\s*=\s*[\"\x27][^\"\x27]{6,}"); hit = any(line.startswith("+") and not line.startswith("+++") and pattern.search(line) for line in sys.stdin); print("credential-shaped staged addition detected" if hit else "no credential-shaped staged additions"); raise SystemExit(1 if hit else 0)'
   ```

   **Expected result:** `no credential-shaped staged additions` and exit code 0.
   Any hit blocks review/commit until resolved within the approved source scope.

5. **CodeGraph gate.** Because `.codegraph/` exists, run the repository's
   post-change index/update checks after the code and test gates:

   ```bash
   codegraph sync
   codegraph status
   ```

   **Expected result:** the sync/status completes and reflects the current
   source. Do not run CodeGraph initialization. If `.codegraph/` no longer
   exists at execution time, do not recreate it for this node; record the
   changed prerequisite and obtain direction.

6. **Direct Claude Code result-review gate.** Provide the approved plan, exact
   owned-path diff, paired-test result, Python 3.11 focused/repository compiler
   outputs, Python 3.12 pytest results, any available Python 3.11 pytest
   results or explicit availability block, diff checks, secret-scan results, and
   CodeGraph output to local Claude Code. Use the same mandatory settings as the
   plan review: `claude-opus-5`, `--effort max`, read-only access, fast mode off,
   no elapsed-time timeout, and inspectable ~30-second health checks.

   Require an explicit `Proceed` or `Blocked` verdict and Critical/Important/
   Minor findings. A missing, unavailable, or non-positive result blocks the
   node; no alternate reviewer is permitted. Any accepted finding must be fixed
   only inside the approved source scope, after which every affected gate and
   the complete result review must be repeated.

## Commit and Push Gates (Future Execution Only)

These steps are deliberately last and are **not authorized or performed by this
plan-writing task**.

1. Confirm every preceding required gate actually passed or has an explicitly
   accepted Python 3.11 pytest-availability disposition. Confirm that no
   Critical/Important Claude finding remains unresolved.
2. Ensure the protected checkout is clean enough to make a focused commit
   without absorbing anyone else's work. If pre-existing dirty/untracked work
   remains, stop: do not stash, reset, clean, amend, or include it in this node.
3. Stage only the production source path, verify the index manifest and staged
   whitespace, then commit a focused change:

   ```bash
   git add -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
   STAGED_PATHS="$(git diff --cached --name-only)"
   test "$STAGED_PATHS" = "src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py"
   git diff --cached --check
   git diff --cached --no-ext-diff -- src/polymarket_alpha_lab/research_strategy_resolution_probability_scenario_ladder_report.py
   git commit -m "fix: restore Python 3.11 scenario ladder syntax"
   ```

   The plan artifact and every pre-existing dirty path stay unstaged unless a
   later explicit instruction separately authorizes them.

4. Only after the focused commit, clean-worktree requirement, full verification,
   CodeGraph gate, secret scans, and explicit Claude result approval are all
   satisfied, push the currently checked-out branch normally (never force):

   ```bash
   BRANCH="$(git branch --show-current)"
   test -n "$BRANCH"
   git push origin "$BRANCH"
   ```

   If any prerequisite is unavailable or fails, stop before commit/push and
   report the exact blocker. Do not bypass the gate with another interpreter,
   reviewer, dependency installation, credential access, or unrelated file edit.

## Final Acceptance Criteria

- Python 3.11's focused and repository-wide **in-memory** compiler gates pass
  after the five intended grammar substitutions.
- The paired test remains byte-for-byte unmodified and passes under the known
  Python 3.12 pytest wrapper; Python 3.11 pytest results are either passing or
  explicitly recorded under the stop condition above.
- No behavior, Python minimum, Node B/C surface, configuration, dependency, or
  unrelated dirty file changes.
- Diff, secret-safety, CodeGraph, and direct Claude Code result-review gates
  have actual recorded results before any commit/push decision.
- This plan itself is not evidence that any future gate has passed.
