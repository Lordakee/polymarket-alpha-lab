# Phase 1 Specialist Team Playbooks

This document defines the category-team playbooks for Phase 1 specialist
research. It is documentation-only guidance for paper-only, report-only, and
readonly research packets. It does not create a runtime surface, migration,
CLI option, Supabase table, execution path, recommendation path, or live
trading path.

Every playbook below preserves the Phase 1 boundary:

- Teams own research responsibility only.
- Central systems own routing, market metadata normalization, cost and fee
  research factors, paper-only diagnostics, outcome scoring, and reports.
- Long-term memory is local research context only and is gated by the
  `allow` / `throttle` / `block` memory policy.
- No team may authorize live trading, wallet use, authentication, private-key
  handling, account reads, order signing, order submission, order
  cancellation, order replacement, recommendations, investment ranking,
  position advice, or position sizing.

## Category Mapping

User-facing category labels map to existing Phase 1 team identifiers as
follows:

| Requested Category | Canonical Team ID | Primary Scope |
| --- | --- | --- |
| `politics` | `politics` | Politics and election-style event markets. |
| `macro` | `macro_rates` | Rates, central banks, inflation, macro releases, and policy-sensitive macro outcomes. |
| `bitcoin` | `crypto_btc` | Bitcoin and BTC-linked markets. |
| `equity_index` | `equity_indices` | Broad equity index and index-level market outcomes. |
| `gold` | `commodities_gold` | Gold and precious-metals markets. |
| `soccer` | `sports_soccer` | Soccer fixture, tournament, table, and player/team outcome markets. |
| `basketball` | `sports_basketball` | Basketball fixture, season, injury, roster, and player/team outcome markets. |

## Shared Packet Expectations

Each specialist team research packet should include:

- market question, selected outcome, resolution source, and rule text hash;
- source references, observed timestamps, source-family independence notes,
  and redacted public evidence summaries;
- forecast probability, confidence, evidence quality, data freshness score,
  resolution-risk notes, and invalidating conditions;
- memory policy used for the assignment and memory references considered;
- manual review blockers and operator review focus;
- `paper_only=true`, `report_only=true`, and `readonly=true` wherever those
  fields are represented.

forecast_probability always denotes canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES).

Calibration compares canonical `P(YES)` with an actual YES target of `1` and actual NO target of `0`, regardless of which paper-review side was selected.

Persisted `actual_outcome` uses the string enum `yes` or `no`; calibration maps `yes` to Decimal target `1` and `no` to Decimal target `0`; `selected_side` never changes that mapping.

Freshness SLAs below are maximum acceptable age for the decisive source at
packet assembly time. Older evidence can still be cited as background, but it
must be marked stale and must not be the decisive basis for a ready packet.

Manual review blockers are hard stops for automated paper handoff readiness:
the packet may still be produced, but it should route to operator review as
`watch` or `block` instead of being treated as research-ready.

Long-term memory writeback items are candidate observations for local
Supabase/Postgres report evidence only. They do not become validated lessons
until existing sample gates, diagnostics, and memory readiness rules allow
them.

## Politics Team

**Research focus**

- Resolution rule interpretation, including whether the market resolves on an
  official act, media call, certification, inauguration, resignation, or
  another defined trigger.
- Event timeline, jurisdiction, office, candidate/entity identity, eligibility
  constraints, and whether the market question uses local time, UTC, or a
  named deadline.
- Polling and forecast context only when relevant to the actual resolution
  condition; polling is not a substitute for rule evidence.
- Source authority hierarchy across election boards, courts, legislatures,
  official campaign filings, public office records, and major wire services.

**Core data sources**

- Official election administrators, court dockets, legislative calendars,
  government gazettes, public office records, and election certification
  notices.
- Reputable wire services and major local outlets for fast event confirmation
  when official sources lag.
- Polling aggregators, survey methodology notes, and turnout records as
  context, not final resolution evidence.
- Market rule text, resolution source text, archived market metadata, and
  prior local outcome rows for comparable event templates.

**Common misjudgments**

- Treating a media projection as final when the market requires certification
  or another formal act.
