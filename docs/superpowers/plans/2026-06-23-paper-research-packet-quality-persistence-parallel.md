# Paper Research Packet Quality Persistence Parallel Plan

Date: 2026-06-23

## Objective

Make paper research packet quality reports durable and observable without crossing
the Phase 1 boundary. The system should be able to build quality reports from
paper research packets, serialize and persist them, read quality history back,
and expose read-only CLI summaries for operator review.

Status: planned/in progress, not shipped. At plan start, main already has the
pure packet quality reducer plus the `paper-research-packet` and
`paper-research-packet-db-history` CLI commands. It does not yet have paper
research packet quality DB persistence, a quality history reducer/loader, or a
quality DB-history CLI command.

Current shipped packet operator commands:

- `polymarket-alpha-lab paper-research-packet --limit 100`
- `polymarket-alpha-lab paper-research-packet-db-history --limit 100`

Do not document or announce a `paper-research-packet-quality-db-history` command
as shipped until the persistence/history/CLI nodes land and pass review.

## Global Constraints

- Phase 1 remains paper-only, report-only, and readonly.
- No live trading, auth, wallet, private key, signing, order, relayer, exchange,
  or network mutation code.
- Domain math stays Decimal-only; do not introduce floats.
- New reducers are pure and must not import DB, env, psycopg, CLI, network, or
  client modules.
- DB helpers use DB-API boundaries and must not leak DSNs, table names, payloads,
  questions, or report hashes in user-facing errors.
- Subagents may implement code, but each node owns a disjoint write set.

## Parallel Nodes

1. Quality CLI node
   - Owns `src/polymarket_alpha_lab/cli.py`.
   - Adds a paper research packet quality summary command wired through injected
     runners and read-only DB loading.
   - Adds only CLI-specific tests.

2. Quality persistence node
   - Owns new quality DB row/store/config modules and their tests.
   - Adds a Supabase migration for `paper_research_packet_quality_reports`.
   - Does not edit CLI.

3. Quality history reducer node
   - Owns a new pure `paper_research_packet_quality_history.py` reducer and
     reducer/scope tests.
   - Does not edit CLI, store, env, or migration files.

4. Quality history load node
   - Owns a new tiny DB-API loader that loads persisted quality reports and
     reduces them into quality history.
   - Does not edit CLI until the CLI node is integrated.

5. Documentation node
   - Owns README/docs updates only.
   - Describes shipped paper-only packet generation/history commands and marks
     quality persistence/history as planned or in progress until code nodes
     define and land final public names.

## Verification Gates

- Focused tests per node.
- Full `./.venv/bin/python -m pytest -q`.
- `./.venv/bin/python -m compileall -q src tests`.
- `git diff --check`.
- OpenCode review with `zhipuai-coding-plan/glm-5.2`, variant `max`, no fast
  mode.
- `codegraph sync`.
- Push `main` after a clean review.
