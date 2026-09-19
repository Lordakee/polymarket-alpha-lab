"""Original real DB claims with explicit uncapped permission and synthetic Codex events.

No actual Codex process/provider, user cluster, credential discovery or new SQL.
"""
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
from threading import Lock
import uuid

import pytest

from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_codex_exec import CodexExecModel, CodexExecOutput
from polymarket_alpha_lab.research_dispatch import ResearchBatch
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_uncapped import UncappedResearchAuthorization
from tests.test_project_postgres_dispatch_native import prepared
from tests.test_team_research_cross_source import Model

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'


def authorization(requests, **kw):
    now = datetime.now(UTC)
    values = dict(authorization_id='synthetic-no-cap', model_id=requests[0].model_id,
        adapter_contract_sha256='a'*64, approved_at=now, expires_at=now+timedelta(hours=1),
        request_keys=tuple((r.record_id, r.content_sha256) for r in requests),
        no_monetary_cap_approved=True, research_data_send_approved=True)
    values.update(kw)
    return UncappedResearchAuthorization(**values)


class SyntheticExec:
    def __init__(self, counts, lock):
        self.original, self.counts, self.lock = Model(), counts, lock

    def run(self, request):
        with self.lock: self.counts.append('operation')
        original = self.original.complete(messages_json=request.messages_json,
                                           max_output_tokens=request.max_output_tokens)
        # Exercise the real adapter without executing another model or CLI.
        actions = [{'name': c.name, 'arguments_json': c.arguments_json} for c in original.calls]
        events = [dict(type='thread.started', thread_id=str(uuid.uuid4())), dict(type='turn.started'),
            dict(type='item.completed', item=dict(id='item_0', type='agent_message',
                 text=json.dumps(dict(calls=actions)))),
            dict(type='turn.completed', usage=dict(input_tokens=10, cached_input_tokens=2,
                 cache_write_input_tokens=0, output_tokens=5, reasoning_output_tokens=1))]
        return CodexExecOutput(0, ('\n'.join(json.dumps(e) for e in events)+'\n').encode())


_CRASH = r'''
import os, sys
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from tests.test_project_postgres_uncapped_native import authorization
class Lost:
    def complete(self, **kwargs): os._exit(86)
with ProjectPostgres(Path(sys.argv[1])).session() as research:
    request = research.inspect_research_batch(batch_id='uncapped-crash').stored.batch.requests[0]
    research.run_uncapped_research(request=request, authorization=authorization((request,)),
        model_factory=lambda _:Lost(), allow_model_calls=True, allow_uncapped_costs=True)
raise SystemExit(99)
'''