- Ignoring recount, litigation, replacement candidate, runoff, withdrawal, or
  appointment mechanics.
- Mixing national, state, district, and party-specific scopes with similar
  names.
- Overweighting late polls without checking sample quality, field dates, and
  whether undecided or third-party voters matter to the exact question.

**Freshness SLA**

- Official resolution or legal status evidence: 24 hours.
- Polling, forecast, or turnout evidence used for probability context: 72
  hours, or 24 hours inside the final week before the relevant event.
- Breaking news evidence used as decisive support: 2 hours, with source-family
  confirmation when official evidence is unavailable.

**Manual review blockers**

- Ambiguous or conflicting resolution rule, deadline, jurisdiction, candidate,
  or office identity.
- Decisive evidence comes only from a campaign, partisan source, social post,
  prediction market comment, or unattributed media report.
- Active litigation, recount, certification delay, eligibility dispute, death,
  withdrawal, replacement, or rule-change risk could alter resolution.
- Memory policy is `block`, or `throttle` with stale or conflicting similar
  cases.

**Long-term memory writeback**

- Rule interpretation patterns by jurisdiction, office, and market template.
- Source families that resolved quickly versus sources that created false
  positives.
- Cases where media-call, certification, recount, or court timing caused
  forecast or settlement error.
- Final blocker reason codes, invalidating conditions, and whether operator
  review changed the team conclusion.

## Macro Team

**Research focus**

- Official release calendar, release time, revision policy, seasonal
  adjustment status, and exact metric definition.
- Central-bank communication, policy meeting schedule, vote split, statement
  language, dot plot/projection changes, and market-implied policy path.
- Inflation, labor, GDP, retail sales, PMI, fiscal, rates, and treasury-market
  context relevant to the event template.
- Whether the market resolves on first print, final revision, range threshold,
  closing value, or named source publication.

**Core data sources**

- Official statistical agencies, central banks, treasury departments, finance
  ministries, and exchange/benchmark publishers.
- Economic release calendars from official agencies and reputable financial
  data vendors.
- Rates futures, OIS curves, treasury yields, inflation breakevens, and
  consensus survey summaries as context.
- Prior local forecast, evidence, outcome, and memory-readiness rows for the
  same data series or policy-event family.

**Common misjudgments**

- Confusing consensus expectations with the market's exact resolution metric.
- Missing first-print versus revised data treatment.
- Mixing seasonally adjusted and non-seasonally adjusted series.
- Applying a policy-meeting thesis to a market that resolves on a numerical
  data threshold or a specific publication timestamp.

**Freshness SLA**

- Official release, calendar, and policy-rate evidence: 24 hours, or 1 hour
  after a scheduled release if the market can resolve immediately.
- Market-implied rates, futures, yields, and consensus context: 4 hours on
  event day, otherwise 24 hours.
- Background macro regime evidence: 7 days unless it is the decisive driver.

**Manual review blockers**

- Source disagreement on the release timestamp, metric definition, revision
  treatment, threshold inclusivity, or publication authority.
- Scheduled release is delayed, corrected, revised, or published with an
  agency warning.
- Decisive data is behind an unverifiable secondary summary rather than the
  official release or accepted public source.
- Memory policy is `block`, or prior similar cases show unresolved conflicts
  for the same data series or rule template.

**Long-term memory writeback**

- Event-template distinctions for first print, revised print, threshold,
  meeting outcome, and closing-rate markets.
- Sources that were late, restated, contradicted, or misread by prior packets.
- Surprise direction, forecast error, source latency, and whether the market
  resolved before or after official publication.
- Macro regime tags, including inflation trend, rate-cut/hike cycle, risk-on
  or risk-off context, and liquidity stress when relevant.

## Bitcoin Team

**Research focus**

- BTC spot and derivative market context, major exchange pricing, market-hour
  behavior, liquidity, volatility, and event-window timing.
- ETF flows, exchange balances, funding/open interest, realized volatility,
  liquidation clusters, and macro/rates drivers when they plausibly affect the
  market question.
- Protocol, custody, regulatory, security, and major issuer/exchange news only
  when tied to the market's resolution horizon.
