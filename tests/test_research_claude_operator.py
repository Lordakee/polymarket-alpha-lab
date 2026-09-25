"""Offline wiring, refusal, failure-preservation, and delegated replay tests.

No real session, database, credential, process, or provider is used anywhere.
Session spies establish exact assembly order and kwargs; a bridge over the
existing audit/rotation harnesses keeps real selection, replay, uncapped
dispatch, claim, and audit behavior behind the operator's fixed inputs.
"""
import dataclasses
import importlib
import sys
from dataclasses import replace
from datetime import timedelta

import pytest

from polymarket_alpha_lab import research_claude_operator as operator
from polymarket_alpha_lab import research_dispatch_rotation as turn_core
from polymarket_alpha_lab import research_dispatch_rotation_runner as rotation
from polymarket_alpha_lab import research_dispatch_store as dispatch_store
from polymarket_alpha_lab import research_uncapped_runner as uncapped_runner
from polymarket_alpha_lab.research_claude_profile import ClaudeExecProfile
from polymarket_alpha_lab.research_dispatch import (
    ResearchBatch, ResearchBatchSnapshot, StoredResearchBatch,
)
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_capture_psycopg import ResearchCaptureConflict
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from polymarket_alpha_lab.research_process import ResearchProcessSpec
from polymarket_alpha_lab.research_uncapped_audit import (
    StoredUncappedAuthorization, UncappedAuditSnapshot,
)
from tests.test_research_capture_codec import NOW, make_run
from tests.test_research_dispatch import Cursor, transaction as fake_transaction
from tests.test_research_execution import request as base_request, state
from tests.test_research_uncapped import approval
from tests.test_research_uncapped_audit import AuditHarness

MODEL = 'claude-opus-5'
_DEFAULT = object()
CREATE = 'create_uncapped_authorization'
INSPECT = 'inspect_uncapped_authorization'
ENQUEUE = 'enqueue_research_batch'
ROTATE = 'run_research_rotation'
BUILDER = 'claude_profile_factory'


class ForbiddenSupplier:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        raise AssertionError('api key supplier must not be invoked')


class ForbiddenSession:
    """Any attribute use fails the test: validation must precede all I/O."""

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        raise AssertionError('session reached: ' + name)


class BuilderSpy:
    def __init__(self, factory, log=None, on_build=None):
        self.factory, self.log, self.on_build = factory, log, on_build
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.log is not None:
            self.log.append((BUILDER, kwargs))
        if self.on_build is not None:
            self.on_build()
        return self.factory


class RecordingSession:
    """In-memory session double; records names/kwargs, replays canned receipts."""

    def __init__(self, stored, report):
        self.stored, self.report = stored, report
        self.calls, self.on_call = [], None
        self.create_result = self.inspect_result = _DEFAULT
        self.enqueue_results = []
        self.rotation_result = _DEFAULT

    def names(self):
        return [name for name, _ in self.calls]

    def _enter(self, name, kwargs):
        self.calls.append((name, kwargs))
        if self.on_call is not None:
            self.on_call(name, kwargs)

    def create_uncapped_authorization(self, *, authorization, allow_authorization_write):
        self._enter(CREATE, dict(authorization=authorization,
                                 allow_authorization_write=allow_authorization_write))
        return self.stored if self.create_result is _DEFAULT else self.create_result

    def inspect_uncapped_authorization(self, *, authorization_id):
        self._enter(INSPECT, dict(authorization_id=authorization_id))
        return self.stored if self.inspect_result is _DEFAULT else self.inspect_result

    def enqueue_research_batch(self, *, batch, allow_queue_write):
        self._enter(ENQUEUE, dict(batch=batch, allow_queue_write=allow_queue_write))
        if self.enqueue_results:
            return self.enqueue_results.pop(0)
        return StoredResearchBatch(batch, NOW + timedelta(seconds=2))

    def run_research_rotation(self, **configuration):
        self._enter(ROTATE, dict(configuration))
        return self.report if self.rotation_result is _DEFAULT else self.rotation_result

    def retry_capture(self, **kwargs):
        raise AssertionError('operator must not retry captures')


class RealEnqueueSession:
    """Authorization receipts in memory; enqueue runs the REAL store code."""

    def __init__(self, stored):
        self.stored, self.calls = stored, []

    def create_uncapped_authorization(self, **kwargs):
        self.calls.append('create')
        return self.stored

    def inspect_uncapped_authorization(self, **kwargs):
        self.calls.append('inspect')
        return self.stored

    def enqueue_research_batch(self, *, batch, allow_queue_write):
        self.calls.append('enqueue:' + batch.batch_id)
        return dispatch_store.enqueue_research_batch_with_psycopg(
            'fake', batch=batch, allow_queue_write=allow_queue_write)

    def run_research_rotation(self, **configuration):
        raise AssertionError('rotation must not run')


