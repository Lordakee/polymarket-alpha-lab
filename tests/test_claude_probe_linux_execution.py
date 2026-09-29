"""L7 outer probe runner qualification; synthetic stand-ins only.

Non-native tests validate the runner's plan validation, admission logic,
deadline policy, argv derivation, bounded export and structural gates on any
host. Native opt-in tests (``POLYMARKET_ALPHA_LAB_RUN_LINUX_PROBE_RUNNER=1``)
run the real runner against synthetic namespace-plan v2 documents (the schema
emitted by scripts/claude_probe_environment.py ``official-config --platform
linux``) whose IMAGE member is a locally resolved Python interpreter stand-in
(NEVER the official binary): namespace separation, the pre-official
guest-loopback proof, host loopback/external-egress denial, read-only
mappings, resource enforcement, escaped-descendant cleanup, stop/timeout,
driver loss, supervisor loss, and the two launcher modes end to end. Missing
prerequisites after the explicit opt-in are failures, never skips. A C
compiler is NOT required here (unlike the L5 containment gate): the stand-in
executable is the payload interpreter.
"""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    'run_claude_probe_linux', ROOT / 'scripts' / 'run_claude_probe_linux.py')
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

RUNNER_ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_LINUX_PROBE_RUNNER') == '1'
CGROUP_ROOT_ENV = 'POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT'


# --------------------------------------------------------------------------
# Synthetic plan construction (worker I's emitted v2 schema)
# --------------------------------------------------------------------------

def base_plan():
    """A minimal structurally valid v2 plan with placeholder host paths."""
    plan = {
        'schema': 'research-linux-launch-v2',
        'generation': 'config_only_not_executed',
        'runner': {'bwrap_version': '0.11.1',
                   'execution': 'outer_runner_owned_separately',
                   'supervision': 'outside_workload_cgroup'},
        'image': {'sha256': 'a' * 64, 'bytes': 1234, 'version': '2.1.278',
                  'platform': 'linux-x86_64', 'member': 'claude',
                  'runtime_interp': '/lib64/ld-linux-x86-64.so.2',
                  'runtime_needed': ['libc.so.6'],
                  'closure_derived_from': 'image_bytes'},
        'namespaces': list(runner.NAMESPACES),
        'network': {'mode': 'loopback_only', 'external_egress': 'unavailable',
                    'address': '127.0.0.1',
                    'loopback': 'automatic_under_unshare_net_no_ip_command'},
        'mounts': [
            {'role': 'INPUT', 'host': '/opt/synth/input', 'guest': '/pal-input',
             'readonly': True, 'kind': 'bind'},
            {'role': 'IMAGE', 'host': '/opt/synth/image',
             'guest': '/pal-claude-image', 'readonly': True, 'kind': 'bind'},
            {'role': 'CONTROL', 'host': '/opt/synth/control',
             'guest': '/pal-control', 'readonly': True, 'kind': 'bind'},
            {'role': 'OUTPUT', 'host': '/opt/synth/output',
             'guest': '/pal-output', 'readonly': False, 'kind': 'tmpfs',
             'size_limit_bytes': runner.OUTPUT_BYTES,
             'host_role': 'export_destination'},
            {'role': 'SCRATCH', 'host': None, 'guest': '/pal-scratch',
             'readonly': False, 'kind': 'tmpfs',
             'size_limit_bytes': runner.SCRATCH_BYTES},
            {'role': 'TMP', 'host': None, 'guest': '/tmp', 'readonly': False,
             'kind': 'tmpfs', 'size_limit_bytes': runner.TMP_BYTES}],
        'export': {'destination': '/opt/synth/output',
                   'bounded_bytes': runner.EXPORT_CAP_BYTES,
                   'creation': 'exclusive_no_follow',
                   'mounted_writable_in_namespace': False},
        'launcher': {'path': '/opt/synth/control/official-probe.sh',
                     'sha256': 'e' * 64, 'bytes': 400},
        'runtime_binds': [
            {'guest': '/bin/sh', 'mode': 'ro', 'source': '/usr/bin/dash',
             'sha256': 'b' * 64, 'bytes': 200},
            {'guest': '/lib/x86_64-linux-gnu/libc.so.6', 'mode': 'ro',
             'source': '/lib/x86_64-linux-gnu/libc.so.6', 'sha256': 'c' * 64,
             'bytes': 300}],
        'runtime_layout': {
            'guest_paths': 'canonical', 'ld_library_path': 'not_used',
            'launcher_externals': 'shell_builtins_and_payload_python_only',
            'library_search': ['/lib/x86_64-linux-gnu', '/usr/lib'],
            'shell_guest': '/bin/sh', 'shell_source': '/usr/bin/dash'},
        'environment': {'clearenv': True, 'setenv': {'PATH': '/usr/bin:/bin'}},
        'modes': [
            {'mode': 'qualify-version',
             'selection': 'outer_runner_final_command_replacement',
             'command': ['/pal-claude-image/claude', '--version'],
             'expected_banner': '2.1.278 (Claude Code)',
             'synthetic_request': False, 'depends_on': []},
            {'mode': 'official-six', 'selection': 'plan_argv_final_command',
             'command': ['/pal-control/official-probe.sh',
                         '--isolated-host-attested'],
             'expected_banner': None, 'synthetic_request': True,
             'depends_on': ['qualify-version']}],
        'excluded_host_surfaces': ['agent_sockets', 'user_home'],
        'argv': None,
        'bounds': {'memory_mb': 4096, 'memory_swap_max': 0, 'pids_max': 64,
                   'deadline_seconds': 900,
                   'cgroup_controls': 'require_qualification_before_run'},
        'official_cli_executed': False,
        'activation_authorized': False}
    plan['argv'] = runner.canonical_argv(plan)
    return plan


def qualify_command_for(code):
    """The synthetic stand-in's qualify-version command (sealed image + args)."""
    return ['/pal-claude-image/claude', '-S', '-c', code]


def write_plan(path, plan):
    (Path(path).parent).mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(plan, indent=2) + '\n', encoding='ascii')
    return Path(path)


def image_manifest_for(member_path):
    data = Path(member_path).read_bytes()
    return {'schema': 'claude-probe-image-linux-v1', 'path': 'claude',
            'sha256': sha256(data).hexdigest(), 'bytes': len(data),
            'version': '2.1.278', 'platform': 'linux-x86_64'}


def environment_manifest_for(payload_root):
    root = Path(payload_root)
    entries = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.name != 'environment-manifest.json':
            data = path.read_bytes()
            entries.append({'path': path.relative_to(root).as_posix(),
                            'bytes': len(data), 'sha256': sha256(data).hexdigest()})
    return {'schema': 'claude-probe-environment-v1',
            'source_commit': '0' * 40, 'source_tree': '0' * 40,
            'dependencies': {}, 'python': 'synthetic',
            'official_cli_included': False, 'activation_authorized': False,
            'files': entries}


# --------------------------------------------------------------------------
# Non-native unit tests (green on every host)
# --------------------------------------------------------------------------

def test_v1_and_unknown_schemas_refused(tmp_path):
    v1 = base_plan()
    v1['schema'] = 'claude-probe-namespace-linux-v1'
    assert runner.plan_problem(v1) == 'plan_schema_v1_refused'
    unknown = base_plan()
    unknown['schema'] = 'research-linux-launch-v3'
    assert runner.plan_problem(unknown) == 'plan_schema_unsupported'
    path = write_plan(tmp_path / 'v1.json', v1)
    with pytest.raises(ValueError, match='plan_schema_v1_refused'):
        runner.load_plan(path)


def test_duplicate_manifest_keys_refused(tmp_path):
    path = tmp_path / 'dup.json'
    path.write_text('{"schema": "a", "schema": "b"}', encoding='ascii')
    with pytest.raises(ValueError, match='plan_invalid_json'):
        runner.load_plan(path)


@pytest.mark.parametrize('mutate,expected', [
    ({'generation': 'executed'}, 'plan_invalid'),
    ({'runner': {'bwrap_version': '0.10.0',
                 'execution': 'outer_runner_owned_separately',
                 'supervision': 'outside_workload_cgroup'}},
     'plan_runner_invalid'),
    ({'bounds': dict(base_plan()['bounds'], memory_mb=8192)},
     'plan_bounds_invalid'),
    ({'bounds': dict(base_plan()['bounds'], deadline_seconds=1800)},
     'plan_bounds_invalid'),
    ({'export': dict(base_plan()['export'],
                     destination='/opt/synth/input/export')},
     'plan_export_invalid'),
    ({'environment': {'clearenv': True,
                      'setenv': {'PATH': '/usr/local/bin:/usr/bin:/bin'}}},
     'plan_environment_invalid'),
])
def test_plan_tampering_refused(mutate, expected):
    plan = base_plan()
    plan.update(mutate)
    plan['argv'] = runner.canonical_argv(plan)
    assert runner.plan_problem(plan) == expected, plan_problem(plan)


