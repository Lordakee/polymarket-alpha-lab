# Project Handover — polymarket-alpha-lab

Date: 2026-09-07
Status at handover: P1 and P2a accepted and pushed; P2 in final closeout
(see "P2 Final Outcome" below, filled at handover time)
Branch: `codex/m0-baseline-persistence-acceptance`
Remote: `origin` -> `https://github.com/Lordakee/polymarket-alpha-lab.git`
Last accepted commit at handover start: `3598ea06` (P2a)

## What This Project Is

A paper-only, report-only, readonly Polymarket research pipeline: registered
public sources -> `SafeGETTransport` -> raw evidence persistence (local
PostgreSQL only) -> normalization -> BTC/ETH control-team forecasts ->
prospective frozen cohorts -> settlement evaluation with paired market
baseline and honest verdicts. No live trading, orders, wallets, accounts,
private keys or credential surfaces exist anywhere in the codebase.

## Completed Nodes (all reviewed, committed, pushed)

| Node | Commit | Content |
| --- | --- | --- |
| M0-M6 | history | baseline persistence, transport, adapters, cycles, M6 evaluator |
| P1 | `030491bc` | settlement sample collection pipeline |
| P2a | `3598ea06` | evaluation infrastructure: event lineage (keyed by forecast payload SHA-256), dual-cutoff correction-safe export, paired metrics, deterministic report command |
| P2 | (final push) | genuine prospective cohort `p2-crypto-control-20260907`: inventory (34 candidates, no outcome inspection), collection (7 ready forecasts with lineage), strict `p2-settlement-checkpoint-v1` frozen pre-outcome, hardened checkpoint-bound export, outcome import, report or constrained closure. See `docs/verification/p2/` and the stage plan. |

## P2 Final Outcome

**Constrained closure, 2026-09-07.** The prospective cohort was genuinely
frozen and audited (7 forecasts, 4 verified event groups; strict checkpoint
`a7111d05...` at `2026-09-07T00:22:35Z`, zero outcomes at freeze). 55
audited import attempts from 04:05Z to 19:28Z imported nothing: the
04:00Z market stayed `closed=false` for 15.5+ hours past end, and the four
16:00Z markets were unresolved 3.5 hours past end when the operating window
closed. N=0; no predictive verdict exists for `zero_impact_market_control`;
the frozen verdict state is `insufficient_sample` with all metrics
undefined. Evidence: `docs/verification/p2/` (inventory, collection,
checkpoint, 550-line attempt log, constrained-closure record, acceptance).
**Resume path:** once these markets finally resolve, the three commands in
`constrained-closure-20260907.md` produce the genuine report against the
same frozen checkpoint with no re-freeze.

## Frozen Governance That Must Survive

- Per-node loop: detailed plan -> Claude plan review -> disposition ->
  implement -> verify -> Claude hard review until PASS -> commit -> push.
- Verdicts are exact (`insufficient_sample` / `no_consistent_edge` /
  `indicative_edge` / `comparative_edge`); N=0 renders metrics undefined.
- The evaluated hypothesis is `zero_impact_market_control` (forecast equals
  contemporaneous market midpoint). No independent hypothesis exists yet.
- Prospective discipline: selection freezes before outcomes exist; lineage
  is never backdated; the control model is never tuned from outcomes.
- Full roadmap: `docs/roadmap/2026-09-07-project-completion-plan.md`.

## Remaining Work (P3-P6, not started)

- P3 independent evidence/quorum: PREP ALREADY DONE — see
  `docs/verification/p3-prep/source-scouting-20260907.md` (Coinbase
  Exchange and Bitstamp both verified keyless/real-time/USD/independent;
  CryptoCompare auth-required, Binance/OKX USDT-quoted, CoinGecko cached
  aggregate — all recorded) and `docs/verification/p3-prep/p3-plan-draft-20260907.md`
  (full stage-plan draft, NOT yet reviewed; its Claude review loop starts
  when P3 formally opens).