class BridgeSession:
    """Session double over the Bridge: real rotation runner, original receipts."""

    def __init__(self, bridge):
        self.bridge, self.calls = bridge, []

    def create_uncapped_authorization(self, *, authorization, allow_authorization_write):
        self.calls.append('create')
        assert allow_authorization_write is True
        if authorization.payload != self.bridge.permission.payload:
            raise AssertionError('changed authorization replay')
        return self.bridge.stored_authorization

    def inspect_uncapped_authorization(self, *, authorization_id):
        self.calls.append('inspect')
        assert authorization_id == self.bridge.permission.authorization_id
        return self.bridge.stored_authorization

    def enqueue_research_batch(self, *, batch, allow_queue_write):
        self.calls.append('enqueue:' + batch.batch_id)
        assert allow_queue_write is True
        stored = self.bridge.queued.get(batch.batch_id)
        if stored is None:
            stored = StoredResearchBatch(batch, NOW + timedelta(seconds=2))
            self.bridge.queued[batch.batch_id] = stored
        if stored.batch.payload != batch.payload:
            raise AssertionError('changed batch replay')
        return stored

    def run_research_rotation(self, **configuration):
        self.calls.append('rotation')
        return rotation.run_research_rotation_with_psycopg('fake', **configuration)

    def retry_capture(self, **kwargs):
        raise AssertionError('operator must not retry captures')


class Bridge(AuditHarness):
    """Operator inputs fed through the existing real runner/audit semantics."""

    def __init__(self, monkeypatch, permission, batches):
        super().__init__(monkeypatch)
        self.permission, self.batches = permission, tuple(batches)
        self.stored_authorization = StoredUncappedAuthorization(
            permission, NOW + timedelta(seconds=1))
        self.queued = {batch.batch_id: StoredResearchBatch(batch, NOW + timedelta(seconds=2))
                       for batch in self.batches}
        self.turns, self.loads, self.builder_calls = {}, [], []
        self.generated_at = NOW + timedelta(seconds=4)
        self.refuse_claims = set()
        monkeypatch.setattr(rotation, 'inspect_research_turn_with_psycopg',
                            lambda dsn, **kw: self.turns.get(kw['turn_id']))
        monkeypatch.setattr(rotation, 'load_research_batch_with_psycopg', self.load)
        monkeypatch.setattr(rotation, '_reserve', self.reserve)
        monkeypatch.setattr(operator, BUILDER, self.builder)

    def claim(self, dsn, request):
        if request.record_id in self.refuse_claims:
            raise RuntimeError('private-db-detail')
        return super().claim(dsn, request)

    def load(self, dsn, *, batch_id):
        self.loads.append(batch_id)
        stored = self.queued[batch_id]
        executions = tuple(
            claim if claim is None or claim.record is None else replace(claim, status='already_captured')
            for claim in (self.claims.get(r.record_id) for r in stored.batch.requests))
        return ResearchBatchSnapshot(stored, self.generated_at, executions)

    def reserve(self, dsn, **kw):
        previous = list(self.turns.values())[-1] if self.turns else None
        turn = turn_core.ResearchRotationTurn(kw['rotation_id'], kw['turn_id'], len(self.turns) + 1,
            kw['roster'], kw['observed_at'], kw['states'], kw['request_keys'],
            0 if previous is None else previous.turn.next_slot, kw['max_tasks'], kw['max_workers'])
        saved = turn_core.StoredResearchRotationTurn(turn, max(kw['observed_at']) + timedelta(seconds=1))
        self.turns[kw['turn_id']] = saved
        return True, saved

    def builder(self, **kwargs):
        self.builder_calls.append(kwargs)
        return self.factory


@pytest.fixture
def no_external_io(monkeypatch):
    monkeypatch.setattr('subprocess.Popen', lambda *a, **k: pytest.fail('process spawned'))
    monkeypatch.setattr('socket.socket', lambda *a, **k: pytest.fail('network entered'))
    monkeypatch.setattr('polymarket_alpha_lab.research_claude_exec.run_research_process',
                        lambda *a, **k: pytest.fail('claude process entered'))


def claude_profile(tmp_path, **changes):
    process = ResearchProcessSpec((str(tmp_path / 'claude-native'),), str(tmp_path / 'work'),
        (('HOME', str(tmp_path / 'home')), ('CLAUDE_CONFIG_DIR', str(tmp_path / 'config'))),
        'a' * 64, 15000)
    values = dict(process=process, endpoint_url='https://gateway.example.invalid')
    values.update(changes)
    return ClaudeExecProfile(**values)


def creq(n=0, *, team='crypto_eth', status='completed'):
    run = make_run(condition='condition-' + str(n), task='task-' + str(n), team=team, status=status)
    return base_request(record_id='q-' + str(n), model_id=MODEL,
                        forecast_cutoff_at=NOW + timedelta(hours=1), intake=run.intake)


