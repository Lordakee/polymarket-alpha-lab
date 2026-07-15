# Source Acquisition Quality Policy

## Purpose

Define how research evidence is acquired, checked, cited, and retained before it can support Polymarket market screening, paper-trading analysis, or human review packets.

This policy is documentation-only. It does not authorize live trading, order creation, wallet access, authentication changes, Supabase schema changes, or automated execution.

## Source Priority

Use the least fragile and most directly attributable source that can answer the research claim.

1. Official APIs and published primary data.
2. Scrapling-based page capture for static or semi-structured public pages.
3. agent-reach research for broad discovery, cross-source triangulation, and source finding.
4. Browser collection for rendered pages, interactive artifacts, and visual verification.
5. Manual fallback when automation cannot capture the source safely or completely.

Website browsing and scraping are evidence acquisition tools, not trading signals by themselves. A claim should not pass quality review only because a single web page appears plausible.

## Acquisition Methods

### Official APIs

Use official APIs first when the source owner exposes stable, documented, or repeatable endpoints.

Good use cases:

- Polymarket Gamma API for events, markets, tags, series, search, comments, and metadata.
- Polymarket CLOB API for order books, prices, spreads, midpoints, last trade prices, and price history.
- Polymarket Data API for trades, activity, positions, holders, open interest, and leaderboards.
- Official government, exchange, sports league, weather, economic, blockchain, or issuer APIs when a market resolution depends on those domains.

Quality requirements:

- Store the endpoint family, request timestamp, response timestamp when available, normalized record id, and raw payload locator.
- Preserve null, zero, missing, and unknown values as distinct states.
- Prefer canonical ids over page titles or display names.
- Record API version, query parameters, pagination state, and rate-limit or partial-response warnings.
- Treat undocumented endpoints as browser or scraping evidence unless they are explicitly stable and reproducible.

Use an official API as primary evidence only when the endpoint is controlled by the relevant source family or by a recognized data publisher for that source family.

### Scrapling

Use Scrapling for public pages that are structurally parseable and do not require interactive browser state.

Good use cases:

- Static public pages with stable HTML structure.
- News articles, press releases, government pages, league pages, and issuer pages where the relevant text appears in initial or lightly rendered markup.
- Batch capture of many similar source pages for source freshness or content drift checks.
- Archiving page text, metadata, and selected structured fragments for later replay.

Quality requirements:

- Capture URL, final URL after redirects, HTTP status, retrieval timestamp, content hash, extracted text hash, title, canonical link, and selected metadata.
- Preserve enough raw or normalized content to reproduce the claim without revisiting the page.
- Flag paywalls, consent walls, truncated pages, bot-block pages, language redirects, and missing critical sections.
- Do not treat extracted snippets as complete when the page includes obvious dynamic, hidden, or pagination-dependent content.
- Re-run or escalate to browser collection when the extracted content conflicts with the rendered page.

Scrapling is preferred over manual copy-paste for repeatable page evidence, but it is not enough when JavaScript rendering, interactive tabs, downloads, or embedded widgets contain the decisive evidence.

### agent-reach

Use agent-reach for research discovery and triangulation, especially when the right source is unknown at the start.

Good use cases:

- Finding official source pages, source families, resolution authorities, and authoritative alternatives.
- Comparing multiple independent source families.
- Discovering conflicting or stale sources that require review.
- Building source candidate lists before targeted API, Scrapling, or browser capture.

Quality requirements:

- Record discovered source candidates separately from accepted evidence.
- Promote a discovered source to accepted evidence only after capturing it through an auditable method.
- Keep query text, search time, selected result ids or URLs, and rejection reasons for important skipped sources.
- Do not allow search-result snippets alone to satisfy capture completeness.
- Use agent-reach output to guide source selection, not to replace source capture.

agent-reach is a routing and discovery aid. Claims still need captured evidence with timestamps, source family labels, and citation digests.

### Browser Collection

Use browser collection when the decisive evidence requires rendered page state or visual confirmation.

Good use cases:

- JavaScript-rendered pages where Scrapling misses content.
- Interactive tables, filters, tabs, charts, widgets, or downloadable resources.
- Pages where screenshots are required to verify displayed values, UI state, or source identity.
- Authentication-free public pages that block non-browser clients but remain accessible in a normal browser.

Quality requirements:

