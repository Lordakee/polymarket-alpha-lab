"""Real 67->68 upgrade and immutable uncapped audit; only CI-owned synthetic data."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import uuid

import pytest

from polymarket_alpha_lab import research_uncapped_audit_store as store
from polymarket_alpha_lab.research_uncapped_audit import UncappedCallStart, UncappedCallOutcome
from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_dispatch import ResearchBatch
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from tests.test_project_postgres_dispatch_native import prepared
from tests.test_project_postgres_uncapped_native import authorization
from tests.test_team_research_cross_source import Model

ROOT = Path(__file__).resolve().parents[1]
TAIL = '20260919000000_research_uncapped_audit.sql'
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'
_CRASH = r'''
import os,sys
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
class Lost:
    def complete(self, **kw): os._exit(86)
with ProjectPostgres(Path(sys.argv[1])).session() as s:
    r=s.inspect_research_batch(batch_id='audit-crash').stored.batch.requests[0]
    p=s.inspect_uncapped_authorization(authorization_id='audit-crash-policy').authorization
    s.run_uncapped_research(request=r,authorization=p,model_factory=lambda _:Lost(),
        allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True)
raise SystemExit(99)
'''


def _stop_after_crash(db):
    # The crashed child left its own engine running. A new managed session
    # would borrow it, not stop it. Explicitly stop the CI-owned instance first
    # to test an actual engine restart without changing production ownership.
    assert db.status()['status'] == 'running'
    db.down()
    assert db.status()['status'] == 'stopped'


@pytest.mark.skipif(not ENABLED, reason='explicit native uncapped audit proof is opt-in')
def test_audited_uncapped_upgrade_calls_uncertainty_and_process_loss(tmp_path, monkeypatch):
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    parent = tmp_path
    if os.name == 'nt':
        parent = Path(os.environ['RUNNER_TEMP']) / ('pal-call-audit-'+uuid.uuid4().hex)
        files.private_directory(parent, create=True)
    root = parent / 'Audited Research With Spaces'; root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database', root/'database')
    shutil.copytree(ROOT/'supabase/migrations', root/'supabase/migrations')
    manifest_file = root/'database/migrations.lock.json'
    full = manifest_file.read_bytes(); manifest = json.loads(full)
    assert len(manifest['migrations']) == 68 and manifest['migrations'][-1]['name'] == TAIL
    (root/'supabase/migrations'/TAIL).unlink()
    manifest_file.write_text(json.dumps(dict(manifest, migrations=manifest['migrations'][:-1])))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
    import_runtime_directory(root,prefix); db = ProjectPostgres(root)
    entered = []
    def forbidden(_): pytest.fail('no second provider entry')
    class Counted(Model):
        def complete(self, **kw):
            entered.append('complete')
            return super().complete(**kw)
    try:
        assert db.initialize(port=port)['migrations_applied'] == 67
        with db.session() as s:
            old = s.run_research(request=prepared(6100),model_factory=lambda _:Model())
            assert old.record.run.research.status == 'completed'
        shutil.copyfile(ROOT/'supabase/migrations'/TAIL,root/'supabase/migrations'/TAIL)
        manifest_file.write_bytes(full)
        assert db.migrate()['migrations_applied'] == 1
        assert db.migrate()['migrations_applied'] == 0
        identity = db._state()
        originals = []
        with db.session() as s:
            assert s.inspect(record_id=old.request.record_id).record == old.record
            assert s.inspect_uncapped_calls(record_id=old.request.record_id).to_dict()['audit_coverage'] == 'no_audited_calls'
            requests = (prepared(6101,'crypto_btc'),prepared(6102,'crypto_eth'))
            p = authorization(requests,authorization_id='audited-two-teams')
            with pytest.raises(ValueError): s.create_uncapped_authorization(authorization=p)
            assert s.inspect_uncapped_authorization(authorization_id=p.authorization_id) is None
            with pytest.raises(ValueError):
                s.run_uncapped_research(request=requests[0],authorization=p,model_factory=forbidden,
                    allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True)
            assert s.inspect(record_id=requests[0].record_id) is None
            with ThreadPoolExecutor(max_workers=2) as pool:
                copies = list(pool.map(lambda _:s.create_uncapped_authorization(authorization=p,
                    allow_authorization_write=True),range(2)))
            assert copies[0] == copies[1]
            with pytest.raises(store.db.ResearchCaptureConflict):
                s.create_uncapped_authorization(authorization=replace(p,adapter_contract_sha256='f'*64),
                    allow_authorization_write=True)
            s.enqueue_research_batch(batch=ResearchBatch('audited-teams',requests),allow_queue_write=True)
            control = ResearchDispatchStop(); control.request_stop()
            stopped = s.run_research_batch(batch_id='audited-teams',model_factory=forbidden,allow_model_calls=True,
                uncapped_authorization=p,allow_uncapped_costs=True,require_durable_audit=True,stop=control)
            assert not stopped.attempts
            first = s.run_research_rotation(rotation_id='audit-rounds',turn_id='one',batch_ids_to_run=('audited-teams',),
                model_factory=lambda _:Counted(),allow_model_calls=True,uncapped_authorization=p,
                allow_uncapped_costs=True,require_durable_audit=True,max_tasks=1,max_workers=1)
            assert first.attempts[0].execution.record.run.research.status == 'completed'
            assert len(entered) == 3
        assert db.status()['status'] == 'stopped'
        with db.session() as s:
            assert s.inspect_uncapped_authorization(authorization_id=p.authorization_id) == copies[0]
            second = s.run_research_rotation(rotation_id='audit-rounds',turn_id='two',batch_ids_to_run=('audited-teams',),
                model_factory=lambda _:Counted(),allow_model_calls=True,uncapped_authorization=p,
                allow_uncapped_costs=True,require_durable_audit=True,max_tasks=1,max_workers=1)
            assert second.attempts[0].execution.record.run.research.status == 'completed'
            assert len(entered) == 6
            for r in requests:
                audit = s.inspect_uncapped_calls(record_id=r.record_id)
                info = audit.to_dict()
                assert info['started_call_count'] == info['validated_reply_count'] == 3
                assert info['unknown_usage_call_count'] == 0
                original = s.inspect(record_id=r.record_id)
                assert info['reported_tokens_known_subset'] == original.record.run.research.total_tokens
                assert info['actual_billed_micros'] is info['provider_submission_count'] is None
                assert s.run_uncapped_research(request=r,authorization=p,model_factory=forbidden,
                    allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True) == original
                originals.append((r,original,audit))
            assert db._psql(identity,'SELECT count(*) FROM research_capture.model_call_reservations;') == '0'
            # Concurrent identical original requests own only one execution.
            same = prepared(6103); sp = authorization((same,),authorization_id='duplicate-original')
            s.create_uncapped_authorization(authorization=sp,allow_authorization_write=True)
            before = len(entered)
            def invoke(_):
                return s.run_uncapped_research(request=same,authorization=sp,model_factory=lambda _:Counted(),
                    allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True)
            with ThreadPoolExecutor(max_workers=2) as pool:
                twins = list(pool.map(invoke,range(2)))
            assert len(entered)-before == 3
            assert s.inspect_uncapped_calls(record_id=same.record_id).to_dict()['started_call_count'] == 3
            assert any(t.record is not None for t in twins)
            # DB time rejects new expired permission; no existing record is altered.
            expired = replace(sp,authorization_id='expired',approved_at=sp.approved_at-timedelta(hours=2),
                              expires_at=sp.approved_at-timedelta(hours=1))
            with pytest.raises(RuntimeError):
                s.create_uncapped_authorization(authorization=expired,allow_authorization_write=True)
            assert s.inspect_uncapped_authorization(authorization_id='expired') is None
            # Actual COMMIT acknowledged to DB but lost at application boundary.
            transaction = store.db._local_transaction
            for i, target in enumerate((UncappedCallStart,UncappedCallOutcome)):
                r = prepared(6110+i); permission = authorization((r,),authorization_id='ack-'+str(i))
                s.create_uncapped_authorization(authorization=permission,allow_authorization_write=True)
                before = len(entered)
                def lost(dsn, operation, **kwargs):
                    result = transaction(dsn, operation, **kwargs)
                    if type(result) is target: raise RuntimeError('synthetic lost acknowledgement')
                    return result
                with monkeypatch.context() as patch:
                    patch.setattr(store.db,'_local_transaction',lost)
                    execution = s.run_uncapped_research(request=r,authorization=permission,model_factory=lambda _:Counted(),
                        allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True)
                assert execution.record.run.research.status == 'failed'
                assert len(entered)-before == i
                snap = s.inspect_uncapped_calls(record_id=r.record_id)
                assert len(snap.calls) == 1 and len(snap.outcomes) == i
                assert snap.to_dict()['calls'][0]['status'] == ('unknown' if i==0 else 'returned')
                assert s.run_uncapped_research(request=r,authorization=permission,model_factory=forbidden,
                    allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True).record == execution.record
            # Trigger-level append-only guarantees, even under the instance owner.
            for table in ('uncapped_authorizations','uncapped_call_starts','uncapped_call_outcomes'):
                for change in (f'DELETE FROM research_capture.{table};',f'TRUNCATE research_capture.{table};',
                               f'UPDATE research_capture.{table} SET paper_only=false;'):
                    with pytest.raises(files.ProjectDatabaseError): db._psql(identity,change)
            # Direct SQL cannot record a successful unknown/zero-usage outcome;
            # nor can another call start while its predecessor is unresolved.
            from polymarket_alpha_lab import research_execution_psycopg as execution_store
            raw = prepared(6118); rp = authorization((raw,),authorization_id='sql-guards')
            s.create_uncapped_authorization(authorization=rp,allow_authorization_write=True)
            owned, claim = s._call(execution_store._claim,request=raw)
            assert owned and claim.record is None
            rs = s._call(store._begin_call,authorization=rp,request=raw,call_number=1,
                         messages_json='[{}]',max_output_tokens=100)
            for token_sql,hash_sql in (('NULL','NULL'),('0',"'"+'a'*64+"'")):
                with pytest.raises(files.ProjectDatabaseError):
                    db._psql(identity,"INSERT INTO research_capture.uncapped_call_outcomes "
                        "(record_id,call_number,status,reported_total_tokens,reply_sha256) VALUES "
                        "('"+raw.record_id+"',1,'returned',"+token_sql+","+hash_sql+");")
            for number in (1,2):
                with pytest.raises(RuntimeError):
                    s._call(store._begin_call,authorization=rp,request=raw,call_number=number,
                            messages_json='[{}]',max_output_tokens=100)
            terminal = s._call(store._finish_call,start=rs,status='failed')
            assert terminal.reported_total_tokens is None
            assert s._call(store._finish_call,start=rs,status='failed') == terminal
            with pytest.raises(store.db.ResearchCaptureConflict):
                s._call(store._finish_call,start=rs,status='interrupted')
            assert s.inspect_uncapped_calls(record_id=raw.record_id).to_dict()['calls'][0]['status'] == 'failed'
            first_start = s.inspect_uncapped_calls(record_id=requests[0].record_id).calls[0]
            with pytest.raises(Exception):
                s._call(store._finish_call,start=first_start,status='returned',reply=None)
            assert db._psql(identity,'SELECT count(*) FROM project_private.migrations;') == '68'
            crash = prepared(6120); cp = authorization((crash,),authorization_id='audit-crash-policy')
            s.create_uncapped_authorization(authorization=cp,allow_authorization_write=True)
            s.enqueue_research_batch(batch=ResearchBatch('audit-crash',(crash,)),allow_queue_write=True)
        child = subprocess.run([sys.executable,'-c',_CRASH,str(root)],cwd=ROOT,env=files.clean_environment(),
            capture_output=True,timeout=60,check=False)
        assert child.returncode == 86 and child.stdout == child.stderr == b''
        _stop_after_crash(db)
        with db.session() as s:
            lost = s.inspect(record_id=crash.record_id)
            assert lost.status == 'incomplete' and lost.record is None
            unknown = s.inspect_uncapped_calls(record_id=crash.record_id)
            assert len(unknown.calls) == 1 and unknown.outcomes == ()
            assert unknown.to_dict()['unknown_usage_call_count'] == 1
            assert s.run_uncapped_research(request=crash,authorization=cp,model_factory=forbidden,
                allow_model_calls=True,allow_uncapped_costs=True,require_durable_audit=True) == lost
            for r,original,audit in originals:
                assert s.inspect(record_id=r.record_id) == original
                assert s.inspect_uncapped_calls(record_id=r.record_id) == audit
            assert s.inspect(record_id=old.request.record_id).record == old.record
            assert db._psql(identity,'SELECT count(*) FROM research_capture.model_call_reservations;') == '0'
        _prove_actual_process_transport(db, parent)
        _prove_claude_process_transport(db, parent)
        assert db.status()['status'] == 'stopped'
        print('native uncapped audit: PASS;67->68,immutable authorization,call-before-client,unknown ack/crash,no resend')
    finally:
        if db.layout.home.exists(): db.down()


def _prove_actual_process_transport(db, parent):
    """The same real audit database plus real synthetic processes, no provider."""
    from hashlib import sha256
    from polymarket_alpha_lab.research_codex_exec import CodexExecModel
    from polymarket_alpha_lab.research_codex_process import CodexProcessTransport
    from tests.test_research_process import spec as process_spec
    from tests.test_research_codex_exec import action, events, output
    executable = str(Path(sys.executable).resolve())
    image = (executable, sha256(Path(executable).read_bytes()).hexdigest())
    work = parent / 'Synthetic Process With Spaces'; work.mkdir()
    originals = []
    for number, team in enumerate(('crypto_btc', 'crypto_eth')):
        request = prepared(6140+number, team)
        permission = authorization((request,), authorization_id='actual-process-'+str(number))
        launches = []
        with db.session() as session:
            session.create_uncapped_authorization(authorization=permission, allow_authorization_write=True)
            def factory(actual_team):
                assert actual_team == team
                def prepare_command(incoming):
                    # Read through a separate real DB transaction before launch;
                    # the original start must already be visible/committed.
                    audit = session.inspect_uncapped_calls(record_id=request.record_id)
                    assert len(audit.calls) == len(launches)+1
                    assert len(audit.outcomes) == len(launches)
                    launches.append(incoming)
                    sources = request.required_source_ids
                    calls = ([action('read_evidence', {'source_id': sid}) for sid in sources]
                             if len(launches) == 1 else [action('finish_research', dict(
                                 probability_yes='0.6', confidence='0.5',
                                 summary='Synthetic subprocess research', source_ids=list(sources)))])
                    wire = output(events(calls)).stdout
                    command = 'import sys,json;json.loads(sys.stdin.buffer.read());sys.stdout.buffer.write('+repr(wire)+')'
                    return process_spec(image, work, command)
                return CodexExecModel(model_id=request.model_id, transport=CodexProcessTransport(
                    prepare_command=prepare_command, allow_process_start=True))
            result = session.run_uncapped_research(request=request, authorization=permission,
                model_factory=factory, allow_model_calls=True, allow_uncapped_costs=True, require_durable_audit=True)
            assert result.record.run.research.status == 'completed' and len(launches) == 2
            audit = session.inspect_uncapped_calls(record_id=request.record_id)
            assert audit.to_dict()['reported_tokens_known_subset'] == 240
            assert len(audit.calls) == len(audit.outcomes) == 2
            originals.append((request, permission, result, audit))
        assert db.status()['status'] == 'stopped'
    with db.session() as session:
        for request, permission, result, audit in originals:
            def forbidden(_): pytest.fail('replayed subprocess')
            replay = session.run_uncapped_research(request=request, authorization=permission,
                model_factory=forbidden, allow_model_calls=True, allow_uncapped_costs=True,
                require_durable_audit=True)
            assert result.status == 'captured' and replay.status == 'already_captured'
            # This is a new operation receipt over the SAME durable execution.
            # Compare every other field, not just the record or token count.
            assert replace(replay, status=result.status) == result
            assert session.inspect_uncapped_calls(record_id=request.record_id) == audit
    assert not list(work.iterdir())


def _prove_claude_process_transport(db, parent):
    """Original real DB + real synthetic process; NOT an official Claude CLI test."""
    from polymarket_alpha_lab.research_claude_exec import ClaudeProcessModel
    from tests.test_research_claude_exec import MODEL, action, envelope, wire, synthetic_spec
    work = parent / 'Claude Synthetic Work'; work.mkdir()
    originals = []
    for number, team in enumerate(('crypto_btc', 'crypto_eth')):
        for invalid in (False, True):
            request = replace(prepared(6200+number*2+int(invalid), team), model_id=MODEL)
            permission = authorization((request,), authorization_id='claude-native-'+str(number)+'-'+str(int(invalid)))
            launched = []
            with db.session() as session:
                session.create_uncapped_authorization(authorization=permission, allow_authorization_write=True)
                def factory(actual_team):
                    assert actual_team == team
                    def prepare_command(incoming):
                        audit = session.inspect_uncapped_calls(record_id=request.record_id)
                        assert len(audit.calls) == len(launched)+1
                        assert len(audit.outcomes) == len(launched)
                        launched.append(incoming)
                        calls = ([action('read_evidence', source_id=sid) for sid in request.required_source_ids]
                                 if len(launched) == 1 else [action('finish_research',
                                     probability_yes='0.6', confidence='0.5', summary='Synthetic Claude protocol',
                                     source_ids=list(request.required_source_ids))])
                        response = envelope(calls, num_turns=2 if invalid else 1)
                        return synthetic_spec(work, wire(response).stdout)
                    return ClaudeProcessModel(model_id=MODEL, prepare_command=prepare_command, allow_process_start=True)
                result = session.run_uncapped_research(request=request, authorization=permission,
                    model_factory=factory, allow_model_calls=True, allow_uncapped_costs=True, require_durable_audit=True)
                assert result.record.run.research.status == ('failed' if invalid else 'completed')
                audit = session.inspect_uncapped_calls(record_id=request.record_id)
                assert len(launched) == len(audit.calls) == len(audit.outcomes) == (1 if invalid else 2)
                assert audit.to_dict()['reported_tokens_known_subset'] == (None if invalid else 52)
                assert audit.to_dict()['actual_billed_micros'] is None
                originals.append((request, permission, result, audit))
            assert db.status()['status'] == 'stopped'
    with db.session() as session:
        for request, permission, original, audit in originals:
            def forbidden(_): pytest.fail('replayed Claude process')
            replay = session.run_uncapped_research(request=request, authorization=permission,
                model_factory=forbidden, allow_model_calls=True, allow_uncapped_costs=True, require_durable_audit=True)
            assert replay.status == 'already_captured'
            assert replace(replay, status=original.status) == original
            assert session.inspect_uncapped_calls(record_id=request.record_id) == audit
    assert not list(work.iterdir())


@pytest.mark.skipif(not ENABLED, reason='explicit native uncapped audit proof is opt-in')
def test_operator_assembly_native_two_team_stop_restart_replay_and_audit(tmp_path, monkeypatch):
    """Real operator assembly over one disposable native instance; synthetic factory.

    Reviewed BTC/ETH single-request batches, cooperative stop on BTC's final
    successful reply, real engine down/up restart, inert same-turn operator
    replay, an explicit new turn completing ETH, then a per-record audit join.
    No official binary, credential, process launch, or provider is involved.
    """
    from hashlib import sha256
    from polymarket_alpha_lab import research_claude_operator as operator
    from polymarket_alpha_lab.research_claude_profile import (
        ClaudeExecProfile, FiniteInMemoryApiKeySupplier,
    )
    from polymarket_alpha_lab.research_process import ResearchProcessSpec
    from polymarket_alpha_lab.research_uncapped import UncappedResearchAuthorization
    from polymarket_alpha_lab.research_uncapped_audit import reply_fingerprint
    from tests.test_research_process_linux import fixed_launch

    class ObservedSession:
        # Pass-through observer over the real session; no canned receipts.
        def __init__(self, real):
            self.real = real
            self.rotation_kwargs = []
            self.reports = []

        def __getattr__(self, name):
            return getattr(self.real, name)

        def run_research_rotation(self, **kwargs):
            self.rotation_kwargs.append(kwargs)
            report = self.real.run_research_rotation(**kwargs)
            self.reports.append(report)
            return report

    builder_calls = []
    factory_entries = []
    completions = []  # (team, ordinal, messages_json, max_output_tokens, reply)
    state = {'stop_after_btc': True, 'forbidden': False}

    def builder(**kwargs):
        builder_calls.append(kwargs)
        if state['forbidden']:
            # The operator reconstructs its inert factory before the rotation
            # runner recognizes the reserved turn; this returned factory must
            # never actually be entered.
            return lambda team_id: pytest.fail('forbidden replayed factory entered')
        stop, stop_after = kwargs['stop'], state['stop_after_btc']

        def factory(team_id):
            factory_entries.append(team_id)
            trigger = stop_after and team_id == 'crypto_btc'

            class Counted(Model):
                # A fresh Model subclass per executed request records the
                # exact team, ordinal, messages, output cap, and reply.
                def complete(self, *, messages_json, max_output_tokens):
                    reply = super().complete(messages_json=messages_json,
                                             max_output_tokens=max_output_tokens)
                    completions.append((team_id, self.calls, messages_json,
                                        max_output_tokens, reply))
                    # Cooperative stop AFTER the audited wrapper admitted the
                    # final finish_research call, immediately BEFORE returning
                    # the successful reply. A stop placed inside the factory
                    # would fail readmission and lose this exact result.
                    if trigger and self.calls == 3:
                        stop.request_stop()
                    return reply

            return Counted()

        return factory

    monkeypatch.setattr(operator, 'claude_profile_factory', builder)

    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    parent = tmp_path
    root = parent / 'Operator Assembly With Spaces'; root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database', root/'database')
    shutil.copytree(ROOT/'supabase/migrations', root/'supabase/migrations')
    assert len(json.loads((root/'database/migrations.lock.json').read_text())['migrations']) == 68
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
    import_runtime_directory(root,prefix); db = ProjectPostgres(root); restarted = None
    try:
        # (a) Real fixture: full 68-migration init and the first explicit up,
        # then the time-sensitive typed inputs (freshness starts at prepared()).
        assert db.initialize(port=port)['migrations_applied'] == 68
        assert db.up()['status'] == 'running'
        work = root/'Claude Synthetic Work'; work.mkdir()
        process = ResearchProcessSpec((str(work/'claude-native'),), str(work),
            (('HOME', str(work/'home')), ('CLAUDE_CONFIG_DIR', str(work/'config'))), 'b'*64, 15000)
        profile = ClaudeExecProfile(process=process,
                                    endpoint_url='https://gateway.example.invalid',
                                    linux_launch=fixed_launch())
        assert type(profile) is ClaudeExecProfile
        btc = replace(prepared(6300,'crypto_btc'), model_id=profile.model_id)
        eth = replace(prepared(6301,'crypto_eth'), model_id=profile.model_id)
        assert btc.max_start_delay_seconds == eth.max_start_delay_seconds == 300
        assert btc.forecast_cutoff_at == btc.intake.as_of+timedelta(minutes=10)
        assert eth.forecast_cutoff_at == eth.intake.as_of+timedelta(minutes=10)
        batches = (ResearchBatch('operator-btc',(btc,)), ResearchBatch('operator-eth',(eth,)))
        permission = authorization((btc,eth), authorization_id='operator-assembly-two-teams',
                                   adapter_contract_sha256=profile.contract_sha256)
        assert type(permission) is UncappedResearchAuthorization
        assert permission.model_id == profile.model_id
        assert permission.request_keys == ((btc.record_id,btc.content_sha256),
                                           (eth.record_id,eth.content_sha256))
        def silent_supplier(control):
            return FiniteInMemoryApiKeySupplier(stop=control,
                crypto_btc=('SYNTHETIC-BTC-SLOT',), crypto_eth=('SYNTHETIC-ETH-SLOT',))

        def invoke(observed, turn_id, control):
            return operator.run_claude_research_rotation(observed,
                reviewed_batches=batches, profile=profile, authorization=permission,
                api_key_supplier=silent_supplier(control), rotation_id='operator-rotation',
                turn_id=turn_id, stop=control, max_tasks=2, max_workers=1)

        def shared(result, observed, control):
            # Identity assertions hold within one invocation; cross-reads use equality.
            assert result.report is observed.reports[-1]
            rotation = observed.rotation_kwargs[-1]; built = builder_calls[-1]
            assert set(built) == {'profile','authorization','api_key_supplier',
                                  'allow_process_start','allow_api_key_use','stop'}
            assert (built['authorization'] is rotation['uncapped_authorization']
                    is result.authorization_receipt.authorization)
            assert built['stop'] is rotation['stop'] is control
            assert type(built['api_key_supplier']) is FiniteInMemoryApiKeySupplier
            assert built['api_key_supplier'].bound_stop_is(control)
            assert built['api_key_supplier'].remaining('crypto_btc') == 1
            assert built['api_key_supplier'].remaining('crypto_eth') == 1
            assert built['profile'] == profile
            assert built['allow_process_start'] is True and built['allow_api_key_use'] is True
            assert 'model_budget_id' not in rotation
            assert rotation['allow_model_calls'] is True
            assert rotation['allow_uncapped_costs'] is True
            assert rotation['require_durable_audit'] is True
            assert rotation['batch_ids_to_run'] == ('operator-btc','operator-eth')
            assert (rotation['max_tasks'],rotation['max_workers']) == (2,1)
            assert built['api_key_supplier'].remaining('crypto_btc') == 1
            assert built['api_key_supplier'].remaining('crypto_eth') == 1

        # (b) First operator turn: BTC completes; cooperative stop skips ETH.
        with db.session() as s:
            observed = ObservedSession(s)
            control = ResearchDispatchStop()
            first = invoke(observed,'turn-one',control)
            shared(first, observed, control)
            assert first.report.status == 'dispatched' and first.report.stop_requested is True
            turn = first.report.stored.turn
            assert turn.states == ('pending','pending') and turn.chosen == (0,1)
            assert turn.start_slot == turn.next_slot == 0
            assert len(first.report.attempts) == 1
            attempt = first.report.attempts[0]
            assert attempt.position == 0 and attempt.status == 'returned'
            btc_execution = attempt.execution
            research = btc_execution.record.run.research
            assert btc_execution.status == 'captured' and research.status == 'completed'
            assert research.model_calls == 3 and research.total_tokens == 30
            assert observed.inspect_research_batch(batch_id='operator-btc').states() == ('captured',)
            btc_stored = observed.inspect_research_batch(batch_id='operator-btc').stored
            eth_stored = observed.inspect_research_batch(batch_id='operator-eth').stored
            eth_snapshot = observed.inspect_research_batch(batch_id='operator-eth')
            assert eth_snapshot.states() == ('pending',) and eth_snapshot.executions == (None,)
            assert observed.inspect_uncapped_calls(record_id=eth.record_id).calls == ()
            assert observed.inspect_uncapped_calls(record_id=eth.record_id).outcomes == ()
            receipt = first.authorization_receipt
            assert observed.inspect_uncapped_authorization(
                authorization_id=permission.authorization_id) == receipt
            first_turn = first.report.stored
            btc_audit = observed.inspect_uncapped_calls(record_id=btc.record_id)
            assert factory_entries == ['crypto_btc']
            assert [(c[0],c[1]) for c in completions] == [('crypto_btc',n) for n in (1,2,3)]
            # Cumulative checkpoint after the first turn.
            assert (len(builder_calls),len(factory_entries),len(completions)) == (1,1,3)
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-one') == first_turn
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-two') is None
        # (c) A real stop and restart of the same disposable instance; all
        # lifecycle calls stay between session contexts (same layout lock).
        identity = db._state()
        assert db.status()['status'] == 'running'
        db.down()
        assert db.status()['status'] == 'stopped'
        restarted = ProjectPostgres(root)
        assert restarted._state() == identity
        resumed = restarted.up()
        assert resumed['status'] == 'running' and resumed['pending_migrations'] == 0
        with restarted.session() as s:
            observed = ObservedSession(s)
            assert observed.inspect_uncapped_authorization(
                authorization_id=permission.authorization_id) == receipt
            assert observed.inspect_research_batch(batch_id='operator-btc').stored == btc_stored
            assert observed.inspect_research_batch(batch_id='operator-eth').stored == eth_stored
            assert observed.inspect(record_id=btc.record_id).record == btc_execution.record
            assert observed.inspect_uncapped_calls(record_id=btc.record_id) == btc_audit
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-one') == first_turn
            # (d) Same-turn replay through the operator stays inert.
            state['forbidden'] = True
            replay_stop = ResearchDispatchStop()
            second = invoke(observed,'turn-one',replay_stop)
            shared(second, observed, replay_stop)
            assert second.report.status == 'turn_already_reserved'
            assert second.report.stored == first.report.stored and second.report.attempts == ()
            assert (len(builder_calls),len(factory_entries),len(completions)) == (2,1,3)
            assert observed.inspect_uncapped_authorization(
                authorization_id=permission.authorization_id) == receipt
            assert observed.inspect_research_batch(batch_id='operator-btc').stored == btc_stored
            assert observed.inspect_research_batch(batch_id='operator-eth').stored == eth_stored
            assert observed.inspect_research_batch(batch_id='operator-eth').executions == (None,)
            assert observed.inspect(record_id=btc.record_id).record == btc_execution.record
            assert observed.inspect_uncapped_calls(record_id=btc.record_id) == btc_audit
            assert observed.inspect_uncapped_calls(record_id=eth.record_id).calls == ()
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-one') == first_turn
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-two') is None
            # (e) An explicit new operator turn completes ETH.
            state['forbidden'] = False; state['stop_after_btc'] = False
            eth_stop = ResearchDispatchStop()
            third = invoke(observed,'turn-two',eth_stop)
            shared(third, observed, eth_stop)
            assert third.report.status == 'dispatched' and third.report.stop_requested is False
            second_turn = third.report.stored
            assert second_turn.turn.turn_number == 2
            assert second_turn.turn.start_slot == first_turn.turn.next_slot == 0
            assert second_turn.turn.states == ('captured','pending')
            assert second_turn.turn.chosen == (1,) and second_turn.turn.next_slot == 0
            assert len(third.report.attempts) == 1
            eth_attempt = third.report.attempts[0]
            assert eth_attempt.position == 1 and eth_attempt.status == 'returned'
            eth_execution = eth_attempt.execution
            eth_research = eth_execution.record.run.research
            assert eth_execution.status == 'captured' and eth_research.status == 'completed'
            assert eth_research.model_calls == 3 and eth_research.total_tokens == 30
            assert observed.inspect(record_id=btc.record_id).record == btc_execution.record
            assert observed.inspect_uncapped_calls(record_id=btc.record_id) == btc_audit
            for batch_id in ('operator-btc','operator-eth'):
                assert observed.inspect_research_batch(batch_id=batch_id).states() == ('captured',)
            btc_read = observed.inspect_research_batch(batch_id='operator-btc').stored.batch.requests[0]
            eth_read = observed.inspect_research_batch(batch_id='operator-eth').stored.batch.requests[0]
            assert (btc_read.payload,btc_read.content_sha256) == (btc.payload,btc.content_sha256)
            assert (eth_read.payload,eth_read.content_sha256) == (eth.payload,eth.content_sha256)
            assert observed.inspect_research_batch(batch_id='operator-btc').stored == btc_stored
            assert observed.inspect_research_batch(batch_id='operator-eth').stored == eth_stored
            eth_audit = observed.inspect_uncapped_calls(record_id=eth.record_id)
            assert factory_entries == ['crypto_btc','crypto_eth']
            assert [(c[0],c[1]) for c in completions] == (
                [('crypto_btc',n) for n in (1,2,3)]+[('crypto_eth',n) for n in (1,2,3)])
            # Cumulative checkpoint after the new turn.
            assert (len(builder_calls),len(factory_entries),len(completions)) == (3,2,6)
            # (f) Exhaustive reconciliation of both records and both turns.
            current_receipt = observed.inspect_uncapped_authorization(
                authorization_id=permission.authorization_id)
            assert (current_receipt == receipt == first.authorization_receipt
                    == second.authorization_receipt == third.authorization_receipt)
            bound = current_receipt.authorization
            assert bound.model_id == profile.model_id == btc.model_id == eth.model_id
            assert bound.adapter_contract_sha256 == profile.contract_sha256
            assert bound.request_keys == ((btc.record_id,btc.content_sha256),
                                          (eth.record_id,eth.content_sha256))
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-one') == first_turn
            assert observed.inspect_research_turn(
                rotation_id='operator-rotation',turn_id='turn-two') == second_turn
            assert first_turn.turn.roster == (('operator-btc',batches[0].content_sha256,1),
                                              ('operator-eth',batches[1].content_sha256,1))
            assert first_turn.turn.request_keys == bound.request_keys
            assert (first_turn.turn.max_tasks,first_turn.turn.max_workers) == (2,1)
            assert (second_turn.turn.max_tasks,second_turn.turn.max_workers) == (2,1)
            for stored_turn in (first_turn,second_turn):
                assert 'authorization_id' not in stored_turn.to_dict()
            for request, batch_id, stored, audit_original, execution in (
                    (btc,'operator-btc',btc_stored,btc_audit,btc_execution),
                    (eth,'operator-eth',eth_stored,eth_audit,eth_execution)):
                snapshot = observed.inspect_research_batch(batch_id=batch_id)
                assert snapshot.stored == stored
                assert snapshot.stored.batch.payload == stored.batch.payload
                assert snapshot.stored.batch.content_sha256 == stored.batch.content_sha256
                current = observed.inspect(record_id=request.record_id)
                assert current.status == 'already_captured'
                assert current.record == execution.record
                result = current.record.run.research
                assert result.status == 'completed'
                assert result.model_calls == 3 and result.total_tokens == 30
                audit = observed.inspect_uncapped_calls(record_id=request.record_id)
                assert audit == audit_original
                assert tuple(c.call_number for c in audit.calls) == (1,2,3)
                assert tuple(o.status for o in audit.outcomes) == ('returned',)*3
                recorded = [c for c in completions if c[0] == request.intake.team_id]
                assert [c[1] for c in recorded] == [1,2,3]
                outcomes = {o.start.call_number: o for o in audit.outcomes}
                for start, observation in zip(audit.calls,recorded):
                    _, ordinal, messages_json, output_cap, reply = observation
                    assert start.authorization_id == bound.authorization_id
                    assert start.authorization_sha256 == bound.content_sha256
                    assert start.record_id == request.record_id
                    assert start.request_sha256 == request.content_sha256
                    assert start.message_sha256 == sha256(messages_json.encode('utf-8')).hexdigest()
                    assert start.message_bytes == len(messages_json.encode('utf-8'))
                    assert start.max_output_tokens == output_cap
                    outcome = outcomes[ordinal]
                    assert outcome.start == start and outcome.status == 'returned'
                    assert outcome.reported_total_tokens == 10
                    assert outcome.reply_sha256 == reply_fingerprint(reply)[1]
                summary = audit.to_dict()
                assert summary['started_call_count'] == summary['validated_reply_count'] == 3
                assert summary['unknown_usage_call_count'] == 0
                assert summary['all_calls_have_terminal_record'] is True
                assert summary['reported_tokens_known_subset'] == 30
                assert summary['provider_submission_count'] is None
                assert summary['actual_billed_micros'] is None
                assert summary['monetary_cap'] is None
                assert summary['provider_usage_verified'] is False
                assert summary['paper_only'] is summary['report_only'] is summary['readonly'] is True
            authorization_summary = current_receipt.to_dict()
            assert authorization_summary['approval_identity_authenticated'] is False
            assert authorization_summary['no_monetary_cap_approved'] is True
            assert authorization_summary['research_data_send_approved'] is True
            assert authorization_summary['durable_authorization_record_created'] is True
            assert (authorization_summary['paper_only'] is authorization_summary['report_only']
                    is authorization_summary['readonly'] is True)
            evaluation = observed.evaluate()
            assert len(evaluation.records) == 2
            assert {r.record_id for r in evaluation.records} == {btc.record_id,eth.record_id}
            # (g) Global durable invariants; no monetary ledger anywhere.
            for statement, expected in (
                    ('SELECT count(*) FROM research_capture.execution_claims;','2'),
                    ('SELECT count(*) FROM research_capture.attempts;','2'),
                    ('SELECT count(*) FROM research_capture.outcomes;','0'),
                    ('SELECT count(*) FROM research_capture.dispatch_batches;','2'),
                    ('SELECT count(*) FROM research_capture.dispatch_turns;','2'),
                    ('SELECT count(*) FROM research_capture.uncapped_authorizations;','1'),
                    ('SELECT count(*) FROM research_capture.uncapped_call_starts;','6'),
                    ('SELECT count(*) FROM research_capture.uncapped_call_outcomes;','6'),
                    ('SELECT count(*) FROM research_capture.model_budgets;','0'),
                    ('SELECT count(*) FROM research_capture.model_call_reservations;','0'),
                    ('SELECT count(*) FROM project_private.migrations;','68')):
                # Business rows are counted as the application role;
                # project_private is owner-only (an app-role read fails).
                owner = not statement.startswith('SELECT count(*) FROM research_capture.')
                assert restarted._psql(identity,statement,owner=owner) == expected
        assert restarted.status()['status'] == 'running'
        print('native operator assembly: PASS;two-team stop,restart,replay,new turn,'
              'two-record audit join,zero supplier consumption,zero budget rows')
    finally:
        for handle in (restarted, db):
            if handle is not None and handle.layout.home.exists(): handle.down()


# ---------------------------------------------------------------------------
# Opt-in native contained-operator proofs: the plan's 2/2 finite-supplier
# scenario (real factory, real containment, real operator, real audit) and the
# driver-loss scenario. Both require the native PostgreSQL opt-in AND the
# Linux containment opt-in; missing prerequisites after an explicit opt-in are
# failures, never skips.
CONTAINMENT_ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT') == '1'


def _contained_request(number, team, condition=None):
    """A fresh single-request batch input like prepared(), with an optional
    custom condition id (the ETH block marker rides in the condition text)."""
    from datetime import UTC, datetime, timedelta
    from polymarket_alpha_lab.research_crypto_launch import CryptoResearchPreview, CryptoResearchSpec
    from tests.test_research_crypto_launch import snapshots
    at = datetime.now(UTC)
    name = condition or ('queued-' + str(number))
    spec = CryptoResearchSpec(name, team, '0x' + format(number, '064x'), name,
                              at + timedelta(minutes=10), 'claude-opus-5')
    market, candlesticks, klines = snapshots(spec, at)
    preview = CryptoResearchPreview(spec, at, at, market, candlesticks, klines)
    return preview.request(approved_terms_sha256=preview.to_dict()['terms_sha256'])


def _contained_native_fixture(parent, name):
    files.private_directory(parent)
    root = parent / name
    root.mkdir(parents=True, exist_ok=False)
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT / 'database', root / 'database')
    shutil.copytree(ROOT / 'supabase/migrations', root / 'supabase/migrations')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    return root, port


# ---------------------------------------------------------------------------
# Positively observed, test-owned PID/start-time cleanup evidence. A global
# /proc command-name scan (pgrep-style matching) cannot match the real launch
# shape: the supervisor is the sealed interpreter exec'd with the sealed
# helper payload, and the vendor tree is the sealed image exec'd through
# bwrap inside the per-call cgroup. These helpers never match names; they
# read /proc/<pid>/stat identities (start time, parent) plus the owned
# delegated cgroup subtree the run actually uses.
def _proc_stat(pid):
    """(ppid, starttime, state) from /proc/<pid>/stat, or None when absent.

    ``comm`` may contain spaces and parentheses, so fields are split after the
    LAST ')': with state (field 3) at index 0, ppid (4) is index 1 and
    starttime (22) is index 19.
    """
    try:
        data = Path('/proc/%d/stat' % pid).read_bytes()
    except OSError:
        return None
    try:
        fields = data[data.rindex(b')') + 2:].split()
        return int(fields[1]), int(fields[19]), fields[0].decode('ascii', 'replace')
    except (ValueError, IndexError):
        return None


def _thread_children(pid):
    """Every child PID of the process, unioned over its threads."""
    children = set()
    try:
        tasks = list(Path('/proc/%d/task' % pid).iterdir())
    except OSError:
        return children
    for entry in tasks:
        try:
            children.update(int(value)
                            for value in (entry / 'children').read_text().split())
        except (OSError, ValueError):
            continue
    return children


def _owned_allocations():
    """Live member identities per owned per-call allocation directory.

    Reads only the delegated cgroup root configured for this run
    (POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT, the pal.dev-style subtree the
    launcher creates its pal-call-* directories under). Returns
    {directory name: {member pid: (ppid, starttime, state)}}.
    """
    allocations = {}
    try:
        entries = list(Path(os.environ['POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT']).iterdir())
    except OSError:
        return allocations
    for entry in entries:
        if not entry.name.startswith('pal-call-'):
            continue
        members = {}
        try:
            for value in (entry / 'cgroup.procs').read_text().split():
                stat = _proc_stat(int(value))
                if stat is not None:
                    members[int(value)] = stat
        except (OSError, ValueError):
            continue
        allocations[entry.name] = members
    return allocations


class _DriverLossIdentities:
    """Test-owned identities captured for one driver-loss round.

    driver: the launched driver subprocess. supervisors: the driver children
    structurally identified as the parents of the live vendor-cgroup members
    (they live OUTSIDE the vendor cgroup and are verified separately from it).
    members: the vendor-cgroup member identities. allocations: the owned
    per-call cgroup directories holding exactly those members.
    """

    def __init__(self, driver_pid, supervisors, members, allocations):
        stat = _proc_stat(driver_pid)
        assert stat is not None, 'driver vanished before identity capture'
        self.driver_pid = driver_pid
        self.driver_starttime = stat[1]
        self.supervisors = dict(supervisors)   # pid -> starttime
        self.members = dict(members)           # pid -> starttime
        self.allocations = tuple(allocations)  # owned cgroup directory names

    def survivors(self):
        """Labels of recorded identities whose /proc entry still shows the
        SAME start time (a reused PID number does not count as survival)."""
        alive = []
        stat = _proc_stat(self.driver_pid)
        if stat is not None and stat[1] == self.driver_starttime:
            alive.append('driver-%d' % self.driver_pid)
        for kind, identities in (('supervisor', self.supervisors),
                                 ('member', self.members)):
            for pid, starttime in identities.items():
                current = _proc_stat(pid)
                if current is not None and current[1] == starttime:
                    alive.append('%s-%d' % (kind, pid))
        return alive


def _observe_driver_loss_identities(driver_pid, timeout=120):
    """Capture the live launch shape before the kill, by identity only.

    Polls until at least one owned pal-call-* allocation holds a live member
    whose host parent is a live driver child. The supervisor is bound
    STRUCTURALLY, never by name: it is that parent, it is itself NOT a member
    of the vendor cgroup, and it is a direct child of the driver. Allocations
    whose members belong to other parents (a concurrently running native test)
    are never captured. Fails the test when the shape never appears.
    """
    deadline = time.monotonic() + timeout
    detail = 'no live vendor-cgroup member was ever observed'
    while time.monotonic() < deadline:
        if _proc_stat(driver_pid) is None:
            pytest.fail('driver %d vanished before identity capture' % driver_pid)
        children = {pid: _proc_stat(pid) for pid in _thread_children(driver_pid)}
        children = {pid: stat for pid, stat in children.items() if stat is not None}
        live = {name: members for name, members in _owned_allocations().items()
                if members}
        if live:
            parents = {stat[0] for members in live.values()
                       for stat in members.values()}
            supervisors = parents & set(children)
            detail = ('members %s parents %s driver children %s'
                      % (sorted({pid for members in live.values() for pid in members}),
                         sorted(parents), sorted(children)))
            ours = {name: members for name, members in live.items()
                    if {stat[0] for stat in members.values()} & supervisors}
            if (supervisors and ours
                    and {pid for members in ours.values() for pid in members}.isdisjoint(supervisors)
                    and all(children[pid][0] == driver_pid for pid in supervisors)
                    and all(children[pid][2] != 'Z' for pid in supervisors)):
                observed = _DriverLossIdentities(
                    driver_pid,
                    {pid: children[pid][1] for pid in supervisors},
                    {pid: members[pid][1] for members in ours.values() for pid in members},
                    ours)
                # Positive pre-kill assertions: the expected members were
                # present, and every supervisor was alive, outside the vendor
                # cgroup, and a direct child of the launched driver.
                assert observed.members and observed.supervisors
                return observed
        time.sleep(0.1)
    pytest.fail('driver-loss identity capture never observed a live vendor '
                'cgroup member with a live supervisor parent (%s)' % detail)


def _verify_driver_loss_cleanup(observed, timeout=90):
    """After the kill, every recorded identity must be gone: the driver, each
    supervisor (verified SEPARATELY by its own PID identity because it lives
    outside the vendor cgroup), and each vendor-cgroup member. Each recorded
    owned allocation directory must also be gone: the supervisor's cleanup
    kills the cgroup, verifies it empty, then removes the directory."""
    deadline = time.monotonic() + timeout
    survivors = observed.survivors()
    while survivors and time.monotonic() < deadline:
        time.sleep(0.1)
        survivors = observed.survivors()
    assert not survivors, ('driver loss left processes alive by PID identity: %s'
                           % survivors)
    root = Path(os.environ['POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT'])
    leftover = [name for name in observed.allocations if (root / name).exists()]
    assert not leftover, 'driver loss left owned cgroup allocations behind: %s' % leftover


_DRIVER_LOSS_CODE = '''
import json, os, sys, time
sys.path.insert(0, sys.argv[6])
sys.path.insert(0, sys.argv[6] + '/src')
sys.path.insert(0, sys.argv[6] + '/tests')
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from polymarket_alpha_lab import research_process_linux as linux
from polymarket_alpha_lab import research_claude_operator as operator
from polymarket_alpha_lab.research_claude_profile import (
    ClaudeExecProfile, FiniteInMemoryApiKeySupplier,
)
from polymarket_alpha_lab.research_process import ResearchProcessSpec
from polymarket_alpha_lab.research_dispatch import ResearchBatch
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from tests.test_project_postgres_uncapped_audit_native import _contained_request
from tests.test_project_postgres_dispatch_native import prepared
from tests.test_project_postgres_uncapped_native import authorization

root, artifacts, work = (Path(sys.argv[index]) for index in (1, 2, 3))
vendor = artifacts / 'vendor' / 'pal-standin'
digest = __import__('hashlib').sha256(vendor.read_bytes()).hexdigest()
# Rebuild the EXACT launch the parent measured (serialized beside the
# marker) so the reconstructed profile digest matches the authorization.
data = json.loads(Path(sys.argv[7]).read_text(encoding='utf-8'))
launch = linux.LinuxLaunchSpec(
    wrapper=linux.LinuxArtifactPin(data['wrapper']['path'],
                                   data['wrapper']['sha256'],
                                   data['wrapper']['size_bytes']),
    helper_sha256=data['helper_sha256'],
    interpreter=linux.LinuxArtifactPin(data['interpreter']['path'],
                                       data['interpreter']['sha256'],
                                       data['interpreter']['size_bytes']),
    supervisor_python_home=data['supervisor_python_home'],
    runtime_files=tuple(
        linux.LinuxRuntimeFile(item['guest_path'], item['host_path'],
                               item['sha256'], item['size_bytes'])
        for item in data['runtime_files']),
    vendor_guest_path=data['vendor_guest_path'],
    helper_guest_path=data['helper_guest_path'],
    vendor_size_bytes=data['vendor_size_bytes'],
    expected_version_output=data['expected_version_output'],
    cgroup_root=data['cgroup_root'],
    scratch_size_bytes=data['scratch_size_bytes'],
    guest_tmp_size_bytes=data['guest_tmp_size_bytes'],
    memory_max_bytes=data['memory_max_bytes'],
    pids_max=data['pids_max'])
work.mkdir(parents=True, exist_ok=True)
profile = ClaudeExecProfile(
    process=ResearchProcessSpec((str(vendor),), str(work),
        (('HOME', str(work / 'host-home')), ('CLAUDE_CONFIG_DIR', str(work / 'host-config'))),
        digest, 600000),
    endpoint_url='https://gateway.example.invalid', linux_launch=launch)
scenario = json.loads(Path(sys.argv[8]).read_text(encoding='utf-8'))
def build(entry):
    if entry.get('prepared'):
        return replace(prepared(entry['number'], entry['team']), model_id=profile.model_id)
    return replace(_contained_request(entry['number'], entry['team'],
                                      condition=entry['condition']),
                   model_id=profile.model_id)
btc = build(scenario['btc'])
eth = build(scenario['eth'])
batches = (ResearchBatch(scenario['prefix'] + '-btc', (btc,)),
           ResearchBatch(scenario['prefix'] + '-eth', (eth,)))
permission = authorization((btc, eth), authorization_id=scenario['authorization_id'],
                           adapter_contract_sha256=profile.contract_sha256)
control = ResearchDispatchStop()
supplier = FiniteInMemoryApiKeySupplier(stop=control,
    crypto_btc=tuple('K-B%d' % n for n in range(3)),
    crypto_eth=tuple('K-E%d' % n for n in range(3)))
marker = Path(sys.argv[4])
marker.write_text(json.dumps({'btc': btc.record_id, 'eth': eth.record_id}))
with ProjectPostgres(root).session() as session:
    report = operator.run_claude_research_rotation(session,
        reviewed_batches=batches, profile=profile, authorization=permission,
        api_key_supplier=supplier, rotation_id=scenario['rotation_id'], turn_id='turn-one',
        stop=control, max_tasks=scenario['max_tasks'], max_workers=scenario['max_workers'])
raise SystemExit(0)
'''


@pytest.mark.skipif(not (ENABLED and CONTAINMENT_ENABLED),
                    reason='explicit native contained operator proof is opt-in')
def test_contained_operator_two_by_two_stop_restart_replay_and_audit(tmp_path, monkeypatch):
    """The plan's principal native synthetic scenario.

    Two single-request BTC/ETH batches at max_tasks=2/max_workers=2, one
    contained profile, one finite supplier and one stop token. A barrier proves
    both workers enter their first calls concurrently; ETH's first model
    process stays deliberately blocked; BTC completes and captures; a separate
    observer session verifies both facts; stop terminates ETH with one failed
    audit outcome; a real engine restart precedes the inert same-turn replay,
    an empty explicit new turn and a final counter comparison. The vendor is
    the compiled synthetic stand-in ELF: its outputs are fixture data, never
    official-image evidence.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from polymarket_alpha_lab import research_claude_operator as operator
    from polymarket_alpha_lab import research_process_linux as linux
    from polymarket_alpha_lab.research_claude_profile import (
        ClaudeExecProfile, FiniteInMemoryApiKeySupplier,
    )
    from polymarket_alpha_lab.research_process import ResearchProcessSpec
    from polymarket_alpha_lab.research_dispatch import ResearchBatch
    from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
    from tests.test_research_process_linux import (
        build_native_launch, require_native_containment,
    )
    require_native_containment()
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):
            monkeypatch.delenv(key)
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    root, port = _contained_native_fixture(tmp_path, 'Contained Two By Two')
    import_runtime_directory(root, prefix)
    artifacts = tmp_path / 'native'
    binary, digest, size, launch = build_native_launch(artifacts)
    work = root / 'Contained Work'
    work.mkdir()
    db = ProjectPostgres(root)
    restarted = None
    try:
        assert db.initialize(port=port)['migrations_applied'] == 68
        assert db.up()['status'] == 'running'
        profile = ClaudeExecProfile(
            process=ResearchProcessSpec(
                (binary,), str(work),
                (('HOME', str(work / 'host-home')),
                 ('CLAUDE_CONFIG_DIR', str(work / 'host-config'))),
                digest, 600000),
            endpoint_url='https://gateway.example.invalid', linux_launch=launch)
        btc = replace(prepared(6400, 'crypto_btc'), model_id=profile.model_id)
        eth = replace(_contained_request(6401, 'crypto_eth', condition='blocked-eth'),
                      model_id=profile.model_id)
        batches = (ResearchBatch('contained-btc', (btc,)),
                   ResearchBatch('contained-eth', (eth,)))
        permission = authorization((btc, eth), authorization_id='contained-2by2',
                                   adapter_contract_sha256=profile.contract_sha256)
        control = ResearchDispatchStop()
        supplier = FiniteInMemoryApiKeySupplier(
            stop=control, crypto_btc=tuple('K-B%d' % n for n in range(3)),
            crypto_eth=tuple('K-E%d' % n for n in range(3)))
        barrier = threading.Barrier(2)
        entries = {'count': 0}
        entry_lock = threading.Lock()
        original_prepare = ClaudeExecProfile.prepare

        def barrier_prepare(self, request, *, api_key):
            with entry_lock:
                first = entries['count'] < 2
                if first:
                    entries['count'] += 1
            if first:
                barrier.wait(timeout=120)
            return original_prepare(self, request, api_key=api_key)

        session_patch = pytest.MonkeyPatch()
        session_patch.setattr(ClaudeExecProfile, 'prepare', barrier_prepare)
        counters_before = linux.LINUX_PHASE_COUNTERS.snapshot()
        with db.session() as session:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    operator.run_claude_research_rotation, session,
                    reviewed_batches=batches, profile=profile, authorization=permission,
                    api_key_supplier=supplier, rotation_id='contained-rotation',
                    turn_id='turn-one', stop=control, max_tasks=2, max_workers=2)
                deadline = time.monotonic() + 600
                observed = False
                while time.monotonic() < deadline:
                    try:
                        # The research session serializes calls internally, so
                        # this thread can observe durably committed rows while
                        # the rotation worker runs through the same session.
                        btc_audit = session.inspect_uncapped_calls(
                            record_id=btc.record_id)
                        eth_audit = session.inspect_uncapped_calls(
                            record_id=eth.record_id)
                        btc_state = session.inspect(record_id=btc.record_id)
                        eth_state = session.inspect(record_id=eth.record_id)
                        if (btc_state.status == 'already_captured'
                                and btc_state.record.run.research.status == 'completed'
                                and len(btc_audit.calls) == 3
                                and len(btc_audit.outcomes) == 3
                                and len(eth_audit.calls) == 1
                                and eth_audit.outcomes == ()
                                and eth_state.status == 'incomplete'):
                            observed = True
                            break
                        if (btc_state.status == 'already_captured'
                                and btc_state.record.run.research.status != 'completed'):
                            pytest.fail('BTC captured unsuccessfully: '
                                        + str(btc_state.record.run.research.reason_code))
                    except Exception:
                        pass
                    time.sleep(0.25)
                if not observed:
                    failure = future.exception() if future.done() else None
                    detail = repr(failure) if failure else 'rotation still running'
                    pytest.fail('observer timeout; rotation state: ' + detail)
                control.request_stop()
                report = future.result(timeout=300)
        assert entries['count'] == 2, 'both workers did not enter their first calls'
        session_patch.undo()
        counters_after = linux.LINUX_PHASE_COUNTERS.snapshot()
        with db.session() as audit_probe:
            btc_calls = len(audit_probe.inspect_uncapped_calls(
                record_id=btc.record_id).calls)
            eth_calls = len(audit_probe.inspect_uncapped_calls(
                record_id=eth.record_id).calls)
        assert btc_calls == 3 and eth_calls == 1
        assert report.report.status == 'dispatched' and report.report.stop_requested is True
        attempts = {attempt.position: attempt for attempt in report.report.attempts}
        assert set(attempts) <= {0, 1}
        btc_research = attempts[0].execution.record.run.research
        assert attempts[0].status == 'returned'
        assert attempts[0].execution.status == 'captured'
        assert btc_research.status == 'completed' and btc_research.model_calls == 3
        eth_attempt = attempts[1]
        assert eth_attempt.status == 'returned'
        eth_research = eth_attempt.execution.record.run.research
        assert eth_attempt.execution.status == 'captured'
        assert eth_research.status == 'failed' and eth_research.model_calls == 1
        # The stand-in folds parallel reads into one reply, so the audited
        # model executions are BTC's two or three calls plus ETH's blocked
        # first call; every model execution always has one version execution.
        model_delta = (counters_after['model_executions']
                       - counters_before['model_executions'])
        assert (counters_after['version_executions']
                - counters_before['version_executions'] == model_delta)
        assert model_delta == btc_calls + len(eth_audit.calls)
        assert supplier.remaining('crypto_btc') == 0
        assert supplier.remaining('crypto_eth') == 2
        with db.session() as check:
            btc_audit = check.inspect_uncapped_calls(record_id=btc.record_id)
            eth_audit = check.inspect_uncapped_calls(record_id=eth.record_id)
            assert len(btc_audit.calls) == len(btc_audit.outcomes) == 3
            assert all(o.status == 'returned' for o in btc_audit.outcomes)
            btc_calls = len(btc_audit.calls)
            assert len(eth_audit.calls) == 1 and len(eth_audit.outcomes) == 1
            assert eth_audit.outcomes[0].status == 'failed'
            assert eth_audit.outcomes[0].reported_total_tokens is None
            stored_batches = tuple(check.inspect_research_batch(
                batch_id=batch_id).stored.batch
                for batch_id in ('contained-btc', 'contained-eth'))
            stored_authorization = check.inspect_uncapped_authorization(
                authorization_id=permission.authorization_id).authorization
        assert db.status()['status'] == 'running'
        db.down()
        assert db.status()['status'] == 'stopped'
        restarted = ProjectPostgres(root)
        assert restarted.up()['status'] == 'running'
        with restarted.session() as session:
            assert session.inspect(record_id=btc.record_id).record == attempts[0].execution.record
            assert session.inspect(record_id=eth.record_id).record == eth_attempt.execution.record
            # Inert same-turn replay with the exhausted supplier.
            replay_stop = ResearchDispatchStop()
            exhausted = FiniteInMemoryApiKeySupplier(stop=replay_stop,
                                                     crypto_btc=(), crypto_eth=())
            counters_replay_before = linux.LINUX_PHASE_COUNTERS.snapshot()
            replay = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=profile,
                authorization=stored_authorization, api_key_supplier=exhausted,
                rotation_id='contained-rotation', turn_id='turn-one',
                stop=replay_stop, max_tasks=2, max_workers=2)
            assert replay.report.status == 'turn_already_reserved'
            assert replay.report.attempts == ()
            assert linux.LINUX_PHASE_COUNTERS.snapshot() == counters_replay_before
            # An explicit second turn is empty: both tasks are already claimed.
            second = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=profile,
                authorization=stored_authorization, api_key_supplier=exhausted,
                rotation_id='contained-rotation', turn_id='turn-two',
                stop=replay_stop, max_tasks=2, max_workers=2)
            assert second.report.status == 'dispatched' and second.report.attempts == ()
            assert linux.LINUX_PHASE_COUNTERS.snapshot() == counters_replay_before
            final = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=profile,
                authorization=stored_authorization, api_key_supplier=exhausted,
                rotation_id='contained-rotation', turn_id='turn-one',
                stop=replay_stop, max_tasks=2, max_workers=2)
            assert final.report.status == 'turn_already_reserved'
            assert linux.LINUX_PHASE_COUNTERS.snapshot() == counters_replay_before
            assert session.inspect_uncapped_calls(record_id=btc.record_id) == btc_audit
            assert session.inspect_uncapped_calls(record_id=eth.record_id) == eth_audit
        assert restarted.status()['status'] == 'running'
        print('native contained 2/2: PASS;barrier,btc capture,eth blocked+stopped,'
              '4 slots/4 version/4 model/restart/replay inert,empty second turn')
    finally:
        for handle in (restarted, db):
            if handle is not None and handle.layout.home.exists():
                handle.down()