- P4 source-gated team waves (macro rates first), P5 trigger-gated cost and
  memory arms (need settled N>=30 / real handoff outcomes), P6 release
  closure package. Acceptance criteria are in the roadmap.

## How To Resume

1. Environment: Python 3.11 venv (`pip install -e .` plus `psycopg[binary]`;
   a disposable venv lived at `/tmp/pal-p2a-venv311` during development —
   recreate, it is disposable). `pytest-xdist` is optional (-n 8 gives a
   3.6x full-suite speedup; single-process full run is the baseline).
2. Database: local self-hosted Supabase in `/home/ubuntu/supabase-selfhost`,
   container `supabase-db`, database `postgres`. The host's published 5432
   is the Supavisor pooler and is NOT usable directly: use a disposable
   loopback forward (see `docs/supabase/local-supabase-operations.md` and
   `docs/roadmap/2026-09-05-m0-baseline-decisions.md`):
   `docker run --rm -d --name pal-<x>-db-forward --network supabase_default
   -p 127.0.0.1:55432:5432 alpine/socat tcp-listen:5432,fork,reuseaddr tcp:db:5432`
   DSNs come from env vars only (`POLYMARKET_ALPHA_LAB_*`), are local-only
   validated, and are never printed or committed. There is no `.env` file
   in the repo; the DB password is read from the container environment at
   runtime.
3. Daily operation: `docs/runbooks/research-cycle-operations.md` (census,
   collection, checkpoint, outcome import, export, report, DB lifecycle
   gates). CLI inventory baseline: 85 commands
   (`docs/verification/2026-09-05-m0-cli-command-baseline.txt`).
4. Open the next node by following the roadmap's loop; P3's draft plan and
   source evidence above are the entry point.

## Operational Notes From The P2 Closeout

- Polymarket UMA resolution can lag a market's end time by many hours (the
  2026-09-07T04:00Z ETH market stayed `closed=false` for 15.5+ hours past
  end). The importer is intentionally strict (closed=true AND final prices
  exactly 1/0); refusals are recorded results, not failures.
- Long waits used a detached (`setsid`) watcher script plus a 5-minute cron
  supervisor (`/tmp/p2_supervise.sh` during the session; both removed at
  shutdown). Interactive sessions may be restored and lose in-session
  background tasks; detached processes and cron survive — state recovery is
  a one-command check (watcher PID, settled-row count, report file).
- SUPERVISION LESSON: that supervisor's liveness check used
  `pgrep -f 'bash /tmp/p2_settle.sh'`, which substring-matched a stale
  monitor process whose command line merely mentioned the script — the
  supervisor then stopped relaunching for ~80 minutes (disclosed in the
  closure evidence). If reusing the pattern, match PIDs or a pidfile, not
  command-line substrings.
- Known minor leniencies recorded at closure (review findings LOW 3/4,
  accepted as documented, no behavior change):
  `evaluate-settlement-cohort` still accepts the legacy
  `p2a-settlement-checkpoint-v1` schema for P2a replay compatibility (the
  export gate requires the strict p2 schema, and every published report
  manifest embeds `checkpoint_sha256`), and the checkpoint validator
  coerces `tag_id` through `str()` and drops `event_slug` to null when
  `event_id` is null.
- Evidence artifacts are immutable and hash-chained (checkpoint binds
  inventory+collection byte hashes; report binds sample manifest and
  checkpoint hashes). Never regenerate them; corrections link
  `prior_export_id`.

## Shutdown Checklist (executed at handover)

- [x] Final P2 push (constrained closure) accepted — Claude hard review
      VERDICT: PASS (0 critical/high/medium; 5 LOW documentation findings,
      accepted and fixed/documented)
- [x] This handover + P3 prep docs included in the same push
- [x] cron supervisor entry removed (`crontab -l` verified)
- [x] detached watcher stopped, DB forward container removed
- [x] disposable venv and /tmp working files removed
- [x] `git status` clean and `origin` SHA == local SHA
