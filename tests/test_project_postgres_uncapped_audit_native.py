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
    from polymarket_alpha_lab.research_claude_profile import ClaudeExecProfile
    from polymarket_alpha_lab.research_process import ResearchProcessSpec
    from polymarket_alpha_lab.research_uncapped import UncappedResearchAuthorization
    from polymarket_alpha_lab.research_uncapped_audit import reply_fingerprint

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

    supplier_calls = []

    def forbidden_supplier():
        supplier_calls.append(True)
        raise AssertionError('api key supplier must not be invoked')

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
    if os.name == 'nt':
        parent = Path(os.environ['RUNNER_TEMP']) / ('pal-operator-'+uuid.uuid4().hex)
        files.private_directory(parent, create=True)
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
                                    endpoint_url='https://gateway.example.invalid')
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
        assert supplier_calls == []

        def invoke(observed, turn_id, control):
            return operator.run_claude_research_rotation(observed,
                reviewed_batches=batches, profile=profile, authorization=permission,
                api_key_supplier=forbidden_supplier, rotation_id='operator-rotation',
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
            assert built['api_key_supplier'] is forbidden_supplier
            assert built['profile'] == profile
            assert built['allow_process_start'] is True and built['allow_api_key_use'] is True
            assert 'model_budget_id' not in rotation
            assert rotation['allow_model_calls'] is True
            assert rotation['allow_uncapped_costs'] is True
            assert rotation['require_durable_audit'] is True
            assert rotation['batch_ids_to_run'] == ('operator-btc','operator-eth')
            assert (rotation['max_tasks'],rotation['max_workers']) == (2,1)
            assert supplier_calls == []

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
            assert supplier_calls == []
        assert restarted.status()['status'] == 'running'
        print('native operator assembly: PASS;two-team stop,restart,replay,new turn,'
              'two-record audit join,zero supplier,zero budget rows')
    finally:
        for handle in (restarted, db):
            if handle is not None and handle.layout.home.exists(): handle.down()
