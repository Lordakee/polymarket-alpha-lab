# Public discovery reliability and verified handoff downloads

## Local finding, not a model failure

The owner reported one BTC public-search IncompleteRead and an ETH prepared
preview on PR16. The BTC CLI was never invoked; ETH used genuine public inputs
without a model or database. The first failure remains a failure, not retroactively
converted to a clean run. This node adds no credentials, models, research writes,
automatic approval, database migration or scheduling.

`discover_crypto_research.py` replaces handoff-only discovery logic with a tested
operator entrypoint. It searches one fixed official Gamma page for each explicitly
selected team. Candidate filtering is only an engineering convenience, not an
investment recommendation, market-universe census or verified source relevance.

```powershell
# Configuration only; no network, model, database, or key access.
.\.venv\Scripts\python.exe scripts/discover_crypto_research.py --team crypto_btc --preview

# One BTC search attempt; only if candidates exist, one three-source preview.
.\.venv\Scripts\python.exe scripts/discover_crypto_research.py --team crypto_btc --preview --allow-public-fetch

# Explicitly allow up to three discovery attempts, retaining each failure.
.\.venv\Scripts\python.exe scripts/discover_crypto_research.py --team crypto_btc --preview --attempts 3 --allow-public-fetch
```

Use repeated `--team` to include ETH. Duplicate teams are deduplicated. Default
attempts is ONE; two/three is an explicit opt-in to retry only an incomplete body,
timeout, or connection reset/abort. A fresh GET replaces the entire failed response;
partial bytes are not concatenated, parsed, hashed as a snapshot or saved. Delays
are 0.25 and 0.75 seconds at most, not a total wall-clock timeout. Per-request
blocking timeouts still apply. HTTP errors (including redirects, 429, 503), TLS
failures, malformed JSON/content/framing, empty or oversized responses are not
retried. A persistent failure ends with the full fixed-code attempt trace.

Discovery attempts never retry the subsequent market/Coinbase/Kraken preview,
model, database transaction or research claim. Output retains `attempts`,
`request_attempts` and `recovered_after_failure`. A recovery is not a clean first
attempt. `public_gets_upper_bound` counts actual discovery attempts plus at most
three GETs per invoked preview; on a failed preview the exact internal GET count
is not asserted. The configured ceiling is at most twelve for both teams with
three discovery attempts and preview, or six for one team. No extra pages,
proxy discovery, cookies, account authentication, alternative hosts or redirects.

Successful complete raw search bytes stay in memory only; output exposes their
hash and candidate metadata. No full-history search persistence is claimed. One
page may have no eligible candidates; unknown/malformed envelopes are not silently
converted to an empty valid response. Candidates are canonical Yes/No price
questions with a scheduled end between two hours and one year away, sorted by end,
slug and condition. The actual preview re-fetches and validates the chosen market,
with an ephemeral 30-minute forecast cutoff and a nonexecuting model label.

`prepared` still only means input readiness. Coinbase/Kraken USD hourly evidence
is not equivalent to Binance USDT minute-candle settlement rules. Candidate
questions/rules are untrusted data, not commands; do not auto-approve terms hashes
or use them later as durable authorization. Real model selection, provider-data
permission and bounded spending authorization remain explicitly outstanding.

New previews also return `contract_scope` and `forecast_start_status`; whole-period
path/aggregate and unclassified contracts are blocked from NEW recent-hourly
research even when input preparation succeeded. Discovery ordering and HTTP
budgets are unchanged: this is not a new terminal-only search filter. See
[contract-shape checks](research-crypto-contract-scope.md) before approving a run.
A zero discovery/preview exit code is not a research authorization.

## Complete HTTP bodies before snapshots

