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
