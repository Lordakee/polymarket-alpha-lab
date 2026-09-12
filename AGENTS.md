# Project Instructions

## Current owner override: native project-private PostgreSQL (2026-09-12)

The owner explicitly replaced the Supabase requirement: use only native
PostgreSQL owned and managed by this project, without Docker, Supabase services,
or automatic adoption of an external/shared database. Runtime binaries live in
`runtime/postgres`; the private cluster and OS-protected configuration/credentials
live in `.local/postgres`. These native-engine/configuration files are not a
file-backed substitute for business records: project evidence remains PostgreSQL
only. Do not commit runtime binaries, database clusters or generated credentials.

Use `project_postgres` for new managed application sessions. Preserve the single
audited `validate_local_postgres_dsn` implementation; `local_postgres_dsn` is its
canonical import and the historical `supabase_local_dsn` name remains compatible.
The `supabase/migrations` pathname and old serialized labels are historical API
compatibility, not a requirement to install Supabase. Do not silently move, alter
or replay existing migrations. Native migrations have a checked-in hash manifest
and a transactional PostgreSQL ledger. Existing external/local installations are
not automatically imported, migrated, modified or deleted.

The owner has also authorized self-review, commits and merges without external
Claude Code review or CodeGraph synchronization; do not claim those checks ran.
The remaining research, credential, persistence and Phase 1 safety boundaries
continue to apply. Earlier conflicting Supabase/review wording below is retained
as historical context and is superseded by this section.

## Scope

This repository is for Polymarket market research, data engineering, strategy validation, paper trading, risk analysis, and staged automation toward user-authorized execution.

Current phase boundary: do not add live trading, account authentication, private-key handling, or automated order placement in Phase 1. Treat this as a staged delivery boundary, not a permanent project non-goal.

Future execution work must be introduced through explicit roadmap documentation, validation gates, risk controls, audit logging, and user authorization for credential handling. Do not read, print, or move stored secrets unless the task is specifically about secret-management infrastructure.

Do not perform compliance, legal, geographic-access, or regulatory analysis in this repository unless the user explicitly reopens that topic.

## Project Iron Rules

These rules are mandatory for every main agent, subagent, review, plan,
implementation, test, migration, runbook, and handoff in this repository unless
the user explicitly changes them in a later instruction.

1. **Database Persistence Iron Rule: persistence is local Supabase/Postgres
   only.** All database-related implementation and all project data persistence
   must use the local Supabase Postgres instance on this host. Treat local
   Supabase/Postgres as the only approved database persistence target and the
   only approved durable persistence target for project data. Do not introduce
   alternate database backends, hosted remote database assumptions, SQLite
   substitutes, file-backed database substitutes, JSONL/file journals as durable
   substitutes, SQLAlchemy, Redis, Mongo, or generic database abstraction
   layers. Configuration, stores, loaders, migrations, runbooks, fixtures, and
   tests must preserve the local Supabase/Postgres assumption. Any raw DSN from
   environment, config, CLI plumbing, test fixtures, or helper construction must
   be validated through `validate_local_postgres_dsn` before it can be used to
   open a connection, construct a psycopg wrapper, or reach any persistence
   adapter. Do not bypass this with ad hoc URL parsing, trusted-test shortcuts,
   hosted-DB allowlists, or alternate validator functions.
2. **Legacy file persistence is frozen.** Existing JSONL/file-backed journals,
   logs, archives, and local input loaders are legacy surfaces that predate the
   strict persistence rule. Do not expand them or add new file-backed
   persistence. When touching a legacy persistence surface, prefer migrating the
   write path to local Supabase/Postgres, or document a read-only compatibility
   boundary if immediate migration is out of scope.
3. **Phase 1 execution boundary is paper-only/report-only/readonly.** Phase 1
   must not add live trading, account authentication, private-key handling,
   wallet handling, hosted account reads, order signing, order submission,
   order cancellation, order replacement, or any exchange/order mutation path.
   New reducers, CLIs, stores, runbooks, migrations, and review plans must keep
   `paper_only=True`, `report_only=True`, and `readonly=True` where those flags
   exist, and must describe any DB persistence as local paper evidence storage
   rather than execution authorization.