- Capture URL, final URL, browser timestamp, viewport or relevant rendering state, screenshot or DOM artifact locator, and any selected text or table export.
- Record user-visible page state, including filters, tabs, selected date ranges, locale, timezone, and sorting.
- Prefer source-owned downloadable data over visual extraction when both are available.
- Treat screenshots as supporting evidence unless they are the only faithful capture of the public source.
- Escalate to manual fallback if the browser path requires credentials, private accounts, payment, or fragile user-specific state.

Browser collection is appropriate for verification and rendered capture, not for bypassing official APIs or creating hidden dependencies on personal browser sessions.

### Manual Fallback

Use manual fallback only when automated capture is incomplete, blocked, ambiguous, or not allowed by the source surface.

Good use cases:

- PDF, image, audio, or video evidence that requires human inspection.
- Sites with anti-automation controls where automated capture would be unreliable or inappropriate.
- Critical source pages that require manual confirmation of context, rule wording, or conflict handling.
- One-off resolution checks where the evidence is public but difficult to parse safely.

Quality requirements:

- Record who performed the review when available, review timestamp, public source locator, captured excerpt or summary, and reason automation was not sufficient.
- Include a manual-review reason code such as `manual_fallback_required`, `automation_incomplete`, `source_context_ambiguous`, or `rendered_capture_required`.
- Keep manual summaries short, factual, and traceable to public source locators.
- Do not store private credentials, account-only data, personal browser state, or unnecessary direct identifiers.
- Require a second source family or explicit reviewer note for high-impact claims when manual fallback is the only accepted evidence.

Manual fallback should reduce uncertainty; it should not become an unstructured path around source quality rules.

## Source Family Diversity

A source family is the controlling origin or authority behind the evidence, not merely a domain name.

Examples:

- Polymarket official APIs and Polymarket web pages are one source family for Polymarket market metadata.
- A government statistics agency, a third-party news article quoting that agency, and a data aggregator republishing the agency value are not three independent source families for that statistic.
- Two unrelated news organizations can be separate source families, but they are weaker than the primary agency or issuer when the claim concerns official results.
- Blockchain explorer mirrors may be separate interfaces but can share the same underlying chain data family.

Minimum standard:

- Important research claims need at least two accepted evidence items when feasible.
- Important research claims should include at least two source families when the claim is not directly answered by a primary official source.
- A single primary official source can be sufficient for simple factual claims if capture completeness and freshness pass, but the quality record should mark the claim as single-family.
- Claims with one source family, missing source family labels, or only secondary sources should be `watch` or `blocked` depending on impact.

Source family labels should be canonical, stable, and coarse enough to expose correlated evidence. Do not inflate diversity by splitting one publisher across subdomains, article pages, API endpoints, or copied syndication.

## Capture Completeness

Accepted evidence must be complete enough for another reviewer to reconstruct why the claim was accepted, rejected, or marked uncertain.

Required capture fields:

- `claim_id`
- `evidence_id`
- `source_id`
- `source_family`
- `source_type`
- `directness`
- `observed_at`
- acquisition method
- source locator
- final URL or canonical endpoint
- content or payload fingerprint
- citation digest
- reason codes

Completeness checks:

- The captured artifact includes the decisive text, value, table row, rule, timestamp, or downloadable payload used by the claim.
- The capture records retrieval time separately from source-published time.
- The capture distinguishes original source content from extracted or summarized text.
- The capture preserves pagination, filters, locale, timezone, and sorting when those affect the claim.
- The capture has a stable locator or local artifact reference that can be audited later.
- The capture records failed or partial acquisition attempts when they explain why evidence is missing or degraded.

Incomplete capture should use reason codes such as `capture_partial`, `source_locator_missing`, `source_family_missing`, `decisive_content_missing`, `rendered_state_missing`, or `payload_fingerprint_missing`.

## Freshness

Freshness measures whether evidence is current enough for the claim at the time of use.

Default guidance:

- Market microstructure, prices, order books, spreads, recent trades, and liquidity should be considered fresh only when collected close to the decision timestamp.
- Market metadata, rules, descriptions, resolution sources, and event structure can tolerate longer windows but must be refreshed after edits, closure, or resolution-state changes.
- Official outcome, settlement, and resolution evidence must be collected after the source has published the relevant result.
- News, sports, weather, politics, economic, and issuer claims should use freshness windows matched to the market's update cadence.

Record:

- `observed_at` for when the system or reviewer captured the evidence.
- `published_at` or source event time when available.
- `latest_observed_at` per claim.
- source age at report generation.
- freshness reason code when stale, missing, future-dated, or inconsistent.

