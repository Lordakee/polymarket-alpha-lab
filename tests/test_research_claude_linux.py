"""Contained-profile v2 digests, golden v1 compatibility, and the finite supplier.

Golden digests protect BOTH the Claude v1 and the frozen Codex v1 contracts
against silent digest-input drift; fixed synthetic paths keep them stable per
platform. No real binary, credential, provider, process launch or network is
used anywhere here.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import sys
import traceback

import pytest

from polymarket_alpha_lab import research_claude_operator as operator
from polymarket_alpha_lab import research_claude_profile as profile
from polymarket_alpha_lab import research_claude_exec as cli
from polymarket_alpha_lab.research_claude_profile import (
    ClaudeExecProfile, FiniteInMemoryApiKeySupplier, claude_profile_factory,
)
from polymarket_alpha_lab.research_codex_profile import CodexExecProfile
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_process import ResearchProcessError, ResearchProcessSpec
from tests.test_research_claude_exec import MODEL, action, envelope, wire
from tests.test_research_claude_profile import SENTINEL, permission
from tests.test_research_process_linux import HELPER_DIGEST, fixed_launch, relaunch
from tests.test_research_uncapped import req, run
from tests.test_research_uncapped_audit import AuditHarness

GOLDEN_ROOT = '/opt/pal-golden' if sys.platform == 'linux' else 'C:/pal-golden'
CLAUDE_V1_GOLDEN = {
    'linux': 'a09a6b95666bb9da7ba40e2a55a1c01ce7efcaf3efcb5297fdfbdd0321137b13',
    'win32': '015fdfac61b59f6ef900ba834902edc772063c4da0dbd899f2087b3651356b8b',
}
CODEX_V1_GOLDEN = {
    'linux': '8b4edb02749acddc197bb264fd415b20b1b0ef5b7dd686024e0acd7136bbf162',
    'win32': '3988359c974aa5052c0224c5f16d4be1f7e4ba44a2410462ea07c9a63e48b5aa',
}
# Historical v2 digest with the pre-correction bare banner
# ('<version>\n'), per golden-root platform layout. The corrected profile
# refuses that banner, so this value can no longer be produced by
# construction; authorizations carrying it must be rejected, never rewritten.
PRE_CORRECTION_V2_GOLDEN = {
    'linux': '46c14c1f8bbaf2f9dda2899489b6cc09b0825e0f796d6376bc00381d8112f204',
    'win32': 'f1986a31715dc34c3dbf30dbd42451f8753875ed83d03d6888f37b38ca246390',
}


def golden_process(argv0, cwd, environment, digest):
    return ResearchProcessSpec((argv0,), cwd, environment, digest, 15000)


def golden_claude_v1():
    process = golden_process(GOLDEN_ROOT + '/vendor/claude', GOLDEN_ROOT + '/work',
                             (('HOME', GOLDEN_ROOT + '/home'),
                              ('CLAUDE_CONFIG_DIR', GOLDEN_ROOT + '/config')), 'ab' + 'a' * 62)
    return ClaudeExecProfile(process=process, endpoint_url='https://gateway.example.invalid')


def golden_codex_v1():
    return CodexExecProfile(
        process=golden_process(GOLDEN_ROOT + '/vendor/codex', GOLDEN_ROOT + '/codex-work',
                               (('CODEX_HOME', GOLDEN_ROOT + '/codex-home'),
                                ('HOME', GOLDEN_ROOT + '/home')), 'cd' + 'c' * 62),
        model_id='gpt-5.6-sol', gateway_url='https://codex-gateway.example.invalid',
        schema_path=GOLDEN_ROOT + '/schema.json')


def contained_profile(launch=None):
    return replace(golden_claude_v1(), linux_launch=fixed_launch() if launch is None else launch)


def finite_supplier(stop, btc=('KEY-BTC-1', 'KEY-BTC-2'), eth=('KEY-ETH-1', 'KEY-ETH-2')):
    return FiniteInMemoryApiKeySupplier(stop=stop, crypto_btc=btc, crypto_eth=eth)


def test_claude_v1_golden_digest_is_pinned():
    assert golden_claude_v1().contract_sha256 == CLAUDE_V1_GOLDEN[sys.platform]


def test_codex_v1_golden_digest_is_pinned():
    assert golden_codex_v1().contract_sha256 == CODEX_V1_GOLDEN[sys.platform]


def test_v2_digest_is_stable_distinct_and_secret_free():
    first = contained_profile()
    second = contained_profile()
    assert first.contract_sha256 == second.contract_sha256
    assert first.contract_sha256 != golden_claude_v1().contract_sha256
    assert SENTINEL not in first.contract_sha256
    assert 'SYNTHETIC-KEY' not in first.contract_sha256


@pytest.mark.parametrize('changes', [
    {'wrapper': None}, {'expected_version_output': None}, {'cgroup_root': None},
    {'vendor_guest_path': None}, {'vendor_size_bytes': None},
])
def test_v2_cannot_be_built_with_none_pinned_fields(changes):
    with pytest.raises((ValueError, TypeError)):
        relaunch(fixed_launch(), **changes)


@pytest.mark.parametrize('mutation', [
    lambda launch: relaunch(launch, memory_max_bytes=536870912),
    lambda launch: relaunch(launch, pids_max=16),
    lambda launch: relaunch(launch, scratch_size_bytes=32 * 1024 * 1024),
    lambda launch: relaunch(launch, wrapper=type(launch.wrapper)(
        launch.wrapper.path, 'f' * 64, launch.wrapper.size_bytes)),
    lambda launch: relaunch(launch, interpreter=type(launch.interpreter)(
        '/opt/pal-other/python3', launch.interpreter.sha256,
        launch.interpreter.size_bytes)),
    lambda launch: relaunch(launch, cgroup_root='/opt/pal-other/cgroup'),
    lambda launch: relaunch(launch, guest_home_path='/pal/other-home'),
    lambda launch: relaunch(launch, vendor_guest_path='/pal/other-vendor'),
    lambda launch: relaunch(launch, helper_guest_path='/pal/runtime/other-helper.py'),
    lambda launch: relaunch(launch, allowed_guest_env=tuple(sorted(
        set(launch.allowed_guest_env) - {'LD_LIBRARY_PATH'}))),
    lambda launch: relaunch(launch, runtime_files=(launch.runtime_files[0],
        type(launch.runtime_files[0])(launch.runtime_files[0].guest_path + '.2',
                                      '/opt/pal-other/lib.so', '0' * 64, 10))),
])
def test_v2_digest_covers_every_public_policy_change(monkeypatch, mutation):
    def forbidden(*args, **kwargs):
        pytest.fail('digest computation performed I/O')
    monkeypatch.setattr('pathlib.Path.read_bytes', forbidden)
    base = contained_profile()
    changed = contained_profile(launch=mutation(fixed_launch()))
    assert changed.contract_sha256 != base.contract_sha256


def test_ephemeral_allocation_details_never_enter_the_v2_digest():
    base = contained_profile().contract_sha256
    # The same declared policy digests identically regardless of any later
    # runtime allocation names, descriptor numbers or PIDs (excluded inputs).
    policy = fixed_launch().policy_dict()
    assert 'pal-call' not in repr(policy)
    assert base == contained_profile().contract_sha256


def test_old_authorization_cannot_authorize_a_contained_profile(tmp_path):
    v1 = golden_claude_v1()
    stale = permission(v1)
    stop = ResearchDispatchStop()
    with pytest.raises(ValueError, match='authorization_mismatch'):
        claude_profile_factory(profile=contained_profile(), authorization=stale,
                               api_key_supplier=finite_supplier(stop),
                               allow_process_start=True, allow_api_key_use=True, stop=stop)


def test_pre_correction_v2_authorization_is_rejected_without_rewriting():
    """The banner correction changes the v2 digest: an authorization issued
    against the pre-correction (bare-banner) v2 digest is rejected by the
    corrected profile, and nothing rewrites either side to force a match.
    The pre-correction profile itself no longer even constructs."""
    corrected = contained_profile()
    stale_digest = PRE_CORRECTION_V2_GOLDEN[sys.platform]
    assert corrected.contract_sha256 != stale_digest
    with pytest.raises(ValueError, match='profile_invalid'):
        contained_profile(launch=relaunch(fixed_launch(),
                                          expected_version_output=cli.CLAUDE_VERSION + '\n'))
    stop = ResearchDispatchStop()
    stale = replace(permission(corrected), adapter_contract_sha256=stale_digest)
    with pytest.raises(ValueError, match='authorization_mismatch'):
        claude_profile_factory(profile=corrected, authorization=stale,
                               api_key_supplier=finite_supplier(stop),
                               allow_process_start=True, allow_api_key_use=True, stop=stop)
    # No automatic rewriting happened: the corrected digest and the stale
    # authorization are unchanged after the failed binding, and the corrected
    # profile still accepts its OWN current digest.
    assert corrected.contract_sha256 == contained_profile().contract_sha256
    assert stale.adapter_contract_sha256 == stale_digest
    factory = claude_profile_factory(profile=corrected, authorization=permission(corrected),
                                     api_key_supplier=finite_supplier(stop),
                                     allow_process_start=True, allow_api_key_use=True,
                                     stop=stop)
    assert type(factory('crypto_btc')) is cli.ClaudeProcessModel


@pytest.mark.parametrize('defect', ['wrong_type', 'unbound_stop', 'plain_callable'])
def test_v2_factory_requires_the_exact_bound_finite_supplier(defect, monkeypatch):
    stop = ResearchDispatchStop()
    if defect == 'wrong_type':
        supplier = object()
    elif defect == 'unbound_stop':
        supplier = finite_supplier(ResearchDispatchStop())
    else:
        supplier = lambda: SENTINEL
    with pytest.raises(ValueError, match='supplier'):
        claude_profile_factory(profile=contained_profile(),
                               authorization=permission(contained_profile()),
                               api_key_supplier=supplier, allow_process_start=True,
                               allow_api_key_use=True, stop=stop)


def test_v1_factory_still_accepts_plain_callable_suppliers():
    factory = claude_profile_factory(profile=golden_claude_v1(),
                                     authorization=permission(golden_claude_v1()),
                                     api_key_supplier=lambda: SENTINEL,
                                     allow_process_start=True, allow_api_key_use=True)
    assert type(factory('crypto_btc')) is cli.ClaudeProcessModel


@pytest.mark.parametrize('bad', [None, 123, object()])
def test_supplier_construction_requires_the_rotation_stop(bad):
    with pytest.raises(ValueError):
        FiniteInMemoryApiKeySupplier(stop=bad)


@pytest.mark.parametrize('slots', [
    ('KEY-1', None), ('KEY-1', ''), ('KEY-1', 'has space'), ('KEY-1', 'k' * 4097),
    ('KEY-1', 7), ['KEY-1'], 'KEY-1',
])
def test_supplier_slots_are_explicit_in_memory_values_only(slots):
    stop = ResearchDispatchStop()
    with pytest.raises(ValueError):
        FiniteInMemoryApiKeySupplier(stop=stop, crypto_btc=slots)
    with pytest.raises(ValueError):
        FiniteInMemoryApiKeySupplier(stop=stop, crypto_eth=slots)


def test_supplier_repr_and_errors_never_expose_slot_values():
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop, btc=('SECRET-BTC-VALUE',), eth=('SECRET-ETH-VALUE',))
    assert 'SECRET-BTC-VALUE' not in repr(supplier) and 'SECRET-ETH-VALUE' not in repr(supplier)
    assert supplier.remaining('crypto_btc') == 1
    supplier.acquire('crypto_btc')
    with pytest.raises(ValueError) as caught:
        supplier.acquire('crypto_btc')
    assert 'SECRET-BTC-VALUE' not in str(caught.value)
    assert supplier.remaining('crypto_btc') == 0 and supplier.remaining('crypto_eth') == 1


def test_stop_wins_admission_and_consumes_nothing():
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop)
    stop.request_stop()
    with pytest.raises(ValueError, match='stopped'):
        supplier.acquire('crypto_btc')
    assert supplier.remaining('crypto_btc') == 2 and supplier.remaining('crypto_eth') == 2


def test_admission_before_stop_consumes_permanently():
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop)
    first = supplier.acquire('crypto_btc')
    stop.request_stop()
    with pytest.raises(ValueError, match='stopped'):
        supplier.acquire('crypto_btc')
    assert first == 'KEY-BTC-1'
    assert supplier.remaining('crypto_btc') == 1  # no recycling after the stop
    assert supplier.remaining('crypto_eth') == 2


@pytest.mark.parametrize('team', ['politics', 'crypto_sol', '', None])
def test_supplier_rejects_unknown_teams(team):
    supplier = finite_supplier(ResearchDispatchStop())
    with pytest.raises(ValueError, match='team'):
        supplier.acquire(team)


def test_exhausted_supplier_still_permits_inert_factory_construction():
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop, btc=(), eth=())
    contained = contained_profile()
    factory = claude_profile_factory(profile=contained, authorization=permission(contained),
                                     api_key_supplier=supplier, allow_process_start=True,
                                     allow_api_key_use=True, stop=stop)
    assert type(factory('crypto_btc')) is type(factory('crypto_eth')) is cli.ClaudeProcessModel


def test_two_factory_clients_share_one_supplier_safely(monkeypatch):
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop, btc=('KEY-B-1', 'KEY-B-2', 'KEY-B-3'),
                               eth=('KEY-E-1', 'KEY-E-2', 'KEY-E-3'))
    contained = contained_profile()
    factory = claude_profile_factory(profile=contained, authorization=permission(contained),
                                     api_key_supplier=supplier, allow_process_start=True,
                                     allow_api_key_use=True, stop=stop)
    seen = []
    calls = []

    def process(**kwargs):
        calls.append(kwargs)
        return wire(envelope([action('finish_research', probability_yes='0.5',
                                     confidence='0.5', summary='Synthetic',
                                     source_ids=['s'])] if len(calls) > 1 else None))

    monkeypatch.setattr(cli, 'run_research_process', process)

    def complete(team, count):
        model = factory(team)
        for _ in range(count):
            model.complete(messages_json='[{}]', max_output_tokens=100)

    with ThreadPoolExecutor(max_workers=2) as pool:
        pool.submit(complete, 'crypto_btc', 3)
        pool.submit(complete, 'crypto_eth', 3)
    assert supplier.remaining('crypto_btc') == 0 and supplier.remaining('crypto_eth') == 0
    for kwargs in calls:
        assert dict(kwargs['spec'].environment)['ANTHROPIC_API_KEY'].startswith('KEY-')
        assert kwargs.get('linux_launch') is contained.linux_launch
    assert len(calls) == 6


def test_supplier_exhaustion_fails_the_call_without_recycling(monkeypatch):
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop, btc=('KEY-ONLY',), eth=())
    contained = contained_profile()
    factory = claude_profile_factory(profile=contained, authorization=permission(contained),
                                     api_key_supplier=supplier, allow_process_start=True,
                                     allow_api_key_use=True, stop=stop)
    monkeypatch.setattr(cli, 'run_research_process', lambda **kwargs: wire())
    assert factory('crypto_btc').complete(messages_json='[{}]',
                                          max_output_tokens=100).total_tokens == 26
    monkeypatch.setattr(cli, 'run_research_process',
                        lambda **kwargs: pytest.fail('no process after exhaustion'))
    with pytest.raises(ValueError) as caught:
        factory('crypto_btc').complete(messages_json='[{}]', max_output_tokens=100)
    assert 'KEY-ONLY' not in ''.join(traceback.format_exception(caught.value))
    assert supplier.remaining('crypto_btc') == 0


def test_banner_mismatch_keeps_the_consumed_slot_consumed(monkeypatch):
    """The version-mismatch path consumes the supplier slot before the run and
    never returns it: the malformed banner fails the call inside the version
    phase (before model launch or credential delivery) and the slot stays
    permanently consumed; the key value never leaks into the failure."""
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop, btc=('KEY-ONLY',), eth=())
    contained = contained_profile()
    factory = claude_profile_factory(profile=contained, authorization=permission(contained),
                                     api_key_supplier=supplier, allow_process_start=True,
                                     allow_api_key_use=True, stop=stop)

    def banner_mismatch(**kwargs):
        raise ResearchProcessError('research_process_version_mismatch')

    monkeypatch.setattr(cli, 'run_research_process', banner_mismatch)
    with pytest.raises(ValueError, match='research_claude_call_failed') as caught:
        factory('crypto_btc').complete(messages_json='[{}]', max_output_tokens=100)
    assert 'KEY-ONLY' not in ''.join(traceback.format_exception(caught.value))
    assert supplier.remaining('crypto_btc') == 0
    assert supplier.remaining('crypto_eth') == 0


@pytest.mark.parametrize('team', ['crypto_btc', 'crypto_eth'])
def test_v2_client_forwards_launch_spec_only_to_the_runner(monkeypatch, team):
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop)
    contained = contained_profile()
    factory = claude_profile_factory(profile=contained, authorization=permission(contained),
                                     api_key_supplier=supplier, allow_process_start=True,
                                     allow_api_key_use=True, stop=stop)
    seen = []

    def process(**kwargs):
        seen.append(kwargs)
        return wire()

    monkeypatch.setattr(cli, 'run_research_process', process)
    factory(team).complete(messages_json='[{}]', max_output_tokens=100)
    assert seen[0]['linux_launch'] is contained.linux_launch
    assert dict(seen[0]['spec'].environment)['ANTHROPIC_API_KEY'].startswith('KEY-')
    assert supplier.remaining(team) == 1
    assert supplier.remaining('crypto_eth' if team == 'crypto_btc' else 'crypto_btc') == 2


def test_audit_still_commits_before_the_finite_supplier(monkeypatch):
    harness = AuditHarness(monkeypatch)
    request = replace(req(), model_id=MODEL)
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop, btc=('KEY-B-1', 'KEY-B-2', 'KEY-B-3'),
                               eth=('KEY-E-1', 'KEY-E-2', 'KEY-E-3'))
    contained = contained_profile()
    authorization = permission(contained, request)
    factory = claude_profile_factory(profile=contained, authorization=authorization,
                                     api_key_supplier=supplier, allow_process_start=True,
                                     allow_api_key_use=True, stop=stop)
    calls = []

    def process(**kwargs):
        calls.append(kwargs)
        source = (request.required_source_ids[0] if request.required_source_ids
                          else request.intake.task.evidence[0].source_id)
        replies = ([wire(envelope([action('read_evidence', source_id=source)]))] * 2
                   + [wire(envelope([action('finish_research', probability_yes='0.6',
                                            confidence='0.5', summary='Synthetic',
                                            source_ids=[source])]))])
        return replies[len(calls) - 1]

    monkeypatch.setattr(cli, 'run_research_process', process)
    result = run(harness, request=request, authorization=authorization, model_factory=factory,
                 require_durable_audit=True)
    assert result.record.run.research.status == 'completed'
    assert len(calls) == 3
    assert supplier.remaining('crypto_btc') == 3 and supplier.remaining('crypto_eth') == 0
    for kwargs in calls:
        assert kwargs['linux_launch'] is contained.linux_launch
    replay = run(harness, request=request, authorization=authorization,
                 model_factory=lambda _: pytest.fail('replayed factory'),
                 require_durable_audit=True)
    assert replay == result
    assert supplier.remaining('crypto_eth') == 0 and supplier.remaining('crypto_btc') == 3


def test_operator_rejects_any_session_before_linux(monkeypatch):
    monkeypatch.setattr(operator, '_SESSION_PLATFORM', 'win32')
    stop = ResearchDispatchStop()
    with pytest.raises(ValueError, match='research_claude_operator_linux_required'):
        operator._admit_linux_session(contained_profile(), finite_supplier(stop), stop)


@pytest.mark.parametrize('defect', ['uncontained_profile', 'egress_tampered',
                                    'wrong_supplier_type', 'wrong_stop_object',
                                    'supplier_without_this_stop'])
def test_operator_admission_guard_covers_every_defect(defect, monkeypatch):
    monkeypatch.setattr(operator, '_SESSION_PLATFORM', 'linux')
    stop = ResearchDispatchStop()
    profile_obj = contained_profile()
    if defect == 'uncontained_profile':
        profile_obj = replace(profile_obj, linux_launch=None)
    elif defect == 'egress_tampered':
        launch = profile_obj.linux_launch
        object.__setattr__(launch, 'egress_policy', 'host')
    elif defect == 'wrong_supplier_type':
        supplier = lambda: SENTINEL
    elif defect == 'wrong_stop_object':
        supplier = finite_supplier(ResearchDispatchStop())
    else:
        supplier = finite_supplier(ResearchDispatchStop())
        stop = ResearchDispatchStop()
    supplier = finite_supplier(stop) if defect in ('uncontained_profile',
                                                   'egress_tampered') else supplier
    with pytest.raises(ValueError):
        operator._admit_linux_session(profile_obj, supplier, stop)