@pytest.mark.skipif(not ENABLED, reason='explicit native uncapped execution proof is opt-in')
def test_uncapped_claims_codex_protocol_stop_restart_and_process_loss(tmp_path, monkeypatch):
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    parent = tmp_path
    if os.name == 'nt':
        parent = Path(os.environ['RUNNER_TEMP']) / ('pal-uncapped-'+uuid.uuid4().hex)
        files.private_directory(parent, create=True)
    root = parent / 'Uncapped Research With Spaces'; root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database', root/'database')
    shutil.copytree(ROOT/'supabase/migrations', root/'supabase/migrations')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    import_runtime_directory(root, prefix); db = ProjectPostgres(root)
    calls, made, lock = [], [], Lock()
    def factory(team):
        with lock: made.append(team)
        return CodexExecModel(model_id='synthetic-function-model', transport=SyntheticExec(calls, lock))
    def forbidden(_): pytest.fail('original history must not start another model')
    try:
        assert db.initialize(port=port)['migrations_applied'] == 68
        identity = db._state()
        with db.session() as research:
            prior = research.run_research(request=prepared(1900), model_factory=lambda _:Model())
            requests = (prepared(1901, 'crypto_btc'), prepared(1902, 'crypto_eth'))
            policy = authorization(requests)
            with pytest.raises(ValueError):
                research.run_uncapped_research(request=requests[0], authorization=policy,
                    model_factory=forbidden, allow_model_calls=True)
            assert research.inspect(record_id=requests[0].record_id) is None
            batch = ResearchBatch('uncapped-rounds', requests)
            saved = research.enqueue_research_batch(batch=batch, allow_queue_write=True)
            control = ResearchDispatchStop(); control.request_stop()
            stopped = research.run_research_batch(batch_id=batch.batch_id, model_factory=forbidden,
                allow_model_calls=True, uncapped_authorization=policy, allow_uncapped_costs=True, stop=control)
            assert not stopped.attempts
            first = research.run_research_rotation(rotation_id='uncapped-rotation', turn_id='first',
                batch_ids_to_run=(batch.batch_id,), model_factory=factory, allow_model_calls=True,
                uncapped_authorization=policy, allow_uncapped_costs=True, max_tasks=1, max_workers=1)
            original = first.attempts[0].execution
            assert original.record.run.research.status == 'completed' and len(calls) == 3
            assert original.record.run.research.total_tokens == 45
        assert db.status()['status'] == 'stopped'
        with db.session() as research:
            assert research.enqueue_research_batch(batch=batch, allow_queue_write=True) == saved
            second = research.run_research_rotation(rotation_id='uncapped-rotation', turn_id='second',
                batch_ids_to_run=(batch.batch_id,), model_factory=factory, allow_model_calls=True,
                uncapped_authorization=policy, allow_uncapped_costs=True, max_tasks=1, max_workers=1)
            assert second.attempts[0].execution.record.run.research.status == 'completed'
            assert len(calls) == 6 and made == ['crypto_btc', 'crypto_eth']
            repeat = research.run_research_rotation(rotation_id='uncapped-rotation', turn_id='first',
                batch_ids_to_run=(batch.batch_id,), model_factory=forbidden, allow_model_calls=True,
                uncapped_authorization=policy, allow_uncapped_costs=True, max_tasks=1, max_workers=1)
            assert repeat.status == 'turn_already_reserved' and len(calls) == 6
            expired = replace(policy, approved_at=policy.approved_at-timedelta(hours=2),
                               expires_at=policy.approved_at-timedelta(hours=1))
            replay = research.run_uncapped_research(request=requests[0], authorization=expired,
                model_factory=forbidden, allow_model_calls=True, allow_uncapped_costs=True)
            assert replay.record == original.record
            # Concurrent duplicate starts still use the ONE original DB claim.
            r = prepared(1903); p = authorization((r,)); before = len(calls)
            def invoke(_):
                return research.run_uncapped_research(request=r, authorization=p,
                    model_factory=factory, allow_model_calls=True, allow_uncapped_costs=True)
            with ThreadPoolExecutor(max_workers=4) as pool: results = list(pool.map(invoke, range(8)))
            assert len(calls)-before == 3
            assert all(x.status in ('captured', 'already_captured', 'incomplete') for x in results)
            assert research.inspect(record_id=r.record_id).record.run.research.status == 'completed'
            # Original legacy history and the capped ledger are unaffected.
            assert research.inspect(record_id=prior.request.record_id).record == prior.record
            for table in ('model_budgets', 'model_call_reservations'):
                assert db._psql(identity, f'SELECT count(*) FROM research_capture.{table};', owner=False) == '0'
            # A real mixed batch captures failure without retrying that task.
            mixed_requests = (prepared(1905, 'crypto_eth'), prepared(1906, 'crypto_btc'))
            mixed_policy = authorization(mixed_requests)
            failure_calls = []
            class FailedClient:
                def complete(self, **kwargs):
                    failure_calls.append(True)
                    raise TimeoutError('synthetic provider failure')
            def mixed_factory(team):
                return FailedClient() if team == 'crypto_eth' else factory(team)
            research.enqueue_research_batch(batch=ResearchBatch('uncapped-mixed', mixed_requests),
                                             allow_queue_write=True)
            mixed = research.run_research_batch(batch_id='uncapped-mixed', model_factory=mixed_factory,
                allow_model_calls=True, uncapped_authorization=mixed_policy, allow_uncapped_costs=True,
                max_tasks=2, max_workers=2)
            assert [a.execution.record.run.research.status for a in mixed.attempts] == ['failed', 'completed']
            failure = mixed.attempts[0].execution
            again = research.run_uncapped_research(request=mixed_requests[0], authorization=mixed_policy,
                model_factory=forbidden, allow_model_calls=True, allow_uncapped_costs=True)
            assert again.record == failure.record and failure_calls == [True]
            crash_request = prepared(1904)
            research.enqueue_research_batch(batch=ResearchBatch('uncapped-crash', (crash_request,)),
                                             allow_queue_write=True)
        child = subprocess.run([sys.executable, '-c', _CRASH, str(root)], cwd=ROOT,
            stdin=subprocess.DEVNULL, capture_output=True, encoding='utf-8',
            env=files.clean_environment(), timeout=120)
        assert child.returncode == 86, (child.stdout, child.stderr)
        db.down()
        with db.session() as research:
            incomplete = research.inspect(record_id=crash_request.record_id)
            assert incomplete.status == 'incomplete'
            p = authorization((crash_request,))
            repeated = research.run_uncapped_research(request=crash_request, authorization=p,
                model_factory=forbidden, allow_model_calls=True, allow_uncapped_costs=True)
            assert repeated == incomplete
            assert research.inspect(record_id=prior.request.record_id).record == prior.record
            assert research.inspect(record_id=original.request.record_id).record == original.record
            assert db._psql(identity, 'SELECT count(*) FROM project_private.migrations;') == '68'
            assert db._psql(identity, 'SELECT count(*) FROM research_capture.model_call_reservations;', owner=False) == '0'
        assert db.status()['instance_id'] == identity['instance_id'] and db.status()['status'] == 'stopped'
        print('native uncapped: PASS; BTC/ETH protocol, two turns, restart, one claim, zero fake permits, incomplete retained')
    finally:
        if db.status()['status'] != 'stopped': db.down()
