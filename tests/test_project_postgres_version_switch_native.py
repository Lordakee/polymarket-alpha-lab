"""Real same-root OLD->CURRENT source switch, rollback and refusals (class 3).

Everything runs on ONE disposable synthetic 'Original Project' root inside a
fresh private proof directory. The OLD source and the executed candidate
source are verified binary `git archive` extractions of pinned commits; the
current locked Python environment supplies dependencies for both. No released
kit is re-accepted, no existing installation, user database, user credential
or public network is touched, and the test never fetches history or software.

Business equality means stored records/timestamps/claims/ledger rows, never
cluster-file byte equality: managed admission may legitimately change logs,
control state and WAL. Outcomes stay empty here, so equality only proves the
switch created no outcome rows, not settlement preservation.
"""
from hashlib import sha1, sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
from threading import Event
import time
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SOURCE = ROOT / 'src'


def _select_adjacent_worktree_source() -> None:
    """This file's own tree is CURRENT; never run an unrelated editable copy."""
    try:
        import polymarket_alpha_lab as package
    except ImportError:
        package = None
    if package is None or not Path(package.__file__).resolve().is_relative_to(_SOURCE.resolve()):
        for name in [name for name in sys.modules
                     if name == 'polymarket_alpha_lab' or name.startswith('polymarket_alpha_lab.')]:
            del sys.modules[name]
    sys.path.insert(0, str(_SOURCE))
    import polymarket_alpha_lab as selected
    assert Path(selected.__file__).resolve().is_relative_to(_SOURCE.resolve())


_select_adjacent_worktree_source()

from polymarket_alpha_lab.project_postgres import backup_format as fmt
from polymarket_alpha_lab.project_postgres import distribution, files, sql
from polymarket_alpha_lab.project_postgres.runtime import verify_runtime
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'
OLD_COMMIT = '2b20002c83ee33acb95fb2ca3de841f3e883ebbf'
OLD_TREE = 'd6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4'
OLD_CATALOG_ENTRIES = 63
OLD_CATALOG_FINGERPRINT = '3e8c813dcb7ce2389f11aa7aebba03819392f014e1208910c75d70bf709ccee5'
CANDIDATE_CATALOG_ENTRIES = 68
INSIDE_OLD_MIGRATION = '20260701000000_team_forecast_tables.sql'
NEW_MIGRATIONS = ('20260914000000_research_dispatch_batches.sql',
                  '20260915000000_research_dispatch_turns.sql',
                  '20260915010000_research_model_budgets.sql',
                  '20260915020000_research_paper_simulations.sql',
                  '20260919000000_research_uncapped_audit.sql')
FEATURE_TABLES = ('research_capture.dispatch_batches', 'research_capture.dispatch_turns',
                  'research_capture.model_budgets', 'research_capture.paper_simulations',
                  'research_capture.uncapped_authorizations')
RECORD_IDS = ('vs-record-1', 'vs-record-2', 'vs-record-3')
CONDITION_IDS = ('vs-condition-1', 'vs-condition-2', 'vs-condition-3')
WORKFLOW = ROOT / '.github/workflows/native-postgres.yml'


def _git(*args: str) -> bytes:
    """Sanitized read-only Git, following the distribution helper convention."""
    executable = shutil.which('git')
    if executable is None:
        raise AssertionError('git executable required for the pinned archives')
    env = {k: v for k, v in files.clean_environment().items() if not k.upper().startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT='0')
    result = subprocess.run([executable, '--literal-pathspecs', '-C', str(ROOT),
                             '-c', 'core.fsmonitor=false', *args], env=env,
                            stdin=subprocess.DEVNULL, capture_output=True,
                            timeout=180, check=False, shell=False)
    if result.returncode:
        raise AssertionError('git operation failed: ' + args[0])
    return result.stdout


def _extract_verified_archive(destination: Path, commit: str, expected_tree: str) -> dict[str, str]:
    """Verified `git archive --format=tar` extraction into a fresh directory.

    Commit-to-tree identity, the full member inventory against Git blobs, and
    traversal/absolute/link/duplicate/case-collision/type rejects happen BEFORE
    any byte is written. Only binary subprocess output is used, never shell or
    PowerShell text redirection.
    """
    tree = _git('rev-parse', '--verify', commit + '^{tree}').decode().strip()
    if not re.fullmatch('[0-9a-f]{40}', tree) or tree != expected_tree:
        raise AssertionError('pinned commit does not resolve to the required tree')
    inventory: dict[str, str] = {}
    for entry in _git('ls-tree', '-rlz', '--full-tree', commit).split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        name = raw_name.decode('utf-8')
        mode, kind, blob, size = metadata.split()
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise AssertionError('nonregular Git source member: ' + name)
        inventory[name] = blob.decode()
    if not inventory or len(inventory) > 200000:
        raise AssertionError('implausible source inventory size')
    archive = _git('archive', '--format=tar', commit)
    if len(archive) > 536870912:
        raise AssertionError('archive size limit exceeded')
    destination.mkdir(parents=False, exist_ok=False)
    seen: set[str] = set()
    folded: set[tuple[str, str]] = set()
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        for item in tar:
            name = item.name
            parts = PurePosixPath(name).parts
            if (not name or PurePosixPath(name).is_absolute() or '\\' in name
                    or '..' in parts or re.match(r'^[A-Za-z]:', name)
                    or any(part in ('', '.') for part in parts)):
                raise AssertionError('unsafe archive member: ' + repr(name))
            if item.issym() or item.islnk():
                raise AssertionError('link member rejected: ' + name)
            if not (item.isfile() or item.isdir()):
                raise AssertionError('unsupported member type: ' + name)
            if name in seen:
                raise AssertionError('duplicate member name: ' + name)
            parent = str(PurePosixPath(*parts[:-1]))
            if (parent, parts[-1].casefold()) in folded:
                raise AssertionError('case-colliding member name: ' + name)
            seen.add(name)
            folded.add((parent, parts[-1].casefold()))
            target = destination.joinpath(*parts)
            if item.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if name not in inventory:
                raise AssertionError('member missing from the Git inventory: ' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise AssertionError('extraction target already exists: ' + name)
            raw = tar.extractfile(item).read()
            blob = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if blob != inventory[name]:
                raise AssertionError('extracted bytes differ from the Git blob: ' + name)
            with target.open('xb') as stream:
                stream.write(raw)
    extracted = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
    if extracted != set(inventory):
        raise AssertionError('extracted file inventory differs from the Git tree')
    return inventory


_OLD_ENTRY = r'''
from pathlib import Path
import runpy
import sys

source = Path(sys.argv[1]).resolve()
script = source / "scripts" / sys.argv[2]
arguments = sys.argv[3:]

assert not any(
    name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
    for name in sys.modules
)

sys.path.insert(0, str(source / "src"))
sys.argv = [str(script), *arguments]

try:
    runpy.run_path(str(script), run_name="__main__")
except SystemExit as error:
    exit_code = error.code
else:
    exit_code = 0

loaded = [
    module for name, module in sys.modules.items()
    if name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
]
assert loaded
assert all(
    Path(module.__file__).resolve().is_relative_to(source / "src")
    for module in loaded
)
raise SystemExit(exit_code)
'''

_OLD_RUNNER = r'''
from pathlib import Path
import runpy
import sys

source, payload = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()

assert not any(
    name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
    for name in sys.modules
)

sys.path.insert(0, str(source / "src"))
sys.argv = [str(payload), *sys.argv[3:]]

try:
    runpy.run_path(str(payload), run_name="__main__")
except SystemExit as error:
    exit_code = error.code
else:
    exit_code = 0

loaded = [
    module for name, module in sys.modules.items()
    if name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
]
assert loaded
assert all(
    module.__file__ is not None
    and Path(module.__file__).resolve().is_relative_to(source / "src")
    for module in loaded
)
print("PAYLOAD_SOURCE_OK", file=sys.stderr)
raise SystemExit(exit_code)
'''

# CURRENT script probes: an unrelated package decoy is inserted BEFORE the real
# script runs, CURRENT's package is never preloaded, and provenance is proven.
_CURRENT_ENTRY = r'''
from pathlib import Path
import runpy
import sys

root, foreign = map(Path, sys.argv[1:3])
script, arguments = sys.argv[3], sys.argv[4:]

sys.path.insert(0, str(foreign))
sys.argv = [str(root / "scripts" / script), *arguments]

try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit as error:
    code = error.code
else:
    code = 0

loaded = [
    module for name, module in sys.modules.items()
    if name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
]
assert loaded, "no project modules loaded"
assert all(
    module.__file__ is not None
    and Path(module.__file__).resolve().is_relative_to((root / "src").resolve())
    for module in loaded
), "foreign project code selected"
print("PROJECT_ENTRY_SOURCE_OK", file=sys.stderr)
raise SystemExit(code)
'''

_CURRENT_RUNNER = r'''
from pathlib import Path
import runpy
import sys

source, foreign, payload = map(Path, sys.argv[1:4])

assert not any(
    name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
    for name in sys.modules
)

sys.path.insert(0, str(foreign))
sys.path.insert(0, str(source / "src"))
sys.argv = [str(payload), *sys.argv[4:]]

try:
    runpy.run_path(str(payload), run_name="__main__")
except SystemExit as error:
    exit_code = error.code
else:
    exit_code = 0

loaded = [
    module for name, module in sys.modules.items()
    if name == "polymarket_alpha_lab"
    or name.startswith("polymarket_alpha_lab.")
]
assert loaded
assert all(
    module.__file__ is not None
    and Path(module.__file__).resolve().is_relative_to(source.resolve() / "src")
    for module in loaded
), "foreign project code selected"
print("PAYLOAD_SOURCE_OK", file=sys.stderr)
raise SystemExit(exit_code)
'''

_SNAPSHOT_SQL = {
    'markets': 'SELECT condition_id,market_slug,forecast_cutoff_at,registered_at,'
               'paper_only,report_only,readonly FROM research_capture.markets ORDER BY condition_id',
    'attempts': 'SELECT record_id,condition_id,market_slug,team_id,model_id,protocol_version,task_id,'
                'data_as_of,recorded_at,octet_length(payload),payload_sha256,paper_only,report_only,readonly '
                'FROM research_capture.attempts ORDER BY record_id',
    'claims': 'SELECT record_id,condition_id,market_slug,team_id,model_id,protocol_version,task_id,'
              'data_as_of,claimed_at,octet_length(request_payload),request_sha256,paper_only,report_only,readonly '
              'FROM research_capture.execution_claims ORDER BY record_id',
    'outcomes': 'SELECT condition_id,market_slug,resolved_at,recorded_at,actual_yes,source_reference,'
                'source_content_sha256,paper_only,report_only,readonly '
                'FROM research_capture.outcomes ORDER BY condition_id',
}

# The migration ledger is owner-readable only; read it through the validated
# owner path, never by granting the application role new privileges.
_LEDGER_SQL = ('SELECT coalesce(json_agg(json_build_object(\'name\',name,\'sha256\',sha256,'
               '\'applied_at\',applied_at) ORDER BY name),\'[]\'::json) '
               'FROM project_private.migrations;')

_SNAPSHOT_PAYLOAD = r'''
import json, sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from polymarket_alpha_lab import research_capture_psycopg as capture
from polymarket_alpha_lab.project_postgres import backup_format as fmt
from polymarket_alpha_lab.project_postgres.runtime import verify_runtime
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

queries = json.loads(sys.argv[2])

def plain(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value

def read(dsn):
    def operation(cursor):
        out = {}
        for name, statement in queries.items():
            cursor.execute(statement)
            out[name] = [[plain(value) for value in row] for row in cursor.fetchall()]
        return out
    return capture._local_transaction(dsn, operation, readonly=True)

db = ProjectPostgres(Path(sys.argv[1]))
runtime = verify_runtime(db.layout)
info = db._state()
with db.session() as session:
    business = session._call(read)
    # Owner-path ledger read while the borrowed engine is actually running.
    ledger = json.loads(db._psql(info, sys.argv[3]))
out = dict(instance=dict(info), runtime_version=runtime["version"],
           runtime_files=len(runtime["files"]), runtime_sha256=fmt.fingerprint(runtime["files"]))
out["snapshot"] = dict(business, ledger=ledger)
out["status_after"] = db.status()["status"]
print(json.dumps(out, ensure_ascii=True, allow_nan=False))
'''

_SEED_PAYLOAD = r'''
import json, sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchEvidence, ResearchModelReply, ResearchToolCall,
)
from polymarket_alpha_lab.team_research_intake import (
    GammaMarketSnapshot, prepare_team_research_from_gamma,
)


class Model:
    def __init__(self, source):
        self.source = source
        self.calls = 0

    def complete(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            name, args = "read_evidence", {"source_id": self.source}
        else:
            name, args = "finish_research", dict(
                probability_yes="0.6", confidence="0.2",
                summary="Synthetic version switch fixture.", source_ids=[self.source])
        return ResearchModelReply(
            (ResearchToolCall("call-" + str(self.calls), name, json.dumps(args)),), 1)


def request(index, team):
    now = datetime.now(UTC)
    slug = "vs-market-" + str(index)
    condition = "vs-condition-" + str(index)
    snapshot = GammaMarketSnapshot(slug, now, json.dumps(dict(
        slug=slug, conditionId=condition, question="Synthetic?",
        description="Synthetic resolution criterion", outcomes=["Yes", "No"],
        active=True, closed=False,
        endDate=(now + timedelta(days=1)).isoformat())).encode())
    evidence = ResearchEvidence("vs-source-" + str(index), team, condition,
                                "Synthetic source", "Synthetic text", "synthetic:version-switch", now)
    intake = prepare_team_research_from_gamma(
        snapshot, task_id="vs-task-" + str(index), team_id=team, condition_id=condition,
        as_of=now, evidence=(evidence,))
    return CapturedResearchRequest(
        "vs-record-" + str(index), "synthetic-model", "version-switch-proof-v1",
        now + timedelta(hours=1), intake, required_source_ids=("vs-source-" + str(index),))


root = Path(sys.argv[1])
out = {}
db = ProjectPostgres(root)
with db.session() as session:
    btc = request(1, "crypto_btc")
    completed = session.run_research(
        request=btc, model_factory=lambda _: Model("vs-source-1"))
    out["completed"] = completed.to_dict()
    eth = request(2, "crypto_eth")

    def broken(_):
        raise RuntimeError("synthetic model factory failure")

    failed = session.run_research(request=eth, model_factory=broken)
    out["failed"] = failed.to_dict()
    outstanding = request(3, "crypto_btc")
    owned, state = session._call(execution._claim, request=outstanding)
    out["outstanding_owned"] = owned
    out["outstanding"] = state.to_dict()
    out["inspections"] = {record_id: session.inspect(record_id=record_id).to_dict()
                          for record_id in ("vs-record-1", "vs-record-2", "vs-record-3")}
    try:
        session.evaluate()
        out["evaluation_refusal"] = "none"
    except Exception as error:
        out["evaluation_refusal"] = type(error).__name__ + ":" + str(error)
out["status_after"] = db.status()["status"]
print(json.dumps(out, ensure_ascii=True, allow_nan=False))
'''

_READBACK_PAYLOAD = r'''
import json, sys
from pathlib import Path
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

out = dict(admitted=False, code=None, records=None, evaluation=None, status_after=None)
db = ProjectPostgres(Path(sys.argv[1]))
try:
    with db.session() as session:
        out["admitted"] = True
        out["records"] = {record_id: session.inspect(record_id=record_id).to_dict()
                          for record_id in sys.argv[2:]}
        try:
            session.evaluate()
            out["evaluation"] = "none"
        except Exception as error:
            out["evaluation"] = type(error).__name__ + ":" + str(error)
except ProjectDatabaseError as error:
    out["code"] = str(error)
try:
    out["status_after"] = db.status()["status"]
except ProjectDatabaseError as error:
    out["status_after"] = "error:" + str(error)
print(json.dumps(out, ensure_ascii=True, allow_nan=False))
'''

_BUNDLE_PROBE_PAYLOAD = r'''
import json, sys
from pathlib import Path
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

out = dict(code="admitted", status_after=None)
try:
    with ProjectPostgres(Path(sys.argv[1])).session():
        pass
except ProjectDatabaseError as error:
    out["code"] = str(error)
try:
    out["status_after"] = ProjectPostgres(Path(sys.argv[1])).status()["status"]
except ProjectDatabaseError as error:
    out["status_after"] = "error:" + str(error)
print(json.dumps(out, ensure_ascii=True, allow_nan=False))
'''


def _child_env() -> dict[str, str]:
    env = files.clean_environment()
    for key in tuple(env):
        if key.upper().startswith('PYTEST') or key.upper().startswith('GIT_'):
            del env[key]
    env['PYTHONUTF8'] = '1'
    return env


def _run(args, cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), env=_child_env(), stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=timeout, check=False, shell=False)


def _json_stdout(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout.decode('utf-8'))


def _blocked_reason(result: subprocess.CompletedProcess) -> str:
    # Child stderr may also carry the wrapper's provenance marker; only one
    # line is the CLI's blocked-reason JSON object.
    for line in reversed(result.stderr.decode('utf-8', 'replace').strip().splitlines()):
        try:
            decoded = json.loads(line)
        except ValueError:
            continue
        if type(decoded) is dict and 'reason_code' in decoded:
            return decoded['reason_code']
    raise AssertionError('no blocked-reason JSON in child stderr: '
                         + result.stderr.decode('utf-8', 'replace')[-400:])


def _stderr_text(result: subprocess.CompletedProcess) -> str:
    return result.stderr.decode('utf-8', 'replace')


def test_version_switch_native_ci_is_required():
    """The dedicated storage-partition workflow step and its gates are wired."""
    text = WORKFLOW.read_text(encoding='utf-8').replace('\r\n', '\n')
    worker, gate = text.split('  windows-native:\n')
    checkout = worker.split('      - uses: actions/checkout@', 1)[1].split('      - uses:', 1)[0]
    assert 'fetch-depth: 0\n' in checkout
    assert 'persist-credentials: false\n' in checkout
    assert '      fail-fast: false\n' in worker and '    timeout-minutes: 20\n' in worker
    assert 'continue-on-error' not in text
    partition = worker.split('      - name: Prove isolated native partition\n', 1)[1]
    switch = partition.split('      - name: Verify tracked source unchanged\n', 1)[0]
    assert '      - name: Prove native version switch\n' in switch
    assert "if: matrix.partition == 'storage'" in switch
    assert 'tests/test_project_postgres_version_switch_native.py' in switch
    assert "POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX: 'C:\\Program Files\\PostgreSQL\\17'" in switch
    assert "$env:POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES = '1'" in switch
    assert "$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'" in switch
    assert "$env:PYTHONUTF8 = '1'" in switch
    assert 'Tee-Object -FilePath "$env:RUNNER_TEMP/version-switch-proof.log"' in switch
    assert 'junitxml="$env:RUNNER_TEMP/version-switch-proof.xml"' in switch
    assert '$code = $LASTEXITCODE\n' in switch and 'exit $code\n' in switch
    upload = worker.split('      - uses: actions/upload-artifact@', 1)[1]
    assert '${{ runner.temp }}/version-switch-proof.log' in upload
    assert '${{ runner.temp }}/version-switch-proof.xml' in upload
    assert 'if-no-files-found: error' in upload and 'if: always()' in upload
    assert 'needs: [windows-native-part]' in gate
    assert 'test "$NATIVE_RESULT" = success' in gate


def _plain(value):
    from datetime import date, datetime, time
    from decimal import Decimal
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _snapshot_rows(cursor, queries):
    out = {}
    for name, statement in queries.items():
        cursor.execute(statement)
        out[name] = [[_plain(value) for value in row] for row in cursor.fetchall()]
    return out


def _snapshot_current(original: Path) -> dict:
    from polymarket_alpha_lab import research_capture_psycopg as capture
    db = ProjectPostgres(original)
    runtime = verify_runtime(db.layout)
    info = db._state()
    with db.session() as session:
        snapshot = session._call(
            lambda dsn: capture._local_transaction(
                dsn, lambda cursor: _snapshot_rows(cursor, _SNAPSHOT_SQL), readonly=True))
        # Owner-path ledger read while the session's engine is running.
        ledger = json.loads(db._psql(info, _LEDGER_SQL))
    return dict(instance=dict(info), runtime_version=runtime['version'],
                runtime_files=len(runtime['files']),
                runtime_sha256=fmt.fingerprint(runtime['files']),
                snapshot={**snapshot, 'ledger': ledger})


def _effective_catalog(root: Path) -> tuple[int, str, tuple[tuple[str, str], ...]]:
    rows = sql.migration_catalog(files.Layout(root))
    pairs = tuple((name, digest) for name, digest, _ in rows)
    return len(rows), fmt.fingerprint(pairs), pairs


def _physical_counts(db: ProjectPostgres, info: dict) -> dict:
    return {
        'ledger': db._psql(info, 'SELECT count(*) FROM project_private.migrations;'),
        'tables': {name: db._psql(info, f"SELECT to_regclass('{name}') IS NOT NULL;")
                   for name in FEATURE_TABLES},
        'attempts': db._psql(info, 'SELECT count(*) FROM research_capture.attempts;'),
        'claims': db._psql(info, 'SELECT count(*) FROM research_capture.execution_claims;'),
        'outcomes': db._psql(info, 'SELECT count(*) FROM research_capture.outcomes;'),
    }


def _write_synthetic_bundle(root: Path) -> None:
    """A complete, well-shaped synthetic kit marker set that the verifier passes.

    The engine member is inert bytes; only its manifest hash is ever consulted.
    It is never executed, imported or described as a released kit.
    """
    actual = set(distribution.FIXED)
    for name in distribution.PUBLIC_ENTRYPOINTS:
        if (root / name).is_file():
            actual.add(name)
    for base in distribution.SOURCE_ROOTS:
        for target in (root / base).rglob('*'):
            relative = target.relative_to(root).as_posix()
            if target.is_file() and distribution.selected_source(relative):
                actual.add(relative)
    manifest_files = {name: files.digest_file(root / name) for name in sorted(actual)}
    seed = root / distribution.ENGINE
    seed.write_bytes(b'synthetic inert engine seed; never executed or imported\n')
    manifest_files[distribution.ENGINE] = files.digest_file(seed)
    manifest = dict(format=distribution.FORMAT, source_commit='c' * 40, source_tree='d' * 40,
                    target='windows-x86_64', postgres_version='17.11',
                    python_requires='>=3.11', files=manifest_files)
    (root / distribution.MANIFEST).write_text(json.dumps(manifest, sort_keys=True), encoding='utf-8')
    distribution.verify_distribution(root)


def _remove_bundle_markers(root: Path) -> None:
    for marker in (root / distribution.ENGINE, root / distribution.MANIFEST):
        if marker.exists():
            marker.unlink()


class _Rig(dict):
    __getattr__ = dict.__getitem__


def prepare_verified_archives_and_private_root(tmp_path, monkeypatch) -> _Rig:
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    assert prefix.is_absolute() and all((prefix / part).is_dir() for part in ('bin', 'lib', 'share')), \
        'native PostgreSQL prefix binaries are required once the opt-in is enabled'
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):
            monkeypatch.delenv(key)
    parent = tmp_path
    if os.name == 'nt':
        runner = Path(os.environ['RUNNER_TEMP'])
        assert runner.is_dir(), 'RUNNER_TEMP must exist once the opt-in is enabled'
        parent = runner / ('pal-version-switch-' + uuid.uuid4().hex)
        files.private_directory(parent, create=True)
    neutral = parent / 'neutral-cwd'
    neutral.mkdir()
    foreign = parent / 'unrelated-editable' / 'polymarket_alpha_lab'
    foreign.mkdir(parents=True)
    (foreign / '__init__.py').write_text("raise RuntimeError('FOREIGN_EDITABLE_SELECTED')\n",
                                         encoding='ascii')
    payloads = parent / 'payloads'
    payloads.mkdir()
    old_source = parent / 'old-source'
    candidate = parent / 'candidate-source'
    old_inventory = _extract_verified_archive(old_source, OLD_COMMIT, OLD_TREE)
    candidate_commit = _git('rev-parse', '--verify', 'HEAD').decode().strip()
    candidate_tree = _git('rev-parse', '--verify', 'HEAD^{tree}').decode().strip()
    assert re.fullmatch('[0-9a-f]{40}', candidate_commit)
    assert re.fullmatch('[0-9a-f]{40}', candidate_tree)
    _extract_verified_archive(candidate, candidate_commit, candidate_tree)
    original = parent / 'Original Project'
    original.mkdir()
    selected = [name for name in old_inventory if distribution.selected_source(name)]
    assert set(distribution.FIXED) <= set(selected)
    for name in sorted(selected):
        target = original.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(old_source.joinpath(*PurePosixPath(name).parts), target)
    original_pairs = _effective_catalog(original)
    assert original_pairs[0] == OLD_CATALOG_ENTRIES
    assert original_pairs[1] == OLD_CATALOG_FINGERPRINT
    candidate_entries, candidate_fingerprint, candidate_pairs = _effective_catalog(candidate)
    assert candidate_entries == CANDIDATE_CATALOG_ENTRIES
    assert candidate_pairs[:OLD_CATALOG_ENTRIES] == original_pairs[2]
    assert {name for name, _ in candidate_pairs[OLD_CATALOG_ENTRIES:]} == set(NEW_MIGRATIONS)
    assert (original / 'supabase/migrations' / INSIDE_OLD_MIGRATION).is_file()
    print('version-switch fixture: candidate', candidate_commit, candidate_tree,
          'old-catalog-63', original_pairs[1][:16], 'candidate-catalog-68',
          candidate_fingerprint[:16])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    return _Rig(base=parent, neutral=neutral, foreign=foreign.parent, payloads=payloads,
                old_source=old_source, candidate=candidate, original=original,
                candidate_commit=candidate_commit, candidate_tree=candidate_tree,
                candidate_fingerprint=candidate_fingerprint, port=port, prefix=prefix,
                python=str(Path(sys.executable).resolve()), records={}, snapshot=None,
                identity=None, runtime=None, backup=None, phases=[])


def _phase(rig, name):
    print(f'version-switch phase {name}: start')
    return time.monotonic()


def _phase_done(rig, name, start):
    elapsed = time.monotonic() - start
    rig['phases'].append((name, elapsed))
    print(f'version-switch phase {name}: done in {elapsed:.1f}s')


def _payload_file(rig, name: str, text: str) -> Path:
    path = rig['payloads'] / name
    path.write_text(text, encoding='utf-8')
    return path


def _old_cli(rig, *arguments, timeout: int = 900) -> subprocess.CompletedProcess:
    return _run([rig['python'], '-I', '-B', '-c', _OLD_ENTRY, str(rig['old_source']),
                 'project_database.py', *arguments], rig['neutral'], timeout=timeout)


def _old_payload(rig, name: str, text: str, *arguments, timeout: int = 900):
    payload = _payload_file(rig, name, text)
    result = _run([rig['python'], '-I', '-B', '-c', _OLD_RUNNER, str(rig['old_source']),
                   str(payload), *arguments], rig['neutral'], timeout=timeout)
    assert 'PAYLOAD_SOURCE_OK' in _stderr_text(result)
    return result


def _current_cli(rig, script: str, *arguments, source=None,
                 timeout: int = 900) -> subprocess.CompletedProcess:
    result = _run([rig['python'], '-I', '-B', '-c', _CURRENT_ENTRY, str(source or rig['candidate']),
                   str(rig['foreign']), script, *arguments], rig['neutral'], timeout=timeout)
    stderr = _stderr_text(result)
    assert 'PROJECT_ENTRY_SOURCE_OK' in stderr
    assert 'FOREIGN_EDITABLE_SELECTED' not in stderr
    return result


def _current_payload(rig, name: str, text: str, *arguments, source=None, timeout: int = 900):
    payload = _payload_file(rig, name, text)
    result = _run([rig['python'], '-I', '-B', '-c', _CURRENT_RUNNER,
                   str(source or rig['candidate']), str(rig['foreign']), str(payload),
                   *arguments], rig['neutral'], timeout=timeout)
    assert 'PAYLOAD_SOURCE_OK' in _stderr_text(result)
    return result


def initialize_and_seed_with_old_source(rig) -> None:
    original, port = rig['original'], str(rig['port'])
    installed = _old_cli(rig, '--root', str(original), 'install-runtime',
                         '--from-directory', str(rig['prefix']))
    assert installed.returncode == 0, _stderr_text(installed)
    assert _json_stdout(installed)['status'] == 'runtime_installed'
    initialized = _old_cli(rig, '--root', str(original), 'init', '--port', port)
    assert initialized.returncode == 0, _stderr_text(initialized)
    assert _json_stdout(initialized)['migrations_applied'] == OLD_CATALOG_ENTRIES
    refused = _old_cli(rig, '--root', str(original), 'init', '--port', port)
    assert refused.returncode == 1
    assert _blocked_reason(refused) == 'project_postgres_existing_data_not_reinitialized'
    status = _old_cli(rig, '--root', str(original), 'status')
    assert _json_stdout(status)['status'] == 'stopped'
    seeded = _old_payload(rig, 'seed.py', _SEED_PAYLOAD, str(original))
    assert seeded.returncode == 0, _stderr_text(seeded)
    records = _json_stdout(seeded)
    completed, failed, outstanding = (records['completed'], records['failed'],
                                      records['outstanding'])
    assert completed['status'] == 'captured' and completed['research_status'] == 'completed'
    assert completed['recorded_at'] is not None and completed['paper_only'] is True
    assert completed['report_only'] is True and completed['readonly'] is True
    assert failed['status'] == 'captured' and failed['research_status'] == 'failed'
    assert failed['recorded_at'] is not None
    assert records['outstanding_owned'] is True
    assert outstanding['status'] == 'incomplete' and outstanding['recorded_at'] is None
    for record_id, execution, expected in zip(
            RECORD_IDS, (completed, failed, outstanding),
            ('already_captured', 'already_captured', 'incomplete')):
        inspection = records['inspections'][record_id]
        assert inspection == dict(execution, status=expected), record_id
    assert 'research_execution_history_incomplete' in records['evaluation_refusal']
    assert records['status_after'] == 'stopped'
    # Later phases compare the INSPECTION view keyed by record id; it is the
    # stable cross-source shape for both OLD and CURRENT readers.
    rig['records'] = records['inspections']
    snapshot = _old_payload(rig, 'snapshot-old.py', _SNAPSHOT_PAYLOAD, str(original),
                            json.dumps(_SNAPSHOT_SQL), _LEDGER_SQL)
    assert snapshot.returncode == 0, _stderr_text(snapshot)
    old_view = _json_stdout(snapshot)
    assert old_view['status_after'] == 'stopped'
    data = old_view['snapshot']
    assert len(data['markets']) == 3 and len(data['attempts']) == 2
    assert len(data['claims']) == 3 and data['outcomes'] == []
    assert len(data['ledger']) == OLD_CATALOG_ENTRIES
    assert sorted(row[0] for row in data['markets']) == sorted(CONDITION_IDS)
    assert all(row[4:] == [True, True, True] for row in data['markets'])
    assert all(row[11:] == [True, True, True] for row in data['claims'])
    assert all(row[11:] == [True, True, True] for row in data['attempts'])
    rig['snapshot'] = data
    rig['identity'] = old_view['instance']
    rig['runtime'] = {key: old_view[key] for key in
                      ('runtime_version', 'runtime_files', 'runtime_sha256')}


def prove_lifecycle_and_prepare_cold_backup(rig) -> None:
    from polymarket_alpha_lab import research_execution_psycopg as execution_store
    original = rig['original']
    entered, release = Event(), Event()
    outcomes, failures = [], []

    def held(dsn):
        result = execution_store.inspect_captured_research_with_psycopg(
            dsn, record_id=RECORD_IDS[0])
        entered.set()
        assert release.wait(60), 'test did not release the admitted read'
        return result

    def work():
        try:
            with ProjectPostgres(original).session() as session:
                rig['drain_session'] = session
                outcomes.append(session._call(held))
        except BaseException as error:  # noqa: BLE001  (the worker must retain its failure)
            failures.append(error)

    worker = threading.Thread(target=work)
    worker.start()
    assert entered.wait(120), 'admitted read did not start'
    session = rig['drain_session']
    closer = threading.Thread(target=session.close)
    closer.start()
    deadline = time.monotonic() + 60
    while session._active and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not session._active, 'close did not seal new admissions'
    with pytest.raises(files.ProjectDatabaseError, match='session_closed'):
        session._call(lambda dsn: pytest.fail('work admitted on the closing session'))
    busy = _old_cli(rig, '--root', str(original), 'down')
    assert busy.returncode == 1 and _blocked_reason(busy) == 'project_postgres_busy'
    release.set()
    closer.join(120)
    worker.join(120)
    assert failures == [] and len(outcomes) == 1
    assert outcomes[0].to_dict() == rig['records'][RECORD_IDS[0]]
    del rig['drain_session']
    assert ProjectPostgres(original).status()['status'] == 'stopped'
    started = _old_cli(rig, '--root', str(original), 'up')
    assert _json_stdout(started)['status'] == 'running'
    with ProjectPostgres(original).session() as borrowed:
        assert borrowed.inspect(record_id=RECORD_IDS[0]).to_dict() == \
            rig['records'][RECORD_IDS[0]]
    assert ProjectPostgres(original).status()['status'] == 'running'
    stopped = _old_cli(rig, '--root', str(original), 'down')
    assert _json_stdout(stopped)['status'] == 'stopped'
    destination = rig['base'] / 'Private Backup'
    backed_up = _old_cli(rig, '--root', str(original), 'backup', '--destination', str(destination))
    assert backed_up.returncode == 0, _stderr_text(backed_up)
    receipt = _json_stdout(backed_up)
    assert receipt['status'] == 'backup_created' and receipt['contains_credentials'] is True
    archive = destination / 'snapshot.palpg.zip'
    verified = _old_cli(rig, '--root', str(original), 'verify-backup', '--archive', str(archive),
                        '--sha256', receipt['sha256'], '--trusted-backup')
    assert verified.returncode == 0, _stderr_text(verified)
    assert _json_stdout(verified)['status'] == 'backup_verified'
    rig['backup'] = dict(destination=destination, archive=archive, sha256=receipt['sha256'])


def prove_stopped_selection_and_current_common_reads(rig) -> None:
    original = rig['original']
    old_status = _json_stdout(_old_cli(rig, '--root', str(original), 'status'))
    current = _current_cli(rig, 'project_database.py', '--root', str(original), 'status')
    assert current.returncode == 0, current.stdout.decode('utf-8', 'replace')
    current_status = _json_stdout(current)
    assert old_status == current_status
    assert old_status['status'] == 'stopped'
    assert old_status['instance_id'] == rig['identity']['instance_id']
    assert old_status['port'] == rig['identity']['port']
    assert old_status['version'] == rig['identity']['version']
    for source in (rig['candidate'], rig['old_source']):
        assert not (source / '.local').exists() and not (source / 'runtime').exists()
    worklist = _current_cli(rig, 'review_resolution_queue.py', '--root', str(original))
    assert worklist.returncode == 0, worklist.stdout.decode('utf-8', 'replace')
    listing = _json_stdout(worklist)
    assert listing['incomplete_execution_count'] == 1
    assert listing['evaluation_blocked_by_incomplete'] is True
    assert listing['registered_market_count'] == 3
    text = json.dumps(listing)
    for identity in (*CONDITION_IDS, 'vs-market-1', 'vs-market-2', 'vs-market-3'):
        assert identity in text
    missing = _current_cli(rig, 'manage_research_tasks.py', '--root', str(original),
                           'inspect-batch', '--batch-id', 'vs-missing-batch')
    assert missing.returncode == 1
    refused = _json_stdout(missing)
    assert refused['status'] == 'failed'
    assert refused['reason_code'] == 'research_dispatch_operation_failed'
    readback = _current_payload(rig, 'readback.py', _READBACK_PAYLOAD, str(original), *RECORD_IDS)
    assert readback.returncode == 0, readback.stdout.decode('utf-8', 'replace')
    current_view = _json_stdout(readback)
    assert current_view['admitted'] is True and current_view['code'] is None
    assert current_view['records'] == rig['records']
    assert 'research_execution_history_incomplete' in current_view['evaluation']
    assert current_view['status_after'] == 'stopped'
    snapshot = _snapshot_current(original)
    assert snapshot['snapshot'] == rig['snapshot']
    assert snapshot['instance'] == rig['identity']
    assert {key: snapshot[key] for key in rig['runtime']} == rig['runtime']
    assert ProjectPostgres(original).status()['status'] == 'stopped'


def prove_compatible_old_source_rollback(rig) -> None:
    original = rig['original']
    rolled = _old_payload(rig, 'rollback.py', _READBACK_PAYLOAD, str(original), *RECORD_IDS)
    assert rolled.returncode == 0, rolled.stdout.decode('utf-8', 'replace')
    view = _json_stdout(rolled)
    assert view['admitted'] is True and view['code'] is None
    assert view['records'] == rig['records']
    assert 'research_execution_history_incomplete' in view['evaluation']
    assert view['status_after'] == 'stopped'
    snapshot = _old_payload(rig, 'snapshot-rollback.py', _SNAPSHOT_PAYLOAD, str(original),
                            json.dumps(_SNAPSHOT_SQL), _LEDGER_SQL)
    old_view = _json_stdout(snapshot)
    assert old_view['snapshot'] == rig['snapshot']
    assert old_view['instance'] == rig['identity']
    assert {key: old_view[key] for key in rig['runtime']} == rig['runtime']
    assert old_view['status_after'] == 'stopped'
    print('version-switch rollback: shared APIs admitted at 63/63; original rows intact')


