# Project Instructions

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
4. **Reviews go directly to local opencode.** All plan reviews, code reviews,
   stage audits, post-node external review gates, and handoff review gates must
   go directly to local opencode using model `zhipuai-coding-plan/glm-5.2` with
   variant/thinking level `max`. Do not route reviews to Claude Code or any
   other reviewer unless the user explicitly changes this rule. Review prompts
   must be read-only: reviewers may inspect plans, diffs, and files, but must
   not modify, create, or delete files.
5. **Fast mode is forbidden.** Do not use fast mode for the main Codex agent,
   Codex subagents, opencode reviews, implementation workers, planning workers,
   or audit workers.
6. **Codex subagents use GPT-5.5 xhigh.** Codex subagents dispatched for this
   project must use model `gpt-5.5` with reasoning effort `xhigh`. If the user
   informally writes `xhign`, treat it as the executable setting `xhigh`.

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

- Treat parallel agent utilization as a durable project operating constraint: while avoiding write conflicts, default to keeping multiple independent subagents active, reclaim completed subagents promptly, and redeploy capacity to the next independent research, review, or implementation task.
- The current Codex subagent concurrency cap for this project is **20 active subagent threads**, with a nested subagent depth cap of **3**. Use up to those caps only for independent, non-conflicting work; reduce concurrency when rate limits, memory pressure, test-resource contention, or write-scope overlap would reduce quality.
- Keep as many subagents active as is useful when there are independent tasks that can run in parallel.
- Avoid assigning multiple subagents to edit the same files, the same batch of files, or the same tightly coupled responsibility at the same time.
- For write tasks, split ownership by non-overlapping files or modules before dispatching subagents, and keep each subagent inside its assigned write scope.
- Close completed subagents promptly, then dispatch fresh independent tasks when useful so parallel execution stays active without creating file conflicts.

## Model Defaults

- Codex subagents dispatched for this project must use model `gpt-5.5` with reasoning effort `xhigh`.
- Local opencode reviews for this project must use model `zhipuai-coding-plan/glm-5.2` with variant/thinking level `max`.
- If the user informally writes `xhign` for the Codex subagent reasoning level, treat it as the executable setting `xhigh`.
- Do not use fast mode for the main Codex agent, Codex subagents, opencode
  reviews, or local implementation/review gates.

## Review / Audit Defaults

- All plan reviews, code reviews, stage audits, and post-node external review gates go directly to local opencode.
- Use `zhipuai-coding-plan/glm-5.2` with variant/thinking level `max` for every local opencode review.
- Do not route reviews to Claude Code unless the user explicitly changes this rule again.
- Review prompts must be read-only: reviewers may inspect plans, diffs, and files, but must not modify, create, or delete files.

## Codex Node Push Policy

The prior remote-pin workflow was an opencode/Sisyphus handoff constraint, not a standing Codex rule. When Codex is the active implementation agent, do not intentionally keep `origin/main` pinned behind completed local work.

Push a completed Codex node to GitHub after all of the following are true:

- The node has a focused local commit with a clean worktree.
- Focused tests for the changed surface pass.
- The full test suite passes.
- `git diff --check` is clean.
- Python compile verification passes.
- CodeGraph is synced when `.codegraph/` exists.
- A secret scan finds no leaked credentials or tokens in tracked content.
- The configured post-node external review gate passes through local opencode (`zhipuai-coding-plan/glm-5.2`, variant/thinking level `max`).

Do not push half-finished work, failing tests, unreviewed code, or work that still has unresolved review findings.

After a completed Codex node is verified, committed, reviewed, and pushed to
GitHub, continue to the next suitable task by default. Do not pause solely
because a GitHub push completed. Stop only when user confirmation is needed, a
blocker prevents meaningful progress, a phase or risk boundary would change, or
the user explicitly asks to stop or pause.

## OMO / Sisyphus Session Workflow (opencode only — codex ignores this section)

This section binds every opencode/Sisyphus session working on this repository. It is set by the user on 2026-06-16 and survives across sessions. Codex does not use this section; codex resume continues from the latest main commit.

### Authority and handoff

- The user has fully handed the project to opencode/Sisyphus. Codex is paused; it may resume later or run in parallel.
- Work directly in `/home/ubuntu/polymarket-alpha-lab` on the `main` branch. Do not use worktrees or copies.
- A rollback tag `codex-handoff-20260616` is placed at the last codex commit (currently `8182787 feat: add project screening v0`). Keep commits granular and independently revertable so codex can selectively roll back.

### Git strategy

- Commit locally on `main` as work progresses.
- Do NOT push to `origin/main` unless the user explicitly asks. Keep the remote pinned at the codex handoff commit so codex can resume from a clean remote.
- Push only when the user explicitly authorizes it.

### Model configuration (oh-my-openagent.json)

- All OMO agents and categories use `zhipuai-coding-plan/glm-5.2` with variant `max`.
- Subagent parallelism: maximize throughput. Default to firing 5-8 background subagents for independent work, reclaim finished subagents promptly, and redeploy capacity to the next independent task. Drop to 3-4 only if the API returns rate-limit errors. Never serialize independent tasks.

### OpenCode review gate (MANDATORY — never skip)

External review goes directly to local opencode for plan and code gates.

**Reviewer — local opencode** (`zhipuai-coding-plan/glm-5.2`, variant/thinking `max`, read-only prompt):

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max "<review prompt>"
```

(Append a HARD read-only constraint to the prompt: "DO NOT modify/create/delete ANY file; output ONLY verdict + findings." Run from the project root.)

Two gates are mandatory for every stage:

1. **Pre-stage plan gate** — Before any implementation work begins in a stage:
   - Sisyphus drafts the stage plan (goal, scope, files, approach, risks, tests).
   - Submit the plan to local opencode.
   - Implementation may start ONLY after the reviewer approves. If the reviewer requests changes, revise the plan and re-review until approved.

2. **Post-stage code gate** — After a stage's implementation is complete and tests pass:
   - Submit the stage plan plus the resulting code/diffs to local opencode.
   - The next stage may begin ONLY after the reviewer approves. If the reviewer requests changes, fix them and re-review until approved.

Stage boundary definition: a stage is any meaningful unit of work that has its own plan and deliverable (typically one Node in the existing plan/spec cadence, or a Sisyphus todowrite milestone). Do not collapse multiple stages into one review.

### Workflow summary per stage

1. Draft stage plan → pre-stage opencode review → approval.
2. Execute with maximum parallel subagents (5-8 background).
3. Run tests, verify diagnostics clean on changed files.
4. Commit locally on main (granular commits).
5. Submit plan + code to post-stage opencode review → approval.
6. Only then proceed to the next stage.
