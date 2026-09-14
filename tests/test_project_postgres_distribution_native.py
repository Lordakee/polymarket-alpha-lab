"""Actual Windows kit build -> extraction -> first startup -> retained research.

Uses only a trusted runner binary prefix and fresh, owned disposable directories.
The tested ZIP contains no pre-initialized instance or credentials. No Docker,
Windows database service, paid models or public API calls are made by the proof.
"""
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import uuid
import zipfile

import pytest

from polymarket_alpha_lab.project_postgres import distribution
from polymarket_alpha_lab.project_postgres.files import clean_environment, private_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_DISTRIBUTION') == '1'


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def extract(archive, parent):
    parent.mkdir()
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            distribution.safe_name(item.filename)
            assert item.filename.startswith(distribution.TOP + '/') and not item.is_dir()
            target = parent / item.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(item))
    return parent / distribution.TOP


def install_environment(root):
    uv = shutil.which('uv')
    assert uv is not None
    # All required packages were cached by the workflow's locked setup. Prove
    # that the extracted metadata can create its OWN venv, without network.
    result = subprocess.run([uv, 'sync', '--locked', '--offline', '--extra', 'postgres',
        '--python', sys.executable], cwd=root, env=clean_environment(),
        stdin=subprocess.DEVNULL, capture_output=True, timeout=120, text=True,
        encoding='utf-8', check=False, shell=False)
    if result.returncode:
        pytest.fail('extracted dependency installation failed: ' + result.stderr[-3000:])
    assert (root / '.venv/Scripts/python.exe').is_file()


_SCOPE_BINDING_PROBE = r'''
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from polymarket_alpha_lab.research_crypto_observation import _new_york
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, TeamResearchResult
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun
from polymarket_alpha_lab.research_capture_codec import encode_research_capture
z, _ = _new_york()
at = datetime(2026, 11, 1, 5, 30, tzinfo=UTC).astimezone(z)
raw = json.dumps(dict(slug='scope-fixture', conditionId='scope-fixture', question='Synthetic?',
    description='Synthetic fixture only.', active=True, closed=False, outcomes=['Yes','No'],
    endDate=(at.astimezone(UTC)+timedelta(days=1)).isoformat())).encode()
ev = ResearchEvidence('s','crypto_eth','scope-fixture','Synthetic','Synthetic','synthetic:source',at)
i = prepare_team_research_from_gamma(GammaMarketSnapshot('scope-fixture',at,raw),
    task_id='scope-fixture',team_id='crypto_eth',condition_id='scope-fixture',as_of=at,evidence=(ev,))
r = TeamResearchResult(i.task_id,i.team_id,i.condition_id,i.market_slug,at,'failed','model_failed')
original = MarketTeamResearchRun(i,r)
for target in ('task','receipt','result'):
    def build(when):
        if target == 'task':
            return MarketTeamResearchRun(replace(i,task=replace(i.task,as_of=when)),r)
        if target == 'receipt':
            return MarketTeamResearchRun(replace(i,source_receipts=(replace(i.source_receipts[0],observed_at=when),)),r)
        return MarketTeamResearchRun(i,replace(r,as_of=when))
    valid = build(at.astimezone(UTC))
    def wire(run):
        return encode_research_capture(record_id='scope-fixture',model_id='not-called',protocol_version='fixture',run=run)
    assert wire(valid) == wire(original)
    try:
        build(at.replace(fold=1))
    except ValueError:
        pass
    else:
        raise AssertionError('different instant accepted')
print('packaged scope bindings: PASS; three edges, canonical wire retained, no model or DB')
'''