- Exact price source, threshold inclusivity, intraday high/low rule, closing
  timestamp, timezone, and index methodology.

**Core data sources**

- Named market resolution source and index provider for the specific BTC
  market.
- Major exchange spot prices, futures markets, funding/open-interest sources,
  ETF flow reports, on-chain analytics summaries, and volatility/liquidity
  dashboards.
- Official regulatory, ETF issuer, exchange-status, and protocol/security
  communications.
- Local BTC forecast, evidence, outcome, and memory rows grouped by threshold,
  horizon, volatility regime, and source family.

**Common misjudgments**

- Using one venue's spot price when the market resolves on a different index,
  exchange, candle, or oracle.
- Ignoring timezone, intraday high versus close, wick handling, and threshold
  equality rules.
- Treating social sentiment, liquidation maps, or on-chain metrics as
  standalone resolution evidence.
- Overfitting to recent volatility without checking liquidity, catalyst
  timing, and settlement window.

**Freshness SLA**

- BTC price, index, liquidity, funding, and open-interest evidence: 15 minutes
  for intraday or near-threshold markets; 1 hour for longer-horizon markets.
- ETF flow, regulatory, exchange, and protocol news: 4 hours when decisive,
  otherwise 24 hours.
- Background regime and memory context: 7 days unless used as a direct
  probability driver.

**Manual review blockers**

- Price is within the configured near-threshold band and the decisive source
  is stale, unavailable, or inconsistent across venues.
- Market rule does not clearly define exchange, index, candle, close,
  timezone, high/low, wick, or equality treatment.
- Exchange outage, depeg, oracle/index incident, major regulatory action, or
  chain/security incident affects the event window.
- Memory policy is `block`, or prior similar BTC cases conflict on threshold
  and source-method handling.

**Long-term memory writeback**

- Threshold, horizon, volatility-regime, and source-method tags for settled
  BTC markets.
- Cases where venue/index mismatch, candle timing, liquidity gaps, or
  near-threshold wicks caused errors.
- Source latency and reliability by index, exchange, ETF-flow, on-chain, and
  derivatives source family.
- Forecast deltas around catalyst windows, with invalidating conditions and
  operator review outcomes.

## Equity Index Team

**Research focus**

- Index definition, constituent exposure, market session, exchange holiday,
  settlement price, close/official value, and data-provider methodology.
- Macro, rates, earnings-calendar, sector breadth, volatility, and liquidity
  context relevant to index-level outcomes.
- Whether the market is tied to price level, percentage return, closing value,
  intraday touch, weekly/monthly performance, or relative index comparison.
- Corporate-action and index-rebalance effects only when they can affect the
  relevant index level or resolution source.

**Core data sources**

- Official index providers, exchange calendars, exchange-published market
  status notices, and named resolution sources.
- Major financial data vendors for index levels, futures, implied volatility,
  breadth, and sector performance context.
- Official macro and earnings calendars, central-bank schedules, and relevant
  company/index-provider notices.
- Local equity-index outcome and forecast rows by index, horizon, rule type,
  volatility regime, and event window.

**Common misjudgments**

- Confusing futures, ETF, CFD, indicative value, and official index close.
- Missing market holidays, half-days, early closes, trading halts, or timezone
  cutoffs.
- Applying single-stock news too heavily to broad index outcomes without
  checking weight and breadth.
- Ignoring dividend, total-return versus price-return, rebalance, or official
  settlement methodology differences.

**Freshness SLA**

- Official index level, close, holiday, halt, and market-status evidence: 15
  minutes for intraday markets; 1 hour after close for closing-value markets.
- Futures, volatility, breadth, sector, and macro context: 1 hour during market
  hours, otherwise 24 hours.
- Earnings or scheduled catalyst context: 24 hours, or 4 hours on event day.

**Manual review blockers**

- Rule ambiguity around official close, intraday touch, futures versus cash
  index, total return versus price return, or timezone.
- Exchange halt, index-provider issue, data-provider discrepancy, unscheduled
  holiday, or major market-structure event.
- Market is near threshold and decisive index evidence is stale or conflicts
  across accepted sources.
