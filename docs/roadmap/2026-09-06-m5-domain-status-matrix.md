# M5 Domain Status Matrix

Date: 2026-09-06
Stage: M5 Wave 1 of the [Project Delivery Plan](2026-09-05-project-delivery-plan.md)

Columns: source availability (registered no-auth public sources),
adapter, fixture coverage, end-to-end replay, operational smoke,
settlement data, and evidence families (current/required) for the
team's spot item. "Unsupported" is an explicit, intended state:
dispatch refuses undefined item sets (`team_item_requirements_not_defined`)
rather than fabricating bundles.

| Team | Sources | Adapter | Fixtures | E2E replay | Smoke | Settlement | Families |
| --- | --- | --- | --- | --- | --- | --- | --- |
| crypto_btc | kraken_btc_ticker + gamma + clob | yes (M3) | yes | yes | live green | M6 scope | 1/1 (corroboration deferred) |
| crypto_eth | kraken_eth_ticker + gamma + clob | yes (Wave 1) | yes (Wave 1) | yes (Wave 1) | live green (Wave 1) | M6 scope | 1/1 (corroboration deferred) |
| macro_rates | none viable | no | no | no | no | no | 0/0 |
| politics | none viable | no | no | no | no | no | 0/0 |
| equity_indices | none viable | no | no | no | no | no | 0/0 |
| commodities_gold | none viable | no | no | no | no | no | 0/0 |
| commodities_oil | none viable | no | no | no | no | no | 0/0 |
| sports_soccer | none viable | no | no | no | no | no | 0/0 |
| sports_basketball | none viable | no | no | no | no | no | 0/0 |
| sports_other | none viable | no | no | no | no | no | 0/0 |

## Source Acceptance Criteria

A source may be registered only when it is: public HTTPS GET without
authentication or keys, host-allowlisted, persistence-policy compatible,
and documented with an update cadence. Macro-rates candidates evaluated
and rejected so far: FRED and BLS (require API keys), scraped news
calendars (scraping is a separately reviewed fallback, not a default).
A later wave may register a qualifying rates source (for example a
public treasury yield feed) and re-run this matrix.

## Wave Discipline

Later waves follow the delivery plan: macro once a source qualifies,
then remaining domains in small reviewed batches; each wave gets its own
stage plan and the same review loop. Ten-team completion means ten
verified workflows, not ten registered builders.

## Settlement Export Protocol (added by M6)

Settled samples for evaluation are produced by joining persisted team
forecast rows to resolved outcomes (event identity, actual outcome,
settled timestamp) and exporting the JSON document consumed by
`settlement-evaluation --samples`. The first real evaluation becomes
possible only after markets from the 2026-09-05+ cycles settle; until
then every evaluation run reports `insufficient_sample` with the counts.
The cost-adjustment arm activates at settled N >= 30; the memory-benefit
arm activates when memory-gated handoffs have settled outcomes.
