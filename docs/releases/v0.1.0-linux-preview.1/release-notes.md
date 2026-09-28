# v0.1.0-linux-preview.1 — Linux research/paper engineering preview

Repository Lordakee/polymarket-alpha-lab, tag v0.1.0-linux-preview.1. Built
from source commit 06e49d0fde20c837cda80f0b3e61fcb1f3806ca2 (tree
027996b04f44c0340deb8e73fcf9825ad061c657) on the designated host
(Ubuntu 26.04.1 x86_64, kernel 7.0.0-34-generic, Python 3.12.14, PostgreSQL
18.6 Ubuntu build 18.6-0ubuntu0.26.04.1; prefix provenance, required system
libraries and binary digests in tuple-provenance.txt inside
acceptance-evidence.zip).

The exact ZIP accepted by the native distribution test on that host is
published unchanged: archive_sha256 a0c9a014e4efdfa5215843af84120831457e27e9e319045b5e365e660aea6ce9,
40813935 bytes, 2944 bundle entries (2943 source files plus the embedded
engine archive), target linux-x86_64, PG 18.6. The kit EMBEDS the PostgreSQL
18.6 engine as database/postgres-runtime.zip (engine digest
d7c09eebab2a27f33f677452447e28cc928c42b88467af73295b939d0ac418e4, per the
published PROJECT-BUNDLE.json), built from the qualified runtime prefix whose
provenance is in tuple-provenance.txt. A database cluster, Python, a venv and
the offline dependency collection are not bundled (uv.lock is bundled; the
kit installs offline via uv sync --locked --offline; migrations catalog 68).
The inner PROJECT-BUNDLE.json is published as a byte-for-byte copy.

Acceptance recorded in acceptance-evidence.zip (first failure preserved
separately): native distribution 1 passed (1066.10s, attempt 2 after a host
IO-timing first failure); verify_local --full PASS with 40015 passed / 80
skipped / 0 failed; L5 synthetic containment 122 passed with 4 expected
platform skips (evidence produced at revision 6cfd5ec4, content-identical to
the L5 files merged at C modulo CR-at-EOL line endings on 5 files); contained
PG 2/2 stop/restart/replay and driver-loss PASS. Fixed source-version pair
proof: OLD v0.1.0-native-preview.1 (2b20002c, catalog 63) to candidate C
(catalog 68), 3 passed on the same qualified PG18 prefix — a fixed
source-version pair plus one released candidate kit. The switch test uses
verified Git archives and synthetic integrity fixtures; it does not prove a
pair of published kits.

CI at C (all attempt 1, head_sha C, success):
Offline verification https://github.com/Lordakee/polymarket-alpha-lab/actions/runs/36403256602 (job: offline);
Native project PostgreSQL https://github.com/Lordakee/polymarket-alpha-lab/actions/runs/36406813585 (jobs: linux-native-storage, linux-native-dispatch, linux-native-research, linux-native gate; the Windows matrix and its summary gate are retired as frozen history);
Native project distribution https://github.com/Lordakee/polymarket-alpha-lab/actions/runs/36406819949 (job: linux-kit).

Limits: this is an engineering prerelease. Official Claude Linux artifact
provenance and byte measurement remain open; the six official probe scenarios
remain 0/6; G2 real-run authorization, G3-G5 real evidence and activation
remain open (activation_authorized=false, real provider execution false).
This is not V1 completion, not statistical strategy validation, and not
execution authorization. Windows remains retired and frozen.

Verify downloads against SHA256SUMS; trust measurements only from this
release record.