- Memory policy is `block`, or similar index cases show unresolved methodology
  conflicts.

**Long-term memory writeback**

- Index, horizon, rule type, session, and threshold-distance tags.
- Source discrepancies between official index provider, exchange, ETF,
  futures, and financial-data summaries.
- Cases where holidays, early closes, halts, close methodology, or threshold
  equality caused settlement or forecast error.
- Forecast performance by volatility regime, macro-catalyst window, and
  near-threshold state.

## Gold Team

**Research focus**

- Gold spot, futures, benchmark, ETF, and macro/rates context relevant to the
  exact market question.
- Resolution source, contract month, benchmark methodology, exchange session,
  fixing window, close, high/low, and timezone.
- Real yields, USD strength, inflation expectations, central-bank demand,
  geopolitical risk, and liquidity when they are tied to the event horizon.
- Distinction between gold spot, front-month futures, continuous futures, ETF
  price, and official benchmark/fixing values.

**Core data sources**

- Named resolution source, benchmark administrator, exchange contract
  specifications, exchange calendars, and settlement notices.
- Gold spot and futures data, real yields, dollar index, inflation breakevens,
  ETF flow summaries, and central-bank demand reports.
- Official macro release calendars and central-bank communication when rates
  or currency drivers are decisive.
- Local commodities-gold forecast, evidence, outcome, and memory rows by
  source method, horizon, threshold, and macro regime.

**Common misjudgments**

- Mixing spot, futures, ETF, LBMA/benchmark fixing, and settlement values.
- Ignoring contract rollover, session close, exchange holiday, and timezone
  treatment.
- Overweighting geopolitical headlines without checking USD/rates/liquidity
  offset.
- Treating macro context as resolution evidence when the market requires a
  named price source.

**Freshness SLA**

- Spot/futures/benchmark price evidence: 15 minutes for intraday or
  near-threshold markets; 1 hour for daily close or fixing markets.
- Rates, USD, volatility, and ETF-flow context: 4 hours when decisive,
  otherwise 24 hours.
- Central-bank demand and background regime evidence: 30 days unless directly
  referenced by the market question.

**Manual review blockers**

- Rule ambiguity around spot versus futures versus benchmark, contract month,
  close/fixing time, timezone, high/low, or equality handling.
- Exchange holiday, contract rollover, benchmark disruption, data-provider
  discrepancy, or threshold proximity with stale decisive evidence.
- Major unscheduled macro, geopolitical, central-bank, or exchange event
  changes the event window.
- Memory policy is `block`, or prior similar gold cases conflict on source
  method or settlement timing.

**Long-term memory writeback**

- Source-method, contract, fixing/close, threshold-distance, and macro-regime
  tags for settled gold markets.
- Cases where source confusion, contract rollover, exchange calendars, or
  benchmark timing drove errors.
- Source reliability and latency for benchmark, exchange, spot, ETF-flow, and
  macro/rates sources.
- Operator review outcomes for ambiguous commodity-price settlement cases.

## Soccer Team

**Research focus**

- Fixture identity, competition, home/away designation, kickoff time,
  timezone, venue, postponement rules, and market-specific event definition.
- Team news, injuries, suspensions, rotations, lineups, manager statements,
  fixture congestion, travel, weather, and tournament incentives.
- Market rule handling for regular time, extra time, penalties, aggregate
  score, replay, abandonment, voiding, and official result source.
- Table, promotion/relegation, qualification, award, and transfer markets only
  with the exact governing-body or competition rule.

**Core data sources**

- Official competition, club, league, federation, and governing-body sources.
- Official fixture calendars, match centers, lineup feeds, disciplinary
  reports, referee/VAR notices, and weather/venue notices.
- Reputable local beat reporters and major sports wires for fast team news
  when official lineups are not yet available.
- Local soccer forecast, evidence, outcome, and memory rows by competition,
  market type, rule type, and freshness regime.

**Common misjudgments**

- Treating all soccer markets as 90-minute outcomes when the rule includes or
  excludes extra time or penalties differently.
- Missing postponement, abandonment, venue change, neutral-site, or walkover
  rules.