@pytest.mark.skipif(not (ENABLED and CONTAINMENT_ENABLED),
                    reason='explicit native contained operator proof is opt-in')
def test_contained_driver_loss_preserves_incomplete_claim_and_replays_inert(tmp_path,
                                                                            monkeypatch):
    """Kill the driver after BTC's capture and ETH's committed start and key
    release; supervisor cleanup must reap the contained tree, the ETH claim
    stays incomplete with no terminal outcome, and an inert same-turn replay
    from a fresh parent session adds nothing."""
    from polymarket_alpha_lab import research_process_linux as linux
    from polymarket_alpha_lab import research_claude_operator as operator
    from polymarket_alpha_lab.research_claude_profile import (
        ClaudeExecProfile, FiniteInMemoryApiKeySupplier,
    )
    from polymarket_alpha_lab.research_process import ResearchProcessSpec
    from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
    from tests.test_research_process_linux import (
        build_native_launch, require_native_containment,
    )
    require_native_containment()
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):
            monkeypatch.delenv(key)
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    root, port = _contained_native_fixture(tmp_path, 'Driver Loss')
    import_runtime_directory(root, prefix)
    artifacts = tmp_path / 'native'
    binary, digest, size, launch = build_native_launch(artifacts)
    work = root / 'Driver Loss Work'
    marker = tmp_path / 'driver-ids.json'
    launch_file = tmp_path / 'driver-launch.json'
    from dataclasses import asdict as _asdict
    launch_file.write_text(json.dumps(_asdict(launch)), encoding='utf-8')
    db = ProjectPostgres(root)
    driver = None
    try:
        assert db.initialize(port=port)['migrations_applied'] == 68
        assert db.up()['status'] == 'running'
        environment = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
                       'PYTHONPATH': (str(ROOT) + os.pathsep + str(ROOT / 'src')
                                      + os.pathsep + str(ROOT / 'tests')),
                       'PYTHONUTF8': '1',
                       'POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT': '1',
                       'POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT':
                           os.environ['POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT']}
        scenario = tmp_path / 'driver-scenario.json'
        scenario.write_text(json.dumps({
            'btc': {'number': 6500, 'team': 'crypto_btc', 'prepared': True},
            'eth': {'number': 6501, 'team': 'crypto_eth',
                    'condition': 'blocked-eth-driver-loss'},
            'prefix': 'driver-loss', 'authorization_id': 'contained-driver-loss',
            'rotation_id': 'driver-loss-rotation', 'max_tasks': 2, 'max_workers': 2,
        }), encoding='utf-8')
        driver = subprocess.Popen(
            [sys.executable, '-I', '-c', _DRIVER_LOSS_CODE,
             str(root), str(artifacts), str(work), str(marker), launch.wrapper.path, str(ROOT),
             str(launch_file), str(scenario)],
            cwd=str(tmp_path), env=environment, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
        deadline = time.monotonic() + 180
        while not marker.exists() and driver.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        if not marker.exists():
            driver.poll()
            tail = (driver.stderr.read() or b'')[-900:].decode('utf-8', 'replace')
            pytest.fail('driver did not reach its invocation (rc=%r): %s'
                        % (driver.returncode, tail))
        ids = json.loads(marker.read_text(encoding='utf-8'))
        btc_id, eth_id = ids['btc'], ids['eth']
        # The driver process holds the engine's session lease, so the trusted
        # observer reads committed rows directly over the validated local DSN
        # (the same construction the engine itself uses). Note that
        # research_capture.outcomes is the settlement table (keyed by
        # condition_id): execution completion lives in research_capture.attempts.
        import psycopg
        observer_dsn = db._dsn(db._state())
        def committed_starts(record_id):
            with psycopg.connect(observer_dsn, autocommit=True) as connection:
                starts = connection.execute(
                    'SELECT count(*) FROM research_capture.uncapped_call_starts '
                    'WHERE record_id = %s', (record_id,)).fetchone()[0]
                outcomes = connection.execute(
                    'SELECT count(*) FROM research_capture.uncapped_call_outcomes '
                    'WHERE record_id = %s', (record_id,)).fetchone()[0]
                return starts, outcomes
        def capture_status(record_id):
            with psycopg.connect(observer_dsn, autocommit=True) as connection:
                rows = connection.execute(
                    "SELECT payload::jsonb #>> '{run,research,status}' "
                    'FROM research_capture.attempts WHERE record_id = %s',
                    (record_id,)).fetchall()
                return [row[0] for row in rows]
        deadline = time.monotonic() + 480
        reached = False
        while time.monotonic() < deadline:
            if driver.poll() is not None:
                pytest.fail('driver exited early (rc=%r)' % driver.returncode)
            try:
                btc_starts, btc_outcomes = committed_starts(btc_id)
                eth_starts, eth_outcomes = committed_starts(eth_id)
                btc_attempts = capture_status(btc_id)
                eth_attempts = capture_status(eth_id)
                if eth_attempts or eth_outcomes:
                    pytest.fail('ETH became terminal before the kill '
                                '(starts/outcomes/attempts: %d/%d/%d)'
                                % (eth_starts, eth_outcomes, len(eth_attempts)))
                if (btc_attempts == ['completed'] and btc_starts == 3
                        and btc_outcomes == 3 and eth_starts == 1):
                    reached = True
                    break
            except Exception:
                pass
            time.sleep(0.25)
        if not reached:
            driver.poll()
            driver.kill()
            tail = ''
            try:
                tail = (driver.stderr.read() or b'')[-1200:].decode('utf-8', 'replace')
            except Exception:
                pass
            try:
                print('OBSERVER-STATE btc:', committed_starts(btc_id), 'eth:', committed_starts(eth_id))
            except Exception as error:
                print('OBSERVER-STATE-ERROR:', type(error).__name__, error)
            pytest.fail('observer never saw progress; driver rc=%r stderr tail: %s'
                        % (driver.returncode, tail))
        # Positively observed, test-owned identities BEFORE the kill: the
        # launched driver (PID + start time), the supervisor child(ren)
        # identified structurally as the parents of the live vendor-cgroup
        # members (they live outside the vendor cgroup), and those members
        # with their own start times inside the owned per-call allocations.
        observed = _observe_driver_loss_identities(driver.pid)
        driver.kill()
        driver.kill()
        driver.wait(timeout=15)
        # The supervisor notices the liveness-pipe EOF from its dead parent,
        # kills and empties its owned cgroup, removes the allocation, exits
        # and is reaped: every recorded PID identity and every recorded
        # allocation directory must be gone. No process-name scan remains.
        _verify_driver_loss_cleanup(observed)
        with db.session() as session:
            btc_stored = session.inspect_research_batch(batch_id='driver-loss-btc')
            eth_stored = session.inspect_research_batch(batch_id='driver-loss-eth')
            btc_record = session.inspect(record_id=btc_id)
            eth_state = session.inspect(record_id=eth_id)
            assert btc_record.status == 'already_captured'
            assert btc_record.record.run.research.status == 'completed'
            assert eth_state.status == 'incomplete' and eth_state.record is None
            eth_audit = session.inspect_uncapped_calls(record_id=eth_id)
            assert len(eth_audit.calls) == 1 and eth_audit.outcomes == ()
            assert eth_audit.to_dict()['unknown_usage_call_count'] == 1
            stored_authorization = session.inspect_uncapped_authorization(
                authorization_id='contained-driver-loss').authorization
            stored_batches = (btc_stored.stored.batch, eth_stored.stored.batch)
        # The parent reconstructs the identical profile digest from the same
        # measured artifacts, then replays inertly with an exhausted supplier.
        replay_profile = ClaudeExecProfile(
            process=ResearchProcessSpec(
                (binary,), str(work),
                (('HOME', str(work / 'host-home')),
                 ('CLAUDE_CONFIG_DIR', str(work / 'host-config'))),
                digest, 600000),
            endpoint_url='https://gateway.example.invalid', linux_launch=launch)
        assert replay_profile.contract_sha256 == stored_authorization.adapter_contract_sha256
        with db.session() as session:
            counters_before = linux.LINUX_PHASE_COUNTERS.snapshot()
            replay_stop = ResearchDispatchStop()
            replay = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=replay_profile,
                authorization=stored_authorization,
                api_key_supplier=FiniteInMemoryApiKeySupplier(stop=replay_stop),
                rotation_id='driver-loss-rotation', turn_id='turn-one',
                stop=replay_stop, max_tasks=2, max_workers=2)
            assert replay.report.status == 'turn_already_reserved'
            assert replay.report.attempts == ()
            assert linux.LINUX_PHASE_COUNTERS.snapshot() == counters_before
            assert session.inspect(record_id=eth_id) == eth_state
            assert session.inspect_uncapped_calls(record_id=eth_id) == eth_audit
            assert session.inspect(record_id=btc_id).record == btc_record.record
        assert db.status()['status'] == 'running'
        print('native driver loss: PASS;supervisor cleanup,incomplete claim preserved,'
              'no terminal outcome,inert replay from fresh parent session')
    finally:
        if driver is not None and driver.poll() is None:
            driver.kill()
            driver.wait(timeout=15)
        if db.layout.home.exists():
            db.down()


