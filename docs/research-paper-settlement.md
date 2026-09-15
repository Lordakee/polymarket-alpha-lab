# Settling retained research-paper evidence (WP-05)

`ProjectResearchSession.evaluate_settled_paper_research()` connects the retained
simulation inputs/results from PR #37 to the existing crypto settlement
confirmation workflow from PR #33. It is a read-only application API, not another
forecast scorer, trading engine, portfolio ledger, file writer or provider client.
It returns one entry for every original research attempt, not only profitable or
settled simulations. The original probability diagnostics remain unchanged.

```python
with ProjectPostgres(Path(actual_project_root)).session() as research:
    result = research.evaluate_settled_paper_research()
    # Optional historical cutoff and original evaluator's bounds/settings:
    historical = research.evaluate_settled_paper_research(
        generated_at=explicit_aware_cutoff, max_records=1000,
    )
```

This is developer integration; it does not configure a model or add a standalone
console mode. The documentation is in the source repository; the new Python
module is included by existing kit source selection. Do not overlay an old kit,
change its manifest or point at a user database without separate authorization.
No migration is added: all 67 existing migrations and their manifest are unchanged.

## What the number means

For a previously accepted full-size simulated BUY of YES or NO:

`settled_pnl_lower_bound = binary_payout - saved_assumed_total_cost_upper_bound`

The winning side pays one binary payout unit per hypothetical share; the losing
side pays zero. The quantity, selected side, entry-price upper bound, fee bound
and five non-fee assumptions are the original retained inputs/decision, NOT
reselected after seeing settlement. The original simulator replays only to verify
integrity of the retained row; changed engine output fails closed.

Example: 5 hypothetical YES shares at a worst consumed ask of 0.4, a quadratic
fee coefficient of 0.02 and extra cost of 0.001 per share give saved cost bound
`5 * (0.4 + 0.0048 + 0.001) = 2.029`. A YES settlement yields a bound of `2.971`;
a NO settlement yields `-2.029`. These are computations within the saved model,
not a verified fill price, exchange invoice or account balance. NO is a BUY of
the NO token, not a short sale. Values are in `binary_payout_units`; no collateral
conversion, interest accrual, mark-to-market, reinvestment or currency FX is inferred.

The result explicitly retains `actual_account_pnl=null`, `costs_are_assumptions=true`,
`tariff_verified=false`, `paper_trades_created=0`, `portfolio_return_computed=false`
and `strategy_validation_performed=false`. The lower bound is valid only WITHIN
the stored cost/fill assumptions. It is not a lower bound on real exchange P&L.
No newly invented real fee rate, source authentication or trading authorization.

## Evidence required before assigning settlement money

The original evaluator must select the forecast and show a visible recorded
outcome. The immutable simulation must have been accepted before its original
cutoff. A resolution-review reference is loaded and matched byte-for-byte to its
linked outcome. A crypto-workflow attestation then loads its immutable anchor
forecast and original candidate and replays the EXISTING confirmation builder.
The complete canonical rebuilt submission must equal the retained submission,
including original rules, source descriptor, observation minute, hashes and proof.

The confirmed condition, market, cutoff and complete original rules must also
match the simulated forecast. An outcome originally reviewed against another
model's forecast may apply to the same condition with identical rules; it does
not allow cross-condition substitution or source rewriting. Human assertions
remain assertions: this program does not fetch or authenticate the source.

Legacy direct outcomes and ordinary manual reviews remain visible but receive
`crypto_confirmation_required`, not a numeric P&L or an inferred default NO.
A claimed linked review that is missing/corrupt, or a claimed crypto attestation
with inconsistent provenance, aborts the read rather than returning a partial
apparently complete aggregate. Unknown or disputed outcomes remain unresolved
under the original confirmation rules. No outcome is created or corrected here.

## One snapshot, bounded reads and denominators

Original complete-visible-history queries, paper rows, anchor forecasts,
candidates and confirmed reviews all use ONE managed repeatable-read, read-only
transaction. The original evaluator's query body is extracted unchanged into a
cursor helper; its ordinary public entrypoint retains the same validation,
queries, selection and transaction semantics. The new entry always enables its
existing incomplete-claim check; there is no weaker fallback or automatic retry.

The historical cutoff is applied to every new source as well as the original
history. A future cutoff is rejected. This describes rows visible in the current
transaction with recorded timestamps through the cutoff; it is NOT a reconstruction
of historical COMMIT/WAL visibility. Late commits with earlier recorded timestamps
can change a later historical rerun. Within a single call, such late commits cannot
mix new paper evidence into an older history snapshot. Database admission still
does not certify COMMIT acknowledgement before the original forecast cutoff.

The original 1..10,000-record and 32-MiB history limits remain. Additional paper,
original-request and review payload reads have a conservative aggregate 32-MiB
budget, checked BEFORE fetching bodies; repeated references can consume that budget
more than once. Resolution payloads also retain the existing per-item limit.
Oversized or inconsistent inputs abort, never truncate or return partial totals.
This is a finite-size bound, not a guaranteed total runtime deadline.

Each attempt retains its original selection reason and, when available, the
saved simulation status/reason and input/result hashes. The settlement status is
one of missing paper evidence, research not selected, paper not selected, outcome
pending, crypto confirmation required or settled simulation. Failed, later,
rejected, missing and pending rows never acquire a zero P&L merely to fill a cell.
An empty settled subset has NULL sums; zero is reserved for an actual computed zero.

Totals are only within team/model/protocol and the exact cost/risk assumption
binding (including configuration and assumption identifier). Reusing a label with
different costs does not pool them. Groups describe SAVED scenario subsets; the
original history and global attempt/status counts still expose missing scenarios.
All sums are explicitly `settled_subset_only=true`, not total portfolio performance,
independent-event sample size or statistical promotion evidence. No pooled score,
win-rate claim or annualized return is produced.

## Verification and remaining work

Unit and separate same-assistant adversarial tests cover four YES/NO win/loss
combinations, missing/rejected/unsettled denominators, incompatible-cost grouping,
provenance corruption, outcome-independent selection, payload limits and hostile
Decimal contexts. An actual wrong-valid-review substitution was reproduced and
fixed without weakening its assertion. The initial pass also had one invalid
terms-test fixture; it was corrected on the unchanged implementation before the
remaining real failure was reproduced. Both initial results are retained.

The opt-in native test uses a disposable private PostgreSQL with synthetic BTC/ETH
forecasts, actually waits for the specified UTC minute close, saves original
crypto confirmations and checks all four payout cases. It also holds a real
paper INSERT uncommitted across the history read, commits it before the paper
query, and verifies no cross-snapshot mixing. Restart, historical cutoff, original
row preservation, denied incomplete-history evaluation and no read-path business
writes are checked. No user DB, real provider, source request, credentials or
exchange action is used. Final fixed-head CI evidence is recorded in the PR.

WP-05 remains PARTIAL and G5 remains open. Real approved forecasts, reviewed real
input/fee evidence, full operator acceptance and strategy-validation thresholds
are not replaced by synthetic engineering tests or assumed-cost settlement sums.
D1-D3 and the existing WP-06 first-run reliability issue remain unchanged.

Primary semantics checked 2026-09-15:
https://docs.polymarket.com/concepts/resolution
https://docs.polymarket.com/trading/fees
https://www.postgresql.org/docs/17/transaction-iso.html