The public Gamma market, Coinbase and Kraken readers now share a body-framing
check without changing their single-attempt API or fixed public error codes.
`HTTPResponse.read(amt)` may return fewer bytes than Content-Length without raising.
A valid-looking short JSON document therefore must still be rejected. The shared
check rejects duplicate/conflicting length/transfer headers, unsupported encodings,
oversize and empty bodies, and explicit short lengths. Real chunked truncation
raises without consuming its partial data. Close-delimited bodies have no declared
length and cannot provide an independent completeness guarantee.

The regression suite builds real stdlib HTTPResponse objects over in-memory HTTP
wire bytes, including valid JSON in a truncated Content-Length response and a
missing terminating chunk. It does not rely solely on manually raised exceptions.
Existing public-reader errors remain redacted and existing no-retry behavior remains.

## ASCII PowerShell 5.1 handoff loader

`scripts/download_handoff.ps1` is pure ASCII, avoiding Windows PowerShell 5.1's
ANSI interpretation of non-BOM script text. It does not modify global encoding or
execution policy. A pinned, reviewed loader can be reused for later handoffs.
Hash verification uses .NET SHA256 streams directly, not Get-FileHash cmdlet
autoloading. A PS5.1 subprocess may inherit a module search path from PS7; no
profile/module-path changes or module installation are needed for this hash step.
Files and streams are closed even on failure. The actual shell tests include
non-ASCII directory names and an unavailable Get-FileHash cmdlet.

```powershell
# Supply the actual immutable delivery commit and manifest SHA256 in the handoff.
.\scripts\download_handoff.ps1 -Repository 'wmqfl861/polymarket-alpha-lab' -Commit '<40-hex-commit>' -RelativeDirectory 'handoffs/<delivery-name>' -ExpectedManifestSha256 '<64-hex-sha256>' -OutputParent 'C:\Albert\acceptance-assets'
```

The GitHub manifest must use `github-handoff-v2` and list `files` with leaf `name`,
integer `bytes`, and `sha256`. Metadata may identify source commit/tree and allowed
local actions. The separately supplied manifest SHA256 pins the whole collection;
self-consistent internal hashes alone do not establish publisher trust.

The loader issues public GETs only to raw.githubusercontent.com at the specified
immutable commit/path, with no redirects/proxy/default credentials or retries. It
creates a unique `.downloading` directory under an existing chosen parent. Each
file lands as `.part`, then passes size/hash validation before rename. Only after
ALL listed files pass does it publish the final directory. A failure retains the
partial collection for diagnosis, returns a fixed stage code and nonzero exit,
and never executes a script, applies a patch, overwrites old data or cleans up.

The manifest is capped at 64 KiB, each file at 1 MiB, and a collection at twenty
files / 5 MiB. Windows reserved names, paths, duplicate names and staging-name
collisions are rejected before file downloads. This tool is for engineering
handoffs, not database backups, business-data journals or large runtime downloads.
A user explicitly starting a new download creates a new collection and preserves
old failures. Always inspect instructions after verification; the loader does not
turn downloaded text into authorization. Bootstrap the loader itself only from a
pinned GitHub revision with its separately supplied SHA256.

Native tests run its actual parser/filesystem behavior in Windows PowerShell 5.1
AND PowerShell 7, with synthetic transport bytes, including truncation, bad hashes,
path traversal and no-overwrite behavior. These do not claim the user's network
will be reliable. Review first failures separately from later successes.

## Distribution and compatibility

The clean kit now includes these explicitly reviewed public entrypoints and the
PR15/16 operator CLIs/runbooks. Previously only database startup/management scripts
were selected, so the new public tools were available only in a source checkout.
Old kits without the optional public tools remain verifiable; unrelated scripts,
user databases, passwords and fonts are not selected. The actual kit test executes
the packaged discovery CLI in disabled mode before any DB initialization.

No user database or global model configuration is changed by this node.

Primary references checked 2026-09-13:
- https://docs.python.org/3.12/library/http.client.html
- https://docs.polymarket.com/api-reference/search/search-markets-events-and-profiles
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding
