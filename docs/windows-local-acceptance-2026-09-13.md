# Windows acceptance follow-up, 2026-09-13

## Evidence boundary

The owner supplied a local-agent report for baseline
`4d63b0877ba8a3c4d9aaca26bd2110770cf1ef3c`. The report says Windows
10.0.26200.8894 x64, Python 3.12.10, uv 0.12.13 and PostgreSQL 17.11 were used.
These are **operator-reported results**; the repository-side continuation has
not read the local raw logs or accessed the machine. Do not replace the original
report or turn a successful isolated rerun into a clean first-pass result.

| Local selection | Reported result |
| --- | --- |
| Locked offline verification | 36,083 passed, 10 skipped, zero failures |
| First native selection | 326 passed, one failed, two skipped |
| Isolated rerun of failing lifecycle test | One passed |
| Fresh-kit startup twice | Ready twice; same instance; stopped after each check |

The two additional Windows offline skips explain the difference from hosted
Linux's 36,085 passed / eight skipped. Counts represent different selections and
must not be added. The report also describes separate successful disposable
capture/execution/aggregation checks; it does not provide a combined new total.

The first native failure occurred at `postgres.installing` -> `postgres` rename
with Windows error 5. Directory copying and all five native version probes had
completed. A subsequent isolated rerun succeeded. This supports investigating
intermittent contention, **not proving antivirus/indexer involvement or proving
the error harmless**. Permanent permission errors may use the same error code.

## Repository-side response

The import now retries only that final rename for Windows errors 5/32/33, with
at most seven attempts and 5.1 seconds total requested sleep. It retains the
lifecycle lease and checks directory identity, permissions, destination absence,
engine bytes, manifest and retained notices before every attempt and afterward.
Copying, native version probes, initialization, migrations and model calls are
not retried. Other errors stop immediately. Permanent denial returns a fixed
error code and leaves the owned incomplete staging intact; no cleanup/resume,
ACL change, antivirus exclusion or administrator elevation is introduced.

Offline regressions inject rename failures, file/identity changes and competing
destinations. A separate Windows test holds an actual directory handle without
`FILE_SHARE_DELETE`: one case releases it after the first denied rename; another
keeps it open until the bounded attempts are exhausted. This verifies OS-level
contention behavior; it is not a reproduction of the user's exact background
process or a guarantee against all possible local contention.

The current migration inventory is in `database/migrations.lock.json`; runbook
text no longer repeats a stale number. Historical migration bytes are unchanged.
Actual new revision, hosted results and local-test instructions are recorded in
the PR. No user database, original staging, credential store, uv installation or
antivirus configuration was accessed or changed by this continuation.

## Remaining local acceptance

After the repository fixes pass hosted verification, retest in fresh ordinary-
user-owned temporary directories using the already approved local PostgreSQL
prefix. Preserve the original acceptance and failed-install directories. Do not
copy initialized data, update old kits by overlay extraction, or delete staging
as a workaround. Reuse the accepted runtime assets, not another system service.
Record the first-run failure count and isolated reruns separately. The final
repo-side handoff will identify a concrete tested commit and exact commands.