def reviewed(tmp_path):
    profile_obj = claude_profile(tmp_path)
    batches = (ResearchBatch('batch-btc', (creq(0, team='crypto_btc'),)),
               ResearchBatch('batch-eth', (creq(1, team='crypto_eth'),)))
    permission = approval(tuple(batch.requests[0] for batch in batches), model_id=MODEL,
                          adapter_contract_sha256=profile_obj.contract_sha256)
    return profile_obj, batches, permission


def invoke(session, *, profile_obj, batches, permission, supplier,
           rotation_id='rotation-1', turn_id='turn-1', stop=None, **kw):
    return operator.run_claude_research_rotation(
        session, reviewed_batches=batches, profile=profile_obj, authorization=permission,
        api_key_supplier=supplier, rotation_id=rotation_id, turn_id=turn_id,
        stop=ResearchDispatchStop() if stop is None else stop, **kw)


def batch_row(batch):
    return (batch.batch_id, len(batch.requests), NOW, batch.payload,
            batch.content_sha256, True, True, True)


def test_import_is_inert(monkeypatch):
    supplier = ForbiddenSupplier()
    monkeypatch.setattr('subprocess.Popen', lambda *a, **k: pytest.fail('process spawned'))
    monkeypatch.setattr('socket.socket', lambda *a, **k: pytest.fail('network entered'))
    monkeypatch.setattr('polymarket_alpha_lab.research_claude_exec.run_research_process',
                        lambda *a, **k: pytest.fail('claude process entered'))
    monkeypatch.delitem(sys.modules, 'polymarket_alpha_lab.research_claude_operator', raising=False)
    module = importlib.import_module('polymarket_alpha_lab.research_claude_operator')
    assert callable(module.run_claude_research_rotation)
    assert module.ClaudeResearchAuditHandle.__slots__ is not None
    assert module.ClaudeResearchOperatorResult.__slots__ is not None
    assert supplier.calls == 0


def test_assembly_wires_one_audited_uncapped_two_team_rotation(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    report = object()
    session = RecordingSession(stored, report)
    factory = lambda team: pytest.fail('factory entered')
    builder = BuilderSpy(factory, log=session.calls)
    monkeypatch.setattr(operator, BUILDER, builder)
    supplier = ForbiddenSupplier()
    stop = ResearchDispatchStop()
    result = invoke(session, profile_obj=profile_obj, batches=batches,
                    permission=permission, supplier=supplier, stop=stop)
    assert session.names() == [CREATE, INSPECT, ENQUEUE, ENQUEUE, BUILDER, ROTATE]
    assert session.calls[0][1] == dict(authorization=permission, allow_authorization_write=True)
    assert session.calls[1][1] == dict(authorization_id=permission.authorization_id)
    assert session.calls[2][1] == dict(batch=batches[0], allow_queue_write=True)
    assert session.calls[3][1] == dict(batch=batches[1], allow_queue_write=True)
    assert len(builder.calls) == 1
    builder_kwargs = builder.calls[0]
    assert set(builder_kwargs) == {'profile', 'authorization', 'api_key_supplier',
                                   'allow_process_start', 'allow_api_key_use', 'stop'}
    assert builder_kwargs['profile'] == profile_obj
    assert builder_kwargs['api_key_supplier'] is supplier
    assert builder_kwargs['allow_process_start'] is True
    assert builder_kwargs['allow_api_key_use'] is True
    assert builder_kwargs['stop'] is stop
    rotation_kwargs = session.calls[5][1]
    assert rotation_kwargs['rotation_id'] == 'rotation-1'
    assert rotation_kwargs['turn_id'] == 'turn-1'
    assert rotation_kwargs['batch_ids_to_run'] == ('batch-btc', 'batch-eth')
    assert rotation_kwargs['model_factory'] is factory
    assert rotation_kwargs['allow_model_calls'] is True
    assert rotation_kwargs['allow_uncapped_costs'] is True
    assert rotation_kwargs['require_durable_audit'] is True
    assert rotation_kwargs['max_tasks'] == 2 and rotation_kwargs['max_workers'] == 2
    assert rotation_kwargs['stop'] is stop
    assert 'model_budget_id' not in rotation_kwargs
    assert result.report is report
    assert supplier.calls == 0


def test_factory_and_runner_receive_same_stored_authorization(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    builder = BuilderSpy(lambda team: pytest.fail('factory entered'))
    monkeypatch.setattr(operator, BUILDER, builder)
    supplier = ForbiddenSupplier()
    result = invoke(session, profile_obj=profile_obj, batches=batches,
                    permission=permission, supplier=supplier)
    bound = stored.authorization
    assert builder.calls[0]['authorization'] is bound
    assert session.calls[-1][1]['uncapped_authorization'] is bound
    assert bound is not permission and bound == permission
    assert result.authorization_receipt is stored
    assert result.authorization_receipt.authorization is bound
    assert supplier.calls == 0


def test_factory_and_runner_share_stop_token(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    builder = BuilderSpy(lambda team: pytest.fail('factory entered'))
    monkeypatch.setattr(operator, BUILDER, builder)
    stop = ResearchDispatchStop()
    supplier = ForbiddenSupplier()
    invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
           supplier=supplier, stop=stop)
    assert builder.calls[0]['stop'] is session.calls[-1][1]['stop'] is stop
    assert supplier.calls == 0


def test_default_and_explicit_limits_are_forwarded(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    builder = BuilderSpy(lambda team: pytest.fail('factory entered'))
    monkeypatch.setattr(operator, BUILDER, builder)
    supplier = ForbiddenSupplier()
    for limits, expected in (({}, (2, 2)), ({'max_tasks': 1, 'max_workers': 1}, (1, 1)),
                             ({'max_tasks': 2, 'max_workers': 2}, (2, 2))):
        session = RecordingSession(stored, object())
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier, **limits)
        rotation_kwargs = session.calls[-1][1]
        assert (rotation_kwargs['max_tasks'], rotation_kwargs['max_workers']) == expected
        assert 'max_tasks' not in builder.calls[-1] and 'max_workers' not in builder.calls[-1]
    assert len(builder.calls) == 3 and supplier.calls == 0


@pytest.mark.parametrize('field', ['max_tasks', 'max_workers'])
@pytest.mark.parametrize('value', [True, False, 0, -1, 3, '2', 1.0, None])
def test_invalid_limits_fail_before_io(no_external_io, tmp_path, field, value):
    profile_obj, batches, permission = reviewed(tmp_path)
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError):
        operator.run_claude_research_rotation(
            ForbiddenSession(), reviewed_batches=batches, profile=profile_obj,
            authorization=permission, api_key_supplier=supplier, rotation_id='rotation-1',
            turn_id='turn-1', stop=ResearchDispatchStop(), **{field: value})
    assert supplier.calls == 0


@pytest.mark.parametrize('supplier_value', [None, 123, 'api-key', object()])
def test_missing_or_noncallable_supplier_fails_before_io(no_external_io, tmp_path, supplier_value):
    profile_obj, batches, permission = reviewed(tmp_path)
    with pytest.raises(TypeError):
        operator.run_claude_research_rotation(
            ForbiddenSession(), reviewed_batches=batches, profile=profile_obj,
            authorization=permission, rotation_id='rotation-1', turn_id='turn-1',
            stop=ResearchDispatchStop())
    with pytest.raises(ValueError):
        operator.run_claude_research_rotation(
            ForbiddenSession(), reviewed_batches=batches, profile=profile_obj,
            authorization=permission, api_key_supplier=supplier_value,
            rotation_id='rotation-1', turn_id='turn-1', stop=ResearchDispatchStop())


def defect_roster(defect):
    btc = ResearchBatch('batch-btc', (creq(0, team='crypto_btc'),))
    eth = ResearchBatch('batch-eth', (creq(1, team='crypto_eth'),))
    return {
        'container': [btc, eth],
        'count_one': (btc,),
        'count_three': (btc, eth, ResearchBatch('batch-eth-2', (creq(3, team='crypto_eth'),))),
        'swapped_order': (eth, btc),
        'wrong_second_team': (btc, ResearchBatch('batch-btc-2', (creq(2, team='crypto_btc'),))),
        'duplicate_batch_id': (ResearchBatch('shared-id', (creq(0, team='crypto_btc'),)),
                               ResearchBatch('shared-id', (creq(1, team='crypto_eth'),))),
        'multi_request_batch': (ResearchBatch('batch-btc', (creq(0, team='crypto_btc'),
                                                            creq(2, team='crypto_btc'))), eth),
        'blocked_intake': (ResearchBatch('batch-btc', (creq(0, team='crypto_btc',
                                                            status='intake_blocked'),)), eth),
        'duplicate_request': (ResearchBatch('batch-a', (btc.requests[0],)),
                              ResearchBatch('batch-b', (btc.requests[0],))),
    }[defect]


@pytest.mark.parametrize('defect', ['container', 'count_one', 'count_three', 'swapped_order',
                                    'wrong_second_team', 'duplicate_batch_id',
                                    'multi_request_batch', 'blocked_intake', 'duplicate_request'])
def test_reviewed_batch_roster_is_exact(no_external_io, tmp_path, defect):
    profile_obj, _, permission = reviewed(tmp_path)
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError):
        operator.run_claude_research_rotation(
            ForbiddenSession(), reviewed_batches=defect_roster(defect), profile=profile_obj,
            authorization=permission, api_key_supplier=supplier, rotation_id='rotation-1',
            turn_id='turn-1', stop=ResearchDispatchStop())
    assert supplier.calls == 0