@pytest.mark.parametrize('mutate,expected', [
    ({'runtime_binds': [{'guest': '/lib64/libc.so.6', 'mode': 'rw',
                         'source': '/lib64/libc.so.6', 'sha256': 'd' * 64,
                         'bytes': 300}]}, 'plan_runtime_binds_invalid'),
    ({'mounts': [dict(mount, size_limit_bytes=1288490188)
                 if mount['role'] == 'OUTPUT' else mount
                 for mount in base_plan()['mounts']]}, 'plan_mounts_invalid'),
    ({'mounts': [dict(mount, kind='bind', host='/opt/synth/output')
                 if mount['role'] == 'OUTPUT' else mount
                 for mount in base_plan()['mounts']]}, 'plan_mounts_invalid'),
])
def test_plan_tampering_rebuilds_argv(mutate, expected):
    plan = base_plan()
    plan.update(mutate)
    plan['argv'] = runner.canonical_argv(plan)
    assert runner.plan_problem(plan) == expected, plan_problem(plan)


def test_modes_contract_enforced():
    plan = base_plan()
    assert runner.plan_problem(plan) is None
    for bad in (
            {'mode': 'batch'},
            {'command': ['/pal-control/official-probe.sh',
                         '--isolated-host-attested']},
            {'command': ['/bin/false', '--version']},
            {'synthetic_request': True},
            {'expected_banner': '9.9.9 (Claude Code)'}):
        broken = base_plan()
        broken['modes'][0].update(bad)
        assert runner.plan_problem(broken) == 'plan_modes_invalid', bad
    for bad in (
            {'mode': 'official-twelve'},
            {'command': ['/pal-control/official-probe.sh']},
            {'command': ['/pal-claude-image/claude', '-p']},
            {'synthetic_request': False},
            {'depends_on': []}):
        broken = base_plan()
        broken['modes'][1].update(bad)
        assert runner.plan_problem(broken) == 'plan_modes_invalid', bad


def test_argv_must_match_canonical_reconstruction():
    plan = base_plan()
    assert runner.plan_problem(plan) is None
    for mutation in (
            lambda argv: argv[:-1],                                # dropped tail
            lambda argv: argv + ['--extra-flag'],
            lambda argv: [argv[0]] + argv[2:],                     # dropped unshare
            lambda argv: [argv[0]] + ['--bind', '/x', '/pal-x'] + argv[1:],
            lambda argv: [token for token in argv if token != '--die-with-parent'],
            lambda argv: [token.replace('--size', '--sizelimit')
                          if token == '--size' else token for token in argv],
            lambda argv: [argv[0]] + argv[1:-2]
                         + ['ip', 'link', 'set', 'lo', 'up',
                            '/pal-control/official-probe.sh',
                            '--isolated-host-attested'],
    ):
        broken = base_plan()
        broken['argv'] = mutation(list(plan['argv']))
        assert runner.plan_problem(broken) == 'plan_argv_invalid', broken['argv']


def test_deadline_override_raise_only(monkeypatch):
    monkeypatch.delenv(runner.DEADLINE_ENV, raising=False)
    assert runner.probe_deadline(900) == 900
    monkeypatch.setenv(runner.DEADLINE_ENV, '1200')
    assert runner.probe_deadline(900) == 1200
    monkeypatch.setenv(runner.DEADLINE_ENV, '899')
    with pytest.raises(RuntimeError, match='below the reviewed floor'):
        runner.probe_deadline(900)
    monkeypatch.setenv(runner.DEADLINE_ENV, 'later')
    with pytest.raises(RuntimeError, match='not an integer'):
        runner.probe_deadline(900)


def test_holder_wrap_forms():
    launcher = runner.wrap_guest_entry(['/pal-control/official-probe.sh',
                                        '--isolated-host-attested'])
    assert launcher.startswith(
        "'/pal-control/official-probe.sh' '--isolated-host-attested' ;")
    assert "printf \"%s\\n\" \"$pal_holder_status\"" in launcher
    assert ' > /pal-output/pal-holder-status ' in launcher
    assert 'IFS= read -r pal_holder_hold' in launcher
    assert launcher.rstrip().endswith('exit "$pal_holder_status"')
    version = runner.wrap_guest_entry(['/pal-claude-image/claude', '--version'])
    assert version.startswith("'/pal-claude-image/claude' '--version' ;")
    quoted = runner.wrap_guest_entry(["/pal-input/it's.py", 'x y'])
    assert "'/pal-input/it'\\''s.py' 'x y' ;" in quoted


def test_derived_execution_applies_exactly_the_two_deviations():
    plan = base_plan()
    canonical = list(plan['argv'])
    executed = runner.derive_executed_argv(plan, 'official-six', 123,
                                           '/usr/bin/bwrap')
    assert executed[0] == '/usr/bin/bwrap'
    assert '--ro-bind-data' in executed and '123' in executed
    assert '/opt/synth/image' not in executed
    expected = ['/usr/bin/bwrap'] + canonical[1:]
    index = expected.index('/opt/synth/image')
    expected[index - 1:index + 2] = ['--perms', '0555', '--ro-bind-data', '123',
                                     '/pal-claude-image/claude']
    expected = expected[:-2] + ['/bin/sh', '-c', runner.wrap_guest_entry(
        plan['modes'][1]['command'])]
    assert executed == expected
    qualify = runner.derive_executed_argv(plan, 'qualify-version', 7,
                                          '/usr/bin/bwrap')
    assert qualify[-3:] == ['/bin/sh', '-c', runner.wrap_guest_entry(
        plan['modes'][0]['command'])]
    assert qualify[qualify.index('--ro-bind-data') + 1] == '7'
    tampered = base_plan()
    tampered['argv'] = canonical[:-2]
    with pytest.raises(ValueError, match='plan_argv_invalid'):
        runner.derive_executed_argv(tampered, 'official-six', 5, '/usr/bin/bwrap')


def test_image_manifest_pure_validation():
    good = image_manifest_for(Path(__file__))
    assert runner.image_manifest_problem(good) is None
    for mutate in (
            {'bytes': '1234'}, {'sha256': 'XYZ'}, {'version': '2.1.279'},
            {'platform': 'linux-aarch64'}, {'path': 'claude2'},
            {'schema': 'claude-probe-image-linux-v2'}):
        bad = dict(good)
        bad.update(mutate)
        assert runner.image_manifest_problem(bad) == 'probe_image_manifest_invalid'
    extra = dict(good)
    extra['note'] = 'x'
    assert runner.image_manifest_problem(extra) == 'probe_image_manifest_invalid'
    if sys.platform != 'linux':
        with pytest.raises(ValueError, match='runner_platform_unsupported'):
            runner.verify_image_admission(base_plan()['image'], '/opt/synth/image')


def test_environment_inventory_verification(tmp_path):
    root = tmp_path / 'payload'
    (root / 'sub').mkdir(parents=True)
    (root / 'a.py').write_bytes(b'print(1)\n')
    (root / 'sub' / 'b.txt').write_bytes(b'B' * 32)
    (root / 'environment-manifest.json').write_text(
        json.dumps(environment_manifest_for(root)) + '\n', encoding='utf-8')
    result = runner.verify_environment_inventory(root)
    assert result['files'] == 2 and result['bytes'] == 9 + 32
    (root / 'extra.py').write_bytes(b'x')
    with pytest.raises(ValueError, match='probe_payload_unexpected_files'):
        runner.verify_environment_inventory(root)
    (root / 'extra.py').unlink()
    (root / 'a.py').write_bytes(b'print(2)\n')
    with pytest.raises(ValueError, match='probe_payload_manifest_invalid'):
        runner.verify_environment_inventory(root)


def _can_symlink():
    probe = Path(str(Path(__file__)) + '.link')
    try:
        probe.symlink_to(Path(__file__))
        probe.unlink()
        return True
    except (OSError, NotImplementedError):
        return False


def test_export_tree_exclusive_nofollow_and_cap(tmp_path):
    source = tmp_path / 'nsout'
    (source / 'nested').mkdir(parents=True)
    (source / 'top.txt').write_bytes(b'top')
    (source / 'nested' / 'inner.dat').write_bytes(b'inner')
    destination = tmp_path / 'export1'
    destination.mkdir()
    state = runner.export_output_tree(source, destination)
    assert [item['name'] for item in state['manifest']] == ['nested/inner.dat',
                                                            'top.txt']
    assert state['bytes'] == 8 and not state['unsafe']
    assert (destination / 'top.txt').read_bytes() == b'top'
    assert sha256((destination / 'nested' / 'inner.dat').read_bytes()).hexdigest() \
        == sha256(b'inner').hexdigest()
    with pytest.raises(ValueError, match='export_destination_not_empty'):
        runner.export_output_tree(source, destination)
    capped = tmp_path / 'export2'
    capped.mkdir()
    (source / 'big.bin').write_bytes(b'x' * 4096)
    state = runner.export_output_tree(source, capped, cap=100)
    assert state['limit_exceeded'] is True
    assert all(item['bytes'] <= 100 for item in state['manifest'])
    if _can_symlink():
        trapped = tmp_path / 'export3'
        trapped.mkdir()
        os.symlink('../../../../etc/passwd', source / 'evil')
        (source / 'run-record.json').write_bytes(b'forged')
        state = runner.export_output_tree(source, trapped)
        assert 'evil' in state['unsafe']
        assert 'run-record.json' in state['unsafe']
        assert not (trapped / 'evil').exists()
        assert not (trapped / 'run-record.json').exists()
        (source / 'evil').unlink()
        (source / 'run-record.json').unlink()


def test_native_probe_directories_preserve_evidence_and_reject_symlinks(tmp_path):
    """Codex arbitration (a): the native entry allocates six exclusively owned
    scenario directories via mktemp(numbered=False), so pytest's convenience
    `test_<name>current` alias never appears in the export tree; the exporter
    itself stays unchanged — zero unsafe entries required, every symlink it
    does encounter still fails the export."""
    from _pytest.tmpdir import TempPathFactory

    basetemp = tmp_path / 'pal-output' / 'pytest-tmp'
    basetemp.mkdir(parents=True)
    factory = TempPathFactory(
        given_basetemp=basetemp, retention_count=0, retention_policy='all',
        trace=lambda *args, **kwargs: None, _ispytest=True)

    modes = ('success', 'rate_limit', 'server_error',
             'invalid_action', 'tool_use', 'truncated')
    for index, mode in enumerate(modes):
        case_dir = factory.mktemp(f'claude-probe-{index}', numbered=False)
        root = case_dir / 'claude-probe'
        root.mkdir(parents=True)
        (root / 'evidence.bin').write_bytes(f'proof-{mode}'.encode())
        sibling = case_dir / 'claude-probe-diagnostics'
        sibling.mkdir()
        (sibling / 'server-transcript.json').write_bytes(b'{"transcript":[]}')
    # (1) Six ordinary directories; no *current alias exists.
    entries = sorted(item.name for item in basetemp.iterdir())
    assert entries == [f'claude-probe-{index}' for index in range(6)]
    for item in basetemp.iterdir():
        assert item.is_dir() and not item.is_symlink()
    # (2) Repeating one allocation raises with existing evidence unchanged.
    with pytest.raises(FileExistsError):
        factory.mktemp('claude-probe-0', numbered=False)
    assert (basetemp / 'claude-probe-0' / 'claude-probe'
            / 'evidence.bin').read_bytes() == b'proof-success'
    # (3) The complete set exports with zero unsafe entries.
    destination = tmp_path / 'export-clean'
    destination.mkdir()
    state = runner.export_output_tree(basetemp.parent, destination)
    assert state['unsafe'] == [] and state['limit_exceeded'] is False
    names = {item['name'] for item in state['manifest']}
    for index in range(6):
        assert f'pytest-tmp/claude-probe-{index}/claude-probe/evidence.bin' in names
        assert (f'pytest-tmp/claude-probe-{index}/claude-probe-diagnostics/'
                'server-transcript.json') in names
    # (4) An injected internal alias and an external-pointer symlink still
    # both report unsafe in a FRESH destination, with nothing crossing.
    if _can_symlink():
        os.symlink('claude-probe-0',
                   basetemp / 'test_supplied_claude_profile_lcurrent')
        external = tmp_path / 'external-sentinel'
        external.write_bytes(b'EXTERNAL-SECRET')
        os.symlink('../../../external-sentinel', basetemp / 'escape')
        hostile = tmp_path / 'export-hostile'
        hostile.mkdir()
        state = runner.export_output_tree(basetemp.parent, hostile)
        assert set(state['unsafe']) >= {
            'pytest-tmp/test_supplied_claude_profile_lcurrent',
            'pytest-tmp/escape'}
        assert not (hostile / 'pytest-tmp'
                    / 'test_supplied_claude_profile_lcurrent').exists()
        assert not (hostile / 'pytest-tmp' / 'escape').exists()
        blob = b''.join(file.read_bytes()
                        for file in sorted(hostile.rglob('*')) if file.is_file())
        assert b'EXTERNAL-SECRET' not in blob
        for index in range(6):
            assert (hostile / 'pytest-tmp' / f'claude-probe-{index}'
                    / 'claude-probe' / 'evidence.bin').exists()


def _xml_attr(value):
    return '"' + value.replace('&', '&amp;').replace('"', '&quot;') + '"'


def _junit_document(modes, *, skip=False, failure=False):
    cases = []
    for mode in modes:
        case = ('<testcase classname="tests.test_research_claude_profile_native"'
                ' name="case_%s">' % mode)
        if skip:
            case += '<skipped type="pytest.skip" message="opt-in"/>'
        if failure:
            case += ('<failure type="AssertionError">research_process_signaled'
                     '</failure>')
        case += '</testcase>'
        cases.append(case)
    props = ''.join(
        '<property name="claude_cli_probe" value=%s/>' % _xml_attr(
            json.dumps({'schema_version': 'claude-cli-probe-v2', 'mode': mode,
                        'activation_authorized': False},
                       separators=(',', ':')))
        for mode in modes)
    return ('<?xml version="1.0"?><testsuite tests="%d"><properties>%s'
            '</properties>%s</testsuite>' % (len(modes), props, ''.join(cases)))


def _gate_record(**execution):
    fields = {'holder_status': '0'}
    fields.update(execution)
    return {'stop_condition': 'completed', 'execution': fields}


def _write_export_set(directory, *, junit=_junit_document(runner.SCENARIOS),
                      exit_code='0\n'):
    directory.mkdir(parents=True, exist_ok=True)
    if junit is not None:
        (directory / 'junit.xml').write_text(junit, encoding='ascii')
    if exit_code is not None:
        (directory / 'exit-code.txt').write_text(exit_code, encoding='ascii')


def test_official_six_gate_accepts_only_structural_success(tmp_path):
    export = tmp_path / 'good'
    _write_export_set(export)
    assert runner.gate_official_six(export, _gate_record()) == []
    deadline_record = _gate_record()
    deadline_record['stop_condition'] = 'deadline_exceeded'
    cases = {
        'exit_code_not_zero': dict(exit_code='1\n'),
        'exit_code_missing': dict(exit_code=None),
        'gate_junit_invalid': dict(junit='<not-xml'),
        'junit_structure_rejected': dict(
            junit=_junit_document(runner.SCENARIOS, skip=True)),
        'observation_multiset_rejected': dict(
            junit=_junit_document(runner.SCENARIOS[:5])),
        'launcher_status_not_zero': dict(record=_gate_record(holder_status='3')),
        'stop_condition_deadline_exceeded': dict(record=deadline_record),
    }
    for expected, kwargs in cases.items():
        directory = tmp_path / expected
        record = kwargs.pop('record', _gate_record())
        _write_export_set(directory, **kwargs)
        assert expected in runner.gate_official_six(directory, record), expected


def test_official_six_gate_rejects_bad_observations(tmp_path):
    def document(observation):
        prop = ('<property name="claude_cli_probe" value=%s/>' % _xml_attr(
            json.dumps(observation, separators=(',', ':'))))
        cases = ''.join('<testcase name="c%d"/>' % index for index in range(6))
        return ('<?xml version="1.0"?><testsuite tests="6"><properties>%s'
                '</properties>%s</testsuite>' % (prop * 6, cases))

    v1 = tmp_path / 'v1obs'
    _write_export_set(v1, junit=document(
        {'schema_version': 'claude-cli-probe-v1', 'mode': 'success',
         'activation_authorized': False}))
    assert 'observation_schema_rejected' in runner.gate_official_six(
        v1, _gate_record())
    activated = tmp_path / 'activated'
    _write_export_set(activated, junit=document(
        {'schema_version': 'claude-cli-probe-v2', 'mode': 'success',
         'activation_authorized': True}))
    assert 'observation_activation_rejected' in runner.gate_official_six(
        activated, _gate_record())


def test_qualify_version_gate_banner():
    mode_entry = base_plan()['modes'][0]
    record = _gate_record(stdout_bytes_value=b'2.1.278 (Claude Code)\n',
                          stderr_bytes=0)
    assert runner.gate_qualify_version(record, mode_entry) == []
    mismatch = _gate_record(stdout_bytes_value=b'9.9.9 (Claude Code)\n',
                            stderr_bytes=0)
    assert 'version_banner_mismatch' in runner.gate_qualify_version(
        mismatch, mode_entry)
    noisy = _gate_record(stdout_bytes_value=b'2.1.278 (Claude Code)\n',
                         stderr_bytes=5)
    assert 'version_stderr_nonzero' in runner.gate_qualify_version(
        noisy, mode_entry)
    crashed = _gate_record(stdout_bytes_value=b'', stderr_bytes=0,
                           holder_status='139')
    findings = runner.gate_qualify_version(crashed, mode_entry)
    assert 'version_banner_mismatch' in findings
    assert 'version_status_not_zero' in findings


def test_cli_check_plan_contract(tmp_path, capsys):
    good = write_plan(tmp_path / 'good.json', base_plan())
    assert runner.main(['check-plan', '--plan', str(good)]) == 0
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert result['status'] == 'plan_validated'
    assert result['modes'] == ['qualify-version', 'official-six']
    assert result['activation_authorized'] is False
    v1 = base_plan()
    v1['schema'] = 'claude-probe-namespace-linux-v1'
    bad = write_plan(tmp_path / 'v1.json', v1)
    assert runner.main(['check-plan', '--plan', str(bad)]) == 1
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert result == {'status': 'BLOCKED', 'reason': 'plan_schema_v1_refused',
                      'activation_authorized': False}


