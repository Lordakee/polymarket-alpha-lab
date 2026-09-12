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


def start(root, *args, expected=0):
    result = subprocess.run([sys.executable, '-I', str(root / 'scripts/start_project.py'), *args],
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