def typed_defect(tmp_path, defect):
    profile_obj, batches, permission = reviewed(tmp_path)
    btc, eth = batches
    kwargs = dict(reviewed_batches=batches, profile=profile_obj, authorization=permission,
                  api_key_supplier=ForbiddenSupplier(), rotation_id='rotation-1',
                  turn_id='turn-1', stop=ResearchDispatchStop())
    if defect == 'batch_object':
        kwargs['reviewed_batches'] = (object(), eth)
    elif defect == 'batch_flag':
        broken = replace(btc)
        object.__setattr__(broken, 'readonly', False)
        kwargs['reviewed_batches'] = (broken, eth)
    elif defect == 'authorization_object':
        kwargs['authorization'] = object()
    elif defect == 'authorization_flag':
        object.__setattr__(permission, 'paper_only', False)
    elif defect == 'profile_object':
        kwargs['profile'] = object()
    elif defect == 'stop_object':
        kwargs['stop'] = object()
    elif defect == 'rotation_id':
        kwargs['rotation_id'] = 'has space'
    elif defect == 'turn_id':
        kwargs['turn_id'] = ''
    return kwargs


@pytest.mark.parametrize('defect', ['batch_object', 'batch_flag', 'authorization_object',
                                    'authorization_flag', 'profile_object', 'stop_object',
                                    'rotation_id', 'turn_id'])
def test_invalid_typed_inputs_and_hard_flags_fail_before_io(no_external_io, tmp_path, defect):
    with pytest.raises(ValueError):
        operator.run_claude_research_rotation(ForbiddenSession(), **typed_defect(tmp_path, defect))


def binding_defect(tmp_path, defect):
    profile_obj, batches, permission = reviewed(tmp_path)
    btc, eth = batches
    btc_request, eth_request = btc.requests[0], eth.requests[0]
    digest = profile_obj.contract_sha256
    if defect == 'wrong_model':
        permission = approval((btc_request, eth_request), model_id='other-model',
                              adapter_contract_sha256=digest)
    elif defect == 'wrong_digest':
        permission = approval((btc_request, eth_request), model_id=MODEL,
                              adapter_contract_sha256='c' * 64)
    elif defect == 'missing_key':
        permission = approval((btc_request,), model_id=MODEL, adapter_contract_sha256=digest)
    elif defect == 'altered_key':
        permission = approval((btc_request, creq(9, team='crypto_eth')), model_id=MODEL,
                              adapter_contract_sha256=digest)
    elif defect == 'extra_key':
        permission = approval((btc_request, eth_request, creq(2, team='crypto_btc')),
                              model_id=MODEL, adapter_contract_sha256=digest)
    elif defect == 'reordered_keys':
        permission = approval((eth_request, btc_request), model_id=MODEL,
                              adapter_contract_sha256=digest)
    elif defect == 'request_model':
        batches = (ResearchBatch('batch-btc', (replace(btc_request, model_id='other-model'),)), eth)
    return profile_obj, batches, permission


@pytest.mark.parametrize('defect', ['wrong_model', 'wrong_digest', 'missing_key', 'altered_key',
                                    'extra_key', 'reordered_keys', 'request_model'])
def test_authorization_binds_entire_reviewed_roster_and_profile(no_external_io, tmp_path, defect):
    profile_obj, batches, permission = binding_defect(tmp_path, defect)
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError):
        operator.run_claude_research_rotation(
            ForbiddenSession(), reviewed_batches=batches, profile=profile_obj,
            authorization=permission, api_key_supplier=supplier, rotation_id='rotation-1',
            turn_id='turn-1', stop=ResearchDispatchStop())
    assert supplier.calls == 0


@pytest.mark.parametrize('defect', ['missing', 'wrong_type', 'different_authorization',
                                    'different_timestamp'])
def test_authorization_receipt_mismatch_stops_before_enqueue(no_external_io, tmp_path, defect):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    if defect == 'missing':
        session.inspect_result = None
    elif defect == 'wrong_type':
        session.inspect_result = object()
    elif defect == 'different_authorization':
        other = approval(tuple(batch.requests[0] for batch in batches), model_id=MODEL,
                         adapter_contract_sha256=profile_obj.contract_sha256,
                         authorization_id='a-different-approval')
        session.inspect_result = StoredUncappedAuthorization(other, NOW + timedelta(seconds=1))
    else:
        session.create_result = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
        session.inspect_result = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=2))
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError, match='authorization_receipt_mismatch'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier)
    assert session.names() == [CREATE, INSPECT]
    assert supplier.calls == 0


def test_equal_but_wrong_authorization_receipts_are_rejected(no_external_io, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    wrong = approval(tuple(batch.requests[0] for batch in batches), model_id=MODEL,
                     adapter_contract_sha256=profile_obj.contract_sha256,
                     expires_at=NOW + timedelta(minutes=20))
    receipt = StoredUncappedAuthorization(wrong, NOW + timedelta(seconds=1))
    session = RecordingSession(receipt, object())
    session.create_result = session.inspect_result = receipt
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError, match='authorization_receipt_mismatch'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier)
    assert session.names() == [CREATE, INSPECT]
    assert supplier.calls == 0