_gen_spec = importlib.util.spec_from_file_location(
    'claude_probe_environment', ROOT / 'scripts/claude_probe_environment.py')
gen = importlib.util.module_from_spec(_gen_spec)
_gen_spec.loader.exec_module(gen)


def test_emitted_generator_plan_shape_accepted():
    """Compatibility pin: the runner accepts the preparation generator's v2
    output shape. Values are taken from the generator module's own constants
    (not hand-copied), and the argv is asserted to match the generator's
    exact emission order; only the measured identities are synthetic."""
    binds = [  # the generator emits runtime binds sorted by guest path
        {'guest': gen.LINUX_GUEST_SHELL, 'mode': 'ro',
         'source': gen.LINUX_SHELL_HOST_PATH, 'sha256': 'b' * 64,
         'bytes': 120000},
        {'guest': '/lib64/ld-linux-x86-64.so.2', 'mode': 'ro',
         'source': '/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2',
         'sha256': 'c' * 64, 'bytes': 240000},
        {'guest': gen.LINUX_GUESTS['input'] + '/python/bin/python3',
         'mode': 'ro', 'source': '/opt/payload/python/bin/python3',
         'sha256': 'd' * 64, 'bytes': 8000000}]
    launcher_guest = gen.LINUX_GUESTS['control'] + '/' + gen.LINUX_LAUNCHER_NAME
    image_guest = gen.LINUX_GUESTS['image'] + '/' + gen.LINUX_IMAGE_MEMBER
    # The launcher digest is a pure derivation from the validated image
    # identity (worker I's public official_launcher helper), exactly like the
    # generator's plan emission and its own validator's recomputation.
    launcher_bytes = gen.official_launcher(
        dict(sha256='a' * 64, bytes=234119480), platform='linux')
    launcher_block = {'path': '/opt/control/' + gen.LINUX_LAUNCHER_NAME,
                      'sha256': sha256(launcher_bytes).hexdigest(),
                      'bytes': len(launcher_bytes)}
    argv = ['bwrap', '--unshare-user', '--unshare-ipc', '--unshare-pid',
            '--unshare-net', '--unshare-uts', '--die-with-parent',
            '--new-session', '--cap-drop', 'ALL', '--clearenv',
            '--setenv', 'PATH', gen.LINUX_CHILD_ENVIRONMENT['PATH'],
            '--tmpfs', '/', '--dev', '/dev', '--proc', '/proc',
            '--ro-bind', '/opt/payload', gen.LINUX_GUESTS['input'],
            '--ro-bind', '/opt/image', gen.LINUX_GUESTS['image'],
            '--ro-bind', '/opt/control', gen.LINUX_GUESTS['control'],
            '--size', str(gen.LINUX_SCRATCH_BYTES),
            '--tmpfs', gen.LINUX_GUESTS['scratch'],
            '--size', str(gen.LINUX_TMP_BYTES), '--tmpfs', gen.LINUX_GUESTS['tmp'],
            '--size', str(gen.LINUX_EXPORT_BYTES),
            '--tmpfs', gen.LINUX_GUESTS['output'],
            *(part for bind in binds
              for part in ('--ro-bind', bind['source'], bind['guest'])),
            launcher_guest, '--isolated-host-attested']
    plan = {
        'schema': gen.LINUX_PLAN_SCHEMA,
        'generation': 'config_only_not_executed',
        'runner': {'bwrap_version': gen.LINUX_BWRAP_VERSION,
                   'execution': 'outer_runner_owned_separately',
                   'supervision': 'outside_workload_cgroup'},
        'image': {'sha256': 'a' * 64, 'bytes': 234119480,
                  'version': gen.OFFICIAL_IMAGE_VERSION,
                  'platform': gen.LINUX_IMAGE_PLATFORM,
                  'member': gen.LINUX_IMAGE_MEMBER,
                  'runtime_interp': '/lib64/ld-linux-x86-64.so.2',
                  'runtime_needed': ['libc.so.6', 'libgcc_s.so.1'],
                  'closure_derived_from': 'image_bytes'},
        'namespaces': list(gen.LINUX_NAMESPACES),
        'network': {'mode': 'loopback_only', 'external_egress': 'unavailable',
                    'address': '127.0.0.1', 'loopback': gen.LINUX_LOOPBACK_MODE},
        'mounts': [
            {'role': 'INPUT', 'host': '/opt/payload',
             'guest': gen.LINUX_GUESTS['input'], 'readonly': True,
             'kind': 'bind'},
            {'role': 'IMAGE', 'host': '/opt/image',
             'guest': gen.LINUX_GUESTS['image'], 'readonly': True,
             'kind': 'bind'},
            {'role': 'CONTROL', 'host': '/opt/control',
             'guest': gen.LINUX_GUESTS['control'], 'readonly': True,
             'kind': 'bind'},
            {'role': 'OUTPUT', 'host': '/opt/output',
             'guest': gen.LINUX_GUESTS['output'], 'readonly': False,
             'kind': 'tmpfs', 'size_limit_bytes': gen.LINUX_EXPORT_BYTES,
             'host_role': 'export_destination'},
            {'role': 'SCRATCH', 'host': None,
             'guest': gen.LINUX_GUESTS['scratch'], 'readonly': False,
             'kind': 'tmpfs', 'size_limit_bytes': gen.LINUX_SCRATCH_BYTES},
            {'role': 'TMP', 'host': None, 'guest': gen.LINUX_GUESTS['tmp'],
             'readonly': False, 'kind': 'tmpfs',
             'size_limit_bytes': gen.LINUX_TMP_BYTES}],
        'export': {'destination': '/opt/output',
                   'bounded_bytes': gen.LINUX_EXPORT_BYTES,
                   'creation': 'exclusive_no_follow',
                   'mounted_writable_in_namespace': False},
        'launcher': launcher_block,
        'runtime_binds': binds,
        'runtime_layout': {
            'guest_paths': 'canonical', 'ld_library_path': 'not_used',
            'launcher_externals': 'shell_builtins_and_payload_python_only',
            'library_search': list(gen.LINUX_RUNTIME_LIBRARY_DIRS),
            'shell_guest': gen.LINUX_GUEST_SHELL,
            'shell_source': gen.LINUX_SHELL_HOST_PATH},
        'environment': {'clearenv': True,
                        'setenv': dict(gen.LINUX_CHILD_ENVIRONMENT)},
        'modes': [
            {'mode': 'qualify-version',
             'selection': 'outer_runner_final_command_replacement',
             'command': [image_guest, '--version'],
             'expected_banner': gen.OFFICIAL_IMAGE_VERSION + ' (Claude Code)',
             'synthetic_request': False, 'depends_on': []},
            {'mode': 'official-six', 'selection': 'plan_argv_final_command',
             'command': [launcher_guest, '--isolated-host-attested'],
             'expected_banner': None, 'synthetic_request': True,
             'depends_on': ['qualify-version']}],
        'excluded_host_surfaces': list(gen.LINUX_EXCLUDED_SURFACES),
        'argv': argv,
        'bounds': {'memory_mb': gen.LINUX_MEMORY_MB, 'memory_swap_max': 0,
                   'pids_max': gen.LINUX_PIDS_MAX,
                   'deadline_seconds': gen.LINUX_DEADLINE_SECONDS,
                   'cgroup_controls': 'require_qualification_before_run'},
        'official_cli_executed': False,
        'activation_authorized': False}
    # The runner's pinned policy values must equal the generator's constants.
    assert runner.PLAN_SCHEMA == gen.LINUX_PLAN_SCHEMA
    assert runner.BWRAP_VERSION == gen.LINUX_BWRAP_VERSION
    assert (runner.SCRATCH_BYTES, runner.TMP_BYTES, runner.OUTPUT_BYTES) \
        == (gen.LINUX_SCRATCH_BYTES, gen.LINUX_TMP_BYTES, gen.LINUX_EXPORT_BYTES)
    assert runner.EXPORT_CAP_BYTES == gen.LINUX_EXPORT_BYTES
    assert runner.PIDS_MAX == gen.LINUX_PIDS_MAX
    assert runner.MEMORY_MAX_BYTES == gen.LINUX_MEMORY_MB * 1024 * 1024
    assert runner.DEFAULT_DEADLINE_SECONDS == gen.LINUX_DEADLINE_SECONDS
    assert runner.NAMESPACES == gen.LINUX_NAMESPACES
    assert len(gen.LINUX_RUNTIME_LIBRARY_DIRS) == 6
    assert len(gen.LINUX_EXCLUDED_SURFACES) == 8
    # The launcher block mirrors the generator's pure derivation exactly.
    assert launcher_block['sha256'] == sha256(launcher_bytes).hexdigest()
    assert launcher_block['bytes'] == len(launcher_bytes)
    assert launcher_block['path'] == '/opt/control/' + gen.LINUX_LAUNCHER_NAME
    assert runner.plan_problem(plan) is None, runner.plan_problem(plan)
    assert runner.canonical_argv(plan) == argv


def test_gate_release_value_error_still_tears_down_and_records(tmp_path, monkeypatch):
    """MINOR 1 regression: a fail()-raised ValueError during cgroup placement
    must fall through to the common teardown and run-record path instead of
    escaping run_outer_probe (bootstrap child unreaped, sealed memfd open,
    pal-l7-* cgroup left behind, no evidence)."""
    fake_root = tmp_path / 'cgroup-root'
    fake_root.mkdir()
    (fake_root / 'cgroup.controllers').write_text('cpuset cpu io memory pids\n',
                                                  encoding='ascii')
    export = tmp_path / 'OUTPUT'
    export.mkdir()
    export_posix = export.as_posix()
    plan = base_plan()
    plan['mounts'][3]['host'] = export_posix
    plan['export']['destination'] = export_posix
    plan['argv'] = runner.canonical_argv(plan)
    plan_path = write_plan(tmp_path / 'plan.json', plan)
    _relax_linux_abspath(monkeypatch)

    teardown = {'signal_kill': 0, 'remove': 0}

    class FakeCgroup:
        limits = (('memory.max', str(runner.MEMORY_MAX_BYTES)),
                  ('memory.swap.max', '0'), ('pids.max', str(runner.PIDS_MAX)))
        baseline_events = {}

        def __init__(self, root, allocation):
            self.root = str(root)
            self.path = str(Path(root) / allocation)

        def create(self):
            pass

        def admit(self, pid):
            if _RAISE is ValueError:
                raise ValueError('cgroup_admission_failed')
            raise OSError('placement refused')

        def members(self):
            return []

        def events(self):
            return {}

        def resource_limit_events(self):
            return []

        def signal_kill(self):
            teardown['signal_kill'] += 1

        def wait_empty(self, deadline):
            return True

        def remove(self):
            teardown['remove'] += 1

    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setenv(CGROUP_ROOT_ENV, str(fake_root))
    monkeypatch.setattr(runner, 'bwrap_identity', lambda: dict(
        path='/usr/bin/bwrap', version='0.11.1', sha256='e' * 64, bytes=1000))
    monkeypatch.setattr(runner, 'verify_image_admission',
                        lambda image, image_dir: dict(
                            schema='claude-probe-image-linux-v1', path='claude',
                            sha256=image['sha256'], bytes=image['bytes'],
                            version='2.1.278', platform='linux-x86_64'))
    monkeypatch.setattr(runner, 'seal_verified_file', lambda *a, **k: 123)
    monkeypatch.setattr(runner, 'verify_environment_inventory',
                        lambda root: dict(files=1, bytes=2, source_commit='0' * 40))
    monkeypatch.setattr(runner, 'verify_runtime_binds', lambda plan: [])
    monkeypatch.setattr(runner, 'verify_pinned_file', lambda *a, **k: b'\x7fELF')
    monkeypatch.setattr(runner, 'WorkloadCgroup', FakeCgroup)
    monkeypatch.setattr(os, 'fork', lambda: 424242, raising=False)
    monkeypatch.setattr(os, 'waitpid',
                        lambda *a, **k: (_ for _ in ()).throw(ChildProcessError()))
    for variant, expected in ((ValueError, 'cgroup_admission_failed'),
                              (OSError, 'gate_release_failed')):
        _RAISE = variant  # noqa: F841 - consumed by FakeCgroup.admit
        for name in ('run-record.json',):
            target = export / name
            if target.exists():
                target.unlink()
        teardown['signal_kill'] = teardown['remove'] = 0
        record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                        deadline_seconds=30,
                                        allocation='pal-l7-test-gatefail')
        assert expected in record['findings'], (variant, record['findings'])
        assert record['official_cli_launched'] is False
        assert record['accepted'] is False
        assert 'teardown_failed' not in record['findings']
        assert record['cgroup']['verified_empty'] is True
        assert teardown['signal_kill'] == 1 and teardown['remove'] == 1
        evidence = export / 'run-record.json'
        assert evidence.is_file(), 'run record must survive the gate failure'
        saved = json.loads(evidence.read_text(encoding='utf-8'))
        assert expected in saved['findings']
        assert saved['cgroup']['verified_empty'] is True
        assert saved['official_cli_launched'] is False


def _relax_linux_abspath(monkeypatch):
    """Allow forward-slash drive-absolute host paths in plan validation.

    The lexical guest-path rule is Linux-absolute; Windows-host unit tests
    that point mounts at real temp directories relax exactly that rule."""
    real_abspath = runner._linux_abspath

    def windows_tolerant_abspath(text):
        if real_abspath(text):
            return True
        return (type(text) is str
                and re.fullmatch(r'[A-Za-z]:/[^\\]{0,4000}', text) is not None
                and '..' not in text.split('/')
                and '%' not in text and '\x00' not in text)
    monkeypatch.setattr(runner, '_linux_abspath', windows_tolerant_abspath)


def test_launcher_block_required():
    """MINOR 3: the coordinated launcher-digest block is mandatory."""
    plan = base_plan()
    assert runner.plan_problem(plan) is None
    missing = {key: value for key, value in plan.items() if key != 'launcher'}
    assert runner.plan_problem(missing) == 'plan_invalid'
    for mutate in (
            {'path': '/opt/synth/control/other.sh'},
            {'path': None},
            {'sha256': 'NOT-HEX'},
            {'bytes': '400'},
            {'bytes': 0},
            {'sha256': 'e' * 63}):
        broken = base_plan()
        broken['launcher'].update(mutate)
        assert runner.plan_problem(broken) == 'plan_launcher_invalid', mutate
    extra = base_plan()
    extra['launcher']['note'] = 'x'
    assert runner.plan_problem(extra) == 'plan_launcher_invalid'


def test_launcher_admission_identity(tmp_path, monkeypatch):
    """Admission re-measures the on-disk launcher twin (mode 0755, digest,
    length) against the plan block; mismatches are refused with fixed codes."""
    monkeypatch.setattr(sys, 'platform', 'linux')
    _relax_linux_abspath(monkeypatch)
    # Windows chmod cannot express 0755 (writable files stat as 0666), so
    # translate exactly that case; every other mode passes through unchanged
    # and the exact-mode invariant is exercised on both platforms.
    real_simode = stat.S_IMODE

    def fake_simode(mode):
        if mode & 0o777 == 0o666:
            return 0o755
        return real_simode(mode)
    monkeypatch.setattr(runner.stat, 'S_IMODE', fake_simode)
    control = tmp_path / 'CONTROL'
    control.mkdir()
    launcher = control / 'official-probe.sh'
    launcher.write_text('#!/bin/sh\nexit 0\n', encoding='ascii')
    os.chmod(launcher, 0o755)
    data = launcher.read_bytes()
    sh_source = tmp_path / 'dash'
    sh_source.write_bytes(b'DASH')
    bind_source = tmp_path / 'libc.so.6'
    bind_source.write_bytes(b'LIBC')
    input_dir = tmp_path / 'INPUT'
    image_dir = tmp_path / 'IMAGE'
    input_dir.mkdir()
    image_dir.mkdir()
    plan = base_plan()
    plan['runtime_binds'] = [
        {'guest': '/bin/sh', 'mode': 'ro', 'source': sh_source.as_posix(),
         'sha256': sha256(b'DASH').hexdigest(), 'bytes': 4},
        {'guest': '/lib/x86_64-linux-gnu/libc.so.6', 'mode': 'ro',
         'source': bind_source.as_posix(),
         'sha256': sha256(b'LIBC').hexdigest(), 'bytes': 4}]
    for role, host in (('INPUT', input_dir), ('IMAGE', image_dir),
                       ('CONTROL', control)):
        for mount in plan['mounts']:
            if mount['role'] == role:
                mount['host'] = host.as_posix()
    plan['runtime_layout']['shell_source'] = sh_source.as_posix()
    plan['launcher'] = {'path': launcher.as_posix(),
                        'sha256': sha256(data).hexdigest(),
                        'bytes': len(data)}
    plan['argv'] = runner.canonical_argv(plan)
    assert runner.plan_problem(plan) is None
    measured = runner.verify_runtime_binds(plan)
    assert measured == [dict(guest='/bin/sh', sha256=sha256(b'DASH').hexdigest(),
                             bytes=4),
                        dict(guest='/lib/x86_64-linux-gnu/libc.so.6',
                             sha256=sha256(b'LIBC').hexdigest(), bytes=4)]
    swapped = dict(plan['launcher'],
                   sha256=sha256(data + b'swap').hexdigest(),
                   bytes=len(data) + 4)
    tampered = json.loads(json.dumps(plan))
    tampered['launcher'] = swapped
    with pytest.raises(ValueError, match='launcher_identity_mismatch'):
        runner.verify_runtime_binds(tampered)
    truncated = json.loads(json.dumps(plan))
    truncated['launcher'] = dict(plan['launcher'], bytes=len(data) - 1)
    with pytest.raises(ValueError, match='launcher_identity_mismatch'):
        runner.verify_runtime_binds(truncated)
    os.chmod(launcher, 0o544)  # no write bit: Windows stats it read-only
    with pytest.raises(ValueError, match='launcher_mode_invalid'):
        runner.verify_runtime_binds(plan)
    os.chmod(launcher, 0o755)


# --------------------------------------------------------------------------
# Native opt-in qualification (synthetic stand-ins; never the official binary)
# --------------------------------------------------------------------------