- Overweighting rumored lineups before official team sheets.
- Ignoring fixture congestion, rotation incentives, aggregate-score state, or
  competition priority.

**Freshness SLA**

- Fixture status, kickoff, postponement, venue, and official lineup evidence:
  15 minutes once inside 2 hours before kickoff; 1 hour otherwise on match day.
- Injury, suspension, roster, and manager-news evidence: 24 hours, or 2 hours
  on match day before lineup release.
- Table, tournament, award, and transfer-rule evidence: 24 hours when
  decisive, otherwise 7 days.

**Manual review blockers**

- Rule ambiguity around regular time, extra time, penalties, aggregate score,
  abandonment, postponement, voiding, or official result source.
- Fixture status, venue, kickoff time, lineup, or player eligibility conflicts
  across accepted sources.
- Decisive evidence is only rumor, social-media aggregation, or stale
  pre-match reporting near kickoff.
- Memory policy is `block`, or similar competition/rule cases show unresolved
  settlement ambiguity.

**Long-term memory writeback**

- Competition, market type, rule timing, lineup timing, and fixture-status
  tags.
- Cases where extra time, penalties, postponement, lineup shocks, or official
  source hierarchy caused forecast or settlement error.
- Source reliability by competition, club, lineup feed, local reporter, and
  governing-body source family.
- Operator overrides and final blocker reason codes for match-state or
  competition-rule ambiguity.

## Basketball Team

**Research focus**

- League, fixture identity, tipoff time, timezone, venue, market scope, and
  whether the market resolves on game result, regular season, playoffs,
  tournament, player stat, award, or roster transaction.
- Injury reports, starting lineup/rotation expectations, minutes limits,
  rest/back-to-back context, travel, schedule density, matchup, and team
  incentive.
- Official result/stat source, overtime handling, postponed/suspended game
  treatment, player eligibility, stat corrections, and award voting timeline.
- Distinction between team markets, player props, season outcomes, playoff
  series, draft/transaction markets, and award markets.

**Core data sources**

- Official league, team, injury report, gamebook, box score, transaction, and
  award/voting sources.
- Reputable beat reporters and major sports wires for late injury, lineup, and
  minutes-limit context.
- Schedule, travel, rest, matchup, odds/market-implied context, and historical
  team/player performance summaries.
- Local basketball forecast, evidence, outcome, and memory rows by league,
  market type, player/team scope, rule type, and freshness regime.

**Common misjudgments**

- Missing late injury upgrades/downgrades, rest designations, minutes limits,
  or lineup changes.
- Treating unofficial stat feeds as final when the market depends on official
  box score or later stat correction.
- Ignoring overtime inclusion, suspended-game handling, playoff-series state,
  or eligibility minimums.
- Overweighting season averages without adjusting for role, opponent,
  injuries, pace, rest, and incentive changes.

**Freshness SLA**

- Injury, active/inactive, lineup, and minutes-limit evidence: 15 minutes once
  inside 2 hours before tipoff; 1 hour otherwise on game day.
- Official box score, gamebook, stat correction, transaction, and award
  evidence: 1 hour after publication when decisive.
- Season, roster, schedule, and background performance context: 24 hours, or 4
  hours on game day when decisive.

**Manual review blockers**

- Rule ambiguity around overtime, stat correction, player eligibility,
  postponed/suspended games, official stat source, or award voting window.
- Conflicting active/inactive, lineup, minutes-limit, transaction, or player
  identity evidence near tipoff or resolution.
- Decisive player/team news comes only from rumor, unverified social posts, or
  stale pre-game reporting.
- Memory policy is `block`, or similar basketball cases show unresolved
  conflict for injury, stat-source, or eligibility handling.

**Long-term memory writeback**

- League, market type, player/team scope, injury status, lineup timing, and
  rule-handling tags.
- Cases where late injury news, official stat corrections, overtime,
  eligibility, or suspended-game rules caused forecast or settlement error.
- Source reliability by official league feed, team report, beat reporter, box
  score, and transaction/award source family.
- Operator review outcomes, blocker reason codes, and invalidating conditions
  for late-news and stat-source ambiguity.