4. **Reviews go directly to Claude Code.** All plan reviews, code reviews,
   stage audits, post-node external review gates, and handoff review gates must
   go directly to local Claude Code using model `claude-opus-5` with thinking
   level `max`. Do not route reviews to any other reviewer unless the user
   explicitly changes this rule. If local Claude Code is unavailable, treat the
   review gate as blocked; there is no fallback reviewer under the current
   rules. Review prompts must be read-only: reviewers may inspect plans, diffs,
   and files, but must not modify, create, or delete files. Claude Code review
   invocations must not be wrapped in a fixed elapsed-time timeout. Run long
   reviews in inspectable sessions and check them about every 30 seconds. At
   each check, observe process/session liveness and, when available, stream
   growth or event count, stderr or terminal events, CPU, and network activity.
   Elapsed time alone or a quiet interval is not evidence of a stall. While the
   review remains alive and no concrete terminal failure or stall is proven, do
   not interrupt, terminate, restart, duplicate, or replace it, and do not route
   around it; keep waiting and monitoring. Act only on an explicit result or
   error, confirmed process/session exit, concrete auth/permission/provider
   failure, proven stall, or a newer user instruction.
5. **Fast mode is forbidden.** Do not use fast mode for the main Codex agent,
   Codex subagents, Claude Code reviews, implementation workers, planning workers,
   or audit workers.
6. **Sustained parallel development is a project iron rule.** Whenever useful,
   independent, non-conflicting work exists, keep useful collaboration capacity
   occupied with implementation, testing, review, audit, documentation, or
   next-node preparation. The project does not define a fixed subagent-thread
   count: discover usable capacity dynamically from the current runtime and use
   only as much concurrency as is materially useful for the independent work
   available. Parallel work may span multiple modules and multiple development
   nodes, but write ownership must be split by non-overlapping files or isolated
   worktrees, and every node must retain its own focused tests, full-suite
   verification, CodeGraph sync, Claude Code review, commit, and push gates.
   Reclaim agents immediately when they complete, fail, or become blocked,
   inspect any work they left on disk, and redeploy the freed capacity to the
   next independent task. Do not impose a permanent lower coordinator-side
   concurrency ceiling or leave useful capacity idle merely for sequential
   convenience. Active concurrency may be lower when independent work is
   limited or when write conflicts, rate limits, memory pressure, shared test
   resources, or coordination overhead would materially reduce correctness;
   raise it again when doing so becomes useful.
7. **Codex subagent model is fixed.** Every Codex subagent, including nested
   subagents, implementation workers, planning workers, explorers, test workers,
   and audit workers, must be spawned with model `gpt-5.6-sol` and reasoning
   effort `max` explicitly specified. Do not omit either setting, inherit a
   different model or effort, or substitute another Codex model. Fast mode
   remains forbidden.

## CodeGraph

This repository is intended to be indexed by CodeGraph. If `.codegraph/` exists at the repository root, use CodeGraph before `rg`, `find`, or manual file reads when the goal is to understand or locate code:

```bash
codegraph explore "question or symbol names"
codegraph node <symbol-or-file>
```

Use `rg` only after CodeGraph is not enough or the task is plain text search across documentation.

## Data Source Priority

Use official Polymarket sources first:

1. Gamma API for market, event, tag, search, and metadata discovery.
2. CLOB API for order books, prices, spreads, midpoints, price history, and public market data.
3. Data API for public trades, positions, activity, holders, open interest, and leaderboards.
4. WebSocket market channel for real-time watchlist updates.
5. Officially documented third-party chain data only for historical backfill or verification.

Avoid using website scraping as a primary data path unless a needed field is unavailable through official APIs.

## Engineering Defaults

- Keep source files small and domain-focused.
- Preserve raw API payloads before normalization.
- Distinguish `null`, `0`, and `unknown` in data models.
- Use executable bid/ask and order book depth for research calculations, not only displayed midpoint.
- Keep all research outputs reproducible and timestamped.

## Agent Coordination Defaults

- Treat parallel agent utilization as a durable project operating constraint and
  apply Project Iron Rule 6 continuously.
- The project sets no fixed subagent concurrency count. Coordinators must
  discover current usable capacity dynamically and must not introduce a
  remembered or hard-coded thread-count ceiling. Nested subagent depth remains
  capped at **3**. Use fewer threads whenever the amount of independent work,
  rate limits, memory pressure, test-resource contention, write-scope overlap,
  or coordination cost makes lower active concurrency more effective.
- Keep as many subagents active as is useful when there are independent tasks that can run in parallel.
- Avoid assigning multiple subagents to edit the same files, the same batch of files, or the same tightly coupled responsibility at the same time.
- For write tasks, split ownership by non-overlapping files or modules before dispatching subagents, and keep each subagent inside its assigned write scope.
- Close completed subagents promptly, then dispatch fresh independent tasks when useful so parallel execution stays active without creating file conflicts.

## Model Defaults

- Every Codex subagent must explicitly use model `gpt-5.6-sol` with reasoning
  effort `max`, as required by Project Iron Rule 7. No other Codex subagent
  model or reasoning effort is permitted.