def require_native_runner():
    """Fail closed (never skip) when the explicit opt-in lacks prerequisites."""
    if not RUNNER_ENABLED:
        pytest.skip('explicit native probe-runner qualification is opt-in')
    problems = []
    if sys.platform != 'linux':
        problems.append('linux host required')
    if shutil.which('bwrap') is None:
        problems.append('bwrap containment executable required')
    root = os.environ.get(CGROUP_ROOT_ENV, '')
    if not root or not Path(root, 'cgroup.controllers').is_file():
        problems.append('%s must name a delegated cgroup v2 subtree with '
                        'memory and pids controllers' % CGROUP_ROOT_ENV)
    else:
        controllers = Path(root, 'cgroup.controllers').read_text().split()
        if 'memory' not in controllers or 'pids' not in controllers:
            problems.append('delegated cgroup subtree lacks memory/pids controllers')
    if problems:
        pytest.fail('probe runner prerequisites missing: ' + '; '.join(problems))


def _standin_interpreter():
    return str(Path(sys.executable).resolve())


_CLOSURE_PROBE = (
    'import json,sysconfig\n'
    'libs=set()\n'
    'for line in open("/proc/self/maps"):\n'
    '    parts=line.rstrip().split()\n'
    '    path=parts[-1] if parts else ""\n'
    '    if path.startswith("/") and (".so" in path or "ld-linux" in path):\n'
    '        libs.add(path)\n'
    'print(json.dumps({"libs": sorted(libs),'
    ' "stdlib": sysconfig.get_paths()["stdlib"]}))\n')


def _standin_closure(python):
    completed = subprocess.run([python, '-S', '-c', _CLOSURE_PROBE],
                               capture_output=True, check=True, timeout=60,
                               env={'PATH': '/usr/bin:/bin'})
    value = json.loads(completed.stdout.decode('utf-8'))
    value['prefix'] = str(Path(value['stdlib']).parent.parent)
    return value


GUEST_PROBE = r'''
import json,os,socket
res={'pid':os.getpid(),'uidmap':open('/proc/self/uid_map').read().strip(),
     'nodename':os.uname().nodename,
     'uts_ino':os.stat('/proc/self/ns/uts').st_ino,
     'host_pid_absent':not os.path.exists('/proc/'+os.environ['PAL_TEST_HOST_PID'])}
a=socket.socket();a.bind(('127.0.0.1',0));a.listen(1);port=a.getsockname()[1]
b=socket.create_connection(('127.0.0.1',port),3);c,_=a.accept();b.sendall(b'PAL7')
res['loopback']=(c.recv(4)==b'PAL7');b.close();c.close();a.close()
try:
    s=socket.create_connection(('127.0.0.1',int(os.environ['PAL_TEST_HOST_PORT'])),2)
    s.close();res['host_loopback_denied']=False
except OSError:res['host_loopback_denied']=True
try:
    s=socket.create_connection(('192.0.2.1',9),2);s.close();res['egress_denied']=False
except OSError:res['egress_denied']=True
for target,name in (('/pal-input/probe.py','input_readonly'),
                    ('/pal-claude-image/claude','image_readonly'),
                    ('/pal-control/official-probe.sh','control_readonly')):
    try:
        open(target,'a').close();res[name]=False
    except OSError:res[name]=True
try:
    open('/pal-output/write-test','w').write('x');res['output_writable']=True
except OSError:res['output_writable']=False
json.dump(res,open('/pal-output/guest-result.json','w'))
'''

GUEST_ESCAPE = r'''
import os,time
pid=os.fork()
if pid==0:
    open('/pal-output/survivor.txt','w').write(str(os.getpid()))
    time.sleep(120)
open('/pal-output/guest-result.json','w').write('{"escaped":%d}' % pid)
'''

GUEST_PIDS = r'''
import json,os,time
kids=[];err=None
try:
    for _ in range(200):
        pid=os.fork()
        if pid==0:
            time.sleep(60)
        kids.append(pid)
except OSError as error:
    err=error
json.dump({'forked':len(kids),'eagain':err is not None and err.errno==11,
           'errno':getattr(err,'errno',None)},
          open('/pal-output/guest-result.json','w'))
'''

GUEST_SLEEP = 'import time\ntime.sleep(600)\n'

PAYLOAD_WRITER = r'''
import json,os
modes=['success','rate_limit','server_error','invalid_action','tool_use','truncated']
props=''.join('<property name="claude_cli_probe" value=' +
    chr(34)+json.dumps({'schema_version':'claude-cli-probe-v2','mode':mode,
    'activation_authorized':False},separators=(',',':')).replace('&','&amp;')
    .replace('"','&quot;')+chr(34)+'/>' for mode in modes)
os.makedirs('/pal-output/pytest-tmp',exist_ok=True)
open('/pal-output/pytest.log','w').write('synthetic stand-in run\n')
open('/pal-output/exit-code.txt','x').write('0\n')
open('/pal-output/junit.xml','w').write('<?xml version="1.0"?><testsuite ' +
    'tests="6"><properties>'+props+'</properties>'+''.join(
    '<testcase classname="tests.test_research_claude_profile_native" ' +
    'name="case_'+mode+'"/>' for mode in modes)+'</testsuite>')
'''


def _elf_interp(path):
    """Bounded ELF64 read of PT_INTERP (the literal path exec requires)."""
    try:
        with open(path, 'rb') as stream:
            header = stream.read(64)
            if (len(header) != 64 or not header.startswith(b'\x7fELF')
                    or header[4] != 2 or header[5] != 1):
                return None
            phoff = int.from_bytes(header[32:40], 'little')
            phentsize = int.from_bytes(header[54:56], 'little')
            phnum = int.from_bytes(header[56:58], 'little')
            if phentsize != 56 or not 1 <= phnum <= 1024:
                return None
            stream.seek(phoff)
            phdrs = stream.read(56 * phnum)
            if len(phdrs) != 56 * phnum:
                return None
            for index in range(phnum):
                entry = phdrs[56 * index:56 * (index + 1)]
                if int.from_bytes(entry[0:4], 'little') != 3:  # PT_INTERP
                    continue
                offset = int.from_bytes(entry[8:16], 'little')
                size = int.from_bytes(entry[32:40], 'little')
                stream.seek(offset)
                raw = stream.read(size)
                if raw.endswith(b'\x00'):
                    return raw[:-1].decode('ascii')
        return None
    except (OSError, UnicodeDecodeError):
        return None