def prove_bundle_integrity_refusals(rig) -> None:
    original = rig['original']
    candidate_damaged = rig['base'] / 'candidate-source-damaged'
    shutil.copytree(rig['candidate'], candidate_damaged)
    try:
        _write_synthetic_bundle(candidate_damaged)
        victim = candidate_damaged / 'src/polymarket_alpha_lab/analytics.py'
        victim_bytes = victim.read_bytes()
        probe = _current_payload(rig, 'bundle-source.py', _BUNDLE_PROBE_PAYLOAD, str(original),
                                 source=candidate_damaged)
        assert _json_stdout(probe)['code'] == 'admitted'
        with victim.open('ab') as stream:
            stream.write(b'\n# changed fixture\n')
        probe = _current_payload(rig, 'bundle-source-damaged.py', _BUNDLE_PROBE_PAYLOAD,
                                 str(original), source=candidate_damaged)
        assert _json_stdout(probe) == {'code': 'project_bundle_invalid_or_changed',
                                       'status_after': 'stopped'}
        entrypoint = _current_cli(rig, 'review_resolution_queue.py', '--root', str(original),
                                  source=candidate_damaged)
        assert entrypoint.returncode == 1
        assert _json_stdout(entrypoint)['reason_code'] == 'resolution_queue_operation_failed'
        victim.write_bytes(victim_bytes)
        _write_synthetic_bundle(original)
        migration = original / 'supabase/migrations' / INSIDE_OLD_MIGRATION
        migration_bytes = migration.read_bytes()
        probe = _current_payload(rig, 'bundle-data.py', _BUNDLE_PROBE_PAYLOAD, str(original))
        assert _json_stdout(probe)['code'] == 'admitted'
        with migration.open('ab') as stream:
            stream.write(b'\n-- changed fixture\n')
        probe = _current_payload(rig, 'bundle-data-damaged.py', _BUNDLE_PROBE_PAYLOAD,
                                 str(original))
        assert _json_stdout(probe) == {'code': 'project_bundle_invalid_or_changed',
                                       'status_after': 'stopped'}
        migration.write_bytes(migration_bytes)
    finally:
        _remove_bundle_markers(original)
        _remove_bundle_markers(candidate_damaged)
        shutil.rmtree(candidate_damaged, ignore_errors=True)
    snapshot = _snapshot_current(original)
    assert snapshot['snapshot'] == rig['snapshot'] and snapshot['instance'] == rig['identity']
    assert ProjectPostgres(original).status()['status'] == 'stopped'


def _stop_engine(rig) -> None:
    try:
        ProjectPostgres(rig['original']).down()
    except Exception as error:  # noqa: BLE001  (recorded, never force-killed)
        print('version-switch engine stop during fixture edits failed:', type(error).__name__)


def _running_physical_state(original: Path) -> tuple[dict, dict, dict]:
    """Owner-path ledger/table counts with the engine explicitly up, then down.

    This is also the real `up()` pending-count observation; `down()` always
    runs in finally so the fixture is stopped before the next edit or backup.
    """
    db = ProjectPostgres(original)
    state = db.up()
    try:
        info = db._state()
        counts = _physical_counts(db, info)
    finally:
        db.down()
    assert db.status()['status'] == 'stopped'
    return state, info, counts


def prove_pending_catalog_and_backup_prefix_paths(rig) -> None:
    original, backup = rig['original'], rig['backup']
    lock_file = original / 'database/migrations.lock.json'
    try:
        shutil.copyfile(rig['candidate'] / 'database/migrations.lock.json', lock_file)
        for name in NEW_MIGRATIONS:
            shutil.copyfile(rig['candidate'] / 'supabase/migrations' / name,
                            original / 'supabase/migrations' / name)
        pending = _current_payload(rig, 'pending.py', _BUNDLE_PROBE_PAYLOAD, str(original))
        assert _json_stdout(pending) == {'code': 'project_postgres_migrations_pending',
                                         'status_after': 'stopped'}
        state, info, counts = _running_physical_state(original)
        assert info == rig['identity']
        assert state['status'] == 'migrations_pending' and state['pending_migrations'] == 5
        assert state['started_here'] is True
        assert counts['ledger'] == '63' and counts['attempts'] == '2'
        assert counts['claims'] == '3' and counts['outcomes'] == '0'
        assert set(counts['tables'].values()) == {'f'}
        mismatch = _old_cli(rig, '--root', str(original), 'verify-backup',
                            '--archive', str(backup['archive']), '--sha256', backup['sha256'],
                            '--trusted-backup')
        assert mismatch.returncode == 1
        assert _blocked_reason(mismatch) == 'project_postgres_backup_migrations_mismatch'
        extended = _current_cli(rig, 'project_database.py', '--root', str(original),
                                'verify-backup', '--archive', str(backup['archive']),
                                '--sha256', backup['sha256'], '--trusted-backup',
                                '--allow-catalog-extension')
        assert extended.returncode == 0, extended.stdout.decode('utf-8', 'replace')
        receipt = _json_stdout(extended)
        assert receipt['status'] == 'backup_verified' and receipt['database_started'] is False
        assert receipt['migration_catalog'] == dict(
            match='append_only_extension', backup_entries=63, current_entries=68,
            current_sha256=rig['candidate_fingerprint'], additional_entries=5,
            database_ledger_checked=False, migrations_applied=0)
        restore = _current_cli(rig, 'project_database.py', '--root', str(original), 'restore',
                               '--archive', str(backup['archive']), '--sha256', backup['sha256'],
                               '--trusted-backup', '--allow-catalog-extension')
        assert restore.returncode == 1
        assert _blocked_reason(restore) == 'project_postgres_restore_existing_data_refused'
        assert (original / '.local/postgres').is_dir()
        assert not (original / '.local/postgres.restoring').exists()
        inside_path = original / 'supabase/migrations' / INSIDE_OLD_MIGRATION
        raw_inside, raw_lock = inside_path.read_bytes(), lock_file.read_bytes()
        try:
            altered = raw_inside + b'\n-- test-only non-prefix alteration\n'
            inside_path.write_bytes(altered)
            catalog = json.loads(lock_file.read_text(encoding='utf-8'))
            entry = next(item for item in catalog['migrations']
                         if item['name'] == INSIDE_OLD_MIGRATION)
            entry['sha256'] = sha256(altered).hexdigest()
            lock_file.write_text(json.dumps(catalog), encoding='utf-8')
            refused = _current_cli(rig, 'project_database.py', '--root', str(original),
                                   'verify-backup', '--archive', str(backup['archive']),
                                   '--sha256', backup['sha256'], '--trusted-backup',
                                   '--allow-catalog-extension')
            assert refused.returncode == 1
            assert _blocked_reason(refused) == 'project_postgres_backup_migrations_mismatch'
            conflict = _current_payload(rig, 'conflict.py', _BUNDLE_PROBE_PAYLOAD, str(original))
            assert _json_stdout(conflict) == {
                'code': 'project_postgres_migration_history_conflict', 'status_after': 'stopped'}
        finally:
            inside_path.write_bytes(raw_inside)
            lock_file.write_bytes(raw_lock)
        try:
            with inside_path.open('ab') as stream:
                stream.write(b'\n-- unmanifested change\n')
            changed = _current_cli(rig, 'project_database.py', '--root', str(original), 'up')
            assert changed.returncode == 1
            assert _blocked_reason(changed) == 'project_postgres_migration_changed'
        finally:
            inside_path.write_bytes(raw_inside)
            _stop_engine(rig)
        try:
            (original / 'supabase/migrations' / '20990101000000_extra.sql').write_bytes(
                b'SELECT 1;\n')
            inventory = _current_cli(rig, 'project_database.py', '--root', str(original), 'up')
            assert inventory.returncode == 1
            assert _blocked_reason(inventory) == 'project_postgres_migration_inventory_mismatch'
        finally:
            (original / 'supabase/migrations' / '20990101000000_extra.sql').unlink()
            _stop_engine(rig)
        state, info, counts = _running_physical_state(original)
        assert info == rig['identity']
        assert state['status'] == 'migrations_pending' and state['pending_migrations'] == 5
        assert counts['ledger'] == '63' and counts['attempts'] == '2'
        assert counts['claims'] == '3' and counts['outcomes'] == '0'
        assert set(counts['tables'].values()) == {'f'}
        assert ProjectPostgres(original).status()['status'] == 'stopped'
    finally:
        # The staged valid 68-entry catalog stays for the explicit migration
        # phase; only ensure the engine is stopped for the next fixture edit.
        _stop_engine(rig)
    assert lock_file.read_bytes() == (rig['candidate'] / 'database/migrations.lock.json').read_bytes()
    print('version-switch pending/refusals: 68/63 refused; prefix extension exact')