@pytest.mark.skipif(not (ENABLED and CONTAINMENT_ENABLED),
                    reason='explicit native contained operator proof is opt-in')
def test_contained_driver_loss_useful_recovery_fresh_parent_rounds(tmp_path, monkeypatch):
    """Driver loss mid-call, then USEFUL recovery work from fresh parents.

    Round one is LIMITED to one interrupted request: BTC's first contained
    call blocks, the driver is killed mid-call, and the supervisor (its own
    PID identity, outside the vendor cgroup) reaps the vendor tree and its
    owned allocation. BTC's claim stays permanently incomplete with no
    terminal outcome and one unknown-usage call; ETH's ORIGINAL request stays
    unclaimed. Fresh parent sessions then prove three things: the original
    turn replays inertly; a SEPARATE two-request BTC/ETH scenario ends in an
    ORDINARY, visible failure; and an explicit new turn of the ORIGINAL
    rotation completes ETH's original still-unclaimed request while BTC's
    incomplete state, identities, hashes and audits stay unchanged and no
    renewed call is made for the prior claim. The roster keeps the operator's
    exact BTC-then-ETH single-request batch shape.
    """
    from concurrent.futures import ThreadPoolExecutor
    from polymarket_alpha_lab import research_process_linux as linux
    from polymarket_alpha_lab import research_claude_operator as operator
    from polymarket_alpha_lab.research_claude_profile import (
        ClaudeExecProfile, FiniteInMemoryApiKeySupplier,
    )
    from polymarket_alpha_lab.research_process import ResearchProcessSpec
    from polymarket_alpha_lab.research_dispatch import ResearchBatch
    from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
    from tests.test_research_process_linux import (
        build_native_launch, require_native_containment,
    )
    require_native_containment()
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):
            monkeypatch.delenv(key)
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    root, port = _contained_native_fixture(tmp_path, 'Useful Recovery')
    import_runtime_directory(root, prefix)
    artifacts = tmp_path / 'native'
    binary, digest, size, launch = build_native_launch(artifacts)
    work = root / 'Useful Recovery Work'
    marker = tmp_path / 'recovery-ids.json'
    launch_file = tmp_path / 'recovery-launch.json'
    from dataclasses import asdict as _asdict
    launch_file.write_text(json.dumps(_asdict(launch)), encoding='utf-8')
    db = ProjectPostgres(root)
    driver = None
    try:
        assert db.initialize(port=port)['migrations_applied'] == 68
        assert db.up()['status'] == 'running'
        environment = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
                       'PYTHONPATH': (str(ROOT) + os.pathsep + str(ROOT / 'src')
                                      + os.pathsep + str(ROOT / 'tests')),
                       'PYTHONUTF8': '1',
                       'POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT': '1',
                       'POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT':
                           os.environ['POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT']}
        # Round one: the driver runs ONE turn limited to ONE request (BTC),
        # whose first contained model call blocks forever.
        scenario = tmp_path / 'recovery-scenario.json'
        scenario.write_text(json.dumps({
            # The block marker rides in the condition text; the team is still
            # crypto_btc. ETH's condition has no marker: its original request
            # is simply never claimed in this limited round.
            'btc': {'number': 6600, 'team': 'crypto_btc',
                    'condition': 'driver-loss-btc-blocked-eth'},
            'eth': {'number': 6601, 'team': 'crypto_eth',
                    'condition': 'recovery-eth-original'},
            'prefix': 'useful-recovery', 'authorization_id': 'useful-recovery-driver-loss',
            'rotation_id': 'useful-recovery', 'max_tasks': 1, 'max_workers': 1,
        }), encoding='utf-8')
        driver = subprocess.Popen(
            [sys.executable, '-I', '-c', _DRIVER_LOSS_CODE,
             str(root), str(artifacts), str(work), str(marker), launch.wrapper.path, str(ROOT),
             str(launch_file), str(scenario)],
            cwd=str(tmp_path), env=environment, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
        deadline = time.monotonic() + 180
        while not marker.exists() and driver.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        if not marker.exists():
            driver.poll()
            tail = (driver.stderr.read() or b'')[-900:].decode('utf-8', 'replace')
            pytest.fail('driver did not reach its invocation (rc=%r): %s'
                        % (driver.returncode, tail))
        ids = json.loads(marker.read_text(encoding='utf-8'))
        btc_id, eth_id = ids['btc'], ids['eth']
        # Same trusted committed-row observer as the driver-loss proof: the
        # driver holds the engine's session lease, so reads go over the
        # engine's own validated local DSN.
        import psycopg
        observer_dsn = db._dsn(db._state())

        def committed_counts(record_id):
            with psycopg.connect(observer_dsn, autocommit=True) as connection:
                starts = connection.execute(
                    'SELECT count(*) FROM research_capture.uncapped_call_starts '
                    'WHERE record_id = %s', (record_id,)).fetchone()[0]
                outcomes = connection.execute(
                    'SELECT count(*) FROM research_capture.uncapped_call_outcomes '
                    'WHERE record_id = %s', (record_id,)).fetchone()[0]
                return starts, outcomes

        def committed_attempts(record_id):
            with psycopg.connect(observer_dsn, autocommit=True) as connection:
                rows = connection.execute(
                    "SELECT payload::jsonb #>> '{run,research,status}' "
                    'FROM research_capture.attempts WHERE record_id = %s',
                    (record_id,)).fetchall()
                return [row[0] for row in rows]

        deadline = time.monotonic() + 480
        reached = False
        while time.monotonic() < deadline:
            if driver.poll() is not None:
                pytest.fail('driver exited early (rc=%r)' % driver.returncode)
            try:
                btc_starts, btc_outcomes = committed_counts(btc_id)
                eth_starts, eth_outcomes = committed_counts(eth_id)
                btc_attempts = committed_attempts(btc_id)
                if btc_attempts or btc_outcomes:
                    pytest.fail('BTC became terminal before the kill '
                                '(starts/outcomes/attempts: %d/%d/%d)'
                                % (btc_starts, btc_outcomes, len(btc_attempts)))
                if (btc_starts == 1 and eth_starts == 0 and eth_outcomes == 0):
                    reached = True
                    break
            except Exception:
                pass
            time.sleep(0.25)
        if not reached:
            driver.poll()
            driver.kill()
            tail = ''
            try:
                tail = (driver.stderr.read() or b'')[-1200:].decode('utf-8', 'replace')
            except Exception:
                pass
            try:
                print('OBSERVER-STATE btc:', committed_counts(btc_id),
                      'eth:', committed_counts(eth_id))
            except Exception as error:
                print('OBSERVER-STATE-ERROR:', type(error).__name__, error)
            pytest.fail('observer never saw the interrupted round; driver rc=%r '
                        'stderr tail: %s' % (driver.returncode, tail))
        observed = _observe_driver_loss_identities(driver.pid)
        driver.kill()
        driver.kill()
        driver.wait(timeout=15)
        _verify_driver_loss_cleanup(observed)
        # The parent reconstructs the identical profile digest from the same
        # measured artifacts; every later round reuses exactly this contract.
        replay_profile = ClaudeExecProfile(
            process=ResearchProcessSpec(
                (binary,), str(work),
                (('HOME', str(work / 'host-home')),
                 ('CLAUDE_CONFIG_DIR', str(work / 'host-config'))),
                digest, 600000),
            endpoint_url='https://gateway.example.invalid', linux_launch=launch)
        # Fresh parent: durable state after the kill.
        with db.session() as session:
            btc_stored = session.inspect_research_batch(batch_id='useful-recovery-btc')
            eth_stored = session.inspect_research_batch(batch_id='useful-recovery-eth')
            assert btc_stored.states() == ('incomplete',)
            assert eth_stored.states() == ('pending',)
            btc_state = session.inspect(record_id=btc_id)
            assert btc_state.status == 'incomplete' and btc_state.record is None
            btc_audit = session.inspect_uncapped_calls(record_id=btc_id)
            assert len(btc_audit.calls) == 1 and btc_audit.outcomes == ()
            interrupted = btc_audit.to_dict()
            # The interruption has NO terminal record at all; its single call
            # keeps unknown usage. (The ordinary-failure scenario below is
            # the contrast: terminal, still unknown usage.)
            assert interrupted['unknown_usage_call_count'] == 1
            assert interrupted['all_calls_have_terminal_record'] is False
            assert session.inspect_uncapped_calls(record_id=eth_id).calls == ()
            receipt = session.inspect_uncapped_authorization(
                authorization_id='useful-recovery-driver-loss')
            stored_authorization = receipt.authorization
            assert replay_profile.contract_sha256 == stored_authorization.adapter_contract_sha256
            stored_batches = (btc_stored.stored.batch, eth_stored.stored.batch)
            first_turn = session.inspect_research_turn(
                rotation_id='useful-recovery', turn_id='turn-one')
            assert first_turn.turn.chosen == (0,) and first_turn.turn.next_slot == 1
            assert first_turn.turn.max_tasks == first_turn.turn.max_workers == 1
        # Fresh parent: the original turn replays inertly, consuming nothing.
        with db.session() as session:
            replay_stop = ResearchDispatchStop()
            untouched = FiniteInMemoryApiKeySupplier(stop=replay_stop,
                crypto_btc=tuple('R-B%d' % n for n in range(3)),
                crypto_eth=tuple('R-E%d' % n for n in range(3)))
            counters_before = linux.LINUX_PHASE_COUNTERS.snapshot()
            replay = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=replay_profile,
                authorization=stored_authorization, api_key_supplier=untouched,
                rotation_id='useful-recovery', turn_id='turn-one',
                stop=replay_stop, max_tasks=1, max_workers=1)
            assert replay.report.status == 'turn_already_reserved'
            assert replay.report.attempts == ()
            assert linux.LINUX_PHASE_COUNTERS.snapshot() == counters_before
            assert untouched.remaining('crypto_btc') == untouched.remaining('crypto_eth') == 3
            assert session.inspect(record_id=btc_id) == btc_state
            assert session.inspect_uncapped_calls(record_id=btc_id) == btc_audit
            assert session.inspect_uncapped_calls(record_id=eth_id).calls == ()
        # Fresh parent: a SEPARATE two-request scenario whose visible ending
        # is an ORDINARY failure - BTC completes, ETH's first call blocks and
        # a cooperative stop finishes it with a terminal failed outcome.
        btc2 = replace(_contained_request(6602, 'crypto_btc', condition='ordinary-btc'),
                       model_id=replay_profile.model_id)
        eth2 = replace(_contained_request(6603, 'crypto_eth',
                                          condition='ordinary-eth-blocked-eth'),
                       model_id=replay_profile.model_id)
        ordinary_batches = (ResearchBatch('ordinary-btc', (btc2,)),
                            ResearchBatch('ordinary-eth', (eth2,)))
        ordinary_permission = authorization(
            (btc2, eth2), authorization_id='useful-recovery-ordinary',
            adapter_contract_sha256=replay_profile.contract_sha256)
        with db.session() as session:
            control = ResearchDispatchStop()
            supplier = FiniteInMemoryApiKeySupplier(stop=control,
                crypto_btc=tuple('O-B%d' % n for n in range(3)),
                crypto_eth=tuple('O-E%d' % n for n in range(3)))
            counters_before = linux.LINUX_PHASE_COUNTERS.snapshot()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(operator.run_claude_research_rotation, session,
                    reviewed_batches=ordinary_batches, profile=replay_profile,
                    authorization=ordinary_permission, api_key_supplier=supplier,
                    rotation_id='useful-recovery-ordinary', turn_id='turn-one',
                    stop=control, max_tasks=2, max_workers=2)
                deadline = time.monotonic() + 600
                blocked = False
                while time.monotonic() < deadline:
                    if future.done():
                        pytest.fail('ordinary rotation returned early: %r'
                                    % future.exception())
                    try:
                        btc2_state = session.inspect(record_id=btc2.record_id)
                        if (btc2_state.status == 'already_captured'
                                and btc2_state.record.run.research.status != 'completed'):
                            pytest.fail('ordinary BTC captured unsuccessfully: %r'
                                        % btc2_state.record.run.research.reason_code)
                        btc2_calls = session.inspect_uncapped_calls(record_id=btc2.record_id)
                        eth2_calls = session.inspect_uncapped_calls(record_id=eth2.record_id)
                        if (btc2_state.status == 'already_captured'
                                and btc2_state.record.run.research.status == 'completed'
                                and len(btc2_calls.calls) == len(btc2_calls.outcomes) == 3
                                and len(eth2_calls.calls) == 1
                                and eth2_calls.outcomes == ()):
                            blocked = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.25)
                assert blocked, 'ordinary scenario never reached BTC complete + ETH blocked'
                control.request_stop()
                ordinary = future.result(timeout=300)
            assert ordinary.report.status == 'dispatched'
            assert ordinary.report.stop_requested is True
            attempts = {attempt.position: attempt for attempt in ordinary.report.attempts}
            assert set(attempts) == {0, 1}
            assert attempts[0].status == 'returned'
            assert attempts[0].execution.status == 'captured'
            assert attempts[0].execution.record.run.research.status == 'completed'
            assert attempts[1].status == 'returned'
            assert attempts[1].execution.status == 'captured'
            eth2_research = attempts[1].execution.record.run.research
            assert eth2_research.status == 'failed' and eth2_research.model_calls == 1
            btc2_audit = session.inspect_uncapped_calls(record_id=btc2.record_id)
            eth2_audit = session.inspect_uncapped_calls(record_id=eth2.record_id)
            assert len(btc2_audit.calls) == len(btc2_audit.outcomes) == 3
            assert all(outcome.status == 'returned' for outcome in btc2_audit.outcomes)
            assert len(eth2_audit.calls) == 1 and len(eth2_audit.outcomes) == 1
            assert eth2_audit.outcomes[0].status == 'failed'
            assert eth2_audit.outcomes[0].reported_total_tokens is None
            summary = eth2_audit.to_dict()
            # An ordinary failure is TERMINAL and visible - every call has a
            # terminal record, unlike the interruption - while the stopped
            # call's usage stays honestly unknown: the killed vendor reported
            # no provider usage for it.
            assert summary['all_calls_have_terminal_record'] is True
            assert summary['unknown_usage_call_count'] == 1
            assert summary['reported_tokens_known_subset'] is None
            assert supplier.remaining('crypto_btc') == 0
            assert supplier.remaining('crypto_eth') == 2
            counters_after = linux.LINUX_PHASE_COUNTERS.snapshot()
            assert (counters_after['model_executions']
                    - counters_before['model_executions'] == 4)
            assert (counters_after['version_executions']
                    - counters_before['version_executions'] == 4)
            # The interrupted rotation was untouched by the ordinary scenario.
            assert session.inspect(record_id=btc_id) == btc_state
            assert session.inspect_uncapped_calls(record_id=btc_id) == btc_audit
            assert session.inspect_uncapped_calls(record_id=eth_id).calls == ()
        # Fresh parent: an explicit new turn completes ETH's ORIGINAL
        # still-unclaimed request; the prior incomplete claim is never renewed.
        with db.session() as session:
            control = ResearchDispatchStop()
            supplier = FiniteInMemoryApiKeySupplier(stop=control,
                crypto_btc=tuple('S-B%d' % n for n in range(3)),
                crypto_eth=tuple('S-E%d' % n for n in range(3)))
            counters_before = linux.LINUX_PHASE_COUNTERS.snapshot()
            recovered = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=replay_profile,
                authorization=stored_authorization, api_key_supplier=supplier,
                rotation_id='useful-recovery', turn_id='turn-two',
                stop=control, max_tasks=1, max_workers=1)
            assert recovered.report.status == 'dispatched'
            assert recovered.report.stop_requested is False
            second_turn = recovered.report.stored
            assert second_turn.turn.turn_number == 2
            assert second_turn.turn.start_slot == first_turn.turn.next_slot == 1
            assert second_turn.turn.chosen == (1,) and second_turn.turn.next_slot == 0
            assert len(recovered.report.attempts) == 1
            attempt = recovered.report.attempts[0]
            assert attempt.position == 1 and attempt.status == 'returned'
            eth_execution = attempt.execution
            assert eth_execution.status == 'captured'
            assert eth_execution.request.record_id == eth_id
            eth_research = eth_execution.record.run.research
            assert eth_research.status == 'completed'
            assert eth_research.model_calls == 3 and eth_research.total_tokens == 78
            eth_audit = session.inspect_uncapped_calls(record_id=eth_id)
            assert len(eth_audit.calls) == len(eth_audit.outcomes) == 3
            assert tuple(outcome.status for outcome in eth_audit.outcomes) == ('returned',) * 3
            summary = eth_audit.to_dict()
            assert summary['started_call_count'] == summary['validated_reply_count'] == 3
            assert summary['unknown_usage_call_count'] == 0
            assert summary['reported_tokens_known_subset'] == 78
            # No renewed call for the prior claim: BTC's audit and state are
            # unchanged and BTC's fresh supplier slots were never consumed.
            assert session.inspect(record_id=btc_id) == btc_state
            assert session.inspect_uncapped_calls(record_id=btc_id) == btc_audit
            assert supplier.remaining('crypto_btc') == 3
            assert supplier.remaining('crypto_eth') == 0
            counters_after = linux.LINUX_PHASE_COUNTERS.snapshot()
            assert (counters_after['model_executions']
                    - counters_before['model_executions'] == 3)
            assert (counters_after['version_executions']
                    - counters_before['version_executions'] == 3)
        # Fresh parent: final inert original-turn replay and full durable
        # reconciliation of identities, hashes, audits and global counts.
        with db.session() as session:
            final_stop = ResearchDispatchStop()
            counters_before = linux.LINUX_PHASE_COUNTERS.snapshot()
            final = operator.run_claude_research_rotation(
                session, reviewed_batches=stored_batches, profile=replay_profile,
                authorization=stored_authorization,
                api_key_supplier=FiniteInMemoryApiKeySupplier(stop=final_stop),
                rotation_id='useful-recovery', turn_id='turn-one',
                stop=final_stop, max_tasks=1, max_workers=1)
            assert final.report.status == 'turn_already_reserved'
            assert final.report.attempts == ()
            assert linux.LINUX_PHASE_COUNTERS.snapshot() == counters_before
            btc_after = session.inspect_research_batch(batch_id='useful-recovery-btc')
            eth_after = session.inspect_research_batch(batch_id='useful-recovery-eth')
            assert btc_after.stored == btc_stored.stored
            assert eth_after.stored == eth_stored.stored
            stored_btc = btc_after.stored.batch.requests[0]
            stored_eth = eth_after.stored.batch.requests[0]
            # The recovered execution was the ORIGINAL request: same record
            # ids and content hashes as the round-one reservation.
            assert first_turn.turn.request_keys == (
                (stored_btc.record_id, stored_btc.content_sha256),
                (stored_eth.record_id, stored_eth.content_sha256))
            assert eth_execution.request.content_sha256 == stored_eth.content_sha256
            assert session.inspect_uncapped_authorization(
                authorization_id='useful-recovery-driver-loss') == receipt
            assert session.inspect_research_turn(
                rotation_id='useful-recovery', turn_id='turn-one') == first_turn
            assert session.inspect(record_id=btc_id) == btc_state
            assert session.inspect_uncapped_calls(record_id=btc_id) == btc_audit
            assert session.inspect_uncapped_calls(record_id=eth_id) == eth_audit
        identity = db._state()
        for statement, expected in (
                ('SELECT count(*) FROM research_capture.execution_claims;','4'),
                ('SELECT count(*) FROM research_capture.attempts;','3'),
                ('SELECT count(*) FROM research_capture.outcomes;','0'),
                ('SELECT count(*) FROM research_capture.dispatch_batches;','4'),
                ('SELECT count(*) FROM research_capture.dispatch_turns;','3'),
                ('SELECT count(*) FROM research_capture.uncapped_authorizations;','2'),
                ('SELECT count(*) FROM research_capture.uncapped_call_starts;','8'),
                ('SELECT count(*) FROM research_capture.uncapped_call_outcomes;','7'),
                ('SELECT count(*) FROM research_capture.model_budgets;','0'),
                ('SELECT count(*) FROM research_capture.model_call_reservations;','0'),
                ('SELECT count(*) FROM project_private.migrations;','68')):
            # Business rows are counted as the application role;
            # project_private is owner-only (an app-role read fails).
            owner = not statement.startswith('SELECT count(*) FROM research_capture.')
            assert db._psql(identity, statement, owner=owner) == expected
        assert db.status()['status'] == 'running'
        print('native useful recovery: PASS;identity cleanup,one interrupted claim kept,'
              'inert replay,ordinary visible failure,new turn completes original request,'
              'no renewed calls,unchanged audits')
    finally:
        if driver is not None and driver.poll() is None:
            driver.kill()
            driver.wait(timeout=15)
        if db.layout.home.exists():
            db.down()