- Local Claude Code reviews for this project must use model `claude-opus-5`
  with reasoning effort `max` (CLI `--effort max`).
- Do not use fast mode for the main Codex agent, Codex subagents, Claude Code
  reviews, or local implementation/review gates.

## Review / Audit Defaults

- All plan reviews, code reviews, stage audits, and post-node external review gates go directly to local Claude Code.
- Use `claude-opus-5` with reasoning effort `max` (CLI `--effort max`) for every local Claude Code review.
- Do not route reviews to any other reviewer unless the user explicitly changes this rule again.
- If local Claude Code is unavailable, treat the review gate as blocked; there is no fallback reviewer under the current rules.
- Review prompts must be read-only: reviewers may inspect plans, diffs, and files, but must not modify, create, or delete files.
- Do not impose a fixed elapsed-time timeout on Claude Code reviews. Run long
  reviews in an inspectable session and check their health about every 30
  seconds without interrupting a review that is still working.
- Elapsed time alone or a quiet monitoring interval does not prove a stall. If
  the process/session remains alive and no concrete terminal failure or stall
  is proven, keep waiting and monitoring; do not terminate, restart, duplicate,
  replace, or route around the review.

## Codex Node Push Policy

The prior remote-pin workflow was a Sisyphus handoff constraint, not a standing Codex rule. When Codex is the active implementation agent, do not intentionally keep `origin/main` pinned behind completed local work.

Push a completed Codex node to GitHub after all of the following are true:

- The node has a focused local commit with a clean worktree.
- Focused tests for the changed surface pass.
- The full test suite passes.
- `git diff --check` is clean.
- Python compile verification passes.
- CodeGraph is synced when `.codegraph/` exists.
- A secret scan finds no leaked credentials or tokens in tracked content.
- The configured post-node external review gate passes through Claude Code (`claude-opus-5`, reasoning effort `max`, CLI `--effort max`).
- If local Claude Code is unavailable, treat the review gate as blocked; there is no fallback reviewer under the current rules.

Do not push half-finished work, failing tests, unreviewed code, or work that still has unresolved review findings.

After a completed Codex node is verified, committed, reviewed, and pushed to
GitHub, continue to the next suitable task by default. Do not pause solely
because a GitHub push completed. Stop only when user confirmation is needed, a
blocker prevents meaningful progress, a phase or risk boundary would change, or
the user explicitly asks to stop or pause.

## OMO / Sisyphus Session Workflow (historical)

This section is retained only as historical context for the 2026-06-16 Sisyphus handoff. It is not an active Codex rule and does not override the current Claude Code review default above.

### Authority and handoff

- The user had handed the project to Sisyphus for that historical window. Codex has since resumed from the latest main commit.
- Work directly in `/home/ubuntu/polymarket-alpha-lab` on the `main` branch. Do not use worktrees or copies.
- A rollback tag `codex-handoff-20260616` is placed at the last codex commit (currently `8182787 feat: add project screening v0`). Keep commits granular and independently revertable so codex can selectively roll back.

### Git strategy

- Commit locally on `main` as work progresses.
- Do NOT push to `origin/main` unless the user explicitly asks. Keep the remote pinned at the codex handoff commit so codex can resume from a clean remote.
- Push only when the user explicitly authorizes it.

### Historical model configuration

The old OMO/Sisyphus model and review-gate configuration has been superseded.
Do not use it as current project guidance. Current plan and code review goes to
Claude Code with model `claude-opus-5` and reasoning effort `max` (CLI
`--effort max`).

Two gates were mandatory during that historical workflow:

1. **Pre-stage plan gate** — Before any implementation work begins in a stage:
   - Sisyphus drafts the stage plan (goal, scope, files, approach, risks, tests).
   - Submit the plan to the configured reviewer.
   - Implementation may start ONLY after the reviewer approves. If the reviewer requests changes, revise the plan and re-review until approved.

2. **Post-stage code gate** — After a stage's implementation is complete and tests pass:
   - Submit the stage plan plus the resulting code/diffs to the configured reviewer.
   - The next stage may begin ONLY after the reviewer approves. If the reviewer requests changes, fix them and re-review until approved.

Stage boundary definition: a stage is any meaningful unit of work that has its own plan and deliverable (typically one Node in the existing plan/spec cadence). Do not collapse multiple stages into one review.

### Workflow summary per stage

1. Draft stage plan → pre-stage review → approval.
2. Execute with maximum parallel subagents (5-8 background).
3. Run tests, verify diagnostics clean on changed files.
4. Commit locally on main (granular commits).
5. Submit plan + code to post-stage review → approval.
6. Only then proceed to the next stage.