@pytest.mark.parametrize('defect', ['wrong_type', 'other_batch', 'changed_content'])
def test_enqueue_receipt_must_match_reviewed_batch(no_external_io, tmp_path, defect):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    if defect == 'wrong_type':
        session.enqueue_results = [object()]
    elif defect == 'other_batch':
        session.enqueue_results = [StoredResearchBatch(batches[1], NOW + timedelta(seconds=2))]
    else:
        altered = ResearchBatch('batch-btc', (replace(batches[0].requests[0],
            forecast_cutoff_at=NOW + timedelta(hours=3)),))
        session.enqueue_results = [StoredResearchBatch(altered, NOW + timedelta(seconds=2))]
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError, match='research_claude_operator_batch_receipt_mismatch'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier)
    assert session.names() == [CREATE, INSPECT, ENQUEUE]
    assert supplier.calls == 0


@pytest.mark.parametrize('case', ['stale_btc', 'future_btc', 'stale_eth'])
def test_stale_new_batch_stops_assembly_without_retry(no_external_io, monkeypatch, tmp_path, case):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    answers = {
        'stale_btc': [None, None, (NOW + timedelta(seconds=301),)],
        'future_btc': [None, None, (NOW - timedelta(seconds=1),)],
        'stale_eth': [None, None, (NOW,), batch_row(batches[0]),
                      None, None, (NOW + timedelta(seconds=301),)],
    }[case]
    cursor = Cursor(answers)
    fake_transaction(monkeypatch, cursor)
    builder = BuilderSpy(lambda team: pytest.fail('factory entered'))
    monkeypatch.setattr(operator, BUILDER, builder)
    session = RealEnqueueSession(stored)
    supplier = ForbiddenSupplier()
    with pytest.raises(dispatch_store.db.ResearchCaptureConflict, match='not_startable'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier)
    if case == 'stale_eth':
        assert session.calls == ['create', 'inspect', 'enqueue:batch-btc', 'enqueue:batch-eth']
        assert sum('INSERT INTO' in q for q, _ in cursor.calls) == 1
        assert sum('clock_timestamp' in q for q, _ in cursor.calls) == 2
    else:
        assert session.calls == ['create', 'inspect', 'enqueue:batch-btc']
        assert sum('INSERT INTO' in q for q, _ in cursor.calls) == 0
        assert sum('clock_timestamp' in q for q, _ in cursor.calls) == 1
    assert not builder.calls
    assert supplier.calls == 0


def test_pre_stopped_token_does_no_io(no_external_io, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stop = ResearchDispatchStop()
    stop.request_stop()
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError, match='research_claude_operator_stopped'):
        invoke(ForbiddenSession(), profile_obj=profile_obj, batches=batches,
               permission=permission, supplier=supplier, stop=stop)
    assert supplier.calls == 0


def step_trigger(trigger, name, kwargs):
    if trigger == 'create':
        return name == CREATE
    if trigger == 'inspect':
        return name == INSPECT
    if trigger == 'rotation':
        return name == ROTATE
    if trigger in ('enqueue_btc', 'enqueue_eth'):
        return name == ENQUEUE and kwargs['batch'].batch_id == 'batch-' + trigger.split('_')[1]
    return False


@pytest.mark.parametrize('trigger', ['create', 'inspect', 'enqueue_btc', 'enqueue_eth', 'builder'])
def test_stop_between_steps_preserves_committed_prefix(no_external_io, monkeypatch, tmp_path, trigger):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    stop = ResearchDispatchStop()
    session.on_call = lambda name, kwargs: (stop.request_stop()
                                            if step_trigger(trigger, name, kwargs) else None)
    builder = BuilderSpy(lambda team: pytest.fail('factory entered'),
                         on_build=stop.request_stop if trigger == 'builder' else None)
    monkeypatch.setattr(operator, BUILDER, builder)
    supplier = ForbiddenSupplier()
    expected = {
        'create': [CREATE, INSPECT],
        'inspect': [CREATE, INSPECT],
        'enqueue_btc': [CREATE, INSPECT, ENQUEUE],
        'enqueue_eth': [CREATE, INSPECT, ENQUEUE, ENQUEUE],
        'builder': [CREATE, INSPECT, ENQUEUE, ENQUEUE],
    }[trigger]
    with pytest.raises(ValueError, match='research_claude_operator_stopped'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier, stop=stop)
    assert session.names() == expected
    assert len(builder.calls) == (1 if trigger == 'builder' else 0)
    assert ROTATE not in session.names()
    assert supplier.calls == 0


def test_actual_claude_factory_binding_does_not_resolve_supplier(no_external_io, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    report = object()
    session = RecordingSession(stored, report)
    supplier = ForbiddenSupplier()
    result = invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
                    supplier=supplier)
    assert session.names() == [CREATE, INSPECT, ENQUEUE, ENQUEUE, ROTATE]
    rotation_kwargs = session.calls[-1][1]
    bound_factory = rotation_kwargs['model_factory']
    assert callable(bound_factory) and result.report is report
    assert supplier.calls == 0