Evidence is stale when its age exceeds the configured window for the claim type or when a newer conflicting source exists. Stale evidence can remain in the audit trail, but it should not satisfy current claim quality without a newer confirming capture.

## Citation Digest

Every accepted evidence item should have a citation digest that lets reviewers identify exactly what was cited without storing unnecessary sensitive or bulky content.

Digest principles:

- Build digests from canonicalized public citation fields, not private credentials or user-specific state.
- Include source locator, final URL or endpoint, observed timestamp, source-published timestamp when available, content or payload fingerprint, selected excerpt hash, source family, and acquisition method.
- Use stable serialization and a cryptographic hash so equivalent citation records produce the same digest.
- Store the digest with the evidence row and include it in review packets when space allows.
- Recompute the digest after recapture if the source content, locator, timestamp, or selected excerpt changes.

The digest is an audit pointer, not a substitute for the captured artifact. A digest without a source locator and artifact reference is not complete evidence.

## Conflict Evidence Handling

Conflicts are expected in fast-moving markets and should be preserved rather than hidden.

Conflict categories:

- Same source family publishes different values at different times.
- Primary source and secondary source disagree.
- Two primary authorities disagree or define the event differently.
- Page text conflicts with downloadable data.
- API payload conflicts with rendered website state.
- Current source conflicts with archived source.
- Market rules conflict with external event interpretation.

Handling rules:

- Keep all material conflicting evidence rows with `conflict_flag = true`.
- Prefer primary official sources over secondary summaries when the claim concerns official facts or resolution.
- Prefer source-published data files or APIs over rendered summaries when they are clearly the same authority and the data file is canonical.
- Prefer newer evidence only when the source family has authority to revise the value and the revision is captured.
- Do not delete older conflicting evidence; mark it superseded, stale, or contradicted through reason codes.
- Escalate to manual review when conflicts affect market eligibility, resolution interpretation, paper-trade thesis, or human proposal packets.
- Block claims when conflict resolution depends on private interpretation, unavailable sources, or unclear market rules.

Reason codes should distinguish `source_conflict`, `primary_secondary_conflict`, `api_render_conflict`, `stale_conflict`, `rule_ambiguity`, and `manual_conflict_review_required`.

## Local Supabase Recording Principles

Local Supabase records are for research evidence, auditability, and paper-only/report-only workflows. They must not create live trading authority or store unnecessary sensitive data.

Record only:

- normalized evidence metadata
- public source locators
- source family labels
- acquisition method and timestamps
- content, payload, or excerpt fingerprints
- local artifact references
- citation digests
- reason codes and quality status
- reviewer notes needed to explain manual fallback or conflict handling

Avoid recording:

- private credentials, wallet data, session cookies, tokens, or account-only source content
- unnecessary direct identifiers
- full page dumps when a redacted artifact reference and source summary are sufficient
- personal browser state or user-specific access details
- live order instructions or execution state in research evidence tables

Retention principles:

- Keep raw or unredacted artifacts local and access-limited.
- Prefer source summaries, fingerprints, and digests for longer retention.
- Deidentify or redact records when direct identifiers are not required for audit.
- Maintain append-only audit logs for material acquisition, recapture, conflict, and manual-review events.
- Preserve enough metadata to reproduce quality scores without preserving unnecessary content.
- Mark records as paper-only, report-only, and readonly where applicable.

Local Supabase should make research claims reproducible and reviewable. It should not become a source of truth that overrides the original public source.

## Quality Status

Use quality status consistently:

- `pass`: Evidence is fresh enough, complete enough, directly relevant, source-family labeled, digestable, and free of unresolved material conflicts.
- `watch`: Evidence is usable for observation but has limitations such as single-family support, secondary-only support, mild staleness, partial capture, or non-material conflicts.
- `blocked`: Evidence is missing, stale for the decision, materially incomplete, source-family ambiguous, conflict unresolved, manually asserted without adequate traceability, or dependent on private/unavailable access.

Research systems may compute weighted quality scores, but status should remain explainable from reason codes and reviewable evidence rows.

## Review Checklist

Before a claim can support research ranking, paper trading, or a human packet, confirm:

- The acquisition method is appropriate for the source surface.
- The source family labels reflect true independence.
- The capture includes the decisive content and required retrieval metadata.
- The evidence freshness window matches the claim type.
- The citation digest can be recomputed from retained metadata.
- Conflicting evidence is retained and explicitly handled.
- Local Supabase records contain enough audit metadata without sensitive or live-trading data.
- The final status and reason codes explain the quality decision.