def build_synthetic_plan(tmp_path, *, mode='qualify-version', guest_code=None,
                         payload_files=None, launcher_body=None,
                         extra_child_env=None, allocation=None):
    """Assemble a runnable synthetic v2 plan around the interpreter stand-in.

    The v2 schema has no arbitrary read-only directory binds, so the stand-in
    interpreter's runtime lives INSIDE the payload tree exactly like the
    official INPUT layout (python/bin/python3 + python/lib/python3.x stdlib);
    the guest PYTHONHOME points at /pal-input/python. The sealed IMAGE member
    (a copy of the same interpreter) initializes against that payload runtime,
    which is why qualify-mode commands stay in the documented superset form
    (argv[0] == the sealed image) while still executing the probe code.
    """
    python = _standin_interpreter()
    closure = _standin_closure(python)
    image_dir = tmp_path / 'IMAGE'
    image_dir.mkdir()
    member = image_dir / 'claude'
    shutil.copyfile(python, member)
    os.chmod(member, 0o755)
    manifest = image_manifest_for(member)
    (image_dir / 'image-manifest.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='ascii')
    payload_root = tmp_path / 'INPUT'
    payload_root.mkdir()
    (payload_root / 'probe.py').write_text('stand-in payload marker\n',
                                           encoding='ascii')
    runtime = payload_root / 'python'
    (runtime / 'bin').mkdir(parents=True)
    shutil.copyfile(python, runtime / 'bin' / 'python3')
    os.chmod(runtime / 'bin' / 'python3', 0o755)
    stdlib = Path(closure['stdlib'])
    shutil.copytree(stdlib, runtime / 'lib' / stdlib.name, symlinks=False)
    prefix = Path(closure['prefix'])
    for shared in sorted(prefix.glob('lib/libpython*.so*')):
        if shared.is_file():
            shutil.copyfile(shared, runtime / 'lib' / shared.name)
    for name, text in (payload_files or {}).items():
        target = payload_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='ascii')
    (payload_root / 'environment-manifest.json').write_text(
        json.dumps(environment_manifest_for(payload_root), indent=2) + '\n',
        encoding='utf-8')
    control_dir = tmp_path / 'CONTROL'
    control_dir.mkdir()
    launcher = control_dir / 'official-probe.sh'
    if launcher_body is None:
        launcher_body = ('#!/bin/sh\nexec /pal-claude-image/claude -S'
                         ' /pal-input/write_evidence.py "$@"\n')
    launcher.write_text(launcher_body, encoding='ascii')
    os.chmod(launcher, 0o755)
    launcher_data = launcher.read_bytes()
    launcher_block = {'path': str(control_dir) + '/official-probe.sh',
                      'sha256': sha256(launcher_data).hexdigest(),
                      'bytes': len(launcher_data)}
    export_destination = tmp_path / 'OUTPUT'
    export_destination.mkdir()
    runtime_binds = []
    sh_source = str(Path('/bin/sh').resolve())
    data = Path(sh_source).read_bytes()
    runtime_binds.append({'guest': '/bin/sh', 'mode': 'ro',
                          'source': sh_source,
                          'sha256': sha256(data).hexdigest(),
                          'bytes': len(data)})
    lib_dirs = set()
    for lib in closure['libs']:
        info = Path(lib).stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or lib == python:
            continue
        data = Path(lib).read_bytes()
        runtime_binds.append({'guest': lib, 'mode': 'ro', 'source': lib,
                              'sha256': sha256(data).hexdigest(),
                              'bytes': len(data)})
        lib_dirs.add(str(Path(lib).parent))
    # The sandbox root is an empty tmpfs (no usrmerge symlinks), so every
    # exec'd ELF needs its interpreter bound at the LITERAL PT_INTERP path;
    # on usr-merged hosts that resolves onto the same file already bound at
    # its canonical path (one source, two guests, one identity).
    bound_guests = {bind['guest'] for bind in runtime_binds}
    for executable in (sh_source, python):
        interp = _elf_interp(executable)
        if interp is None or interp in bound_guests:
            continue
        real = str(Path(interp).resolve())
        data = Path(real).read_bytes()
        runtime_binds.append({'guest': interp, 'mode': 'ro', 'source': real,
                              'sha256': sha256(data).hexdigest(),
                              'bytes': len(data)})
        lib_dirs.add(str(Path(real).parent))
        bound_guests.add(interp)
    runtime_binds.sort(key=lambda item: item['guest'])
    lib_dirs.add(str(Path(sh_source).parent))
    lib_dirs.add('/pal-input/python/lib')
    child = {'PATH': '/usr/bin:/bin', 'PYTHONHOME': '/pal-input/python',
             'LD_LIBRARY_PATH': ':'.join(sorted(lib_dirs))}
    child.update(extra_child_env or {})
    plan = {
        'schema': 'research-linux-launch-v2',
        'generation': 'config_only_not_executed',
        'runner': {'bwrap_version': '0.11.1',
                   'execution': 'outer_runner_owned_separately',
                   'supervision': 'outside_workload_cgroup'},
        'image': {'sha256': manifest['sha256'], 'bytes': manifest['bytes'],
                  'version': '2.1.278', 'platform': 'linux-x86_64',
                  'member': 'claude',
                  'runtime_interp': '/lib64/ld-linux-x86-64.so.2',
                  'runtime_needed': ['libc.so.6'],
                  'closure_derived_from': 'image_bytes'},
        'namespaces': list(runner.NAMESPACES),
        'network': {'mode': 'loopback_only', 'external_egress': 'unavailable',
                    'address': '127.0.0.1',
                    'loopback': 'automatic_under_unshare_net_no_ip_command'},
        'mounts': [
            {'role': 'INPUT', 'host': str(payload_root),
             'guest': '/pal-input', 'readonly': True, 'kind': 'bind'},
            {'role': 'IMAGE', 'host': str(image_dir),
             'guest': '/pal-claude-image', 'readonly': True, 'kind': 'bind'},
            {'role': 'CONTROL', 'host': str(control_dir),
             'guest': '/pal-control', 'readonly': True, 'kind': 'bind'},
            {'role': 'OUTPUT', 'host': str(export_destination),
             'guest': '/pal-output', 'readonly': False, 'kind': 'tmpfs',
             'size_limit_bytes': runner.OUTPUT_BYTES,
             'host_role': 'export_destination'},
            {'role': 'SCRATCH', 'host': None, 'guest': '/pal-scratch',
             'readonly': False, 'kind': 'tmpfs',
             'size_limit_bytes': runner.SCRATCH_BYTES},
            {'role': 'TMP', 'host': None, 'guest': '/tmp', 'readonly': False,
             'kind': 'tmpfs', 'size_limit_bytes': runner.TMP_BYTES}],
        'export': {'destination': str(export_destination),
                   'bounded_bytes': runner.EXPORT_CAP_BYTES,
                   'creation': 'exclusive_no_follow',
                   'mounted_writable_in_namespace': False},
        'launcher': launcher_block,
        'runtime_binds': runtime_binds,
        'runtime_layout': {
            'guest_paths': 'canonical', 'ld_library_path': 'ld_library_path_env',
            'launcher_externals': 'shell_builtins_and_payload_python_only',
            'library_search': sorted(lib_dirs),
            'shell_guest': '/bin/sh', 'shell_source': sh_source},
        'environment': {'clearenv': True, 'setenv': child},
        'modes': [
            {'mode': 'qualify-version',
             'selection': 'outer_runner_final_command_replacement',
             'command': (['/pal-claude-image/claude', '--version']
                         if guest_code is None
                         else qualify_command_for(guest_code)),
             'expected_banner': '2.1.278 (Claude Code)',
             'synthetic_request': False, 'depends_on': []},
            {'mode': 'official-six', 'selection': 'plan_argv_final_command',
             'command': ['/pal-control/official-probe.sh',
                         '--isolated-host-attested'],
             'expected_banner': None, 'synthetic_request': True,
             'depends_on': ['qualify-version']}],
        'excluded_host_surfaces': ['agent_sockets', 'user_home'],
        'argv': None,
        'bounds': {'memory_mb': 4096, 'memory_swap_max': 0, 'pids_max': 64,
                   'deadline_seconds': 900,
                   'cgroup_controls': 'require_qualification_before_run'},
        'official_cli_executed': False,
        'activation_authorized': False}
    plan['argv'] = runner.canonical_argv(plan)
    problem = runner.plan_problem(plan)
    assert problem is None, problem
    plan_path = tmp_path / 'plan.json'
    plan_path.write_text(json.dumps(plan, indent=2) + '\n', encoding='ascii')
    return plan_path, plan


def _assert_clean_teardown(record):
    assert record['cgroup']['verified_empty'] is True
    assert 'teardown_failed' not in record['findings']
    assert not Path(record['cgroup']['path']).exists()
    run_record = Path(record['export']['destination']) / 'run-record.json'
    assert run_record.is_file(), 'run record must survive as evidence'
    return json.loads(run_record.read_text(encoding='utf-8'))