_DIAGNOSTIC_START = r'''
import json, pathlib, re, runpy, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / 'src'))
from polymarket_alpha_lab.project_postgres import files
original = files.subprocess.run

def safe(value):
    return re.sub(r'[a-fA-F0-9]{64}', '<redacted>', value or '').replace(str(root), '<project>').replace(root.as_posix(), '<project>')[-2500:]

def probe(args, **kwargs):
    result = original(args, **kwargs)
    name = pathlib.Path(args[0]).stem
    if result.returncode not in (0, 3) and name in ('postgres', 'initdb', 'pg_ctl', 'psql', 'pg_controldata'):
        print(json.dumps({'program': name, 'exit': result.returncode, 'stdout': safe(result.stdout), 'stderr': safe(result.stderr)}), file=sys.stderr)
    return result
files.subprocess.run = probe
sys.argv = [str(root / 'scripts/start_project.py'), *sys.argv[2:]]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


def start(root, *args, expected=0):
    # The wrapper only diagnoses failed child commands in this synthetic project;
    # it runs the packaged entry point unchanged and never prints SQL/stdin/argv.
    result = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-I', '-c', _DIAGNOSTIC_START, str(root), *args],
        env=clean_environment(), stdin=subprocess.DEVNULL, capture_output=True,
        timeout=240, text=True, encoding='utf-8', check=False, shell=False)
    # Production startup emits only fixed public codes, never child stderr/DSNs.
    if result.returncode != expected:
        pytest.fail(f'startup exit={result.returncode}; stdout={result.stdout}; stderr={result.stderr}')
    return json.loads(result.stdout if expected == 0 else result.stderr)


class Model:
    def __init__(self): self.calls = 0
    def complete(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            name, args = 'read_evidence', {'source_id': 's'}
        else:
            name, args = 'finish_research', dict(probability_yes='0.6', confidence='0.2',
                summary='Synthetic distribution acceptance only.', source_ids=['s'])
        return ResearchModelReply((ResearchToolCall(f'c-{self.calls}', name, json.dumps(args)),), 1)


def request():
    now = datetime.now(UTC)
    snapshot = GammaMarketSnapshot('kit-fixture', now, json.dumps(dict(slug='kit-fixture',
        conditionId='kit-condition', question='Synthetic?', description='Synthetic criterion',
        outcomes=['Yes', 'No'], active=True, closed=False, endDate=(now + timedelta(days=1)).isoformat())).encode())
    evidence = ResearchEvidence('s', 'crypto_eth', 'kit-condition', 'Synthetic source',
        'Synthetic text', 'synthetic:kit-proof', now)
    intake = prepare_team_research_from_gamma(snapshot, task_id='kit-task', team_id='crypto_eth',
        condition_id='kit-condition', as_of=now, evidence=(evidence,))
    return CapturedResearchRequest('kit-record', 'synthetic-model', 'kit-proof-v1',
        now + timedelta(hours=1), intake, required_source_ids=('s',))


@pytest.mark.skipif(not ENABLED, reason='explicit native Windows distribution acceptance is opt-in')
def test_build_and_run_actual_relocatable_kit(monkeypatch):
    assert os.name == 'nt'
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    output = Path(os.environ['POLYMARKET_ALPHA_LAB_DISTRIBUTION_OUTPUT'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    proof = Path(os.environ['RUNNER_TEMP']) / ('pal-kit-' + uuid.uuid4().hex)
    private_directory(proof, create=True)
    print('native distribution: build clean committed source and native engine', flush=True)
    receipt = distribution.build_distribution(ROOT, prefix, output)
    print(json.dumps(receipt), flush=True)
    first = extract(output, proof / 'First Extraction With Spaces')
    second = extract(output, proof / 'Second Extraction With Spaces')
    for root in (first, second):
        distribution.verify_distribution(root)
        assert not (root / '.local').exists() and not (root / 'runtime').exists()
        assert not (root / '.env').exists() and not (root / '.git').exists()
        install_environment(root)
        # The shipped operator CLI is inert without public opt-in and needs no DB.
        cli = root / 'scripts/discover_crypto_research.py'
        assert cli.is_file() and (root / 'scripts/download_handoff.ps1').is_file()
        disabled = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-I', str(cli),
            '--team', 'crypto_btc', '--preview'], capture_output=True, text=True,
            encoding='utf-8', timeout=30, check=True, env=clean_environment())
        assert json.loads(disabled.stdout)['status'] == 'disabled'
        # The extracted package owns its timezone dependency; this must work on
        # Windows with no system IANA data and no source-worktree import fallback.
        probe = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-I', '-c',
            'from datetime import datetime; '
            'from polymarket_alpha_lab.research_crypto_observation import _new_york; '
            'z, version = _new_york(); '
            'assert datetime(2026, 1, 15, 12, tzinfo=z).utcoffset().total_seconds() == -18000; '
            'assert datetime(2026, 7, 15, 12, tzinfo=z).utcoffset().total_seconds() == -14400; '
            'print("packaged timezone:", version)'], capture_output=True, text=True,
            encoding='utf-8', timeout=30, check=True, env=clean_environment())
        assert 'packaged timezone:' in probe.stdout
        binding = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-I', '-c',
            _SCOPE_BINDING_PROBE], capture_output=True, text=True, encoding='utf-8',
            timeout=30, check=True, env=clean_environment())
        assert 'packaged scope bindings: PASS' in binding.stdout
        assert not (root / '.local').exists()
    with zipfile.ZipFile(first / distribution.ENGINE) as seed:
        assert all(not name.lower().endswith(distribution.FONT_SUFFIXES) for name in seed.namelist())
        assert not any(name.startswith('pgsql/data/') for name in seed.namelist())
    print('native distribution: launch extracted code; import/init automatic', flush=True)
    created = start(first, '--port', str(port()))
    assert created['status'] == 'ready' and created['initialized_here'] is True
    assert created['recorded_attempts'] == 0 and created['live_model_called'] is False
    db = ProjectPostgres(first)
    credentials = sha256((db.layout.home / 'app.pgpass').read_bytes()).hexdigest()
    try:
        with db.session() as research:
            captured = research.run_research(request=request(), model_factory=lambda _: Model())
            assert captured.status == 'captured'
        repeated = start(first)
        assert repeated['initialized_here'] is False
        assert repeated['instance_id'] == created['instance_id'] and repeated['recorded_attempts'] == 1
        assert sha256((db.layout.home / 'app.pgpass').read_bytes()).hexdigest() == credentials
        assert db.status()['status'] == 'stopped'
        print('native distribution: same kit yields independent project database', flush=True)
        other = start(second, '--port', str(port()))
        assert other['recorded_attempts'] == 0 and other['instance_id'] != created['instance_id']
        other_db = ProjectPostgres(second)
        assert sha256((other_db.layout.home / 'app.pgpass').read_bytes()).hexdigest() != credentials
        assert other_db.status()['status'] == 'stopped'
        # A changed immutable package blocks without modifying stored research.
        target = first / 'src/polymarket_alpha_lab/local_postgres_dsn.py'
        original = target.read_bytes()
        target.write_bytes(original + b'\n# synthetic tamper probe\n')
        try:
            blocked = start(first, expected=1)
            assert blocked['reason_code'] == 'project_bundle_invalid_or_changed'
        finally:
            target.write_bytes(original)
        with db.session() as research:
            assert research.inspect(record_id='kit-record').record == captured.record
        assert start(first)['recorded_attempts'] == 1
    finally:
        db.down()
    print('native distribution: PASS; two fresh instances, restart retention, no models or Docker', flush=True)