@pytest.mark.parametrize('kind', ['exception', 'interrupt'])
@pytest.mark.parametrize('step', ['create', 'inspect', 'enqueue_btc', 'enqueue_eth',
                                  'builder', 'rotation'])
def test_step_failure_or_interrupt_does_not_retry(no_external_io, monkeypatch, tmp_path, step, kind):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    error = RuntimeError('SECRET-SENTINEL') if kind == 'exception' else KeyboardInterrupt()
    session.on_call = lambda name, kwargs: (_ for _ in ()).throw(error) \
        if step_trigger(step, name, kwargs) else None
    builder = BuilderSpy(lambda team: pytest.fail('factory entered'),
                         on_build=lambda: (_ for _ in ()).throw(error) if step == 'builder' else None)
    monkeypatch.setattr(operator, BUILDER, builder)
    supplier = ForbiddenSupplier()
    expected = {
        'create': [CREATE],
        'inspect': [CREATE, INSPECT],
        'enqueue_btc': [CREATE, INSPECT, ENQUEUE],
        'enqueue_eth': [CREATE, INSPECT, ENQUEUE, ENQUEUE],
        'builder': [CREATE, INSPECT, ENQUEUE, ENQUEUE],
        'rotation': [CREATE, INSPECT, ENQUEUE, ENQUEUE, ROTATE],
    }[step]
    with pytest.raises(type(error)) as caught:
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier)
    assert caught.value is error
    assert session.names() == expected
    assert len(builder.calls) == (1 if step in ('builder', 'rotation') else 0)
    assert 'SECRET-SENTINEL' not in repr(session)
    assert supplier.calls == 0


def test_factory_refusal_never_falls_back_to_codex(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    session = RecordingSession(stored, object())
    builder_calls = []

    def refusing_builder(**kwargs):
        builder_calls.append(kwargs)
        raise ValueError('research_claude_profile_authorization_mismatch')

    monkeypatch.setattr(operator, BUILDER, refusing_builder)
    supplier = ForbiddenSupplier()
    with pytest.raises(ValueError, match='authorization_mismatch'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier)
    assert len(builder_calls) == 1
    assert session.names() == [CREATE, INSPECT, ENQUEUE, ENQUEUE]
    assert supplier.calls == 0


def test_same_turn_replay_is_inert_even_after_expiry(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    bridge = Bridge(monkeypatch, permission, batches)
    session = BridgeSession(bridge)
    supplier = ForbiddenSupplier()
    stop = ResearchDispatchStop()
    first = invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
                   supplier=supplier, stop=stop)
    assert first.report.status == 'dispatched'
    assert [attempt.position for attempt in first.report.attempts] == [0, 1]
    assert [attempt.execution.request.record_id for attempt in first.report.attempts] == ['q-0', 'q-1']
    assert all(attempt.status == 'returned' for attempt in first.report.attempts)
    assert all(attempt.execution.record.run.research.status == 'completed'
               for attempt in first.report.attempts)
    for record_id in ('q-0', 'q-1'):
        snapshot = UncappedAuditSnapshot(record_id,
            tuple(s for s in bridge.starts if s.record_id == record_id),
            tuple(o for o in bridge.outcomes if o.start.record_id == record_id))
        summary = snapshot.to_dict()
        assert summary['validated_reply_count'] == 2
        assert summary['unknown_usage_call_count'] == 0
        assert summary['all_calls_have_terminal_record'] is True
    events_after_first = list(bridge.events)
    loads_after_first = list(bridge.loads)
    starts_after_first = len(bridge.starts)
    builders_before = len(bridge.builder_calls)
    monkeypatch.setattr(uncapped_runner, '_now',
                        lambda: permission.expires_at + timedelta(seconds=1))
    replay = invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
                    supplier=supplier, stop=stop)
    assert replay.report.status == 'turn_already_reserved'
    assert replay.report.stored == first.report.stored and replay.report.attempts == ()
    assert len(bridge.builder_calls) == builders_before + 1
    assert bridge.loads == loads_after_first
    assert bridge.events == events_after_first
    assert len(bridge.starts) == starts_after_first
    assert supplier.calls == 0


def test_changed_same_turn_inputs_delegate_conflict(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    bridge = Bridge(monkeypatch, permission, batches)
    session = BridgeSession(bridge)
    supplier = ForbiddenSupplier()
    invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
           supplier=supplier)
    events_after_first = list(bridge.events)
    loads_after_first = list(bridge.loads)
    with pytest.raises(ResearchCaptureConflict, match='turn_conflict'):
        invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
               supplier=supplier, turn_id='turn-1', max_tasks=1)
    changed_roster = (batches[0], ResearchBatch('batch-eth-alt', (batches[1].requests[0],)))
    with pytest.raises(ResearchCaptureConflict, match='turn_conflict'):
        invoke(session, profile_obj=profile_obj, batches=changed_roster, permission=permission,
               supplier=supplier)
    assert bridge.events == events_after_first
    assert bridge.loads == loads_after_first
    assert supplier.calls == 0