def _exported_result(plan, name='guest-result.json'):
    return json.loads((Path(plan['export']['destination']) / name)
                      .read_text(encoding='utf-8'))


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_bwrap_identity_admission():
    require_native_runner()
    identity = runner.bwrap_identity()
    assert identity['version'] == '0.11.1'
    mode = stat.S_IMODE(os.stat(identity['path']).st_mode)
    assert not mode & (stat.S_ISUID | stat.S_ISGID)
    assert re.fullmatch('[0-9a-f]{64}', identity['sha256'])
    assert identity['bytes'] > 0


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_namespace_separation_and_readonly_bindings(tmp_path):
    require_native_runner()
    host_uts_ino = os.stat('/proc/self/ns/uts').st_ino
    plan_path, plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_PROBE,
        extra_child_env={'PAL_TEST_HOST_PID': str(os.getpid()),
                         'PAL_TEST_HOST_PORT': '9',
                         'PAL_TEST_UTS_INO': str(host_uts_ino)},
        allocation='pal-l7-test-separation')
    record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                    deadline_seconds=120)
    evidence = _assert_clean_teardown(record)
    assert record['stop_condition'] == 'completed'
    assert evidence['mode'] == 'qualify-version'
    assert record['export']['files'] >= 1
    result = _exported_result(plan)
    assert result['host_pid_absent'] is True
    assert result['uidmap'] != Path('/proc/self/uid_map').read_text().strip()
    # --unshare-uts keeps the inherited nodename until sethostname is called,
    # so UTS isolation is proven by a distinct namespace inode instead.
    assert result['uts_ino'] != host_uts_ino
    assert result['input_readonly'] is True
    assert result['image_readonly'] is True
    assert result['control_readonly'] is True
    assert result['output_writable'] is True
    assert 'resource_limit_event' not in record['findings']


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_guest_loopback_listener_client(tmp_path):
    """The plan's pre-official loopback proof through the exact bwrap command."""
    require_native_runner()
    plan_path, plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_PROBE,
        extra_child_env={'PAL_TEST_HOST_PID': str(os.getpid()),
                         'PAL_TEST_HOST_PORT': '9'},
        allocation='pal-l7-test-loopback')
    record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                    deadline_seconds=120)
    _assert_clean_teardown(record)
    result = _exported_result(plan)
    assert result['loopback'] is True, 'guest loopback must work before L7 official'


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_host_loopback_and_external_egress_denied(tmp_path):
    require_native_runner()
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    try:
        port = server.getsockname()[1]
        plan_path, plan = build_synthetic_plan(
            tmp_path, guest_code=GUEST_PROBE,
            extra_child_env={'PAL_TEST_HOST_PID': str(os.getpid()),
                             'PAL_TEST_HOST_PORT': str(port)},
            allocation='pal-l7-test-egress')
        record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                        deadline_seconds=120)
        _assert_clean_teardown(record)
        result = _exported_result(plan)
        assert result['host_loopback_denied'] is True
        assert result['egress_denied'] is True
    finally:
        server.close()


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_escaped_descendant_cleanup(tmp_path):
    require_native_runner()
    plan_path, plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_ESCAPE, allocation='pal-l7-test-escaped')
    # Observe DURING the run that the escaped descendant is actually alive in
    # the workload cgroup (launcher, monitor, wrapper sh, python, survivor);
    # the survivor's pid is a NAMESPACE pid, meaningless against host /proc.
    observed = {'members': 0}
    outcome = {}

    def probe():
        outcome['record'] = runner.run_outer_probe(
            plan_path, mode='qualify-version', deadline_seconds=120,
            allocation='pal-l7-test-escaped')

    worker = threading.Thread(target=probe)
    worker.start()
    procs = Path(os.environ[CGROUP_ROOT_ENV], 'pal-l7-test-escaped',
                 'cgroup.procs')
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline and observed['members'] < 4:
        try:
            observed['members'] = len(procs.read_text().split())
        except OSError:
            pass
        time.sleep(0.05)
    worker.join(timeout=180)
    record = outcome['record']
    _assert_clean_teardown(record)
    # Steady state during the run: bwrap monitor + wrapper sh + entry python
    # + the escaped survivor (the bwrap launcher exits after setup).
    assert observed['members'] >= 4, 'escaped descendant never ran'
    survivor = int((Path(plan['export']['destination']) / 'survivor.txt')
                   .read_text(encoding='ascii').strip())
    assert survivor >= 2, 'survivor pid must be a guest-namespace pid'
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and procs.exists():
        try:
            remaining = procs.read_text().split()
        except OSError:
            remaining = []
        if not remaining:
            break
        time.sleep(0.1)
    assert not procs.exists() or not procs.read_text().split(), \
        'workload cgroup still occupied after teardown'


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_pids_resource_enforcement(tmp_path):
    require_native_runner()
    plan_path, plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_PIDS, allocation='pal-l7-test-pids')
    record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                    deadline_seconds=180)
    _assert_clean_teardown(record)
    result = _exported_result(plan)
    assert result['eagain'] is True
    assert result['forked'] < 100, 'pids.max must bound the process count'
    assert 'pids.events.max' in record['cgroup'].get('resource_limit_events', [])
    assert 'resource_limit_event' in record['findings']
    assert record['accepted'] is False


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_deadline_timeout_stop(tmp_path):
    require_native_runner()
    plan_path, _plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_SLEEP, allocation='pal-l7-test-timeout')
    record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                    deadline_seconds=3)
    _assert_clean_teardown(record)
    assert record['stop_condition'] == 'deadline_exceeded'
    assert record['accepted'] is False
    assert 'stop_condition_deadline_exceeded' in record['findings']


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_qualify_version_banner_gate(tmp_path):
    require_native_runner()
    # The stand-in prints the expected banner itself (the official plan's
    # pinned --version command produces the same bytes from the real CLI).
    plan_path, plan = build_synthetic_plan(
        tmp_path,
        guest_code="import sys; sys.stdout.write('2.1.278 (Claude Code)\\n')",
        allocation='pal-l7-test-qv-ok')
    record = runner.run_outer_probe(plan_path, mode='qualify-version',
                                    deadline_seconds=120)
    _assert_clean_teardown(record)
    assert record['mode'] == 'qualify-version'
    assert record['mode_depends_on'] == []
    assert record['execution']['stdout_bytes_value'] == b'2.1.278 (Claude Code)\n'
    assert record['execution']['holder_status'] == '0'
    assert record['accepted'] is True, record['findings']
    wrong = tmp_path.parent / (tmp_path.name + '-mismatch')
    wrong.mkdir()
    plan_path2, _plan2 = build_synthetic_plan(
        wrong, guest_code="import sys; sys.stdout.write('9.9.9 (Claude Code)\\n')",
        allocation='pal-l7-test-qv-bad')
    record2 = runner.run_outer_probe(plan_path2, mode='qualify-version',
                                     deadline_seconds=120)
    _assert_clean_teardown(record2)
    assert 'version_banner_mismatch' in record2['findings']
    assert record2['accepted'] is False


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_official_six_style_export_and_gate(tmp_path):
    require_native_runner()
    plan_path, plan = build_synthetic_plan(
        tmp_path, mode='official-six',
        payload_files={'write_evidence.py': PAYLOAD_WRITER},
        allocation='pal-l7-test-six')
    record = runner.run_outer_probe(plan_path, mode='official-six',
                                    deadline_seconds=120)
    _assert_clean_teardown(record)
    exported = Path(plan['export']['destination'])
    assert (exported / 'junit.xml').is_file()
    assert (exported / 'exit-code.txt').read_text(encoding='ascii').strip() == '0'
    assert (exported / 'pytest-tmp').is_dir()
    assert record['mode'] == 'official-six'
    assert record['mode_depends_on'] == ['qualify-version']
    assert record['execution']['holder_status'] == '0'
    assert 'export_limit_exceeded' not in record['findings']
    assert record['accepted'] is True, record['findings']
    manifest = json.loads((exported / 'export-manifest.json').read_text(
        encoding='utf-8'))
    names = {item['name'] for item in manifest['files']}
    assert {'junit.xml', 'exit-code.txt', 'pytest.log',
            'pal-holder-status'} <= names


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_driver_loss_cli(tmp_path):
    require_native_runner()
    root = Path(os.environ[CGROUP_ROOT_ENV])
    before = {entry.name for entry in root.glob('pal-l7-*')}
    plan_path, _plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_SLEEP, allocation='pal-l7-test-driver')
    process = subprocess.Popen(
        [sys.executable, str(ROOT / 'scripts' / 'run_claude_probe_linux.py'),
         'run', '--plan', str(plan_path), '--mode', 'qualify-version'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # A real driver is connected while the runner starts and disconnects
    # mid-run: hold the pipe open until the workload cgroup is populated
    # (the CLI derives a random allocation, so discover it by diff), then
    # close the pipe. (A pipe already at EOF when the CLI starts now means
    # "no driver ever connected" and must NOT trigger driver_lost.)
    populated = False
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail('runner exited before the driver disconnected')
        current = {entry.name for entry in root.glob('pal-l7-*')} - before
        if current:
            try:
                if (root / sorted(current)[0]).joinpath('cgroup.procs') \
                        .read_text().split():
                    populated = True
                    break
            except OSError:
                pass
        time.sleep(0.05)
    if not populated:
        process.kill()
        pytest.fail('workload cgroup never appeared for driver-loss run')
    # communicate() flushes stdin; detach the closed pipe first.
    process.stdin.close()
    process.stdin = None
    output, _error = process.communicate(timeout=180)
    result = json.loads(output.decode('utf-8').strip().splitlines()[-1])
    assert result['stop_condition'] == 'driver_lost'
    assert process.returncode == 1
    export = Path(_plan['export']['destination'])
    record = json.loads((export / 'run-record.json').read_text(encoding='utf-8'))
    assert record['cgroup']['verified_empty'] is True
    assert not Path(record['cgroup']['path']).exists()


@pytest.mark.skipif(not RUNNER_ENABLED, reason='explicit native probe-runner qualification is opt-in')
def test_native_supervisor_loss_cli(tmp_path):
    require_native_runner()
    root = Path(os.environ[CGROUP_ROOT_ENV])
    before = {entry.name for entry in root.glob('pal-l7-*')}
    plan_path, _plan = build_synthetic_plan(
        tmp_path, guest_code=GUEST_SLEEP, allocation='pal-l7-test-supervisor')
    process = subprocess.Popen(
        [sys.executable, str(ROOT / 'scripts' / 'run_claude_probe_linux.py'),
         'run', '--plan', str(plan_path), '--mode', 'qualify-version'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.monotonic() + 60
    created = None
    initial_members = []
    while time.monotonic() < deadline:
        current = {entry.name for entry in root.glob('pal-l7-*')} - before
        if current:
            created = root / sorted(current)[0]
            try:
                initial_members = created.joinpath('cgroup.procs').read_text().split()
            except OSError:
                initial_members = []
            if initial_members:
                break
        time.sleep(0.05)
    assert created is not None, 'workload cgroup never appeared'
    assert initial_members, 'workload processes never appeared'
    process.kill()
    process.wait(timeout=30)
    # Detach the closed stdin so communicate() below does not flush an
    # already-closed file; the namespace holder's EOF comes from the
    # supervisor-internal hold pipe closing when the killed runner dies.
    process.stdin.close()
    process.stdin = None
    members = initial_members
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            members = created.joinpath('cgroup.procs').read_text().split()
        except OSError:
            members = []
        if not members:
            break
        time.sleep(0.1)
    assert not members, 'workload survived supervisor loss'
    # Zombies of a SIGKILLed supervisor are reaped asynchronously by init;
    # the guarantee under test is that no LIVE process remains.
    def _live(pid):
        try:
            with open('/proc/%s/status' % pid) as handle:
                for line in handle:
                    if line.startswith('State:'):
                        return 'Z' not in line and 'X' not in line
            return True
        except OSError:
            return False
    deadline = time.monotonic() + 10
    remaining = list(initial_members)
    while time.monotonic() < deadline and remaining:
        remaining = [pid for pid in remaining if _live(pid)]
        time.sleep(0.1)
    assert not remaining, 'workload processes survived supervisor loss: %s' \
        % remaining
    try:
        created.rmdir()
    except OSError:
        pass