def prove_explicit_migration_and_old_catalog_refusal(rig) -> None:
    original = rig['original']
    migrated = _current_cli(rig, 'project_database.py', '--root', str(original), 'migrate')
    assert migrated.returncode == 0, migrated.stdout.decode('utf-8', 'replace')
    assert _json_stdout(migrated)['migrations_applied'] == 5
    again = _current_cli(rig, 'project_database.py', '--root', str(original), 'migrate')
    assert _json_stdout(again)['migrations_applied'] == 0
    readback = _current_payload(rig, 'readback-68.py', _READBACK_PAYLOAD, str(original), *RECORD_IDS)
    view = _json_stdout(readback)
    assert view['admitted'] is True and view['records'] == rig['records']
    assert 'research_execution_history_incomplete' in view['evaluation']
    assert view['status_after'] == 'stopped'
    missing = _current_cli(rig, 'manage_research_tasks.py', '--root', str(original),
                           'inspect-batch', '--batch-id', 'vs-missing-batch')
    assert missing.returncode == 3
    envelope = _json_stdout(missing)
    assert envelope['operation'] == 'inspect-batch'
    assert envelope['status'] == 'not_found' and envelope['result'] is None
    state, info, counts = _running_physical_state(original)
    assert info == rig['identity']
    assert state['status'] == 'running' and state['pending_migrations'] == 0
    assert counts['ledger'] == '68' and set(counts['tables'].values()) == {'t'}
    assert counts['attempts'] == '2' and counts['claims'] == '3' and counts['outcomes'] == '0'
    snapshot = _snapshot_current(original)
    for section in ('markets', 'attempts', 'claims', 'outcomes'):
        assert snapshot['snapshot'][section] == rig['snapshot'][section]
    assert snapshot['snapshot']['ledger'][:63] == rig['snapshot']['ledger']
    assert len(snapshot['snapshot']['ledger']) == 68
    assert snapshot['instance'] == rig['identity']
    lock_file = original / 'database/migrations.lock.json'
    staged_lock = lock_file.read_bytes()
    try:
        lock_file.write_bytes((rig['old_source'] / 'database/migrations.lock.json').read_bytes())
        for name in NEW_MIGRATIONS:
            (original / 'supabase/migrations' / name).unlink()
        conflict = _current_payload(rig, 'conflict-63-68.py', _BUNDLE_PROBE_PAYLOAD, str(original))
        assert _json_stdout(conflict) == {
            'code': 'project_postgres_migration_history_conflict', 'status_after': 'stopped'}
    finally:
        lock_file.write_bytes(staged_lock)
        for name in NEW_MIGRATIONS:
            shutil.copyfile(rig['candidate'] / 'supabase/migrations' / name,
                            original / 'supabase/migrations' / name)
    assert ProjectPostgres(original).status()['status'] == 'stopped'
    print('version-switch migration: five appended; 68/68 admitted; 63 receipts preserved')


def stop_owned_disposable_instance_preserving_failures(rig) -> None:
    home = rig['original'] / '.local' / 'postgres'
    if not home.exists():
        return
    try:
        result = ProjectPostgres(rig['original']).down()
        print('version-switch cleanup:', result['status'])
    except Exception as error:  # noqa: BLE001  (a cleanup failure must not mask the first one)
        rig['cleanup_failure'] = f'{type(error).__name__}:{error}'
        print('version-switch CLEANUP FAILURE (first failure above stays authoritative):',
              type(error).__name__)


@pytest.mark.skipif(not ENABLED, reason='explicit disposable native version-switch proof is opt-in')
def test_native_same_root_source_selection_rollback_and_refusals(tmp_path, monkeypatch):
    rig = prepare_verified_archives_and_private_root(tmp_path, monkeypatch)
    try:
        start = _phase(rig, 'old-initialize')
        initialize_and_seed_with_old_source(rig)
        _phase_done(rig, 'old-initialize', start)
        start = _phase(rig, 'lifecycle-backup')
        prove_lifecycle_and_prepare_cold_backup(rig)
        _phase_done(rig, 'lifecycle-backup', start)
        start = _phase(rig, 'current-selection')
        prove_stopped_selection_and_current_common_reads(rig)
        _phase_done(rig, 'current-selection', start)
        start = _phase(rig, 'old-rollback')
        prove_compatible_old_source_rollback(rig)
        _phase_done(rig, 'old-rollback', start)
        start = _phase(rig, 'bundle-refusals')
        prove_bundle_integrity_refusals(rig)
        _phase_done(rig, 'bundle-refusals', start)
        start = _phase(rig, 'pending-backup-refusals')
        prove_pending_catalog_and_backup_prefix_paths(rig)
        _phase_done(rig, 'pending-backup-refusals', start)
        start = _phase(rig, 'explicit-migration')
        prove_explicit_migration_and_old_catalog_refusal(rig)
        _phase_done(rig, 'explicit-migration', start)
        print('version-switch native: PASS;', ';'.join(f'{name}:{elapsed:.1f}s'
                                                       for name, elapsed in rig['phases']))
    finally:
        stop_owned_disposable_instance_preserving_failures(rig)
    if rig.get('cleanup_failure'):
        raise AssertionError('cleanup could not stop the owned disposable instance: '
                             + rig['cleanup_failure'])