def test_explicit_new_turn_preserves_existing_recovery_rules(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    bridge = Bridge(monkeypatch, permission, batches)
    session = BridgeSession(bridge)
    supplier = ForbiddenSupplier()
    stop = ResearchDispatchStop()
    base = dict(profile_obj=profile_obj, batches=batches, permission=permission,
                supplier=supplier, stop=stop)
    btc_request, eth_request = batches[0].requests[0], batches[1].requests[0]
    bridge.claims[eth_request.record_id] = state(eth_request)
    bridge.refuse_claims = {btc_request.record_id}
    first = invoke(session, turn_id='t1', **base)
    assert first.report.status == 'dispatched'
    assert [attempt.status for attempt in first.report.attempts] == ['operation_failed']
    assert first.report.attempts[0].position == 0
    assert bridge.events.count('claim') == 0
    bridge.refuse_claims = set()
    second = invoke(session, turn_id='t2', **base)
    assert [attempt.status for attempt in second.report.attempts] == ['returned']
    assert second.report.attempts[0].execution.request.record_id == btc_request.record_id
    assert second.report.attempts[0].execution.record.run.research.status == 'completed'
    assert bridge.events.count('claim') == 1
    assert bridge.claims[eth_request.record_id].status == 'incomplete'
    assert not any(s.record_id == eth_request.record_id for s in bridge.starts)
    bridge.claims.pop(eth_request.record_id)
    bridge.generated_at = NOW + timedelta(seconds=301)
    third = invoke(session, turn_id='t3', **base)
    assert third.report.status == 'dispatched' and third.report.attempts == ()
    assert bridge.events.count('factory') == 1 and bridge.events.count('complete') == 2
    assert supplier.calls == 0


def test_result_preserves_report_and_audit_lookup_keys(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    stored = StoredUncappedAuthorization(permission, NOW + timedelta(seconds=1))
    report = object()
    session = RecordingSession(stored, report)
    monkeypatch.setattr(operator, BUILDER, BuilderSpy(lambda team: pytest.fail('factory entered')))
    supplier = ForbiddenSupplier()
    result = invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
                    supplier=supplier)
    assert result.report is report
    assert result.authorization_receipt is stored
    assert (result.rotation_id, result.turn_id) == ('rotation-1', 'turn-1')
    assert result.audit_handles == (
        operator.ClaudeResearchAuditHandle('crypto_btc', 'batch-btc', batches[0].content_sha256,
                                           'q-0', batches[0].requests[0].content_sha256),
        operator.ClaudeResearchAuditHandle('crypto_eth', 'batch-eth', batches[1].content_sha256,
                                           'q-1', batches[1].requests[0].content_sha256))
    assert set(operator.ClaudeResearchAuditHandle.__dataclass_fields__) == {
        'team_id', 'batch_id', 'batch_sha256', 'record_id', 'request_sha256'}
    for handle in result.audit_handles:
        assert all(type(value) is str for value in dataclasses.astuple(handle))
    assert repr(result)
    assert supplier.calls == 0


def test_capture_failed_pending_run_is_retained(no_external_io, monkeypatch, tmp_path):
    profile_obj, batches, permission = reviewed(tmp_path)
    bridge = Bridge(monkeypatch, permission, batches)
    session = BridgeSession(bridge)
    pending_runs = {}

    def fake_uncapped(dsn, *, request, authorization, model_factory, allow_model_calls,
                      allow_uncapped_costs, stop, require_durable_audit):
        run = make_run(condition=request.intake.condition_id, task=request.intake.task_id,
                       team=request.intake.team_id)
        pending_runs[request.record_id] = run
        return CapturedResearchExecution(request, NOW + timedelta(seconds=2),
                                         'capture_failed', pending_run=run)

    monkeypatch.setattr(uncapped_runner, 'run_uncapped_research_with_psycopg', fake_uncapped)
    supplier = ForbiddenSupplier()
    result = invoke(session, profile_obj=profile_obj, batches=batches, permission=permission,
                    supplier=supplier)
    assert result.report.status == 'dispatched'
    assert result.report.stored == bridge.turns['turn-1']
    for attempt in result.report.attempts:
        assert attempt.status == 'returned'
        assert attempt.execution.status == 'capture_failed'
        assert attempt.execution.pending_run == pending_runs[attempt.execution.request.record_id]
    # The rotation-level durable-authorization check ran once; no factory,
    # model call, audit start, or capture was ever entered.
    assert bridge.events == ['authorization']
    assert not bridge.starts and not bridge.outcomes
    assert supplier.calls == 0
